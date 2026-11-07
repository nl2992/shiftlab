# UCI ElectricityLoadDiagrams F8 profile screen

**Status:** frozen development protocol. This is one bounded independent-domain screen of the
Failure Atlas F8 rare-informative model-pair condition. It does not open a confirmation holdout or
make a method-novelty claim.

## Source and attribution

- UCI Machine Learning Repository dataset 321, `ElectricityLoadDiagrams20112014`, DOI
  `10.24432/C58C86`, licensed CC BY 4.0.
- Official record: <https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112>.
- Download: <https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip>.
- The publisher describes 370 client series, 15-minute kW values, Portuguese local timestamps, and
  zero-filled history before some clients began contributing. It notes DST artifacts despite 96 rows
  per day. The file is semicolon-separated with decimal commas. The source has no verified
  label-release log; any delayed feedback used later must be described as simulated.
- Save the raw archive under the ignored `data/raw/` tree, record URL, retrieval time, byte count and
  SHA-256, and never add raw data to Git.

## Fixed task and chronology

- Unit: client; event: one ordered 15-minute source row. Preserve source row order and original
  timestamp strings. Do not reinterpret local timestamps as UTC or bridge rows.
- Eligible clients are determined from 2011 only: require at least 20,000 nonzero observations in
  that year and at least two observed classes for the fixed high-load target. This excludes series
  with insufficient pre-deployment training history without looking at later entry or outcomes.
- Target threshold per eligible client: 2011 p90 among positive observed loads. Label is whether
  event load meets/exceeds that frozen threshold. Use only 2011 for threshold and model fitting.
- Incumbent: previous-day persistence, thresholding the load 96 source rows earlier.
- Challenger: `HistGradientBoostingClassifier` with the EIA-F8 registered parameters
  (`max_iter=150`, `learning_rate=0.05`, `max_leaf_nodes=15`, `l2_regularization=1.0`,
  `random_state=1729`) and balanced class weights. Features use only information available before
  the event: lag 1, 96, 672, and 1,344 rows; trailing 96-row mean and maximum ending at `t-1`; and
  fixed cyclic encodings of event index within day/week/year. Do not use target-time load or
  future-derived preprocessing.
- Development: fit on 2011; screen profile and candidate coverage on 2012 only. Confirmation
  partition: 2013–2014 remains unopened in this run and cannot be used to change the model, client
  eligibility, target, thresholds, or decision rule.
- The source's first row is `2011-01-01 00:15:00`; the frozen training partition has 35,039 rows
  through `2011-12-31 23:45:00`, and development has the following 35,136 rows through
  `2012-12-31 23:45:00`. The program must stop at this boundary and not read the next row.
- F8 profile: in 2012, challenger disagreements must be 1–5% of eligible events and challenger
  accuracy on disagreements must be at least 85%. Report every eligible client's result; do not
  select favorable clients after seeing profile outcomes. A prospective deployment rule would
  apply challenger only to clients meeting this validation profile, otherwise retain the
  incumbent. This is ordinary validation-based model selection and is not presumed novel.

## Screening and stop rule

This stage only establishes whether the F8 data condition occurs on an independent source with
chronological model training. Report every eligible client, profile metrics, and time-block
uncertainty. Require at least 20 clients to match before constructing a policy replay; the minimum
provides multiple client clusters and is fixed before acquisition. If fewer than 20 match, stop this
dataset lane without changing the thresholds or opening 2013–2014.

If the profile screen passes, a separate protocol is required before any economic policy outcomes
are computed. It must specify how 2012 validation labels and their cost are treated, give all methods
identical information, compare against CAMS/SMCS/gated/never-switch and the matched fixed controls,
and state how client and common-time dependence enter the interval. The test years remain closed
until a candidate first passes fresh synthetic falsification and a targeted novelty audit. Any
future replay will use a clearly labeled simulated 24-hour feedback delay unless authentic
publication/release times are sourced.

## Reproduction record

After raw acquisition and implementation, add exact commands, dependency versions, source checksum,
model/code hashes, row counts, client eligibility counts, and profile results to `RUN_STATUS.md`.
Preserve adverse outcomes and any parser/chronology failures.
