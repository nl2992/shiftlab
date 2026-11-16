"""Stage 2 of 03F section 7: score the 12 v3 candidates on dev seeds 70000-70199 (scarce family),
apply the pre-stated rule and freeze configs/paper3/f3_v3_frozen.json + 03F_V3_SELECTION.md.

Rule: score = pooled equal-weight (47 regimes) mean J at h = 50; choose the lowest; candidates within
0.5% of the lowest are tied and the larger pi_min wins (then the lower score).
"""

import json
import sys

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.harness_v3 import (
    FROZEN_V3,
    OUT,
    R_of,
    cand_name,
    candidate_grid,
    load_family,
)

PROG = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme"
RES = PROG / "results/riskbudget"


def wilson(k, n, z=1.959964):
    p = k / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    d = 1 + z * z / n
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


def main(tag="v3_select"):
    names, rids, seeds, A = load_family(OUT / tag, "scarce")
    R = R_of(50)
    cands = {cand_name(c): c for c in candidate_grid()}
    rows = {}
    for i, n in enumerate(names):
        J = A["J"][i].mean(1)  # per regime
        sup = A["sup_harm"][i]
        viol = sup > R + 1e-9
        per = viol.mean(1)
        j = int(np.argmax(per))
        k, N = int(viol.sum()), viol.size
        rows[n] = {
            "score": float(J.mean()),
            "labels": float(A["n_queries"][i].mean()),
            "deployed": float(A["frac_time_deployed"][i].mean()),
            "violation_pooled": {"k": k, "n": N, "rate": k / N, "wilson": wilson(k, N)},
            "violation_worst_regime": {"regime": rids[j], "rate": float(per[j]),
                                       "k": int(viol[j].sum()), "n": viol.shape[1],
                                       "wilson": wilson(int(viol[j].sum()), viol.shape[1])},
        }  # fmt: skip
    cs = {n: rows[n] for n in cands}
    best = min(r["score"] for r in cs.values())
    tied = [n for n, r in cs.items() if r["score"] <= best * 1.005]
    pm_max = max(cands[n]["pi_min"] for n in tied)
    pool = [n for n in tied if cands[n]["pi_min"] == pm_max]
    chosen = min(pool, key=lambda n: cs[n]["score"])
    frozen = {
        "version": "f3_v3_frozen_v1",
        "note": "Frozen before any evaluation on fresh seeds or real streams (03F section 7).",
        "selected_candidate": chosen,
        "shield": cands[chosen],
        "inner": "tuned wald_cut of configs/paper3/f3_confirmation_arms_v1.json",
        "budget_rule": "R = 2k + h",
        "window": "declared delay (None in the shield => spec.delay_known; explicit in real runs)",
        "selection": {
            "seeds": [seeds[0], seeds[-1]],
            "score": "pooled equal-weight mean J over 47 scarce regimes at h = 50 (R = 60)",
            "best_score": best,
            "tied_within_0.5pct": tied,
            "rule": "lowest score; ties within 0.5% -> larger pi_min, then lower score",
        },
    }
    FROZEN_V3.write_text(json.dumps(frozen, indent=1))
    ref = {n: rows[n] for n in names if n not in cands}
    (RES / "v3_select_summary.json").write_text(
        json.dumps({"candidates": cs, "reference_arms": ref, "chosen": chosen}, indent=1)
    )
    L = [
        "# F v3: candidate selection (03F section 7, step 2)\n",
        (
            "Exploratory, simulation only. Scarce family `regimes_f3_scarce_v1.json` (47 regimes, T = 2000, "
            f"B = 200, k = 5), dev seeds {seeds[0]}-{seeds[-1]} ({len(seeds)} per regime), h = 50 (R = 60). "
            "Nothing here uses the 14 real streams, the confirmation block or model_selection.\n"
        ),
        (
            "Rule (fixed before running): score = pooled equal-weight mean J over the 47 regimes; choose the "
            "lowest; candidates within 0.5% of the lowest are tied and the larger pi_min wins (then the lower "
            "score). All candidates: delta .05, paced, ride-out, mixture grid V = 4, 16, 64, 256, 1024, 4096, "
            "window = declared delay, inner = frozen tuned wald_cut.\n"
        ),
        (
            "| candidate | pi_min | label_reserve | blind_margin | score (pooled J) | labels | deployed | "
            "violation pooled (Wilson) | worst regime (rate, Wilson) |\n|---|---|---|---|---|---|---|---|---|"
        ),
    ]
    for n, c in cands.items():
        r = rows[n]
        v, w = r["violation_pooled"], r["violation_worst_regime"]
        L.append(
            f"| {n} | {c['pi_min']:g} | {c['label_reserve_frac']:g} | {c['blind_margin']} | "
            f"{r['score']:.2f} | {r['labels']:.1f} | {r['deployed']:.3f} | "
            f"{v['k']}/{v['n']} ({v['wilson'][0]:.4f}-{v['wilson'][1]:.4f}) | "
            f"{w['rate']:.3f} ({w['wilson'][0]:.3f}-{w['wilson'][1]:.3f}) {w['regime']} |"
        )
    L += ["\nReference arms on the same tapes (h = 50, R = 60):\n",
          "| arm | score (pooled J) | labels | deployed | violation / exceedance of R = 60 pooled |",
          "|---|---|---|---|---|"]  # fmt: skip
    for n, r in ref.items():
        v = r["violation_pooled"]
        L.append(
            f"| {n} | {r['score']:.2f} | {r['labels']:.1f} | {r['deployed']:.3f} | "
            f"{v['k']}/{v['n']} ({v['rate']:.4f}) |"
        )
    L += [
        f"\nLowest score {best:.2f}; tied within 0.5% (<= {best * 1.005:.2f}): {', '.join(tied)}.\n",
        (
            f"**Chosen: {chosen}** (pi_min {cands[chosen]['pi_min']:g}, label_reserve_frac "
            f"{cands[chosen]['label_reserve_frac']:g}, blind_margin {cands[chosen]['blind_margin']}). "
            "Frozen in `configs/paper3/f3_v3_frozen.json` before the fresh evaluation.\n"
        ),
    ]
    (PROG / "03F_V3_SELECTION.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main(*sys.argv[1:2])
