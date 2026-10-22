"""Build and validate the CRSP CIZ next-observed-return research panel."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scripts.extract_crsp_ciz_wrds_cloud import (
        COLUMNS,
        EXCHANGES,
        TABLE,
        build_query,
        query_hash,
    )
except ModuleNotFoundError:  # Direct `python scripts/...` execution puts scripts/ on sys.path.
    from extract_crsp_ciz_wrds_cloud import COLUMNS, EXCHANGES, TABLE, build_query, query_hash
from shiftlab.data.provenance import sha256, write_json
from shiftlab.data.storage import save_dataset

FEATURES = [
    "dlyret",
    "dlyretx",
    "dlyreti",
    "log_abs_dlyprc",
    "log1p_dlyvol",
    "log1p_dlycap",
    "log1p_dlynumtrd",
    "vwretd",
    "vwretx",
    "ewretd",
    "ewretx",
    "sprtrn",
]
ONE_TRADING_DAY_DURATIONS = {"D1", "D2", "D3", "D4", "DU"}
TARGET_QUALITY_RULE = (
    "Use the immediately next observed row for the same PERMNO; retain the target only when "
    "dlyret is finite, dlyretmissflg is NA (documented as not missing), and "
    "dlyretdurflg is one of D1,D2,D3,D4,DU (one trading day). Do not skip a bad next "
    "observation to find a later valid return. Delisting rows are retained when they pass this rule."
)
SPLITS = {
    "train": (2000, 2014),
    "validation": (2015, 2017),
    "calibration": (2018, 2019),
    "test": (2020, 2025),
}
BOUNDARY_COLUMNS = [
    "permno",
    "dlycaldt",
    "dlyret",
    "dlyretmissflg",
    "dlyretdurflg",
    "dlydelflg",
    "securitytype",
    "securitysubtype",
    "sharetype",
    "primaryexch",
]
READ_COLUMNS = list(COLUMNS)
FLAG_COLUMNS = ["dlyretmissflg", "dlyretdurflg", "dlyprcflg", "dlycapflg", "dlydelflg"]


def _csv_chunks(path: Path, columns: list[str], chunksize: int):
    return pd.read_csv(
        path,
        compression="gzip",
        usecols=columns,
        chunksize=chunksize,
        keep_default_na=False,
        na_values=["", "nan", "NaN"],
        low_memory=False,
    )


def _row_key(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    permno = pd.to_numeric(frame["permno"], errors="raise").to_numpy(dtype=np.int64)
    dates = frame["dlycaldt"].astype(str).to_numpy()
    return permno, dates


def _check_order(frame: pd.DataFrame, previous: tuple[int, str] | None):
    permno, dates = _row_key(frame)
    if not len(permno):
        return previous
    invalid = (permno[1:] < permno[:-1]) | ((permno[1:] == permno[:-1]) & (dates[1:] <= dates[:-1]))
    if invalid.any() or (previous is not None and (permno[0], dates[0]) <= previous):
        raise ValueError("CRSP rows are not strictly ordered by PERMNO and date")
    return int(permno[-1]), dates[-1]


def _check_universe(frame: pd.DataFrame, year: int) -> None:
    dates = pd.to_datetime(frame["dlycaldt"], errors="coerce")
    if dates.isna().any() or (dates.dt.year != year).any():
        raise ValueError(f"Invalid or out-of-year dates in {year}")
    expected = (
        frame.securitytype.eq("EQTY")
        & frame.securitysubtype.eq("COM")
        & frame.sharetype.eq("NS")
        & frame.primaryexch.isin(EXCHANGES)
    )
    if not expected.all():
        raise ValueError(f"Extracted CRSP universe filters do not hold for {year}")


def _boundary_record(row) -> dict:
    return {
        "date": str(row.dlycaldt),
        "ret": pd.to_numeric(row.dlyret, errors="coerce"),
        "missflag": row.dlyretmissflg,
        "duration": row.dlyretdurflg,
        "delflag": row.dlydelflg,
    }


def audit_source(root: Path, chunksize: int):
    """Verify all source parts and record first/last rows per security/year."""
    first: dict[tuple[int, int], dict] = {}
    last: dict[tuple[int, int], dict] = {}
    raw_checksums: dict[str, str] = {}
    flag_counts: Counter = Counter()
    part_count = 0
    total_rows = 0

    for year in range(2000, 2026):
        year_dir = root / f"year={year}"
        manifest_path = year_dir / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Missing annual extraction manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("year") != year or manifest.get("table") != TABLE:
            raise ValueError(f"Unexpected CRSP manifest identity for {year}")
        if manifest.get("query_sha256") != query_hash(build_query(year)):
            raise ValueError(f"Query hash mismatch in {manifest_path}")
        entries = manifest.get("files")
        if not entries:
            raise ValueError(f"No part checksums recorded for {year}")
        expected_names = {entry["name"] for entry in entries}
        actual_names = {p.name for p in year_dir.glob("part-*.csv.gz")}
        if actual_names != expected_names:
            raise ValueError(f"Annual part inventory mismatch for {year}")

        year_rows = 0
        previous = None
        for entry in entries:
            path = year_dir / entry["name"]
            digest = sha256(path)
            if digest != entry["sha256"]:
                raise ValueError(f"CRSP raw part checksum mismatch: {path}")
            raw_checksums[(Path(f"year={year}") / path.name).as_posix()] = digest
            raw_checksums[(Path(f"year={year}") / "manifest.json").as_posix()] = sha256(
                manifest_path
            )
            part_rows = 0
            for chunk in _csv_chunks(path, BOUNDARY_COLUMNS, chunksize):
                if set(chunk.columns) != set(BOUNDARY_COLUMNS):
                    raise ValueError(f"Unexpected selected CRSP columns in {path}")
                _check_universe(chunk, year)
                previous = _check_order(chunk, previous)
                part_rows += len(chunk)
                for name in ("dlyretmissflg", "dlyretdurflg"):
                    values = chunk[name].fillna("<blank>").astype(str)
                    for key, count in values.value_counts(dropna=False).items():
                        flag_counts[f"{name}:{key}"] += int(count)
                flag_counts["dlyret_finite"] += int(
                    np.isfinite(pd.to_numeric(chunk.dlyret, errors="coerce")).sum()
                )
                permnos = pd.to_numeric(chunk.permno, errors="raise").astype("int64")
                starts = permnos.ne(permnos.shift()).to_numpy()
                ends = permnos.ne(permnos.shift(-1)).to_numpy()
                for row in chunk.loc[starts, BOUNDARY_COLUMNS].itertuples(index=False):
                    key = (year, int(row.permno))
                    first.setdefault(key, _boundary_record(row))
                for row in chunk.loc[ends, BOUNDARY_COLUMNS].itertuples(index=False):
                    key = (year, int(row.permno))
                    last[key] = _boundary_record(row)
            if part_rows != int(entry["rows"]):
                raise ValueError(f"Part row count mismatch for {path}: {part_rows}")
            year_rows += part_rows
            part_count += 1
        if year_rows != int(manifest["row_count"]):
            raise ValueError(f"Annual row count mismatch for {year}")
        total_rows += year_rows
        print(f"{year}: verified {len(entries)} parts, {year_rows:,} rows", flush=True)

    following: dict[tuple[int, int], dict] = {}
    per_permno: dict[int, list[int]] = defaultdict(list)
    for year, permno in first:
        per_permno[permno].append(year)
    for permno, years in per_permno.items():
        years.sort()
        for current_year, future_year in itertools.pairwise(years):
            following[(current_year, permno)] = first[(future_year, permno)]
    boundary = {key: following[key] for key in last if key in following}
    return {
        "first": first,
        "last": last,
        "boundary": boundary,
        "raw_checksums": raw_checksums,
        "flag_counts": dict(sorted(flag_counts.items())),
        "part_count": part_count,
        "source_rows": total_rows,
    }


def _split_for_year(year: int) -> str:
    for split, (start, end) in SPLITS.items():
        if start <= year <= end:
            return split
    return "unassigned"


def _numeric(frame: pd.DataFrame, name: str) -> pd.Series:
    return pd.to_numeric(frame[name], errors="coerce").astype("float64")


def _features(frame: pd.DataFrame) -> np.ndarray:
    price = _numeric(frame, "dlyprc").abs()
    volume = _numeric(frame, "dlyvol")
    cap = _numeric(frame, "dlycap")
    trades = _numeric(frame, "dlynumtrd")
    values = [
        _numeric(frame, "dlyret"),
        _numeric(frame, "dlyretx"),
        _numeric(frame, "dlyreti"),
        np.log(price.where(price > 0)),
        np.log1p(volume.where(volume >= 0)),
        np.log1p(cap.where(cap >= 0)),
        np.log1p(trades.where(trades >= 0)),
        _numeric(frame, "vwretd"),
        _numeric(frame, "vwretx"),
        _numeric(frame, "ewretd"),
        _numeric(frame, "ewretx"),
        _numeric(frame, "sprtrn"),
    ]
    matrix = np.column_stack([np.asarray(value, dtype=np.float64) for value in values])
    matrix[~np.isfinite(matrix)] = np.nan
    return matrix


def _attach_next(frame: pd.DataFrame, year: int, boundary: dict) -> pd.DataFrame:
    frame = frame.copy()
    grouped = frame.groupby("permno", sort=False)
    frame["_target_return"] = grouped.dlyret.shift(-1)
    frame["_target_date"] = grouped.dlycaldt.shift(-1)
    frame["_target_missflag"] = grouped.dlyretmissflg.shift(-1)
    frame["_target_duration"] = grouped.dlyretdurflg.shift(-1)
    frame["_target_delflag"] = grouped.dlydelflg.shift(-1)
    group_end = frame.permno.ne(frame.permno.shift(-1))
    end_rows = frame.loc[group_end, "permno"]
    for index, permno in end_rows.items():
        next_row = boundary.get((year, int(permno)))
        if next_row is None:
            continue
        frame.at[index, "_target_return"] = next_row["ret"]
        frame.at[index, "_target_date"] = next_row["date"]
        frame.at[index, "_target_missflag"] = next_row["missflag"]
        frame.at[index, "_target_duration"] = next_row["duration"]
        frame.at[index, "_target_delflag"] = next_row["delflag"]
    return frame


def _to_observations(frame: pd.DataFrame, year: int, boundary: dict, stats: Counter):
    if frame.empty:
        return None
    frame = _attach_next(frame, year, boundary)
    target = pd.to_numeric(frame._target_return, errors="coerce").to_numpy(dtype=float)
    duration = frame._target_duration.fillna("").astype(str)
    missflag = frame._target_missflag.fillna("").astype(str)
    target_date = pd.to_datetime(frame._target_date, errors="coerce")
    quality = (
        np.isfinite(target)
        & missflag.eq("NA").to_numpy()
        & duration.isin(ONE_TRADING_DAY_DURATIONS).to_numpy()
        & target_date.notna().to_numpy()
    )
    stats["source_rows_processed"] += len(frame)
    stats["no_next_observation"] += int(target_date.isna().sum())
    stats["excluded_target_quality"] += int((~quality & target_date.notna().to_numpy()).sum())
    current_dates = pd.to_datetime(frame.dlycaldt, errors="raise")
    split = np.array([_split_for_year(int(value)) for value in current_dates.dt.year], dtype=object)
    target_split = np.array(
        [
            _split_for_year(int(value)) if pd.notna(value) else "unassigned"
            for value in target_date.dt.year
        ]
    )
    split[(split != target_split) & (split != "unassigned")] = "unassigned"
    keep = quality
    if not keep.any():
        return None

    selected = frame.loc[keep].copy()
    selected_dates = current_dates.loc[keep]
    selected_target_dates = target_date.loc[keep]
    selected_target = target[keep]
    selected_split = split[keep]
    times = selected_dates.map(lambda value: 2 * value.date().toordinal()).to_numpy(
        dtype=np.float64
    )
    target_times = selected_target_dates.map(lambda value: 2 * value.date().toordinal()).to_numpy(
        dtype=np.float64
    )
    features = _features(selected)
    for i, name in enumerate(FEATURES):
        stats[f"feature_missing:{name}"] += int(np.isnan(features[:, i]).sum())
    stats["retained_targets"] += len(selected)
    for name, count in zip(*np.unique(selected_split, return_counts=True)):
        stats[f"split:{name}"] += int(count)
    stats["cross_split_purged"] += int(np.count_nonzero(selected_split == "unassigned"))

    def strings(series):
        return series.fillna("").astype(str).replace("<NA>", "").to_numpy()

    return pd.DataFrame(
        {
            "sample_id": [
                f"crsp-ciz:{int(permno)}:{date:%Y%m%d}"
                for permno, date in zip(selected.permno, selected_dates)
            ],
            "entity_id": selected.permno.astype("int64").astype(str).to_numpy(),
            "event_time": times,
            "feature_available_time": times,
            "prediction_time": times + 1,
            "label_event_time": target_times,
            "label_available_time": target_times,
            "features": list(features),
            "target": selected_target,
            "domain_id": strings(selected.primaryexch),
            "regime_id": None,
            "decision_context": None,
            "sample_weight": np.ones(len(selected), dtype=np.float64),
            "split": selected_split,
            "metadata": ["CRSP CIZ daily; retrospective session-order clock; see dataset manifest"]
            * len(selected),
            "permno": selected.permno.astype("int64").to_numpy(),
            "permco": pd.to_numeric(selected.permco, errors="coerce").to_numpy(),
            "dlycaldt": selected_dates.dt.strftime("%Y-%m-%d").to_numpy(),
            "target_date": selected_target_dates.dt.strftime("%Y-%m-%d").to_numpy(),
            "ticker": strings(selected.ticker),
            "primaryexch": strings(selected.primaryexch),
            "tradingstatusflg": strings(selected.tradingstatusflg),
            "dlydelflg": strings(selected.dlydelflg),
            "dlyretmissflg": strings(selected.dlyretmissflg),
            "dlyretdurflg": strings(selected.dlyretdurflg),
            "target_dlyretmissflg": missflag.loc[keep].to_numpy(),
            "target_dlyretdurflg": duration.loc[keep].to_numpy(),
            "target_dlydelflg": strings(frame.loc[keep, "_target_delflag"]),
            "dlyprcflg": strings(selected.dlyprcflg),
            "dlycapflg": strings(selected.dlycapflg),
        }
    )


def observation_chunks(raw_root: Path, chunksize: int, audit: dict, stats: Counter):
    boundary = audit["boundary"]
    for year in range(2000, 2026):
        year_dir = raw_root / f"year={year}"
        carry = pd.DataFrame()
        previous = None
        year_count = 0
        manifest = json.loads((year_dir / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            path = year_dir / entry["name"]
            part_count = 0
            for chunk in _csv_chunks(path, READ_COLUMNS, chunksize):
                _check_universe(chunk, year)
                previous = _check_order(chunk, previous)
                year_count += len(chunk)
                part_count += len(chunk)
                frame = pd.concat([carry, chunk], ignore_index=True) if len(carry) else chunk
                final_permno = frame.permno.iloc[-1]
                complete = frame.loc[frame.permno != final_permno]
                carry = frame.loc[frame.permno == final_permno].copy()
                result = _to_observations(complete, year, boundary, stats)
                if result is not None and len(result):
                    yield result, None
            if part_count != int(entry["rows"]):
                raise ValueError(f"Source part changed after audit: {path}")
        result = _to_observations(carry, year, boundary, stats)
        if result is not None and len(result):
            yield result, None
        if year_count != int(manifest["row_count"]):
            raise ValueError(f"Source annual count changed after audit: {year}")
        print(f"{year}: source rows processed {year_count:,}", flush=True)


def validate_panel(directory: Path) -> dict:
    """Recheck the published Parquet in bounded batches, including target/split invariants."""
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(directory / "observations.parquet")
    counts: Counter = Counter()
    columns = [
        "permno",
        "dlycaldt",
        "target_date",
        "event_time",
        "feature_available_time",
        "prediction_time",
        "label_event_time",
        "label_available_time",
        "target",
        "split",
        "target_dlyretmissflg",
        "target_dlyretdurflg",
        "features",
    ]
    for batch in parquet.iter_batches(columns=columns, batch_size=100_000):
        frame = batch.to_pandas()
        current = pd.to_datetime(frame.dlycaldt, errors="coerce")
        target_date = pd.to_datetime(frame.target_date, errors="coerce")
        if current.isna().any() or target_date.isna().any() or not (target_date > current).all():
            raise ValueError("Published panel has an invalid or non-forward target date")
        if not np.isfinite(frame.target.to_numpy(dtype=float)).all():
            raise ValueError("Published panel contains a non-finite target")
        if not frame.target_dlyretmissflg.eq("NA").all():
            raise ValueError(
                "Published panel contains a target with a disallowed missing-return flag"
            )
        if not frame.target_dlyretdurflg.isin(ONE_TRADING_DAY_DURATIONS).all():
            raise ValueError("Published panel contains a multi-period or missing-duration target")
        expected_current = np.array([_split_for_year(int(y)) for y in current.dt.year])
        expected_target = np.array([_split_for_year(int(y)) for y in target_date.dt.year])
        expected = np.where(expected_current == expected_target, expected_current, "unassigned")
        if not np.array_equal(frame.split.astype(str).to_numpy(), expected):
            raise ValueError("Published panel has a split assignment or target-boundary leak")
        event = 2 * current.map(lambda x: x.date().toordinal()).to_numpy(dtype=np.float64)
        target_event = 2 * target_date.map(lambda x: x.date().toordinal()).to_numpy(
            dtype=np.float64
        )
        if not np.array_equal(frame.event_time.to_numpy(dtype=float), event):
            raise ValueError("event_time does not match the documented daily session clock")
        if not np.array_equal(frame.feature_available_time.to_numpy(dtype=float), event):
            raise ValueError("Feature availability does not match the daily session clock")
        if not np.array_equal(frame.prediction_time.to_numpy(dtype=float), event + 1):
            raise ValueError("prediction_time does not follow same-day feature availability")
        if not np.array_equal(frame.label_event_time.to_numpy(dtype=float), target_event):
            raise ValueError("label_event_time does not match target_date")
        if not np.array_equal(frame.label_available_time.to_numpy(dtype=float), target_event):
            raise ValueError("label availability does not match the retrospective close convention")
        features = np.stack(frame.features.to_numpy())
        if np.isinf(features).any():
            raise ValueError("Published panel features contain infinity")
        counts.update(f"split:{key}" for key in frame.split.astype(str).tolist())
        counts["rows"] += len(frame)
    return {
        "rows": counts.pop("rows"),
        "split_counts": dict(sorted(counts.items())),
        "manifest_file_sha256": json.loads((directory / "dataset_manifest.json").read_text())[
            "files"
        ]["observations.parquet"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/licensed/crsp"))
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--chunk-rows", type=int, default=100_000)
    args = parser.parse_args()
    if args.chunk_rows < 1:
        parser.error("--chunk-rows must be positive")

    raw_root = args.raw_root.resolve()
    if not raw_root.is_dir():
        parser.error(f"CRSP raw directory not found: {raw_root}")
    print("Verifying all annual manifests, raw part hashes, row counts, and sort order...")
    audit = audit_source(raw_root, args.chunk_rows)
    print(
        f"Verified {audit['part_count']} parts across 26 years "
        f"({audit['source_rows']:,} source rows). Building panel...",
        flush=True,
    )

    config = {
        "builder_script_sha256": sha256(Path(__file__)),
        "source_table": TABLE,
        "start_year": 2000,
        "end_year": 2025,
        "universe": {
            "securitytype": "EQTY",
            "securitysubtype": "COM",
            "sharetype": "NS",
            "primaryexch": list(EXCHANGES),
            "historical_delistings": "retained",
        },
        "target": "next observed dlyret within PERMNO; target-date retained",
        "target_quality_rule": TARGET_QUALITY_RULE,
        "feature_names": FEATURES,
        "feature_transformations": {
            "dlyprc": "natural log of absolute nonzero daily price",
            "dlyvol": "log1p of nonnegative daily volume",
            "dlycap": "log1p of nonnegative market capitalization",
            "dlynumtrd": "log1p of nonnegative trade count",
            "other_features": "same-date daily return and market-index fields",
            "missing_values": "preserved as null; smoke model median-imputes using training only",
        },
        "split_years": SPLITS,
        "cross_split_targets": "purged to unassigned; never shift across PERMNO or assigned split",
        "time_protocol": (
            "retrospective daily-close session-order ticks: event/feature at 2*date.toordinal; "
            "prediction at that tick + 1; target event/availability at 2*target_date.toordinal. "
            "This orders daily records but does not verify historical CRSP publication times."
        ),
        "chunk_rows": args.chunk_rows,
    }
    task_specs = [
        {
            "task_id": "crsp_ciz_next_observed_daily_return",
            "task_kind": "regression",
            "target_definition": (
                "The immediately next observed dlyret for the same PERMNO, with its target date. "
                "No observation is skipped to replace a missing or invalid return."
            ),
            "forecast_horizon": {
                "value": 1,
                "unit": "next observed PERMNO record",
                "event_semantics": "target is the next date present for that PERMNO",
            },
            "valid_target_mask": TARGET_QUALITY_RULE,
            "evaluation_metrics": [
                "MSE",
                "RMSE",
                "MAE",
                "90% split-conformal coverage",
                "mean interval width",
            ],
            "label_availability_rule": (
                "Retrospective daily-close ordering convention based on CRSP dates; exact historical "
                "publication/availability times are not supplied by the source."
            ),
            "utility_provenance": "No application-grounded decision utility is supplied.",
        }
    ]
    provenance = {
        "publisher": "CRSP via Wharton Research Data Services (WRDS)",
        "source_url": "https://wrds-www.wharton.upenn.edu/pages/get-data/center-research-security-prices-crsp/",
        "citation": "CRSP Stock Version 2/CIZ Daily Stock File, accessed through WRDS.",
        "license": "WRDS institutional subscription; see source and Columbia agreement.",
        "permitted_use": "Private academic research under the institution's WRDS agreement.",
        "retrieval_parameters": config,
        "raw_checksums": audit["raw_checksums"],
        "feature_names": FEATURES,
        "task_specs": task_specs,
        "limitations": [
            "Retrospective daily close ordering; exact historical feature and label release times are unavailable.",
            "Empirical market regimes are not known causal changepoints.",
            "Decision utility is not supplied; decision-loss claims require an explicit research utility.",
            "Return-quality flags are retained in audit columns; the target mask is conservative and explicit.",
            "Universe is the extracted US common-equity/share/exchange filter; inactive and delisted history remains included.",
        ],
    }
    stats = Counter()
    destination = save_dataset(
        observation_chunks(raw_root, args.chunk_rows, audit, stats),
        "crsp_ciz_next_day",
        args.root,
        provenance,
        config,
    )
    panel_validation = validate_panel(destination)
    manifest = json.loads((destination / "dataset_manifest.json").read_text(encoding="utf-8"))
    if panel_validation["rows"] != manifest["n_observations"]:
        raise ValueError("Panel row count does not match its manifest")
    report = {
        "dataset": manifest["dataset"],
        "version": manifest["version"],
        "dataset_path": str(destination),
        "built_from_source_rows": audit["source_rows"],
        "output_rows": manifest["n_observations"],
        "source_parts_verified": audit["part_count"],
        "raw_part_checksums_verified": True,
        "annual_manifests_verified": 26,
        "target_quality_rule": TARGET_QUALITY_RULE,
        "split_counts": panel_validation["split_counts"],
        "processing_counts": dict(sorted(stats.items())),
        "feature_names": manifest["feature_names"],
        "output_file_checksums": manifest["files"],
        "dataset_manifest_sha256": sha256(destination / "dataset_manifest.json"),
        "builder_script_sha256": config["builder_script_sha256"],
        "observations_parquet_sha256": panel_validation["manifest_file_sha256"],
        "raw_checksums_manifest_sha256": hashlib.sha256(
            json.dumps(audit["raw_checksums"], sort_keys=True).encode()
        ).hexdigest(),
        "limitations": manifest["limitations"],
    }
    report_path = args.root / "reports" / "crsp_study_panel_validation.json"
    write_json(report_path, report)
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "dataset_path",
                    "output_rows",
                    "split_counts",
                    "annual_manifests_verified",
                    "source_parts_verified",
                    "dataset_manifest_sha256",
                ]
            },
            indent=2,
        )
    )
    print(f"Validation report: {report_path}")


if __name__ == "__main__":
    main()
