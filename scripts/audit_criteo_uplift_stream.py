"""Stream-audit the Criteo Uplift v2.1 source without storing raw observations.

This is a data-eligibility audit, not a ShiftGuard method evaluation. It checks
the pinned public artifact, schema, aggregate treatment/outcome consistency,
and whether a small feature-only classifier can predict randomized treatment.
No record-level values or identifiers are written to stdout or disk.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import random
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

DATASET = "criteo/criteo-uplift"
REVISION = "2424920019e49d52d72c13ac1143ec5d53af276b"
FILENAME = "criteo-research-uplift-v2.1.csv.gz"
URL = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{FILENAME}"
EXPECTED_BYTES = 311_422_618
EXPECTED_SHA256 = "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc"
EXPECTED_ROWS = 13_979_592
EXPECTED_COLUMNS = [
    *(f"f{i}" for i in range(12)),
    "treatment",
    "conversion",
    "visit",
    "exposure",
]


class HashingRaw(io.RawIOBase):
    """A non-seeking raw stream that hashes compressed response bytes as read."""

    def __init__(self, response: Any) -> None:
        self.response = response
        self.digest = hashlib.sha256()

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        chunk = self.response.read(len(buffer))
        self.digest.update(chunk)
        buffer[: len(chunk)] = chunk
        return len(chunk)


def parse_data_row(row: list[str], line_number: int) -> list[float]:
    if len(row) != len(EXPECTED_COLUMNS):
        raise ValueError(f"unexpected field count at source row {line_number}")
    try:
        values = [float(value) for value in row]
    except ValueError as exc:
        if line_number == 1 and [value.strip() for value in row] == EXPECTED_COLUMNS:
            raise RuntimeError("header row encountered; data header handling is required") from exc
        raise ValueError(f"non-numeric field at source row {line_number}") from exc
    if not np.isfinite(values).all():
        raise ValueError(f"non-finite field at source row {line_number}")
    if any(values[index] not in (0.0, 1.0) for index in range(12, 16)):
        raise ValueError(f"non-binary treatment/outcome field at source row {line_number}")
    return values


def fit_treatment_predictability(
    sampled: list[list[float]], seed: int, requested_device: str
) -> dict[str, Any]:
    if len(sampled) < 20_000:
        raise ValueError("too few sampled rows for the preregistered diagnostic")

    sample = np.asarray(sampled, dtype=np.float32)
    x = sample[:, :12]
    treatment = sample[:, 12].astype(np.int64)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(sample))
    split = int(0.8 * len(order))
    train_index, test_index = order[:split], order[split:]
    mean = x[train_index].mean(axis=0)
    scale = x[train_index].std(axis=0)
    scale[scale < 1e-6] = 1.0
    x_train = torch.as_tensor((x[train_index] - mean) / scale)
    x_test = torch.as_tensor((x[test_index] - mean) / scale)
    y_train = torch.as_tensor(treatment[train_index], dtype=torch.float32)
    y_test = treatment[test_index]

    cuda_available = torch.cuda.is_available()
    if requested_device == "cuda" and not cuda_available:
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(
        "cuda"
        if requested_device == "cuda" or (requested_device == "auto" and cuda_available)
        else "cpu"
    )
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = torch.nn.Sequential(
        torch.nn.Linear(12, 32),
        torch.nn.ReLU(),
        torch.nn.Linear(32, 16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 1),
    ).to(device)
    x_train = x_train.to(device)
    y_train = y_train.to(device)
    x_test = x_test.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_function = torch.nn.BCEWithLogitsLoss()
    batch_size = 4096
    generator = torch.Generator(device="cpu").manual_seed(seed)
    model.train()
    for _ in range(12):
        permutation = torch.randperm(len(y_train), generator=generator)
        for start in range(0, len(permutation), batch_size):
            batch = permutation[start : start + batch_size].to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(x_train[batch]).squeeze(1), y_train[batch])
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        probabilities = torch.sigmoid(model(x_test).squeeze(1)).cpu().numpy()
    auc = float(roc_auc_score(y_test, probabilities))
    return {
        "sample_rows": len(sample),
        "train_rows": len(train_index),
        "test_rows": len(test_index),
        "device": str(device),
        "model": "12-32-16-1 MLP; 12 epochs; feature-only treatment predictability diagnostic",
        "test_auc": auc,
        "interpretation": (
            "descriptive source-eligibility diagnostic only; chance-level performance "
            "does not prove randomization or identify a causal propensity"
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    request = Request(URL, headers={"User-Agent": "ShiftLab-research-data-audit/1.0"})
    start = time.monotonic()
    with urlopen(request, timeout=120) as response:
        advertised_size = response.headers.get("Content-Length")
        if advertised_size and int(advertised_size) != EXPECTED_BYTES:
            raise ValueError("pinned source size differs from the recorded source metadata")
        hashing_raw = HashingRaw(response)
        buffered = io.BufferedReader(hashing_raw, buffer_size=1024 * 1024)
        gzip_file = gzip.GzipFile(fileobj=buffered, mode="rb")
        text_stream = io.TextIOWrapper(gzip_file, encoding="utf-8", newline="")
        reader = csv.reader(text_stream)

        first = next(reader, None)
        if first is None:
            raise ValueError("empty dataset stream")
        has_header = [value.strip() for value in first] == EXPECTED_COLUMNS
        if has_header:
            first = next(reader, None)
            if first is None:
                raise ValueError("dataset contains a header but no records")

        rng = random.Random(args.seed)
        counts: Counter[str] = Counter()
        treatment_counts: Counter[str] = Counter()
        outcome_sums: Counter[str] = Counter()
        exposure_counts: Counter[str] = Counter()
        sample: list[list[float]] = []
        rows = 0

        def consume(row: list[str]) -> None:
            nonlocal rows
            values = parse_data_row(row, rows + 1)
            rows += 1
            treatment = int(values[12])
            conversion, visit, exposure = (int(value) for value in values[13:16])
            counts["rows"] += 1
            treatment_counts[str(treatment)] += 1
            outcome_sums["conversion_treated" if treatment else "conversion_control"] += conversion
            outcome_sums["visit_treated" if treatment else "visit_control"] += visit
            exposure_counts["exposure_treated" if treatment else "exposure_control"] += exposure
            if treatment == 0 and exposure == 1:
                counts["control_with_exposure"] += 1
            if rng.random() < args.sample_fraction:
                sample.append(values)

        consume(first)
        for row in reader:
            consume(row)

        compressed_sha256 = hashing_raw.digest.hexdigest()
        if rows != EXPECTED_ROWS:
            raise ValueError(
                f"source row count mismatch: expected {EXPECTED_ROWS}, observed {rows}"
            )
        if compressed_sha256 != EXPECTED_SHA256:
            raise ValueError("source SHA-256 mismatch against the pinned public artifact")

    model_audit = fit_treatment_predictability(sample, args.seed, args.device)
    treatment_total = sum(treatment_counts.values())
    elapsed = time.monotonic() - start
    return {
        "status": "source_and_structure_verified",
        "audit_type": "streamed_data_eligibility_not_method_evaluation",
        "dataset": DATASET,
        "revision": REVISION,
        "filename": FILENAME,
        "source_url": URL,
        "license": "CC BY-NC-SA 4.0 per the official Criteo dataset page",
        "compressed_bytes": EXPECTED_BYTES,
        "compressed_sha256": compressed_sha256,
        "rows": rows,
        "columns": EXPECTED_COLUMNS,
        "header_present": has_header,
        "treatment_fraction": treatment_counts["1"] / treatment_total,
        "conversion_rate_by_assignment": {
            "treated": outcome_sums["conversion_treated"] / treatment_counts["1"],
            "control": outcome_sums["conversion_control"] / treatment_counts["0"],
        },
        "visit_rate_by_assignment": {
            "treated": outcome_sums["visit_treated"] / treatment_counts["1"],
            "control": outcome_sums["visit_control"] / treatment_counts["0"],
        },
        "exposure_by_assignment": {
            "treated_mean": exposure_counts["exposure_treated"] / treatment_counts["1"],
            "control_mean": exposure_counts["exposure_control"] / treatment_counts["0"],
            "control_with_exposure": counts["control_with_exposure"],
        },
        "treatment_predictability": model_audit,
        "elapsed_seconds": round(elapsed, 3),
        "raw_data_written": False,
        "record_values_written": False,
        "timestamp_or_feedback_delay_available": False,
        "interpretation_limits": [
            "The source aggregates multiple randomized incrementality tests and is non-uniformly subsampled.",
            "The released file has no trial identifier, event time, or label-release time.",
            "The exposure field is post-assignment and must not enter a targeting policy's features.",
            "A feature-only treatment classifier is a diagnostic, not proof of the randomization mechanism.",
            "Any treatment cost is research-imposed unless independently grounded.",
        ],
        "audited_at_utc": datetime.now(UTC).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("data/reports/criteo_uplift_stream_audit.json")
    )
    parser.add_argument("--sample-fraction", type=float, default=0.025)
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()
    if not 0.0 < args.sample_fraction <= 1.0:
        parser.error("--sample-fraction must be in (0, 1]")
    try:
        result = run(args)
    except (OSError, ValueError, RuntimeError, csv.Error, EOFError) as exc:
        print(
            json.dumps({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}),
            file=sys.stderr,
        )
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "dataset",
                    "revision",
                    "rows",
                    "compressed_bytes",
                    "compressed_sha256",
                    "treatment_fraction",
                    "treatment_predictability",
                    "elapsed_seconds",
                    "raw_data_written",
                    "record_values_written",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
