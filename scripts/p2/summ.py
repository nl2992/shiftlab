"""Quick summary: mean net / promote / labels per (regime, policy)."""

import collections
import json
import sys
from pathlib import Path

import numpy as np

d = collections.defaultdict(list)
for l in Path(sys.argv[1], "records.jsonl").read_text().splitlines():
    r = json.loads(l)
    d[(r["regime"], r["policy"])].append(
        (
            r["net"],
            r["ever_promote"],
            r["labels"],
            -r["db"],
            r["first_deploy"]
            if r["first_deploy"] is not None and r["first_deploy"] >= 0
            else np.nan,
        )
    )
for k, v in sorted(d.items()):
    a = np.array(v, float)
    print(
        f"{k[0]:22s} {k[1]:24s} n={len(a):4d} J={a[:, 0].mean():7.1f}±{a[:, 0].std() / np.sqrt(len(a)):4.1f} prom={a[:, 1].mean():.3f} lab={a[:, 2].mean():5.1f} harm={a[:, 3].mean():6.2f} t1={np.nanmean(a[:, 4]) if np.isfinite(a[:, 4]).any() else float('nan'):6.0f}"
    )
