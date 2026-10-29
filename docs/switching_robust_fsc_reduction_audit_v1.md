# Robust finite-state controller reduction: representation is available, compression is not

**Date:** 2026-10-28. **Status:** primary-source audit and exact modeling reduction; no new algorithm or theorem.

## Source-level result

Cubuktepe et al., “Robust Finite-State Controllers for Uncertain POMDPs,” AAAI 2021, [official paper](https://ojs.aaai.org/index.php/AAAI/article/view/17401/17208). The primary nine-page PDF is cached at `outputs/switching_source_audit_v1/cubuktepe_robust_finite_state_controllers_aaai21.pdf` (482,490 bytes; SHA256 `A9F6AF361644865D20448B52FAAC67A76D0E7A569EB60078C657F25624AE11A8`). Inspected its uPOMDP/FSC model and observation-based policy definition (Section 2), robust expected-reward formulation and uncertainty dualization (Section 3), sequential-convex local optimization and exact robust verification (Algorithm 1), and finite-memory experiments (Section 5).

The method searches over finite-memory controllers for partially observed models with interval/polytopic transition uncertainty and robust reachability or expected-reward specifications. The authors characterize the general problem as theoretically and practically intractable; their dualized nonconvex FSC optimization is linearized by sequential convex programming. The returned controller is locally optimized, and a separate robust verification step checks whether its specification is satisfied. It is not a globally optimal policy guarantee or a regret bound.

## Exact representation of the ShiftLab safety branch

For a finite horizon, the causal-null process can be represented as an uncertain partially observed model by augmenting the physical state with

`(time, full public action/query history, all generated queried outcomes, release queue, budget spent, promoted flag)`.

At each queried event, the transition interval for the binary outcome is `[0, 1/2]`; the augmented history is part of the state, so Nature may choose a different conditional probability at every event-time history. The learner's observation reveals only outcomes whose release time has arrived. Query rights are removed at request time, and the promoted flag makes “ever promoted” a reachability objective. Thus a finite-state controller over this augmented model can robustly enforce the global false-promotion probability, subject to the FSC method's model assumptions. The augmentation is exact but has a history-sized state space; a crude upper bound includes `2^T` public action paths and up to `sum_{q=0}^B binom(T,q) 2^q` query/outcome histories. This is an encoding, not a compact sufficient statistic.

The same FSC can be evaluated on a second copy of the process whose hidden regime follows the economic HMM; its expected deployment, query and switch costs define the objective. But the resulting task has one controller tied across two different kernels, with reward measured only on the HMM copy and a worst-case reachability constraint only on the causal-null copy. Cubuktepe et al.'s single-uPOMDP robust-reward formulation does not directly optimize this two-model objective. Constructing a product model or adding multiple initial modes makes a finite optimization formulation, but does not provide a new scalable bound.

## Novelty consequence

This prior closes novelty from “use a finite-memory robust controller,” “augment delayed labels and budget into state,” “verify reachability risk exactly,” or “optimize a robust FSC by generic dualization/SCP.” The same broad ingredients, including partial observation, interval uncertainty, finite controller memory, reachability specifications, and robust verification, are established. The exact-history reduction also corrects an overly strong interpretation that the causal conditional null is unrepresentable as a robust POMDP: it is representable after history augmentation, at exponential state cost.

The substantive unresolved question is whether the ShiftLab structure admits a compression/approximation theorem for this *two-model* objective that (i) preserves the causal-null reachability guarantee, (ii) accounts for a hard pathwise query cap with pending labels and repeated switches, and (iii) has a nontrivial utility/regret guarantee against the full-history oracle. A risk gate plus FSC planner, robust-verification wrapper, or SCP solver without such a theorem is a standard-method combination and fails the novelty gate.

## Decision

Do not implement a new generic FSC planner or launch efficacy experiments. Keep G1 open, but sharpen the next gate to a source-audited compression or approximation result for the augmented two-model formulation. If no nontrivial structure is available beyond exponential history or standard controller optimization, revise or stop this algorithm hypothesis before G3.
