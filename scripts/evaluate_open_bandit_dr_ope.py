"""Run cross-fitted DM/IPS/SNIPS/DR on full Open Bandit BTS/all.

The reward model uses only item and position, matching the OBD paper's
item-position reward assumption. It estimates action-position click means on
the opposite half of a fixed random two-fold split. All results are descriptive
point estimates against the concurrently observed Random/all policy value.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import platform
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "data/raw/open_bandit_dataset_full.zip"
DEFAULT_SOURCE_MANIFEST = ROOT / "data/reports/open_bandit_full_acquisition_manifest.json"
DEFAULT_OBP_SOURCE = ROOT / "tmp/obp_reference"
DEFAULT_OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/open_bandit_dr_ope_v1"
MEMBER = "open_bandit_dataset/bts/all/all.csv"
EXPECTED_ROWS = 12_357_200
N_ITEMS = 80
N_POSITIONS = 3
N_FOLDS = 2
TARGET_PROBABILITY = 1.0 / N_ITEMS
SPLIT_SEED = 20261026
CHUNK_ROWS = 250_000
EXPECTED_OBP_COMMIT = "8cbd5fa4558b7ad2ba4781546d6604e4cc3e07c4"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_official_dr_formula(source: Path) -> dict[str, Any]:
    if not source.is_dir():
        raise FileNotFoundError(
            f"Pinned official OBP source is required at {source}; see the reproduction instructions"
        )
    commit = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != EXPECTED_OBP_COMMIT:
        raise RuntimeError(f"Expected OBP commit {EXPECTED_OBP_COMMIT}, found {commit}")
    estimator_file = source / "obp/ope/estimators.py"
    if not estimator_file.is_file():
        raise FileNotFoundError(estimator_file)
    sys.path.insert(0, str(source.resolve()))
    official_dr = importlib.import_module("obp.ope").DoublyRobust

    # A tiny deterministic case checks the streamed sufficient-statistic formula
    # against the pinned authors' actual estimate_policy_value implementation.
    n, n_actions, n_positions = 4, 3, 2
    action = np.asarray([0, 2, 1, 0], dtype=np.int64)
    position = np.asarray([0, 0, 1, 1], dtype=np.int64)
    reward = np.asarray([1.0, 0.0, 1.0, 0.0])
    pscore = np.asarray([0.3, 0.2, 0.7, 0.4])
    q_hat = np.random.default_rng(12).uniform(0.1, 0.8, size=(n, n_actions, n_positions))
    action_dist = np.full((n, n_actions, n_positions), 1.0 / n_actions)
    q_observed = q_hat[np.arange(n), action, position]
    direct = (action_dist * q_hat).sum(axis=1)[np.arange(n), position].mean()
    ours = float(
        direct
        + np.mean(action_dist[np.arange(n), action, position] / pscore * (reward - q_observed))
    )
    official = float(
        official_dr().estimate_policy_value(
            reward=reward,
            action=action,
            pscore=pscore,
            action_dist=action_dist,
            estimated_rewards_by_reg_model=q_hat,
            position=position,
        )
    )
    max_abs_diff = abs(ours - official)
    if max_abs_diff > 1e-12:
        raise RuntimeError(f"DR formula mismatch against pinned OBP source: {max_abs_diff}")
    return {
        "repository": "https://github.com/st-tech/zr-obp",
        "commit": commit,
        "estimator": "obp.ope.DoublyRobust.estimate_policy_value",
        "estimator_source_path": "obp/ope/estimators.py",
        "estimator_source_sha256": sha256(estimator_file),
        "small_case_max_absolute_difference": max_abs_diff,
    }


def _bincount(values: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    return np.bincount(values, weights=weights, minlength=N_ITEMS * N_POSITIONS).reshape(
        N_ITEMS, N_POSITIONS
    )


def scan_bts(archive_path: Path) -> tuple[np.ndarray, ...]:
    fold_rows = np.zeros((N_FOLDS, N_ITEMS, N_POSITIONS), dtype=np.int64)
    fold_clicks = np.zeros_like(fold_rows)
    fold_weight = np.zeros((N_FOLDS, N_ITEMS, N_POSITIONS), dtype=np.float64)
    fold_weight_click = np.zeros_like(fold_weight)
    fold_weight_sq = np.zeros_like(fold_weight)
    rng = np.random.default_rng(SPLIT_SEED)
    total_rows = 0
    missing_cells = 0
    with zipfile.ZipFile(archive_path) as archive:
        if archive.getinfo(MEMBER).file_size <= 0:
            raise RuntimeError("BTS/all archive member is empty")
        with archive.open(MEMBER) as source:
            reader = pd.read_csv(
                source,
                usecols=["item_id", "position", "click", "propensity_score"],
                chunksize=CHUNK_ROWS,
            )
            try:
                for chunk in reader:
                    missing_cells += int(chunk.isna().sum().sum())
                    item = pd.to_numeric(chunk["item_id"], errors="raise").to_numpy(dtype=np.int64)
                    position = (
                        pd.to_numeric(chunk["position"], errors="raise").to_numpy(dtype=np.int64)
                        - 1
                    )
                    click = pd.to_numeric(chunk["click"], errors="raise").to_numpy(dtype=np.int64)
                    propensity = pd.to_numeric(chunk["propensity_score"], errors="raise").to_numpy(
                        dtype=np.float64
                    )
                    if not np.isin(click, [0, 1]).all():
                        raise RuntimeError("BTS click is not binary")
                    if not np.isin(position, [0, 1, 2]).all():
                        raise RuntimeError("BTS contains an unexpected display position")
                    if not np.isin(item, np.arange(N_ITEMS)).all():
                        raise RuntimeError("BTS item ID is outside the all-campaign action set")
                    if (propensity <= 0.0).any() or (propensity > 1.0).any():
                        raise RuntimeError("BTS propensity is outside (0, 1]")

                    fold = rng.integers(0, N_FOLDS, size=len(chunk), dtype=np.int8)
                    cell = item * N_POSITIONS + position
                    weight = TARGET_PROBABILITY / propensity
                    for fold_id in range(N_FOLDS):
                        mask = fold == fold_id
                        cells = cell[mask]
                        clicks = click[mask]
                        weights = weight[mask]
                        fold_rows[fold_id] += _bincount(cells).astype(np.int64)
                        fold_clicks[fold_id] += _bincount(cells, clicks.astype(np.float64)).astype(
                            np.int64
                        )
                        fold_weight[fold_id] += _bincount(cells, weights)
                        fold_weight_click[fold_id] += _bincount(cells, weights * clicks)
                        fold_weight_sq[fold_id] += _bincount(cells, np.square(weights))
                    total_rows += len(chunk)
            finally:
                reader.close()
    if total_rows != EXPECTED_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_ROWS} BTS rows, found {total_rows}")
    if missing_cells:
        raise RuntimeError(f"BTS required columns contain {missing_cells} missing values")
    if (fold_rows.sum(axis=0) == 0).any():
        raise RuntimeError("At least one item-position pair is absent from BTS")
    return fold_rows, fold_clicks, fold_weight, fold_weight_click, fold_weight_sq


def random_reference(source_manifest_path: Path) -> dict[str, Any]:
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    random_info = source_manifest["random_all"]
    parquet_path = ROOT / random_info["parquet_path"]
    if sha256(parquet_path) != random_info["parquet_sha256"]:
        raise RuntimeError("Random/all Parquet checksum does not match its source manifest")
    frame = pd.read_parquet(parquet_path, columns=["position", "click"])
    rates = frame.groupby("position")["click"].mean().to_dict()
    counts = frame.groupby("position")["click"].agg(["size", "sum"]).to_dict("index")
    return {
        "rows": len(frame),
        "by_position": {
            str(int(position)): {
                "rows": int(values["size"]),
                "clicks": int(values["sum"]),
                "click_rate": float(rates[position]),
            }
            for position, values in counts.items()
        },
        "parquet_sha256": random_info["parquet_sha256"],
    }


def estimate(
    fold_rows: np.ndarray,
    fold_clicks: np.ndarray,
    fold_weight: np.ndarray,
    fold_weight_click: np.ndarray,
    fold_weight_sq: np.ndarray,
    random: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rows_by_position: list[dict[str, Any]] = []
    for position in range(N_POSITIONS):
        eval_n = fold_rows[:, :, position].sum(axis=1).astype(np.float64)
        total_n = float(eval_n.sum())
        dm_numerator = 0.0
        residual_numerator = 0.0
        ips_numerator = 0.0
        eval_weight_total = 0.0
        weight_sq_total = 0.0
        brier_numerator = 0.0
        for evaluation_fold in range(N_FOLDS):
            training_fold = 1 - evaluation_fold
            training_rows = fold_rows[training_fold, :, position]
            training_clicks = fold_clicks[training_fold, :, position]
            if (training_rows == 0).any():
                raise RuntimeError("Cross-fit training fold lacks item-position support")
            q_hat = training_clicks / training_rows
            direct_value = float(q_hat.mean())
            observed_rows = fold_rows[evaluation_fold, :, position]
            observed_clicks = fold_clicks[evaluation_fold, :, position]
            weights = fold_weight[evaluation_fold, :, position]
            weighted_clicks = fold_weight_click[evaluation_fold, :, position]
            weight_squares = fold_weight_sq[evaluation_fold, :, position]
            dm_numerator += eval_n[evaluation_fold] * direct_value
            residual_numerator += float(np.sum(weighted_clicks - weights * q_hat))
            ips_numerator += float(weighted_clicks.sum())
            eval_weight_total += float(weights.sum())
            weight_sq_total += float(weight_squares.sum())
            brier_numerator += float(
                np.sum(
                    observed_rows * np.square(q_hat)
                    - 2.0 * q_hat * observed_clicks
                    + observed_clicks
                )
            )
        random_stats = random["by_position"][str(position + 1)]
        dm_value = dm_numerator / total_n
        ips_value = ips_numerator / total_n
        snips_value = ips_numerator / eval_weight_total if eval_weight_total else float("nan")
        dr_value = (dm_numerator + residual_numerator) / total_n
        rows_by_position.append(
            {
                "position": position + 1,
                "bts_eval_rows": int(total_n),
                "random_reference_rows": random_stats["rows"],
                "random_on_policy_click_rate": random_stats["click_rate"],
                "bts_direct_method": dm_value,
                "bts_ips": ips_value,
                "bts_snips": snips_value,
                "bts_doubly_robust": dr_value,
                "dm_abs_error_vs_random": abs(dm_value - random_stats["click_rate"]),
                "ips_abs_error_vs_random": abs(ips_value - random_stats["click_rate"]),
                "snips_abs_error_vs_random": abs(snips_value - random_stats["click_rate"]),
                "dr_abs_error_vs_random": abs(dr_value - random_stats["click_rate"]),
                "ips_weight_ess": eval_weight_total**2 / weight_sq_total,
                "ips_weight_ess_fraction": eval_weight_total**2 / weight_sq_total / total_n,
                "crossfit_reward_model_brier": brier_numerator / total_n,
            }
        )
    estimator_names = (
        "random_on_policy_click_rate",
        "bts_direct_method",
        "bts_ips",
        "bts_snips",
        "bts_doubly_robust",
    )
    overall = {
        name: float(np.mean([row[name] for row in rows_by_position])) for name in estimator_names
    }
    for estimator in ("bts_direct_method", "bts_ips", "bts_snips", "bts_doubly_robust"):
        overall[f"{estimator}_absolute_error"] = abs(
            overall[estimator] - overall["random_on_policy_click_rate"]
        )
        overall[f"{estimator}_relative_error"] = (
            overall[f"{estimator}_absolute_error"] / overall["random_on_policy_click_rate"]
        )
    return rows_by_position, overall


def run(
    archive_path: Path,
    source_manifest_path: Path,
    obp_source: Path,
    output: Path,
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    if not archive_path.is_file() or not source_manifest_path.is_file():
        raise FileNotFoundError("Full OBD archive and acquisition manifest are required")
    archive_hash = sha256(archive_path)
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source_manifest["source"]["archive_sha256"] != archive_hash:
        raise RuntimeError("Archive checksum does not match acquisition manifest")
    obp = check_official_dr_formula(obp_source)
    random = random_reference(source_manifest_path)
    fold_stats = scan_bts(archive_path)
    position_rows, overall = estimate(*fold_stats, random)
    if len(position_rows) != N_POSITIONS:
        raise RuntimeError("Expected one metric row for each of three positions")

    output.mkdir(parents=True)
    position_metrics = output / "position_metrics.csv"
    with position_metrics.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(position_rows[0]))
        writer.writeheader()
        writer.writerows(position_rows)
    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "full_archive_cross_fitted_ope_development_not_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "publisher": "ZOZO Research / ZOZO, Inc.",
            "archive_version": "08/18/2020 Open Bandit Dataset 1.0",
            "archive_sha256": archive_hash,
            "source_manifest_sha256": sha256(source_manifest_path),
            "bts_source_member": MEMBER,
            "bts_rows": EXPECTED_ROWS,
            "random_rows": random["rows"],
            "random_parquet_sha256": random["parquet_sha256"],
            "paper_reported_bts_rows": 12_168_084,
            "archive_minus_paper_bts_rows": EXPECTED_ROWS - 12_168_084,
        },
        "protocol": {
            "question": "Does a cross-fitted item-position outcome model reduce OPE error for the uniform Random policy compared with IPS/SNIPS?",
            "target_policy": "uniform Random: probability 1/80 for each item at each position",
            "behavior_policy": "Bernoulli Thompson Sampling with recorded propensity_score",
            "estimand": "equal-weight mean of position-specific binary click values for positions 1-3",
            "reward_model": "cross-fitted empirical click mean by item and position; no user affinity feature due unverified as-of semantics",
            "cross_fit": {
                "folds": N_FOLDS,
                "assignment": "row-wise uniform random split",
                "seed": SPLIT_SEED,
            },
            "estimators": ["DM", "IPS", "SNIPS", "DR"],
            "uncertainty": "none; point estimates only",
            "feedback_unit": "item-position impression, following the OBD per-impression assumption",
            "gpu": "not used; streaming CSV reduction and low-dimensional cell estimates are CPU/IO bound",
        },
        "official_reference": obp,
        "results": {"overall_equal_position": overall, "by_position": position_rows},
        "limitations": [
            "This is a ShiftLab adaptation using the official OBP DR formula and a simple item-position reward model, not a full reproduction of the paper's 200-seed estimator benchmark.",
            "The OBD paper assumes a click depends on item and position, while slate interactions may violate that assumption.",
            "No confidence interval is reported; seven days and missing user/session IDs prevent a defensible row-independent uncertainty claim.",
            "The archive has 189,116 more BTS/all rows than the paper table; the current official release does not resolve component-level version lineage.",
            "Click value is not revenue, user welfare, or deployment utility; no candidate policy was selected or promoted.",
            "The observed propensity minimum is not a theoretical global support bound; no sequential guarantee is claimed.",
        ],
        "artifacts": {
            "position_metrics_csv": position_metrics.relative_to(ROOT).as_posix(),
            "position_metrics_sha256": sha256(position_metrics),
            "runner_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "runner_sha256": sha256(Path(__file__).resolve()),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"status": result["status"], **overall, "manifest": str(output / "manifest.json")},
            indent=2,
        )
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--obp-source", type=Path, default=DEFAULT_OBP_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    run(args.archive, args.source_manifest, args.obp_source, args.output)


if __name__ == "__main__":
    main()
