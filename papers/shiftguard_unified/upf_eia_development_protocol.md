# UPF on EIA: retrospective development comparison protocol

**Version:** 0.1  
**Status:** frozen for one exploratory development run; not confirmation and not preregistered.  
**Primary method:** independent implementation of the published UPF finite-horizon cost rule in `src/shiftlab/dive/upf_retraining.py`.  
**Source:** EIA EBA release `e47bdef8b208f8e7d788`.

## Question and scope

Can the UPF forecast-and-quantile retraining rule reduce the declared bounded forecasting-loss-plus-update-cost objective relative to no retraining, periodic retraining, and a fixed error-threshold rule on this retrospective electricity series?

This is a Q3 resource/retraining development comparison. It is not a paired decision-harm test, does not use an anytime-valid certificate, and does not represent observed electricity-system utility. The source's historical feature publication, target revision and label availability times are unknown. All results are retrospective event-time replay under explicit additional-delay assumptions. Existing diagnostics have inspected the source period, so this experiment cannot serve as independent real-data confirmation.

## Data and chronology

Use the verified EIA EBA release `e47bdef8b208f8e7d788` and its four features (`D`, `DF`, `NG`, `TI`) to predict the next-hour `D` target. Run CISO and ERCO separately. Keep the full recorded hourly order, including the few rows whose legacy split is `unassigned`; the original split label is retained for exposure auditing but does not define the new temporal blocks.

For each domain, sort observations by event time and divide the ordered series into 15 contiguous, near-equal periods. Periods 0–6 are offline forecaster development; periods 7–14 are the online retraining horizon. Within each period, the first 80% of rows by event order form the information/training prefix and the last 20% form its held-out evaluation tail. The model decision is made at the start of that tail. Only prefix labels mature by that decision time may enter the candidate model. The evaluation tail is never used to fit the model scored on that same tail.

The availability rule is a sensitivity convention: a label becomes usable at `label_event_time + delay_hours * 3600`, for delays 0 and 168 hours. The original one-hour target horizon remains in `label_event_time`. At each period decision, retain only rows whose features occur before the evaluation-tail start and whose target labels have matured by that start. Earlier evaluation tails can enter later candidate training pools only after their labels mature. Predictor availability is assumed at its event timestamp; no source evidence establishes that assumption in real operation.

## Loss and costs

The regression target is not bounded. To use the paper's Beta performance forecaster, define a bounded normalized absolute-error score

`loss = min(abs(target - prediction) / S, 1)`.

For each domain, set `S` once to the 1.4826-scaled median absolute deviation of target values in the training prefix of period 0, with a floor of `1e-6`. This uses no evaluation-tail outcomes. Record `S`, the fraction of evaluation errors clipped at 1, and raw MAE/RMSE alongside the bounded score. The bounded score is a ShiftLab adaptation of the paper's classification loss; it is not a publisher metric and clipped-loss calibration is not guaranteed.

For the finite-horizon objective, each evaluation period has equal weight. A retraining at a period boundary incurs a constant relative cost `alpha`; no unit conversion to dollars, electricity operations or system utility is made. For each domain and delay, the evaluator computes `alpha_max` as the largest break-even value over all online retraining schedules at which the full-information oracle still benefits from at least one retraining. Evaluate 10 equally spaced `alpha` values from 0 through `alpha_max`, inclusive. This oracle-derived range is for frontier display only; it is never an input to the learner's choice except as the requested `alpha` operating point.

## Models and information contract

Use the existing four-feature Ridge model with alpha 1, median imputation and standardization fitted on the eligible training pool. Fit the linear solve with PyTorch on CUDA when available, with CPU fallback. The model family is frozen across periods. The evaluator may precompute every period-specific candidate Ridge model and its held-out losses to construct an oracle; learner policies only receive candidate models they train at that point and observed losses for models they have already trained.

UPF offline fitting uses the performance matrix from models trained at each offline period and their eligible evaluation tails at that period and later offline periods. An observed performance entry is admitted to the forecaster only when its evaluation label tail has matured by the current decision time. At each online period, refit the forecaster from the currently available observations; use the current observed raw feature-centroid shift between the period prefix and the preceding period prefix, held constant when forecasting future periods. Do not expose evaluator-computed future losses, `alpha_max`, oracle schedules, or future feature summaries to the policy.

The UPF parameterization follows the audited primary paper: ElasticNetCV mean prediction on `[model time, evaluation time, time since training, L1 mean-feature shift]`, constant in-sample residual variance, moment conversion to Beta parameters, independence across forecast performance cells, and 0.95 quantiles of total cost under retrain versus keep. Monte Carlo uses a fixed seed per domain/delay/alpha/decision and 10,000 draws. The disputed Proposition 3.1 retraining-count bound is not used.

## Comparators

On the exact same period partitions, trained candidate sequence, bounded loss, delays, and cost grid, report:

1. `never`: retain the period-6 model throughout the online horizon.
2. `periodic_2`: retrain at the start of every second online period.
3. `periodic_4`: retrain at the start of every fourth online period.
4. `error_threshold`: retrain when the most recently matured normalized evaluation loss for the active model exceeds the 95th percentile of the seven offline diagonal model losses; freeze this threshold before online evaluation.
5. `UPF`: recompute the forward finite-horizon policy at each decision from matured performance entries; execute only its first decision, then refit after new feedback.
6. `oracle`: enumerate all 2^8 online retraining schedules using the full evaluator performance matrix; use only as a non-achievable lower bound.

The policy frontier is exploratory and does not complete the SOTA requirement. In particular, this protocol omits CARA and the paper's drift-detector baselines; those require separate source-level implementations before a final Q3 comparison. Do not label this comparison SOTA-complete.

## Outcomes and stopping rule

Primary outcome: sum of mean bounded normalized absolute loss over the eight online periods plus `alpha` times the number of retraining events. Report the 10-point cost frontier and its normalized AUC separately for CISO and ERCO. Also report raw MAE/RMSE, number of retrains, fit rows, fit time, clipping fraction, per-period losses, and the oracle schedule. These two balancing authorities are not independent replications; show each as a separate descriptive trace and do not use event-level rows as independent uncertainty units.

Run exactly the two domains × two delays × the fixed alpha grid. Stop after all configurations complete and integrity checks pass. Do not change the loss scale, block count, feature-shift statistic, quantile, cost grid, or policies after seeing online outcomes. Any change creates a new development protocol and must retain this run's artifacts.

## Integrity and provenance

Before execution, copy this exact protocol into the output directory and hash the copied bytes. Record source manifest and observation hashes, script and method-module hashes, environment, GPU model, period boundaries, label-delay rules, bounded-loss scales, every alpha value, all per-period policy outcomes, output hashes, prior-exposure status, and the explicit adaptation limitations. Verify that all training rows precede each evaluation tail, all labels satisfy the assumed maturity cutoff, the UPF forecaster excludes future performance entries, all policy metrics cover identical evaluation rows, and the oracle is not used in any learner decision.

No row-level predictions, labels, or raw observations are written to outputs. No scientific figure is produced in this development run.
