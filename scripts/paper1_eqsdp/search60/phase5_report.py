"""Phase 5: best config per size k, panel comparison, PHASE5_REPORT.md (every number from records)."""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import run_phase345 as p
from phase3_report import md

SC = "out_of_subset"
MAIN = p.Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
PANEL_DIR = MAIN / "outputs/qsg_methods_search/sota_expansion"
sys.path.insert(0, str(MAIN / "scripts/qsg_methods_search"))


def panel_lists():
    src = (MAIN / "scripts/qsg_methods_search/analyze_all.py").read_text(encoding="utf-8")
    ns = {}
    for name in ("ADAPTERS", "CONTROLS"):
        i = src.index(f"\n{name} = [") + 1
        j = src.index("\n]", i) + 2
        exec(src[i:j], ns)  # noqa: S102 - literal list from our own repo
    return ns["ADAPTERS"], ns["CONTROLS"]


def load_panel(streams):
    fr = []
    for t in ("nine", "nine_armR", "batch2"):
        d = pd.read_json(PANEL_DIR / t / "records.jsonl", lines=True, dtype={"policy": str})
        fr.append(
            d[d.stream.isin(streams)][
                ["stream", "ep", "seed", "policy", "net", "loss", "labels", "switches"]
            ]
        )
    d = pd.concat(fr).drop_duplicates(["stream", "ep", "seed", "policy"])
    return d.rename(columns={"policy": "config_id"})


def full_tags():
    return sorted(q.name for q in p.RUN.glob("p[34]*") if (q / "DONE").exists() and (q / "records.jsonl").exists()
                  and not q.name.startswith("p4_cal"))  # fmt: skip


def all_stats(df, ref, w1, ledger_k, rng):
    rows = []
    for n in sorted(df.config_id.unique()):
        if n == p.PARENT:
            continue
        g = p.pair(df[df.config_id == n], ref)
        for scope, gg in (("out_of_subset", g[~g.in_sub]), ("all", g)):
            s = p.stats(gg, rng)
            gw = p.pair(df[df.config_id == n], w1)
            gw = gw if scope == "all" else gw[~gw.in_sub]
            sw = p.stats(gw, rng)
            s.update(config_id=n, scope=scope, k=ledger_k.get(n, -1), vs_w98_dJ=sw["dJ"], vs_w98_lo=sw["dJ_lo"], vs_w98_hi=sw["dJ_hi"],
                     vs_w98_dL=sw["dL"])  # fmt: skip
            rows.append(s)
    return pd.DataFrame(rows)


def panel_cmp(df, cfg_names, panel, adapters, controls, ref, rng):
    """cfg minus each panel comparator on matched (stream, ep, seed) keys, equal-dataset, out-of-subset and all."""
    out = []
    pols = adapters + controls + ["EQSDp_l0.98_g0.3"]
    for n in cfg_names:
        c = df[df.config_id == n]
        for pol in pols:
            d = panel[panel.config_id == pol]
            if d.empty:
                continue
            g = p.pair(c, d)
            if g.empty:
                continue
            for scope, gg in (("out_of_subset", g[~g.in_sub]), ("all", g)):
                s = p.stats(gg, rng)
                out.append({"config_id": n, "comparator": pol, "kind": "adapter" if pol in adapters else "control", "scope": scope,
                            "dJ": s["dJ"], "lo": s["dJ_lo"], "hi": s["dJ_hi"], "dL": s["dL"], "n_streams": gg.stream.nunique()})  # fmt: skip
    return pd.DataFrame(out)


def per_ds_table(df, n, ref, w1, w2, scope):
    c = df[df.config_id == n]
    rows = {}
    for lab, r in (("vs parent", ref), ("vs Wald .98/.3+cut", w1), ("vs Wald .97/.2+cut", w2)):
        g = p.pair(c, r)
        g = g if scope == "all" else g[~g.in_sub]
        x = g.groupby("stream").dJ.mean()
        rows[lab] = {**x.to_dict(), "EQUAL-MEAN": x.mean()}
    g = p.pair(c, ref)
    g = g if scope == "all" else g[~g.in_sub]
    rows["dL vs parent (pp)"] = {
        **g.groupby("stream").dL.mean().to_dict(),
        "EQUAL-MEAN": p.eqmean(g, "dL"),
    }
    rows["labels"] = {**g.groupby("stream").lab.mean().to_dict(), "EQUAL-MEAN": p.eqmean(g, "lab")}
    t = pd.DataFrame(rows).T.reset_index().rename(columns={"index": "row"})
    return t


def main():
    rng = np.random.default_rng(20261111)
    tags = full_tags()
    df = p.load_tags(tags)
    led = {
        r["source_config_id"]: r
        for r in p.r12.ledger_rows()
        if r.get("eval") == "full" and r.get("modules") is not None
    }
    k_of = {n: len(r["modules"]) for n, r in led.items()}
    wald_variant = {n for n, r in led.items() if r.get("parent", {}).get("kind") == "wald"}
    ref = df[df.config_id == p.PARENT]
    w1, w2 = df[df.config_id == p.W1], df[df.config_id == p.W2]
    A = all_stats(df[~df.config_id.isin(wald_variant)], ref, w1, k_of, rng)
    A.to_csv(p.TABLES / "phase5_all_full_configs.csv", index=False)
    cand = A[(A.scope == SC) & (A.k >= 1)]
    best = {
        k: cand[cand.k == k].sort_values("dJ").iloc[0].config_id
        for k in range(1, 6)
        if (cand.k == k).any()
    }
    streams = list(df.stream.unique())
    adapters, controls = panel_lists()
    panel = load_panel(streams)
    # sanity: arm R in panel vs our full run on matched keys
    ours = df[df.config_id == "EQSDp_l0.98_g0.3"].merge(
        panel[panel.config_id == "EQSDp_l0.98_g0.3"],
        on=["stream", "ep", "seed"],
        suffixes=("", "_p"),
    )
    san = {"matched_rows": len(ours), "net_mismatch": int((ours.net != ours.net_p).sum())}
    pc = panel_cmp(df, [*best.values(), p.PARENT, p.W1], panel, adapters, controls, ref, rng)
    pc.to_csv(p.TABLES / "phase5_panel_comparison.csv", index=False)
    L = [
        "# Paper 1 search60: Phase 5 report",
        "",
        (
            "Status: development-stage search results. Every number is generated by `scripts/paper1_eqsdp/search60/phase5_report.py` from full-data records; "
            "no originality or validity claim; mechanism novelty is unknown until audited."
        ),
        "",
        "## Selection exposure (exact)",
        "- All nine datasets and both episode parities (odd and even) are development-exposed; they were used in Stages 1-5 and now in Phases 1-5.",
        (
            "- Phase 1-2 screening used 12 episodes per dataset (subset `S60-3c5e68d4d4`, seeds 0-1). The primary statistic below uses only episodes outside this subset; "
            "that is a partial guard against screen selection only. Phases 3-4 and the choice of best-k configs below are further selection on the same out-of-subset episodes "
            "(about 100+ configs examined on them), so the reported out-of-subset dJ values are still optimistic."
        ),
        "- F59 was trained on even episodes of these datasets; its results are not out-of-sample on the even parity.",
        "- Independent confirmation (fresh data, locked config and rule) is a separate future step and has not been done.",
        "",
        "## Setup",
        (
            "J = net cost / T x 100 (pp of T); L = loss / T x 100; paired against parent `s2armr_H1100` (arm R lam .98 gamma .3, cutoff 1100) on identical (dataset, episode, seed) keys, "
            "10 seeds, equal dataset weights, seed-averaged per episode; 95% CI = stratified episode bootstrap (2000 resamples). Negative dJ = better than parent. "
            f"Tags used: {', '.join(tags)}. Panel sanity (our `EQSDp_l0.98_g0.3` vs panel record, matched keys): {json.dumps(san)}."
        ),
        "",
    ]
    L += [
        "## Best config at each size k (primary statistic: out-of-subset dJ, over all full-data configs of Phases 3-4)",
        "",
    ]
    cols = [
        "k",
        "config_id",
        "dJ",
        "pct",
        "dJ_lo",
        "dJ_hi",
        "dL",
        "labels",
        "switches",
        "dLA",
        "dFP",
        "vs_w98_dJ",
        "vs_w98_lo",
        "vs_w98_hi",
    ]
    rows = []
    for k, n in best.items():
        r = A[(A.scope == SC) & (A.config_id == n)].iloc[0]
        rows.append({c: r[c] for c in cols} | {"config_id": n})
    L += [md(pd.DataFrame(rows), {"pct": "{:.2f}"}), ""]
    for k, n in best.items():
        txt = led[n]["modules"]
        mods = "+".join(f"{m['id']}[s{m['setting']}]" for m in txt)
        L += [
            f"### k={k}: `{n}` ({mods})",
            "Out-of-subset, 9 datasets (pp of T):",
            md(per_ds_table(df, n, ref, w1, w2, SC)),
            "",
            "All episodes:",
            md(per_ds_table(df, n, ref, w1, w2, "all")),
            "",
        ]
    L += [
        "## Three separate comparisons",
        "",
        "### (a) Direct superiority over matched Wald+cutoff (config minus control, out-of-subset)",
    ]
    ra = [{"k": k, "config_id": n, **{c: A[(A.scope == SC) & (A.config_id == n)].iloc[0][c] for c in ("vs_w98_dJ", "vs_w98_lo", "vs_w98_hi", "vs_w98_dL")}}
          for k, n in best.items()]  # fmt: skip
    L += [md(pd.DataFrame(ra)), ""]
    ref_rows = A[(A.scope == SC) & A.config_id.isin([p.W1, p.W2])][
        ["config_id", "dJ", "dJ_lo", "dJ_hi", "dL", "labels"]
    ]
    L += ["Controls minus parent (out-of-subset):", md(ref_rows), ""]
    tr = p.TABLES / "phase4_wald_transfer.csv"
    L += [
        "### (b) Wald-transferable add-on (Phase 4; Wald lam .98 gamma .3 + cutoff 1100 + same modules)"
    ]
    if tr.exists():
        t = pd.read_csv(tr)
        t = t[t.scope == SC] if "scope" in t and (t.scope == SC).any() else t
        L += [md(t), ""]
    else:
        L += ["not run", ""]
    L += ["### (c) Wins over unchanged comparator adapters (original panel, matched keys)"]
    pcs = pc[pc.scope == SC]
    sm = []
    for n in [*best.values(), p.PARENT, p.W1]:
        g = pcs[pcs.config_id == n]
        for kind in ("adapter", "control"):
            h = g[g.kind == kind]
            sm.append({"config_id": n, "kind": kind, "n_comparators": len(h), "wins_ci_below0": int((h.hi < 0).sum()), "dJ_negative": int((h.dJ < 0).sum()),
                       "worst_dJ_vs_panel": float(h.dJ.max()) if len(h) else np.nan})  # fmt: skip
    L += [
        md(pd.DataFrame(sm)),
        "",
        (
            "(`worst_dJ_vs_panel` = largest candidate-minus-comparator dJ, i.e. the strongest comparator; positive means that comparator is better.) "
            "Panel streams matched to our nine datasets; see `tables/phase5_panel_comparison.csv`."
        ),
        "",
    ]
    for name, f in (("Ablations (full data)", "phase4_ablation.csv"), ("Matched label-count controls", "phase4_matched_controls.csv"),
                    ("Pair synergy (full data)", "phase4_synergy_pairs.csv")):  # fmt: skip
        fp = p.TABLES / f
        L += [
            f"## {name}",
            f"Source `tables/{f}` (out-of-subset rows shown; `all` scope in CSV).",
            "",
        ]
        if fp.exists():
            t = pd.read_csv(fp)
            if "scope" in t:
                t = t[t.scope == SC]
            L += [md(t.head(80)), ""]
        else:
            L += ["not run", ""]
    L += [
        "Interaction heatmap: `tables/phase4_synergy_heatmap.csv`, `phase4_synergy_heatmap.png` (matplotlib diagnostic; PaperBanana is not installed in this environment, so no PaperBanana figure was produced).",
        "",
    ]
    a = p.DOCS / "PHASE5_ASSESSMENT.txt"
    L += [
        "## Continue / pivot / stop assessment",
        a.read_text(encoding="utf-8") if a.exists() else "(pending)",
        "",
    ]
    L += [
        "## Sources and reproduction",
        "- Records: `outputs/paper1_eqsdp/search60/full/p3_*`, `p4_*`, `p4g_full` (`records.jsonl`); ledger `outputs/paper1_eqsdp/search60/ledger.jsonl` (rows with `eval=full`, `phase` in 3, 4, 4G, 4GF).",
        "- Tables: `docs/paper1_eqsdp/search60/tables/phase3_*.csv`, `phase4_*.csv`, `phase5_*.csv`.",
        "- Commands (`OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8`, repo venv python): `run_phase345.py p3run`, `p3check`, `p3analyze`, `p4select`, `p4run`, `p4cal`, `p4analyze`, `p4guided`, `p4gsub`, `p4gfull`, `p5report`.",
        "- Panel records: `shift-research-starter/outputs/qsg_methods_search/sota_expansion/{nine,nine_armR,batch2}/records.jsonl`; comparator lists ADAPTERS and CONTROLS in `scripts/qsg_methods_search/analyze_all.py`.",
    ]
    (p.DOCS / "PHASE5_REPORT.md").write_text("\n".join(L), encoding="utf-8")
    print("best per k:", best, san)


if __name__ == "__main__":
    main()
