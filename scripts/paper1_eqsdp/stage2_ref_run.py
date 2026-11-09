"""Stage 2 step 1: re-tuned reference grid on even episodes (detached-friendly).

  python stage2_ref_run.py grid           # Wald lam x gamma x H (84) + arm R x H (7)
  python stage2_ref_run.py thin NAME...   # thinned registry names, e.g. s2wald_l0.98_g0.3_H1100_k0.5
Writes outputs/paper1_eqsdp/stage2/ref_<mode>/records.jsonl (+ progress.txt).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_eval as ev
import stage2_policies as sp2
import trace_run as tr

OUT = tr.ROOT / "outputs/paper1_eqsdp/stage2"


def main():
    mode = sys.argv[1]
    if mode == "grid":
        names = [
            sp2.wald_name(lam, g, h)
            for lam in sp2.WALD_LAMS
            for g in sp2.WALD_GAMS
            for h in sp2.H_GRID
        ] + [sp2.armr_name(h) for h in sp2.H_GRID]
    elif mode == "thin":
        names = [n for n in sys.argv[2:]]  # explicit registry names (k in {.5,.25})
    else:
        raise SystemExit(mode)
    ev.run_named(names, "even", OUT / f"ref_{mode}", workers=16)


if __name__ == "__main__":
    main()
