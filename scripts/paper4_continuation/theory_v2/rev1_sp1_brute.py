"""Reviewer 1: exact (Fraction) checks of SP1 and its corollaries against N1-by-brute-DP (no LP), larger T.

usage: rev1_sp1_brute.py OUT.json
Checks, all exact:
 F   sp1_formula == n1_brute_sym (tests Lemmas S, Pre, W, K and the assembly, given N1)
 GEO primitive geometric forms of G0, G1 and the alternating identity == Lemma-W sums
 A   even d => Gamma = 0;  B lower bound (and equality when T >= d+2, g r^{d+1} <= 2k)
 C   SP1-C bound when 2c+k < g r^d (1-r);  D r = 1 bullets;  E k = 0 formula
 S3  T-saturation for T >= max(J,d+1)+1 (k>0, r<1); k=0 delay factor interval; monotone in d (odd d -> d+2)
 MOD continuity modulus |dGamma| <= 8 alpha (T(1+k)+c) TVB on asymmetric perturbations (N1-brute both sides)
"""

from __future__ import annotations

import random
import sys
from fractions import Fraction as F

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import save_refuse_overwrite  # noqa: E402
from rev1_sp1_lib import n1_brute, n1_brute_sym, sp1_formula, sp1_lower_bound  # noqa: E402

TS = [F(1), F(99, 100), F(9, 10), F(3, 4), F(3, 5), F(51, 100)]
ES = [F(1, 1000), F(1, 10), F(1, 4), F(49, 100)]
AL = [F(1, 20), F(1, 4), F(1, 2)]


def geo(T, d, t, e, c, k):
    """Primitive closed forms of SP1 (d odd, T >= d+2)."""
    r = 2 * t - 1
    g = (1 - 2 * e) ** 2
    a = lambda j: g * r**j  # noqa: E731
    # J = max{j : a_j > 2k}
    if k == 0 or (r == 1 and g > 2 * k):
        J = 10**9
    else:
        J = -1
        j = 0
        while a(j) > 2 * k and j < 10**4:
            J = j
            j += 1
    Ms = min(T - 1, J)
    n0 = len([j for j in range(d, Ms + 1) if (j - d) % 2 == 0])
    n1 = len([j for j in range(d + 1, Ms + 1) if (j - d) % 2 == 1])
    S = lambda n: (F(n) if r == 1 else (1 - r ** (2 * n)) / (1 - r**2))  # noqa: E731
    G0 = k + g * r**d * S(n0) - 2 * k * n0 if n0 >= 1 else g * r**d - k
    G1 = k + g * r ** (d + 1) * S(n1) - 2 * k * n1 if n1 >= 1 else g * r ** (d + 1) - k
    Mp = max(Ms, d + 1)
    n = Mp - d + 1
    rho = -r
    diff = g * r**d * (1 - rho**n) / (1 - rho) - 2 * k * (n % 2)
    return G0, G1, diff


def main():
    out = sys.argv[1]
    rng = random.Random(11)
    cnt = {}
    bad = {}

    def rec(key, ok, info):
        cnt.setdefault(key, [0, 0])
        cnt[key][0] += 1
        if not ok:
            cnt[key][1] += 1
            bad.setdefault(key, [])
            if len(bad[key]) < 6:
                bad[key].append(info)

    for _ in range(3000):
        t, e, al = rng.choice(TS), rng.choice(ES), rng.choice(AL)
        d = rng.choice([1, 2, 3, 4, 5])
        T = rng.randint(d + 1, min(d + 9, 13))
        r = 2 * t - 1
        g = (1 - 2 * e) ** 2
        ks = [F(0), g * r**d / 2, g * r ** (d + 1) / 2, g * r ** (d + 2) / 2, g * r**d, F(1, 50), F(1, 10)]
        k = rng.choice(ks) * rng.choice([1, 1, F(999, 1000), F(1001, 1000)])
        ad = g * r**d
        cs = [F(0), F(1, 100), max(F(0), (ad - k) / 2), sp1_lower_bound(d, t, e, 0, k)]
        c = rng.choice(cs) * rng.choice([1, F(999, 1000)])
        info = dict(T=T, d=d, t=str(t), e=str(e), c=str(c), k=str(k), alpha=str(al))
        f = sp1_formula(T, d, t, e, c, k, al)
        b = n1_brute_sym(T, d, t, e, c, k, al)
        info.update(sp1=str(f), brute=str(b))
        rec("F_formula_eq_brute", f == b, info)
        if d % 2 == 0:
            rec("A_even_d_zero", b == 0, info)
            continue
        L = sp1_lower_bound(d, t, e, c, k)
        rec("B_lower_bound", b >= al * L, dict(info, L=str(al * L)))
        if T >= d + 2 and g * r ** (d + 1) <= 2 * k:
            rec("B_equality", b == al * L, dict(info, L=str(al * L)))
        if 0 < r < 1 and 2 * c + k < g * r**d * (1 - r):
            bc = (al / 2) * (g * r**d - 2 * c - max(k, g * r ** (d + 1) - k))
            rec("C_bound", b >= bc > 0, dict(info, bound=str(bc)))
        if T >= d + 2:
            G0, G1, diff = geo(T, d, t, e, c, k)
            # Lemma-W sums (from the formula module's definition) recomputed here
            P0 = [j for j in range(d, T) if (j - d) % 2 == 0]
            P1 = [j for j in range(d, T) if (j - d) % 2 == 1]
            a = lambda j: g * r**j  # noqa: E731
            W = lambda P: (k + sum(max(F(0), a(j) - 2 * k) for j in P)) if a(P[0]) > 2 * k else a(P[0]) - k  # noqa: E731
            rec("GEO_G0", G0 == W(P0), dict(info, geo=str(G0), W=str(W(P0))))
            rec("GEO_G1", G1 == W(P1), dict(info, geo=str(G1), W=str(W(P1))))
            rec("GEO_diff_identity", diff == W(P0) - W(P1), dict(info, geo=str(diff), W=str(W(P0) - W(P1))))
        if r == 1:
            if T == d + 1:
                rec("D_bullet3_T=d+1", b == al * max(F(0), (g - k) / 2 - c), info)
            bullet1 = (T - d) % 2 == 0 or g <= 2 * k
            if bullet1:
                rec("D_bullet1_zero", b == 0, info)
            elif T >= d + 2:
                G0 = k + F(T - d + 1, 2) * (g - 2 * k)
                rec("D_bullet2", b == al * max(F(0), min(G0 / 2 - c, g - 2 * k, (g - k) / 2 - c)), info)
        if k == 0:
            v = al * max(F(0), g * r**d * (1 - (-r) ** (T - d)) / (2 * (1 + r)) - c)
            rec("E_k0", b == v, info)
            if c == 0 and 0 < r:
                fac = b / al / (g * r**d)
                rec("S3_delay_factor_in_[1/(2(1+r)),1/2]", F(1) / (2 * (1 + r)) <= fac <= F(1, 2),
                    dict(info, factor=str(fac), lo=str(F(1) / (2 * (1 + r)))))
        if T >= d + 3:
            b2 = n1_brute_sym(T, d + 2, t, e, c, k, al)
            rec("S3_monotone_d_to_d+2" + ("_k0" if k == 0 else "_kpos"), b2 <= b, dict(info, d2=str(b2)))
        if k > 0 and 0 < r < 1:
            J = -1
            j = 0
            while g * r**j > 2 * k:
                J = j
                j += 1
            T0 = max(J, d + 1) + 1
            if T0 <= 13 and T >= T0 and T + 2 <= 15:
                rec("S3_T_saturation", n1_brute_sym(T + 2, d, t, e, c, k, al) == b
                    and n1_brute_sym(T + 1, d, t, e, c, k, al) == b, info)

    # continuity modulus on asymmetric perturbations (N1 any HMM, alpha <= 1/2)
    for _ in range(400):
        t, e, al = rng.choice(TS[1:]), rng.choice([F(1, 10), F(1, 4)]), rng.choice(AL)
        d = rng.choice([1, 2, 3])
        T = rng.randint(d + 1, d + 4)
        c, k = rng.choice([F(0), F(1, 100)]), rng.choice([F(0), F(1, 50), F(1, 10)])
        h = rng.choice([F(1, 1000), F(1, 100), F(1, 20)])
        dt01, dt10 = h * rng.choice([-1, 0, 1]), h * rng.choice([-1, 0, 1])
        de0, de1, dp = h * rng.choice([-1, 0, 1]), h * rng.choice([-1, 0, 1]), h * rng.choice([-1, 0, 1])
        t01, t10 = min(F(1), t + dt01), min(F(1), t + dt10)
        e0, e1, pr = e + de0, 1 - e + de1, F(1, 2) + dp
        g1 = n1_brute(T, d, t, t, e, 1 - e, F(1, 2), c, k, al)
        g2 = n1_brute(T, d, t01, t10, e0, e1, pr, c, k, al)
        # p_1 = P(S_1=1) after one propagation
        p1a = F(1, 2)
        p1b = pr * (1 - t10) + (1 - pr) * t01
        tvb = abs(p1a - p1b) + (T - 1) * max(abs(t01 - t), abs(t10 - t)) + T * max(abs(e0 - e), abs(e1 - 1 + e))
        bound = 8 * al * (T * (1 + k) + c) * tvb
        rec("MOD_continuity", abs(g1 - g2) <= bound,
            dict(T=T, d=d, t=str(t), e=str(e), c=str(c), k=str(k), alpha=str(al), dG=str(abs(g1 - g2)),
                 bound=str(bound)))

    payload = dict(script="rev1_sp1_brute.py", seed=11, counts={k_: dict(n=v[0], fail=v[1]) for k_, v in cnt.items()},
                   failures=bad)
    save_refuse_overwrite(out, payload)
    for k_, v in cnt.items():
        print(f"{k_:45s} n={v[0]:5d} fail={v[1]}")


if __name__ == "__main__":
    main()
