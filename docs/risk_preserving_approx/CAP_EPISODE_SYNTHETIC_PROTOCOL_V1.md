# Capped planner versus episode composition: synthetic development protocol

Registered before execution on 2026-10-29 from commit f2b3ccf. This is a
known-model development comparison on the six HMM cells previously used in
`docs/switching_episode_composition_grid_protocol_v1.md`, not independent
confirmation. The earlier results were exposed; no tuning or performance-based
selection of these cells is permitted.

Fix T=6, B=3, d=2, alpha=1/10, query fee 1/100, switch fee 1/10, prior 1/2.
Use transition rates {1/10,1/4,9/20} and emissions {(1/10,9/10),(1/50,49/50)}.
Compare (1) full first-promotion decomposed oracle, (2) pre-promotion cap m=2
with original B=3 after promotion, and (3) the existing episode-composition
baseline: best of all 15 eligible fixed calendars and the three registered
spending rules. Both optimizers and comparator receive the same model, losses,
delay, costs, total budget and causal-null definition. Baseline calendar and
spending are selected with the known alternative model; this favors the baseline
and is not deployment-time evidence. Evaluate each policy's exact rational
expected costs and worst causal-null risk. For floating-point recovered policies,
report any root activation required for exact safety and its adjusted cost.
Record cost, cost difference against comparator and full oracle, risk, expected
queries/switches, sequence and node counts, solver status, elapsed times, and
source hashes. Retain failures, zero-promotion outcomes and ties. If an episode
policy violates the cap or risk, record failure instead of excluding it silently.

This test does not claim a published source-matched strongest baseline, empirical
uncertainty, a novelty result, or real-data validation. No Monte Carlo seeds,
real-data rows, held-out data or historical outputs are accessed. Store new
non-overwriting JSON; do not alter the original comparison. Require validation of
the existing implementation and cap safety; preserve numerical versus exact
certificate distinctions. Re-run focused existing tests after implementation.
