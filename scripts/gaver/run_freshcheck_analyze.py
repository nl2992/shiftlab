"""Aggregate WP3 records into CSV tables and a markdown fragment (paired bootstrap, Clopper-Pearson).

Usage: python scripts/gaver/run_freshcheck_analyze.py [--dir outputs/gaver/wp3]
Writes cell_summary.csv, contrasts.csv, rates.csv, tables.md next to records.jsonl.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from shiftlab.gaver import freshcheck as fc

KINDS_ALT = ("persistent", "reversal", "transient")
COMPARATORS = (
    "existing_promo_only",
    "existing_cusum",
    "existing_hysteresis",
    "paced_cusum",
    "paced_cost_threshold",
    "erb",
    "erb_a05",
    "two_phase",
)
ABL = (
    ("reuse_reserve", "fresh_reserve", "reuse old wealth vs fresh (both reserve)"),
    ("reuse_noreserve", "fresh_noreserve", "reuse old wealth vs fresh (both no reserve)"),
    ("fresh_noreserve", "fresh_reserve", "no reserve vs reserve (fresh)"),
    ("cusum_reserve", "paced_cusum", "reserve vs no reserve (CUSUM)"),
)


def load(d: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(d.glob("records*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows += json.loads(line)["rows"]
    df = pd.DataFrame(rows).drop_duplicates(["study", "cell", "seed", "method"])
    df["kind"] = df["cell"].str.split("_").str[0]
    return df


def wide(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    return df.pivot_table(index=["cell", "seed"], columns="method", values=metric)


def contrast(w: pd.DataFrame, a: str, b: str, rel_den: float | None = None):
    """Improvement of ``a`` over ``b`` = mean(b - a) (positive = a lower/better); CI + relative."""
    diff = (w[b] - w[a]).to_numpy()
    m, lo, hi = fc.paired_bootstrap(diff)
    den = float(w[b].mean()) if rel_den is None else rel_den
    if abs(den) < 1e-12:
        return m, lo, hi, float("nan"), float("nan"), float("nan"), "n/a"
    rel, rlo, rhi = m / den, lo / den, hi / den
    return m, lo, hi, rel, rlo, rhi, fc.grade(rel, rlo, rhi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="outputs/gaver/wp3")
    a = ap.parse_args()
    d = Path(a.dir)
    df = load(d)
    alt = df[df.study == "alt"]
    md = []

    # ---- per-cell means
    metrics = ["J", "loss", "qcost", "scost", "switches", "queries", "post_harm", "rb_delay"]
    cs = alt.groupby(["cell", "method"])[
        metrics + ["exposed", "censored", "promotions", "rollbacks"]
    ].mean()
    cs.to_csv(d / "cell_summary.csv")

    # ---- contrasts (pooled by kind and per cell)
    con = []
    for metric in ("J", "post_harm"):
        w_all = wide(alt, metric)
        for kind in KINDS_ALT:
            if metric == "post_harm" and kind == "persistent":
                continue
            idx = w_all.index[w_all.index.get_level_values("cell").str.startswith(kind)]
            wk = w_all.loc[idx]
            groups = [("ALL_" + kind, wk)] + [
                (c, wk.loc[c]) for c in sorted(set(wk.index.get_level_values("cell")))
            ]
            for gname, w in groups:
                for a_m, b_m in [("fresh_reserve", c) for c in COMPARATORS] + [
                    (x, y) for x, y, _ in ABL
                ]:
                    m, lo, hi, rel, rlo, rhi, g = contrast(w, a_m, b_m)
                    con.append(
                        {
                            "metric": metric,
                            "kind": kind,
                            "group": gname,
                            "a": a_m,
                            "b": b_m,
                            "n": len(w),
                            "mean_b": float(w[b_m].mean()),
                            "mean_a": float(w[a_m].mean()),
                            "gain": m,
                            "lo": lo,
                            "hi": hi,
                            "rel": rel,
                            "rel_lo": rlo,
                            "rel_hi": rhi,
                            "grade": g,
                        }
                    )
    con = pd.DataFrame(con)
    con.to_csv(d / "contrasts.csv", index=False)

    # ---- rates
    rates = []
    for study, col in (("null500", "fp"), ("persist500", "false_rb"), ("persist500", "fp")):
        sub = df[df.study == study]
        for (cell, method), g in sub.groupby(["cell", "method"]):
            k, n = int(g[col].sum()), len(g)
            r, lo, hi = fc.clopper_pearson(k, n)
            rates.append(
                {
                    "study": study,
                    "rate": col,
                    "cell": cell,
                    "method": method,
                    "k": k,
                    "n": n,
                    "p": r,
                    "lo": lo,
                    "up": hi,
                }
            )
        for method, g in sub.groupby("method"):
            k, n = int(g[col].sum()), len(g)
            r, lo, hi = fc.clopper_pearson(k, n)
            rates.append(
                {
                    "study": study,
                    "rate": col,
                    "cell": "POOLED",
                    "method": method,
                    "k": k,
                    "n": n,
                    "p": r,
                    "lo": lo,
                    "up": hi,
                }
            )
    rates = pd.DataFrame(rates)
    rates.to_csv(d / "rates.csv", index=False)

    def fmt(x, p=3):
        return f"{x:.{p}f}"

    # ---- markdown
    order = list(fc.METHODS)
    md.append("### Table A. Mean J/T by kind (pooled over onset x d, 4 cells x 60 seeds)\n")
    md.append("| method | persistent | reversal | transient |")
    md.append("|---|---|---|---|")
    for m in order:
        row = [fmt(alt[(alt.kind == k) & (alt.method == m)].J.mean()) for k in KINDS_ALT]
        md.append(f"| {m} | " + " | ".join(row) + " |")

    md.append("\n### Table B. Components (reversal and persistent), mean per stream\n")
    md.append(
        "| kind | method | loss/T | query cost/T | switch cost/T | switches | queries | post-reversal harm/T | rollback delay (rounds) | exposed at window end | censored |"
    )
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for k in ("reversal", "persistent", "transient"):
        for m in order:
            g = alt[(alt.kind == k) & (alt.method == m)]
            md.append(
                f"| {k} | {m} | {fmt(g.loss.mean())} | {fmt(g.qcost.mean(), 4)} | {fmt(g.scost.mean(), 4)} "
                f"| {fmt(g.switches.mean(), 2)} | {fmt(g.queries.mean(), 1)} | {fmt(g.post_harm.mean(), 4)} "
                f"| {fmt(g.rb_delay.mean(), 1) if k != 'persistent' else '-'} "
                f"| {fmt(g.exposed.mean(), 2) if k != 'persistent' else '-'} "
                f"| {fmt(g.censored.mean(), 2) if k != 'persistent' else '-'} |"
            )

    def contrast_table(metric, kind, title, a_list):
        md.append(f"\n### {title}\n")
        md.append(
            "Gain = mean(comparator - FreshCheck); positive favours the first-named method. Relative = gain / comparator mean.\n"
        )
        md.append(
            "| first (a) | comparator (b) | mean b | mean a | gain [95% CI] | relative [95% CI] | grade |"
        )
        md.append("|---|---|---|---|---|---|---|")
        sub = con[(con.metric == metric) & (con.kind == kind) & (con.group == "ALL_" + kind)]
        for _, r in sub.iterrows():
            md.append(
                f"| {r.a} | {r.b} | {fmt(r.mean_b, 4)} | {fmt(r.mean_a, 4)} | {fmt(r.gain, 4)} [{fmt(r.lo, 4)}, {fmt(r.hi, 4)}] "
                f"| {fmt(100 * r.rel, 1)}% [{fmt(100 * r.rel_lo, 1)}, {fmt(100 * r.rel_hi, 1)}] | {r.grade} |"
            )

    contrast_table("J", "reversal", "Table C1. J/T, reversal (pooled)", None)
    contrast_table(
        "post_harm",
        "reversal",
        "Table C2. Post-reversal harm/T before rollback, reversal (pooled)",
        None,
    )
    contrast_table("J", "persistent", "Table C3. J/T, persistent (value lost if gain < 0)", None)
    contrast_table("J", "transient", "Table C4. J/T, transient (pooled)", None)

    md.append("\n### Table D. Per-cell J/T gain of fresh_reserve over existing_cusum\n")
    md.append("| cell | mean existing_cusum | mean fresh_reserve | gain [95% CI] | grade |")
    md.append("|---|---|---|---|---|")
    sub = con[
        (con.metric == "J")
        & (con.a == "fresh_reserve")
        & (con.b == "existing_cusum")
        & (~con.group.str.startswith("ALL_"))
    ]
    for _, r in sub.iterrows():
        md.append(
            f"| {r.group} | {fmt(r.mean_b)} | {fmt(r.mean_a)} | {fmt(r.gain, 4)} [{fmt(r.lo, 4)}, {fmt(r.hi, 4)}] | {r.grade} |"
        )

    md.append(
        "\n### Table E. False-promotion rate in boundary-null streams (500 per d; Clopper-Pearson 95% two-sided)\n"
    )
    md.append("| method | d=1: k/n (upper) | d=10: k/n (upper) | pooled 1000: rate (upper) |")
    md.append("|---|---|---|---|")
    nr = rates[(rates.study == "null500") & (rates.rate == "fp")]
    for m in order:
        cells = []
        for dd in (1, 10):
            r = nr[(nr.method == m) & (nr.cell.str.startswith(f"null_d{dd}_"))].iloc[0]
            cells.append(f"{r.k}/{r.n} ({fmt(r.up)})")
        r = nr[(nr.method == m) & (nr.cell == "POOLED")].iloc[0]
        md.append(f"| {m} | {cells[0]} | {cells[1]} | {fmt(r.p)} ({fmt(r.up)}) |")

    md.append(
        "\n### Table F. False-rollback rate in persistent streams (500 per cell; rollback while challenger truly better by the hurdle)\n"
    )
    md.append(
        "| method | "
        + " | ".join(sorted(rates[(rates.study == "persist500")].cell.unique()))
        + " |"
    )
    pcells = sorted(c for c in rates[(rates.study == "persist500")].cell.unique())
    md[-1] = "| method | " + " | ".join(pcells) + " |"
    md.append("|---|" + "---|" * len(pcells))
    fr = rates[(rates.study == "persist500") & (rates.rate == "false_rb")]
    for m in order:
        row = []
        for c in pcells:
            r = fr[(fr.method == m) & (fr.cell == c)].iloc[0]
            row.append(
                f"{r.k}/{r.n} ({fmt(r.up)})" if c != "POOLED" else f"{fmt(r.p)} ({fmt(r.up)})"
            )
        md.append(f"| {m} | " + " | ".join(row) + " |")

    md.append("\n### Table G. Ablations: J/T and post-reversal harm gain (pooled over kind)\n")
    md.append("| metric | kind | a | b | gain [95% CI] | relative | grade |")
    md.append("|---|---|---|---|---|---|---|")
    for metric, kinds in (("J", KINDS_ALT), ("post_harm", ("reversal", "transient"))):
        for kind in kinds:
            sub = con[(con.metric == metric) & (con.kind == kind) & (con.group == "ALL_" + kind)]
            for x, y, _ in ABL:
                r = sub[(sub.a == x) & (sub.b == y)].iloc[0]
                md.append(
                    f"| {metric} | {kind} | {x} | {y} | {fmt(r.gain, 4)} [{fmt(r.lo, 4)}, {fmt(r.hi, 4)}] "
                    f"| {fmt(100 * r.rel, 1)}% | {r.grade} |"
                )

    kn = df[df.study == "keepnull500"] if "keepnull500" in set(df.study) else None
    if kn is not None and len(kn):
        md.append(
            "\n### Table H. Keep-null streams (benefit >= h throughout; 500 per d): "
            "rollback among promoted streams\n"
        )
        md.append(
            "Statistic trigger = the rollback statistic fired while deployed (no economic gate); "
            "realised = the method actually rolled back. Clopper-Pearson, d pooled.\n"
        )
        md.append(
            "| method | promoted | statistic trigger k (rate, upper) | realised false rollback k (rate, upper) |"
        )
        md.append("|---|---|---|---|")
        for m in order:
            g = kn[(kn.method == m) & (kn.any_promo == 1)]
            n = len(g)
            if n == 0:
                continue
            kt, kr = int(g.stat_trigger.sum()), int(g.false_rb.sum())
            rt, rr = fc.clopper_pearson(kt, n), fc.clopper_pearson(kr, n)
            trig = (
                f"{kt}/{n} ({fmt(rt[0])}, {fmt(rt[2])})"
                if m.startswith(("fresh", "reuse", "paced_cusum", "cusum", "existing_cusum", "erb"))
                else "n/a"
            )
            md.append(f"| {m} | {n} | {trig} | {kr}/{n} ({fmt(rr[0])}, {fmt(rr[2])}) |")
    (d / "tables.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote", d / "tables.md")


if __name__ == "__main__":
    main()
