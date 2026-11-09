"""Analytic information rates (expected log-growth per event) of the envelope bet.

For a Markov alternative (stationary success pa, persistence rho) sampled at event gap g on a
disagreement process of rate dis, with budget-sustainable spacing T/B, the growth-optimal
envelope e-process for class M(rho_bar) has per-event rate
    R(g) = I(g) / max(g + 1/dis, T/B),
    I(g) = pa KL(q1 || u1) + (1-pa) KL(q0 || 1/2),  q1 = a + (1-a) pa, q0 = (1-a) pa, a = rho^g,
    u1 = 1/2 + rho_bar^g / 2   (the bound is attained by a null member, so I(g) is exact).
Prints max_g R(g), argmax, and log(1/alpha)/R as a first-passage time scale.
"""

import math

import numpy as np


def kl(a, b):
    a = min(max(a, 1e-12), 1 - 1e-12)
    b = min(max(b, 1e-12), 1 - 1e-12)
    return a * math.log(a / b) + (1 - a) * math.log((1 - a) / (1 - b))


def rate(g, pa, rho, rb, dis, gb):
    a = rho**g
    q1, q0 = a + (1 - a) * pa, (1 - a) * pa
    u1 = 0.5 + 0.5 * rb**g
    I = pa * (kl(q1, u1) if q1 > u1 else 0) + (1 - pa) * (kl(q0, 0.5) if q0 > 0.5 else 0)
    return I / max(g + 1 / dis, gb)


if __name__ == "__main__":
    dis, gb, alpha = 0.2, 10.0, 0.05
    print("pa   rho   rb    g*   rate*1e3  t*=log(1/a)/rate")
    for pa in (0.6, 0.65):
        for rho in (0.0, 0.8, 0.95):
            for rb in (0.0, 0.8, 0.9, 0.95):
                rs = [rate(g, pa, rho, rb, dis, gb) for g in range(200)]
                g = int(np.argmax(rs))
                r = rs[g]
                print(
                    f"{pa:.2f} {rho:.2f} {rb:.2f} {g:4d} {1e3 * r:8.3f} {math.log(1 / alpha) / r if r > 0 else float('inf'):8.0f}"
                )
