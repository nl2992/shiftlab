# Does the IID-null assumption break standard promotion policies? (protocol, written before any run)

**Date:** 2026-11-17. **Author:** lead. **Requested by the user:** show, on synthetic and real-data chains, that standard
algorithms designed under the IID null fail when the null is causal; try up to n settings and present 5 that make the
point.

## Question

Take standard promotion policies, calibrate each so its false-promotion probability is exactly α (or the largest value
≤ α) under the IID(1/2) null, then compute its **exact worst-case** false-promotion probability over all causal nulls
(conditional label probability p ∈ [0, 1/2] chosen by the null from the whole public history). Report the ratio
causal risk / α.

## Expected outcome, stated in advance (so it cannot be tuned away)

A policy whose promotion event is monotone in the count of positive labels and whose query times do not depend on the
labels (fixed-sample test, count-based SPRT) should stay safe: a causal null cannot do better than p = 1/2 against a
monotone count rule. The failure is expected only for **belief-adaptive** policies, which use the hidden-Markov filter, so
that a label 0 can raise the promotion probability (anti-persistent chains). The write-up must say which kind failed; it
will not claim that "all standard methods" fail.

## Policies (all deterministic or explicitly randomised, all using at most B queries, delay d = 1)

1. **Fixed-sample binomial test.** Query at times 1..B; promote at time B + 1 if the count of ones is ≥ k (randomise at the
   boundary to hit α exactly).
2. **Count-based SPRT (Wald).** Query every step until the budget is used; stop and promote when the IID log-likelihood
   ratio of the counts crosses the upper boundary; boundaries calibrated to IID risk α.
3. **Bayesian HMM-filter threshold.** Query every step until the budget is used; promote the first time the filtered
   posterior P(good state | labels) exceeds τ; τ calibrated to IID risk α.
4. **Myopic value-of-information design.** Query when the one-step value of information exceeds a fixed cost; promote when
   the posterior exceeds τ; τ calibrated to IID risk α.
5. **IID-optimal constrained-POMDP policy.** The exact optimum under the IID null (RB-DP in `iid` mode; this is what a
   constrained POMDP solver would return).
6. **Fixed-bet e-process gate** (from E4): safe by construction; included as the safe reference.
7. **RB-DP causal policy**: safe by construction and optimal; included as the reference.

Exact risk for 1–4: backward recursion of `PROOFS.md` Lemma A on the policy's own history tree (m(a, b) = max(a, (a+b)/2)
causal, (a+b)/2 IID); cross-checked on small cells by brute force over deterministic nulls (as in
`scripts/paper4_continuation/rbdp/review/check_a_lemmaA.py`). Calibration is done by bisection on τ or k with boundary
randomisation, under the IID recursion.

## Settings

- **Synthetic:** symmetric and asymmetric two-state chains, t01, t10 ∈ {0.6, 0.75, 0.9} (anti-persistent) and
  {0.1, 0.25} (persistent controls), e0 ∈ {0.1, 0.2}, e1 = 1 − e0, α ∈ {0.05, 0.1}, B ∈ {2, 3, 4}, T ∈ {12, 20}. All
  combinations, a fixed list in this order.
- **Real-data chains:** the fitted chains of datasets that qualified in `../real_data/` (Old Faithful c01, P23, P24 now; Phase 4
  qualifiers when that run ends), same α, B, T grid.
- "Shuffle" in the user's sense is read as: try many settings. Each real stream's time-shuffle is also run as a control
  (shuffling removes the hidden structure, so the failure should disappear).

## Reporting and the "5 that prove the point"

- Every setting run is reported: n settings, per policy the distribution (min, median, max) of causal risk / α, and the
  number of settings where causal risk exceeds α by more than 1e-9.
- The **5 illustrations** are the 5 settings with the largest causal-risk ratio for the belief-adaptive policies, chosen by
  that rule, at most 2 synthetic and at least 3 from real-data chains if 3 real chains show a failure. They are labelled
  "selected as the most extreme of n", never as typical.
- Persistent-chain controls and shuffled real streams are reported next to the illustrations.

## Outputs

Scripts: `scripts/paper4_continuation/rbdp/iid_failure/`. Results: `docs/paper4_continuation/rbdp/iid_failure/results/`.
Write-up: `docs/paper4_continuation/rbdp/iid_failure/IID_FAILURE.md`.
