# Recurrent-regime lower-bound screen: episode floors do not add automatically

**Date:** 2026-10-30. **Status:** derivation screen; no new lower bound or algorithm.

## Question

Can the one-reversal budget/delay/safety lower bound be extended to arbitrary recurrent regimes
by summing its per-episode information floor, thereby exposing a new limitation for safe model
switching?

## The tempting but invalid step

For a single post-reversal interval, the binary-KL argument in
[`switching_noisy_information_lower_bound_v1.md`](switching_noisy_information_lower_bound_v1.md)
compares a no-benefit law with a law that differs after one onset. It bounds promotion by the
information in post-onset labels released so far. Applying that bound separately to each of `m`
intervals and adding the `m` answers is not valid: the `m` applications use different pairs of
probability laws. They do not establish one joint distribution under which the learner must incur
all `m` losses.

There is a direct counterexample to an automatic additive query requirement. Let a finite regime
type `S` be drawn once at the beginning, let queried labels reveal `S`, and let a known public
clock or observed context reveal which recurrent episode is active. Conditional on `S`, the
episode payoffs repeat according to that public schedule. After one informative label (including
its release delay), the learner can reuse the inferred type in every later episode; subsequent
episodes do not each require fresh information. The path may have arbitrarily many reversals,
yet summing a one-episode label floor would incorrectly charge the same information repeatedly.
This construction is within broad recurrent-regime descriptions unless fresh episode innovations
or hidden episode timing are imposed.

The opposite construction, with an independent hidden sign newly drawn at every episode and no
revealing context, can require fresh information repeatedly. But deriving its minimax cost is a
multiple-change problem: the proof must compare a *single joint recurrent alternative* against a
joint null, account for reuse and pending labels, and allocate one global promotion-risk event.
The episode count alone does not give that theorem. Piecewise-stationary dynamic-regret and
detection-augmented-learning results are already close baselines; the repo's
[`switching_dal_prior_audit_v1.md`](switching_dal_prior_audit_v1.md) and
[`switching_finite_horizon_qcd_budget_delay_audit_v1.md`](switching_finite_horizon_qcd_budget_delay_audit_v1.md)
record their theorem scopes and the remaining hard-cap/delay gaps. Those gaps are comparison
obligations, not novelty evidence.

## Decision and reopening test

Reject “sum the one-reversal floor over recurrent episodes” as a theorem or method claim. Do not
use it to motivate an efficacy experiment. A valid multi-episode lower bound would need, at minimum:

1. one registered joint family of recurrent alternatives and a single causal-null family;
2. explicit dependence (or conditional independence) of episode innovations, plus whether regime
   identity/timing is observable from free context;
3. one transcript-level KL calculation that counts each queried label once, including delayed
   releases and any information reusable across episodes;
4. a single global false-promotion event and an explicit dynamic comparator; and
5. a strict separation from the applicable multi-change, delayed-budget, and safe-testing
   baselines, rather than only from the one-change bound.

No current repo result passes this test. This closes one possible restatement of the G1 question;
it does not close the overall research objective. Keep G2–G5 held and retain the distinction
between historical promotion validity and current-regime evidence after reversal.
