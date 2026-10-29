# First-promotion decomposition: fixed-budget scaling protocol

**Registered:** 2026-10-29 before execution. This is a solver-complexity comparison only; it is not
an efficacy or real-data study.

## Question

At a fixed pathwise query cap, does eliminating unconstrained post-promotion realization variables
reduce the exact two-law solver's size as the horizon grows, while preserving alternative cost and
full-history causal-null promotion risk?

## Frozen configurations and comparator

Run the untouched `CausalSwitchingGame` and `FirstPromotionDecomposedGame` on `T in {6,7,8}` with
`B=3`, delay `d=1`, `alpha=1/10`, query price `1/100`, switch price `1/10`, symmetric HMM transition
probabilities `1/4`, emissions `(1/20,19/20)`, and prior `1/2`. The `T=6` cell is the certified
reference anchor; `T=7,8` extend horizon at fixed budget without tuning. Preserve the solver's
200,000-node cap and 60-second LP time limit. Do not shrink a failed configuration or alter
parameters.

## Endpoints and pass/failure handling

For both methods, record builder nodes, learner sequences/information sets, opponent sequences,
LP objective, independently forward-evaluated five-metric tuple, and exact causal-null risk.
Require each returned policy to satisfy `risk <= 1/10`, pathwise queries `<=3`, and per-method
agreement between the LP objective and independently evaluated expected cost within `1e-7`.
Compare full and reduced optimum costs within `1e-7`; exact policy metrics need not agree if an LP
has multiple optima. Preserve time/node-limit failures verbatim. Do not run Monte Carlo, tune a
method, or inspect any held-out real data.

## Interpretation gate

The endpoint tests only whether the implementation exploits the first-promotion factorization.
A size reduction is not by itself a methodological contribution. Any G1 claim still requires a
source-level novelty audit of robust stopping/event-tree elimination under asymmetric alternative
utility and null risk, and a theorem showing an advantage over the best applicable composition.
