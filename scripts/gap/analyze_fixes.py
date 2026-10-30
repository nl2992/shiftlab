import pandas as pd

from shiftlab.gap.store import wilson

pd.set_option("display.width", 230)
sm = pd.read_csv("outputs/gap_closure/e14_fixes_dev2/summary_by_world.csv")
sm["parent"] = sm.config.str.split("|").str[0]
sm["variant"] = sm.config.str.split("|").str[1]
nul = sm[sm.world.str.contains("D2\\|null")]
dep = nul[nul.world.str.contains("ar|cluster|fin")]
iid_h = sm[sm.world.str.contains("D2\\|harm") & (sm.role == "harm")]
tr = sm[sm.world.str.contains("D2\\|trans") & (sm.role == "harm")]
nh = sm[(sm.role == "nonharm")]
res = []
for par in ("pprm", "HG", "cost"):
    for v in sorted(sm.variant.unique()):
        if v == "parent":
            continue

        def g(d, col, par=par, v=v):
            a = d[(d.parent == par) & (d.variant == v)].set_index("world")[col]
            b = d[(d.parent == par) & (d.variant == "parent")].set_index("world")[col]
            return a, b

        pa, pb = g(iid_h, "power")
        ta, tb = g(tr, "power")
        fa, fb = g(nh, "fa")
        da, db = g(dep, "fa")
        n = int(sm.n.iloc[0])
        res.append(
            {
                "parent": par,
                "variant": v,
                "d_power_iid_harm": (pa - pb).mean(),
                "d_power_transient": (ta - tb).mean(),
                "d_fa_nonharm": (fa - fb).mean(),
                "max_fa_dep_parent": db.max(),
                "max_fa_dep_fix": da.max(),
                "dep_fix_ci_hi": wilson(da.max() * n, n)[1],
                "max_fa_any_nonharm_fix": fa.max(),
            }
        )
r = pd.DataFrame(res)
print(r.round(3).to_string(index=False))
print("\nparent FA on dependence worlds")
print(
    dep[dep.variant == "parent"]
    .pivot_table(index="world", columns="parent", values="fa")
    .round(3)
    .to_string()
)
print("\nfix FA (lrv100) on dependence worlds")
print(
    dep[dep.variant == "F2_lrv100"]
    .pivot_table(index="world", columns="parent", values="fa")
    .round(3)
    .to_string()
)
print("\npower iid harm: parent vs fixes (mean)")
print(iid_h.pivot_table(index="variant", columns="parent", values="power").round(3).to_string())
print("\npower transient")
print(tr.pivot_table(index="variant", columns="parent", values="power").round(3).to_string())
r.to_csv("outputs/gap_closure/e14_fixes_dev2/fix_decisions.csv", index=False)
