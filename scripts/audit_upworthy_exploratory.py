"""Validate aggregate structure of the Upworthy exploratory experiment split."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/upworthy/upworthy-archive-exploratory-packages-03.12.2020.csv"
OUTPUT = ROOT / "data/reports/upworthy_exploratory_audit.json"
EXPECTED_ROWS = 22_666
EXPECTED_EXPERIMENTS = 4_873
EXPECTED_SHA256 = "8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce"
REQUIRED_COLUMNS = {
    "created_at",
    "updated_at",
    "clickability_test_id",
    "impressions",
    "clicks",
    "winner",
    "test_week",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    """Return aggregate-only integrity and source-timing diagnostics."""
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if frame.empty:
        raise ValueError("Exploratory split is empty")
    if frame["clickability_test_id"].isna().any():
        raise ValueError("Experiment IDs contain missing values")
    if frame["impressions"].isna().any() or frame["clicks"].isna().any():
        raise ValueError("Exposure or click totals contain missing values")

    impressions = frame["impressions"].to_numpy(dtype="int64")
    clicks = frame["clicks"].to_numpy(dtype="int64")
    if (impressions <= 0).any() or (clicks < 0).any() or (clicks > impressions).any():
        raise ValueError("Invalid arm exposure or click count")

    created = pd.to_datetime(frame["created_at"], format="mixed", errors="coerce")
    if created.isna().any():
        raise ValueError("Some package creation timestamps cannot be parsed")

    by_test = frame.groupby("clickability_test_id", sort=False)
    arm_counts = by_test.size()
    start = pd.Timestamp("2013-06-24")
    end = pd.Timestamp("2014-01-11")
    conservative_flag = created.dt.normalize().between(start, end, inclusive="both")
    affected_tests = frame.loc[conservative_flag, "clickability_test_id"].nunique()
    winner_counts = by_test["winner"].sum()

    return {
        "rows": len(frame),
        "experiments": int(frame["clickability_test_id"].nunique()),
        "columns": sorted(str(column) for column in frame.columns),
        "missing_experiment_ids": 0,
        "missing_or_invalid_arm_totals": 0,
        "experiments_with_one_arm": int((arm_counts < 2).sum()),
        "arms_per_experiment": {
            "min": int(arm_counts.min()),
            "median": float(arm_counts.median()),
            "max": int(arm_counts.max()),
        },
        "experiments_with_multiple_editor_winners": int((winner_counts > 1).sum()),
        "created_at_naive_range": {
            "min": str(created.min()),
            "max": str(created.max()),
            "timezone": "not specified by source; parsed as naive timestamps",
        },
        "publisher_flagged_problem_column_present": "Problem" in frame.columns,
        "conservative_assignment_risk_window": {
            "start_inclusive": str(start.date()),
            "end_inclusive": str(end.date()),
            "rationale": "one-day buffer around the publisher's reported 2013-06-25 through 2014-01-10 concern period because created_at timezone is unspecified",
            "experiments_with_any_package_created_in_window": int(affected_tests),
        },
        "test_week_range": [int(frame["test_week"].min()), int(frame["test_week"].max())],
        "total_impressions": int(impressions.sum()),
        "total_clicks": int(clicks.sum()),
    }


def run(*, force: bool = False) -> dict[str, Any]:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing exploratory source file: {SOURCE}")
    if OUTPUT.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}; pass --force to replace it")
    source_hash = sha256(SOURCE)
    if source_hash != EXPECTED_SHA256:
        raise ValueError(f"Unexpected exploratory source SHA-256: {source_hash}")

    frame = pd.read_csv(
        SOURCE,
        usecols=lambda column: column in REQUIRED_COLUMNS,
    )
    summary = summarize(frame)
    if summary["rows"] != EXPECTED_ROWS or summary["experiments"] != EXPECTED_EXPERIMENTS:
        raise ValueError(
            "Exploratory split size mismatch: "
            f"rows={summary['rows']}, experiments={summary['experiments']}"
        )
    report = {
        "schema_version": "1.0.0",
        "status": "exploratory_source_and_schema_qualification_only",
        "dataset": "Upworthy Research Archive, exploratory packages split",
        "source": {
            "url": "https://osf.io/jd64p/",
            "osf_node": "jd64p",
            "osf_file_id": "608ff67f5533b40296e21e5a",
            "filename": SOURCE.name,
            "bytes": SOURCE.stat().st_size,
            "sha256": source_hash,
            "license": "CC BY 4.0",
            "citation": "Matias et al. (2021), Scientific Data, doi:10.1038/s41597-021-00934-7; author correction doi:10.1038/s41597-024-03600-w",
        },
        "audit": summary,
        "scope_limitations": [
            "Only the exploratory partition was opened; confirmatory and holdout partitions remain unopened.",
            "The OSF exploratory CSV predates the 2024 archive update and does not contain the publisher's Problem flag.",
            "The potential assignment-integrity period is excluded conservatively by package creation date with a one-day buffer; timestamp timezone is unspecified.",
            "Outcomes are package-level aggregate clicks and impressions, not impression-level feedback or release times.",
            "The source supports consideration of fixed-horizon experiment-level policy selection only; it does not establish sequential monitoring or online resource-allocation eligibility.",
            "No candidate-selection performance was computed in this audit.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace an existing aggregate report")
    args = parser.parse_args()
    print(json.dumps(run(force=args.force), indent=2))


if __name__ == "__main__":
    main()
