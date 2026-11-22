"""Lead control for Phase 3: the 'rises' stream of an i.i.d. series is anti-persistent by construction.

Draw i.i.d. Gaussian series (no hidden regime at all), build the 'rises' stream exactly as in Phase 3, then run the same
screen and eval_stream. Reports how often Phase 3's positive criteria are met on pure noise.
Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/wn_control.py OUT.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase3 as p3  # noqa: E402

SEED = 20261117
SIZES = (108, 118, 278, 425)


def main(out: str) -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for i in range(24):
        n = SIZES[i % len(SIZES)]
        series = rng.standard_normal(n + 1)
        x = (np.diff(series) > 0).astype(int)
        r1 = float(np.corrcoef(x[:-1], x[1:])[0, 1])
        rec = {"i": i, "n": n, "r1": r1, "screen_pass": r1 <= -0.15}
        if rec["screen_pass"]:
            e = p3.eval_stream(x, f"wn{i}")
            rec.update(
                g1=e["g1"]["pass_"],
                g2=e["g2"]["pass_"],
                fit=[e["fit"][k] for k in ("t01", "t10", "e0", "e1")],
                positive_any_cell=e["positive_any_cell"],
                nondegenerate_positive=e["nondegenerate_positive"],
                rho_max=e.get("rho_max"),
                best_cell=e.get("best_cell"),
            )
        rows.append(rec)
        print(i, n, round(r1, 3), {k: rec.get(k) for k in ("g1", "g2", "positive_any_cell", "nondegenerate_positive", "rho_max")}, flush=True)
    Path(out).write_text(json.dumps(rows, indent=1))
    ev = [r for r in rows if r["screen_pass"]]
    print("series", len(rows), "screen pass", len(ev), "G1 pass", sum(r["g1"] for r in ev),
          "positive any-cell", sum(r["positive_any_cell"] for r in ev),
          "positive + nondegenerate", sum(r["nondegenerate_positive"] for r in ev))


if __name__ == "__main__":
    main(sys.argv[1])
