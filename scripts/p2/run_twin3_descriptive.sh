#!/usr/bin/env bash
# Post-registration DESCRIPTIVE validity check on rebuilt twin v3 (docs/p2/_twin_v3_rebuild.md).
# Not part of the registered confirmation; starts after outputs/p2/confirm/STATUS exists.
cd "$(dirname "$0")/../.."
source scripts/p2/env.sh
until [ -f outputs/p2/confirm/STATUS ]; do sleep 60; done
P="NAD2S-g10-f6,NAD-m80-g10,PB80-g10,A5b,gated_deployment_native,gated_adaptive_range_native,gated_adaptive_range_native+front,QSG,SMCS+retain-incumbent,choe_ramdas_eb+front,CONTROL_never_switch"
S=$(for d in metro beijing_pm25 bike_hour appliances household_power; do printf "file:data/sprint_twin_losses_v3/twin3_%s.npz:twin3_%s," $d $d; done | sed 's/,$//')
$PY scripts/sota_sprint/wp2_run.py --sources "$S" --policies "$P" --seeds 1 --seed-base 2026110961 --workers 22 --out outputs/p2/twin3_desc > outputs/p2/twin3_desc.log 2>&1
