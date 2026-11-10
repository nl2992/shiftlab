"""WP B: tabulate the multi-label W condition (CAUSAL_SAFETY_PREMIUM_THEORY.md F3) on a cell with d = 1.

Info states h = labels at any set S of earlier query times (|S| <= B-1, all released by tau since
d = 1), any binary values, next query at any tau <= T - d.  For y in {0,1}, G_y(h, s) = open-loop gain (no further labels) of promoting at
s >= tau + d after Y_tau = y versus never promoting, with switch cost k on every action change.
W(h, tau) holds iff P(Y_tau=1|h) G_1(s) >= P(Y_tau=0|h) G_0(s) for every s with G_0(s) > 0.
Reports every failure.
usage: wpB_multiW.py OUT.json 'cell tuple (T,B,d,t01,t10,e0,e1,prior,c,k)'
"""

from __future__ import annotations

import sys
from itertools import product

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
from gamma_lib import save_refuse_overwrite  # noqa: E402


def main():
    out, cell = sys.argv[1], eval(sys.argv[2])
    T, B, d, t01, t10, e0, e1, prior, c, k = [float(x) for x in cell]
    T, B, d = int(T), int(B), int(d)
    P = [[1 - t01, t01], [t10, 1 - t10]]
    p1 = prior * (1 - t10) + (1 - prior) * t01
    em = [e0, e1]

    def joint(labels, upto=None):
        """Unnormalised law of S_{upto+1} given labels {time: y} observed at times <= upto."""
        if not isinstance(labels, dict):
            labels = {i + 1: y for i, y in enumerate(labels)}
        if upto is None:
            upto = max(labels) if labels else 0
        a = [1 - p1, p1]
        for t in range(1, upto + 1):
            if t in labels:
                y = labels[t]
                a = [a[s_] * (em[s_] if y else 1 - em[s_]) for s_ in (0, 1)]
            a = [a[0] * P[0][0] + a[1] * P[1][0], a[0] * P[0][1] + a[1] * P[1][1]]
        return a

    def q_future(labels, tau):
        """q_t = P(Y_t=1 | labels at times <= tau) for t = tau+1..T."""
        a = joint(labels, tau)
        z = sum(a)
        b = [a[0] / z, a[1] / z]
        qs = {}
        for t in range(tau + 1, T + 1):
            qs[t] = b[0] * e0 + b[1] * e1
            b = [b[0] * P[0][0] + b[1] * P[1][0], b[0] * P[0][1] + b[1] * P[1][1]]
        return qs

    def gain(qs, s):
        best = None
        for acts in product((0, 1), repeat=T - s):
            a = (1,) + acts
            g = sum(ai * (2 * qs[s + i] - 1) for i, ai in enumerate(a))
            sw = 1 + sum(a[i] != a[i + 1] for i in range(len(a) - 1))
            g -= k * sw
            best = g if best is None or g > best else best
        return best

    fails, checked, nonvacuous = [], 0, 0
    from itertools import combinations
    for tau in range(1, T - d + 1):
        for r in range(0, min(B - 1, tau - 1) + 1):
            for S in combinations(range(1, tau), r):
                for vals in product((0, 1), repeat=r):
                    h = dict(zip(S, vals))
                    a = joint(h, tau - 1)
                    pY1 = (a[0] * e0 + a[1] * e1) / sum(a)
                    for s in range(tau + d, T + 1):
                        g0 = gain(q_future({**h, tau: 0}, tau), s)
                        g1 = gain(q_future({**h, tau: 1}, tau), s)
                        checked += 1
                        nonvacuous += g0 > 1e-15
                        if g0 > 1e-15 and pY1 * g1 < (1 - pY1) * g0 - 1e-15:
                            fails.append({"h": str(h), "tau": tau, "s": s, "P(Y=1|h)": pY1, "G0": g0, "G1": g1})
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_multiW.py", "cell": [str(x) for x in cell],
               "n_checked": checked, "n_nonvacuous_G0_pos": nonvacuous, "n_fail": len(fails), "fails": fails}
    save_refuse_overwrite(out, payload)
    print({k_: v for k_, v in payload.items() if k_ != "fails"}, fails[:6])


if __name__ == "__main__":
    main()
