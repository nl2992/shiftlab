"""Summarise WP1 records (null FP with Clopper-Pearson bounds; power, delay, paired contrasts)."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[2]
PAIRS = (  # (candidate, comparator)
    ("exact0.8_s4", "mlr_default8"),
    ("exact0.95_s4", "mlr_default8"),
    ("env0.8_s4", "mlr_default8"),
    ("exact0.8_s4", "iid_repo32"),
    ("exact0.95_s4", "iid_repo32"),
    ("exact0.8_s4", "exact0.8_s1"),
    ("mlr_s4", "mlr_s1"),
)


def cp_upper(k: int, n: int, level: float = 0.95) -> float:
    """One-sided Clopper-Pearson upper bound."""
    return 1.0 if k >= n else float(beta.ppf(level, k + 1, n - k))


def load(path: Path):
    rows = defaultdict(lambda: defaultdict(list))  # cell -> method -> list of records (seed order)
    for line in path.read_text("utf-8").splitlines():
        r = json.loads(line)
        for m, v in r["values"].items():
            rows[r["cell"]][m].extend(v)
    return rows


def boot_ci(x, n_boot=2000, seed=0):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), (n_boot, len(x)))
    means = x[idx].mean(1)
    return float(x.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize_null(rows, out: Path):
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "method", "n", "fp", "fp_rate", "cp95_upper", "mean_labels_used"])
        for cell in sorted(rows):
            for m, v in rows[cell].items():
                k, n = sum(x["fp"] for x in v), len(v)
                w.writerow(
                    [
                        cell,
                        m,
                        n,
                        k,
                        f"{k / n:.4f}",
                        f"{cp_upper(k, n):.4f}",
                        f"{np.mean([x['n_used'] for x in v]):.1f}",
                    ]
                )


def summarize_alt(rows, out: Path, out_pairs: Path):
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "cell",
                "method",
                "n",
                "detect",
                "detect_rate",
                "false_early_rate",
                "mean_delay_cond",
                "mean_labels_used",
                "mean_cost",
            ]
        )
        for cell in sorted(rows):
            for m, v in rows[cell].items():
                det = [x for x in v if x["on_promo_t"] is not None]
                dl = [x["on_promo_t"] - x["onset"] for x in det]
                w.writerow(
                    [
                        cell,
                        m,
                        len(v),
                        len(det),
                        f"{len(det) / len(v):.3f}",
                        f"{np.mean([x['fp'] for x in v]):.3f}",
                        f"{np.mean(dl):.1f}" if dl else "",
                        f"{np.mean([x['n_used'] for x in v]):.1f}",
                        f"{np.mean([x['cost'] for x in v]):.4f}",
                    ]
                )
    groups = defaultdict(list)  # group -> cells
    for cell in rows:
        typ = cell.split("_rho")[0]
        groups[typ].append(cell)
        groups["ALL"].append(cell)
    with out_pairs.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "group",
                "candidate",
                "comparator",
                "n_pairs",
                "d_detect",
                "lo",
                "hi",
                "d_cost",
                "cost_lo",
                "cost_hi",
            ]
        )
        for g, cells in sorted(groups.items()):
            for a, b in PAIRS:
                dd, dc = [], []
                for c in cells:
                    if a not in rows[c] or b not in rows[c]:
                        continue
                    for xa, xb in zip(rows[c][a], rows[c][b], strict=True):
                        dd.append(
                            int(xa["on_promo_t"] is not None) - int(xb["on_promo_t"] is not None)
                        )
                        dc.append(xa["cost"] - xb["cost"])
                if dd:
                    m1, l1, h1 = boot_ci(dd)
                    m2, l2, h2 = boot_ci(dc)
                    w.writerow(
                        [
                            g,
                            a,
                            b,
                            len(dd),
                            f"{m1:.4f}",
                            f"{l1:.4f}",
                            f"{h1:.4f}",
                            f"{m2:.5f}",
                            f"{l2:.5f}",
                            f"{h2:.5f}",
                        ]
                    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "outputs/gaver/wp1"))
    a = ap.parse_args()
    d = Path(a.dir)
    if (d / "null/records.jsonl").exists():
        summarize_null(load(d / "null/records.jsonl"), d / "null_summary.csv")
    if (d / "alt/records.jsonl").exists():
        summarize_alt(load(d / "alt/records.jsonl"), d / "alt_summary.csv", d / "alt_pairs.csv")


if __name__ == "__main__":
    main()
