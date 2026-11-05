# SOTA benchmark fidelity audit

**Audit date:** 2026-11-04
**Revision:** `1e46378132c8c090f67b39e9bd10b91a75cb4919`
**Scope:** the SOTA comparator pool and the common-contract certificate adapters used by the SOTA sprint and Sprint 2. This is a paper-to-code and protocol audit, not a fresh rerun of the benchmark.

## Verdict

The simulator and paired economic comparison are useful for the declared two-frozen-model deployment problem. The published methods are not all being compared as native algorithms, and one important class label was wrong: `xu_acquisition_only` was included in `CERTIFIED_PUBLISHED`, although Xu et al.'s paper is about active, anytime-valid risk-controlling prediction sets. The benchmark policy combines Xu's acquisition component with ShiftLab's own paired-loss certificate. It can be recorded as a V1 composite policy, but it must not be described as Xu's published certificate or counted as a published certified deployment comparator.

Therefore the measurements remain usable as **common-contract adapter comparisons**, but published-SOTA claims that identify Xu as the strongest certified comparator are not verified. The class correction is implemented in `bench.py`; separately written amended analyses exclude Xu from published-certificate pools while preserving registered outputs. A follow-up source audit found the Family-H summary still had a local legacy pool that included Xu and the non-native Choe–Ramdas port while omitting other registered certificate ports. The historical H summaries are preserved and marked legacy; a corrected matched 20-seed replay is complete at `outputs/sprint2/round5/H_corrected_real_20/`, with its report in `docs/sprint2/family_h/corrected_real_20.md`. The replay does not resolve same-sample comparator-selection uncertainty or establish confirmatory superiority.

The validation amendment also had a broader selected pool than the shared registry: it removed Xu but continued to rank the Choe–Ramdas adapter and ShiftLab QCE ports as “best certified.” That output is preserved as a legacy adapter-pool sensitivity. A new strict validation analysis uses only the six `bench.CERTIFIED_PUBLISHED` ports. On that pool, A5b and A1b are null-safe but each passes only 2/5 iid non-inferiority checks, so neither meets the full H1 criterion; no H2 candidate meets its combined safety and four-of-five significance rule. These are still same-sample selected contrasts and common-contract ports, not confirmatory or author-native results.

## Paper-to-implementation checks

| Method | What the paper establishes | What this benchmark runs | Audit result |
|---|---|---|---|
| Karampatziakis, Mineiro & Ramdas, *Off-policy Confidence Sequences* (ICML 2021) | Time-uniform off-policy value CSs; paper includes gated deployment. | MOPE-based paired binary-loss certificate, HT query weights, fixed range or adaptive-range adapter, delay and hard-budget handling. | Mathematically relevant and plausibly mapped, but it is an adapter: the benchmark changes the logged-feedback setup, reward coding, delay semantics, and cost objective. Local notes disclose that it does not port appendices C–E. Do not call the whole deployment policy author-native. |
| Balachandran, *Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates with Matching Label-Complexity Bounds* (arXiv:2609.17560) | Paired update auditing on disagreements; a zero-label disagreement tier and an anytime-valid labeled tier, with its stated assumptions. | Printed PrPl empirical-Bernstein construction and selected verdict semantics; common pacer; optional omissions of Tier 0 and learned judge routing. | Relevant target. Local code notes the missing author code and adapter choices. Label as “DISCERN-style certificate adapter”; do not imply full protocol reproduction. The PrPl variance scaling fix should remain explicit. |
| Arnold et al., *Sequential Model Confidence Sets* (published in JRSSB, 2026; preprint arXiv:2404.18678) | Time-uniform confidence sets for strongly, weakly, and uniformly weakly superior models via sequential tests/e-processes, confidence sequences and multiple-testing control. The final article retains the pairwise bounded-difference e-process constructions and explains that predictable scaling changes the target to a normalized loss. | Source-reproduced pairwise inference with a selective-feedback, predictable-bound extension, plus a ShiftLab retain-incumbent rule and pacer. | Native inference core has local numerical replication. Deployment, selective feedback and delayed feedback are adapters; the paper’s native full-feedback result is not the entire simulator policy. Current-regime superiority is not the same estimand as its cumulative confidence set. The final 2026 article was checked against the cited preprint. |
| Xu, Karampatziakis & Mineiro, *Active, Anytime-Valid Risk Controlling Prediction Sets* (NeurIPS 2024) | Anytime-valid risk control for prediction sets under adaptive labeling and an expected-proportion label constraint. | Acquisition component combined with ShiftLab’s own paired-loss e-process, a pathwise hard cap, and switching/rollback costs. | Useful V1 composite and acquisition baseline, **not** a Xu certificate for the benchmark’s challenger-advantage null. Keep out of `CERTIFIED_PUBLISHED`; the ShiftLab certificate, not Xu's theorem, supplies the paired null test. |
| Karimi et al., *Online Active Model Selection for Pre-trained Classifiers* (AISTATS 2021) | Online selective sampling to identify the best among pretrained classifiers, with stated guarantees. | Author-reproduced native selector plus a distinct hard-cap deployment adapter. | Local source comparison is strong; the adapter is correctly disclosed. In the two-model binary setting, its query score is instance-blind, so conclusions must be scoped to this setting. |
| Liu et al., *Contextual Active Model Selection* (NeurIPS 2024) | CAMS and CAMS-MAX model selection and active querying under their policy/advice setup. | Source-reproduced CAMS and CAMS-MAX cores with the benchmark context-free constant-policy advice, plus argmax-incumbent deployment, hard cap, delayed-update adapters and switching costs. | Both algorithm cores are implementable and now registered. Evaluation uses only constant policies, not the paper’s contextual policy sets or full experimental system. Call entries “CAMS/CAMS-MAX constant-policy deployment adapters.” D2 is a ShiftLab hybrid, not published CAMS. |

**CAMS-MAX.** Appendix G.7 defines a stochastic-setting ablation that selects the most probable
policy under learned policy weights and then that policy's most probable model. The paper permits a
context-free special case with constant policies; the WP1/WP2 streams' two-model loss contract
supports exactly that advice set. Its recommendation core is therefore applicable and is now
registered as `cams_max_adapter`. Action deployment, delayed feedback, hard budget and switching
cost remain common-contract adapters, as for `cams_adapter`. This is not a reproduction of the
paper's contextual datasets or complete experimental system. [NeurIPS paper, Appendix G.7](https://proceedings.neurips.org/paper_files/paper/2024/file/5966e7c5c017d8449d215faeb1db4173-Paper-Conference.pdf)

The paired post hoc replay covers all 348 non-twin WP1 episodes (14 source clusters, three seeds)
under the common T=2000, B=200, c_s=5, native-delay contract. Relative to CAMS-MAX, the CAMS
adapter's mean J is lower by 3.73 [95% source-cluster bootstrap CI: 1.30, 5.60] over all episodes.
For the 10 late-improvement episodes, CAMS-MAX minus CAMS is +5.29 [−2.33, +17.00]; for 16
reversals it is −6.49 [−27.26, +17.67]. This shows no clear advantage for CAMS-MAX in this
loss-only deployment setting. The 186 stationary-better episodes give +3.93 [1.76, 6.03], and 136
null episodes give +4.55 [−0.48, +8.43]. These are same-sample descriptive intervals, not adjusted
confirmatory tests. Machine-readable contrasts and run provenance are in
[`wp1/cams_max_comparison.json`](wp1/cams_max_comparison.json) and the gitignored
`outputs/sprint2/WP1/cams_max_comparison/manifest.json`.

Broader matched validation compares CAMS-MAX and CAMS on the same seeds across 21 synthetic
regimes (100 seeds each), in-class null/adverse regimes (1,000 seeds), two out-of-class nulls
(1,000 seeds each), nine cached real datasets (10 seeds), and five fresh real datasets (20 seeds).
The report includes per-regime and equal-source clustered intervals, with exact panel definitions
and reproduction commands in [`CAMS_MAX_VALIDATION.md`](CAMS_MAX_VALIDATION.md) and machine-readable
contrasts in [`CAMS_MAX_VALIDATION.json`](CAMS_MAX_VALIDATION.json). CAMS-MAX's equal-source ΔJ is
+4.24 [1.95, 6.92] on the cached sources and +1.99 [−0.51, +4.41] on the fresh sources. These
post-development, same-contract results are descriptive and do not establish confirmatory
superiority or a null-validity guarantee.

Reproduction command:

```sh
uv run python scripts/sota_sprint/late_real.py run --streams all --policies cams_adapter,cams_max_adapter --seeds 3 --seed-base 2026110803 --workers 2 --out outputs/sprint2/WP1/cams_max_comparison
uv run python scripts/sota_sprint/late_real.py analyze outputs/sprint2/WP1/cams_max_comparison --classes outputs/sprint2/WP1/classes.json --extra-pairs 'cams_max_adapter|cams_adapter:' --out docs/sprint2/wp1/cams_max_comparison.json
```
| Choe & Ramdas, *Comparing Sequential Forecasters* (Operations Research 2024) | Time-uniform inference for bounded sequential score differences and weak-null comparisons under its conditions. | Sprint’s `choe_ramdas_eb` is documented locally as a query-conditional PrPl-EB-style port, also named DiscernQCE; it is not author code. | Relevant statistical comparator, but not a faithful paper implementation. Name it as a port and state its precise null and filtration. Do not count it as a directly reproduced published method. |

These statements align with the repository’s own implementation-validation notes, which report numerical source reproduction for CAMS, Model Picker and SMCS, and explicitly distinguish several adapters. Those are useful controls against overclaiming; they do not make all benchmark entries native implementations.

## Protocol and inference caveats

1. **Comparator class correction.** The shared registry in `bench.py` separates `xu_acquisition_only` into `ACQUISITION_ADAPTERS`, while retaining `REGISTERED_CERTIFIED_PUBLISHED` to reconstruct historical protocols. Xu remains a V1 composite only because ShiftLab supplies its test. Amended reports exist for SOTA validation, WP1 and WP2. The original Family-H summary used a stale local pool; it is now marked historical, and the corrected rerun is recorded separately when complete.
2. **Selection uncertainty.** “Best comparator” is selected using the same evaluation seeds, then a paired interval/test is reported against that selected method. This is a useful conservative ranking rule for the candidate’s point contrast, but the nominal interval or p-value does not account for selection among baselines. For confirmatory superiority claims, select the comparator on development data or correct for the baseline-selection procedure.
3. **Scope of guarantees.** “V1” is not one universal null. A conditional-mean process can control different filtrations and estimands depending on whether all events, only queried disagreements, or inverse-propensity outcomes enter the process. Store the exact null, filtration, event index, and feedback conditions per adapter. Do not infer validity from a method’s name or from a low empirical rate.
4. **Fair cost contract.** Applying a common hard cap, label price, delay and switching cost creates a useful deployment comparison, but changes native algorithms whose papers use expected label proportions, full feedback, or no switching-cost objective. Report native-paper fidelity and common-contract results in separate columns.
5. **Citations/versioning.** Pin the actual paper versions and source-code commits used. The local audit names source commits for several code reproductions, but DISCERN is a recent preprint and some other adapters have no source-code reproduction.

## Required correction before SOTA verdicts

- Remove Xu from `CERTIFIED_PUBLISHED`; add it to a named acquisition-component/adapted-baseline category. **Done.**
- Recompute affected validation, WP1, and WP2 summaries in separate amended outputs. **Done.** Sprint 2 family R/T and benchmark validation summaries preserve historical numbers and explicitly qualify claims. Raw policy simulations were not repeated.
- Update publication-register and leaderboard wording so every claim names the exact comparator implementation, null, regime, metric, uncertainty procedure and common-contract deviations.
- For future confirmatory tests, freeze the strongest comparator on development data, or account for comparator selection in inference.

## Amendment outputs

- SOTA validation: `docs/sprint2/validation_amendment_20261104/` is the historical Xu-excluded adapter-pool sensitivity (it retains Choe–Ramdas and QCE ports); `docs/sprint2/validation_strict_published_20261104/` ranks only the six `CERTIFIED_PUBLISHED` ports. Same-seed per-regime comparator selection remains descriptive.
- WP1: `docs/sprint2/wp1/results_amended_no_xu.json` is the historical no-Xu adapter-panel sensitivity. The separate strict shared-pool analysis is in `wp1/strict_published_subset_20261104.json`; a supplemental 1,044-job replay completes all six ports, and the selected late-class comparator and NOT_SUPPORTED verdict are unchanged. Same-episode comparator selection remains unadjusted.
- WP2: `docs/sprint2/wp2/amended_no_xu/` preserves the Xu-excluded mixed adapter-panel sensitivity. The strict six-port pooled analysis is in `wp2/strict_published_20261104/` and `wp2/COMPARATOR_CLASS_AUDIT.md`: H2 remains positive, H4 fails, and the H1a strict-panel count is 4/6. Xu remains visible as an acquisition composite in descriptive rows only; historical tables and raw runs are preserved.
- Family H: historical `screen_synthetic.json` and `screen_real_fresh.json` best-comparator fields were generated from `LEGACY_SUMMARY_COMPARATOR_POOL = {Xu acquisition adapter, adaptive-range+front, Choe–Ramdas port, SMCS}`. This pool is neither the registered published-certificate pool nor complete. The summarizer now defaults to `bench.CERTIFIED_PUBLISHED`; `--legacy-comparator-pool` reproduces the old summary exactly. The corrected 20-seed fresh-real replay includes all six registered certificate ports and reports the two non-published adapters separately.

## Primary sources consulted

- Karampatziakis, Mineiro & Ramdas, [*Off-policy Confidence Sequences*](https://proceedings.mlr.press/v139/karampatziakis21a.html), ICML 2021; [preprint](https://arxiv.org/abs/2102.09540).
- Balachandran, [*Pay Only for Disagreement*](https://arxiv.org/abs/2609.17560), arXiv:2609.17560.
- Arnold et al., [*Sequential Model Confidence Sets*](https://doi.org/10.1093/jrsssb/qkag066), JRSSB (2026); [preprint](https://arxiv.org/abs/2404.18678), arXiv:2404.18678.
- Xu, Karampatziakis & Mineiro, [*Active, Anytime-Valid Risk Controlling Prediction Sets*](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6eb05d8bc6bd7bb6868c64b5802125bd-Abstract-Conference.html), NeurIPS 2024; [preprint](https://arxiv.org/abs/2406.10490).
- Karimi et al., [*Online Active Model Selection for Pre-trained Classifiers*](https://proceedings.mlr.press/v130/reza-karimi21a.html), AISTATS 2021; [preprint](https://arxiv.org/abs/2010.09818).
- Liu et al., [*Contextual Active Model Selection*](https://proceedings.nips.cc/paper_files/paper/2024/hash/5966e7c5c017d8449d215faeb1db4173-Abstract-Conference.html), NeurIPS 2024; [preprint](https://arxiv.org/abs/2207.06030).
- Choe & Ramdas, [*Comparing Sequential Forecasters*](https://doi.org/10.1287/opre.2021.0792), Operations Research 72(4), 1368–1387 (2024); [preprint](https://arxiv.org/abs/2110.00115).
