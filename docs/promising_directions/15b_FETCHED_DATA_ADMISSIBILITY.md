# 15b. Fetched public drift streams: admissibility audit (dev-only)

Date: 2026-11-01. Status: descriptive admissibility audit, not confirmatory evidence.

## LOCKED EVALUATION WINDOW (hard rule)
For every stream, after chronological ordering, rows `[int(0.6 n), n)` (final 40%) are locked. No label, loss, plot or statistic from that window was read or computed. The code (`scripts/promising_directions/realdata_audit/fetch_audit.py`) truncates labels to `[:n60]` at load time; for spam, the locked feature rows are never parsed. Only row counts are reported. Train = `[0, int(.3n))`, dev = `[int(.3n), int(.6n))`. All preprocessing (scaler, one-hot, majority-class rule) is fit on train rows only.

## Acquired (raw data in `shift-research-starter/data/raw/<name>/`, gitignored; receipts `*.receipt.json` beside each file; fetch script `fetch_streams.py`; JSON outputs in `results/realdata_audit/fetched/*_dev_audit.json`)

| name | source | sha256 (prefix) | n x d |
|---|---|---|---|
| uci_bank_marketing | UCI id 222 `archive.ics.uci.edu/static/public/222/bank+marketing.zip` (Moro, Cortez, Rita 2014); CC BY 4.0 | e0bf5f5de5b8 | 41188 x 19 (bank-additional-full, `duration` dropped as non-prospective leakage) |
| openml_airlines_1169 | OpenML 1169 parquet `data.openml.org/datasets/0000/1169/dataset_1169.pq` (Bifet/Ikonomovska; licence "Public") | 9969df72e438 | 539383 x 7 |
| weather_elwell_polikar | `vlosing/driftDatasets@01d08de` realWorld/weather (original: Elwell & Polikar 2011, Offutt AFB Bellevue NE, 1949-1999) | e38ef95890ec (data), 90f39b754a9c (class) | 18159 x 8 |
| spam_katakis | same repo, realWorld/spam.zip (Katakis et al. spam-filtering stream; 744 MB uncompressed dense, streamed not extracted) | 0c3eb317fcca | 9324 x 39916 (sparse) |
| rialto | same repo (Losing et al. 2016 own dataset, Rialto bridge images) | 1ff9e55a52e9 / 42c7fc42363c | 82250 x 27, 10 classes |
| outdoor_objects | same repo (Losing et al. 2015) | 53f9d793056b / e2dceebd3ab8 | 4000 x 21, 40 classes |

Caveats: the GitHub repo (Viktor Losing) is a mirror/author repo with no declared licence (API reports none); original author pages for weather/spam give no explicit licence. Research use only; do not redistribute. OpenML parquet used instead of ARFF (the ARFF endpoint was ~10x slower); same dataset id and content.

**Failed / skipped:** INSECTS (Souza et al. 2020): not on OpenML (name search returns nothing), the authors' Google Sites page links via JS/Drive with no direct URL retrievable; skipped, no URL invented. Official NOAA/Elwell page (Rowan) not fetched; weather taken from the Losing mirror (same 18159-row file). Other mirror candidates (airlines2, phishing, chess, covtype, poker, elec) are either already covered locally, non-chronological, or synthetic-virtual drift; not used.

## Provenance, order, labels, delay, leakage
- **bank**: file order is chronological (May 2008 - Nov 2010, UCI doc) but there is no date column; order cannot be verified from data. Label y=yes (term deposit); real delay is days-weeks (campaign outcome) but unknown per-row; impose. Leakage: `duration` dropped; macro features (euribor3m, nr.employed) are time-varying and legitimately drift. Positive rate shifts strongly with time (early window very different), so train-only scaling matters.
- **airlines**: no date; rows are sorted by departure time within day with ~66 midnight wraps and ~30 day-of-week changes, i.e. a ~2-month day-level chronology with minute-of-day (verified from features only). Label Delay (binary, native). True delay = arrival time (hours); impose. Airport/airline are high-cardinality categoricals (train-only one-hot, min_frequency 20, unseen -> zeros).
- **weather**: daily 1949-1999, label = rain that day (native binary, 30% pos in dev). Label known at end of day (real delay ~1 event); fully chronological.
- **spam**: arrival order, binary, native. Real delay unknown; impose. Text bag-of-words with a single dominant concept change.
- **rialto / outdoor**: 10 / 40 classes, reduced by a pre-registered rule: majority class of the train block (rows < 30%) vs rest (rialto -> class 0, ~10% positive; outdoor -> class 23, 1.7% dev positive). Images in capture order; no timestamp; drift is lighting/time-of-day.

## Exposure
`git grep -il` over all 39 local/remote branch tips (docs, src, scripts, configs, papers, experiments) for insects|airlines|bank marketing|NEweather|elwell|spam_data|katakis|rialto|outdoorStream: only hit is one line of prior-art text in `docs/decision_value/02_PRIOR_ART_AND_NOVELTY.md` listing "Airlines" among a cited paper's benchmarks. No code, results or data use of any of these streams. (An unrestricted whole-tree grep exceeded the time limit and was not completed; `data/` and `results/` not searched.) Exposure = none for all six.

## Dev audit (train = first 30%, dev = next 30%, 0/1 loss, q = 0.05)
Pair rule (pre-stated): among 5 candidate pairs {LR15|LR15-30, LR15|HGB15-30, LR0-30|HGB0-30, LR15|HGB0-30, HGB15|HGB15-30} (LR = logistic regression, HGB = sklearn HistGradientBoosting depth 4, windows as % of n) pick max dev clairvoyant headroom at switch cost 5 subject to dev disagreement >= 5%. Headroom = (always-incumbent cost - hindsight-optimal cost incl. switches)/dev rows, per event. Break-even label fraction = headroom/q (fraction of events one could label at q=0.05 before headroom is consumed). Sklearn 1.6.1 was available.

| stream | selected pair | inc err | chal err | disagree | mean adv | headroom cs5 (switches) | headroom cs20 (sw) | break-even label frac cs5/cs20 |
|---|---|---|---|---|---|---|---|---|
| airlines | LR15\|HGB15-30 | .387 | .382 | .145 | +.0051 | .0171 (107) | .0141 (15) | .34 / .28 |
| weather | LR15\|HGB0-30 | .231 | .208 | .098 | +.0224 | .0231 (1) | .0204 (1) | .46 / .41 |
| spam | LR15\|LR15-30 | .267 | .047 | .242 | +.220 | .218 (1) | .213 (1) | 1.0 / 1.0 |
| rialto | LR15\|HGB0-30 | .100 | .022 | .085 | +.078 | .078 (1) | .077 (1) | 1.0 / 1.0 |
| bank | LR15\|LR15-30 | .453 | .061 | .449 | +.392 | .391 (1) | .390 (1) | 1.0 / 1.0 |
| outdoor | none eligible (max disagree 4.8%) | | | | | (best .021) | | |

Advantage profile over 10 dev chunks (selected pair):
- airlines: .026 .008 .011 -.013 -.045 -.017 .018 .036 .020 .006 (sign flips; genuine switching structure)
- weather: -.006 .017 .029 .018 .024 .028 .029 .029 .018 .037 (mostly positive, one switch)
- spam: .082 .186 .046 .146 .296 .143 .196 .294 .502 .312 (monotone-ish growth)
- rialto: .058 .067 .083 .097 .068 .071 .058 .086 .092 .099 (constant gap)
- bank: .740 .732 .731 .791 .711 .182 .012 .006 .008 .002 (advantage vanishes after chunk 5)

Interpretation:
- **bank**: degenerate. LR trained on the first 15% (May-mid 2008 era, unusual base rate) is miscalibrated by prior shift; the challenger is effectively "predict no". Headroom is one switch at t=0 and then the advantage disappears; no sustained switching problem. HGB0-30 vs LR0-30 are identical (disagree 0).
- **rialto**: LR is basically a constant predictor for the 1-vs-9 target; headroom is model-class gap, one switch.
- **spam**, **weather**: one persistent switch (a stale incumbent; useful as "stale incumbent / easy switch" controls but not switching-policy stress tests).
- **airlines**: only stream with a nontrivial profile (many sign changes, headroom 1.4-1.7 pts, 15 switches even at cost 20), consistent with day-of-week/time-of-day cycling. Caveat: it is a ~2-month sample, so "drift" is largely periodic and the chronological index is inferred, not timestamped.
- **outdoor**: 4000 events, 1.7% positives under the rule, disagreement < 5%; inadmissible.

## Recommendations for a locked evaluation
Primary: **airlines** (best switching structure). Secondary: **weather** (genuine multi-decade chronology; small n, headroom ~2 pts, only ~1 switch, so low power). Controls (one-switch regimes; report but do not use as evidence of a switching policy beating calendar baselines): **spam**, **bank**, **rialto**. Exclude: **outdoor**. Note headroom on dev is a ceiling under hindsight on 30% of data, not a measure of attainable gain; the final 40% is still untouched, so none of these results gate anything yet.

Split boundaries (row indices, 0-based, half-open): 
- airlines n=539383: train [0,161814), dev [161814,323629), locked [323629,539383)
- weather n=18159: [0,5447), [5447,10895), locked [10895,18159)
- spam n=9324: [0,2797), [2797,5594), locked [5594,9324)
- bank n=41188: [0,12356), [12356,24712), locked [24712,41188)
- rialto n=82250: [0,24675), [24675,49350), locked [49350,82250)
- outdoor n=4000 (excluded): [0,1200), [1200,2400), locked [2400,4000)

Imposed label delay (events; none of these has a recorded label timestamp): airlines 500 (about 1 hour of flights at ~8k flights/day), weather 1 (next-day), bank 200, spam 50, rialto 500. Label budget fraction: 10% of events at q=0.05 (below the airlines break-even of 28-34% and weather 41-46%); a second budget of 25% is a reasonable sensitivity check. Fix pair, delay, budget, thresholds before any locked-window access. Pair selection here used dev only; re-selecting on a different dev would be tuning and must stay out of the locked run.

Limitations: single seeds, default model hyperparameters, 0/1 loss with cost units where one error = 1; only 5 candidate pairs; headroom is hindsight-optimal and ignores label delay and the cost of acquiring the labels used to detect when to switch.
