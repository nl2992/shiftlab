"""Exact finite-support check of the restart mixture (T = 7, binary increments, history-dependent predictable bets)."""

import itertools
import json

import numpy as np

T, ALPHA = 7, 0.05
a, b, p_b = 0.5, 1.0, 0.25  # X = +b w.p. p_b, else -a * ... centred below
x_hi, x_lo = 1.0, -1.0 / 3.0
p_hi = (0 - x_lo) / (x_hi - x_lo)  # E[X] = 0 (boundary of the null)
w = np.array([0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])  # predetermined start weights, sum 1


def lam(history):  # predictable bet: depends on the past only (bounded so that 1 + lam X >= 0.5)
    k = sum(1 for h in history if h == x_hi)
    return min(1.5, 0.3 + 0.3 * k)


tail = np.cumsum(w[::-1])[::-1]
max_viol, p_cross, worst_drift = 0.0, 0.0, 0.0
for path in itertools.product([x_hi, x_lo], repeat=T):
    prob = np.prod([p_hi if v == x_hi else 1 - p_hi for v in path])
    s, m_prev, crossed = 0.0, 1.0, False
    for t in range(T):
        f = 1.0 + lam(path[:t]) * path[t]
        s = (s + w[t]) * f
        m = s + (tail[t + 1] if t + 1 < T else 0.0)
        crossed |= m >= 1 / ALPHA
    p_cross += prob * crossed
# conditional-drift check: E[M_t | history] <= M_{t-1} for every history
for t in range(T):
    for hist in itertools.product([x_hi, x_lo], repeat=t):
        s = 0.0
        for u in range(t):
            s = (s + w[u]) * (1.0 + lam(hist[:u]) * hist[u])
        m_prev = s + tail[t]
        exp_m = sum(
            (p_hi if v == x_hi else 1 - p_hi) * ((s + w[t]) * (1.0 + lam(hist) * v) + (tail[t + 1] if t + 1 < T else 0.0))
            for v in (x_hi, x_lo)
        )
        worst_drift = max(worst_drift, exp_m - m_prev)
out = {"T": T, "alpha": ALPHA, "exact_P_sup_M_ge_1/alpha": p_cross, "bound": ALPHA, "max_conditional_drift_E[M_t|F]-M_{t-1}": worst_drift}
print(out)
with open("outputs/h2c_restart/exact_restart_test.json", "w") as fh:
    json.dump(out, fh, indent=2)
