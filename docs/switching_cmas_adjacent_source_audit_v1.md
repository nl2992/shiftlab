# CMAS: adjacent prior art for sequential model switching

**Date:** 2026-10-29. **Status:** primary-source screen; mandatory comparator/positioning obligation,
not a novelty conclusion.

## Primary source inspected

Ali Atiah Alzahrani, “Conservative Meta-Agent Search: Architecture Adaptation under
Non-Stationarity,” [arXiv:2610.31436v1](https://arxiv.org/abs/2610.31436), submitted 22 Oct 2026.
I inspected the arXiv HTML v1: abstract and Sections 1–4, the formal update and promotion
definitions, Proposition 1 and Appendix A proof/assumptions, the information chronology, the
false-promotion denominators, and rollback/failure examples.

## Exact overlap

CMAS formalizes sequential incumbent replacement with switching costs and hard eligibility
constraints, uses paired candidate/incumbent shadow replay under common random numbers, scores
delayed dependent utility, promotes a candidate, and runs a simulated canary with rollback. Its
simulator has recurrent regimes, and it evaluates dynamic-oracle regret, held-out utility, false
promotions and rollback. Therefore “combine model switching, delayed evaluation, a promotion gate,
and rollback” is already claimed in adjacent contemporary work. A ShiftLab methodological paper
cannot present that system-level integration as its novelty.

## Guarantee and information boundary

The paper's implemented score is explicitly empirical calibration, not a valid confidence bound:
its 26-week replay windows overlap at monthly updates, its variance-only radius omits the range
term, and its effective block count and variance are estimated. Proposition 1 is separately
idealized: a candidate pool is frozen before its shadow sample, each candidate has a valid
simultaneous confidence radius, and update-wise error levels are summable to control family-wise
false promotion. The authors state that Eq. (6) does not satisfy the proposition's valid-radius
premise and that the reported runs do not activate the anytime sequence-level schedule. The
reported false-promotion rate is per update; 11.4% of streams contain at least one false promotion.
The paper also describes simulated canary-stage harm before rollback.

The formal protocol has fixed shadow-replay windows, candidate-pool and search-compute budgets,
and architecture eligibility constraints. The inspected model does not specify a pathwise cap on
online label requests that reserves rights for pending labels, nor the event-time observation
filtration in which a causal-null opponent may see queried labels before release. Its safety target
is a candidate's mean improvement in a replay statistic conditional on a frozen pool, not the
ShiftLab global conditional-null event for any promotion. Thus CMAS is a strong systems-level
neighbor and required empirical comparator where its candidate/evaluation interface applies; it
does not supply the exact ShiftLab observation, null-risk or anytime guarantee.

## Novelty decision

The adjacent source further rules out contribution claims based on generic sequential replacement,
paired candidate evaluation, delayed utility, switching costs, or rollback. The remaining ShiftLab
delta, if any, must be an acquisition-and-switching theorem under a pathwise observation budget,
request-time reservation with delayed labels, and the declared anytime causal-null event, with
current-regime value evidence kept separate after reversal. An anytime-valid wrapper alone is
already standard in the repository's prior audits; these contract differences alone do not prove
novelty. No algorithm, experiment, or real-data claim follows from this source audit.

## Source locations

- Formal scope and stated contribution: arXiv HTML v1, Sections 1 and 3–4.
- Implemented score vs. idealized Proposition 1: Section 4 and Appendix A.
- Per-update vs. per-stream false-promotion rates, overlapping windows, and no activated anytime
  schedule: Appendix G and discussion.
- Simulated canary rollback harm: Appendix F.
