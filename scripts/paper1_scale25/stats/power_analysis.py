"""Power / required-effect analysis from the real fresh records (7 datasets, 547 episodes).

    python power_analysis.py --records <records_all.jsonl> --out results/power

Outputs (CSV + printed): per-dataset SE of r under block dependence; the point reduction r_hat needed so that
(i) L_i > 0 and (ii) L_i >= 2.5 at the Design-B level alpha_i; cohort-level needed r_hat for mean(L) >= 2.5;
Design A / A2 / B' comparisons; Monte-Carlo success probability; what v1 would certify.
The structure (b_k, D_k) of each real series is kept (n, variance, dependence); only mean(D) is shifted.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from certify import alpha_i, primary_lower

T = 2000.0
CAND = "P2_K2__E48_F60"
EQ_CUT = "s2armr_H1100"
INDICES = [1, 2, 5, 10, 25, 40, 60]


def load(path):
    d = pd.read_json(path, lines=True, dtype={"config_id": str}).drop_duplicates(
        ["stream", "ep", "seed", "config_id"]
    )
    m = d.groupby(["stream", "ep", "config_id"]).net.mean().unstack("config_id") / T * 100
    return m


def series(m, stream, cand, ref):
    x = m.xs(stream, level="stream").sort_index()
    return x[cand].to_numpy(), x[ref].to_numpy()


def needed_r(
    a,
    b,
    alpha,
    threshold,
):
    """Smallest point reduction r_hat (percent) such that Fieller L >= threshold, keeping the (b, D) structure."""
    D = b - a
    mb = b.mean()

    def f(tgt):
        return primary_lower(b - (D - D.mean() + tgt * mb / 100), b, alpha)["L"] - threshold

    lo, hi = threshold, threshold + 60.0
    if f(hi) < 0:
        return np.inf
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if f(mid) >= 0 else (mid, hi)
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", default="results/power")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    m = load(args.records)
    streams = sorted(m.index.get_level_values("stream").unique())
    pols = [c for c in m.columns if c != CAND]
    nonparent = [c for c in pols if c not in ("P4W__P2_K2__E48_F60",)]

    # ---- 1. SE of r for each (dataset, reference)
    rows = []
    for s in streams:
        mj = m.xs(s, level="stream").mean()
        strongest = mj.drop([CAND, "P4W__P2_K2__E48_F60"]).idxmin()
        for ref in nonparent:
            a, b = series(m, s, CAND, ref)
            r = primary_lower(a, b, 0.05)
            rows.append(
                {
                    "stream": s,
                    "ref": ref,
                    "n": len(b),
                    "block": r["block_len"],
                    "n_blocks": r["n_blocks"],
                    "r_hat": r["r_hat"],
                    "se": r["se"],
                    "strongest": ref == strongest,
                    "eq_cut": ref == EQ_CUT,
                    "sdD_over_mb": 100 * np.std(b - a) / b.mean(),
                }
            )
    se = pd.DataFrame(rows)
    se.to_csv(out / "se_by_dataset_ref.csv", index=False)
    summ = (
        se.groupby("stream")
        .agg(
            n=("n", "first"),
            n_blocks=("n_blocks", "first"),
            se_median=("se", "median"),
            se_max=("se", "max"),
        )
        .join(
            se[se.eq_cut]
            .set_index("stream")[["r_hat", "se"]]
            .rename(columns={"r_hat": "r_vs_EQcut", "se": "se_vs_EQcut"})
        )
        .join(
            se[se.strongest]
            .set_index("stream")[["ref", "r_hat", "se"]]
            .rename(
                columns={"ref": "strongest_ref", "r_hat": "r_vs_strongest", "se": "se_vs_strongest"}
            )
        )
    )
    summ.to_csv(out / "se_summary.csv")
    print(summ.round(3).to_string())

    # ---- 2. needed point reduction per dataset at index i (pool over references, keep per-dataset structure)
    need = []
    for s in streams:
        for ref in [EQ_CUT, *[c for c in nonparent if c != EQ_CUT]]:
            a, b = series(m, s, CAND, ref)
            for i in INDICES:
                for thr in (0.0, 2.5):
                    need.append(
                        {
                            "stream": s,
                            "ref": ref,
                            "i": i,
                            "alpha": alpha_i(i),
                            "thr": thr,
                            "need": needed_r(a, b, alpha_i(i), thr),
                            "is_eqcut": ref == EQ_CUT,
                        }
                    )
    nd = pd.DataFrame(need)
    nd.to_csv(out / "needed_r_all.csv", index=False)
    pool = (
        nd[~nd.is_eqcut]
        .groupby(["i", "thr"])
        .need.agg(median="median", p90=lambda x: x.quantile(0.9), mean="mean")
        .reset_index()
    )
    near = (
        nd[nd.is_eqcut]
        .groupby(["i", "thr"])
        .need.agg(median="median")
        .reset_index()
        .rename(columns={"median": "median_vs_EQcut"})
    )
    tab = pool.merge(near, on=["i", "thr"])
    tab.insert(2, "alpha_i", [alpha_i(int(i)) for i in tab.i])
    tab.to_csv(out / "needed_r_by_index.csv", index=False)
    print(tab.round(3).to_string())
    bydata = nd[(nd.i == 25) & (nd.thr == 2.5) & ~nd.is_eqcut].groupby("stream").need.median()
    bydata.to_csv(out / "needed_r_i25_thr2.5_by_dataset.csv")
    print(
        "needed r_hat for L_25>=2.5, by dataset (median over references):\n",
        bydata.round(2).to_string(),
    )

    # ---- 3. cohort of 25 (homogeneous true r), needed common r_hat for mean(L)>=2.5
    rng = np.random.default_rng(0)
    structs = [(s, ref) for s in streams for ref in nonparent if ref != EQ_CUT]
    cache = {k: series(m, k[0], CAND, k[1]) for k in structs}

    def cohort_need(alphas, picks):
        """common shift target t such that mean_j L_j(t) = 2.5 (bisection)."""

        def meanL(t):
            Ls = []
            for al, k in zip(alphas, picks):
                a, b = cache[k]
                D = b - a
                Ls.append(primary_lower(b - (D - D.mean() + t * b.mean() / 100), b, al)["L"])
            return np.mean(Ls)

        lo, hi = 2.5, 70.0
        for _ in range(45):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if meanL(mid) >= 2.5 else (mid, hi)
        return hi

    coh = []
    for N in (
        25,
        40,
        60,
    ):  # N attempts opened, 25 of them are the successes, positions uniformly random
        res = []
        for rep in range(12):
            pos = (
                np.sort(rng.choice(np.arange(1, N + 1), 25, replace=False))
                if N > 25
                else np.arange(1, 26)
            )
            picks = [structs[j] for j in rng.choice(len(structs), 25)]
            res.append(cohort_need([alpha_i(int(p)) for p in pos], picks))
        coh.append(
            {
                "design": f"B (chronological), 25 successes among {N} attempts",
                "needed_common_r_hat": float(np.mean(res)),
                "sd_over_draws": float(np.std(res)),
            }
        )
    picks = [structs[j] for j in rng.choice(len(structs), 25)]
    for K, label in (
        (25, "A1 Bonferroni, one pre-registered cohort of 25"),
        (30, "A1 Bonferroni, pre-registered cohort of 30"),
        (40, "A1 Bonferroni, pre-registered cohort of 40"),
    ):
        pk = [structs[j] for j in rng.choice(len(structs), K)]
        coh.append(
            {
                "design": label,
                "needed_common_r_hat": cohort_need([0.05 / K] * K, pk),
                "sd_over_draws": np.nan,
            }
        )
    # B' batch: one batch registered together, all datasets share alpha = .05/(j(j+1))/M, j = batch number
    for M in (25, 30, 40):
        pk = [structs[j] for j in rng.choice(len(structs), M)]
        coh.append(
            {
                "design": f"B' batch 1 of M={M} (alpha=.025/M each)",
                "needed_common_r_hat": cohort_need([0.025 / M] * M, pk),
                "sd_over_draws": np.nan,
            }
        )
    # A2: cohort-mean bound with independence across datasets (level .05, Welch-Satterthwaite-free: t with K*(df)-ish -> use normal)
    se_pool = se[~se.eq_cut & (se.ref != "P4W__P2_K2__E48_F60")].se.to_numpy()
    for K in (25, 30):
        s_c = np.sqrt(np.mean(rng.choice(se_pool, (4000, K)) ** 2, axis=1) / K)
        coh.append(
            {
                "design": f"A2 mean bound at .05 assuming independence, K={K} (no per-dataset gate)",
                "needed_common_r_hat": 2.5 + stats.norm.isf(0.05) * float(np.median(s_c)),
                "sd_over_draws": np.nan,
            }
        )
    cd = pd.DataFrame(coh)
    cd.to_csv(out / "cohort_needed.csv", index=False)
    print(cd.round(3).to_string())

    # ---- 4. Monte-Carlo success probability (normal approx of r_hat; t critical values at the block df)
    def p_success(true_r, se_d, df, design, K=25, N=25, reps=20000, seed=0):
        g = np.random.default_rng(seed)
        ok = 0
        for _ in range(reps):
            rh = true_r + se_d * g.standard_normal(K)
            if design == "B":
                pos = (
                    np.sort(g.choice(np.arange(1, N + 1), K, replace=False))
                    if N > K
                    else np.arange(1, K + 1)
                )
                al = np.array([alpha_i(int(p)) for p in pos])
            elif design == "A1":
                al = np.full(K, 0.05 / K)
            elif design == "B'":
                al = np.full(K, 0.025 / K)
            L = rh - stats.t.isf(al, df) * se_d
            ok += (L > 0).all() and L.mean() >= 2.5
        return ok / reps

    pw = []
    for se_d in (0.15, 0.25, 0.40):
        for df in (9, 19):
            for tr in (3.0, 3.5, 4.0, 5.0, 6.0):
                pw.append(
                    {
                        "se": se_d,
                        "df": df,
                        "true_r": tr,
                        "B_25_attempts": p_success(tr, se_d, df, "B", reps=4000),
                        "B_60_attempts": p_success(tr, se_d, df, "B", N=60, reps=4000),
                        "A1_bonferroni": p_success(tr, se_d, df, "A1", reps=4000),
                        "Bprime_batch1": p_success(tr, se_d, df, "B'", reps=4000),
                    }
                )
    pw = pd.DataFrame(pw)
    pw.to_csv(out / "power_mc.csv", index=False)
    print(pw.round(3).to_string())

    # ---- 5. what v1 would certify on the real fresh data
    v1 = []
    for label, refsel in (
        ("vs EQ+cut (doc19 H1)", lambda s: EQ_CUT),
        (
            "vs per-dataset strongest reference",
            lambda s: se[(se.stream == s) & se.strongest].ref.iloc[0],
        ),
    ):
        for design, al_f in (
            ("B indices 8..14 (next 7 attempts after legacy 1..7)", lambda j: alpha_i(8 + j)),
            ("B indices 1..7 (if legacy were not reserved)", lambda j: alpha_i(1 + j)),
            ("A1 Bonferroni K=7", lambda j: 0.05 / 7),
        ):
            Ls, rs = [], []
            for j, s in enumerate(streams):
                a, b = series(m, s, CAND, refsel(s))
                r = primary_lower(a, b, al_f(j))
                Ls.append(r["L"])
                rs.append(r["r_hat"])
            v1.append(
                {
                    "reference": label,
                    "design": design,
                    "mean_r_hat": np.mean(rs),
                    "mean_L": np.mean(Ls),
                    "n_L_positive": int(sum(x > 0 for x in Ls)),
                    "K": len(Ls),
                    "cohort_certifies_2_5": not (np.mean(Ls) < 2.5 or len(Ls) < 25),
                }
            )
    v1 = pd.DataFrame(v1)
    v1.to_csv(out / "v1_would_certify.csv", index=False)
    print(v1.round(3).to_string())


if __name__ == "__main__":
    main()
