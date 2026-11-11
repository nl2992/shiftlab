"""rev3 recheck: recompute the pure-plan ratio zeta_best with the corrected (tag-consistent) combiner
best_ratio_pure_v2 against the stored certified intervals of rev3_mix_b{1,2}_v1.json.  No gamma_cell calls.
Usage: python rev3_mix_recheck.py IN.json OUT.json"""
import json, os, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rev3_mix_lib import Chain, best_ratio_pure_v2, slopes

inp, out = sys.argv[1], sys.argv[2]
if os.path.exists(out):
    sys.exit(f"refusing to overwrite {out}")
d = json.load(open(inp))
rows, summ = [], {"M3iii_Gamma_ge_v2": [0, 0], "eval_consistency_IID_ge_zeta_v2": [0, 0], "S_I_equals_VOI_IID_c0": [0, 0]}
for rec in d["cells"]:
    cc = rec["cell"]
    if cc["k"] != "0":
        continue
    T, B, dd, t, e, c, al = cc["T"], cc["B"], cc["d"], F(cc["t"]), F(cc["e"]), F(cc["c"]), F(cc["alpha"])
    ch = Chain(t, e)
    zb = best_ratio_pure_v2(ch, T, B, dd, c, al)
    s = slopes(ch, T, B, dd, c)
    glo, ghi = [F(x) for x in rec["Gamma"]]
    vlo, vhi = [F(x) for x in rec["VOI_IID"]]
    a = al * (zb - s["S_prime"]) <= ghi
    b = al * zb <= vhi
    summ["M3iii_Gamma_ge_v2"][0] += a; summ["M3iii_Gamma_ge_v2"][1] += 1
    summ["eval_consistency_IID_ge_zeta_v2"][0] += b; summ["eval_consistency_IID_ge_zeta_v2"][1] += 1
    if c == 0 and al <= F(1, 2):
        eq = vlo <= al * s["S_I"] <= vhi
        summ["S_I_equals_VOI_IID_c0"][0] += eq; summ["S_I_equals_VOI_IID_c0"][1] += 1
    rows.append({"cell": cc, "zeta_best_v2": str(zb), "zeta_best_v2_f": float(zb), "M3iii_v2": a, "consistency_v2": b,
                 "VOI_IID_over_alpha": [float(vlo / al), float(vhi / al)]})
with open(out, "w") as fh:
    json.dump({"source": inp, "summary_pass_total": summ, "rows": rows}, fh, indent=1)
print(summ)
