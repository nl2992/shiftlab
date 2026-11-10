# 03 — Optimisation and certificates (WP3)

**Date:** 2026-11-10. Proofs are in `theory/01` §4. This file gives the end-to-end specification and the
certificate contents.

## End-to-end algorithm (FCG-fast, `src/shiftlab/paper4/frontier_cuts_fast.py`)

```
input: config (T, B, d, alpha, query fee, switch fee), alternative HMM
build learner-only first-promotion decomposed tree (float costs; belief cache by learner information)
K <- {IID}                                    # p = 1/2 at every null node
loop:
    x <- argmin c.x  s.t.  E x = e,  r_nu . x <= alpha (nu in K),  x >= 0      # HiGHS, float
    pi <- behavioural policy recovered from x
    (risk, nu*) <- exact endpoint best response of the null to pi            # Fraction
    if risk <= alpha: break
    assert r_nu* . x > alpha + 1e-9 ;  K <- K + {nu*}                         # strict, new cut
final certificate (exact, once):
    exact cost vector and exact rows for K
    L <- rationalised dual objective - reduced-cost residual correction       # valid since 0 <= x <= 1
    q <- min(1, alpha / risk)                                                # 1 at termination
    U <- exact cost of the realization-space root mixture q.x + (1-q).x_never
    assert exact robust risk(U-policy) <= alpha and L <= U
output: policy, U, L, U - L, |K|, timing split
```

## Certificate contents (per run)

- **Lower bound:** `L`, the exact rational value, plus the dual multipliers and the correction terms.
- **Feasible policy:** its realization plan and behavioural form.
- **Risk certificate:** the exact rational robust risk from `game.null_risk`, plus the best-response strategy.
- **Economic cost:** `U`, exact from `game.expected_metrics`.
- **Numerical error accounting:** LP tolerances `1e-9`. The final `L` absorbs residual dual infeasibility via the
  correction, and `U` is exact.
- **Certified gap:** at most 4e-14 on every cell (`experiments/04`).

## WP3.1–3.5 status

| Item | Status |
|---|---|
| WP3.1 IID-relaxed candidate and lower bound | Done. This is iteration 0 |
| WP3.2 candidate classes | The unrestricted sequence-form plan only. FSC, decision-diagram and branch-and-bound variants are not needed, because the gap is already 0 |
| WP3.3 safety repair | Done in realization space. Its value loss is quantified: 0.3–0.5% on IID-unsafe cells, which the cuts recover |
| WP3.4 certified `[L, U]` | Done, `U - L <= 4e-14` |
| WP3.5 tightening | Done by the cuts themselves (exact `V*`). No further hierarchy is needed |

## Prior-art reduction

The method is constraint generation over adversary strategies (sequence-form oracle methods, Bošanský et al.
2014, which the paper itself relates to Dantzig–Wolfe constraint/column generation). See `PRIOR_ART_MATRIX.md`.
