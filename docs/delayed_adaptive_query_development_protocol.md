# Delayed feedback with predictable variance-adaptive querying: development protocol

**Status:** frozen development screen; not a confirmatory experiment. The question is whether a simple history-adaptive acquisition heuristic remains useful when its state can use only labels that have arrived and entered the resolved event prefix.

## Design

The simulator pairs a source period of 1,000 observations with a target period of 3,000 events. The three target scenarios are stationary zero-mean paired-cost contrast, a benign variance decrease beginning at 40% of the target horizon, and boundary-local decision harm beginning at 40%. The latter increases the target mean paired contrast by 0.12. Contrasts are bounded by the registered amplitude 0.60. Each queried label has an independent discrete-uniform delay from 0 through 12 events. CUDA is used for synthetic tensor generation when available; evidence updates and event-order buffering are evaluated on CPU.

The two paired acquisition policies use the same per-event query uniforms. Uniform querying uses propensity 0.25. The variance-adaptive heuristic estimates recent second moment from the last 64 queried labels released through the contiguous event prefix. After at least eight labels, its propensity is `clip(0.25 * sqrt(recent_second_moment / source_second_moment), 0.10, 0.40)`. The current event's label and any pending or out-of-order label are unavailable to the propensity choice. This predictable Neyman-style allocation is an established class of design heuristic; no novelty or optimality claim is made.

For each event, the monitored increment is `Q_t (Z_t - epsilon) / q_t`, where `epsilon=0.02`, `Q_t` is the randomized query indicator, and `q_t` is the logged propensity. The per-event absolute support bound is `(0.60 + epsilon + numerical_slack) / q_t`. A history-conditional null `E[Z_t | G_t] <= epsilon` and a propensity chosen from `G_t` before the query coin imply a nonpositive conditional mean for the increment. The event-specific bound must also be predictable in that same filtration. A nonnegative bounded-mean e-process is updated only when the contiguous resolved event prefix advances; the arrival-time alarm can only be a crossing of this event-time process. Correct event identity and eventual resolution are assumed. Delays and non-arrival are not used as evidence.

## Outcomes and analysis

The stream-seed is the inferential unit. Report alarm rate and event/wall-clock delay for boundary harm; alarm rate on stationary and benign-variance controls; labels queried and realized mean propensity for every scenario; and paired adaptive-minus-uniform differences by seed. This is a development screen, so intervals are descriptive and do not constitute calibration, confirmation, or a method-selection gate. Label counts are reported directly: both policies have the same expected nominal rate only at initialization, and the adaptive rule can have a different realized and expected query cost as its state changes.

Integrity checks require one row per scenario, seed, and policy; propensities in `[0.10,0.40]`; all 3,000 event increments released by the end of the finite simulation; no duplicate or missing keys; finite metrics; and a manifest with configuration, code hash, runtime, output row count and grouped metrics. No figure is planned.

## Limitations and next gate

The result is limited to this bounded synthetic generator and the stated history-conditional null. It does not cover non-random missingness, query-dependent outcomes, model updates, budget-constrained stopping, or policy-induced outcomes. The simulator's finite null behavior cannot replace the e-process argument. A separate null-calibration protocol and disjoint-seed confirmation are required before retaining the heuristic. If detection gains are purchased only by more labels or increased false escalation, stop the branch or compare under an explicitly matched hard budget. No literature novelty claim follows from this screen.
