"""Summaries and tables for the F3 comparison. ``python analyze.py --tag pilot|dev``."""

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np

from shiftlab.paper3.joint.harness import paired_delta
from shiftlab.paper3.riskbudget.harness import RS, build_arms, load_results, stress_ids

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "paper3" / "riskbudget"
RES = ROOT / "papers" / "paper3_cost_aware_adaptation" / "2026_programme" / "results" / "riskbudget"
EPS = 1e-9
MAIN = ["never", "wald_cut", "wald_paced", "cusum", "gate_wald"]
TUNED_BASE = ["wald_cut", "wald_paced", "cusum", "gate_wald"]
SWEEP = (
    [f"wald_cut_g{g}" for g in ("0.02", "0.05", "0.1", "0.2")]
    + [f"cusum_h{h}" for h in (2, 4, 8, 12)]
    + [f"gate_a{a}" for a in ("0.01", "0.05", "0.1", "0.2")]
)
BASELINES = TUNED_BASE + SWEEP


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (float(max(0.0, c - h)), float(min(1.0, c + h)))


def nm(x):
    return float(np.nanmean(x)) if np.any(~np.isnan(x)) else None


def stats(sh, arrs, i, ri_list, R):
    """Stats of arm i over regimes ri_list (equal weight) from arrays (arm, regime, seed)."""
    s = sh[i][ri_list]  # (reg, seed)
    d = {
        "J": float(arrs["J"][i][ri_list].mean()),
        "sup_mean": float(s.mean()),
        "sup_q95": float(np.quantile(s, 0.95)),
        "sup_q99": float(np.quantile(s, 0.99)),
        "sup_max": float(s.max()),
        "labels": float(arrs["n_queries"][i][ri_list].mean()),
        "switches": float(arrs["n_switches"][i][ri_list].mean()),
        "frac_deployed": float(arrs["frac_time_deployed"][i][ri_list].mean()),
        "forced_rollbacks": nm(arrs["n_forced_rollbacks"][i][ri_list]),
        "vetoed": nm(arrs["n_vetoed_promotions"][i][ri_list]),
        "ride_out_rate": nm(arrs["rode_out"][i][ri_list]),
        "exceed": {str(r): float((s > r + EPS).mean()) for r in RS},
    }
    if R is not None:
        v = s > R + EPS
        d["violation"] = float(v.mean())
        d["violation_wilson"] = wilson(int(v.sum()), v.size)
    return d


def analyze(tag):
    arms, rids, seeds, A = load_results(OUT / tag)
    spec = {a["name"]: a for a in build_arms()}
    budget = {n: float(s["R"]) for n, s in spec.items() if "R" in s}
    ix = {n: i for i, n in enumerate(arms)}
    st = set(stress_ids())
    pools = {
        "all": list(range(len(rids))),
        "orig": [i for i, r in enumerate(rids) if r not in st],
        "stress": [i for i, r in enumerate(rids) if r in st],
    }
    sh = A["sup_harm"]
    J = A["J"]
    out = {
        "meta": {
            "tag": tag,
            "n_seeds": len(seeds),
            "seed_first": seeds[0],
            "n_regimes": len(rids),
            "regimes": rids,
            "arms": arms,
            "budget": budget,
            "note": "pooled sup_harm quantiles are quantiles of the equal-weight mixture "
            "across regimes (equal seeds per regime); violation pooled = mean of "
            "per-regime rates; delta CIs: seed-cluster bootstrap (joint.paired_delta)",
        },
        "arms": {},
    }
    base = {"wald_cut": J[ix["wald_cut"]], "never": J[ix["never"]]}
    for n in arms:
        i, R = ix[n], budget.get(n)
        e = {"pooled": {}, "per_regime": {}, "delta": {}}
        for pn, idx in pools.items():
            e["pooled"][pn] = stats(sh, A, i, idx, R)
            if R is not None:
                rates = [(sh[i][j] > R + EPS).mean() for j in idx]
                e["pooled"][pn]["violation_regime_mean"] = float(np.mean(rates))
                jw = int(idx[int(np.argmax(rates))])
                e["pooled"][pn]["worst_regime"] = rids[jw]
                e["pooled"][pn]["worst_regime_violation"] = float(max(rates))
            q95s = [np.quantile(sh[i][j], 0.95) for j in idx]
            e["pooled"][pn]["worst_regime_q95"] = float(max(q95s))
            e["pooled"][pn]["worst_regime_q95_id"] = rids[int(idx[int(np.argmax(q95s))])]
        for j, r in enumerate(rids):
            e["per_regime"][r] = stats(sh, A, i, [j], R)
        for bn, bJ in base.items():
            d_all = paired_delta(J[i], bJ)
            e["delta"][bn] = {
                "all": {k: d_all[k] for k in ("delta", "lo", "hi", "rel_pct", "base")}
            }
            for pn in ("orig", "stress"):
                idx = pools[pn]
                dd = paired_delta(J[i][idx], bJ[idx], n_boot=1000)
                e["delta"][bn][pn] = {k: dd[k] for k in ("delta", "lo", "hi", "rel_pct", "base")}
            e["delta"][bn]["per_regime"] = {
                r: dict(zip(("delta", "lo", "hi", "rel_pct"), d_all["per_regime"][j], strict=True))
                for j, r in enumerate(rids)
            }
        out["arms"][n] = e

    # ---- sanity
    san = {"deterministic_violations": [], "never_ok": True}
    for n in arms:
        if re.fullmatch(r"f3_(pi1|always)_R\d+", n):
            R = budget[n]
            for j, r in enumerate(rids):
                bad = np.flatnonzero(sh[ix[n]][j] > R + EPS)
                for b in bad:
                    san["deterministic_violations"].append(
                        {
                            "arm": n,
                            "regime": r,
                            "seed": seeds[b],
                            "sup_harm": float(sh[ix[n]][j][b]),
                        }
                    )
    inv = ix["never"]
    san["never_sup_harm_max"] = float(sh[inv].max())
    san["never_J_minus_Jnever_maxabs"] = float(np.abs(J[inv] - A["J_never"][inv]).max())
    for n in ("never", "wald_cut"):
        san[f"{n}_J_orig24"] = out["arms"][n]["pooled"]["orig"]["J"]
    # I_max <= R for deterministic shield arms
    san["I_max_over_R_max"] = {
        n: float(np.nanmax(A["I_max"][ix[n]]) / budget[n])
        for n in arms
        if re.fullmatch(r"f3_pi1_R\d+", n)
    }
    out["sanity"] = san
    # ---- price of safety
    pos = {}
    for r in ("stationary_better", "long_persistent"):
        if r in rids:
            pos[r] = {
                str(int(R)): {
                    "frac_forced_rollback": float(
                        (
                            A["n_forced_rollbacks"][ix[f"f3_pi1_R{int(R)}"]][rids.index(r)] >= 1
                        ).mean()
                    ),
                    "frac_vetoed": float(
                        (
                            A["n_vetoed_promotions"][ix[f"f3_pi1_R{int(R)}"]][rids.index(r)] >= 1
                        ).mean()
                    ),
                    "frac_ride_out": float(
                        A["rode_out"][ix[f"f3_pi1_R{int(R)}"]][rids.index(r)].mean()
                    ),
                    "delta_vs_wald_cut": out["arms"][f"f3_pi1_R{int(R)}"]["delta"]["wald_cut"][
                        "per_regime"
                    ][r],
                }
                for R in RS
            }
    out["price_of_safety"] = pos
    return out, arms, rids


# ------------------------------------------------------------------------------- tables
def f(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


def md(rows, header):
    s = "| " + " | ".join(header) + " |\n|" + "|".join(["---"] * len(header)) + "|\n"
    for r in rows:
        s += "| " + " | ".join(str(c) for c in r) + " |\n"
    return s + "\n"


def tables(S, rids):
    arms, A, budget = S["meta"]["arms"], S["arms"], S["meta"]["budget"]
    head = (
        f"# F3 dev comparison tables ({S['meta']['tag']}, {S['meta']['n_seeds']} seeds, "
        f"{S['meta']['n_regimes']} regimes)\n\nSeeds are dev-block only. Pooled = equal weight over "
        "regimes; sup_harm quantiles are over the pooled mixture. DeltaJ negative = better than "
        "reference.\n\n"
    )
    t = [head]
    # (a)
    rows = []
    for n in arms:
        a = A[n]
        p = a["pooled"]["all"]
        dw, dn = a["delta"]["wald_cut"]["all"], a["delta"]["never"]["all"]
        v = f"{pct(p['violation'])} / {pct(p['worst_regime_violation'])}" if n in budget else "-"
        rows.append(
            [
                n,
                f(p["J"]),
                f(a["pooled"]["orig"]["J"]),
                f(a["pooled"]["stress"]["J"]),
                f"{dw['delta']:+.2f} [{dw['lo']:+.2f},{dw['hi']:+.2f}]",
                f"{dn['delta']:+.2f} [{dn['lo']:+.2f},{dn['hi']:+.2f}]",
                f(p["sup_mean"]),
                f(p["sup_q95"]),
                f(p["sup_q99"]),
                f(p["sup_max"], 0),
                v,
                f(p["labels"], 1),
                f(p["switches"]),
                f(p["frac_deployed"]),
                f(p["forced_rollbacks"]),
                f(p["ride_out_rate"], 3),
            ]
        )
    t.append(
        "## (a) Pooled table, all arms\n\nviol = pooled mean violation rate / worst-regime rate "
        "(budget arms only; budget arms violate if sup_harm > R).\n\n"
    )
    t.append(
        md(
            rows,
            [
                "arm",
                "J all",
                "J orig24",
                "J stress6",
                "dJ vs wald_cut",
                "dJ vs never",
                "sup mean",
                "q95",
                "q99",
                "max",
                "viol pooled/worst",
                "labels",
                "switches",
                "frac dep",
                "forced RB",
                "ride-out",
            ],
        )
    )
    # (b)
    for Rv in (12, 20):
        base_ex = {
            r: np.mean([A[n]["per_regime"][r]["exceed"][str(Rv)] for n in TUNED_BASE]) for r in rids
        }
        top = sorted(rids, key=lambda r: -base_ex[r])[:6]
        keep = list(
            dict.fromkeys(
                top
                + stress_ids()
                + ["dep_null_rho_0.95", "informative_delay", "random_delay", "multiple_reversals"]
            )
        )
        keep = [r for r in keep if r in rids]
        cols = [
            ("wald_cut", "wald_cut"),
            ("wald_paced", "wald_paced"),
            ("cusum", "cusum"),
            ("gate_wald", "gate_wald"),
            ("cusum_rb_h4", "cusum_rb_h4"),
            (f"stoploss_R{Rv}", "stoploss"),
            (f"f3_pi1_R{Rv}", "f3_pi1"),
            (f"f3_pi50_R{Rv}", "f3_pi50"),
            (f"f3_pi25_R{Rv}", "f3_pi25"),
            (f"f3_always_R{Rv}", "f3_always"),
        ]
        cols = [(a, b) for a, b in cols if a in A]
        rows = []
        for r in keep:
            row = [r + (" *" if r in top else "")]
            for a, _ in cols:
                p = A[a]["per_regime"][r]
                row.append(pct(p["violation"] if a in budget else p["exceed"][str(Rv)]))
            rows.append(row)
        for lab, pn in (("POOLED mean", "all"),):
            row = [lab]
            for a, _ in cols:
                p = A[a]["pooled"][pn]
                row.append(
                    pct(
                        p["violation_regime_mean"]
                        if a in budget
                        else float(
                            np.mean([A[a]["per_regime"][r]["exceed"][str(Rv)] for r in rids])
                        )
                    )
                )
            rows.append(row)
        row = ["WORST regime"]
        for a, _ in cols:
            vals = {
                r: (
                    A[a]["per_regime"][r]["violation"]
                    if a in budget
                    else A[a]["per_regime"][r]["exceed"][str(Rv)]
                )
                for r in rids
            }
            w = max(vals, key=vals.get)
            row.append(f"{pct(vals[w])} ({w})")
        rows.append(row)
        t.append(
            f"## (b) P(sup_harm > R) at R={Rv}\n\nBaselines: exceedance of R={Rv} (they do not target it). "
            f"Budget arms (stoploss, f3_*): violation rate for their own R={Rv}. "
            "* = among the 6 regimes with highest mean exceedance over the 4 tuned baselines.\n\n"
        )
        t.append(md(rows, ["regime"] + [b for _, b in cols]))
    # (c)
    for Rv in (12, 20):
        n = f"f3_pi1_R{Rv}"
        rows = []
        for r in rids:
            d = A[n]["delta"]["wald_cut"]["per_regime"][r]
            sig = "better" if d["hi"] < 0 else ("WORSE" if d["lo"] > 0 else "")
            rows.append(
                [
                    r,
                    f(A["wald_cut"]["per_regime"][r]["J"]),
                    f(A[n]["per_regime"][r]["J"]),
                    f"{d['delta']:+.2f} [{d['lo']:+.2f},{d['hi']:+.2f}]",
                    f(d["rel_pct"], 1),
                    sig,
                ]
            )
        dd = A[n]["delta"]["wald_cut"]
        rows.append(
            [
                "POOLED all",
                f(dd["all"]["base"]),
                "-",
                f"{dd['all']['delta']:+.2f} [{dd['all']['lo']:+.2f},{dd['all']['hi']:+.2f}]",
                f(dd["all"]["rel_pct"], 1),
                "",
            ]
        )
        for pn in ("orig", "stress"):
            rows.append(
                [
                    f"POOLED {pn}",
                    f(dd[pn]["base"]),
                    "-",
                    f"{dd[pn]['delta']:+.2f} [{dd[pn]['lo']:+.2f},{dd[pn]['hi']:+.2f}]",
                    f(dd[pn]["rel_pct"], 1),
                    "",
                ]
            )
        t.append(f"## (c) {n} vs wald_cut, per regime (paired, 95% seed-cluster bootstrap CI)\n\n")
        t.append(md(rows, ["regime", "J wald_cut", f"J {n}", "dJ [CI]", "rel %", "significant"]))
    # (d)
    abl = [
        "f3_pi1_R12",
        "f3_pi1_R12_nopending",
        "f3_pi1_R12_norollback",
        "f3_pi1_R12_noride",
        "f3_pi1_R12_nolabelres",
        "f3_pi25_R12",
        "f3_pi25_R12_noconf",
    ]
    rows = []
    for n in abl:
        p = A[n]["pooled"]["all"]
        pr = A[n]["per_regime"]
        bad = sorted(((r, pr[r]["violation"]) for r in rids), key=lambda x: -x[1])[:3]
        nbad = sum(1 for r in rids if pr[r]["violation"] > 0)
        rows.append(
            [
                n,
                f(p["J"]),
                f(p["sup_mean"]),
                f(p["sup_q95"]),
                f(p["sup_max"], 0),
                pct(p["violation_regime_mean"]),
                pct(p["worst_regime_violation"]),
                nbad,
                "; ".join(f"{r} {pct(v)}" for r, v in bad if v > 0) or "none",
                f(p["labels"], 1),
                f(p["forced_rollbacks"]),
            ]
        )
    t.append(
        "## (d) Ablations at R=12\n\nviol = violation rate of sup_harm > 12; #reg = regimes with any violation.\n\n"
    )
    t.append(
        md(
            rows,
            [
                "arm",
                "J",
                "sup mean",
                "q95",
                "max",
                "viol pooled",
                "viol worst",
                "#reg>0",
                "worst regimes",
                "labels",
                "forced RB",
            ],
        )
    )
    # (e)
    base_ok = [n for n in BASELINES if n in A]
    rows = []
    for n in [a for a in arms if a.startswith("f3_")]:
        p = A[n]["pooled"]["all"]
        ok = [b for b in base_ok if A[b]["pooled"]["all"]["sup_q95"] <= p["sup_q95"] + 1e-12]
        if ok:
            b = min(ok, key=lambda x: A[x]["pooled"]["all"]["J"])
            pb = A[b]["pooled"]["all"]
            rows.append(
                [
                    n,
                    f(p["sup_q95"]),
                    f(p["J"]),
                    b,
                    f(pb["sup_q95"]),
                    f(pb["J"]),
                    f"{p['J'] - pb['J']:+.2f}",
                ]
            )
        else:
            rows.append([n, f(p["sup_q95"]), f(p["J"]), "none", "-", "-", "-"])
    t.append(
        "## (e) Frontier comparison (pooled, all 30 regimes)\n\nFor each F3 arm: the lowest-J baseline "
        "arm (tuned baselines and sweeps; never excluded) whose pooled q95 sup_harm <= the F3 arm's. "
        f"never: J={f(A['never']['pooled']['all']['J'])}, q95=0. Last column = J(F3) - J(baseline); "
        "negative = F3 cheaper at equal-or-lower tail.\n\n"
    )
    t.append(
        md(rows, ["F3 arm", "q95 sup", "J", "best safe-enough baseline", "its q95", "its J", "dJ"])
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
                ]
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    S, _arms, rids = analyze(a.tag)
    RES.mkdir(parents=True, exist_ok=True)
    name = "pilot" if a.tag.startswith("pilot") else "dev"
    (RES / f"{name}_summary.json").write_text(json.dumps(S, indent=1))
    if name == "dev":
        (RES / "dev_tables.md").write_text(tables(S, rids))
        frontier_csv(S, RES / "frontier.csv")
    else:
        (OUT / "pilot_tables.md").write_text(tables(S, rids))
        frontier_csv(S, OUT / "pilot_frontier.csv")
    print(json.dumps(S["sanity"], indent=1))
    print(json.dumps(S["price_of_safety"], indent=1)[:3000])


if __name__ == "__main__":
    main()
