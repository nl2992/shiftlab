# R0: metadata-only real-data eligibility audit (Lane B)

**Date:** 2026-10-28. **Gate:** R0 (tick 6 mission). **Status:** audit only. No data values were read
into this document or into any report. No downloads. No eligibility claim for confirmation.

## Scope and method

Datasets that `switching_real_data_eligibility_v1.md` (Lane A) did not assess: Binance, OPSD, NOAA,
FRED, elec2, Gas Sensor, Monash, and Folktables (brief). Contract tested: `switching_problem_v1.md`
(two frozen policies, losses l_t(0), l_t(1) identified by one queried common outcome; labels visible
at t+d; pending labels charged at request; hard budget B; switching cost k; query cost c) plus Lane A's
G4 dependency list (a)-(e) in `switching_real_data_eligibility_v1.md`.

Only these were inspected: file lists and sizes, receipts, `dataset_manifest.json`, parquet schemas,
row counts, timestamp ranges, per-split and per-batch row counts, per-year non-null counts for six OPSD
columns, the OPSD `datapackage.json` field descriptions, the adapter code `src/shiftlab/data/real/binance.py`,
and existing audit docs. Inspection scripts live in `C:/Users/nigel/AppData/Local/Temp/claude/laneb_r0/`.
The main checkout's `.venv` interpreter was used with `-I`.

Cross-cutting facts that decide most verdicts:

1. **Label queries are free in every dataset here** (finance, power, weather, macro, benchmark
   classification). A hard label budget is therefore always an imposed constraint. The only honest
   interpretations of query cost are: (i) analyst or audit-review capacity, (ii) a recalibration or
   retraining compute budget, or (iii) a deliberately imposed information scarcity. Say which one in R1.
   The single partial exception is Gas Sensor, where ground-truth gas identity needs a costly lab
   exposure in the physical setting, but it has no clock.
2. **No dataset here has a documented switching cost.** No fee schedule or operational cost document
   exists in the repo. A search of `docs`, `papers`, `configs` and `src` for taker, maker, fee schedule
   and trading fee found nothing for Binance. Hits for commission and transaction cost concern CRSP
   and are imposed. Any fee schedule would be an external source, time-varying, and needs a dated,
   hashed snapshot. That would need a download, which is out of scope here.
3. **Every manifest records `ground_truth: none` (Gas Sensor: `coarse_domains`) and "no verified
   changepoints".** Burst or onset structure cannot be taken from the data. Under AGENTS.md it must not
   be inferred from alarms or from convenient cost settings.
4. **The processed schema leaves `prediction_time` and `label_available_time` null** in Binance, OPSD,
   NOAA, Gas Sensor and Monash. Only FRED fills `label_available_time`, as a derived end-of-day
   assumption. Availability clocks are therefore not in the standardized data. They must come from the
   source's documented mechanics or an imposed assumption, and R1 must say which.

## Per-dataset table

| | Binance | OPSD | NOAA | FRED | elec2 | Gas Sensor | Monash |
|---|---|---|---|---|---|---|---|
| **Local extent** | `raw/binance`: BTCUSDT 1d 2023-01 (30 usable bars), ETHUSDT 1h 2025-01 (743 usable bars; splits train 371, val 111, cal 112, test 149) | `raw/opsd/2020-10-06/hourly.csv` (130 MB, 50,401 rows, 300 columns), UTC 2014-12-31 23:00 to 2020-09-30 23:00 | `raw/noaa`: 3 stations, calendar 2023 only, 41,194 usable records (about 13.4k per station); irregular reports | `raw/fred`: 5 series, observation window 2022-2023, 630 revision records (UNRATE alone: 37) | `raw/elec2/electricity-normalized.arff`, 45,312 rows, 3.1 MB | `raw/gas_sensor/uci-224.zip`, 13,910 rows, 128 features, 10 ordered batches (sizes 161 to 3,613; batch 10: 3,600) | Five `.tsf` archives (M4 hourly/daily/weekly, electricity_hourly, weather); processed subsets of the first 10-20 series |
| **(1) Common-label pairing** | Yes. One next-bar return scores any two position rules; both action losses follow from it under a price-taker, no-impact assumption (stated, not observed). | Yes. One realised hourly load scores any two forecasters. The file carries a published TSO day-ahead load forecast column (`DE_load_forecast_entsoe_transparency`, complete 2015-2020) and actual load, so a published forecast and a frozen model can be paired on the same outcome. | Yes. One realised next observation scores any two forecasters. Horizon is irregular ("next later report"). | Yes in principle (a release value scores two nowcasts) but only about 25-37 releases per series. | Yes, a class label scores two classifiers. Target is a moving-average price direction, not an executed outcome. | Yes. A gas class label scores two classifiers. | Yes, a held-out value scores two forecasters. Official final-horizon split only. |
| **(2) Verified availability clocks** | Strongest of all. Open and close times are exact UTC; the adapter's calendar check requires no missing, duplicate or shifted bars. For the next-bar return the label is determined at the next bar's close. Features need the current bar's close. So decision at bar close, **label delay is exactly one interval (1 h or 1 d)**. Publisher SHA-256 verified on both zips. Caveat: the stored `event_time` is the bar *open*; `label_event_time` minus `event_time` is 7,200 s for 1 h bars, so the learner-side delay is one bar after the decision. R1 must define the decision time as bar close, not event_time. Archive publication latency of the files is unknown and irrelevant for a replay. | Event times exact (UTC, with CET/CEST strings cross-checked by the adapter). Release times **not in the data**. `limitations` states "publication lag unknown" and that the snapshot may contain revisions. Actual load is published by ENTSO-E with a regulatory deadline, and the day-ahead forecast before gate closure. That would give an auditable fixed-delay contract, but it is **external knowledge not documented in the repo**: the citation must be pinned in R1 and checked. Receipt shows `publisher_checksum_verified: false` for the CSV. | Measurement times exact, release latency explicitly unknown. | Conservative end-of-day derived assumption only. ALFRED vintage logic provides real vintage dates, the best revision semantics of any dataset here, but no intraday time and a tiny sample. | **None.** Normalised `date` is not a timestamp, 528 duplicated (date, period) keys with non-identical records, 5 date decreases (audit, `papers/shiftguard_unified/elec2_candidate_audit.md`). | **None.** Batch order only; no within-batch time. | **None usable.** Start dates are source attributes; within-series positions are not wall-clock; fixed-origin protocol. |
| **(3) Untouched chronological windows** | No analytical use in the repo. Exposure is limited to validation/suitability reports, tests and a `data/reports` summary. Everything outside the two acquired months is unexposed but **not local**. Local test split is 149 bars. | Processed windows used: **2018 and 2019 only** (hourly and daily; descriptive train-only regressions, rolling loss, moving-block test-loss intervals per `phase1_completion_audit.md` G). No outcome-bearing result file for OPSD under `outputs/`. **Unprocessed and apparently unexposed: 2015-2017 (26,280 h) and 2020-01-01 to 2020-09-30 (6,576 h, 274 days).** 2020 holdout contains the spring-2020 demand disturbance; choosing it is a forking path to be frozen before opening. | Whole 2023 used in a shared three-station panel with descriptive diagnostics. Test split about 8.4k records. No other year local. **No untouched window.** | 2022-2023 only; everything used in revision-table audits. Too small anyway. | Entire stream is public and row-order replays are common. No clean split and chronology ambiguous. | Batches 7-10 (and 6) are exposed by the frozen exploratory run in `real_data_development_results.md`; batches 1-5 are train. **None untouched.** | The first 10-20 series per dataset only; official-horizon baselines exist (descriptive). No unexposed chronological window defined. |
| **(4) Application-grounded costs** | **Switching:** an exchange fee schedule is the natural source and is **not in the repo**. Needs a dated external snapshot (blocked). Slippage, fills and market impact are absent and are not modelled. **Query:** labels are free; every return arrives. Interpret c as analyst-review or recalibration-compute cost, imposed. | **Switching:** none documented. A model-redeployment or bidding cost would be imposed. Day-ahead price columns exist (DE_LU price from 2018-10, 2,209 h in 2018, 8,758 h in 2019, 6,573 h in 2020), so the value of a load-forecast error can be tied to a price, but the imbalance or penalty price is not local. Costs remain partly imposed. **Query:** as for Binance, imposed. | None; "frost/heat alert" costs would be imposed. | None. | None; classification cost imposed. | Class-cost matrices are imposed. **Query:** closest to a real cost (lab exposure for ground truth) but undocumented in the repo. | None; imposed. |
| **(5) Licence / redistribution** | Publisher repo MIT; exchange data terms and attribution retained; research only. | `datapackage.json` has **no `licenses` field**; manifest says package and source-specific terms apply, no blanket relicensing. Sources are ENTSO-E Transparency. Treat as research use, no redistribution of values, until the OPSD and ENTSO-E terms are pinned. | US government data; attribution retained. Low risk. | Series-specific terms; the API key is required for new pulls. | OpenML "Public" is metadata only; original source page unavailable. | UCI page says CC BY 4.0; original description restricts commercial use. Research only. | Zenodo CC BY 4.0 (M4 hourly: "no blanket license"). |
| **(6) Disagreement density** | Unknown from metadata. Two sign rules are expected to disagree on a large fraction of bars; no output exists to confirm. | Unknown. The disagreement indicator must be defined (for example, absolute gap between two forecasts above a frozen threshold); the rate cannot be estimated without reading values. | Unknown. | Unknown, and the sample is too small to matter. | Unknown. | Unknown from metadata; per-batch class mismatch only visible in exposed outputs. | Unknown. |
| **Verdict** | **DEVELOPMENT-ONLY locally** (743 bars). **ELIGIBLE-CANDIDATE conditional on a small acquisition** (see blockers). | **ELIGIBLE-CANDIDATE** (conditional on the timing citation and licence pin). | **DEVELOPMENT-ONLY** | **INELIGIBLE** (size). | **INELIGIBLE** for any clocked claim; at most an offline row-order development replay. | **DEVELOPMENT-ONLY** | **DEVELOPMENT-ONLY** (a simulated clock only) |

## Folktables (brief)

Raw 2017-2019 ACS 1-year PUMS for CA, FL, NJ, NY and TX plus a 2018 NJ file; 18 processed versions;
tasks are cross-sectional person records with a survey year and state as coarse domains. There is no
within-year event time and no per-row release time (annual publication is a fixed, public, yearly
delay, but it cannot define a within-stream label clock). The inventory already classifies it as
offline classification with imposed costs. **Verdict: INELIGIBLE** for a clocked stream; at most an
offline domain-block replay.

## Verdict rationale per dataset

- **Binance.** The clock, calendar integrity and publisher checksum are the best of any dataset, and
  a fee schedule is a documented-in-the-world source for k. It cannot carry R1 locally: one hourly month
  (149 test bars) gives no meaningful burst count and one daily month (30 bars) gives none. The query
  side remains imposed. Disagreement bursts between sign rules in near-martingale returns are an
  empirical unknown.
- **OPSD.** Only dataset with enough data (about 50k hourly rows across 2015-2020), a natural pair
  (published TSO forecast against a frozen model), an apparently unexposed year-long window
  (2020 Jan-Sep) and an unexposed training period. Weaknesses: clocks come from external regulation,
  not the repo; revisions possible; costs imposed; no verified onset.
- **Gas Sensor.** Has the only naturally costly label, but there is no timeline; it can only test
  budget mechanics under an imposed batch-order clock. Exposed.
- **NOAA.** Real data and real seasonal change, but free labels, unknown release latency, irregular
  horizons, whole year exposed.
- **Monash.** No wall-clock time; useful only as a development panel for the acquisition rule with a
  declared clock.
- **elec2.** Chronology is not trustworthy; already excluded by `elec2_candidate_audit.md`. Do not
  reopen.
- **FRED.** Best revision and vintage semantics, wrong size (25-37 events per series).

## Ranked recommendation for R1

1. **OPSD hourly DE load (published TSO day-ahead forecast against a frozen own forecaster).** Only
   dataset that can be specified now. R1 must:
   - freeze the training period (2015-2016), the validation year (2017) and the development block
     (2018-2019, already descriptively exposed) and treat 2020-01-01 to 2020-09-30 as a single-use
     holdout, with its choice declared as a forking path;
   - state the clock as an explicit external assumption: decision at the start of delivery hour h;
     label at h plus a documented delay of about 1 h, with a sensitivity grid {1, 2, 24} h, and pin the
     regulatory citation (not verified by this audit);
   - define loss (absolute error) and a disagreement indicator before any look at values;
   - declare c as review or compute cost and k as a redeployment cost, both imposed, and the
     DE_LU price as an optional grounded value of error.
2. **Binance (ETHUSDT 1h), conditional on an explicit user-approved small acquisition.** It has the
   best clock and a world-documented switching cost. The acquisition must be requested in a separate
   step. The monthly kline zips are tiny (about 42 kB each), and each ships a publisher CHECKSUM file.
3. **Gas Sensor** as a development-only budget-mechanics testbed (natural query cost, no clock).
4. NOAA, 5. Monash (development panels with declared clocks). elec2, FRED and Folktables are not
   recommended.

Because every dataset has free labels, the hard budget and the burst structure remain imposed whatever
the choice. R1 should therefore claim only "the allocation rule survives a real dependent stream with
verified timing and imposed budget", never application cost savings.

## Exact missing information for blocked datasets

**Binance (blocked on size and fee source).**
- A pinned span of at least about 12 months of ETHUSDT (and optionally BTCUSDT) 1h monthly klines from
  `data.binance.vision`, with each month's publisher CHECKSUM verified. At about 740 bars a month that is
  roughly 9k bars. The test span must be chosen in advance and must not overlap 2025-01 (the only
  acquired month; low prior exposure, descriptive only).
- A dated, archived snapshot of the Binance spot fee schedule (maker, taker, VIP tier assumed) to
  define k, and a decision on the tier.
- An explicit statement of what c means, since labels are free.
- A position rule pair frozen before opening any unseen month.

**OPSD (not blocked, but unpinned).**
- Citation for actual-load and day-ahead-forecast publication deadlines in the ENTSO-E Transparency
  regulation (this audit did not verify it).
- OPSD and ENTSO-E reuse terms (the datapackage has no licence field).
- Whether `DE_load_forecast_entsoe_transparency` in the 2020-10-06 snapshot equals the as-published
  vintage or a later revision (not stated in `datapackage.json`).
- Definition and rate of the disagreement indicator; the first look at values must be in R1 on the
  development block only, never on 2020.

**Gas Sensor / NOAA / Monash (development-only; cannot be unblocked by metadata).** Within-stream times
or release latencies do not exist in the local or documented data. A fresh chronological period would
need a new source.

**Lane A's open G4 dependency overall.** No local dataset supplies (a)-(e) together. The
nearest is OPSD for (c) plus a regulatory clock for (b), with (d) imposed. Say so openly in any
write-up rather than upgrading imposed clocks or costs into facts.

## Exposure notes

- This audit read only non-null counts and timestamp ranges from the OPSD raw CSV (including the
  2020 rows), and no values. It did not open any 2020 outcome values.
- Binance and OPSD have no outcome-bearing result files in `outputs/`. Their code hashes appear in
  several run manifests only because those manifests list the whole module set.
- NOAA, Gas Sensor and Monash descriptive diagnostics exist in `data/reports/` and the Phase 1 audit.

## Continue / pivot / stop assessment

**Continue to R1 on OPSD**, with the Binance acquisition as a parallel request. R0 does not exit: at
least one dataset (OPSD) passes the metadata screen with named caveats. Nothing here supports a
confirmation claim.
