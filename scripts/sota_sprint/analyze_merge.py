"""Amendment 6 (P1 x P2 merge) analysis, exactly as registered: HM1 validity, HM2 late benefit, HM3.

    uv run python scripts/sota_sprint/analyze_merge.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_real import contrast as ep_contrast
from analyze_twin_null import boot
from analyze_validation import BOUND, CERT, diff, holm, wilson

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/sota_sprint/merge"
DATA = ROOT / "data/sprint_twin_losses"
DOC = ROOT / "docs/sota_sprint/merge"
CANDS = ["M_LRMD_SUI", "M_RMMSUI_A5b", "M_RMMSUI_gar"]
HM1_NULLS = ["V_null", "V_worse", "V_null_dep_r8", "W_null_dep_r9", "W_null_dep_r95"]
LATE = ["V_late_600", "W_late_1000"]
CERT_PUB = CERT  # certified published class incl. the QCE betting ports (Amendment 2)


def main():
    syn = pd.read_json(OUT / "synth/records.jsonl", lines=True)
    nul = pd.read_json(OUT / "null1000/records.jsonl", lines=True)
    twin = pd.read_json(OUT / "twin_null/records.jsonl", lines=True)
    real = pd.read_json(OUT / "real_fresh/records.jsonl", lines=True)
    res = {}
    for c in CANDS:
        r = {"nulls": {}, "twin": {}, "late": {}, "stationary": {}, "reversal": {}, "real": {}}
        for reg, g in nul[nul.policy == c].groupby("regime"):
            k, n = int(g.ever_promote.sum()), len(g)
            r["nulls"][reg] = {"rate": k / n, "wilson_hi": round(wilson(k, n)[1], 4)}
        for reg, g in twin[twin.policy == c].groupby("regime"):
            split = np.load(DATA / f"{reg}.npz")["split"]
            per = g.assign(split=split[g.ep.to_numpy()]).groupby("split").ever_promote.mean().to_numpy()
            lo, hi = boot(per)
            r["twin"][reg] = {"rate": float(per.mean()), "boot_lo": lo, "boot_hi": hi}
        hm1 = all(r["nulls"][x]["wilson_hi"] <= BOUND for x in HM1_NULLS) and \
            all(v["boot_hi"] <= BOUND for v in r["twin"].values())
        tests = []
        for reg in LATE:
            Q = syn[syn.regime == reg].pivot_table(index="seed", columns="policy", values="net")
            bc = Q[[x for x in CERT_PUB if x in Q]].mean().idxmin()
            vs_a5b, vs_bc = diff(Q, c, "A5b"), diff(Q, c, bc)
            gain_iid = Q[bc].mean() - Q["rmm:gated_deployment+RMM"].mean()
            r["late"][reg] = {"vs_A5b": vs_a5b, "vs_best_certified": vs_bc,
                              "retained_fraction_of_iid_RMM_gain":
                                  round(float((Q[bc].mean() - Q[c].mean()) / gain_iid), 3) if gain_iid > 0 else None}
            tests.append(vs_bc["p_one_sided_less"])
        adj = holm(np.array(tests))
        for reg, a in zip(LATE, adj):
            r["late"][reg]["vs_best_certified"]["holm_p"] = round(float(a), 6)
        hm2 = all(r["late"][x]["vs_A5b"]["hi"] < 0 for x in LATE) and all(a < 0.05 for a in adj)
        for reg in ["V_better_a", "V_better_b", "V_better_c", "V_near"]:
            Q = syn[syn.regime == reg].pivot_table(index="seed", columns="policy", values="net")
            bc = Q[[x for x in CERT_PUB if x in Q]].mean().idxmin()
            r["stationary"][reg] = {"vs_A5b": diff(Q, c, "A5b"), "vs_best_certified": diff(Q, c, bc)}
        for reg in ["V_reversal_1000", "W_reversal_700", "V_recurrent"]:
            Q = syn[syn.regime == reg].pivot_table(index="seed", columns="policy", values="net")
            r["reversal"][reg] = {"vs_A5b": diff(Q, c, "A5b"), "vs_never": diff(Q, c, "CONTROL_never_switch")}
        for ds, g in real.groupby("regime"):
            E = g.groupby(["ep", "policy"]).net.mean().unstack()
            bc = E[[x for x in CERT_PUB if x in E]].mean().idxmin()
            r["real"][ds] = {"vs_A5b": ep_contrast(E, c, "A5b"), "vs_best_certified": ep_contrast(E, c, bc)}
        r["HM1"], r["HM2"] = bool(hm1), bool(hm2)
        res[c] = r
    res["merge_success"] = res["M_LRMD_SUI"]["HM1"] and res["M_LRMD_SUI"]["HM2"]
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "merge_results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")

    def ci(d):
        return f"{d['mean']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}]"

    L = [f"# P1 x P2 merge (Amendment 6): **{'SUCCESS' if res['merge_success'] else 'NOT MET'}** (primary M_LRMD_SUI)", ""]
    for c in CANDS:
        r = res[c]
        L += [f"## {c}: HM1 validity {'PASS' if r['HM1'] else 'FAIL'}; HM2 late benefit {'PASS' if r['HM2'] else 'FAIL'}", "",
              "Nulls (1000 seeds): " + "; ".join(f"{k} {v['rate']:.3f} (ub {v['wilson_hi']:.3f})" for k, v in r["nulls"].items()),
              "",
              "Twin-null real (split bootstrap): " + "; ".join(f"{k.removeprefix('twin_')} {v['rate']:.3f} [{v['boot_lo']:.3f},{v['boot_hi']:.3f}]" for k, v in r["twin"].items()),
              ""]
        for reg, v in r["late"].items():
            L.append(f"* {reg}: vs A5b {ci(v['vs_A5b'])}; vs best certified {ci(v['vs_best_certified'])} ({v['vs_best_certified']['vs']}, Holm p={v['vs_best_certified']['holm_p']:.3g}); retained fraction of iid-RMM gain {v['retained_fraction_of_iid_RMM_gain']}")
        L.append("* stationary vs A5b / best certified: " + "; ".join(f"{k} {ci(v['vs_A5b'])} / {ci(v['vs_best_certified'])}" for k, v in r["stationary"].items()))
        L.append("* reversal/recurrent vs A5b: " + "; ".join(f"{k} {ci(v['vs_A5b'])}" for k, v in r["reversal"].items()))
        L.append("* fresh real vs A5b / best certified (improved/K): " + "; ".join(
            f"{k} {v['vs_A5b']['mean']:+.1f} / {v['vs_best_certified']['mean']:+.1f} ({v['vs_best_certified']['improved']}/{v['vs_best_certified']['K']})" for k, v in r["real"].items()))
        L.append("")
    (DOC / "merge_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
