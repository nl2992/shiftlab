"""Build the H8 twin v4 cohort (splits 160..279), registered in docs/p2_benchmark/TIER_B_GATE_PROTOCOL.md.

Fails closed unless rebuilding split 40 reproduces the stored twin v3 arrays exactly for every
dataset. Writes ``data/sprint_twin_losses_v4/twin4_<ds>.npz`` and a stats file, copied to
``docs/p2_benchmark/results/twin_v4_stats.json``.

    uv run python scripts/p2_benchmark/build_twin_v4.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import wp2_twins as W

V3 = ROOT / "data/sprint_twin_losses_v3"
V4 = ROOT / "data/sprint_twin_losses_v4"
V4_SPLITS = range(160, 280)


def main():
    for nm in W.LOADERS:
        z = np.load(V3 / f"twin3_{nm}.npz")
        keep = z["split"] == 40
        b = W.build_splits(nm, [40])
        if not (np.array_equal(b["l0"], z["l0"][keep]) and np.array_equal(b["l1"], z["l1"][keep])):
            raise SystemExit(f"{nm}: split 40 rebuild does not match twin v3")
        print(f"{nm}: v3 split 40 reproduced")
    V4.mkdir(parents=True, exist_ok=True)
    stats = {"v3_split40_reproduced": True, "splits": [160, 279], "datasets": {}}
    for nm in W.LOADERS:
        b = W.build_splits(nm, V4_SPLITS)
        np.savez(V4 / f"twin4_{nm}.npz", l0=b["l0"], l1=b["l1"], split=b["split"], ep=b["ep"])
        stats["datasets"][nm] = b["stats"]
        s = b["stats"]
        print(f"{nm}: {s['episodes']} episodes, mean adv {s['mean_adv_over_splits']:+.4f}")
    text = json.dumps(stats, indent=1) + "\n"
    (V4 / "stats.json").write_text(text)
    (ROOT / "docs/p2_benchmark/results/twin_v4_stats.json").write_text(text)


if __name__ == "__main__":
    main()
