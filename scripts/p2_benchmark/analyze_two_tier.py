"""Registered analysis for the FLQ two-tier re-test (written 2026-11-06, before any run).

Implements the decision rules in docs/p2_benchmark/FLQ_TWO_TIER_PROTOCOL.md. Fails closed if a
(regime, seed) cell is missing any policy or the seed count differs from the registration.

    uv run python scripts/p2_benchmark/analyze_two_tier.py --runs DIR [DIR ...] --out PREFIX
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

CANDIDATES = {  # candidate -> its host
    "gated_adaptive_range+front": "gated_adaptive_range",  # primary
    "gated_deployment+QCE+front": "gated_deployment",  # secondary (FLQ as registered in Atlas v2)
}
PRIMARY = "gated_adaptive_range+front"
COMPARATORS = [
    "gated_deployment",
    "gated_adaptive_range",
    "discern_style",
    "discern_design_floor",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
]
PACE = "gated_adaptive_range+pace_tuned"
UNCERTIFIED = "model_selector_causal"
NEVER = "CONTROL_never_switch"
POLICIES = sorted(set(CANDIDATES) | set(CANDIDATES.values()) | set(COMPARATORS)
                  | {PACE, UNCERTIFIED, NEVER})  # fmt: skip

TIER_A = {"V_null": 1000, "V_worse": 1000, "F0_null": 1000, "N_null": 1000}
TIER_B = {
    r: 500
    for r in [
        "V_null_dep_r5",
        "V_null_dep_r8",
        "N_null_dep_r7",
        "N_null_dep_r9",
        "W_null_dep_r95",
        "O_null_order2",
        "O_null_semimarkov",
    ]
}
REGION = {r: 200 for r in ["N_better_a", "N_better_b", "N_better_c", "N_dep_better_r6",
                           "N_near", "N_bursty"]}  # fmt: skip
REPLICATION = {r: 200 for r in ["V_better_a", "V_better_b", "V_better_c", "V_dep_better_r5",
                                "V_near", "V_bursty"]}  # fmt: skip
OUTSIDE = {r: 100 for r in ["V_late_600", "V_reversal_1000", "V_recurrent", "W_late_1000",
                            "W_reversal_700", "N_late_800", "N_reversal_900"]}  # fmt: skip

ALPHA = 0.05
DELTA_B = 5.0  # one switch cost
REGION_WINS_NEEDED = 4
PACE_BAND = 2.0
N_BOOT = 4000
BOOT_SEED = 20261106


def load(dirs: list[Path]) -> dict:
    cells: dict = defaultdict(dict)
    for d in dirs:
        with open(d / "records.jsonl") as f:
            for line in f:
                r = json.loads(line)
                cells[(r["regime"], r["seed"])][r["policy"]] = r
    return cells


def check(cells: dict, plan: dict) -> None:
    for regime, n in plan.items():
        seeds = sorted(s for (rg, s) in cells if rg == regime)
        if seeds != list(range(n)):
            raise SystemExit(f"{regime}: expected seeds 0..{n - 1}, found {len(seeds)}")
        for s in seeds:
            missing = set(POLICIES) - set(cells[(regime, s)])
            if missing:
                raise SystemExit(f"{regime} seed {s}: missing {sorted(missing)}")


def col(cells, regime, n, policy, field="net"):
    return np.array([float(cells[(regime, s)][policy][field]) for s in range(n)])


def t_ci(d: np.ndarray) -> tuple[float, float, float]:
    m = float(d.mean())
    if len(d) < 2 or d.std(ddof=1) == 0:
        return m, m, m
    h = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / math.sqrt(len(d))
    return m, m - h, m + h


def simultaneous_upper(diffs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One-sided simultaneous 95% upper bounds for the column means of ``diffs`` (seeds x k).

    Max-statistic paired bootstrap over seeds: c is the 95% quantile of max_k (m_k - m*_k)/se_k.
    A zero-variance column gets its mean as the bound.
    """
    n, _ = diffs.shape
    m = diffs.mean(0)
    se = diffs.std(0, ddof=1) / math.sqrt(n)
    live = se > 0
    if not live.any():
        return m
    idx = rng.integers(0, n, size=(N_BOOT, n))
    mstar = diffs[idx].mean(1)  # N_BOOT x k
    tmax = ((m[live] - mstar[:, live]) / se[live]).max(1)
    c = float(np.quantile(tmax, 0.95))
    return np.where(live, m + c * se, m)


def analyse(cells: dict) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    out: dict = {"candidates": {}}
    for cand, host in CANDIDATES.items():
        res: dict = {"host": host}
        # Tier A: hard gate on the claimed (iid conditional) null.
        tier_a = {}
        for rg, n in TIER_A.items():
            rate = float(col(cells, rg, n, cand, "ever_promote").mean())
            bound = ALPHA + 2 * math.sqrt(ALPHA * (1 - ALPHA) / n)
            tier_a[rg] = {"promotion": rate, "bound": bound, "pass": rate <= bound}
        res["tier_a"] = tier_a
        res["tier_a_pass"] = all(v["pass"] for v in tier_a.values())
        # Tier B: dependent nulls; economic tolerance vs host.
        tier_b = {}
        for rg, n in TIER_B.items():
            d = col(cells, rg, n, cand) - col(cells, rg, n, host)
            m, lo, hi = t_ci(d)
            tier_b[rg] = {
                "promotion": float(col(cells, rg, n, cand, "ever_promote").mean()),
                "host_promotion": float(col(cells, rg, n, host, "ever_promote").mean()),
                "dJ_vs_host": [m, lo, hi],
                "dJ_vs_never": list(t_ci(col(cells, rg, n, cand) - col(cells, rg, n, NEVER))),
                "pass": hi <= DELTA_B,
            }
        res["tier_b"] = tier_b
        res["tier_b_pass"] = all(v["pass"] for v in tier_b.values())
        # Efficacy: simultaneous superiority over every certified comparator.
        for label, plan in (("region", REGION), ("replication", REPLICATION)):
            rows = {}
            for rg, n in plan.items():
                c = col(cells, rg, n, cand)
                diffs = np.stack([c - col(cells, rg, n, k) for k in COMPARATORS], axis=1)
                ub = simultaneous_upper(diffs, rng)
                rows[rg] = {
                    "dJ_mean": dict(zip(COMPARATORS, diffs.mean(0).round(3).tolist())),
                    "sim_upper95": dict(zip(COMPARATORS, ub.round(3).tolist())),
                    "win": bool((ub < 0).all()),
                    "dJ_vs_host": list(t_ci(c - col(cells, rg, n, host))),
                    "dJ_vs_pace_tuned": list(t_ci(c - col(cells, rg, n, PACE))),
                }
            res[label] = rows
            res[f"{label}_wins"] = sum(v["win"] for v in rows.values())
        res["efficacy_pass"] = res["region_wins"] >= REGION_WINS_NEEDED
        # Outside the declared region: descriptive.
        res["outside"] = {
            rg: {
                "dJ_vs_host": list(t_ci(col(cells, rg, n, cand) - col(cells, rg, n, host))),
                "dJ_vs_never": list(t_ci(col(cells, rg, n, cand) - col(cells, rg, n, NEVER))),
                "dJ_vs_best_comparator_mean": min(
                    float((col(cells, rg, n, cand) - col(cells, rg, n, k)).mean())
                    for k in COMPARATORS
                ),
            }
            for rg, n in OUTSIDE.items()
        }
        pace_in_band = sum(
            -PACE_BAND <= v["dJ_vs_pace_tuned"][1] and v["dJ_vs_pace_tuned"][2] <= PACE_BAND
            for v in res["region"].values()
        )
        res["pace_equivalent_regimes"] = pace_in_band
        res["framing"] = "budget-feasible pacing" if pace_in_band >= REGION_WINS_NEEDED else (
            "front-loading")  # fmt: skip
        res["verdict"] = (
            "SUPPORTED"
            if res["tier_a_pass"] and res["tier_b_pass"] and res["efficacy_pass"]
            else "NOT_SUPPORTED"
        )
        out["candidates"][cand] = res
    out["uncertified_context"] = {
        rg: {
            "promotion": float(col(cells, rg, n, UNCERTIFIED, "ever_promote").mean()),
            "dJ_vs_never": list(t_ci(col(cells, rg, n, UNCERTIFIED) - col(cells, rg, n, NEVER))),
        }
        for rg, n in {**TIER_A, **TIER_B}.items()
    }
    out["primary_verdict"] = out["candidates"][PRIMARY]["verdict"]
    return out


def fmt(v):
    return f"{v[0]:+.1f} [{v[1]:+.1f}, {v[2]:+.1f}]"


def markdown(res: dict) -> str:
    L = [(f"# FLQ two-tier re-test: registered analysis output\n\nPrimary verdict "
         f"(`{PRIMARY}`): **{res['primary_verdict']}**\n")]  # fmt: skip
    for cand, r in res["candidates"].items():
        L.append(f"## {cand} (host `{r['host']}`): {r['verdict']}\n")
        L.append(f"Tier A pass: {r['tier_a_pass']}; Tier B pass: {r['tier_b_pass']}; region wins "
                 f"{r['region_wins']}/6 (need {REGION_WINS_NEEDED}); replication wins "
                 f"{r['replication_wins']}/6; framing: {r['framing']} "
                 f"({r['pace_equivalent_regimes']}/6 pace-equivalent).\n")  # fmt: skip
        L.append("| Tier A null | promotion | bound | pass |\n|---|---:|---:|---|")
        L += [f"| {k} | {v['promotion']:.3f} | {v['bound']:.4f} | {v['pass']} |"
              for k, v in r["tier_a"].items()]  # fmt: skip
        L.append("\n| Tier B null | promotion (host) | ΔJ vs host | ΔJ vs never | pass (≤ +5) |"
                 "\n|---|---:|---:|---:|---|")  # fmt: skip
        L += [f"| {k} | {v['promotion']:.3f} ({v['host_promotion']:.3f}) | {fmt(v['dJ_vs_host'])}"
              f" | {fmt(v['dJ_vs_never'])} | {v['pass']} |" for k, v in r["tier_b"].items()]  # fmt: skip
        for label in ("region", "replication"):
            L.append(f"\n| {label} regime | win | max simultaneous upper bound | ΔJ vs host | "
                     "ΔJ vs pace_tuned |\n|---|---|---:|---:|---:|")  # fmt: skip
            L += [f"| {k} | {v['win']} | {max(v['sim_upper95'].values()):+.2f} | "
                  f"{fmt(v['dJ_vs_host'])} | {fmt(v['dJ_vs_pace_tuned'])} |"
                  for k, v in r[label].items()]  # fmt: skip
        L.append("\n| outside regime | ΔJ vs host | ΔJ vs never | ΔJ vs best comparator (mean) |"
                 "\n|---|---:|---:|---:|")  # fmt: skip
        L += [f"| {k} | {fmt(v['dJ_vs_host'])} | {fmt(v['dJ_vs_never'])} | "
              f"{v['dJ_vs_best_comparator_mean']:+.1f} |" for k, v in r["outside"].items()]  # fmt: skip
        L.append("")
    L.append(f"## Uncertified context (`{UNCERTIFIED}`)\n\n| null | promotion | ΔJ vs never |"
             "\n|---|---:|---:|")  # fmt: skip
    L += [f"| {k} | {v['promotion']:.3f} | {fmt(v['dJ_vs_never'])} |"
          for k, v in res["uncertified_context"].items()]  # fmt: skip
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, nargs="+", type=Path, help="run directories")
    ap.add_argument("--out", required=True, type=Path, help="output prefix (writes .json, .md)")
    a = ap.parse_args(argv)
    cells = load(a.runs)
    check(cells, {**TIER_A, **TIER_B, **REGION, **REPLICATION, **OUTSIDE})
    res = analyse(cells)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps(res, indent=2) + "\n")
    a.out.with_suffix(".md").write_text(markdown(res))
    print(f"primary verdict: {res['primary_verdict']}")


if __name__ == "__main__":
    main()
