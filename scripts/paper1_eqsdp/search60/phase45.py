"""Phase 4 (interactions / attribution / matched controls / Wald transfer / guided) for search60.

Dispatched from run_phase345.py: p4select, p4specs, p4run, p4cal, p4analyze, p4guided, p4gsub, p4gfull.
All runs are full data (split=all, seeds 0-9). Selection of the top 8 uses Phase 3 out-of-subset dJ.
"""

from __future__ import annotations

import itertools
import json
import multiprocessing as mp
import sys
import time

import numpy as np
import pandas as pd
import run_phase345 as p

r12 = p.r12
SC = "out_of_subset"
CUT_GRID = [None, 500, 700, 900, 1300, 1500, 1750]
CAL_M = (10, 15, 20, 25, 30, 40, 50, 60, 80, 100)
WALD_PARENT = {"kind": "wald", "lam": 0.98, "gamma": 0.3, "cutoff": 1100}


def key_of(mods):
    return tuple(sorted((m["id"], int(m["setting"])) for m in mods))


def sname(key):
    return "P4_" + "_".join(f"{i}s{s}" for i, s in key)


def sp_of(key, name, parent=None):
    s = {"modules": [r12.mod_spec(i, st) for i, st in key], "name": name}
    if parent:
        s["parent"] = parent
    return s


def top8():
    f = p.OUT / "p4_top8.json"
    if f.exists():
        return json.loads(f.read_text())
    S = pd.read_csv(p.TABLES / "phase3_summary.csv")
    S = S[(S.scope == SC) & (S.kind_sl == "shortlist") & (S.dL <= 0.1)].sort_values("dJ").head(8)
    sc = p.screen_rows()
    out = [{"config_id": r.config_id, "key": key_of(sc[r.config_id]["modules"]),
            "dJ": r.dJ, "dL": r.dL} for _, r in S.iterrows()]  # fmt: skip
    f.write_text(json.dumps(out, indent=1))
    return out


def existing_names():
    """key -> name for configs already run on full data in Phase 3."""
    sc = p.screen_rows()
    sl = set(p.shortlist().config_id)
    names = {}
    for n in sl:
        names[key_of(sc[n]["modules"])] = n
    for n, r in sc.items():
        if str(r.get("phase")) == "1" and len(r["modules"]) == 1:
            k = key_of(r["modules"])
            if p.RUN.exists() and k not in names:
                names.setdefault(k, n)
    return names


def p4_specs():
    ex = existing_names()
    specs, meta = {}, {}
    for t in top8():
        key = tuple(map(tuple, t["key"]))
        k = len(key)
        subs = set()
        for size in {2, 3, k - 1}:
            if 1 < size < k:
                subs.update(itertools.combinations(key, size))
        for sub in sorted(subs):
            if sub in ex:
                continue
            n = sname(sub)
            specs[n] = sp_of(sub, n)
            meta[n] = {"kind": "subset", "k": len(sub)}
        n = f"P4W__{t['config_id']}"  # Wald-transfer variant of the full config
        specs[n] = sp_of(key, n, WALD_PARENT)
        meta[n] = {"kind": "wald_transfer", "k": k, "source": t["config_id"]}
    for h in CUT_GRID:
        n = f"P4_ctlcut_H{h if h is not None else 'none'}"
        specs[n] = {"modules": [], "name": n, "parent": {"kind": "eqsdp", "cutoff": h}}
        meta[n] = {"kind": "cutoff_control", "cutoff": h}
    return list(specs.values()), meta


def p4run(workers):
    p.RUN.mkdir(parents=True, exist_ok=True)
    specs, meta = p4_specs()
    for i in range(0, len(specs), p.BATCH):
        p.run_full(f"p4_{i // p.BATCH:03d}", specs[i : i + p.BATCH], 4, meta, workers)


def _cal_job(args):
    import stage5_eval as e5

    return e5.job5(args)


def p4cal(workers):
    """Uniform-calendar controls on the odd parity (the even parity exists in stage5/even/B)."""
    sys.path.insert(0, str(p.HERE.parent))
    import stage5_eval as e5

    out = p.RUN / "p4_cal_odd"
    if (out / "DONE").exists():
        return
    specs = {}
    for m in CAL_M:
        for c in (1100, None):
            specs[f"s5cal_m{m}_c{'none' if c is None else c}"] = {
                "kind": "cal",
                "m": m,
                "cutoff": c,
            }
    t0 = time.perf_counter()
    e5.run_specs([], specs, "odd", out, workers=workers)
    (out / "DONE").write_text(f"{time.perf_counter() - t0:.0f}s")
    r12.ledger_append({"config_id": "P4F__calendar_controls_odd", "phase": "4", "eval": "full", "batch": "p4_cal_odd",
                       "kind": "calendar_controls", "specs": specs, "code_sha": r12.sha(), "status": "OK",
                       "records_path": str((out / "records.jsonl").relative_to(p.ROOT)), "contract": r12.CONTRACT})  # fmt: skip


def load_cal():
    ev = p.pd.read_json(
        p.ROOT / "outputs/paper1_eqsdp/stage5/even/B/records.jsonl",
        lines=True,
        dtype={"policy": str},
    )
    od = p.pd.read_json(p.RUN / "p4_cal_odd/records.jsonl", lines=True, dtype={"policy": str})
    d = pd.concat([ev, od])
    d = d[d.policy.str.startswith("s5cal_")].rename(columns={"policy": "config_id"})
    return d[[c for c in p.COLS if c in d.columns]]


# ------------------------------------------------------------------ analysis
def gdict(df, ref, names):
    return {n: p.pair(df[df.config_id == n], ref) for n in names if (df.config_id == n).any()}


def sel(g, scope):
    return g if scope == "all" else g[~g.in_sub]


def syn_frame(gab, ga, gb):
    m = gab.merge(ga[["stream", "ep", "dJ"]], on=["stream", "ep"], suffixes=("", "_a"))
    m = m.merge(gb[["stream", "ep", "dJ"]].rename(columns={"dJ": "dJ_b"}), on=["stream", "ep"])
    m["dJ"] = m.dJ - m.dJ_a - m.dJ_b
    return m


def analyze():
    rng = np.random.default_rng(20261110)
    tags = sorted(
        q.name for q in p.RUN.glob("p[34]_*") if (q / "DONE").exists() and q.name[3:].isdigit()
    )
    df = p.load_tags(tags)
    ref = df[df.config_id == p.PARENT]
    p.screen_rows()
    t8 = top8()
    ex = existing_names()
    p.shortlist().set_index("config_id")
    needed = set(df.config_id)
    G = gdict(df, ref, [n for n in needed if n != p.PARENT])
    w1 = df[df.config_id == p.W1]
    abl, syn, tr_rows, mc, _sp_rows = [], [], [], [], []
    cal = load_cal() if (p.RUN / "p4_cal_odd/DONE").exists() else None
    for t in t8:
        cid = t["config_id"]
        key = tuple(map(tuple, t["key"]))
        k = len(key)
        full = G[cid]
        row0 = {"config_id": cid, "k": k}
        for scope in (SC, "all"):
            s = p.stats(sel(full, scope), rng)
            abl.append({**row0, "scope": scope, "variant": "FULL", "removed": "", "dJ": s["dJ"], "lo": s["dJ_lo"], "hi": s["dJ_hi"],
                        "dL": s["dL"], "labels": s["labels"], "contrib_dJ": 0.0})  # fmt: skip
            subs = []
            for size in sorted({1, 2, 3, k - 1}):
                if 1 <= size < k:
                    subs += [(c, size) for c in itertools.combinations(key, size)]
            for sub, size in subs:
                n = ex.get(sub) or sname(sub)
                if n not in G:
                    continue
                g = sel(G[n], scope)
                s2 = p.stats(g, rng)
                rem = [f"{i}s{st}" for i, st in key if (i, st) not in sub]
                typ = "removal" if size == k - 1 else f"sub{size}"
                gg = sel(full, scope).merge(
                    g[["stream", "ep", "dJ"]], on=["stream", "ep"], suffixes=("", "_v")
                )
                gg["dJ"] = gg.dJ_v - gg.dJ  # variant minus full: positive = module(s) help
                c = p.boot_ci(gg, ["dJ"], rng)
                abl.append({**row0, "scope": scope, "variant": typ, "removed": "+".join(rem) if typ == "removal" else "",
                            "modules": "+".join(f"{i}s{st}" for i, st in sub), "dJ": s2["dJ"], "lo": s2["dJ_lo"], "hi": s2["dJ_hi"],
                            "dL": s2["dL"], "labels": s2["labels"], "contrib_dJ": p.eqmean(gg, "dJ"), "contrib_lo": c["dJ"][0], "contrib_hi": c["dJ"][1]})  # fmt: skip
            # pair synergy
            for a, b in itertools.combinations(key, 2):
                nab = ex.get(tuple(sorted((a, b)))) or sname(tuple(sorted((a, b))))
                na, nb = ex.get((a,)), ex.get((b,))
                if nab not in G or na not in G or nb not in G:
                    continue
                f = syn_frame(sel(G[nab], scope), sel(G[na], scope), sel(G[nb], scope))
                c = p.boot_ci(f, ["dJ"], rng)
                syn.append({"config_id": cid, "scope": scope, "A": f"{a[0]}s{a[1]}", "B": f"{b[0]}s{b[1]}", "dJ_AB": p.eqmean(sel(G[nab], scope), "dJ"),
                            "dJ_A": p.eqmean(sel(G[na], scope), "dJ"), "dJ_B": p.eqmean(sel(G[nb], scope), "dJ"), "synergy": p.eqmean(f, "dJ"), "lo": c["dJ"][0], "hi": c["dJ"][1]})  # fmt: skip
        # Wald transfer
        nw = f"P4W__{cid}"
        if nw in set(df.config_id):
            cw = df[df.config_id == nw]
            for scope in (SC, "all"):
                gw_vs_wc = sel(p.pair(cw, w1), scope)  # Wald+addon vs Wald+cutoff
                g_eq_vs_w = sel(
                    p.pair(df[df.config_id == cid], cw), scope
                )  # EQSDp+addon vs Wald+addon
                g_eq_vs_wc = sel(p.pair(df[df.config_id == cid], w1), scope)
                g_wc_vs_par = sel(p.pair(w1, ref), scope)
                for lab, g in (("Wald+addon minus Wald+cutoff", gw_vs_wc), ("EQSDp+addon minus Wald+addon", g_eq_vs_w),
                               ("EQSDp+addon minus Wald+cutoff", g_eq_vs_wc), ("Wald+cutoff minus EQSDp parent", g_wc_vs_par)):  # fmt: skip
                    s = p.stats(g, rng)
                    tr_rows.append({"config_id": cid, "scope": scope, "contrast": lab, "dJ": s["dJ"], "lo": s["dJ_lo"], "hi": s["dJ_hi"],
                                    "pct": s["pct"], "dL": s["dL"], "dlab": s["dlab"], "dsw": s["dsw"]})  # fmt: skip
        else:
            tr_rows.append({"config_id": cid, "scope": "-", "contrast": "NO_WALD_VARIANT_RECORDS"})
        # matched controls (nearest label count among cutoff controls and uniform calendars)
        lab = p.eqmean(full, "lab")
        pools = {}
        for n in [x for x in needed if x.startswith("P4_ctlcut_")]:
            pools[n] = ("cutoff", df[df.config_id == n])
        if cal is not None:
            for n in cal.config_id.unique():
                pools[n] = ("calendar", cal[cal.config_id == n])
        cand = []
        for n, (kind, d) in pools.items():
            gg = p.pair(d, ref)
            cand.append((abs(p.eqmean(gg, "lab") - lab), kind, n, gg))
        for kind in ("cutoff", "calendar"):
            c_ = sorted([x for x in cand if x[1] == kind], key=lambda x: x[0])[:1]
            for dist, kd, n, gc in c_:
                for scope in (SC, "all"):
                    m = sel(full, scope).merge(
                        sel(gc, scope)[["stream", "ep", "dJ", "dL", "lab"]],
                        on=["stream", "ep"],
                        suffixes=("", "_c"),
                    )
                    m["dJ"] = m.dJ - m.dJ_c
                    m["dL"] = m.dL - m.dL_c
                    ci = p.boot_ci(m, ["dJ", "dL"], rng)
                    mc.append({"config_id": cid, "scope": scope, "control_kind": kd, "control": n, "label_gap": dist,
                               "config_labels": lab, "control_labels": p.eqmean(sel(gc, scope), "lab"),
                               "control_dJ_vs_parent": p.eqmean(sel(gc, scope), "dJ"), "config_dJ_vs_parent": p.eqmean(sel(full, scope), "dJ"),
                               "config_minus_control_dJ": p.eqmean(m, "dJ"), "lo": ci["dJ"][0], "hi": ci["dJ"][1],
                               "config_minus_control_dL": p.eqmean(m, "dL")})  # fmt: skip
    T = p.TABLES
    T.mkdir(exist_ok=True, parents=True)
    pd.DataFrame(abl).to_csv(T / "phase4_ablation.csv", index=False)
    pd.DataFrame(syn).to_csv(T / "phase4_synergy_pairs.csv", index=False)
    pd.DataFrame(tr_rows).to_csv(T / "phase4_wald_transfer.csv", index=False)
    pd.DataFrame(mc).to_csv(T / "phase4_matched_controls.csv", index=False)
    heat()
    print("p4 analysis written", len(abl), len(syn), len(tr_rows), len(mc))


def heat():
    s = pd.read_csv(p.TABLES / "phase4_synergy_pairs.csv")
    s = s[s.scope == SC]
    if s.empty:
        return
    mods = sorted(set(s.A) | set(s.B))
    M = pd.DataFrame(np.nan, index=mods, columns=mods)
    for (a, b), g in s.groupby(["A", "B"]):
        M.loc[a, b] = M.loc[b, a] = g.synergy.mean()
    M.to_csv(p.TABLES / "phase4_synergy_heatmap.csv")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(max(5, 0.5 * len(mods) + 2), max(4, 0.5 * len(mods) + 1.5)))
    v = np.nanmax(np.abs(M.to_numpy())) or 1
    im = ax.imshow(M.to_numpy(), cmap="RdBu", vmin=-v, vmax=v)
    ax.set_xticks(range(len(mods)), mods, rotation=90, fontsize=7)
    ax.set_yticks(range(len(mods)), mods, fontsize=7)
    fig.colorbar(im, label="synergy dJ(AB)-dJ(A)-dJ(B) (pp of T); negative = complementary")
    ax.set_title("Full-data pair synergy, out-of-subset (diagnostic; not PaperBanana)", fontsize=8)
    fig.tight_layout()
    fig.savefig(p.DOCS / "phase4_synergy_heatmap.png", dpi=130)


def dispatch(cmd, workers):
    if cmd == "p4select":
        print(json.dumps(top8())[:600])
    elif cmd == "p4specs":
        s, _m = p4_specs()
        print(len(s), "specs")
    elif cmd == "p4run":
        p4run(workers)
    elif cmd == "p4cal":
        p4cal(workers)
    elif cmd == "p4analyze":
        analyze()
    elif cmd == "p5report":
        import phase5_report

        phase5_report.main()
    else:
        import phase45g

        phase45g.dispatch(cmd, workers)


_ = (mp,)
