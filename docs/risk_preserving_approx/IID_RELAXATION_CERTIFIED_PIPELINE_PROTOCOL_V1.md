# IID-relaxation, exact-null certification and repair

Registered 2026-10-29 before execution. This is a bounded Candidate B development
test on the previously registered largest-gap cell: T=8, B=4, d=2, alpha=1/10,
query cost=1/100, switch cost=1/10, symmetric transition=1/10,
emissions=(1/50,49/50), prior=1/2. It uses no seeds, real rows or holdouts.

## Candidate procedure

1. Build the exact pre-promotion learner tree and alternative-HMM economic
   continuation costs, but omit the strategic null-player tree from optimization.
2. Add one risk row for the IID fair-label null, which is a member of the full
   causal-null family. Solve the resulting LP. Its optimum is a lower bound on the
   original robust optimum because it relaxes the risk constraint.
3. Recover the LP policy and evaluate its exact alternative cost and its full
   history-adaptive causal-null first-promotion risk. If risk exceeds alpha, mix
   with the never-query/never-promote policy at activation probability
   `min(1, alpha/R)`.
4. Compute an exact rational lower bound from the LP dual, correcting any rationalized
   dual residual. Compute the repaired policy's exact alternative cost and exact
   robust risk. The interval `[lower, repaired_cost]` is the certified gap to the
   unrestricted robust optimum when both ends verify.

The lower-bound direction is: robust-feasible policies are IID-risk-feasible, so
the IID-relaxed minimum cannot exceed the robust optimum. The repaired upper-bound
direction uses the full adaptive-null verifier, not the relaxed risk row. If exact
dual verification or exact feasible-policy verification fails, report no certified
gap.

## Frozen comparisons and measurements

Read the already registered comparison artifacts for the full decomposed
reference, all calendars, cap/e-process policies and the finite calendar portfolio.
Compare against the best calendar and the full decomposed reference in this cell.
Report raw IID-policy cost/risk, robust risk, activation, repaired cost/risk,
certified lower/upper/gap, LP learner variables/equalities/risk rows, opponent
variables (zero in the relaxed master), learner-tree builder nodes, verifier
states/nodes, solve/verification time, and peak process memory when available.

The method passes this screen only if the exact repaired policy is alpha-safe, the
dual lower certificate is valid, the resulting value gap is nonvacuous and useful
relative to the best calendar, and total resource use improves on the robust
reference. A zero or small gap on this single cell does not establish a general
approximation theorem, novelty, synthetic efficacy across a test family or real
data performance. If it fails, preserve the candidate and continue to the next
mathematically justified mechanism.
