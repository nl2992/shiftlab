"""Stream the official OBD full archive into a bounded, checksum-backed audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "data/raw/open_bandit_dataset_full.zip"
DEFAULT_OUTPUT = ROOT / "data/interim/open_bandit_full_all_v4"
DEFAULT_MANIFEST = ROOT / "data/reports/open_bandit_full_acquisition_manifest.json"
EXPECTED_RANDOM_ALL_ROWS = 1_374_327
# Verified against the number of rows streamed from archive version 1.0.
EXPECTED_BTS_ALL_ROWS = 12_357_200
CHUNK_ROWS = 50_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _table_schema(frame: pd.DataFrame) -> pa.Schema:
    return pa.Table.from_pandas(frame.iloc[:0], preserve_index=False).schema


def _read_random_log(archive: zipfile.ZipFile, output: Path) -> tuple[dict[str, Any], list[str]]:
    member = "open_bandit_dataset/random/all/all.csv"
    member_info = archive.getinfo(member)
    output_path = output / "random_all.parquet"
    writer: pq.ParquetWriter | None = None
    rows = 0
    missing_cells = 0
    out_of_order = 0
    previous_time: pd.Timestamp | None = None
    date_accumulator: dict[str, dict[str, int]] = {}
    position_accumulator: dict[str, dict[str, Any]] = {}
    propensity_min = float("inf")
    propensity_max = float("-inf")
    propensity_values: set[float] = set()
    item_ids: set[int] = set()
    expected_columns: list[str] | None = None
    with archive.open(member) as source:
        reader = pd.read_csv(source, chunksize=CHUNK_ROWS)
        try:
            for chunk in reader:
                if expected_columns is None:
                    expected_columns = list(chunk.columns)
                    required = {
                        "timestamp",
                        "item_id",
                        "position",
                        "click",
                        "propensity_score",
                    }
                    absent = required - set(expected_columns)
                    if absent:
                        raise RuntimeError(f"Random log missing required fields: {sorted(absent)}")
                elif list(chunk.columns) != expected_columns:
                    raise RuntimeError("Random log columns changed between chunks")

                # The published archive mixes ISO ``T`` and space separators
                # in otherwise valid UTC timestamps; infer each value's format.
                times = pd.to_datetime(
                    chunk["timestamp"], errors="coerce", utc=True, format="mixed"
                )
                if times.isna().any():
                    raise RuntimeError("Random log contains unparseable timestamps")
                if previous_time is not None and times.iloc[0] < previous_time:
                    out_of_order += 1
                out_of_order += int((times.diff().dropna() < pd.Timedelta(0)).sum())
                previous_time = times.iloc[-1]
                chunk["timestamp"] = times
                if writer is None:
                    writer = pq.ParquetWriter(
                        output_path,
                        _table_schema(chunk),
                        compression="zstd",
                        use_dictionary=True,
                    )
                missing_cells += int(chunk.isna().sum().sum())
                rows += len(chunk)
                propensity = pd.to_numeric(chunk["propensity_score"], errors="raise")
                if (propensity <= 0).any() or (propensity > 1).any():
                    raise RuntimeError("Random log propensity is outside (0, 1]")
                propensity_min = min(propensity_min, float(propensity.min()))
                propensity_max = max(propensity_max, float(propensity.max()))
                propensity_values.update(float(v) for v in propensity.unique())
                item_ids.update(int(v) for v in chunk["item_id"].unique())

                dates = times.dt.strftime("%Y-%m-%d")
                audit_frame = pd.DataFrame(
                    {
                        "date": dates,
                        "position": pd.to_numeric(chunk["position"], errors="raise"),
                        "click": pd.to_numeric(chunk["click"], errors="raise"),
                        "propensity_score": propensity,
                        "item_id": pd.to_numeric(chunk["item_id"], errors="raise"),
                    }
                )
                daily = audit_frame.groupby("date", sort=False).agg(
                    rows=("click", "size"), clicks=("click", "sum")
                )
                for date, values in daily.iterrows():
                    slot = date_accumulator.setdefault(str(date), {"rows": 0, "clicks": 0})
                    slot["rows"] += int(values["rows"])
                    slot["clicks"] += int(values["clicks"])
                positions = audit_frame.groupby("position", sort=False).agg(
                    rows=("click", "size"),
                    clicks=("click", "sum"),
                    propensity_min=("propensity_score", "min"),
                    propensity_max=("propensity_score", "max"),
                    unique_items=("item_id", "nunique"),
                )
                for position, values in positions.iterrows():
                    slot = position_accumulator.setdefault(
                        str(int(position)),
                        {
                            "rows": 0,
                            "clicks": 0,
                            "propensity_min": float("inf"),
                            "propensity_max": float("-inf"),
                            "items": set(),
                        },
                    )
                    slot["rows"] += int(values["rows"])
                    slot["clicks"] += int(values["clicks"])
                    slot["propensity_min"] = min(
                        slot["propensity_min"], float(values["propensity_min"])
                    )
                    slot["propensity_max"] = max(
                        slot["propensity_max"], float(values["propensity_max"])
                    )
                    slot["items"].update(
                        int(v)
                        for v in audit_frame.loc[
                            audit_frame.position.eq(position), "item_id"
                        ].unique()
                    )

                table = pa.Table.from_pandas(chunk, preserve_index=False)
                writer.write_table(table)
        finally:
            reader.close()
            if writer is not None:
                writer.close()

    if rows != EXPECTED_RANDOM_ALL_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_RANDOM_ALL_ROWS} Random/all rows, found {rows}")
    if writer is None or expected_columns is None:
        raise RuntimeError("Random/all log is empty")
    if missing_cells:
        raise RuntimeError(f"Random/all log has {missing_cells} missing cells")
    if propensity_min != propensity_max or abs(propensity_min - 1.0 / 80.0) > 1e-12:
        raise RuntimeError(
            "Random/all propensities do not match the documented uniform 1/80 support"
        )

    daily_summary = {
        day: {**values, "click_rate": values["clicks"] / values["rows"]}
        for day, values in sorted(date_accumulator.items())
    }
    position_summary = {
        position: {
            "rows": values["rows"],
            "clicks": values["clicks"],
            "click_rate": values["clicks"] / values["rows"],
            "propensity_min": values["propensity_min"],
            "propensity_max": values["propensity_max"],
            "unique_items": len(values["items"]),
        }
        for position, values in sorted(position_accumulator.items())
    }
    metrics = {
        "source_member": member,
        "source_member_uncompressed_bytes": member_info.file_size,
        "source_member_compressed_bytes": member_info.compress_size,
        "rows": rows,
        "columns": len(expected_columns),
        "column_names": expected_columns,
        "missing_cells": missing_cells,
        "rows_out_of_file_order": out_of_order,
        "timestamp_min_utc": min(daily_summary),
        "timestamp_max_utc": max(daily_summary),
        "unique_items": len(item_ids),
        "positions": sorted(int(p) for p in position_summary),
        "propensity_min": propensity_min,
        "propensity_max": propensity_max,
        "propensity_unique_values": len(propensity_values),
        "click_rate": sum(v["clicks"] for v in daily_summary.values()) / rows,
        "daily": daily_summary,
        "by_position": position_summary,
        "parquet_path": output_path.relative_to(ROOT).as_posix(),
        "parquet_sha256": _sha256(output_path),
        "parquet_bytes": output_path.stat().st_size,
    }
    return metrics, expected_columns


def _read_bts_reference(archive: zipfile.ZipFile) -> dict[str, Any]:
    member = "open_bandit_dataset/bts/all/all.csv"
    member_info = archive.getinfo(member)
    daily: dict[str, dict[str, int]] = {}
    by_position: dict[str, dict[str, int]] = {}
    rows = 0
    missing = 0
    pmin = float("inf")
    pmax = float("-inf")
    with archive.open(member) as source:
        reader = pd.read_csv(
            source,
            usecols=["timestamp", "position", "click", "propensity_score"],
            chunksize=250_000,
        )
        try:
            for chunk in reader:
                times = pd.to_datetime(
                    chunk["timestamp"], errors="coerce", utc=True, format="mixed"
                )
                if times.isna().any():
                    raise RuntimeError("BTS/all log contains unparseable timestamps")
                propensity = pd.to_numeric(chunk["propensity_score"], errors="raise")
                if (propensity <= 0).any() or (propensity > 1).any():
                    raise RuntimeError("BTS/all propensity is outside (0, 1]")
                pmin = min(pmin, float(propensity.min()))
                pmax = max(pmax, float(propensity.max()))
                missing += int(chunk.isna().sum().sum())
                rows += len(chunk)
                audit = pd.DataFrame(
                    {
                        "date": times.dt.strftime("%Y-%m-%d"),
                        "position": pd.to_numeric(chunk["position"], errors="raise"),
                        "click": pd.to_numeric(chunk["click"], errors="raise"),
                    }
                )
                day = audit.groupby("date", sort=False).agg(
                    rows=("click", "size"), clicks=("click", "sum")
                )
                for date, values in day.iterrows():
                    slot = daily.setdefault(str(date), {"rows": 0, "clicks": 0})
                    slot["rows"] += int(values["rows"])
                    slot["clicks"] += int(values["clicks"])
                position = audit.groupby("position", sort=False).agg(
                    rows=("click", "size"), clicks=("click", "sum")
                )
                for key, values in position.iterrows():
                    slot = by_position.setdefault(str(int(key)), {"rows": 0, "clicks": 0})
                    slot["rows"] += int(values["rows"])
                    slot["clicks"] += int(values["clicks"])
        finally:
            reader.close()
    if rows != EXPECTED_BTS_ALL_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_BTS_ALL_ROWS} BTS/all rows, found {rows}")
    if missing:
        raise RuntimeError(f"BTS/all selected columns contain {missing} missing cells")
    return {
        "source_member": member,
        "source_member_uncompressed_bytes": member_info.file_size,
        "source_member_compressed_bytes": member_info.compress_size,
        "rows": rows,
        "propensity_min": pmin,
        "propensity_max": pmax,
        "click_rate": sum(v["clicks"] for v in daily.values()) / rows,
        "daily": {
            day: {**values, "click_rate": values["clicks"] / values["rows"]}
            for day, values in sorted(daily.items())
        },
        "by_position": {
            position: {**values, "click_rate": values["clicks"] / values["rows"]}
            for position, values in sorted(by_position.items())
        },
    }


def prepare(archive_path: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    if not archive_path.is_file():
        raise FileNotFoundError(f"Full OBD archive is missing: {archive_path}")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing OBD output: {output}")
    output.mkdir(parents=True)
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        required = {
            "open_bandit_dataset/README",
            "open_bandit_dataset/VERSION",
            "open_bandit_dataset/random/all/all.csv",
            "open_bandit_dataset/random/all/item_context.csv",
            "open_bandit_dataset/bts/all/all.csv",
        }
        if not required.issubset(names):
            raise RuntimeError(f"Full OBD archive is missing members: {sorted(required - names)}")
        version = archive.read("open_bandit_dataset/VERSION").decode("utf-8").strip()
        readme = archive.read("open_bandit_dataset/README").decode("utf-8")
        if "CC BY 4.0" not in readme:
            raise RuntimeError(
                "Full OBD README did not confirm the expected CC BY 4.0 data license"
            )

        random_metrics, columns = _read_random_log(archive, output)
        item_member = "open_bandit_dataset/random/all/item_context.csv"
        with archive.open(item_member) as item_handle:
            item_context = pd.read_csv(item_handle)
        if item_context["item_id"].nunique() != 80:
            raise RuntimeError("Expected 80 unique items in the full all-campaign item context")
        item_path = output / "item_context.parquet"
        item_context.to_parquet(item_path, index=False, compression="zstd")

        bts_metrics = _read_bts_reference(archive)
        all_archive_members = [
            {
                "name": entry.filename,
                "uncompressed_bytes": entry.file_size,
                "compressed_bytes": entry.compress_size,
            }
            for entry in archive.infolist()
            if not entry.is_dir()
        ]

    result = {
        "manifest_schema_version": "1.0.0",
        "dataset": "open_bandit_dataset_full_all_campaign",
        "version": version,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "full_random_logger_processed_bts_reference_streamed_not_confirmation",
        "source": {
            "publisher": "ZOZO Research / ZOZO, Inc.",
            "url": "https://research.zozo.com/data_release/open_bandit_dataset.zip",
            "citation": "Saito et al. (2020), Open Bandit Dataset and Pipeline, arXiv:2008.07146",
            "license": "CC BY 4.0, as stated in the full archive README",
            "archive_path": archive_path.relative_to(ROOT).as_posix(),
            "archive_bytes": archive_path.stat().st_size,
            "archive_sha256": _sha256(archive_path),
            "archive_readme_sha256": hashlib.sha256(readme.encode("utf-8")).hexdigest(),
            "archive_version": version,
            "full_archive_uncompressed_bytes": sum(
                item["uncompressed_bytes"] for item in all_archive_members
            ),
            "archive_members": all_archive_members,
        },
        "random_all": random_metrics,
        "bts_all_on_policy_reference": bts_metrics,
        "item_context": {
            "source_member": item_member,
            "rows": len(item_context),
            "columns": list(item_context.columns),
            "parquet_path": item_path.relative_to(ROOT).as_posix(),
            "parquet_sha256": _sha256(item_path),
            "parquet_bytes": item_path.stat().st_size,
        },
        "included_random_log_columns": columns,
        "task_contract_status": {
            "available": [
                "UTC impression time",
                "item action",
                "position",
                "click outcome",
                "logged propensity",
            ],
            "unknown": [
                "click feedback release time",
                "feature delivery time",
                "user/session identifier",
                "whole-slate request identifier",
            ],
            "scope": "fixed-horizon off-policy policy-value comparison only; no online or anytime-valid claim",
        },
        "limitations": [
            "The archive covers a 7-day historical experiment; it has only seven coarse calendar blocks.",
            "The 10,000-row small sample and full archive are not independent datasets; the small sample is a subset for plumbing only.",
            "The logged click is real platform feedback, not revenue, conversion, welfare, or net business utility.",
            "The published method assumes per-item click reward depends on item and position; reproduce that assumption explicitly for slate evaluation.",
            "User-item affinity features encode prior clicks and are excluded from any learner until their as-of availability is verified.",
            "The Random log is stored in a projected research-ready Parquet; the BTS log was streamed into aggregate on-policy reference metrics and was not expanded to disk.",
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    result = prepare(args.archive, args.output, args.manifest)
    print(
        json.dumps(
            {
                "status": result["status"],
                "archive_sha256": result["source"]["archive_sha256"],
                "random_all": {
                    "rows": result["random_all"]["rows"],
                    "click_rate": result["random_all"]["click_rate"],
                    "days": len(result["random_all"]["daily"]),
                    "parquet_bytes": result["random_all"]["parquet_bytes"],
                },
                "bts_all": {
                    "rows": result["bts_all_on_policy_reference"]["rows"],
                    "click_rate": result["bts_all_on_policy_reference"]["click_rate"],
                    "days": len(result["bts_all_on_policy_reference"]["daily"]),
                },
                "manifest": str(args.manifest),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
