"""C4-0 pilot analysis: per-stream episode-level deltas, pooled go/no-go, power."""

import sys

import numpy as np
import pandas as pd
from scipy import stats

ARM = "EQSDp_l0.9_g0.2"
COMPS = ("gongT_w100_m10", "qiu_delayed_movement")
DESC = (
    "EQSDp_l0.95_g0.2",
    "wald_l0.9_g0.2",
    "smarg_l0.9_k0.2",
    "dwell_l0.9_s5",
    "econF_mo5_m5",
    "CONTROL_never_switch",
)


def boot_ci(x, rng, n=2000):
    if len(x) < 2:
        return np.nan, np.nan
    m = rng.choice(x, (n, len(x))).mean(1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def main(path):
    d = pd.read_json(path, lines=True)
    ep = d.groupby(["stream", "ep", "policy"]).net.mean().unstack()  # seed-averaged per episode
    rng = np.random.default_rng(0)
    rows, sds = [], {}
    for s, g in ep.groupby(level=0):
        r = {"stream": s, "episodes": len(g), "J_B": g[ARM].mean()}
        for c in COMPS + DESC:
            x = (g[ARM] - g[c]).to_numpy()
            lo, hi = boot_ci(x, rng)
            r[f"d_{c}"] = x.mean()
            if c in COMPS:
                r[f"ci_{c}"] = f"[{lo:+.1f},{hi:+.1f}]"
                sds.setdefault(c, []).append(x.std(ddof=1) if len(x) > 1 else np.nan)
        rows.append(r)
    t = pd.DataFrame(rows).set_index("stream")
    pd.set_option("display.width", 300)
    show = ["episodes", "J_B"] + [f"{p}_{c}" for c in COMPS for p in ("d", "ci")]
    print(t[show].round(2).to_string())
    print(t[[f"d_{c}" for c in DESC]].round(2).to_string())
    big = t[t.episodes >= 5]
    go = True
    for c in COMPS:
        pooled = t[f"d_{c}"].mean()
        lo, hi = boot_ci(t[f"d_{c}"].to_numpy(), rng)
        frac = (big[f"d_{c}"] < 0).mean()
        sd = np.nanmedian(sds[c])
        need = (
            int(np.ceil(((stats.norm.ppf(0.95) + stats.norm.ppf(0.8)) * sd / abs(pooled)) ** 2))
            if pooled < 0
            else None
        )
        print(
            f"{c}: pooled stream-mean delta {pooled:+.2f} [stream boot {lo:+.2f},{hi:+.2f}]; "
            f"neg in {frac:.2f} of {len(big)} streams with >=5 eps; median per-episode SD {sd:.2f}; "
            f"episodes for 80% one-sided power at pooled effect: {need}"
        )
        go &= pooled < 0
    both_neg = ((big[f"d_{COMPS[0]}"] < 0) & (big[f"d_{COMPS[1]}"] < 0)).mean()
    print(f"share of >=5-episode streams negative vs BOTH: {both_neg:.2f}")
    go &= both_neg >= 0.5
    print("PILOT VERDICT:", "GO" if go else "NO-GO")


if __name__ == "__main__":
    main(sys.argv[1])
