# 10 - Paper 1 scale-25: C1 confirmation (frozen v1 on a 21-dataset cohort)

**Honest title.** This is the C1 confirmation of the frozen v1 package on **21 eligible datasets**, not a 25-dataset
result. 22 datasets were registered in `07a`; one failed a C4 gate and is reported, not replaced. All numbers below are
produced by `scripts/paper1_scale25/confirm_c1_analyze.py` from `docs/paper1_scale25/confirm_C1_results/`.

## 1. Provenance

- Protocol: `07a_PROTOCOL_C1_V1_22.md` (locked at `607a7eea`, before any confirmation build). Registration:
  `confirm_registration_C1.json` and ledger rows 8-28, committed at `af2d76a9` before any policy ran on these windows.
- Builds: `scripts/paper1_scale25/data/confirm_build.py` (wraps `c4_build.build`, unchanged gates; records only validation
  statistics). Records in `confirm_builds/`; sealed arrays in `data/scale25_confirm/` (gitignored, checksums in the registration).
- Run: `scripts/paper1_scale25/confirm/c1_run.py` via `c1_watch.py` (detached, resumable), seed base 2026111001, 10 policy seeds, all
  episodes, 62 policies per (dataset, episode, seed); code SHA `af2d76a9` (clean). The runner was first smoke-tested to reproduce
  the stored fresh sf_311 records bit-exactly for all 30 stored policies (incl. v1, W+cut, W+pair, 25 panel) on 2 episodes x 3 seeds.
  Record-file hashes: `confirm_C1_results/records_sha256.txt` (the records themselves, 409 MB, are not in Git).
- Analysis: single pass, `confirm_C1_results/summary.json`. Commands:
  `python scripts/paper1_scale25/data/run_confirm_builds.py`, `python scripts/paper1_scale25/confirm/confirm_register.py`,
  `python scripts/paper1_scale25/confirm/c1_watch.py -- --reg docs/paper1_scale25/confirm_registration_C1.json --out outputs/paper1_scale25/c1/run --parts core,panel,cut,ports --workers 18`,
  `python scripts/paper1_scale25/confirm_c1_analyze.py --records-dir outputs/paper1_scale25/c1/run --open-ledger`.

## 2. Eligibility (C4 gates, validation statistics only)

| # | dataset | window | n_after_filter | episodes | delay | val disagreement | val err inc/chal | eligible | ledger idx |
|---|---|---|---|---|---|---|---|---|---|
| 1 | boston_311 | 2025-01-01..2026-01-01 | 185195 | 46 | 100 | 0.146 | 0.137/0.135 | yes | 8 |
| 2 | philly_311 | 2025-07-01..2026-07-01 | 528651 | 100 | 100 | 0.074 | 0.093/0.101 | yes | 9 |
| 3 | sacramento_311 | 2025-01-01..2026-01-01 | 569604 | 100 | 100 | 0.096 | 0.159/0.138 | yes | 10 |
| 4 | baltimore_311 | 2025-01-01..2025-05-01 | 274794 | 68 | 100 | 0.072 | 0.103/0.099 | yes | 11 |
| 5 | louisville_311 | 2025-01-01..2026-07-01 | 283011 | 70 | 100 | 0.042 | 0.159/0.153 | yes | 12 |
| 6 | chicago_311 | 2025-01-01..2026-01-01 | 1960595 | 100 | 100 | 0.097 | 0.128/0.080 | yes | 13 |
| 7 | chicago_traffic_crashes | 2023-01-01..2025-01-01 | 222810 | 55 | 100 | 0.037 | 0.279/0.273 | yes | 14 |
| 8 | bts_ontime | 2025-07-01..2025-09-01 | 1233806 | 100 | 100 | 0.141 | 0.304/0.285 | yes | 15 |
| 9 | dc_311 | 2026-01-01..2026-07-01 | 250354 | 62 | 100 | 0.360 | 0.326/0.167 | yes | 16 |
| 10 | sandiego_311 | 2026-01-01..2026-07-01 | 209412 | 52 | 100 | 0.127 | 0.172/0.158 | yes | 17 |
| 11 | edmonton_311 | 2025-07-01..2026-07-01 | 943713 | 100 | 100 | 0.077 | 0.146/0.114 | yes | 18 |
| 12 | winnipeg_311 | 2025-07-01..2026-07-01 | 843400 | 100 | 100 | 0.058 | 0.137/0.131 | yes | 19 |
| 13 | mc311_montgomery | 2025-07-01..2026-07-01 | 543705 | 100 | 100 | 0.030 | 0.055/0.046 | yes | 20 |
| 14 | calgary_311 | 2025-07-01..2026-07-01 | 494674 | 100 | 100 | 0.150 | 0.224/0.246 | yes | 21 |
| 15 | nyc_ems_response | 2025-07-01..2026-07-01 | 1476690 | 100 | 100 | 0.153 | 0.313/0.313 | yes | 22 |
| 16 | nyc_fire_response | 2025-07-01..2026-07-01 | 493023 | 100 | 100 | 0.110 | 0.297/0.282 | yes | 23 |
| 17 | montgomery_police_dispatch | 2025-07-01..2026-07-01 | 155578 | 38 | 100 | 0.057 | 0.214/0.208 | yes | 24 |
| 18 | divvy_chicago | 2025-07-01..2026-07-01 | 769288 | 100 | 100 | 0.094 | 0.242/0.216 | yes | 25 |
| 19 | capitalbikeshare_dc | 2025-07-01..2026-07-01 | 774868 | 100 | 100 | 0.023 | 0.209/0.207 | NO: failed C4 gate(s): disagreement |  |
| 20 | epa_aqi_county | 2025-07-01..2026-07-01 | 235278 | 58 | 1000 | 0.052 | 0.119/0.112 | yes | 26 |
| 21 | ghcn_us_rain | 2025-07-01..2026-07-01 | 957575 | 100 | 1000 | 0.129 | 0.298/0.273 | yes | 27 |
| 22 | eia930_pooled | 2025-07-01..2026-07-01 | 573586 | 100 | 100 | 0.214 | 0.292/0.245 | yes | 28 |

Ineligible: **capitalbikeshare_dc** (validation disagreement below the .03 gate). It is not repaired or replaced and holds no ledger
index. Notes: `epa_aqi_county` is truncated by publication (last event 2026-05-31) and has delay 1000; `ghcn_us_rain` has delay 1000;
`montgomery_police_dispatch` has 38 episodes (just above the 35 gate).

**Cutoff degeneracy (a protocol consequence, not a tuning choice).** For delay 1000 the frozen cutoff (no purchase when
`t + delay > T - 1100`) is closed for the entire 2000-event episode. On `epa_aqi_county` and `ghcn_us_rain` every cutoff arm buys zero
labels and never switches, so v1 = W+cut exactly (r = 0, L = 0). These two datasets carry no information about the method and enter
the primary mean as zeros, as the protocol fixed.

## 3. Pre-opening development evaluation (07a section 3; descriptive)

Core arms on the DEV windows of the 12 new sources (`c1_dev_eval.csv`, seed base 2026111000): mean r (v1 vs W+cut) = 0.407 %,
8 positive / 2 negative / 2 zero. The matching confirmation results are in the per-dataset table below. No dataset was added, dropped or reordered on this basis.

## 4. Primary result (design A2, one test)

H0: mean r_d <= 0 over the 21 eligible datasets; reference W+cut; r_d = 100 (J_W+cut - J_v1) / J_W+cut.

| quantity | value |
|---|---|
| equal-dataset mean r | **0.362 %** |
| 95% t-CI | [0.228, 0.496] |
| one-sided t-test | t = 5.65, **p = 7.89e-06** (K = 21) |
| sign count | 18 positive, 1 negative, 2 exactly zero |
| mean dJ (pp of T) | -0.0635 |
| mean dL/T (pp) | 0.0165 (constraint <= +0.1: met) |
| verdict by the 07a rule | **passes** |

Organisation-merged sensitivity (pairs {nyc_ems, nyc_fire}, {divvy, capitalbikeshare} [only divvy eligible], {mc311_montgomery, montgomery_police_dispatch} averaged first): K = 19,
mean r = 0.354 % [0.211, 0.498], p = 3.08e-05.

Post-hoc descriptive (not a protocol test): excluding the two degenerate delay-1000 datasets, K = 19, mean r = 0.400 %, t-test p = 3.94e-06.

**Size.** The effect is statistically clear but small: v1 saves 0.36 % of W+cut's net cost on average (about 0.063 pp of T). By the
programme's grading (substantial >= 2 %, meaningful >= 0.5 %, small otherwise) this is **small**. It is far below the 2.5 % per-dataset
target of the scale-25 programme.

## 5. Per-dataset certification (design B, union bound; ledger rows opened)

Ledger validation problems: none.

| counter | value |
|---|---|
| registered (incl. 7 legacy) | 28 |
| legacy reserved | 7 |
| opened (this cohort) | 21 |
| positive point estimate (r_hat > 0) | 18 |
| supported (L > 0) | **0** |
| selected | 0 |

`certify_cohort` (target |S| >= 25, mean L >= 2.5): **success = False**. All-opened mean r_hat = 0.362 %;
cross-dataset t95 interval [0.228, 0.496]; simultaneous lower bound of the all-opened mean: -inf
(some per-dataset L are -inf). As predicted in 09, the registered target is not reachable with K <= 22, and in addition no individual
dataset has a positive union-bound lower bound at alpha_i = .05/(i(i+1)) with i = 8..28. The population-level mean is positive; the
per-dataset effect sizes are too small to certify one by one.

## 6. Secondary contrasts (Holm over the two)

| contrast | K | mean r % | 95% t-CI | p (one-sided) | Holm p | r>0 / r<0 | mean dL pp |
|---|---|---|---|---|---|---|---|
| v1_vs_EQcut | 21 | 0.357 | [0.223, 0.490] | 9.27e-06 | 1.23e-05 | 18 / 1 | 0.016 |
| Wpair_vs_Wcut | 21 | 0.377 | [0.240, 0.513] | 6.15e-06 | 1.23e-05 | 18 / 1 | 0.013 |

W+pair vs W+cut and v1 vs EQ+cut are both positive, and the two pair variants give similar mean r (W+pair minus v1: 0.015 % points; not tested). The cohort result is therefore a property of the E48+F60 add-on, not of a particular parent.

## 7. Per-dataset results (registration order)

| # | idx | dataset | domain | eps | J v1 | J W+cut | r % | dL pp | alpha_i | L % (primary_lower) | labels v1 | labels W+cut | sw v1 | sw W+cut |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8 | boston_311 | municipal-311 | 46 | 14.100 | 14.227 | 0.892 | -0.028 | 6.90e-04 | -2.690 | 54.437 | 76.524 | 1.189 | 1.365 |
| 2 | 9 | philly_311 | municipal-311 | 100 | 13.032 | 13.068 | 0.281 | 0.054 | 5.60e-04 | -inf | 26.885 | 60.236 | 1.135 | 1.166 |
| 3 | 10 | sacramento_311 | municipal-311 | 100 | 20.009 | 20.000 | -0.046 | 0.049 | 4.50e-04 | -1.756 | 66.769 | 79.857 | 1.561 | 1.589 |
| 4 | 11 | baltimore_311 | municipal-311 | 68 | 10.133 | 10.225 | 0.903 | 0.040 | 3.80e-04 | -1.298 | 21.732 | 56.288 | 1.037 | 1.219 |
| 5 | 12 | louisville_311 | municipal-311 | 70 | 16.354 | 16.391 | 0.227 | 0.057 | 3.20e-04 | -1.699 | 12.081 | 36.743 | 0.866 | 0.994 |
| 6 | 13 | chicago_311 | municipal-311 | 100 | 9.462 | 9.523 | 0.639 | 0.040 | 2.70e-04 | -2.514 | 27.894 | 65.353 | 1.122 | 1.151 |
| 7 | 14 | chicago_traffic_crashes | public-safety | 55 | 28.429 | 28.473 | 0.155 | 0.012 | 2.40e-04 | -0.671 | 8.189 | 29.665 | 1.076 | 1.085 |
| 8 | 15 | bts_ontime | transport | 100 | 26.079 | 26.104 | 0.097 | 0.018 | 2.10e-04 | -0.550 | 36.864 | 45.979 | 0.777 | 0.860 |
| 9 | 16 | dc_311 | municipal-311 | 62 | 19.678 | 19.742 | 0.325 | -0.103 | 1.80e-04 | -1.918 | 97.947 | 84.742 | 1.163 | 1.140 |
| 10 | 17 | sandiego_311 | municipal-311 | 52 | 19.056 | 19.094 | 0.196 | 0.085 | 1.60e-04 | -2.235 | 40.554 | 71.983 | 1.308 | 1.483 |
| 11 | 18 | edmonton_311 | municipal-311 | 100 | 11.237 | 11.331 | 0.829 | 0.025 | 1.50e-04 | -0.865 | 16.108 | 43.569 | 0.933 | 1.133 |
| 12 | 19 | winnipeg_311 | municipal-311 | 100 | 14.128 | 14.149 | 0.150 | 0.096 | 1.30e-04 | -2.380 | 11.153 | 39.950 | 0.957 | 1.138 |
| 13 | 20 | mc311_montgomery | municipal-311 | 100 | 6.340 | 6.376 | 0.565 | 0.038 | 1.20e-04 | -2.086 | 11.453 | 28.959 | 0.772 | 0.892 |
| 14 | 21 | calgary_311 | municipal-311 | 100 | 23.047 | 23.095 | 0.208 | 0.072 | 1.10e-04 | -1.695 | 32.218 | 68.467 | 1.237 | 1.354 |
| 15 | 22 | nyc_ems_response | emergency-services | 100 | 31.468 | 31.668 | 0.633 | -0.058 | 1.00e-04 | -0.611 | 41.714 | 75.381 | 1.224 | 1.456 |
| 16 | 23 | nyc_fire_response | emergency-services | 100 | 29.320 | 29.426 | 0.363 | 0.026 | 9.00e-05 | -0.307 | 34.051 | 71.676 | 1.295 | 1.452 |
| 17 | 24 | montgomery_police_dispatch | public-safety | 38 | 20.735 | 20.772 | 0.178 | 0.062 | 8.00e-05 | -2.076 | 14.108 | 37.489 | 0.955 | 1.118 |
| 18 | 25 | divvy_chicago | transport | 100 | 28.636 | 28.795 | 0.553 | -0.098 | 8.00e-05 | -1.670 | 51.842 | 59.728 | 1.123 | 1.290 |
| 20 | 26 | epa_aqi_county | environment | 58 | 20.769 | 20.769 | 0.000 | 0.000 | 7.00e-05 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 21 | 27 | ghcn_us_rain | environment | 100 | 32.154 | 32.154 | 0.000 | 0.000 | 7.00e-05 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 22 | 28 | eia930_pooled | energy | 100 | 24.960 | 25.074 | 0.456 | -0.041 | 6.00e-05 | -0.338 | 62.216 | 80.364 | 1.233 | 1.344 |

Negative r: sacramento_311.

By domain (mean of per-dataset r, v1 vs W+cut):

| domain | K | mean_r | n_pos | mean_dL |
|---|---|---|---|---|
| emergency-services | 2 | 0.498 | 2 | -0.016 |
| energy | 1 | 0.456 | 1 | -0.041 |
| environment | 2 | 0.000 | 0 | 0.000 |
| municipal-311 | 12 | 0.431 | 11 | 0.035 |
| public-safety | 2 | 0.166 | 2 | 0.037 |
| transport | 2 | 0.325 | 2 | -0.040 |

## 8. Descriptive panel comparisons (v1 vs each comparator)

r = 100 (J_comp - J_v1) / J_comp, positive favours v1; pooled over datasets with t-CIs. The >= SOTA rule is the amendment-11 rule (v1 non-inferior
within 1 % of the comparator's cost, episode-bootstrap one-sided 95 %, against every comparator in the set). Raw and cutoff-equipped panels are
reported separately.

**>= SOTA counts (of 21 datasets):** raw 25 comparators: **18**; arm R alone: 19; cutoff-equipped 25 (24 wrapped + unwrapped model_selector_causal): **12**;
both: 11; paper-formula ports raw: 19, with cutoff: 21.
Datasets failing the raw panel: epa_aqi_county, ghcn_us_rain, sacramento_311. Failing the cutoff-equipped panel: baltimore_311, boston_311, calgary_311, dc_311, edmonton_311, eia930_pooled, ghcn_us_rain, sacramento_311, sandiego_311.

### Raw panel (25 + arm R)
| comparator | mean r % (v1 better if >0) | 95% t-CI | r>0 | r<0 |
|---|---|---|---|---|
| econF_mo5_m0 | 0.683 | [-0.245, 1.611] | 18 | 3 |
| econF_mo5_m5 | 0.693 | [-0.230, 1.616] | 18 | 3 |
| wald_l0.97_g0.2 | 1.023 | [0.197, 1.849] | 19 | 2 |
| smarg_l0.97_k0.2 | 1.043 | [0.230, 1.857] | 19 | 2 |
| EQSDp_l0.98_g0.3 | 1.177 | [0.348, 2.006] | 19 | 2 |
| hoef_l0.9_g0.45 | 1.413 | [0.524, 2.302] | 19 | 2 |
| gongT_w800_m20 | 1.597 | [0.770, 2.424] | 20 | 1 |
| chalgse_l0.9_g0.3 | 1.614 | [0.548, 2.679] | 19 | 2 |
| hoef_l0.97_g0.3 | 1.670 | [0.652, 2.687] | 18 | 3 |
| economic_replacement | 1.689 | [0.593, 2.785] | 19 | 2 |
| dwell_l0.97_s3 | 1.887 | [0.928, 2.847] | 20 | 1 |
| wald_l0.9_g0.2 | 1.994 | [1.017, 2.970] | 20 | 1 |
| chalgse_l1.0_g0.2 | 2.313 | [1.122, 3.504] | 19 | 2 |
| smarg_l0.9_k0.2 | 2.413 | [1.360, 3.466] | 20 | 1 |
| upf_d0.8_m50 | 2.587 | [1.359, 3.815] | 20 | 1 |
| upf_d0.95_m50 | 2.690 | [1.368, 4.011] | 20 | 1 |
| model_picker_adapter | 2.788 | [1.585, 3.991] | 19 | 2 |
| model_selector_causal | 2.805 | [1.727, 3.883] | 20 | 1 |
| dwell_l0.9_s5 | 2.828 | [1.679, 3.976] | 20 | 1 |
| gong_zhang_paid_obs | 2.908 | [1.724, 4.092] | 19 | 2 |
| gongT_w100_m10 | 3.252 | [2.314, 4.190] | 21 | 0 |
| online_llm_picker | 3.724 | [2.447, 5.002] | 20 | 1 |
| qiu_delayed_movement | 3.859 | [3.028, 4.689] | 21 | 0 |
| cams_adapter | 3.911 | [2.576, 5.245] | 19 | 2 |
| variance_min_ipw | 4.632 | [3.281, 5.984] | 20 | 1 |
| han_arw_label_clock | 18.680 | [15.532, 21.829] | 21 | 0 |

### Cutoff-equipped panel (H = 1100; model_selector_causal unwrapped)
| comparator | mean r % (v1 better if >0) | 95% t-CI | r>0 | r<0 |
|---|---|---|---|---|
| econF_mo5_m0_H1100 | -0.067 | [-0.500, 0.365] | 6 | 13 |
| econF_mo5_m5_H1100 | -0.057 | [-0.475, 0.361] | 7 | 12 |
| wald_l0.97_g0.2_H1100 | 0.218 | [0.037, 0.399] | 12 | 7 |
| smarg_l0.97_k0.2_H1100 | 0.334 | [0.177, 0.492] | 17 | 2 |
| hoef_l0.9_g0.45_H1100 | 0.430 | [0.139, 0.720] | 13 | 6 |
| wald_l0.9_g0.2_H1100 | 0.661 | [0.392, 0.929] | 17 | 2 |
| gongT_w800_m20_H1100 | 0.706 | [0.380, 1.032] | 16 | 3 |
| dwell_l0.97_s3_H1100 | 0.769 | [0.512, 1.027] | 19 | 0 |
| economic_replacement_H1100 | 0.877 | [0.199, 1.555] | 13 | 6 |
| chalgse_l0.9_g0.3_H1100 | 1.062 | [0.461, 1.663] | 15 | 4 |
| smarg_l0.9_k0.2_H1100 | 1.071 | [0.723, 1.418] | 19 | 0 |
| hoef_l0.97_g0.3_H1100 | 1.083 | [0.491, 1.674] | 15 | 4 |
| dwell_l0.9_s5_H1100 | 1.292 | [0.828, 1.755] | 17 | 2 |
| qiu_delayed_movement_H1100 | 1.482 | [1.034, 1.931] | 19 | 0 |
| chalgse_l1.0_g0.2_H1100 | 1.726 | [0.850, 2.603] | 15 | 4 |
| gongT_w100_m10_H1100 | 1.768 | [1.032, 2.504] | 18 | 1 |
| upf_d0.8_m50_H1100 | 1.772 | [0.743, 2.801] | 16 | 3 |
| gong_zhang_paid_obs_H1100 | 1.774 | [1.308, 2.240] | 19 | 0 |
| model_picker_adapter_H1100 | 1.848 | [1.346, 2.350] | 19 | 0 |
| upf_d0.95_m50_H1100 | 1.858 | [0.715, 3.001] | 16 | 3 |
| cams_adapter_H1100 | 2.467 | [1.865, 3.069] | 19 | 0 |
| online_llm_picker_H1100 | 2.565 | [1.912, 3.218] | 19 | 0 |
| variance_min_ipw_H1100 | 2.575 | [1.959, 3.191] | 19 | 0 |
| model_selector_causal | 2.805 | [1.727, 3.883] | 20 | 1 |
| han_arw_label_clock_H1100 | 15.650 | [12.330, 18.969] | 19 | 0 |

### Paper-formula ports (Model Picker, CAMS), raw and with cutoff
| comparator | mean r % (v1 better if >0) | 95% t-CI | r>0 | r<0 |
|---|---|---|---|---|
| mp_paper_recommend_H1100 | 1.812 | [1.359, 2.266] | 19 | 0 |
| cams_paper_gated_H1100 | 2.360 | [1.769, 2.951] | 19 | 0 |
| mp_paper_recommend | 2.755 | [1.555, 3.954] | 19 | 2 |
| cams_paper_H1100 | 3.011 | [2.307, 3.715] | 19 | 0 |
| cams_paper_gated | 3.753 | [2.418, 5.089] | 19 | 2 |
| cams_paper | 4.665 | [3.249, 6.081] | 20 | 1 |
| mp_paper_sample | 91.682 | [90.114, 93.249] | 21 | 0 |
| mp_paper_sample_H1100 | 92.054 | [90.671, 93.438] | 21 | 0 |

(`mp_paper_sample` acts by sampling the model each step and is cost-infeasible under c_s = 5, as found in 05. `han_arw_label_clock` is a weak adapter.)

**Best-of-panel (OPTIMISTIC: the per-dataset best policy among all 60 panel, control and port policies is chosen after seeing these results).**
v1 vs that reference: mean r = -0.807 % [-1.446, -0.168]; v1 better on 3, worse on 18 datasets. The most frequent best policy is
econF_mo5_m0_H1100 (8 datasets), a cutoff-equipped economic-rule control (`econF_mo5_*_H1100`): v1 does not beat the best cutoff-equipped control.
This is the honest limit on the novelty claim: the cohort win is against the matched cutoff reference W+cut and against nearly all raw adapters, but a tuned economic-rule control
equipped with the same cutoff is as good or slightly better (pooled r vs `econF_mo5_m5_H1100` = -0.057 %, CI includes 0).

## 9. Labels, switches, decomposition

Equal-dataset means per episode (net, loss in cost units per 2000 events):

| policy | net | loss | labels | switches | late_adoption | false_promotion | reversal_churn | label_spend | residual | regret |
|---|---|---|---|---|---|---|---|---|---|---|
| P2_K2__E48_F60 | 399.17 | 392.59 | 31.82 | 1.00 | 14.97 | 1.87 | 1.24 | 1.59 | 3.17 | 22.83 |
| s2wald_l0.98_g0.3_H1100 | 400.44 | 392.26 | 53.00 | 1.11 | 14.68 | 1.86 | 1.60 | 2.65 | 3.31 | 24.09 |
| s2armr_H1100 | 400.42 | 392.26 | 53.00 | 1.10 | 14.69 | 1.86 | 1.58 | 2.65 | 3.31 | 24.08 |
| P4W__P2_K2__E48_F60 | 399.11 | 392.51 | 31.78 | 1.00 | 14.92 | 1.84 | 1.26 | 1.59 | 3.17 | 22.77 |
| EQSDp_l0.98_g0.3 | 402.52 | 388.33 | 151.12 | 1.33 | 10.81 | 1.88 | 2.17 | 7.56 | 3.77 | 26.18 |

v1 buys 31.8 labels per episode against 53.0 for W+cut (40 % fewer) with a similar loss and a slightly lower switch count: the gain
is label spend and reversal churn, not accuracy (mean dL/T = 0.016 pp).

## 10. Caveats

- K = 21, not 22 or 25; two datasets (epa, ghcn) are degenerate by the delay-1000/cutoff interaction; 12 of the 21 are municipal-311 streams (the organisation-merged sensitivity gives a similar mean).
- Per-dataset certification is not achieved on any dataset; the cohort claim is a population-mean claim with t-based inference across datasets (independence across datasets is assumed; same-operator or same-city pairs are addressed only by the merged sensitivity).
- Reference choice: W+cut was locked as primary. Against the best cutoff-equipped control the result is negative (best-of-panel, optimistic).
- The cutoff-equipped panel uses a single H = 1100 for every comparator, not per-family tuned values; `model_selector_causal` is unwrapped; author-code parity (T1) for the ports is not established (05).
- epa_aqi_county window ends 2026-05-31 by publication; baltimore (4 months), bts (2 months), dc and sandiego (half-year) windows are as specified.
- Smoke/dev checks (runner parity, dev evaluation) are not confirmatory; only sections 4-6 are confirmatory evidence.

## 11. Continue / pivot / stop

- **Confirmed (small):** the frozen v1 beats its matched W+cut reference on the pre-registered cohort (mean r = 0.362 %, p = 7.9e-06, 18/21 datasets positive, accuracy constraint met).
- **Not achieved:** the 2.5 % certified-reduction target (0 of 21 datasets with L > 0; cohort certificate false) and superiority over the best cutoff-equipped control.
- **Assessment: pivot the claim, continue the programme.** Report v1 as a small, statistically reliable cost-trimming add-on (label spend), not as a state-of-the-art monitoring result with a certified 2.5 % gain. Further gains need a different lever
  (information source or acquisition) rather than more tuning of this package; the ceiling visible in the best-of-panel table is the economic-rule family with a cutoff.
