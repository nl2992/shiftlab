"""Frozen, resumable cycle-7 validation; see docs/failure_atlas_cycle7_execution_v1.md."""

from __future__ import annotations

import os

for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_key, "1")

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from run_atlas_cycle6_validity_v1 import build_null_cell, config_list
from run_atlas_dss_tuning_v1 import F1_CELLS, build_cell, f3_failure_ids

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_dependence_baselines import DEP_METHODS, build_dep
from shiftlab.dive.switching_explore import paired_ci, wilson

BASELINES = (
    "episode_geo",
    "episode_equal",
    "episode_front",
    "allonset_edetector",
    "online_fwer_spending",
    "markov_lr_gate",
    "thinned_hedged_gate",
)
VARIANTS = ("dss", "no_delay_switch", "gap1", "uniform")
SUPPLEMENTARY = tuple(k for k, v in fa.r6_methods().items() if not v[1])
SOURCES = (
    "scripts/run_atlas_cycle7_validation_v1.py",
    "scripts/run_atlas_dss_tuning_v1.py",
    "scripts/run_atlas_cycle6_validity_v1.py",
    "src/shiftlab/dive/failure_atlas.py",
    "src/shiftlab/dive/atlas_components.py",
    "src/shiftlab/dive/atlas_dependence_baselines.py",
    "src/shiftlab/dive/atlas_r6_baselines.py",
    "src/shiftlab/dive/switching_explore.py",
    "src/shiftlab/dive/eprocess.py",
    "docs/failure_atlas_cycle7_execution_v1.md",
    "docs/failure_atlas_dss_positioning_v1.md",
    "outputs/failure_atlas_v1_cycle7/tuning/frozen.json",
    "outputs/failure_atlas_v1_cycle5/family3/summary.md",
)


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def specs():
    dss = comp.dss_spec(4, True)
    abl = comp.dss_ablations(dss)
    return {
        "dss": dss,
        "no_delay_switch": abl["no_switch"],
        "gap1": abl["gap1"],
        "uniform": abl["uniform"],
    }


def pack(cell):
    return {"family": cell.family, **asdict(cell)}


def unpack(data):
    data = dict(data)
    cls = {1: fa.CellSpec, 3: fa.Family3CellSpec}[data.pop("family")]
    return cls(**data)


def design(smoke=False):
    frozen = json.loads((ROOT / SOURCES[-2]).read_text("utf-8"))
    sp = specs()
    assert frozen["status"] == "frozen" and frozen["frozen_g"] == 4
    assert sp["dss"].spec_id == frozen["dss_spec_id"]
    assert {m for m in fa.gated_methods() if m not in ("c1_hmm_cs", "c2_rho0.75")} == set(
        BASELINES
    ) - set(DEP_METHODS)
    primary = [build_cell(i) for i in (*F1_CELLS, *f3_failure_ids())]
    if smoke:
        primary = [primary[0], primary[1], primary[-1]]
    neighbours = {c.cell_id: [n.cell_id for n in fa.neighbours(c)] for c in primary}
    cells = {c.cell_id: c for c in primary}
    cells.update({n.cell_id: n for c in primary for n in fa.neighbours(c)})
    if smoke:
        neighbours = {k: v[:1] for k, v in neighbours.items()}
        keep = {c.cell_id for c in primary} | {i for ns in neighbours.values() for i in ns}
        cells = {k: v for k, v in cells.items() if k in keep}
    nulls = [p for p in config_list(1000) if p["kind"] == "dep"]
    if smoke:
        nulls = [nulls[i] for i in (0, 10, 20, 30)]
    seed_list = list(range(180000, 180002)) if smoke else list(range(290000, 290200))
    jobs = []
    for cid, cell in cells.items():
        methods = (
            (*BASELINES, *VARIANTS, *SUPPLEMENTARY) if cid in neighbours else (*BASELINES, "dss")
        )
        jobs.append({"key": cid, "kind": "cost", "cell": pack(cell), "methods": methods})
    for p in nulls:
        jobs.append(
            {
                "key": p["id"],
                "kind": "null",
                "params": p,
                "cell": pack(build_null_cell("dep", p, 1000)),
                "methods": (*BASELINES, *VARIANTS, *SUPPLEMENTARY),
            }
        )
    return {
        "version": 1,
        "smoke": smoke,
        "seeds": seed_list,
        "chunk": 10,
        "primary": [c.cell_id for c in primary],
        "neighbours": neighbours,
        "spec_ids": {k: v.spec_id for k, v in sp.items()},
        "baselines": BASELINES,
        "supplementary": SUPPLEMENTARY,
        "jobs": jobs,
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES},
    }


def make_method(name, cfg, sp=None):
    if name in VARIANTS:
        return comp.build_candidate((sp or specs())[name])
    if name in DEP_METHODS:
        return build_dep(name, cfg)
    return fa.make_method(name, fa.bernoulli_grid_spec(), cfg)


def task(args):
    job, seeds = args
    cell, sp = unpack(job["cell"]), specs()
    values = {m: [] for m in job["methods"]}
    for sd in seeds:
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        for name in job["methods"]:
            r = fa.run_for(cell, stream, make_method(name, cfg, sp), cfg)
            if r.queries > cfg.B:
                raise AssertionError("hard budget violated")
            values[name].append(
                {
                    "cost": float(r.cost) / cell.T,
                    "loss": float(r.decision_loss) / cell.T,
                    "query_cost": float(r.query_cost) / cell.T,
                    "switch_cost": float(r.switch_cost) / cell.T,
                    "queries": r.queries,
                    "switches": r.switches,
                    "fp": int((r.fp_regime or 0) > 0),
                    "promoted": int(r.promotions > 0),
                    "correct": int(r.promotions > (r.fp_regime or 0)),
                }
            )
    return {"key": job["key"], "seeds": seeds, "values": values}


def load_records(path, manifest):
    records = {}
    if not path.exists():
        return records
    for line in path.read_text("utf-8").splitlines():
        r = json.loads(line)  # a truncated append is an integrity error, never silently skipped
        if r["manifest_digest"] != manifest:
            raise ValueError("checkpoint belongs to another manifest")
        key = (r["key"], tuple(r["seeds"]))
        if key in records:
            raise ValueError("duplicate completed seed chunk")
        records[key] = r
    return records


def ci(values):
    return [float(v) for v in paired_ci(np.asarray(values, dtype=float))]


def analyse(plan, records):
    data = {}
    for job in plan["jobs"]:
        parts = sorted(
            (r for r in records.values() if r["key"] == job["key"]), key=lambda r: r["seeds"][0]
        )
        if [sd for r in parts for sd in r["seeds"]] != plan["seeds"]:
            raise ValueError(f"incomplete seed set: {job['key']}")
        data[job["key"]] = {m: [v for r in parts for v in r["values"][m]] for m in job["methods"]}

    def arr(key, method, metric="cost"):
        return np.array([r[metric] for r in data[key][method]], dtype=float)

    best = {
        j["key"]: min(BASELINES, key=lambda m: arr(j["key"], m).mean())
        for j in plan["jobs"]
        if j["kind"] == "cost"
    }
    diffs = {k: arr(k, "dss") - arr(k, m) for k, m in best.items()}
    primary = {
        k: {
            "best": best[k],
            "delta": ci(diffs[k]),
            "passes_margin": ci(diffs[k])[2] < -0.01,
            "methods": {
                m: {
                    metric: float(arr(k, m, metric).mean())
                    for metric in ("cost", "fp", "promoted", "correct", "queries")
                }
                for m in data[k]
            },
        }
        for k in plan["primary"]
    }
    overall = np.mean([diffs[k] for k in plan["primary"]], axis=0)
    a1 = {
        "cell_passes": sum(v["passes_margin"] for v in primary.values()),
        "n_cells": len(primary),
        "aggregate": ci(overall),
    }
    a1["pass"] = a1["cell_passes"] * 2 >= len(primary) and a1["aggregate"][2] < 0
    neighbour = {
        k: ci(np.mean([diffs[n] for n in ns], axis=0)) for k, ns in plan["neighbours"].items()
    }
    a2 = {"per_parent": neighbour, "pass": all(v[2] < 0.01 for v in neighbour.values())}
    a3rows = {}
    for job in plan["jobs"]:
        if job["kind"] != "null":
            continue
        key, p = job["key"], job["params"]
        ms = {
            m: {
                "fp": float(arr(key, m, "fp").mean()),
                "k": int(arr(key, m, "fp").sum()),
                "wilson": list(wilson(int(arr(key, m, "fp").sum()), len(plan["seeds"]))),
            }
            for m in data[key]
        }
        b = min(BASELINES, key=lambda m: (ms[m]["fp"], arr(key, m).mean(), m))
        in_grid = p["rho"] in (0.0, 0.5, 0.8) and p["bt"] in (0.05, 0.1, 0.25)
        required_abs = in_grid and (p["rho"] == 0 or (p["rho"] == 0.5 and p["bt"] <= 0.1))
        required_rel = in_grid and p["rho"] == 0.8
        a3rows[key] = {
            "params": p,
            "methods": ms,
            "best_safety": b,
            "required_absolute": required_abs,
            "required_relative": required_rel,
            "absolute_pass": ms["dss"]["fp"] <= 0.15 + 1e-12,
            "relative_pass": ms["dss"]["fp"] - ms[b]["fp"] <= 0.05 + 1e-12,
        }
    a3 = {
        "rows": a3rows,
        "pass": all(
            (not r["required_absolute"] or r["absolute_pass"])
            and (not r["required_relative"] or r["relative_pass"])
            for r in a3rows.values()
        ),
        "absolute_rho08_pass": all(
            r["absolute_pass"] for r in a3rows.values() if r["required_relative"]
        ),
    }
    gain = -overall
    ablations = {}
    for name in VARIANTS[1:]:
        removed = np.mean([arr(k, name) - arr(k, "dss") for k in primary], axis=0)
        contrast = removed - 0.5 * gain
        ablations[name] = {
            "removed_gain": ci(removed),
            "half_gain_contrast": ci(contrast),
            "fraction_removed": float(removed.mean() / gain.mean()) if gain.mean() > 0 else None,
            "pass": bool(gain.mean() > 0 and contrast.mean() >= 0),
        }
    verdicts = {
        "A1": a1["pass"],
        "A2": a2["pass"],
        "A3": a3["pass"],
        "A4": ablations["uniform"]["pass"],
        "A5": "scoped prior-art audit carried forward; conditional",
    }
    return {
        "status": "SMOKE_ONLY" if plan["smoke"] else "VALIDATION_COMPLETE_NOT_CONFIRMATORY",
        "A1": a1,
        "A2": a2,
        "A3": a3,
        "A4": ablations,
        "primary": primary,
        "cost_cells": {k: {"best": best[k], "delta": ci(v)} for k, v in diffs.items()},
        "verdicts": verdicts,
        "accepted": bool(not plan["smoke"] and all(verdicts[k] for k in ("A1", "A2", "A3", "A4"))),
        "unique_method_runs": sum(len(j["methods"]) for j in plan["jobs"]) * len(plan["seeds"]),
    }


def fmt(v):
    return f"{v[0]:+.4f} [{v[1]:+.4f},{v[2]:+.4f}]"


def report(plan, result, manifest, elapsed):
    lines = [
        "# Failure Atlas cycle 7: fresh-seed validation",
        "",
        f"Status: {result['status']}. Manifest SHA256 `{manifest}`.",
        f"Seeds [{plan['seeds'][0]},{plan['seeds'][-1] + 1}); T=1000; {result['unique_method_runs']} method runs; execution session {elapsed:.1f}s.",
        "No pilot results are pooled into validation. Intervals are unadjusted and paired by seed; aggregate within seed before computing uncertainty.",
        "",
        "## Acceptance",
        "",
        "| criterion | result |",
        "|---|---|",
    ]
    lines += [f"| {k} | {v} |" for k, v in result["verdicts"].items()]
    lines += [
        "",
        f"Accepted: **{result['accepted']}**. Confirmation seeds remain untouched.",
        "A5 is the existing scoped absence search, not a proof of novelty. A4 primary refers to the whole acquisition component; inspect individual ablations before attributing a gain to new rules.",
        "",
        "## Primary cost comparisons",
        "",
        "| failure cell | best gated comparator | DSS minus best [95% CI] | margin pass |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| {k} | {v['best']} | {fmt(v['delta'])} | {v['passes_margin']} |"
        for k, v in result["primary"].items()
    ]
    lines += [
        "",
        f"A1: {result['A1']['cell_passes']}/{result['A1']['n_cells']} cells; aggregate {fmt(result['A1']['aggregate'])}.",
        "",
        "## Neighbour checks by parent",
        "",
        "| parent | average DSS minus neighbour's best [95% CI] |",
        "|---|---|",
    ]
    lines += [f"| {k} | {fmt(v)} |" for k, v in result["A2"]["per_parent"].items()]
    lines += [
        "",
        "## Acquisition ablations",
        "",
        "| ablation | gain removed [95% CI] | fraction removed | half-gain contrast [95% CI] | point rule |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {k} | {fmt(v['removed_gain'])} | {v['fraction_removed']} | {fmt(v['half_gain_contrast'])} | {v['pass']} |"
        for k, v in result["A4"].items()
    ]
    lines += [
        "",
        "## Full dependence null grid",
        "",
        "Wilson 95% intervals, per-cell and unadjusted. rho=.95 and B/T=.5 are stress-only; a relative pass does not establish absolute safety.",
        "",
        "| null cell | " + " | ".join((*BASELINES, *VARIANTS, *SUPPLEMENTARY)) + " |",
        "|---|" + "---|" * (len(BASELINES) + len(VARIANTS) + len(SUPPLEMENTARY)),
    ]
    for key, row in result["A3"]["rows"].items():
        values = [
            f"{m['fp']:.3f} [{m['wilson'][1]:.3f},{m['wilson'][2]:.3f}]"
            for m in row["methods"].values()
        ]
        lines.append(f"| {key} | " + " | ".join(values) + " |")
    lines += [
        "",
        "## Primary promotion and cost diagnostics",
        "",
        "Any promotion / correctly timed promotion / any false promotion are fractions of streams, separately scored from evaluator truth. Nongated R6 methods are contextual comparisons only.",
        "",
        "| cell | method | cost/round | queried labels | any promotion | correct promotion | false promotion |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, row in result["primary"].items():
        for name, vals in row["methods"].items():
            lines.append(
                f"| {key} | {name} | {vals['cost']:.5f} | {vals['queries']:.1f} | {vals['promoted']:.3f} | {vals['correct']:.3f} | {vals['fp']:.3f} |"
            )
    lines += [
        "",
        "## Complete cost-cell comparison table",
        "",
        "| cell | best comparator | DSS minus best [95% CI] |",
        "|---|---|---|",
    ]
    lines += [f"| {k} | {v['best']} | {fmt(v['delta'])} |" for k, v in result["cost_cells"].items()]
    lines += [
        "",
        "## Scope and implementation limitations",
        "",
        "The comparator registry consists of repository adaptations. Markov LR approximates unequal query gaps by a homogeneous skeleton. Gap-10 betting is the repository started mixture, with no proved mixing correction. Source-paper assumptions and guarantees are not transferred by the method names. No real-data or universal SOTA claim is supported.",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--freeze-only", action="store_true")
    ap.add_argument("--summarize-only", action="store_true")
    args = ap.parse_args()
    out = (
        ROOT
        / "outputs/failure_atlas_v1_cycle7"
        / ("validation_smoke" if args.smoke else "validation")
    )
    out.mkdir(parents=True, exist_ok=True)
    plan = design(args.smoke)
    manifest = digest(plan)
    mp = out / "manifest.json"
    if mp.exists():
        saved = json.loads(mp.read_text("utf-8"))
        if saved["digest"] != manifest or digest(saved["design"]) != manifest:
            raise ValueError("frozen inputs changed; refusing checkpoint reuse")
    else:
        saved = {
            "digest": manifest,
            "design": plan,
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "git_status": subprocess.check_output(
                ["git", "status", "--short"], cwd=ROOT, text=True
            ).strip(),
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        mp.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    print(f"manifest {manifest}; {len(plan['jobs'])} cells; {len(plan['seeds'])} seeds", flush=True)
    if args.freeze_only:
        return
    records = load_records(out / "records.jsonl", manifest)
    work = [
        (j, plan["seeds"][i : i + plan["chunk"]])
        for j in plan["jobs"]
        for i in range(0, len(plan["seeds"]), plan["chunk"])
    ]
    expected = {(j["key"], tuple(s)) for j, s in work}
    if set(records) - expected:
        raise ValueError("unexpected completed chunk")
    todo = [(j, s) for j, s in work if (j["key"], tuple(s)) not in records]
    t0 = time.time()
    if not args.summarize_only and todo:
        with (
            ProcessPoolExecutor(max_workers=max(1, min(args.workers, 12))) as pool,
            (out / "records.jsonl").open("a", encoding="utf-8") as handle,
        ):
            futures = [pool.submit(task, w) for w in todo]
            last = 0.0
            for future in as_completed(futures):
                r = future.result()
                r["manifest_digest"] = manifest
                handle.write(json.dumps(r) + "\n")
                handle.flush()
                records[(r["key"], tuple(r["seeds"]))] = r
                now = time.time() - t0
                if now - last >= 20 or len(records) == len(work):
                    print(f"{len(records)}/{len(work)} chunks; elapsed {now:.0f}s", flush=True)
                    last = now
    if set(records) != expected:
        raise ValueError(f"incomplete: {len(records)}/{len(expected)} chunks")
    if digest(design(args.smoke)) != manifest:
        raise ValueError("inputs changed during execution; results withheld")
    result = analyse(plan, records)
    result["manifest_digest"] = manifest
    (out / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary = report(plan, result, manifest, time.time() - t0)
    (out / "summary.md").write_text(summary, encoding="utf-8")
    if not args.smoke:
        (ROOT / "docs/failure_atlas_cycle7_validation_results_v1.md").write_text(
            summary, encoding="utf-8"
        )
    print(json.dumps(result["verdicts"]), flush=True)


if __name__ == "__main__":
    main()
