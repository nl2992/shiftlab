# Registered causal-oracle reversal diagnostic

2026-10-28. Register before execution. This is one targeted known-model oracle diagnostic, not
a candidate-method efficacy study or a parameter sweep.

## Motivation and fixed cell

The completed `T=5,B=2,d=2` causal-game oracle was later matched exactly by a randomized
fixed-cohort rule with one promotion and no rollback. It therefore does not reveal whether
repeated reversal has value when regimes turn over during the horizon. Test one deliberately
reversal-relevant cell with `T=6`, `B=3`, `d=1`, `alpha=1/10`, `c=1/100`, `k=1/10`,
`transition01=transition10=1/4`, emissions `1/20` and `19/20`, and initial regime probability
`1/2`. The conditional null, causal opponent information, pending-label reservation and action/query
choice set remain exactly those of `CausalSwitchingGame`.

## Registered comparison

Solve the all-randomized sequence-form oracle under the hidden Markov working alternative and
causal conditional null. Compare its independently reevaluated cost and five metrics with this
fixed-cohort reference: activate with probability `4/5` before any outcomes; on active paths query
events 1, 2 and 3; at the start of round 4, promote iff all three labels are positive; never
rollback; inactive paths stay at 0 and issue no queries. Under every conditional null each of
three positives has probability at most `1/2`, so the unconditional promotion risk is at most
`(4/5)(1/2)^3=1/10`. The pathwise query cap is three. Independently compute its risk with the
causal-null verifier and its alternative metrics with the forward evaluator.

The diagnostic is informative only if the all-policy oracle differs in expected cost or
switching behavior from this simple cohort, with solver residuals and risk verification passing.
If the cohort matches, record another no-go for contingent acquisition/reversal as the source of
a contribution in this small known-model regime. If the oracle improves, treat that as evidence
that the restricted cohort leaves value in the model, not as novelty: compare the structure with
standard constrained POMDP/sequential design before developing an approximation. Stop at the
existing `200,000` node guard or solver's `60s` limit; preserve resource failure without tuning
or shrinking the cell.

Reproduce with `python scripts/solve_switching_reversal_diagnostic.py`. Save full report and
policy to `outputs/switching_reversal_diagnostic_v1/`. No additional cell is authorized by this
registration. Synthetic efficacy, fresh-seed confirmation and real-data runs remain gated on a
surviving algorithm and theorem.

## Pre-registered follow-up: optimize the fixed-cohort baseline

The first run beats the registered three-positive cohort by only `15393/1600000` cost units.
Before interpreting this difference, solve the stronger fixed-cohort frontier on the *same* cell.
Allow an independent upfront lottery over `n=1,2,3` consecutive queries at events `1,...,n`,
with a randomized terminal promotion test on the complete binary word at time `n+d`; after a
rejection, remain at 0, and after promotion, remain at 1. Include the no-query/no-promotion plan.
Optimize expected model cost subject to the same alpha risk under every depth-3 causal null
strategy. Since the chosen `n` is initially private but becomes inferable from the public query
continuation, risk constraints must use a single common null strategy on the shared queried-prefix
tree, not independent IID calibrations or a separate alpha allowance for each cohort.

Use variables `w_n` for cohort-lottery mass and `z_(n,y)` for unconditional cohort-and-promotion
mass after word `y`, with `0<=z_(n,y)<=w_n` and `sum_n w_n<=1`. For every pure causal null strategy
that chooses each queried label's success probability in `{0,1/2}` as a function of its past
queried outcomes, impose `sum_(n,y) P_sigma(y[1:n]) z_(n,y)<=alpha`. Maximize alternative expected
cumulative gain minus switching and query costs, using the exact hidden Markov working model.
Enumerate all `2^(2^3-1)=128` endpoint strategies. Recover a rounded policy and independently
recompute its worst null risk over those strategies; if rational rounding exceeds alpha, mix it
with the no-query/no-promotion plan and report the value change.

This comparison can decide whether the first oracle/cohort gap survives a strong optimal
fixed-sample comparator. It does not include outcome-contingent stopping or rollback and is not
a new algorithm. Preserve the same resource limits; do not add another alternative-model cell.

## Pre-registered follow-up: separate adaptive acquisition from rollback

The robust fixed-cohort LP still matches the original cohort and leaves a small lower cost for the
full oracle. Before interpreting that delta, solve the same `T=6` causal game with the *same*
known alternative and null, but restrict deployed actions to be absorbing after first promotion
(`1` can never return to `0`). Keep query decisions adaptive to all currently released labels and
allow queries after promotion. Reuse the same `200,000` node and `60s` limits. Compare this
no-rollback adaptive-query policy with both the unrestricted numerical oracle and the robust
fixed-cohort frontier. The difference between no-rollback and fixed cohort isolates value
available to outcome-contingent acquisition/decision timing; the further difference between the
unrestricted and no-rollback policies isolates rollback's incremental value in this exact cell.

Use the existing `CausalSwitchingGame` information, risk and cost semantics. Implement the action
restriction as a separate subclass for this diagnostic; do not modify the production reference.
Require residuals within the existing tolerances and independently verify recovered policy null
risk by the game's causal endpoint best response. This is a source-guided development comparison,
not a new algorithm or a theorem. Do not add another parameter cell.

## Executed result and interpretation

All three same-contract calculations completed. The unrestricted and no-rollback sequence-form LPs
had zero reported equality residual and inequality violation; their recovered policies had exactly
`1/10` causal-null risk under the independent endpoint response. The fixed-cohort LP considered all
three cohort sizes and all randomized terminal tests under 128 common causal-null strategies; its
rationally recovered policy also had risk exactly `1/10` and required no safety scaling.

The strongest fixed-cohort frontier uses an upfront `4/5` activation, requests all three labels,
and promotes at round 4 only after three positives. The adaptive-query, no-rollback oracle recovers
the same promotion law but stops querying after the first nonpositive label. Its compact rule has
exactly the same decision and switch costs as the fixed cohort while lowering expected queries
from `12/5` to `1481/1000`; total cost falls from `4626223/1600000` (`2.891389375`) to
`4611519/1600000` (`2.882199375`). This accounts for a `919/100000` saving entirely through
avoided query charges.

The unrestricted oracle activates with probability `2/5`, queries again after a positive first
label, promotes after two positives at round 3, queries once at round 4 while policy 1 is deployed,
and rolls back at round 5 if that maintenance label is negative. The distilled rule independently
matches all five recovered metrics and causal-null risk exactly. Its total cost is
`461083/160000` (`2.88176875`), only `689/1600000` (`0.000430625`) below the no-rollback
adaptive policy. The extra query/reversal choice increases expected decision cost by
`0.007543125`; its query savings and reduced switch cost offset most of that amount.

The false-promotion checks have a simple conditional-null proof: after an independent activation
coin, promotion requires two (or three) adaptively requested positive labels. Since every queried
label has conditional success probability at most `1/2`, the promotion risks are at most
`(2/5)(1/2)^2=1/10` and `(4/5)(1/2)^3=1/10`. The later maintenance query occurs after the first promotion and cannot increase the event probability of *any* promotion. Exact risk recursion confirms both values.

This cell shows contingent early stopping can save query cost, but sequential sampling, randomized
test allocation and post-adoption monitoring/rollback are established approaches in the audited
controlled-sensing, sequential-design and intervention literature. The benefit is small in the
chosen model, the oracle assumes its hidden Markov alternative is known, and the comparison is
only one finite development cell. It supplies neither a novel rule nor a theorem-level separation.
Decision: **reject generic contingent querying plus rollback as the contribution**. Do not expand
this cell or start efficacy/real-data runs. G1 remains unresolved; revise the research hypothesis
only around a precise theorem that survives the existing active-testing and constrained-planning
baselines.

Numerical-solver caveat: HiGHS supplied the sequence-form and fixed-cohort LP solutions with zero
reported primal residual/violation, but no exact rational optimality certificate was constructed.
The displayed rational costs and risks are exact evaluations of recovered feasible policies. Treat
the solver objective as a numerical oracle estimate, and do not describe the small cost differences
as certified exact gaps between globally optimal policy classes.
