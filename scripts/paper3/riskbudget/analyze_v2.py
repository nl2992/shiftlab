"""Summaries and tables for the F3 v2 dev run: ``python analyze_v2.py [--tag dev_v2]``.

Writes results/riskbudget/{dev_v2_summary.json, dev_v2_tables.md, frontier_v2.csv}.
"""

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np

from shiftlab.paper3.joint.harness import paired_delta
from shiftlab.paper3.riskbudget.harness import load_results, stress_ids

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "paper3" / "riskbudget"
RES = ROOT / "papers" / "paper3_cost_aware_adaptation" / "2026_programme" / "results" / "riskbudget"
EPS = 1e-9
RGRID = (8, 10, 12, 15, 20, 30, 45)
DELTA = 0.05


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (float(max(0.0, c - h)), float(min(1.0, c + h)))


def nm(x):
    return float(np.nanmean(x)) if np.any(~np.isnan(x)) else None


def stats(A, i, idx, R):
    sh = A["sup_harm"][i][idx]
    d = {
        "J": float(A["J"][i][idx].mean()),
        "sup_mean": float(sh.mean()),
        "sup_q95": float(np.quantile(sh, 0.95)),
        "sup_q99": float(np.quantile(sh, 0.99)),
        "sup_max": float(sh.max()),
        "labels": float(A["n_queries"][i][idx].mean()),
        "switches": float(A["n_switches"][i][idx].mean()),
        "frac_deployed": float(A["frac_time_deployed"][i][idx].mean()),
        "forced_rollbacks": nm(A["n_forced_rollbacks"][i][idx]),
        "vetoed": nm(A["n_vetoed_promotions"][i][idx]),
        "ride_out_rate": nm(A["rode_out"][i][idx]),
        "n_blind": nm(A["n_blind"][i][idx]),
        "n_sampled": nm(A["n_sampled"][i][idx]),
        "mean_pi": nm(A["mean_pi"][i][idx]),
        "exceed": {str(r): float((sh > r + EPS).mean()) for r in RGRID},
    }
    if R is not None:
        v = sh > R + EPS
        d["violation"] = float(v.mean())
        d["violation_wilson"] = wilson(int(v.sum()), v.size)
    return d


def dstat(JA, JB, idx, n_boot=2000):
    d = paired_delta(JA[idx], JB[idx], n_boot=n_boot)
    return {k: d[k] for k in ("delta", "lo", "hi", "rel_pct", "base")}, d["per_regime"]


def analyze(tag):
    arms, rids, seeds, A = load_results(OUT / tag)
    specs = {a["name"]: a for a in json.loads((OUT / tag / "_arms.spec").read_text())}
    budget = {n: float(s["R"]) for n, s in specs.items() if s["type"] in ("stoploss", "f3", "f3v2")}
    ix = {n: i for i, n in enumerate(arms)}
    st = set(stress_ids())
    pools = {
        "all": list(range(len(rids))),
        "orig": [i for i, r in enumerate(rids) if r not in st],
        "stress": [i for i, r in enumerate(rids) if r in st],
    }
    J = A["J"]
    S = {
        "meta": {
            "tag": tag,
            "n_seeds": len(seeds),
            "seed_first": seeds[0],
            "seed_last": seeds[-1],
            "regimes": rids,
            "arms": arms,
            "budget": budget,
            "specs": specs,
            "note": "pooled = equal weight over regimes; sup_harm quantiles of the pooled mixture;"
            " delta CIs = seed-cluster bootstrap (joint.paired_delta); negative = better",
        },
        "arms": {},
    }
    for n in arms:
        i, R = ix[n], budget.get(n)
        e = {"pooled": {}, "per_regime": {}, "delta": {}}
        for pn, idx in pools.items():
            p = stats(A, i, idx, R)
            if R is not None:
                rates = [(A["sup_harm"][i][j] > R + EPS).mean() for j in idx]
                p["violation_regime_mean"] = float(np.mean(rates))
                p["worst_regime"] = rids[int(idx[int(np.argmax(rates))])]
                p["worst_regime_violation"] = float(max(rates))
            q95s = [np.quantile(A["sup_harm"][i][j], 0.95) for j in idx]
            p["worst_regime_q95"] = float(max(q95s))
            e["pooled"][pn] = p
        for j, r in enumerate(rids):
            e["per_regime"][r] = stats(A, i, [j], R)
            if R is not None:
                k = int((A["sup_harm"][i][j] > R + EPS).sum())
                e["per_regime"][r]["violation_count"] = k
        for bn in ("wald_cut", "never"):
            e["delta"][bn] = {}
            for pn, idx in pools.items():
                d, per = dstat(J[i], J[ix[bn]], idx, 2000 if pn == "all" else 1000)
                e["delta"][bn][pn] = d
                if pn == "all":
                    e["delta"][bn]["per_regime"] = {
                        r: dict(zip(("delta", "lo", "hi", "rel_pct"), per[j], strict=True))
                        for j, r in enumerate(rids)
                    }
        S["arms"][n] = e

    # ---- paired comparisons of v2 against v1 and the tuned-v1
    S["compare"] = {}
    for R in (12, 20):
        for a, b in (
            (f"f3v2_R{R}", f"f3_pi1_R{R}"),
            (f"f3v2_R{R}", f"f3v1t_R{R}"),
            (f"f3v2_R{R}", f"f3v2d_R{R}"),
            (f"f3v2_R{R}", "wald_cut"),
        ):
            if a in ix and b in ix:
                c = {}
                for pn, idx in pools.items():
                    d, per = dstat(J[ix[a]], J[ix[b]], idx, 2000 if pn == "all" else 1000)
                    c[pn] = d
                    if pn == "all":
                        c["per_regime"] = {
                            r: dict(zip(("delta", "lo", "hi", "rel_pct"), per[j], strict=True))
                            for j, r in enumerate(rids)
                        }
                        c["n_better"] = sum(1 for p in per if p[2] < 0)
                        c["n_worse"] = sum(1 for p in per if p[1] > 0)
                S["compare"][f"{a} vs {b}"] = c
    for R in RGRID:
        a = f"f3v2_R{R}"
        c = {}
        for pn, idx in pools.items():
            d, per = dstat(J[ix[a]], J[ix["wald_cut"]], idx, 1000)
            c[pn] = d
            if pn == "all":
                c["n_better"] = sum(1 for p in per if p[2] < 0)
                c["n_worse"] = sum(1 for p in per if p[1] > 0)
        S["compare"][f"{a} vs wald_cut [R sweep]"] = c

    # ---- sanity
    san = {
        "deterministic_violations": [],
        "sampled_arm_pi1only_violations": [],
        "flagged_regimes": [],
    }
    for n, R in budget.items():
        i = ix[n]
        if specs[n]["type"] == "f3":  # v1 shield with delta 0: deterministic
            for j, r in enumerate(rids):
                for b in np.flatnonzero(A["sup_harm"][i][j] > R + EPS):
                    san["deterministic_violations"].append(
                        {
                            "arm": n,
                            "regime": r,
                            "seed": seeds[b],
                            "sup_harm": float(A["sup_harm"][i][j][b]),
                        }
                    )
        if specs[n]["type"] == "f3v2":
            ns = A["n_sampled"][i]
            det = ns == 0  # no pi<1 round: guarantee is pathwise
            bad = det & (A["sup_harm"][i] > R + EPS)
            san.setdefault("n_pi1only_runs", {})[n] = int(det.sum())
            for j, b in zip(*np.nonzero(bad), strict=True):
                san["sampled_arm_pi1only_violations"].append(
                    {
                        "arm": n,
                        "regime": rids[j],
                        "seed": seeds[b],
                        "sup_harm": float(A["sup_harm"][i][j][b]),
                    }
                )
            for j, r in enumerate(rids):
                k = int((A["sup_harm"][i][j] > R + EPS).sum())
                lo, hi = wilson(k, len(seeds))
                if lo > DELTA:
                    san["flagged_regimes"].append(
                        {
                            "arm": n,
                            "regime": r,
                            "violations": k,
                            "rate": k / len(seeds),
                            "wilson": (lo, hi),
                        }
                    )
    san["never_sup_harm_max"] = float(A["sup_harm"][ix["never"]].max())
    for n in ("never", "wald_cut"):
        san[f"{n}_J_all30"] = S["arms"][n]["pooled"]["all"]["J"]
        san[f"{n}_J_orig24"] = S["arms"][n]["pooled"]["orig"]["J"]
    san["I_max_over_R_max"] = {
        n: float(np.nanmax(A["I_max"][ix[n]]) / budget[n])
        for n in budget
        if specs[n]["type"] in ("f3", "f3v2")
    }
    S["sanity"] = san

    # ---- dominance: does some F3 v2 arm have <= pooled J and <= pooled q99 sup_harm?
    f3v2_arms = [n for n in arms if n.startswith("f3v2")]
    dom = {}
    for b in arms:
        if b in f3v2_arms:
            continue
        pb = S["arms"][b]["pooled"]["all"]
        wins = []
        for a in f3v2_arms:
            pa = S["arms"][a]["pooled"]["all"]
            if pa["J"] <= pb["J"] + 1e-12 and pa["sup_q99"] <= pb["sup_q99"] + 1e-12:
                wins.append(a)
        wins_strict = [
            a
            for a in wins
            if S["arms"][a]["pooled"]["all"]["J"] < pb["J"]
            and S["arms"][a]["pooled"]["all"]["sup_q99"] < pb["sup_q99"]
        ]
        dom[b] = {
            "J": pb["J"],
            "q99": pb["sup_q99"],
            "dominated_by": wins,
            "strictly_dominated_by": wins_strict,
        }
    S["dominance"] = dom
    return S, arms, rids


# ----------------------------------------------------------------------------------- tables
def f(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


def md(rows, header):
    s = "| " + " | ".join(header) + " |\n|" + "|".join(["---"] * len(header)) + "|\n"
    for r in rows:
        s += "| " + " | ".join(str(c) for c in r) + " |\n"
    return s + "\n"


def ci(d):
    return f"{d['delta']:+.2f} [{d['lo']:+.2f},{d['hi']:+.2f}]"


def tables(S, rids):
    arms, A, budget = S["meta"]["arms"], S["arms"], S["meta"]["budget"]
    t = [
        (
            f"# F3 v2 dev tables ({S['meta']['tag']}, {S['meta']['n_seeds']} seeds from "
            f"{S['meta']['seed_first']}, {len(rids)} regimes)\n\nDev seed block only. Pooled = equal "
            "weight over regimes. dJ negative = better than the reference.\n\n"
        )
    ]
    rows = []
    for n in arms:
        a, p = A[n], A[n]["pooled"]["all"]
        viol = (
            f"{pct(p['violation_regime_mean'])} / {pct(p['worst_regime_violation'])}"
            if n in budget
            else "-"
        )
        rows.append(
            [
                n,
                f(p["J"]),
                f(a["pooled"]["orig"]["J"]),
                f(a["pooled"]["stress"]["J"]),
                ci(a["delta"]["wald_cut"]["all"]),
                ci(a["delta"]["wald_cut"]["orig"]),
                ci(a["delta"]["wald_cut"]["stress"]),
                ci(a["delta"]["never"]["all"]),
                f(p["sup_q95"]),
                f(p["sup_q99"]),
                f(p["sup_max"], 0),
                viol,
                f(p["labels"], 1),
                f(p["frac_deployed"]),
                f(p["forced_rollbacks"]),
                f(p["n_blind"], 1),
                f(p["n_sampled"], 1),
                f(p["mean_pi"], 2),
            ]
        )
    t.append(
        "## (a) Pooled table\n\nviol = mean-over-regimes violation / worst-regime violation.\n\n"
    )
    t.append(
        md(
            rows,
            [
                "arm",
                "J all30",
                "J orig24",
                "J stress6",
                "dJ vs wald_cut (all)",
                "(orig24)",
                "(stress6)",
                "dJ vs never (all)",
                "q95",
                "q99",
                "max",
                "viol pooled/worst",
                "labels",
                "frac dep",
                "forced RB",
                "blind",
                "sampled",
                "mean pi",
            ],
        )
    )
    # (b) violation with Wilson per budget arm
    rows = []
    for n in budget:
        p = A[n]["pooled"]["all"]
        lo, hi = p["violation_wilson"]
        rows.append(
            [
                n,
                pct(p["violation"]),
                f"[{pct(lo)},{pct(hi)}]",
                pct(p["worst_regime_violation"]),
                p["worst_regime"],
            ]
        )
    t.append("## (b) Violation rate P(sup_harm > R), pooled over all 30 regimes x seeds\n\n")
    t.append(md(rows, ["arm", "violation", "Wilson 95%", "worst regime rate", "worst regime"]))
    # (c) baseline exceedance
    rows = []
    for n in arms:
        if n in budget:
            continue
        p = A[n]["pooled"]["all"]
        rows.append([n] + [pct(p["exceed"][str(r)]) for r in (8, 12, 20, 30, 45)])
    t.append("## (c) Exceedance P(sup_harm > R) of arms with no budget\n\n")
    t.append(md(rows, ["arm", "R=8", "R=12", "R=20", "R=30", "R=45"]))
    # (d) per-regime
    for key, title in (
        ("R12", "R=12"),
        ("R20", "R=20"),
    ):
        rv = key[1:]
        n2, n1, n1t = f"f3v2_R{rv}", f"f3_pi1_R{rv}", f"f3v1t_R{rv}"
        rows = []
        for r in rids:
            dw = A[n2]["delta"]["wald_cut"]["per_regime"][r]
            d1 = S["compare"][f"{n2} vs {n1}"]["per_regime"][r]
            pr = A[n2]["per_regime"][r]
            sig = "better" if dw["hi"] < 0 else ("WORSE" if dw["lo"] > 0 else "")
            sig1 = "better" if d1["hi"] < 0 else ("WORSE" if d1["lo"] > 0 else "")
            lo, hi = pr["violation_wilson"]
            rows.append(
                [
                    r,
                    f(A["wald_cut"]["per_regime"][r]["J"]),
                    f(A[n1]["per_regime"][r]["J"]),
                    f(pr["J"]),
                    f"{dw['delta']:+.2f} [{dw['lo']:+.2f},{dw['hi']:+.2f}] {sig}",
                    f"{d1['delta']:+.2f} [{d1['lo']:+.2f},{d1['hi']:+.2f}] {sig1}",
                    f"{pct(pr['violation'])} ({pr['violation_count']})",
                    f(pr["labels"], 1),
                    f(pr["frac_deployed"]),
                    f(pr["forced_rollbacks"]),
                    f(pr["n_blind"], 1),
                    f(pr["n_sampled"], 1),
                    f(pr["mean_pi"], 2),
                ]
            )
        t.append(f"## (d) Per-regime, {n2} ({title}) vs wald_cut and vs {n1}\n\n")
        t.append(
            md(
                rows,
                [
                    "regime",
                    "J wald_cut",
                    f"J {n1}",
                    f"J {n2}",
                    "dJ vs wald_cut",
                    f"dJ vs {n1}",
                    "viol (n)",
                    "labels",
                    "frac dep",
                    "forced RB",
                    "blind",
                    "sampled",
                    "mean pi",
                ],
            )
        )
        _ = n1t
    # (e) compare
    rows = []
    for k, c in S["compare"].items():
        rows.append(
            [
                k,
                ci(c["all"]),
                ci(c["orig"]),
                ci(c["stress"]),
                c.get("n_better", "-"),
                c.get("n_worse", "-"),
            ]
        )
    t.append(
        "## (e) Paired comparisons (pooled dJ [95% CI]; regimes significantly better/worse)\n\n"
    )
    t.append(md(rows, ["comparison", "all30", "orig24", "stress6", "#better", "#worse"]))
    # (f) dominance
    rows = []
    for b, d in S["dominance"].items():
        rows.append(
            [
                b,
                f(d["J"]),
                f(d["q99"]),
                ", ".join(d["dominated_by"]) or "none",
                ", ".join(d["strictly_dominated_by"]) or "none",
            ]
        )
    t.append(
        "## (f) Dominance (pooled all30): an F3 v2 arm with J <= and q99 sup_harm <= the row's\n\n"
    )
    t.append(md(rows, ["arm", "J", "q99", "dominated by (<=)", "strictly dominated by (<)"]))
    # (g) sanity
    san = S["sanity"]
    t.append(
        "## (g) Sanity\n\n```\n"
        + json.dumps({k: v for k, v in san.items() if k != "I_max_over_R_max"}, indent=1)[:6000]
        + "\n```\n"
    )
    return "".join(t)


def frontier_csv(S, path):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "arm",
                "budget_R",
                "pooled_mean_J",
                "pooled_q95_sup_harm",
                "pooled_q99_sup_harm",
                "worst_regime_q95_sup_harm",
                "mean_labels",
                "violation_rate",
            ]
        )
        for n in S["meta"]["arms"]:
            p = S["arms"][n]["pooled"]["all"]
            w.writerow(
                [
                    n,
                    S["meta"]["budget"].get(n, ""),
                    p["J"],
                    p["sup_q95"],
                    p["sup_q99"],
                    p["worst_regime_q95"],
                    p["labels"],
                    p.get("violation", ""),
                ]
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="dev_v2")
    a = ap.parse_args()
    S, _arms, rids = analyze(a.tag)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "dev_v2_summary.json").write_text(json.dumps(S, indent=1, default=float))
    (RES / "dev_v2_tables.md").write_text(tables(S, rids))
    frontier_csv(S, RES / "frontier_v2.csv")
    print(json.dumps({k: v for k, v in S["sanity"].items()}, indent=1, default=float)[:4000])


if __name__ == "__main__":
    main()
    _ = re
