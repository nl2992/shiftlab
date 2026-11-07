#!/bin/sh
set -e
REG="V_late_600,W_late_1000,V_better_a,V_better_b,V_better_c,V_near,V_reversal_1000,W_reversal_700,V_recurrent"
H="gated_deployment,discern_style,SMCS+retain-incumbent,gated_adaptive_range"
R="rmm:gated_deployment+RMM,rmm:discern_style+RMM,rmm:SMCS+retain-incumbent+RMM,rmm:gated_adaptive_range+RMM"
C="gated_adaptive_range+front,discern_design_floor,xu_acquisition_only,choe_ramdas_eb,choe_ramdas_eb+front,gated_deployment+QCE,gated_deployment+QCE+front,CONTROL_never_switch"
uv run python scripts/sota_sprint/screen.py --regimes $REG --policies $H,$R,$C --seeds 100 --seed-base 2026110611 --workers 9 --out outputs/sota_sprint/amend5/synth
uv run python scripts/sota_sprint/screen.py --regimes V_null,V_worse,V_null_dep_r8,W_null_dep_r95 --policies $R,CONTROL_never_switch --seeds 1000 --seed-base 2026110612 --workers 9 --out outputs/sota_sprint/amend5/null1000
