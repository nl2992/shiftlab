# ruff: noqa: SIM115
"""Certifiability-frontier table: gamma_lb (KL), gamma_np (exact NP, B<=14), gamma_ub (Hoeffding window),
ratio, plus large-B grid (no NP).  Writes outputs/paper3/payback/frontier.json."""

import json
import math

from shiftlab.paper3.payback import theory as th
from shiftlab.paper3.payback.envelope import Envelope

rows = []
for alpha in (0.05,):
    beta = 0.5 if False else 0.2
    for v in (0.0, 0.002, 0.01, 0.03):
        for B in (6, 10, 14, 50, 200, 1000):
            base = 0.1 + 0.0  # k/h + irreducible slack, absorbed (KL uses L=gamma+base)
            lb = th.gamma_lb(B, v, base, alpha, beta)
            ub, n = th.gamma_ub(B, Envelope(v), alpha, beta)
            np_ = th.exact_np_gamma(B, v, base, alpha, beta) if B <= 14 else None
            rows.append(
                {
                    "alpha": alpha,
                    "beta": beta,
                    "v": v,
                    "B": B,
                    "base": base,
                    "gamma_lb": lb,
                    "gamma_np": np_,
                    "gamma_ub": ub,
                    "n_ub": n,
                    "ratio_ub_lb": (ub / lb if math.isfinite(lb) and lb > 0 else None),
                    "ratio_ub_np": (ub / np_ if np_ and math.isfinite(np_) else None),
                }
            )
json.dump(rows, open("outputs/paper3/payback/frontier.json", "w"), indent=1)
for r in rows:
    f = lambda x: "  inf" if x is None or not math.isfinite(x) else f"{x:.3f}"
    print(
        f"v={r['v']:<6} B={r['B']:<5} lb={f(r['gamma_lb'])} np={f(r['gamma_np'])} ub={f(r['gamma_ub'])} n_ub={r['n_ub']:<4} ub/lb={f(r['ratio_ub_lb'])} ub/np={f(r['ratio_ub_np'])}"
    )
# rate check: v^{1/3} regime
for v in (1e-5, 1e-4, 1e-3):
    lb = th.gamma_lb(10**6, v, 0.0, 0.05, 0.2)
    ub, n = th.gamma_ub(10**5, Envelope(v), 0.05, 0.2)
    print("rate", v, lb, ub, lb / v ** (1 / 3), ub / v ** (1 / 3), ub / lb)
