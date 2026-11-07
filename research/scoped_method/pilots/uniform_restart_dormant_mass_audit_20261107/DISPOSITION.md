# Dormant-mass audit disposition (2026-11-07)

**Finding: the concern does not invalidate the stated any-false-crossing bound.** An independent
read-only review derived the result from the exact `MarkovSUI` component and checked the existing
family-A validity argument. No synthetic null run was completed: it was unnecessary to answer the
mathematical question, and the proposed 5,000-stream implementation-level probe was stopped because
it redundantly recomputed the same stream and was not a useful proof of validity.

For a fixed start `j`, the likelihood-ratio component `Q_{j:k}/L_theta(j:k)` is a nonnegative
martingale from that predictable start under each member `theta` of the stated stationary
first-order Markov null. The implementation component `Q_{j:k}/U_{j:k}` is pointwise no larger,
because `U` upper-bounds the null likelihood. Form the augmented mixture by giving each not-yet-opened
component its fixed prior mass at value 1. This is a test supermartingale initialized at 1. The
reported statistic omits that dormant mass and is pointwise bounded above by the augmented process.
Therefore, crossing the same threshold with the reported statistic implies that the augmented test
supermartingale crossed it; Ville's inequality bounds the reported statistic's false-crossing
probability by the nominal level.

The precision matters: the reported statistic need not itself be a supermartingale; it is a
Ville-valid crossing statistic dominated by one. The repository's family-A validity section already
states this “started mixture plus tail weight” argument in
[`docs/sota_sprint/family_a/RESULTS.md`](../../../../docs/sota_sprint/family_a/RESULTS.md).
This audit found no reason to quarantine the published P6/RMM comparison records on this issue.

Scope remains conditional on predictable deterministic start times, the claimed segment-wise
likelihood upper bound, and the stationary first-order Markov conditional null independent of
disagreement. It does not expand the guarantee to higher-order, nonstationary, or disagreement-
dependent streams. The frozen diagnostic protocol and runner are retained for reproducibility but
were not run; running them later may check software behavior, not replace the proof.
