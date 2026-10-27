# EIA electricity sequential retraining development protocol

**Status:** frozen retrospective event-time development protocol, 2026-10-26.
The source period and test partition have appeared in existing forecast
diagnostics; this is not independent confirmation.

## Data and prediction task

Use EIA EBA processed release `e47bdef8b208f8e7d788`, containing hourly
one-step-ahead demand forecasts for CISO and ERCO from 2023–2025. Each row's
four EBA fields at event time `t` predict the source demand at `t+1 hour`.
Features are treated as available at their event timestamp for this
retrospective replay, although historical publication and revision times are
unknown. The target event time is source-recorded; actual label release time
is unknown. No application-specific decision or operating cost is available.

Use the manifest's chronological `train`, `validation`, `calibration` and
`test` partitions within each balancing authority. Fit the initial Ridge model
on eligible training rows only; leave validation unused; use calibration
rows only to define the trigger threshold; evaluate only test rows. For each
assumed label delay, a source training label is eligible at test start only
when `label_event_time + delay <= first_test_event_time`.

## Frozen model and policies

Use a linear Ridge model with alpha 1, training-pool median imputation,
training-only feature standardisation and an unpenalized intercept. Refit the
imputation medians and scaler with each permitted retraining pool. Fit the
linear solve with PyTorch on CUDA when available and retain CPU fallback. At each test event, a policy may use only
labels whose target event time plus the assumed delay is no later than the
current prediction event. All policies receive the same complete feedback;
there is no label-query policy.

Compare four policies:

1. **Frozen:** never refit after test begins.
2. **Weekly:** refit every 168 event hours when at least one new label has matured.
3. **Monthly:** refit every 720 event hours under the same rule.
4. **Error trigger:** refit when the mean squared residual among the latest
   24 hours of arriving feedback exceeds the 95th percentile of 24-hour
   rolling squared error from the calibration period under the frozen model;
   enforce a 168-hour cooldown and require new matured labels since the last
   fit.

This threshold trigger is a conventional heuristic, not an anytime-valid
test. The delay-sensitivity values are imposed assumptions, not estimates of
historical EIA latency. Periodic and trigger schedules are fixed in advance;
no tuning uses test labels.

## Outcomes and interpretation

Report RMSE, MAE and MSE by balancing authority, assumed delay and test month,
plus total updates, fitting time, cumulative training rows processed, and
matured feedback count. Present forecasting error against update resources
as a Pareto comparison; do not convert compute or update counts into
invented electricity-system utility. Do not combine CISO and ERCO into an
independent sample count. Existing diagnostics have used this test period, so
all outputs are development/descriptive. There is no causal adaptation
effect, application decision value, real-time guarantee, or claim that the
heuristic trigger controls false alarms.

## Integrity checks

Verify source manifest/data hashes, hourly unique chronology, no infinite
predictors, finite outcomes, training-pool imputation, deterministic fit/prediction,
nonnegative delay, no label consumed before `label_event_time + delay`, and
identical test-event coverage across policies at each delay. Save aggregate
monthly metrics and a manifest with source, protocol, script and output
hashes. Do not write row-level forecasts or labels to the output directory.
