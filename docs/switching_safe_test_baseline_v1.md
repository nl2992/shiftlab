# Delayed e-process plus hard-cap acquisition: safe baseline composition

**Date:** 2026-10-28. **Status:** elementary baseline theorem; no novelty claim and no regret guarantee.

## Contract

Let `Z_t = l_t(0)-l_t(1)` lie in `[-1,1]`. Query decision `Q_t` is made before observing `Z_t`, may depend on the available history and a fresh private coin, and obeys `sum_t Q_t <= B` on every sample path. A queried `Z_t` is released at event time `t+d` for known fixed `d >= 1`; unqueried and unreleased outcomes are not in the decision filtration. Assume the conditional null

    E[Z_t | F_(t-1), C_t, Q_t] <= 0

for every `t`, where `C_t` is any current covariate revealed before querying and `F_(t-1)` is the full event-time history before that covariate and the query coin. This permits context-based queries and is stronger than conditioning only on previously observed labels. Fixed delay preserves the order of queried events at their release times.

For fixed `lambda` in `(0,1]`, initialize `E=1`. On each queried label release, update

    E <- E * (1 + lambda * Z_t).

Hold `E` constant at other times. During promotion episode `j`, promote from model 0 to model 1 at the first release with `E >= 1/alpha_j`, where `alpha_j > 0` and `sum_j alpha_j <= alpha`. After a rollback, start a fresh process for the next episode and include only queries initiated in that episode; exclude labels from requests already pending at episode start. The query policy may use all arrived labels and pending-request metadata, but it must not use unreleased `Z_t` values.

## Guarantee

Under the stated null, the event-time process

    M_t = product over s <= t with Q_s=1 of (1 + lambda * Z_s)

is a nonnegative supermartingale: conditional on the full history, current covariate and query choice,

    E[1 + lambda Z_t | F_(t-1), C_t, Q_t=1] <= 1.

Predictable skipping leaves the process unchanged. Because fixed delay preserves query-event order, every threshold crossing computed from released labels is also a crossing of `M_t` at the event time of the last released label in that prefix. A promotion therefore implies `sup_t M_t >= 1/alpha_j`. Ville's inequality gives

    P(any promotion in episode j | history at episode start) <= alpha_j.

Summing over episodes yields

    P(exists t: A_(t-1)=0 and A_t=1) <= sum_j alpha_j <= alpha.

The bound holds for every adaptive acquisition rule satisfying the conditional null, and any pathwise query budget `B`; budget feasibility is enforced by the query policy itself. Delayed arrivals do not inflate type-I error under this fixed, order-preserving release rule. No distributional model for the alternative is used.

For the simple Bernoulli alternative `Y_t~Ber(1/2+epsilon)` with `Z_t=2Y_t-1`, choosing
`lambda=2*epsilon` makes the factor `1+lambda*Z_t` exactly the likelihood ratio of that
alternative to the boundary null `Ber(1/2)`. This is the information-matched simple-alternative
baseline; the coefficient is not a new betting rule. More generally, to avoid an old evidence
product suppressing a late change, start one such process at every candidate onset and mix them
with fixed weights summing to one. Under the event-time conditional null, this mixture is again
a nonnegative supermartingale. Thresholding at `1/alpha` controls the probability of any false
promotion. Under fixed delay, the released labels are an event-time prefix, so the visible mixture
is the same event-time mixture at the last released event. This is the standard e-detector
construction audited in [`switching_change_point_safe_baseline_v1.md`](switching_change_point_safe_baseline_v1.md);
it handles late changes at the detection layer but does not optimize query allocation or
deployment economics.

## What the composition does not establish

The result says nothing about how quickly evidence arrives, whether promotion has positive future net value, expected decision regret, query optimality, or rollback quality. The allocation `alpha_j` can make later promotions arbitrarily conservative. It does not solve the economic acquisition problem. A separately valid rollback test under the opposite null is also insufficient to give a dynamic regret bound. Therefore “hard-cap predictable sampling + delayed e-process + alpha spending” is a baseline composition, not the contribution sought.

The repo already contains standard delayed Hedge and exact causal finite-game references, but neither combines a dynamic-comparator regret theorem with this risk guarantee. A candidate algorithm must beat the best relevant composition on economic performance under matched `B,d,c,k`, horizon knowledge, and the same alpha event. A claimed gain must survive the unavoidable delay lower bound in `switching_problem_v1.md`.

## Proof details

For each queried event initiated within an episode, `1+lambda Z_t >= 0` and its conditional expectation is at most one after conditioning on the full event-time past, current covariate and query choice. Define the product process in event time, multiplying by one when no query is made. This is a nonnegative supermartingale starting at one. The proof does not assert that it remains a supermartingale in the larger arrival-time filtration: intervening covariates could reveal information about an unreleased `Z_t`. Instead, fixed delay preserves the order of query events, so every released-prefix product used for promotion is one of the event-time products `M_t`. A promotion is contained in the event-time event `sup_t M_t >= 1/alpha_j`, which Ville bounds.

For example, let `Z_1` be a fair sign, query it at round 1, set delay `d=2`, and reveal `C_2=Z_1` before the label's release at round 3. Under the event-time null, `E[Z_1]=0`; the event-time process `1+Z_1` is valid. But at its round-3 release, conditional on the already observed `C_2`, its value is known to be either 0 or 2, so it is not a supermartingale increment in that enlarged arrival filtration. The crossing-probability argument above remains valid because the promotion event is still a subset of the event-time maximum. If release order were allowed to reorder labels based on outcomes, that subset argument would fail.

At a promotion, the current episode ends. A later rollback starts a new episode; only requests made after that episode begins enter its test, so no pre-episode outcome is reused as if it were a future increment. The episode start is a stopping time for the full event-time filtration because the decision is made using only already released labels and observed covariates. Conditional on the full event history at that time, future factors still satisfy the null; conditional Ville bounds the episode's event-time crossing probability by `alpha_j`. A union bound over the (possibly random) episode index is justified by summing `P(episode j promotes) <= alpha_j`; pad a finite horizon with inactive episodes if needed. The pathwise query cap is orthogonal: none of these inequalities assumes a particular number or timing of the predictable queries.

This proof does not cover informative or outcome-dependent release ordering: an arrival prefix may then be a non-prefix subset of event-time queries, and its product need not be bounded by the event-time maximum. Such a design needs a valid arrival-time e-process or an explicit censoring model. Nor does the proof validate conditioning on current covariates or the query coin unless the null is stated to include them as above.
