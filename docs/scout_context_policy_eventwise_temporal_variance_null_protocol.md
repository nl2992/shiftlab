# Eventwise-scout variance-query temporal null calibration protocol

**Status:** frozen 2026-10-25 before the registered variance-query calibration seed block.
This is a finite calibration of false-promotion behavior, not a power result or confirmation.

## Null and scope

The calibration uses the existing synthetic candidate-context-heterogeneity null. For both latent
groups and every event, the outcome probability is the decision threshold `1/6` under false-negative
cost 5 and false-positive cost 1. Each candidate therefore has zero gross expected cost advantage;
the registered switching cost is 0.05, so expected net gain is nonpositive at every event. The
evaluator must verify `candidate_is_monitor_null` on every stream.

The tested monitor is the eventwise-propensity-bound target scout with fixed split, validation-ranked
candidate, direct-IPW estimator, fixed-mixture certification, alpha 0.05, immediate complete
feedback, and hard label-budget rates 0.20 and 0.40. The query policy is `variance`: its probabilities
are predictable, based on the validation-fitted residual-second-moment score, with `q_min` equal to
half the target budget rate and `q_max=max(0.5, budget_rate)`. The propensity multiplier is fit on
the pre-monitor validation slice and frozen before monitoring. No evaluator-only oracle quantity is
an input to this policy. Query-policy and monitor settings are fixed before calibration.

## Frozen design and gate

- Use 1,000 independent streams per cell on the fresh seed block `21430000`–`21430999`.
- Cross four deterministic context-prevalence schedules (gradual up, gradual down, recurring
  low-first, recurring high-first), two proxy-error rates (0 and 0.25), and two hard label caps
  (0.20 and 0.40): 16 simultaneous cells, 16,000 stream records total.
- Compute one-sided exact Clopper–Pearson upper limits with familywise alpha 0.05 and per-cell alpha
  `0.05/16`. Every cell must contain at least 1,000 unique streams, pass every evaluator-null
  check, have positive propensity support, respect all realized label caps, and have simultaneous
  upper limit at most 0.05. The family passes only if every cell passes.
- Save stream-level records, cell counts and limits, cap/null audits, source/artifact SHA-256 hashes,
  runtime/GPU environment, and this protocol's SHA-256. Fewer than 1,000 streams per cell is a smoke
  test, not calibration.

## Interpretation limits

A pass supports only the specified event-conditional null, deterministic schedule family, fixed
split and candidate set, validation-fitted variance query process, immediate feedback, and costs. It
does not establish power, protection against harmful promotion on alternatives, validity under
delayed or selectively observed labels, query probabilities adapted to certification evidence,
other outcome dependence, or real-data utility. Passing permits a separately frozen positive-signal
confirmation on fresh seeds; it does not compel that confirmation if development evidence no longer
supports the candidate. Any selected schedule-level endpoints must be registered before that run.
No novelty claim follows. No figure is planned; use PaperBanana if a visual is needed later.

## Reproduction

```powershell
uv run shiftlab-dive-scout-temporal-calibrate `
  --query-policy variance --seeds 1000 --seed-offset 21430000 `
  --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_temporal_variance_null_protocol.md `
  --output outputs/scout_context_policy_eventwise_temporal_variance_null_1000
```
