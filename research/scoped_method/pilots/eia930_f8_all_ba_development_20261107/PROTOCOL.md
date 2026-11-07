# EIA-930 broad-panel F8 profile screen

**Purpose:** determine whether the frozen F8 rare-informative-pair profile occurs in a broader
chronological panel of EIA-930 balancing authorities (BAs). This is a development screen only;
no adaptation policies or economic outcomes are evaluated here.

## Fixed data and split

Use the same six checksum-verified EIA-930 bulk CSVs (2021–2023) listed in
`../eia930_f8_development_20261107/source_manifest.json`. Include every BA appearing in the files;
do not drop a BA based on its profile. Fit each BA's model using 2021 only and evaluate only 2022–
2023. This screen has no access to 2024–2025 outcomes. EIA historical values are revised snapshots;
label release at one hour after the event is simulated. BAs are subclusters of one provider, not
independent data-source clusters.

## Frozen model pair

For each BA, use the same definitions as the earlier three-BA screen:

- Threshold: that BA's 2021 p90 actual demand.
- Incumbent: predict `D[t] >= threshold` iff `D[t-24h] >= threshold`.
- Challenger: HistGradientBoostingClassifier, fit only on eligible 2021 rows, with fixed
  `max_iter=150`, `learning_rate=0.05`, `max_leaf_nodes=15`, `l2_regularization=1.0`,
  `random_state=1729`, inverse-frequency 2021 class weights, and probability cutoff 0.5.
- Features at t: day-ahead forecast, actual-demand lags 1/24/168/336 hours, prior 24-hour mean and
  maximum ending t-1, and sine/cosine encodings for UTC hour, weekday, and day of year.
- Exclude rows with missing features/target, nonpositive actual/forecast, or a populated imputed
  demand field. Rolling windows and lags require uninterrupted hourly timestamps. No 2022–2023
  label is used for fitting or preprocessing.

## Profile-only gate

Report for every BA with sufficient training data: eligible 2022–2023 events, disagreement rate,
challenger accuracy conditional on disagreement, and number of complete contiguous 2,000-hour
development blocks. A BA matches the F8 profile if disagreement is in `[0.01, 0.05]` and
challenger conditional accuracy is at least `0.85`.

Proceed to a separately frozen development policy experiment only if at least five BAs match. If
fewer than five match, stop this EIA/F8 lane. Do not change the model, thresholds, eligibility,
target interval, or gate after seeing profiles. If the gate passes, all matching BAs—not a selected
subset—must enter the next development protocol. A subsequent confirmation claim would still
require untouched chronology and an independent provider/domain.

The screen does not test algorithm performance, economic value, novelty, field validity, or a
statistical guarantee. The prior three-BA screen remains unchanged and separately reportable.
