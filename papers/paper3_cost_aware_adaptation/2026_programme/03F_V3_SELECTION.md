# F v3: candidate selection (03F section 7, step 2)

Exploratory, simulation only. Scarce family `regimes_f3_scarce_v1.json` (47 regimes, T = 2000, B = 200, k = 5), dev seeds 5301070000-5301070199 (200 per regime), h = 50 (R = 60). Nothing here uses the 14 real streams, the confirmation block or model_selection.

Rule (fixed before running): score = pooled equal-weight mean J over the 47 regimes; choose the lowest; candidates within 0.5% of the lowest are tied and the larger pi_min wins (then the lower score). All candidates: delta .05, paced, ride-out, mixture grid V = 4, 16, 64, 256, 1024, 4096, window = declared delay, inner = frozen tuned wald_cut.

| candidate | pi_min | label_reserve | blind_margin | score (pooled J) | labels | deployed | violation pooled (Wilson) | worst regime (rate, Wilson) |
|---|---|---|---|---|---|---|---|---|
| v3c_pm0.05_lr0.1_bmnone | 0.05 | 0.1 | None | 397.60 | 144.2 | 0.417 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.05_lr0.1_bm8 | 0.05 | 0.1 | 8.0 | 435.27 | 106.8 | 0.155 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.05_lr0.25_bmnone | 0.05 | 0.25 | None | 396.23 | 133.7 | 0.416 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.05_lr0.25_bm8 | 0.05 | 0.25 | 8.0 | 434.44 | 91.9 | 0.154 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.1_lr0.1_bmnone | 0.1 | 0.1 | None | 397.51 | 144.2 | 0.417 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.1_lr0.1_bm8 | 0.1 | 0.1 | 8.0 | 435.27 | 106.8 | 0.155 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.1_lr0.25_bmnone | 0.1 | 0.25 | None | 396.15 | 133.7 | 0.416 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.1_lr0.25_bm8 | 0.1 | 0.25 | 8.0 | 434.44 | 91.9 | 0.154 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.25_lr0.1_bmnone | 0.25 | 0.1 | None | 396.76 | 144.6 | 0.420 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.25_lr0.1_bm8 | 0.25 | 0.1 | 8.0 | 435.20 | 106.8 | 0.154 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.25_lr0.25_bmnone | 0.25 | 0.25 | None | 395.54 | 134.1 | 0.418 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |
| v3c_pm0.25_lr0.25_bm8 | 0.25 | 0.25 | 8.0 | 434.39 | 91.8 | 0.154 | 0/9400 (0.0000-0.0004) | 0.000 (0.000-0.019) sc_r10_d24_benstrong |

Reference arms on the same tapes (h = 50, R = 60):

| arm | score (pooled J) | labels | deployed | violation / exceedance of R = 60 pooled |
|---|---|---|---|---|
| never | 434.00 | 0.0 | 0.000 | 0/9400 (0.0000) |
| wald_cut | 340.82 | 127.9 | 0.608 | 33/9400 (0.0035) |
| cusum | 349.19 | 157.6 | 0.552 | 78/9400 (0.0083) |
| gate_wald | 371.35 | 167.4 | 0.406 | 30/9400 (0.0032) |
| cusum_rb_h8 | 363.96 | 180.0 | 0.627 | 528/9400 (0.0562) |
| stoploss_h50 | 364.55 | 180.1 | 0.630 | 536/9400 (0.0570) |
| f3_pi1_h50 | 393.06 | 167.0 | 0.433 | 0/9400 (0.0000) |
| f3v2d_h50 | 388.30 | 146.3 | 0.447 | 0/9400 (0.0000) |

Lowest score 395.54; tied within 0.5% (<= 397.51): v3c_pm0.05_lr0.25_bmnone, v3c_pm0.1_lr0.1_bmnone, v3c_pm0.1_lr0.25_bmnone, v3c_pm0.25_lr0.1_bmnone, v3c_pm0.25_lr0.25_bmnone.

**Chosen: v3c_pm0.25_lr0.25_bmnone** (pi_min 0.25, label_reserve_frac 0.25, blind_margin None). Frozen in `configs/paper3/f3_v3_frozen.json` before the fresh evaluation.
