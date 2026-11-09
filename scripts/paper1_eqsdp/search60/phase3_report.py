"""Phase 3 analysis: tables/phase3_*.csv, Pareto archive, PHASE3_RESULTS.md (all numbers from records)."""

from __future__ import annotations

import json

import pandas as pd
import run_phase345 as p

SC = "out_of_subset"


def md(df, fmt=None):
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                v = fmt.get(c, "{:.3f}").format(v)
            cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def add_synergy(S, scope):
    """Full-data additive-expectation synergy: dJ(config) - sum dJ(single module at same setting)."""
    sc = p.screen_rows()
    single = S[(S.scope == scope)].set_index("config_id").dJ.to_dict()
    syn = {}
    for _, r in S[S.scope == scope].iterrows():
        m = sc.get(r.config_id)
        if not m or len(m["modules"]) < 2:
            continue
        ks = [f"P1_{x['id']}_s{x['setting']}" for x in m["modules"]]
        if all(k in single for k in ks):
            syn[r.config_id] = r.dJ - sum(single[k] for k in ks)
    return syn


def archive(S, per):
    sh = S[(S.scope == SC) & (S.kind_sl == "shortlist")].copy()
    syn = add_synergy(S, SC)
    sh["synergy"] = sh.config_id.map(syn)
    roles = {}
    roles["lowest_cost"] = sh.sort_values("dJ").iloc[0].config_id
    par = sh[sh.dL <= 0]
    roles["best_error_parity"] = (
        (par if len(par) else sh).sort_values("dJ" if len(par) else "dL").iloc[0].config_id
    )
    roles["strongest_downside_cvar95"] = sh.sort_values("cvar95").iloc[0].config_id
    s2 = sh.dropna(subset=["synergy"])
    roles["highest_synergy"] = s2.sort_values("synergy").iloc[0].config_id
    roles["best_late_change_kc_sf"] = sh.sort_values("late_dJ").iloc[0].config_id
    return roles, sh


def main():
    S, per, _df = p.p3_tables()
    meta = {
        r["source_config_id"]: r
        for r in p.r12.ledger_rows()
        if r.get("eval") == "full" and r.get("phase") == "3"
    }
    S["kind_sl"] = S.config_id.map(lambda c: meta.get(c, {}).get("kind", "control"))
    S["kind_sl"] = S.kind_sl.where(~S.config_id.isin(p.CONTROLS), "control")
    roles, sh = archive(S, per)
    S.to_csv(p.TABLES / "phase3_summary.csv", index=False)
    rows = []
    for role, cid in roles.items():
        for scope in (SC, "all"):
            pd_ = per[(per.config_id == cid) & (per.scope == scope)]
            for _, r in pd_.iterrows():
                rows.append(
                    {
                        "role": role,
                        "config_id": cid,
                        "scope": scope,
                        "dataset": r.dataset,
                        "dJ": r.dJ,
                    }
                )
    pd.DataFrame(rows).to_csv(p.TABLES / "phase3_pareto_archive.csv", index=False)
    top = sh.sort_values("dJ")
    fmt = {"pct": "{:.2f}", "pct_lo": "{:.2f}", "pct_hi": "{:.2f}"}
    cols = [
        "config_id",
        "k",
        "dJ",
        "pct",
        "dJ_lo",
        "dJ_hi",
        "dL",
        "labels",
        "switches",
        "dLA",
        "dFP",
        "p95",
        "cvar95",
        "vs_w98_dJ",
        "vs_w98_lo",
        "vs_w98_hi",
        "vs_w97_dJ",
    ]
    n_sig = int((top.dJ_hi < 0).sum())
    n_neg = int((top.dJ < 0).sum())
    n_all_sig = int(((S[(S.scope == "all") & (S.kind_sl == "shortlist")].dJ_hi) < 0).sum())
    chk = json.loads((p.OUT / "p3_parent_check.json").read_text())
    L = [
        "# Paper 1 search60 Phase 3: full matched development evaluation",
        "",
        (
            "Status: development-stage results. All nine datasets and both episode parities are development-exposed; the 40 configs were selected on a screen subset, "
            "so the primary statistic uses only episodes outside the screen subset (`SCREEN_SUBSET.json`, partial guard only). No originality or validity claim."
        ),
        "",
        (
            "Protocol: `split=all` (every episode of nine datasets), policy seeds 0-9, registered seed derivation, paired against parent `s2armr_H1100` on identical (dataset, episode, seed) keys, "
            "seed-averaged per episode, equal dataset weights. J = net cost / T x 100 (pp of T), L = prediction loss / T x 100. "
            f"CI = 95% stratified episode bootstrap ({p.BOOT} resamples, seed 20261109). pct = dJ / parent J x 100. "
            "dLA / dFP = change in late-adoption / false-promotion regret components (pp of T, from `trace_run.decompose`). p95/CVaR95 = over paired episode dJ."
        ),
        "",
        "Source: `outputs/paper1_eqsdp/search60/full/p3_*/records.jsonl`; ledger rows with `phase=3, eval=full`; tables `docs/paper1_eqsdp/search60/tables/phase3_*.csv`.",
        "Commands: `python scripts/paper1_eqsdp/search60/run_phase345.py p3run|p3check|p3analyze`.",
        "",
        "## Parent reproduction",
        f"`s2armr_H1100` in the new run vs existing records: {json.dumps(chk)}",
        "",
        "## Headline",
        f"Of the 40 shortlisted configs, {n_neg} have out-of-subset dJ < 0; {n_sig} have the 95% CI excluding 0 on the negative side (all-episode: {n_all_sig}).",
        "",
        "## Shortlist ranked by primary dJ (out-of-subset), top 15 of 40",
        md(top.head(15)[cols], fmt),
        "",
        "## Controls vs parent (out-of-subset)",
        md(
            S[(S.scope == SC) & S.config_id.isin(p.CONTROLS)][
                ["config_id", "dJ", "pct", "dJ_lo", "dJ_hi", "dL", "labels", "switches"]
            ],
            fmt,
        ),
        "",
        "## Pareto archive (out-of-subset; full nine-dataset tables in `phase3_pareto_archive.csv`)",
    ]
    for role, cid in roles.items():
        r = sh[sh.config_id == cid].iloc[0]
        L.append(
            f"- **{role}**: `{cid}` ({r.txt}) dJ={r.dJ:.3f} [{r.dJ_lo:.3f}, {r.dJ_hi:.3f}] ({r.pct:.2f}%), dL={r.dL:.3f}, cvar95={r.cvar95:.2f}, synergy={r.synergy:.3f}"
            if pd.notna(r.synergy)
            else f"- **{role}**: `{cid}` ({r.txt}) dJ={r.dJ:.3f} [{r.dJ_lo:.3f}, {r.dJ_hi:.3f}] ({r.pct:.2f}%), dL={r.dL:.3f}, cvar95={r.cvar95:.2f}, late_dJ={r.late_dJ:.3f}"
        )
    ar = pd.read_csv(p.TABLES / "phase3_pareto_archive.csv")
    ar = ar[ar.scope == SC].pivot_table(index="role", columns="dataset", values="dJ").reset_index()
    L += ["", "Per-dataset dJ of archive entries (out-of-subset):", md(ar), ""]
    L += ["## All 40 (out-of-subset), full columns", "see `tables/phase3_summary.csv`.", ""]
    (p.DOCS / "PHASE3_RESULTS.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote", roles)


if __name__ == "__main__":
    main()
