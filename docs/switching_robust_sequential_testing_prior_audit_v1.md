# Robust sequential testing prior: novelty boundary

**Date:** 2026-10-29. **Status:** theorem-scope audit from the primary source; no new method claim.

## Primary result inspected

Saha and Ramdas, “Robust Likelihood Ratio Tests for Composite Nulls and Alternatives,” arXiv:2408.14015 (2024). I downloaded and inspected the arXiv PDF, including the adaptive-contamination setup in Sections 2.1 and 3.1, Corollary 3.4, the composite-null predictable plug-in construction in Section 4.1, Theorem 4.1 and its conditional expectation argument, and the appendix proof. The paper constructs nonnegative test supermartingales under a composite null whose conditional observation law may be chosen adaptively from a total-variation neighborhood at each step. Ville's inequality then gives anytime level control. Corollary 3.4 also gives a robust least-favorable likelihood-ratio construction when a least-favorable pair exists.

For the ShiftLab binary causal null, let the queried-label sequence be indexed by label release and take `P0={Bernoulli(p): p<=1/2}`. The exact causal null has each label's conditional law in `P0`; hence it lies in the paper's adaptive null class (and in any positive-radius TV enlargement). Predictable query decisions can be represented by inserting a neutral factor of one on rounds without a released queried label. A pathwise cap and finite-horizon stopping preserve the resulting supermartingale safety. Delayed labels require careful filtration bookkeeping, but delay alone does not create a new anytime-valid testing principle.

## Consequence for ShiftLab

Close the following as novelty claims: (1) using an e-process or robust likelihood ratio to control false promotion under an adaptive causal null; (2) estimating a composite alternative predictably and multiplying safe factors; and (3) obtaining a least-favorable robust likelihood ratio for a fixed testing problem. These are covered by the cited work or standard sequential-testing consequences.

The paper does not solve the economic switching problem. It does not jointly optimize a hard request budget, delayed feedback acquisition, recurring regime-dependent deployment utility, transaction/switch costs, reversals, and one global any-promotion event against a separate null law. Nor does a valid promotion e-process certify that the challenger remains valuable after a regime reversal. Statistical evidence for the declared null and current-regime continuation value must remain separate.

The residual G1 question is therefore not “how to build an anytime-valid gate.” It is whether the established gate's remaining risk/wealth can be integrated with an exact or provably approximate resource-constrained switching controller that strictly improves the best matched policy, or whether a lower bound rules that out. Any claimed bound must state whether risk is spent per promotion, globally across all time, and whether re-promotions count as new events. The proof must preserve the filtration when labels are pending and the adversary sees more than the learner.

## Decision

Use the paper's result as the safety baseline in the algorithm audit, not as the new contribution. Keep G1 open only for a technically nontrivial interaction among global risk allocation, delayed costly acquisition, and reversible economic switching with a demonstrated theorem or oracle separation. Do not proceed to efficacy sweeps or real-data analysis until that G1 gate passes. Post-reversal value remains uncertified without post-change evidence or an explicit persistence/predictive-signal assumption.

## Provenance

- Primary source: [arXiv:2408.14015](https://arxiv.org/abs/2408.14015), especially Sections 2.1, 3.1, 3.2, 4.1, Corollary 3.4, Theorem 4.1, and the appendix proof of Theorem 4.1.
- Cached PDF: `outputs/switching_source_audit_v1/saha_ramdas_robust_likelihood_ratio_tests_2024.pdf`.
- SHA256: `F52F60B24C7402366DEEBFB975EE12DAB877C21AFA53782F85CF6D1FE0D29135`.
- This is a selected theorem-scope audit, not an independent reproof. The predictable skipping and delayed-release filtration observations above are direct reductions to the theorem's conditional-null setup; they should be written formally before use in a paper proof.
