"""Power analysis for the P2 confirmatory twin-null hypotheses (W4, 2026-11-06).

Reads the exposed v2 twin run (splits 20..39) and reports, per dataset and policy, the mean and
between-split SD of the per-split promotion rate. Then, for each dataset, it finds the smallest
split count giving >= 80% power for the rule "upper 95% bound <= .0936" when the true rate is .05,
using a normal approximation with the observed A5b SD (floored at the binomial SD for one split).

    uv run python scripts/p2_benchmark/twin_power.py RECORDS.jsonl [--out power.json]
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

POLICIES = ["A5b", "D5", "gated_adaptive_range", "discern_design_floor", "SMCS+retain-incumbent",
            "QSG", "D2", "cams_adapter", "model_picker_adapter"]  # fmt: skip
BOUND, TRUE_RATE, TARGET = 0.0936, 0.05, 0.80
GRID = (20, 40, 60, 80, 100, 120, 160, 200)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    d = collections.defaultdict(list)
    with open(a.records) as f:
        for line in f:
            r = json.loads(line)
            d[(r["regime"], r["policy"], r["split"])].append(r["ever_promote"])
    datasets = sorted({k[0] for k in d})
    splits = sorted({k[2] for k in d})
    out = {"source": str(a.records), "splits": [splits[0], splits[-1]], "rates": {}, "power": {}}
    for pol in POLICIES:
        for ds in datasets:
            if (ds, pol, splits[0]) not in d:
                continue
            rates = np.array([np.mean(d[(ds, pol, s)]) for s in splits])
            out["rates"][f"{ds}|{pol}"] = [float(rates.mean()), float(rates.std(ddof=1))]
    for ds in datasets:
        rates = np.array([np.mean(d[(ds, "A5b", s)]) for s in splits])
        per_split_n = len(d[(ds, "A5b", splits[0])])
        sd = max(float(rates.std(ddof=1)), math.sqrt(TRUE_RATE * (1 - TRUE_RATE) / per_split_n))
        rows = {n: float(norm.cdf((BOUND - TRUE_RATE) / (sd / math.sqrt(n)) - 1.96)) for n in GRID}
        need = next((n for n in GRID if rows[n] >= TARGET), None)
        out["power"][ds] = {"sd": sd, "power_by_n": rows, "splits_needed": need}
        print(f"{ds}: sd={sd:.3f} splits needed={need} power@20={rows[20]:.2f}")
    if a.out:
        a.out.write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
