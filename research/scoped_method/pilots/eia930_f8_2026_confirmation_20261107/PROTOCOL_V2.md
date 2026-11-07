# EIA-930 F8 temporal confirmation — source-corrected protocol v2

**Status:** frozen before EIA-930 2024–2026 balance CSV outcomes are loaded or scored. This version
corrects protocol v1's wrong source format. Protocol v1 and its failed source-integrity preflight
remain preserved; no outcome analysis was performed under v1.

## Question and scope

For the 11 EIA-930 balancing authorities (BAs) selected by the registered 2022–2023 F8 profile
screen, does the preselected static challenger retain a net-cost advantage over CAMS and the full
registered method panel on the chronological 2026 test stream?

This is a later-period replay on one EIA provider, with the 11 BAs as subclusters. It does not
establish cross-provider generalization, operational electricity utility, or live availability of
revised historical values. Label and switching prices are hypothetical Failure Atlas units.

## Source lock

- Canonical source: official EIA-930 six-month balance CSVs at
  `https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_<YEAR>_<HALF>.csv`.
- Fixed prior sources: the six 2021–2023 files and their checksums in
  `research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json`.
- New files: `2024_Jan_Jun`, `2024_Jul_Dec`, `2025_Jan_Jun`, `2025_Jul_Dec`, `2026_Jan_Jun`, and
  `2026_Jul_Dec`. Freeze their byte counts and SHA-256 values in a source receipt before any test
  outcome metric is computed. The final 2026 file may contain only a partial half-year.
- Test events: `2026-01-01 00:00 UTC` through `2026-10-19 17:00 UTC` at most, matching the last
  complete event in the prior coverage-only audit. Do not use later rows even if present.
- Fixed BA registry inherited from the development profile gate:
  `AZPS, BANC, EPE, ERCO, FMPP, FPC, MISO, NEVP, NYIS, SWPP, TIDC`.
- EIA's public documentation says historical submissions are accessible through its API and
  downloadable six-month CSVs. The CSVs include actual demand, demand forecast, and the imputed
  demand indicator used by the existing model definition. They are current revisions, not
  point-in-time snapshots.

The 2026 period was previously inspected for coverage only. A prior audit found no 2026 scoring in
earlier EIA experiment outputs; retain that audit and re-run the text/manifest exposure check before
opening any 2026 model outcomes. Prior 2024–2025 EIA use in other ShiftLab projects is recorded; it
does not count as independent confirmation for this model pair.

## Frozen model pair and chronology

Recreate the already registered pair exactly: persistence incumbent and per-BA
`HistGradientBoostingClassifier` challenger trained only on eligible 2021 rows, with the BA's 2021
p90 demand threshold, inverse-frequency class weights, the fixed feature definitions, model
parameters, random seed, and 0.5 cut-off from
`research/scoped_method/pilots/eia930_f8_all_ba_development_20261107/PROTOCOL.md`.

At hour `t`, the model uses day-ahead forecast for `t`, actual demand lags through `t-1`, rolling
summaries ending at `t-1`, and UTC calendar features. It predicts whether actual demand at `t`
exceeds the training-year p90. Apply the prior eligibility rule unchanged, including exclusion of
imputed-demand rows. Do not fill missing timestamps or bridge gaps. One requested label matures at
`t+1h`; this is the same assumed delay as development and is not verified release timing.

The static candidate was selected before this test: always deploy model 1 (the challenger), request
zero labels, and charge one switch cost of 5 per episode. No 2026 label, profile, disagreement
statistic, or policy cost may alter that action.

## Episode and method contract

Use complete non-overlapping sequences of 2,000 consecutive eligible hourly events within each
continuous timestamp run. Report and omit incomplete tails, and never join across a gap. Reset each
method and budget per episode. Per episode: `T=2000`, pathwise `B=200`, label price `0.05`, switch
price `5`, `alpha=0.05`, and assumed label delay of one hour.

Primary comparator is `cams_adapter`, fixed as the strongest published-method Failure Atlas F8
discovery method before this test. Secondary published/registered comparator panel is:
PFA-SR:gated_deployment; corrected RMM on the registered hosts; E_rb on the registered host;
SMCS+retain-incumbent; Xu acquisition-only; gated deployment; gated adaptive range; CAMS; Model
Selector adapter; Model Picker adapter; Online LLM Picker; Gong-Zhang; Qiu; variance-min IPW;
economic replacement; and never-switch. Include fixed-incumbent and fixed-challenger controls.
Use the existing registry/fidelity table for exact method identities. Each gets identical model
predictions, label-release queue, episode boundaries, and costs. Record source hashes for method
implementations and configuration.

Primary endpoint is net cost = predictive loss + label expenditure + switching expenditure. Report
each term, labels, switches, promotions, rollbacks, and time-to-first-promotion. Paired contrast is
static challenger minus CAMS. Require at least 5 cost units saved per episode and the hierarchical
paired 95% interval upper bound below zero to pass the primary gate. Bootstrap 10,000 times with
seed `2026110719`, first sampling BAs and then complete episodes within sampled BAs; average policy
random seeds within episode before resampling. Show all BA-specific estimates and interval
limitations. Also show every published method, so a lower-cost applicable published method than
CAMS cannot be hidden by the primary-comparator choice.

## Freeze and stop rules

1. Verify every prior 2021–2023 CSV against its frozen checksum and record new file hashes.
2. Before policy outcomes, verify chronology/exposure audit and fit the frozen model pair only on
   2021 rows; save model hashes, source hashes, BA list, split and test-opening marker.
3. Generate 2026 predictions and costs only after the marker is durable. Save aggregate results and
   prediction-stream checksums, not row-level demand/prediction/loss data.
4. Stop without scoring if a source or prior-file hash fails, 2026 rows appear in old scoring,
   fitting uses post-2021 labels, feature/target timestamps overlap, future features enter a
   prediction, a gap is bridged, or actual release times are claimed from event timestamps.
5. Preserve any failure and all adverse BA-level outcomes.

This confirmation does not satisfy independent-provider validation. A successful result is still
only one-provider chronological transfer for the registered model pair and cost assumptions.
