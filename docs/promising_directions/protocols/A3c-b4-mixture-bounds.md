# A3c registered protocol: exact mixture-gap bounds at B = 4, alpha = 1/10

Registered 2026-11-01 after `3d8138c` and before execution. Development / theory probe; no
method claim.

## Question

A3 found a positive pure-calendar gap in every one of the 54 families at B = 4, alpha = 1/10. A3b
showed that 50 of those 54 recovered optima are label-adaptive, not pre-label mixtures. The open
question is whether public-coin mixtures of calendars close the gap at the programme's risk
level.

## Cells

The six families with the largest A3 pure gaps. All use T = 8, B = 4, d = 1 and cq = 1/100.

| acc | transition | prior1 | cs | A3 pure gap |
|---|---|---|---|---|
| 49/50 | 1/20 | 1/20 | 1/20 | 1.41% |
| 49/50 | 1/20 | 1/20 | 1/5 | 1.23% |
| 49/50 | 1/20 | 1/10 | 1/20 | 1.23% |
| 49/50 | 1/20 | 1/10 | 1/5 | 1.20% |
| 19/20 | 1/20 | 1/20 | 1/20 | 1.09% |
| 19/20 | 1/20 | 1/20 | 1/5 | 0.92% |

## Computation

1. For each family, compute `C_c(a)` for all 99 calendars with at most 4 slots in 1..7, on the
   grid {0, 1/40, 1/20, 3/40, 1/10, 1/8, 3/20, 1/5, 1/4, 3/10, 2/5, 1/2, 3/4, 1}. Solver
   `2bd2e8e`, max_nodes 200,000. That is 6 × 99 × 14 = 8,316 solves.
2. J(1/10) and J(1) are taken from the A3 Part 2 rows (exact). As a sanity check, the grid
   minimum at a = 1/10 must equal the A3 C* exactly.
3. Before any bound is used, verify that every calendar curve is nonincreasing and convex on
   the grid. A violation invalidates the lower bound and is reported.
4. Compute bounds `[g_lo, g_up]` on the mixture gap at alpha = 1/10 using
   `mixture_bounds.mixture_bounds`.
5. Compute the unconstrained gap g(1) from the A3 reference rows. At a = 1, conv(C*) equals
   C*(1), because C* is nonincreasing.

Run as a single detached process, resumable through JSONL, with at most 2 workers and a 3-hour
cap.

## Decision rules

| Outcome | Condition |
|---|---|
| MIXTURES CLOSE IT | `g_up(1/10) = 0` in every family |
| GENUINE GAP AT alpha = 0.10 | `g_lo(1/10) > 0` in some family |
| RISK-SPECIFIC AT alpha = 0.10 | Additionally, `g_lo(1/10) − g(1) ≥ 0.005` in some family |
| INCONCLUSIVE | None of the above |

All gap sizes are reported against the 10% practical threshold.
