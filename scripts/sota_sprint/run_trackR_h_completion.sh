#!/bin/sh
set -eu
REG=F0_null,F0_worse,F5_dep_null_r8,F5_dep_null_r95,F0_better,F7_near_better,F9_bursty_better,F1_late_800,F5_dep_better_r8,S_dep_better_r95
POL=H1,H3,D2,A5b
for spec in 2026110701:dev 2026110711:eval; do
  BASE=${spec%%:*}
  LABEL=${spec#*:}
  for A in 0.005 0.01 0.02 0.05 0.1 0.2 0.3 0.5; do
    OUT=outputs/sprint2/H/trackR_remaining/${LABEL}_a${A}
    if [ ! -f "$OUT/manifest.json" ]; then
      uv run python scripts/sota_sprint/screen.py --regimes "$REG" --policies "$POL" --seeds 20 --seed-base "$BASE" --workers 2 --alpha "$A" --out "$OUT"
    fi
  done
done
uv run python scripts/sota_sprint/risk_curves.py \
  --dev outputs/sprint2/H/trackR_remaining/dev_a0.005 outputs/sprint2/H/trackR_remaining/dev_a0.01 outputs/sprint2/H/trackR_remaining/dev_a0.02 outputs/sprint2/H/trackR_remaining/dev_a0.05 outputs/sprint2/H/trackR_remaining/dev_a0.1 outputs/sprint2/H/trackR_remaining/dev_a0.2 outputs/sprint2/H/trackR_remaining/dev_a0.3 outputs/sprint2/H/trackR_remaining/dev_a0.5 \
  --eval outputs/sprint2/H/trackR_remaining/eval_a0.005 outputs/sprint2/H/trackR_remaining/eval_a0.01 outputs/sprint2/H/trackR_remaining/eval_a0.02 outputs/sprint2/H/trackR_remaining/eval_a0.05 outputs/sprint2/H/trackR_remaining/eval_a0.1 outputs/sprint2/H/trackR_remaining/eval_a0.2 outputs/sprint2/H/trackR_remaining/eval_a0.3 outputs/sprint2/H/trackR_remaining/eval_a0.5 \
  --out docs/sprint2/family_h/track_R_remaining.json
