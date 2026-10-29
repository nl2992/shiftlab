# Finite-window POMDP approximation: novelty boundary

**Date:** 2026-10-29. **Status:** source-level candidate screen; generic finite-memory
approximation is established, while the exact two-law risk-constrained reduction remains unresolved.

## Primary source inspected

Kara and Yüksel, “Near Optimality of Finite Memory Feedback Policies in Partially Observed Markov
Decision Processes,” *Journal of Machine Learning Research* 23(11), 2022, pp. 1–46. The official
JMLR PDF was inspected for the information structure, finite-window policy definition, filter
stability conditions, and Theorems 12, 16, and 17. A local source copy is recorded by
`switching_source_manifest_v33.json`; its SHA256 is
`8F967EB90151973668E15FF7FA17AF19831F4355E1341087B7BDCC761A422597`.

The paper constructs a finite belief model from a window of recent observations/actions and gives
near-optimality bounds for the resulting finite-memory policies under explicit filter-stability
conditions. Theorem 12 bounds conditional expected discounted cost after an initial window;
Theorem 16 bounds the gap between the best finite-window policy and the unrestricted discounted
POMDP optimum at an exponential rate when the stability coefficient is below one; Theorem 17 gives
a corresponding value bound in terms of a uniform total-variation filter approximation error. The
work assumes a known controlled transition/observation model and a single expected-cost objective.

## Mapping to the ShiftLab target

The closest possible candidate was to truncate old released labels when computing the alternative
HMM belief, then optimize a finite-memory query/deployment controller. This would retain a hard
query cap and pending-label ages as explicit controller state. It would need to preserve the
project's separate statistical event

`sup_{P in causal conditional null} P(any promotion by T) <= alpha`,

where the null sees queried event outcomes before their delayed release and the learner cannot.
The JMLR result does not analyze that two-law information asymmetry, chance constraint, query-cost
budget, or delayed label-release state. Its discounted single-model near-optimality theorem cannot
be transferred to this contract by simply appending budget and queue coordinates.

## Decision

Close “finite-window belief truncation for tractability” as a novelty claim. It is an established
POMDP approximation ingredient and adding the existing query-budget/queue state is routine state
augmentation. A potentially distinct theorem would have to give separate, nonvacuous economic-value
and worst-case causal-risk approximation errors for this two-law delayed game, with a complexity
advantage over the exact sequence-form oracle and robust finite-state-controller methods. No such
bound has been derived or checked here; the mismatch with Kara–Yüksel is a comparison obligation,
not evidence that the extension is novel. No algorithm, synthetic efficacy study, or real-data
evaluation follows from this screen.

Primary links: [JMLR article](https://jmlr.org/papers/v23/20-1152.html),
[official full PDF](https://jmlr2020.csail.mit.edu/papers/volume23/20-1152/20-1152.pdf).
