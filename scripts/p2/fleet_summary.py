"""Summarise fleet runs: cost, FDR, power, paired J vs base (fleet-clustered bootstrap)."""

import collections
import json
import sys
from pathlib import Path

import numpy as np


def main(d, group="pi0"):
    F = collections.defaultdict(list)
    for line in Path(d, "records.jsonl").read_text().splitlines():
        r = json.loads(line)
        F[(r.get(group, r.get("source")), r.get("fleet", r.get("source")), r["arm"])].append(r)
    groups = sorted({k[0] for k in F}, key=str)
    arms = sorted({k[2] for k in F})
    rng = np.random.default_rng(0)
    for g in groups:
        print(f"== {group}={g}")
        fleets = sorted({k[1] for k in F if k[0] == g}, key=str)
        base = {f: np.mean([r["net"] for r in F[(g, f, "base")]]) for f in fleets}
        for a in arms:
            J, fdr, pw, lab, dJ = [], [], [], [], []
            for f in fleets:
                rs = F[(g, f, a)]
                J.append(np.mean([r["net"] for r in rs]))
                lab.append(np.mean([r["labels"] for r in rs]))
                dJ.append(J[-1] - base[f])
                if "null" in rs[0]:
                    R = sum(r["promoted"] for r in rs)
                    V = sum(r["promoted"] and r["null"] for r in rs)
                    fdr.append(V / max(R, 1))
                    nn = [r for r in rs if not r["null"]]
                    pw.append(np.mean([r["promoted"] for r in nn]) if nn else np.nan)
                else:  # real: proxy "false" = promoted on an episode with realised adv <= 0
                    R = sum(r["promoted"] for r in rs)
                    V = sum(r["promoted"] and r["adv"] <= 0 for r in rs)
                    fdr.append(V / max(R, 1))
                    pw.append(R / len(rs))
            dJ = np.array(dJ)
            bs = dJ[rng.integers(0, len(dJ), (4000, len(dJ)))].mean(1)
            lo, hi = np.percentile(bs, [2.5, 97.5])
            print(f"  {a:10s} J={np.mean(J):7.2f} dJ_vs_base={dJ.mean():+6.2f} [{lo:+.2f},{hi:+.2f}] "
                  f"FDR={np.mean(fdr):.3f} power/promo={np.nanmean(pw):.3f} labels={np.mean(lab):.0f}")  # fmt: skip


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "pi0")
