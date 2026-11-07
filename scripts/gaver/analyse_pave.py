"""Summaries for WP2 rows.csv: paired bootstrap CIs on cost/round, grades, null FP bounds.

python scripts/gaver/analyse_pave.py <stage> [--ref dss]   (reads outputs/gaver/wp2/<stage>/rows.csv)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[2]


def boot_ci(x: np.ndarray, reps: int = 4000, seed: int = 0) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(reps, len(x)))
    means = x[idx].mean(axis=1)
    return float(x.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def grade(rel: float, lo: float, hi: float) -> str:
    """rel = relative cost reduction vs reference (positive = better); CI on the same scale."""
    if rel <= -0.01 and hi < 0:
        return "worse (CI excl. 0)"
    if rel <= -0.01:
        return "worse (CI incl. 0)"
    if rel >= 0.10 and lo > 0:
        return "substantial"
    if rel >= 0.03 and lo > 0:
        return "meaningful"
    if rel >= 0.01:
        return "small"
    return "negligible"


def cp_upper(k: int, n: int, level: float = 0.95) -> float:
    return 1.0 if k == n else float(beta.ppf(level, k + 1, n - k))


def paired(df: pd.DataFrame, cell: str, a: str, b: str, col: str = "cost"):
    x = df[(df.cell == cell) & (df.method == a)].set_index("seed")[col]
    y = df[(df.cell == cell) & (df.method == b)].set_index("seed")[col]
    j = x.index.intersection(y.index)
    return (x[j] - y[j]).to_numpy(), y[j].mean()


def cost_table(df: pd.DataFrame, new: str, refs: list[str]) -> pd.DataFrame:
    rows = []
    for cell in sorted(df.cell.unique()):
        for ref in refs:
            if ref not in set(df[df.cell == cell].method):
                continue
            d, base = paired(df, cell, new, ref)
            m, lo, hi = boot_ci(d)
            rel, rlo, rhi = -m / base, -hi / base, -lo / base
            rows.append(
                {
                    "cell": cell,
                    "ref": ref,
                    "n": len(d),
                    "ref_cost": base,
                    "new_cost": base + m,
                    "diff": m,
                    "lo": lo,
                    "hi": hi,
                    "rel_gain": rel,
                    "rel_lo": rlo,
                    "rel_hi": rhi,
                    "grade": grade(rel, rlo, rhi),
                }
            )
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("--new", default=None)
    a = ap.parse_args()
    df = pd.read_csv(ROOT / "outputs/gaver/wp2" / a.stage / "rows.csv")
    pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_columns", 30)
    if a.stage == "null":
        g = df.groupby(["cell", "method"]).agg(n=("fp", "size"), k=("fp", "sum")).reset_index()
        g["rate"] = g.k / g.n
        g["cp_ucb95"] = [cp_upper(int(k), int(n)) for k, n in zip(g.k, g.n)]
        print(g.to_string(index=False))
        return
    if a.stage == "tune":
        m = df.groupby(["cell", "method"]).cost.mean().unstack()
        print(m.round(4).to_string())
        print(m.mean().sort_values().round(4).to_string())
        return
    new = a.new or next(m for m in df.method.unique() if m.startswith("pave:p1d1r1"))
    refs = [m for m in df.method.unique() if m != new]
    print(cost_table(df, new, refs).round(4).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
