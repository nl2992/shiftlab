# T=8, B=4 branchwise monotonicity verification

Registered 2026-10-29 before execution. This is a one-cell exact structural
verification of the saved full-decomposition policy, not a new efficacy grid or
algorithm claim. It uses the registered largest-gap cell: T=8, B=4, d=2,
alpha=1/10, query fee=1/100, switch fee=1/10, symmetric transition=1/10,
emissions=(1/50,49/50), prior=1/2. Input policy:
`t8_b4_policy_shape_v1.json`.

The saved behavior has one randomized pre-promotion information state: after
queries at events 1, 2 and 3, if labels 1 and 2 are both positive, wait at event 4
with probability 3/5 or query a fourth label with probability 2/5. Construct two
deterministic branch policies by forcing each action at that information state and
leaving every other recovered action unchanged. Use the exact alternative
continuation policy for post-promotion decisions.

Before evaluating risk, enumerate all 2^8 potential-label tapes for each branch.
Verify the pre-promotion policy is deterministic, pathwise queries never exceed
four, and the first-promotion indicator is coordinatewise nondecreasing in all
eight tape bits. Record every monotonicity violation if any. Independently compute
the IID fair-tape risk and the worst-case causal-null risk under the full-history
endpoint recursion with hidden pending labels. Evaluate exact alternative cost and
all five expected metrics for each branch and the saved behavioral mixture. Check
that branch costs combine with weights 3/5 and 2/5 to the saved policy cost, and
that the exact mixture risk is 1/10.

Expected structural check: if each deterministic promotion event is monotone,
coordinatewise coupling implies its worst-case null risk equals the IID fair-tape
risk. The branchwise risks need not individually be at most alpha; only their
publicly branchable mixture is required to satisfy alpha. A monotone *marginal*
event alone is not accepted as a certificate. This experiment does not optimize
over the branch class, prove the class is near-optimal beyond this saved policy,
or establish novelty. No seeds, real data, or holdouts are accessed.

Fail the check on any mismatch, nondeterministic branch action, pathwise budget
violation, nonmonotone tape event, or exact metric/risk disagreement. Save outputs
to a unique JSON result without changing the saved policy or any earlier artifact.
