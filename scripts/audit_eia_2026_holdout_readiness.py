"""Audit EIA 2026 event coverage and prior ShiftLab exposure without scoring outcomes."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/eia/EBA.zip"
RECEIPT = ROOT / "data/raw/eia/EBA.zip.receipt.json"
PROCESSED = ROOT / "data/processed/eia/e47bdef8b208f8e7d788"
OUTPUTS = ROOT / "outputs"
REPORT = ROOT / "data/reports/eia_2026_holdout_readiness.json"
RESPONDENTS = ("CISO", "ERCO")
TYPES = ("D", "DF", "NG", "TI")
EXPECTED_SHA256 = "3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f"
HOUR = 3600


def _epoch(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp())


SPLITS = (
    ("train", _epoch("2019-01-01T00:00:00Z"), _epoch("2024-12-30T23:00:00Z")),
    ("calibration", _epoch("2025-01-01T00:00:00Z"), _epoch("2025-12-30T23:00:00Z")),
    ("test", _epoch("2026-01-01T00:00:00Z"), _epoch("2026-10-19T17:00:00Z")),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _date(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(float(epoch), tz=UTC).isoformat()


def _read_selected_series(archive_path: Path) -> dict[str, dict[int, float | None]]:
    wanted = {f"EBA.{respondent}-ALL.{kind}.H" for respondent in RESPONDENTS for kind in TYPES}
    series: dict[str, dict[int, float | None]] = {}
    with zipfile.ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if Path(name).name == "EBA.txt"]
        if len(members) != 1:
            raise ValueError("EBA archive must contain exactly one EBA.txt member")
        with archive.open(members[0]) as source:
            for line_number, line in enumerate(source, start=1):
                try:
                    item = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(f"Malformed EBA JSON at line {line_number}") from exc
                series_id = item.get("series_id")
                if series_id not in wanted:
                    continue
                if item.get("f") != "H":
                    raise ValueError(f"Expected hourly frequency for {series_id}")
                if series_id in series:
                    raise ValueError(f"Duplicate EBA series {series_id}")
                values: dict[int, float | None] = {}
                for period, raw_value in item.get("data", []):
                    key = int(
                        datetime.strptime(period, "%Y%m%dT%H").replace(tzinfo=UTC).timestamp()
                    )
                    if key in values:
                        raise ValueError(f"Duplicate hour in {series_id}: {period}")
                    values[key] = None if raw_value is None else float(raw_value)
                series[series_id] = values
    missing = wanted - set(series)
    if missing:
        raise ValueError(f"EBA archive lacks required series: {sorted(missing)}")
    return series


def _eligible_rows(series: dict[str, dict[int, float | None]], respondent: str) -> list[dict]:
    by_type = {kind: series[f"EBA.{respondent}-ALL.{kind}.H"] for kind in TYPES}
    output: list[dict] = []
    for event_time in by_type["D"]:
        target_time = event_time + HOUR
        target = by_type["D"].get(target_time)
        if target is None or not np.isfinite(target):
            continue
        features = [by_type[kind].get(event_time) for kind in TYPES]
        split = next((name for name, start, end in SPLITS if start <= event_time <= end), None)
        if split is None:
            continue
        output.append(
            {
                "event_time": event_time,
                "target_time": target_time,
                "split": split,
                "complete_features": all(
                    value is not None and np.isfinite(value) for value in features
                ),
            }
        )
    output.sort(key=lambda row: row["event_time"])
    return output


def _summarize_rows(rows: list[dict]) -> dict:
    result = {}
    for name, _, _ in SPLITS:
        part = [row for row in rows if row["split"] == name]
        complete = [row for row in part if row["complete_features"]]
        times = [row["event_time"] for row in complete]
        gaps = [right - left for left, right in itertools.pairwise(times) if right - left != HOUR]
        result[name] = {
            "rows_with_observed_next_hour_target": len(part),
            "rows_with_complete_four_feature_vector": len(complete),
            "first_complete_event_utc": _date(times[0]) if times else None,
            "last_complete_event_utc": _date(times[-1]) if times else None,
            "non_hourly_gaps_in_complete_event_sequence": len(gaps),
            "largest_event_gap_seconds": max(gaps, default=HOUR),
        }
    return result


def _audit_prior_shiftlab_exposure(processed_manifest: dict) -> dict:
    eia_manifests = []
    for path in OUTPUTS.rglob("manifest.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("dataset_version") == processed_manifest["version"]:
            eia_manifests.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "study": item.get("study"),
                    "dataset_version": item.get("dataset_version"),
                }
            )

    # Search EIA result artifacts only for explicit event dates inside the held-out
    # window. Run timestamps and code-generation dates are not treated as data use.
    eia_dirs = [
        path
        for path in (OUTPUTS / "shiftguard_unified/real_data_development").glob("*eia*")
        if path.is_dir()
    ]
    pattern = re.compile(r"2026(?:-?(?:0[1-9]|10)-?(?:0[1-9]|[12][0-9]|3[01]))")
    date_hits: list[dict] = []
    scanned = 0
    for directory in eia_dirs:
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() in {".parquet", ".png", ".pdf"}:
                continue
            scanned += 1
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            hits = sorted(set(pattern.findall(content)))
            if hits:
                # Remove the audit/run date; only report dates within the registered
                # Jan 1 through Oct 19 event-time window.
                event_hits = [
                    value
                    for value in hits
                    if value.replace("-", "") >= "20260101" and value.replace("-", "") <= "20261019"
                ]
                if event_hits:
                    date_hits.append(
                        {"path": path.relative_to(ROOT).as_posix(), "matches": event_hits}
                    )
    max_event = float(processed_manifest["time_coverage"][1])
    return {
        "processed_development_dataset_version": processed_manifest["version"],
        "processed_development_event_coverage": processed_manifest["time_coverage"],
        "processed_development_ends_before_2026": max_event < _epoch("2026-01-01T00:00:00Z"),
        "prior_result_manifests_using_processed_version": eia_manifests,
        "eia_result_text_files_scanned": scanned,
        "explicit_2026_event_date_matches_in_prior_eia_result_text": date_hits,
        "interpretation": "Manifest and text audit supports no prior ShiftLab scoring of the 2026 period; it is not a proof about unrecorded human inspection. The 2026 EBA source dates were inspected for coverage only.",
    }


def run() -> Path:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    archive_hash = _sha256(ARCHIVE)
    if archive_hash != EXPECTED_SHA256 or receipt.get("sha256") != archive_hash:
        raise ValueError("EBA archive checksum does not match the frozen source receipt")
    processed_manifest = json.loads(
        (PROCESSED / "dataset_manifest.json").read_text(encoding="utf-8")
    )
    if processed_manifest.get("version") != "e47bdef8b208f8e7d788":
        raise ValueError("Unexpected prior EIA development dataset version")
    if not _audit_prior_shiftlab_exposure(processed_manifest)[
        "processed_development_ends_before_2026"
    ]:
        raise ValueError("Prior processed development dataset reaches into the 2026 holdout")

    series = _read_selected_series(ARCHIVE)
    series_coverage = {}
    for series_id, values in sorted(series.items()):
        periods = list(values)
        null_count = sum(value is None for value in values.values())
        series_coverage[series_id] = {
            "n_periods": len(values),
            "n_null_values": null_count,
            "first_period_utc": _date(min(periods)),
            "last_period_utc": _date(max(periods)),
        }
    by_domain = {
        respondent: _summarize_rows(_eligible_rows(series, respondent))
        for respondent in RESPONDENTS
    }
    prior_exposure = _audit_prior_shiftlab_exposure(processed_manifest)
    if prior_exposure["explicit_2026_event_date_matches_in_prior_eia_result_text"]:
        raise ValueError(
            "Prior EIA result text contains a date inside the reserved 2026 event period"
        )
    report = {
        "audit": "eia_2026_out_of_time_holdout_readiness",
        "audit_timestamp_utc": datetime.now(UTC).isoformat(),
        "source_url": "https://www.eia.gov/opendata/bulk/EBA.zip",
        "source_retrieved_at": receipt.get("downloaded_at"),
        "source_last_modified": receipt.get("last_modified"),
        "source_bytes": ARCHIVE.stat().st_size,
        "source_sha256": archive_hash,
        "source_receipt_sha256": _sha256(RECEIPT),
        "prior_processed_manifest_sha256": _sha256(PROCESSED / "dataset_manifest.json"),
        "audit_script_sha256": _sha256(Path(__file__)),
        "coverage_only_inspection": True,
        "raw_rows_or_policy_metrics_persisted": False,
        "series_coverage": series_coverage,
        "forecast_rows_by_domain_and_split": by_domain,
        "prior_shiftlab_exposure_audit": prior_exposure,
        "protocol": "papers/shiftguard_unified/eia_2026_out_of_time_confirmation_protocol_v1.md",
        "eligibility": "candidate out-of-time period; score only after gap-safe runner and frozen protocol checks pass",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return REPORT


if __name__ == "__main__":
    run()
    print("data/reports/eia_2026_holdout_readiness.json")
