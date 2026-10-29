# Cheng et al. (ICML 2023): hard-budget switching audit

**Date:** 2026-10-28. **Status:** primary-source theorem and protocol read; exact contract comparison, not a novelty claim.

## Source and inspected result

Cheng, Zhou and Ji, [“Understanding the Role of Feedback in Online Learning with Switching Costs,” ICML 2023](https://proceedings.mlr.press/v202/cheng23f.html), PMLR 202:5521–5543. I inspected the paper's Sections 2 and 4, Theorem 2, Algorithm 1, Proposition 2 and Appendix C proof. The primary [PDF](https://proceedings.mlr.press/v202/cheng23f/cheng23f.pdf) is preserved in the repository's existing source cache and recorded as `cheng23` in `switching_source_manifest_v9.json` (SHA256 `01275cb90376c916c359ffb275b6c068ddc4d50112083d39a3da27a57e317237`).

The protocol is an oblivious adversarial K-action loss sequence with known horizon. Every chosen action incurs its loss and a unit cost for changing from the previous action. Section 4 lets the learner choose a set of action losses to observe each round; total individual action-loss observations satisfy `N_ob <= B`. Theorem 2 gives minimax regret `soft-Theta(T sqrt(K/B))` against the best fixed action. For full-information feedback, Algorithm 1 with `N=B/K` batches, one uniformly sampled full-information round per batch, and Shrinking Dartboard action persistence achieves Proposition 2's `O(T sqrt(K log K/B))` worst-case expected regret. Appendix C combines the unbiased batch-loss estimate, mirror-descent regret, and an expected switching-cost bound. No delayed-release queue or time-uniform safety event appears in this protocol or result.

## Mapping to the ShiftLab contract

| Dimension | Cheng et al. | Current ShiftLab problem |
|---|---|---|
| Feedback object | Individual action losses; full information observes K losses at a sampled round | One query reveals a paired common-outcome comparison, equivalent to two action-loss observations when both policies' losses are identifiable |
| Budget | Hard total count `B` of individual action-loss observations | Hard total cap `B_q` on paired queries, including pending requests |
| Release time | At the sampled round; no delay queue | Fixed known delay `d >= 1`, with unreleased outcomes unavailable |
| Comparator | Best fixed action in hindsight; its switching cost is zero | Dynamic policy path with at most S switches, charged the same switch cost |
| Safety | Expected regret; no false-promotion probability constraint | Global time-uniform false-promotion risk at most alpha under a declared conditional null |
| Information cost | Observations are free subject to B | Queries incur `c` and consume the hard cap |

For K=2, a paired query costs two entries of Cheng's observation budget, so the closest full-information budget match is `B=2 B_q`; this accounting conversion does not bridge the delay, query price, comparator, or risk differences. The paper therefore establishes that hard-budget observation plus switching-cost learning is occupied. Its theorem does not imply the ShiftLab guarantee, and those mismatches alone do not prove an open novelty gap.

## Research consequence

Use Cheng's full-information batched Shrinking Dartboard method, with the two-observation conversion and the same delayed-feedback and safety wrapper, as a mandatory baseline wherever its assumptions can be made comparable. Report its delay treatment and safety status explicitly; do not compare only against budgeted Hedge without switching costs. G1 remains unresolved until either (a) a matched theorem gives an attainable risk-regret frontier better than this and the separately-valid-test composition, or (b) a reduction shows the composition already attains the frontier and the hypothesis is revised. The current audit only closes the broad premise and narrows the proof obligation.
