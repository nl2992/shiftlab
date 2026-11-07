"""X3 gas arm (registered as IN-SAMPLE/DESCRIPTIVE: gas motivated the MAG hypothesis). Reuses the frozen D2 runner unchanged."""
import contextlib, io, json, runpy, sys
import numpy as np
ZIP, OUT = sys.argv[1], sys.argv[2]
sys.argv = ["d2", ZIP, "/tmp/claude-0/-home-user-shiftlab/8f9894d9-b4e7-539c-b88b-fffd7b544160/scratchpad/d2_rerun"]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("research/novelty_validation_2026-10-30/scripts/d2_gas_sensor_replay.py")
det, simB, EPS, ARMS, THR, DELTA_S, n_cal = ns["det"], ns["simB"], ns["EPS"], ns["ARMS"], ns["THR"], ns["DELTA_S"], ns["n_cal"]
r0b = det._SOURCE_CACHE["GAS"]["brier"][0]
u0b = r0b + np.sqrt(np.log(1 / DELTA_S) / (2 * n_cal))
T = simB["y"].shape[1]; rows = []
for frac in (0.05, 0.10, 0.20):
    ls = 6000 + int(frac * 1000)
    al = {}
    for name in ("C1_cost_disc_Kelly", "C2_cost_ONS", "H2c_guided_disc"):
        al[name] = det.first_cross(ARMS[name](simB, frac, ls, EPS), THR)
    det._SOURCE_CACHE["GAS"]["brier"] = (u0b, 0.0)      # MAG: guide centred at its own UCB
    al["MAG"] = det.first_cross(ARMS["H2c_guided_disc"](simB, frac, ls, EPS), THR)
    det._SOURCE_CACHE["GAS"]["brier"] = (r0b, 0.0)
    for k, a in al.items():
        rows.append(dict(frac=frac, arm=k, alarm_rate=float((a < T).mean()), median_alarm=float(np.median(a))))
    print(frac, {k: int(np.median(a)) for k, a in al.items()})
json.dump(dict(r0_brier=r0b, u0_brier=u0b, rows=rows), open(f"{OUT}/x3_gas_in_sample.json", "w"), indent=1)
