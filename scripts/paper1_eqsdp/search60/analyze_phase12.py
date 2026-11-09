"""Phase 1/2 analysis: registry CSV, synergy table + heatmap, shortlist, PHASE12_RESULTS.md.

All numbers are read from outputs/paper1_eqsdp/search60/ledger.jsonl and the records files it points to.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import run_phase12 as rp

OUT, DOCS, ROOT = rp.OUT, rp.DOCS, rp.ROOT
COLS = ["config_id", "phase", "k", "modules_txt", "status", "delta_j", "se_j", "delta_loss_pp", "d_labels",
        "d_switches", "worst_ep_dj", "p95_dj", "cvar95_dj", "inert", "runtime_ratio", "anchor"]  # fmt: skip


def mtxt(r):
    return "+".join(f"{m['id']}[s{m['setting']}]" for m in r.get("modules", []))


def md(df, floatfmt="{:.3f}"):
    if df.empty:
        return "_(none)_\n"
    h = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    body = ""
    for _, r in df.iterrows():
        body += (
            "| "
            + " | ".join(floatfmt.format(v) if isinstance(v, float) else str(v) for v in r)
            + " |\n"
        )
    return h + body


def episode_vec(row, parent, cache):
    """seed-averaged paired (dJ, dL) per (stream, ep) for one ledger row."""
    p = row["records_path"]
    if p not in cache:
        cache[p] = rp.load_records(ROOT / p)
    d = cache[p]
    d = d[d.config_id == row["config_id"]]
    g, *_ = rp.paired(d, parent)
    return g


def synergy(L, parent):
    cache, rows = {}, []
    for n, r in L.items():
        if r.get("k") != 2 or r.get("phase") not in (2, "2G", "2A"):
            continue
        a, b = r["modules"]
        refs = []
        for m in (a, b):
            ref = L.get(f"P1_{m['id']}_s{m['setting']}")
            refs.append(ref)
        if any(x is None for x in refs):
            continue
        gab, ga, gb = (episode_vec(x, parent, cache) for x in (r, *refs))
        s = (gab[["dJ"]] - ga[["dJ"]] - gb[["dJ"]]).rename(columns={"dJ": "syn"})
        mu = s.syn.groupby(level=0).mean()
        se = float(
            np.sqrt((s.syn.groupby(level=0).var(ddof=1) / s.syn.groupby(level=0).count()).sum())
            / len(mu)
        )
        rows.append({"pair": f"{a['id']}+{b['id']}", "a": a["id"], "b": b["id"], "config_id": n, "phase": r["phase"],
                     "syn": float(mu.mean()), "se": se, "delta_j": r["delta_j"],
                     "dJ_a": refs[0]["delta_j"], "dJ_b": refs[1]["delta_j"]})  # fmt: skip
        if len(cache) > 40:
            cache.clear()
    return pd.DataFrame(rows)


def heatmap(syn, ids):
    M = pd.DataFrame(np.nan, index=ids, columns=ids)
    pref = {2: 0, "2G": 1, "2A": 2}
    for _, r in syn.assign(o=syn.phase.map(pref)).sort_values("o", ascending=False).iterrows():
        M.loc[r.a, r.b] = M.loc[r.b, r.a] = r.syn  # lowest-priority first, so base overwrites last
    M.to_csv(OUT / "synergy_heatmap.csv")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    v = np.nanmax(np.abs(M.values)) if np.isfinite(M.values).any() else 1
    fig, ax = plt.subplots(figsize=(11, 10))
    im = ax.imshow(M.values, cmap="RdBu", vmin=-v, vmax=v)
    ax.set_xticks(range(len(ids)), ids, rotation=90, fontsize=5)
    ax.set_yticks(range(len(ids)), ids, fontsize=5)
    fig.colorbar(im, label="synergy (pp of T); negative = complementary")
    ax.set_title("Pairwise synergy J(A+B)-J(A)-J(B)+J(parent); blank = untested (diagnostic only)")
    fig.tight_layout()
    fig.savefig(DOCS / "synergy_heatmap.png", dpi=130)
    plt.close(fig)
    M.to_csv(DOCS / "synergy_heatmap.csv")


def jac(a, b):
    return len(a & b) / len(a | b)


def shortlist(df, anchors_ok, syn, parent_late, n=40):
    pool = df[(df.status == "OK") & (~df.inert) & (df.delta_loss_pp <= 0.1)].sort_values("delta_j")
    allok = df[(df.status == "OK") & (~df.inert)]
    sel, why = [], {}

    def add(cfg, role):
        if cfg not in why:
            sel.append(cfg)
            why[cfg] = role
        else:
            why[cfg] += "," + role

    add(allok.sort_values("delta_j").iloc[0].config_id, "lowest_cost")
    add(allok.sort_values(["delta_loss_pp", "delta_j"]).iloc[0].config_id, "best_error_parity")
    add(allok.sort_values("cvar95_dj").iloc[0].config_id, "best_downside_cvar95")
    if len(syn):
        s = syn.sort_values("syn").iloc[0]
        add(s.config_id, f"highest_synergy({s.pair})")
    late_ds = parent_late
    for ds, nm in (
        (late_ds, f"late_proxy_largest_parent_late_adoption({late_ds})"),
        ("kc_311", "late_proxy_kc_311"),
    ):
        col = allok.per_dataset.map(lambda d, ds=ds: d.get(ds, np.inf))
        add(allok.loc[col.idxmin()].config_id, nm)
    for a in anchors_ok:
        add(a, "anchor_ok")
    quota = {1: 4, 2: 9, 3: 9, 4: 8, 5: 6}
    cnt = {k: sum(1 for c in sel if df.set_index("config_id").loc[c, "k"] == k) for k in quota}
    fam = {}
    for relax in (0, 1):
        for _, r in pool.iterrows():
            if len(sel) >= n:
                break
            if r.config_id in why:
                continue
            ms = set(r.mods)
            if any(jac(ms, set(df.set_index("config_id").loc[c, "mods"])) > 0.5 for c in sel):
                continue
            sig = "".join(sorted({m[0] for m in ms}))
            if not relax and (cnt[r.k] >= quota[r.k] or fam.get(sig, 0) >= 3):
                continue
            add(r.config_id, "diversified_fill")
            cnt[r.k] += 1
            fam[sig] = fam.get(sig, 0) + 1
    return sel, why


def main():
    rows = rp.ledger_rows()
    L = {r["config_id"]: r for r in rows if r.get("status") == "OK" and "modules" in r}
    parent = rp.parent_df()
    sub = rp.subset()
    # ---- registry
    reg = []
    for r in rows:
        if r.get("kind") == "control":
            continue
        reg.append({"config_id": r["config_id"], "phase": r.get("phase"), "k": r.get("k", 1), "modules_txt": mtxt(r),
                    "status": r["status"], **{c: r.get(c) for c in COLS[5:-1]}, "anchor": r.get("anchor", False)})  # fmt: skip
    R = pd.DataFrame(reg)[COLS]
    R.to_csv(DOCS / "registry_phase12.csv", index=False)
    df = pd.DataFrame(
        [
            {
                "config_id": n,
                "phase": r.get("phase"),
                "k": r.get("k", 1),
                "combo_id": r.get("combo_id"),
                "mods": [m["id"] for m in r["modules"]],
                "txt": mtxt(r),
                "per_dataset": r["per_dataset_dj"],
                "status": "OK",
                "anchor": r.get("anchor", False),
                **{
                    c: r[c]
                    for c in (
                        "delta_j",
                        "se_j",
                        "delta_loss_pp",
                        "d_labels",
                        "d_switches",
                        "worst_ep_dj",
                        "p95_dj",
                        "cvar95_dj",
                        "inert",
                        "runtime_ratio",
                    )
                },
            }
            for n, r in L.items()
        ]
    )
    # ---- phase 1
    p1 = df[df.phase == 1].copy()
    p1["module"] = p1.mods.map(lambda m: m[0])
    p1["setting"] = p1.config_id.str[-1].astype(int)
    best = p1.sort_values("delta_j").groupby("module").head(1)
    t1 = p1.pivot(index="module", columns="setting", values="delta_j")
    t1.columns = ["dJ_s0", "dJ_s1"]
    for c in (
        "se_j",
        "delta_loss_pp",
        "d_labels",
        "d_switches",
        "worst_ep_dj",
        "cvar95_dj",
        "runtime_ratio",
    ):
        t1[c] = best.set_index("module")[c]
    t1["inert_s0"] = p1[p1.setting == 0].set_index("module").inert
    t1["inert_s1"] = p1[p1.setting == 1].set_index("module").inert
    t1["best"] = best.set_index("module").setting
    t1["best_dJ"] = t1[["dJ_s0", "dJ_s1"]].min(axis=1)
    t1 = t1.sort_values("best_dJ").reset_index()
    t1.to_csv(OUT / "phase1_table.csv", index=False)
    inert = t1[t1.inert_s0 & t1.inert_s1].module.tolist()
    half_inert = t1[(t1.inert_s0 ^ t1.inert_s1)].module.tolist()
    # ---- synergy
    syn = synergy(L, parent)
    syn.to_csv(OUT / "synergy_pairs.csv", index=False)
    heatmap(syn, sorted(comp_ids()))
    # ---- per-k tops (k=1 from P1 best)
    allc = pd.concat([best.assign(k=1), df[df.phase != 1]])
    allc["id"] = allc.config_id
    allc.drop(columns=["per_dataset", "mods"]).to_csv(OUT / "all_configs.csv", index=False)
    cols = [
        "config_id",
        "delta_j",
        "se_j",
        "delta_loss_pp",
        "worst_ep_dj",
        "p95_dj",
        "cvar95_dj",
        "d_labels",
        "d_switches",
    ]
    # ---- parent late adoption
    late = parent.groupby("stream").late_adoption.mean()
    late_ds = late.idxmax()
    anchors_ok = [
        r.config_id
        for _, r in df[df.anchor & (df.delta_loss_pp <= 0.1) & (df.delta_j < 0)].iterrows()
    ]
    sel, why = shortlist(df.assign(per_dataset=df.per_dataset), anchors_ok, syn, late_ds)
    sl = df.set_index("config_id").loc[sel].reset_index()
    sl["role"] = sl.config_id.map(why)
    sl["config"] = sl.txt
    sl[["config_id", "k", "txt", "delta_j", "se_j", "delta_loss_pp", "cvar95_dj", "role"]].to_csv(
        OUT / "phase3_shortlist.csv", index=False
    )
    # ---- wall
    seen, wall = set(), {"1": 0.0, "2": 0.0, "2A": 0.0, "2G": 0.0}
    for r in rows:
        b = r.get("batch")
        if b and b not in seen and "batch_wall_s" in r:
            seen.add(b)
            wall[str(r["phase"])] += r["batch_wall_s"]
    ph = pd.Series([r.get("phase") for r in rows if r.get("kind") != "control"]).astype(str)
    st = pd.Series([r["status"] for r in rows if r.get("kind") != "control"])
    counts = pd.crosstab(ph, st)
    # ---- write doc
    s = []
    A = s.append
    A("# Paper 1 search60: Phase 1 and Phase 2 screen results\n")
    A(
        "Status: **screening results on a small, development-exposed subset; every number is an optimistic best-of-many. "
        "No originality or validity claim.** Generated by `scripts/paper1_eqsdp/search60/analyze_phase12.py` from "
        "`outputs/paper1_eqsdp/search60/ledger.jsonl`.\n"
    )
    A(
        "## Caveats\n- Screen subset: 12 episodes x 9 datasets x 2 policy seeds (216 jobs per configuration); small, noisy; se values are paired, "
        "dataset-stratified (episodes as units) and not corrected for the thousands of configurations examined.\n"
        "- F59 was trained on even episodes of these datasets; the subset contains even episodes (F59 results are not out-of-sample).\n"
        "- All nine datasets and their odd/even splits are development-exposed.\n"
        "- PaperBanana (preferred for research visuals in AGENTS.md) is not installed; the heatmap PNG is a matplotlib diagnostic only.\n"
        "- J = mean net cost per episode / T x 100 (pp of T); L = prediction loss / T x 100; delta = candidate minus parent `s2armr_H1100`, "
        "equal-weighted over the nine datasets; negative = better. Tails (worst, p95, CVaR95 = mean of worst 5%) are over the 108 paired "
        "episode-level dJ values (seed-averaged).\n"
    )
    A(
        f"## Subset\n`{rp.SUBSET.relative_to(ROOT).as_posix()}` (id `{sub['subset_id']}`): rule `{sub['rule']}`; seeds {sub['policy_seeds']}. "
        "Episodes per dataset are listed in that file (written before any run).\n"
    )
    A(
        "## Commands\n```\nPY=shift-research-starter/.venv/Scripts/python.exe   # OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8\n"
        "$PY scripts/paper1_eqsdp/search60/run_phase12.py subset\n$PY ... run_phase12.py phase1 --workers 16\n"
        "$PY ... run_phase12.py phase2 --workers 16     # 620 manifest + 12 anchors, better Phase-1 setting\n"
        "$PY ... run_phase12.py adjust --workers 16     # one local setting switch each\n"
        "$PY ... run_phase12.py guided --workers 16     # paper1_combo_sampler.py guided -> 240 proposals, run\n"
        "$PY ... run_phase12.py analyze\n```\n"
    )
    A(
        "## Run counts\n"
        + md(counts.reset_index().rename(columns={"row_0": "phase"}), "{:.0f}")
        + "\nPhase labels: 1 singletons (2 settings), 2 manifest/anchor base pass, 2A one-setting adjustment, 2G guided proposals. "
        "K1 manifest rows reuse the Phase-1 better-setting run (not re-run). Wall seconds (sum of batch walls): "
        + json.dumps({k: round(v) for k, v in wall.items()})
        + "\n"
    )
    A(
        "## Controls on the same keys (legacy references)\n"
        + md(
            pd.DataFrame(
                [
                    {
                        "config": r["config_id"],
                        "mean_net_pp": r.get("mean_net_pp"),
                        "delta_j_vs_parent": r.get("delta_j"),
                        "delta_loss_pp": r.get("delta_loss_pp"),
                    }
                    for r in rows
                    if r.get("kind") == "control"
                ]
            ).fillna("")
        )
    )
    A(
        "## Phase 1: all 60 modules (both settings), sorted by better-setting dJ\n"
        f"Inert in both settings (0 changed jobs): {inert if inert else 'none'}. Inert in one setting only: {half_inert if half_inert else 'none'}. "
        "Columns after dJ_s1 describe the better setting.\n"
    )
    A(md(t1.drop(columns=["best_dJ"])))
    for k in range(1, 6):
        d = (best if k == 1 else df[(df.k == k)]).sort_values("delta_j").head(20)
        d = d.assign(config_id=d.config_id + " " + d.txt)
        A(f"## Top 20 at k={k} (base, adjusted and guided pooled; ranked by dJ)\n" + md(d[cols]))
    A("## Anchor combinations\n")
    an = df[df.anchor].sort_values(["combo_id", "delta_j"])
    A(md(an.assign(config_id=an.config_id + " " + an.txt)[cols]))
    unsup = R[
        R.status.isin(
            ["UNSUPPORTED_COMBO", "NOT_IMPLEMENTED", "FAILED", "SKIPPED_NO_SETTING_EFFECT"]
        )
    ]
    A(
        f"## Unsupported / failed / skipped ({len(unsup)})\n"
        + md(unsup[["config_id", "status", "modules_txt"]])
    )
    g = df[df.phase == "2G"].sort_values("delta_j")
    A(
        f"## Guided phase (2G): {len(g)} proposals run\n"
        f"Best 10 by dJ; fraction with dJ<0: {float((g.delta_j < 0).mean()) if len(g) else float('nan'):.3f}; "
        f"median dJ {float(g.delta_j.median()) if len(g) else float('nan'):.3f}. "
        f"For comparison, the base pass (2) median dJ {float(df[df.phase == 2].delta_j.median()):.3f}, fraction<0 {float((df[df.phase == 2].delta_j < 0).mean()):.3f}.\n"
    )
    A(md(g.head(10).assign(config_id=g.head(10).config_id + " " + g.head(10).txt)[cols]))
    A(
        "## Interaction synergy, pairs: syn = dJ(A+B) - dJ(A) - dJ(B) (identical keys; negative = complementary)\n"
        f"{len(syn)} pair results; heatmap `docs/paper1_eqsdp/search60/synergy_heatmap.png`, matrix `synergy_heatmap.csv` (NaN = untested).\n"
    )
    sc = ["pair", "phase", "syn", "se", "delta_j", "dJ_a", "dJ_b"]
    A("### Most negative (complementary)\n" + md(syn.sort_values("syn").head(15)[sc]))
    A(
        "### Most positive (anti-synergy)\n"
        + md(syn.sort_values("syn", ascending=False).head(15)[sc])
    )
    A(
        f"## Phase 3 shortlist ({len(sl)})\nRule: roles first (lowest cost, best error parity, best CVaR95, highest synergy, late-change proxies: "
        f"{late_ds} = dataset with the largest parent mean late adoption, and kc_311), anchors with dJ<0 and dL<=0.1, then lowest dJ with dL<=0.1 pp, "
        "module-set Jaccard <= 0.5 to anything chosen, <=3 per family signature, per-k quotas 4/9/9/8/6 (relaxed if short of 40). "
        "dJ values are screen estimates and selection-biased.\n"
    )
    A(md(sl[["config_id", "k", "txt", "delta_j", "se_j", "delta_loss_pp", "cvar95_dj", "role"]]))
    A("## Module bugs\nSee the final report / ledger `failure` fields; none are fixed here.\n")
    (DOCS / "PHASE12_RESULTS.md").write_text("\n".join(s), encoding="utf-8")
    print("wrote", DOCS / "PHASE12_RESULTS.md", counts.to_dict())


def comp_ids():
    import compositor as comp

    return list(comp.load_modules())


if __name__ == "__main__":
    main()
