# EIA 2026 out-of-time replay protocol v1

**Status:** frozen before computing any 2026 predictive metrics. This is a retrospective event-time confirmation of the existing EIA forecasting/retraining comparison, not an operational deployment or decision-utility study.

## Question and scope

Do the previously specified frozen, periodic, and error-triggered Ridge retraining policies retain their forecasting-risk/resource behavior on the newly available 2026 CISO and ERCO event period? This addresses external temporal transfer for predictive risk and update resources only. It does not test downstream electricity decisions, economic utility, prospective feedback availability, or a distribution-free false-alarm guarantee.

## Source and exposure

Use the local official EIA EBA snapshot at `data/raw/eia/EBA.zip` (SHA-256 `3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f`; retrieved 2026-10-20; receipt says source `Last-Modified` 2026-10-19). The 2026 source coverage check found CISO/ERCO demand (`D`) through 2026-10-19 18:00 UTC, demand forecast (`DF`) through 2026-10-20 07:00/05:00 UTC, and other selected predictors (`NG`, `TI`) through 2026-10-19 06:00/04:00 UTC. The full archive covers 2019-01-01 onward. This coverage-only inspection did not compute errors, fit models, or inspect policy comparisons on 2026 outcomes.

Prior ShiftLab EIA development uses processed version `e47bdef8b208f8e7d788` and stops in 2025. Before confirming eligibility, the runner must assert no 2026 target record is present in any earlier result artifact and record exact source, processing, and output hashes. Source historical publication and revision times are unknown. The replay therefore uses event time as a retrospective ordering convention, with no claim of actual live availability.

## Fixed task and partitions

For each balancing authority separately, predict next-hour EIA demand `D[t+1]` from the four EBA values `(D[t], DF[t], NG[t], TI[t])`. Include only finite target rows with the complete feature vector and an exactly one-hour target-event gap. Use the source snapshot at its current revision. Assign chronologically:

- **Training:** eligible events from 2019-01-01 through 2024-12-30 23:00 UTC.
- **Calibration:** eligible events from 2025-01-01 through 2025-12-30 23:00 UTC; only the frozen error-trigger threshold may use these labels.
- **Final test:** eligible events from 2026-01-01 through the last complete one-step forecast available in the source, no later than 2026-10-19.

The final test outcomes are evaluator-only. No 2026 outcomes may affect fitting, calibration, policy choice, thresholds, or code changes. There is no tuning split in this frozen confirmation; the training algorithm and policy constants are taken unchanged from `eia_retraining_protocol.md`.

## Frozen policies and feedback assumptions

Use the existing Ridge model (alpha 1), training-pool median imputation and standardization, and the existing policies `frozen`, `weekly`, `monthly`, and `error_trigger`. Keep trigger window 24 hours, calibration quantile 0.95, and cooldown 168 hours. Apply assumed label delays `{0, 24, 168}` hours. Every policy receives the same complete matured feedback; target labels mature at `label_event_time + assumed_delay`. These are delay sensitivities, not observed EIA release times. No policy may train on a label before that assumed maturity time.

If an authority has a missing hourly event, do not fabricate observations or carry values forward. The runner must preserve source gaps, process delayed labels in event-time order, and report gaps and eligible-test counts. Weekly/monthly schedules are measured in elapsed event hours. If the current runner's contiguous-hour invariant cannot support source gaps, stop and implement a gap-safe equivalent before looking at 2026 scores; do not silently drop or interpolate rows.

## Outcomes, comparisons, and uncertainty

Primary outcome is test RMSE; resource outcome is cumulative refit rows by policy, authority, and delay. Secondary outcomes are MAE, MSE, number of updates, matured labels, and fitting time. Compare each adaptive policy with `frozen` on the exact same test events. For paired differences in RMSE, MAE, and MSE, resample 168-hour blocks with replacement, anchored at 2026-01-01 00:00 UTC; use 10,000 draws and seed `20261026`, separately for CISO and ERCO. Report the number of populated blocks. These intervals are descriptive and are not multiplicity-adjusted; do not treat the two authorities or individual hours as independent deployments. With at most one held-out period per authority, uncertainty cannot establish general future performance.

Show the error/resource Pareto frontier. Do not convert fitting rows, update counts, or forecast error into electricity cost or operational utility. The error trigger is a repeated-look heuristic and carries no anytime-valid guarantee. Report all three delay settings and all authorities, including failures and missingness.

## Stop conditions and artifacts

Stop without scoring if source hashes fail, any 2026 outcome appears in a prior ShiftLab result, train/calibration/test chronology overlaps, a future label enters a fit, predictions are not one-step aligned, the runner changes any frozen method setting, or source gaps make the policy timing ambiguous. Save the split manifest, series coverage and missingness audit, per-policy/per-delay aggregate CSV, paired block-bootstrap intervals, device/runtime record, source/protocol/script/data hashes, and a report that states the timing and utility limitations. No row-level forecasts or targets may be written to outputs.

This EIA period is only one real task family. It does not satisfy the separate requirement for an independent real downstream intervention/resource-allocation evaluation.
