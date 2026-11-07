"""GAVE-R WP5 analysis: factorial contrasts, interaction, null UCBs.

Writes outputs/gaver/wp5/tables.md.  Sign convention: diff = candidate - reference in J/T, so a
negative diff favours the candidate; "rel. gain" = -diff / reference mean (positive = better).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src")]
OUT = ROOT / "outputs/gaver/wp5"
NB = 4000
DD, GD, DP, GP = "gaver:dss:dss", "gaver:gapmix:dss", "gaver:dss:pave", "gaver:gapmix:pave"
ED, EP = "gaver:env:dss", "gaver:env:pave"
ML, MP = "gaver:mlr:dss", "gaver:mlr:pave"  # post-hoc valid evidence reference
REFS = [DD, GD, DP, GP, ED, EP, ML, MP, "uniform", "episode_front"]
rng = np.random.default_rng(5)


def grade(gain, lo, hi):
    """gain = relative improvement (positive better); lo/hi = CI of the absolute diff (cand-ref)."""
    sig = hi < 0 or lo > 0
    if gain < 0:
        return "worse (CI excl. 0)" if sig else "worse (CI incl. 0)"
    if gain >= 0.10 and sig:
        return "substantial"
    if gain >= 0.03 and sig:
        return "meaningful"
    if gain >= 0.01:
        return "small" if sig else "small (CI incl. 0)"
    return "negligible"


def cp_ucb(k, n, conf=0.95):
    return 1.0 if k >= n else float(beta.ppf(conf, k + 1, n - k))


def boot_pool(diffs):
    """Equal-weight mean over cells; bootstrap over seeds within each cell."""
    pt = float(np.mean([d.mean() for d in diffs]))
    bs = np.zeros(NB)
    for d in diffs:
        idx = rng.integers(0, len(d), size=(NB, len(d)))
        bs += d[idx].mean(axis=1)
    bs /= len(diffs)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return pt, float(lo), float(hi)


def contrast(W, cells, f):
    pt, lo, hi = boot_pool([f(W.loc[c]).to_numpy() for c in cells])
    return pt, lo, hi


def f4(x):
    return f"{x:+.4f}"


def main():
    L = []
    alt = pd.read_csv(OUT / "alt/rows.csv")
    W = alt.pivot_table(index=["cell", "seed"], columns="arm", values="cost")
    cells = sorted(W.index.get_level_values(0).unique())
    n_seeds = alt.groupby("cell").seed.nunique()
    gate_on = [c for c in cells if (W.loc[c, DP] != W.loc[c, DD]).any()]
    gate_off = [c for c in cells if c not in gate_on]
    L.append(
        f"## Alternative cells: {len(cells)} cells, seeds/cell {n_seeds.min()}-{n_seeds.max()}"
    )
    L.append(f"gate-on cells ({len(gate_on)}): " + ", ".join(gate_on))
    L.append("")
    pairs = [
        ("Gap-Mix evidence alone (gapmix:dss vs dss:dss)", GD, DD),
        ("delay-gated PAVE alone (dss:pave vs dss:dss)", DP, DD),
        ("joint (gapmix:pave vs dss:dss)", GP, DD),
        ("joint vs Gap-Mix alone (gapmix:pave vs gapmix:dss)", GP, GD),
        ("joint vs PAVE alone (gapmix:pave vs dss:pave)", GP, DP),
        ("envelope evidence alone (env:dss vs dss:dss)", ED, DD),
        ("envelope + PAVE (env:pave vs dss:dss)", EP, DD),
        ("[post-hoc] mlr:dss vs dss:dss", ML, DD),
        ("[post-hoc] gapmix:dss vs mlr:dss", GD, ML),
        ("[post-hoc] gapmix:pave vs mlr:dss", GP, ML),
        ("[post-hoc] gapmix:pave vs mlr:pave", GP, MP),
        ("[post-hoc] mlr:pave vs mlr:dss", MP, ML),
        ("dss:dss vs uniform", DD, "uniform"),
        ("gapmix:pave vs uniform", GP, "uniform"),
        ("dss:dss vs episode_front", DD, "episode_front"),
        ("gapmix:pave vs episode_front", GP, "episode_front"),
    ]
    for sname, cs in {"all cells": cells, "gate-on": gate_on, "gate-off": gate_off}.items():
        if not cs:
            continue
        L += [
            f"### Pooled J/T contrasts, {sname} (n={len(cs)} cells); negative diff = candidate better",
            "",
            "| contrast | diff [95% CI] | rel. gain | grade |",
            "|---|---|---|---|",
        ]
        for nm, a, b in pairs:
            if a in W and b in W:
                pt, lo, hi = contrast(W, cs, lambda w, a=a, b=b: w[a] - w[b])
                ref = float(np.mean([W.loc[c, b].mean() for c in cs]))
                gain = -pt / ref
                L.append(
                    f"| {nm} | {f4(pt)} [{f4(lo)}, {f4(hi)}] | {gain * 100:+.1f}% | {grade(gain, lo, hi)} |"
                )
        L.append("")
        pe = contrast(W, cs, lambda w: w[DD] - w[GD])
        pa = contrast(W, cs, lambda w: w[DD] - w[DP])
        pj = contrast(W, cs, lambda w: w[DD] - w[GP])
        pi = contrast(W, cs, lambda w: w[GD] + w[DP] - w[DD] - w[GP])
        L.append(f"Gains (J/T reduction vs dss:dss), {sname}:")
        for nm, v in (("evidence", pe), ("acquisition", pa), ("joint", pj)):
            L.append(f"- {nm}: {f4(v[0])} [{f4(v[1])}, {f4(v[2])}]")
        L.append(
            f"- interaction = joint gain - (evidence gain + acquisition gain) "
            f"(= J_gd+J_dp-J_dd-J_gp; positive = synergy, negative = sub-additive): "
            f"{f4(pi[0])} [{f4(pi[1])}, {f4(pi[2])}]"
        )
        L.append("")
    cols = [a for a in REFS if a in W]
    L += ["### Per-cell J/T (mean over seeds)", "", "| cell | n | " + " | ".join(cols) + " |"]
    L.append("|---|---|" + "---|" * len(cols))
    for c in cells:
        L.append(
            f"| {c}{' (gate on)' if c in gate_on else ''} | {n_seeds[c]} | "
            + " | ".join(f"{W.loc[c, a].mean():.4f}" for a in cols)
            + " |"
        )
    L.append("")
    for nm, a, b in [
        ("gapmix:dss vs dss:dss", GD, DD),
        ("dss:pave vs dss:dss", DP, DD),
        ("gapmix:pave vs dss:dss", GP, DD),
        ("gapmix:pave vs episode_front", GP, "episode_front"),
        ("[post-hoc] gapmix:dss vs mlr:dss", GD, ML),
        ("[post-hoc] gapmix:pave vs mlr:dss", GP, ML),
    ]:
        if a not in W or b not in W:
            continue
        cnt: dict[str, int] = {}
        for c in cells:
            if a == DP and c in gate_off:
                continue
            lo, hi = boot_pool([(W.loc[c, a] - W.loc[c, b]).to_numpy()])[1:]
            g = grade(-(W.loc[c, a] - W.loc[c, b]).mean() / W.loc[c, b].mean(), lo, hi)
            cnt[g] = cnt.get(g, 0) + 1
        L.append(
            f"Per-cell grade counts, {nm}: "
            + ", ".join(f"{k}: {v}" for k, v in sorted(cnt.items()))
            + (" (gate-on cells only)" if a == DP else "")
        )
    L.append("")
    L += [
        "### Components, detection, labels (equal-weight mean over alt cells)",
        "",
        "| arm | J/T | loss | query cost | switch cost | queries | detect | mean delay |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in REFS:
        s = alt[alt.arm == a]
        if s.empty:
            continue
        g = s.groupby("cell")
        dl = pd.to_numeric(s.delay, errors="coerce")
        L.append(
            f"| {a} | {g.cost.mean().mean():.4f} | {g.loss.mean().mean():.4f} | "
            f"{g.query_cost.mean().mean():.4f} | {g.switch_cost.mean().mean():.4f} | "
            f"{g.queries.mean().mean():.1f} | {g.detect.mean().mean():.3f} | {dl.mean():.0f} |"
        )
    L.append("")
    for stage, title in (
        ("null", "Factorial null false promotion"),
        ("pavenull", "Step 0: PAVE null completion (raw PAVE, reserve off)"),
    ):
        p = OUT / stage / "rows.csv"
        if not p.exists() or p.stat().st_size < 200:
            continue
        nd = pd.read_csv(p)
        g = nd.groupby(["cell", "arm"]).fp.agg(["sum", "count"]).reset_index()
        g["ucb"] = [cp_ucb(k, n) for k, n in zip(g["sum"], g["count"], strict=True)]
        L += [f"## {title}", "", "k/n (Clopper-Pearson 95% one-sided UCB)", ""]
        arms = sorted(g.arm.unique())
        L += ["| cell | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
        for c in sorted(g.cell.unique(), key=lambda s: ("rho0.95" in s, s)):
            out = []
            for a in arms:
                r = g[(g.cell == c) & (g.arm == a)]
                out.append(
                    f"{int(r['sum'].iloc[0])}/{int(r['count'].iloc[0])} ({r.ucb.iloc[0]:.3f})"
                    if len(r)
                    else "-"
                )
            L.append(f"| {c} | " + " | ".join(out) + " |")
        L += [
            "",
            "| arm | worst UCB rho<=.8 | at cell | worst UCB rho=.95 | min n |",
            "|---|---|---|---|---|",
        ]
        for a in arms:
            s = g[g.arm == a]
            lo_, hi_ = s[~s.cell.str.contains("rho0.95")], s[s.cell.str.contains("rho0.95")]
            w = lo_.loc[lo_.ucb.idxmax()]
            hv = hi_.ucb.max() if len(hi_) else float("nan")
            L.append(f"| {a} | {w.ucb:.3f} | {w.cell} | {hv:.3f} | {int(s['count'].min())} |")
        L.append("")
        L.append(
            "Mean null J/T by arm: "
            + ", ".join(f"{a}: {nd[nd.arm == a].cost.mean():.4f}" for a in arms)
        )
        L.append("")
    (OUT / "tables.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
