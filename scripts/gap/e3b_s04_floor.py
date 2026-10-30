"""S04 v2: same arms and worlds as e3 but with propensity floors frac/2 (v1 used frac/4, which throttles the bet cap 4x)."""
from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St

PARENTS = {"pprm": dict(risk="brier"), "HG": dict(risk="brier", gamma=0.99, gate_w=100)}
ARMS = {"uniform": {}, "variance": dict(alloc="variance"), "growth": dict(alloc="growth"), "growth_oracle": dict(alloc="growth", oracle_alt=True), "growth_harm": dict(alloc="growth_harm"), "growth_look": dict(alloc="growth_look"),
        "robust_mix": dict(alloc="mix", mix=(0.5, 0.5, 0.0), mix_mode="conservative")}
cfgs = {}
for pn, pk in PARENTS.items():
    for frac in (0.05, 0.10, 0.20):
        for an, ak in ARMS.items():
            kw = dict(ak)
            if an not in ("uniform", "robust_mix"):
                kw["qmin"] = frac / 2
            cfgs[f"{pn}|{an}|f{frac}"] = E.Cfg(frac=frac, **pk, **kw)
specs = St.dev_worlds_g1() + P.g1_g2_extra() + [s for s in P.g3_specs() if "K3_cycle" in s.name] + [s for s in P.g4_specs() if "K3" in s.name]
df = St.run_grid("e3b_s04_floor", specs, cfgs, S=150, seed0=30000, qseed=3, note="S04 v2 floors frac/2")
sm = St.summarise(df)
sm.to_csv("outputs/gap_closure/e3b_s04_floor/summary_by_world.csv", index=False)
St.table(sm).to_csv("outputs/gap_closure/e3b_s04_floor/summary_by_config.csv")
