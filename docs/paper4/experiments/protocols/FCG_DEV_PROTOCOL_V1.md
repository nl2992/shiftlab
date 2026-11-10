# Frontier-Cut Generation (FCG): development protocol v1

**Registered:** 2026-11-09, before any FCG code exists. **Branch:** `research/paper4-antitone-frontier-2026-11-09`.
**Status:** development screen on synthetic cells only. No holdouts, no real data, no CRSP.
**Gate philosophy (user direction, 2026-11-09):** lax gates. The aim is to establish a correct,
problem-specific computational algorithm with a certificate. Beating every SOTA method is not required.

## Algorithm under test

Let `x` be the learner realization plan of the exact first-promotion decomposed game
(`FirstPromotionDecomposedGame`), with flow constraints `E x = e, x >= 0` and linear alternative cost `c x`.
For a fixed pure causal-null strategy `nu` (a map from generated history, including pending
outcomes and public actions, to `p in {0, 1/2}`), first-promotion risk is linear: `r_nu x`.

1. `K <- {IID}` (`p = 1/2` everywhere, an extreme point).
2. Solve LP `P_K: min c x  s.t.  E x = e,  r_nu x <= alpha  (nu in K),  x >= 0`.
3. Certify a lower bound `L_K` from the rationalised dual, with an exact reduced-cost correction.
4. Recover the behavioural policy. Compute its exact robust risk and the argmax null `nu*` with the
   endpoint recursion (`p = 0` exactly where `v(h0) > v(h1)`, the inversion frontier).
5. Root-mix with never-promote at `q = min(1, alpha / risk)` and compute the exact cost `U_K`.
6. If `risk <= alpha` (exact rational), stop. Otherwise add `nu*` to `K` and go to 2.

**Correctness claims to check numerically** (proved in `docs/paper4/theory/01_structural_theorem_audit.md`):
- `L_K <= V*`, because `P_K` relaxes the full robust constraint.
- `U_K >= V*`, because the repaired policy is feasible.
- Each cut is new and finite termination follows.

## Cells (full configurations; prior 1/2, alpha 1/10, query fee 1/100, switch fee 1/10 throughout)

| id | T | B | d | transition (both ways) | emissions | role |
|---|---|---|---|---|---|---|
| C1 | 5 | 2 | 1 | 1/4 | (1/20, 19/20) | persistent control (existing T=5 anchor family) |
| C2 | 5 | 2 | 1 | 9/10 | (1/10, 9/10) | anti-persistent |
| C3 | 6 | 3 | 1 | 3/4 | (1/20, 19/20) | anti-persistent |
| C4 | 6 | 3 | 1 | 1/4 | (1/20, 19/20) | control; anchor cost 461083/160000 if matched |
| C5 | 8 | 3 | 1 | 1/4 | (1/20, 19/20) | control; anchor cost 24735833/6400000 |
| C6 | 8 | 3 | 1 | 3/4 | (1/20, 19/20) | anti-persistent scale |

The reference for every cell is the exact decomposed sequence-form solve (`FirstPromotionDecomposedGame.solve()`).
The anchor costs are matched only if the configuration hash agrees with the anchor's source.
Otherwise they are not claimed.

## Gates (lax)

- **G-correct (required):** on every cell, the final policy has exact rational robust risk `<= alpha`;
  `L <= U`; `|U - V_ref| <= 1e-6`; and, at termination, `U - L <= 1e-6` (relative to `|U|`).
- **G-demo (required for an algorithm claim):** on at least one cell, the IID optimum is unsafe
  (exact robust risk `> alpha`), at least one frontier cut is generated, and the final certified
  `U` is strictly below the IID-plus-repair `U_0`. In other words, cuts recover value that repair discards.
- **G-compute (reported, not required):** number of risk rows `|K|` versus reference opponent sequences.
  Also end-to-end wall-clock (build, LP, verification and repair all included) versus the reference.
  A runtime advantage is claimed only where it is measured.

If G-demo fails on every anti-persistent cell, record the reason (for example, IID optimum always safe,
or cuts recover no value) and the algorithm is not claimed.

## Prior-art boundary fixed in advance

FCG is a cutting-plane / double-oracle scheme (sequence-form double oracle: Bošanský et al.; Benders-type
constraint generation). Any claim is limited to the **problem-specific exact separation oracle**: the
polynomial product-state best response, whose cut is the inversion-frontier strategy. The claim also covers the
anytime certified interval against the unrestricted oracle `V*`. It is not a new optimisation principle.
