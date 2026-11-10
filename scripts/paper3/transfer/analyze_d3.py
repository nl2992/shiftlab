from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("outputs/paper3/transfer")
rng = np.random.default_rng(0)
d = pd.read_csv(OUT / "d3_results_main.csv")
lines = [
    "| fold | variant | n | iters | train s | peak MB | dJ vs global_fixed [CI] | dJ vs per_stream_tuned [CI] | dJ vs ref wald [CI] | train J first10 -> last10 |",
    "|---|---|---|---|---|---|---|---|---|---|",
]


def ci(x):
    b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(2000)]
    lo, hi = np.percentile(b, [2.5, 97.5])
    return f"{x.mean():+.1f} [{lo:+.1f},{hi:+.1f}]"


for (f, v), g in d.groupby(["fold", "variant"]):
    lines.append(
        f"| {f} | {v} | {len(g)} | {g.iters.iloc[0]} | {g.train_s.iloc[0]:.0f} | {g.peak_mb.iloc[0]:.0f} | "
        f"{ci((g.J - g.J_global_fixed).values)} | {ci((g.J - g.J_per_stream_tuned).values)} | {ci((g.J - g.J_ref_wald).values)} | "
        f"{g.first10.iloc[0]:.0f} -> {g.last10.iloc[0]:.0f} |"
    )
for v, g in d.groupby("variant"):
    lines.append(
        f"| ALL | {v} | {len(g)} | | | | {ci((g.J - g.J_global_fixed).values)} | {ci((g.J - g.J_per_stream_tuned).values)} | {ci((g.J - g.J_ref_wald).values)} | |"
    )
p = d.pivot_table(index=["fold", "stream"], columns="variant", values="J")
lines.append(f"\nstructured - generic: {ci((p.structured - p.generic).values)} (n={len(p)})")
txt = "\n".join(lines)
(OUT / "analysis_d3.md").write_text(txt, encoding="utf-8")
print(txt)
