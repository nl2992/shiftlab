# Adaptive gated-range replay impact inventory

Generated from saved `manifest.json` files under `outputs/`. The inventory is a replay schedule, not a claim that every affected result changes.

The bug fixed in the shared `GatedAdaptiveRange` hook selected/updated the bet range after the current query draw or flush. Direct adaptive-range, `+front`, and wrapper rows require corrected same-seed replay. The semantic alias scan includes M_RMMSUI_gar, T2 gated-host transfers, T6 gated-controller transfers, and fam_c GatedC variants (C1/C2/C5/C6), whose old query range was stored after the query coin.

- Execution manifests with an affected policy: **130**
- Aggregate manifests affected through their constituents: **6**
- Direct adaptive-range policy entries: **87**
- `+front` policy entries: **102**
- Hidden host-alias policy entries: **222**
- Total affected policy entries requiring replay (including aliases): **411**
- Record directories without manifests that contain affected policies: **2**
- Historical record-only directories needing provenance recovery: **1**
- Corrected replay manifests already produced: **2**
- See `outputs/sprint2/adaptive_gate_impact.json` for paths, seeds, job counts, and policy names.

| Run | Seeds | Seed base | Jobs | Affected policies |
|---|---:|---:|---:|---|
| `outputs/sota_sprint/A/screen1` | 20 | 2026110501 | 220 | gated_adaptive_range+front, gated_adaptive_range |
| `outputs/sota_sprint/B/baseline` | 20 | 2026110501 | 100 | gated_adaptive_range+front, gated_adaptive_range |
| `outputs/sota_sprint/B/screen1` | 20 | 2026110501 | 240 | gated_adaptive_range+front, gated_adaptive_range |
| `outputs/sota_sprint/C/comparators` | 20 | 2026110501 | 200 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/C/heldout_check` | 20 | 2026110513 | 200 | C2, C6, gated_adaptive_range+front, gated_adaptive_range+pace_tuned |
| `outputs/sota_sprint/C/null300` | 300 | 2026110513 | 600 | C2, C5, C6, gated_adaptive_range+front |
| `outputs/sota_sprint/C/screen1` | 20 | 2026110501 | 200 | C1, C2, C5, C6, gated_adaptive_range+pace_tuned, C1-uniformbase, C2-noadapt, C2-floorskip, C6-no_deadline, C6-no_shadow, C6-no_two_stage |
| `outputs/sota_sprint/C/smoke` | 4 | 2026110501 | 12 | gated_adaptive_range, gated_adaptive_range+front, Cchk:gated_uniform, Cchk:gated_front, C1, C2, C5, C6 |
| `outputs/sota_sprint/C/tune` | 20 | 2026110501 | 200 | gated_adaptive_range+pace_k1.5, gated_adaptive_range+pace_k2, gated_adaptive_range+pace_k3, gated_adaptive_range+pace_k4, gated_adaptive_range+pace_k6, gated_adaptive_range+frontfrac0.25, gated_adaptive_range+frontfrac0.5, gated_adaptive_range+frontfrac0.75, C1-k1, C1-k1.5, C1-k2, C1-k3, C1-k4, C2-g0z0.25, C2-g0z0.5, C2-g0z1, C2-g1z0.25, C2-g1z0.5, C2-g1z1, C2-g2z0.25, C2-g2z0.5, C2-g2z1, C6-f0.5, C6-f0.75, C6-f0.9 |
| `outputs/sota_sprint/C/tune2` | 20 | 2026110501 | 200 | C2-g0z0.1, C2-g1z0.1, C2-g2z0.1, C2-g3z0.1, C2-g3z0.25, C2-g3z0.5, C2-g3z1 |
| `outputs/sota_sprint/C/tune3` | 20 | 2026110501 | 200 | C6-f0.5, C6-f0.75, C6-f0.9 |
| `outputs/sota_sprint/D/null300_cert` | 300 | 2026110514 | 300 | gated_adaptive_range+front |
| `outputs/sota_sprint/D/screen1` | 20 | 2026110501 | 180 | gated_adaptive_range+front, gated_adaptive_range |
| `outputs/sota_sprint/M/dev_screen` | 20 | 2026110501 | 180 | M_RMMSUI_gar, rmm:gated_adaptive_range+RMM, gated_adaptive_range |
| `outputs/sota_sprint/X/combo_screen` | 20 | 2026110501 | 160 | gated_adaptive_range+front, gated_adaptive_range |
| `outputs/sota_sprint/amend5/null1000` | 1000 | 2026110612 | 4000 | rmm:gated_adaptive_range+RMM |
| `outputs/sota_sprint/amend5/synth` | 100 | 2026110611 | 900 | gated_adaptive_range, rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sota_sprint/gate/A` | 20 | 2026110501 | 220 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/gate/B` | 20 | 2026110501 | 240 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/gate/C` | 20 | 2026110501 | 200 | C1, C1-k1, C1-k1.5, C1-k2, C1-k3, C1-k4, C1-uniformbase, C2, C2-floorskip, C2-g0z0.1, C2-g0z0.25, C2-g0z0.5, C2-g0z1, C2-g1z0.1, C2-g1z0.25, C2-g1z0.5, C2-g1z1, C2-g2z0.1, C2-g2z0.25, C2-g2z0.5, C2-g2z1, C2-g3z0.1, C2-g3z0.25, C2-g3z0.5, C2-g3z1, C2-noadapt, C5, C6, C6-f0.5, C6-f0.75, C6-f0.9, C6-no_deadline, C6-no_shadow, C6-no_two_stage, Cchk:gated_front, Cchk:gated_uniform, gated_adaptive_range, gated_adaptive_range+front, gated_adaptive_range+frontfrac0.25, gated_adaptive_range+frontfrac0.5, gated_adaptive_range+frontfrac0.75, gated_adaptive_range+pace_k1.5, gated_adaptive_range+pace_k2, gated_adaptive_range+pace_k3, gated_adaptive_range+pace_k4, gated_adaptive_range+pace_k6, gated_adaptive_range+pace_tuned |
| `outputs/sota_sprint/gate/D` | 20 | 2026110501 | 180 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/gate_transfer/real_fresh` | 20 | 2026110610 | 1240 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/gate_transfer/synth` | 100 | 2026110608 | 2100 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/merge/null1000` | 1000 | 2026110631 | 6000 | M_RMMSUI_gar |
| `outputs/sota_sprint/merge/real_fresh` | 20 | 2026110633 | 1240 | M_RMMSUI_gar, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/merge/synth` | 100 | 2026110630 | 900 | M_RMMSUI_gar, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/merge/twin_null` | 3 | 2026110632 | 3720 | M_RMMSUI_gar |
| `outputs/sota_sprint/rmm_transfer/synth` | 100 | 2026110606 | 1100 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/smoke` | 6 | 2026110501 | 18 | gated_adaptive_range |
| `outputs/sota_sprint/twin_null` | 3 | 2026110620 | 3720 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sota_sprint/validation/null1000` | 1000 | 2026110602 | 7000 | C2, C6, gated_adaptive_range+pace_tuned, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/validation/ooc1000` | 1000 | 2026110605 | 2000 | C2, C6, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/validation/real_exposed` | 10 | 2026110603 | 1680 | C2, C6, gated_adaptive_range+pace_tuned, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/validation/real_fresh` | 20 | 2026110604 | 1240 | C2, C6, gated_adaptive_range+pace_tuned, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sota_sprint/validation/synth` | 100 | 2026110601 | 2100 | C2, C6, gated_adaptive_range+pace_tuned, gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sprint2/H/real_fresh` | 3 | 2026110701 | 186 | gated_adaptive_range+front |
| `outputs/sprint2/H/screen1c` | 20 | 2026110701 | 240 | gated_adaptive_range+front |
| `outputs/sprint2/P/dev_real` | 1 | 2026110701 | 62 | gated_adaptive_range+front |
| `outputs/sprint2/P/dev_syn` | 20 | 2026110701 | 460 | gated_adaptive_range+front |
| `outputs/sprint2/P/smoke` | 2 | 2026110501 | 4 | gated_adaptive_range |
| `outputs/sprint2/R/dev_screen_a05` | 20 | 2026110701 | 220 | gated_adaptive_range+front, C6 |
| `outputs/sprint2/R/real/fresh` | 3 | 2026110701 | 330 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.005` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.01` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.02` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.1` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.2` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.3` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/dev_a0.5` | 20 | 2026110701 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.005` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.01` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.02` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.05` | 20 | 2026110711 | 220 | gated_adaptive_range+front, C6 |
| `outputs/sprint2/R/trackR/eval_a0.1` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.2` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.3` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR/eval_a0.5` | 20 | 2026110711 | 220 | gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.005` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.01` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.02` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.05` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.1` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.2` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.3` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/eval_a0.5` | 20 | 2026111311 | 200 | C6, gated_adaptive_range+front |
| `outputs/sprint2/R/trackR_coverage_followup/smoke_a005` | 1 | 2026111311 | 10 | C6, gated_adaptive_range+front |
| `outputs/sprint2/T/R_dev_a0.005` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_dev_a0.01` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_dev_a0.02` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_dev_a0.1` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_dev_a0.2` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_dev_a0.3` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_dev_a0.5` | 20 | 2026110701 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.005` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.01` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.02` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.05` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.1` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.2` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.3` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/R_eval_a0.5` | 20 | 2026110711 | 200 | T6:a5bxC2, C2 |
| `outputs/sprint2/T/T125_trackR/dev_a0.005` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.01` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.02` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.05` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.1` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.2` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.3` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/dev_a0.5` | 20 | 2026111201 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.005` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.01` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.02` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.05` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.1` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.2` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.3` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/T125_trackR/eval_a0.5` | 20 | 2026111211 | 200 | T2:gated/a5b, T2:gated/a5b+front, T2:gated/env8, T2:gated/env8+front, gated_adaptive_range+front |
| `outputs/sprint2/T/devB` | 20 | 2026110701 | 240 | T2:gated/a5b, T2:gated/a5b+front, T2:gatedAND/a5b+front, T2:gated/env8, T2:gated/env8+front, T2:gatedAND/env8+front, T2:gated/qsg+front, T6:a5bxC2, T6:a5bxC6, T6:env8xC2, T6:env8xC6, gated_adaptive_range, gated_adaptive_range+front, C2, C6 |
| `outputs/sprint2/T/real_fresh` | 3 | 2026110701 | 186 | T2:gated/a5b, T2:gated/a5b+front, T6:a5bxC2, gated_adaptive_range+front |
| `outputs/sprint2/T/real_twin` | 1 | 2026110701 | 1240 | T2:gated/a5b, T6:a5bxC2 |
| `outputs/sprint2/WP1/primary` | 3 | 2026110803 | 1044 | rmm:gated_adaptive_range+RMM, gated_adaptive_range, gated_adaptive_range+front, E_rb:gated_adaptive_range, E_srr:gated_adaptive_range, E_srr_noacq:gated_adaptive_range, E_glr:gated_adaptive_range |
| `outputs/sprint2/WP1/screen_dev` | 20 | 2026110701 | 180 | E_rb:gated_adaptive_range, rmm:gated_adaptive_range+RMM, gated_adaptive_range, E_srr:gated_adaptive_range, E_glr:gated_adaptive_range, gated_adaptive_range+front, E_rb:gated_adaptive_range-nogate, E_srr_noacq:gated_adaptive_range |
| `outputs/sprint2/WP1/sens_B100` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_B400` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_cs10` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_cs2` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_delay0.5` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_delay1` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_delay2` | 3 | 2026110803 | 78 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/sens_fullpanel_B100` (aggregate: outputs/sprint2/WP1/sens_B100, outputs/sprint2/WP1/sens_more_B100, outputs/sprint2/WP1/sens_strict_B100) | 3 | 2026110803 | 1092 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP1/sens_fullpanel_B400` (aggregate: outputs/sprint2/WP1/sens_B400, outputs/sprint2/WP1/sens_more_B400, outputs/sprint2/WP1/sens_strict_B400) | 3 | 2026110803 | 1092 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP1/sens_fullpanel_cs10` (aggregate: outputs/sprint2/WP1/sens_cs10, outputs/sprint2/WP1/sens_more_cs10, outputs/sprint2/WP1/sens_strict_cs10) | 3 | 2026110803 | 1092 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP1/sens_fullpanel_cs2` (aggregate: outputs/sprint2/WP1/sens_cs2, outputs/sprint2/WP1/sens_more_cs2, outputs/sprint2/WP1/sens_strict_cs2) | 3 | 2026110803 | 1092 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP1/sens_fullpanel_delay0.5` (aggregate: outputs/sprint2/WP1/sens_delay0.5, outputs/sprint2/WP1/sens_more_delay0.5, outputs/sprint2/WP1/sens_strict_delay0.5) | 3 | 2026110803 | 1092 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP1/sens_fullpanel_delay2` (aggregate: outputs/sprint2/WP1/sens_delay2, outputs/sprint2/WP1/sens_more_delay2, outputs/sprint2/WP1/sens_strict_delay2) | 3 | 2026110803 | 1092 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP1/sens_more_B100` | 3 | 2026110803 | 78 | gated_adaptive_range |
| `outputs/sprint2/WP1/sens_more_B400` | 3 | 2026110803 | 78 | gated_adaptive_range |
| `outputs/sprint2/WP1/sens_more_cs10` | 3 | 2026110803 | 78 | gated_adaptive_range |
| `outputs/sprint2/WP1/sens_more_cs2` | 3 | 2026110803 | 78 | gated_adaptive_range |
| `outputs/sprint2/WP1/sens_more_delay0.5` | 3 | 2026110803 | 78 | gated_adaptive_range |
| `outputs/sprint2/WP1/sens_more_delay2` | 3 | 2026110803 | 78 | gated_adaptive_range |
| `outputs/sprint2/WP1/syn_budget` | 20 | 2026110701 | 240 | rmm:gated_adaptive_range+RMM, gated_adaptive_range+front |
| `outputs/sprint2/WP1/twin` | 3 | 2026110803 | 372 | rmm:gated_adaptive_range+RMM, E_rb:gated_adaptive_range, E_srr:gated_adaptive_range |
| `outputs/sprint2/WP2/run1_twin2` | 1 | 2026110701 | 1240 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP2/run3_synth` | 50 | 2026110701 | 950 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/WP2/run4_fresh` | 3 | 2026110701 | 186 | gated_adaptive_range, gated_adaptive_range+front, rmm:gated_adaptive_range+RMM |
| `outputs/sprint2/round5/H2_followup100` | 100 | 2026110801 | 900 | gated_adaptive_range+front |
| `outputs/sprint2/round5/H2_real14_3seed` | 3 | 2026110803 | 690 | gated_adaptive_range+front |
| `outputs/sprint2/round5/H_corrected_real_20` | 20 | 2026110701 | 1240 | gated_adaptive_range, gated_adaptive_range+front |
| `outputs/sprint2/round5/P6_corrected_comparators_100` | 100 | 2026110815 | 700 | gated_adaptive_range+front |
| `outputs/sprint2/round5/R5_all14_real20` | 20 | 2026110903 | 4600 | gated_adaptive_range+front |
| `outputs/sprint2/round5/R5_all14_real20_smoke` | 1 | 2026110988 | 1 | gated_adaptive_range+front |
| `outputs/sprint2/round5/R5_eval100_a002` | 100 | 2026110901 | 1000 | gated_adaptive_range+front |
| `outputs/sprint2/round5/p6_all14_real20` | 20 | 2026110902 | 4600 | gated_adaptive_range+front |
| `outputs/sprint2/round5/p6_all14_real20_smoke` | 1 | 2026110999 | 16 | gated_adaptive_range+front |
| `outputs/sprint2/round5/wp1_erb_reversal_postdev100` | 100 | 2026110811 | 300 | E_rb:gated_adaptive_range, rmm:gated_adaptive_range+RMM |

## Record directories without a run manifest

These directories require provenance reconstruction before a corrected replay can be tied to exact original arguments. `wmaxfix` paths are corrected runs, not pre-fix source runs.

| Run | Records | State hint | Policies |
|---|---:|---|---|
| `outputs/sota_sprint/validation/null1000_wmaxfix_20261105` | 9795 | corrected-output-partial-or-complete | gated_adaptive_range, gated_adaptive_range+front, gated_adaptive_range+pace_tuned |
| `outputs/sprint2/H/screen1` | 962 | historical-output-needs-run-provenance | gated_adaptive_range+front |

## Corrected replay manifests already produced

These are outputs of the corrected runner and are excluded from the historical replay schedule.

| Run | Jobs | Policies |
|---|---:|---|
| `outputs/failure_atlas_v2/validation_real_wmaxfix_20261105` | 1680 |  |
| `outputs/failure_atlas_v2/validation_synth_wmaxfix_20261105` | 1300 |  |
