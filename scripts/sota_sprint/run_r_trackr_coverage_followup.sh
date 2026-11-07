#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

REGIMES="F0_null,F0_worse,F5_dep_null_r8,F5_dep_null_r95,F0_better,F7_near_better,F9_bursty_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95"
POLICIES="A5b,C6,CONTROL_never_switch,D2,H1-iid1,H2,R2,R2-floor25,R2-qc,R3-alloc,R3-base,R3-near,R3-plugin,R3-plugnear,R4-both,R4-comb,R5,R6:D2-always,R6:D2-floor25,R:economic_stop,R:xu_acquisition_only@alpha,SMCS+retain-incumbent,choe_ramdas_eb+front,gated_adaptive_range+front,gated_deployment,xu_acquisition_only"
ALPHAS=(0.005 0.01 0.02 0.05 0.1 0.2 0.3 0.5)
SEED_BASE=2026111311

for alpha in "${ALPHAS[@]}"; do
  out="outputs/sprint2/R/trackR_coverage_followup/eval_a${alpha}"
  if [[ -e "$out" ]]; then
    echo "Refusing to overwrite existing run: $out" >&2
    exit 2
  fi
  uv run python scripts/sota_sprint/screen.py \
    --workers 4 \
    --regimes "$REGIMES" \
    --policies "$POLICIES" \
    --seeds 20 \
    --seed-base "$SEED_BASE" \
    --alpha "$alpha" \
    --out "$out"
done
