"""Independently verify MOPE gated-calibration outputs and provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CELLS = {
    "zero_mean": 0.0,
    "positive_gain": 0.12,
    "negative_gain": -0.12,
}
EXPECTED_METHODS = {"official_mope", "fixed_n_hoeffding"}
EXPECTED_MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"
CONTEXT_PROBABILITIES = {"zero_mean": 0.5, "positive_gain": 0.75, "negative_gain": 0.25}
TARGET_ACTION1 = {0: 0.2, 1: 0.8}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cp_interval(successes: int, trials: int) -> tuple[float, float]:
    lower = 0.0 if successes == 0 else float(beta.ppf(0.025, successes, trials - successes + 1))
    upper = (
        1.0 if successes == trials else float(beta.ppf(0.975, successes + 1, trials - successes))
    )
    return lower, upper


def cp_upper(successes: int, trials: int, confidence: float) -> float:
    return (
        1.0
        if successes == trials
        else float(beta.ppf(confidence, successes + 1, trials - successes))
    )


def bootstrap_interval(values: np.ndarray, seed: int, replicates: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, values.size, size=(replicates, values.size))
    means = values[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def close(actual: Any, expected: Any, *, atol: float = 1e-10) -> bool:
    return bool(np.isclose(float(actual), float(expected), rtol=1e-10, atol=atol))


def regenerate_input_fingerprints(
    seed_offset: int, seeds: int, horizon: int
) -> tuple[str, str, dict[str, np.ndarray]]:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required to regenerate the registered input stream")
    device = torch.device("cuda")
    generator = torch.Generator(device=device).manual_seed(seed_offset)
    uniforms = torch.rand((seeds, horizon, 3), generator=generator, device=device).cpu().numpy()
    uniform_hash = hashlib.sha256(uniforms.tobytes(order="C")).hexdigest()
    streams_by_cell = {}
    stream_hash = hashlib.sha256()
    for cell, probability in CONTEXT_PROBABILITIES.items():
        context1 = uniforms[:, :, 0] < probability
        action1 = uniforms[:, :, 1] < 0.5
        target_probability = np.where(context1, TARGET_ACTION1[1], TARGET_ACTION1[0])
        action_probability = np.where(action1, target_probability, 1.0 - target_probability)
        weights = action_probability / 0.5
        rewards = (uniforms[:, :, 2] < np.where(action1, 0.9, 0.1)).astype(np.float64)
        streams = np.stack((weights, rewards), axis=-1)
        streams_by_cell[cell] = streams
        stream_hash.update(cell.encode("utf-8") + b"\0")
        stream_hash.update(streams.tobytes(order="C"))
    return uniform_hash, stream_hash.hexdigest(), streams_by_cell


def verify(output: Path) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    stream_path = output / "stream_metrics.csv"
    summary_path = output / "summary_metrics.csv"
    checksums_path = output / "artifact_checksums.json"
    for path in (manifest_path, stream_path, summary_path, checksums_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    protocol = manifest["protocol"]
    seeds = int(protocol["streams_per_cell"])
    horizon = int(protocol["events_per_stream"])
    if manifest["reference_commit"] != EXPECTED_MOPE_COMMIT:
        raise AssertionError("unexpected pinned MOPE source revision")
    if protocol["alpha"] != 0.05 or protocol["importance_weight_support"] != [0.4, 1.6]:
        raise AssertionError("registered MOPE operating parameters changed")
    if protocol["cells"] != {"zero_mean": 0.5, "positive_gain": 0.75, "negative_gain": 0.25}:
        raise AssertionError("registered cell probabilities changed")
    if protocol["true_delta_by_cell"] != EXPECTED_CELLS:
        raise AssertionError("registered true deltas changed")
    if protocol["generation_device"] != "cuda":
        raise AssertionError("registered input generation was not CUDA-backed")

    source_checks = {}
    for relative, expected in manifest["source_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"source hash mismatch: {relative}")
        source_checks[relative] = expected

    checksum_manifest = json.loads(checksums_path.read_text(encoding="utf-8"))
    for name, record in checksum_manifest["files"].items():
        path = output / name
        if not path.is_file() or path.stat().st_size != int(record["bytes"]):
            raise AssertionError(f"output size mismatch: {name}")
        if sha256(path) != record["sha256"]:
            raise AssertionError(f"output hash mismatch: {name}")

    per_stream = pd.read_csv(stream_path)
    expected_rows = len(EXPECTED_CELLS) * seeds * len(EXPECTED_METHODS)
    if len(per_stream) != expected_rows:
        raise AssertionError(
            f"expected {expected_rows} stream-method rows, found {len(per_stream)}"
        )
    if per_stream.duplicated(["cell", "seed", "method"]).any():
        raise AssertionError("duplicate cell/seed/method keys")
    if set(per_stream["cell"].unique()) != set(EXPECTED_CELLS):
        raise AssertionError("missing or unexpected cells")
    if set(per_stream["method"].unique()) != EXPECTED_METHODS:
        raise AssertionError("missing or unexpected methods")
    expected_seeds = set(range(int(protocol["seed_offset"]), int(protocol["seed_offset"]) + seeds))
    for cell, true_delta in EXPECTED_CELLS.items():
        for method in EXPECTED_METHODS:
            frame = per_stream[(per_stream.cell == cell) & (per_stream.method == method)]
            if len(frame) != seeds or set(frame.seed.astype(int)) != expected_seeds:
                raise AssertionError(f"incomplete stream keys: {cell}/{method}")
            if not np.allclose(frame.true_delta, true_delta, rtol=0, atol=1e-12):
                raise AssertionError(f"wrong true delta: {cell}/{method}")
            if not frame.labels_used.between(1, horizon).all():
                raise AssertionError(f"invalid label counts: {cell}/{method}")
    if per_stream["promoted"].isna().any() or per_stream["empty_confidence_set"].isna().any():
        raise AssertionError("missing Boolean endpoints")
    promoted_values = per_stream.promoted.astype(bool)
    crossing_present = per_stream.crossing_event.notna()
    if not np.array_equal(promoted_values.to_numpy(), crossing_present.to_numpy()):
        raise AssertionError("promotion flags disagree with crossing events")
    for row in per_stream.itertuples(index=False):
        if row.promoted and not 1 <= int(row.crossing_event) <= horizon:
            raise AssertionError("crossing event is outside the registered horizon")
        if row.method == "official_mope" and row.promoted:
            if int(row.labels_used) != int(row.crossing_event):
                raise AssertionError("MOPE label use does not match its first-crossing event")
        elif int(row.labels_used) != horizon:
            raise AssertionError("fixed-N or non-crossing MOPE row must use the full horizon")
    fixed_rows = per_stream[per_stream.method == "fixed_n_hoeffding"]
    if fixed_rows.empty_confidence_set.astype(bool).any():
        raise AssertionError("fixed-horizon comparator cannot have MOPE empty-set events")
    uniform_hash, stream_hash, streams_by_cell = regenerate_input_fingerprints(
        int(protocol["seed_offset"]), seeds, horizon
    )
    if torch.cuda.get_device_name(0) != protocol["generation_gpu"]:
        raise AssertionError("input regeneration GPU differs from the recorded generator")
    radius = 1.2 * np.sqrt(np.log(1.0 / 0.05) / (2.0 * horizon))
    for cell, streams in streams_by_cell.items():
        fixed_promotions = ((streams[:, :, 0] - 1.0) * streams[:, :, 1]).mean(axis=1) - radius > 0
        records = per_stream[
            (per_stream.cell == cell) & (per_stream.method == "fixed_n_hoeffding")
        ].sort_values("seed")
        if not np.array_equal(records.promoted.astype(bool).to_numpy(), fixed_promotions):
            raise AssertionError(f"fixed-N outputs do not match regenerated inputs for {cell}")

    alpha_family = 1.0 - 0.05 / 7.0
    recomputed = []
    for (cell, method), frame in per_stream.groupby(["cell", "method"], sort=True):
        promotions = int(frame.promoted.astype(bool).sum())
        lo, hi = cp_interval(promotions, len(frame))
        empty_count = int(frame.empty_confidence_set.astype(bool).sum())
        row = {
            "cell": cell,
            "method": method,
            "streams": len(frame),
            "promotions": promotions,
            "promotion_rate": promotions / len(frame),
            "promotion_ci95_low": lo,
            "promotion_ci95_high": hi,
            "simultaneous_one_sided_upper_nonpositive_cells": (
                cp_upper(promotions, len(frame), alpha_family)
                if cell in ("zero_mean", "negative_gain")
                else None
            ),
            "empty_confidence_set_rate": empty_count / len(frame),
            "simultaneous_one_sided_upper_empty_set": (
                cp_upper(empty_count, len(frame), alpha_family)
                if method == "official_mope"
                else None
            ),
            "mean_labels_used": float(frame.labels_used.mean()),
            "true_delta": EXPECTED_CELLS[cell],
        }
        recomputed.append(row)

    summary = pd.read_csv(summary_path)
    actual_rows = {
        (str(row.cell), str(row.method)): row._asdict() for row in summary.itertuples(index=False)
    }
    manifest_rows = {(row["cell"], row["method"]): row for row in manifest["results"]["summary"]}
    if set(actual_rows) != set(manifest_rows) or set(actual_rows) != {
        (row["cell"], row["method"]) for row in recomputed
    }:
        raise AssertionError("summary group keys do not match")
    numeric_fields = [
        "streams",
        "promotions",
        "promotion_rate",
        "promotion_ci95_low",
        "promotion_ci95_high",
        "simultaneous_one_sided_upper_nonpositive_cells",
        "empty_confidence_set_rate",
        "simultaneous_one_sided_upper_empty_set",
        "mean_labels_used",
        "true_delta",
    ]
    for calculated in recomputed:
        key = (calculated["cell"], calculated["method"])
        for record in (actual_rows[key], manifest_rows[key]):
            for field in numeric_fields:
                expected = calculated[field]
                actual = record[field]
                if expected is None:
                    if actual is not None and not pd.isna(actual):
                        raise AssertionError(f"expected null for {field} in {key}")
                elif not close(actual, expected):
                    raise AssertionError(f"summary mismatch for {field} in {key}")

    error_bounds = [
        row["simultaneous_one_sided_upper_nonpositive_cells"]
        for row in recomputed
        if row["cell"] in ("zero_mean", "negative_gain")
    ] + [
        row["simultaneous_one_sided_upper_empty_set"]
        for row in recomputed
        if row["method"] == "official_mope"
    ]
    maximum_upper = max(error_bounds)
    if not close(manifest["results"]["max_simultaneous_null_upper_bound"], maximum_upper):
        raise AssertionError("manifest maximum error bound does not recompute")

    positive = per_stream[per_stream.cell == "positive_gain"].pivot(
        index="seed", columns="method", values=["promoted", "labels_used"]
    )
    power_difference = (
        positive["promoted"]["official_mope"].astype(float)
        - positive["promoted"]["fixed_n_hoeffding"].astype(float)
    ).to_numpy()
    label_difference = (
        positive["labels_used"]["official_mope"].astype(float)
        - positive["labels_used"]["fixed_n_hoeffding"].astype(float)
    ).to_numpy()
    bootstrap_seeds = protocol["bootstrap_seeds"]
    replicates = int(protocol["bootstrap_replicates"])
    contrasts = {
        "paired_power_difference_mope_minus_fixed_n": float(power_difference.mean()),
        "paired_power_difference_bootstrap_95": list(
            bootstrap_interval(power_difference, int(bootstrap_seeds[0]), replicates)
        ),
        "paired_label_difference_mope_minus_fixed_n": float(label_difference.mean()),
        "paired_label_difference_bootstrap_95": list(
            bootstrap_interval(label_difference, int(bootstrap_seeds[1]), replicates)
        ),
    }
    recorded = manifest["results"]["paired_contrasts"]["positive_gain"]
    for name, expected in contrasts.items():
        actual = recorded[name]
        if isinstance(expected, list):
            if len(actual) != 2 or not all(
                close(a, b) for a, b in zip(actual, expected, strict=True)
            ):
                raise AssertionError(f"paired interval mismatch: {name}")
        elif not close(actual, expected):
            raise AssertionError(f"paired contrast mismatch: {name}")

    if manifest["outputs"]["row_level_features_or_outcomes_written"] != 0:
        raise AssertionError("unexpected row-level output declaration")
    expected_status = (
        "smoke_not_research"
        if (seeds, horizon) != (1_000, 200)
        else "calibration_and_power_complete"
        if maximum_upper < 0.05
        else "calibration_gate_failed"
    )
    if manifest["status"] != expected_status:
        raise AssertionError("manifest status does not follow the frozen stopping rule")
    result = {
        "status": "verified",
        "streams_per_cell": seeds,
        "events_per_stream": horizon,
        "stream_method_rows_verified": len(per_stream),
        "source_files_verified": len(source_checks),
        "artifact_files_verified": len(checksum_manifest["files"]),
        "verifier_sha256": sha256(Path(__file__)),
        "seeded_uniforms_sha256": uniform_hash,
        "mope_input_streams_sha256": stream_hash,
        "input_regeneration": {
            "torch_version": str(torch.__version__),
            "cuda_version": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
        "max_simultaneous_error_upper_bound": maximum_upper,
        "method_status": manifest["status"],
    }
    (output / "independent_verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="MOPE calibration output directory")
    args = parser.parse_args()
    print(json.dumps(verify(args.output), indent=2))


if __name__ == "__main__":
    main()
