"""S03 proxy-failure sensitivity curves and label-fraction sweep (frac .01/.05/.10/.20)."""

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St

specs = [
    P.logit_sched_spec(f"S03|concept2|blend{s}", "concept", 2.0, proxy=f"blend{s}")
    for s in (0.0, 0.25, 0.5, 0.75, 1.0)
]
specs.append(P.logit_sched_spec("S03|null|blend1.0", "none", 0.0, proxy="blend1.0"))
specs.append(P.logit_sched_spec("S03|cov_benign3|blend1.0", "cov_benign", 3.0, proxy="blend1.0"))
cfgs = {}
for f in (0.01, 0.05, 0.10, 0.20):
    for pn, pk in (
        ("pprm", {"risk": "brier"}),
        ("HG", {"risk": "brier", "gamma": 0.99, "gate_w": 100}),
    ):
        cfgs[f"{pn}|parent|f{f}"] = E.Cfg(frac=f, **pk)
        cfgs[f"{pn}|soft_w128_none|f{f}"] = E.Cfg(
            frac=f, rel="soft", rel_window=128, rel_smooth=0.95, rel_fallback="none", **pk
        )
        cfgs[f"{pn}|hard_w64_uniform|f{f}"] = E.Cfg(
            frac=f, rel="hard", rel_window=64, rel_smooth=0.95, rel_fallback="uniform", **pk
        )
        cfgs[f"{pn}|unc_w128_uniform|f{f}"] = E.Cfg(
            frac=f, rel="unc", rel_window=128, rel_smooth=0.95, rel_fallback="uniform", **pk
        )
        cfgs[f"{pn}|theta0|f{f}"] = E.Cfg(
            frac=f, rel="soft", rel_window=10**9, rel_smooth=0.0, rel_fallback="uniform", **pk
        )  # placeholder, replaced below
df = St.run_grid(
    "e2b_s03_sensitivity",
    specs,
    {k: v for k, v in cfgs.items() if "theta0" not in k},
    S=200,
    seed0=21000,
    qseed=2,
    note="S03 sensitivity curves",
)
sm = St.summarise(df)
sm.to_csv("outputs/gap_closure/e2b_s03_sensitivity/summary_by_world.csv", index=False)
print(sm.pivot_table(index="config", columns="world", values="power").round(2).to_string())
