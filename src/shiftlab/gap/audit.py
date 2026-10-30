"""Exact finite-support validity calculations (no simulation)."""

from __future__ import annotations

import itertools

from shiftlab.gap import worlds as W


def exact_cap_check(qs=(0.05, 0.1, 0.2, 0.5), cap_fracs=(0.25, 0.5, 0.9)) -> list[dict]:
    """E[1 + lam(x) X] for the re-arranged heterogeneous null whose marginal risk equals r0 exactly.

    A valid betting factor needs expectation <= 1. ``x`` is the legacy covariate-dependent cap
    lam(x) = c / (h_x (1/q - 1) + r0); ``sup`` uses the predictable bound with max_x h_x.
    """
    hn = W.HeteroNull()
    r0, rho = hn.r0(), hn.rho(True)
    assert abs((1 - hn.p_x1) * rho[0] + hn.p_x1 * rho[1] - r0) < 1e-12
    rows = []
    for q, c in itertools.product(qs, cap_fracs):
        res = {}
        for mode in ("x", "sup"):
            tot = 0.0
            for x, px in ((0, 1 - hn.p_x1), (1, hn.p_x1)):
                hx = hn.h[x]
                bound = (hx if mode == "x" else max(hn.h)) * (1 / q - 1) + r0
                lam = c / bound
                for Q, pq in ((1, q), (0, 1 - q)):
                    for loss, pl in ((1, rho[x]), (0, 1 - rho[x])):
                        X = hx + (Q / q) * (loss - hx) - r0
                        tot += px * pq * pl * (1 + lam * X)
            res[mode] = tot
        rows.append(
            {"q": q, "cap_frac": c, "E_factor_x_cap": res["x"], "E_factor_sup_cap": res["sup"]}
        )
    return rows
