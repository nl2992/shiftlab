"""S05: full simplex grid of uniform/variance/growth propensity mixtures x reliability mode. Parent HG, frac .10, delay 5."""

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St

cfgs = {"HG|uniform": E.Cfg(risk="brier", frac=0.10, gamma=0.99, gate_w=100)}
for u in (0, 0.10, 0.25, 0.50, 0.75, 1.0):
    for gsh in (0, 0.25, 0.50, 0.75, 1.0):
        if u + gsh > 1 + 1e-9:
            continue
        v = round(1 - u - gsh, 4)
        for mode in ("fixed", "adaptive", "conservative"):
            if mode == "conservative" and u >= 0.5:
                continue  # identical to fixed
            cfgs[f"HG|mix|u{u}|g{gsh}|v{v}|{mode}"] = E.Cfg(
                risk="brier",
                frac=0.10,
                gamma=0.99,
                gate_w=100,
                alloc="mix",
                mix=(u, v, gsh),
                mix_mode=mode,
            )
specs = [
    s
    for s in St.dev_worlds_g1()
    if any(
        k in s.name
        for k in (
            "concept|abrupt|2",
            "concept|gradual|2",
            "concept|transient|2",
            "concept|abrupt|1.5",
            "subgroup",
            "cov_benign|abrupt|3",
            "cov_inform|abrupt|2",
            "prior|abrupt|1",
            "none",
        )
    )
]
specs += P.g1_g2_extra() + [s for s in P.g3_specs() if "K3_cycle" in s.name]
print(len(cfgs), "configs", len(specs), "worlds", flush=True)
df = St.run_grid(
    "e4_s05_mixture", specs, cfgs, S=100, seed0=40000, qseed=4, note="S05 simplex grid"
)
sm = St.summarise(df)
sm.to_csv("outputs/gap_closure/e4_s05_mixture/summary_by_world.csv", index=False)
St.table(sm).to_csv("outputs/gap_closure/e4_s05_mixture/summary_by_config.csv")
