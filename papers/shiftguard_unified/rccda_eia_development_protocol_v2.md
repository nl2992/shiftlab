# RCCDA on EIA: matched retrospective development protocol

**Version:** 0.2  
**Status:** frozen before the corrected RCCDA rerun; exploratory development only, not preregistered and not confirmation. This v2 supersedes v1 because the matched UPF reference's evaluator-only oracle was misaligned by one offline period.  
**Question:** Does the published RCCDA resource-scheduling rule provide a useful loss-versus-update-cost operating point relative to the existing EIA retraining policies when its gain estimate is computed only from feedback mature at the decision time?

## Scope and interpretation

This is a task-specific adaptation of RCCDA to the existing EIA electricity forecasting replay. It is not a reproduction of the paper's PACS or DigitsDG experiments, and it is not a test of an anytime-valid decision-harm certificate. The EIA periods have already been inspected during earlier development; results are exploratory and cannot count as independent real-data confirmation. The two balancing-authority series are separate case studies, not independent replications.

The data source is processed EIA release `e47bdef8b208f8e7d788`. For each balancing authority, retain the existing protocol's 15 contiguous, near-equal event-time periods, period-specific Ridge candidates, bounded normalized absolute-error outcome, eight online periods, two assumed label delays (0 and 168 hours), and ten-point `alpha` grid. Reuse the corrected UPF v2 run only after its dataset manifest hash, observation hash, domains, delays, periods, and alpha values match. Do not tune or select RCCDA parameters using the online outcomes.

## Information available to RCCDA

At each online period's evaluation-tail start, RCCDA may use only matured held-out losses whose label event time plus the registered delay is no later than that decision time. The first online decision is initialized from diagonal held-out losses for the seven offline periods, filtered by the same maturity cutoff. Later decisions append the most recent prior online evaluation tail, scored under the model that was actually active in that period, only when at least 20 labels from that tail have matured. If fewer than 20 are available, no new feedback summary is added; the method reuses the last available feedback summary and records its source period and row count.

The loss-history estimator is

`G_hat_t = Kp * (L_t - min_{s <= t} L_s) + Kd * (L_t - L_{t-1})`.

Use the official common setting `Kp=1`, `Kd=0.3`, `V=10`, target average update rate `lambda_bar=0.1`, and equal update-cost parameter `lambda=1`. The decision rule is `V * G_hat_t >= lambda * Q_t + 0.5 * (lambda^2 - 2 * lambda * lambda_bar)`. Update the virtual queue as `Q_{t+1}=max(0, Q_t + lambda * I(update) - lambda_bar)`. The policy promotes the candidate trained from the current period's eligible prefix when it chooses an update; otherwise it retains the current incumbent.

The official paper's average-resource argument assumes an ideal gain estimator. Here the estimator uses finite, delayed, history-dependent EIA feedback, and the eight-step replay is too short to infer an asymptotic rate guarantee. Therefore report the realized update count and queue trajectory; do not describe 0.1 as a hard cap or claim the theorem guarantees the observed schedule.

## Paper and reference-code fidelity

The method is based on the RCCDA paper's published threshold, queue transition, and common parameter setting. The official repository is recorded at commit `91d0558f0b77d476b69d4e21aaa16c9e69881831`. Its inspected PACS evaluator appends the current loss and then reads that same last element as `loss_prev`, which removes the derivative term. This adaptation uses the prior available loss in the paper's displayed estimator and records that discrepancy. It is a correction to the inspected evaluator behavior, not a claim that the official paper's experiments were reproduced.

## Comparators and outcomes

Compare on identical candidate models, period tails, delay assumptions, and evaluation rows against the frozen run's `never`, `always`, `periodic_2`, `periodic_4`, `error_threshold`, `upf`, and evaluator-only `oracle` schedules. The oracle is included only as an unattainable reference and is never exposed to RCCDA. It is computed across exactly online periods 7–14; the v1 output's oracle schedule started at offline period 6 and is superseded. RCCDA's scheduling rule is fixed across the `alpha` grid; `alpha` is used only to display the same loss-plus-update-cost frontier as the existing policies.

Report for each authority, delay, method, and alpha: cumulative bounded loss across the eight online periods, update count, and total normalized objective `sum(period bounded loss) + alpha * number of updates`, alongside period-level bounded loss, MAE, RMSE, and clipping fraction. Also retain RCCDA's feedback periods and counts, current/previous/best loss estimates, estimated gain, decision threshold, and virtual queue before/after each action. Do not pool the two authorities as independent observations or attach inferential confidence intervals to their hourly rows.

## Integrity, stopping, and claims

Stop after the fixed two authorities x two delays x ten alpha values are executed and integrity checks pass. Check identical alpha grids and evaluation keys against the frozen UPF artifact, absence of duplicate method-period keys, expected row counts, source and data hashes, and output artifact hashes. Keep raw observations, labels, and row-level predictions out of the outputs.

The result can establish only how this fixed RCCDA adaptation behaved on these inspected EIA event-time replays under the specified delay and cost scenarios. It cannot establish real-time availability, causal intervention value, independent external generalization, statistical certification, strict finite-horizon budget compliance, or superiority in general. No scientific figure is produced in this run.
