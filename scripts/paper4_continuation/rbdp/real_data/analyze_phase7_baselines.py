"""Summarise results/phase7_baselines/settings.jsonl: per chain, causal risk/alpha for P1-P7, VOI share of P1/P2/P6, support flag."""
import json, os, sys, collections
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
D = os.path.join(ROOT, "docs/paper4_continuation/rbdp/real_data/results", sys.argv[1] if len(sys.argv) > 1 else "phase7_baselines")
rows = [json.loads(l) for l in open(os.path.join(D, "settings.jsonl"))]
extra = {e["id"]: e for e in json.load(open(os.path.join(D, "extra_chains.json")))}
POL = {"P1_fixed_sample": "P1", "P2_count_sprt": "P2", "P3_hmm_filter": "P3", "P4_myopic_voi": "P4",
       "P5_iid_optimal_pomdp": "P5", "P6_eprocess_gate": "P6", "P7_rbdp_causal": "P7"}
names = sorted({r["policy"] for r in rows})
short = {n: n.split("_")[0] for n in names}
by = collections.defaultdict(lambda: collections.defaultdict(dict))
for r in rows:
    by[r["chain_id"]][r["setting_id"]][short[r["policy"]]] = r
out, lines = [], []
hdr = ("chain | n | r1 | #set | ratio_causal/alpha mean(max): P1 P2 P3 P4 P5 P6 P7 | VOI share median: P1 P2 P6 | "
       "P7 safe | any IID-calibrated (P3,P4,P5) breaks | P7 cost < all safe (P1,P2,P6)")
lines.append(hdr)
for cid, sets in by.items():
    ratio = collections.defaultdict(list); share = collections.defaultdict(list)
    p7safe = []; anybreak = []; below = []; vplus = 0
    for sid, d in sets.items():
        for p, r in d.items():
            ratio[p].append(r["ratio_causal_over_alpha"])
        s7 = d["P7"]["cost_saving_vs_never"]
        p7safe.append(not d["P7"]["violates"])
        anybreak.append(any(d[p]["violates"] for p in ("P3", "P4", "P5")))
        if s7 > 1e-9:
            vplus += 1
            for p in ("P1", "P2", "P6"):
                share[p].append(d[p]["cost_saving_vs_never"] / s7)
            below.append(all(d["P7"]["cost"] < d[p]["cost"] - 1e-9 for p in ("P1", "P2", "P6")))
    rec = {"chain": cid, "n": extra[cid]["n"], "r1": extra[cid]["r1"], "phase": extra[cid]["phase"], "settings": len(sets),
           "settings_with_voi": vplus,
           "ratio_mean": {p: float(np.mean(v)) for p, v in ratio.items()}, "ratio_max": {p: float(np.max(v)) for p, v in ratio.items()},
           "voi_share_median": {p: (float(np.median(v)) if v else None) for p, v in share.items()},
           "p7_safe_all": bool(all(p7safe)), "iid_calibrated_breaks_any": bool(any(anybreak)),
           "frac_settings_iid_break": float(np.mean(anybreak)),
           "p7_below_all_safe_frac": (float(np.mean(below)) if below else None)}
    rec["supports"] = bool(rec["p7_safe_all"] and rec["iid_calibrated_breaks_any"] and below and all(below))
    out.append(rec)
    f = lambda d, k: " ".join("%.2f(%.2f)" % (d["ratio_mean"][p], d["ratio_max"][p]) for p in k)
    v = lambda p: ("%.2f" % rec["voi_share_median"][p]) if rec["voi_share_median"].get(p) is not None else "NA"
    lines.append(f"{cid} | {rec['n']} | {rec['r1']:+.3f} | {len(sets)} | {f(rec, ['P1','P2','P3','P4','P5','P6','P7'])} | "
                 f"{v('P1')} {v('P2')} {v('P6')} | {rec['p7_safe_all']} | {rec['iid_calibrated_breaks_any']} ({rec['frac_settings_iid_break']:.2f}) | "
                 f"{rec['p7_below_all_safe_frac'] if rec['p7_below_all_safe_frac'] is None else '%.2f' % rec['p7_below_all_safe_frac']} | supports={rec['supports']}")
json.dump(out, open(os.path.join(D, "summary.json"), "w"), indent=1)
open(os.path.join(D, "summary.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("chains", len(out), "supports", sum(r["supports"] for r in out), "P7 safe all", sum(r["p7_safe_all"] for r in out),
      "iid break any", sum(r["iid_calibrated_breaks_any"] for r in out), "no VOI", sum(r["settings_with_voi"] == 0 for r in out))
