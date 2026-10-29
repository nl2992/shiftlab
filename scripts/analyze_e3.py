"""Analyse E3 dose-response rows (protocol P2 v2): operating-region estimand.

  uv run --no-sync python scripts/analyze_e3.py --rows RUN/e3_rows.parquet --out RUN/analysis

Primary estimand (stratum S* = onset "before", rollback "parity", coverage averaged):
the dose curve D(dose) = E[U(revert) - U(certify_promote)] over the registered dose grid,
with 95% simultaneous paired-bootstrap max-t bands across the whole grid. Promote side:
band upper < 0; revert side: band lower > 0. The crossover threshold is the first grid dose
whose band lies on the promote side, bracketed by the previous dose, and it is reported only
if a lower dose lies on the revert side. A per-seed OLS slope of D on dose is the registered
monotone-trend statistic (secondary, one-sided t, descriptive support).

Decomposition (exact identity, per dose): promote advantage -D = U(promote) - U(revert)
  = [0 - U(revert)]  abstention component (staying on the incumbent instead of reverting)
  + [U(promote) - 0] promotion component (incremental utility versus `continue`).
Matched-wait control: U(promote) - U(wait_revert) and U(wait_revert) - U(revert) separate the
value of certifying from reverting later. Every seed is analysed; certification-conditional
utility is descriptive only. Failure to find a crossover is reported as "no crossover
detected on the grid at this n", never as "timing and rollback only".
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

UTILITY = "expected_net_gain_vs_incumbent"
DOSES = (0.0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0)
ONSETS = ("before", "at", "after")
COVERAGES = ("short", "long")
ROLLBACKS = ("off", "parity")
RESPONSES = ("continue", "revert", "certify_promote", "revert_while_certifying", "wait_revert")
KEYS = ["seed", "onset", "coverage", "rollback", "dose"]
STRATUM = {"onset": "before", "rollback": "parity"}
BAND_LEVEL = 0.95
BOOT_DRAWS = 10_000
BOOT_SEED = 20261030
POWER_TARGET = 0.9
EFFECT_SHRINK = 0.75  # development effects are shrunk before sizing (winner's curse)
NEXT_BLOCK_MAX = 10_000
MIN_CONFIRMATION_N = 500
CONFIRMATION_FIRST_SEED = 100300000
CONFIRMATION_N = 1000


def validate_grid(rows: pd.DataFrame) -> None:
    """Reject incomplete grids, duplicate rows, unregistered levels and NaN utilities."""
    required = set(KEYS) | {"response", UTILITY, "realized_net_gain_vs_incumbent"}
    if missing := required - set(rows.columns):
        raise ValueError(f"missing columns: {sorted(missing)}")
    if rows.duplicated(KEYS + ["response"]).any():
        raise ValueError("duplicate seed x cell x response rows")
    if rows[UTILITY].isna().any() or not np.isfinite(rows[UTILITY]).all():
        raise ValueError("non-finite utilities")
    observed = sorted(rows.dose.unique())
    if len(observed) != len(DOSES) or not np.allclose(observed, DOSES):
        raise ValueError(f"dose levels {observed} differ from registered {DOSES}")
    for column, levels in (
        ("onset", ONSETS),
        ("coverage", COVERAGES),
        ("rollback", ROLLBACKS),
        ("response", RESPONSES),
    ):
        if set(rows[column].unique()) != set(levels):
            raise ValueError(f"{column} levels differ from registered {levels}")
    per_seed = len(ONSETS) * len(COVERAGES) * len(ROLLBACKS) * len(DOSES) * len(RESPONSES)
    counts = rows.groupby("seed").size()
    if not (counts == per_seed).all():
        raise ValueError(f"incomplete grid: every seed needs exactly {per_seed} rows")


def validate_confirmation_seeds(rows: pd.DataFrame) -> None:
    """Confirmation needs exactly seeds 100300000-100300999 (n = 1000): no more, none missing."""
    expected = set(range(CONFIRMATION_FIRST_SEED, CONFIRMATION_FIRST_SEED + CONFIRMATION_N))
    observed = {int(x) for x in rows.seed.unique()}
    if observed != expected:
        missing, extra = sorted(expected - observed), sorted(observed - expected)
        raise ValueError(
            f"confirmation requires exactly seeds {CONFIRMATION_FIRST_SEED}.."
            f"{CONFIRMATION_FIRST_SEED + CONFIRMATION_N - 1}: "
            f"{len(missing)} missing, {len(extra)} extra"
        )


def is_confirmation(rows: pd.DataFrame, manifest: dict, forced: bool) -> bool:
    in_block = bool(
        (
            (rows.seed >= CONFIRMATION_FIRST_SEED) & (rows.seed < CONFIRMATION_FIRST_SEED + 10_000)
        ).any()
    )
    return forced or manifest.get("block") == "confirmation" or in_block


def wide_utility(rows: pd.DataFrame, value: str = UTILITY) -> pd.DataFrame:
    validate_grid(rows)
    return rows.pivot(index=KEYS, columns="response", values=value)


def stratum_curves(wide: pd.DataFrame) -> pd.DataFrame:
    """Per (seed, dose) responses in S*, averaged over the coverage levels."""
    idx = wide.index
    mask = (idx.get_level_values("onset") == STRATUM["onset"]) & (
        idx.get_level_values("rollback") == STRATUM["rollback"]
    )
    return wide[mask].reset_index().groupby(["seed", "dose"], as_index=True)[list(RESPONSES)].mean()


def curve_matrix(curves: pd.DataFrame, fn) -> np.ndarray:
    """seeds x doses matrix of a per-(seed, dose) statistic."""
    values = fn(curves)
    return values.unstack("dose").reindex(columns=list(DOSES)).to_numpy(dtype=float)


def simultaneous_band(matrix: np.ndarray) -> pd.DataFrame:
    """Paired bootstrap max-t simultaneous band over the dose columns (two-sided)."""
    n = matrix.shape[0]
    mean = matrix.mean(axis=0)
    se = matrix.std(axis=0, ddof=1) / np.sqrt(n)
    rng = np.random.default_rng(BOOT_SEED)
    max_t = np.empty(BOOT_DRAWS)
    chunk = 500
    for start in range(0, BOOT_DRAWS, chunk):
        size = min(chunk, BOOT_DRAWS - start)
        idx = rng.integers(0, n, size=(size, n))
        draws = matrix[idx]  # size x n x doses
        boot_mean = draws.mean(axis=1)
        boot_se = draws.std(axis=1, ddof=1) / np.sqrt(n)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(boot_se > 0, (boot_mean - mean) / boot_se, 0.0)
        max_t[start : start + size] = np.abs(t).max(axis=1)
    crit = float(np.quantile(max_t, BAND_LEVEL))
    return pd.DataFrame(
        {
            "dose": DOSES,
            "mean": mean,
            "sd": matrix.std(axis=0, ddof=1),
            "se": se,
            "crit": crit,
            "band_low": mean - crit * se,
            "band_high": mean + crit * se,
        }
    )


def crossover(band: pd.DataFrame) -> dict[str, object]:
    """Grid-bracketed crossover of D = revert - promote (positive: revert better).

    Bracket = (last dose below the threshold whose simultaneous band is entirely on the revert
    side, first dose whose band is entirely on the promote side]. If those doses are not
    adjacent on the grid, the wider interval is reported and the doses between them are listed
    as unresolved (neither side established). No crossover is claimed without a resolved
    revert-side dose below the first promote-side dose.
    """
    doses = [float(d) for d in band.dose]
    revert_side = [float(d) for d in band.dose[band.band_low > 0]]
    promote_side = [float(d) for d in band.dose[band.band_high < 0]]
    unresolved_all = [d for d in doses if d not in revert_side and d not in promote_side]
    threshold = None
    lower_resolved = None
    for dose in promote_side:
        below = [r for r in revert_side if r < dose]
        if below:
            threshold, lower_resolved = dose, max(below)
            break
    between = (
        [d for d in doses if lower_resolved < d < threshold]
        if threshold is not None and lower_resolved is not None
        else []
    )
    point_zero = [float(d) for d, m in zip(band.dose, band["mean"], strict=True) if m < 0]
    return {
        "revert_side_doses": revert_side,
        "promote_side_doses": promote_side,
        "unresolved_doses": unresolved_all,
        "crossover_found": threshold is not None,
        "threshold_dose": threshold,
        "bracket": (lower_resolved, threshold) if threshold is not None else None,
        "bracket_adjacent": threshold is not None and not between,
        "unresolved_doses_inside_bracket": between,
        "first_dose_with_negative_point_estimate": point_zero[0] if point_zero else None,
    }


def promotion_supported_doses(tables: dict[str, pd.DataFrame]) -> list[float]:
    """Promote-side doses (D band upper < 0) where promotion beats `continue` (band lower > 0).

    Other promote-side doses are reported as "promotion benefit not detected": an inconclusive
    band does not establish that promotion adds nothing, and no negligible-effect margin is
    registered, so no "abstention-only" claim is made.
    """
    d = tables["D_revert_minus_promote"]
    pb = tables["promotion_component_promote_vs_continue"]
    flag = (d.band_high < 0) & (pb.band_low > 0)
    return [float(x) for x in d.dose[flag]]


def trend_test(matrix: np.ndarray) -> dict[str, float]:
    """Registered monotone trend: per-seed OLS slope of D on dose, one-sided t (slope < 0)."""
    x = np.asarray(DOSES) - np.mean(DOSES)
    slopes = matrix @ x / np.sum(x**2)
    mean, sd = float(slopes.mean()), float(slopes.std(ddof=1))
    t = mean / (sd / np.sqrt(len(slopes))) if sd > 0 else (-np.inf if mean < 0 else np.inf)
    return {
        "mean_slope": mean,
        "sd": sd,
        "p_one_sided_negative": float(stats.t.cdf(t, len(slopes) - 1)),
    }


def dose_tables(curves: pd.DataFrame) -> dict[str, pd.DataFrame]:
    defs = {
        "D_revert_minus_promote": lambda c: c["revert"] - c["certify_promote"],
        "abstention_component_neg_revert": lambda c: -c["revert"],
        "promotion_component_promote_vs_continue": lambda c: c["certify_promote"],
        "promote_minus_wait_revert": lambda c: c["certify_promote"] - c["wait_revert"],
        "wait_revert_minus_revert_timing": lambda c: c["wait_revert"] - c["revert"],
        "background_cert_over_revert": lambda c: c["revert_while_certifying"] - c["revert"],
        "revert_vs_continue": lambda c: c["revert"],
    }
    return {name: simultaneous_band(curve_matrix(curves, fn)) for name, fn in defs.items()}


def probability_table(rows: pd.DataFrame) -> pd.DataFrame:
    """Alarm / certification / deployment / abstention / rollback probabilities per dose (S*)."""
    sub = rows[(rows.onset == STRATUM["onset"]) & (rows.rollback == STRATUM["rollback"])]
    out = []
    for (dose, response), g in sub.groupby(["dose", "response"]):
        cert = response in {"certify_promote", "revert_while_certifying"}
        out.append(
            {
                "dose": dose,
                "response": response,
                "n_rows": len(g),
                "p_alarm": g.alarmed.mean(),
                "p_cert_infeasible": g.cert_infeasible.mean() if cert else np.nan,
                "p_certified": g.certified.mean() if cert else np.nan,
                "p_deployed": g.deployed.mean() if cert else np.nan,
                "p_abstained_given_alarm": (
                    g.abstained.sum() / max(1, g.alarmed.sum()) if cert else np.nan
                ),
                "p_reference_rollback": (g.reference_rollback >= 0).mean(),
                "p_candidate_rollback": (g.candidate_rollback >= 0).mean(),
                "p_candidate_monitor_starved_given_deploy": (
                    g.candidate_monitor_starved.sum() / max(1, g.deployed.sum())
                    if response == "revert_while_certifying"
                    else np.nan
                ),
                "mean_utility": g[UTILITY].mean(),
                "mean_utility_given_certified": (
                    g.loc[g.certified, UTILITY].mean() if cert and g.certified.any() else np.nan
                ),
                "mean_utility_given_not_certified": (
                    g.loc[~g.certified, UTILITY].mean() if cert and (~g.certified).any() else np.nan
                ),
                "mean_labels_total": g.labels_total.mean(),
                "mean_labels_cert": g.labels_cert.mean(),
                "mean_labels_rollback": g.labels_rollback.mean(),
                "mean_compute_units": g.compute_units.mean(),
                "mean_switches": g.switches.mean(),
                "mean_rollbacks": g.rollbacks.mean(),
            }
        )
    return pd.DataFrame(out)


def cell_descriptives(rows: pd.DataFrame) -> pd.DataFrame:
    group = rows.groupby(["onset", "coverage", "rollback", "dose", "response"])
    return group.agg(
        n=("seed", "nunique"),
        alarm_rate=("alarmed", "mean"),
        certified_rate=("certified", "mean"),
        infeasible_rate=("cert_infeasible", "mean"),
        deployed_rate=("deployed", "mean"),
        mean_expected_net_gain=(UTILITY, "mean"),
        sd_expected_net_gain=(UTILITY, "std"),
        mean_realized_net_gain=("realized_net_gain_vs_incumbent", "mean"),
        mean_labels=("labels_total", "mean"),
        mean_compute_units=("compute_units", "mean"),
        mean_switches=("switches", "mean"),
        mean_rollbacks=("rollbacks", "mean"),
        mean_intervention_cost=("intervention_cost", "mean"),
    ).reset_index()


def power_table(bands: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """n so each decisive dose (dev band excludes 0) keeps its band off 0 with power 0.9."""
    z_beta = stats.norm.isf(1 - POWER_TARGET)
    rows = []
    for name, band in bands.items():
        for rec in band.itertuples():
            decisive = rec.band_low > 0 or rec.band_high < 0
            effect = EFFECT_SHRINK * abs(rec.mean)
            n = (
                float(np.ceil(((rec.crit + z_beta) * rec.sd / effect) ** 2))
                if effect > 0
                else np.inf
            )
            rows.append(
                {
                    "curve": name,
                    "dose": rec.dose,
                    "dev_mean": rec.mean,
                    "dev_sd": rec.sd,
                    "decisive_in_dev": decisive,
                    "n_for_power_0.9": n,
                }
            )
    frame = pd.DataFrame(rows)
    need = frame.loc[frame.decisive_in_dev, "n_for_power_0.9"]
    need = need[np.isfinite(need)]
    rec_n = MIN_CONFIRMATION_N
    if len(need):
        rec_n = int(min(NEXT_BLOCK_MAX, max(MIN_CONFIRMATION_N, np.ceil(need.max() / 100) * 100)))
    frame.attrs["recommended_n"] = rec_n
    return frame


def verdict(cross: dict[str, object]) -> str:
    if cross["crossover_found"]:
        return f"crossover_located_in_bracket_{cross['bracket']}"
    return "no_crossover_detected_on_grid_at_this_n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--confirmation", action="store_true")
    args = parser.parse_args()
    rows = pd.read_parquet(args.rows)
    manifest_path = args.rows.parent / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    )
    if is_confirmation(rows, manifest, args.confirmation):
        validate_confirmation_seeds(rows)
    wide = wide_utility(rows)  # validates the grid
    curves = stratum_curves(wide)
    tables = dose_tables(curves)
    primary = tables["D_revert_minus_promote"]
    cross = crossover(primary)
    trend = trend_test(curve_matrix(curves, lambda c: c["revert"] - c["certify_promote"]))
    power = power_table(
        {
            k: tables[k]
            for k in ("D_revert_minus_promote", "promotion_component_promote_vs_continue")
        }
    )
    supported = promotion_supported_doses(tables)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.out / f"dose_curve_{name}.csv", index=False)
    power.to_csv(args.out / "power_from_dev.csv", index=False)
    probability_table(rows).to_csv(args.out / "dose_probabilities_stratum.csv", index=False)
    cell_descriptives(rows).to_csv(args.out / "cell_descriptives.csv", index=False)
    summary = {
        "block": manifest.get("block"),
        "status": manifest.get("status"),
        "n_seeds": int(rows.seed.nunique()),
        "rows": len(rows),
        "utility": UTILITY,
        "stratum": {**STRATUM, "coverage": "mean of short and long"},
        "doses": list(DOSES),
        "simultaneous_band_level": BAND_LEVEL,
        "primary_crit": float(primary.crit.iloc[0]),
        "crossover": cross,
        "promotion_supported_promote_side_doses": supported,
        "trend": trend,
        "verdict": verdict(cross),
        "recommended_n_for_confirmation": power.attrs["recommended_n"],
        "primary_curve": primary.to_dict(orient="records"),
        "power": power.to_dict(orient="records"),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.set_option("display.width", 240)
    for name, table in tables.items():
        print(name)
        print(table.round(2).to_string(index=False))
    print(json.dumps({"crossover": cross, "trend": trend}, indent=1))
    print(power.round(1).to_string(index=False))
    print(
        "verdict:",
        summary["verdict"],
        "| recommended n:",
        summary["recommended_n_for_confirmation"],
    )


if __name__ == "__main__":
    main()
