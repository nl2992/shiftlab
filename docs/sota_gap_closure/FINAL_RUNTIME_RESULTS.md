# Final runtime results (matched repeated runs on one idle machine)
The frozen arms were timed on identical streams (T=2000, S=100, 10% labels, delay 5) with 5 repeats in one process after the statistical confirmation run finished; see `COMPUTE_ACCURACY_PARETO.md` for the full tables.

| method | cold_s | warm_s | warm_sd_s | us_per_obs | tracemalloc_peak_mb |
|---|---|---|---|---|---|
| pprm_parent(engine) | 0.1614 | 0.1563 | 0.0274 | 0.7813 | 17.3157 |
| HG | 0.2173 | 0.2120 | 0.0153 | 1.0598 | 22.1244 |
| discount_only | 0.1584 | 0.1619 | 0.0048 | 0.8095 | 17.3158 |
| costgate_only | 0.2278 | 0.2046 | 0.0265 | 1.0229 | 22.1245 |
| multiwindow(3) | 0.6814 | 0.6320 | 0.0235 | 3.1602 | 23.7409 |
| HG_growth_alloc | 0.6095 | 0.6033 | 0.0159 | 3.0167 | 71.9523 |
| HG_robustmix | 0.6189 | 0.6245 | 0.0736 | 3.1227 | 71.9542 |
| cost_discount | 0.1894 | 0.1829 | 0.0244 | 0.9144 | 17.3158 |
| HG_lrv100 | 0.4059 | 0.3978 | 0.0116 | 1.9891 | 22.5256 |
| pprm_tight(legacy cumsum) | 0.0127 | 0.0127 | 0.0015 | 0.0634 | 19.2197 |
| HG(legacy cumsum) | 0.0417 | 0.0389 | 0.0024 | 0.1947 | 33.6042 |
| page_hinkley | 0.0169 | 0.0152 | 0.0001 | 0.0761 | 6.6016 |
| cusum | 0.0153 | 0.0150 | 0.0006 | 0.0749 | 6.6016 |

HG costs ~1.36x the parent per run in the event-level engine (the cost gate adds a second channel); the robust mixture and the long-run-variance bet add 2.95x and 1.88x over HG. HG takes 1.1 microseconds per stream-step in the engine (vectorised over 100 streams); compare with the 0.1-100 ms per window test of the drift tests in `S12_EFFICIENT_DETECTION_RESULTS.md`.
