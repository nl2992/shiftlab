"""E1: what does the validity repair (predictable sup cap, in-order release) cost HG? G1 dev pool, 200 seeds."""
import sys

import pandas as pd

from shiftlab.gap import engine as E
from shiftlab.gap import store as St

cfgs = {}
for frac in (0.10, 0.20):
    for cap in ("x", "sup"):
        kw = {"cap_mode": cap, "release": "legacy" if cap == "x" else "prefix", "unq_delay": cap == "x"}
        b = dict(risk="brier", frac=frac, **kw)
        cfgs[f"pprm_tight|{cap}|{frac}"] = E.Cfg(**b)
        cfgs[f"DK|{cap}|{frac}"] = E.Cfg(gamma=0.99, **b)
        cfgs[f"HG|{cap}|{frac}"] = E.Cfg(gamma=0.99, gate_w=100, **b)
        cfgs[f"cost_tight|{cap}|{frac}"] = E.Cfg(**{**b, "risk": "cost"})
specs = St.dev_worlds_g1()
df = St.run_grid("e1_repair_effect", specs, cfgs, S=200, seed0=1000, qseed=1, note="validity repair effect on dev pool")
sm = St.summarise(df)
t = St.table(sm)
pd.set_option("display.width", 200)
print(t.round(3).to_string())
sm.to_csv("outputs/gap_closure/e1_repair_effect/summary_by_world.csv", index=False)
t.to_csv("outputs/gap_closure/e1_repair_effect/summary_by_config.csv")
