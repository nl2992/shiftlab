"""Small frozen fixed-calendar transfer screen; see its registered protocol."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_atlas_gap_envelope_development_v1 as previous

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_dependence_baselines import DEP_METHODS, build_dep
from shiftlab.dive.switching_explore import paired_ci

PROTOCOL = "docs/failure_atlas_gap_markov_sui_development_protocol_v1.md"
OUT = ROOT / "outputs/failure_atlas_gap_markov_sui_dev"
SEEDS = tuple(range(720000, 720020))
METHODS = ("episode_front", "markov_lr_gate", "gap_envelope_rho08", "gap_markov_sui")
ALT_IDS = (
    "f3_rho0.5_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0.8_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1",
)
NULLS = tuple(
    fa.Family3CellSpec(rho, 0.3, 0.6, "strong", "harmful", 1, bt).null_twin()
    for rho in (0.0, 0.5, 0.8, 0.95)
    for bt in (0.1, 0.25)
)


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def make_method(name: str, cfg):
    if name in DEP_METHODS:
        return build_dep(name, cfg)
    return fa.make_method(name, fa.bernoulli_grid_spec(), cfg)


def run_one(cell, seed: int, method: str, kind: str) -> dict:
    cfg = cell.config(seed)
    result = fa.run_for(cell, fa.make_stream(cell, seed), make_method(method, cfg), cfg)
    return {
        "cell_id": cell.cell_id,
        "seed": seed,
        "method": method,
        "kind": kind,
        "cost_per_round": float(np.sum(result.per_round_cost) / cell.T),
        "queries": int(result.queries),
        "switches": int(result.switches),
        "promoted": int(result.promotions > 0),
        "false_promotion": int((result.fp_regime or 0) > 0),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cells = [previous.cell_from_id(cid) for cid in ALT_IDS]
    sources = [
        PROTOCOL,
        "scripts/run_atlas_gap_markov_sui_development_v1.py",
        "scripts/run_atlas_gap_markov_sui_sparse_development_v1.py",
        "src/shiftlab/dive/atlas_dependence_baselines.py",
        "src/shiftlab/dive/failure_atlas.py",
        "src/shiftlab/dive/atlas_components.py",
        "src/shiftlab/dive/switching_explore.py",
    ]
    manifest = {
        "protocol": PROTOCOL,
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seeds": list(SEEDS),
        "methods": list(METHODS),
        "alternatives": list(ALT_IDS),
        "nulls": [c.cell_id for c in NULLS],
        "source_sha256": {p: sha(p) for p in sources},
    }
    manifest_text = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(manifest_text.encode()).hexdigest()
    manifest_path = OUT / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != {
        **manifest,
        "sha256": digest,
    }:
        raise RuntimeError("existing output belongs to a different frozen manifest")
    manifest_path.write_text(json.dumps({**manifest, "sha256": digest}, indent=2) + "\n")
    records_path = OUT / "records.jsonl"
    rows = {}
    if records_path.exists():
        for line in records_path.read_text().splitlines():
            rec = json.loads(line)
            if rec.pop("manifest_sha256") != digest:
                raise RuntimeError("record manifest mismatch")
            key = (rec["cell_id"], rec["seed"], rec["method"])
            if key in rows:
                raise RuntimeError(f"duplicate record {key}")
            rows[key] = rec
    all_cells = [(c, "alternative") for c in cells] + [(c, "null") for c in NULLS]
    total = len(all_cells) * len(SEEDS) * len(METHODS)
    with records_path.open("a", encoding="utf-8") as f:
        done = len(rows)
        for cell, kind in all_cells:
            for seed in SEEDS:
                for method in METHODS:
                    key = (cell.cell_id, seed, method)
                    if key in rows:
                        continue
                    row = run_one(cell, seed, method, kind)
                    rows[key] = row
                    f.write(json.dumps({**row, "manifest_sha256": digest}, sort_keys=True) + "\n")
                    done += 1
                    if done % 100 == 0 or done == total:
                        f.flush()
                        print(f"completed {done}/{total}", flush=True)

    summary = {"manifest_sha256": digest, "alternatives": {}, "nulls": {}}
    for cell in cells:
        table = {}
        for method in METHODS:
            rr = [rows[(cell.cell_id, s, method)] for s in SEEDS]
            table[method] = {
                k: float(np.mean([r[k] for r in rr]))
                for k in ("cost_per_round", "queries", "switches", "promoted", "false_promotion")
            }
        summary["alternatives"][cell.cell_id] = table
    for cell in NULLS:
        table = {"rho": cell.rho, "budget": cell.budget_frac}
        for method in METHODS:
            rr = [rows[(cell.cell_id, s, method)] for s in SEEDS]
            table[method] = {
                "false_promotions": int(sum(r["false_promotion"] for r in rr)),
                "n": len(rr),
                "rate": float(np.mean([r["false_promotion"] for r in rr])),
            }
        summary["nulls"][cell.cell_id] = table
    contrasts = {}
    for method in METHODS[1:]:
        contrasts[method] = {}
        for baseline in ("episode_front", "markov_lr_gate", "gap_envelope_rho08"):
            diffs = []
            for seed in SEEDS:
                vals = [
                    rows[(cid, seed, method)]["cost_per_round"]
                    - rows[(cid, seed, baseline)]["cost_per_round"]
                    for cid in ALT_IDS
                ]
                diffs.append(float(np.mean(vals)))
            contrasts[method][baseline] = [float(x) for x in paired_ci(np.asarray(diffs))]
    summary["paired_equal_cell_cost_delta_ci"] = contrasts
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary["paired_equal_cell_cost_delta_ci"], indent=2), flush=True)


if __name__ == "__main__":
    main()
