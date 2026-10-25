# Eventwise target-scout development under gradual and recurring contexts

**Status:** frozen 2026-10-25 before the development run. This is an exploratory synthetic
stress test. It is not a null calibration, confirmatory test, or novelty claim.

## Question and scope

Does the previously calibrated eventwise-propensity target scout retain its development-stage
utility advantage over minimum-propensity scouting, pooled candidate-rank allocation, and nested
context-volume allocation when the latent context prevalence changes gradually or returns to prior
levels? The design tests deterministic temporal prevalence schedules with independent Bernoulli
context draws conditional on the schedule. It does not combine those schedules with Markov context
persistence, delayed feedback, or adaptive query propensities.

## Frozen data-generating process

- 3,200 events, 16 features, the existing train/validation/monitor/deployment split, FN cost 5,
  FP cost 1, switching cost 0.05, alpha 0.05, fixed-mixture certification, and uniform querying.
- Four target-period prevalence schedules, each with endpoints 0.10 and 0.90: linear 0.10→0.90,
  linear 0.90→0.10, four equal phases 0.10/0.90/0.10/0.90, and the phase-reversed recurring
  schedule. The deterministic schedule starts at the monitor boundary and continues through
  deployment. Context labels are independent Bernoulli draws given their eventwise prevalence.
- Signal strengths {0, 0.05, 0.10}, proxy error {0, 0.25}, and hard label caps {20%, 40%} form
  48 cells. At signal zero, each event's outcome probability remains exactly the Bayes threshold
  1/6 under the registered costs, regardless of context prevalence. Positive signal sets the
  conditional outcome probabilities to 1/6 ± delta by latent group; evaluator truth is used only
  for scoring, while the learner observes the independently corrupted binary context proxy.
- Compare eventwise-propensity scout, minimum-propensity scout, pooled rank, and nested
  context-volume methods on the same seed-specific stream. Reuse one seed across cells for paired
  contrasts, but use a fresh block 20,274,000–20,274,059, disjoint from all recorded development,
  calibration, confirmation, and smoke blocks.

## Metrics and gates

The exploratory grid has 60 seeds per cell and must contain all 11,520 method-cell-seed rows with
unique keys. Save expected and realized postpromotion net gain, promotions and harmful promotions,
labels, monitor events, support minima, and hard-cap checks. Report equal-cell paired expected-net-
gain contrasts with seed-cluster bootstrap intervals, plus schedule- and signal-level summaries.
Every propensity must be positive; every reported utility must be finite; no cap may be exceeded.
At zero signal, evaluator-known conditional expected net gain must be nonpositive. These are
integrity checks, not a false-promotion guarantee.

The 60-seed zero-signal cells are diagnostic only and must not be treated as calibration. Do not
select a winner or tune thresholds from these results. If results justify advancing, freeze an
independent eventwise-rule null calibration over the temporal schedules before any disjoint
positive-signal confirmation. Apply a new calibration familywise gate; do not infer validity from the
stationary or abrupt-prevalence calibrations. The standard predictable bounded-factor argument
continues to rely on the stated event-conditional mean null, fixed split, uniform query probability,
complete immediate labels, and known predictable support bound.

No figure is planned. Any later research visual must use PaperBanana and must be checked against the
saved metrics.

## Reproduction

```powershell
uv run shiftlab-dive-scout-temporal-development `
  --seeds 60 --seed-offset 20274000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_temporal_development_protocol.md `
  --output outputs/scout_context_policy_eventwise_temporal_development_60
```
