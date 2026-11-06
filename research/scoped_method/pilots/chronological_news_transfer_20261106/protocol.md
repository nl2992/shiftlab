# Chronological news transfer protocol — 2026-11-06

**Status:** frozen pre-outcome protocol for an application-transfer study of the already-published PFA-SR detector. This is not a new-method claim. The datasets supply chronological model-pair examples; queried-label release is simulated because source release logs are not available.

## Research question and claim boundary

Does the canonical PFA-SR detector, attached to the same `gated_adaptive_range` deployment host, improve net cost over corrected RMM and other applicable ShiftLab baselines when a fixed challenger model has a strong, sustained validation-period advantage on chronological news classification?

The target regime is identified only on the pre-confirmation validation window by the rule below. The test window is opened only by the frozen evaluator after model training and eligibility are recorded. A successful result supports a published-method transfer benchmark on the registered news sources with a simulated feedback contract; it does not establish a new detector, a causal deployment effect, or PFA's conditional-null guarantee under real serial dependence.

## Frozen sources and windows

| Registry | Source, version / location | Train incumbent | Train challenger | Validation (target selection only) | Untouched test window |
|---|---|---|---|---|---|
| `uci_news_aggregator_359` | UCI dataset 359, News Aggregator, 422,937 rows, timestamp/category/publisher/title; source period 2014-03-10 through 2014-08-10. UCI states timestamps are approximate publication times. | 2014-03-10 through 2014-04-20 | 2014-04-21 through 2014-06-01 | 2014-06-02 through 2014-06-30 | 2014-07-01 through 2014-08-10 |
| `wildtime_huffpost` | Wild-Time HuffPost source; News Category Dataset v2, headline/category/date; retain dates 2012-2018 and the official 11-category Wild-Time mapping. CC0 per Wild-Time source README. | 2012-01-01 through 2013-12-31 | 2014-01-01 through 2016-12-31 | 2017-01-01 through 2017-12-31 | 2018-01-01 through 2018-05-25 (available archive range only) |
| `mnds_zenodo_7394851` | MN-DS version 1, 10,917 labelled articles from 2019, first-level NewsCodes categories; CC BY 4.0. | 2019-01-01 through 2019-03-31 | 2019-04-01 through 2019-06-30 | 2019-07-01 through 2019-09-30 | 2019-10-01 through 2019-12-31 |

For every source, split boundaries are based on the recorded publication timestamp, converted to UTC where timezone is supplied. Data rows are sorted by timestamp and stable source row ID. Rows with invalid/missing timestamp, text, or target are excluded by the same rule in every window and the counts are reported before model fitting. A dataset with fewer than 2,000 usable test rows, fewer than 1,000 rows in either model-training window, or fewer than 500 validation rows is ineligible; no alternative window will be selected after looking at results.

Raw dataset artifact URLs are pinned in the acquisition manifest after download, along with byte size, SHA-256, license/terms, retrieval time and upstream repository/version. Raw/licensed values remain outside Git.

## Frozen model pair and chronology

Within each source, fit two independent `HashingVectorizer` + `SGDClassifier(loss="log_loss")` models with identical architecture and fixed seed. The vectorizer is stateless: word unigrams/bigrams, lowercase, English stop words, 2^18 features, alternate signs disabled, L2 normalization. Use headline/title text when available; otherwise use the dataset's supplied article text truncated to its first 2,000 characters. No publisher, URL, date, target, or future-derived statistic is a model feature. Fit each classifier only on its named train window, using single-label source targets (HuffPost's frozen 11 categories; UCI's four categories; MN-DS's first-level NewsCodes category). No model or tokenizer is pretrained on the confirmation records. Training code, model parameters and fitted model hashes are written before test labels are evaluated.

The incumbent and challenger are both trained at the start of validation/test using disjoint earlier windows. The incumbent represents the older model; the challenger represents a later retrain. Validation is used only for the eligibility gate, not model or hyperparameter tuning. Predictions are generated once, chronologically, for both models on every test row. Both losses are identifiable from the single observed target label.

## Target-regime classification and stop rule

On validation, compute disagreement fraction and signed paired advantage `mean(1[incumbent wrong] - 1[challenger wrong])` overall and in three chronological equal-count blocks. A source is eligible for test evaluation only if:

1. there are at least 100 validation disagreements;
2. the candidate's overall error advantage is at least 0.03 (three percentage points);
3. mean signed advantage conditional on model disagreement is at least 0.20; and
4. the challenger has lower error in at least two of the three chronological blocks.

This labels a strong persistent model-pair advantage using validation only. Eligibility is set in `source_eligibility.json` before any test-period outcome metrics are computed. If no source qualifies, stop this registry; do not retune or move boundaries. If one or two qualify, report the eligible-source result and state the limited transfer scope; do not expand this registry after viewing their test outcomes.

## Feedback, policy and cost contract

For test rows, event time and prediction time are the recorded article publication timestamp. The label-release time is `publication_time + 24 hours`, an explicitly simulated feedback delay for every registry source. Requests are issued before any labels with release time equal to the current event time are delivered. Only queried labels are visible through policy feedback; no labels are used for test-period retraining. The model predictions are frozen before the test window.

Replay each eligible source as one chronological stream with a timestamp-aware release queue. Compare `PFA-SR:gated_adaptive_range`, `rmm:gated_adaptive_range+RMM`, `xu_acquisition_only`, `E_rb:gated_adaptive_range`, `E_swcert`, and `CONTROL_never_switch`. Keep all predictions, label budgets, delay contract, alpha, label price, switch price and information channels identical within source. Use horizon = all eligible test rows, hard label budget `B=min(200, floor(0.10*T))`, label cost 0.05, switch cost 5, and alpha 0.05. Report both absolute net cost and per-1,000-event cost, predictive error, labels, label expenditure, switches, switching expenditure, promotion/rollback counts, and time to promotion.

Since the test streams are serially dependent and labels are not independently released by the source, do not use PFA's iid conditional-null guarantee as a real-data guarantee. Report calibration claims only for the synthetic null experiments. The test is a retrospective chronological replay with imposed feedback, not prospective deployment evidence.

## Primary analysis and source-level uncertainty

The primary contrasts are paired net-cost differences PFA-SR minus same-host RMM and PFA-SR minus Xu adapter, computed on the identical ordered event stream. Require at least 5 units saved per 1,000 events with a two-sided 95% source/time-block interval below zero on each eligible registry to call the transfer successful. Otherwise report the estimate and interval as inconclusive or unfavorable. There is no pooled superiority claim if fewer than three independent dataset/source clusters qualify.

For UCI News Aggregator, use publisher as the source cluster; include all publishers with at least 100 validation examples, with the list frozen before test outcome analysis. For HuffPost, the publisher is one cluster; for MN-DS use the outlet/domain field if present, otherwise the dataset is one source cluster. Within each cluster, preserve chronological blocks and use a paired moving-block bootstrap with 7-day blocks (or, for MN-DS if dates have only daily resolution, 7-day calendar blocks), 2,000 resamples, and seed `2026110641`. Report each dataset and source cluster separately; do not treat rows or articles as independent replicates. If source metadata do not support the registered clusters, report the dataset as one cluster and do not claim generalization from it.

## Test opening and artifacts

The evaluator must not compute or print test labels, test performance, or policy outcomes before model/eligibility freezes are written. The opening step records an exclusive marker, source/code/model hashes, exact test time range, exact included row IDs, and the run command before producing outcomes. No policy or model change is allowed after opening. Raw values and model weights remain local; Git receives the protocol, source checksums/provenance, code, prediction-stream hashes, aggregate reports and reproducibility manifest.

## Reproducibility / prior-art boundary

- PFA-SR is the published weighted e-SR baseline in `scripts/sota_sprint/pfa_srr_baseline.py`, not a new detector.
- Wild-Time official repository commit is `23b0696dc82479a0689d678f44328153a19527e1` (MIT-licensed code; data license statements in upstream README).
- MN-DS DOI: `10.5281/zenodo.7394851`, version v1.
- UCI News Aggregator DOI: `10.24432/C5F61C`, dataset ID 359.
- Label delays and label/switch prices are study assumptions. Do not call them observed field costs or label clocks.
