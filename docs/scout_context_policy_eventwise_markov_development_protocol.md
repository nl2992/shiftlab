# Eventwise target-scout development under persistent contexts

**Status:** frozen 2026-10-25 before execution. Smoke checks reserve seeds 20272000–20272001; the development block below is disjoint from them and from prior development, null-calibration, and confirmation blocks. This is an exploratory screen of the eventwise-propensity-bound scout under serially persistent learner-visible contexts. It is not a null calibration or confirmatory test.

## Research question

Does the eventwise scout's utility advantage over minimum-bound scout, pooled rank, and nested-volume persist when context is temporally dependent? The tested context process is a stationary two-state Markov chain with stationary prevalence (p\in\{0.10,0.50,0.90\}) and lag-one persistence (\rho\in\{0,0.50,0.80\}). Signal strength, proxy noise, and label budget vary factorially. This tests context dependence, not gradual or recurring prevalence drift.

## Frozen design

- 60 matched development seed clusters, 20273000–20273059, disjoint from smoke checks and previous development, null-calibration, and confirmation blocks.
- 108 cells: three stationary context prevalences × three persistence values × three signal strengths (0, 0.05, 0.10) × two proxy-error rates (0, 0.25) × two realized label caps (20%, 40%). The 36 zero-signal cells are null controls; they are descriptive only and do not calibrate false-promotion rates.
- Compare eventwise-bound scout, minimum-propensity scout, pooled rank, and nested-volume on matched streams. Keep uniform randomized querying, direct-IPW estimation, the fixed-mixture e-process, FN cost 5, FP cost 1, switching charge 0.05, alpha 0.05, `n=3,200`, `d=16`, and the registered scout/certification split.
- Primary development summaries are equal-cell expected postpromotion net decision gain on the 72 positive-signal cells, paired by seed cluster. Report eventwise-minus-minimum-bound, eventwise-minus-rank, and eventwise-minus-nested-volume contrasts overall, by signal strength, and by persistence. Use 10,000 descriptive seed-cluster bootstrap draws; do not treat intervals as confirmation.
- Save all 25,920 method-cell-seed rows, cell summaries, contrasts, zero-signal promotion rates, processed horizon, labels, cap checks, protocol hash, environment, and checksums. Require complete unique keys, positive propensities, finite evaluator utility, and no hard-cap violation.
- Execute on CUDA with six independent worker processes and deterministic seed-derived streams. Preserve seed ordering in the output. No figure is planned; use PaperBanana for any future visual.

## Interpretation limits and next gate

The uniform-query support bound (B_t=C/q_t+\kappa) remains predictable here, but the existing eventwise-bound null calibration was performed under abrupt prevalence profiles rather than this stationary Markov family. The existing Markov null calibration covered the minimum-bound scout, not the eventwise variant. Therefore, do not use the 60-seed zero-signal controls as calibration or claim Markov-robust false-promotion control. If positive-signal development results justify continuing, freeze a fresh Markov null calibration for the eventwise rule before any disjoint positive-signal confirmation. Do not alter the rule using confirmation results.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-development `
  --seeds 60 --seed-offset 20273000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_markov_development_protocol.md `
  --output outputs/scout_context_policy_eventwise_markov_development_60
```
