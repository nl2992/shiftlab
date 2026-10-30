"""Apply the frozen A3 decision rules (docs/rpoq_next/SYNTHETIC_PROTOCOL_A3.md) to the saved results."""

import json
import sys

import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else "outputs/rpoq_next/screen_a3/results.json"
d = json.load(open(path))["results"]
rng = np.random.default_rng(17)


def ci(a):
    a = np.asarray(a, float)
    b = a[rng.integers(0, len(a), (2000, len(a)))].mean(1)
    return a.mean(), np.quantile(b, 0.025), np.quantile(b, 0.975)


def best(key, arm):
    return max((np.array(d[key][f"{arm}+{b}"]["crossed"]) for b in ("ctx", "common")), key=lambda x: x.mean())


rows = {}
for key in d:
    base_arms = ("uniform", "neyman", "rasi", "random_conc")
    base = max((best(key, a) for a in base_arms), key=lambda x: x.mean())
    delta = best(key, "growth_fixed") - base
    rows[key] = ci(delta)
    nulls = max(v["power"] for v in d[key].values()) if key.startswith("null") else None
    spent = max(v["mean_spent"] for v in d[key].values())
    print(f"{key:20s} delta={rows[key][0]:+.3f} [{rows[key][1]:+.3f}, {rows[key][2]:+.3f}]"
          f"  best-baseline power={base.mean():.3f}  growth_fixed(best)={best(key,'growth_fixed').mean():.3f}"
          f"  max spend={spent:.0f}" + (f"  MAX NULL CROSSING={nulls:.3f}" if nulls is not None else ""))
