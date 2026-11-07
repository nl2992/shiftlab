# W5 scope: untouched real sources for P2 (2026-11-07)

**Purpose.** Every P2 confirmatory result so far (W4, H8) rests on five UCI-derived sources the
programme had already used. W5 adds independent chronological sources that no ShiftLab code has
read. They will test whether the findings generalise. This file is a scope: nothing has been
downloaded, and no source below has been opened.

## Constraints carried over

- **No authentic label clocks.** The Wild-Time audit
  (`docs/scoped_method_research_2026-11-06/WILDTIME_FEASIBILITY.md`) and the criteria review (C6) found
  that public chronological datasets give event times, not label-release times. W5 therefore uses
  **imposed delays swept over a grid**, labelled as imposed everywhere (scope decision 2).
- **Locked holdouts stay locked.** The OPSD 2020 and Binance 2026 holdouts are reserved for a
  Lane B method freeze (`docs/scoped_method_research_2026-11-06/REAL_DATA_AUDIT.md`). P2 must not
  consume them. OPSD's exposed development years could serve as a descriptive external-clock case
  study, but they are not untouched.
- **One opening.** Each source is fitted and run once, by one committed command, after its
  hypotheses and analysis are registered (W6). Crash recovery may re-run with identical seeds; no
  other re-run is allowed.

## Exposure check (2026-11-07)

A repository search (excluding `.venv`, `outputs`, `vendor_sota`, `graphify-out`) found no code that
reads any of the candidates below. They appear only in planning documents. Sources already
exposed, which are therefore ineligible: the five UCI fresh sources, elec2, airlines, bank
marketing, criteo, insects, occupancy, LDPA, EEG, NOAA/weather, folktables/ACS, CRSP, OPSD,
Binance and the WILDS sets.

## Candidates

| Source | Licence / access (verified) | Size | Event clock | Proposed target | Verdict |
|---|---|---|---|---|---|
| **UCI Online Retail II** ([UCI 502](https://archive.ics.uci.edu/dataset/502/online+retail+ii)) | CC BY 4.0; direct download, no login | 1,067,371 invoice lines, 2009-12-01 to 2011-12-09 | Invoice timestamp (minute) | Line quantity ≥ training-period median, from stock code, unit price, country, hour/weekday and known-customer flag. Cancellation lines (C-prefixed invoices, negative quantity) are excluded **before** fitting, because they leak the target | **Primary** |
| **arXiv metadata** ([HF mirror of Kaggle Cornell arXiv](https://huggingface.co/datasets/librarian-bots/arxiv-metadata-snapshot)) | CC0 (mirror card; Wild-Time also lists CC0); HF mirror needs no login; pin the mirror commit | About 2.5M records, about 2.1 GB download | v1 date in the version history | Primary category (multi-class) from title, restricted to `cs.*` first versions in a fixed date range; 0/1 loss | **Primary, with caveat:** the `categories` field is the *current* value, not the value at v1. Label it a retrospective loss replay |
| **NYC TLC yellow taxi** ([TLC trip records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)) | NYC website terms (AWS Open Data registry); anonymous monthly Parquet downloads | About 3M trips per month; about 50 MB per month | Pickup timestamp | Tip ≥ 20% of fare on credit-card trips (payment type 1), the only trips with recorded tips; features are pickup zone, hour/weekday, distance, passenger count and fare. **Exclude the tip and total columns** | **Primary;** confirm the parquet schema (snake_case names) at schema-check time |
| **HuffPost News Category** ([author page](https://rishabhmisra.github.io/publications/), [arXiv 2209.11429](https://arxiv.org/abs/2209.11429)) | Licence **not stated** on the author page; mirrors say CC0. Kaggle login needed | About 210k headlines, 2012–2022 | Publication date (day) | Category from headline | **Reserve:** needs you to download from Kaggle and confirm the licence |
| UCI Steel Industry Energy ([UCI 851](https://archive.ics.uci.edu/dataset/851)) | CC BY 4.0 | 35,040 rows (2018, 15 min) | Timestamp | Load type | **Reject:** too small for 20 episodes after training, and the label may follow the plant's time-of-day schedule |
| Chicago Crimes 2001–present | Terms page unreadable (403/404); metadata says "see terms of use" | About 8.6M rows | Incident date (sometimes estimated) | Arrest | **Reject:** unverified terms; preliminary classifications are revised later; an arrest-prediction target is ethically unsuitable for a benchmark |

With three primary sources, P2 gains three independent domains (retail, scholarly text, urban
transport). The fourth, HuffPost, depends on you. Three or four source clusters are still too few
for a well-calibrated source-level interval. W6 must report per-source results and treat any
pooled source-level interval as low-powered.

## Construction (to be frozen in the W6 registration)

Shared with `fresh_real.py` / `wp2_twins.py`, so that the benchmark has one construction:

1. **Window.** A fixed calendar range per source, chosen from documentation only. Proposed:
   - Online Retail II: all of it.
   - arXiv: `cs.*` first versions 2015–2019.
   - Taxi: January–March 2023.
   Rows are sorted by event time, with ties broken by the source's own record ID.
2. **Frozen pair.** The incumbent is fit on [0, 0.15n), the challenger on [0, 0.30n), and
   preprocessing is fit on training rows only. Tabular sources use the `fresh_real.py` pair
   (logistic regression vs gradient-boosted trees). Text sources use TF-IDF word unigrams plus
   logistic regression (incumbent) vs unigram+bigram TF-IDF plus logistic regression (challenger),
   all trained from scratch. No pretrained encoders are used, to avoid pretraining contamination.
3. **Episodes.** 20 non-overlapping 2000-event windows **evenly spaced** over the evaluation span
   [0.30n, n), not consecutive from 0.30n, so that each source's whole span is covered.
4. **Known nulls.** Exchangeable twins from the `twin_null` construction, with 60 splits per
   source. Power: twin v3 needed 60–100 splits for the hardest datasets, and the number will be
   re-checked against observed SDs at W6 using exposed data only.
5. **Imposed delays (swept).** d ∈ {25, 100, 400} events for every source, i.e. 1.25%, 5% and 20%
   of an episode. Primary analyses use d = 100. The others are sensitivity checks.
6. **Eligibility check (development window only).** A source is used only if incumbent–challenger
   disagreement on [0.15n, 0.30n) is ≥ .005. Otherwise twins carry almost no information. The check
   reads training-period labels only, never the evaluation span. A failing source is dropped by rule
   and recorded.

## What W6 will test on these sources

These are proposals for the W6 registration; nothing is registered yet:
- **Generality of F1/F2/F4/F7:** strict-pool promotion on twin nulls, informed promotions, failure
  of the uncertified selectors, and A5b's per-source bound. The same rules as W4, applied per source.
- **F8 / H8 gate on real nulls:** H8 found that real twins never bind Tier B. The registered
  prediction is that this holds on the new sources.
- **F6 pacing confound:** front-loaded vs unmodified gated deployment on real alternatives, J
  difference per source. This finding was deferred to untouched data.
- **Real-alternative leaderboard:** all-in J for the panel, ranked under the single and two-tier
  gates (descriptive).

## Stages and approvals

| Stage | What happens | Reads target labels? | Needs |
|---|---|---|---|
| S0 | Freeze windows, targets, features, models, delays, twin splits, hypotheses and analysis (W6 registration); commit | No | — |
| S1 | Download raw archives into `data/raw/w5/<source>/` (gitignored); record SHA-256, size, retrieval time, source version (HF commit, TLC month URLs) | No | **Your approval** (about 2.3 GB total, mostly arXiv) |
| S2 | Schema check: print column names, dtypes, row counts, date ranges and feature missingness only. A missing column triggers a registered amendment before S3 | No | — |
| S3 | Builder unit tests on synthetic frames with the same schema; eligibility check on development windows | Training period only | — |
| S4 | One-shot command: build streams and twins, run panel P and the H8 gates, run the analysis, record results with hashes | Yes, once | A few hours of CPU |

## Decisions needed

1. **Sources:** Online Retail II, arXiv `cs.*` 2015–2019 and NYC taxi Q1 2023 as the primary set?
   Add HuffPost only if you can download it from Kaggle and the licence checks out.
2. **Downloads:** approve S1 (about 45 MB, 2.1 GB and 150 MB).
3. **OPSD:** leave it out of P2, or include the exposed development years as a *descriptive*
   external-clock case study (no confirmatory weight)? Recommendation: leave it out, since the
   holdout belongs to Lane B.

## Risks

- **arXiv labels are current, not as-of-v1.** Reclassification after v1 adds label noise that
  correlates with time. This is acceptable for a loss replay, but must be stated.
- **Taxi tips** exist only for card trips, and conditioning on card payment is a selection step.
  It is stated as part of the task definition.
- **Event density:** a 2000-event taxi episode spans about 30 minutes, while an arXiv episode spans
  days. Episodes therefore differ in calendar time. Report events per day per source.
- **Pooling:** three or four sources give weak source-level inference. Per-source results are primary.
- **Nothing here is fabricated, but nothing is verified against the raw files yet.** Schema and
  size claims come from documentation and mirrors and are re-checked at S2.
