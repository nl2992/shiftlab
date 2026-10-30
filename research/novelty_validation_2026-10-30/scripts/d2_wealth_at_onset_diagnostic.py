"""Diagnostic (post-hoc, descriptive): log-wealth of H2c vs cost-only Kelly at the batch-6 boundary on gas stream B."""
import io, contextlib, json, runpy, sys
import numpy as np
ZIP, OUT = sys.argv[1], sys.argv[2]
sys.argv = ["d2", ZIP, OUT]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("research/novelty_validation_2026-10-30/scripts/d2_gas_sensor_replay.py")
det, simB, EPS, GAMMA, DELAY, ARMS = ns["det"], ns["simB"], ns["EPS"], ns["GAMMA"], ns["DELAY"], ns["ARMS"]
res = {}
for frac in (0.05, 0.10, 0.20):
    ls = 6000 + int(frac * 1000)
    row = {}
    for name in ("C1_cost_disc_Kelly", "C2_cost_ONS", "H2c_guided_disc"):
        lw = ARMS[name](simB, frac, ls, EPS)
        row[name] = {"logw_at_1943_mean": float(lw[:, 1943].mean()), "logw_at_1943_min": float(lw[:, 1943].min()),
                     "logw_at_4243_mean": float(lw[:, 4243].mean())}
    res[str(frac)] = row
    print(frac, {k: {a: round(b, 2) for a, b in v.items()} for k, v in row.items()})
json.dump(res, open(f"{OUT}/d2_wealth_at_onset_diagnostic.json", "w"), indent=1)
