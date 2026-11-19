"""Phase 3 (Addendum B): systematic Rdatasets mining.

Stage 1 (screen): fetch every candidate CSV in results/phase3_candidates.json, form streams, compute r1, write
results/attempts_phase3_screen.jsonl. Stage 2 (evaluate): passing streams in order (max 150): fit, G1, G2, delay-1
grid, non-degeneracy (max-rho positive cell needs C0 - U_iid >= 0.1), delay 2 for non-degenerate positives, shuffle
control (5 shuffles, seeds 20261116 + k). Stops when 10 distinct items qualify (positive, non-degenerate, <= 1 of 5
shuffles positive). Resumable. Usage: run_phase3.py [screen|eval]
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as ev  # noqa: E402
import fit as ft  # noqa: E402

ROOT = HERE.parents[3]
RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
RAW = ROOT / "data/raw/real_chains/phase3"
CANDS = RES / "phase3_candidates.json"
SCREEN = RES / "attempts_phase3_screen.jsonl"
ATT = RES / "attempts_phase3.jsonl"
MANIFEST = RAW / "SOURCE_manifest.jsonl"
R1_CUT = -0.15
RHO_POS = 1e-3
GAP_MIN = 0.1
MAX_EVAL = 150
TARGET = 10
FIT_CAP_S = 120.0
INDEX_NAMES = {"time", "Time", "date", "Date", "year", "Year", "month", "rownames", "X", ""}
NA = {"NA", "", "NaN", "nan", "NULL"}


def lag1(x):
    x = np.asarray(x, float)
    if len(x) < 3 or x.std() == 0:
        return float("nan")
    return float(np.corrcoef(x[:-1], x[1:])[0, 1])


def is_counter(v):
    v = np.asarray(v, float)
    return len(v) > 1 and bool(np.all(v == np.round(v))) and bool(np.all(np.diff(v) == 1))


def get_csv(c):
    d = RAW / c["package"]
    d.mkdir(parents=True, exist_ok=True)
    safe = c["item"].replace("/", "_").replace(" ", "_")
    p = d / f"{safe}.csv"
    if p.exists():
        return p.read_bytes()
    r = requests.get(c["csv"], timeout=60, headers={"User-Agent": "research-fetch/1.0"})
    if r.status_code != 200 or len(r.content) > 1_000_000:
        raise RuntimeError(f"HTTP {r.status_code}, {len(r.content)} bytes")
    p.write_bytes(r.content)
    with open(MANIFEST, "a") as fh:
        fh.write(json.dumps(dict(url=c["csv"], retrieved_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(),
                                 file=str(p.relative_to(ROOT)))) + "\n")
    time.sleep(0.2)
    return r.content


def streams_of(content):
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace"))))
    if not rows:
        return []
    out = []
    for name in sorted(rows[0].keys()):
        if name in INDEX_NAMES:
            continue
        vals = [r.get(name, "") for r in rows]
        if any(s not in NA and not _isnum(s) for s in vals):
            continue  # not numeric
        v = np.array([float(s) for s in vals if s not in NA])
        if len(v) < 3:
            continue
        if is_counter(v):
            out.append(dict(column=name, skipped="integer row counter"))
            continue
        nd = len(np.unique(v))
        if nd < 40:
            out.append(dict(column=name, skipped=f"{nd} distinct values < 40"))
            continue
        out.append(dict(column=name, rule="abovemedian", x=(v > np.median(v)).astype(int), n_values=len(v)))
        out.append(dict(column=name, rule="rises", x=(np.diff(v) > 0).astype(int), n_values=len(v)))
    return out


def _isnum(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def stage_screen():
    cands = json.loads(CANDS.read_text())["candidates"]
    done = set()
    if SCREEN.exists():
        for line in SCREEN.read_text().splitlines():
            r = json.loads(line)
            done.add((r["package"], r["item"]))
    RAW.mkdir(parents=True, exist_ok=True)
    for c in cands:
        if (c["package"], c["item"]) in done:
            continue
        recs = []
        try:
            ss = streams_of(get_csv(c))
            for s in ss:
                if "skipped" in s:
                    recs.append(dict(column=s["column"], skipped=s["skipped"]))
                    continue
                x = s["x"]
                r1 = lag1(x)
                recs.append(dict(column=s["column"], rule=s["rule"], n=int(len(x)), n_ones=int(x.sum()), r1=r1,
                                 passes_screen=bool(r1 == r1 and r1 <= R1_CUT)))
            err = None
        except Exception as ex:  # noqa: BLE001
            err = f"{type(ex).__name__}: {ex}"
        with open(SCREEN, "a") as fh:
            fh.write(json.dumps(dict(package=c["package"], item=c["item"], error=err, streams=recs)) + "\n")
        print(c["package"], c["item"], err or f"{sum(1 for r in recs if 'r1' in r)} streams", flush=True)


def eval_stream(x, tag):
    """Fit, gates, delay-1 grid, non-degeneracy for one 0/1 stream. Returns dict."""
    t0 = time.perf_counter()
    rec = {}
    fit = ft.fit_hmm(x, deadline=t0 + 80)
    g1 = ft.gate_g1(x, full_fit=fit, deadline=time.perf_counter() + 40)
    g2 = ft.gate_g2(fit)
    rec.update(fit=fit, g1=g1, g2=g2, eigenvalue=1 - fit["t01"] - fit["t10"],
               time_fit_s=time.perf_counter() - t0, fit_time_cap_hit=bool(fit["time_cap_hit"] or g1["first_half_fit"]["time_cap_hit"]))
    flags = []
    if any(g2["at_bounds"].values()):
        flags.append("param_at_bound:" + ",".join(k for k, v in g2["at_bounds"].items() if v))
    if fit["e0"] < 0.02 or fit["e1"] > 0.98:
        flags.append("near_deterministic_emission")
    if fit["t01"] + fit["t10"] > 1 and (fit["t01"] > 0.9 or fit["t10"] > 0.9):
        flags.append("t01+t10>1_with_t_near_1")
    pos = False
    nondeg = False
    if g2["pass_"]:
        sp = ft.solver_params(fit)
        rec["solver_params"] = sp
        cells = ev.eval_chain(sp, delay1=True, delay2=False, log=lambda *_: None)
        rec["cells_d1"] = cells
        ok = [c for c in cells if c["status"] == "ok"]
        rec["n_cells_ok"] = len(ok)
        prim = next((c for c in ok if (c["T"], c["B"]) == ev.PRIMARY), None)
        rec["rho_primary"] = prim["rho_Gamma"] if prim else None
        if ok:
            best = max(ok, key=lambda c: c["rho_Gamma"])
            rec["rho_max"] = best["rho_Gamma"]
            rec["best_cell"] = dict(T=best["T"], B=best["B"], rho=best["rho_Gamma"], C0=best["C0"], U_iid=best["U_iid"],
                                    C0_minus_Uiid=best["C0"] - best["U_iid"], risk_iid_policy=best["risk_causal_of_iid_policy"],
                                    gamma=best["Gamma"])
            posc = [c for c in ok if c["rho_Gamma"] > RHO_POS]
            rec["positive_cells"] = [dict(T=c["T"], B=c["B"], rho=c["rho_Gamma"], C0_minus_Uiid=c["C0"] - c["U_iid"],
                                          risk_iid_policy=c["risk_causal_of_iid_policy"]) for c in posc]
            pos = bool(g1["pass_"] and posc)
            nondeg = bool(pos and rec["best_cell"]["C0_minus_Uiid"] >= GAP_MIN)
            rec["nondeg_alt_any_positive_cell_gap_ok"] = bool(posc and max(c["C0"] - c["U_iid"] for c in posc) >= GAP_MIN)
            if any(c.get("degenerate_zero_voi") for c in ok):
                flags.append("zero_voi_cells")
        rec["positive_primary_rule"] = bool(g1["pass_"] and rec["rho_primary"] is not None and rec["rho_primary"] > RHO_POS)
    rec.update(positive_any_cell=pos, nondegenerate_positive=nondeg, degeneracy_flags=flags, tag=tag,
               runtime_s=time.perf_counter() - t0)
    return rec


def stage_eval():
    scr = [json.loads(line) for line in SCREEN.read_text().splitlines()]
    passing = []
    for it in scr:
        for s in it["streams"]:
            if s.get("passes_screen"):
                passing.append((it["package"], it["item"], s["column"], s["rule"], s))
    passing.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    done = {}
    if ATT.exists():
        for line in ATT.read_text().splitlines():
            r = json.loads(line)
            done[r["seq"]] = r
    contents = {}
    print(len(passing), "streams passed the screen;", min(MAX_EVAL, len(passing)), "to evaluate", flush=True)
    for seq, (pkg, item, col, rule, s) in enumerate(passing[:MAX_EVAL], start=1):
        qual = {r["item_key"] for r in done.values() if r.get("qualifies")}
        if len(qual) >= TARGET:
            print("10 distinct items qualify; stopping")
            break
        if seq in done:
            continue
        key = f"{pkg}/{item}"
        if key not in contents:
            cand = next(c for c in json.loads(CANDS.read_text())["candidates"] if (c["package"], c["item"]) == (pkg, item))
            contents[key] = streams_of(get_csv(cand))
        x = next(q["x"] for q in contents[key] if q.get("column") == col and q.get("rule") == rule)
        print(f"[Q{seq}] {key} {col} {rule} n={len(x)} r1={s['r1']:.3f}", flush=True)
        rec = eval_stream(x, f"{key}:{col}:{rule}")
        rec.update(seq=seq, package=pkg, item=item, item_key=key, column=col, rule=rule, n=int(len(x)), r1=s["r1"],
                   n_ones=int(x.sum()))
        rec["qualifies"] = False
        if rec["nondegenerate_positive"]:
            rec["cells_d2"] = ev.eval_chain(rec["solver_params"], delay1=False, delay2=True, log=lambda *_: None)
            sh = []
            for k in range(5):
                rng = np.random.default_rng(20261116 + k)
                xs = rng.permutation(x)
                r = eval_stream(xs, f"shuffle{k}")
                sh.append(dict(k=k, seed=20261116 + k, g1_pass=r["g1"]["pass_"], g2_pass=r["g2"]["pass_"],
                               positive_any_cell=r["positive_any_cell"], nondegenerate_positive=r["nondegenerate_positive"],
                               rho_max=r.get("rho_max"), fit={a: r["fit"][a] for a in ("t01", "t10", "e0", "e1")},
                               fit_time_cap_hit=r["fit_time_cap_hit"], runtime_s=r["runtime_s"]))
            rec["shuffles"] = sh
            rec["shuffle_g1_passes"] = sum(r["g1_pass"] for r in sh)
            rec["shuffle_positives"] = sum(r["nondegenerate_positive"] for r in sh)
            rec["shuffle_positives_any_cell_only"] = sum(r["positive_any_cell"] for r in sh)
            rec["qualifies"] = bool(rec["shuffle_positives"] <= 1)
        (RES / f"q{seq:03d}_{pkg}_{item.split(' ')[0]}_{col}_{rule}.json".replace("/", "_")).write_text(json.dumps(rec, indent=1, default=str))
        with open(ATT, "a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        done[seq] = rec
        print(f"   -> pos={rec['positive_any_cell']} nondeg={rec['nondegenerate_positive']} qual={rec['qualifies']} "
              f"G1={rec['g1']['pass_']} G2={rec['g2']['pass_']} rho_max={rec.get('rho_max')} ({rec['runtime_s']:.0f}s)", flush=True)
        print("   QUALIFYING ITEMS:", len({r['item_key'] for r in done.values() if r.get('qualifies')}), flush=True)
    print("DONE")


if __name__ == "__main__":
    {"screen": stage_screen, "eval": stage_eval}[sys.argv[1]]()
