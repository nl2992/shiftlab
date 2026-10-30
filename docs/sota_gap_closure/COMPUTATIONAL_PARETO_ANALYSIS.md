# Computational Pareto analysis
Three trade-offs, each with its own accuracy notion; runtimes include preprocessing and fitting.

## Drift tests (S12, window 128; accuracy = power under a harmful 0.3-sigma shift)
| method | d | harmful_power | benign_rejection | ms_per_test | pareto (harmful power up, time down) |
|---|---|---|---|---|---|
| mmd_exact | 5 | 0.660 | 0.600 | 9.319 | True |
| mmd_rff | 5 | 0.540 | 0.480 | 7.384 | True |
| mmd_multi_exact | 5 | 0.610 | 0.590 | 16.947 | False |
| mmd_multi_rff | 5 | 0.430 | 0.470 | 17.089 | False |
| c2st_lr | 5 | 0.190 | 0.230 | 8.540 | False |
| c2st_lda | 5 | 0.250 | 0.400 | 0.702 | False |
| bbsd | 5 | 0.280 | 0.050 | 0.136 | True |
| mmd_exact | 20 | 0.410 | 0.570 | 11.353 | True |
| mmd_rff | 20 | 0.280 | 0.200 | 11.736 | False |
| mmd_multi_exact | 20 | 0.350 | 0.360 | 19.818 | False |
| mmd_multi_rff | 20 | 0.310 | 0.380 | 22.059 | False |
| c2st_lr | 20 | 0.160 | 0.090 | 7.917 | False |
| c2st_lda | 20 | 0.250 | 0.180 | 0.479 | False |
| bbsd | 20 | 0.340 | 0.050 | 0.144 | True |
| mmd_exact | 100 | 0.180 | 0.220 | 37.984 | False |
| mmd_rff | 100 | 0.110 | 0.130 | 39.424 | False |
| mmd_multi_exact | 100 | 0.110 | 0.190 | 59.809 | False |
| mmd_multi_rff | 100 | 0.110 | 0.090 | 48.026 | False |
| c2st_lr | 100 | 0.090 | 0.120 | 10.552 | False |
| c2st_lda | 100 | 0.040 | 0.010 | 0.569 | False |
| bbsd | 100 | 0.250 | 0.100 | 0.268 | True |
BBSD is the only test whose benign-shift rejection stays at the null level while it has harmful-shift power; it is also by far the cheapest. Exact MMD is dominated by RFF-MMD at d = 5 and 20 only in time, not in power; at d = 100 the closed-form LDA test is slow because of the covariance solve.

## Amortised planners (S11, exact toy instance; accuracy = mean gap to the exact optimum)
| policy | gap | latency_ms | pareto (gap down, latency down) |
|---|---|---|---|
| always_1 | 0.0234 | 0.0146 | True |
| const_0.5 | 0.0948 | 0.0167 | False |
| fsc | 0.1056 | 0.0177 | False |
| lookup | 0.0863 | 0.0285 | False |
| mlp_16 | 0.0623 | 0.1990 | False |
| neyman | 0.0542 | 0.0106 | True |
| remaining | 0.0779 | 0.0172 | False |
| tree_d3 | 0.1104 | 0.1275 | False |
| tree_d6 | 0.0943 | 0.1278 | False |
A learned approximator does not reach the Pareto set: the trivial always-query policy is both cheaper and closer to the optimum than every fitted model on this instance.

## Sequential monitors
See `COMPUTE_ACCURACY_PARETO.md` (engine and legacy detectors; confirmation-pool power vs microseconds per stream-step).
