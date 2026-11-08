"""Matched-assumption Gap-Mix study runner (docs/methods_recovery/51_GAPMIX_MATCHED.md). Resumable.

python scripts/methods_recovery/gapmix_match.py run --kind null --workers 4 [--max-rho 0.8]
python scripts/methods_recovery/gapmix_match.py run --kind alt --workers 4
python scripts/methods_recovery/gapmix_match.py summarize
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "gaver"))

import numpy as np
from run_gapmix_common import alt_cells, null_cells  # WP1 cell definitions (unchanged)
from scipy.stats import beta

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver import gapmix_matched as mm

OUT = ROOT / "outputs/methods_recovery/gapmix_match"
NULL_BASE, NULL_END = 101900000, 101909999  # registered gapmix_match_null
ALT_BASE, ALT_END = 102000000, 102029999  # registered gapmix_match_power
SMOKE_BASE = 7100000
ARMS = mm.MATCHED_ARMS
PAIRS_ALL = (  # (candidate, comparator)
    ("exact0.8_s4", "mlr_rb0.8"),
    ("exact0.8_s4", "ui_gap_allstarts"),
    ("exact0.8_s4", "mlr_default8"),
    ("exact0.8_s4", "thin10_s4"),
    ("ui_gap_allstarts", "mlr_rb0.8"),
)


def seeds_for(kind, idx, n, smoke):
    if smoke:
        return [SMOKE_BASE + (0 if kind == "null" else 500000) + idx * 1000 + i for i in range(n)]
    base, end = (NULL_BASE, NULL_END) if kind == "null" else (ALT_BASE, ALT_END)
    s = [base + idx * 1000 + i for i in range(n)]
    assert s[-1] <= end
    return s


def task(args):
    cid, cell, seeds, arms = args
    out = {m: [] for m in arms}
    t0 = {m: 0.0 for m in arms}
    for seed in seeds:
        stream = fa.make_stream(cell, seed)
        for name in arms:
            cfg = cell.config(seed)
            m = mm.build_gate(name)
            tic = time.perf_counter()
            r = fa.run_for(cell, stream, m, cfg)
            t0[name] += time.perf_counter() - tic
            path = stream.truth.regime
            onset = int(np.argmax(path)) + 1 if path.any() else None
            hit = np.nonzero((r.actions == 1) & (path == 1))[0]
            out[name].append(
                {
                    "fp": int((r.fp_regime or 0) > 0),
                    "promoted": int(r.promotions > 0),
                    "on_promo_t": int(hit[0]) + 1 if len(hit) else None,
                    "onset": onset,
                    "alarm_ev": m.first_alarm_ev,
                    "n_used": m.n_used,
                    "queries": int(r.queries),
                    "cost": float(r.cost) / cell.T,
                }
            )
    return {"cell": cid, "seeds": list(seeds), "values": out, "secs": t0}


def run(kind, n_seeds, chunk, workers, smoke, max_rho, out_dir):
    cells = null_cells() if kind == "null" else alt_cells()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "records.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            r = json.loads(line)
            done.add((r["cell"], r["seeds"][0]))
    jobs = []
    for idx, c in enumerate(cells):
        if c["cell"].rho > max_rho + 1e-9:
            continue  # idx (hence seeds) of the remaining cells is unchanged
        sd = seeds_for(kind, idx, n_seeds, smoke)
        for i in range(0, n_seeds, chunk):
            part = sd[i : i + chunk]
            if (c["id"], part[0]) not in done:
                jobs.append((c["id"], c["cell"], part, ARMS))
    print(f"{len(jobs)} chunks to run, {len(done)} done", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool, path.open("a", encoding="utf-8") as fh:
        for k, rec in enumerate(pool.map(task, jobs)):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(
                f"[{k + 1}/{len(jobs)}] {rec['cell']} {rec['seeds'][0]} { ({a: round(s) for a, s in rec['secs'].items()}) }",
                flush=True,
            )


# ------------------------------------------------------------------ summaries


def cp_upper(k, n, level=0.95):
    return 1.0 if k >= n else float(beta.ppf(level, k + 1, n - k))


def load(path):
    rows = defaultdict(lambda: defaultdict(list))
    for line in path.read_text("utf-8").splitlines():
        r = json.loads(line)
        for m, v in r["values"].items():
            rows[r["cell"]][m].extend(v)
    return rows


def boot(x, n_boot=2000, seed=0):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        means[b] = x[rng.integers(0, len(x), len(x))].mean()
    return float(x.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize():
    res = {}
    npath, apath = OUT / "null/records.jsonl", OUT / "alt/records.jsonl"
    if npath.exists():
        rows = load(npath)
        with (OUT / "null_summary.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["cell", "method", "n", "fp", "fp_rate", "cp95_upper", "mean_labels_used"])
            for cell in sorted(rows):
                for m in ARMS:
                    v = rows[cell].get(m)
                    if v:
                        k, n = sum(x["fp"] for x in v), len(v)
                        w.writerow([cell, m, n, k, f"{k / n:.4f}", f"{cp_upper(k, n):.4f}",
                                    f"{np.mean([x['n_used'] for x in v]):.1f}"])  # fmt: skip
        res["null"] = rows
    if apath.exists():
        rows = load(apath)
        with (OUT / "alt_summary.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(
                [
                    "cell",
                    "method",
                    "n",
                    "detect_rate",
                    "mean_delay_cond",
                    "mean_labels_used",
                    "mean_cost",
                ]
            )
            for cell in sorted(rows):
                for m in ARMS:
                    v = rows[cell].get(m)
                    if not v:
                        continue
                    det = [x for x in v if x["on_promo_t"] is not None]
                    dl = [x["on_promo_t"] - x["onset"] for x in det]
                    w.writerow([cell, m, len(v), f"{len(det) / len(v):.3f}",
                                f"{np.mean(dl):.1f}" if dl else "", f"{np.mean([x['n_used'] for x in v]):.1f}",
                                f"{np.mean([x['cost'] for x in v]):.4f}"])  # fmt: skip
        groups = defaultdict(list)
        for cell in rows:
            typ = cell.split("_rho")[0].replace("alt_", "")
            groups["ALL"].append(cell)
            groups[typ].append(cell)
            groups["B" + ("100" if cell.endswith("bt0.1") else "250")].append(cell)
        with (OUT / "alt_pairs.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["group", "candidate", "comparator", "n_pairs", "mean_detect_cand", "mean_detect_comp",
                        "d_detect", "lo", "hi", "mean_cost_cand", "mean_cost_comp", "d_cost", "cost_lo", "cost_hi",
                        "rel_cost_gain"])  # fmt: skip
            for g, cells in sorted(groups.items()):
                for a, b in PAIRS_ALL:
                    da, db, ca, cb = [], [], [], []
                    for c in cells:
                        if a in rows[c] and b in rows[c]:
                            for xa, xb in zip(rows[c][a], rows[c][b], strict=True):
                                da.append(int(xa["on_promo_t"] is not None))
                                db.append(int(xb["on_promo_t"] is not None))
                                ca.append(xa["cost"])
                                cb.append(xb["cost"])
                    if not da:
                        continue
                    da, db, ca, cb = map(np.asarray, (da, db, ca, cb))
                    m1, l1, h1 = boot(da - db)
                    m2, l2, h2 = boot(ca - cb)
                    w.writerow([g, a, b, len(da), f"{da.mean():.4f}", f"{db.mean():.4f}", f"{m1:.4f}", f"{l1:.4f}",
                                f"{h1:.4f}", f"{ca.mean():.5f}", f"{cb.mean():.5f}", f"{m2:.5f}", f"{l2:.5f}",
                                f"{h2:.5f}", f"{-(ca.mean() - cb.mean()) / cb.mean():.4f}"])  # fmt: skip
        res["alt"] = rows
    return res


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--kind", choices=["null", "alt"], required=True)
    r.add_argument("--n-seeds", type=int, default=None)
    r.add_argument("--chunk", type=int, default=None)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--max-rho", type=float, default=0.95)
    r.add_argument("--smoke", action="store_true")
    sub.add_parser("summarize")
    a = ap.parse_args()
    if a.cmd == "run":
        n = a.n_seeds or (500 if a.kind == "null" else 60)
        ch = a.chunk or (25 if a.kind == "null" else 10)
        out = OUT / (("smoke_" if a.smoke else "") + a.kind)
        run(a.kind, n, ch, a.workers, a.smoke, a.max_rho, out)
    else:
        summarize()


if __name__ == "__main__":
    main()
