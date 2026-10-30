"""Follow-up to D2 (post-hoc, DIAGNOSTIC ONLY; no parameter is changed and nothing is re-tuned)."""
import json, sys, runpy
import numpy as np
ZIP, OUT = sys.argv[1], sys.argv[2]
sys.argv = ["d2", ZIP, OUT]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("research/novelty_validation_2026-10-30/scripts/d2_gas_sensor_replay.py")
det, simB, EPS, GAMMA, DELAY = ns["det"], ns["simB"], ns["EPS"], ns["GAMMA"], ns["DELAY"]
npz = np.load(f"{OUT}/d2_gas_sensor_per_seed_alarm_idx.npz")
rng = np.random.default_rng(0)
res = {"paired": [], "diag": {}}
T = simB["y"].shape[1]
for frac in (0.05, 0.10, 0.20):
    k = lambda a: npz[f"B_batches3to10_documented_order|{frac}|{EPS}|{a}"].astype(float)
    h, c1, c2 = k("H2c_guided_disc"), k("C1_cost_disc_Kelly"), k("C2_cost_ONS")
    better = c1 if c1.mean() <= c2.mean() else c2          # comparator chosen by realised mean (conservative for H2c's critics? favours comparator)
    for nm, ref in (("C1", c1), ("C2", c2), ("better_of_C1_C2", better)):
        d = h - ref
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(5000)]
        res["paired"].append(dict(frac=frac, vs=nm, mean_delay_diff_H2c_minus_ref=float(d.mean()),
                                  ci95=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))],
                                  frac_seeds_H2c_later=float((d > 0).mean())))
# mechanism: bets around the batch-6 onset (index 1944) for seed 0, frac .10
frac, lseed = 0.10, 6000 + int(0.10 * 1000)
xc, _, _, tc = det._pp_parts(simB, frac, lseed, "cost", None, None, EPS, uniform_cap=True)
xb, _, _, tb = det._pp_parts(simB, frac, lseed, "brier", None, None, 0.0, uniform_cap=True)
cap = 0.5
def disc(x):
    ones = np.ones_like(x)
    n = det.shift_time(det._ewm_cumsum(ones, GAMMA), DELAY + 1)
    m1 = det.shift_time(det._ewm_cumsum(x, GAMMA), DELAY + 1) / (n + 1)
    m2 = det.shift_time(det._ewm_cumsum(x**2, GAMMA), DELAY + 1) / (n + 1)
    return m1, m2
m1c, m2c = disc(xc); m1b, m2b = disc(xb)
hic, hib = cap / tc, cap / tb
lam_c1 = np.minimum(np.where(m2c > 0, np.maximum(m1c, 0) / np.maximum(m2c, 1e-12), 0), hic)
rel = np.minimum(np.where(m2b > 0, np.maximum(m1b, 0) / np.maximum(m2b, 1e-12), 0), hib) / hib
lam_h2c = rel * hic
rows = []
for t in (1900, 2000, 2200, 2500, 3000, 3500, 4000, 5000):
    rows.append(dict(t=t, cost_cap=float(hic[0, t]), lam_C1=float(lam_c1[0, t]), lam_H2c=float(lam_h2c[0, t]),
                     brier_rel_position=float(rel[0, t]), m1_cost=float(m1c[0, t]), m1_brier=float(m1b[0, t])))
res["diag"]["seed0_frac0.10_bets"] = rows
# mean bet ratio over seeds in the window of batch 6 (indices 1944..4244)
w = slice(1944, 4244)
res["diag"]["mean_lam_C1_batch6"] = float(lam_c1[:, w].mean()); res["diag"]["mean_lam_H2c_batch6"] = float(lam_h2c[:, w].mean())
res["diag"]["mean_cost_cap_hic"] = float(hic[:, w].mean()); res["diag"]["mean_brier_cap_hib"] = float(hib[:, w].mean())
json.dump(res, open(f"{OUT}/d2_followup_paired_and_diagnostic.json", "w"), indent=1)
for r in res["paired"]: print(r)
print(json.dumps(res["diag"], indent=0)[:1800])
