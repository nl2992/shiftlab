#!/bin/sh
set -e
VAL="V_better_a,V_better_b,V_better_c,V_dep_better_r5,V_near,V_bursty,V_null,V_worse,V_null_dep_r5,V_null_dep_r8,V_late_600,V_reversal_1000,V_recurrent,W_better_dep_r7,W_better_dep_r9,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8,W_late_1000,W_reversal_700,W_delay600_better"
CERT="gated_deployment,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,SMCS+retain-incumbent,xu_acquisition_only,choe_ramdas_eb,choe_ramdas_eb+front"
CAND="A5b,A1b,X_A5C,B2,rmm:gated_deployment+RMM,C2,C6,gated_adaptive_range+pace_tuned,D1,D2"
UNC="model_picker_adapter,model_selector_causal,online_llm_picker,cams_adapter,variance_min_ipw,gong_zhang_paid_obs,qiu_delayed_movement,ryabchenko_capacity"
INT="QSG,QSG-env8,P7s_settled,CONTROL_never_switch,economic_replacement"
uv run python scripts/sota_sprint/screen.py --regimes $VAL --policies $CAND,$CERT,$UNC,$INT --seeds 100 --seed-base 2026110601 --workers 9 --out outputs/sota_sprint/validation/synth
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8 --policies $CAND,$CERT,QSG,CONTROL_never_switch --seeds 1000 --seed-base 2026110602 --workers 9 --out outputs/sota_sprint/validation/null1000
# Amendment 1: B5 (second Family B candidate)
uv run python scripts/sota_sprint/screen.py --regimes $VAL --policies B5,B2,rmm:gated_deployment+RMM,CONTROL_never_switch --seeds 100 --seed-base 2026110601 --workers 9 --out outputs/sota_sprint/validation/synth_b5
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8 --policies B5,CONTROL_never_switch --seeds 1000 --seed-base 2026110602 --workers 9 --out outputs/sota_sprint/validation/null1000_b5
# Real data: fresh external validation (registered aeb2d4f) and exposed streams (descriptive)
POLR="A5b,A1b,X_A5C,B2,B5,rmm:gated_deployment+RMM,C2,C6,gated_adaptive_range+pace_tuned,D1,D2,$CERT,$UNC,QSG,P7s_settled,CONTROL_never_switch,economic_replacement"
uv run python scripts/sota_sprint/screen.py --kind real --regimes metro,beijing_pm25,bike_hour,appliances,household_power --policies $POLR --seeds 20 --seed-base 2026110604 --workers 9 --out outputs/sota_sprint/validation/real_fresh
uv run python scripts/sota_sprint/screen.py --kind real --regimes rialto,spam,weather,openml_ldpa,uci_occupancy,airlines,bank,elec2,criteo --policies $POLR --seeds 10 --seed-base 2026110603 --workers 9 --out outputs/sota_sprint/validation/real_exposed
# Amendment 2: supplemental comparators (same seeds) and out-of-class nulls
uv run python scripts/sota_sprint/screen.py --regimes $VAL --policies gated_deployment+QCE,gated_deployment+QCE+front,CONTROL_never_switch --seeds 100 --seed-base 2026110601 --workers 9 --out outputs/sota_sprint/validation/synth_qce
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8 --policies gated_deployment+QCE,gated_deployment+QCE+front,CONTROL_never_switch --seeds 1000 --seed-base 2026110602 --workers 9 --out outputs/sota_sprint/validation/null1000_qce
uv run python scripts/sota_sprint/screen.py --regimes O_null_semimarkov,O_null_order2 --policies A5b,A1b,X_A5C,B2,B5,C2,C6,D1,D2,$CERT,gated_deployment+QCE,gated_deployment+QCE+front,QSG,CONTROL_never_switch --seeds 1000 --seed-base 2026110605 --workers 9 --out outputs/sota_sprint/validation/ooc1000
