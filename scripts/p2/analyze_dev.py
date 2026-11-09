"""Development-screen table: J on alternatives, promotion and decision harm on every null."""

import collections
import json
import sys
from pathlib import Path

import numpy as np

NULLS = [
    "F0_null",
    "F5_dep_null_r8",
    "F5_dep_null_r95",
    "O_null_order2",
    "WP2_o2_null",
    "O_null_semimarkov",
    "WP2_sm_null",
    "WP2_hs_null",
]
ALTS = [
    "F0_better",
    "F5_dep_better_r8",
    "S_dep_better_r95",
    "WP2_o2_better",
    "WP2_sm_better",
    "WP2_hs_better",
]


def load(d):
    R = collections.defaultdict(lambda: collections.defaultdict(list))
    for l in Path(d, "records.jsonl").read_text().splitlines():
        r = json.loads(l)
        R[r["policy"]][r["regime"]].append((r["net"], r["ever_promote"], -r["db"], r["seed"]))
    return R


def main(d, ref="QSG"):
    R = load(d)
    rows = []
    for p, regs in R.items():
        if not all(a in regs for a in ALTS):
            continue
        J = np.mean([np.mean([x[0] for x in regs[a]]) for a in ALTS])
        Jr = {a: np.mean([x[0] for x in regs[a]]) for a in ALTS}
        pr = {n: np.mean([x[1] for x in regs[n]]) for n in NULLS if n in regs}
        hm = {n: np.mean([x[2] for x in regs[n]]) for n in NULLS if n in regs}
        rows.append((J, p, Jr, pr, hm))
    rows.sort()
    print(
        f"{'policy':28s} {'J_alt':>6s} | "
        + " ".join(f"{a[:8]:>8s}" for a in ALTS)
        + " | promo: "
        + " ".join(f"{n[:9]:>9s}" for n in NULLS)
        + " | maxharm"
    )
    for J, p, Jr, pr, hm in rows:
        print(
            f"{p:28s} {J:6.1f} | "
            + " ".join(f"{Jr[a]:8.1f}" for a in ALTS)
            + " | promo: "
            + " ".join(f"{pr.get(n, np.nan):9.3f}" for n in NULLS)
            + f" | {max(hm.values()):6.2f}"
        )


if __name__ == "__main__":
    main(sys.argv[1])
