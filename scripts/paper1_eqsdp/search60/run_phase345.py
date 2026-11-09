"""Phases 3-5 driver for the Paper 1 60-module search (full-data matched evaluation).

    python run_phase345.py p3run   [--workers 16]   # 40 shortlisted + controls + full-data singletons
    python run_phase345.py p3check                  # parent reproduction vs stage3 (odd) / stage5 (even)
    python run_phase345.py p3analyze                # tables/phase3_*.csv, PHASE3_RESULTS.md
    python run_phase345.py p4select|p4run|p4analyze
    python run_phase345.py p4guided|p4guidedanalyze # optional guided proposals (further development selection)
    python run_phase345.py p5report

Every run uses split=all (every episode of the nine datasets), policy seeds 0-9 and the registered seed
derivation (eval60 / trace_run). Batch directories with a DONE marker are skipped; the ledger is
append-only and every row carries a ``phase`` tag. J = net cost per episode / T * 100 (pp of T).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eval60 as e60
import numpy as np
import pandas as pd
import run_phase12 as r12

ROOT = r12.ROOT
OUT = r12.OUT
RUN = OUT / "full"
LEDGER = r12.LEDGER
DOCS = r12.DOCS
TABLES = DOCS / "tables"
PARENT = r12.PARENT
T = 2000
SEEDS = tuple(range(10))
W1 = "s2wald_l0.98_g0.3_H1100"
W2 = "s2wald_l0.97_g0.2_H1100"
CONTROLS = e60.CONTROLS
BATCH = 20
BOOT = 2000


# ------------------------------------------------------------------ specs
def spec_from_ledger_row(row, name):
    mods = [r12.mod_spec(m["id"], m["setting"]) for m in row["modules"]]
    sp = {"modules": mods, "name": name}
    got = r12.resolved(sp)
    assert [g["params"] for g in got] == [m["params"] for m in row["modules"]], name
    return sp


def screen_rows():
    return {r["config_id"]: r for r in r12.ledger_rows() if r.get("status") == "OK" and "modules" in r
            and str(r.get("phase")) in ("1", "2", "2A", "2G")}  # fmt: skip


def shortlist():
    return pd.read_csv(OUT / "phase3_shortlist.csv")


# ------------------------------------------------------------------ running
def ledger_batches():
    return {r.get("batch") for r in r12.ledger_rows() if r.get("eval") == "full"}


def run_full(tag, specs, phase, meta, workers, controls=False):
    """Full-data run of ``specs`` (+ matched controls); one append-only ledger row per spec."""
    bdir = RUN / tag
    if (bdir / "DONE").exists():
        return False
    t0 = time.perf_counter()
    err = ""
    try:
        e60.run_eval(specs, bdir, split="all", seeds=SEEDS, workers=workers, controls=controls)
    except Exception:  # noqa: BLE001 - recorded in the ledger
        err = traceback.format_exc()[-1500:]
    wall = time.perf_counter() - t0
    rec = bdir / "records.jsonl"
    n = {}
    if rec.exists():
        d = pd.read_json(rec, lines=True, dtype={"config_id": str})
        n = d.groupby("config_id").size().to_dict()
    if tag not in ledger_batches():
        for s in specs:
            row = {"config_id": f"P{phase}F__{s['name']}", "source_config_id": s["name"], "phase": str(phase),
                   "eval": "full", "modules": r12.resolved(s), "parent": s.get("parent", {"kind": "eqsdp"}),
                   "code_sha": r12.sha(), "contract": r12.CONTRACT, "batch": tag, "batch_wall_s": wall,
                   "seeds": list(SEEDS), "episodes": "all", "n_rows": int(n.get(s["name"], 0)),
                   "status": "OK" if n.get(s["name"], 0) > 0 else "FAILED", "failure": err,
                   "records_path": str(rec.relative_to(ROOT)), **meta.get(s["name"], {})}  # fmt: skip
            r12.ledger_append(row)
        if controls:
            for c in CONTROLS:
                r12.ledger_append({"config_id": f"P{phase}F__{c}", "source_config_id": c, "phase": str(phase),
                                   "eval": "full", "kind": "control", "code_sha": r12.sha(), "batch": tag,
                                   "contract": r12.CONTRACT, "n_rows": int(n.get(c, 0)),
                                   "status": "OK" if n.get(c, 0) > 0 else "FAILED",
                                   "records_path": str(rec.relative_to(ROOT))})  # fmt: skip
    (bdir / "DONE").write_text(f"{wall:.1f}s")
    print(
        f"[{time.strftime('%H:%M:%S')}] {tag}: {len(specs)} specs in {wall:.0f}s {('ERR ' + err[-200:]) if err else ''}",
        flush=True,
    )
    return True


def p3_specs():
    sc = screen_rows()
    sl = shortlist()
    specs, meta = [], {}
    names = set()
    for _, r in sl.iterrows():
        specs.append(spec_from_ledger_row(sc[r.config_id], r.config_id))
        meta[r.config_id] = {"role": r.role, "k": int(r.k), "kind": "shortlist"}
        names.add(r.config_id)
    singles = {}
    for sp in specs:
        for m in sp["modules"]:
            singles[(m["id"], m["setting"])] = f"P1_{m['id']}_s{m['setting']}"
    for (mid, st), n in sorted(singles.items()):
        if n in names:
            meta[n]["also_single"] = True
            continue
        specs.append({"modules": [r12.mod_spec(mid, st)], "name": n})
        meta[n] = {"role": "full_singleton", "k": 1, "kind": "singleton"}
    return specs, meta


def p3run(workers):
    RUN.mkdir(parents=True, exist_ok=True)
    specs, meta = p3_specs()
    for i in range(0, len(specs), BATCH):
        run_full(f"p3_{i // BATCH:03d}", specs[i : i + BATCH], 3, meta, workers, controls=(i == 0))


# ------------------------------------------------------------------ loading / pairing
COLS = ["stream", "ep", "seed", "config_id", "net", "loss", "labels", "switches", "late_adoption",
        "false_promotion", "first_deploy", "better"]  # fmt: skip


def load_dir(d):
    x = pd.read_json(Path(d) / "records.jsonl", lines=True, dtype={"config_id": str})
    return x[[c for c in COLS if c in x.columns]]


def load_tags(tags):
    return pd.concat(
        [load_dir(RUN / t) for t in tags if (RUN / t / "DONE").exists()], ignore_index=True
    )


def subset_eps():
    s = r12.subset()
    return {d: set(v["episodes"]) for d, v in s["datasets"].items()}


def pair(cand, ref):
    """Seed-averaged paired deltas per (stream, ep): candidate minus reference."""
    m = cand.merge(ref, on=["stream", "ep", "seed"], suffixes=("", "_r"))
    out = pd.DataFrame({"stream": m.stream, "ep": m.ep, "seed": m.seed})
    out["J"] = m.net / T * 100
    out["Jr"] = m.net_r / T * 100
    out["dJ"] = out.J - out.Jr
    out["dL"] = (m.loss - m.loss_r) / T * 100
    out["dlab"] = m.labels - m.labels_r
    out["dsw"] = m.switches - m.switches_r
    has = "late_adoption_r" in m
    out["dLA"] = (m.late_adoption - m.late_adoption_r) / T * 100 if has else np.nan
    out["dFP"] = (m.false_promotion - m.false_promotion_r) / T * 100 if has else np.nan
    out["lab"] = m.labels
    out["sw"] = m.switches
    g = out.groupby(["stream", "ep"]).mean(numeric_only=True).drop(columns="seed").reset_index()
    sub = subset_eps()
    g["in_sub"] = [e in sub[s] for s, e in zip(g.stream, g.ep)]
    return g


def eqmean(g, col):
    return float(g.groupby("stream")[col].mean().mean())


def boot_ci(g, cols, rng, B=BOOT):
    """Stratified episode bootstrap of equal-dataset means; returns {col: (lo, hi)} and pct CI of dJ/Jr."""
    arrs = {s: x for s, x in g.groupby("stream")}
    reps = {c: np.zeros(B) for c in cols}
    reps["pct"] = np.zeros(B)
    for x in arrs.values():
        n = len(x)
        idx = rng.integers(0, n, size=(B, n))
        for c in cols:
            reps[c] += x[c].to_numpy()[idx].mean(1)
        reps["pct_num"] = reps.get("pct_num", 0) + x["dJ"].to_numpy()[idx].mean(1)
        reps["pct_den"] = reps.get("pct_den", 0) + x["Jr"].to_numpy()[idx].mean(1)
    k = len(arrs)
    out = {c: tuple(np.quantile(reps[c] / k, [0.025, 0.975])) for c in cols}
    out["pct"] = tuple(np.quantile(100 * reps["pct_num"] / reps["pct_den"], [0.025, 0.975]))
    return out


def tails(g):
    x = np.sort(g.dJ.to_numpy())[::-1]
    k = max(1, int(np.ceil(0.05 * len(x))))
    return float(np.quantile(x, 0.95)), float(x[:k].mean()), float(x[0])


def stats(g, rng, ci=True):
    cols = ["dJ", "dL", "dlab", "dsw", "dLA", "dFP"]
    r = {c: eqmean(g, c) for c in cols}
    r["Jr"] = eqmean(g, "Jr")
    r["J"] = eqmean(g, "J")
    r["pct"] = 100 * r["dJ"] / r["Jr"]
    r["labels"] = eqmean(g, "lab")
    r["switches"] = eqmean(g, "sw")
    r["p95"], r["cvar95"], r["worst"] = tails(g)
    r["n_ep"] = len(g)
    if ci:
        c = boot_ci(g, ["dJ", "dL"], rng)
        r["dJ_lo"], r["dJ_hi"] = c["dJ"]
        r["dL_lo"], r["dL_hi"] = c["dL"]
        r["pct_lo"], r["pct_hi"] = c["pct"]
    return r


def per_dataset(g):
    return g.groupby("stream").dJ.mean().to_dict()


# ------------------------------------------------------------------ Phase 3 check + analysis
def p3check():
    """Parent reproduction: full-run s2armr_H1100 vs existing stage3 (odd) / stage5 even records."""
    new = load_tags(["p3_000"])
    new = new[new.config_id == PARENT]
    res = {}
    for nm, p in (("stage3_odd", "outputs/paper1_eqsdp/stage3/run/records.jsonl"),
                  ("stage5_even", "outputs/paper1_eqsdp/stage5/even/A/records.jsonl")):  # fmt: skip
        o = pd.read_json(ROOT / p, lines=True, dtype={"policy": str})
        o = o[o.policy == PARENT].rename(columns={"policy": "config_id"})
        m = o.merge(new, on=["stream", "ep", "seed"], suffixes=("_o", "_n"))
        res[nm] = {"n_old": len(o), "n_matched": len(m),
                   "net_mismatch": int((m.net_o != m.net_n).sum()), "loss_mismatch": int((m.loss_o != m.loss_n).sum()),
                   "labels_mismatch": int((m.labels_o != m.labels_n).sum()),
                   "switches_mismatch": int((m.switches_o != m.switches_n).sum()),
                   "max_abs_net_diff": float((m.net_o - m.net_n).abs().max())}  # fmt: skip
    res["n_new"] = len(new)
    (OUT / "p3_parent_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res))
    return res


def p3_tables(tags=None):
    tags = tags or sorted(p.name for p in RUN.glob("p3_*") if (p / "DONE").exists())
    df = load_tags(tags)
    rng = np.random.default_rng(20261109)
    ref = df[df.config_id == PARENT]
    w1, w2 = df[df.config_id == W1], df[df.config_id == W2]
    sl = shortlist().set_index("config_id")
    rows, pds = [], []
    names = [c for c in df.config_id.unique() if c != PARENT]
    for n in names:
        c = df[df.config_id == n]
        g = pair(c, ref)
        for scope, gg in (("out_of_subset", g[~g.in_sub]), ("all", g)):
            s = stats(gg, rng)
            s.update(config_id=n, scope=scope)
            if scope == "out_of_subset":
                late = gg[gg.stream.isin(["kc_311", "sf_311"])]
                s["late_dJ"] = float(late.groupby("stream").dJ.mean().mean())
            for tag, w in (("w98", w1), ("w97", w2)):
                if n in (W1, W2):
                    continue
                gw = pair(c, w)
                gw = gw if scope == "all" else gw[~gw.in_sub]
                sw = stats(gw, rng)
                s[f"vs_{tag}_dJ"], s[f"vs_{tag}_lo"], s[f"vs_{tag}_hi"] = (
                    sw["dJ"],
                    sw["dJ_lo"],
                    sw["dJ_hi"],
                )
                s[f"vs_{tag}_dL"], s[f"vs_{tag}_pct"] = sw["dL"], sw["pct"]
            rows.append(s)
            for ds, v in per_dataset(gg).items():
                pds.append({"config_id": n, "scope": scope, "dataset": ds, "dJ": v})
    S = pd.DataFrame(rows)
    S["role"] = S.config_id.map(sl.role)
    S["k"] = S.config_id.map(sl.k)
    S["txt"] = S.config_id.map(sl.txt)
    S["screen_dJ"] = S.config_id.map(sl.delta_j)
    TABLES.mkdir(parents=True, exist_ok=True)
    S.to_csv(TABLES / "phase3_summary.csv", index=False)
    pd.DataFrame(pds).to_csv(TABLES / "phase3_per_dataset.csv", index=False)
    return S, pd.DataFrame(pds), df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    if a.cmd == "p3run":
        p3run(a.workers)
    elif a.cmd == "p3check":
        p3check()
    elif a.cmd == "p3analyze":
        import phase3_report

        phase3_report.main()
    else:
        import phase45

        phase45.dispatch(a.cmd, a.workers)


if __name__ == "__main__":
    main()
