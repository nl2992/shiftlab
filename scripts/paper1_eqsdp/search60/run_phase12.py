"""Phase 1 (singletons) and Phase 2 (combinations) screen driver for the Paper 1 60-module search.

    python run_phase12.py subset                 # write docs/.../SCREEN_SUBSET.json (before any run)
    python run_phase12.py phase1|phase2|adjust|guided [--workers 16]
    python run_phase12.py analyze                # CSVs, synergy heatmap, PHASE12 tables (no simulation)

Resumable: a batch directory with a DONE marker is skipped; the ledger is append-only.
J is reported as net cost per episode / T * 100 (percentage points of T); L is prediction loss / T * 100.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compositor as comp
import eval60 as e60
import numpy as np
import pandas as pd
import trace_run as tr

ROOT = HERE.parents[2]
OUT = ROOT / "outputs/paper1_eqsdp/search60"
RUN = OUT / "phase12"
LEDGER = OUT / "ledger.jsonl"
DOCS = ROOT / "docs/paper1_eqsdp/search60"
SUBSET = DOCS / "SCREEN_SUBSET.json"
PARENT = "s2armr_H1100"
T = 2000
CONTRACT = "paper1_search60_contract_v1: T=2000,B=200,c_q=0.05,c_s=5,registered delays,sota_nine seed derivation"
BATCH = 24
ANCHORS = [
    ["A01", "B13"], ["A06", "B20"], ["A04", "B16", "F53"], ["A09", "B11", "C23"],
    ["B14", "D32", "D33"], ["A09", "C21", "E45"], ["A07", "B16", "F54"], ["A01", "D33", "E49"],
    ["A04", "B13", "D37", "E45"], ["A06", "B20", "C28", "E45", "F55"],
    ["A09", "B14", "C26", "D32", "E42"], ["B13", "C21", "D37", "E41", "F53"],
]  # fmt: skip


def cid_of(mods):
    c = sorted(mods)
    return f"K{len(c)}__" + "_".join(c)


# ---------------------------------------------------------------- subset
def make_subset():
    out = {}
    for ds, (p, _, _) in tr.sealed_paths().items():
        n = int(np.load(p)["l0"].shape[0])
        key = lambda e, ds=ds: hashlib.sha256(f"{ds}:{e}:search60".encode()).hexdigest()
        out[ds] = {"n_episodes": n, "episodes": sorted(sorted(range(n), key=key)[:12])}
    body = {"rule": "sort episode indices by sha256(f'{dataset}:{ep}:search60'), take first 12",
            "policy_seeds": [0, 1], "datasets": out}  # fmt: skip
    body["subset_id"] = (
        "S60-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:10]
    )
    SUBSET.write_text(json.dumps(body, indent=1))
    return body


def subset():
    return json.loads(SUBSET.read_text())


# ---------------------------------------------------------------- ledger / summaries
def sha():
    return e60.code_sha()


def ledger_append(row):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def ledger_rows():
    if not LEDGER.exists():
        return []
    return [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines() if x]


def paired(df, parent):
    """Per (stream, ep) seed-averaged candidate-minus-parent deltas, plus changed-job count."""
    m = df.merge(parent, on=["stream", "ep", "seed"], suffixes=("", "_p"))
    changed = ((m.net != m.net_p) | (m.loss != m.loss_p) | (m.labels != m.labels_p)
               | (m.switches != m.switches_p)).sum()  # fmt: skip
    m["dJ"] = (m.net - m.net_p) / T * 100
    m["dL"] = (m.loss - m.loss_p) / T * 100
    m["dlab"] = m.labels - m.labels_p
    m["dsw"] = m.switches - m.switches_p
    g = m.groupby(["stream", "ep"])[["dJ", "dL", "dlab", "dsw"]].mean()
    return g, int(changed), len(m), m


def eq_mean_se(g, col):
    per = g[col].groupby(level=0)
    mu = per.mean()
    var = per.var(ddof=1) / per.count()
    return float(mu.mean()), float(np.sqrt(var.sum()) / len(mu)), mu


def summarize(df, parent):
    g, changed, n, m = paired(df, parent)
    dj, se, mu = eq_mean_se(g, "dJ")
    dl, sel, _ = eq_mean_se(g, "dL")
    x = np.sort(g.dJ.values)[::-1]
    k = max(1, math.ceil(0.05 * len(x)))
    secs_c, secs_p = float(m.secs.sum()), float(m.secs_p.sum())
    return {
        "delta_j": dj, "se_j": se, "delta_loss_pp": dl, "se_loss": sel,
        "d_labels": float(g.groupby(level=0).dlab.mean().mean()),
        "d_switches": float(g.groupby(level=0).dsw.mean().mean()),
        "worst_ep_dj": float(x[0]), "p95_dj": float(np.quantile(x, 0.95)),
        "cvar95_dj": float(x[:k].mean()), "n_changed_jobs": changed, "n_jobs": n,
        "inert": changed == 0, "runtime_ratio": secs_c / secs_p if secs_p else float("nan"),
        "per_dataset_dj": {k_: float(v) for k_, v in mu.items()},
        "per_dataset_late_adopt_d": {k_: float(v) for k_, v in
                                     (m.assign(la=m.late_adoption - m.late_adoption_p)
                                      .groupby("stream").la.mean()).items()},
        "mean_labels": float(df.groupby("stream").labels.mean().mean()),
        "mean_switches": float(df.groupby("stream").switches.mean().mean()),
    }  # fmt: skip


def load_records(path):
    return pd.read_json(path, lines=True)


def parent_df():
    return load_records(RUN / "p1_000" / "records.jsonl").query("config_id == @PARENT")


# ---------------------------------------------------------------- running
def mod_spec(mid, setting):
    return {"id": mid, "setting": int(setting)}


def resolved(spec):
    reg = comp.load_modules()
    out = []
    for m in spec["modules"]:
        p = (
            {
                **reg[m["id"]].DEFAULTS,
                **reg[m["id"]].SETTINGS[int(m["setting"])],
                **m.get("params", {}),
            }
            if m.get("setting") is not None
            else {**reg[m["id"]].DEFAULTS, **m.get("params", {})}
        )
        out.append({"id": m["id"], "setting": m.get("setting"), "params": p})
    return out


def run_batch(tag, specs, meta, workers, controls=False):
    """specs: list of spec dicts with unique ``name``. meta[name] = dict of extra ledger fields."""
    bdir = RUN / tag
    if (bdir / "DONE").exists():
        return False
    sub = subset()
    eps = {d: v["episodes"] for d, v in sub["datasets"].items()}
    t0 = time.perf_counter()
    try:
        e60.run_eval(specs, bdir, episodes=eps, seeds=tuple(sub["policy_seeds"]), workers=workers,
                     controls=controls)  # fmt: skip
        err = {}
    except Exception:  # noqa: BLE001 - isolate failing configs, logged to ledger
        err = {"batch_traceback": traceback.format_exc()[-1500:]}
        for s in specs:
            try:
                e60.run_eval([s], bdir / f"single_{s['name']}", episodes=eps,
                             seeds=tuple(sub["policy_seeds"]), workers=workers)  # fmt: skip
            except Exception:  # noqa: BLE001 - isolate failing configs, logged to ledger
                err[s["name"]] = traceback.format_exc()[-1500:]
    wall = time.perf_counter() - t0
    recs = []
    if (bdir / "records.jsonl").exists():
        recs.append((bdir / "records.jsonl", load_records(bdir / "records.jsonl")))
    for d in bdir.glob("single_*"):
        if (d / "records.jsonl").exists():
            recs.append((d / "records.jsonl", load_records(d / "records.jsonl")))
    par = parent_df() if tag != "p1_000" else None
    allr = pd.concat([r for _, r in recs]) if recs else pd.DataFrame(columns=["config_id"])
    if par is None:
        par = allr.query("config_id == @PARENT")
    for s in specs:
        name = s["name"]
        row = {"config_id": name, "modules": resolved(s), "code_sha": sha(), "subset_id": sub["subset_id"],
               "seeds": sub["policy_seeds"], "contract": CONTRACT, "batch": tag, "batch_wall_s": wall,
               **meta.get(name, {})}  # fmt: skip
        d = allr[allr.config_id == name]
        if len(d) == 0:
            row.update(
                status="FAILED", failure=err.get(name, err.get("batch_traceback", "no records"))
            )
        else:
            src = next(p for p, r in recs if (r.config_id == name).any())
            row.update(status="OK", records_path=str(src.relative_to(ROOT)), **summarize(d, par))
            if d.net.isna().any():
                row.update(status="FAILED", failure="NaN net")
        ledger_append(row)
    if tag == "p1_000":  # parent + legacy-control reference rows
        for c in e60.CONTROLS:
            d = allr[allr.config_id == c]
            ledger_append({"config_id": c, "kind": "control", "status": "OK", "code_sha": sha(),
                           "subset_id": sub["subset_id"], "contract": CONTRACT, "batch": tag,
                           "records_path": str((bdir / "records.jsonl").relative_to(ROOT)),
                           **(summarize(d, par) if c != PARENT else
                              {"mean_labels": float(d.groupby("stream").labels.mean().mean()),
                               "mean_switches": float(d.groupby("stream").switches.mean().mean()),
                               "mean_net_pp": float(d.groupby("stream").net.mean().mean() / T * 100),
                               "mean_loss_pp": float(d.groupby("stream").loss.mean().mean() / T * 100)})})  # fmt: skip
    (bdir / "DONE").write_text(f"{wall:.1f}s")
    print(
        f"[{time.strftime('%H:%M:%S')}] {tag} done {len(specs)} configs in {wall:.0f}s", flush=True
    )
    return True


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def ledger_ok():
    return {r["config_id"]: r for r in ledger_rows() if r.get("status") == "OK" and "modules" in r}


# ---------------------------------------------------------------- phases
def phase1(workers):
    reg = comp.load_modules()
    ids = sorted(reg)
    assert len(ids) == 60
    specs, meta = [], {}
    for m in ids:
        for s in (0, 1):
            n = f"P1_{m}_s{s}"
            specs.append({"modules": [mod_spec(m, s)], "name": n})
            meta[n] = {"phase": 1, "module": m, "setting": s}
    run_batch("p1_000", specs[:BATCH], meta, workers, controls=True)
    for i, ch in enumerate(chunks(specs[BATCH:], BATCH), 1):
        run_batch(f"p1_{i:03d}", ch, meta, workers)


def phase1_table():
    L = ledger_ok()
    rows = []
    for m in sorted(comp.load_modules()):
        for s in (0, 1):
            r = L.get(f"P1_{m}_s{s}")
            if r:
                rows.append(
                    {"module": m, "setting": s, "delta_j": r["delta_j"], "inert": r["inert"]}
                )
    return pd.DataFrame(rows)


def best_settings():
    t = phase1_table()
    best, diff = {}, {}
    for m, g in t.groupby("module"):
        g = g.sort_values(["delta_j", "setting"])
        best[m] = int(g.iloc[0].setting)
        diff[m] = float(abs(g.delta_j.max() - g.delta_j.min()))
    return best, diff


def load_manifest():
    rows = [
        json.loads(x)
        for x in (HERE / "paper1_initial_candidates.jsonl").read_text().splitlines()
        if x
    ]
    seen = {r["combo_id"] for r in rows}
    for a in ANCHORS:
        if cid_of(a) not in seen:
            rows.append({"combo_id": cid_of(a), "modules": sorted(a), "anchor_added": True})
    anchor_ids = {cid_of(a) for a in ANCHORS}
    for r in rows:
        r["anchor"] = r["combo_id"] in anchor_ids
    return rows


def supported_or_record(rows, best, phase, prefix, setting_fn):
    """Split rows into runnable specs and record UNSUPPORTED/NOT_IMPLEMENTED ones in the ledger."""
    specs, meta = [], {}
    done = {r["config_id"] for r in ledger_rows()}
    for r in rows:
        n = f"{prefix}_{r['combo_id']}"
        if n in done:
            continue
        sp = {"modules": [mod_spec(m, setting_fn(r, m)) for m in r["modules"]], "name": n}
        mt = {"phase": phase, "combo_id": r["combo_id"], "k": len(r["modules"]),
              "anchor": r.get("anchor", False), "families": sorted({m[0] for m in r["modules"]})}  # fmt: skip
        try:
            comp.validate_spec(sp)
            specs.append(sp)
            meta[n] = mt
        except (comp.UnsupportedCombo, comp.NotImplementedModule) as e:
            ledger_append({"config_id": n, "modules": resolved(sp), "code_sha": sha(), "status": e.status,
                           "failure": str(e), "subset_id": subset()["subset_id"], "contract": CONTRACT, **mt})  # fmt: skip
    return specs, meta


def phase2(workers):
    best, _ = best_settings()
    rows = [r for r in load_manifest() if len(r["modules"]) > 1]
    # K1 manifest rows reuse the Phase-1 better-setting run (identical config, identical keys)
    specs, meta = supported_or_record(rows, best, 2, "P2", lambda r, m: best[m])
    for i, ch in enumerate(chunks(specs, BATCH)):
        run_batch(f"p2_{i:03d}", ch, meta, workers)


def adjust(workers, top_frac=1.0):
    best, diff = best_settings()
    L = ledger_ok()
    rows = [r for r in load_manifest() if len(r["modules"]) > 1 and f"P2_{r['combo_id']}" in L]
    rows.sort(key=lambda r: L[f"P2_{r['combo_id']}"]["delta_j"])
    rows = rows[: math.ceil(top_frac * len(rows))]
    specs, meta = [], {}
    done = {r["config_id"] for r in ledger_rows()}
    for r in rows:
        n = f"P2A_{r['combo_id']}"
        if n in done:
            continue
        sw = max(r["modules"], key=lambda m: (diff[m], m))
        if diff[sw] == 0:
            ledger_append({"config_id": n, "status": "SKIPPED_NO_SETTING_EFFECT", "combo_id": r["combo_id"],
                           "phase": "2A", "failure": "both Phase-1 settings of every module gave identical dJ"})  # fmt: skip
            continue
        specs.append({"modules": [mod_spec(m, (1 - best[m]) if m == sw else best[m]) for m in r["modules"]],
                      "name": n})  # fmt: skip
        meta[n] = {"phase": "2A", "combo_id": r["combo_id"], "k": len(r["modules"]), "switched_module": sw,
                   "anchor": r.get("anchor", False), "families": sorted({m[0] for m in r["modules"]})}  # fmt: skip
    for i, ch in enumerate(chunks(specs, BATCH)):
        run_batch(f"p2a_{i:03d}", ch, meta, workers)


def results_csv():
    """combo_id, delta_j, delta_loss_pp, se_j for every evaluated base configuration (K1 from Phase 1)."""
    best, _ = best_settings()
    L = ledger_ok()
    rows = []
    for m, s in best.items():
        r = L[f"P1_{m}_s{s}"]
        rows.append((cid_of([m]), r["delta_j"], r["delta_loss_pp"], r["se_j"]))
    for n, r in L.items():
        if n.startswith("P2_"):
            rows.append((r["combo_id"], r["delta_j"], r["delta_loss_pp"], r["se_j"]))
    p = OUT / "results_phase2.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["combo_id", "delta_j", "delta_loss_pp", "se_j"])
        w.writerows(rows)
    return p


def guided(workers):
    p = results_csv()
    out = OUT / "guided_proposals.jsonl"
    if not out.exists():
        subprocess.run([sys.executable, str(HERE / "paper1_combo_sampler.py"), "guided", "--results",
                        str(p), "--out", str(out)], check=True)  # fmt: skip
    best, _ = best_settings()
    rows = [json.loads(x) for x in out.read_text().splitlines() if x]
    specs, meta = supported_or_record(rows, best, "2G", "P2G", lambda r, m: best[m])
    for i, ch in enumerate(chunks(specs, BATCH)):
        run_batch(f"p2g_{i:03d}", ch, meta, workers)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "cmd", choices=["subset", "phase1", "phase2", "adjust", "guided", "analyze", "all"]
    )
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--adjust-frac", type=float, default=1.0)
    a = ap.parse_args()
    RUN.mkdir(parents=True, exist_ok=True)
    if a.cmd == "subset":
        print(json.dumps(make_subset())[:300])
        return
    if a.cmd in ("phase1", "all"):
        phase1(a.workers)
    if a.cmd in ("phase2", "all"):
        phase2(a.workers)
    if a.cmd in ("adjust", "all"):
        adjust(a.workers, a.adjust_frac)
    if a.cmd in ("guided", "all"):
        guided(a.workers)
    if a.cmd == "analyze":
        import analyze_phase12

        analyze_phase12.main()


if __name__ == "__main__":
    main()
