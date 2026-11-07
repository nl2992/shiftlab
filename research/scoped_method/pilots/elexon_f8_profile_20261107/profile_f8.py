"""Run the frozen 2024-train/2025-development Elexon F8 profile screen."""

from __future__ import annotations

import hashlib
import json
import math
import time
from bisect import bisect_right
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[4]
PILOT = ROOT / "research/scoped_method/pilots/elexon_f8_profile_20261107"
RAW = ROOT / "data/raw/elexon_f8_profile_20261107"
PROFILE = PILOT / "DATASET_PROFILE.json"
BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets/{dataset}/stream"
ATTRIBUTION = "Contains BMRS data © Elexon Limited copyright and database right 2026"
DATASETS = ("ATL", "DATL")
FIRST_PUBLISH = datetime(2023, 12, 1, tzinfo=UTC)
LAST_PUBLISH_EXCLUSIVE = datetime(2025, 12, 30, tzinfo=UTC)
HALF_HOUR = timedelta(minutes=30)
HGB = {
    "max_iter": 150,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "l2_regularization": 1.0,
    "random_state": 1729,
}


def month_windows() -> list[tuple[datetime, datetime]]:
    windows = []
    start = FIRST_PUBLISH
    while start < LAST_PUBLISH_EXCLUSIVE:
        if start.month == 12:
            next_month = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month + 1, day=1)
        end = min(next_month, LAST_PUBLISH_EXCLUSIVE)
        windows.append((start, end))
        start = end
    return windows


def iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_month(dataset: str, start: datetime, end: datetime) -> tuple[bytes, bool]:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{dataset}_{start:%Y%m}.json"
    if path.exists():
        return path.read_bytes(), True
    query = urlencode({"publishDateTimeFrom": iso_utc(start), "publishDateTimeTo": iso_utc(end)})
    url = f"{BASE.format(dataset=dataset)}?{query}"
    request = Request(url, headers={"User-Agent": "ShiftLab-research/1.0"})
    for attempt in range(5):
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
            rows = json.loads(body)
            if not isinstance(rows, list):
                raise TypeError(f"Elexon returned non-list payload: {dataset} {start:%Y-%m}")
            path.write_bytes(body)
            return body, False
        except HTTPError as exc:
            if exc.code != 429 and exc.code < 500:
                raise
            if attempt == 4:
                raise
            time.sleep(2**attempt)
        except (URLError, TimeoutError):
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"Unreachable retry exit: {dataset} {start:%Y-%m}")


def read_records() -> tuple[dict[str, list[dict[str, object]]], list[dict[str, object]]]:
    records: dict[str, list[dict[str, object]]] = {dataset: [] for dataset in DATASETS}
    receipts: list[dict[str, object]] = []
    for dataset in DATASETS:
        for start, end in month_windows():
            body, cached = fetch_month(dataset, start, end)
            rows = json.loads(body)
            start_epoch = start.timestamp()
            end_epoch = end.timestamp()
            kept = 0
            for row in rows:
                publish = datetime.fromisoformat(str(row["publishTime"]))
                if not start_epoch <= publish.timestamp() < end_epoch:
                    continue
                valid = datetime.fromisoformat(str(row["startTime"]))
                if valid >= datetime(2026, 1, 1, tzinfo=UTC):
                    raise RuntimeError(
                        "Response includes a 2026 valid time; refusing to parse outcomes"
                    )
                records[dataset].append(row)
                kept += 1
            receipts.append(
                {
                    "dataset": dataset,
                    "publish_time_window_utc": [iso_utc(start), iso_utc(end)],
                    "response_records": len(rows),
                    "records_in_window": kept,
                    "cached": cached,
                    "response_sha256": hashlib.sha256(body).hexdigest(),
                }
            )
            print(f"{dataset} {start:%Y-%m}: {kept} records", flush=True)
    for dataset in DATASETS:
        unique: dict[tuple[str, str, str, str], dict[str, object]] = {}
        for row in records[dataset]:
            key = (
                str(row["documentId"]),
                str(row["startTime"]),
                str(row["publishTime"]),
                str(row["quantity"]),
            )
            unique[key] = row
        records[dataset] = list(unique.values())
    return records, receipts


def build_versions(
    rows: list[dict[str, object]],
) -> dict[datetime, tuple[list[float], list[float], list[str]]]:
    grouped: dict[datetime, list[tuple[float, float, str]]] = {}
    for row in rows:
        valid = datetime.fromisoformat(str(row["startTime"]))
        publish = datetime.fromisoformat(str(row["publishTime"]))
        grouped.setdefault(valid, []).append(
            (publish.timestamp(), float(str(row["quantity"])), str(row["documentId"]))
        )
    result = {}
    for valid, versions in grouped.items():
        versions.sort(key=lambda item: (item[0], item[2]))
        result[valid] = (
            [item[0] for item in versions],
            [item[1] for item in versions],
            [item[2] for item in versions],
        )
    return result


def value_as_of(
    versions: dict[datetime, tuple[list[float], list[float], list[str]]],
    valid: datetime,
    cutoff_epoch: float,
) -> float | None:
    options = versions.get(valid)
    if options is None:
        return None
    publish_times, quantities, _documents = options
    index = bisect_right(publish_times, cutoff_epoch) - 1
    return quantities[index] if index >= 0 else None


def first_published_labels(
    versions: dict[datetime, tuple[list[float], list[float], list[str]]],
) -> dict[datetime, float]:
    return {valid: quantities[0] for valid, (_pub, quantities, _doc) in versions.items()}


def calendar_features(target: datetime) -> list[float]:
    hour = target.hour + target.minute / 60
    weekday = target.weekday()
    yearday = target.timetuple().tm_yday
    return [
        math.sin(2 * math.pi * hour / 24),
        math.cos(2 * math.pi * hour / 24),
        math.sin(2 * math.pi * weekday / 7),
        math.cos(2 * math.pi * weekday / 7),
        math.sin(2 * math.pi * yearday / 366),
        math.cos(2 * math.pi * yearday / 366),
    ]


def make_features(
    targets: list[datetime],
    forecast_versions: dict[datetime, tuple[list[float], list[float], list[str]]],
    actual_versions: dict[datetime, tuple[list[float], list[float], list[str]]],
) -> tuple[list[datetime], np.ndarray, dict[str, int]]:
    actual_times = sorted(actual_versions)
    eligible_targets: list[datetime] = []
    feature_rows: list[list[float]] = []
    excluded = {"missing_asof_forecast": 0, "missing_mature_actual_history": 0}
    for target in targets:
        cutoff = target - timedelta(hours=12)
        cutoff_epoch = cutoff.timestamp()
        forecast = value_as_of(forecast_versions, target, cutoff_epoch)
        if forecast is None:
            excluded["missing_asof_forecast"] += 1
            continue
        actual_index = bisect_right(actual_times, cutoff) - 1
        while (
            actual_index >= 0
            and value_as_of(actual_versions, actual_times[actual_index], cutoff_epoch) is None
        ):
            actual_index -= 1
        if actual_index < 335:
            excluded["missing_mature_actual_history"] += 1
            continue
        latest_actual_time = actual_times[actual_index]
        needed_offsets = sorted(set(range(48)) | {335})
        history_by_offset: dict[int, float] = {}
        for offset in needed_offsets:
            value = value_as_of(
                actual_versions,
                latest_actual_time - HALF_HOUR * offset,
                cutoff_epoch,
            )
            if value is None:
                break
            history_by_offset[offset] = value
        if len(history_by_offset) != len(needed_offsets):
            excluded["missing_mature_actual_history"] += 1
            continue
        past_values = [history_by_offset[offset] for offset in range(48)]
        one = history_by_offset[0]
        day = history_by_offset[47]
        week = history_by_offset[335]
        feature_rows.append(
            [forecast, one, day, week, float(np.mean(past_values)), max(past_values)]
            + calendar_features(target)
        )
        eligible_targets.append(target)
    return eligible_targets, np.asarray(feature_rows, dtype=np.float64), excluded


def event_grid(start: datetime, end_exclusive: datetime) -> list[datetime]:
    values = []
    current = start
    while current < end_exclusive:
        values.append(current)
        current += HALF_HOUR
    return values


def main() -> None:
    if PROFILE.exists():
        raise SystemExit(f"Refusing to overwrite existing profile: {PROFILE}")
    print(
        "Fetching only publish-time windows from 2023-12-01 through 2025-12-30T00:00Z", flush=True
    )
    records, receipts = read_records()
    actual_versions = build_versions(records["ATL"])
    forecast_versions = build_versions(records["DATL"])
    labels = first_published_labels(actual_versions)

    train_start = datetime(2024, 1, 1, tzinfo=UTC)
    train_end = datetime(2025, 1, 1, tzinfo=UTC)
    dev_start = train_end
    dev_end = datetime(2025, 12, 30, tzinfo=UTC)
    train_grid = event_grid(train_start, train_end)
    dev_grid = event_grid(dev_start, dev_end)
    train_targets, x_train, train_excluded = make_features(
        train_grid, forecast_versions, actual_versions
    )
    dev_targets, x_dev, dev_excluded = make_features(dev_grid, forecast_versions, actual_versions)
    train_labels = np.asarray([labels[t] for t in train_targets], dtype=np.float64)
    threshold = float(np.quantile(train_labels, 0.90))
    y_train = (train_labels > threshold).astype(np.int8)
    if np.unique(y_train).size != 2:
        raise RuntimeError("2024 training targets do not contain both classes")
    with threadpool_limits(limits=1, user_api="openmp"):
        model = HistGradientBoostingClassifier(**HGB)
        model.fit(x_train, y_train, sample_weight=compute_sample_weight("balanced", y_train))

    dev_labels = np.asarray([labels[t] for t in dev_targets], dtype=np.float64)
    y_dev = (dev_labels > threshold).astype(np.int8)
    incumbent_values = []
    for target in dev_targets:
        value = value_as_of(forecast_versions, target, (target - timedelta(hours=12)).timestamp())
        if value is None:
            raise RuntimeError("Eligible development row lost its as-of forecast")
        incumbent_values.append(value)
    incumbent = np.asarray([value > threshold for value in incumbent_values], dtype=np.int8)
    challenger = (model.predict_proba(x_dev)[:, 1] >= 0.5).astype(np.int8)
    half_results = {}
    for name, start, end in (
        ("2025_H1", dev_start, datetime(2025, 7, 1, tzinfo=UTC)),
        ("2025_H2", datetime(2025, 7, 1, tzinfo=UTC), dev_end),
    ):
        ix = np.asarray([start <= target < end for target in dev_targets])
        disagreement = incumbent[ix] != challenger[ix]
        count = int(disagreement.sum())
        rate = float(disagreement.mean()) if len(disagreement) else None
        accuracy = (
            float((challenger[ix][disagreement] == y_dev[ix][disagreement]).mean())
            if count
            else None
        )
        blocks = int(ix.sum()) // 2000
        profile_match = bool(
            rate is not None and 0.01 <= rate <= 0.05 and accuracy is not None and accuracy >= 0.85
        )
        half_results[name] = {
            "eligible_events": int(ix.sum()),
            "disagreement_count": count,
            "disagreement_rate": rate,
            "challenger_accuracy_on_disagreements": accuracy,
            "complete_nonoverlap_2000_event_blocks": blocks,
            "profile_match": profile_match,
            "minimum_blocks_pass": blocks >= 4,
        }
    overall_pass = all(
        item["profile_match"] and item["minimum_blocks_pass"] for item in half_results.values()
    )

    duplicate_valids = {
        dataset: sum(len(v[0]) > 1 for v in build_versions(records[dataset]).values())
        for dataset in DATASETS
    }
    result = {
        "protocol": "research/scoped_method/pilots/elexon_f8_profile_20261107/PROTOCOL.md",
        "status": "development_profile_only",
        "source": "Elexon BMRS ATL and DATL; one GB system operator/source cluster",
        "source_attribution": ATTRIBUTION,
        "source_licence": "https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/",
        "publication_query_boundary_utc": [iso_utc(FIRST_PUBLISH), iso_utc(LAST_PUBLISH_EXCLUSIVE)],
        "response_receipts": receipts,
        "response_count": len(receipts),
        "total_records_by_dataset": {name: len(rows) for name, rows in records.items()},
        "duplicate_valid_times_with_multiple_documents": duplicate_valids,
        "target_registry": {
            "train": [iso_utc(train_start), iso_utc(train_end)],
            "development": [iso_utc(dev_start), iso_utc(dev_end)],
            "2026_outcomes_read": False,
            "model_fit_rows": len(train_targets),
            "profile_rows": len(dev_targets),
            "train_exclusions": train_excluded,
            "development_exclusions": dev_excluded,
            "threshold_definition": "90th percentile of first-published 2024 ATL labels",
            "threshold_value_withheld": True,
            "issue_time": "target startTime minus 12 hours UTC",
            "forecast_vintage": "latest DATL document with publishTime <= issue time",
            "actual_feature_vintage": "latest ATL document for each past valid time with publishTime <= issue time",
            "policy_label": "first ATL publication per target valid time",
        },
        "model": {
            "class": "HistGradientBoostingClassifier",
            "parameters": HGB,
            "features": [
                "as-of DATL forecast",
                "as-of ATL lags 1, 48, 336 half-hour valid periods",
                "48-period trailing ATL mean and maximum, using as-of records",
                "fixed UTC cyclical hour, weekday, and day-of-year encodings",
            ],
            "training_rows": len(train_targets),
            "positive_rate_training": float(y_train.mean()),
        },
        "half_year_results": half_results,
        "profile_screen_pass": overall_pass,
        "interpretation": "F8 prediction-profile screen only; no adaptation policy cost comparison or 2026 outcomes evaluated",
        "limitation": "A single operator and two chronological halves do not establish independent source-level generalization.",
    }
    PROFILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    report = [
        "# Elexon F8 profile screen — development only",
        "",
        f"**Profile gate: {'PASS' if overall_pass else 'FAIL'}.** This is a 2024-train / 2025-development profile screen; it is not a policy-cost experiment or independent confirmation.",
        "",
        "Contains BMRS data © Elexon Limited copyright and database right 2026. Source: [Elexon BMRS](https://bmrs.elexon.co.uk/). [Data licence](https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/).",
        "",
        "| Half-year | Eligible events | Disagreement | Challenger accuracy on disagreement | 2,000-event blocks | Profile gate |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, item in half_results.items():
        report.append(
            f"| {name} | {item['eligible_events']} | {item['disagreement_rate']:.3%} | {item['challenger_accuracy_on_disagreements']:.3%} | {item['complete_nonoverlap_2000_event_blocks']} | {'PASS' if item['profile_match'] and item['minimum_blocks_pass'] else 'FAIL'} |"
        )
    report.extend(
        [
            "",
            f"Records read: ATL {len(records['ATL']):,}; DATL {len(records['DATL']):,}. Publication-window receipts and response SHA-256 values are in `DATASET_PROFILE.json`; quantity values and row-level outcomes remain in ignored `data/raw/`. The request boundary ended at 2025-12-30 00:00 UTC, and the program rejects any response containing a 2026 valid time.",
            "",
            f"Duplicate valid times with multiple publications/documents: ATL {duplicate_valids['ATL']}; DATL {duplicate_valids['DATL']}. Vintage selection uses the latest publication available at issue time; labels use first publication.",
            "",
            "**Interpretation:** the method here is the standard validation-selected fixed-challenger rule. A passing profile would show that Elexon 2025 contains an F8-like model-pair stream, not that a new algorithm transfers or that deploying the challenger is economically beneficial. Keep the 2026 period closed unless a separately frozen case-study decision permits it; one operator remains one source cluster.",
        ]
    )
    (PILOT / "RUN_STATUS.md").write_text("\n".join(report) + "\n")
    print(
        json.dumps(
            {"profile_screen_pass": overall_pass, "half_year_results": half_results}, indent=2
        )
    )


if __name__ == "__main__":
    main()
