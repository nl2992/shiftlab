"""End-to-end runtime and peak memory per detector on 1000 streams x 2000 steps (single core, warm)."""

import resource
import time

import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

ARMS = {
    "parent": ("pprm_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
    "F2_gONS_hard200": ("pp_ons_gated", {"gate": "hard", "w": 200}),
    "F3_gONS_multi": ("pp_ons_gated", {"gate": "multi", "w_short": 30, "w_long": 200}),
    "F1_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "mixture8": ("pp_mixture", {}),
}
sim = g.simulate_g4(1000, 60000)
rows = []
for arm, (name, extra) in ARMS.items():
    det.DETECTORS[name](
        g.simulate_g4(20, 1), frac=0.1, delay=5, lseed=0, tol=0.0, **extra
    )  # warm-up
    t0 = time.perf_counter()
    det.DETECTORS[name](sim, frac=0.1, delay=5, lseed=0, tol=0.0, **extra)
    rows.append(
        {
            "arm": arm,
            "seconds": round(time.perf_counter() - t0, 2),
            "peak_rss_mb_so_far": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
        }
    )
df = pd.DataFrame(rows)
df.to_csv("outputs/hg_v2/runtime_profile.csv", index=False)
print(df.to_string(index=False))
