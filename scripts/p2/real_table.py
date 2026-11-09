"""Per-source mean J on real streams and paired differences vs a candidate (episode-cluster CIs)."""

import collections
import json
import sys
from pathlib import Path

import numpy as np


def main(d, cand, comps):
    D = collections.defaultdict(dict)
    for line in Path(d, "records.jsonl").read_text().splitlines():
        r = json.loads(line)
        D[r["policy"]][(r["regime"], r["ep"], r["seed"])] = r["net"]
    srcs = sorted({k[0] for k in D[cand]})
    rng = np.random.default_rng(0)
    for c in comps:
        diffs, wins = [], 0
        for s in srcs:
            eps = sorted({k[1] for k in D[cand] if k[0] == s})
            per_ep = []
            for e in eps:
                ks = [k for k in D[cand] if k[0] == s and k[1] == e and k in D[c]]
                per_ep.append(np.mean([D[cand][k] - D[c][k] for k in ks]))
            diffs.append(np.array(per_ep))
            wins += np.mean(per_ep) < 0
        est = np.mean([x.mean() for x in diffs])
        bs = np.mean([x[rng.integers(0, len(x), (2000, len(x)))].mean(1) for x in diffs], 0)
        base = np.mean([np.mean([v for k, v in D[c].items() if k[0] == s]) for s in srcs])
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print(f"{cand} - {c:28s} {est:+7.2f} [{lo:+6.2f},{hi:+6.2f}] ({100 * est / base:+5.1f}%) "
              f"wins {wins}/{len(srcs)}  " + " ".join(f"{s[:6]}:{x.mean():+.1f}" for s, x in zip(srcs, diffs)))  # fmt: skip


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3].split(","))
