#!/bin/sh
# P2 exchangeable-twin known-null real runs (docs/sota_sprint/p2_known_null_protocol.md)
set -e
P="gated_deployment,gated_adaptive_range,gated_adaptive_range+front,discern_style,discern_design_floor,SMCS+retain-incumbent,xu_acquisition_only,choe_ramdas_eb,choe_ramdas_eb+front,gated_deployment+QCE,gated_deployment+QCE+front,A5b,A1b,rmm:gated_deployment+RMM,rmm:discern_style+RMM,rmm:SMCS+retain-incumbent+RMM,rmm:gated_adaptive_range+RMM,D1,D2,QSG,model_picker_adapter,cams_adapter,CONTROL_never_switch"
uv run python scripts/sota_sprint/screen.py --kind real --regimes twin_metro,twin_beijing_pm25,twin_bike_hour,twin_appliances,twin_household_power --policies $P --seeds 3 --seed-base 2026110620 --workers 9 --out outputs/sota_sprint/twin_null
