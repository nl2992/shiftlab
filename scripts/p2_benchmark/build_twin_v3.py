"""Build the P2 twin v3 cohort (splits 40..159) after verifying v2 reproduction (W4, 2026-11-07).

Fails closed unless rebuilding v2 splits 20..39 reproduces the recorded ``array_content_sha256`` for
every dataset. Writes ``data/sprint_twin_losses_v3/twin3_<ds>.npz`` plus T=1000/4000 re-windowings
and a stats file; copies the stats into ``docs/p2_benchmark/results/twin_v3_stats.json``.

    uv run python scripts/p2_benchmark/build_twin_v3.py --v2-stats PATH/TO/sprint_twin_losses_v2/stats.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import wp2_twins as W

V3 = ROOT / "data/sprint_twin_losses_v3"
V3_SPLITS = range(40, 160)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-stats", required=True, type=Path)
    a = ap.parse_args(argv)
    v2 = json.loads(a.v2_stats.read_text())
    for nm in W.LOADERS:
        got = W.build_splits(nm, W.V2_SPLITS)["stats"]["array_content_sha256"]
        if got != v2[nm]["array_content_sha256"]:
            raise SystemExit(
                f"{nm}: v2 rebuild {got[:12]} != recorded {v2[nm]['array_content_sha256'][:12]}"
            )
        print(f"{nm}: v2 reproduced")
    V3.mkdir(parents=True, exist_ok=True)
    stats = {"v2_reproduced": True, "splits": [40, 159], "datasets": {}, "variants": {}}
    for nm in W.LOADERS:
        b = W.build_splits(nm, V3_SPLITS)
        np.savez(V3 / f"twin3_{nm}.npz", l0=b["l0"], l1=b["l1"], split=b["split"], ep=b["ep"])
        stats["datasets"][nm] = b["stats"]
        z = np.load(V3 / f"twin3_{nm}.npz")
        for T in (1000, 4000):
            v = W.rewindow(z, T)
            np.savez(V3 / f"twin3_{nm}_T{T}.npz", **v)
            stats["variants"][f"{nm}_T{T}"] = {
                "episodes": int(v["l0"].shape[0]),
                "array_content_sha256": W.content_hash(v["l0"], v["l1"]),
            }
        s = b["stats"]
        print(
            f"{nm}: {s['episodes']} episodes, mean adv {s['mean_adv_over_splits']:+.4f}, rho {s['median_rho_hat']}"
        )
    text = json.dumps(stats, indent=1) + "\n"
    (V3 / "stats.json").write_text(text)
    out = ROOT / "docs/p2_benchmark/results/twin_v3_stats.json"
    out.write_text(text)


if __name__ == "__main__":
    main()
