"""Alarm-metric vs economic ranking inversions (synthetic atlas dev pilot). Seed-cluster bootstrap CIs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from shiftlab.paper3.atlas.cells import design

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper3/atlas"
CORE = [
    "gated_mope",
    "discern_fixed",
    "smcs_retain",
    "cusum",
    "cusum_cal",
    "page_hinkley",
    "edetector",
    "edetector_cal",
    "wald_econ",
    "thinned_iid",
    "markov_skeleton",
    "iid_gate",
]
COMP = ["fees", "intervention", "harm_bad", "noise_neutral", "cert_lag", "remiss"]


def load():
    a = pd.read_pickle(OUT / "dev1_all.pkl")
    frames = [a]
    for i in range(32):
        p = OUT / "dev1b" / f"cell_{i:02d}.jsonl"
        frames.append(pd.read_json(p, lines=True))
    return pd.concat(frames, ignore_index=True)


def cell_tables(df, seeds, methods):
    d = df[df.seed.isin(seeds) & df.method.isin(methods)]
    alt = (
        d[d["null"] == 0]
        .groupby(["cell", "method"])
        .agg(
            J=("J", "mean"),
            edd=("edd", "mean"),
            missed=("missed", "mean"),
            **{c: (c, "mean") for c in COMP},
        )
        .reset_index()
    )
    nul = d[d["null"] == 1].groupby(["cell", "method"]).agg(fa=("null_fp", "mean")).reset_index()
    return alt.merge(nul, on=["cell", "method"])


def inversions(tab):
    rows = []
    for c, g in tab.groupby("cell"):
        g = g.set_index("method")
        ms = list(g.index)
        tau_e = kendalltau(g.edd, g.J)[0]
        tau_f = kendalltau(g.fa, g.J)[0]
        comp = g.edd.rank() + g.fa.rank() + g.missed.rank()
        tau_c = kendalltau(comp, g.J)[0]
        n_dom = n_inv = n_dom_e = n_inv_e = 0
        mag = []
        mag_e = []
        for x in ms:
            for y in ms:
                if x == y:
                    continue
                dj = g.J[x] - g.J[y]
                if g.edd[x] < g.edd[y] and g.fa[x] <= g.fa[y]:
                    n_dom += 1
                    if dj > 0:
                        n_inv += 1
                        mag.append(dj)
                if g.edd[x] < g.edd[y]:
                    n_dom_e += 1
                    if dj > 0:
                        n_inv_e += 1
                        mag_e.append(dj)
        rows.append(
            {
                "cell": c,
                "tau_edd": tau_e,
                "tau_fa": tau_f,
                "tau_comp": tau_c,
                "n_dom": n_dom,
                "n_inv": n_inv,
                "n_dom_e": n_dom_e,
                "n_inv_e": n_inv_e,
                "mag": np.sum(mag),
                "mag_e": np.sum(mag_e),
            }
        )
    return pd.DataFrame(rows)


def pooled(inv):
    return {
        "tau_edd": inv.tau_edd.mean(),
        "tau_fa": inv.tau_fa.mean(),
        "tau_comp": inv.tau_comp.mean(),
        "inv_rate": inv.n_inv.sum() / max(inv.n_dom.sum(), 1),
        "inv_rate_edd": inv.n_inv_e.sum() / max(inv.n_dom_e.sum(), 1),
        "mag_per_inv": inv.mag.sum() / max(inv.n_inv.sum(), 1),
        "mag_per_inv_edd": inv.mag_e.sum() / max(inv.n_inv_e.sum(), 1),
    }


def run(df, methods, nboot=300, seed=0):
    seeds = np.array(sorted(df.seed.unique()))
    tab = cell_tables(df, seeds, methods)
    inv = inversions(tab)
    pt = pooled(inv)
    rng = np.random.default_rng(seed)
    sub = df[df.method.isin(methods)]
    cols = ["J", "edd", "missed"] + COMP
    A = sub[sub["null"] == 0].set_index(["cell", "method", "seed"])[cols].sort_index()
    N = sub[sub["null"] == 1].set_index(["cell", "method", "seed"])[["null_fp"]].sort_index()
    idx = A.groupby(level=[0, 1]).size().index
    arrA = {c: A[c].unstack("seed").reindex(idx).values for c in cols}
    arrN = N["null_fp"].unstack("seed").reindex(idx).values
    sd = list(A[cols[0]].unstack("seed").columns)
    bs = []
    for _ in range(nboot):
        w = np.bincount(rng.integers(0, len(sd), len(sd)), minlength=len(sd)).astype(float)
        w /= w.sum()
        t = pd.DataFrame({c: arrA[c] @ w for c in cols}, index=idx).reset_index()
        t["fa"] = arrN @ w
        bs.append(pooled(inversions(t)))
    bs = pd.DataFrame(bs)
    ci = {k: (float(bs[k].quantile(0.025)), float(bs[k].quantile(0.975))) for k in bs.columns}
    return tab, inv, pt, ci


if __name__ == "__main__":
    df = load()
    df = df[df.cell.notna()]
    res = {}
    for label, ms in [("core12", CORE), ("core12+never", CORE + ["never_switch"])]:
        tab, inv, pt, ci = run(df, ms)
        res[label] = {"pooled": pt, "ci": ci}
        if label == "core12":
            tab.to_csv(OUT / "cell_method_table.csv", index=False)
            inv.to_csv(OUT / "cell_inversions.csv", index=False)
            # decomposition of inverted pairs
            g = tab.set_index(["cell", "method"])
            dec = []
            for c in tab.cell.unique():
                for x in CORE:
                    for y in CORE:
                        if x == y:
                            continue
                        a, b = g.loc[(c, x)], g.loc[(c, y)]
                        if a.edd < b.edd and a.fa <= b.fa and a.J > b.J:
                            dec.append({"dJ": a.J - b.J, **{k: a[k] - b[k] for k in COMP}})
            dec = pd.DataFrame(dec)
            res["inverted_pair_decomposition_mean"] = dec.mean().to_dict() if len(dec) else {}
            res["n_inverted_pairs"] = len(dec)
            # axes
            cs = design()
            P = pd.DataFrame(
                [
                    {
                        "cell": c.cid,
                        "onset": c.onset,
                        "dwell": min(c.dwell, 2000 - c.onset) / (2000 - c.onset),
                        "delta": c.delta,
                        "rho": c.rho,
                        "delay": c.delay,
                        "informative": int(c.informative),
                        "budget_frac": c.budget_frac,
                        "price": c.price,
                        "k": c.switch_cost,
                        "dis": c.dis,
                    }
                    for c in cs
                ]
            )
            inv2 = inv.merge(P, on="cell")
            inv2["inv_rate"] = inv2.n_inv / inv2.n_dom.replace(0, np.nan)
            ax = {}
            for col in P.columns[1:]:
                r1 = spearmanr(inv2[col], inv2.inv_rate, nan_policy="omit")
                r2 = spearmanr(inv2[col], inv2.tau_comp, nan_policy="omit")
                ax[col] = {
                    "rho_vs_inv_rate": float(r1[0]),
                    "p": float(r1[1]),
                    "rho_vs_tau": float(r2[0]),
                    "p_tau": float(r2[1]),
                }
            res["axes"] = ax
            X = (inv2[list(P.columns[1:])] - inv2[list(P.columns[1:])].mean()) / inv2[
                list(P.columns[1:])
            ].std()
            y = inv2.inv_rate.fillna(inv2.inv_rate.mean())
            Xm = np.c_[np.ones(len(X)), X.values]
            beta, *_ = np.linalg.lstsq(Xm, y.values, rcond=None)
            res["ols_std_coef_inv_rate"] = dict(zip(["const"] + list(X.columns), map(float, beta)))
            res["ols_r2"] = float(1 - ((y - Xm @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum())
            res["rho_means"] = (
                inv2.groupby("rho")[["inv_rate", "tau_comp", "tau_edd", "tau_fa"]].mean().to_dict()
            )
            res["informative_means"] = (
                inv2.groupby("informative")[["inv_rate", "tau_comp"]].mean().to_dict()
            )
            res["by_method_mean"] = (
                tab.groupby("method")[["J", "edd", "missed", "fa"] + COMP]
                .mean()
                .round(3)
                .to_dict("index")
            )
            res["by_method_mean"]["never_switch"] = (
                df[(df.method == "never_switch") & (df["null"] == 0)][["J"]].mean().to_dict()
            )
    (OUT / "inversion_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float)[:6000])
