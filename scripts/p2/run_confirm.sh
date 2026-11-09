#!/usr/bin/env bash
# P2-NAD frozen confirmation (docs/p2/07_CONFIRMATION.md). Resumable: skips finished cohorts.
cd "$(dirname "$0")/../.."
source scripts/p2/env.sh
P="NAD2S-g10-f6,PB80-g10,NAD-m80-g10,A5b,D5,QSG-env8,gated_deployment_native,gated_adaptive_range_native,gated_adaptive_range_native+front,gated_adaptive_range,discern_style,discern_design_floor,SMCS+retain-incumbent,choe_ramdas_eb+front,QSG,D2,economic_replacement,cams_adapter,model_picker_adapter,CONTROL_never_switch"
O=outputs/p2/confirm; mkdir -p $O
go() { local name=$1; shift; grep -q "^done" $O/$name.log 2>/dev/null && return; rm -rf $O/$name; $PY scripts/sota_sprint/wp2_run.py "$@" --policies "$P" --workers 22 --out $O/$name > $O/$name.log 2>&1; }
go salt --sources F0_better,F5_dep_better_r8,S_dep_better_r95,WP2_o2_better,WP2_sm_better,WP2_hs_better --seeds 200 --seed-base 2026110951
C4=../shift-research-starter/data/c4_sealed
SRC=$(ls $C4/*.npz | sed 's|.*/||; s|\.npz||' | while read s; do printf "file:%s/%s.npz:c4_%s," $C4 $s $s; done | sed 's/,$//')
go c4 --sources "$SRC" --seeds 3 --seed-base 2026110952
TW=$(for d in metro beijing_pm25 bike_hour appliances household_power; do printf "twin_%s," $d; done | sed 's/,$//')
go twin --sources "$TW" --seeds 5 --seed-base 2026110953
go snull --sources F0_null,F5_dep_null_r8,F5_dep_null_r95,O_null_semimarkov,O_null_order2,WP2_o2_null,WP2_sm_null,WP2_hs_null --seeds 500 --seed-base 2026110951
echo ALL_DONE > $O/STATUS
