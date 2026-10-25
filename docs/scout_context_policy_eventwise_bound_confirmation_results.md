# Eventwise-propensity scout confirmation results

## Confirmatory question

The frozen confirmation asked whether the eventwise-propensity-bound scout improves evaluator-known postpromotion net decision utility over pooled rank and nested-volume selection under the registered abrupt context-prevalence DGP. The primary contrasts were equally weighted over 24 cells and paired by seed cluster. The two primary one-sided lower limits use Bonferroni allocation and percentile seed-cluster bootstrap resampling; coverage is approximate rather than an exact finite-sample guarantee.

## Result

The frozen 600-seed-per-cell comparison completed on CUDA with seed block 20271000–20271599. It contains 57,600 method-cell-seed rows: 600 paired seeds across 24 prevalence × signal × proxy-error × budget settings, with four methods per stream.

| Contrast | Mean expected-utility difference | 95% paired seed-cluster bootstrap interval | Approx. familywise one-sided lower limit |
| --- | ---: | ---: | ---: |
| Eventwise scout − pooled rank | +0.5990 | [+0.4515, +0.7619] | +0.4515 |
| Eventwise scout − nested-volume | +0.5703 | [+0.4311, +0.7217] | +0.4311 |
| Eventwise scout − minimum-bound scout | +0.4383 | [+0.3325, +0.5528] | Not a primary comparison |

Both primary lower limits exceed zero, so the registered grid-level success rule passed. Cell-equal mean expected postpromotion utility was +0.5707 for the eventwise scout, +0.1324 for the minimum-bound scout, +0.0004 for nested-volume, and −0.0283 for pooled rank.

The eventwise scout promoted 108/14,400 cell-streams (0.75%); one was harmful by evaluator-known future utility. The minimum-bound scout promoted 17, rank 4, and nested-volume 2; their harmful-promotion counts were 0, 3, and 0, respectively. All methods averaged 473.45 queried labels per stream under matched hard caps, and no cap violation occurred. The complete cellwise promotion, utility, label, and horizon results are in the Parquet summary.

## Interpretation and limits

This is evidence that the sharper predictable support bound improves the registered eventwise scout on this synthetic grid. It does not establish general superiority or novelty. The argument relies on the fixed split, uniform randomized query probability, positive query support, bounded paired costs, the stated eventwise conditional-mean null, and the registered immediate-feedback process. The primary bootstrap comparison is approximate and cluster-based.

The candidate remains a research method for further stress tests. Next vary gradual and recurring context prevalence, temporal dependence, signal magnitude, proxy quality, and resource caps on development seeds; retain the same null calibration where its assumptions apply and use a fresh seed block for any new confirmation. Delayed/selective feedback and covariate-adaptive querying require separate protocols and validity arguments.

## Reproduction artifacts

- Frozen design: [`scout_context_policy_eventwise_bound_confirmation_protocol.md`](scout_context_policy_eventwise_bound_confirmation_protocol.md)
- Stream-level metrics: [`scout_context_drift_confirmation_streams.parquet`](../outputs/scout_context_policy_eventwise_bound_confirmation_600/metrics/scout_context_drift_confirmation_streams.parquet)
- Cell-level metrics: [`scout_context_drift_confirmation_cells.parquet`](../outputs/scout_context_policy_eventwise_bound_confirmation_600/metrics/scout_context_drift_confirmation_cells.parquet)
- Primary contrasts: [`scout_context_drift_confirmation_contrasts.parquet`](../outputs/scout_context_policy_eventwise_bound_confirmation_600/metrics/scout_context_drift_confirmation_contrasts.parquet)
- Run report and manifest: [`scout_context_drift_confirmation.md`](../outputs/scout_context_policy_eventwise_bound_confirmation_600/reports/scout_context_drift_confirmation.md), [`manifest.json`](../outputs/scout_context_policy_eventwise_bound_confirmation_600/reports/manifest.json)

No figure was generated. Use PaperBanana for any future visual and verify it against the saved metrics.
