#!/bin/sh
# Family-isolated gate re-screen at the committed revision (dev seed base, 20 seeds)
for F in A B C D; do
  uv run python scripts/sota_sprint/screen.py --regimes $(cat outputs/sota_sprint/gate_regimes_$F.txt) --policies $(cat outputs/sota_sprint/gate_policies_$F.txt) --seeds 20 --seed-base 2026110501 --workers 4 --out outputs/sota_sprint/gate/$F
done
