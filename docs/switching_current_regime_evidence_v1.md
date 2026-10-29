# Historical test evidence and current-regime value

**Date:** 2026-10-28. **Status:** elementary limitation and design contract; not a novelty claim.

## Separate the claims

The safe-test baseline in [`switching_safe_test_baseline_v1.md`](switching_safe_test_baseline_v1.md)
controls the probability of any promotion under its global conditional no-benefit null. Its
likelihood-ratio/e-process wealth is evidence against that null, accumulated from the queried
outcomes in the current test episode. That validity statement is not a certificate that the
challenger is beneficial now, will remain beneficial, or will recover its switching cost over a
future horizon. In particular, evidence earned in a positive regime is not evidence about the
sign of a regime that begins after the last observed label.

## Nonidentifiability after an unconstrained reversal

Fix any history available at a decision time `tau`, including all delayed labels released by then.
Construct two environments with exactly the same distribution over that history and the same
future covariates and query outcomes up to `tau`. After `tau`, let paired gain be deterministic:
`Z_t=+Delta` in environment `P+` and `Z_t=-Delta` in `P-`, for `H` rounds, where
`0 < Delta <= 1` and `H Delta > k`. Use the convention that switching to policy 1 costs `k`.
The expected incremental net value of switching and keeping policy 1 throughout this horizon is
`H Delta-k` under `P+`, and `-H Delta-k` under `P-`.

Any decision or forecast based on the time-`tau` information has the same distribution in both
environments. Thus no such rule can guarantee the correct sign of future net value uniformly:
for a binary sign decision, the two error probabilities sum to one, so at least one is at least
`1/2`. This remains true if an anytime-valid test has accumulated arbitrarily large wealth from
earlier positive outcomes. The worlds diverge only after `tau`, outside the evidence used by that
test. The statement is an identifiability argument, not a lower bound specific to a new algorithm.

Delayed feedback sharpens the operational point: immediately after an unannounced reversal,
several actions may be taken before any post-reversal label is released. A promotion test can
remain valid for its declared null while its historical wealth is stale for deployment decisions.
The existing delay lower bound in [`switching_problem_v1.md`](switching_problem_v1.md) quantifies
unavoidable loss in that interval.

## Consequence for the research contract

Keep three objects distinct in every method, theorem, and table:

1. **Promotion validity:** a time-uniform bound on false promotion under a stated global or
   episode-local null. A fresh episode test must not recycle outcomes collected before that
   episode; episode-local validity also needs a valid predictable start and alpha accounting.
2. **Current-regime evidence:** post-change observations or a forecast model whose assumptions
   connect those observations to the current regime. Old e-wealth alone does not provide it.
3. **Future economic value:** a claim about cumulative gains after switching, which requires an
   explicit persistence, dwell-time, or drift assumption. Under arbitrary abrupt changes the
   nonidentifiability argument above rules out a uniform positive-value certificate.

Any continuation should either state and defend a regime-persistence/drift contract, or target
realized dynamic regret with a comparator and accept the unavoidable feedback-delay penalty.
An empirical method that uses evaluator-known post-switch outcomes to label a promotion harmful
may measure future utility, but those outcomes must remain hidden from the learner and cannot be
presented as evidence available at promotion time.

## Decision

This clarification does not reopen algorithm selection or authorize a new efficacy sweep. It
closes the interpretation gap in the safe-test composition. The next theory step remains the
matched risk-regret frontier against budgeted delayed switching and constrained sequential design.


### User annotation checkpoint — 2026-10-28

The likelihood-ratio gate has a deliberately narrow interpretation: it controls false promotion under its declared fixed null. Accumulated evidence from a beneficial regime does not certify benefit after an unobserved reversal. In any future implementation, separate the promotion-validity process from current-regime forecasts/evidence; do not reuse historical e-wealth as a current-value certificate. This clarification is part of the active research contract, not a claim that an algorithm has been selected.
