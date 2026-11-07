"""WP1b power on WP1's four alternatives (paired seeds); resumable. See docs/gaver/11_GAPMIX_RHO_RESULTS.md."""

from __future__ import annotations

import argparse
from pathlib import Path

from run_gapmix_rho_common import OUT, POWER_METHODS, alt_cells, run_study


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=60)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", action="store_true", help="throwaway seeds, separate output dir")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT / ("alt_smoke" if a.smoke else "alt")
    run_study(alt_cells(), a.n_seeds, a.chunk, out, a.smoke, a.workers, POWER_METHODS)


if __name__ == "__main__":
    main()
