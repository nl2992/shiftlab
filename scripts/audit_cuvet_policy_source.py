"""Audit CUVET-Policy source metadata and aggregate-only train-stream statistics.

The script never persists dataset rows. It records public source metadata,
performs a bounded-memory stream of the training CSV for aggregate validation,
and saves aggregate-only provenance under data/reports/. The official test
file is inspected only for metadata.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
import shutil
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from math import log
from pathlib import Path
from typing import Any

REPO_ID = "anonadata/CUVET-policy"
REVISION = "36583ac60379ed83fd375c84d2bf8ce1c73869c1"
TRAIN_OID = "f3700741375c68a267de6ed8eae6b05652766ec8"
TEST_OID = "a170a2a3572e7f7cfe608ee5eab72e684603c44b"
BASE_URL = f"https://huggingface.co/datasets/{REPO_ID}/resolve/{REVISION}"
API_URL = f"https://huggingface.co/api/datasets/{REPO_ID}"
TRAIN_FILE = "cuvet_policy_train.csv"
TEST_FILE = "cuvet_policy_test.csv"
EXPECTED_FIELDS = [
    "",
    "f3",
    "f0",
    "f1",
    "f4",
    "f2",
    "policy",
    "spend",
    "value",
    "is_val",
]
RANGE_BYTES = 1024 * 1024
RANDOM_BLOCKS = 16
SAMPLE_SEED = 2601026


def get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ShiftLab-source-audit/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def head_file(filename: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}/{filename}",
        method="HEAD",
        headers={"User-Agent": "ShiftLab-source-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return {
            "http_status": response.status,
            "final_url_host": urllib.parse.urlparse(response.geturl()).hostname,
            "content_length_bytes": int(response.headers.get("Content-Length", "0")),
            "etag": response.headers.get("ETag"),
            "x_linked_etag": response.headers.get("X-Linked-ETag"),
            "xet_hash": response.headers.get("X-Xet-Hash"),
            "accept_ranges": response.headers.get("Accept-Ranges"),
        }


def inspect_prefix(filename: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}/{filename}",
        headers={
            "Range": f"bytes=0-{RANGE_BYTES - 1}",
            "User-Agent": "ShiftLab-source-audit/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 206:
            raise RuntimeError(f"Expected HTTP 206 for bounded range, got {response.status}")
        content = response.read(RANGE_BYTES)
        content_range = response.headers.get("Content-Range")

    reader = csv.reader(io.TextIOWrapper(io.BytesIO(content), encoding="utf-8", newline=""))
    fields = next(reader)
    complete_records = 0
    malformed_record_count = 0
    treatment_codes: set[str] = set()
    for row in reader:
        if len(row) != len(fields):
            malformed_record_count += 1
            continue
        complete_records += 1
        treatment_codes.add(row[fields.index("policy")])

    return {
        "http_status": 206,
        "content_range": content_range,
        "bytes_read": len(content),
        "fields": fields,
        "complete_records_in_prefix": complete_records,
        "malformed_or_partial_records_in_prefix": malformed_record_count,
        "treatment_codes_seen_in_prefix": sorted(treatment_codes),
        "interpretation": "Prefix-only schema/access check; not a representative sample or propensity estimate.",
        "raw_bytes_written": False,
    }


def inspect_train_assignment_sample(train_size_bytes: int) -> dict[str, Any]:
    """Aggregate a deterministic sample of ranges spread across train only."""
    rng = random.Random(SAMPLE_SEED)
    max_offset = train_size_bytes - RANGE_BYTES
    offsets: set[int] = set()
    while len(offsets) < RANDOM_BLOCKS:
        offsets.add(rng.randrange(1, max_offset))

    counts: Counter[str] = Counter()
    validation_counts: Counter[str] = Counter()
    feature_sums: dict[str, list[float]] = defaultdict(lambda: [0.0] * 5)
    feature_squares: dict[str, list[float]] = defaultdict(lambda: [0.0] * 5)
    parsed = 0
    malformed = 0
    fields = EXPECTED_FIELDS

    for offset in sorted(offsets):
        request = urllib.request.Request(
            f"{BASE_URL}/{TRAIN_FILE}",
            headers={
                "Range": f"bytes={offset}-{offset + RANGE_BYTES - 1}",
                "User-Agent": "ShiftLab-source-audit/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            if response.status != 206:
                raise RuntimeError(f"Expected HTTP 206 at offset {offset}, got {response.status}")
            chunk = response.read(RANGE_BYTES)

        split_lines = chunk.split(b"\n")
        if len(split_lines) < 3:
            malformed += 1
            continue
        reader = csv.reader(
            io.StringIO(b"\n".join(split_lines[1:-1]).decode("utf-8", errors="replace"))
        )
        for row in reader:
            if len(row) != len(fields):
                malformed += 1
                continue
            treatment = row[fields.index("policy")]
            counts[treatment] += 1
            validation_counts[f"{treatment}|{row[fields.index('is_val')]}"] += 1
            values = [float(row[fields.index(f"f{i}")]) for i in range(5)]
            for index, value in enumerate(values):
                feature_sums[treatment][index] += value
                feature_squares[treatment][index] += value * value
            parsed += 1

    reference = "1.0"
    arms: dict[str, Any] = {}
    for treatment, count in sorted(counts.items()):
        arm_result: dict[str, Any] = {
            "sampled_n": count,
            "sampled_fraction": count / parsed if parsed else None,
        }
        if treatment != reference and counts.get(reference, 0) > 1 and count > 1:
            smds: dict[str, float] = {}
            for index in range(5):
                ref_mean = feature_sums[reference][index] / counts[reference]
                arm_mean = feature_sums[treatment][index] / count
                ref_var = max(
                    0.0,
                    feature_squares[reference][index] / counts[reference] - ref_mean**2,
                )
                arm_var = max(
                    0.0,
                    feature_squares[treatment][index] / count - arm_mean**2,
                )
                pooled_sd = ((ref_var + arm_var) / 2) ** 0.5
                smds[f"f{index}"] = (arm_mean - ref_mean) / pooled_sd if pooled_sd else 0.0
            arm_result["feature_smd_vs_reference"] = smds
            arm_result["max_abs_feature_smd_vs_reference"] = max(
                abs(value) for value in smds.values()
            )
        arms[treatment] = arm_result

    return {
        "split": "train only; official test file not read",
        "method": "16 deterministic 1 MiB HTTP byte ranges spread uniformly over the training CSV; each range skips partial boundary lines",
        "seed": SAMPLE_SEED,
        "ranges_read": len(offsets),
        "bytes_read": len(offsets) * RANGE_BYTES,
        "records_parsed": parsed,
        "malformed_or_partial_records_skipped": malformed,
        "treatment_assignment_sample": arms,
        "validation_flag_counts_by_treatment": dict(sorted(validation_counts.items())),
        "interpretation": "Exploratory distributed byte-range sample; approximate assignment/balance diagnostic only, not a full-data propensity estimate or confirmatory result.",
        "raw_bytes_written": False,
    }


def inspect_full_train_stream(expected_size_bytes: int) -> dict[str, Any]:
    """Stream all training rows and retain only aggregate assignment statistics."""
    request = urllib.request.Request(
        f"{BASE_URL}/{TRAIN_FILE}",
        headers={
            "Accept-Encoding": "identity",
            "User-Agent": "ShiftLab-source-audit/1.0",
        },
    )
    counts: Counter[str] = Counter()
    assignment_by_index_band: dict[str, Counter[str]] = defaultdict(Counter)
    validation_counts: Counter[str] = Counter()
    missing_counts: Counter[str] = Counter()
    feature_sums: dict[str, list[float]] = defaultdict(lambda: [0.0] * 5)
    feature_squares: dict[str, list[float]] = defaultdict(lambda: [0.0] * 5)
    outcomes_by_arm_and_validation: dict[str, dict[str, float]] = defaultdict(
        lambda: {"n": 0, "value_sum": 0.0, "spend_sum": 0.0}
    )
    parsed = 0
    malformed = 0
    start = time.monotonic()

    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"Expected HTTP 200 for full training stream, got {response.status}")
        response_size = int(response.headers.get("Content-Length", "0"))
        if response_size != expected_size_bytes:
            raise RuntimeError(
                f"Train content length {response_size} does not match pinned metadata {expected_size_bytes}"
            )
        stream = io.TextIOWrapper(response, encoding="utf-8", newline="")
        reader = csv.reader(stream)
        fields = next(reader)
        if fields != EXPECTED_FIELDS:
            raise RuntimeError(f"Unexpected source schema: {fields!r}")

        policy_index = fields.index("policy")
        spend_index = fields.index("spend")
        value_index = fields.index("value")
        validation_index = fields.index("is_val")
        source_index = fields.index("")
        feature_indices = [fields.index(f"f{i}") for i in range(5)]

        for row in reader:
            if len(row) != len(fields):
                malformed += 1
                continue
            for index, value in enumerate(row):
                if value == "":
                    missing_counts[fields[index] or "source_row_index"] += 1
            treatment = row[policy_index]
            counts[treatment] += 1
            try:
                source_row_id = int(row[source_index])
            except ValueError:
                malformed += 1
                continue
            index_band = f"{(source_row_id // 10_000_000) * 10_000_000:09d}s"
            assignment_by_index_band[index_band][treatment] += 1
            validation_counts[f"{treatment}|{row[validation_index]}"] += 1
            try:
                features = [float(row[index]) for index in feature_indices]
                value_outcome = float(row[value_index])
                spend_outcome = float(row[spend_index])
                validation_flag = int(row[validation_index])
            except ValueError:
                malformed += 1
                continue
            if validation_flag not in (0, 1):
                malformed += 1
                continue
            for index, value in enumerate(features):
                feature_sums[treatment][index] += value
                feature_squares[treatment][index] += value * value
            outcome_key = f"{treatment}|is_val={validation_flag}"
            outcome_sums = outcomes_by_arm_and_validation[outcome_key]
            outcome_sums["n"] += 1
            outcome_sums["value_sum"] += value_outcome
            outcome_sums["spend_sum"] += spend_outcome
            parsed += 1
            if parsed % 5_000_000 == 0:
                elapsed = time.monotonic() - start
                print(
                    json.dumps(
                        {
                            "progress": "train_only_full_stream",
                            "parsed_rows": parsed,
                            "elapsed_seconds": round(elapsed, 1),
                        }
                    ),
                    file=sys.stdout,
                    flush=True,
                )

    total = sum(counts.values())
    reference = "1.0"
    arms: dict[str, Any] = {}
    for treatment, count in sorted(counts.items()):
        arm_result: dict[str, Any] = {
            "n": count,
            "empirical_train_fraction": count / total if total else None,
        }
        if treatment != reference and counts.get(reference, 0) > 1 and count > 1:
            smds: dict[str, float] = {}
            for index in range(5):
                ref_mean = feature_sums[reference][index] / counts[reference]
                arm_mean = feature_sums[treatment][index] / count
                ref_var = max(
                    0.0,
                    feature_squares[reference][index] / counts[reference] - ref_mean**2,
                )
                arm_var = max(
                    0.0,
                    feature_squares[treatment][index] / count - arm_mean**2,
                )
                pooled_sd = ((ref_var + arm_var) / 2) ** 0.5
                smds[f"f{index}"] = (arm_mean - ref_mean) / pooled_sd if pooled_sd else 0.0
            arm_result["feature_smd_vs_reference"] = smds
            arm_result["max_abs_feature_smd_vs_reference"] = max(
                abs(value) for value in smds.values()
            )
        arms[treatment] = arm_result

    index_band_shares: dict[str, Any] = {}
    for index_band, band_counts in sorted(assignment_by_index_band.items()):
        band_total = sum(band_counts.values())
        index_band_shares[index_band] = {
            "n": band_total,
            "empirical_arm_shares": {
                treatment: band_counts[treatment] / band_total for treatment in sorted(counts)
            },
        }

    outcome_means: dict[str, Any] = {}
    for key, aggregate in sorted(outcomes_by_arm_and_validation.items()):
        n = int(aggregate["n"])
        outcome_means[key] = {
            "n": n,
            "mean_value": aggregate["value_sum"] / n,
            "mean_spend": aggregate["spend_sum"] / n,
        }

    def response_elasticity(validation_flag: int, metric: str) -> float | None:
        means: list[float] = []
        for treatment in ("0.8", "0.9", "1.0", "1.1", "1.2"):
            mean = outcome_means[f"{treatment}|is_val={validation_flag}"][f"mean_{metric}"]
            if mean <= 0:
                return None
            means.append(mean)
        log_alpha = [log(float(treatment)) for treatment in ("0.8", "0.9", "1.0", "1.1", "1.2")]
        log_mean = [log(value) for value in means]
        center_x = sum(log_alpha) / len(log_alpha)
        center_y = sum(log_mean) / len(log_mean)
        numerator = sum(
            (x - center_x) * (y - center_y) for x, y in zip(log_alpha, log_mean, strict=True)
        )
        denominator = sum((x - center_x) ** 2 for x in log_alpha)
        return numerator / denominator

    root_response_fits = {}
    for validation_flag in (0, 1):
        gamma = response_elasticity(validation_flag, "value")
        eta = response_elasticity(validation_flag, "spend")
        root_response_fits[f"is_val={validation_flag}"] = {
            "value_elasticity_gamma": gamma,
            "spend_elasticity_eta": eta,
            "source_power_law_ordering_holds": (
                gamma is not None and eta is not None and gamma > 0 and eta > gamma
            ),
        }

    return {
        "split": "full train only; official test file not read",
        "method": "single HTTP stream; aggregate counts, missingness, feature moments, and treatment-by-is_val outcome sums only; no row persistence",
        "content_length_bytes": response_size,
        "records_parsed": parsed,
        "malformed_rows": malformed,
        "missing_cells_by_field": dict(sorted(missing_counts.items())),
        "treatment_assignment": arms,
        "treatment_shares_by_source_row_id_band_10m": index_band_shares,
        "validation_flag_counts_by_treatment": dict(sorted(validation_counts.items())),
        "mean_outcomes_by_treatment_and_is_val": outcome_means,
        "root_power_law_response_fit": root_response_fits,
        "elapsed_seconds": round(time.monotonic() - start, 1),
        "interpretation": "Full training-split descriptive audit; arm shares by source row-ID band diagnose assignment-rate heterogeneity but do not establish design probabilities or randomization. Balance in feature means is not proof of randomization.",
        "raw_bytes_written": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-train-stream",
        action="store_true",
        help="Stream all of train.csv once; store only aggregate audit metadata.",
    )
    args = parser.parse_args()

    metadata = get_json(API_URL)
    tree = get_json(f"{API_URL}/tree/{REVISION}?recursive=true&expand=true")
    files = {item["path"]: item for item in tree if item.get("type") == "file"}
    if files[TRAIN_FILE].get("oid") != TRAIN_OID or files[TEST_FILE].get("oid") != TEST_OID:
        raise RuntimeError(
            "Pinned CUVET source object IDs do not match the audited revision: "
            f"train={files[TRAIN_FILE].get('oid')}, test={files[TEST_FILE].get('oid')}"
        )
    train_head = head_file(TRAIN_FILE)
    test_head = head_file(TEST_FILE)
    train_full_stream = None
    if args.full_train_stream:
        train_full_stream = inspect_full_train_stream(int(files[TRAIN_FILE].get("size", 0)))
        prefix = None
        assignment_sample = None
    else:
        prefix = inspect_prefix(TRAIN_FILE)
        if prefix["fields"] != EXPECTED_FIELDS:
            raise RuntimeError(f"Unexpected source schema: {prefix['fields']!r}")
        assignment_sample = inspect_train_assignment_sample(int(files[TRAIN_FILE].get("size", 0)))

    report = {
        "audit": "cuvet_policy_source_access",
        "audit_timestamp_utc": datetime.now(UTC).isoformat(),
        "dataset_id": REPO_ID,
        "dataset_revision": REVISION,
        "license_reported_by_source": metadata.get("cardData", {}).get("license"),
        "source_files": {
            TRAIN_FILE: {
                "api_size_bytes": files[TRAIN_FILE].get("size"),
                "api_oid": files[TRAIN_FILE].get("oid"),
                **train_head,
            },
            TEST_FILE: {
                "api_size_bytes": files[TEST_FILE].get("size"),
                "api_oid": files[TEST_FILE].get("oid"),
                **test_head,
            },
        },
        "bounded_remote_read": prefix,
        "train_assignment_sample": assignment_sample,
        "train_full_stream": train_full_stream,
        "local_dataset_downloaded": False,
        "local_rows_persisted": False,
        "local_disk_free_bytes_after_audit": shutil.disk_usage(Path.cwd()).free,
    }
    output = Path("data/reports/cuvet_policy_source_audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
