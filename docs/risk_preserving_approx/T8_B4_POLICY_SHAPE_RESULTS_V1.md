# T=8, B=4 adaptive-policy structure verification

The saved full-decomposition policy on the registered largest-gap cell was
reconstructed from its 1,275 pre-promotion information states. A separate exact
behavioral recursion, using the recorded actions but no optimizer or risk-matrix
construction, verifies worst-case causal-null first-promotion risk `1/10`. An
independently coded IID-boundary recursion also gives `1/10`. The verifier's
source and output are preserved in
`t8_b4_policy_shape_verifier_executed_source_v1.txt` and
`t8_b4_policy_shape_verification_v1.json`.

The initially apparent `1/8` versus `1/10` discrepancy came from reading the
policy's aggregate rows as a single promotion rule. Its supported pre-promotion
behavior has two exact paths:

1. Query at events 1, 2 and 3. At event 4, after the first two released labels are
   positive, wait with probability `3/5` or request a fourth label with probability
   `2/5`. On the wait branch, promote at event 5 only after all three labels are
   positive; the event-5 action also requests a label for post-promotion
   continuation. Its IID-null promotion mass is `(1/2)^3 (3/5) = 3/40`.
2. On the fourth-query branch, wait for its delayed release and promote at event 6
   only after all four labels are positive. Its IID-null promotion mass is
   `(1/2)^4 (2/5) = 1/40`.

These masses sum to `1/10`. The exact causal-null recursion also maximizes over
history-adaptive endpoint responses (`0` or `1/2`) with hidden pending labels and
returns `1/10`; this is the relevant robust-risk check. The query at event 5 in
the first branch occurs with first promotion, so its outcome affects subsequent
economic continuation but not the already-determined promotion event.

The optimizer-recorded alternative cost remains
`1666179899873/488281250000`; this risk verifier does not independently recompute
the post-promotion economic continuation. In the registered comparison, the best
calendar costs more by `11126044659/976562500000`. This identifies adaptive,
label-conditioned reservation of the final query as the mechanism behind the
instance-level gap, but does not establish a new algorithm or general guarantee.
Randomized sequential sample-size allocation, futility/continuation boundaries
and alpha spending are direct prior-art comparisons; novelty remains unresolved.

No real observations, holdouts or new seeds were accessed. This is a descriptive
policy verification on a development cell, not an independent efficacy result.
