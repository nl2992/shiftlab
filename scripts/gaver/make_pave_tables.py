"""Build markdown tables for docs/gaver/20_PAVE_RESULTS.md from outputs/gaver/wp2/*/rows.csv."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "gaver"))
from analyse_pave import boot_ci, cost_table, cp_upper

W = ROOT / "outputs/gaver/wp2"
REG = (
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1",
)
REFS = ["dss", "uniform", "undecided_only", "episode_front"]
R1, R0 = "pave:p1d1r1:k0.1:q0.03", "pave:p1d1r0:k0.1:q0.03"


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(out)


def fmt_ct(t: pd.DataFrame) -> pd.DataFrame:
    t = t.copy()
    t["PAVE cost"] = t.new_cost.map("{:.4f}".format)
    t["ref cost"] = t.ref_cost.map("{:.4f}".format)
    t["diff [95% CI]"] = [
        f"{a:+.4f} [{b:+.4f}, {c:+.4f}]" for a, b, c in zip(t["diff"], t.lo, t.hi, strict=True)
    ]
    t["rel gain"] = [f"{a:+.1%}" for a in t.rel_gain]
    return t[["cell", "ref", "n", "ref cost", "PAVE cost", "diff [95% CI]", "rel gain", "grade"]]


def main():
    out = []
    ev = pd.read_csv(W / "eval/rows.csv")
    ev2 = pd.read_csv(W / "eval2/rows.csv") if (W / "eval2/rows.csv").exists() else None
    for label, df, new in (
        ("PAVE-full (reserve on)", ev, R1),
        ("PAVE no-reserve (fresh seeds)", ev2, R0),
    ):
        if df is None:
            continue
        t = cost_table(df, new, REFS)
        out += [f"### Regression cells: {label}", "", md(fmt_ct(t[t.cell.isin(REG)])), ""]
        g = t.groupby("ref").grade.value_counts().unstack(fill_value=0)
        out += [
            f"### Grade counts over all {df.cell.nunique()} cells: {label}",
            "",
            md(g.reset_index()),
            "",
        ]
        mean = df.groupby("method").cost.mean().round(4).sort_values()
        out += [f"Mean cost/round over cells ({label}):", "", md(mean.reset_index()), ""]
        t.to_csv(W / f"table_{'r1' if new == R1 else 'r0'}.csv", index=False)
    ab = W / "ablate/rows.csv"
    if ab.exists():
        d = pd.read_csv(ab)
        d["arm"] = d.method.str.extract(r"pave:(p\dd\dr\d)")[0].fillna(d.method)
        full = d[d.arm == "p1d1r1"].set_index(["cell", "seed"]).cost
        rows = []
        for a in sorted(d.arm.unique()):
            x = d[d.arm == a].set_index(["cell", "seed"]).cost
            m, lo, hi = boot_ci(
                (x - d[d.arm == "uniform"].set_index(["cell", "seed"]).cost).to_numpy()
            )
            fm, flo, fhi = boot_ci((full - x).to_numpy()) if a != "p1d1r1" else (0, 0, 0)
            rows.append(
                {
                    "arm": a,
                    "mean cost": f"{x.mean():.4f}",
                    "minus uniform [95% CI]": f"{m:+.4f} [{lo:+.4f}, {hi:+.4f}]",
                    "full minus arm [95% CI]": "-"
                    if a == "p1d1r1"
                    else f"{fm:+.4f} [{flo:+.4f}, {fhi:+.4f}]",
                }
            )
        out += [
            "### Factorial ablation (pending, deadline, reserve; 7 cells x 60 seeds)",
            "",
            md(pd.DataFrame(rows)),
            "",
        ]
    for stage in ("null", "null2"):
        p = W / stage / "rows.csv"
        if not p.exists():
            continue
        n = pd.read_csv(p)
        g = n.groupby(["cell", "method"]).agg(n=("fp", "size"), k=("fp", "sum")).reset_index()
        g["FP rate"] = (g.k / g.n).round(4)
        g["CP 95% UCB"] = [
            round(cp_upper(int(k), int(m)), 4) for k, m in zip(g.k, g.n, strict=True)
        ]
        g["method"] = g.method.str.replace("pave:", "pave ")
        out += [f"### Null false promotion ({stage})", "", md(g), ""]
    (W / "tables.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
