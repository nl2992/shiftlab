# PPRM predictive-risk independent confirmation protocol

**Status:** frozen before execution, 2026-10-26. This is an independent
synthetic confirmation of the development operating point, not a method-tuning
run and not evidence of real-world performance.

## Question and estimands

Using the unchanged PPRM benchmark implementation and configuration, does the
development pattern persist on a disjoint seed block? PPRM and supervised risk
monitoring (SRM) test a running-average predictive-risk null. DIVE tests its
own paired-cost null. Their alarm rates will be reported separately and will
not be ranked as though they tested the same hypothesis.

## Frozen design

- Runner: `scripts/run_pprm_predictive_risk_benchmark.py`.
- Seed offset: `71,000,000`, disjoint from development seeds beginning at
  `70,000,000`.
- Replicates: 300 independent generated streams per scenario.
- Scenarios: stationary, benign nuisance, predictive-risk harm, and
  decision-cost-only shift.
- Configuration otherwise unchanged: CUDA generation when available, 1,200
  rounds, onset 400, 1 labeled plus 15 disjoint unlabeled inputs per round,
  source sample 2,048 labeled plus 30,720 disjoint unlabeled observations,
  alpha split 0.025/0.025, and both margins 0.05.
- No thresholds, scenarios, seed block, source sample size, batch sizes,
  methods, or reporting endpoints may be modified after inspection of these
  confirmation results. A subsequent change requires a new protocol and seed
  block.

## Outcomes and interpretation

Report every stream, any-alarm rate, pre-onset alarms, post-onset detection,
first-crossing delay with non-detections censored at the horizon, and the
scenario's evaluator-known predictive risk and paired cost. Report binomial
uncertainty intervals for rates. Controls estimate operating behavior at this
one frozen point; 300 streams per cell do not prove a theorem or validate
arbitrary dependence, feedback, or shift processes. The positive predictive
harm cell is an alternative confirmation for this specified generator only.
The decision-cost-only cell checks endpoint separation. Do not tune or select a
method using these results.

## Pass/fail and stop rule

Run exactly once at the frozen configuration. Preserve all results whether
favorable or not. Treat failed validation, unavailable CUDA with an explicit
CUDA request, or incomplete manifests as a failed run; fix only mechanical
execution issues without changing the scientific configuration. Following
inspection, update the Q1 gap analysis and make a go/no-go decision; do not
automatically launch a larger parameter sweep.

## Reproduction

```powershell
uv run python scripts/run_pprm_predictive_risk_benchmark.py `
  --seeds 300 --seed-offset 71000000 --device cuda `
  --output-dir outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_confirmation_v1
```
