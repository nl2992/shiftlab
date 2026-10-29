# G1 candidate: promotion and reversal-monitoring budget frontier

**Date:** 2026-10-29. **Status:** theorem target and no-go screen; no algorithm or novelty claim.

## Why this is the next narrow test

The registered failures include both late harmful shifts and losses before rollback. Prior audits
already close generic delayed CUSUM, controlled sensing with observation-switching costs, safe
promotion tests, and finite-horizon two-law planning separately. The remaining plausible interaction
is whether a single hard query budget should be split between *earning permission to promote* and
*retaining the ability to detect a later economic reversal*, while one global causal-null event
controls false promotion. A pre-promotion e-process cannot serve as current-value evidence after a
reversal. This candidate keeps promotion wealth and post-promotion economic likelihood evidence as
separate state variables.

## Exact local lower bound

Consider a post-promotion monitoring episode with a no-reversal observation law `P0` and a
post-reversal law `P1`. Each query reveals one binary paired outcome after fixed delay `d >= 1`.
Assume `0 < kappa < infinity` and `beta < 1-gamma`. Conditional on every common past, the KL
divergence of one queried post-reversal outcome is at most `kappa`; pre-reversal outcomes have the
same law in both worlds.
Queries are predictable from released data, at most one may be requested per round, and at most
`R` query rights are reserved for this episode. Let `sigma` be the rollback time. Suppose that for
every horizon `n`, the probability of rollback by `n` under no reversal is at most `beta`, while
after a reversal at time zero the probability of rollback by time `n` is at least `1-gamma`.

For the event `A_n = {sigma <= n}`, data processing and the chain rule give

`kl(1-gamma || beta) <= KL(P1^(n) || P0^(n)) <= kappa * E1[N_n] <= kappa * min(R, max(0,n-d+1))`,

where `N_n` is the number of post-reversal queried labels released by time `n` and
`kl(a||b)=a log(a/b)+(1-a)log((1-a)/(1-b))`. Thus no policy can meet these two rollback
requirements unless

`R*kappa >= kl(1-gamma || beta)`

and, for a finite detection deadline,

`n >= d - 1 + ceil(kl(1-gamma || beta)/kappa)`.

The result is a standard information lower bound specialized to delayed, capped observations. It
does not prove a new algorithm or a promotion theorem. It also does not apply unchanged if the
pre-reversal and post-reversal laws are not specified, if KL is unbounded, or if the false-rollback
requirement is replaced by an expected economic-loss objective without a probability guarantee.

## Novelty gate and required comparison

The algorithmic candidate is a **joint allocation rule** for the remaining query rights: it may
spend a label on a not-yet-promoted candidate under the anytime causal-null promotion test, or
preserve/query a post-promotion reversal monitor. It must optimize the expected cumulative
alternative utility and switching cost, satisfy the global any-false-promotion probability at most
`alpha`, and state a rollback false-alarm/loss criterion. The deployment-value forecast and current
reversal likelihood must use post-promotion evidence; the promotion e-process is not reset into a
claim of current benefit.

The mandatory null hypothesis is that this reduces to separately allocating `B_P` queries to a
standard anytime-valid promotion procedure and `B-B_P` queries to a standard delayed CUSUM or
Bayesian change monitor, then selecting `B_P` by a one-dimensional search. Compare that split
against the full two-law sequence-form oracle on growing, registered instances and against the
strongest source-matched CUSUM/controlled-sensing baselines. A theorem must show a strict joint
frontier improvement or a scalable approximation bound over this separable composition, under
the same information, delay, hard-budget, switching and risk contract. Merely reserving queries,
running two tests, or restating the information lower bound fails G1.

The small exact cell is a diagnostic, not evidence of a growing result. Before any efficacy study,
derive the joint recursion and test whether it collapses to the separable budget split or standard
constrained POMDP planning. If it does, record a no-go and revise the hypothesis. G2-G5 remain
held until this comparison establishes a real delta.

## Sources used for the prior boundary

- The repository's source-level audit of Lau and Tay covers adaptive sampling and GLR-CUSUM under
  average observation-switching cost: [`switching_observation_switching_qcd_audit_v1.md`](switching_observation_switching_qcd_audit_v1.md).
- The repository's audit of anytime-valid promotion tests records why promotion evidence does not
  certify current benefit after reversal:
  [`switching_robust_sequential_testing_prior_audit_v1.md`](switching_robust_sequential_testing_prior_audit_v1.md).
- The exact two-law small-game oracle and its exponential generic sequence-form representation are
  recorded in [`switching_two_law_game_duality_v1.md`](switching_two_law_game_duality_v1.md).

## Registered small-cell result: no joint-allocation gain

The existing registered `T=6, B=3, d=1` recurrent-HMM cell already provides a decisive first
screen. Its full-history two-law optimum is certified in
[`switching_reversal_lp_certificate_v1.md`](switching_reversal_lp_certificate_v1.md) to lie in
`[2.881768749955, 2.88176875]`. The independently risk-checked feasible policy in
[`switching_two_component_fsc_lp_v1.md`](switching_two_component_fsc_lp_v1.md) uses no more than two
queries before its first promotion and one query after promotion for rollback; its exact cost is
`461083/160000 = 2.88176875`, with causal-null promotion risk `1/10`. It is therefore feasible in
the split class `(B_P,B_R)=(2,1)`. Since the full-game lower bound applies to every policy, the
best policy in that split class is bracketed by the same interval. Joint allocation does not
improve the split on this cell, to a certified tolerance below `4.5e-11`.

This is a no-go for claiming a joint-allocation advantage from the registered small cell. It does
not establish equality on a growing family. A continued test must strengthen the comparator from a
fixed `(B_P,B_R)` pair to an adaptive, history-dependent partition whose continuation policy sees
the promotion history, current economic belief, pending labels and remaining query rights. If the
full two-law recursion is just this Bellman composition on growing instances, reject this candidate
as a method and revise G1. The policy's promotion risk certificate still says nothing about current
benefit after reversal.

## Exact adaptive-allocation equivalence (candidate closure)

Let a feasible policy observe the same queried paired labels, under the same fixed-delay queue,
request-time hard cap, actions, switching costs and global causal-null promotion event. Consider an
augmented implementation that assigns each query an internal purpose tag `Z_t` in
`{promotion, rollback}` and may change that tag based on the learner's released history. If the
label is available to both evidence processes, the tag changes no observation, transition, reward,
query charge or risk event. Erasing tags maps every tagged policy to a feasible policy of the
original two-law game with identical pathwise actions, query times, released information,
alternative cost and null promotion probability. Conversely, any original-game policy can be
implemented in the tagged form by assigning an arbitrary tag (or by tagging from its internal
history without changing decisions). Thus the tagged adaptive-allocation class and the original
oracle class have the same attainable cost-risk pairs, exactly at every finite horizon.

If the tag instead withholds a queried label from one evidence process, or a reserved sub-budget
prevents use by the other process, the tagged class is a restriction of the original policy class.
Its optimum cannot be better than the full oracle; any improvement over a fixed split is ordinary
policy-class headroom until a separate theorem proves a structural gain over the strongest
history-dependent split. It is not evidence that the label-purpose wrapper itself is new.

This is a policy-equivalence argument, not a new theorem of statistical or computational value.
It closes the proposed joint-allocation wrapper as a standalone method. A surviving candidate must
supply an actual structure: for example, a proved compact sufficient state or an approximation
with separate economic-value and causal-risk errors that improves on the full-history game. That
requirement is already the G1 boundary in `switching_lagrangian_posg_reduction_v1.md`; the small
cell's exact `(2,1)` split match does not weaken it.
