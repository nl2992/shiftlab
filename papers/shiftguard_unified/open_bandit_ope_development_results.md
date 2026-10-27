# Open Bandit Random-policy OPE development results

**Status:** descriptive full-archive development run; not confirmation, sequential monitoring, or a deployment decision.

## Question and protocol

Can the uniform Random policy's observed click rate be approximated from the Bernoulli Thompson Sampling (BTS) logger using the documented action propensities? The runner streams the full `bts/all/all.csv` member, computes inverse-propensity scoring (IPS) and self-normalized IPS (SNIPS) for the Random target policy, and compares each estimate with the processed `random/all` on-policy click rate. It reports separate results for display positions 1–3 and then takes the equal-weight mean of those position-specific values. The target action probability is 1/80 per item-position.

The run uses the official Open Bandit Dataset 1.0 archive, and validates its checksum against the acquisition manifest. It streamed 12,357,200 BTS rows and used 1,374,327 Random rows. The OBD paper reports 12,168,084 BTS rows, a difference of 189,116. A release-version difference is plausible: the current official ZOZO page describes a 26-million-row dataset, but it does not publish a component-level count or checksum that resolves this exact difference. The archive and paper counts therefore remain unreconciled. The implementation follows the paper's per-impression, item-position click estimand; it does not treat the result as revenue, user welfare, or slate-level utility.

## Results

For logged row `i`, the target-to-logging ratio is `w_i = (1/80) / p_i`; IPS averages `w_i * click_i`, and SNIPS divides the sum of `w_i * click_i` by the sum of `w_i`. The Random logger's equal-position mean click rate was **0.00346934**. BTS-based IPS estimated **0.00343377** (absolute difference 0.00003558; relative difference 1.03%). SNIPS estimated **0.00330438** (absolute difference 0.00016496; relative difference 4.75%).

| Position | Random observed click rate | BTS IPS | BTS SNIPS | IPS weight ESS / rows | Largest observed weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.003541 | 0.003481 | 0.003504 | 95,842 / 4,118,481 (2.33%) | 1,250 |
| 2 | 0.003470 | 0.003278 | 0.003020 | 4,721 / 4,119,618 (0.115%) | 12,500 |
| 3 | 0.003396 | 0.003542 | 0.003390 | 4,744 / 4,119,101 (0.115%) | 12,500 |

The overall IPS point estimate is close to the Random reference, while the position-level diagnostics show severe weight concentration at positions 2 and 3. The low effective sample fractions mean the aggregate agreement alone is not persuasive evidence of stable estimation. No confidence intervals were computed, so the differences cannot be interpreted as statistically meaningful or insignificant.

### Exploratory day-by-position diagnostic

After the overall analysis, a supplementary v2 diagnostic compared each BTS IPS/SNIPS estimate with the Random logger's observed click rate for the same UTC date and display position (7 dates × 3 positions = 21 cells). This was added post hoc and is descriptive. Mean absolute cell error was **0.000553 for IPS** and **0.000681 for SNIPS**; the largest cell errors were 0.001520 and 0.001636, respectively. Mean day-cell ESS fraction was 2.46% (range 0.035%–5.21%). Thus, the close full-period IPS mean does not describe uniformly close estimates across the observed week. Seven day blocks do not support a reliable cluster-based confidence interval here, so none is reported.

### Cross-fitted DM/DR development supplement

A second full-archive pass compared Direct Method (DM), IPS, SNIPS, and Doubly Robust (DR). The reward model is a cross-fitted empirical click mean for each of 80 items × 3 positions, matching the paper's item-position-only reward assumption and excluding user-affinity features with unverified as-of timing. A fixed, row-wise random two-fold split (seed 20261026) trains each fold's reward model on the opposite fold. The DR formula was checked against the authors' `DoublyRobust.estimate_policy_value` at pinned OBP commit `8cbd5fa4558b7ad2ba4781546d6604e4cc3e07c4`; the deterministic check differed by 1.11e-16.

| Estimator | Equal-position value | Absolute error vs Random | Relative error |
| --- | ---: | ---: | ---: |
| Random observed reference | 0.00346934 | — | — |
| DM, cross-fitted item-position means | 0.00347409 | 0.00000475 | 0.14% |
| IPS, same two-fold evaluation rows | 0.00343377 | 0.00003558 | 1.03% |
| SNIPS, same two-fold evaluation rows | 0.00330438 | 0.00016496 | 4.75% |
| DR, same two-fold evaluation rows | 0.00333390 | 0.00013545 | 3.90% |

The simple item-position DM estimate is closest overall in this particular full-week comparison; DR does not improve on IPS. This is an exploratory point-estimate result, not evidence that DM generally dominates, and it does not reproduce the paper's full 200-seed estimator benchmark. Position-specific DR errors remain uneven: 0.000031, 0.000287, and 0.000088 for positions 1–3. The severe position-2/3 propensity-weight ESS loss persists. No interval or formal estimator comparison is available.

## Interpretation and limits

This establishes that the full archive can support a real logged-bandit OPE development workflow and supplies a useful empirical weight-stability warning. It does not close the real-data confirmation requirement for Q2. The source has only seven days of impressions; no user/session key or verified full-slate identifier; and impression timestamps do not establish feature availability or click-release times. The observed minimum propensity is not a proven population-wide support bound. Dependence, prospective feedback timing, and a deployable utility/cost contract remain unverified. Candidate selection and policy promotion were not studied.

The workstation's NVIDIA GeForce RTX 4060 was available, but this run used CPU processing: decompression, CSV parsing, and small-key aggregation dominate the workload, with no model fitting or large tensor operation suited to CUDA. The decision is recorded in the run manifest.

The BTS row-count discrepancy must be resolved before describing this as an exact paper reproduction or using the BTS estimate as a trusted external reference. The next OBD step is a source-version/action-slot audit, followed by a predeclared temporal holdout and a stronger DR/conservative policy-improvement comparison only if the seven-day source can support defensible uncertainty. Any uncertainty analysis must respect the available dependence structure rather than treating impression rows as independent by default.

## Reproduction

Run from the repository root:

```powershell
uv run --with pandas --with numpy python scripts/evaluate_open_bandit_random_ope.py
```

The IPS/SNIPS runner refuses to overwrite existing output. It records source and runner hashes, aggregate position metrics, and daily-by-position metrics in the [v2 manifest](../../outputs/shiftguard_unified/real_data_development/open_bandit_random_policy_ope_v2/manifest.json). The cross-fitted DM/DR supplement is recorded in its [manifest](../../outputs/shiftguard_unified/real_data_development/open_bandit_dr_ope_v1/manifest.json) and [position metrics](../../outputs/shiftguard_unified/real_data_development/open_bandit_dr_ope_v1/position_metrics.csv). Both outputs contain aggregates only. To reproduce the DM/DR pass, clone the pinned official OBP source, then run:

```powershell
git clone --depth 1 https://github.com/st-tech/zr-obp.git tmp/obp_reference
git -C tmp/obp_reference checkout 8cbd5fa4558b7ad2ba4781546d6604e4cc3e07c4
uv run --with tqdm --with mypy-extensions --with pyyaml --with seaborn --with pyieoe --with pingouin python scripts/evaluate_open_bandit_dr_ope.py
```

Source: Saito et al., [*Open Bandit Dataset and Pipeline*](https://arxiv.org/abs/2008.07146); [official ZOZO dataset page](https://research.zozo.com/data.html).
