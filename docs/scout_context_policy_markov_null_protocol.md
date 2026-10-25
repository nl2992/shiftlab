# Target-scout null calibration with serially persistent context

**Status:** frozen 2026-10-25 before execution. This is a new robustness
calibration after the IID calibration and positive-signal confirmation. It
tests context dependence while preserving the pointwise conditional-mean null.

## Question and null

Does the already calibrated target-scout rule maintain its false-promotion
control when the learner-visible context is serially persistent? During the
target stream, latent group membership follows a stationary two-state Markov
chain with persistence 0.80 and registered stationary prevalence. Proxy noise
is applied independently after group generation. Given each current group,
the outcome probability remains exactly the FN/FP decision threshold, so every
candidate has zero gross conditional expected gain at every event. The
switching charges 0.00 and 0.05 respectively give the least-favorable boundary
and weakly negative net utility. Thus the conditional-mean null remains true
even though covariates and candidate costs are serially dependent.

## Frozen design

- 1,000 independent matched seeds, 20265000–20265999, shared across cells only
  for pairing and disjoint from all prior development, calibration and
  confirmation blocks.
- Six profiles: stationary prevalence 0.10/0.50/0.90 crossed with learner
  proxy error 0/0.25; target-context persistence is fixed at 0.80.
- Two switching charges (0.00 and 0.05) and two pathwise label caps
  (20% and 40%), for 24 prespecified cells.
- Preserve the exact scout selector, candidate family, fixed-mixture
  certification rule, alpha 0.05, uniform direct-IPW query process, global
  support bound, FN/FP costs, monitor split, and `n=3,200`, `d=16`.
- Require every stream to have the evaluator-defined nonpositive expected
  certification gain, positive query support, and no realized cap breach.
  Report one-sided exact Clopper–Pearson promotion-rate upper limits with
  simultaneous 95% Bonferroni coverage using cell alpha 0.05/24. A cell passes
  only with at least 1,000 streams and an upper limit at most 0.05; the family
  passes only if all 24 cells pass.

This tests dependence in observable contexts and costs under an eventwise
martingale null. It does not cover label dependence beyond that null, delayed
or selective feedback, nonstationary context drift, or real applications. A
failed calibration retires the current robustness claim for persistent
contexts; do not tune on these streams. No figure is planned; use PaperBanana
for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-calibration `
  --seeds 1000 --seed-offset 20265000 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_markov_null_protocol.md `
  --output outputs/scout_context_policy_markov_null_1000
```
