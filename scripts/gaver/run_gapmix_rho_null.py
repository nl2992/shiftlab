"""WP1b null calibration (rho in {0,.5,.8,.95,.99}); resumable. See docs/gaver/11_GAPMIX_RHO_RESULTS.md."""

from __future__ import annotations

import argparse
from pathlib import Path

from run_gapmix_rho_common import NULL_METHODS, OUT, null_cells, run_study


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=500)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", action="store_true", help="throwaway seeds, separate output dir")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT / ("null_smoke" if a.smoke else "null")
    run_study(null_cells(), a.n_seeds, a.chunk, out, a.smoke, a.workers, NULL_METHODS)


if __name__ == "__main__":
    main()
