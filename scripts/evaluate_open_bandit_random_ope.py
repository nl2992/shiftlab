"""Evaluate the official Random policy from the full OBD BTS logger.

This reproduces a minimal logged-bandit OPE comparison: IPS and SNIPS estimate
the Random policy's click value from Bernoulli-TS logged actions, then compare
with the on-policy Random click rate. It is a descriptive point-estimation
benchmark, not an anytime-valid or confirmatory result.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "data/raw/open_bandit_dataset_full.zip"
DEFAULT_SOURCE_MANIFEST = ROOT / "data/reports/open_bandit_full_acquisition_manifest.json"
DEFAULT_OUTPUT = (
    ROOT / "outputs/shiftguard_unified/real_data_development/open_bandit_random_policy_ope_v2"
)
MEMBER = "open_bandit_dataset/bts/all/all.csv"
EXPECTED_ROWS = 12_357_200
N_ITEMS = 80
RANDOM_PROPENSITY = 1.0 / N_ITEMS
CHUNK_ROWS = 250_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_bts(archive: zipfile.ZipFile) -> tuple[dict[str, Any], dict[str, Any]]:
    member_info = archive.getinfo(MEMBER)
    by_position: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "clicks": 0,
            "sum_weight": 0.0,
            "sum_weight_click": 0.0,
            "sum_weight_sq": 0.0,
            "weight_max": 0.0,
            "propensity_min": float("inf"),
            "items": set(),
        }
    )
    by_day_position: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "clicks": 0,
            "sum_weight": 0.0,
            "sum_weight_click": 0.0,
            "sum_weight_sq": 0.0,
        }
    )
    n = 0
    missing = 0
    p_min = float("inf")
    p_max = 0.0
    with archive.open(MEMBER) as source:
        reader = pd.read_csv(
            source,
            usecols=["timestamp", "item_id", "position", "click", "propensity_score"],
            chunksize=CHUNK_ROWS,
        )
        try:
            for chunk in reader:
                missing += int(chunk.isna().sum().sum())
                position = pd.to_numeric(chunk["position"], errors="raise")
                item = pd.to_numeric(chunk["item_id"], errors="raise")
                click = pd.to_numeric(chunk["click"], errors="raise")
                propensity = pd.to_numeric(chunk["propensity_score"], errors="raise")
                if not click.isin([0, 1]).all():
                    raise RuntimeError("BTS click field is not binary")
                if (propensity <= 0).any() or (propensity > 1).any():
                    raise RuntimeError("BTS logged propensity is outside (0, 1]")
                if not position.isin([1, 2, 3]).all():
                    raise RuntimeError("BTS contains an unexpected display position")
                if not item.between(0, N_ITEMS - 1).all():
                    raise RuntimeError("BTS item ID is outside the all-campaign action set")
                times = pd.to_datetime(
                    chunk["timestamp"], errors="coerce", utc=True, format="mixed"
                )
                if times.isna().any():
                    raise RuntimeError("BTS has an unparseable UTC impression timestamp")

                weights = RANDOM_PROPENSITY / propensity.to_numpy(dtype=np.float64)
                click_array = click.to_numpy(dtype=np.float64)
                dates = times.dt.strftime("%Y-%m-%d")
                audit = pd.DataFrame(
                    {
                        "date": dates,
                        "position": position.to_numpy(dtype=np.int64),
                        "item_id": item.to_numpy(dtype=np.int64),
                        "click": click_array,
                        "weight": weights,
                        "propensity": propensity.to_numpy(dtype=np.float64),
                    }
                )
                grouped = audit.groupby("position", sort=False)
                for pos, group in grouped:
                    key = str(int(pos))
                    slot = by_position[key]
                    slot["rows"] += len(group)
                    slot["clicks"] += int(group["click"].sum())
                    slot["sum_weight"] += float(group["weight"].sum())
                    slot["sum_weight_click"] += float((group["weight"] * group["click"]).sum())
                    slot["sum_weight_sq"] += float(np.square(group["weight"]).sum())
                    slot["weight_max"] = max(slot["weight_max"], float(group["weight"].max()))
                    slot["propensity_min"] = min(
                        slot["propensity_min"], float(group["propensity"].min())
                    )
                    slot["items"].update(int(value) for value in group["item_id"].unique())
                grouped_day = audit.groupby(["date", "position"], sort=False)
                for (date, pos), group in grouped_day:
                    key = f"{date}|{int(pos)}"
                    slot = by_day_position[key]
                    slot["rows"] += len(group)
                    slot["clicks"] += int(group["click"].sum())
                    slot["sum_weight"] += float(group["weight"].sum())
                    slot["sum_weight_click"] += float((group["weight"] * group["click"]).sum())
                    slot["sum_weight_sq"] += float(np.square(group["weight"]).sum())
                n += len(chunk)
                p_min = min(p_min, float(propensity.min()))
                p_max = max(p_max, float(propensity.max()))
        finally:
            reader.close()
    if n != EXPECTED_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_ROWS} BTS archive rows, found {n}")
    if missing:
        raise RuntimeError(f"BTS required fields contain {missing} missing cells")
    result = {
        "rows": n,
        "source_member_uncompressed_bytes": member_info.file_size,
        "source_member_compressed_bytes": member_info.compress_size,
        "propensity_min": p_min,
        "propensity_max": p_max,
        "observed_importance_weight_max": RANDOM_PROPENSITY / p_min,
        "by_position": by_position,
    }
    return result, by_day_position


def run(archive_path: Path, source_manifest_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    if not archive_path.is_file() or not source_manifest_path.is_file():
        raise FileNotFoundError("Full archive and its acquisition manifest are required")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    archive_hash = sha256(archive_path)
    if source_manifest["source"]["archive_sha256"] != archive_hash:
        raise RuntimeError("Archive hash does not match its acquisition manifest")
    random = source_manifest["random_all"]
    if random["rows"] != 1_374_327:
        raise RuntimeError("Random/all row count does not match the acquisition manifest")
    if (
        random["propensity_min"] != RANDOM_PROPENSITY
        or random["propensity_max"] != RANDOM_PROPENSITY
    ):
        raise RuntimeError("Random logger propensity is not the documented uniform 1/80")

    with zipfile.ZipFile(archive_path) as archive:
        bts, daily = scan_bts(archive)
        readme = archive.read("open_bandit_dataset/README").decode("utf-8")
        version = archive.read("open_bandit_dataset/VERSION").decode("utf-8").strip()
    if "CC BY 4.0" not in readme:
        raise RuntimeError("Full archive README did not confirm CC BY 4.0")

    position_rows: list[dict[str, Any]] = []
    for position, bts_stats in sorted(bts["by_position"].items()):
        random_stats = random["by_position"][position]
        n_bts = bts_stats["rows"]
        ips = bts_stats["sum_weight_click"] / n_bts
        snips = bts_stats["sum_weight_click"] / bts_stats["sum_weight"]
        on_policy = random_stats["clicks"] / random_stats["rows"]
        position_rows.append(
            {
                "position": int(position),
                "bts_rows": n_bts,
                "bts_click_rate": bts_stats["clicks"] / n_bts,
                "random_on_policy_click_rate": on_policy,
                "ips_random_value_from_bts": ips,
                "snips_random_value_from_bts": snips,
                "ips_absolute_error_vs_random": abs(ips - on_policy),
                "snips_absolute_error_vs_random": abs(snips - on_policy),
                "ips_relative_error_vs_random": abs(ips - on_policy) / on_policy,
                "snips_relative_error_vs_random": abs(snips - on_policy) / on_policy,
                "importance_weight_ess": bts_stats["sum_weight"] ** 2 / bts_stats["sum_weight_sq"],
                "importance_weight_ess_fraction": (
                    bts_stats["sum_weight"] ** 2 / bts_stats["sum_weight_sq"] / n_bts
                ),
                "observed_items": len(bts_stats["items"]),
                "observed_propensity_min": bts_stats["propensity_min"],
                "observed_weight_max": bts_stats["weight_max"],
            }
        )
    if len(position_rows) != 3:
        raise RuntimeError("Expected one result for each of the three display positions")

    overall = {
        "random_on_policy_click_rate": float(
            np.mean([row["random_on_policy_click_rate"] for row in position_rows])
        ),
        "ips_random_value_from_bts": float(
            np.mean([row["ips_random_value_from_bts"] for row in position_rows])
        ),
        "snips_random_value_from_bts": float(
            np.mean([row["snips_random_value_from_bts"] for row in position_rows])
        ),
    }
    overall["ips_absolute_error"] = abs(
        overall["ips_random_value_from_bts"] - overall["random_on_policy_click_rate"]
    )
    overall["snips_absolute_error"] = abs(
        overall["snips_random_value_from_bts"] - overall["random_on_policy_click_rate"]
    )
    overall["ips_relative_error"] = (
        overall["ips_absolute_error"] / overall["random_on_policy_click_rate"]
    )
    overall["snips_relative_error"] = (
        overall["snips_absolute_error"] / overall["random_on_policy_click_rate"]
    )

    output.mkdir(parents=True)
    metrics_path = output / "position_metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(position_rows[0]))
        writer.writeheader()
        writer.writerows(position_rows)

    random_daily_position = pd.read_parquet(
        ROOT / random["parquet_path"], columns=["timestamp", "position", "click"]
    )
    random_daily_position["date_utc"] = pd.to_datetime(
        random_daily_position["timestamp"], utc=True, errors="raise"
    ).dt.strftime("%Y-%m-%d")
    random_daily_position = random_daily_position.groupby(
        ["date_utc", "position"], as_index=False
    ).agg(random_rows=("click", "size"), random_clicks=("click", "sum"))
    if int(random_daily_position["random_rows"].sum()) != random["rows"]:
        raise RuntimeError("Daily Random position counts do not match the source manifest")
    random_daily_index = random_daily_position.set_index(["date_utc", "position"])

    day_rows: list[dict[str, Any]] = []
    for key, values in sorted(daily.items()):
        date, position = key.split("|")
        random_values = random_daily_index.loc[(date, int(position))]
        n_bts = values["rows"]
        random_rate = float(random_values["random_clicks"] / random_values["random_rows"])
        day_ips = float(values["sum_weight_click"] / n_bts)
        day_snips = float(values["sum_weight_click"] / values["sum_weight"])
        day_rows.append(
            {
                "date_utc": date,
                "position": int(position),
                "bts_rows": n_bts,
                "bts_clicks": values["clicks"],
                "bts_click_rate": values["clicks"] / values["rows"],
                "random_rows": int(random_values["random_rows"]),
                "random_clicks": int(random_values["random_clicks"]),
                "random_on_policy_click_rate": random_rate,
                "ips_random_value_from_bts": day_ips,
                "snips_random_value_from_bts": day_snips,
                "ips_absolute_error_vs_random": abs(day_ips - random_rate),
                "snips_absolute_error_vs_random": abs(day_snips - random_rate),
                "importance_weight_ess": (values["sum_weight"] ** 2 / values["sum_weight_sq"]),
                "importance_weight_ess_fraction": (
                    values["sum_weight"] ** 2 / values["sum_weight_sq"] / n_bts
                ),
            }
        )
    daily_path = output / "bts_daily_position_metrics.csv"
    with daily_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(day_rows[0]))
        writer.writeheader()
        writer.writerows(day_rows)

    result = {
        "schema_version": "1.0.0",
        "status": "full_archive_descriptive_ope_development_not_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "publisher": "ZOZO Research / ZOZO, Inc.",
            "paper": "Saito et al. (2021), Open Bandit Dataset and Pipeline, arXiv:2008.07146",
            "archive_version": version,
            "license": "CC BY 4.0; cite the OBD paper",
            "archive_path": archive_path.relative_to(ROOT).as_posix(),
            "archive_sha256": archive_hash,
            "source_manifest_sha256": sha256(source_manifest_path),
            "bts_source_member": MEMBER,
            "random_manifest_path": source_manifest_path.relative_to(ROOT).as_posix(),
        },
        "protocol": {
            "target_policy": "uniform Random policy, probability 1/80 for each item at each position",
            "behavior_policy": "Bernoulli Thompson Sampling (BTS), observed item-position propensity from source log",
            "estimand": "mean binary click reward per item-position impression, equal-weight average across positions 1, 2, 3",
            "estimators": ["IPS", "SNIPS"],
            "comparison": "position-specific OPE values versus the full Random/all on-policy position click rates",
            "position_stratification": "predeclared to respect source reward and propensity definitions by display slot",
            "paper_reported_bts_rows": 12_168_084,
            "archive_streamed_bts_rows": bts["rows"],
            "bts_count_discrepancy": bts["rows"] - 12_168_084,
        },
        "results": {"overall": overall, "by_position": position_rows},
        "diagnostics": {
            "bts_archive_rows": bts["rows"],
            "random_archive_rows": random["rows"],
            "bts_observed_propensity_min": bts["propensity_min"],
            "bts_observed_propensity_max": bts["propensity_max"],
            "bts_observed_weight_max": bts["observed_importance_weight_max"],
            "bts_member_uncompressed_bytes": bts["source_member_uncompressed_bytes"],
            "bts_member_compressed_bytes": bts["source_member_compressed_bytes"],
            "bts_days": len({key.split("|")[0] for key in daily}),
            "source_archive_total_uncompressed_bytes": source_manifest["source"][
                "full_archive_uncompressed_bytes"
            ],
        },
        "compute": {
            "selected_device": "cpu",
            "reason": (
                "The workload is compressed CSV streaming, parsing, and low-cardinality "
                "aggregation; it has no model training or large tensor operation for CUDA."
            ),
        },
        "limitations": [
            "Point estimates and observed-weight diagnostics only; no confidence interval or sequential guarantee is reported.",
            "The 2020 archive has 189,116 more BTS/all records than the count in the OBD paper; resolve the version difference before claiming exact paper reproduction.",
            "The OPE calculation follows the paper's per-impression and item-position reward assumption; it does not identify business value or user welfare.",
            "The source exposes no user/session key, and impression timestamps are not click-release times; dependence and prospective feedback timing are not established.",
            "Observed positive propensity values do not alone certify population-wide action support; do not use the observed minimum as a theoretical global bound.",
            "No candidate was learned or selected here; this is an OPE estimator reproduction only, not a model-adaptation result.",
        ],
        "artifacts": {
            "position_metrics_csv": metrics_path.relative_to(ROOT).as_posix(),
            "position_metrics_sha256": sha256(metrics_path),
            "bts_daily_position_metrics_csv": daily_path.relative_to(ROOT).as_posix(),
            "bts_daily_position_metrics_sha256": sha256(daily_path),
            "runner_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "runner_sha256": sha256(Path(__file__).resolve()),
            "runtime": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.archive, args.source_manifest, args.output)
    print(
        json.dumps(
            {
                "status": result["status"],
                **result["results"]["overall"],
                "bts_archive_rows": result["diagnostics"]["bts_archive_rows"],
                "manifest": str(args.output / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
