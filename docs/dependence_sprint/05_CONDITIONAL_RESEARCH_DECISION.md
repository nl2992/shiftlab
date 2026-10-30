# 05 Conditional research decision (the path actually taken)
Code commit at start: `8552911`; sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: docs 02-04.

| gate | state | reason (evidence) |
|---|---|---|
| A. is the dependence failure a genuine inferential problem? | **PASS** (as a null-class mismatch) | dependent processes satisfying H0-cond stay valid (UCB <= 0.044); persistent processes violating H0-cond inflate; no theorem violated |
| B. is the desired guarantee achievable? | **FAIL** for stationary-average safety with useful power under persistent regimes; PASS only near-iid or for the reformulated conditional null | Theorem B1; oracle power 0.07-0.48 at 20-400-step regimes |
| C. does published work already solve it? | **UNRESOLVED** (general); KNOWN (fully observed finite-state) | Sethi et al. Thm 4.1; hidden-Markov open per authors; bounded search |

## Controller path
Stage 1: null defined (cond. and marg.), target guarantee impossible under the persistence class → obstruction proved, narrowed to near-iid / conditional null, feasibility restarted once (reformulation) → conditional null is already served by existing monitors. Stage 2: source access adequate for the key papers but search not exhaustive → MARK UNRESOLVED for the general claim, KNOWN for the fully observed case; do not claim novelty. Stage 3-5: **not entered** (no theorem candidate whose regime is non-vacuous; nothing to prove, no method to confirm). 
Case taken: **Case 2** (valid method exists/is known; not novel) for dependence monitoring → dependence-monitoring methodology is marked **NO_GO as a contribution**; the repaired conditional-null monitors (HG and the PR/PPRM family) are kept as infrastructure. Not Case 1 (no non-vacuous theorem opportunity), not Case 3/4/5 (no new method was built; the LRV heuristic stays EMPIRICAL_ONLY: its false-alarm reduction was specific to the clustered null it was tuned against and it lost power).
Then, as required by Case 2, the switching question and the fallbacks were examined in order (docs 06, 11): Fallback A rejected (trivial/known), Fallback B rejected (failed round 2; established), Fallback C unresolved (no theorem).
Why alternatives were rejected: *building a new dependence-robust detector* — Gate B proves no detector, even an oracle, has useful power in the persistence range of interest, so empirical gains would be either invalid (EMPIRICAL_ONLY) or null-calibrated; *proceeding to confirmation* — nothing eligible to freeze.
