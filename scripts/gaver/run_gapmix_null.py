"""WP1.4 null calibration (uniform calendar). Resumable; see docs/gaver/10_GAPMIX_RESULTS.md."""

from __future__ import annotations

import argparse
from pathlib import Path

from run_gapmix_common import ROOT, null_cells, run_study


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=500)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--smoke", action="store_true", help="throwaway seeds, separate output dir")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    default = ROOT / "outputs/gaver/wp1" / ("null_smoke" if a.smoke else "null")
    out = Path(a.out) if a.out else default
    run_study(null_cells(), a.n_seeds, a.chunk, out, a.smoke, a.workers)


if __name__ == "__main__":
    main()
