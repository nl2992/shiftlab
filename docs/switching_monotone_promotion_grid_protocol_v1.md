# Monotone-promotion structural grid: preregistered screen

**Registered:** 2026-10-29, before execution. **Purpose:** falsify a structural theorem hypothesis,
not measure efficacy or establish novelty. The existing single-cell result is
`docs/switching_monotone_adaptive_oracle_cell_v1.md`.

## Hypothesis

For the finite two-state HMM alternative with increasing binary emissions, the unrestricted
causal-game optimum may admit a first-promotion probability that is coordinatewise increasing in
the potential-label tape. If true for a declared family, the one-sided conditional null
`P(Y_t=1 | full past, query) <= 1/2` is maximized by the iid Bernoulli(1/2) boundary for that
promotion event. The optimization with an increasing-event constraint would then be exact for the
unrestricted robust-null problem on that family.

The monotone-null-risk implication for a *fixed increasing event* is elementary stochastic
dominance. The research question is whether an optimal economic switching policy can be chosen
with such a promotion event under delays, pending queries, a pathwise cap, and reversal costs.

## Frozen cells

Use `CausalSwitchingGame.solve(monotone_promotion=False/True)` with exact Fraction-valued
configurations. Keep horizon small enough for the full sequence-form LP. All cells use query cost
and switch cost charged per the current harness and the same alternative HMM in both planners.

| Cell | T | B | d | alpha | query c | switch k | transition (0→1,1→0) | emissions (state 0, state 1) |
|---|---:|---:|---:|---:|---:|---:|---|---|
| M1 | 5 | 3 | 1 | 1/10 | 1/100 | 1/10 | (1/4,1/4) | (1/10,9/10) |
| M2 | 5 | 3 | 1 | 1/20 | 1/100 | 1/10 | (1/4,1/4) | (1/10,9/10) |
| M3 | 5 | 3 | 1 | 1/5 | 1/100 | 1/10 | (1/4,1/4) | (1/10,9/10) |
| M4 | 5 | 3 | 2 | 1/10 | 1/100 | 1/10 | (1/4,1/4) | (1/10,9/10) |
| M5 | 5 | 2 | 1 | 1/10 | 1/100 | 1/10 | (1/4,1/4) | (1/10,9/10) |
| M6 | 5 | 3 | 1 | 1/10 | 1/10 | 1/10 | (1/4,1/4) | (1/10,9/10) |
| M7 | 5 | 3 | 1 | 1/10 | 1/100 | 1 | (1/4,1/4) | (1/10,9/10) |
| M8 | 5 | 3 | 1 | 1/10 | 1/100 | 1/10 | (1/10,3/10) | (1/10,9/10) |
| M9 | 5 | 3 | 1 | 1/10 | 1/100 | 1/10 | (1/4,1/4) | (1/4,3/4) |

The initial good-state probability is 1/2 in every cell. No cell may be dropped because it is
computationally inconvenient; if a registered cell exceeds the existing node cap, record that as a
scalability result and do not shrink its horizon after observing other cells.

## Procedure and decision rule

For every cell, solve unrestricted and monotone-constrained LPs. Re-evaluate each recovered policy
with exact rational forward recursion for alternative cost and robust causal-null risk. Enumerate
all `2^T` potential label tapes for the recovered monotone policy and verify every cover relation.
Record solver objective, equality/inequality residuals, recovered policy metrics, and code hashes.

**Falsification:** any cell with an unrestricted-minus-monotone cost advantage greater than
`1e-5` and both LP residuals below `1e-7` kills the unqualified monotone-optimum conjecture. A cell
with a numerical gap but failed exact risk/forward verification is inconclusive and must be
repaired once. If the gap is at most `1e-5` everywhere, the grid only supports the conjecture; it
does not prove it or establish a method contribution.

**Novelty gate:** even an all-cell match is not a pass. Before naming a method, prove the result for
a growing horizon/resource family, give the resulting compact algorithm and complexity, and audit
monotone Bayesian control / isotone stochastic games / one-sided sequential testing. If the theorem
is a direct monotone-DP or Neyman–Pearson corollary, stop. No broad synthetic sweep, real-data run,
or manuscript work follows from this screen alone.

Reproduction command after implementation: `uv run python scripts/screen_switching_monotone_promotion_grid.py`.

## Results and updated decision (2026-10-29)

The registered script completed all nine cells at the configured node cap. The unrestricted LP's
recovered first-promotion event was coordinatewise increasing in all nine cells; the constrained
LP recovered the same calibrated cost in every cell (exact recovered-policy difference `0`).
For eight informative cells, exact recursive null risk equaled the iid `1/2` boundary risk, which
was exactly the registered alpha. M7 (`k=1`) never promoted and has risk zero, so it is
uninformative for the monotonicity claim. Maximum LP residual over all cells was
`5.56e-17`. Results, all 32-label-tape event tables per cell, and source hashes are in
`outputs/switching_monotone_promotion_grid_v1/results.json`.

The initial screen contained LP solver outputs plus exact evaluations of recovered policies, not
rational primal-dual optimality certificates. That limitation was addressed by
`scripts/certify_switching_monotone_promotion_grid.py`, which rebuilds both LPs and verifies
rationalized dual lower bounds and recovered-policy upper bounds using exact `Fraction` arithmetic.
Reproduction command: `uv run python scripts/certify_switching_monotone_promotion_grid.py`.
The certificate artifact is
`outputs/switching_monotone_promotion_grid_cert_v1/results.json`. All 18 primal-dual brackets
closed to within `1e-7`; every unrestricted recovered event remained monotone, and exact robust
null risk equaled iid-boundary risk in all nine cells. These certificates establish equality of
the unrestricted and monotone-constrained optima only for these nine finite instances. They do not
establish equality for a growing family or a method contribution.

The targeted source check found a close established component: Krishnamurthy's [*POMDP Structural
Results for Controlled Sensing*](https://arxiv.org/abs/1701.00179), Theorem V.2, gives an MLR-
monotone value result under first-order-stochastically ordered costs and TP2 action-specific
transition and observation matrices. Its model permits controlled observations, but the theorem
is about value monotonicity; it does not state the two-law global promotion-risk constraint,
history-adaptive null opponent, or pending-label/request-budget process here. Classical POMDP
threshold results therefore raise the novelty bar; they are not an exact reduction by themselves.

**Decision update:** a separate registered, exact counterexample already establishes that the
monotone terminal-promotion class can lose economic value under a recurrent alternative; see
`docs/switching_monotone_restriction_counterexample_v1.md`. The nine exact brackets above do not
reverse that result. Close monotone promotion as a general lossless restriction and do not attempt
to elevate the finite matches into a theorem. The exact causal-null/IID identity remains available
for policies independently shown to have increasing promotion events. Generic constrained-POMDP
scalarization remains a standard reduction, not a method contribution. Any reopening requires a
different theorem-backed compression/approximation or strict growing-family separation against
robust-FSC/sequence-form and matched established control baselines. G2–G5 remain closed.
