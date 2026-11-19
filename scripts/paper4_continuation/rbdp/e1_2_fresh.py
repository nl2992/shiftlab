"""E1.2: fresh seeded random grid vs fresh gamma_cell calls."""
import json, os, random, sys, time
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SEED, N, N_BETA, WSD = 20261113, 40, 201, 10
JSONL = os.path.join(RES, "e1_2_fresh.jsonl"); OUT = os.path.join(RES, "e1_2_fresh.json")

def rfrac(rng, lo, hi, dens):
    while True:
        d = rng.choice(dens); n = rng.randint(1, d - 1)
        if lo < F(n, d) < hi: return F(n, d)

def main():
    rng = random.Random(SEED); cells = []
    for _ in range(N):
        T = rng.randint(4, 8); B = rng.randint(1, min(3, T))
        cells.append(dict(T=T, B=B, t01=str(rfrac(rng, F(5, 100), F(95, 100), [4, 5, 6, 8, 10, 12])),
                          t10=str(rfrac(rng, F(5, 100), F(95, 100), [4, 5, 6, 8, 10, 12])),
                          e0=str(rfrac(rng, F(5, 100), F(45, 100), [10, 20])), e1=str(rfrac(rng, F(55, 100), F(95, 100), [10, 20])),
                          prior=str(rng.choice([F(0), F(1, 3), F(1, 2)])), c=str(rng.choice([F(0), F(1, 100)])),
                          k=str(rng.choice([F(0), F(1, 20), F(1, 10)])), alpha=str(rng.choice([F(1, 20), F(1, 10), F(1, 5)]))))
    done = set()
    if os.path.exists(JSONL):
        done = {json.dumps(json.loads(l)["cell"], sort_keys=True) for l in open(JSONL)}
    with open(JSONL, "a") as fh:
        for cell in cells:
            if json.dumps(cell, sort_keys=True) in done: continue
            rec = {"cell": cell}
            for m in ("causal", "iid"):
                r = rb(cell, m, N_BETA, WSD)
                rec[m] = {k: r[k] for k in ("L", "U", "risk_causal", "risk_iid", "C0", "wall_s")}
            rec["ref"] = ref(cell, 120)
            fh.write(json.dumps(rec) + "\n"); fh.flush()
    recs = [json.loads(l) for l in open(JSONL)]
    json.dump(dict(meta(__file__), grid=dict(n_beta=N_BETA, w_step_div=WSD), seed=SEED, n_cells=len(recs), cells=recs),
              open(OUT, "w"), indent=1)

main()
