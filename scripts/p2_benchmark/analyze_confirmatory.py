"""Registered analysis for the P2 confirmatory hypotheses H1-H7 (W4).

Implements docs/p2_benchmark/CONFIRMATORY_HYPOTHESES.md. Written and committed before any twin v3,
synthetic-confirmatory or fresh-real confirmatory policy run. Per-run fields (first promotion tau,
first-promotion EI, adv_rest) come from ``scripts/sota_sprint/wp2_score.load``.

    uv run python scripts/p2_benchmark/analyze_confirmatory.py \
        --twin DIR --twin-t1000 DIR --twin-t4000 DIR --synth DIR --fresh DIR \
        --out docs/p2_benchmark/results/confirmatory
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

from wp2_score import load

STRICT = ["gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front", "discern_style",
          "discern_design_floor", "SMCS+retain-incumbent"]  # fmt: skip
UNCERT = ["cams_adapter", "model_picker_adapter"]
DATASETS = ["metro", "beijing_pm25", "bike_hour", "appliances", "household_power"]
MEANREV_NULLS = ["F5_dep_null_r8", "F5_dep_null_r95", "O_null_semimarkov", "O_null_order2",
                 "WP2_o2_null", "WP2_sm_null", "WP2_hs_null"]  # fmt: skip
ALTS = ["F0_better", "F5_dep_better_r8", "S_dep_better_r95", "WP2_o2_better", "WP2_sm_better",
        "WP2_hs_better"]  # fmt: skip
CLAIMED_NULL = {"V1": ["F0_null"], "V2": ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95"]}
BOUND = 0.0936
N_BOOT = int(__import__("os").environ.get("P2_NBOOT", 4000))
SEED = 20261107


def ds_of(regime: str) -> str:
    for pre in ("twin3_", "twin2_", "twin_"):
        regime = regime.removeprefix(pre)
    return regime.split("_T")[0] if "_T" in regime and regime.split("_T")[-1].isdigit() else regime


def strat_boot(df, cluster, stratum, stat, rng):
    """Point estimate and bootstrap draws of ``stat(df)``, resampling clusters within strata."""
    groups = {s: g for s, g in df.groupby(stratum)}
    keys = {s: g[cluster].unique() for s, g in groups.items()}
    by = {s: {k: gg for k, gg in g.groupby(cluster)} for s, g in groups.items()}
    draws = []
    for _ in range(N_BOOT):
        parts = []
        for s, ks in keys.items():
            pick = rng.choice(ks, size=len(ks), replace=True)
            parts += [by[s][k] for k in pick]
        draws.append(stat(pd.concat(parts, ignore_index=True)))
    return stat(df), np.array(draws)


def eq_rate(d):  # equal-weight mean over strata of mean over clusters
    return float(
        d.groupby(["stratum", "cluster"]).ever_promote.mean().groupby("stratum").mean().mean()
    )


def ratio(num, den):
    return lambda d: float(d[num].sum() / max(d[den].sum(), 1e-12))


def q(draws, lo, hi):
    return [float(np.quantile(draws, lo)), float(np.quantile(draws, hi))]


def twin_frame(dirs):
    df = load(dirs)
    df["dataset"] = df.regime.map(ds_of)
    df["stratum"] = df["dataset"]
    df["cluster"] = df["dataset"] + "|" + df["split"].astype(str)
    df["promoted"] = (df.tau >= 0).astype(int)
    df["ei_first"] = df.ei.where(df.promoted == 1, 0)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("twin", "twin-t1000", "twin-t4000", "synth", "fresh"):
        ap.add_argument(f"--{k}", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expect-splits", type=int, default=120, help="registered: 120")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(SEED)
    res = {}

    tw = twin_frame([a.twin])
    if sorted(tw.dataset.unique()) != sorted(DATASETS):
        raise SystemExit(f"twin datasets {sorted(tw.dataset.unique())}")
    splits = tw.groupby("dataset").split.nunique()
    if (splits != a.expect_splits).any():
        raise SystemExit(f"expected {a.expect_splits} splits per dataset, got {splits.to_dict()}")
    strict = tw[tw.policy.isin(STRICT)]

    # H1: pooled strict-pool promotion on twin v3, 99% lower bound > .05.
    est, dr = strat_boot(strict, "cluster", "stratum", eq_rate, rng)
    res["H1"] = {
        "estimate": est,
        "ci99": q(dr, 0.005, 0.995),
        "pass": q(dr, 0.005, 0.995)[0] > 0.05,
    }
    # H1b: horizon re-windowings, descriptive.
    res["H1b"] = {"T2000": est}
    for T, d in (("T1000", a.twin_t1000), ("T4000", a.twin_t4000)):
        f = twin_frame([d])
        res["H1b"][T] = eq_rate(f[f.policy.isin(STRICT)])
    # H2: mean adv_rest at first promotion over the strict pool, 99% lower bound > 0.
    pr = strict[strict.promoted == 1].copy()
    est, dr = strat_boot(pr, "cluster", "stratum", lambda d: float(d.adv_rest.mean()), rng)
    res["H2"] = {"estimate": est, "ci99": q(dr, 0.005, 0.995), "n_promotions": len(pr),
                 "pass": q(dr, 0.005, 0.995)[0] > 0}  # fmt: skip

    sy = load([a.synth])
    sy["stratum"], sy["cluster"] = sy.regime, sy.regime + "|" + sy.seed.astype(str)
    sy["promoted"] = (sy.tau >= 0).astype(int)
    sy["ei_first"] = sy.ei.where(sy.promoted == 1, 0)
    # H3: equivalence of pi_EI between mean-reverting synthetic nulls and twin v3.
    mr = sy[sy.policy.isin(STRICT) & sy.regime.isin(MEANREV_NULLS)]
    pe_mr, d_mr = strat_boot(mr, "cluster", "stratum", ratio("ei_first", "promoted"), rng)
    pe_tw, d_tw = strat_boot(strict, "cluster", "stratum", ratio("ei_first", "promoted"), rng)
    diff = d_mr - d_tw
    ci = q(diff, 0.025, 0.975)
    res["H3"] = {"pi_ei_meanrev": pe_mr, "pi_ei_twin": pe_tw, "diff_ci95": ci,
                 "pass": -0.15 <= ci[0] and ci[1] <= 0.15 and 0.3 <= pe_mr <= 0.7
                 and 0.3 <= pe_tw <= 0.7}  # fmt: skip
    # H4: uncertified selectors, per-dataset 99% lower bound on promotion > .5.
    res["H4"] = {}
    for pol in UNCERT:
        rows = {}
        for ds in DATASETS:
            d = tw[(tw.policy == pol) & (tw.dataset == ds)]
            est, dr = strat_boot(d, "cluster", "stratum", eq_rate, rng)
            rows[ds] = {"estimate": est, "lb99": float(np.quantile(dr, 0.005))}
        res["H4"][pol] = rows
    res["H4"]["pass"] = all(v["lb99"] > 0.5 for pol in UNCERT for v in res["H4"][pol].values())
    # H5: synthetic dependent alternatives, J(A5b) - J(QSG), 99% lower bound > 0.
    alt = sy[sy.regime.isin(ALTS) & sy.policy.isin(["A5b", "QSG"])]
    w = alt.pivot_table(index=["stratum", "cluster"], columns="policy", values="net").reset_index()
    w["d"] = w["A5b"] - w["QSG"]
    est, dr = strat_boot(w, "cluster", "stratum",
                         lambda d: float(d.groupby("stratum").d.mean().mean()), rng)  # fmt: skip
    res["H5"] = {"estimate": est, "ci99": q(dr, 0.005, 0.995), "pass": q(dr, 0.005, 0.995)[0] > 0}
    # H6: A5b per dataset (95% upper bound vs .0936); H6b bike_hour 99% lower bound > .05.
    res["H6"] = {}
    for ds in DATASETS:
        d = tw[(tw.policy == "A5b") & (tw.dataset == ds)]
        est, dr = strat_boot(d, "cluster", "stratum", eq_rate, rng)
        res["H6"][ds] = {"estimate": est, "ub95": float(np.quantile(dr, 0.975)),
                         "lb99": float(np.quantile(dr, 0.005)),
                         "meets_bound": float(np.quantile(dr, 0.975)) <= BOUND}  # fmt: skip
    res["H6b_pass"] = res["H6"]["bike_hour"]["lb99"] > 0.05
    # H7: leaderboard under the single all-null gate vs the two-tier rule (descriptive).
    from bench2 import NULL_TESTED

    fr = load([a.fresh])
    fr["dataset"] = fr.regime.map(ds_of)
    jmean = fr.groupby(["policy", "dataset"]).net.mean().groupby("policy").mean()
    certified = [p for p in jmean.index if str(NULL_TESTED.get(p, "none")).startswith(("V1", "V2"))]
    nsy = sy[sy.regime.str.contains("null")]
    rate_sy = nsy.groupby(["policy", "regime"]).ever_promote.mean()
    rate_tw = tw.groupby(["policy", "dataset"]).ever_promote.mean()
    n_seeds = sy.groupby("regime").seed.nunique().min()
    tier_a_bound = 0.05 + 2 * math.sqrt(0.05 * 0.95 / n_seeds)
    single, two = [], []
    for p in certified:
        if rate_sy.loc[p].max() <= BOUND and rate_tw.loc[p].max() <= BOUND:
            single.append(p)
        cls = "V2" if str(NULL_TESTED[p]).startswith("V2") else "V1"
        if all(rate_sy.loc[(p, r)] <= tier_a_bound for r in CLAIMED_NULL[cls]):
            two.append(p)
    rank = lambda ps: [[p, float(jmean[p])] for p in sorted(ps, key=lambda p: jmean[p])]
    res["H7"] = {"tier_a_bound": tier_a_bound, "single_gate": rank(single), "two_tier": rank(two),
                 "top_changes": (rank(single)[:1] != rank(two)[:1])}  # fmt: skip

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    lines = ["# P2 confirmatory hypotheses: registered analysis output\n"]
    for h in ("H1", "H2", "H3", "H5"):
        lines.append(f"- **{h}**: {json.dumps(res[h], default=float)}")
    lines.append(f"- **H1b**: {res['H1b']}")
    lines.append(f"- **H4** pass: {res['H4']['pass']}; " + json.dumps(
        {p: {d: round(v['lb99'], 3) for d, v in res['H4'][p].items()} for p in UNCERT}))  # fmt: skip
    lines.append("- **H6**: " + json.dumps({d: {k: (round(v, 4) if isinstance(v, float) else v)
                 for k, v in r.items()} for d, r in res["H6"].items()}) + f"; H6b pass: {res['H6b_pass']}")  # fmt: skip
    lines.append(
        f"- **H7**: single gate {res['H7']['single_gate']}; two-tier {res['H7']['two_tier']}"
    )
    a.out.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
