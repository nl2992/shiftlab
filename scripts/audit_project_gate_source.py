"""Validate and summarize the public-use Project GATE trial without row exports.

The SAS files are read from the archived DOL ZIP, extracted only into a
temporary directory, and summarized as counts, schema labels, missingness,
assignment balance, and follow-up linkage diagnostics. No participant-level
data are written to the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ARCHIVE = ROOT / "data/raw/project_gate/SASDataset.zip"
DEFAULT_DOC_ARCHIVE = ROOT / "data/raw/project_gate/ProjectGate.zip"
DEFAULT_OUTPUT = ROOT / "data/reports/project_gate_source_audit.json"
EXPECTED_ARCHIVE_SHA256 = {
    "SASDataset.zip": "c25ba81923888a004641356358200b7f04f59e4f1d13a83d0f2fe384ed6af721",
    "ProjectGate.zip": "f7b200db081828267da775b00074f557844bf76664b5ee3f9ac758e817ca8547",
}
EXPECTED_DATASETS = {
    "application.sas7bdat",
    "wave1.sas7bdat",
    "wave2.sas7bdat",
    "wave3.sas7bdat",
}
EXPECTED_FORMAT_CATALOGS = {
    "formats_appl.sas7bcat",
    "formats_w1_w2.sas7bcat",
    "formats_w3.sas7bcat",
}
ID_NAME = re.compile(
    r"(^|_)(id|caseid|case_id|respondentid|respondent_id|studyid|study_id|gateid)($|_)",
    re.IGNORECASE,
)
OUTCOME_LABEL = re.compile(
    r"business|employ|earn|income|unemploy|wage|profit|benefit|self-employ|"
    r"revenue|sales|hours|insurance|ui |ui$|household",
    re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_member_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Unsafe ZIP member path: {name!r}")


def verify_zip(path: Path, expected_sha256: str) -> dict[str, Any]:
    observed_hash = sha256_file(path)
    if observed_hash != expected_sha256:
        raise ValueError(f"Unexpected SHA-256 for {path.name}: {observed_hash}")
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            validate_member_name(info.filename)
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"CRC failure in {path.name}:{bad_member}")
        entries = {
            info.filename: {
                "uncompressed_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "crc32": f"{info.CRC:08x}",
            }
            for info in archive.infolist()
            if not info.is_dir()
        }
    return {
        "archive_bytes": path.stat().st_size,
        "archive_sha256": observed_hash,
        "zip_crc_check": "passed",
        "entries": entries,
    }


def find_dataset_member(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if PurePosixPath(name).name.casefold() == basename.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {basename} member, found {matches}")
    validate_member_name(matches[0])
    return matches[0]


def sas_summary(frame: pd.DataFrame, metadata: Any) -> dict[str, Any]:
    labels = getattr(metadata, "column_names_to_labels", {}) or {}
    columns = [str(column) for column in frame.columns]
    return {
        "rows": len(frame),
        "columns": len(columns),
        "column_names": columns,
        "column_labels": {str(key): str(value) for key, value in labels.items() if value},
        "missing_cells": int(frame.isna().to_numpy().sum()),
        "rows_with_any_missing": int(frame.isna().any(axis=1).sum()),
        "id_like_columns": [column for column in columns if ID_NAME.search(column)],
        "outcome_field_candidates": [
            {
                "column": column,
                "label": str(labels.get(column, "")),
                "nonmissing": int(frame[column].notna().sum()),
                "distinct_nonmissing": int(frame[column].nunique(dropna=True)),
            }
            for column in columns
            if OUTCOME_LABEL.search(str(labels.get(column, column)))
        ],
    }


def candidate_linkage(
    application: pd.DataFrame, followup: pd.DataFrame, followup_name: str
) -> list[dict[str, Any]]:
    shared = set(application.columns).intersection(followup.columns)
    candidates: list[dict[str, Any]] = []
    for column in sorted(shared):
        if not ID_NAME.search(str(column)):
            continue
        app_key = application[column]
        wave_key = followup[column]
        app_valid = app_key.notna()
        wave_valid = wave_key.notna()
        app_unique = bool(app_key[app_valid].is_unique)
        wave_unique = bool(wave_key[wave_valid].is_unique)
        app_values = set(app_key[app_valid].tolist())
        wave_values = set(wave_key[wave_valid].tolist())
        candidates.append(
            {
                "followup": followup_name,
                "column": str(column),
                "application_nonmissing": int(app_valid.sum()),
                "followup_nonmissing": int(wave_valid.sum()),
                "application_unique": app_unique,
                "followup_unique": wave_unique,
                "matched_unique_ids": len(app_values.intersection(wave_values)),
            }
        )
    return candidates


def summarize_assignment(frame: pd.DataFrame) -> dict[str, Any]:
    lower_names = {str(column).casefold(): column for column in frame.columns}
    treatment_column = lower_names.get("treatment")
    date_column = lower_names.get("date_random_assignment")
    result: dict[str, Any] = {}
    if treatment_column is not None:
        values = frame[treatment_column]
        counts = values.value_counts(dropna=False)
        result["treatment_counts"] = {
            ("<missing>" if pd.isna(value) else str(value)): int(count)
            for value, count in counts.items()
        }
    else:
        result["treatment_column"] = "not found"
    if date_column is not None:
        dates = pd.to_datetime(frame[date_column], errors="coerce")
        result["assignment_date"] = {
            "column": str(date_column),
            "nonmissing": int(dates.notna().sum()),
            "missing": int(dates.isna().sum()),
            "minimum": None if dates.notna().sum() == 0 else dates.min().isoformat(),
            "maximum": None if dates.notna().sum() == 0 else dates.max().isoformat(),
        }
    else:
        result["assignment_date_column"] = "not found"
    return result


def summarize_followup_response(
    application: pd.DataFrame, followups: dict[str, pd.DataFrame]
) -> dict[str, Any]:
    """Compare linked follow-up counts with application completion flags by arm."""
    id_column = "gateid"
    arm_column = "treatment"
    summaries: dict[str, Any] = {}
    if id_column not in application or arm_column not in application:
        return {"status": "required_application_fields_not_found"}

    for wave_name, followup in followups.items():
        wave_number = re.search(r"wave([123])", wave_name)
        if wave_number is None or id_column not in followup:
            continue
        flag_column = f"w{wave_number.group(1)}_completed"
        response_ids = set(followup[id_column].dropna().tolist())
        linked = application[id_column].isin(response_ids)
        by_arm: dict[str, Any] = {}
        for arm, group in application.groupby(arm_column, dropna=False, sort=True):
            arm_linked = linked.loc[group.index]
            n = len(group)
            responses = int(arm_linked.sum())
            arm_result: dict[str, Any] = {
                "application_n": n,
                "linked_followup_n": responses,
                "response_rate": None if n == 0 else responses / n,
                "nonresponse_n": n - responses,
            }
            if flag_column in application:
                flag = application.loc[group.index, flag_column]
                flag_binary = flag.isin([1, 1.0, True])
                arm_result["completion_flag_matches_link"] = int(flag_binary.eq(arm_linked).sum())
                arm_result["completion_flag_mismatches_link"] = int(
                    flag_binary.ne(arm_linked).sum()
                )
            by_arm["<missing>" if pd.isna(arm) else str(arm)] = arm_result
        summaries[wave_name] = {
            "application_flag": flag_column if flag_column in application else None,
            "total_linked_followup_n": int(linked.sum()),
            "by_treatment": by_arm,
        }
    return summaries


def summarize_w3_policy_endpoint(application: pd.DataFrame, wave3: pd.DataFrame) -> dict[str, Any]:
    """Summarize a codebook-defined wave-3 endpoint and interview lag."""
    required = {"gateid", "treatment", "date_random_assignment"}
    wave_required = {"gateid", "int_dt", "dwkc_a"}
    if not required.issubset(application.columns) or not wave_required.issubset(wave3.columns):
        return {"status": "required_endpoint_or_date_fields_not_found"}

    outcome_counts: dict[str, Any] = {}
    merged = application[["gateid", "treatment", "date_random_assignment"]].merge(
        wave3[["gateid", "int_dt", "dwkc_a"]],
        on="gateid",
        how="inner",
        validate="one_to_one",
    )
    for arm, group in merged.groupby("treatment", dropna=False, sort=True):
        counts = group["dwkc_a"].value_counts(dropna=False)
        outcome_counts["<missing>" if pd.isna(arm) else str(arm)] = {
            "respondent_n": len(group),
            "endpoint_counts": {
                "<system_missing>" if pd.isna(value) else str(value): int(count)
                for value, count in counts.items()
            },
        }

    arm_totals = application["treatment"].value_counts(dropna=False).to_dict()
    arm_bounds: dict[str, Any] = {}
    for arm in (0, 1):
        arm_key = str(arm)
        n_assigned = int(arm_totals.get(float(arm), arm_totals.get(arm, 0)))
        arm_outcomes = merged.loc[merged["treatment"].eq(arm), "dwkc_a"]
        successes = int(arm_outcomes.eq(1).sum())
        observed_binary = int(arm_outcomes.isin([0, 1]).sum())
        unobserved = n_assigned - observed_binary
        arm_bounds[arm_key] = {
            "assigned_n_in_public_application_file": n_assigned,
            "observed_binary_outcomes_n": observed_binary,
            "yes_outcomes_n": successes,
            "unobserved_or_unrecognized_outcomes_n": unobserved,
            "no_assumption_mean_lower": successes / n_assigned,
            "no_assumption_mean_upper": (successes + unobserved) / n_assigned,
        }
    control = arm_bounds.get("0.0", arm_bounds.get("0", {}))
    treatment = arm_bounds.get("1.0", arm_bounds.get("1", {}))
    ate_bounds = {
        "lower": treatment["no_assumption_mean_lower"] - control["no_assumption_mean_upper"],
        "upper": treatment["no_assumption_mean_upper"] - control["no_assumption_mean_lower"],
    }

    assignment_dates = pd.to_datetime(merged["date_random_assignment"], errors="coerce")
    interview_dates = pd.to_datetime(merged["int_dt"], errors="coerce")
    elapsed_days = (interview_dates - assignment_dates).dt.total_seconds() / 86400
    valid_lag = elapsed_days.dropna()
    lag_summary = {
        "valid_pairs": int(valid_lag.size),
        "missing_or_invalid_pairs": int(elapsed_days.isna().sum()),
        "minimum_days": None if valid_lag.empty else float(valid_lag.min()),
        "median_days": None if valid_lag.empty else float(valid_lag.median()),
        "maximum_days": None if valid_lag.empty else float(valid_lag.max()),
        "interpretation": "assignment-to-interview measurement lag; label-release time is not recorded",
    }
    return {
        "status": "aggregate_screen_only",
        "source_table": "wave3.sas7bdat",
        "endpoint_column": "dwkc_a",
        "endpoint_label": "D2: Currently: Self-employed",
        "codebook_values": {"0": "No", "1": "Yes"},
        "counts_by_treatment": outcome_counts,
        "no_assumption_attrition_bounds": {
            "scale": "binary outcome difference, treatment offer minus control",
            "by_arm": arm_bounds,
            "ate_bounds": ate_bounds,
            "assumptions": "outcome lies in [0,1]; no assumption about outcomes for wave-3 nonrespondents",
            "scope": "finite public-use application-file cohort; omits sampling uncertainty and the published mixed-arm partnership exclusion/weighting, so it is not a no-interference ITT bound",
        },
        "assignment_to_interview_lag": lag_summary,
        "rows_written": False,
    }


def build_report(data_archive: Path, doc_archive: Path) -> dict[str, Any]:
    try:
        import pyreadstat
    except ImportError as exc:
        raise RuntimeError(
            "pyreadstat is required for SAS validation; run with `uv run --with pyreadstat`."
        ) from exc

    data_hash = EXPECTED_ARCHIVE_SHA256[data_archive.name]
    doc_hash = EXPECTED_ARCHIVE_SHA256[doc_archive.name]
    data_verification = verify_zip(data_archive, data_hash)
    doc_verification = verify_zip(doc_archive, doc_hash)

    with zipfile.ZipFile(data_archive) as data_zip, zipfile.ZipFile(doc_archive) as doc_zip:
        data_basenames = {PurePosixPath(name).name for name in data_zip.namelist()}
        doc_basenames = {PurePosixPath(name).name for name in doc_zip.namelist()}
        missing_data = EXPECTED_DATASETS - data_basenames
        missing_catalogs = EXPECTED_FORMAT_CATALOGS - data_basenames
        if missing_data or missing_catalogs:
            raise ValueError(
                f"SASDataset archive lacks expected entries: datasets={sorted(missing_data)}, "
                f"catalogs={sorted(missing_catalogs)}"
            )
        if not EXPECTED_DATASETS.issubset(doc_basenames):
            raise ValueError("ProjectGate.zip does not contain all four SAS datasets")

        member_hashes: dict[str, str] = {}
        for basename in sorted(EXPECTED_DATASETS | EXPECTED_FORMAT_CATALOGS):
            data_member = find_dataset_member(data_zip, basename)
            doc_member = find_dataset_member(doc_zip, basename)
            data_digest = hashlib.sha256(data_zip.read(data_member)).hexdigest()
            doc_digest = hashlib.sha256(doc_zip.read(doc_member)).hexdigest()
            if data_digest != doc_digest:
                raise ValueError(f"Conflicting copies of {basename} in the two source ZIPs")
            member_hashes[basename] = data_digest

        tables: dict[str, pd.DataFrame] = {}
        table_summaries: dict[str, Any] = {}
        with tempfile.TemporaryDirectory(prefix="shiftlab-gate-audit-") as tmp:
            temp_dir = Path(tmp)
            for basename in sorted(EXPECTED_DATASETS):
                member = find_dataset_member(data_zip, basename)
                local_path = temp_dir / basename
                with data_zip.open(member) as source, local_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
                frame, metadata = pyreadstat.read_sas7bdat(str(local_path))
                tables[basename] = frame
                table_summaries[basename] = sas_summary(frame, metadata)

        application = tables["application.sas7bdat"]
        assignment_summary = summarize_assignment(application)
        linkages = [
            item
            for wave_name in ("wave1.sas7bdat", "wave2.sas7bdat", "wave3.sas7bdat")
            for item in candidate_linkage(application, tables[wave_name], wave_name)
        ]
        matched_id_candidates = [
            item for item in linkages if item["application_unique"] and item["followup_unique"]
        ]
        response_summary = summarize_followup_response(
            application,
            {
                wave_name: tables[wave_name]
                for wave_name in ("wave1.sas7bdat", "wave2.sas7bdat", "wave3.sas7bdat")
            },
        )
        w3_endpoint_summary = summarize_w3_policy_endpoint(application, tables["wave3.sas7bdat"])

    report = {
        "schema_version": "1.0.0",
        "dataset": "project_gate_public_use_randomized_intervention",
        "status": "source_files_verified_and_aggregate_schema_audited",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "publisher": "U.S. Department of Labor, Employment and Training Administration",
            "official_landing_page": "https://www.dol.gov/agencies/eta/reports/project-gate-dataset",
            "official_data_guide": "https://www.dol.gov/sites/dolgov/files/ETA/reports/pdfs/Project%20GATE%20Public%20Use%20Dataset.pdf",
            "official_impact_report": "https://www.dol.gov/sites/dolgov/files/ETA/publications/Growing%20America%20through%20Entrepreneurship%20-%20Final%20Evaluation%20of%20Project%20GATE.pdf",
            "data_gov_record": "https://catalog.data.gov/dataset/project-gate-growing-america-through-entrepreneurship-final-evaluation-dataset",
            "retrieval_route": "Internet Archive capture of DOL page dated 2026-06-15; archived URLs resolve to DOL-hosted SASDataset.zip and ProjectGate.zip",
            "archived_page_capture": "https://web.archive.org/web/20260615080718id_/https://www.dol.gov/agencies/eta/reports/project-gate-dataset",
            "archive_files": [data_archive.name, doc_archive.name],
            "official_live_download_returned_http_403": True,
            "participant_rows_reported_by_publisher": 4198,
            "trial_accounting_from_final_report": {
                "randomized_n": 4198,
                "nonrandom_assignment_removed_from_analysis_n": 1,
                "public_use_application_n": 4197,
                "mixed_arm_business_partnership_members_excluded_from_published_impact_analysis_n": 120,
                "published_analysis_sample_after_partnership_exclusion_n": 4078,
                "partnership_identifiers_in_public_use_application_schema": False,
                "individual_analysis_weights_in_public_use_schema": False,
            },
            "followup_horizons_months": [6, 18, 60],
            "assignment_design": "DOL evaluation report states each eligible applicant had 50% probability of control and 50% probability of treatment offer; assignment occurred on average less than one week after application",
            "documented_intervention_cost": {
                "amount_usd": 1321,
                "unit": "per program-group member",
                "basis": "invoice data, as reported by DOL",
                "dollar_year": "not identified in extracted report summary; verify before combining with outcome dollars",
            },
            "use_and_redistribution": "public-use source; raw files remain ignored locally pending source-specific redistribution review",
        },
        "archives": {data_archive.name: data_verification, doc_archive.name: doc_verification},
        "sas_member_sha256": member_hashes,
        "datasets": table_summaries,
        "assignment": assignment_summary,
        "followup_response_by_treatment": response_summary,
        "wave3_policy_endpoint_screen": w3_endpoint_summary,
        "followup_linkage_candidates": linkages,
        "unique_linkage_candidates": matched_id_candidates,
        "data_handling": {
            "participant_rows_written": False,
            "sas_files_extracted_to": "temporary directory removed after audit",
            "report_contains": "aggregate counts, schema names/labels, missingness, and linkage counts only",
            "missingness_semantics": "pandas system-missing values only; codebook-coded skip, dont-know, and refusal values remain numeric and require field-specific recoding",
        },
        "limitations": [
            "The final report explains the 4,198-to-4,197 difference as removal of one nonrandomly assigned applicant; its 120 mixed-arm business-partnership exclusions cannot be recreated from the public-use application schema because partnership identifiers are absent.",
            "This is fixed-horizon intention-to-treat evidence, not an event-level stream or delayed-feedback evaluation.",
            "Wave response is differential by treatment arm; population policy values require explicit missingness assumptions and sensitivity analysis.",
            "Aggregate missing-cell counts do not classify codebook-coded skip, dont-know, or refusal values as missing outcomes.",
            "DOL reports an invoice-based program-group cost of $1,321 per member, but the extracted summary does not identify its dollar year or a cost suitable for individualized policy evaluation.",
            "This dataset is a development candidate until a final split and outcome contract are frozen; no policy evaluation has been run.",
        ],
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-archive", type=Path, default=DEFAULT_DATA_ARCHIVE)
    parser.add_argument("--doc-archive", type=Path, default=DEFAULT_DOC_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_report(args.data_archive, args.doc_archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(args.output),
                "archive_sha256": report["archives"][args.data_archive.name]["archive_sha256"],
                "tables": {name: summary["rows"] for name, summary in report["datasets"].items()},
                "unique_linkage_candidates": report["unique_linkage_candidates"],
                "assignment": report["assignment"],
                "participant_rows_written": report["data_handling"]["participant_rows_written"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
