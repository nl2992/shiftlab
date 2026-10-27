"""Real-data paired reserve-procurement decision stream from the verified EIA EBA snapshot.

Deployed policy = frozen Ridge, reference policy = weekly-refit Ridge (24 h label delay), both
simulated by the existing retraining-frontier helpers. Costs come from ``reserve_costs``.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.dive.reserve_costs import TAU_QUANTILE, paired_cost, reserve_actions

ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = ROOT / "scripts"
try:
    from scripts.audit_eia_2026_holdout_readiness import (
        ARCHIVE,
        REPORT,
        RESPONDENTS,
        TYPES,
        _eligible_rows,
        _read_selected_series,
    )
    from scripts.evaluate_eia_retraining_frontier import _simulate_policy
except ModuleNotFoundError:  # scripts/ not importable as a package
    sys.path.insert(0, str(_SCRIPTS))
    from audit_eia_2026_holdout_readiness import (  # type: ignore[no-redef]
        ARCHIVE,
        REPORT,
        RESPONDENTS,
        TYPES,
        _eligible_rows,
        _read_selected_series,
    )
    from evaluate_eia_retraining_frontier import _simulate_policy  # type: ignore[no-redef]

__all__ = [
    "ARCHIVE",
    "RESPONDENTS",
    "TYPES",
    "WINDOWS",
    "PairedReserveStream",
    "StreamWindows",
    "build_respondent_streams",
    "load_series",
    "read_streams",
    "write_streams",
]

DELAY_HOURS = 24
CALIBRATION_ROWS = 8760
HOUR = 3600
MAX_ABS_PAIRED_COST = 5.0


def _epoch(value: str) -> float:
    return float(pd.Timestamp(value).timestamp())


@dataclass(frozen=True)
class StreamWindows:
    """Inclusive event-time bounds (epoch seconds) for fit, rehearsal and development sets."""

    fit_full_start: float
    fit_full_end: float
    fit_rehearsal_end: float
    rehearsal_start: float
    rehearsal_end: float
    development_start: float
    development_end: float
    split_2026: float


WINDOWS = StreamWindows(
    fit_full_start=_epoch("2019-01-01T00:00:00Z"),
    fit_full_end=_epoch("2024-12-30T23:00:00Z"),
    fit_rehearsal_end=_epoch("2023-12-31T23:00:00Z"),
    rehearsal_start=_epoch("2024-01-01T00:00:00Z"),
    rehearsal_end=_epoch("2024-12-30T23:00:00Z"),
    development_start=_epoch("2025-01-01T00:00:00Z"),
    development_end=_epoch("2026-10-19T17:00:00Z"),
    split_2026=_epoch("2026-01-01T00:00:00Z"),
)


@dataclass(frozen=True)
class PairedReserveStream:
    """One respondent/window of paired reserve decisions.

    ``demand`` and ``paired_cost`` are evaluator-side; monitors may read ``paired_cost`` only at
    queried disagreement events.
    """

    respondent: str
    window: str
    event_time: np.ndarray
    x: np.ndarray
    demand: np.ndarray
    tau: float
    deployed_prediction: np.ndarray
    reference_prediction: np.ndarray
    deployed_action: np.ndarray
    reference_action: np.ndarray
    paired_cost: np.ndarray
    disagreement: np.ndarray
    frozen_margin: np.ndarray


def _complete_arrays(series: dict, respondent: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = [row for row in _eligible_rows(series, respondent) if row["complete_features"]]
    by_type = {kind: series[f"EBA.{respondent}-ALL.{kind}.H"] for kind in TYPES}
    event_time = np.asarray([row["event_time"] for row in rows], dtype=np.float64)
    target_time = np.asarray([row["target_time"] for row in rows], dtype=np.float64)
    if len(event_time) == 0:
        raise ValueError(f"{respondent} has no complete rows")
    if len(event_time) > 1 and np.any(np.diff(event_time) <= 0):
        raise ValueError(f"{respondent} event times are not strictly increasing")
    if np.any(target_time != event_time + HOUR):
        raise ValueError(f"{respondent} target is not exactly one hour after event")
    x = np.asarray(
        [[by_type[kind][int(t)] for kind in TYPES] for t in event_time], dtype=np.float64
    )
    y = np.asarray([by_type["D"][int(t)] for t in target_time], dtype=np.float64)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError(f"{respondent} contains nonfinite complete-feature rows")
    return event_time, x, y


def _assemble(
    respondent: str,
    window: str,
    event_time: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    tau: float,
    deployed: np.ndarray,
    reference: np.ndarray,
) -> PairedReserveStream:
    deployed_action = reserve_actions(deployed, tau)
    reference_action = reserve_actions(reference, tau)
    cost = paired_cost(deployed_action, reference_action, y, tau)
    disagreement = deployed_action != reference_action
    if np.any(np.abs(cost) > MAX_ABS_PAIRED_COST):
        raise ValueError("paired cost exceeds 5 in magnitude")
    if np.any(cost[~disagreement] != 0):
        raise ValueError("paired cost nonzero where actions agree")
    return PairedReserveStream(
        respondent=respondent,
        window=window,
        event_time=event_time,
        x=x,
        demand=y,
        tau=float(tau),
        deployed_prediction=deployed,
        reference_prediction=reference,
        deployed_action=deployed_action,
        reference_action=reference_action,
        paired_cost=cost,
        disagreement=disagreement,
        frozen_margin=deployed - tau,
    )


def _simulate_pair(
    *,
    event_time: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    train: tuple[np.ndarray, np.ndarray, np.ndarray],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    train_event, train_x, train_y = train
    if len(event_time) == 0:
        raise ValueError("no events to simulate")
    cal = slice(max(0, len(train_y) - CALIBRATION_ROWS), None)
    out = {}
    for policy in ("frozen", "weekly"):
        # Calibration arguments only feed the error_trigger threshold; _simulate_policy computes
        # it unconditionally but only branches on it for policy == "error_trigger".
        out[policy], _ = _simulate_policy(
            policy=policy,
            delay_hours=DELAY_HOURS,
            x=x,
            y=y,
            event_time=event_time,
            label_event_time=event_time + HOUR,
            train_x=train_x,
            train_y=train_y,
            train_label_event_time=train_event + HOUR,
            calibration_x=train_x[cal],
            calibration_y=train_y[cal],
            calibration_time=train_event[cal],
            device=device,
        )
    return out["frozen"], out["weekly"]


def build_respondent_streams(
    series: dict,
    respondent: str,
    device: torch.device,
    windows: StreamWindows = WINDOWS,
) -> list[PairedReserveStream]:
    """Build rehearsal_2024, 2025 and 2026 paired streams for one respondent."""
    event_time, x, y = _complete_arrays(series, respondent)

    def mask(low: float, high: float) -> np.ndarray:
        return (event_time >= low) & (event_time <= high)

    fit_full = mask(windows.fit_full_start, windows.fit_full_end)
    fit_reh = mask(windows.fit_full_start, windows.fit_rehearsal_end)
    reh = mask(windows.rehearsal_start, windows.rehearsal_end)
    dev = mask(windows.development_start, windows.development_end)
    tau = float(np.quantile(y[fit_full], TAU_QUANTILE))

    frozen, weekly = _simulate_pair(
        event_time=event_time[reh],
        x=x[reh],
        y=y[reh],
        train=(event_time[fit_reh], x[fit_reh], y[fit_reh]),
        device=device,
    )
    streams = [
        _assemble(
            respondent, "rehearsal_2024", event_time[reh], x[reh], y[reh], tau, frozen, weekly
        )
    ]
    dev_time, dev_x, dev_y = event_time[dev], x[dev], y[dev]
    frozen, weekly = _simulate_pair(
        event_time=dev_time,
        x=dev_x,
        y=dev_y,
        train=(event_time[fit_full], x[fit_full], y[fit_full]),
        device=device,
    )
    for name, part in (
        ("2025", dev_time < windows.split_2026),
        ("2026", dev_time >= windows.split_2026),
    ):
        if not part.any():
            raise ValueError(f"{respondent}/{name} has no events")
        streams.append(
            _assemble(
                respondent,
                name,
                dev_time[part],
                dev_x[part],
                dev_y[part],
                tau,
                frozen[part],
                weekly[part],
            )
        )
    return streams


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_series(archive_path: Path = ARCHIVE, expected_sha256: str | None = None) -> dict:
    """Verify the archive SHA-256 (against the readiness receipt by default), then read series."""
    expected = expected_sha256 or str(
        json.loads(REPORT.read_text(encoding="utf-8"))["source_sha256"]
    )
    actual = _sha256(Path(archive_path))
    if actual != expected:
        raise ValueError(f"EIA archive SHA-256 mismatch: {actual} != {expected}")
    return dict(_read_selected_series(Path(archive_path)))


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL).decode()
    except (subprocess.CalledProcessError, OSError):
        return None


def _frame(streams: list[PairedReserveStream]) -> pd.DataFrame:
    frames = []
    for s in streams:
        data = {
            "respondent": s.respondent,
            "window": s.window,
            "event_time": s.event_time,
            **{f"x{i}": s.x[:, i] for i in range(s.x.shape[1])},
            "demand": s.demand,
            "tau": np.full(len(s.demand), s.tau),
            "deployed_prediction": s.deployed_prediction,
            "reference_prediction": s.reference_prediction,
            "deployed_action": s.deployed_action,
            "reference_action": s.reference_action,
            "paired_cost": s.paired_cost,
            "disagreement": s.disagreement,
            "frozen_margin": s.frozen_margin,
        }
        frames.append(pd.DataFrame(data))
    return pd.concat(frames, ignore_index=True)


def write_streams(
    streams: list[PairedReserveStream],
    out_dir: Path,
    *,
    device: torch.device | None = None,
    archive_path: Path = ARCHIVE,
) -> Path:
    """Write ``streams.parquet`` and ``manifest.json``; refuse a non-empty directory."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"{out_dir} is not empty")
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet = out_dir / "streams.parquet"
    _frame(streams).to_parquet(parquet, index=False)
    receipt = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    archive_sha = _sha256(Path(archive_path)) if Path(archive_path).exists() else None
    code_files = {
        "src/shiftlab/dive/eia_paired_reserve.py": Path(__file__),
        "src/shiftlab/dive/reserve_costs.py": ROOT / "src/shiftlab/dive/reserve_costs.py",
        "scripts/audit_eia_2026_holdout_readiness.py": _SCRIPTS
        / "audit_eia_2026_holdout_readiness.py",
        "scripts/evaluate_eia_retraining_frontier.py": _SCRIPTS
        / "evaluate_eia_retraining_frontier.py",
    }
    counts: dict[str, dict[str, int]] = {}
    tau: dict[str, float] = {}
    for s in streams:
        counts.setdefault(s.respondent, {})[s.window] = len(s.event_time)
        tau[s.respondent] = s.tau
    manifest = {
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha,
        "receipt_source_sha256": receipt.get("source_sha256"),
        "receipt_check": archive_sha is not None and archive_sha == receipt.get("source_sha256"),
        "git_head": (_git("rev-parse", "HEAD") or "").strip() or None,
        "git_status_porcelain": _git("status", "--porcelain"),
        "code_sha256": {k: _sha256(v) for k, v in code_files.items()},
        "tau": tau,
        "tau_quantile": TAU_QUANTILE,
        "n_per_window": counts,
        "delay_hours": DELAY_HOURS,
        "utc_time": pd.Timestamp.now(tz="UTC").isoformat(),
        "device": None if device is None else device.type,
        "cuda_device_name": (
            torch.cuda.get_device_name(device)
            if device is not None and device.type == "cuda"
            else None
        ),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "streams_parquet_sha256": _sha256(parquet),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_dir


def read_streams(out_dir: Path) -> list[PairedReserveStream]:
    """Read streams back, re-verifying the parquet hash against the manifest."""
    out_dir = Path(out_dir)
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    parquet = out_dir / "streams.parquet"
    if _sha256(parquet) != manifest["streams_parquet_sha256"]:
        raise ValueError("streams.parquet does not match manifest SHA-256")
    frame = pd.read_parquet(parquet)
    streams = []
    for (respondent, window), part in frame.groupby(["respondent", "window"], sort=False):
        x_cols = [f"x{i}" for i in range(len(TYPES))]
        streams.append(
            PairedReserveStream(
                respondent=str(respondent),
                window=str(window),
                event_time=part["event_time"].to_numpy(np.float64),
                x=part[x_cols].to_numpy(np.float64),
                demand=part["demand"].to_numpy(np.float64),
                tau=float(part["tau"].iloc[0]),
                deployed_prediction=part["deployed_prediction"].to_numpy(np.float64),
                reference_prediction=part["reference_prediction"].to_numpy(np.float64),
                deployed_action=part["deployed_action"].to_numpy(np.int8),
                reference_action=part["reference_action"].to_numpy(np.int8),
                paired_cost=part["paired_cost"].to_numpy(np.float64),
                disagreement=part["disagreement"].to_numpy(bool),
                frozen_margin=part["frozen_margin"].to_numpy(np.float64),
            )
        )
    return streams
