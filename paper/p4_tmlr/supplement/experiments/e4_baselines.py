"""E4: baselines vs RB-DP causal policy (d=1)."""
import json, os, sys, time
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

N_BETA, WSD = 201, 10
JSONL = os.path.join(RES, "e4_baselines.jsonl"); OUT = os.path.join(RES, "e4_baselines.json")
CHAINS = {"anti2/3": ("2/3", "2/3"), "anti3/4": ("3/4", "3/4"), "anti9/10": ("9/10", "9/10"),
          "pers1/10": ("1/10", "1/10"), "pers1/4": ("1/4", "1/4"), "asym(1/4,3/4)": ("1/4", "3/4"),
          "asym(9/10,2/3)": ("9/10", "2/3")}  # added after first run: (1/4,3/4) has exactly zero VOI

def cells():
    out = []
    for name, (a, b) in CHAINS.items():
        for B in (2, 3):
            out.append((name, dict(B=B, t01=a, t10=b, c="0", k="0")))
    for name in ("anti3/4", "pers1/4", "asym(1/4,3/4)"):
        a, b = CHAINS[name]
        for B in (2, 3):
            out.append((name, dict(B=B, t01=a, t10=b, c="1/100", k="1/20")))
    return out

def main():
    alpha = F(1, 10)
    done = set()
    if os.path.exists(JSONL):
        done = {tuple(json.loads(l)["key"]) for l in open(JSONL)}
    with open(JSONL, "a") as fh:
        for T in (8, 32):
            for name, p in cells():
                key = (T, name, p["B"], p["c"], p["k"])
                if key in done: continue
                cell = dict(T=T, e0="1/10", e1="9/10", prior="1/2", alpha="1/10", **p)
                rec = {"key": list(key), "cell": cell}
                a = rb(cell, "causal", N_BETA, WSD); b = rb(cell, "iid", N_BETA, WSD)
                C0 = a["C0"]
                rec["C0"] = C0
                rec["a_causal"] = dict(cost=a["U"], L=a["L"], risk=a["risk_causal"], wall_s=a["wall_s"])
                rec["b_iid"] = dict(cost=b["U"], L=b["L"], risk_causal=b["risk_causal"], risk_iid=b["risk_iid"],
                                    violation=b["risk_causal"] / float(alpha), wall_s=b["wall_s"])
                act = min(1.0, float(alpha) / b["risk_causal"]) if b["risk_causal"] > 0 else 1.0
                rec["c_repair"] = dict(activation=act, cost=act * b["U"] + (1 - act) * C0, risk=act * b["risk_causal"])
                rec["d_never"] = dict(cost=C0)
                eps = {}
                for th in (2, 4, 8):
                    if th > 2 ** p["B"]: continue
                    r = eproc(cell, th, 120)
                    if r["status"] == "ok":
                        # Ville: gate false-promotion prob <= 1/th for the causal null (stake 1 => supermartingale).
                        act_e = min(1.0, float(alpha) * th)
                        r.update(activation=act_e, risk_bound=act_e / th, cost_repaired=act_e * r["cost"] + (1 - act_e) * C0)
                    eps[str(th)] = r
                rec["e_eproc"] = eps
                good = [v["cost_repaired"] for v in eps.values() if v["status"] == "ok"]
                rec["e_best_cost"] = min(good + [C0])
                if T == 8:
                    r = ref(cell, 120); rec["ref_exact"] = r
                fh.write(json.dumps(rec) + "\n"); fh.flush()
    recs = [json.loads(l) for l in open(JSONL)]
    json.dump(dict(meta(__file__), grid=dict(n_beta=N_BETA, w_step_div=WSD), seed=None, n_cells=len(recs), cells=recs),
              open(OUT, "w"), indent=1)

main()
