#!/bin/sh
set -e
VAL="V_late_600,W_late_1000,V_better_a,V_better_b,V_better_c,V_near,V_reversal_1000,W_reversal_700,V_recurrent,V_bursty,V_dep_better_r5"
H="gated_deployment,discern_style,SMCS+retain-incumbent,model_picker_adapter,cams_adapter"
R="rmm:gated_deployment+RMM,rmm:discern_style+RMM,rmm:SMCS+retain-incumbent+RMM,rmm:model_picker_adapter+RMM,rmm:cams_adapter+RMM"
ABL="rmm:gated_deployment+RMM_single,rmm:discern_style+RMM_single,rmm:SMCS+retain-incumbent+RMM_single,rmm:gated_deployment+RMM_noacq,rmm:discern_style+RMM_noacq"
S="gated_adaptive_range,gated_adaptive_range+front,gated_deployment+QCE+front,xu_acquisition_only,discern_design_floor,choe_ramdas_eb+front,P7s_settled,A5b,rmm:LRMD,CONTROL_never_switch"
uv run python scripts/sota_sprint/screen.py --regimes $VAL --policies $H,$R,$ABL,$S --seeds 100 --seed-base 2026110606 --workers 9 --out outputs/sota_sprint/rmm_transfer/synth
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r8,W_null_dep_r95 --policies $H,$R,CONTROL_never_switch --seeds 1000 --seed-base 2026110607 --workers 9 --out outputs/sota_sprint/rmm_transfer/null1000
# Amendment 4: deploy-gate transfer across three hosts
VALALL="V_better_a,V_better_b,V_better_c,V_dep_better_r5,V_near,V_bursty,V_null,V_worse,V_null_dep_r5,V_null_dep_r8,V_late_600,V_reversal_1000,V_recurrent,W_better_dep_r7,W_better_dep_r9,W_null_dep_r9,W_null_dep_r95,W_worse_dep_r8,W_late_1000,W_reversal_700,W_delay600_better"
CERT="gated_deployment,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,SMCS+retain-incumbent,xu_acquisition_only,choe_ramdas_eb,choe_ramdas_eb+front,gated_deployment+QCE,gated_deployment+QCE+front"
G="D1,D2,D6-D1params:ms,model_picker_adapter,cams_adapter,model_selector_causal,CONTROL_never_switch"
uv run python scripts/sota_sprint/screen.py --regimes $VALALL --policies $G,$CERT --seeds 100 --seed-base 2026110608 --workers 9 --out outputs/sota_sprint/gate_transfer/synth
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r5,V_null_dep_r8 --policies D1,D2,D6-D1params:ms,CONTROL_never_switch --seeds 1000 --seed-base 2026110609 --workers 9 --out outputs/sota_sprint/gate_transfer/null1000
uv run python scripts/sota_sprint/screen.py --kind real --regimes metro,beijing_pm25,bike_hour,appliances,household_power --policies $G,$CERT --seeds 20 --seed-base 2026110610 --workers 9 --out outputs/sota_sprint/gate_transfer/real_fresh
