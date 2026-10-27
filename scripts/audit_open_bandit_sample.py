"""Aggregate-only schema and support audit for the official OBD small sample."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/raw/open_bandit_small"
DEFAULT_OUTPUT = ROOT / "data/reports/open_bandit_small_source_manifest.json"
SOURCE_COMMIT = "8cbd5fa4558b7ad2ba4781546d6604e4cc3e07c4"
SOURCE_REPO = "https://github.com/st-tech/zr-obp"
EXPECTED_ROWS_PER_LOG = 10_000
BEHAVIORS = ("random", "bts")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _number(value: Any) -> float:
    return float(value) if pd.notna(value) else float("nan")


def _audit_log(path: Path, behavior: str) -> dict[str, Any]:
    frame = pd.read_csv(path)
    required = {
        "timestamp",
        "item_id",
        "position",
        "click",
        "propensity_score",
    }
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise RuntimeError(f"{behavior}: missing required fields {sorted(missing_columns)}")
    if len(frame) != EXPECTED_ROWS_PER_LOG:
        raise RuntimeError(f"{behavior}: expected {EXPECTED_ROWS_PER_LOG} rows, found {len(frame)}")

    timestamps = frame["timestamp"].astype("string")
    parsed = pd.to_datetime(timestamps, errors="coerce", format="mixed")
    if parsed.isna().any():
        raise RuntimeError(f"{behavior}: {int(parsed.isna().sum())} timestamps failed to parse")
    explicit_zone = timestamps.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True).fillna(False)
    times = pd.Series(parsed)
    decreases = int((times.diff().dropna() < pd.Timedelta(0)).sum())
    timestamp_sizes = frame.groupby("timestamp", sort=False).size()
    propensity = pd.to_numeric(frame["propensity_score"], errors="raise")
    positions = pd.to_numeric(frame["position"], errors="raise")
    clicks = pd.to_numeric(frame["click"], errors="raise")

    if (propensity <= 0).any() or (propensity > 1).any():
        raise RuntimeError(f"{behavior}: invalid propensity score in [0, 1]")
    if not set(positions.unique()).issubset({1, 2, 3}):
        raise RuntimeError(f"{behavior}: unexpected slate positions")
    if not set(clicks.unique()).issubset({0, 1}):
        raise RuntimeError(f"{behavior}: click outcome is not binary")

    per_position: dict[str, Any] = {}
    for position, group in frame.groupby("position", sort=True):
        p = pd.to_numeric(group["propensity_score"], errors="raise")
        per_position[str(int(position))] = {
            "rows": len(group),
            "click_rate": float(pd.to_numeric(group["click"]).mean()),
            "propensity_min": float(p.min()),
            "propensity_p01": float(p.quantile(0.01)),
            "propensity_median": float(p.median()),
            "propensity_max": float(p.max()),
            "unique_items": int(group["item_id"].nunique()),
        }

    user_features = [c for c in frame.columns if c.startswith("user_feature_")]
    affinity_features = [c for c in frame.columns if c.startswith("user-item_affinity_")]
    return {
        "behavior_policy": behavior,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
        "rows": len(frame),
        "columns": len(frame.columns),
        "column_names": list(frame.columns),
        "missing_cells": int(frame.isna().sum().sum()),
        "unique_source_row_ids": int(frame["Unnamed: 0"].nunique())
        if "Unnamed: 0" in frame
        else None,
        "timestamp": {
            "minimum_as_published": str(timestamps.min()),
            "maximum_as_published": str(timestamps.max()),
            "parsed_minimum": str(parsed.min()),
            "parsed_maximum": str(parsed.max()),
            "rows_by_parsed_calendar_date": {
                str(date): int(count)
                for date, count in pd.Series(parsed.dt.date).value_counts().sort_index().items()
            },
            "rows_with_explicit_timezone_suffix": int(explicit_zone.sum()),
            "parsed_timezone": str(getattr(parsed.dtype, "tz", None)),
            "rows_out_of_file_order": decreases,
            "unique_timestamp_values": int(timestamp_sizes.size),
            "rows_with_repeated_timestamp": int(timestamp_sizes[timestamp_sizes > 1].sum()),
            "maximum_rows_per_timestamp": int(timestamp_sizes.max()),
        },
        "action_and_reward": {
            "unique_items": int(frame["item_id"].nunique()),
            "positions": sorted(int(x) for x in positions.unique()),
            "click_rate": float(clicks.mean()),
            "by_position": per_position,
        },
        "propensity": {
            "minimum": float(propensity.min()),
            "p01": _number(propensity.quantile(0.01)),
            "median": float(propensity.median()),
            "maximum": float(propensity.max()),
            "nonpositive_count": int((propensity <= 0).sum()),
            "unique_value_count": int(propensity.nunique()),
        },
        "feature_groups": {
            "user_feature_count": len(user_features),
            "affinity_feature_count": len(affinity_features),
            "affinity_availability_verified": False,
            "item_context_file": "item_context.csv",
        },
    }


def audit(data_root: Path, output: Path) -> dict[str, Any]:
    logs = {
        behavior: _audit_log(data_root / behavior / "all" / "all.csv", behavior)
        for behavior in BEHAVIORS
    }
    item_contexts = {
        behavior: {
            "path": (data_root / behavior / "all" / "item_context.csv")
            .relative_to(ROOT)
            .as_posix(),
            "sha256": _sha256(data_root / behavior / "all" / "item_context.csv"),
            "rows": len(pd.read_csv(data_root / behavior / "all" / "item_context.csv")),
        }
        for behavior in BEHAVIORS
    }
    readme = data_root / "README.md"
    if not readme.is_file():
        raise FileNotFoundError(f"upstream README is missing: {readme}")
    random_times = set(
        pd.read_csv(data_root / "random/all/all.csv", usecols=["timestamp"])["timestamp"].astype(
            str
        )
    )
    bts_times = set(
        pd.read_csv(data_root / "bts/all/all.csv", usecols=["timestamp"])["timestamp"].astype(str)
    )
    result = {
        "manifest_schema_version": "1.0.0",
        "dataset": "open_bandit_dataset_small",
        "version": SOURCE_COMMIT,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "sample_schema_and_support_verified_not_research_confirmation",
        "source": {
            "publisher": "ZOZO Research / ZOZO, Inc.",
            "repository": SOURCE_REPO,
            "commit": SOURCE_COMMIT,
            "small_sample_definition": "10,000 records per behavior-policy and campaign pair, per the upstream dataset README",
            "campaign": "all",
            "behaviors": list(BEHAVIORS),
            "full_archive_url": "https://research.zozo.com/data_release/open_bandit_dataset.zip",
            "full_archive_content_length_bytes": 412_931_917,
            "readme_path": readme.relative_to(ROOT).as_posix(),
            "readme_sha256": _sha256(readme),
            "data_license_note": "Upstream describes research use; no explicit SPDX license for the data files was found in the official README or release page. Do not redistribute this local copy without terms review.",
        },
        "logs": logs,
        "item_contexts": item_contexts,
        "cross_log_timestamp_overlap": {
            "exact_shared_timestamp_count": len(random_times & bts_times),
            "random_unique_timestamp_count": len(random_times),
            "bts_unique_timestamp_count": len(bts_times),
            "interpretation": "Timestamp equality alone does not establish shared users or paired potential outcomes.",
        },
        "research_scope": {
            "potential_use": "offline logged-bandit policy-value and candidate-certification development using observed clicks and logged propensities",
            "not_supported_by_this_audit": [
                "adequately powered inference from the 10,000-row samples",
                "prospective or anytime-valid monitoring because click-release times are undocumented",
                "slate-level evaluation without accounting for within-impression dependence and joint slate probabilities",
                "application-wide utility beyond the observed click reward",
                "redistribution rights for the full or small data files",
            ],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = audit(args.data_root, args.output)
    print(
        json.dumps(
            {
                "status": result["status"],
                "output": str(args.output),
                "logs": {
                    behavior: {
                        "rows": log["rows"],
                        "date_min": log["timestamp"]["parsed_minimum"],
                        "date_max": log["timestamp"]["parsed_maximum"],
                        "timezone": log["timestamp"]["parsed_timezone"],
                        "click_rate": log["action_and_reward"]["click_rate"],
                        "propensity_min": log["propensity"]["minimum"],
                        "propensity_max": log["propensity"]["maximum"],
                    }
                    for behavior, log in result["logs"].items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
