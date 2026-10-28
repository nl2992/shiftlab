"""Analyse E3 factorial rows (protocol P2): registered contrasts, Holm, descriptives, power.

  uv run --no-sync python scripts/analyze_e3.py --rows RUN/e3_rows.parquet --out RUN/analysis

Registered family (all in the primary stratum S* = onset "before", coverage averaged over
both levels, rollback "parity"), d = U(revert) - U(certify_promote):
  C1  interaction  mean[d_safe - d_deteriorating] > 0
  C2  safe sign    mean[d_safe] > 0
  C3  det. sign    mean[-d_deteriorating] > 0
  C4  background   mean[U(revert_while_certifying) - U(revert)]_deteriorating > 0
One-sided paired t on per-seed scalars, Holm over the four, alpha = 0.05. Paired bootstrap
intervals are a sensitivity check. U = expected_net_gain_vs_incumbent. Every seed is
analysed (no conditioning on alarms).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

UTILITY = "expected_net_gain_vs_incumbent"
KEYS = ["seed", "onset", "coverage", "rollback", "reference_state"]
STRATUM = {"onset": "before", "rollback": "parity"}
ALPHA = 0.05
BOOT_DRAWS = 10_000
BOOT_SEED = 20261030
POWER_TARGET = 0.9
EFFECT_SHRINK = 0.75  # development effects are shrunk before sizing (winner's curse)
NEXT_BLOCK_MAX = 10_000


def wide_utility(rows: pd.DataFrame, value: str = UTILITY) -> pd.DataFrame:
    wide = rows.pivot_table(index=KEYS, columns="response", values=value, aggfunc="first")
    if wide.isna().any().any():
        raise ValueError("unmatched response rows: every seed must enter every cell and response")
    return wide


def stratum_scalars(wide: pd.DataFrame) -> pd.DataFrame:
    """Per-seed scalars in S*: averages over the coverage levels, rows aligned by seed."""
    index = wide.index
    mask = (index.get_level_values("onset") == STRATUM["onset"]) & (
        index.get_level_values("rollback") == STRATUM["rollback"]
    )
    sub = wide[mask].reset_index()
    out = {}
    for state in ("safe", "deteriorating"):
        part = sub[sub.reference_state == state].groupby("seed")
        d = (part["revert"].mean() - part["certify_promote"].mean()).rename(f"d_{state}")
        bg = (part["revert_while_certifying"].mean() - part["revert"].mean()).rename(f"bg_{state}")
        out[f"d_{state}"], out[f"bg_{state}"] = d, bg
    return pd.DataFrame(out)


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    order = sorted(pvalues, key=pvalues.__getitem__)
    adjusted, running = {}, 0.0
    for rank, name in enumerate(order):
        running = max(running, min(1.0, (len(order) - rank) * pvalues[name]))
        adjusted[name] = running
    return adjusted


def one_sided_t(values: np.ndarray) -> tuple[float, float, float]:
    """Mean, sd and one-sided p for H1: mean > 0 (paired t on per-seed scalars)."""
    mean, sd = float(values.mean()), float(values.std(ddof=1))
    if sd == 0.0:
        return mean, sd, 0.0 if mean > 0 else 1.0
    t = mean / (sd / np.sqrt(len(values)))
    return mean, sd, float(stats.t.sf(t, df=len(values) - 1))


def bootstrap_ci(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(values), size=(BOOT_DRAWS, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def registered_contrasts(scalars: pd.DataFrame) -> pd.DataFrame:
    series = {
        "C1_interaction_safe_minus_det": scalars.d_safe - scalars.d_deteriorating,
        "C2_revert_over_promote_when_safe": scalars.d_safe,
        "C3_promote_over_revert_when_deteriorating": -scalars.d_deteriorating,
        "C4_background_cert_over_revert_when_deteriorating": scalars.bg_deteriorating,
    }
    rows, pvals = [], {}
    for name, values in series.items():
        arr = values.to_numpy(dtype=float)
        mean, sd, p = one_sided_t(arr)
        lo, hi = bootstrap_ci(arr)
        rows.append(
            {
                "contrast": name,
                "n_seeds": len(arr),
                "mean": mean,
                "sd": sd,
                "p_one_sided": p,
                "boot_ci95_low": lo,
                "boot_ci95_high": hi,
            }
        )
        pvals[name] = p
    adj = holm(pvals)
    frame = pd.DataFrame(rows)
    frame["p_holm"] = frame.contrast.map(adj)
    frame["reject_holm_0.05"] = frame.p_holm < ALPHA
    return frame


def power_table(contrasts: pd.DataFrame) -> pd.DataFrame:
    z_alpha = stats.norm.isf(ALPHA / len(contrasts))  # conservative: full Bonferroni level
    z_beta = stats.norm.isf(1 - POWER_TARGET)
    rows = []
    for rec in contrasts.itertuples():
        effect = EFFECT_SHRINK * rec.mean
        if effect <= 0 or rec.sd == 0:
            n = float("inf")
        else:
            n = float(np.ceil(((z_alpha + z_beta) * rec.sd / effect) ** 2))
        rows.append(
            {
                "contrast": rec.contrast,
                "dev_mean": rec.mean,
                "dev_sd": rec.sd,
                "shrunk_effect": effect,
                "n_for_power_0.9": n,
            }
        )
    frame = pd.DataFrame(rows)
    finite = frame["n_for_power_0.9"].replace(np.inf, np.nan).dropna()
    frame.attrs["recommended_n"] = (
        int(min(NEXT_BLOCK_MAX, max(finite.max(), 200))) if len(finite) else None
    )
    frame.attrs["unreachable"] = frame.loc[
        ~np.isfinite(frame["n_for_power_0.9"]), "contrast"
    ].tolist()
    return frame


def cell_descriptives(rows: pd.DataFrame) -> pd.DataFrame:
    group = rows.groupby(["onset", "coverage", "rollback", "reference_state", "response"])
    return group.agg(
        n=("seed", "nunique"),
        alarm_rate=("alarmed", "mean"),
        certified_rate=("certified", "mean"),
        infeasible_rate=("cert_infeasible", "mean"),
        mean_expected_net_gain=(UTILITY, "mean"),
        sd_expected_net_gain=(UTILITY, "std"),
        mean_realized_net_gain=("realized_net_gain_vs_incumbent", "mean"),
        mean_labels=("labels_total", "mean"),
        mean_compute_units=("compute_units", "mean"),
        mean_switches=("switches", "mean"),
        mean_rollbacks=("rollbacks", "mean"),
        mean_intervention_cost=("intervention_cost", "mean"),
    ).reset_index()


def main_effects(rows: pd.DataFrame) -> pd.DataFrame:
    """Descriptive only: mean utility by single factor level and response."""
    parts = []
    for factor in ("onset", "coverage", "rollback", "reference_state"):
        part = rows.groupby([factor, "response"])[UTILITY].mean().reset_index()
        part.insert(0, "factor", factor)
        part = part.rename(columns={factor: "level"})
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def all_cell_interactions(wide: pd.DataFrame) -> pd.DataFrame:
    """Descriptive: the revert-minus-promote interaction in every onset/coverage/rollback cell."""
    d = (wide["revert"] - wide["certify_promote"]).unstack("reference_state")
    delta = (d["safe"] - d["deteriorating"]).rename("interaction")
    out = (
        pd.concat([d["safe"].rename("d_safe"), d["deteriorating"].rename("d_det"), delta], axis=1)
        .groupby(["onset", "coverage", "rollback"])
        .agg(["mean", "std"])
    )
    out.columns = ["_".join(c) for c in out.columns]
    return out.reset_index()


def verdict(contrasts: pd.DataFrame) -> str:
    rejected = dict(zip(contrasts.contrast, contrasts["reject_holm_0.05"], strict=True))
    c1 = rejected["C1_interaction_safe_minus_det"]
    c2 = rejected["C2_revert_over_promote_when_safe"]
    c3 = rejected["C3_promote_over_revert_when_deteriorating"]
    if c1 and c2 and c3:
        return "crossover_supported"
    if c1:
        return "interaction_without_full_crossover"
    return "no_interaction_ranking_set_by_timing_and_rollback_only"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = pd.read_parquet(args.rows)
    manifest_path = args.rows.parent / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    )
    wide = wide_utility(rows)
    scalars = stratum_scalars(wide)
    contrasts = registered_contrasts(scalars)
    power = power_table(contrasts)
    args.out.mkdir(parents=True, exist_ok=True)
    contrasts.to_csv(args.out / "registered_contrasts.csv", index=False)
    power.to_csv(args.out / "power_from_dev.csv", index=False)
    cell_descriptives(rows).to_csv(args.out / "cell_descriptives.csv", index=False)
    main_effects(rows).to_csv(args.out / "main_effects_descriptive.csv", index=False)
    all_cell_interactions(wide).to_csv(
        args.out / "all_cell_interactions_descriptive.csv", index=False
    )
    summary = {
        "block": manifest.get("block"),
        "status": manifest.get("status"),
        "n_seeds": int(rows.seed.nunique()),
        "rows": len(rows),
        "utility": UTILITY,
        "stratum": {**STRATUM, "coverage": "mean of short and long"},
        "verdict": verdict(contrasts),
        "recommended_n_for_confirmation": power.attrs["recommended_n"],
        "unreachable_power_contrasts": power.attrs["unreachable"],
        "contrasts": contrasts.to_dict(orient="records"),
        "power": power.to_dict(orient="records"),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    pd.set_option("display.width", 220)
    print(contrasts.round(4).to_string(index=False))
    print(power.round(2).to_string(index=False))
    print(
        "verdict:",
        summary["verdict"],
        "| recommended n:",
        summary["recommended_n_for_confirmation"],
    )


if __name__ == "__main__":
    main()
