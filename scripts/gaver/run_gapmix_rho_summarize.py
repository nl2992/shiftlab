"""Summarise WP1b records: null FP (Clopper-Pearson), power, paired contrasts, gain fraction."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
from run_gapmix_summarize import boot_ci, cp_upper, load

ROOT = Path(__file__).resolve().parents[2]
REF, ANCHOR = "mlr_default8", "exact0.8_s4"
CANDS = (
    "exact0.8_s4",
    "exact0.95_s4",
    "exact0.99_s4",
    "exactcs_s4",
    "gate_eq_s4",
    "gate_w_s4",
    "gate_fine_eq_s4",
    "envcs_s4",
)
EXTRA_PAIRS = (("exactcs_s4", "exact0.95_s4"), ("exactcs_s4", "exact0.99_s4"))


def summarize_null(rows, out: Path):
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "method", "n", "fp", "fp_rate", "cp95_upper", "mean_ub_final"])
        for cell in sorted(rows):
            for m, v in rows[cell].items():
                k, n = sum(x["fp"] for x in v), len(v)
                ubs = [x["ub_final"] for x in v if x.get("ub_final") is not None]
                w.writerow(
                    [cell, m, n, k, f"{k / n:.4f}", f"{cp_upper(k, n):.4f}"]
                    + [f"{np.mean(ubs):.3f}" if ubs else ""]
                )


def _det(v):
    return np.array([int(x["on_promo_t"] is not None) for x in v], float)


def summarize_alt(rows, out: Path, out_pairs: Path):
    groups = defaultdict(list)
    for cell in rows:
        groups[cell.split("_rho")[0]].append(cell)
        groups["ALL"].append(cell)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["group", "method", "n", "detect_rate", "false_early", "mean_cost", "delay_cond"]
        )
        for g, cells in sorted(groups.items()):
            for m in CANDS + (REF,):
                v = [x for c in cells if m in rows[c] for x in rows[c][m]]
                if not v:
                    continue
                dl = [x["on_promo_t"] - x["onset"] for x in v if x["on_promo_t"] is not None]
                w.writerow(
                    [
                        g,
                        m,
                        len(v),
                        f"{_det(v).mean():.3f}",
                        f"{np.mean([x['fp'] for x in v]):.3f}",
                        f"{np.mean([x['cost'] for x in v]):.4f}",
                        f"{np.mean(dl):.0f}" if dl else "",
                    ]
                )
    pairs = [(c, REF) for c in CANDS if c != REF] + list(EXTRA_PAIRS)
    with out_pairs.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["group", "cand", "comp", "n", "d_detect", "lo", "hi", "d_cost", "clo", "chi",
             "gain_frac_of_anchor", "gf_lo", "gf_hi"]
        )  # fmt: skip
        rng = np.random.default_rng(0)
        for g, cells in sorted(groups.items()):
            cells = [c for c in cells if all(m in rows[c] for m in (ANCHOR, REF))]
            if not cells:
                continue
            anchor = np.concatenate([_det(rows[c][ANCHOR]) - _det(rows[c][REF]) for c in cells])
            for a, b in pairs:
                cs = [c for c in cells if a in rows[c] and b in rows[c]]
                if not cs:
                    continue
                dd = np.concatenate([_det(rows[c][a]) - _det(rows[c][b]) for c in cs])
                dc = np.concatenate(
                    [
                        [x["cost"] - y["cost"] for x, y in zip(rows[c][a], rows[c][b], strict=True)]
                        for c in cs
                    ]
                )
                m1, l1, h1 = boot_ci(dd)
                m2, l2, h2 = boot_ci(dc)
                gf = gl = gh = ""
                if b == REF and len(anchor) == len(dd) and anchor.mean() > 0:
                    idx = rng.integers(0, len(dd), (2000, len(dd)))
                    r = dd[idx].mean(1) / np.maximum(anchor[idx].mean(1), 1e-9)
                    gf = f"{dd.mean() / anchor.mean():.3f}"
                    gl, gh = f"{np.quantile(r, 0.025):.3f}", f"{np.quantile(r, 0.975):.3f}"
                w.writerow(
                    [g, a, b, len(dd), f"{m1:.4f}", f"{l1:.4f}", f"{h1:.4f}",
                     f"{m2:.5f}", f"{l2:.5f}", f"{h2:.5f}", gf, gl, gh]
                )  # fmt: skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "outputs/gaver/wp1b"))
    d = Path(ap.parse_args().dir)
    if (d / "null/records.jsonl").exists():
        summarize_null(load(d / "null/records.jsonl"), d / "null_summary.csv")
    if (d / "alt/records.jsonl").exists():
        summarize_alt(load(d / "alt/records.jsonl"), d / "alt_summary.csv", d / "alt_pairs.csv")


if __name__ == "__main__":
    main()
