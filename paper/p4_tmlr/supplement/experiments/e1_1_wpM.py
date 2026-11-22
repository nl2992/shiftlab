"""E1.1: RB-DP vs certified wpM_scaling cells (d=1, ok). Writes JSONL incrementally then a summary JSON."""
import json, os, sys, time
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

N_BETA, WSD = 201, 10
COMPACT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_scaling_v1_compact.json")
JSONL = os.path.join(RES, "e1_1_wpM.jsonl")
OUT = os.path.join(RES, "e1_1_wpM.json")
WALL = float(os.environ.get("E11_WALL_S", 1100))
E0, E1 = "1/10", "9/10"

def cellkey(c): return (c["T"], c["B"], c["t01"], c["k"], c["alpha"])

def main():
    cells = json.load(open(COMPACT))["cells"]
    ok = sorted([c for c in cells if c["status"] == "ok" and c["d"] == 1],
                key=lambda c: (c["T"], c["B"], F(c["t01"]), F(c["k"]), F(c["alpha"])))
    big = [c for c in ok if c["T"] >= 12]
    small = [c for c in ok if c["T"] < 12]
    stride = len(small) / 90
    sel = [small[int(i * stride)] for i in range(90)] + big
    # run cheap cells first so partial results are broad
    sel.sort(key=lambda c: (F(c["alpha"]) == F(1, 20)) * 1000 + c["T"] * c["B"])
    done = set()
    if os.path.exists(JSONL):
        for l in open(JSONL): done.add(tuple(json.loads(l)["key"]))
    t_start = time.time()
    with open(JSONL, "a") as fh:
        for c in sel:
            if cellkey(c) in done: continue
            if time.time() - t_start > WALL: break
            cell = dict(T=c["T"], B=c["B"], t01=c["t01"], t10=c["t01"], e0=E0, e1=E1, prior="1/2",
                        c="0", k=c["k"], alpha=c["alpha"])
            rec = {"key": list(cellkey(c)), "cell": cell}
            for m in ("causal", "iid"):
                r = rb(cell, m, N_BETA, WSD)
                rec[m] = {k: r[k] for k in ("L", "U", "risk_causal", "risk_iid", "C0", "wall_s")}
            C0 = rec["causal"]["C0"]
            rec["C0_cert"] = c["C0"]
            Gam = rec["causal"]["U"] - rec["iid"]["U"]
            VOI = C0 - rec["iid"]["U"]
            glo, ghi = c["Gamma_f"]; vlo, vhi = c["VOI_interval_f"]
            rec.update(Gamma_rbdp=Gam, VOI_rbdp=VOI, rho_rbdp=(Gam / VOI if VOI > 1e-9 else None),
                       Gamma_cert=[glo, ghi], VOI_cert=[vlo, vhi], rho_cert_mid=c["rho_mid"],
                       dev_Gamma_interval=max(glo - Gam, Gam - ghi, 0.0),
                       dev_Gamma_mid=abs(Gam - c["Gamma_mid_f"]),
                       dev_VOI_interval=max(vlo - VOI, VOI - vhi, 0.0),
                       dev_VOI_mid=abs(VOI - c["VOI_mid_f"]),
                       dev_rho=(abs(rec_rho - c["rho_mid"]) if (rec_rho := (Gam / VOI if VOI > 1e-9 else None)) is not None and c["rho_mid"] is not None else None),
                       dev_C0=abs(C0 - c["C0"]), cert_runtime_s=c["runtime_s"])
            fh.write(json.dumps(rec) + "\n"); fh.flush()
    recs = [json.loads(l) for l in open(JSONL)]
    json.dump(dict(meta(__file__), grid=dict(n_beta=N_BETA, w_step_div=WSD), seed=None,
                   selection="90 evenly strided over sorted ok d=1 cells with T<12, plus all T>=12", wall_budget_s=WALL,
                   n_cells=len(recs), cells=recs), open(OUT, "w"), indent=1)

main()
