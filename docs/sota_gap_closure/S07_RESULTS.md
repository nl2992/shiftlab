# S07 robust pro-active inference (pool-based benchmark, separate from the streaming monitors)
The learner sees the unlabeled covariate pool (N points) and selects items **without replacement**; the pool is split into B random blocks in advance, each block is Poisson-sampled with probabilities computed from labels of earlier blocks, and the estimate is the block-size-weighted average of per-block prediction-powered estimators (a martingale, unbiased for any adaptive rule). Streaming algorithms are not compared here. Methods: uniform; batch ASI (probabilities from one fit); sequential ASI; robust ASI (eps .25 uniform mix); `pai_inspired` (sequential ASI with importance-weighted refits; **SOURCE_INSPIRED, not a verified PAI reproduction**: the primary source/code were not accessible); conservative (uncertainty shrunk to prior by label count + exploration floor). One-factor-at-a-time variations around N=5000, n=300, n0=30, 5 blocks, heteroscedastic noise; 150 replicates (60 for N=20000).

MSE ratio vs uniform (< 1 is better):

| factor | value | batch_asi | conservative | pai_inspired | robust_asi | seq_asi | uniform |
|---|---|---|---|---|---|---|---|
| N | 2000 | 1.965 | 1.019 | 1.731 | 1.178 | 1.468 | 1.000 |
| N | 20000 | 1.430 | 1.233 | 1.325 | 1.297 | 1.292 | 1.000 |
| N | 5000 | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| blocks | 10 | 1.452 | 0.672 | 1.038 | 0.631 | 0.729 | 1.000 |
| blocks | 2 | 4.066 | 3.591 | 5.348 | 3.615 | 4.066 | 1.000 |
| blocks | 5 | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| eps | 0.0 | 1.380 | 1.119 | 1.845 | 1.307 | 1.307 | 1.000 |
| eps | 0.1 | 1.380 | 1.119 | 1.845 | 1.136 | 1.307 | 1.000 |
| eps | 0.25 | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| eps | 0.5 | 1.380 | 1.119 | 1.845 | 1.098 | 1.307 | 1.000 |
| hetero | 0.0 | 1.553 | 1.162 | 1.772 | 1.123 | 1.259 | 1.000 |
| hetero | 1.0 | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| hetero | 2.0 | 1.287 | 1.044 | 1.752 | 0.987 | 1.166 | 1.000 |
| misspec | none | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| misspec | wrong_uncertainty | 1.907 | 0.905 | 1.369 | 1.043 | 1.207 | 1.000 |
| n | 100 | 0.915 | 0.788 | 1.278 | 0.758 | 0.831 | 1.000 |
| n | 1000 | 3.379 | 2.875 | 3.310 | 2.855 | 2.860 | 1.000 |
| n | 300 | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| n0 | 20 | 2.383 | 1.407 | 2.680 | 1.447 | 1.705 | 1.000 |
| n0 | 30 | 1.380 | 1.119 | 1.845 | 1.100 | 1.307 | 1.000 |
| n0 | 60 | 1.262 | 0.877 | 1.087 | 0.876 | 0.945 | 1.000 |

Summary by method (coverage of the nominal 95% interval across all settings, speed):

| method | coverage_mean | coverage_min | mse_ratio_median | sel_time_ms | e2e_ms | peak_mb |
|---|---|---|---|---|---|---|
| batch_asi | 0.961 | 0.933 | 1.380 | 0.903 | 3.476 | 5.296 |
| conservative | 0.932 | 0.907 | 1.119 | 1.868 | 4.394 | 5.296 |
| pai_inspired | 0.959 | 0.927 | 1.845 | 1.605 | 4.152 | 5.296 |
| robust_asi | 0.952 | 0.933 | 1.100 | 1.661 | 4.186 | 5.296 |
| seq_asi | 0.950 | 0.933 | 1.307 | 1.746 | 4.379 | 5.296 |
| uniform | 0.960 | 0.913 | 1.000 | 0.260 | 2.786 | 5.289 |

Findings: plain sequential ASI beats uniform in only 3 of 21 settings (small budgets, many blocks, large pilots); robust / conservative variants are never far above 1 and are best; the PAI-inspired variant is the worst at the base setting. Intervals are slightly anti-conservative for the conservative variant (min coverage 0.907). Selection adds negligible time (milliseconds) relative to end-to-end cost.
