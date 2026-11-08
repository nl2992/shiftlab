"""Next-method development analysis: family means, best fixed-discount Wald, paired contrasts.

usage: analyze_nm.py records.jsonl [comparator] [arm1,arm2,...]
Without a comparator, the best ``wald_*`` arm on these seeds (in-sample) is used.
"""

import sys

import pandas as pd
from analyze_c3 import ttest
from analyze_d2 import CHANGE, GUARD, seedmean

FAMS = ("wald_", "ms_", "rs_", "ld_", "asym_", "EQSDp", "gongT", "qiu")


def main(path, comp=None, arms=None):
    d = pd.read_json(path, lines=True)
    fam, ch, gu = seedmean(d, CHANGE + GUARD), seedmean(d, CHANGE), seedmean(d, GUARD)
    m = fam.mean().sort_values()
    comp = comp or m[[c for c in m.index if c.startswith("wald_")]].idxmin()
    print(f"seeds={fam.shape[0]}  comparator={comp} ({m[comp]:.2f})")
    print("\n== best per family (in-sample) ==")
    best = {}
    for f in FAMS:
        cols = [c for c in m.index if c.startswith(f)]
        if cols:
            best[f] = m[cols].idxmin()
            print(f"{f:7s} {best[f]:32s} {m[best[f]]:.2f}")
    arms = arms or [best[f] for f in FAMS if f in best and best[f] != comp]
    print("\n== paired vs comparator (family | change | guard) ==")
    for a in arms:
        t = ttest(fam[a] - fam[comp])
        print(
            f"{a:32s} {t['mean']:+.2f} [{t['lo']:+.2f},{t['hi']:+.2f}] p={t['p']:.2g} | "
            f"{(ch[a] - ch[comp]).mean():+.2f} | {(gu[a] - gu[comp]).mean():+.2f}"
        )
    print("\n== per-regime mean net (arms vs comparator) ==")
    sub = d[d.policy.isin([comp, *arms])]
    pr = sub.pivot_table(index="regime", columns="policy", values="net", aggfunc="mean")
    print(pr[[comp, *arms]].round(1).to_string())
    sw = sub.pivot_table(index="regime", columns="policy", values="switches", aggfunc="mean")
    print("\n== switches ==")
    print(sw[[comp, *arms]].round(2).to_string())
    print("\n== top 25 overall ==")
    print(m.head(25).round(2).to_string())


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1] if len(a) > 1 and a[1] else None, a[2].split(",") if len(a) > 2 else None)
