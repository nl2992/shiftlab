"""Frozen development screen for the gap-conditioned Failure Atlas evidence candidate.

Protocol: ``docs/failure_atlas_gap_envelope_development_protocol_v1.md``. This runner uses
development seeds only and writes raw records under ignored ``outputs/``.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_dependence_baselines import DEP_METHODS, build_dep
from shiftlab.dive.switching_explore import paired_ci

PROTOCOL = "docs/failure_atlas_gap_envelope_development_protocol_v1.md"
RESULTS = "docs/failure_atlas_cycle7_validation_results_v1.md"
OUT = ROOT / "outputs/failure_atlas_v1_gap_envelope_dev"
SEEDS = tuple(range(700000, 700040))
METHODS = (
    "episode_front",
    "markov_lr_gate",
    "thinned_hedged_gate",
    "gap_envelope_rho08",
    "gap_envelope_rho95",
)

F1_CELLS = (
    "on0.3_L0.6_strong_harmful_d10_b0.05_s0.1",
    "on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "on0.1_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.1_L0.6_strong_harmful_d10_b0.05_s0.5",
)
F3_CELLS = (
    "f3_rho0.5_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0.5_on0.6_L0.6_strong_harmful_d10_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1",
    "f3_rho0_on0.6_L1_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1",
    "f3_rho0.8_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.05_s0.1",
)
CELL_IDS = (*F1_CELLS, *F3_CELLS)
ADVERSE_CELLS = (
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1",
)
F3_PATTERN = re.compile(
    r"^f3_rho(?P<rho>[\d.]+)_on(?P<on>[\d.]+)_L(?P<L>[\d.]+)_"
    r"(?P<ef>\w+?)_(?P<off>harmful|neutral)_d(?P<d>\d+)_"
    r"b(?P<b>[\d.]+)_s(?P<s>[\d.]+)$"
)


def cell_from_id(cell_id: str):
    if not cell_id.startswith("f3_"):
        for cell in fa.all_cells():
            if cell.cell_id == cell_id:
                return cell
        raise KeyError(cell_id)
    match = F3_PATTERN.match(cell_id)
    if match is None:
        raise ValueError(f"invalid Family-3 cell id: {cell_id}")
    cell = fa.Family3CellSpec(
        float(match["rho"]),
        float(match["on"]),
        float(match["L"]),
        match["ef"],
        match["off"],
        int(match["d"]),
        float(match["b"]),
        s=float(match["s"]),
    )
    if cell.cell_id != cell_id:
        raise ValueError(f"cell id round-trip mismatch: {cell.cell_id} != {cell_id}")
    return cell


def null_cells():
    return [
        fa.Family3CellSpec(rho, 0.3, 0.6, "strong", "harmful", d, bt).null_twin()
        for rho in (0.0, 0.5, 0.8, 0.95)
        for bt in (0.05, 0.1, 0.25, 0.5)
        for d in (1, 10)
    ]


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def make_method(name: str, cfg):
    if name in DEP_METHODS:
        return build_dep(name, cfg)
    return fa.make_method(name, fa.bernoulli_grid_spec(), cfg)


def run_one(cell, seed: int, method_name: str, kind: str) -> dict:
    cfg = cell.config(seed)
    stream = fa.make_stream(cell, seed)
    result = fa.run_for(cell, stream, make_method(method_name, cfg), cfg)
    fp = int((result.fp_regime or 0) > 0)
    return {
        "cell_id": cell.cell_id,
        "kind": kind,
        "seed": int(seed),
        "method": method_name,
        "cost_per_round": float(np.sum(result.per_round_cost) / cell.T),
        "queries": int(result.queries),
        "switches": int(result.switches),
        "promoted": int(result.promotions > 0),
        "correctly_timed_promotion": int(result.promotions > (result.fp_regime or 0)),
        "false_promotion": fp,
    }


def plan():
    cells = [cell_from_id(cid) for cid in CELL_IDS]
    nulls = null_cells()
    sources = (
        PROTOCOL,
        RESULTS,
        "scripts/run_atlas_gap_envelope_development_v1.py",
        "src/shiftlab/dive/atlas_dependence_baselines.py",
        "src/shiftlab/dive/atlas_components.py",
        "src/shiftlab/dive/eprocess.py",
        "src/shiftlab/dive/failure_atlas.py",
        "src/shiftlab/dive/horizon_edetectors.py",
        "src/shiftlab/dive/switching_explore.py",
    )
    return {
        "protocol": PROTOCOL,
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seeds": list(SEEDS),
        "methods": list(METHODS),
        "alternative_cells": [cell.cell_id for cell in cells],
        "null_cells": [cell.cell_id for cell in nulls],
        "source_sha256": {path: sha256(path) for path in sources},
    }


def load_records(manifest_digest: str) -> dict[tuple[str, int, str], dict]:
    path = OUT / "records.jsonl"
    if not path.exists():
        return {}
    rows = {}
    for line in path.read_text("utf-8").splitlines():
        record = json.loads(line)
        if record.pop("manifest_digest", None) != manifest_digest:
            raise ValueError("existing record belongs to a different frozen manifest")
        key = (record["cell_id"], record["seed"], record["method"])
        if key in rows:
            raise ValueError(f"duplicate record: {key}")
        rows[key] = record
    return rows


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(mid - half), float(mid + half)


def ci(values: list[float]) -> tuple[float, float, float]:
    return tuple(float(x) for x in paired_ci(np.asarray(values, dtype=float)))


def summarize(rows: dict[tuple[str, int, str], dict], cells, nulls) -> dict:
    def values(cell_id: str, method: str, field: str) -> list[float]:
        return [rows[(cell_id, seed, method)][field] for seed in SEEDS]

    null_table = {}
    for cell in nulls:
        cell_id = cell.cell_id
        null_table[cell_id] = {"rho": cell.rho, "bt": cell.budget_frac, "d": cell.d}
        for method in METHODS:
            v = values(cell_id, method, "false_promotion")
            k, n = int(sum(v)), len(v)
            null_table[cell_id][method] = {
                "false_promotion": k / n,
                "k": k,
                "n": n,
                "wilson95": list(wilson(k, n)),
            }

    alt_table = {}
    for cell in cells:
        cell_id = cell.cell_id
        alt_table[cell_id] = {"rho": getattr(cell, "rho", 0.0), "methods": {}}
        for method in METHODS:
            costs = values(cell_id, method, "cost_per_round")
            alt_table[cell_id]["methods"][method] = {
                "mean_cost": float(np.mean(costs)),
                "mean_queries": float(np.mean(values(cell_id, method, "queries"))),
                "promotion_rate": float(np.mean(values(cell_id, method, "promoted"))),
                "correct_promotion_rate": float(
                    np.mean(values(cell_id, method, "correctly_timed_promotion"))
                ),
                "false_promotion_rate": float(np.mean(values(cell_id, method, "false_promotion"))),
            }

    contrasts = {}
    for rho_bar, method in ((0.8, "gap_envelope_rho08"), (0.95, "gap_envelope_rho95")):
        eligible = [c for c in cells if c.cell_id in F3_CELLS and getattr(c, "rho", 0.0) <= rho_bar]
        seed_differences = []
        episode_differences = []
        cell_wins = 0
        per_cell = {}
        for cell in eligible:
            delta = np.array(values(cell.cell_id, method, "cost_per_round")) - np.array(
                values(cell.cell_id, "markov_lr_gate", "cost_per_round")
            )
            seed_differences.append(delta)
            episode_differences.append(
                np.array(values(cell.cell_id, method, "cost_per_round"))
                - np.array(values(cell.cell_id, "episode_front", "cost_per_round"))
            )
            cell_wins += int(float(delta.mean()) < 0)
            per_cell[cell.cell_id] = list(ci(delta.tolist()))
        per_seed = np.mean(seed_differences, axis=0)
        episode_per_seed = np.mean(episode_differences, axis=0)
        contrasts[method] = {
            "eligible_cells": [c.cell_id for c in eligible],
            "mean_cost_delta_vs_markov_lr": list(ci(per_seed.tolist())),
            "mean_cost_delta_vs_episode_front": list(ci(episode_per_seed.tolist())),
            "cells_lower_mean_cost": cell_wins,
            "per_cell_ci": per_cell,
        }

    gates = {}
    for rho_bar, method in ((0.8, "gap_envelope_rho08"), (0.95, "gap_envelope_rho95")):
        in_scope = [cell for cell in nulls if cell.rho <= rho_bar]
        rates = [null_table[c.cell_id][method]["false_promotion"] for c in in_scope]
        contrast = contrasts[method]
        adverse_regressions = {}
        for cell_id in ADVERSE_CELLS:
            reference = min(
                ("episode_front", "markov_lr_gate"),
                key=lambda baseline: np.mean(values(cell_id, baseline, "cost_per_round")),
            )
            delta = np.asarray(values(cell_id, method, "cost_per_round")) - np.asarray(
                values(cell_id, reference, "cost_per_round")
            )
            adverse_regressions[cell_id] = {
                "reference": reference,
                "delta_ci": list(ci(delta.tolist())),
                "upper_bound_le_0_01": ci(delta.tolist())[2] <= 0.01,
            }
        gates[method] = {
            "all_in_scope_null_point_rates_le_0_15": bool(all(x <= 0.15 for x in rates)),
            "mean_cost_ci_below_zero_vs_markov_lr": contrast["mean_cost_delta_vs_markov_lr"][2] < 0,
            "mean_cost_ci_below_zero_vs_episode_front": contrast[
                "mean_cost_delta_vs_episode_front"
            ][2]
            < 0,
            "at_least_6_of_11_f3_cells_lower_cost": sum(
                1
                for cid in F3_CELLS
                if getattr(cell_from_id(cid), "rho", 0.0) <= rho_bar
                and alt_table[cid]["methods"][method]["mean_cost"]
                < alt_table[cid]["methods"]["markov_lr_gate"]["mean_cost"]
            )
            >= 6,
            "both_adverse_cost_cells_upper_bound_le_0_01": all(
                row["upper_bound_le_0_01"] for row in adverse_regressions.values()
            ),
            "adverse_cost_cells": adverse_regressions,
            "protocol_advance": False,
        }
        gates[method]["protocol_advance"] = all(
            gates[method][key]
            for key in (
                "all_in_scope_null_point_rates_le_0_15",
                "mean_cost_ci_below_zero_vs_markov_lr",
                "mean_cost_ci_below_zero_vs_episode_front",
                "at_least_6_of_11_f3_cells_lower_cost",
                "both_adverse_cost_cells_upper_bound_le_0_01",
            )
        )

    return {
        "status": "DEVELOPMENT_ONLY",
        "n_seeds": len(SEEDS),
        "alternatives": alt_table,
        "nulls": null_table,
        "contrasts": contrasts,
        "gates": gates,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = plan()
    frozen_bytes = json.dumps(frozen, sort_keys=True, indent=2).encode("utf-8")
    manifest_digest = hashlib.sha256(frozen_bytes).hexdigest()
    manifest_path = OUT / "manifest.json"
    if manifest_path.exists() and manifest_path.read_bytes() != frozen_bytes:
        raise ValueError("frozen manifest mismatch; refusing to resume under changed sources")
    manifest_path.write_bytes(frozen_bytes)
    rows = load_records(manifest_digest)
    cells = [cell_from_id(cid) for cid in CELL_IDS]
    nulls = null_cells()
    jobs = [(cell, "alternative") for cell in cells] + [(cell, "null") for cell in nulls]
    record_path = OUT / "records.jsonl"
    completed = len(rows)
    total = len(jobs) * len(SEEDS) * len(METHODS)
    with record_path.open("a", encoding="utf-8", newline="\n") as f:
        for cell, kind in jobs:
            for seed in SEEDS:
                for method in METHODS:
                    key = (cell.cell_id, seed, method)
                    if key in rows:
                        continue
                    record = run_one(cell, seed, method, kind)
                    f.write(
                        json.dumps(
                            {**record, "manifest_digest": manifest_digest},
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                    rows[key] = record
                    completed += 1
                    if completed % 250 == 0 or completed == total:
                        f.flush()
                        print(f"completed {completed}/{total}", flush=True)

    summary = summarize(rows, cells, nulls)
    (OUT / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Gap-conditioned evidence development screen",
        "",
        "Status: development only; no confirmation or SOTA claim.",
        f"Manifest SHA256: `{manifest_digest}`; seeds `[700000,700040)`.",
        "",
        "## Aggregate alternative cost contrasts",
        "",
        "| method | eligible cells | delta vs Markov LR [95% paired CI] | cells lower cost | advance screen |",
        "|---|---:|---:|---:|---|",
    ]
    for method, row in summary["contrasts"].items():
        mean, lo, hi = row["mean_cost_delta_vs_markov_lr"]
        lines.append(
            f"| {method} | {len(row['eligible_cells'])} | {mean:+.4f} [{lo:+.4f},{hi:+.4f}] | "
            f"{row['cells_lower_mean_cost']} | {summary['gates'][method]['protocol_advance']} |"
        )
    lines += [
        "",
        "## Null promotion by configuration",
        "",
        "Full per-cell frequencies and Wilson intervals are retained in `summary.json`; no rate is an independent validity proof.",
        "",
        "## Cellwise cost and decision metrics",
        "",
        "Full per-seed records are retained in `records.jsonl`; the summary JSON contains cellwise means.",
        "",
        "## Mandatory adverse-cost cells",
        "",
        "Paired cost delta is candidate minus the lower-mean-cost reference among `episode_front` and `markov_lr_gate`; negative favors the candidate.",
        "",
        "| method | cell | selected reference | delta mean [95% paired CI] | upper <= +0.01 |",
        "|---|---|---|---:|---|",
    ]
    for method in ("gap_envelope_rho08", "gap_envelope_rho95"):
        for cell_id, row in summary["gates"][method]["adverse_cost_cells"].items():
            mean, lo, hi = row["delta_ci"]
            lines.append(
                f"| {method} | `{cell_id}` | {row['reference']} | "
                f"{mean:+.4f} [{lo:+.4f},{hi:+.4f}] | {row['upper_bound_le_0_01']} |"
            )
    lines += [
        "",
        "",
        "Advance gates are development stopping rules only. A passing row requires a newly frozen validation protocol.",
    ]
    (ROOT / "docs/failure_atlas_gap_envelope_development_results_v1.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUT / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
