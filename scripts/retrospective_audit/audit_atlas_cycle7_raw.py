"""Independently tally key Atlas cycle-7 results from archived seed records."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from math import sqrt
from pathlib import Path
from statistics import mean, stdev

from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "shift-research-starter/outputs/failure_atlas_v1_cycle7/validation"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/ATLAS_CYCLE7_RAW_AUDIT.json"
HASHES = {
    "manifest.json": "1e5d96c539d9a308f8409272de2c3e3ba9b2ea8c8de8d4722115241171f71978",
    "records.jsonl": "74f2258d78f816e62ae8a9ca5a016e8e6b7fa4223e09952425102be586388c36",
    "results.json": "d62ba5b0438989c60c2e2b67d94f36f882ffe25a743b09915bac12e0e67adc1a",
}


def run() -> dict[str, object]:
    for name, expected in HASHES.items():
        if hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"cycle-7 archived hash mismatch: {name}")
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    result = json.loads((SOURCE / "results.json").read_text(encoding="utf-8"))
    plan = manifest["design"]
    jobs = {job["key"]: job for job in plan["jobs"]}
    seeds = set(plan["seeds"])
    if len(jobs) != 134 or len(seeds) != 200 or min(seeds) != 290000 or max(seeds) != 290199:
        raise AssertionError("cycle-7 design contract")
    costs: dict[str, dict[str, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    null_fp: dict[str, dict[str, dict[int, int]]] = defaultdict(lambda: defaultdict(dict))
    null_cost: dict[str, dict[str, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    run_count = 0
    for line in (SOURCE / "records.jsonl").open(encoding="utf-8"):
        record = json.loads(line)
        key = record["key"]
        job = jobs[key]
        chunk_seeds = record["seeds"]
        if set(record["values"]) != set(job["methods"]):
            raise AssertionError(f"cycle-7 methods mismatch: {key}")
        for method, values in record["values"].items():
            if len(values) != len(chunk_seeds):
                raise AssertionError(f"cycle-7 chunk length mismatch: {key}/{method}")
            for seed, row in zip(chunk_seeds, values, strict=True):
                if seed not in seeds:
                    raise AssertionError("cycle-7 seed outside validation block")
                run_count += 1
                if job["kind"] == "cost":
                    if seed in costs[key][method]:
                        raise AssertionError("duplicate cost seed")
                    costs[key][method][seed] = row["cost"]
                if job["kind"] == "null":
                    if seed in null_fp[key][method]:
                        raise AssertionError("duplicate null seed")
                    null_fp[key][method][seed] = row["fp"]
                    null_cost[key][method][seed] = row["cost"]
    if run_count != 281600 or len(costs) != 102 or len(null_fp) != 32:
        raise AssertionError("cycle-7 archived coverage")

    def interval(values: list[float]) -> list[float]:
        avg = mean(values)
        half = float(t.ppf(0.975, len(values) - 1)) * stdev(values) / sqrt(len(values))
        return [avg, avg - half, avg + half]

    selected = {}
    paired = {}
    for key, cells in costs.items():
        if any(set(values) != seeds for values in cells.values()):
            raise AssertionError("incomplete cost seed panel")
        best = min(plan["baselines"], key=lambda name: mean(cells[name].values()))
        selected[key] = best
        paired[key] = [cells["dss"][seed] - cells[best][seed] for seed in sorted(seeds)]
    primary: dict[str, dict[str, object]] = {}
    for key in plan["primary"]:
        cells = costs[key]
        best = selected[key]
        ci = interval(paired[key])
        delta = ci[0]
        uniform = mean(cells["uniform"][seed] - cells["dss"][seed] for seed in seeds)
        if best != result["primary"][key]["best"] or any(
            abs(left - right) > 1e-12
            for left, right in zip(ci, result["primary"][key]["delta"], strict=True)
        ):
            raise AssertionError(f"primary contrast mismatch: {key}")
        primary[key] = {"best": best, "dss_minus_best": delta, "uniform_minus_dss": uniform}
    aggregate_by_seed = [mean(paired[key][i] for key in plan["primary"]) for i in range(len(seeds))]
    aggregate_ci = interval(aggregate_by_seed)
    aggregate = aggregate_ci[0]
    uniform_aggregate = mean(row["uniform_minus_dss"] for row in primary.values())
    if any(
        abs(left - right) > 1e-12
        for left, right in zip(aggregate_ci, result["A1"]["aggregate"], strict=True)
    ):
        raise AssertionError("cycle-7 A1 aggregate mismatch")
    if abs(uniform_aggregate - result["A4"]["uniform"]["removed_gain"][0]) > 1e-12:
        raise AssertionError("cycle-7 A4 uniform ablation mismatch")
    parent_intervals = {}
    for key, neighbours in plan["neighbours"].items():
        ci = interval(
            [mean(paired[neighbour][i] for neighbour in neighbours) for i in range(len(seeds))]
        )
        if any(
            abs(left - right) > 1e-12
            for left, right in zip(ci, result["A2"]["per_parent"][key], strict=True)
        ):
            raise AssertionError(f"cycle-7 A2 neighbour mismatch: {key}")
        parent_intervals[key] = ci
    null_rates = {}
    a3_relative_failures = {}
    a3_absolute_failures = {}
    for key, methods in null_fp.items():
        if any(
            set(values) != seeds or not set(values.values()) <= {0, 1}
            for values in methods.values()
        ):
            raise AssertionError("cycle-7 null panel mismatch")
        counts = {name: sum(values.values()) for name, values in methods.items()}
        for name, count in counts.items():
            if count != result["A3"]["rows"][key]["methods"][name]["k"]:
                raise AssertionError(f"cycle-7 null count mismatch: {key}/{name}")
        best = min(
            plan["baselines"],
            key=lambda name: (counts[name], mean(null_cost[key][name].values()), name),
        )
        archived = result["A3"]["rows"][key]
        if best != archived["best_safety"]:
            raise AssertionError(f"cycle-7 null baseline mismatch: {key}")
        count = counts["dss"]
        null_rates[key] = {"false_promotions": count, "denominator": 200, "rate": count / 200}
        if archived["required_relative"] and count - counts[best] > 10:
            a3_relative_failures[key] = {"dss": count, "best": best, "best_count": counts[best]}
        if archived["required_absolute"] and count > 30:
            a3_absolute_failures[key] = count
    if len(a3_relative_failures) != 6 or a3_absolute_failures:
        raise AssertionError("cycle-7 A3 registered failure count")
    ablation_intervals = {}
    for name in ("no_delay_switch", "gap1", "uniform"):
        removed = [
            mean(costs[key][name][seed] - costs[key]["dss"][seed] for key in plan["primary"])
            for seed in sorted(seeds)
        ]
        half_gain = [removed[i] + 0.5 * aggregate_by_seed[i] for i in range(len(seeds))]
        removed_ci = interval(removed)
        contrast_ci = interval(half_gain)
        archived = result["A4"][name]
        for actual, stored in (
            (removed_ci, archived["removed_gain"]),
            (contrast_ci, archived["half_gain_contrast"]),
        ):
            if any(abs(left - right) > 1e-12 for left, right in zip(actual, stored, strict=True)):
                raise AssertionError(f"cycle-7 A4 interval mismatch: {name}")
        ablation_intervals[name] = {"removed_gain": removed_ci, "half_gain_contrast": contrast_ci}
    rho08 = [value["rate"] for key, value in null_rates.items() if key.startswith("dep_rho0.8_")]
    if len(rho08) != 8:
        raise AssertionError("cycle-7 rho=.8 grid size")
    return {
        "scope": "Archived aggregate seed outcomes only; no trajectory, source-level filtration, or simulator replay",
        "source_commit": "d099821479f28eec2659e250296db877541cdd89",
        "archived_source_hashes": HASHES,
        "method_runs": run_count,
        "primary_cells": len(primary),
        "primary_dss_minus_best_mean": aggregate,
        "primary_dss_minus_best_ci": aggregate_ci,
        "primary_cells_passing_registered_margin": sum(
            interval(paired[key])[2] < -0.01 for key in plan["primary"]
        ),
        "primary_positive_dss_cost_cells": [
            key for key, row in primary.items() if row["dss_minus_best"] > 0
        ],
        "uniform_minus_dss_mean": uniform_aggregate,
        "a2_parent_intervals_recomputed": len(parent_intervals),
        "a2_failing_parents": {key: ci for key, ci in parent_intervals.items() if ci[2] >= 0.01},
        "a3_relative_failures": a3_relative_failures,
        "a3_absolute_failures": a3_absolute_failures,
        "a4_ablation_intervals": ablation_intervals,
        "rho08_null_rate_range": [min(rho08), max(rho08)],
        "all_null_rates": null_rates,
        "registered_verdicts": result["verdicts"],
        "registered_accepted": result["accepted"],
    }


if __name__ == "__main__":
    outcome = run()
    DEST.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(outcome["method_runs"], outcome["primary_dss_minus_best_mean"])
