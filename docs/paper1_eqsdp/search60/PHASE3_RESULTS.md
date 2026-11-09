# Paper 1 search60 Phase 3: full matched development evaluation

Status: development-stage results. All nine datasets and both episode parities are development-exposed; the 40 configs were selected on a screen subset, so the primary statistic uses only episodes outside the screen subset (`SCREEN_SUBSET.json`, partial guard only). No originality or validity claim.

Protocol: `split=all` (every episode of nine datasets), policy seeds 0-9, registered seed derivation, paired against parent `s2armr_H1100` on identical (dataset, episode, seed) keys, seed-averaged per episode, equal dataset weights. J = net cost / T x 100 (pp of T), L = prediction loss / T x 100. CI = 95% stratified episode bootstrap (2000 resamples, seed 20261109). pct = dJ / parent J x 100. dLA / dFP = change in late-adoption / false-promotion regret components (pp of T, from `trace_run.decompose`). p95/CVaR95 = over paired episode dJ.

Source: `outputs/paper1_eqsdp/search60/full/p3_*/records.jsonl`; ledger rows with `phase=3, eval=full`; tables `docs/paper1_eqsdp/search60/tables/phase3_*.csv`.
Commands: `python scripts/paper1_eqsdp/search60/run_phase345.py p3run|p3check|p3analyze`.

## Parent reproduction
`s2armr_H1100` in the new run vs existing records: {"stage3_odd": {"n_old": 3740, "n_matched": 3740, "net_mismatch": 0, "loss_mismatch": 0, "labels_mismatch": 0, "switches_mismatch": 0, "max_abs_net_diff": 0.0}, "stage5_even": {"n_old": 3770, "n_matched": 3770, "net_mismatch": 0, "loss_mismatch": 0, "labels_mismatch": 0, "switches_mismatch": 0, "max_abs_net_diff": 0.0}, "n_new": 7510}

## Headline
Of the 40 shortlisted configs, 28 have out-of-subset dJ < 0; 9 have the 95% CI excluding 0 on the negative side (all-episode: 17).

## Shortlist ranked by primary dJ (out-of-subset), top 15 of 40
| config_id | k | dJ | pct | dJ_lo | dJ_hi | dL | labels | switches | dLA | dFP | p95 | cvar95 | vs_w98_dJ | vs_w98_lo | vs_w98_hi | vs_w97_dJ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P2_K4__B15_D40_E48_F60 | 4.000 | -0.112 | -0.47 | -0.170 | -0.063 | 0.010 | 53.123 | 0.907 | 0.028 | -0.026 | 0.616 | 1.027 | -0.116 | -0.172 | -0.067 | -0.118 |
| P2_K2__E48_F60 | 2.000 | -0.097 | -0.41 | -0.154 | -0.052 | -0.038 | 52.826 | 1.159 | -0.020 | -0.016 | 0.636 | 0.874 | -0.101 | -0.158 | -0.057 | -0.104 |
| P2G_K4__E46_E48_F51_F60 | 4.000 | -0.086 | -0.36 | -0.139 | -0.043 | -0.028 | 53.410 | 1.160 | -0.013 | -0.013 | 0.645 | 0.891 | -0.090 | -0.145 | -0.047 | -0.092 |
| P2G_K4__A03_E48_E49_F60 | 4.000 | -0.085 | -0.36 | -0.141 | -0.038 | -0.044 | 59.437 | 1.164 | -0.022 | -0.019 | 0.657 | 0.882 | -0.089 | -0.144 | -0.043 | -0.092 |
| P2_K5__A02_B15_C23_E48_F60 | 5.000 | -0.085 | -0.36 | -0.147 | -0.038 | -0.049 | 60.654 | 1.175 | -0.018 | -0.029 | 0.685 | 0.965 | -0.088 | -0.152 | -0.039 | -0.091 |
| P2G_K4__A04_B13_F55_F59 | 4.000 | -0.054 | -0.23 | -0.102 | -0.007 | -0.089 | 81.084 | 1.257 | -0.045 | -0.043 | 0.561 | 1.090 | -0.058 | -0.105 | -0.012 | -0.060 |
| P2A_K5__B20_D34_E41_E46_E50 | 5.000 | -0.053 | -0.22 | -0.090 | -0.013 | 0.019 | 75.764 | 0.880 | -0.007 | 0.015 | 0.582 | 1.248 | -0.057 | -0.097 | -0.021 | -0.059 |
| P2G_K4__B18_E41_E43_E47 | 4.000 | -0.042 | -0.18 | -0.089 | 0.016 | 0.029 | 48.752 | 1.152 | 0.006 | 0.022 | 0.746 | 1.631 | -0.046 | -0.091 | 0.007 | -0.049 |
| P2A_K5__A06_B20_C28_E45_F55 | 5.000 | -0.037 | -0.16 | -0.092 | 0.009 | -0.031 | 69.635 | 1.205 | 0.012 | -0.043 | 0.361 | 0.586 | -0.041 | -0.097 | 0.005 | -0.043 |
| P2G_K3__A04_C22_F59 | 3.000 | -0.033 | -0.14 | -0.064 | -0.001 | -0.056 | 76.005 | 1.257 | -0.045 | -0.010 | 0.526 | 1.087 | -0.037 | -0.067 | -0.005 | -0.039 |
| P2_K5__A06_A08_D36_E44_F59 | 5.000 | -0.023 | -0.10 | -0.069 | 0.040 | 0.016 | 85.078 | 0.916 | 0.038 | -0.034 | 0.539 | 1.377 | -0.027 | -0.077 | 0.030 | -0.030 |
| P1_E48_s0 | 1.000 | -0.023 | -0.10 | -0.055 | 0.014 | 0.069 | 43.507 | 1.124 | 0.039 | 0.029 | 0.486 | 0.937 | -0.027 | -0.060 | 0.010 | -0.029 |
| P2_K5__A06_B20_C28_E45_F55 | 5.000 | -0.023 | -0.10 | -0.075 | 0.018 | -0.030 | 69.635 | 1.260 | 0.012 | -0.043 | 0.382 | 0.682 | -0.027 | -0.076 | 0.014 | -0.029 |
| P2_K3__B20_E45_F54 | 3.000 | -0.022 | -0.09 | -0.045 | -0.001 | 0.031 | 55.166 | 1.163 | 0.017 | 0.013 | 0.288 | 0.690 | -0.026 | -0.048 | -0.003 | -0.028 |
| P2_K3__A05_B13_F59 | 3.000 | -0.020 | -0.08 | -0.063 | 0.036 | -0.036 | 75.481 | 1.237 | -0.030 | -0.006 | 0.576 | 1.302 | -0.024 | -0.067 | 0.028 | -0.026 |

## Controls vs parent (out-of-subset)
| config_id | dJ | pct | dJ_lo | dJ_hi | dL | labels | switches |
|---|---|---|---|---|---|---|---|
| s2wald_l0.98_g0.3_H1100 | 0.004 | 0.02 | -0.000 | 0.010 | 0.002 | 70.121 | 1.233 |
| s2wald_l0.97_g0.2_H1100 | 0.006 | 0.03 | -0.011 | 0.024 | 0.067 | 70.121 | 0.984 |
| EQSDp_l0.98_g0.3 | 0.190 | 0.80 | 0.130 | 0.239 | -0.102 | 175.640 | 1.337 |
| wald_l0.97_g0.2 | 0.191 | 0.81 | 0.123 | 0.247 | -0.044 | 175.640 | 1.108 |

## Pareto archive (out-of-subset; full nine-dataset tables in `phase3_pareto_archive.csv`)
- **lowest_cost**: `P2_K4__B15_D40_E48_F60` (B15[s0]+D40[s1]+E48[s0]+F60[s0]) dJ=-0.112 [-0.170, -0.063] (-0.47%), dL=0.010, cvar95=1.03, synergy=-0.053
- **best_error_parity**: `P2_K2__E48_F60` (E48[s0]+F60[s0]) dJ=-0.097 [-0.154, -0.052] (-0.41%), dL=-0.038, cvar95=0.87, synergy=-0.019
- **strongest_downside_cvar95**: `P1_B15_s0` (B15[s0]) dJ=-0.002 [-0.005, 0.000] (-0.01%), dL=-0.002, cvar95=0.00, late_dJ=0.000
- **highest_synergy**: `P2A_K2__B19_C26` (B19[s1]+C26[s1]) dJ=0.422 [0.334, 0.528] (1.79%), dL=0.315, cvar95=3.53, synergy=-1.065
- **best_late_change_kc_sf**: `P2_K5__A02_B15_C23_E48_F60` (A02[s0]+B15[s0]+C23[s1]+E48[s0]+F60[s0]) dJ=-0.085 [-0.147, -0.038] (-0.36%), dL=-0.049, cvar95=0.97, synergy=-0.003

Per-dataset dJ of archive entries (out-of-subset):
| role | austin_311 | cincinnati_311 | dallas_311 | dc_311 | kc_311 | montgomery_traffic | oakland_311 | sandiego_311 | sf_311 |
|---|---|---|---|---|---|---|---|---|---|
| best_error_parity | -0.046 | -0.048 | -0.084 | -0.129 | -0.251 | -0.103 | -0.003 | -0.101 | -0.112 |
| best_late_change_kc_sf | -0.040 | -0.039 | -0.020 | -0.098 | -0.333 | -0.097 | 0.003 | -0.053 | -0.084 |
| highest_synergy | 0.342 | 0.198 | 0.185 | 0.504 | 1.070 | 0.402 | 0.268 | 0.520 | 0.307 |
| lowest_cost | -0.037 | -0.024 | -0.156 | -0.079 | -0.311 | -0.187 | 0.103 | -0.231 | -0.082 |
| strongest_downside_cvar95 | 0.000 | 0.000 | 0.000 | -0.012 | 0.001 | 0.001 | 0.000 | -0.008 | 0.000 |

## All 40 (out-of-subset), full columns
see `tables/phase3_summary.csv`.
