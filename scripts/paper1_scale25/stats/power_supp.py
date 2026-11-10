"""Supplement to power_analysis.py: cohort-level needed common r_hat restricted to n>=71-episode datasets, for the
primary (min of cube-root and sqrt block rules) and the cube-root-only rule. Output: results/power/cohort_needed_n71.csv"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from certify import alpha_i, fieller_lower, primary_lower
from power_analysis import CAND, EQ_CUT, load, series

rec = sys.argv[1]
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
m = load(rec)
streams = [
    s
    for s in sorted(m.index.get_level_values("stream").unique())
    if m.xs(s, level="stream").shape[0] >= 71
]
refs = [c for c in m.columns if c not in (CAND, "P4W__P2_K2__E48_F60", EQ_CUT)]
structs = [(s, r) for s in streams for r in refs]
cache = {k: series(m, k[0], CAND, k[1]) for k in structs}
rules = {
    "primary": lambda a, b, al: primary_lower(a, b, al)["L"],
    "cuberoot_only": lambda a, b, al: fieller_lower(a, b, al)["L"],
}


def need(alphas, picks, f):
    def meanL(t):
        Ls = []
        for al, k in zip(alphas, picks):
            a, b = cache[k]
            D = b - a
            Ls.append(f(b - (D - D.mean() + t * b.mean() / 100), b, al))
        return np.mean(Ls)

    lo, hi = 2.5, 40.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if meanL(mid) >= 2.5 else (mid, hi)
    return hi


rng = np.random.default_rng(0)
rows = []
for rn, f in rules.items():
    picks25 = [structs[j] for j in rng.choice(len(structs), 25)]
    for label, al in [
        ("B: indices 1..25", [alpha_i(i) for i in range(1, 26)]),
        ("B: indices 8..32 (after 7 legacy)", [alpha_i(i) for i in range(8, 33)]),
        ("B: 25 successes at random among 40 attempts", None),
        ("B: 25 successes at random among 60 attempts", None),
        ("A1 Bonferroni K=25 (.002 each)", [0.05 / 25] * 25),
        ("B' batch 1, M=25 (.001 each)", [0.025 / 25] * 25),
        ("single-level .05 each (no multiplicity; reference only)", [0.05] * 25),
    ]:
        if al is None:
            N = int(label.split("among ")[1].split()[0])
            v = [
                need(
                    [
                        alpha_i(int(p))
                        for p in np.sort(rng.choice(np.arange(1, N + 1), 25, replace=False))
                    ],
                    [structs[j] for j in rng.choice(len(structs), 25)],
                    f,
                )
                for _ in range(8)
            ]
            rows.append(
                {"rule": rn, "design": label, "needed_common_r_hat": np.mean(v), "sd": np.std(v)}
            )
        else:
            rows.append(
                {
                    "rule": rn,
                    "design": label,
                    "needed_common_r_hat": need(al, picks25, f),
                    "sd": np.nan,
                }
            )
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(out / "cohort_needed_n71.csv", index=False)
