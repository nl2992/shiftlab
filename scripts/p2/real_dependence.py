import glob
import os

import numpy as np


def stats(f):
    z = np.load(f)
    d = z["l0"].astype(float) - z["l1"].astype(float)
    out = []
    for e in d:
        idx = np.nonzero(e)[0]
        s = e[idx]
        if len(s) < 30:
            continue
        # lag-k autocorr on disagreement subsequence, and by event-gap
        r = [
            np.corrcoef(s[:-k], s[k:])[0, 1] if s[:-k].std() > 0 and s[k:].std() > 0 else np.nan
            for k in (1, 5, 20)
        ]
        out.append([len(s) / len(e), s.mean()] + r)
    o = np.array(out)
    return o.shape[0], np.nanmean(o, 0)


fs = sorted(glob.glob("../shiftlab-p2-nad-2026-11-09/data/sprint_fresh_losses/*.npz")) + sorted(
    glob.glob("data/c4_sealed/*.npz")
)
for f in fs:
    n, m = stats(f)
    print(
        f"{os.path.basename(f):28s} K={n:3d} disag={m[0]:.3f} mean_adv={m[1]:+.3f} ac1={m[2]:.2f} ac5={m[3]:.2f} ac20={m[4]:.2f}"
    )
