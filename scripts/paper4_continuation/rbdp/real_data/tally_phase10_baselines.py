"""Old (35) vs new (35+4) tallies of the T16/32 panel (Phase 7 rows + Phase 9 safe baselines).
With --phase10c: previous 39 vs combined 44 (39 + the 5 Phase 10c chains) vs the 5 alone, written to
results/phase10c_baselines/tally.json (key "old" = 39 chains, "new" = 44, "added" = the 5); phase10_baselines/tally.json is not touched.
"""
import json, collections, os, sys
R = "docs/paper4_continuation/rbdp/real_data/results/"
def rd(p): return [json.loads(l) for l in open(R + p)]
P7 = rd("phase7_baselines_T16_32/settings.jsonl"); P7n = rd("phase10_baselines/settings.jsonl")
P9 = rd("phase9_panel.jsonl"); P9n = rd("phase10_baselines_panel9.jsonl")
NEWIDS = {r["chain_id"] for r in P7n}
def tally(p7, p9, label):
    ch = {r["chain_id"] for r in p7 if "policy" in r}
    br = collections.defaultdict(float); viol = collections.Counter(); cnt = collections.Counter()
    for r in p7:
        if "policy" not in r: continue
        s = r["policy"].split("_")[0]
        br[(s, r["chain_id"])] = max(br[(s, r["chain_id"])], r["ratio_causal_over_alpha"])
        if r["ratio_causal_over_alpha"] > 1 + 1e-9: viol[s] += 1
    iidb = {c for c in ch if any(br[(p, c)] > 1 + 1e-9 for p in ("P3", "P4", "P5"))}
    mx = {p: max(br[(p, c)] for c in ch) for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7")}
    d = [r["delta"] for r in p9]
    for r in p9:
        for p, v in r["policies"].items():
            if v["risk_causal"] > r["alpha"] + 1e-9: cnt[p] += 1
    # P1,P2,P6 only
    by = collections.defaultdict(dict)
    for r in p7:
        if "policy" in r: by[r["setting_id"]][r["policy"].split("_")[0]] = r["cost"]
    d3 = [min(v["P1"], v["P2"], v["P6"]) - v["P7"] for v in by.values()]
    out = dict(label=label, chains=len(ch), settings=len(p9), p7settings=len(by),
               cheaper=sum(x > 1e-9 for x in d), tie=sum(abs(x) <= 1e-9 for x in d), dearer=sum(x < -1e-9 for x in d),
               min_delta=min(d), cheaper3=sum(x > 1e-9 for x in d3), tie3=sum(abs(x) <= 1e-9 for x in d3), dearer3=sum(x < -1e-9 for x in d3),
               min_delta3=min(d3), iid_break_datasets=len(iidb), max_ratio=mx, violations=dict(cnt),
               violating_chains_p7_p1_p2_p6=[c for c in ch if any(br[(p, c)] > 1 + 1e-9 for p in ("P1", "P2", "P6", "P7"))])
    print(json.dumps(out, indent=1))
    return out
if "--phase10c" in sys.argv:
    P7c = rd("phase10c_baselines/settings.jsonl"); P9c = rd("phase10c_baselines_panel9.jsonl")
    a = tally(P7 + P7n, P9 + P9n, "old 39"); b = tally(P7 + P7n + P7c, P9 + P9n + P9c, "new 44"); c = tally(P7c, P9c, "5 new only")
    json.dump(dict(old=a, new=b, added=c), open(R + "phase10c_baselines/tally.json", "w"), indent=1)
    sys.exit()
a = tally(P7, P9, "old 35"); b = tally(P7 + P7n, P9 + P9n, "new 39"); c = tally(P7n, P9n, "4 new only")
print("iid-break among the 4:", [x for x in NEWIDS if any(r["chain_id"] == x and "policy" in r and r["policy"][:2] in ("P3", "P4", "P5") and r["ratio_causal_over_alpha"] > 1 + 1e-9 for r in P7n)])
json.dump(dict(old=a, new=b, added=c), open(R + "phase10_baselines/tally.json", "w"), indent=1)
