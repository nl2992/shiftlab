"""rev2: Lemma A (exhaustive, exact for B <= 12, float to 16), RIPr LR bound, T1 corollaries (a),(b),
and Proposition P on the static calendar slope LP (exact IID side, float HiGHS causal side), incl. the
ceil(B/2) sharpening and the B = 2 closed form.

usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/rev2_genB_lemmas.py OUT.json
"""
import hashlib, json, math, random, sys, time
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rev2_genB_lib import S_iid, calendar_leaves, m_of, tree_risk, w_at  # noqa: E402

out = Path(sys.argv[1])
if out.exists():
    sys.exit(f"refusing to overwrite {out}")
res, t0 = {}, time.time()
ES = [F(1, 50), F(1, 20), F(1, 10), F(1, 4), F(2, 5)]

# ---- Lemma A + RIPr LR ----
la = []
for e in ES:
    for B in range(1, 17):
        exact = B <= 10
        ee = e if exact else float(e)
        maxcnt, maxLR, consec_viol, kl = 0, 0, 0, 0.0
        for y in product((0, 1), repeat=B):
            D, cnt, prev_pos, lr = 0, 0, False, (F(1) if exact else 1.0)
            for i in range(1, B + 1):
                wi = w_at(i, D, ee)  # labels 1..i-1 released at time i (calendar, d = 1)
                q = F(1, 2) + wi / 2 if exact else 0.5 + wi / 2
                pos = wi > 0
                if pos and prev_pos:
                    consec_viol += 1
                cnt += pos
                prev_pos = pos
                p = min(q, F(1, 2) if exact else 0.5)
                yi = y[i - 1]
                lr *= (q / p) if yi else ((1 - q) / (1 - p))
                xi = yi if i % 2 == 1 else 1 - yi
                D += 2 * xi - 1
            maxcnt = max(maxcnt, cnt)
            maxLR = max(maxLR, lr)
        bound = (2 * (1 - ee)) ** (B // 2)
        la.append(dict(e=str(e), B=B, exact=exact, max_count=maxcnt, floor_half=B // 2,
                       consecutive_positive=consec_viol, maxLR=float(maxLR), LR_bound=float(bound),
                       LR_ok=bool(maxLR <= bound * (1 + 1e-12))))
res["lemmaA"] = la
res["lemmaA_all_ok"] = all(r["max_count"] == r["floor_half"] and r["consecutive_positive"] == 0 and r["LR_ok"] for r in la)
print("lemma A ok", res["lemmaA_all_ok"], flush=True)

# ---- T1 corollaries ----
rng = random.Random(7)
t1 = dict(pattern_checked=0, pattern_fail=0, upset_checked=0, upset_fail=0)
for B in range(1, 6):
    for idx in range(2 ** B):
        g = [F(0)] * (2 ** B); g[idx] = F(1)
        ones = bin(idx).count("1")
        t1["pattern_checked"] += 1
        t1["pattern_fail"] += tree_risk(g)[0] != F(1, 2 ** ones)
    for _ in range(300):
        # random nondecreasing f: max of random up-set indicators weighted
        gens = [rng.randrange(2 ** B) for _ in range(rng.randint(1, 3))]
        wts = [F(rng.randint(1, 9), 10) for _ in gens]
        g = [max([wt for gg, wt in zip(gens, wts) if (i & gg) == gg] + [F(0)]) for i in range(2 ** B)]
        c, iid = tree_risk(g)
        t1["upset_checked"] += 1
        t1["upset_fail"] += c != iid
res["T1"] = t1
print("T1", t1, flush=True)


# ---- Prop P: static calendar slope LP ----
def S_causal(B, e, alpha):
    leaves = calendar_leaves(B, e)
    nL = 2 ** B
    wt = np.array([float(lf["PA"] * m_of(sum(2 * x - 1 for x in lf["x"]), e)) for lf in leaves])
    nN = 2 ** (B + 1) - 1  # heap: node k children 2k+1, 2k+2; leaves nN-nL..nN-1 in order
    nv = nL + nN
    R, C, V, b = [], [], [], []
    r = 0
    R.append(r); C.append(nL + 0); V.append(1.0); b.append(float(alpha)); r += 1
    for k in range(nN):
        if k >= nN - nL:
            R += [r, r]; C += [k - (nN - nL), nL + k]; V += [1.0, -1.0]; b.append(0.0); r += 1
        else:
            c0, c1 = 2 * k + 1, 2 * k + 2
            R += [r, r]; C += [nL + c0, nL + k]; V += [1.0, -1.0]; b.append(0.0); r += 1
            R += [r] * 3; C += [nL + c0, nL + c1, nL + k]; V += [.5, .5, -1.0]; b.append(0.0); r += 1
    A = sp.csr_matrix((V, (R, C)), shape=(r, nv))
    obj = np.concatenate([-wt, np.zeros(nN)])
    bounds = [(0, 1)] * nL + [(0, None)] * nN
    s = linprog(obj, A_ub=A, b_ub=b, bounds=bounds, method="highs",
                options={"primal_feasibility_tolerance": 1e-11, "dual_feasibility_tolerance": 1e-11})
    assert s.success
    return -s.fun


pp = []
for e in [F(1, 20), F(1, 10), F(1, 4), F(2, 5)]:
    for B in range(1, 11):
        for k in (0, 1, 2, 4, 7):
            alpha = F(2) ** (1 - B - k)
            SI, _ = S_iid(B, alpha, e)
            Sc = S_causal(B, e, alpha)
            rho = 1 - Sc / float(SI)
            one = float(1 - 2 * e)
            bnd_floor = 1 - 2 / (one * (2 * (1 - float(e))) ** (B // 2))
            bnd_ceil = 1 - 2 / (one * (2 * (1 - float(e))) ** (-(-B // 2)))
            pp.append(dict(e=str(e), B=B, alpha=str(alpha), S_iid=float(SI), S_causal=Sc, rho_inf=rho,
                           bound_floor=bnd_floor, bound_ceil=bnd_ceil, ok_floor=rho >= bnd_floor - 1e-9,
                           ok_ceil=rho >= bnd_ceil - 1e-9))
        for alpha in (F(1, 20), F(1, 10), F(1, 4)):
            if B == 2:
                Sc = S_causal(2, e, alpha)
                pp.append(dict(e=str(e), B=2, alpha=str(alpha), B2_closed=float(F(3, 2) * alpha * (1 - 2 * e) ** 2),
                               S_causal=Sc, B2_ok=abs(Sc - float(F(3, 2) * alpha * (1 - 2 * e) ** 2)) < 1e-9))
res["propP"] = pp
res["propP_floor_viol"] = sum(1 for r in pp if r.get("ok_floor") is False)
res["propP_ceil_viol"] = sum(1 for r in pp if r.get("ok_ceil") is False)
res["propP_n"] = sum(1 for r in pp if "ok_floor" in r)
res["B2_closed_ok"] = all(r["B2_ok"] for r in pp if "B2_ok" in r)
print("propP n", res["propP_n"], "viol floor", res["propP_floor_viol"], "ceil", res["propP_ceil_viol"],
      "B2", res["B2_closed_ok"], flush=True)
res["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
res["elapsed_s"] = time.time() - t0
out.write_text(json.dumps(res, indent=1, default=str))
print("wrote", out)
