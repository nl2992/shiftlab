"""Run the frozen exploratory MOPE gate on a held-forward OBD Random/all segment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from shiftlab.dive.open_bandit_mope import (
    build_mope_stream,
    choose_best_item,
    fixed_horizon_hoeffding_lower,
    validate_mope_path,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "data/reports/open_bandit_full_acquisition_manifest.json"
PROTOCOL = ROOT / "papers/shiftguard_unified/open_bandit_mope_development_protocol_v1.md"
MOPE_REPO = ROOT / "tmp/mope_reference"
OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/open_bandit_mope_v1"
EXPECTED_MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"
FAST_SOLVER_VALIDATION = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/mope_fast_solver_validation_v2"
    / "reference_qp_and_path_validation.json"
)
EXPECTED_ROWS = 1_374_327
N_ITEMS = 80
TARGET_POSITION = 1
ALPHA = 0.05
WEIGHT_RANGE_WIDTH = 80.0
TRAIN_DATES = {"2019-11-24", "2019-11-25", "2019-11-26"}
EVALUATION_DATES = {"2019-11-27", "2019-11-28", "2019-11-29", "2019-11-30"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_mope(fast_optimizer: bool = False) -> tuple[Any, str, str, str | None]:
    if not (MOPE_REPO / ".git").is_dir():
        raise FileNotFoundError(f"MOPE reference repository is absent: {MOPE_REPO}")
    revision = subprocess.run(
        ["git", "-C", str(MOPE_REPO), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != EXPECTED_MOPE_COMMIT:
        raise RuntimeError(f"Expected MOPE commit {EXPECTED_MOPE_COMMIT}, found {revision}")
    sys.path.insert(0, str(MOPE_REPO))
    tqdm: Any = importlib.import_module("tqdm")
    tqdm.tqdm = lambda iterable, **_kwargs: iterable
    module = importlib.import_module("opebetrp")
    source_path = MOPE_REPO / "opebetrp.py"
    optimizer_hash = None
    if fast_optimizer:
        from fast_mope_optimizer import solve_gd_exact

        validation = json.loads(FAST_SOLVER_VALIDATION.read_text(encoding="utf-8"))
        optimizer_path = Path(__file__).with_name("fast_mope_optimizer.py")
        optimizer_hash = sha256(optimizer_path)
        if validation.get("status") != "passed":
            raise RuntimeError("Fast MOPE optimizer has no passing reference validation")
        if validation.get("fast_solver_file_sha256") != optimizer_hash:
            raise RuntimeError("Fast optimizer differs from the checked validation artifact")
        if validation.get("reference_repository_commit") != EXPECTED_MOPE_COMMIT:
            raise RuntimeError("Fast optimizer validation used an unexpected MOPE revision")
        if validation.get("reference_file_sha256") != sha256(source_path):
            raise RuntimeError("Fast optimizer validation used a different MOPE source file")
        module.solve_gd = solve_gd_exact
    return module.wealth_lb_gd, revision, sha256(source_path), optimizer_hash


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(fast_optimizer: bool = False) -> dict[str, Any]:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {OUTPUT}")
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    random_info = source_manifest["random_all"]
    source_path = ROOT / random_info["parquet_path"]
    source_hash = sha256(source_path)
    if source_hash != random_info["parquet_sha256"]:
        raise RuntimeError("OBD Random/all Parquet hash does not match its source manifest")
    source_manifest_hash = sha256(SOURCE_MANIFEST)
    protocol_hash = sha256(PROTOCOL)

    frame = pd.read_parquet(
        source_path,
        columns=["timestamp", "item_id", "position", "click", "propensity_score"],
    )
    if len(frame) != EXPECTED_ROWS or len(frame) != int(random_info["rows"]):
        raise RuntimeError(
            f"Random/all row count mismatch: expected {EXPECTED_ROWS}, got {len(frame)}"
        )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    frame["date_utc"] = frame["timestamp"].dt.strftime("%Y-%m-%d")
    frame = frame.sort_values("timestamp", kind="mergesort", ignore_index=True)
    if set(frame["date_utc"].unique()) != TRAIN_DATES | EVALUATION_DATES:
        raise RuntimeError("OBD UTC dates differ from the frozen seven-day split")
    if not frame["timestamp"].is_monotonic_increasing:
        raise RuntimeError("Timestamp sort failed")
    if not np.isin(frame["position"].to_numpy(dtype=np.int64), [1, 2, 3]).all():
        raise RuntimeError("Unexpected position value")
    if not np.isin(frame["click"].to_numpy(dtype=np.int64), [0, 1]).all():
        raise RuntimeError("Click reward is not binary")
    if not np.allclose(
        frame["propensity_score"].to_numpy(dtype=np.float64), 1.0 / N_ITEMS, rtol=0.0, atol=1e-12
    ):
        raise RuntimeError("Random logger propensity does not equal 1/80 for all rows")

    train = frame.loc[frame["date_utc"].isin(TRAIN_DATES) & (frame["position"] == TARGET_POSITION)]
    evaluation = frame.loc[
        frame["date_utc"].isin(EVALUATION_DATES) & (frame["position"] == TARGET_POSITION)
    ].reset_index(drop=True)
    target_item, train_counts, train_clicks = choose_best_item(
        train["item_id"].to_numpy(dtype=np.int64),
        train["position"].to_numpy(dtype=np.int64),
        train["click"].to_numpy(dtype=np.int64),
        target_position=TARGET_POSITION,
        n_items=N_ITEMS,
    )
    stream, scores = build_mope_stream(
        evaluation["item_id"].to_numpy(dtype=np.int64),
        evaluation["click"].to_numpy(dtype=np.int64),
        evaluation["propensity_score"].to_numpy(dtype=np.float64),
        target_item=target_item,
        n_items=N_ITEMS,
    )
    if not np.isin(stream[:, 0], [0.0, WEIGHT_RANGE_WIDTH]).all():
        raise RuntimeError("Importance weights are not in the frozen {0, 80} support")
    if np.any(scores < -1.0 - 1e-12) or np.any(scores > 79.0 + 1e-12):
        raise RuntimeError("Candidate/logger score falls outside [-1, 79]")

    mope, revision, mope_hash, optimizer_hash = load_mope(fast_optimizer)
    started = datetime.now(UTC)
    lower, upper = mope(stream, 0.0, WEIGHT_RANGE_WIDTH, ALPHA)
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    empty_indices = validate_mope_path(lower, upper, len(evaluation))
    promote_indices = np.flatnonzero(lower > 0.0)
    empty_first = int(empty_indices[0]) if empty_indices.size else None
    promote_first = int(promote_indices[0]) if promote_indices.size else None
    promoted = promote_first is not None and (empty_first is None or promote_first < empty_first)
    end_time = datetime.now(UTC)

    fixed_lower = fixed_horizon_hoeffding_lower(scores, alpha=ALPHA, range_width=WEIGHT_RANGE_WIDTH)
    date_strings = evaluation["date_utc"].to_numpy()
    daily_rows: list[dict[str, Any]] = []
    start = 0
    for date in sorted(EVALUATION_DATES):
        indices = np.flatnonzero(date_strings == date)
        if indices.size == 0 or indices[0] != start:
            raise RuntimeError("Evaluation dates are not contiguous in timestamp order")
        end = int(indices[-1]) + 1
        daily_rows.append(
            {
                "date_utc": date,
                "events_through_day": end,
                "day_events": int(indices.size),
                "day_clicks": int(evaluation.loc[indices, "click"].sum()),
                "running_candidate_value_ipw": float(stream[:end, 0].dot(stream[:end, 1]) / end),
                "running_logger_click_rate": float(stream[:end, 1].mean()),
                "running_value_difference": float(scores[:end].mean()),
                "mope_lower": float(lower[end - 1]),
                "mope_upper": float(upper[end - 1]),
            }
        )
        start = end
    if start != len(evaluation):
        raise RuntimeError("Daily summary did not cover the entire evaluation stream")

    summary: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "exploratory_retrospective_development_not_confirmation",
        "created_at_utc": end_time.isoformat(),
        "source": {
            "dataset": source_manifest["dataset"],
            "version": source_manifest["version"],
            "license": source_manifest["source"]["license"],
            "parquet_path": random_info["parquet_path"],
            "parquet_sha256": source_hash,
            "source_manifest_sha256": source_manifest_hash,
            "source_rows": len(frame),
        },
        "protocol": {
            "path": PROTOCOL.relative_to(ROOT).as_posix(),
            "sha256": protocol_hash,
            "training_dates_utc": sorted(TRAIN_DATES),
            "evaluation_dates_utc": sorted(EVALUATION_DATES),
            "decision_unit": "one item-placement record at position 1",
            "target_item_id": target_item,
            "target_policy": "training-selected deterministic item with highest position-1 click rate",
            "incumbent_policy": "uniform Random item policy",
            "estimand": "position-1 mean binary click-value difference candidate minus Random logger",
            "reward_range": [0.0, 1.0],
            "importance_weight_support": [0.0, 80.0],
            "alpha": ALPHA,
            "time_interpretation": "retrospective UTC impression-time order; click-release times unknown",
            "independence_interpretation": "MOPE theorem not asserted on OBD because IID/cluster and slate assumptions are unresolved",
            "evaluation_exposure": "exploratory; the full OBD week was used in prior ShiftLab OPE diagnostics",
        },
        "method": {
            "name": "official MOPE gated-deployment confidence sequence",
            "repository": "https://github.com/n17s/mope",
            "commit": revision,
            "implementation_file_sha256": mope_hash,
            "numeric_device": "CPU",
            "optimizer_mode": (
                "exact analytic 2-D concave-QP optimizer, independently compared to pinned CVXPY reference"
                if fast_optimizer
                else "pinned reference CVXPY optimizer"
            ),
            "fast_optimizer_file_sha256": optimizer_hash,
            "fast_optimizer_validation_path": (
                FAST_SOLVER_VALIDATION.relative_to(ROOT).as_posix() if fast_optimizer else None
            ),
            "fast_optimizer_validation_sha256": (
                sha256(FAST_SOLVER_VALIDATION) if fast_optimizer else None
            ),
        },
        "training": {
            "position": TARGET_POSITION,
            "rows": len(train),
            "item_counts": train_counts.tolist(),
            "item_clicks": train_clicks.astype(int).tolist(),
            "selected_item_id": target_item,
            "selected_item_click_rate": float(
                train_clicks[target_item] / train_counts[target_item]
            ),
        },
        "results": {
            "evaluation_events": len(evaluation),
            "evaluation_clicks": int(evaluation["click"].sum()),
            "incumbent_observed_click_rate": float(evaluation["click"].mean()),
            "candidate_ipw_value": float(stream[:, 0].dot(stream[:, 1]) / len(stream)),
            "candidate_minus_incumbent_ipw": float(scores.mean()),
            "mope_first_lower_crossing_event": promote_first + 1
            if promote_first is not None
            else None,
            "mope_first_empty_set_event": empty_first + 1 if empty_first is not None else None,
            "mope_promoted_before_empty_set": promoted,
            "mope_lower_at_horizon": float(lower[-1]),
            "mope_upper_at_horizon": float(upper[-1]),
            "fixed_horizon_hoeffding_lower_at_horizon": fixed_lower,
            "fixed_horizon_hoeffding_promoted": fixed_lower > 0.0,
            "labels_or_feedback_records_used_at_promotion": (
                promote_first + 1 if promoted and promote_first is not None else len(evaluation)
            ),
            "mope_empty_set_count": int(empty_indices.size),
            "fixed_horizon_score_range_width": WEIGHT_RANGE_WIDTH,
        },
        "limitations": [
            "single seven-day historical dataset, not an independent replication",
            "evaluation days were previously included in aggregate ShiftLab OBD OPE diagnostics",
            "MOPE and Hoeffding coverage are not asserted because the IID/cluster contract is unresolved",
            "no complete-slate or user/session identifiers; position-1 no-interference/factorization is assumed",
            "feature and click-release availability times are not verified",
            "click reward is not revenue, welfare, or net business utility",
        ],
        "runtime": {
            "started_at_utc": started.isoformat(),
            "finished_at_utc": end_time.isoformat(),
        },
    }

    OUTPUT.mkdir(parents=True)
    daily_path = OUTPUT / "daily_metrics.csv"
    write_csv(daily_path, daily_rows)
    summary_path = OUTPUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    report = (
        "# OBD MOPE fixed-candidate development replay\n\n"
        "**Status:** exploratory retrospective development, not real-data confirmation or a valid-data guarantee.\n\n"
        f"The training-selected position-1 item was `{target_item}`. The held-forward segment contains "
        f"{len(evaluation):,} position-1 records over 2019-11-27 through 2019-11-30. Its IPW candidate-minus-Random "
        f"click-value estimate is `{summary['results']['candidate_minus_incumbent_ipw']:.8f}`. MOPE's lower bound "
        f"first crossed zero at event `{summary['results']['mope_first_lower_crossing_event']}`; its first empty set "
        f"was `{summary['results']['mope_first_empty_set_event']}`. The fixed-horizon Hoeffding lower bound is "
        f"`{fixed_lower:.8f}` and promoted is `{fixed_lower > 0.0}`.\n\n"
        "The OBD unit/dependence, slate-interference, feature timing and label-release contracts remain unresolved. "
        "Accordingly, neither the MOPE nor Hoeffding guarantee is asserted for this replay. See the frozen protocol "
        "and aggregate manifest for the exact scope and provenance.\n"
    )
    report_path = OUTPUT / "report.md"
    report_path.write_text(report, encoding="utf-8")
    manifest = {
        "schema_version": "1.0.0",
        "status": summary["status"],
        "source": summary["source"],
        "protocol_sha256": protocol_hash,
        "runner": "scripts/reproduce_open_bandit_mope_development.py",
        "runner_sha256": sha256(Path(__file__).resolve()),
        "method": summary["method"],
        "artifacts": {
            "summary.json": sha256(summary_path),
            "daily_metrics.csv": sha256(daily_path),
            "report.md": sha256(report_path),
        },
        "key_results": summary["results"],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fast-optimizer",
        action="store_true",
        help="Use the validated exact 2-D optimizer in place of per-event CVXPY solves.",
    )
    args = parser.parse_args()
    result = run(fast_optimizer=args.fast_optimizer)
    print(json.dumps(result["results"], indent=2))
