"""Amendment 9 development pilot; never consumes cycle-7 validation seeds."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(key, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from run_atlas_cycle6_validity_v1 import build_null_cell, config_list
from run_atlas_dss_tuning_v1 import build_cell, f3_failure_ids
from scipy.stats import binomtest

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_dependence_baselines import build_dep
from shiftlab.dive.switching_explore import paired_ci

METHODS = ("episode_front", "markov_lr_gate", "thinned_hedged_gate", "dss_g4", "uniform")
SEEDS = tuple(range(170000, 170020))


def task(item):
    kind, key, params = item
    cell = build_null_cell("dep", params, 1000) if kind == "null" else build_cell(key)
    values = {m: [] for m in METHODS}
    for seed in SEEDS:
        cfg = cell.config(seed)
        stream = fa.make_stream(cell, seed)
        for name in METHODS:
            if name in ("markov_lr_gate", "thinned_hedged_gate"):
                method = build_dep(name, cfg)
            elif name in ("dss_g4", "uniform"):
                spec = comp.dss_spec(4, True)
                if name == "uniform":
                    spec = comp.dss_ablations(spec)["uniform"]
                method = comp.build_candidate(spec)
            else:
                method = fa.make_method(name, fa.bernoulli_grid_spec(), cfg)
            result = fa.run_for(cell, stream, method, cfg)
            values[name].append(
                {
                    "fp": int((result.fp_regime or 0) > 0),
                    "cost": float(result.cost) / cell.T,
                    "promoted": int(result.promotions > 0),
                    "correct_promotion": int(result.promotions > (result.fp_regime or 0)),
                }
            )
    return {"kind": kind, "id": key, "params": params, "seeds": SEEDS, "values": values}


def main():
    out = ROOT / "outputs/failure_atlas_v1_cycle7/dependence_pilot"
    out.mkdir(parents=True, exist_ok=True)
    items = [("null", p["id"], p) for p in config_list(1000) if p["kind"] == "dep"]
    items += [("power", cid, {}) for cid in f3_failure_ids()]
    path = out / "records.jsonl"
    done = (
        {r["id"]: r for r in map(json.loads, path.read_text("utf-8").splitlines())}
        if path.exists()
        else {}
    )
    with ProcessPoolExecutor(max_workers=4) as pool, path.open("a", encoding="utf-8") as handle:
        for record in pool.map(
            task,
            [
                i
                for i in items
                if i[1] not in done
                or (i[0] == "power" and "promoted" not in done[i[1]]["values"][METHODS[0]][0])
            ],
        ):
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            done[record["id"]] = record
            print(f"{len(done)}/{len(items)} {record['id']}", flush=True)
    lines = [
        "# Dependence pilot (development only; n=20 per cell)",
        "",
        "Seeds [170000,170020); T=1000. No acceptance verdict. Alternative rows report cost and false promotion outside favourable regimes; they do not estimate detection power.",
        "",
        "| kind / cell | " + " | ".join(METHODS) + " |",
        "|---|" + "---|" * len(METHODS),
    ]
    for kind, key, _ in items:
        r = done[key]
        vals = []
        for m in METHODS:
            fp = np.mean([v["fp"] for v in r["values"][m]])
            cost = np.mean([v["cost"] for v in r["values"][m]])
            vals.append(f"FP={fp:.3f}; cost={cost:.4f}")
        lines.append(f"| {kind} / {key} | " + " | ".join(vals) + " |")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = [
        "# Failure Atlas dependence pilot: complete development tables",
        "",
        "2026-11-01. Amendment 9. T=1000; 20 paired seeds [170000,170020) per cell.",
        "32 null cells and 11 alternative cells; five methods, 4300 method runs.",
        "This pilot is not A1–A4 validation. Comparator coverage is deliberately limited.",
        "Alternative promotion frequencies are development diagnostics, not confirmatory power estimates. Replayed alternatives use the same seeds and add no independent evidence.",
        "",
        "## Null false-promotion frequencies",
        "",
        "Exact binomial 95% intervals are per cell, unadjusted. Even 0/20 does not establish alpha=.1.",
        "",
        "| cell | " + " | ".join(METHODS) + " |",
        "|---|" + "---|" * len(METHODS),
    ]
    for kind, key, _ in items:
        if kind != "null":
            continue
        vals = []
        for name in METHODS:
            k = sum(v["fp"] for v in done[key]["values"][name])
            ci = binomtest(k, len(SEEDS)).proportion_ci()
            vals.append(f"{k}/20 [{ci.low:.3f},{ci.high:.3f}]")
        report.append(f"| {key} | " + " | ".join(vals) + " |")
    report += [
        "",
        "## Alternative costs and paired differences",
        "",
        "Lower cost is better. Best pilot baseline is the minimum mean among episode_front, Markov LR and gap-10 betting, selected on these same seeds. This is not the full SOTA registry.",
        "Paired t intervals are descriptive and unadjusted; cells share seeds. No across-cell significance claim is made.",
        "",
        "| cell | "
        + " | ".join(METHODS)
        + " | best baseline | DSS minus best [95% CI] | DSS minus uniform [95% CI] |",
        "|---|" + "---|" * (len(METHODS) + 3),
    ]
    for kind, key, _ in items:
        if kind == "null":
            continue
        costs = {m: np.array([v["cost"] for v in done[key]["values"][m]]) for m in METHODS}
        best = min(METHODS[:3], key=lambda m: costs[m].mean())
        deltas = []
        for ref in (best, "uniform"):
            mean, low, high = paired_ci(costs["dss_g4"] - costs[ref])
            deltas.append(f"{mean:+.4f} [{low:+.4f},{high:+.4f}]")
        report.append(
            f"| {key} | "
            + " | ".join(f"{costs[m].mean():.4f}" for m in METHODS)
            + f" | {best} | "
            + " | ".join(deltas)
            + " |"
        )
    report += [
        "",
        "## Promotion diagnostics on alternative streams",
        "",
        "Each entry is any promotion / at least one correctly timed promotion / any false promotion, out of 20 streams. Correctly timed means the evaluator's favourable regime, not a causal real-data label.",
        "",
        "| cell | " + " | ".join(METHODS) + " |",
        "|---|" + "---|" * len(METHODS),
    ]
    for kind, key, _ in items:
        if kind == "null":
            continue
        vals = []
        for name in METHODS:
            values = done[key]["values"][name]
            if "promoted" not in values[0]:
                vals.append("not recorded; rerun to add metrics")
            else:
                vals.append(
                    " / ".join(
                        str(sum(v[field] for v in values))
                        for field in ("promoted", "correct_promotion", "fp")
                    )
                )
        report.append(f"| {key} | " + " | ".join(vals) + " |")
    sources = [
        Path(__file__),
        ROOT / "src/shiftlab/dive/atlas_dependence_baselines.py",
        ROOT / "src/shiftlab/dive/atlas_components.py",
        path,
    ]
    provenance = {
        "status": "post-run analysis snapshot; decision rules unchanged; promotion bookkeeping added and alternatives replayed on identical seeds; summary/import formatting revised during run",
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seeds": list(SEEDS),
        "sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
        },
    }
    (out / "analysis_manifest.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    report += [
        "",
        "## Provenance",
        "",
        "Starting Git HEAD: `"
        + provenance["git_head"]
        + "`. Working tree contains this uncommitted pilot and documentation changes.",
        "The manifest is a post-run analysis snapshot, not proof of a clean committed execution.",
        "Reproduce from repository root: `.venv/Scripts/python scripts/run_atlas_dependence_pilot_v1.py`.",
        "Existing records are reused; archive the output directory first for a fresh rerun.",
        "Raw records SHA256: `" + provenance["sha256"][str(path.relative_to(ROOT))] + "`.",
    ]
    (ROOT / "docs/failure_atlas_dependence_pilot_2026_11_01.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
