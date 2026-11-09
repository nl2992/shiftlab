# 18 — EQSDp + late-label cutoff vs the full comparator panel, held-out odd episodes

Written 2026-11-08 at the user's prompt ("barriers too high?"). Descriptive analysis of existing records; no new runs.

- **Policy:** `s2armr_H1100` = EQSDp arm R (λ.98 γ.3) + hard label cutoff H=1100 (no purchase if t+delay > T−H). Selected on **even** episodes (Stage 2 step 1, doc 13) and frozen before odd episodes were opened (freeze 167f5ae8).
- **Held-out data:** odd episodes of the nine datasets. Records: Stage 3 run (`outputs/paper1_eqsdp/stage3/run/records.jsonl`) for the policy; SOTA-expansion panel records (`nine`, `nine_armR`, `batch2`) for comparators. Same seeds; Stage 3 reproduces panel arm R exactly.
- **Statistic:** equal-dataset mean of per-dataset paired ΔJ (policy − comparator), seed-mean per episode; 95% stratified episode-bootstrap CI (2,000, rng 0).

| comparator | class | ΔJ | % | 95% CI | datasets better |
|---|---|---|---|---|---|
| qiu_delayed_movement | adapter | −13.09 | −2.70 | [−14.72, −11.25] | 9/9 |
| gong_zhang_paid_obs | adapter | −11.35 | −2.35 | [−13.07, −9.48] | 9/9 |
| gongT_w100_m10 | adapter | −12.91 | −2.66 | [−14.99, −10.56] | 9/9 |
| gongT_w800_m20 | adapter | −6.29 | −1.31 | [−7.32, −4.94] | 9/9 |
| upf_d0.95_m50 | adapter | −20.21 | −4.10 | [−22.67, −18.25] | 9/9 |
| upf_d0.8_m50 | adapter | −18.34 | −3.74 | [−20.60, −16.33] | 9/9 |
| chalgse_l1.0_g0.2 | adapter | −12.76 | −2.63 | [−16.43, −10.16] | 8/9 |
| chalgse_l0.9_g0.3 | adapter | −10.64 | −2.20 | [−13.97, −8.25] | 9/9 |
| cams_adapter | adapter | −14.60 | −3.00 | [−16.19, −13.14] | 9/9 |
| model_selector_causal | adapter | −9.68 | −2.01 | [−11.63, −7.67] | 9/9 |
| model_picker_adapter | adapter | −9.56 | −1.98 | [−11.02, −7.90] | 9/9 |
| online_llm_picker | adapter | −11.45 | −2.37 | [−13.07, −9.56] | 9/9 |
| variance_min_ipw | adapter | −16.09 | −3.29 | [−17.85, −14.26] | 9/9 |
| han_arw_label_clock | adapter | −78.13 | −14.19 | [−80.83, −75.52] | 9/9 |
| wald_l0.9_g0.2 | control | −7.69 | −1.60 | [−9.34, −5.58] | 9/9 |
| wald_l0.97_g0.2 | control | −4.35 | −0.91 | [−5.42, −2.89] | 8/9 |
| hoef_l0.9_g0.45 | control | −5.13 | −1.07 | [−6.44, −3.44] | 8/9 |
| hoef_l0.97_g0.3 | control | −7.45 | −1.55 | [−8.63, −6.14] | 7/9 |
| smarg_l0.9_k0.2 | control | −8.78 | −1.82 | [−10.51, −6.46] | 9/9 |
| smarg_l0.97_k0.2 | control | −4.25 | −0.89 | [−5.21, −2.99] | 9/9 |
| dwell_l0.9_s5 | control | −12.03 | −2.48 | [−13.86, −10.06] | 9/9 |
| dwell_l0.97_s3 | control | −7.29 | −1.52 | [−8.62, −5.62] | 9/9 |
| econF_mo5_m5 | control | −12.88 | −2.65 | [−19.45, −7.57] | 9/9 |
| econF_mo5_m0 | control | −12.84 | −2.65 | [−19.39, −7.75] | 9/9 |
| economic_replacement | control | −16.69 | −3.41 | [−20.46, −13.74] | 9/9 |
| EQSDp arm R (no cutoff) | own | −4.33 | −0.91 | [−5.37, −2.97] | 8/9 |
| EQSDp arm B (no cutoff) | own | −7.15 | −1.49 | [−8.80, −5.13] | 9/9 |

**Result:** superior to all 25 uncertified comparators on held-out episodes (every CI < 0). Against all 14 published-method adapters the gain is 1.3–14.2% (≥ 2% against 11 of 14). Prediction error vs `wald_l0.97_g0.2`: +0.018 pp (doc 14).

**Scope:**
- The comparators are run as specified, without a label cutoff. When the same cutoff is given to Wald (`s2wald_l0.98_g0.3_H1100`), it ties EQSDp + cutoff (doc 17: odd J 472.53 vs 472.42). So the claim is about the *method package*, confidence-bound economic switching plus a deadline-aware label cutoff. It does not say that the Beta quantile beats Wald.
- The datasets are the nine C4-supporting datasets (00_SCOPE). Odd episodes are held out from all tuning, but the datasets themselves were exposed.
