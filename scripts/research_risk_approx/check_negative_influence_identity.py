"""Exhaustive check of the Paper 4 negative-influence (causal-risk surcharge) identities.

Exact Fraction arithmetic over every Boolean promotion event on complete binary tapes, T <= 3.
For each event A, with causal-null value v(h) = max{v(h0), (v(h0)+v(h1))/2} (p_t in [0, 1/2])
and fair-IID value f(h) = (f(h0)+f(h1))/2, checks:
  1. R_causal - R_IID == sum_t 2^-t sum_{|h|=t-1} [v(h0) - v(h1)]_+   (Proposition A)
  2. R_IID <= R_causal <= P_IID(upward hull of A)                     (Proposition B)
Also evaluates the randomized-policy counterexample: the marginal promotion map's hull
certificate (1/2) understates the true robust risk (3/4) when public queries leak the coin.
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import product


def values(T: int, event: set) -> tuple[dict, dict]:
    v: dict = {}
    f: dict = {}
    for t in range(T, -1, -1):
        for h in product((0, 1), repeat=t):
            if t == T:
                v[h] = f[h] = F(int(h in event))
            else:
                v0, v1 = v[h + (0,)], v[h + (1,)]
                v[h] = max(v0, (v0 + v1) / 2)
                f[h] = (f[h + (0,)] + f[h + (1,)]) / 2
    return v, f


def check_horizon(T: int) -> dict:
    tapes = list(product((0, 1), repeat=T))
    failures = hull_exact = 0
    worst_gap, worst_event = F(0), set()
    for mask in range(2 ** len(tapes)):
        event = {tapes[i] for i in range(len(tapes)) if mask >> i & 1}
        v, f = values(T, event)
        surcharge = sum(
            F(1, 2**t) * max(v[h + (0,)] - v[h + (1,)], F(0))
            for t in range(1, T + 1)
            for h in product((0, 1), repeat=t - 1)
        )
        hull = {x for x in tapes if any(all(a <= b for a, b in zip(y, x)) for y in event)}
        p_hull = F(len(hull), 2**T)
        if v[()] - f[()] != surcharge or not f[()] <= v[()] <= p_hull:
            failures += 1
        hull_exact += p_hull == v[()]
        if p_hull - v[()] > worst_gap:
            worst_gap, worst_event = p_hull - v[()], event
    return {
        "events": 2 ** len(tapes),
        "failures": failures,
        "hull_exact": hull_exact,
        "max_hull_gap": worst_gap,
        "worst_event": sorted(worst_event),
    }


def randomized_counterexample() -> tuple[F, F]:
    """Root coin U (fair, private). U=0: query events 1,2; promote iff Y2=0.
    U=1: query event 2 only; promote iff Y2=1. The null sees whether event 1 was queried."""
    # Branch U=0: promotion iff Y2=0; null picks p2 in [0,1/2] to maximise 1-p2 -> p2=0.
    risk_u0 = max(1 - p for p in (F(0), F(1, 2)))
    # Branch U=1: promotion iff Y2=1; null maximises p2 -> p2=1/2.
    risk_u1 = max(p for p in (F(0), F(1, 2)))
    robust = (risk_u0 + risk_u1) / 2
    # Marginal promotion map E_U[g_U(y)] = 1/2 on every tape; its monotone hull is also 1/2.
    marginal = F(1, 2) * 1 + F(1, 2) * 0  # any tape: exactly one branch promotes
    return robust, marginal


def main() -> None:
    total_failures = 0
    for T in (1, 2, 3):
        r = check_horizon(T)
        total_failures += r["failures"]
        print(
            f"T={T}: events={r['events']} failures={r['failures']} hull_exact={r['hull_exact']} "
            f"max_hull_gap={r['max_hull_gap']} worst={r['worst_event']}"
        )
    v, f = values(3, {(0, 1, 0), (1, 0, 1)})
    print(f"A={{010,101}}: IID={f[()]} causal={v[()]} hull=5/8")
    robust, marginal = randomized_counterexample()
    print(
        f"randomized counterexample: true robust risk={robust}, marginal-hull certificate={marginal}"
    )
    assert total_failures == 0 and robust == F(3, 4) and marginal == F(1, 2)
    print("all checks passed")


if __name__ == "__main__":
    main()
