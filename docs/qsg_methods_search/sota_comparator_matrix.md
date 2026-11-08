# SOTA comparator matrix (Action 2)

Implementations are adapters on the shared simulator, not author-native reproductions, unless
stated otherwise. The "strongest fair comparator" is the strongest variant that gets the same
information, budget and cost accounting. Numbers are from the D0 panel (50 seeds) unless stated.

| Mech. | Implementation | Source | Failure under the contract | Strongest fair comparator for a repair |
|---|---|---|---|---|
| M1 latency | `gated_deployment`, `gated_adaptive_range(+front)` (`strong_hosts.py`) | Karampatziakis et al. 2021; MOPE (author repo pinned at `a4b8584`; parity unchecked) | uniform pacing under a binding budget; F0_better 427 vs never-switch 418 | `gated_adaptive_range+front` (its range-ordering defect was fixed 2026-11-05 on the codex branch) |
| M1 | `discern_style`, `discern_design_floor(+front)` | Balachandran 2026 (DISCERN) | as above; front-loading *hurts* the design-floor port | `discern_style+QCE+front` (alt mean 382) |
| M1 | `SMCS+retain-incumbent`, `SMCS+QCE+front` | SMCS (T1 parity tests skipped: `vendor_sota/` is empty) | slow promotion; with front-loading, fails the rho=.8 null (.22) | `SMCS+QCE+front` (377) |
| M1 | `xu_acquisition_only(+front)` | Xu et al. acquisition rule plus a ShiftLab certificate | late certification | `xu+front_only` (379; the only front-loaded host that stays safe at rho=.8, .08) |
| M1/M3 | e-SR / RMM / E_rb (other branches) | Shin, Ramdas & Rinaldo 2024 | misses late changes once the budget is exhausted; loses to never-switch on reversal | `esr_rmmbets_fullalpha`, `rmm:LRMD_k1` (methods-strategy branch) |
| M2 churn | `model_picker_adapter`, `model_selector_causal`, `online_llm_picker`, `cams_adapter`, `variance_min_ipw` | Model Picker; Model Selector (AISTATS 2025); Online LLM Picker; CAMS (NeurIPS 2024) | 64–100% null promotion, 5–11 switches | `model_selector_causal` (best in class) |
| M2/M3 | `gong_zhang_paid_obs` (`r6_policies.py`) | Gong–Zhang paid observation (adapted) | null churn (about 7 switches) | **tuned Gong–Zhang**, `gongT_w100_m10` (this work; 16-config grid) |
| M3 | `qiu_delayed_movement` | Qiu et al. delayed movement (adapted) | null churn; slow reversal | `qiu_delayed_movement` |
| M2 | `economic_replacement` (`controls.py`) | horizon-pays rule (Wan et al. 2023; Chick et al. 2017) | no rollback (reversal 411 vs 348) | `econF_mo5_m5` (front-loaded, tuned; this work) |
| M4 | QSG, QSG-env8/95 (`qsg.py`) | ours (Atlas v2) | QSG .26 at rho=.8; the envelope loses power | `xu+front_only` among safe methods; QSG-env8 |
