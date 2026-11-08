"""Locked Stage-2 analysis for comparator_panel_protocol.md."""

import sys

import pandas as pd
from analyze_c3 import holm, ttest
from analyze_d2 import CHANGE, GUARD, seedmean

ARMS = ("EQSDp_l0.95_g0.2", "EQSDp_l0.9_g0.2")


def main(path, best):
    d = pd.read_json(path, lines=True)
    fam, ch, gu = seedmean(d, CHANGE + GUARD), seedmean(d, CHANGE), seedmean(d, GUARD)
    rows = [(a, c, ttest(fam[a] - fam[c])) for a in ARMS for c in best]
    adj = holm([r[2]["p"] for r in rows])
    print("arm | comparator | diff [95% CI] | p_holm | change diff | guard diff")
    for (a, c, t), pa in zip(rows, adj, strict=True):
        cd, gd = (ch[a] - ch[c]).mean(), (gu[a] - gu[c]).mean()
        print(
            f"{a} | {c} | {t['mean']:+.2f} [{t['lo']:+.2f},{t['hi']:+.2f}] | {pa:.2g} | "
            f"{cd:+.2f} | {gd:+.2f}"
        )
    for a in ARMS:
        ok = [
            c
            for (aa, c, t), pa in zip(rows, adj, strict=True)
            if aa == a and pa < 0.05 and t["mean"] < 0
        ]
        print(a, "beats", len(ok), "/", len(best), ok)
    s = pd.DataFrame({"family": fam.mean(), "change": ch.mean(), "guard": gu.mean()})
    s["sw_null"] = d[d.regime.isin(["F0_null", "V_null"])].groupby("policy").switches.mean()
    print(s.sort_values("family").round(2).to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2].split(","))
