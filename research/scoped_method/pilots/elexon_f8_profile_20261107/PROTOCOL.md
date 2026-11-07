# Elexon F8 cross-operator profile screen

**Status:** frozen development protocol. This checks whether the EIA high-load model-pair profile
transfers to an independent operator with authentic forecast and actual publication records. It
does not open 2026 outcomes, evaluate adaptation costs, or claim method novelty. The model pair and
fixed-challenger policy are conventional model-selection baselines; this is a cross-operator case
study screen, not a new-method experiment.

## Source and chronology

- Elexon BMRS stream datasets: Actual Total Load (`ATL`) and Day-Ahead Total Load Forecast
  (`DATL`), official API `https://data.elexon.co.uk/bmrs/api/v1/datasets/{ATL|DATL}/stream`.
- Official docs identify `publishTime`, `startTime`, `documentId`, `documentRevisionNumber`, and
  quantity fields. The prior metadata audit verified repeated forecast vintages and sampled actual
  publication about 25 minutes after a half-hour interval ended. Preserve UTC timestamps and
  document IDs; revision number alone is not a vintage key.
- Raw responses for the profile screen are limited to training targets in calendar 2024 and
  development targets in calendar 2025, plus only the 2023-12 forecast history and matured ATL
  history needed to construct point-in-time features. Do not request, parse, or score any 2026 valid
  time or forecast for a 2026 target. The last day of 2025 is excluded if a label would require
  reading a 2026 publication window.
- Store quantities only in ignored `data/raw/`; publish response hashes, counts, and schema metadata,
  not row-level load values.
- BMRS data use is subject to Elexon's open-data licence. Any artifact that uses the data must
  include the attribution `Contains BMRS data © Elexon Limited copyright and database right 2025`
  and link to the [BMRS data licence](https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/).
  Do not imply Elexon endorsement.

## Prediction task

- Unit: GB bidding zone; event: one half-hour UTC settlement period, aligned by `startTime`, never by
  local settlement period number. Preserve spring/autumn DST periods using UTC valid times.
- Target: actual load at target period `t` exceeds the p90 threshold computed from first-published
  2024 ATL values only.
- Issue time: `t - 12 hours`. For each target, select the latest DATL vintage with `publishTime`
  no later than that cutoff. Never use a later revision, even if the API now exposes it.
- Incumbent: classify the as-of issue-time DATL forecast against the frozen 2024 p90 threshold.
- Challenger: a per-source `HistGradientBoostingClassifier` with the EIA F8 registered parameters
  (`max_iter=150`, `learning_rate=0.05`, `max_leaf_nodes=15`, `l2_regularization=1.0`,
  `random_state=1729`) and balanced class weights. Features are the as-of DATL forecast, the most
  recent ATL values whose `publishTime` is no later than issue time (lags 1, 48, 336 valid periods),
  a 48-period rolling mean and maximum over mature actuals, and fixed UTC calendar encodings.
  Fit only on 2024 targets; no 2025 labels may enter preprocessing or fitting.
- Use the first ATL publication for each valid time as the policy-visible label and release time.
  Report duplicates/revisions. Policy evaluation, if later authorized by the gates, must release
  each queried label at its recorded first `publishTime`, mapped to the first subsequent issue event
  at or after publication. No fixed-delay approximation is used when the authentic release exists.

## F8 profile gate

Evaluate the frozen model pair on 2025 only. The F8 profile must hold separately in both 2025
half-years: disagreement rate in `[0.01, 0.05]` and challenger accuracy conditional on disagreement
at least `0.85`. Each half-year must contain at least four complete, nonoverlapping 2,000-event
blocks after applying eligibility. Do not retune parameters or cutoffs by half-year. This requires
stability across two chronological blocks; it does not create two independent source clusters.

If either half fails, stop this model-pair lane and keep 2026 closed. If both pass, preserve the
profile result and require a separate development/novelty gate before computing policy economics.
Any later Elexon evaluation remains one operator; cross-domain generalization requires another
independent source, such as the existing EIA replay, and must use source-level uncertainty.

## Interpretation and cost boundary

This screen establishes only the presence of an F8-like real prediction profile. The HGB model and
fixed-challenger rule are conventional methods. Cost weights from Failure Atlas are hypothetical
benchmark units, not electricity-market utility. A later policy experiment must account for the
full common event horizon, pathwise label budget, label costs, switching costs, authentic release
queue, promotion timing, and adverse periods; the temporal profile result alone cannot establish
deployment benefit.

## Reproduction record

Record exact API publication windows, request/response hashes, code and dependency hashes, valid-time
counts, first-published ATL policy, as-of DATL vintage rule, DST handling, client/source cluster
count, and full half-year profile metrics in `RUN_STATUS.md` and `DATASET_PROFILE.json`. Preserve any
API, vintage, timestamp, missingness, or model-fit failure. Do not overwrite a completed profile.
