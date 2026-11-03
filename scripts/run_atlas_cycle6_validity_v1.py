"""Failure Atlas v1, Amendment 7 (cycle 6): sampling-density validity study on boundary null streams.

Protocol: docs/failure_atlas_v1_protocol.md, Amendment 7 (predictions V1-V4 locked there). Null twins
only; no cost stages. Development evidence, not confirmatory. Seeds: development [150000, 150200).

    .venv/Scripts/python scripts/run_atlas_cycle6_validity_v1.py                 # full, resumable
    .venv/Scripts/python scripts/run_atlas_cycle6_validity_v1.py --summarize-only
    .venv/Scripts/python scripts/run_atlas_cycle6_validity_v1.py --smoke --out <dir>

Checkpoint: ``<out>/configs.jsonl`` (one line per finished configuration; completed configurations
are skipped on restart).
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_release_hook import outcome_delay
from shiftlab.dive.switching_explore import paired_ci

SOURCES = (
    "src/shiftlab/dive/failure_atlas.py",
    "src/shiftlab/dive/atlas_components.py",
    "src/shiftlab/dive/atlas_release_hook.py",
    "src/shiftlab/dive/atlas_r6_baselines.py",
    "src/shiftlab/dive/switching_explore.py",
    "src/shiftlab/dive/eprocess.py",
    "scripts/run_failure_atlas_loop.py",
    "scripts/run_atlas_cycle6_validity_v1.py",
)
STRADDLE_ID = "b1a17927d9ad"
AXES_SEARCHED = ["onset", "duration", "s", "d", "budget_frac", "effect", "rate", "unknown"]
ALPHA = 0.1
THRESH = ALPHA + 0.05
RHOS = (0.0, 0.5, 0.8, 0.95)
BTS = (0.05, 0.1, 0.25, 0.5)
DS = (1, 10)
REL_BTS = (0.1, 0.25)
N_SEEDS = 200
SEED_OFFSET = 50000  # development [150000, 150200)
CHUNK = 10
V1_METHODS = (
    "episode_geo",
    "episode_equal",
    "episode_front",
    "allonset_edetector",
    "online_fwer_spending",
    "c2_rho0.75",
)
GATED = tuple(fa.gated_methods())
ALL_COLS = (*GATED, "R_valid", "straddle", "straddle_abl")


# ------------------------------------------------------------------ cells (thin wrappers)


@dataclass(frozen=True)
class ReleaseCell(fa.Family4CellSpec):
    """Family-4 cell with explicit ``(d_f, d_u)`` release delays (e.g. 10g, which the registry lacks)."""

    df: int = 1
    du: int = 1

    @property
    def delays(self) -> tuple[int, int]:
        return (self.df, self.du)

    @property
    def delay_fn(self):
        return outcome_delay(self.df, self.du)

    @property
    def cell_id(self) -> str:
        return (
            f"f4x_df{self.df}_du{self.du}_d{self.d}_b{self.budget_frac:g}_s{self.s:g}"
            + (f"_T{self.T}" if self.T != fa.T_DEFAULT else "")
            + ("_NULL" if self.null else "")
        )


def build_null_cell(kind: str, p: dict, T: int):
    if kind == "dep":
        c = fa.Family3CellSpec(p["rho"], 0.3, 0.6, "strong", "harmful", p["d"], p["bt"], T=T)
    else:
        c = ReleaseCell(
            "same", 0.3, 0.6, "strong", "harmful", p["g"], p["bt"], T=T, df=p["df"], du=p["du"]
        )
    return c.null_twin()


def config_list(T: int) -> list[dict]:
    out = []
    for rho in RHOS:
        for bt in BTS:
            for d in DS:
                out.append(
                    {
                        "id": f"dep_rho{rho:g}_bt{bt:g}_d{d}",
                        "kind": "dep",
                        "rho": rho,
                        "bt": bt,
                        "d": d,
                    }
                )
    for bt in REL_BTS:
        g = round(1 / bt)
        out.append(
            {
                "id": f"rel_bt{bt:g}_fav_first",
                "kind": "rel",
                "arm": "fav",
                "bt": bt,
                "g": g,
                "df": g,
                "du": 10 * g,
            }
        )
        out.append(
            {
                "id": f"rel_bt{bt:g}_control",
                "kind": "rel",
                "arm": "ctl",
                "bt": bt,
                "g": g,
                "df": 10 * g,
                "du": g,
            }
        )
    return out


# ------------------------------------------------------------------ worker

_SPECS: dict = {}


def specs():
    if not _SPECS:
        st = None
        for ax in AXES_SEARCHED:
            for sp in comp.propose_candidates(ax, max_n=60):
                if sp.spec_id == STRADDLE_ID:
                    st = sp
                    break
            if st:
                break
        if st is None:
            raise LookupError(STRADDLE_ID)
        _SPECS["straddle"] = st
        _SPECS["straddle_abl"] = comp.ablation_of(st, st.focus)
    return _SPECS


def task(args: tuple) -> dict:
    cfg_def, seed_list, T = args
    cell = build_null_cell(cfg_def["kind"], cfg_def, T)
    sp = specs()
    bern = fa.bernoulli_grid_spec()
    fp = {m: [] for m in ALL_COLS}
    for sd in seed_list:
        stream = fa.make_stream(cell, sd)
        cfg = cell.config(sd)

        def go(method, stream=stream, cfg=cfg):
            r = fa.run_for(cell, stream, method, cfg)
            return int((r.fp_regime or 0) > 0)

        for m in GATED:
            fp[m].append(go(fa.make_method(m, bern, cfg)))
        fp["R_valid"].append(go(fa.build_ref_valid(cell)))
        for n in ("straddle", "straddle_abl"):
            fp[n].append(go(comp.build_candidate(sp[n])))
    return {"id": cfg_def["id"], "seeds": [int(s) for s in seed_list], "fp": fp}


# ------------------------------------------------------------------ checkpoint / run


def load_done(path: Path) -> dict[str, dict]:
    done = {}
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            if line.strip():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # truncated last line from a killed process
                done[r["id"]] = r
    return done


def run(out: Path, T: int, seed_list, workers: int, configs: list[dict]) -> None:
    ck = out / "configs.jsonl"
    done = load_done(ck)
    todo = [c for c in configs if c["id"] not in done]
    print(f"{len(done)} configs done, {len(todo)} to run; workers={workers}", flush=True)
    t0 = time.time()
    work = [
        (c, tuple(seed_list[i : i + CHUNK]), T)
        for c in todo
        for i in range(0, len(seed_list), CHUNK)
    ]
    parts: dict[str, list[dict]] = {c["id"]: [] for c in todo}
    n_chunks = -(-len(seed_list) // CHUNK)
    cdef = {c["id"]: c for c in todo}
    fin = [0]

    def finish(cid: str) -> None:
        ps = sorted(parts[cid], key=lambda p: p["seeds"][0])
        rec = {
            "id": cid,
            "config": cdef[cid],
            "T": T,
            "seeds": [s for p in ps for s in p["seeds"]],
            "fp": {m: [v for p in ps for v in p["fp"][m]] for m in ALL_COLS},
        }
        with ck.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        fin[0] += 1
        el = time.time() - t0
        print(
            f"[{el:.0f}s] finished {cid} ({fin[0]}/{len(todo)}); "
            f"ETA {el / fin[0] * (len(todo) - fin[0]):.0f}s",
            flush=True,
        )

    def handle(res: dict) -> None:
        parts[res["id"]].append(res)
        if len(parts[res["id"]]) == n_chunks:
            finish(res["id"])

    if workers <= 1:
        for w in work:
            handle(task(w))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(task, w) for w in work]
            for f in as_completed(futs):
                handle(f.result())


# ------------------------------------------------------------------ analysis


def git_info() -> dict:
    def g(*a):
        return subprocess.run(
            ["git", *a], check=False, cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()

    return {
        "head": g("rev-parse", "HEAD"),
        "dirty": bool(g("status", "--porcelain")),
        "src_sha256": {
            f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
            for f in SOURCES
            if (ROOT / f).exists()
        },
    }


def W(k: int, n: int) -> tuple[float, float, float]:
    return fa.wilson(int(k), int(n))


def cell_txt(k: int, n: int) -> str:
    p, lo, hi = W(k, n)
    return f"{p:.3f} [{lo:.3f},{hi:.3f}]"


def pooled(recs: list[dict], m: str) -> tuple[int, int]:
    return sum(sum(r["fp"][m]) for r in recs), sum(len(r["fp"][m]) for r in recs)


def _rate(recs, m):
    k, n = pooled(recs, m)
    return {"k": k, "n": n, "rate": k / n if n else float("nan")}


def analyse(done: dict[str, dict]) -> dict:
    dep = [r for r in done.values() if r["config"]["kind"] == "dep"]
    rel = [r for r in done.values() if r["config"]["kind"] == "rel"]
    res: dict = {"n_dep": len(dep), "n_rel": len(rel)}
    # V1
    sub = [r for r in dep if r["config"]["rho"] == 0.8 and r["config"]["bt"] == 0.5]
    v1 = {m: _rate(sub, m) for m in V1_METHODS}
    res["V1"] = {
        "rates": v1,
        "pass": bool(sub) and any(v["rate"] > THRESH for v in v1.values()),
        "complete": len(sub) == len(DS),
    }
    # V2
    sub = [r for r in dep if r["config"]["rho"] == 0.8]
    if sub:
        a = np.concatenate([r["fp"]["straddle"] for r in sub]).astype(float)
        b = np.concatenate([r["fp"]["straddle_abl"] for r in sub]).astype(float)
        m, lo, hi = paired_ci(a - b)
        res["V2"] = {
            "mean_diff": m,
            "ci": [lo, hi],
            "n": len(a),
            "straddle_rate": float(a.mean()),
            "ablation_rate": float(b.mean()),
            "pass": bool(lo > 0),
            "complete": len(sub) == len(BTS) * len(DS),
        }
    else:
        res["V2"] = None
    # V3
    fav = [r for r in rel if r["config"]["arm"] == "fav"]
    ctl = [r for r in rel if r["config"]["arm"] == "ctl"]
    v3 = {"fav": {m: _rate(fav, m) for m in GATED}, "ctl": {m: _rate(ctl, m) for m in GATED}}
    exceed = [m for m in GATED if v3["fav"][m]["n"] and v3["fav"][m]["rate"] > THRESH]
    ctl_ok = bool(ctl) and all(v3["ctl"][m]["rate"] <= ALPHA for m in exceed)
    ctl_strict = bool(ctl) and all(v3["ctl"][m]["rate"] <= ALPHA for m in GATED)
    res["V3"] = {
        "rates": v3,
        "exceeding_fav": exceed,
        "control_ok_for_exceeding": ctl_ok,
        "control_ok_all_gated": ctl_strict,
        "pass": bool(exceed) and ctl_ok,
        "complete": len(fav) == len(REL_BTS) and len(ctl) == len(REL_BTS),
    }
    # V4
    v4 = {}
    for m in (*V1_METHODS, "c1_hmm_cs", "R_valid", "straddle", "straddle_abl"):
        xs = [r["config"]["rho"] ** (1.0 / r["config"]["bt"]) for r in dep]
        ys = [float(np.mean(r["fp"][m])) for r in dep]
        if len(set(ys)) > 1 and len(set(xs)) > 1:
            s = float(stats.spearmanr(xs, ys).statistic)
        else:
            s = float("nan")
        v4[m] = {"spearman": s, "n_configs": len(xs)}
    npos = sum(1 for m in V1_METHODS if v4[m]["spearman"] > 0)
    res["V4"] = {
        "per_method": v4,
        "n_positive_eprocess": npos,
        "n_eprocess": len(V1_METHODS),
        "most_positive": npos > len(V1_METHODS) / 2,
    }
    if res["V1"]["pass"] and res["V4"]["most_positive"]:
        verdict = (
            "RETAINED: V1 holds and the V4 Spearman correlation is positive for most e-process "
            "baselines; the sampling-density explanation is retained."
        )
    elif not res["V1"]["pass"]:
        verdict = (
            "NOT RETAINED (V1 fails): the e-process gates are robust to Markov dependence at this "
            "boundary; the dependence row of the failure table is closed for published baselines."
        )
    else:
        verdict = (
            "NOT RETAINED: V1 holds but the V4 Spearman correlation is positive for at most half "
            "of the e-process baselines."
        )
    res["verdict"] = verdict
    return res


def pf(b: bool) -> str:
    return "PASS" if b else "FAIL"


def write_summary(out: Path, T: int, done: dict[str, dict]) -> None:
    A = analyse(done)
    g = git_info()
    L = [
        "# Failure Atlas v1, cycle 6 (Amendment 7): sampling-density validity study",
        "",
        (
            "Boundary null twins only; development seeds; descriptive (nothing here is confirmatory). "
            f"T={T}, alpha={ALPHA}, threshold alpha+0.05={THRESH:.2f}. "
            f"Configurations finished: dependence {A['n_dep']}/{len(RHOS) * len(BTS) * len(DS)}, "
            f"release {A['n_rel']}/{2 * len(REL_BTS)}."
        ),
        "",
    ]
    some = next(iter(done.values()), None)
    if some:
        L.append(
            f"Seeds per configuration: {len(some['seeds'])} "
            f"([{some['seeds'][0]}, {some['seeds'][-1]}]). False promotion = any promotion on the "
            "null twin (`fp_regime > 0`); Wilson 95% CIs."
        )
        L.append("")
    hdr = " | ".join(ALL_COLS)
    L += [
        "## Dependence grid: null false-promotion rate",
        "",
        f"| rho | B/T | d | {hdr} |",
        "|---|---|---|" + "---|" * len(ALL_COLS),
    ]
    for r in sorted(
        (r for r in done.values() if r["config"]["kind"] == "dep"),
        key=lambda r: (r["config"]["rho"], r["config"]["bt"], r["config"]["d"]),
    ):
        c = r["config"]
        L.append(
            f"| {c['rho']:g} | {c['bt']:g} | {c['d']} | "
            + " | ".join(cell_txt(sum(r["fp"][m]), len(r["fp"][m])) for m in ALL_COLS)
            + " |"
        )
    L += [
        "",
        "## Release grid (rho = 0): null false-promotion rate",
        "",
        f"| B/T | arm | (d_f, d_u) | {hdr} |",
        "|---|---|---|" + "---|" * len(ALL_COLS),
    ]
    for r in sorted(
        (r for r in done.values() if r["config"]["kind"] == "rel"),
        key=lambda r: (r["config"]["bt"], r["config"]["arm"]),
    ):
        c = r["config"]
        L.append(
            f"| {c['bt']:g} | {'favourable-first' if c['arm'] == 'fav' else 'control'} | "
            f"({c['df']}, {c['du']}) | "
            + " | ".join(cell_txt(sum(r["fp"][m]), len(r["fp"][m])) for m in ALL_COLS)
            + " |"
        )
    L += ["", "## Locked predictions", ""]
    v1 = A["V1"]
    L.append(
        f"**V1: {pf(v1['pass'])}** (rho=0.8, B/T=0.5, pooled over d; any of "
        f"{', '.join(V1_METHODS)} with rate > {THRESH:.2f})"
        + ("" if v1["complete"] else "  [INCOMPLETE: configurations missing]")
    )
    L += ["", "| method | k/n | rate [Wilson] | exceeds |", "|---|---|---|---|"]
    for m, v in v1["rates"].items():
        L.append(
            f"| {m} | {v['k']}/{v['n']} | {cell_txt(v['k'], v['n'])} | "
            f"{'yes' if v['rate'] > THRESH else 'no'} |"
        )
    v2 = A["V2"]
    L.append("")
    if v2:
        L.append(
            f"**V2: {pf(v2['pass'])}** (rho=0.8 pooled over B/T and d, n={v2['n']} paired seeds): "
            f"straddle {v2['straddle_rate']:.3f} - ablation {v2['ablation_rate']:.3f} = "
            f"{v2['mean_diff']:+.4f}, 95% paired CI [{v2['ci'][0]:+.4f}, {v2['ci'][1]:+.4f}]"
            + ("" if v2["complete"] else "  [INCOMPLETE]")
        )
    else:
        L.append("**V2: NOT EVALUABLE** (no rho=0.8 configurations)")
    v3 = A["V3"]
    L += [
        "",
        f"**V3: {pf(v3['pass'])}** (favourable-first, d_u = 10g, pooled over the two spacings; "
        f"gated baselines above {THRESH:.2f}: {', '.join(v3['exceeding_fav']) or 'none'}; "
        f"control (10g, g) at or below alpha for those baselines: {pf(v3['control_ok_for_exceeding'])}; "
        f"for all gated baselines: {pf(v3['control_ok_all_gated'])})"
        + ("" if v3["complete"] else "  [INCOMPLETE]"),
        "",
        "| method | favourable-first | control |",
        "|---|---|---|",
    ]
    for m in GATED:
        a, b = v3["rates"]["fav"][m], v3["rates"]["ctl"][m]
        L.append(f"| {m} | {cell_txt(a['k'], a['n'])} | {cell_txt(b['k'], b['n'])} |")
    L += [
        "",
        (
            "**V4 (descriptive)**: Spearman correlation across the dependence grid between null "
            "false-promotion rate and rho^(T/B)."
        ),
        "",
        "| method | Spearman | e-process baseline |",
        "|---|---|---|",
    ]
    for m, v in A["V4"]["per_method"].items():
        L.append(f"| {m} | {v['spearman']:.3f} | {'yes' if m in V1_METHODS else 'no'} |")
    L += [
        "",
        (
            f"Positive for {A['V4']['n_positive_eprocess']}/{A['V4']['n_eprocess']} e-process baselines "
            f"(most: {A['V4']['most_positive']})."
        ),
        "",
        "## Interpretation-rule verdict",
        "",
        A["verdict"],
        "",
        "## Provenance",
        "",
        f"- git head: `{g['head']}`",
        f"- dirty working tree: {g['dirty']}",
        "- source sha256:",
    ]
    for f, h in g["src_sha256"].items():
        L.append(f"  - `{f}`: `{h}`")
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "analysis.json").write_text(
        json.dumps({"analysis": A, "git": g}, indent=1, default=float), encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--T", type=int, default=fa.T_DEFAULT)
    ap.add_argument("--n-seeds", type=int, default=N_SEEDS)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "failure_atlas_v1_cycle6"))
    ap.add_argument("--smoke", action="store_true", help="small subset of configurations")
    ap.add_argument("--summarize-only", action="store_true")
    a = ap.parse_args()
    workers = max(1, min(a.workers, 10))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    configs = config_list(a.T)
    if a.smoke:
        keep = {
            "dep_rho0.8_bt0.5_d10",
            "dep_rho0_bt0.1_d1",
            "rel_bt0.25_fav_first",
            "rel_bt0.25_control",
        }
        configs = [c for c in configs if c["id"] in keep]
    sd = fa.seeds("development", a.n_seeds, offset=SEED_OFFSET)
    assert sd[0] >= 150000 and sd[-1] < 160000
    if not a.summarize_only:
        run(out, a.T, sd, workers, configs)
    ids = {c["id"] for c in configs}
    done = {k: v for k, v in load_done(out / "configs.jsonl").items() if k in ids}
    write_summary(out, a.T, done)
    print(f"summary written to {out / 'summary.md'}", flush=True)


if __name__ == "__main__":
    main()
