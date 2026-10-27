# Robust ASI California ACS reproduction results

**Status:** corrected fixed-horizon reproduction completed and independently verified on CUDA, 2026-10-26. This is one seeded ACS task sample with repeated Bernoulli query trials, not independent data replications and not a ShiftGuard monitoring or intervention result.

## Design and audit trail

The experiment follows the California 2019 ACS age-income task in Li, Zrnic, and Candès, [Robust Sampling for Active Statistical Inference (NeurIPS 2025)](https://papers.nips.cc/paper_files/paper/2025/file/6389470564214983604d1ac81631c2c5-Paper-Conference.pdf), and the authors' [released implementation](https://github.com/lphLeo/Robust-Active-Statistical-Inference). It estimates the age coefficient in unweighted no-intercept OLS of `PINCP` on `AGEP` and `SEX`, comparing uniform, residual/influence-scale active, and robust active sampling. It uses 20,000 seeded sample records, 6,000 base-model labels, 420 burn-in labels, a 13,580-record inference pool, five-fold burn-in cross-validation, 10 budgets from 5% through 20%, and 500 trials per method and budget. XGBoost training and Monte Carlo calculations ran on the NVIDIA RTX 4060 Laptop GPU.

The first full run, `robust_asi_acs_v1`, is **invalid and superseded**. Its influence-scale helper clipped `abs(h.T @ x) * predicted_absolute_residual` to `[0, 1]`. On this sample that collapsed the scores to a constant, making the active allocation uniform and the three output arms identical. The source paper defines the target-coordinate residual score and its released notebook computes this score without that clipping; the notebook clips final probabilities instead. The corrected implementation preserves the score scale and normalizes only the propensity vector. The invalid run's manifest is marked `invalid_superseded`; its artifacts remain for audit and must not be used as results.

The corrected run is `outputs/shiftguard_unified/sota_reproductions/robust_asi_acs_v2/`. Its independent verifier checks all 15,000 rows, 30 complete budget-method groups, equal expected budgets, valid support, recomputed summary metrics, source/data/receipt hashes, and output hashes. The verifier passed. The protocol, runner, independent estimator and verifier are source-hashed in the manifest. See [`robust_asi_acs_reproduction_protocol.md`](robust_asi_acs_reproduction_protocol.md).

## Results

RMSE and interval width are in age-coefficient units. Coverage is empirical 90% sandwich-interval coverage across the 500 query trials for this one sampled dataset.

| Expected pool-label budget | Uniform RMSE | Active RMSE | Robust active RMSE | Uniform coverage | Active coverage | Robust coverage | Selected robust `rho` |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.00% | 91.32 | 103.71 | **80.71** | 91.4% | 91.4% | 91.0% | 0.30 |
| 6.66% | 81.96 | 95.21 | **74.21** | 89.4% | 88.4% | 89.8% | 0.29 |
| 8.34% | 71.20 | 82.48 | **65.66** | 91.6% | 89.6% | 90.0% | 0.29 |
| 10.00% | **68.05** | 74.51 | 74.51 | 89.6% | 92.2% | 92.2% | 0.00 |
| 11.66% | 64.58 | 67.93 | **52.45** | 89.2% | 91.2% | 90.6% | 0.28 |
| 13.34% | 58.51 | 59.79 | **52.16** | 88.4% | 88.6% | 88.8% | 0.27 |
| 15.00% | 54.73 | 54.59 | **43.90** | 90.4% | 92.4% | 93.4% | 0.26 |
| 16.66% | 49.73 | 46.65 | **40.79** | 91.0% | 91.8% | 93.2% | 0.25 |
| 18.34% | 50.69 | 47.80 | **41.57** | 91.4% | 90.2% | 91.8% | 0.25 |
| 20.00% | 47.04 | 42.48 | **37.54** | 91.6% | 93.8% | 94.6% | 0.24 |

Across the 10 budget points, the unweighted mean RMSE was 63.78 for uniform, 67.51 for active, and 56.35 for robust active. Robust active had lower RMSE than uniform at 9 of 10 budgets; at 10%, cross-validation selected `rho=0`, so robust active reduced to the active arm and both had higher RMSE than uniform. Active alone beat uniform at 4 of 10 budgets. These are descriptive comparisons over repeated queries on a fixed sample, not uncertainty intervals over datasets.

Burn-in cross-validation selected the largest candidate radius `c=10,000` at 9 of 10 budgets; it selected `c=50` at 10%. This boundary selection means the frozen candidate grid did not locate an interior optimum for most budgets. The robust path's selected `rho` values were 0.24–0.30 at the nine boundary-radius budgets. Treat that as a sensitivity and tuning limitation, not evidence that the boundary is optimal beyond the frozen grid.

## Interpretation and remaining limits

The corrected result is consistent with the paper's motivation: residual-scale active sampling can be harmed by an inaccurate scale estimate, while robust interpolation can hedge toward uniform and improve this particular fixed-horizon estimator. It does not validate the authors' reported figures, because the implementation uses a reproducible seeded split and exact expected-budget propensities; it covers only the ACS task, and uses an unweighted sample-average target. The 500 Bernoulli trials share one sample, model fit, and burn-in set. The empirical interval coverage is therefore not an independent calibration study, and the asymptotic sandwich intervals have no finite-sample guarantee here.

This reproduction closes the original-task implementation gap for one high-priority Q3 comparator. It does not close the broader resource-allocation benchmark: the method's fixed-horizon batch-label setting does not establish a sequential harm monitor, delayed-label validity, intervention utility, or a hard pathwise budget for the integrated ShiftGuard system. The main integrated efficacy comparison, broader source-based comparator audit, and credible fresh real-data confirmation remain open.
