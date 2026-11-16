"""Analysis of the v3 fresh evaluations (03F section 7, step 3).
usage: analyze_v3.py scarce|orig30

Pooled = equal weight over regimes. Delta J is arm minus reference (negative is better); the CI is a
seed-cluster bootstrap (resample seed indices, average over regimes within each resample).
Per-regime significance uses a seed bootstrap within the regime.
"""

import json
import re
import sys

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.harness_v3 import OUT, load_family

PROG = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme"
RES = PROG / "results/riskbudget"
N_BOOT_POOL, N_BOOT_REG, EPS = 5000, 2000, 1e-9
BUDGET = re.compile(r"^(stoploss|f3_pi1|f3v2d|v3)_[hR](\d+)$")
CFG = {
    "scarce": {"tag": "v3_scarce", "k": 5.0, "exceed": (24, 60, 110)},
    "orig30": {"tag": "v3_orig30", "k": 3.0, "exceed": (12, 20, 30)},
}


def wilson(k, n, z=1.959964):
    p = k / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    d = 1 + z * z / n
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


def budget_R(name, which):
    m = BUDGET.match(name)
    if not m:
        return None
    x = int(m.group(2))
    return 2 * CFG[which]["k"] + x if "_h" in name else float(x)


def boot_pool(D, rng):
    """D: (regime, seed) differences -> (mean, lo, hi) of the equal-weight pooled mean."""
    per_seed = D.mean(0)
    idx = rng.integers(0, per_seed.size, (N_BOOT_POOL, per_seed.size))
    b = per_seed[idx].mean(1)
    return float(per_seed.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main(which):
    cfg = CFG[which]
    names, rids, seeds, A = load_family(OUT / cfg["tag"], "scarce" if which == "scarce" else "orig")
    ix = {n: i for i, n in enumerate(names)}
    J = A["J"]  # (arm, regime, seed)
    rng = np.random.default_rng(12345)
    idx_reg = rng.integers(0, len(seeds), (N_BOOT_REG, len(seeds)))
    S = {"which": which, "seeds": [seeds[0], seeds[-1]], "n_seeds": len(seeds), "regimes": rids,
         "arms": {}}  # fmt: skip
    for n in names:
        i = ix[n]
        a = {
            "J": float(J[i].mean(1).mean()),
            "labels": float(A["n_queries"][i].mean()),
            "deployed": float(A["frac_time_deployed"][i].mean()),
            "switches": float(A["n_switches"][i].mean()),
        }
        fr = A["n_forced_rollbacks"][i]
        a["forced_rollbacks"] = None if np.isnan(fr).all() else float(np.nanmean(fr))
        ns, mp = A["n_sampled"][i], A["mean_pi"][i]
        if not np.isnan(ns).all():
            a["frac_runs_sampled"] = float(np.nanmean(ns > 0))
            a["mean_pi"] = float(np.nanmean(mp))
            a["mean_pi_when_sampled"] = float(np.nanmean(mp[ns > 0])) if np.any(ns > 0) else None
            a["blind_rounds"] = float(np.nanmean(A["n_blind"][i]))
        sup = A["sup_harm"][i]
        a["sup_q95"], a["sup_max"] = float(np.quantile(sup, 0.95)), float(sup.max())
        for ref in ("wald_cut", "never"):
            D = J[i] - J[ix[ref]]
            m, lo, hi = boot_pool(D, rng)
            sig_b = sig_w = 0
            for r in range(len(rids)):
                bs = D[r][idx_reg].mean(1)
                l, h = np.percentile(bs, [2.5, 97.5])
                sig_b += h < 0
                sig_w += l > 0
            a[f"d_{ref}"] = {"mean": m, "ci": [lo, hi], "n_better": int(sig_b),
                             "n_worse": int(sig_w), "n_regimes": len(rids)}  # fmt: skip
        R = budget_R(n, which)
        if R is not None:
            v = sup > R + EPS
            per = v.mean(1)
            j = int(np.argmax(per))
            k, N = int(v.sum()), v.size
            a["R"] = R
            a["violation"] = {"k": k, "n": N, "rate": k / N, "wilson": wilson(k, N)}
            kw = int(v[j].sum())
            a["violation_worst"] = {"regime": rids[j], "k": kw, "n": v.shape[1],
                                    "rate": kw / v.shape[1], "wilson": wilson(kw, v.shape[1])}  # fmt: skip
            flags = []
            for r in range(len(rids)):
                kk = int(v[r].sum())
                lo_w = wilson(kk, v.shape[1])[0]
                if lo_w > 0.05 and not n.startswith(("stoploss",)):
                    first = [int(seeds[s]) for s in np.flatnonzero(v[r])[:3]]
                    flags.append({"regime": rids[r], "k": kk, "rate": kk / v.shape[1],
                                  "wilson_lo": lo_w, "first_seeds": first})  # fmt: skip
            a["flagged_wilson_lo_gt_.05"] = flags
            # deterministic claim: runs with no sampled round must have zero violations
            nsr = A["n_sampled"][i]
            if n.startswith("f3_pi1"):
                a["det_runs"] = {"n": int(v.size), "violations": k}
            elif not np.isnan(nsr).all():
                m0 = nsr == 0
                a["det_runs"] = {"n": int(m0.sum()), "violations": int((v & m0).sum())}
        else:
            a["exceed"] = {}
            for Rx in cfg["exceed"]:
                v = sup > Rx + EPS
                k, N = int(v.sum()), v.size
                a["exceed"][str(Rx)] = {"k": k, "n": N, "rate": k / N, "wilson": wilson(k, N)}
        S["arms"][n] = a
    # per-regime J table
    S["per_regime_J"] = {n: [float(x) for x in J[ix[n]].mean(1)] for n in names}
    if which == "scarce":
        S["breakdown"] = breakdown(rids, names, J, ix)
    (RES / f"v3_{which}_summary.json").write_text(json.dumps(S, indent=1))
    (RES / f"v3_{which}_tables.md").write_text(render(S))
    print("\n".join(render(S).splitlines()[:60]))


def parse(rid):
    m = re.match(r"sc_r(\d+)_d(\d+)_([a-z]+)(_rho80)?$", rid)
    return int(m.group(1)), int(m.group(2)), m.group(3), bool(m.group(4))


BD_ARMS = [
    "never",
    "wald_cut",
    "stoploss_h50",
    "f3_pi1_h50",
    "f3v2d_h50",
    "v3_h14",
    "v3_h50",
    "v3_h100",
]


def breakdown(rids, names, J, ix):
    info = [parse(r) for r in rids]
    out = {}
    facets = {
        "r": lambda t: f"r={t[0] / 100:g}",
        "d": lambda t: f"d={t[1]}",
        "path": lambda t: t[2],
    }
    for fac, f in facets.items():
        groups: dict[str, list[int]] = {}
        for k, t in enumerate(info):
            if not t[3]:
                groups.setdefault(f(t), []).append(k)
        out[fac] = {}
        for g, ks in groups.items():
            d = {}
            for n in BD_ARMS:
                if n not in ix:
                    continue
                Ja = J[ix[n]][ks].mean()
                dw = (J[ix[n]][ks] - J[ix["wald_cut"]][ks]).mean(0)
                dn = (J[ix[n]][ks] - J[ix["never"]][ks]).mean(0)
                d[n] = {"J": float(Ja), "d_wald_cut": float(dw.mean()), "d_never": float(dn.mean())}
            out[fac][g] = {"n_regimes": len(ks), "arms": d}
    ks = [k for k, t in enumerate(info) if t[3]]
    out["rho0.8"] = {
        "rho=.8 (2 regimes)": {
            "n_regimes": len(ks),
            "arms": {
                n: {
                    "J": float(J[ix[n]][ks].mean()),
                    "d_wald_cut": float((J[ix[n]][ks] - J[ix["wald_cut"]][ks]).mean()),
                    "d_never": float((J[ix[n]][ks] - J[ix["never"]][ks]).mean()),
                }
                for n in BD_ARMS
                if n in ix
            },
        }
    }
    return out


def md_table(header, rows):
    return (
        "| " + " | ".join(header) + " |\n|" + "|".join("---" for _ in header) + "|\n"
        + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows) + "\n"
    )  # fmt: skip


def f1(x):
    return "n/a" if x is None else f"{x:.2f}"


def fd(d):
    return f"{d['mean']:+.2f} [{d['ci'][0]:+.2f},{d['ci'][1]:+.2f}]"


def render(S):
    which = S["which"]
    L = [
        f"# F v3: fresh evaluation, {which} (03F section 7, step 3)\n",
        (
            f"Dev seeds {S['seeds'][0]}-{S['seeds'][1]} ({S['n_seeds']} per regime), {len(S['regimes'])} regimes, "
            "equal-weight pooling. Frozen v3 from `configs/paper3/f3_v3_frozen.json`. Delta J = arm minus "
            "reference (negative is better); brackets are 95% seed-cluster bootstrap CIs "
            f"({N_BOOT_POOL} resamples). 'sig b/w' = regimes whose own seed-bootstrap CI excludes 0 "
            "(better/worse).\n"
        ),
        "## Pooled\n",
    ]
    rows = []
    for n, a in S["arms"].items():
        w, nv = a["d_wald_cut"], a["d_never"]
        v = a.get("violation")
        if v:
            vs = f"{v['k']}/{v['n']} ({v['wilson'][0]:.4f}-{v['wilson'][1]:.4f})"
            wv = a["violation_worst"]
            ws = f"{wv['rate']:.3f} ({wv['wilson'][0]:.3f}-{wv['wilson'][1]:.3f}) {wv['regime']}"
        else:
            vs = "; ".join(f"R{R}:{e['rate']:.3f}" for R, e in a["exceed"].items())
            ws = ""
        rows.append([
            n, f1(a["J"]), fd(w), f"{w['n_better']}/{w['n_worse']}", fd(nv),
            f"{nv['n_better']}/{nv['n_worse']}", vs, ws, f1(a["labels"]), f"{a['deployed']:.3f}",
            f1(a["forced_rollbacks"]), f"{a['mean_pi']:.3f}" if "mean_pi" in a else "",
        ])  # fmt: skip
    L.append(md_table(["arm", "J", "dJ vs wald_cut", "sig b/w", "dJ vs never", "sig b/w",
                       "violation (own R) / exceedance rate of R" + "/".join(
                           str(x) for x in CFG[which]["exceed"]), "worst regime", "labels",
                       "deployed", "forced rb", "mean pi"], rows))  # fmt: skip
    L.append("\n## Deterministic-claim and flag checks (budget arms)\n")
    rows = []
    for n, a in S["arms"].items():
        if "violation" in a:
            d = a.get("det_runs")
            rows.append([n, f"{d['violations']}/{d['n']}" if d else "n/a",
                         f"{a.get('frac_runs_sampled', 0):.3f}" if "frac_runs_sampled" in a else "0",
                         "; ".join(f"{f['regime']} {f['k']}/{S['n_seeds']} (lo {f['wilson_lo']:.3f}, "
                                   f"seeds {f['first_seeds']})" for f in a["flagged_wilson_lo_gt_.05"]) or "none"])  # fmt: skip
    L.append(md_table(["arm", "violations in runs with no sampled round (must be 0)",
                       "frac runs with a sampled round", "regimes with Wilson lower > .05"], rows))  # fmt: skip
    if "breakdown" in S:
        for fac, gs in S["breakdown"].items():
            L.append(f"\n## Breakdown by {fac} (J; dJ vs wald_cut; dJ vs never), rho = 0 regimes\n")
            arms = list(next(iter(gs.values()))["arms"])
            rows = [
                [g, v["n_regimes"]] + [
                    f"{v['arms'][n]['J']:.1f} ({v['arms'][n]['d_wald_cut']:+.1f}; {v['arms'][n]['d_never']:+.1f})"
                    for n in arms
                ] for g, v in gs.items()
            ]  # fmt: skip
            L.append(md_table(["group", "regimes"] + arms, rows))
    L.append("\n## Per-regime mean J\n")
    show = [n for n in BD_ARMS if n in S["per_regime_J"]] if which == "scarce" else list(S["arms"])
    rows = [
        [r] + [f"{S['per_regime_J'][n][k]:.1f}" for n in show] for k, r in enumerate(S["regimes"])
    ]
    L.append(md_table(["regime"] + show, rows))
    return "".join(L)


if __name__ == "__main__":
    main(sys.argv[1])
