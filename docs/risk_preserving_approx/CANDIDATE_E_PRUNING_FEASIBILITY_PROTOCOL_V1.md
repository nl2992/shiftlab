# Candidate E safe-history pruning feasibility screen

**Registered:** 2026-10-29 before the tree-size screen. This is one bounded
development-only structural calculation on an already exposed synthetic cell.
It does not solve the pruned optimization problem and cannot pass G1–G3.

## Frozen case and thresholds

Use the registered T=10/B=4/d=2 low-persistence, high-separation case from
`IID_RELAXATION_T10_STRESS_PROTOCOL_V1.md`: symmetric transition `1/10`,
emissions `(1/50,49/50)`, prior `1/2`, `alpha=1/10`, query fee `1/100`, switch
fee `1/10`. Build a fresh in-memory exact reference tree, with its registered
200,000-node cap. Do not solve any LP, use any policy outcome, or access any
real or reserved data.

Inspect pre-promotion information histories at decision events `t in {5,6,7,8}`.
For a history `h`, compute its exact alternative probability envelope `p_h` by
summing the HMM probability of its released-label transcript over hidden pending
outcomes, conditional on its fixed public action/query history; learner action
probabilities are omitted and bounded by one. For each depth independently,
sort histories by `p_h` ascending and select the largest prefix whose sum is at
most `delta / (L*(T-t+1))`, for each fixed loss budget
`delta in {1/100,1/20}` and `L=111/100`. Histories at one depth form an antichain.

For each selected set, report the exact envelope sum, resulting theorem loss
bound `L*(T-t+1)*sum(p_h)`, number of collapsed information sets and realization
columns, and fraction of the full pre-promotion realization columns removed. A
collapsed set receives the fixed incumbent/no-query continuation; never inspect
the null policy's hidden pending outcomes when selecting actions. Hash source,
protocol and reference configuration. Preserve output at
`docs/risk_preserving_approx/candidate_e_pruning_feasibility_v1.json` and refuse
to overwrite it.

## Decision rule

Do not implement a solver if at every depth and both budgets the maximum
prunable realization-column fraction is below 5%, or if evaluating the
policy-independent envelope required building essentially the full information
tree. A pass only authorizes a separate preregistered ablation that measures
end-to-end tree-construction and solve resources, exact full-null risk, and
exact oracle cost. It does not establish novelty; the source audit must compare
against RAO* chance-constrained branch pruning and POMDP hypothesis-pruning
value bounds first. No threshold tuning, new seeds, holdouts, T=8/T=6 reruns, or
real data are in scope.
