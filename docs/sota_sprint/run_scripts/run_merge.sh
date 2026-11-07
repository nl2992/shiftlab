#!/bin/sh
# Amendment 6: P1 x P2 merge confirmatory runs
set -e
M="M_LRMD_SUI,M_RMMSUI_A5b,M_RMMSUI_gar"
CERT="gated_deployment,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,SMCS+retain-incumbent,xu_acquisition_only,choe_ramdas_eb,choe_ramdas_eb+front,gated_deployment+QCE,gated_deployment+QCE+front"
uv run python scripts/sota_sprint/screen.py --regimes V_late_600,W_late_1000,V_better_a,V_better_b,V_better_c,V_near,V_reversal_1000,W_reversal_700,V_recurrent --policies $M,A5b,rmm:gated_deployment+RMM,$CERT,CONTROL_never_switch --seeds 100 --seed-base 2026110630 --workers 9 --out outputs/sota_sprint/merge/synth
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8,W_null_dep_r9,W_null_dep_r95 --policies $M,A5b,CONTROL_never_switch --seeds 1000 --seed-base 2026110631 --workers 9 --out outputs/sota_sprint/merge/null1000
uv run python scripts/sota_sprint/screen.py --kind real --regimes twin_metro,twin_beijing_pm25,twin_bike_hour,twin_appliances,twin_household_power --policies $M,A5b,xu_acquisition_only,CONTROL_never_switch --seeds 3 --seed-base 2026110632 --workers 9 --out outputs/sota_sprint/merge/twin_null
uv run python scripts/sota_sprint/screen.py --kind real --regimes metro,beijing_pm25,bike_hour,appliances,household_power --policies $M,A5b,rmm:gated_deployment+RMM,$CERT,model_picker_adapter,model_selector_causal,online_llm_picker,cams_adapter,variance_min_ipw,gong_zhang_paid_obs,qiu_delayed_movement,ryabchenko_capacity,CONTROL_never_switch --seeds 20 --seed-base 2026110633 --workers 9 --out outputs/sota_sprint/merge/real_fresh
