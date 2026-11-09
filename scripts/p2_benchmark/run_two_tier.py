"""Run ``scripts/sota_sprint/screen.py`` with the two-tier N_* regimes registered.

Workers are forked so they inherit the extra regimes. Arguments pass through to screen.py:

    PYTHONPATH=scripts/promising_directions/sota uv run python scripts/p2_benchmark/run_two_tier.py \
        --regimes N_better_a,... --policies ... --seeds 200 --seed-base 2026110681 --out OUT
"""

from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "scripts/sota_sprint", ROOT / "scripts/p2_benchmark"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

if __name__ == "__main__":
    mp.set_start_method("fork", force=True)
    import screen
    import two_tier_regimes  # noqa: F401  (registers N_* regimes)

    screen.main(sys.argv[1:])
