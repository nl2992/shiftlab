"""wpG: the T -> infinity slope problem (Proposition L of GENERAL_B_PREMIUM.md) at t = 1, d = 1, c = k = 0.
S_X(alpha) = max_f sum_y P_A(y) m(|D(y)|) f(y), f in [0,1]^{2^B}, s.t. Risk_X(f) <= alpha;
IID risk 2^-B sum f (fractional knapsack, exact sort); causal risk via R(h) = max(R(h0), (R(h0)+R(h1))/2) (LP).
rho_inf(B, alpha) = 1 - S_c / S_I.  Float LP (HiGHS).
usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/wpG_static.py OUT.json BMAX"""
import hashlib, json, sys, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

def weights(B, e):
    y = np.arange(2 ** B)
    bits = (y[:, None] >> np.arange(B - 1, -1, -1)) & 1  # bit j = label j+1 (first label most significant)
    par = (np.arange(B) % 2 == 1)  # label index i = j+1 even  <=> j odd
    X = np.where(par, 1 - bits, bits)
    a = X.sum(1); n0 = B - a
    pa = 0.5 * ((1 - e) ** a * e ** n0 + e ** a * (1 - e) ** n0)
    D = a - n0
    L = np.log((1 - e) / e)
    m = (1 - 2 * e) * np.tanh(np.abs(D) * L / 2)
    return pa * m

def s_iid(w, alpha, B):
    cap = alpha * 2 ** B
    ws = np.sort(w)[::-1]
    full = int(np.floor(cap))
    return ws[:full].sum() + (cap - full) * (ws[full] if full < len(ws) else 0.0)

def s_causal(w, alpha, B):
    nleaf = 2 ** B
    # variables: f (nleaf), R for internal nodes level l = 0..B-1 (2^l each); leaves' R = f
    off = {}; n = nleaf
    for l in range(B):
        off[l] = n; n += 2 ** l
    def rid(l, i):
        return i if l == B else off[l] + i
    rows, cols, vals, b = [], [], [], []
    r = 0
    for l in range(B):
        for i in range(2 ** l):
            me, c0, c1 = rid(l, i), rid(l + 1, 2 * i), rid(l + 1, 2 * i + 1)
            rows += [r, r]; cols += [c0, me]; vals += [1, -1]; b.append(0); r += 1
            rows += [r, r, r]; cols += [c0, c1, me]; vals += [.5, .5, -1]; b.append(0); r += 1
    rows.append(r); cols.append(off[0]); vals.append(1); b.append(alpha); r += 1
    A = sp.csr_matrix((vals, (rows, cols)), shape=(r, n))
    c = np.zeros(n); c[:nleaf] = -w
    bounds = [(0, 1)] * nleaf + [(0, None)] * (n - nleaf)
    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")
    assert res.success, res.message
    return -res.fun

def main():
    out = Path(sys.argv[1])
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    bmax = int(sys.argv[2]); t0 = time.time(); rows = []
    for e in (0.02, 0.1, 0.2):
        for B in range(1, bmax + 1):
            w = weights(B, e)
            for k in range(1, 11):
                a = 2.0 ** -k
                si, sc = s_iid(w, a, B), s_causal(w, a, B)
                rows.append(dict(e=e, B=B, alpha=a, S_IID=si, S_causal=sc, rho_inf=1 - sc / si))
            for a in (0.05, 0.1, 0.25):
                si, sc = s_iid(w, a, B), s_causal(w, a, B)
                rows.append(dict(e=e, B=B, alpha=a, S_IID=si, S_causal=sc, rho_inf=1 - sc / si))
            print(e, B, round(time.time() - t0, 1), flush=True)
    out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                   elapsed_s=time.time() - t0, rows=rows), indent=1))
    print("wrote", out)

if __name__ == "__main__":
    main()
