"""Summarize local Monash archive and processed-version evidence."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd

from shiftlab.data.real.monash import DATASETS


def build_report(root: Path) -> dict[str, object]:
    records: list[dict[str, object]] = []
    processed_root = root / "data/processed/monash"
    raw_root = root / "data/raw/monash"
    for dataset, (record, filename, publisher_md5) in DATASETS.items():
        archive_path = raw_root / record / filename
        item: dict[str, object] = {
            "dataset": dataset,
            "zenodo_record": record,
            "archive_present": archive_path.exists(),
        }
        if archive_path.exists():
            digest = hashlib.md5(archive_path.read_bytes(), usedforsecurity=False).hexdigest()
            item["archive_bytes"] = archive_path.stat().st_size
            item["local_md5"] = digest
            item["publisher_md5"] = publisher_md5
            item["publisher_md5_matches"] = digest == publisher_md5
            item["local_sha256"] = hashlib.sha256(archive_path.read_bytes()).hexdigest()
            with zipfile.ZipFile(archive_path) as archive:
                members = [name for name in archive.namelist() if name.endswith(".tsf")]
                if len(members) != 1:
                    item["tsf_error"] = "expected exactly one TSF member"
                else:
                    header = []
                    with archive.open(members[0]) as source:
                        for raw in source:
                            line = raw.decode("cp1252").strip()
                            if line == "@data":
                                break
                            if line.startswith("@"):
                                header.append(line)
                    item["tsf_header"] = header
                    item["declares_horizon"] = any(
                        line.lower().startswith("@horizon ") for line in header
                    )

        matching: list[dict[str, object]] = []
        if processed_root.exists():
            for version_dir in processed_root.iterdir():
                manifest_path = version_dir / "dataset_manifest.json"
                if not version_dir.is_dir() or version_dir.name.startswith(".building-"):
                    continue
                if not manifest_path.exists():
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                parameters = manifest.get("retrieval_parameters", {})
                if parameters.get("dataset") != dataset:
                    continue
                frame = pd.read_parquet(version_dir / "observations.parquet")
                metadata = frame["metadata"].map(json.loads)
                horizons = sorted(
                    {
                        int(value["official_horizon"])
                        for value in metadata
                        if "official_horizon" in value
                    }
                )
                matching.append(
                    {
                        "version": manifest["version"],
                        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                        "code_commit": manifest.get("code_commit"),
                        "source_hash": manifest.get("source_hash"),
                        "forecast_horizon": manifest.get("processing_config", {}).get(
                            "forecast_horizon"
                        ),
                        "forecast_horizon_source": manifest.get("processing_config", {}).get(
                            "forecast_horizon_source", "TSF @horizon when declared"
                        ),
                        "observations": len(frame),
                        "entities": int(frame["entity_id"].nunique()),
                        "split_counts": {
                            str(key): int(value)
                            for key, value in frame.groupby("split", dropna=False).size().items()
                        },
                        "official_horizons": horizons,
                    }
                )
        item["processed_versions"] = matching
        if matching:
            item["status"] = "acquired_and_converted"
        elif item.get("archive_present") and item.get("declares_horizon") is False:
            item["status"] = "archive_acquired_conversion_rejected_missing_declared_horizon"
        elif item.get("archive_present"):
            item["status"] = "archive_acquired_conversion_not_published"
        else:
            item["status"] = "not_acquired"
        records.append(item)
    return {
        "purpose": "Executed Monash source and fixed-horizon conversion evidence",
        "selection_note": "Processed versions are deterministic series subsets, not full archive results.",
        "time_note": "TSF date attributes and sequence indices do not establish release or availability times.",
        "records": records,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = build_report(root)
    output = root / "data/reports/monash_execution.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    records = report["records"]
    assert isinstance(records, list)
    for record in records:
        print(record["dataset"], record["status"])


if __name__ == "__main__":
    main()
