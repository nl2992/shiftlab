# CRSP full-cohort retrospective monitor comparison

**Status: frozen before the full-cohort run.** This experiment compares existing monitor families on the complete CRSP test cohort, using one policy frozen from the training split. It is a retrospective diagnostic and does not establish a real-world false-alarm rate or a new algorithmic contribution.

## Objective and policy

The evaluator asks whether standard monitor scores distinguish future periods in which the frozen candidate policy has higher realized cost than its explicit reference. The estimand is paired candidate-minus-reference cost. Positive values mean the candidate is worse under the stated utility.

- Include every observation and PERMNO in the panel's test split; do not sample or screen the test cohort. Fit one pooled policy using every train-split observation.
- Fit one standardized Ridge model (`alpha=1`) using train-only exact feature medians, means and scales, and all training observations. The implementation streams Parquet batches and accumulates Ridge sufficient statistics on CUDA when available.
- Candidate action: long when the next-observed-return prediction is positive. Reference action: long when same-date `vwretd` is positive. Both actions are fixed before test outcomes enter the evaluator.
- Clip next-observed simple returns to `[-0.10, +0.10]`; charge turnover at 0, 5, 10 and 25 basis points. The primary comparison is 5 basis points. Each policy pays entry, changes in position, and the terminal test-path close.
- Reuse the frozen model on the 2018–2019 calibration split and 2020–2025 test split. No test outcomes fit the policy, preprocessing, monitor baseline, or empirical threshold.

## Monitor candidates

1. **Paired decision-cost CUSUM:** one-sided standardized CUSUM of daily mean paired cost, centered and scaled by 2018–2019 daily calibration values. Its threshold is the 95th percentile of 2,000 circular 20-date block-bootstrap maximum statistics over a test-length horizon.
2. **Bounded paired-cost e-process:** existing fixed-mixture `BoundedMeanEProcess`, updated with daily mean paired cost, `epsilon=0`, `alpha=0.05`, and absolute bound `0.20 + 4 * fee`. The bound follows from the 10% return cap and the maximum two units of binary-position turnover per event for each of the two policies.
3. **Predictive-loss CUSUM:** separate diagnostic on daily mean squared error after clipping prediction and target to the same 10% range. It monitors predictive loss, not decision harm.
4. **RBF MMD-squared:** feature-distribution diagnostic comparing each nonoverlapping 20-date window with up to 256 rows sampled from the first 20 calibration dates. The RBF bandwidth is fixed from that reference sample. Its threshold is the 95th percentile of later nonoverlapping calibration-window MMD values.

For retrospective ranking only, each monitor score is compared with an evaluator-only label indicating whether the **next** 20 test dates have positive mean paired decision cost. These overlapping future labels are hindsight diagnostics, not valid online labels or a new monitoring guarantee. Report AUROC and average precision, plus threshold crossing date and frequency.

## Uncertainty and interpretation

The primary 5-basis-point event-weighted mean receives a product bootstrap interval: resample PERMNO clusters and circular 20-trading-date blocks independently, with 2,000 replicates. It is a fixed-policy descriptive interval and does not include model-refit uncertainty. Also report date-equal-weighted means, event-weighted means, action rates and each turnover-cost sensitivity.

This is one historical path. CRSP retrospective close dates do not establish actual release timestamps. Cross-security and serial dependence, the conditional-on-past mean null, and stationary calibration-period behavior are not verified. The e-process threshold is therefore a mathematical reference under its assumptions, not a claimed 5% CRSP error guarantee. CUSUM and MMD thresholds are empirical. The candidate reference is a comparator, not an oracle. Cost clipping and turnover charges are imposed research utilities, not validated market-impact estimates. Do not infer causal drift, live trading performance, deployment safety, or method novelty from this experiment.

## Reproduction

```powershell
uv run python scripts/evaluate_crsp_monitor_comparison.py --root data --device cuda --batch-size 200000 --seed 20261025 --output outputs/crsp_monitor_comparison_full
```

The runner verifies the panel checksum, refuses to overwrite a nonempty output directory, uses temporary disk-backed arrays for the large feature panels, and writes aggregate JSON, CSV, Parquet and SHA-256 checksums. It creates no figure. Any later research figure must use PaperBanana and be checked against these saved aggregates.
