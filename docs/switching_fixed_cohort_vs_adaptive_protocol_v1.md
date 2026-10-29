# Matched fixed-cohort terminal test versus adaptive causal oracle

**Registered:** 2026-10-28 before implementation. **Purpose:** isolate how much of the certified small-cell value requires contingent acquisition/action timing beyond a randomized fixed cohort and terminal test. This is a structural diagnostic, not a method-efficacy study.

## Frozen cell and contract

Use exactly the certified recurrent-HMM cell: horizon `T=6`, pathwise label cap `B=3`, fixed delay `d=1`, causal-null false-promotion level `alpha=1/10`, query fee `c=1/100`, switch fee `k=1/10`, symmetric transition rates `1/4`, emissions `(1/20,19/20)`, and prior good-state probability `1/2`. The full-history adaptive reference is the saved `CausalSwitchingGame` and independent rational oracle certificate. Promotion risk remains under the causal conditional null; the HMM is used only for alternative economic utility. Historical e-wealth is never interpreted as evidence of benefit after reversal.

## Restricted comparator class

Before observing outcomes, draw a private cohort size `n in {0,1,2,3}`. On that branch, request labels at events `1,...,n`; each request consumes budget immediately and costs `c`, and the fixed delay means all `n` labels are released at the start of event `n+d`. If `n>0`, choose a randomized terminal test based on the full label word, promote at most once at that event, and hold through `T`. The `n=0` branch is no query/no promotion. No contingent acquisition, early action, or rollback is allowed. This class contains arbitrary randomized terminal tests and randomization over cohort sizes, so it is stronger than a fixed likelihood-ratio cutoff. Every branch satisfies the pathwise cap.

Enumerate all endpoint causal-null profiles `p_i(y_{<i}) in {0,1/2}` on the common query prefix. A null conditional probability must be shared across cohort branches until their observable query histories diverge; the private cohort lottery is not revealed at time zero. Impose worst risk over these joint profiles. The alternative HMM tape probability and conditional expected post-decision deployment cost are computed exactly with `Fraction`. Optimize the test LP numerically, rationalize the recovered policy, and verify its exact risk/cost. Rationalize the LP dual and check all dual signs and column inequalities with exact arithmetic, using the fact all primal variables lie in `[0,1]`; report the resulting primal-dual bracket.

## Decision criteria

Report the recovered feasible fixed-cohort policy's exact risk and cost, compare it with the unrestricted adaptive oracle's certified interval, and show the cohort lottery and test probabilities. A gap identifies value of policy-class flexibility in this one cell only; it does not prove a new algorithmic contribution or a general benefit of adaptive acquisition. Equality would not certify the restricted optimum absent an exact dual certificate. The stronger adaptive/sequential-testing prior-art audit remains mandatory.

Run from the repository root with `$env:PYTHONPATH='src;.'; python scripts/compare_switching_fixed_cohort_to_adaptive_oracle.py`. Save exact inputs, source hashes, and rational recovered-policy verification under `outputs/switching_fixed_cohort_vs_adaptive_v1/results.json`.


## Exact result and interpretation

The mixed fixed-cohort class has certified optimal total cost `4626223/1600000` with exact causal-null risk `1/10`. Its optimal plan chooses cohort `n=3` with probability `4/5`, otherwise does nothing, and promotes only on tape `111`. It requests `12/5` labels in expectation while using at most three on every path. The exact primal recovery and an exactly checked rational dual have zero bracket width. An independent forward recursion through `CausalSwitchingGame.expected_metrics` matches the total cost, and `null_risk` matches risk `1/10`. The exact arrays and dual multipliers are stored in `outputs/switching_fixed_cohort_vs_adaptive_v1/results.json`.

The certified unrestricted adaptive oracle is in `[576353749991/200000000000, 461083/160000]`. Therefore the best fixed-cohort terminal-test policy is worse by at least `15393/1600000 = 0.009620625` in this cell. The recovered unrestricted policy spends two early labels conditionally, promotes after two positives, then buys a maintenance label and can roll back; the fixed cohort spends three labels up front and has no rollback. The separation is for the combined policy-class freedoms; it does not attribute the gap to adaptive acquisition, early action timing, or rollback individually.

This is a rigorous one-instance separation from fixed-cohort terminal testing, not a new algorithm. Active sequential testing, delayed economic experimentation, and hidden-Markov optimal switching are established; the result does not compare against a faithful composition of their strongest methods or establish a scalable approximation. The acquisition-and-switching novelty gate therefore remains open. Keep the current-regime HMM forecast separate from causal-null promotion validity; the risk guarantee does not certify future profit after reversal.
