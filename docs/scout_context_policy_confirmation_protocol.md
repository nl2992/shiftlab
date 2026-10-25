# Target-scout contextual policy independent confirmation protocol

**Status:** frozen 2026-10-25 after the registered independent development
replication passed both utility gates and the separate 36-cell null calibration
passed. No confirmation outcomes have been inspected.

## Question

On new IID synthetic streams, does target-scout selection with holdout
certification improve evaluator-known future net decision utility over (1)
pooled-rank candidate testing and (2) nested candidate-by-context volume
alpha, by at least one cumulative utility unit under each registered primary
contrast?

This tests the two-stage rule already described in
[`scout_selected_context_policy_protocol.md`](scout_selected_context_policy_protocol.md).
It does not test a new e-process or establish novelty.

## Frozen design

- Use 600 matched seed IDs, 20264000–20264599, in each of the 18 positive-signal
  cells. This block is disjoint from all development blocks, the null
  calibration block (20261300–20262299), and the noninferential runner smoke
  checks.
- Cross target context prevalence 0.10/0.50/0.90, decision-boundary signal
  delta 0.05/0.10, and learner-proxy misclassification 0/0.10/0.25.
- Use `n=3,200`, `d=16`, CUDA stream generation, FN cost 5, FP cost 1, uniform
  direct-IPW queries, fixed-mixture certification at alpha 0.05, 0.05 switching
  charge, and the common realized 40% label cap. Scout uses the first half of
  the target monitor and freezes its context-specific action map before the
  independent certification half.
- Compare `scout_context_policy`, pooled `rank`, and `rank_context_volume` on
  identical streams and query uniforms. The primary metric is evaluator-known
  cumulative future net gain after certification and switching charges. The
  18 cells receive equal weight; seeds are paired within every cell and
  resampled as common seed blocks across cells.
- The two primary contrasts are scout minus pooled-rank and scout minus
  nested-volume. Use 10,000 matched seed-block bootstrap draws and 97.5%
  two-sided percentile intervals per contrast, giving simultaneous 95%
  coverage by Bonferroni. The confirmation gate passes only if both lower
  limits exceed +1.0 cumulative utility units and every hard cap is respected.
- Report per-cell utility, promotion rate, harmful-promotion rate, processed
  certification fraction and label use as descriptive diagnostics. Do not
  select cells, tune the method, or change the endpoint after seeing results.

The population target is the registered IID synthetic family only. The
independent null calibration supports the stated fixed-candidate, known
positive-propensity, bounded-increment assumptions; this confirmation does not
extend them to serial dependence, delayed or selectively observed labels,
context drift, misspecified deployment charges, or real applications. A
failed primary gate stops the performance claim for this rule. A passed gate
supports only these two registered synthetic comparisons. No figure is
planned; use PaperBanana for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-scout-confirm `
  --seeds 600 --seed-offset 20264000 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_context_policy_confirmation_protocol.md `
  --output outputs/scout_context_policy_confirmation_600
```
