"""Summarise Failure Atlas v2 records into algorithm-by-regime tables and shared-failure counts.

A (policy, source) cell is flagged as a FAILURE when its mean net cost exceeds the best published
competitor in that source by more than ``--margin`` per 1000 events AND, for change/alt regimes,
it misses the expected-oracle deployment for more than 25% of the horizon. Paired differences
use the source's seeds (synthetic) or episodes (real) as units, with a percentile bootstrap.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

CONTROLS = {"CONTROL_never_switch", "economic_replacement"}
OURS = {"P7s_settled"}


def load(paths):
    rows = []
    for p in paths:
        with open(p) as fh:
            rows += [json.loads(x) for x in fh]
    return rows


def boot_ci(x, rng, n=4000):
    x = np.asarray(x, float)
    if len(x) < 2:
        return float("nan"), float("nan")
    idx = rng.integers(0, len(x), (n, len(x)))
    m = x[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def table(rows, unit_key=("episode", "seed")):
    by = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        by[r["source"]][r["policy"]][(r["episode"], r["seed"]) if r["kind"] == "real"
                                     else r["seed"]] = r
    return by


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--margin", type=float, default=0.0)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(991)
    rows = load(a.records)
    by = table(rows)
    summary = {}
    for src, pols in by.items():
        keys = sorted(set.intersection(*[set(v) for v in pols.values()]), key=str)
        kind = next(iter(next(iter(pols.values())).values()))["kind"]
        ent = {"kind": kind, "n_units": len(keys), "policies": {}}
        for p, recs in pols.items():
            M = {k: np.array([recs[u][k] for u in keys], float) for k in
                 ("net", "loss", "labels", "switches", "first_deploy", "final", "ever_promote",
                  "frac_on_wrong", "label_mean_t", "labels_by_500", "exhaust_t",
                  "regret_hindsight", "regret_expected_oracle")}
            fd = M["first_deploy"]
            ent["policies"][p] = {
                "net": float(M["net"].mean()), "loss": float(M["loss"].mean()),
                "labels": float(M["labels"].mean()), "switches": float(M["switches"].mean()),
                "ever_promote": float(M["ever_promote"].mean()),
                "final_challenger": float(M["final"].mean()),
                "median_first_deploy": float(np.median(fd[fd >= 0])) if (fd >= 0).any() else None,
                "frac_on_wrong": float(M["frac_on_wrong"].mean()),
                "label_mean_t": float(np.nanmean(M["label_mean_t"])),
                "labels_by_500": float(M["labels_by_500"].mean()),
                "exhaust_t": float(M["exhaust_t"].mean()),
                "regret_hindsight": float(M["regret_hindsight"].mean()),
                "regret_expected_oracle": float(M["regret_expected_oracle"].mean()),
                "_net": M["net"],
            }
        pubs = [p for p in ent["policies"] if p not in CONTROLS | OURS]
        best = min(pubs, key=lambda p: ent["policies"][p]["net"])
        ent["best_published"] = best
        for p, s in ent["policies"].items():
            d = s["_net"] - ent["policies"][best]["_net"]
            lo, hi = boot_ci(d, rng)
            s["gap_to_best_published"] = {"mean": float(d.mean()), "lo": lo, "hi": hi}
        summary[src] = ent
    for ent in summary.values():
        for s in ent["policies"].values():
            s.pop("_net")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    # compact print
    for src, ent in summary.items():
        print(f"\n== {src} ({ent['kind']}, n={ent['n_units']}) best published: {ent['best_published']}")
        for p, s in sorted(ent["policies"].items(), key=lambda kv: kv[1]["net"]):
            g = s["gap_to_best_published"]
            print(f"  {p:24s} net={s['net']:8.2f} gap={g['mean']:+7.2f} [{g['lo']:+6.2f},{g['hi']:+6.2f}]"
                  f" lab={s['labels']:5.1f} sw={s['switches']:4.2f} prom={s['ever_promote']:.2f}"
                  f" fin1={s['final_challenger']:.2f} t1={s['median_first_deploy']}"
                  f" wrong={s['frac_on_wrong']:.2f} regE={s['regret_expected_oracle']:7.2f}"
                  f" lab500={s['labels_by_500']:5.1f}")


if __name__ == "__main__":
    main()
