"""R0: CRSP context heterogeneity and stability on development splits only (see REAL_DATA_PROTOCOL.md)."""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from shiftlab.dive.rpoq_crsp_replay import COHORT_SIZE, COLUMNS, N_COHORTS, SEED, _load_rows
from shiftlab.dive.rpoq_crsp_replay_b import build_cohort_b

panel = Path(sys.argv[1])
base = _load_rows(panel, None, ["permno", "split"])
permno_all, split_all = (
    base["permno"].to_numpy(),
    np.asarray(base["split"].to_pylist(), dtype=object),
)
chosen = np.random.default_rng(SEED).permutation(np.unique(permno_all[split_all == "train"]))[
    : N_COHORTS * COHORT_SIZE
]
table = _load_rows(panel, chosen, COLUMNS)
B = 8
stats = {}  # (split, ctx_def) -> arrays [cohort, bin, (n, sumY, sumR)]
for split in ("validation", "calibration"):
    for ci in range(N_COHORTS):
        c = build_cohort_b(
            table, chosen[ci * COHORT_SIZE : (ci + 1) * COHORT_SIZE], eval_split=split
        )
        if c is None:
            continue
        y, r = (
            -c["z"],
            (c["z"] - c["h"]) ** 2,
        )  # benefit of candidate over reference; residual vs proxy
        for name in ("ctx_size", "ctx_abs_return"):
            a = stats.setdefault((split, name), np.zeros((N_COHORTS, B, 3)))
            for b in range(B):
                m = c[name] == b
                a[ci, b] = (m.sum(), y[m].sum(), r[m].sum())
    print("done", split, flush=True)

rng = np.random.default_rng(4)
out = {}
for name in ("ctx_size", "ctx_abs_return"):
    v, cal = stats[("validation", name)], stats[("calibration", name)]

    def snr(a):
        t = a.sum(0)
        mu, r = t[:, 1] / np.maximum(t[:, 0], 1), t[:, 2] / np.maximum(t[:, 0], 1)
        return mu, mu**2 / r

    mu_v, snr_v = snr(v)
    mu_c, snr_c = snr(cal)
    top = int(np.argmax(snr_v))
    keep = [i for i in range(N_COHORTS) if v[i, :, 0].sum() > 0]
    boots = []
    for _ in range(2000):
        s = v[rng.choice(keep, len(keep))].sum(0)
        boots.append(s[top, 1] / max(s[top, 0], 1))
    lo, hi = np.quantile(boots, [0.025, 0.975])
    rho = spearmanr(snr_v, snr_c).statistic
    out[name] = {
        "val_mu": mu_v.tolist(),
        "val_snr": snr_v.tolist(),
        "cal_mu": mu_c.tolist(),
        "cal_snr": snr_c.tolist(),
        "top_bin": top,
        "top_to_median_snr_val": float(snr_v[top] / np.median(snr_v)),
        "top_bin_val_mu_ci": [float(lo), float(hi)],
        "top_bin_cal_mu": float(mu_c[top]),
        "spearman_val_cal_snr": float(rho),
        "heterogeneity": bool(snr_v[top] / np.median(snr_v) >= 3 and (lo > 0 or hi < 0)),
        "stable": bool(rho >= 0.5 and np.sign(mu_c[top]) == np.sign(mu_v[top])),
    }
    print(
        name,
        {
            k: (round(x, 4) if isinstance(x, float) else x)
            for k, x in out[name].items()
            if not isinstance(x, list)
        },
        flush=True,
    )
    print("  val mu (bps)", np.round(mu_v * 1e4, 2), "\n  cal mu (bps)", np.round(mu_c * 1e4, 2))
Path("outputs/rpoq_next/r0").mkdir(parents=True, exist_ok=True)
Path("outputs/rpoq_next/r0/results.json").write_text(json.dumps(out, indent=2))
