"""WP2 registered analyses (docs/sprint2/wp2/protocol.md): H0-H6, the three-null matrix, re-analysis.

uv run python scripts/sota_sprint/wp2_analyze.py      # writes docs/sprint2/wp2/results.json + tables.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from bench import CERTIFIED_PUBLISHED

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp2_score as S
from bench2 import NULL_TESTED

ROOT = HERE.parents[1]
OUT = ROOT / "outputs/sprint2/WP2"
DOC = ROOT / "docs/sprint2/wp2"
BOUND = 0.0936
DS = ["metro", "beijing_pm25", "bike_hour", "appliances", "household_power"]
POWERED = [
    "gated_adaptive_range",
    "gated_adaptive_range+front",
    "discern_design_floor",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "choe_ramdas_eb",
    "choe_ramdas_eb+front",
    "gated_deployment+QCE",
    "gated_deployment+QCE+front",
]
CERT = ["gated_deployment", "discern_style", *POWERED]
RMM = [
    "rmm:gated_deployment+RMM",
    "rmm:discern_style+RMM",
    "rmm:SMCS+retain-incumbent+RMM",
    "rmm:gated_adaptive_range+RMM",
]
V1SET = CERT + ["xu_acquisition_only", "QSG", "D2", *RMM]
ORDER = CERT + [
    "xu_acquisition_only",
    "QSG",
    "D2",
    *RMM,
    "A5b",
    "D5",
    "DM_HAC_monitor",
    "DM_HAC_monitor-iid",
    "economic_replacement",
    "cams_adapter",
    "cams_max_adapter",
    "model_picker_adapter",
]
MEANREV = [
    "F5_dep_null_r8",
    "F5_dep_null_r95",
    "O_null_semimarkov",
    "O_null_order2",
    "WP2_o2_null",
    "WP2_sm_null",
    "WP2_hs_null",
]
FE_SYN = ["WP2_iid_twin", "WP2_m8_twin", "WP2_o2_twin", "WP2_sm_twin", "WP2_hs_twin"]
ALTS_SYN = [
    "F0_better",
    "F5_dep_better_r8",
    "S_dep_better_r95",
    "WP2_o2_better",
    "WP2_sm_better",
    "WP2_hs_better",
]
NULLS_SYN = ["F0_null", *MEANREV, *FE_SYN]
NULL_LABEL = {
    **NULL_TESTED,
    # ShiftLab's certificate supplies a V1 test; Xu supplies only the acquisition component.
    "xu_acquisition_only": "V1 composite (ShiftLab certificate; Xu acquisition adapter)",
    # The registered WP2 protocol pools all four restart-mixture hosts in its V1-certified set.
    # bench2.NULL_TESTED lists only the gated host, so fill in the other three labels here.
    **{p: "V1" for p in RMM},
    "DM_HAC_monitor": "V2 (asymptotic)",
    "DM_HAC_monitor-iid": "V2 (iid, asymptotic)",
}


def _ci(d, k):
    return [round(d[k], 4), round(d[k + "_lo"], 4), round(d[k + "_hi"], 4)]


def pooled(df, policies):
    g = df[df.policy.isin(policies)]
    return S.score_group(g) if len(g) else None


def paired(df, a, b, metrics=("net", "delay_t", "labels", "ever_promote")):
    """Cluster-bootstrap paired difference a - b (same regime, ep, seed)."""
    k = ["regime", "ep", "seed", "cluster"]
    x = df[df.policy == a].set_index(k)[list(metrics)]
    y = df[df.policy == b].set_index(k)[list(metrics)]
    d = (x - y).dropna().reset_index()
    out = {}
    if not len(d):
        return out
    for m in metrics:
        agg = d.groupby("cluster").agg(v=(m, "sum"), n=(m, "size"), stratum=("regime", "first"))
        p, lo, hi = S.boot(agg, "v", None)
        out[m] = [round(p, 3), round(lo, 3), round(hi, 3)]
    out["clusters"] = int(d.cluster.nunique())
    return out


def matrix_rows(sc, regimes):
    """Three-target matrix: V1(H=500), V2, and the registered first-promotion EI proxy."""
    rows = []
    for _, r in sc[sc.regime.isin(regimes)].iterrows():
        rows.append(
            {
                "policy": r.policy,
                "regime": r.regime,
                "claims": NULL_LABEL.get(r.policy, "?"),
                "V1_err_100": _ci(r, "v1_err_100"),
                "V1_err_500": _ci(r, "v1_err_500"),
                "V2_err": _ci(r, "ever_promote"),
                "V3_err": _ci(r, "hp"),
                "pi_ei": _ci(r, "pi_ei") if r.ever_promote > 0 else None,
                "adv_rest": _ci(r, "adv_rest") if r.ever_promote > 0 else None,
                "harm": _ci(r, "harm"),
                "runtime_max": r.runtime_max,
            }
        )
    return rows


def reanalyse_sprint1():
    """Sprint-1 twin records (registered splits): first-promotion EI from first_deploy + losses."""
    df = pd.read_json(ROOT / "outputs/sota_sprint/twin_null/records.jsonl", lines=True)
    rows = []
    for reg, g in df.groupby("regime"):
        z = np.load(ROOT / f"data/sprint_twin_losses/{reg}.npz")
        d = z["l0"].astype(float) - z["l1"]
        rest = np.cumsum(d[:, ::-1], axis=1)[:, ::-1]  # rest[e, t] = sum_{s>=t} d[e, s]
        tau = g.first_deploy.to_numpy()
        e = g.ep.to_numpy()
        pr = tau >= 0
        rs = np.where(pr, rest[e, np.clip(tau, 0, None)], 0.0)
        a500 = np.array([d[i, t : t + 500].mean() if t >= 0 else np.nan for i, t in zip(e, tau)])
        rows.append(
            g.assign(
                kind="real",
                split=z["split"][e],
                ei=(pr & (rs - S.CS <= 0)).astype(int),
                adv_100=np.nan,
                adv_500=a500,
                adv_rest=np.where(pr, rs / np.maximum(2000 - tau, 1), np.nan),
                T=2000,
                delay_mult=1.0,
                harm=np.nan,
                db=np.nan,
            )
        )
    x = S.derive(pd.concat(rows, ignore_index=True))
    sc = S.score(x, keys=("regime", "policy"))
    res = {
        "per_cell": {
            f"{r.regime}|{r.policy}": {
                "promote": _ci(r, "ever_promote"),
                "hp": _ci(r, "hp"),
                "pi_ei": _ci(r, "pi_ei") if r.ever_promote else None,
                "adv_rest": _ci(r, "adv_rest") if r.ever_promote else None,
            }
            for _, r in sc.iterrows()
        }
    }
    pv = pooled(x, V1SET)
    res["pooled_V1"] = {
        "promote": _ci(pv, "ever_promote"),
        "hp": _ci(pv, "hp"),
        "pi_ei": _ci(pv, "pi_ei"),
        "adv_rest": _ci(pv, "adv_rest"),
    }
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--amendment-dir",
        type=Path,
        help="Write a separate corrected comparator-pool sensitivity analysis here; preserve registered output.",
    )
    ap.add_argument(
        "--exclude-xu-pool",
        action="store_true",
        help="Also remove xu_acquisition_only from pooled V1 summaries (H2/H4/H6); requires --amendment-dir.",
    )
    ap.add_argument(
        "--strict-published-dir",
        type=Path,
        help="Write a separate sensitivity using only the six shared CERTIFIED_PUBLISHED ports in V1 pools.",
    )
    args = ap.parse_args(argv)
    if args.strict_published_dir and (args.amendment_dir or args.exclude_xu_pool):
        ap.error(
            "--strict-published-dir is a separate sensitivity; do not combine it with other amendment flags"
        )
    if args.exclude_xu_pool and not args.amendment_dir:
        ap.error(
            "--exclude-xu-pool requires --amendment-dir so the registered analysis remains untouched"
        )
    global DOC, POWERED, CERT, V1SET, ORDER
    if args.strict_published_dir:
        CERT = list(CERTIFIED_PUBLISHED)
        POWERED = list(CERTIFIED_PUBLISHED)
        V1SET = list(CERTIFIED_PUBLISHED) + ["QSG", "D2", *RMM]
        # Keep non-published adapters visible as descriptive rows, while excluding them from all
        # strict-pool rankings and pooled V1 estimands.
        ORDER = list(
            dict.fromkeys(
                CERT
                + [
                    "xu_acquisition_only",
                    "choe_ramdas_eb",
                    "choe_ramdas_eb+front",
                    "gated_deployment+QCE",
                    "gated_deployment+QCE+front",
                    "QSG",
                    "D2",
                    *RMM,
                    "A5b",
                    "D5",
                    "DM_HAC_monitor",
                    "DM_HAC_monitor-iid",
                    "economic_replacement",
                    "cams_adapter",
                    "model_picker_adapter",
                ]
            )
        )
        DOC = args.strict_published_dir
        DOC.mkdir(parents=True, exist_ok=True)
    elif args.amendment_dir:
        POWERED = [p for p in POWERED if p != "xu_acquisition_only"]
        CERT = [p for p in CERT if p != "xu_acquisition_only"]
        # Preserve the historical amended sensitivity by default. A second sensitivity can remove
        # the composite from pooled H2/H4/H6 V1 summaries as well as published-method rankings.
        ORDER = list(
            dict.fromkeys(
                CERT
                + [
                    "xu_acquisition_only",
                    "QSG",
                    "D2",
                    *RMM,
                    "A5b",
                    "D5",
                    "DM_HAC_monitor",
                    "DM_HAC_monitor-iid",
                    "economic_replacement",
                    "cams_adapter",
                    "model_picker_adapter",
                ]
            )
        )
        if args.exclude_xu_pool:
            V1SET = [p for p in V1SET if p != "xu_acquisition_only"]
            ORDER = [p for p in ORDER if p != "xu_acquisition_only"]
        DOC = args.amendment_dir
        DOC.mkdir(parents=True, exist_ok=True)
    res = {}
    if args.strict_published_dir:
        res["analysis_status"] = (
            "strict published-pool sensitivity; only the six bench.CERTIFIED_PUBLISHED ports enter "
            "V1/powered pools; supplemental Xu, Choe-Ramdas and QCE adapters remain descriptive rows; "
            "same-sample pooling/selection is unadjusted"
        )
    elif args.amendment_dir:
        res["analysis_status"] = (
            "amended no-Xu pooled sensitivity; xu_acquisition_only excluded from published-method ranking, "
            "powered baseline, and pooled V1 H2/H4/H6 summaries; remaining policies are common-contract "
            "ports/adapters, not author-native deployments; same-sample pooling/selection is unadjusted"
            if args.exclude_xu_pool
            else "amended comparator-class sensitivity; xu_acquisition_only excluded from published-method "
            "comparator and powered baseline ranking but retained in pooled V1 composite results because "
            "ShiftLab supplies the test; remaining policies are common-contract ports/adapters, not "
            "author-native deployments; same-sample pooling/selection is unadjusted"
        )
    else:
        res["analysis_status"] = "registered historical analysis"
    # ---------------- H0
    res["H0"] = json.loads((ROOT / "docs/sprint2/wp2/reproduction.json").read_text())
    res["H0_pass"] = all(v["match"] for v in res["H0"].values())
    # ---------------- Run 1: v2 twins
    st2 = json.loads((ROOT / "data/sprint_twin_losses_v2/stats.json").read_text())
    r1 = S.load([OUT / "run1_twin2"])
    sc1 = S.score(r1)
    sc1.to_csv(OUT / "scores_run1.csv", index=False)
    res["K0_v2"] = {}
    for ds in DS:
        z = np.load(ROOT / f"data/sprint_twin_losses_v2/twin2_{ds}.npz")
        ps = pd.Series((z["l0"].astype(float) - z["l1"]).mean(axis=1)).groupby(z["split"]).mean()
        rng = np.random.default_rng(0)
        bs = ps.to_numpy()[rng.integers(0, len(ps), (2000, len(ps)))].mean(axis=1)
        res["K0_v2"][ds] = {
            "mean_adv": float(ps.mean()),
            "ci": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))],
            "median_rho_hat": st2[ds]["median_rho_hat"],
            "disagreement": st2[ds]["disagreement"],
        }
    reg2 = {f"twin2_{d}": d for d in DS}
    cell = lambda p, d: sc1[(sc1.policy == p) & (sc1.regime == f"twin2_{d}")].iloc[0]
    eligible = [d for d in DS if (st2[d]["median_rho_hat"] or 0) >= 0.5]
    res["H1a"] = {
        p: [
            d
            for d in eligible
            if cell(p, d).ever_promote > BOUND and cell(p, d).ever_promote_lo > 0.05
        ]
        for p in POWERED
    }
    res["H1a_n"] = sum(bool(v) for v in res["H1a"].values())
    res["H1a_pass"] = res["H1a_n"] >= 5
    res["H1b"] = {d: round(cell("A5b", d).ever_promote_hi, 4) for d in DS}
    res["H1b_pass"] = all(v <= BOUND for v in res["H1b"].values())
    v1tw = pooled(r1, V1SET)
    res["H2"] = {
        "adv_rest": _ci(v1tw, "adv_rest"),
        "pi_ei": _ci(v1tw, "pi_ei"),
        "promote": _ci(v1tw, "ever_promote"),
        "hp": _ci(v1tw, "hp"),
    }
    res["H2_pass"] = v1tw["adv_rest_lo"] > 0
    res["matrix_twin2"] = matrix_rows(sc1, list(reg2))
    # ---------------- Run 3: synthetic
    r3 = S.load([OUT / "run3_synth"])
    sc3 = S.score(r3)
    sc3.to_csv(OUT / "scores_run3.csv", index=False)
    res["matrix_synth_null"] = matrix_rows(sc3, NULLS_SYN)
    mr = pooled(r3[r3.regime.isin(MEANREV)], V1SET)
    fes = pooled(r3[r3.regime.isin(FE_SYN)], V1SET)
    res["H4"] = {
        "meanrev_pi_ei": _ci(mr, "pi_ei"),
        "fe_real_pi_ei": _ci(v1tw, "pi_ei"),
        "fe_syn_pi_ei": _ci(fes, "pi_ei"),
        "meanrev_promote": _ci(mr, "ever_promote"),
        "fe_syn_promote": _ci(fes, "ever_promote"),
    }
    res["H4_pass"] = bool(
        mr["pi_ei_lo"] >= 0.7 and v1tw["pi_ei_hi"] <= 0.5 and fes["pi_ei_hi"] <= 0.5
    )
    # per-regime pooled-V1 pi_ei and per-class precision/recall of the V1 horizon labels vs EI
    res["H4_per_regime"] = {}
    for reg, g in pd.concat([r1, r3]).groupby("regime"):
        if reg in ALTS_SYN:
            continue
        p = pooled(g, V1SET)
        res["H4_per_regime"][reg] = {
            "pi_ei": _ci(p, "pi_ei"),
            "promote": _ci(p, "ever_promote"),
            "adv_rest": _ci(p, "adv_rest"),
        }
    res["H4_labels"] = {}
    for cls, g in (
        ("meanrev", r3[r3.regime.isin(MEANREV)]),
        ("fe_syn", r3[r3.regime.isin(FE_SYN)]),
        ("fe_real", r1),
    ):
        g = g[g.policy.isin(V1SET) & (g.ever_promote == 1)]
        ei = g.ei == 1
        out = {"n_promotions": len(g), "EI_share": float(ei.mean())}
        for H in (100, 500):
            lab = g[f"adv_{H}"] <= 0
            out[f"V1_H{H}_precision"] = float((lab & ei).sum() / max(lab.sum(), 1))
            out[f"V1_H{H}_recall"] = float((lab & ei).sum() / max(ei.sum(), 1))
        out["V2_precision"] = float(ei.mean())
        out["V2_recall"] = 1.0
        res["H4_labels"][cls] = out
    # across-policy rank agreement: does a method's V2 (marginal) rate rank its V3 (harmful) rate?
    res["rank_V2_vs_V3"] = {}
    for cls, sc, regs in (
        ("meanrev", sc3, MEANREV),
        ("fe_syn", sc3, FE_SYN),
        ("fe_real", sc1, list(reg2)),
    ):
        m = (
            sc[sc.regime.isin(regs) & sc.policy.isin(ORDER)]
            .groupby("policy")[["ever_promote", "hp", "v1_err_500"]]
            .mean()
        )
        res["rank_V2_vs_V3"][cls] = {
            "spearman_V2_V3": float(m.ever_promote.rank().corr(m.hp.rank())),
            "spearman_V1_500_V3": float(m.v1_err_500.rank().corr(m.hp.rank())),
        }
    # ---------------- H5: cost of dependence robustness
    r4 = S.load([OUT / "run4_fresh"])
    sc4 = S.score(r4)
    sc4.to_csv(OUT / "scores_run4.csv", index=False)
    better = r4[r4.ep_adv > 0]
    res["H5"] = {"fresh_better": {}, "synthetic_alt": {}}
    for a, b in (
        ("A5b", "QSG"),
        ("D5", "D2"),
        ("A5b", "D2"),
        ("DM_HAC_monitor", "QSG"),
        ("A5b", "DM_HAC_monitor"),
        ("DM_HAC_monitor", "DM_HAC_monitor-iid"),
    ):
        res["H5"]["fresh_better"][f"{a}-{b}"] = paired(better, a, b)
        res["H5"]["fresh_better"][f"{a}-{b}"]["per_dataset"] = {
            d: paired(better[better.regime == d], a, b, ("net", "delay_t")) for d in DS
        }
        res["H5"]["synthetic_alt"][f"{a}-{b}"] = {
            reg: paired(r3[r3.regime == reg], a, b) for reg in ALTS_SYN
        }
    res["fresh_better_episodes"] = {
        d: int(better[(better.regime == d) & (better.policy == "QSG")].ep.nunique()) for d in DS
    }
    res["fresh_policy_table"] = {}
    sb = S.score(better, keys=("regime", "policy"))
    for _, r in sb.iterrows():
        res["fresh_policy_table"][f"{r.regime}|{r.policy}"] = {
            "net": _ci(r, "net"),
            "promote": _ci(r, "ever_promote"),
            "delay": _ci(r, "delay_t"),
            "labels": round(r.labels, 1),
            "harm": _ci(r, "harm"),
        }
    res["synth_alt_table"] = {
        f"{r.regime}|{r.policy}": {
            "net": _ci(r, "net"),
            "promote": _ci(r, "ever_promote"),
            "delay": _ci(r, "delay_t"),
            "labels": round(r.labels, 1),
            "harm": _ci(r, "harm"),
        }
        for _, r in sc3[sc3.regime.isin(ALTS_SYN)].iterrows()
    }
    # ---------------- H6: variants
    var_dirs = sorted(p for p in OUT.glob("run2_*") if (p / "records.jsonl").exists())
    r2 = S.load(var_dirs + [OUT / "run1_twin2"])
    panel_r = set(r2[r2.delay_mult != 1.0].policy) | set(r2[r2["T"] != 2000].policy)
    r2 = r2[r2.policy.isin(panel_r)]
    r2 = r2.assign(regime_base=r2.regime.str.replace(r"_T\d+$", "", regex=True))
    res["H6"] = {}
    v1r = [p for p in V1SET if p in panel_r]
    for (T, m), g in r2.groupby(["T", "delay_mult"]):
        g = g.assign(regime=g.regime_base)  # strata = dataset
        pv = pooled(g, v1r)
        a5 = {
            d: _ci(
                S.score_group(g[(g.policy == "A5b") & (g.regime == f"twin2_{d}")]), "ever_promote"
            )
            for d in DS
            if len(g[(g.policy == "A5b") & (g.regime == f"twin2_{d}")])
        }
        dm = pooled(g, ["DM_HAC_monitor"])
        res["H6"][f"T{T}_x{m}"] = {
            "V1_promote": _ci(pv, "ever_promote"),
            "V1_pi_ei": _ci(pv, "pi_ei"),
            "V1_hp": _ci(pv, "hp"),
            "A5b": a5,
            "DM_HAC_promote": _ci(dm, "ever_promote") if dm else None,
            "A5b_pass": all(v[2] <= BOUND for v in a5.values()),
        }
    res["H6a"] = {}
    for m in (0.5, 1.0, 2.0):
        seq = [
            res["H6"].get(f"T{T}_x{m}", {}).get("V1_promote", [np.nan])[0]
            for T in (1000, 2000, 4000)
        ]
        res["H6a"][str(m)] = {"rates": seq, "nondecreasing": bool(np.all(np.diff(seq) >= 0))}
    res["H6a_pass"] = all(v["nondecreasing"] for v in res["H6a"].values())
    res["H6b_pass"] = all(v["A5b_pass"] for v in res["H6"].values())
    # ---------------- sprint-1 re-analysis
    res["sprint1_reanalysis"] = reanalyse_sprint1()
    res["runtime_max_s"] = float(
        max(r1.runtime_s.max(), r3.runtime_s.max(), r4.runtime_s.max(), r2.runtime_s.max())
    )
    (DOC / "results.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    tables(res, sc1, sc3)
    print(
        json.dumps(
            {
                k: res[k]
                for k in res
                if k.endswith("_pass")
                or k in ("H1a_n", "H2", "H4", "H4_labels", "rank_V2_vs_V3", "H6a")
            },
            indent=1,
            default=float,
        )
    )


def _f(v, nd=3):
    return "" if v is None else f"{v[0]:.{nd}f} [{v[1]:.{nd}f},{v[2]:.{nd}f}]"


def tables(res, sc1, sc3):
    if "strict published" in res["analysis_status"]:
        pool_note = (
            "> **STRICT PUBLISHED-POOL SENSITIVITY:** pooled V1/H1a comparisons use only the six "
            "`bench.CERTIFIED_PUBLISHED` ports; Xu, Choe–Ramdas and QCE adapters appear only as "
            "separate descriptive rows. Same-sample pooling/selection is unadjusted."
        )
    elif "pooled sensitivity" in res["analysis_status"]:
        pool_note = (
            "> **AMENDED NO-XU POOLED SENSITIVITY:** Xu acquisition composite excluded from published-method "
            "ranking, H1a powered-baseline set, and pooled V1 H2/H4/H6 summaries. Remaining policies are "
            "common-contract ports/adapters, not author-native deployments. Registered runs/outputs are "
            "unchanged; selection is unadjusted."
        )
    elif "amended" in res["analysis_status"]:
        pool_note = (
            "> **AMENDED SENSITIVITY:** Xu excluded from published-method comparator ranking and H1a "
            "powered-baseline set, but retained in pooled V1 as a ShiftLab-certificate composite. "
            "Remaining policies are common-contract ports/adapters, not author-native deployments. "
            "Registered runs/outputs are unchanged; selection is unadjusted."
        )
    else:
        pool_note = (
            "> **Historical-pool caveat:** `xu_acquisition_only` is an acquisition adapter using "
            "the benchmark's certificate, not Xu et al.'s published certificate. The registered "
            "V1 pools include it; see `DECISION_FLAG_AUDIT.md` before interpreting those values "
            "as results for Xu's published certificate."
        )
    L = [
        "# WP2 generated tables",
        "",
        (
            "Generated by `scripts/sota_sprint/wp2_analyze.py` from the run directories in "
            "outputs/sprint2/WP2. 95% cluster-bootstrap CIs (split for real twins, seed for synthetic)."
        ),
        "",
        pool_note,
        "",
    ]
    L += [
        "## Three-null matrix, v2 real twins (20 new splits)",
        "",
        (
            "Columns per dataset: V2 = promote on a marginal null, V1(500) = promote and realised next-500 advantage <= 0, "
            "V3 (registered EI proxy) = first promotion with hold-to-end benefit - c_s <= 0; mean all-in excess economic cost = mean J - J(never). "
            "EI excludes label spend and ignores later rollback. Its prediction-loss, label-cost, and switch-cost components, plus the positive-cost rate, "
            "are reported separately in `REALIZED_HARM.md`. The historical raw field `harm` does not denote application-level decision harm."
        ),
        "",
    ]
    for ds in DS:
        L += [
            f"### {ds}",
            "",
            "| policy | claims | V2 | V1(100) | V1(500) | V3 (EI proxy) | P(EI given promote) | adv_rest at promotion | mean all-in excess cost |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        rows = {r["policy"]: r for r in res["matrix_twin2"] if r["regime"] == f"twin2_{ds}"}
        for p in ORDER:
            if p in rows:
                r = rows[p]
                L.append(
                    f"| {p} | {r['claims']} | {_f(r['V2_err'])} | {_f(r['V1_err_100'])} | {_f(r['V1_err_500'])} | "
                    f"{_f(r['V3_err'])} | {_f(r['pi_ei'], 2)} | {_f(r['adv_rest'], 4)} | {_f(r['harm'], 1)} |"
                )
        L.append("")
    L += ["## Three-null matrix, synthetic nulls (50 seeds)", ""]
    for reg in NULLS_SYN:
        rows = {r["policy"]: r for r in res["matrix_synth_null"] if r["regime"] == reg}
        if not rows:
            continue
        L += [
            f"### {reg}",
            "",
            "| policy | claims | V2 | V1(100) | V1(500) | V3 (EI proxy) | P(EI given promote) | mean all-in excess cost |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for p in ORDER:
            if p in rows:
                r = rows[p]
                L.append(
                    f"| {p} | {r['claims']} | {_f(r['V2_err'])} | {_f(r['V1_err_100'])} | {_f(r['V1_err_500'])} | "
                    f"{_f(r['V3_err'])} | {_f(r['pi_ei'], 2)} | {_f(r['harm'], 1)} |"
                )
        L.append("")
    L += [
        "## Fresh real episodes where the challenger realised better (adv > 0), 3 policy seeds",
        "",
        "| policy | " + " | ".join(DS) + " |",
        "|---|" + "---|" * len(DS),
    ]
    for p in ORDER + ["CONTROL_never_switch"]:
        cells = []
        for d in DS:
            v = res["fresh_policy_table"].get(f"{d}|{p}")
            cells.append(
                ""
                if v is None
                else f"J {v['net'][0]:.1f}; prom {v['promote'][0]:.2f}; delay {v['delay'][0]:.0f}; lab {v['labels']:.0f}"
            )
        L.append(f"| {p} | " + " | ".join(cells) + " |")
    L += [
        "",
        "## Synthetic dependent alternatives (50 seeds)",
        "",
        "| policy | " + " | ".join(ALTS_SYN) + " |",
        "|---|" + "---|" * len(ALTS_SYN),
    ]
    for p in ORDER + ["CONTROL_never_switch"]:
        cells = []
        for reg in ALTS_SYN:
            v = res["synth_alt_table"].get(f"{reg}|{p}")
            cells.append(
                ""
                if v is None
                else f"J {v['net'][0]:.1f}; prom {v['promote'][0]:.2f}; delay {v['delay'][0]:.0f}"
            )
        L.append(f"| {p} | " + " | ".join(cells) + " |")
    # H5 registered matched contrasts, omitted from the original generated report. Negative
    # values favor the first-named policy. Fresh-real rows are conditioned on realized positive
    # advantage and use dataset-cluster bootstrap intervals; synthetic rows are paired by seed.
    L += [
        "",
        "## H5 paired cost-of-robustness contrasts",
        "",
        (
            "Negative differences favor the first-named method. The fresh-real subset conditions on "
            "realized positive challenger advantage (not a prospective selection rule); its 56 "
            "episode clusters are grouped within five datasets. Intervals are 95% paired cluster "
            "bootstrap intervals for real data and paired seed-bootstrap intervals for synthetic "
            "regimes. These are descriptive development comparisons."
        ),
        "",
        "### Fresh real, realized advantage > 0 (A5b−QSG and D5−D2)",
        "",
        "| contrast | ΔJ | Δ first-promotion delay | Δ labels | Δ promotion rate | clusters |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for contrast in ("A5b-QSG", "D5-D2"):
        v = res["H5"]["fresh_better"][contrast]

        def fmt_ci(x, digits=1):
            return f"{x[0]:+.{digits}f} [{x[1]:+.{digits}f}, {x[2]:+.{digits}f}]"

        L.append(
            f"| {contrast} | {fmt_ci(v['net'])} | {fmt_ci(v['delay_t'])} | "
            f"{fmt_ci(v['labels'])} | {fmt_ci(v['ever_promote'], 3)} | {v['clusters']} |"
        )
    L += [
        "",
        "### Synthetic dependent alternatives (50 paired seeds)",
        "",
        "| regime | contrast | ΔJ | Δ first-promotion delay | Δ labels | Δ promotion rate |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for reg in ALTS_SYN:
        for contrast in ("A5b-QSG", "D5-D2"):
            v = res["H5"]["synthetic_alt"][contrast][reg]
            L.append(
                f"| {reg} | {contrast} | {fmt_ci(v['net'])} | {fmt_ci(v['delay_t'])} | "
                f"{fmt_ci(v['labels'])} | {fmt_ci(v['ever_promote'], 3)} |"
            )
    (DOC / "tables.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
