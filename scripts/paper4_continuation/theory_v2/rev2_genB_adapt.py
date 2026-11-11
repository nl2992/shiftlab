"""rev2: ADAPT check against EVERY fixed pre-promotion calendar (not only 1..B).

Calendar class for a set tau of <= B query times in 1..T-1 (d = 1, c = k = 0, t = 1): pre-promotion queries
exactly at tau, action 0; first promotion = randomised stopping time on released labels; after promotion the
learner queries its remaining budget at every step (optimal at t = 1 by Blackwell monotonicity) and plays
(w_t)^+.  Causal constraint: T1 recursion (linearised).  Float LP (HiGHS); compared with the exact certified
gamma_cell V*_causal.  Also reproduces the wpG_lib calendar-1..B value as a cross-check.

usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/rev2_genB_adapt.py OUT.json
"""
import hashlib, json, math, sys, time
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "theory_C"))
from gamma_lib import gamma_cell  # noqa: E402
from wpG_lib import gamma as wpG_gamma  # noqa: E402


def wpos(t, D, e):
    sgn = 1 if t % 2 else -1
    lam = (1 - e) / e
    return max(0.0, sgn * (1 - 2 * e) * math.tanh(D * math.log(lam) / 2))


def w(t, D, e):
    sgn = 1 if t % 2 else -1
    return sgn * (1 - 2 * e) * math.tanh(D * math.log((1 - e) / e) / 2)


def cont_gain(s, D, l, B, T, e):
    """w_s(D) + sum_{t>s} E[(w_t)^+ | D] with labels released ASAP after s (remaining budget B - l)."""
    lam = (1 - e) / e
    p1 = lam ** D / (1 + lam ** D)
    tot = w(s, D, e)
    for t in range(s + 1, T + 1):
        k = min(t - s, B - l)
        acc = 0.0
        for a in range(k + 1):
            pr = p1 * math.comb(k, a) * (1 - e) ** a * e ** (k - a) + (1 - p1) * math.comb(k, a) * e ** a * (1 - e) ** (k - a)
            acc += pr * wpos(t, D + 2 * a - k, e)
        tot += acc
    return tot


def cal_lp(T, B, tau, e, alpha, causal):
    tau = sorted(tau)
    lens = [sum(1 for tj in tau if tj <= s - 1) for s in range(1, T + 1)]
    off, n = [], 0
    for s in range(T):
        off.append(n); n += 2 ** lens[s]
    obj = np.zeros(2 * n + (n if causal else 0))
    for s in range(T):
        l = lens[s]
        for i in range(2 ** l):
            y = [(i >> (l - 1 - j)) & 1 for j in range(l)]
            x = [yj if tau[j] % 2 == 1 else 1 - yj for j, yj in enumerate(y)]
            a = sum(x)
            pa = ((1 - e) ** a * e ** (l - a) + e ** a * (1 - e) ** (l - a)) / 2
            obj[off[s] + i] = -pa * cont_gain(s + 1, 2 * a - l, l, B, T, e)
    R, C, V, beq = [], [], [], []
    r = 0
    for s in range(T):
        for i in range(2 ** lens[s]):
            R += [r, r]; C += [off[s] + i, n + off[s] + i]; V += [1.0, 1.0]
            if s == 0:
                beq.append(1.0)
            else:
                par = i // 2 if lens[s] > lens[s - 1] else i
                R.append(r); C.append(n + off[s - 1] + par); V.append(-1.0); beq.append(0.0)
            r += 1
    Aeq = sp.csr_matrix((V, (R, C)), shape=(r, len(obj)))
    ur, uc, uv, b = [], [], [], []
    k = 0
    if not causal:
        for s in range(T):
            for i in range(2 ** lens[s]):
                ur.append(0); uc.append(off[s] + i); uv.append(2.0 ** -lens[s])
        b.append(alpha); k = 1
    else:
        Rb = 2 * n
        ur.append(0); uc.append(Rb); uv.append(1.0); b.append(alpha); k = 1
        for s in range(T):
            for i in range(2 ** lens[s]):
                me, xi = Rb + off[s] + i, off[s] + i
                if s == T - 1:
                    ur += [k, k]; uc += [xi, me]; uv += [1.0, -1.0]; b.append(0.0); k += 1
                elif lens[s + 1] == lens[s]:
                    ch = Rb + off[s + 1] + i
                    ur += [k] * 3; uc += [xi, ch, me]; uv += [1.0, 1.0, -1.0]; b.append(0.0); k += 1
                else:
                    c0 = Rb + off[s + 1] + 2 * i
                    ur += [k] * 3; uc += [xi, c0, me]; uv += [1.0, 1.0, -1.0]; b.append(0.0); k += 1
                    ur += [k] * 4; uc += [xi, c0, c0 + 1, me]; uv += [1.0, .5, .5, -1.0]; b.append(0.0); k += 1
    Aub = sp.csr_matrix((uv, (ur, uc)), shape=(k, len(obj)))
    res = linprog(obj, A_ub=Aub, b_ub=b, A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * len(obj), method="highs",
                  options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
    assert res.success, res.message
    return T / 2 + res.fun


out = Path(sys.argv[1])
if out.exists():
    sys.exit(f"refusing to overwrite {out}")
cells = [(6, 2, F(1, 10), F(1, 20)), (8, 2, F(1, 10), F(1, 20)), (10, 2, F(1, 10), F(1, 20)),
         (8, 2, F(1, 4), F(1, 10)), (8, 2, F(1, 20), F(1, 4)), (9, 3, F(1, 10), F(1, 20)), (10, 3, F(1, 10), F(1, 20))]
rows, t0 = [], time.time()
for T, B, e, a in cells:
    g = gamma_cell(T, B, 1, 1, 1, e, 1 - e, F(1, 2), 0, 0, a)
    ef, af = float(e), float(a)
    wp = wpG_gamma(T, B, 1.0, ef, af)
    base_c = cal_lp(T, B, list(range(1, B + 1)), ef, af, True)
    base_i = cal_lp(T, B, list(range(1, B + 1)), ef, af, False)
    best, best_tau = None, None
    n_cal = 0
    for size in range(0, B + 1):
        for tau in combinations(range(1, T), size):
            v = cal_lp(T, B, list(tau), ef, af, True) if size else T / 2
            n_cal += 1
            if best is None or v < best - 1e-12:
                best, best_tau = v, tau
    U_c, L_c = float(F(g["U_causal"])), float(F(g["L_causal"]))
    row = dict(T=T, B=B, e=str(e), alpha=str(a), exact_V_causal=[L_c, U_c], exact_V_IID=float(F(g["U_IID"])),
               wpG_cal_V_causal=wp["V_causal"], wpG_cal_V_IID=wp["V_IID"], my_cal1B_V_causal=base_c,
               my_cal1B_V_IID=base_i, n_calendars=n_cal, best_calendar=best_tau, best_cal_V_causal=best,
               exact_strictly_beats_every_calendar=bool(best > U_c + 1e-9),
               gap_best_cal_minus_exact=best - U_c)
    rows.append(row)
    print(row, flush=True)
out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               elapsed_s=time.time() - t0, rows=rows), indent=1, default=str))
print("wrote", out)
