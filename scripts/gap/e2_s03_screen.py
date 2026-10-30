"""S03 stage 1 (preregistered in docs/sota_gap_closure/02_*): all 108 reliability combos x 2 parents at frac 0.10, G5 dev pool."""

import itertools

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St

cfgs = {}
PARENTS = {"pprm": {"risk": "brier"}, "HG": {"risk": "brier", "gamma": 0.99, "gate_w": 100}}
for pn, pk in PARENTS.items():
    cfgs[f"{pn}|parent"] = E.Cfg(frac=0.10, **pk)
    for win, sm, fb, gate in itertools.product(
        (32, 64, 128, 256),
        (0.90, 0.95, 0.99),
        ("none", "uniform", "conservative_bet"),
        ("hard", "soft", "unc"),
    ):
        cfgs[f"{pn}|S03|w{win}|s{sm}|{fb}|{gate}"] = E.Cfg(
            frac=0.10, rel=gate, rel_window=win, rel_smooth=sm, rel_fallback=fb, **pk
        )
print(len(cfgs), "configs", flush=True)
df = St.run_grid(
    "e2_s03_screen",
    P.g5_pool(),
    cfgs,
    S=100,
    seed0=20000,
    qseed=2,
    note="S03 stage 1 screen, frac 0.10",
)
sm = St.summarise(df)
sm.to_csv("outputs/gap_closure/e2_s03_screen/summary_by_world.csv", index=False)
St.table(sm).to_csv("outputs/gap_closure/e2_s03_screen/summary_by_config.csv")
print("done", len(df))
