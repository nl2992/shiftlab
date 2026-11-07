"""Registered analysis for the P2 Tier B validity gate (H8).

Implements docs/p2_benchmark/TIER_B_GATE_PROTOCOL.md. Committed before any H8 cohort run.

    PYTHONPATH=scripts/promising_directions/sota uv run python scripts/p2_benchmark/analyze_tier_b.py \
        --synth DIR --twin DIR --out docs/p2_benchmark/results/tier_b
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

CERTIFIED = ["A5b", "D2", "D5", "QSG", "SMCS+retain-incumbent", "choe_ramdas_eb",
             "choe_ramdas_eb+front", "discern_design_floor", "discern_style", "gated_adaptive_range",
             "gated_adaptive_range+front", "gated_deployment", "gated_deployment+QCE",
             "gated_deployment+QCE+front", "rmm:gated_deployment+RMM", "xu_acquisition_only"]  # fmt: skip
CONTROL = "CONTROL_never_switch"
SYN_NULLS = ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95", "O_null_semimarkov", "O_null_order2",
             "WP2_o2_null", "WP2_sm_null", "WP2_hs_null"]  # fmt: skip
ALTS = ["F0_better", "F5_dep_better_r8", "S_dep_better_r95", "WP2_o2_better", "WP2_sm_better",
        "WP2_hs_better"]  # fmt: skip
DATASETS = ["metro", "beijing_pm25", "bike_hour", "appliances", "household_power"]
CLAIMED = {"V1": ["F0_null"], "V2": ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95"]}
PREDICTED_ADMIT = {"A5b", "D5", "discern_design_floor", "discern_style", "gated_adaptive_range",
                   "gated_deployment"}  # fmt: skip
P_STAR = "gated_adaptive_range"
H8B = ["QSG", "SMCS+retain-incumbent"]
TOL, SINGLE_BOUND = 5.0, 0.0936
N_BOOT = int(os.environ.get("P2_NBOOT", "4000"))
SEED = 20261108
FIELDS = ("regime", "split", "seed", "policy", "net", "labels", "db", "harm", "ever_promote")


def read(d: Path) -> pd.DataFrame:
    rows = []
    with open(d / "records.jsonl") as f:
        for line in f:
            r = json.loads(line)
            rows.append({k: r[k] for k in FIELDS})
    return pd.DataFrame(rows)


def ds_of(regime: str) -> str:
    for pre in ("twin4_", "twin3_"):  # twin3_ only for development smoke runs
        regime = regime.removeprefix(pre)
    return regime


def boot_mean(values: np.ndarray, rng) -> np.ndarray:
    idx = rng.integers(0, len(values), size=(N_BOOT, len(values)))
    return values[idx].mean(axis=1)


def claim_class(p: str) -> str:
    from bench2 import NULL_TESTED

    c = str(NULL_TESTED[p])
    if not c.startswith(("V1", "V2")):
        raise SystemExit(f"{p} is not certified in bench2.NULL_TESTED: {c}")
    return c[:2]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--synth", required=True, type=Path)
    ap.add_argument("--twin", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expect-null-seeds", type=int, default=500, help="registered: 500")
    ap.add_argument("--expect-alt-seeds", type=int, default=200, help="registered: 200")
    ap.add_argument("--expect-splits", type=int, default=120, help="registered: 120")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(SEED)

    sy, tw = read(a.synth), read(a.twin)
    tw["null"] = tw.regime.map(ds_of)
    tw["cl"] = tw["null"] + "|" + tw.split.astype(str)
    sy["null"], sy["cl"] = sy.regime, sy.seed.astype(str)
    for name, frame, regs, n, key in (("null", sy, SYN_NULLS, a.expect_null_seeds, "seed"),
                                      ("alt", sy, ALTS, a.expect_alt_seeds, "seed"),
                                      ("twin", tw, DATASETS, a.expect_splits, "cl")):  # fmt: skip
        got = frame[frame.null.isin(regs)].groupby("null")[key].nunique()
        if sorted(got.index) != sorted(regs):
            raise SystemExit(f"{name}: regimes {sorted(got.index)}")
        if (got != n).any():
            raise SystemExit(f"{name}: expected {n} per regime, got {got.to_dict()}")
    for p in [*CERTIFIED, CONTROL]:
        for frame in (sy, tw):
            if p not in set(frame.policy):
                raise SystemExit(f"missing policy {p}")

    nulls = pd.concat([sy[sy.regime.isin(SYN_NULLS)], tw], ignore_index=True)
    nulls["dh"] = -nulls.db
    n_seeds = a.expect_null_seeds
    tier_a_bound = 0.05 + 2 * math.sqrt(0.05 * 0.95 / n_seeds)
    all_nulls = SYN_NULLS + DATASETS
    gates, dh_tables = {}, {}
    for p in CERTIFIED:
        cls = claim_class(p)
        d = nulls[nulls.policy == p]
        rate = d.groupby("null").ever_promote.mean()
        tier_a = {n: float(rate[n]) for n in CLAIMED[cls]}
        tb = {}
        for n in all_nulls:
            if n in CLAIMED[cls]:
                continue
            v = d[d.null == n].groupby("cl").dh.mean().to_numpy()  # cluster means
            dr = boot_mean(v, rng)
            harm_all = d[d.null == n].harm.mean()
            tb[n] = {"mean": float(v.mean()), "ub95": float(np.quantile(dr, 0.975)),
                     "lb95": float(np.quantile(dr, 0.025)), "promote": float(rate[n]),
                     "all_in_harm_mean": float(harm_all)}  # fmt: skip
        pass_a = all(r <= tier_a_bound for r in tier_a.values())
        pass_b = all(r["ub95"] <= TOL for r in tb.values())
        single = all(float(rate[n]) <= SINGLE_BOUND for n in all_nulls)
        worst = max(tb, key=lambda n: tb[n]["ub95"])
        gates[p] = {"class": cls, "tier_a_rates": tier_a, "pass_tier_a": pass_a,
                    "pass_tier_b": pass_b, "two_tier": pass_a and pass_b, "single_gate": single,
                    "worst_tier_b_null": worst, "worst_tier_b_ub95": tb[worst]["ub95"],
                    "max_null_promotion": float(rate[all_nulls].max())}  # fmt: skip
        dh_tables[p] = tb

    alt = sy[sy.regime.isin(ALTS)]
    jmean = alt.groupby(["policy", "regime"]).net.mean().groupby("policy").mean()
    two = sorted((p for p in CERTIFIED if gates[p]["two_tier"]), key=lambda p: jmean[p])
    single = sorted((p for p in CERTIFIED if gates[p]["single_gate"]), key=lambda p: jmean[p])
    res = {"n_boot": N_BOOT, "tier_a_bound": tier_a_bound, "tolerance": TOL,
           "two_tier_admitted": [[p, float(jmean[p])] for p in two],
           "single_gate_admitted": [[p, float(jmean[p])] for p in single],
           "control_J": float(jmean[CONTROL])}  # fmt: skip

    # H8a: Tier A alone.
    res["H8a"] = {
        "n_pass_tier_a": sum(g["pass_tier_a"] for g in gates.values()),
        "of": len(CERTIFIED),
    }

    # H8b: decision harm on F5_dep_null_r95, 99% lower bound > 0, QSG and SMCS separately.
    res["H8b"] = {}
    for p in H8B:
        v = nulls[(nulls.policy == p) & (nulls.null == "F5_dep_null_r95")].groupby("cl").dh.mean()
        dr = boot_mean(v.to_numpy(), rng)
        lb = float(np.quantile(dr, 0.005))
        res["H8b"][p] = {"mean": float(v.mean()), "lb99": lb, "pass": lb > 0}
    res["H8b"]["pass"] = all(res["H8b"][p]["pass"] for p in H8B)

    # H8c: P* two-tier admitted, single-gate rejected, paired J(P*) - J(S*) 99% UB < -5.
    s_star = single[0] if single else CONTROL
    w = alt[alt.policy.isin([P_STAR, s_star])].pivot_table(
        index=["regime", "seed"], columns="policy", values="net"
    )
    diff = (w[P_STAR] - w[s_star]).reset_index(name="d")
    groups = [g.d.to_numpy() for _, g in diff.groupby("regime")]
    est = float(np.mean([g.mean() for g in groups]))
    dr = np.mean([boot_mean(g, rng) for g in groups], axis=0)
    ub = float(np.quantile(dr, 0.995))
    c1, c2, c3 = gates[P_STAR]["two_tier"], not gates[P_STAR]["single_gate"], ub < -TOL
    res["H8c"] = {"P_star": P_STAR, "S_star": s_star, "diff_mean": est,
                  "ci99": [float(np.quantile(dr, 0.005)), ub], "i_two_tier_admits": c1,
                  "ii_single_rejects": c2, "iii_ub_below_minus5": c3,
                  "pass": bool(c1 and c2 and c3)}  # fmt: skip

    # H8d: prediction scorecard.
    obs = {p for p in CERTIFIED if gates[p]["two_tier"]}
    res["H8d"] = {"predicted": sorted(PREDICTED_ADMIT), "observed": sorted(obs),
                  "agree": sum((p in obs) == (p in PREDICTED_ADMIT) for p in CERTIFIED),
                  "of": len(CERTIFIED)}  # fmt: skip
    res["gates"], res["tier_b"] = gates, dh_tables

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    lines = ["# P2 Tier B gate (H8): registered analysis output\n",
             f"- two-tier admitted: {res['two_tier_admitted']}",
             f"- single gate admitted: {res['single_gate_admitted']}",
             f"- H8a: {res['H8a']}", f"- H8b: {json.dumps(res['H8b'])}",
             f"- H8c: {json.dumps(res['H8c'])}",
             f"- H8d: agree {res['H8d']['agree']}/{res['H8d']['of']}; observed {res['H8d']['observed']}",
             "", "| policy | class | Tier A | Tier B | worst null | worst UB95 | single | J alt |",
             "|---|---|---|---|---|---:|---|---:|"]  # fmt: skip
    for p in sorted(CERTIFIED, key=lambda p: jmean[p]):
        g = gates[p]
        lines.append(f"| {p} | {g['class']} | {g['pass_tier_a']} | {g['pass_tier_b']} | "
                     f"{g['worst_tier_b_null']} | {g['worst_tier_b_ub95']:.2f} | "
                     f"{g['single_gate']} | {jmean[p]:.1f} |")  # fmt: skip
    a.out.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
