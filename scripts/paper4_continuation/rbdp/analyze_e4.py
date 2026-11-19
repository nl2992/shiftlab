"""Print E4 table from JSONL."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RES
rs = [json.loads(l) for l in open(os.path.join(RES, "e4_baselines.jsonl"))]
print("T chain B c/k | C0 | VOI_a | frac_c | frac_e(best) | VOI_b  viol | e_status | ref VOI_exact(causal) iid")
for r in rs:
    T, n, B, c, k = r["key"]; C0 = r["C0"]
    va = C0 - r["a_causal"]["cost"]
    f = lambda cost: ((C0 - cost) / va if va > 1e-9 else float("nan"))
    es = ",".join(f"{t}:{v['status'][:2]}" for t, v in r["e_eproc"].items())
    ref = r.get("ref_exact")
    rv = ""
    if ref and ref["status"] == "ok":
        from fractions import Fraction as F
        rv = "%.5f..%.5f" % (C0 - float(F(ref["U_causal"])), C0 - float(F(ref["L_causal"])))
    print(f"{T} {n} B{B} {c}/{k} | {C0:.4f} | {va:.5f} | {f(r['c_repair']['cost']):.3f} | {f(r['e_best_cost']):.3f} | {C0-r['b_iid']['cost']:.5f} {r['b_iid']['violation']:.2f}x | {es} | {rv}")
