"""S04 growth-aware querying vs variance/uniform/robust (preregistered). Expected budget unless stated; realised labels recorded."""

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St

PARENTS = {"pprm": {"risk": "brier"}, "HG": {"risk": "brier", "gamma": 0.99, "gate_w": 100}}
ARMS = {
    "uniform": {},
    "variance": {"alloc": "variance"},
    "growth": {"alloc": "growth"},
    "growth_oracle": {"alloc": "growth", "oracle_alt": True},
    "growth_harm": {"alloc": "growth_harm"},
    "growth_look": {"alloc": "growth_look"},
    "robust_mix": {"alloc": "mix", "mix": (0.5, 0.5, 0.0), "mix_mode": "conservative"},
    "budget_growth": {"alloc": "growth", "pacing": "growth_pace", "budget": None},
}
cfgs = {}
for pn, pk in PARENTS.items():
    for frac in (0.05, 0.10):
        for an, ak in ARMS.items():
            kw = dict(ak)
            if an == "budget_growth":
                kw["budget"] = round(frac * 2000)
            cfgs[f"{pn}|{an}|f{frac}"] = E.Cfg(frac=frac, **pk, **kw)
specs = (
    St.dev_worlds_g1()
    + P.g1_g2_extra()
    + [s for s in P.g3_specs() if "K3_cycle" in s.name]
    + [s for s in P.g4_specs() if "K3" in s.name]
)
print(len(cfgs), "configs", len(specs), "worlds", flush=True)
# delay 5 (default) ; delay-20 variant on the same worlds
df5 = St.run_grid("e3_s04_delay5", specs, cfgs, S=150, seed0=30000, qseed=3, note="S04 delay 5")
specs20 = [St.WorldSpec(s.name, s.make, 20, s.role_hint, s.group) for s in specs]
df20 = St.run_grid(
    "e3_s04_delay20", specs20, cfgs, S=150, seed0=30000, qseed=3, note="S04 delay 20"
)
for nm, df in (("delay5", df5), ("delay20", df20)):
    sm = St.summarise(df)
    sm.to_csv(f"outputs/gap_closure/e3_s04_{nm}/summary_by_world.csv", index=False)
    St.table(sm).to_csv(f"outputs/gap_closure/e3_s04_{nm}/summary_by_config.csv")
