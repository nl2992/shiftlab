# Adaptive sample allocation in sequential multiple testing: novelty boundary

**Date:** 2026-10-29. **Status:** primary-source theorem-scope audit; no new method claim.

## Source and inspected result

Malek, Katariya, Chow and Ghavamzadeh, “Sequential Multiple Hypothesis Testing with Type I Error
Control,” AISTATS 2017, PMLR 54:1468–1476. I inspected the full PMLR paper, including the
sequential-p-value definition, Algorithm 1, Theorem 5.4, and the proof outline in Section 5.2.

They take a monotone fixed-horizon multiple-testing procedure with an `(f,q)` error guarantee and
replace its p-values with sequential p-values that remain super-uniform under optional stopping.
The resulting rule updates the p-values of tests not yet rejected and stops sampling each rejected
test; at each round the set of tests receiving samples is a function of the current sequential
p-values. Theorem 5.4 shows the sequential conversion inherits the original guarantee, including
FWER, under the stated sequential-p-value conditions. Their construction permits data-dependent
allocation across tests and an overall stopping time. The proof equates its decisions with applying
the original procedure to all tests run to the common horizon. The paper's sample-allocation
objective is the number of rejected hypotheses; samples have no modeled acquisition price or
deployment value.

## Consequence for ShiftLab

This closes generic claims that (a) sequentially valid tests can be stopped early, (b) evidence can
be allocated among a fixed family of candidate models based on previous p-values, or (c) FWER is
preserved by combining adaptive sampling with a monotone fixed-horizon multiple-testing rule. A
candidate comparing only with uniform sampling, fixed alpha-spending, or fixed per-model sample
sizes would be too weak. Include sequential MHT with the strongest applicable FWER procedure as a
baseline, and charge its labels under the same hard budget and release schedule when adapting it to
ShiftLab.

The paper fixes the family of hypotheses and considers stopping and sample allocation among those
tests. It does not optimize priced observations against deployment utility, support a hidden
recurrent regime or repeated reversible model replacement, account for a shared query pool whose
labels are pending at the decision time, or control the full-history causal-null promotion event
for ShiftLab's adaptive paired-label model. Those mismatches leave a precise combination to test;
they are not a novelty claim. In particular, simply adding query prices and switch costs to their
sample-allocation rule is not enough. A result must show a new acquisition/switching structure and a
theorem beyond the sequential-MHT reduction, online FWER/SRGP, and costed sequential-experiment
baselines already audited.

Promotion-risk validity remains separate from current-regime utility. Even a test that validly
approves an update under the null does not certify its benefit after the regime reverses; that
decision needs post-reversal evidence or an explicit persistence assumption.

## Decision

Treat data-dependent sequential allocation across tests as established. Add it to the mandatory
matched-budget comparator family. G1 remains open only for an acquisition-and-reversible-switching
result that exceeds this and the other audited baselines under one information, delay, risk, and
economic contract. No G2–G5 gate is opened by this audit.

## Provenance

- Official source: [PMLR article](https://proceedings.mlr.press/v54/malek17a.html) and
  [full PDF](https://proceedings.mlr.press/v54/malek17a/malek17a.pdf).
- Cached PDF: `outputs/switching_source_audit_v1/malek_sequential_mht_2017.pdf`.
- SHA256: `9F63C35191EFA89AD362CC14BCCBA08BA6B705DAAD35D77D89EFF951731BDEB8` (561,551 bytes).
- Selected theorem-scope/proof-outline audit, not an independent reproof.
