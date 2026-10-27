# Upworthy real-data eligibility audit

**Date:** 2026-10-26; holdout evaluation completed 2026-10-27 UTC  
**Status:** source qualified and one frozen fixed-horizon headline-selection evaluation independently reconstructed.  
**Data accessed:** official exploratory and holdout partitions. The confirmatory partition remains unopened.

## Source and local verification

The [Upworthy Research Archive](https://upworthy.natematias.com/) contains aggregate A/B test results for headline/image packages. The [data descriptor](https://www.nature.com/articles/s41597-021-00934-7) reports 32,487 tests and 150,817 arms; assignments were randomized at browser-session level. Each package record carries impressions and clicks, and packages in the same test share an experiment ID. The official archive describes exclusive exploratory (4,873 tests), confirmatory (22,743 tests), and holdout (4,871 tests) partitions, stratified by test week. The archive is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The exploratory file was downloaded from OSF node `jd64p`, file ID `608ff67f5533b40296e21e5a`. Its size is 14,260,949 bytes and SHA-256 is `8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce`. The independent aggregate audit verifies 22,666 package records across 4,873 tests, 2–14 arms per test, no missing test IDs, positive impressions, and `0 <= clicks <= impressions`. Totals are 81,024,151 impressions and 1,231,208 clicks. No text rows are copied into the audit output. The reproducible audit is `scripts/audit_upworthy_exploratory.py`; its aggregate result is `data/reports/upworthy_exploratory_audit.json`. The raw CSV is under `data/raw/` and ignored by Git.

## Assignment-integrity restriction

The archive maintainers' [June 2024 update](https://upworthy.natematias.com/2024-06-upworthy-archive-update.html) reports a suspected caching-related assignment problem from June 25, 2013 through January 10, 2014. They recommend against causal analysis of that period; the mechanism is suspected rather than proven. The 2020 OSF exploratory CSV predates this correction and has no `Problem` flag. Its `created_at` values are timezone-naive. Therefore, the source audit identifies tests with any package created from June 24, 2013 through January 11, 2014 inclusive as a conservative exclusion set. This flags 1,057 of 4,873 exploratory tests. It is a date-based sensitivity rule, not a verified package-level randomization indicator. A future evaluation must report results with this exclusion and, if data permit, a separate sensitivity analysis using the publisher's corrected flag or supplementary materials.

## Scientific fit and limits

The source can support a **fixed-horizon Q2 decision study**: choose one package from each new headline experiment using a frozen rule learned only on prior experiments, then estimate the selected package's click-through value from the independent randomized arm outcomes. A simple candidate is a regularized text-based CTR predictor. A uniform-over-arms choice is a deployable reference. The `winner`, `first_place`, `significance`, `clicks`, and `impressions` fields are post-assignment or outcome-derived and must not be learner inputs. `lede` is shown after a click, and `share_text`/`square` were not shown in the test; they are also ineligible inputs. Treat the publisher's selected `winner` as an evaluator-only descriptive comparator, not a feature or ground-truth oracle.

This is a real downstream action (choosing which headline package to show) with a randomized click outcome, but **click-through rate is the only supported utility**. The archive provides neither revenue nor deployment cost. Keep CTR and impression counts separate; do not translate clicks to money or claim net economic benefit. Since the observations are package-level aggregates, the archive cannot reconstruct label arrival order, individual feedback delays, adaptive querying, or an anytime-valid online monitor. It therefore cannot close Paper 1's live sequential claim or Paper 3's feedback-budget allocation claim. The time-stratified randomized partitions are not future-time holdouts; results would test transfer across held-out experiments, not future platform drift.

One experiment has multiple randomized arms, but the release does not include impression-level outcomes or individual context. The estimand must be the equal-test average value of the selected package, with an impression-weighted aggregate reported separately. Uncertainty should be computed across independent tests with week-aware clustering/sensitivity, not by treating package rows as independent people. Selection from text across experiments also assumes that future experiment packages and their click outcomes are exchangeable enough for the declared target population; that is a development assumption to test, not a property guaranteed by the archive.

## Eligibility decision and next controlled step

**GO for the registered fixed-horizon Q2 evaluation; NO-GO for sequential monitoring or cost-aware online adaptation.** Protocol v1 was frozen before opening the official holdout. Its single evaluation used only headline/excerpt text, selected the regularization parameter on the exploratory partition, excluded 1,063 holdout tests in the predeclared assignment-risk window, and compared selected-package CTR with uniform-over-packages CTR. Across 3,808 eligible holdout tests (18,278 arms), the equal-test selected-minus-uniform CTR difference was **0.001002** (0.1002 percentage points); the 95% week-cluster bootstrap interval was **[0.000850, 0.001170]**, with one-sided 95% lower bound **0.000872**. The impression-weighted difference was 0.000981. A separate verifier reconstructed training, selection, all per-test contrasts, and the bootstrap from the hash-pinned source and code. The holdout is public and project-relative, not globally secret. This result supports only historical fixed-horizon package selection under the registered exclusion and task assumptions; it does not establish future platform performance, sequential validity, or economic utility.

This is one real-data task family, not the two-family final evaluation required for the overall programme. It does not establish a complete decision-aware monitor-certify-intervene system or a novel contribution. The result is positive for the registered CTR estimand, but the broader real-data gate remains open.

## Primary sources

- [Upworthy Research Archive](https://upworthy.natematias.com/)
- [Matias et al. (2021), data descriptor](https://www.nature.com/articles/s41597-021-00934-7)
- [Author update on assignment reliability (2024)](https://upworthy.natematias.com/2024-06-upworthy-archive-update.html)
- [OSF archive node](https://osf.io/jd64p/)
- [Zenodo mirror of the confirmatory CSV](https://zenodo.org/records/5896854) — used only to independently verify that the filename and released file size are consistent; no mirror data were downloaded.
