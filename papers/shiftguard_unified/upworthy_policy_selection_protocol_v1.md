# Upworthy fixed-horizon headline policy selection protocol v1

**Status:** frozen before opening the official holdout partition.  
**Study role:** one real-data Q2 candidate-selection evaluation; not a full ShiftGuard evaluation.  
**Source partition plan:** exploratory split for model development; official holdout split for one locked evaluation. The larger confirmatory split will not be accessed in this protocol.  
**Primary source audit:** [`upworthy_real_data_eligibility_audit.md`](upworthy_real_data_eligibility_audit.md).

## Question and estimand

Does a text-only, training-selected headline-package policy achieve a higher held-out click-through rate than uniformly choosing among the packages in each randomized experiment?

For experiment `i` with eligible package set `A_i`, let `r_ia = clicks_ia / impressions_ia` be the observed arm click rate and let `a_i` be the package selected by the frozen policy using only package text. The primary descriptive estimand is the equal-experiment average

`Delta = mean_i [ r_i,a_i - mean_{a in A_i}(r_ia) ]`.

The second term is the expected value of a policy that chooses uniformly over the offered packages. The causal interpretation requires the archive's within-experiment random-assignment account and the exclusion of the suspected cache-problem period. Report the impression-weighted contrast separately. Click is the only supported outcome utility; it is not revenue, welfare, or net business value.

Primary null: `H0: Delta <= 0`. Report the paired point estimate, two-sided 95% uncertainty interval, and one-sided 95% lower bound. A positive interval is evidence only for average CTR gain under this archive and task contract. No minimum business-significant CTR threshold is asserted because no application cost or value conversion is supplied.

## Information and action contract

- Decision unit: one article-level headline experiment; action: choose one offered headline/image package for future display.
- Training partition: the official exploratory CSV, 4,873 tests / 22,666 arms. It is the only source used to fit the policy.
- Evaluation partition: the official holdout CSV, documented as 4,871 tests / 22,600 arms, stratified by test week and exclusive from the other archive partitions. It will be downloaded and read only after this protocol and runner are frozen.
- The holdout has been public since 2021. “Held out” means unused by this ShiftLab analysis, not globally secret or untouched by other researchers.
- Exclude any test with an arm whose `created_at` falls within the inclusive buffered dates 2013-06-24 through 2014-01-11. This conservatively covers the maintainer-reported 2013-06-25 through 2014-01-10 concern period while accounting for the timezone-naive field. If an official corrected `Problem` flag is present, exclude flagged tests as well and report the overlap; never re-include tests based on results.
- Require at least two arms, positive impressions, and `0 <= clicks <= impressions`. Report all exclusions by reason.
- The learner may use only `headline` and `excerpt`, both shown before a click. Missing text becomes an empty string. Do not use `lede` (shown after selecting the package), `share_text` or `square` (not shown in the test), `winner`, `first_place`, `significance`, clicks, impressions, timestamps, week, IDs, or image IDs as predictive features. Training counts are used only as binomial outcomes and observation weights.
- `winner`, if present, is an evaluator-only descriptive summary of the editor's post-test choice. It is not the target label for the learner and is not a fair independent policy comparator.
- The release contains aggregate arm counts, not impression-level histories. No event-by-event feedback, query schedule, delay, or online information filtration is reconstructed.

## Frozen policies

**Candidate policy:** bag-of-words regularized binomial logistic CTR predictor. Fit on exploratory arms after the assignment-risk exclusion. Use a word TF-IDF vectorizer with `(1, 2)` n-grams, `min_df=3`, `max_features=50,000`, and `sublinear_tf=True`. Fit the binomial likelihood without expanding to impression rows by representing each package twice (click and non-click response) with sample weights equal to `clicks` and `impressions - clicks`; this is algebraically the grouped-binomial likelihood. Select inverse regularization `C` from `{0.01, 0.1, 1, 10}` using 5-fold `GroupKFold` on `clickability_test_id`, maximizing the equal-experiment policy-value contrast versus uniform choice. Resolve exact ties toward the smaller `C`. Refit the selected pipeline on all eligible exploratory tests. Use `LogisticRegression(solver='liblinear', max_iter=1000, random_state=20261026)`. Select the package with the largest predicted CTR; break ties lexicographically by package text, then source row order.

**Reference policy:** uniform random choice among each experiment's eligible packages. Its expected CTR is the unweighted mean of package-arm CTRs for that experiment. The model policy and reference use the same eligible arms.

**Descriptive evaluator-only bound:** the best observed arm CTR within each holdout experiment. This uses evaluation outcomes and is an oracle upper bound only; it is never treated as a deployable policy or as a candidate policy result.

No monitor, statistical promotion gate, label-acquisition policy, retraining rule, or intervention-cost controller is evaluated in this protocol.

## Metrics and uncertainty

Primary endpoint: equal-experiment mean paired CTR difference `Delta` on eligible holdout tests. Secondary endpoints: the same difference weighted by total experiment impressions; candidate and uniform-reference CTR separately; evaluator-only best-arm CTR; number of eligible tests/arms; impression totals; distribution of `Delta_i`; and results by `test_week` as descriptive temporal sensitivity.

Primary uncertainty: 10,000 paired bootstrap replicates resampling `test_week` clusters with replacement and retaining all experiments in each selected week; use the registered percentile interval. Sensitivity: experiment-level paired bootstrap and a block jackknife over `test_week`. Do not treat package arms as independent replications. If too few nonempty week clusters remain after filtering, report inference as underpowered and do not replace the primary method after seeing the holdout.

## Provenance, resource budget, and stopping rule

Verify source file sizes and SHA-256 against OSF metadata before processing; verify exclusive test IDs and expected row/test counts. Save the trained model configuration and source hashes, an aggregate-only per-test metrics file, bootstrap summary, exclusions, and a manifest. Do not export package text or row-level outcomes into summary artifacts. Use CPU sparse linear algebra; this small sparse-text task does not warrant dense GPU conversion. Stop after one complete run and independent artifact verification. No holdout tuning or rerun is permitted. If validation fails, stop and report the failure without changing the split, exclusion window, policy, or endpoint.

## Interpretation boundary

This is a nonsequential, fixed-horizon, experiment-level policy-selection evaluation. It may provide external evidence for selecting among randomized headline packages using CTR. It cannot validate anytime-valid monitoring, delayed feedback, active querying, deployment costs, market-wide time drift, or the integrated three-track ShiftGuard system. A favorable result would be one real-data task family only; the overall programme still requires another qualifying family and strong compatible published baselines.
