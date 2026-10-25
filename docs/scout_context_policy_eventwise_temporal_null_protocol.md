# Eventwise-scout null calibration under gradual and recurring contexts

**Status:** frozen 2026-10-25 after the temporal development grid and before calibration. This is a
finite calibration of the registered false-promotion gate, not positive-signal confirmation.

## Null and scope

The target-period learner-visible context prevalence follows one of four deterministic schedules:
linear 0.10→0.90, linear 0.90→0.10, or four equal phases alternating 0.10 and 0.90 in either
starting order. Context draws are independent Bernoulli conditional on the schedule. Proxy-error
rates are 0 and 0.25. For both latent groups and every event, the Bernoulli outcome probability is
exactly the decision threshold 1/6 for FN cost 5 and FP cost 1. Thus every fixed candidate has zero
gross expected cost advantage at each event, and the registered 0.05 switching charge makes net
expected gain nonpositive. The evaluator must verify `candidate_is_monitor_null` for every stream.

The tested procedure is the frozen eventwise-propensity-bound target scout with fixed split,
candidate family, context-selection rule, fixed-mixture certification, direct-IPW estimator, alpha
0.05, uniform randomized query process, immediate complete labels, and 20%/40% hard label caps.
No parameter, schedule, threshold, or method is tuned on these calibration streams.

## Frozen design and familywise gate

- 1,000 independent streams per cell, fresh seed block 20275000–20275999, disjoint from all prior
  development, smoke, Markov, abrupt-drift, and confirmation blocks.
- 16 simultaneous cells: four prevalence schedules × two proxy-error rates × two label caps.
- Use one-sided exact Clopper–Pearson upper limits with familywise alpha 0.05 and per-cell alpha
  0.05/16. Each cell passes only with at least 1,000 streams, verified conditional null for every
  stream, positive query support, zero hard-cap violations, and an upper limit at most 0.05. The
  family passes only if every cell passes.
- Save all eventwise stream records, cell counts/rates/limits, evaluator-null and cap audits,
  source/artifact SHA-256 hashes, software/GPU environment, and protocol hash. Fewer than 1,000
  streams per cell is `smoke_only_not_calibration`.

This supports a false-promotion statement only for the registered event-conditional null,
deterministic schedule family, fixed split and candidate set, uniform-query process, immediate
feedback, and specified costs. It does not cover delayed/selective labels, adaptive propensities,
unregistered schedules, other outcome dependence, or real-world utility. A calibration failure
blocks confirmation; retain it and return to development rather than changing the procedure on the
same calibration streams. No figure is planned; use PaperBanana for any later visual.

## Reproduction

```powershell
uv run shiftlab-dive-scout-temporal-calibrate `
  --seeds 1000 --seed-offset 20275000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_temporal_null_protocol.md `
  --output outputs/scout_context_policy_eventwise_temporal_null_1000
```
