"""S08 balanced growth-aware sampling: rare-group shift with group imbalance, cost asymmetry, proxy quality."""

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St

R = P.W.Regime
specs = []
for thr, tag in ((0.5, "prev31"), (1.0, "prev16"), (1.5, "prev07")):
    for fn in (5.0, 15.0):
        for px in ("accurate", "calibration"):
            w = P.W.LogitWorld(
                regimes=(R(), R("subgroup", 8.0, fn)), t0=0, name="s08", sub_thr=thr, harm_thr=0.02
            )

            def make(S, seed, w=w, px=px):
                st = P._g_sched(w, "abrupt", S, seed, 800)
                return P.W.apply_proxy(st, px) if px != "accurate" else st

            specs.append(St.WorldSpec(f"S08|{tag}|fn{fn:g}|{px}", make, 5, group="S08"))
import numpy as np


def null_make(S, sd):
    return P.W.make_stream(
        P.W.LogitWorld(regimes=(R(),), t0=0), S, sd, z=np.zeros((S, 2000), dtype=int)
    )


specs.append(St.WorldSpec("S08|null|prev16", null_make, 5, group="S08"))
cfgs = {}
for frac in (0.05, 0.10):
    base = {"risk": "brier", "frac": frac, "gamma": 0.99, "gate_w": 100}
    for an, ak in {
        "uniform": {},
        "variance": {"alloc": "variance"},
        "balanced": {"alloc": "balanced"},
        "growth": {"alloc": "growth"},
        "bal_growth": {"alloc": "bal_growth"},
    }.items():
        cfgs[f"HG|{an}|f{frac}"] = E.Cfg(
            **base, **ak, **({"qmin": frac / 2} if an != "uniform" else {})
        )
df = St.run_grid("e10b_s08_balanced_floor", specs, cfgs, S=150, seed0=70000, qseed=7, note="S08")
sm = St.summarise(df)
sm.to_csv("outputs/gap_closure/e10b_s08_balanced_floor/summary_by_world.csv", index=False)
rare = (
    df.groupby(["config"])
    .apply(lambda d: d.labels_rare.sum() / d.labels.sum(), include_groups=False)
    .rename("rare_label_share")
)
print(
    sm[sm.role == "harm"]
    .groupby("config")
    .agg(power=("power", "mean"), harm_before=("harm_before", "mean"))
    .join(rare)
    .round(3)
    .to_string()
)
print(sm[sm.role == "nonharm"].groupby("config").fa.mean().round(3).to_string())
