"""Stage 4: frozen confirmation on the confirm partition (PROTOCOL section 9, A1.6-A1.8, section 10).

Guarded by freeze.confirm_seeds_allowed(): refuses unless frontier and finalists hashes verify. Runs finalists, the
selector rule, every J-track frontier baseline, per-channel ablations, a contextual-ONS replacement of the stake
channel and the cyclic-shift negative control on N seeds per cell (N from finalists.json). Resumable per
(method, cell) shard. Writes <out>/confirmation.json (schema: scripts/hgxh2c/make_report.py docstring).

  PYTHONPATH=src .venv/Scripts/python.exe scripts/hgxh2c/stage4_confirm.py [--smoke]
"""

import argparse
import importlib.util
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.hgxh2c import freeze, stats
from shiftlab.hgxh2c import grammar as G
from shiftlab.hgxh2c import search as SR
from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.baselines import REGISTRY
from shiftlab.hgxh2c.evaluate import score

ROOT = Path(__file__).resolve().parents[2]
KEEP = [
    "method_id",
    "cell_id",
    "family",
    "seed",
    "tau",
    "alarm_B",
    "alarm_C",
    "alarm_J",
    "n_queries",
    "J_cost",
    "excess_cost_before_alarm",
    "null_B",
    "null_C",
    "loss_before_alarm",
    "cumulative_decision_cost",
    "n_interventions",
    "n_switches",
    "intervention_cost",
    "switching_cost",
    "info_cost",
    "runtime_s",
]
NEG_TRANSFER = ("cost_only", "pred_only", "opposed")
rp = lambda p: Path(p) if Path(p).is_absolute() else ROOT / p
safe = lambda s: re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def load_make_report():
    sp = importlib.util.spec_from_file_location(
        "make_report", ROOT / "scripts/hgxh2c/make_report.py"
    )
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def specs(fin_cands):
    """method id -> kind. Candidates are G.Candidate; ablations drop one slot; ctx = contextual-ONS stakes; nc = shifted source."""
    m = {}
    for c in fin_cands:
        m[c.hash] = ("cand", c)
        for s in range(6):
            if c.slots[s]:
                m[f"{c.hash}|abl:{'_'.join(G.SLOTS[s])}"] = ("cand", c.without(s))
        m[f"{c.hash}|ctx"] = ("ctx", c)
        which = ("B" if any(c.slots[:3]) else "") + ("C" if any(c.slots[3:]) else "")
        m[f"{c.hash}|nc"] = ("nc", c, which)
    return m


def run_chunk(tape, todo, spec):
    """Run all methods in `todo` on one tape; returns {method: df}. Candidate-type methods are batched per (base, comb)."""
    out, S = {}, tape["B"].shape[0]

    def add(mid, res, k, dt):
        df = score(res, tape, REGISTRY[mid][1] if mid in REGISTRY else "J", k, mid)
        df["runtime_s"], df["peak_mem_mb"] = dt / S, 0.0
        out[mid] = df[KEEP]

    cand_ids = [m for m in todo if m in spec and spec[m][0] == "cand"]
    groups = {}
    for m in cand_ids:
        groups.setdefault(spec[m][1].group, []).append(m)
    for ms in groups.values():
        t0 = time.perf_counter()
        # Candidate updates are tensor-only and graph-compatible. Capturing the
        # time loop once avoids thousands of small CUDA launches per cell.
        res = G.compile_batch([spec[m][1] for m in ms], graph=True).run(tape)
        for k, m in enumerate(ms):
            add(m, res, k, (time.perf_counter() - t0) / len(ms))
    for m in todo:
        t0 = time.perf_counter()
        if m in spec and spec[m][0] == "ctx":
            add(
                m,
                G.compile_batch([spec[m][1]], ctx_replace=True, graph=True).run(tape),
                0,
                time.perf_counter() - t0,
            )
        elif m in spec and spec[m][0] == "nc":
            tp = SR.shuffled(tape, spec[m][2], seed=7) if spec[m][2] else tape
            add(m, G.compile_batch([spec[m][1]], graph=True).run(tp), 0, time.perf_counter() - t0)
        elif m not in spec:
            add(m, REGISTRY[m][0]().run(tape), 0, time.perf_counter() - t0)
    return out


_M = {}
BOOT_DEV = "cuda" if torch.cuda.is_available() else "cpu"


def mat(df, col, key):
    """[cells, seeds] matrix of df[col] (NaN padded), cached per (key, col)."""
    if (key, col) not in _M:
        cid, pos = pd.factorize(df.cell_id)[0], df.groupby("cell_id").cumcount().to_numpy()
        X = np.full((cid.max() + 1, pos.max() + 1), np.nan)
        X[cid, pos] = df[col].to_numpy(float)
        _M[(key, col)] = X
    return _M[(key, col)]


def boot(df, a, b, n_boot, seed=0, key="W", dev=None):
    """Paired cluster bootstrap of gain = df[b] - df[a] (positive: a better): cells resampled, then seeds within each drawn
    cell, equal-weight mean over cells, one-sided p for H0: gain <= 0. Vectorised over resamples (one gather per chunk)."""
    dev = dev or BOOT_DEV
    Xa, Xb = mat(df, a, key), mat(df, b, key)
    X = torch.tensor(Xb - Xa, dtype=torch.float64, device=dev)
    ok = ~torch.isnan(X)
    nc = ok.sum(1).clamp(min=1).to(torch.float64)
    X0 = torch.nan_to_num(X)
    C, S = X.shape
    g = torch.Generator(device=dev).manual_seed(seed)
    m = max(1, min(n_boot, int(6e7 // (C * S))))
    out, i = [], 0
    ar = torch.arange(S, device=dev)
    while i < n_boot:
        k = min(m, n_boot - i)
        cells = torch.randint(0, C, (k, C), generator=g, device=dev)
        pos = (
            torch.rand((k, C, S), generator=g, device=dev, dtype=torch.float64)
            * nc[cells][..., None]
        ).long()
        vals = X0[cells[..., None], pos] * (ar[None, None] < nc[cells][..., None])
        out.append((vals.sum(-1) / nc[cells]).mean(1))
        i += k
    out = torch.cat(out).cpu().numpy()
    mean = float((X0.sum(1) / nc).mean())
    lo, hi = np.quantile(out, [0.025, 0.975])
    return {
        "mean": mean,
        "lo": float(lo),
        "hi": float(hi),
        "p": float((1 + (out <= 0).sum()) / (n_boot + 1)),
    }


def far_cp(d, fams):
    r = {}
    for f in fams:
        x = d[d.family == f]
        if len(x):
            k, n = (
                int(((x.alarm_J >= 0) & x.null_B & x.null_C).sum()),
                int((x.null_B & x.null_C).sum()),
            )
            r[f] = {"far": k / max(n, 1), "k": k, "n": n, "cp": list(stats.clopper_pearson(k, n))}
    return r


def analyse(sh, fin, sel, bases, secondary, fcs, fr, a, out):
    mr = load_make_report()
    ids = sorted(p.name for p in sh.iterdir() if p.is_dir() and p.name != "_calib")
    orig = {
        safe(m): m
        for m in list(bases)
        + list(secondary)
        + [f["hash"] + s for f in fin["finalists"] for s in ("", "|ctx", "|nc")]
        + [f"{f['hash']}|abl:{'_'.join(G.SLOTS[s])}" for f in fin["finalists"] for s in range(6)]
    }
    final_ids = {f["hash"] for f in fin["finalists"]}
    ref_id = orig.get(ids[0], ids[0])
    meta_cols = ["family", "tau", "null_B", "null_C"]
    cost_cols = [
        "n_queries",
        "excess_cost_before_alarm",
        "info_cost",
        "intervention_cost",
        "switching_cost",
        "loss_before_alarm",
        "cumulative_decision_cost",
        "runtime_s",
    ]
    # The full KEEP table is several GB at confirmation scale. Read only fields
    # consumed below; retain float64 for paired inference calculations.
    dfs = {}
    for i in ids:
        method = orig.get(i, i)
        cols = ["cell_id", "seed", "J_cost"]
        if method in bases or method in final_ids:
            cols.append("alarm_J")
        if method == ref_id or method in final_ids:
            cols.extend(meta_cols)
        if method in final_ids:
            cols.extend(cost_cols)
        files = sorted((sh / i).glob("*.parquet"))
        d = pd.concat([pd.read_parquet(f, columns=cols) for f in files], ignore_index=True)
        # Store repeated cell IDs as category codes instead of millions of
        # Python string objects in every method table.
        d["cell_id"] = d["cell_id"].astype("category")
        dfs[i] = d
    D = {orig.get(i, i): d.set_index(["cell_id", "seed"]) for i, d in dfs.items()}
    ref = D[ref_id]
    idx = ref.index
    meta = ref[["family", "tau", "null_B", "null_C"]]
    W = pd.DataFrame({m: d.J_cost.reindex(idx) for m, d in D.items()})
    W = W.join(meta[["family"]]).reset_index()
    nb = [b for b in bases if b in D]
    ns = [b for b in secondary if b in D]
    _M.clear()
    best = W[nb].mean().idxmin() if nb else None
    harm = (~(meta.null_B & meta.null_C) & (meta.tau >= 0)).reindex(idx).to_numpy()

    def hit(m):
        al, tau = D[m].alarm_J.reindex(idx), meta.tau
        return ((al >= tau) & (al <= tau + SR.WINDOW) & harm).astype(float).to_numpy()

    res = {}
    fams = sorted(W.family.unique())
    for f in fin["finalists"] + ([{"hash": "selector"}] if "selector" in D else []):
        h = f["hash"]
        if h not in D:
            continue
        v = {"vs_baseline": {b: boot(W, h, b, a.boot, 1) for b in nb}}
        v["iut_pass"] = bool(
            nb and all(r["p"] < 0.05 and r["mean"] > 0 for r in v["vs_baseline"].values())
        )
        v["iut_p"] = max((r["p"] for r in v["vs_baseline"].values()), default=1.0)
        v["comparator_family"] = "primary: anytime-valid frontier members of track J (A5)"
        v["vs_secondary"] = {
            b: boot(W, h, b, a.boot, 6) for b in ns
        }  # versus calibrated non-anytime-valid detectors (CUSUM/PH)
        v["iut_p_secondary"] = max((r["p"] for r in v["vs_secondary"].values()), default=1.0)
        v["iut_pass_secondary"] = bool(
            ns and all(r["p"] < 0.05 and r["mean"] > 0 for r in v["vs_secondary"].values())
        )
        v["secondary_status"] = (
            "won"
            if v["iut_pass_secondary"]
            else ("lost" if any(r["hi"] < 0 for r in v["vs_secondary"].values()) else "tied")
        )
        for lab, suf in (("ablations", None), ("negative_control", "|nc"), ("ctx_replace", "|ctx")):
            if suf:
                v[lab] = boot(W, h, h + suf, a.boot, 2) if h + suf in W else None
            else:
                v[lab] = {
                    s.split("abl:")[1]: boot(W, h, s, a.boot, 3)
                    for s in W.columns
                    if str(s).startswith(h + "|abl:")
                }
        if best:
            _M.pop(("Hd", "f"), None), _M.pop(("Hd", "b"), None)
            Hd = pd.DataFrame(
                {
                    "f": hit(h),
                    "b": hit(best),
                    "cell_id": idx.get_level_values(0),
                    "seed": idx.get_level_values(1),
                }
            )[harm]
            v["power_diff"] = (
                {**boot(Hd, "b", "f", a.boot, 4, key="Hd"), "vs": best} if len(Hd) else None
            )
            gain = boot(W, h, best, a.boot, 5)
            jb = float(W[best].mean())
            v["absolute_gain"] = gain
            v["relative_gain"] = {
                "mean": gain["mean"] / jb,
                "lo": gain["lo"] / jb,
                "hi": gain["hi"] / jb,
                "J_best_baseline": jb,
                "baseline": best,
            }
            tbl = {}
            for fam in fams:
                s = W[W.family == fam]
                tbl[fam] = {
                    "gain_vs_best": float((s[best] - s[h]).mean()),
                    "wins_all": bool(all((s[b] - s[h]).mean() > 0 for b in nb)),
                }
            v["regime_table"] = tbl
            v["regime_wins"] = {k: r["wins_all"] for k, r in tbl.items()}
            v["negative_transfer_regimes"] = [
                k for k in fams if k in NEG_TRANSFER and not tbl[k]["wins_all"]
            ]
        d = D[h].reset_index()
        harmw = ~(d.null_B & d.null_C) & (d.tau >= 0)
        v["secondary_unadjusted"] = {
            "far": far_cp(d, list(TP.NULL_FAMILIES)),
            "labels": float(d.n_queries.mean()),
            "delay": float(
                np.where(
                    harmw, np.where(d.alarm_J >= d.tau, d.alarm_J - d.tau, 2000 - d.tau), np.nan
                )[harmw].mean()
            )
            if harmw.any()
            else None,
            "cost_components": {
                c: float(d[c].mean())
                for c in (
                    "excess_cost_before_alarm",
                    "info_cost",
                    "intervention_cost",
                    "switching_cost",
                    "loss_before_alarm",
                    "cumulative_decision_cost",
                    "J_cost",
                )
            },
            "runtime_s": float(d.runtime_s.mean()),
        }
        res[h] = v
    hs = stats.holm({h: v["iut_p"] for h, v in res.items() if h != "selector"})
    hs2 = stats.holm({h: v["iut_p_secondary"] for h, v in res.items() if h != "selector"})
    for h, v in res.items():
        v["holm_p"] = hs.get(h, v["iut_p"])
        v["holm_p_secondary"] = hs2.get(h, v["iut_p_secondary"])
        v["outcome"] = mr.decide(v)
        v["p_note"] = (
            "vs_baseline.p one-sided cluster bootstrap; holm_p = Holm over finalists of max_b p (intersection-union)"
        )
    suite = (
        SR.equivalence_suite(fcs, fr, a.device, n=8, T=min(500, int(fin["plan"]["T12"])))
        if fcs
        else {}
    )  # E1-E10 on audit seeds
    for h, v in res.items():
        if h in suite:
            sz = {
                f: v["secondary_unadjusted"]["far"].get(f)
                for f in ("null_stationary", "null_boundary")
            }
            valid = next(c.comb for c in fcs if c.hash == h) in ("bonf", "mix", "linear")
            suite[h]["E11"] = {
                "res": sz,
                "pass_": bool(valid and all(x is None or x["cp"][1] <= 0.05 for x in sz.values())),
                "criterion": "Clopper-Pearson upper bound <= 0.05 in guaranteed nulls; null_ar is stress only",
            }
            v["equivalence"] = suite[h]
    conf = {
        "finalists": {h: v for h, v in res.items() if h != "selector"},
        "selector": res.get("selector"),
        "baselines": nb,
        "secondary_baselines": ns,
        "best_baseline": best,
        "config": {
            "N_alt": fin["N_per_cell_alt"],
            "N_null": fin["N_per_cell_null"],
            "boot": a.boot,
            "smoke": a.smoke,
            "partition": "confirm",
            "frozen": {k: v["sha256"] for k, v in freeze.read_freeze(a.ffile).items()},
        },
        "outcome_if_empty": None
        if res
        else "nothing survives: negative result; keep the failure atlas and stop the mechanism",
    }
    (out / "confirmation.json").write_text(
        json.dumps(conf, indent=1, default=lambda o: None if o is None else float(o))
    )
    return conf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--stage3", default="outputs/hgxh2c/stage3")
    ap.add_argument("--out", default="outputs/hgxh2c/stage4")
    ap.add_argument("--freeze-file", default=None)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--n", type=int, default=0, help="override N per cell (smoke / debugging only)")
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--max-seeds", type=int, default=4096, help="seeds per tape chunk")
    a = ap.parse_args()
    a.ffile = (
        Path(a.freeze_file)
        if a.freeze_file
        else (ROOT / a.out / "FREEZE.json" if a.smoke else freeze.FREEZE)
    )
    freeze.confirm_seeds_allowed(
        a.ffile
    )  # raises unless frontier and finalists are frozen and verified
    d = freeze.require_frozen(["frontier", "finalists", "selector"], a.ffile)
    out = ROOT / a.out
    sh = out / "shards"
    sh.mkdir(parents=True, exist_ok=True)
    fin = json.loads(rp(d["finalists"]["path"]).read_text())
    sel = json.loads(rp(d["selector"]["path"]).read_text())
    fr = SR.Frontier(rp(d["frontier"]["path"]))
    fcs = [G.Candidate.from_dict(f["cand"]) for f in fin["finalists"]]
    spec = specs(fcs)
    bases, secondary = (
        list(fr.union),
        list(fr.secondary),
    )  # A5: primary (anytime-valid) / secondary (CUSUM, PH)
    methods = bases + secondary + list(spec)
    T = 2000
    if a.smoke:
        T = int(fin["plan"]["T12"])
        cells = [
            TP.ScenarioCell(c.family, c.magnitude, c.delay, c.label_regime, c.proxy, T)
            for c in json_cells(fin)
        ]
    else:
        cells = TP.dev_grid(T)
    nn = lambda c: (
        a.n or (fin["N_per_cell_null"] if c.family in TP.NULL_FAMILIES else fin["N_per_cell_alt"])
    )
    print(
        f"{len(cells)} cells, {len(methods)} methods, N alt/null {fin['N_per_cell_alt']}/{fin['N_per_cell_null']}, device {a.device}",
        flush=True,
    )
    i = 0
    while i < len(cells):
        j, tot = i, 0
        while j < len(cells) and (tot + nn(cells[j]) <= a.max_seeds or j == i):
            tot += nn(cells[j])
            j += 1
        chunk = cells[i:j]
        i = j
        todo = [
            m
            for m in methods
            if not all((sh / safe(m) / (safe(c.cell_id) + ".parquet")).exists() for c in chunk)
        ]
        calib_f = sh / "_calib" / (safe(chunk[0].cell_id) + ".parquet")
        if not todo and calib_f.exists():
            continue
        t0 = time.perf_counter()
        tape = TP.cat_tapes([TP.generate(c, "confirm", nn(c), a.device) for c in chunk])
        res = run_chunk(tape, todo, spec)
        for m, df in res.items():
            (sh / safe(m)).mkdir(exist_ok=True)
            for c in chunk:
                f = sh / safe(m) / (safe(c.cell_id) + ".parquet")
                tmp = f.with_suffix(".tmp")
                df[df.cell_id == c.cell_id].to_parquet(tmp, index=False)
                tmp.replace(f)
        if not calib_f.exists():
            cal = SR.calib_score(tape)
            (sh / "_calib").mkdir(exist_ok=True)
            pd.DataFrame(
                {
                    "cell_id": [c.cell_id for c in chunk for _ in range(nn(c))],
                    "seed": tape["seeds"].cpu().numpy(),
                    "cal": cal,
                }
            ).to_parquet(calib_f, index=False)
        print(
            f"cells {i}/{len(cells)} ({len(todo)} methods) {time.perf_counter() - t0:.1f}s",
            flush=True,
        )
        del tape
    if (
        sel["finalists"] and fcs
    ):  # selector rule: per-stream choice from design-time observables only
        cal = pd.concat([pd.read_parquet(f) for f in sorted((sh / "_calib").glob("*.parquet"))])
        parts = []
        cmap = {c.cell_id: c for c in cells}
        for cid, g in cal.groupby("cell_id"):
            c = cmap[cid]
            pick = np.array([SR.select_index(sel, c.delay, c.label_regime, x) for x in g.cal])
            rows = [
                pd.read_parquet(sh / safe(f["hash"]) / (safe(cid) + ".parquet"))
                .set_index("seed")
                .loc[g.seed.to_numpy()]
                for f in fin["finalists"]
            ]
            sub = pd.concat([rows[k].iloc[[i]] for i, k in enumerate(pick)])
            parts.append(sub.reset_index().assign(method_id="selector"))
        (sh / "selector").mkdir(exist_ok=True)
        for p in parts:
            p[KEEP].to_parquet(
                sh / "selector" / (safe(p.cell_id.iloc[0]) + ".parquet"), index=False
            )
    analyse(sh, fin, sel, bases, secondary, fcs, fr, a, out)
    print("wrote", out / "confirmation.json")


def json_cells(fin):
    """Smoke only: the confirm cells follow the smoke dev cells stage 3 used."""
    import importlib.util as u

    sp = u.spec_from_file_location("stage3_search", ROOT / "scripts/hgxh2c/stage3_search.py")
    m = u.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m.smoke_dev_cells(int(fin["plan"]["T12"]))


if __name__ == "__main__":
    main()
