# ruff: noqa: ISC004, B023  (closures are used within the same loop iteration)
"""C3 analysis for Gap-Mix+ (prereg 00_PREREG_GAPMIX_PLUS.md section 5). Reads eval rows only.

Writes docs/methods_recovery/20_GAPMIX_PLUS_RESULTS.md (tables + criteria + verdict). Numbers are
computed from outputs/methods_recovery/{alt,null}/rows.csv; nothing is typed by hand.
Sign: diff = candidate - reference in J/T; rel = -diff/reference mean (positive = candidate better).
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/methods_recovery"
NB = 4000
rng = np.random.default_rng(20261107)
A1, A2, A3, A4, A5, A4A = (
    "gaver:mlr:dss", "gaver:gapmix:dss", "gaver:gapmix:pave", "gmp:gapmix:plus",
    "gmp:gapmix:pace", "gmp:gapmix:frozen",
)  # fmt: skip
A01 = "gmp:mlr:plus"
EXTRA = ["gmp:qsg:dss", "thinned_hedged_gate", "episode_front", "uniform"]
COMP_POOL = [A1, A2, A3, A5, *EXTRA]
NAME = {A1: "Arm1 Markov-LR/DSS-acq", A2: "Arm2 Gap-Mix/DSS-acq", A3: "Arm3 Gap-Mix/PAVE", A4: "Arm4 Gap-Mix+",
        A5: "Arm5 Gap-Mix/fixed pacing", A4A: "Arm4a (evidence frozen)", A01: "Markov-LR+Gap-Mix+ governor",
        "gmp:qsg:dss": "QSG-envelope evidence", "thinned_hedged_gate": "gap-10 thinning",
        "episode_front": "episode_front", "uniform": "uniform"}  # fmt: skip


def cp_ucb(k, n, conf=0.95):
    return 1.0 if k >= n else float(beta.ppf(conf, k + 1, n - k))


def klass(cid: str) -> str:
    if "_rho0_" in cid:
        return "rho0"
    if "_d50_" in cid:
        return "d50"
    if re.search(r"_b0\.5_", cid):
        return "b0.5"
    return "target"


def fam(cid: str) -> str:
    return (
        "b" + re.search(r"_b([\d.]+)_", cid).group(1) + "_d" + re.search(r"_d(\d+)_", cid).group(1)
    )


def gate_on(cid: str) -> bool:
    b = float(re.search(r"_b([\d.]+)_", cid).group(1))
    d = int(re.search(r"_d(\d+)_", cid).group(1))
    return d >= 2000 / (round(b * 1000) + 2)


def pooled(W, cells, f_new, f_ref=None, nb=NB):
    """Equal-weight pooled diff (and relative gain) with bootstrap over seeds within cells."""
    new = [f_new(W.loc[c]).to_numpy() for c in cells]
    ref = [f_ref(W.loc[c]).to_numpy() for c in cells] if f_ref else None
    dn = np.zeros(nb)
    rf = np.zeros(nb)
    for i in range(len(cells)):
        n = len(new[i])
        idx = rng.integers(0, n, size=(nb, n))
        dn += new[i][idx].mean(axis=1)
        if ref is not None:
            rf += ref[i][idx].mean(axis=1)
    dn /= len(cells)
    rf /= len(cells)
    pt_n = float(np.mean([x.mean() for x in new]))
    if ref is None:
        lo, hi = np.percentile(dn, [2.5, 97.5])
        return pt_n, float(lo), float(hi), None
    pt_r = float(np.mean([x.mean() for x in ref]))
    diff = dn - rf
    rel = -diff / rf
    return (
        pt_n - pt_r, *np.percentile(diff, [2.5, 97.5]).tolist(),
        (-(pt_n - pt_r) / pt_r, *np.percentile(rel, [2.5, 97.5]).tolist()),
    )  # fmt: skip


def f4(x):
    return f"{x:+.4f}"


def pct(r):
    return f"{100 * r[0]:.2f}% [{100 * r[1]:.2f}, {100 * r[2]:.2f}]"


def main():
    alt = pd.read_csv(OUT / "alt/rows.csv")
    nul = pd.read_csv(OUT / "null/rows.csv")
    W = alt.pivot_table(index=["cell", "seed"], columns="arm", values="cost")
    # Arm 3 equals Arm 2 by construction where the PAVE gate is off (not run there)
    if A3 not in W:
        W[A3] = np.nan
    W[A3] = W[A3].fillna(W[A2])
    cells_all = sorted(W.index.get_level_values(0).unique())
    cls = {c: klass(c) for c in cells_all}
    target = [c for c in cells_all if cls[c] == "target"]
    nseed = alt.groupby("cell").seed.nunique()
    L = ["# Gap-Mix+ C3 development results", ""]
    L += [
        "Prereg: `00_PREREG_GAPMIX_PLUS.md` (commit 1fc3a300). Frozen config: "
        f"`configs/methods_recovery/gapmix_plus_frozen.json` sha256 `{hashlib.sha256((ROOT / 'configs/methods_recovery/gapmix_plus_frozen.json').read_bytes()).hexdigest()}`.",
        f"Eval seeds `gapmix_plus_eval` (101400000-101429999). Alt/neighbour cells: {len(cells_all)} cells "
        f"(target {len(target)}), seeds per cell {nseed.min()}-{nseed.max()}. Null: {nul.cell.nunique()} cells, "
        f"streams per cell {nul.groupby('cell').seed.nunique().min()}-{nul.groupby('cell').seed.nunique().max()}.",
        "Development evidence only. Effects are relative reductions of mean J/T (equal-weight over cells; paired bootstrap 95% CI over seeds within cell, 4000 resamples).",
        "",
    ]
    # ---------------- validity (null grid)
    nul = nul.copy()
    nul["k"] = 1
    cols = {}
    for arm in [A1, A2, A3, A4, A5, A4A, *EXTRA]:
        g = nul[nul.arm == arm].groupby("cell").agg(k=("fp", "sum"), n=("fp", "size"))
        cols[arm] = g
    # Arm 3 = Arm 2 where the gate is off
    g3 = cols[A3].reindex(cols[A2].index)
    cols[A3] = g3.fillna(cols[A2])
    ucb_tab, worst = [], {}
    for arm, g in cols.items():
        u = [cp_ucb(int(r.k), int(r.n)) for r in g.itertuples()]
        worst[arm] = max(u)
        ucb_tab.append((arm, worst[arm], g.index[int(np.argmax(u))], float(g.k.sum() / g.n.sum())))
    L += [
        "## 4. Validity: null grid (rho in {0,.5,.8} x B/T in {.05,.1,.25} x d in {1,10}), Clopper-Pearson 95% upper bound",
        "",
    ]
    L += [
        "| arm | worst UCB | at cell | pooled FP rate | valid (<= 0.1) |",
        "|---|---|---|---|---|",
    ]
    for arm, u, c, rate in ucb_tab:
        L.append(f"| {NAME[arm]} | {u:.3f} | {c} | {rate:.4f} | {'yes' if u <= 0.1 else 'NO'} |")
    L.append("")
    valid = {a for a in COMP_POOL if worst[a] <= 0.1}
    # ---------------- comparator choice
    fams = sorted({fam(c) for c in target})
    comp_of = {}
    for f in fams:
        cs = [c for c in target if fam(c) == f]
        means = {a: W.loc[cs, a].mean() for a in valid}
        comp_of[f] = min(means, key=means.get)
    L += [
        "## Comparator per cell family (strongest valid arm among Arms 1,2,3,5 + extras, lowest mean J on eval seeds)",
        "",
    ]
    L += ["| family (B/T, d) | comparator | its mean J/T | Arm 4 mean J/T |", "|---|---|---|---|"]
    for f in fams:
        cs = [c for c in target if fam(c) == f]
        L.append(
            f"| {f} | {NAME[comp_of[f]]} | {W.loc[cs, comp_of[f]].mean():.4f} | {W.loc[cs, A4].mean():.4f} |"
        )
    L.append("")

    def comp_series(c):
        return lambda df, a=comp_of: df[a[fam(c)]]

    def pool_vs_comp(cells, comp_map):
        new = [W.loc[c][A4].to_numpy() for c in cells]
        ref = [W.loc[c][comp_map[fam(c)]].to_numpy() for c in cells]
        dn, rf = np.zeros(NB), np.zeros(NB)
        for i in range(len(cells)):
            n = len(new[i])
            idx = rng.integers(0, n, size=(NB, n))
            dn += new[i][idx].mean(axis=1)
            rf += ref[i][idx].mean(axis=1)
        dn /= len(cells)
        rf /= len(cells)
        pn, pr = np.mean([x.mean() for x in new]), np.mean([x.mean() for x in ref])
        rel = -(dn - rf) / rf
        return (
            pn - pr,
            *np.percentile(dn - rf, [2.5, 97.5]).tolist(),
            (-(pn - pr) / pr, *np.percentile(rel, [2.5, 97.5]).tolist()),
        )

    # ---------------- criteria
    res = {}
    d1 = pool_vs_comp(target, comp_of)
    res[1] = d1[3][0] >= 0.03 and d1[3][1] > 0
    d2 = pooled(W, target, lambda w: w[A4], lambda w: w[A4A])
    res[2] = d2[2] < 0
    d3a = pooled(W, target, lambda w: w[A4], lambda w: w[A2])
    d3b = pooled(W, target, lambda w: w[A4], lambda w: w[A5])
    d3c = pooled(W, target, lambda w: w[A4], lambda w: w[A3])
    gon = [c for c in target if gate_on(c)]
    d3d = pooled(W, gon, lambda w: w[A4], lambda w: w[A3]) if gon else None
    res[3] = d3a[2] < 0 and d3b[2] < 0 and d3c[2] < 0 and (d3d is None or d3d[2] < 0)
    res[4] = all(worst[a] <= 0.1 for a in [A2, A3, A4, A5, A4A])
    neigh = {}
    for k in ("rho0", "d50", "b0.5"):
        cs = [c for c in cells_all if cls[c] == k]
        if not cs:
            continue
        valid_n = valid
        cm = {}
        for f in sorted({fam(c) for c in cs}):
            fc = [c for c in cs if fam(c) == f]
            means = {a: W.loc[fc, a].mean() for a in valid_n}
            cm[f] = min(means, key=means.get)
        neigh[k] = (pool_vs_comp(cs, cm), cm, len(cs))
    res[5] = all(
        v[0][3][2] > -0.03 for v in neigh.values()
    )  # CI lower bound of rel gain >= -3% (i.e. loss upper bound <= 3%)

    def row(label, r):
        rel = f" | {pct(r[3])}" if r[3] else " | -"
        return f"| {label} | {f4(r[0])} [{f4(r[1])}, {f4(r[2])}]{rel} |"

    L += ["## 5. C3 criteria", ""]
    L += [
        "| contrast (candidate minus reference, J/T) | diff [95% CI] | rel. gain [95% CI] |",
        "|---|---|---|",
    ]
    L.append(row("C1: Arm 4 vs strongest valid comparator, pooled target", d1))
    L.append(row("C2: Arm 4 vs Arm 4a, pooled target", (*d2[:3], None) if d2[3] is None else d2))
    L.append(row("C3a: Arm 4 vs Arm 2", d3a))
    L.append(row("C3b: Arm 4 vs Arm 5", d3b))
    L.append(row("C3c: Arm 4 vs Arm 3, pooled target", d3c))
    if d3d:
        L.append(row(f"C3d: Arm 4 vs Arm 3, gate-on subset ({len(gon)} cells)", d3d))
    for k, (r, cm, n) in neigh.items():
        L.append(row(f"C5: Arm 4 vs strongest valid comparator, neighbour `{k}` ({n} cells)", r))
    L.append("")
    L += [
        "| # | criterion | value | pass |",
        "|---|---|---|---|",
        f"| 1 | effect >= 3%, CI excludes 0 | {pct(d1[3])} | {res[1]} |",
        f"| 2 | attribution: Arm 4 < Arm 4a, CI excludes 0 | diff {f4(d2[0])} [{f4(d2[1])}, {f4(d2[2])}] | {res[2]} |",
        f"| 3 | beats Arm 2, Arm 5, Arm 3 (pooled and gate-on) | A2 {f4(d3a[2])}.. / A5 {f4(d3b[2])}.. / A3 {f4(d3c[2])}.. (CI upper bounds) | {res[3]} |",
        f"| 4 | null UCB <= 0.1 for Arms 2-5, 4a | worst {max(worst[a] for a in [A2, A3, A4, A5, A4A]):.3f} | {res[4]} |",
        "| 5 | neighbours: loss upper bound within 3% | "
        + "; ".join(f"{k}: worst-case loss {-100 * v[0][3][1]:.2f}%" for k, v in neigh.items())
        + f" | {res[5]} |",
        "",
    ]
    if all(res[i] for i in (1, 2, 3, 4, 5)):
        verdict = "PASS"
    elif all(res[i] for i in (1, 2, 3, 4)):
        bad = [k for k, v in neigh.items() if v[0][3][1] <= -0.03]
        verdict = f"PASS-narrow (failing neighbour: {', '.join(bad)})"
    else:
        verdict = (
            "FAIL (criteria failed: " + ", ".join(str(i) for i in (1, 2, 3, 4) if not res[i]) + ")"
        )
    L += [f"## Verdict: **{verdict}**", ""]
    # ---------------- interaction
    I = lambda w: (w[A1] - w[A4]) - ((w[A1] - w[A2]) + (w[A1] - w[A01]))
    zero = pd.Series(0.0)
    inter_t = pooled(W, target, I)
    L += [
        "## Interaction I = (J_00 - J_11) - [(J_00 - J_10) + (J_00 - J_01)]",
        "J_00 Markov-LR/existing acquisition, J_10 Gap-Mix/existing, J_01 Markov-LR/Gap-Mix+ governor (E_t from its own e-process, uniform alternative weights), J_11 Gap-Mix/Gap-Mix+. Positive = synergy.",
        "",
        f"Pooled target: I = {f4(inter_t[0])} [{f4(inter_t[1])}, {f4(inter_t[2])}]",
        "",
    ]
    del zero
    # ---------------- pooled contrasts vs every arm
    L += [
        "## Arm 4 vs every other arm (pooled target)",
        "",
        "| reference | ref mean J/T | diff [CI] | rel. gain [CI] |",
        "|---|---|---|---|",
    ]
    for a in [A1, A2, A3, A5, A4A, A01, *EXTRA]:
        r = pooled(W, target, lambda w: w[A4], lambda w, a=a: w[a])
        L.append(
            f"| {NAME[a]} | {W.loc[target, a].groupby('cell').mean().mean():.4f} | {f4(r[0])} [{f4(r[1])}, {f4(r[2])}] | {pct(r[3])} |"
        )
    L.append("")
    # ---------------- per-cell table
    sub = alt.copy()
    L += [
        "## Per-cell table (mean over seeds): J/T; detection rate; delay (rounds, detected only); queries; false-promotion rate",
        "",
    ]
    arms_show = [A1, A2, A3, A4, A5, A4A]
    L.append(
        "| cell | class | "
        + " | ".join(f"J {NAME[a].split()[0]}{a[-5:] if a in (A4A,) else ''}" for a in arms_show)
        + " | best comparator | Arm4 det | Arm2 det | Arm4 delay | Arm2 delay | Arm4 q | Arm2 q |"
    )
    L.append("|" + "---|" * (2 + len(arms_show) + 7))
    g = sub.groupby(["cell", "arm"]).agg(
        cost=("cost", "mean"),
        det=("detect", "mean"),
        delay=("delay", "mean"),
        q=("queries", "mean"),
        fp=("fp", "mean"),
    )
    for c in cells_all:

        def gv(a, k):
            if (c, a) in g.index:
                return g.loc[(c, a), k]
            return g.loc[(c, A2), k] if a == A3 else np.nan

        js = " | ".join(f"{gv(a, 'cost'):.4f}" for a in arms_show)
        best = min(valid, key=lambda a: gv(a, "cost"))
        L.append(
            f"| {c} | {cls[c]} | {js} | {NAME[best]} | {gv(A4, 'det'):.2f} | {gv(A2, 'det'):.2f} | {gv(A4, 'delay'):.0f} | {gv(A2, 'delay'):.0f} | {gv(A4, 'q'):.1f} | {gv(A2, 'q'):.1f} |"
        )
    L.append("")
    L += [
        "Pending-label inventory is not recorded in the rows (only queries and costs); not reported.",
        "",
    ]
    (ROOT / "docs/methods_recovery/20_GAPMIX_PLUS_RESULTS.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8"
    )
    print("verdict:", verdict)
    print({k: bool(v) for k, v in res.items()})


if __name__ == "__main__":
    sys.exit(main())
