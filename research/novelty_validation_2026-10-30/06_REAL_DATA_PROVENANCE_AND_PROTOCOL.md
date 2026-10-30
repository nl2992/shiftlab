# 06. Real-data provenance and protocol

Status: written **2026-10-30 before any outcome on D2 was computed** (commit precedes the first run of
`scripts/d2_gas_sensor_replay.py`). Only D2 (UCI gas) is executed in this programme. D1, D3, D4 are specified
or assessed below and **not executed**; no real-data claim is made for them.

## Acceptance table

| dataset | licence / source | access this session | checksum recorded | executed? |
|---|---|---|---|---|
| D2 UCI Gas Sensor Array Drift (id 224) | CC BY 4.0 (read from the UCI dataset page); official URL `archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip` | HTTP 200 | zip SHA-256 `91e8f466f202e7a093d657673ce47311c3e90416f7df3057966058961c351fe4` (9,989,262 bytes); batch10.dat is the 10/14/2013 corrected version per the UCI page | **yes (exploratory)** |
| D1 NYC TLC yellow trips | public TLC data; the TLC web page returns HTTP 403 to this proxy, the CloudFront parquet host answers 200 (e.g. `yellow_tripdata_2019-01.parquet`, 110,439,634 bytes, ETag `564a9f76dd7c9554718f6ea0c2c372fe-7`, HEAD request only) | CDN reachable; **no file downloaded or analysed** | not recorded (nothing downloaded) | **no** |
| D3 WILDS | official site not contacted this session; earlier repository work already used WILDS CivilComments (see `docs/next_phase_plan.md`, Q2 development) | not re-verified | – | **no** |
| D4 CRSP/WRDS | licensed; no credentials in this environment | blocked by construction | – | **no** (existing replay is exposed 2020–2025 and stays exploratory) |

## D2 design (frozen before running)

Feature/label availability. Source has 128 sensor-response features, 6 gas classes, 13,910 rows in 10 batches
ordered by acquisition month (UCI table: batch 1 = months 1–2; batch 2 = months 3, 4, 8, 9, 10; batch 3 =
months 11–13; later batches later months). **There are no event timestamps, no feedback delays and no
within-batch order guarantee.** Everything below that mentions a delay or a label rate is a *counterfactual
replay*: labels are revealed by a simulated random query mask with a fixed 5-event release delay.

Task and decision loss (declared before outcomes). Positive class = gas 6 (the convention already used in the
repository's gas candidate work, so no new cost setting was searched). Decision: raise the alarm action when
`P(class 6|x) >= 1/6`; loss FN = 5, FP = 1 (the repository's `generators.FN_COST/FP_COST`). Economic
tolerance for the primary null: `eps = 0.10` per event (the repository's long-standing harm threshold; not tuned
on gas). Secondary, descriptive: `eps = 0`.

Partitions. Train: batch 1 only (logistic regression on standardised features, `C = 1.0`, no tuning).
Calibration: a fixed random half of batch 2 (seed 20261030), used for the nominal risk
`r0_ucb = mean + 5*sqrt(ln(1/0.01)/(2 n_cal))` (Hoeffding, range [0,5], `delta_S = 0.01`). Alarm budget
`alpha_T = 0.04`, so the total budget is 0.05 (calibration allocation explicit). Streams:
* **A (real-data null).** The *other* random half of batch 2, independently re-ordered for each of 300 replicates.
  By construction exchangeable with the calibration half; the cost-null therefore holds for the
  marginal pooled risk. This tests calibration + e-process validity on real features. Replicates reuse the
  same 622 rows, so the 300 replicates are **not** independent datasets.
* **B (documented-order drift).** Batches 3–10 concatenated in the documented order, file order within batch.
  There is no causal shift label; I do not define power or "false alarm" for B. Reported: alarm rate across
  300 label-mask seeds, alarm index, labels at alarm, and the evaluator-side realised excess cost accumulated
  before the alarm.

Arms (identical stream, proxy model, label mask, delay, calibration, `alpha`): C0 cost parent, C1 cost
discounted Kelly, C2 cost ONS, H2c (`guided_disc`, gamma 0.995), and a supervised Hoeffding-stitched risk
monitor in the Podkopaev–Ramdas style (`SOURCE_INSPIRED`: labels only, not their CM-EB, not a verified
reproduction). Label rates 5/10/20 %. Primary hypothesis (no result peeked): **H2c is not worse than the better
of C1/C2 in alarm index on B at eps = 0.10**; a failure of this is a reportable negative result.

Exposure statement. Earlier repository work already inspected batches 3–10 (`docs/next_phase_plan.md`, "UCI Gas
Sensor batch-held-out Q2 development", 5×class-6 cost, negative transfer). **D2 therefore cannot be CONFIRMED
evidence for any claim; it is EXPLORATORY.** It is a second domain for transfer *description*, not confirmation.

Known limitation recorded in advance: batch 2 mixes months 3–10, so "calibration" already contains drift
accumulated over months; stream A is exchangeable by construction but does not represent a pre-drift regime.

## Reproduction

```bash
uv sync --all-extras
curl -L -o gas.zip https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip
sha256sum gas.zip   # must equal the checksum above
.venv/bin/python research/novelty_validation_2026-10-30/scripts/d2_gas_sensor_replay.py gas.zip research/novelty_validation_2026-10-30/outputs
```
