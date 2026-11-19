"""Summarise results/settings.jsonl -> results/summary.json and results/tables.md (tables pasted into IID_FAILURE.md)."""
import json, os, statistics as st
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "docs/paper4_continuation/rbdp/iid_failure/results")
rows = [json.loads(l) for l in open(os.path.join(OUT, "settings.jsonl"))]
POL = ["P1_fixed_sample", "P2_count_sprt", "P3_hmm_filter", "P4_myopic_voi", "P5_iid_optimal_pomdp", "P6_eprocess_gate", "P7_rbdp_causal"]
def stats(rs):
    if not rs: return None
    v = [r["ratio_causal_over_alpha"] for r in rs]
    return dict(n=len(v), min=min(v), median=st.median(v), max=max(v), n_violate=sum(r["violates"] for r in rs))
def key(r):
    return (r["group"], r["chain_type"])
S = {"n_settings": len({r["setting_id"] for r in rows}), "by": {}}
for name, f in [("all_non_shuffled", lambda r: r["group"] != "shuffled"), ("synthetic", lambda r: r["group"] == "synthetic"),
                ("synthetic_anti", lambda r: r["group"] == "synthetic" and r["chain_type"] == "anti-persistent"),
                ("synthetic_persistent", lambda r: r["group"] == "synthetic" and r["chain_type"] == "persistent"),
                ("real", lambda r: r["group"] == "real"), ("shuffled", lambda r: r["group"] == "shuffled"),
                ("shuffled_anti", lambda r: r["group"] == "shuffled" and r["chain_type"] == "anti-persistent"),
                ("shuffled_persistent", lambda r: r["group"] == "shuffled" and r["chain_type"] == "persistent")]:
    S["by"][name] = {p: stats([r for r in rows if r["policy"] == p and f(r)]) for p in POL}
    S["by"][name]["n_settings"] = len({r["setting_id"] for r in rows if f(r)})
# per real chain
S["per_real_chain"] = {}
for cid in sorted({r["chain_id"] for r in rows if r["group"] in ("real", "shuffled")}):
    S["per_real_chain"][cid] = {p: stats([r for r in rows if r["policy"] == p and r["chain_id"] == cid]) for p in POL}
# IID calibration check
S["iid_calibration"] = {p: max(abs(r["risk_iid"] - r["alpha"]) for r in rows if r["policy"] == p) for p in POL[:5]}
S["iid_risk_max_P6_P7"] = {p: max(r["risk_iid"] / r["alpha"] for r in rows if r["policy"] == p) for p in ("P6_eprocess_gate", "P7_rbdp_causal")}
S["P7_max_ratio"] = max(r["ratio_causal_over_alpha"] for r in rows if r["policy"] == "P7_rbdp_causal")
# cost consistency: P5 cost <= P1..P4 cost (IID-feasible) ; C0 match
bys = defaultdict(dict)
for r in rows: bys[r["setting_id"]][r["policy"]] = r
bad = [sid for sid, d in bys.items() if any(d["P5_iid_optimal_pomdp"]["cost"] > d[p]["cost"] + 1e-6 for p in POL[:4])]
S["P5_cost_above_some_P1_4"] = len(bad); S["P5_cost_above_examples"] = bad[:5]
S["C0_mismatch_max"] = max(abs(d["P5_iid_optimal_pomdp"]["C0"] - d["P5_iid_optimal_pomdp"]["solver_C0"]) for d in bys.values())
S["P7_cost_above_P6"] = sum(d["P7_rbdp_causal"]["cost"] > d["P6_eprocess_gate"]["cost"] + 1e-6 for d in bys.values())
S["P3_equals_P4_settings"] = sum(abs(d["P3_hmm_filter"]["cost"] - d["P4_myopic_voi"]["cost"]) < 1e-12 for d in bys.values())
# illustrations: belief-adaptive policies P3,P4,P5; non-shuffled
cand = [r for r in rows if r["group"] != "shuffled" and r["policy"] in POL[2:5] and r["violates"]]
real_best = {}
for r in sorted(cand, key=lambda r: -r["ratio_causal_over_alpha"]):
    if r["group"] == "real" and r["chain_id"] not in real_best: real_best[r["chain_id"]] = r
sel = list(real_best.values())[:3]
syn_seen, nsyn = set(), 0
for r in sorted(cand, key=lambda r: -r["ratio_causal_over_alpha"]):
    if r["group"] == "synthetic" and (r["t01"], r["t10"]) not in syn_seen and nsyn < 2:
        sel.append(r); syn_seen.add((r["t01"], r["t10"])); nsyn += 1
if len(sel) < 5:  # fill with next-largest real settings (other settings of failing chains), keep <=2 synthetic
    for r in sorted(cand, key=lambda r: -r["ratio_causal_over_alpha"]):
        if len(sel) >= 5: break
        if r["group"] == "real" and r not in sel: sel.append(r)
S["n_candidate_settings_for_illustration"] = len({r["setting_id"] for r in rows if r["group"] != "shuffled"})
S["illustrations"] = []
for r in sel:
    d = bys[r["setting_id"]]
    ctl = None
    S["illustrations"].append(dict(setting_id=r["setting_id"], group=r["group"], chain_id=r["chain_id"], policy=r["policy"],
        params=dict(t01=r["t01"], t10=r["t10"], e0=r["e0"], e1=r["e1"], prior1=r["prior1"], alpha=r["alpha"], B=r["B"], T=r["T"]),
        risk_iid=r["risk_iid"], risk_causal=r["risk_causal"], ratio=r["ratio_causal_over_alpha"], cost=r["cost"], C0=r["C0"],
        cost_P7=d["P7_rbdp_causal"]["cost"], ratio_all_policies={p: d[p]["ratio_causal_over_alpha"] for p in POL}))
json.dump(S, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
def fmt(s): return "-" if not s else f"{s['min']:.3f} / {s['median']:.3f} / {s['max']:.3f} | {s['n_violate']}/{s['n']}"
L = []
for name, d in S["by"].items():
    L.append(f"\n**{name}** ({d['n_settings']} settings)\n\n| policy | min / median / max of causal risk / alpha | violations (> alpha + 1e-9) |\n|---|---|---|")
    for p in POL: L.append(f"| {p} | {fmt(d[p])} |")
open(os.path.join(OUT, "tables.md"), "w").write("\n".join(L))
print(json.dumps({k: v for k, v in S.items() if k not in ("by", "per_real_chain")}, indent=1)); print("\n".join(L))
