#!/usr/bin/env bash
# Phase-2 neighbourhood sweep (dev seeds 2026110911, 30 seeds): delay, budget, switching and label price.
cd "$(dirname "$0")/../.."
source scripts/p2/env.sh
P="CONTROL_never_switch,QSG,A5b,QSG-env8,gated_adaptive_range,gated_adaptive_range+front,discern_design_floor,SMCS+retain-incumbent,NAD-m80-g10,NAD-m80-g5,NAD-m80-g20,PB80-g10"
NULLS="F0_null,F5_dep_null_r8,F5_dep_null_r95,WP2_o2_null,WP2_hs_null"
ALTS="F0_better,F5_dep_better_r8,S_dep_better_r95,WP2_o2_better,WP2_sm_better,WP2_hs_better"
run() { # name, sources, extra args, env
  local out=outputs/p2/neigh/$1; shift; local src=$1; shift
  [ -s $out/records.jsonl ] && return
  env "$@" $PY scripts/sota_sprint/wp2_run.py --sources $src --policies "$P" --seeds 30 --seed-base 2026110911 --workers 22 --out $out ${ARGS} > $out.log 2>&1
}
mkdir -p outputs/p2/neigh
for dm in 0.25 4; do ARGS="--delay-mult $dm" run delay$dm "$NULLS,$ALTS" X=1; done
ARGS="" run base "$NULLS,$ALTS" X=1
for b in 100 400; do S=$(echo "$NULLS,$ALTS" | sed "s/,/@B$b,/g; s/\$/@B$b/"); ARGS="" run budget$b "$S" X=1; done
for cs in 1 20; do ARGS="" run cs$cs "$NULLS,$ALTS" P2_CS=$cs; done
ARGS="" run cq0.2 "$NULLS,$ALTS" P2_CQ=0.2
echo done
