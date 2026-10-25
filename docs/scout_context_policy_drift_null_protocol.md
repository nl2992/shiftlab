# Target-scout null calibration under abrupt context-prevalence drift

**Status:** frozen 2026-10-25 before execution. This independent stress test follows the IID and stationary-Markov calibrations and the positive-signal confirmation. It tests an abrupt change in learner-visible context prevalence while preserving the eventwise conditional-mean null.

## Question and null

Does the target-scout rule control false promotion when the latent context prevalence changes at the boundary between scout selection and certification? The three registered pre/post pairs are 0.10→0.90, 0.50→0.50 (stable control), and 0.90→0.10. The generated outcome probability remains exactly at the FN=5, FP=1 decision threshold for every event and context. Therefore each candidate's gross conditional expected gain is zero event by event; the registered switching charge makes its net gain nonpositive. The drift changes the distribution of context and candidate costs, not the conditional decision-harm estimand.

## Frozen design

- 1,000 independent seeds, 20267000–20267999, disjoint from development, prior calibration, and confirmation blocks.
- Three pre/post prevalence pairs crossed with proxy error 0 and 0.25, switching charges 0.00 and 0.05, and realized label caps 20% and 40%, for 24 prespecified cells.
- Preserve the target-scout selector, candidate family, fixed-mixture certification, alpha 0.05, uniform direct-IPW query process, global support bound, decision costs, event horizon (n=3,200, d=16), and scout/certification split.
- Verify evaluator-defined nonpositive expected certification gain, positive query support, and no cap breach for every stream. Report one-sided exact Clopper–Pearson promotion-rate upper limits with simultaneous 95% Bonferroni coverage (per-cell alpha 0.05/24). Each cell must contain at least 1,000 streams and have an upper limit at most 0.05; every cell must pass for the family to pass.

This finite calibration addresses the registered abrupt context shift under a pointwise conditional-mean null. It does not establish validity under outcome-law changes that violate that null, delayed or selectively observed labels, a different candidate-selection filtration, or real applications. If any cell fails, do not tune on these streams; investigate on a new development block and freeze a new protocol before fresh calibration. No figure is planned; use PaperBanana for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-drift-calibration `
  --seeds 1000 --seed-offset 20267000 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_drift_null_protocol.md `
  --output outputs/scout_context_policy_drift_null_1000
```
