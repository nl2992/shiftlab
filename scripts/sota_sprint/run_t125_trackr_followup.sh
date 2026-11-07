#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

REGIMES="F0_null,F0_worse,F5_dep_null_r8,F5_dep_null_r95,F0_better,F7_near_better,F9_bursty_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95"
POLICIES="T:mp/a5b,T:mp/a5b+ad,T:mp/a5b+ad+rb,model_picker_adapter,D1,D6:mp,D2,A5b,T2:gated/a5b,T2:gated/a5b+front,T2:gated/env8,T2:gated/env8+front,gated_deployment,gated_adaptive_range+front,T:ms/a5b,model_selector_causal,T:cams/a5b"
ALPHAS=(0.005 0.01 0.02 0.05 0.1 0.2 0.3 0.5)

for split in dev eval; do
  if [[ "$split" == dev ]]; then
    seed_base=2026111201
  else
    seed_base=2026111211
  fi
  for alpha in "${ALPHAS[@]}"; do
    out="outputs/sprint2/T/T125_trackR/${split}_a${alpha}"
    if [[ -e "$out" ]]; then
      echo "Refusing to overwrite existing run: $out" >&2
      exit 2
    fi
    uv run python scripts/sota_sprint/screen.py \
      --workers 4 \
      --regimes "$REGIMES" \
      --policies "$POLICIES" \
      --seeds 20 \
      --seed-base "$seed_base" \
      --alpha "$alpha" \
      --out "$out"
  done
done
