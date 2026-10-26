"""Compare retrospective CRSP decision-harm monitor diagnostics on the full cohort.

The policy is frozen by construction: standardized Ridge(alpha=1), fit on train only,
long when its prediction is positive; reference: long when same-day vwretd is positive.
Test labels are used only by the evaluator after predictions and actions are fixed.
This is a single retrospective market path, not a calibration of sequential guarantees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import torch
from scipy.stats import rankdata

from shiftlab.data.provenance import sha256, write_json
from shiftlab.dive.eprocess import BoundedMeanEProcess
from shiftlab.monitoring import one_sided_cusum, rbf_gamma, rbf_mmd_squared

TRANSACTION_COST_BPS = (0, 5, 10, 25)
PRIMARY_BPS = 5
RETURN_CAP = 0.10
BLOCK_DAYS = 20
BOOTSTRAP_REPLICATES = 2_000
ALPHA = 0.05
PROTOCOL = Path("docs/crsp_monitor_comparison_protocol.md")


def _panel_path(root: Path, version: str | None) -> Path:
    base = root / "processed" / "crsp_ciz_next_day"
    if version:
        path = base / version
        if not (path / "dataset_manifest.json").is_file():
            raise FileNotFoundError(path)
        return path
    candidates = sorted(
        (p for p in base.iterdir() if p.is_dir() and (p / "dataset_manifest.json").exists()),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        raise FileNotFoundError(f"no CRSP CIZ panel under {base}")
    return candidates[-1]


def _nrows(dataset: ds.Dataset, split: str) -> int:
    return dataset.count_rows(filter=ds.field("split") == split)


def _read_split(
    dataset: ds.Dataset,
    *,
    split: str,
    nrows: int,
    nfeatures: int,
    directory: Path,
    batch_size: int,
    include_exchange: bool = False,
) -> dict[str, np.memmap]:
    """Stream one split into compact temporary arrays; never materialize Arrow metadata in pandas."""
    if nrows <= 0:
        raise ValueError(f"split {split!r} is empty")
    fields: dict[str, tuple[np.dtype, tuple[int, ...]]] = {
        "x": (np.dtype("float64"), (nrows, nfeatures)),
        "y": (np.dtype("float64"), (nrows,)),
    }
    if split != "train":
        fields.update(
            permno=(np.dtype("int64"), (nrows,)),
            date=(np.dtype("int32"), (nrows,)),
        )
        if include_exchange:
            fields["exchange"] = (np.dtype("int8"), (nrows,))
    arrays = {
        key: np.memmap(directory / f"{split}_{key}.bin", mode="w+", dtype=dtype, shape=shape)
        for key, (dtype, shape) in fields.items()
    }
    columns = ["features", "target"] + (
        []
        if split == "train"
        else ["permno", "dlycaldt"] + (["primaryexch"] if include_exchange else [])
    )
    scanner = dataset.scanner(
        columns=columns, filter=ds.field("split") == split, batch_size=batch_size
    )
    offset = 0
    for batch in scanner.to_batches():
        n = batch.num_rows
        feature_column = batch.column("features")
        values = feature_column.values.to_numpy(zero_copy_only=False)
        matrix = np.asarray(values, dtype=np.float64).reshape(n, nfeatures)
        arrays["x"][offset : offset + n] = matrix
        arrays["y"][offset : offset + n] = batch.column("target").to_numpy(zero_copy_only=False)
        if split != "train":
            arrays["permno"][offset : offset + n] = batch.column("permno").to_numpy(
                zero_copy_only=False
            )
            dates = batch.column("dlycaldt").to_pylist()
            arrays["date"][offset : offset + n] = np.asarray(dates, dtype="datetime64[D]").astype(
                np.int32
            )
            if include_exchange:
                exchange_codes = {"A": 0, "B": 1, "I": 2, "N": 3, "Q": 4, "R": 5}
                exchanges = batch.column("primaryexch").to_pylist()
                try:
                    arrays["exchange"][offset : offset + n] = np.fromiter(
                        (exchange_codes[value] for value in exchanges), dtype=np.int8, count=n
                    )
                except KeyError as exc:
                    raise ValueError(f"unexpected primary exchange code: {exc.args[0]!r}") from exc
        offset += n
    if offset != nrows:
        raise ValueError(f"split {split!r} row-count mismatch: expected {nrows}, read {offset}")
    for array in arrays.values():
        array.flush()
    return arrays


def _fit_ridge_streaming(
    x: np.memmap,
    y: np.memmap,
    *,
    device: torch.device,
    batch_size: int,
    alpha: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, np.ndarray, str]:
    """Exact train-only median/mean/scale and GPU sufficient-statistic Ridge fit."""
    n, p = x.shape
    medians = np.empty(p, dtype=np.float64)
    for j in range(p):
        medians[j] = np.nanmedian(x[:, j])
        if not np.isfinite(medians[j]):
            medians[j] = 0.0
    sums = np.zeros(p, dtype=np.float64)
    squares = np.zeros(p, dtype=np.float64)
    y_mean = float(np.mean(y, dtype=np.float64))
    for start in range(0, n, batch_size):
        values = np.asarray(x[start : start + batch_size]).copy()
        mask = ~np.isfinite(values)
        if mask.any():
            values[mask] = np.broadcast_to(medians, values.shape)[mask]
        sums += values.sum(axis=0, dtype=np.float64)
        squares += np.square(values, dtype=np.float64).sum(axis=0)
    means = sums / n
    scales = np.sqrt(np.maximum(squares / n - means**2, 0.0))
    scales[scales <= 1e-12] = 1.0

    gram = torch.zeros((p, p), dtype=torch.float64, device=device)
    cross = torch.zeros(p, dtype=torch.float64, device=device)
    for start in range(0, n, batch_size):
        stop = min(start + batch_size, n)
        values = np.asarray(x[start:stop]).copy()
        mask = ~np.isfinite(values)
        if mask.any():
            values[mask] = np.broadcast_to(medians, values.shape)[mask]
        z = torch.as_tensor((values - means) / scales, dtype=torch.float64, device=device)
        ty = torch.as_tensor(np.asarray(y[start:stop]) - y_mean, dtype=torch.float64, device=device)
        gram.add_(z.T @ z)
        cross.add_(z.T @ ty)
    coef = torch.linalg.solve(
        gram + alpha * torch.eye(p, dtype=torch.float64, device=device), cross
    )
    return medians, means, scales, y_mean, coef.detach().cpu().numpy(), str(device)


def _predict_streaming(
    x: np.memmap,
    *,
    medians: np.ndarray,
    means: np.ndarray,
    scales: np.ndarray,
    y_mean: float,
    coef: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    predictions = np.empty(len(x), dtype=np.float64)
    weight = torch.as_tensor(coef, dtype=torch.float64, device=device)
    for start in range(0, len(x), batch_size):
        stop = min(start + batch_size, len(x))
        values = np.asarray(x[start:stop]).copy()
        mask = ~np.isfinite(values)
        if mask.any():
            values[mask] = np.broadcast_to(medians, values.shape)[mask]
        z = torch.as_tensor((values - means) / scales, dtype=torch.float64, device=device)
        predictions[start:stop] = (z @ weight + y_mean).cpu().numpy()
    return predictions


def _turnover_in_path(actions: np.ndarray, permnos: np.ndarray, dates: np.ndarray) -> np.ndarray:
    """Return event-aligned binary-position turnover, including each test-path exit."""
    order = np.lexsort((dates, permnos))
    sorted_permno = permnos[order]
    sorted_action = actions[order].astype(np.float64)
    delta = np.abs(np.diff(sorted_action, prepend=0.0))
    first = np.r_[True, sorted_permno[1:] != sorted_permno[:-1]]
    delta[first] = sorted_action[first]
    last = np.r_[sorted_permno[1:] != sorted_permno[:-1], True]
    delta[last] += sorted_action[last]
    aligned = np.empty(len(actions), dtype=np.float64)
    aligned[order] = delta
    return aligned


def _daily_costs(
    y: np.ndarray,
    candidate: np.ndarray,
    reference: np.ndarray,
    cand_turnover: np.ndarray,
    ref_turnover: np.ndarray,
    date_index: np.ndarray,
    ndates: int,
    bps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fee = bps / 10_000.0
    clipped = np.clip(y, -RETURN_CAP, RETURN_CAP)
    difference = (
        -candidate * clipped + fee * cand_turnover - (-reference * clipped + fee * ref_turnover)
    )
    sums = np.bincount(date_index, weights=difference, minlength=ndates).astype(np.float64)
    counts = np.bincount(date_index, minlength=ndates).astype(np.float64)
    return sums, counts, difference


def _cusum(values: np.ndarray, mean: float, scale: float) -> np.ndarray:
    return one_sided_cusum(values, baseline_mean=mean, baseline_scale=max(scale, 1e-12), slack=0.0)


def _bootstrap_cusum_threshold(
    baseline: np.ndarray, *, horizon: int, seed: int, replicates: int = 2_000
) -> float:
    rng = np.random.default_rng(seed)
    centered = baseline - baseline.mean()
    scale = max(float(centered.std(ddof=1)), 1e-12)
    blocks = math.ceil(horizon / BLOCK_DAYS)
    offsets = np.arange(BLOCK_DAYS)
    maxima = np.empty(replicates, dtype=np.float64)
    for r in range(replicates):
        starts = rng.integers(0, len(centered), size=blocks)
        sample = np.concatenate([(s + offsets) % len(centered) for s in starts])[:horizon]
        maxima[r] = _cusum(centered[sample], 0.0, scale).max(initial=0.0)
    return float(np.quantile(maxima, 1 - ALPHA, method="higher"))


def _auc_ap(scores: np.ndarray, labels: np.ndarray) -> tuple[float | None, float | None, int]:
    valid = np.isfinite(scores) & np.isfinite(labels)
    s, y = scores[valid], labels[valid].astype(bool)
    positives = int(y.sum())
    if positives == 0 or positives == len(y):
        return None, None, positives
    ranks = rankdata(s, method="average")
    auc = (ranks[y].sum() - positives * (positives + 1) / 2) / (positives * (len(y) - positives))
    order = np.argsort(-s, kind="stable")
    cumulative = np.cumsum(y[order])
    precision = cumulative / np.arange(1, len(y) + 1)
    ap = float((precision * y[order]).sum() / positives)
    return float(auc), ap, positives


def _two_way_block_interval(
    values: np.ndarray,
    counts: np.ndarray,
    *,
    seed: int,
    device: torch.device,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> list[float]:
    """Product bootstrap of PERMNO clusters and circular calendar-date blocks."""
    n_dates, n_names = values.shape
    if min(n_dates, n_names) < 2:
        raise ValueError("two-way bootstrap needs multiple dates and securities")
    rng = np.random.default_rng(seed)
    date_weights = np.zeros((replicates, n_dates), dtype=np.float32)
    sec_weights = np.zeros((replicates, n_names), dtype=np.float32)
    block_count = math.ceil(n_dates / BLOCK_DAYS)
    offsets = np.arange(BLOCK_DAYS)
    for r in range(replicates):
        starts = rng.integers(0, n_dates, size=block_count)
        chosen_dates = np.concatenate([(s + offsets) % n_dates for s in starts])[:n_dates]
        date_weights[r] = np.bincount(chosen_dates, minlength=n_dates)
        chosen_names = rng.integers(0, n_names, size=n_names)
        sec_weights[r] = np.bincount(chosen_names, minlength=n_names)
    tensor_device = device
    v = torch.as_tensor(values, dtype=torch.float64, device=tensor_device)
    c = torch.as_tensor(counts, dtype=torch.float64, device=tensor_device)
    estimates = np.empty(replicates, dtype=np.float64)
    batch = 64
    for start in range(0, replicates, batch):
        stop = min(start + batch, replicates)
        dw = torch.as_tensor(date_weights[start:stop], dtype=torch.float64, device=tensor_device)
        sw = torch.as_tensor(sec_weights[start:stop], dtype=torch.float64, device=tensor_device)
        numerator = ((dw @ v) * sw).sum(dim=1)
        denominator = ((dw @ c) * sw).sum(dim=1)
        estimates[start:stop] = (numerator / denominator).detach().cpu().numpy()
    return [float(x) for x in np.quantile(estimates, [0.025, 0.975])]


def _mmd_windows(
    x: np.ndarray,
    dates: np.ndarray,
    *,
    window: int,
    rng: np.random.Generator,
    sample_size: int = 256,
) -> tuple[np.ndarray, np.ndarray]:
    """Nonoverlapping date-window RBF MMD² against a calibration-only reference sample."""
    order = np.argsort(dates, kind="stable")
    sorted_dates = dates[order]
    unique_dates = np.unique(sorted_dates)
    starts = range(0, len(unique_dates), window)
    reference_end = int(np.searchsorted(sorted_dates, unique_dates[window - 1], side="right"))
    if len(unique_dates) < window:
        reference_end = len(sorted_dates)
    reference_rows = order[:reference_end]
    if len(reference_rows) < 2:
        raise ValueError("calibration reference window has too few rows")
    ref_sel = rng.choice(reference_rows, size=min(sample_size, len(reference_rows)), replace=False)
    ref = np.asarray(x[ref_sel]).copy()
    # This function receives standardized features with missing values already imputed.
    gamma = rbf_gamma(ref)
    scores, right_edges = [], []
    for raw_start in starts:
        start = int(raw_start)
        end = min(start + window, len(unique_dates))
        if end - start < 2:
            continue
        lo = int(np.searchsorted(sorted_dates, unique_dates[start], side="left"))
        hi = int(np.searchsorted(sorted_dates, unique_dates[end - 1], side="right"))
        rows = order[lo:hi]
        if len(rows) < 2:
            continue
        sel = rng.choice(rows, size=min(sample_size, len(rows)), replace=False)
        scores.append(rbf_mmd_squared(ref, np.asarray(x[sel]), gamma))
        right_edges.append(int(unique_dates[end - 1]))
    return np.asarray(scores), np.asarray(right_edges, dtype=np.int32)


def _impute_standardize(
    x: np.ndarray, medians: np.ndarray, means: np.ndarray, scales: np.ndarray
) -> np.ndarray:
    result = np.asarray(x, dtype=np.float64).copy()
    missing = ~np.isfinite(result)
    if missing.any():
        result[missing] = np.broadcast_to(medians, result.shape)[missing]
    return (result - means) / scales


def evaluate(
    *, root: Path, version: str | None, batch_size: int, device_name: str, output: Path, seed: int
) -> Path:
    path = _panel_path(root, version)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    manifest_path = path / "dataset_manifest.json"
    panel_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observation_file = path / "observations.parquet"
    expected_hash = panel_manifest["files"]["observations.parquet"]
    if sha256(observation_file) != expected_hash:
        raise ValueError("CRSP panel checksum does not match its manifest")
    dataset = ds.dataset(observation_file, format="parquet")
    nfeatures = len(panel_manifest["feature_names"])
    vwretd_index = panel_manifest["feature_names"].index("vwretd")
    counts_by_split = {s: _nrows(dataset, s) for s in ("train", "calibration", "test")}
    resolved = torch.device(
        "cuda"
        if device_name == "auto" and torch.cuda.is_available()
        else "cpu"
        if device_name == "auto"
        else device_name
    )
    if resolved.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="shiftlab_crsp_monitor_") as temp_name:
        temp = Path(temp_name)
        train = _read_split(
            dataset,
            split="train",
            nrows=counts_by_split["train"],
            nfeatures=nfeatures,
            directory=temp,
            batch_size=batch_size,
        )
        medians, means, scales, y_mean, coef, fit_device = _fit_ridge_streaming(
            train["x"], train["y"], device=resolved, batch_size=batch_size
        )
        del train
        metrics_by_cost: dict[str, dict[str, object]] = {}
        primary_daily: dict[str, np.ndarray] = {}
        test_features_for_mmd = None
        test_dates_for_mmd = None
        cal_features_for_mmd = None
        cal_dates_for_mmd = None
        for split in ("calibration", "test"):
            arrays = _read_split(
                dataset,
                split=split,
                nrows=counts_by_split[split],
                nfeatures=nfeatures,
                directory=temp,
                batch_size=batch_size,
            )
            pred = _predict_streaming(
                arrays["x"],
                medians=medians,
                means=means,
                scales=scales,
                y_mean=y_mean,
                coef=coef,
                device=resolved,
                batch_size=batch_size,
            )
            candidate = (pred > 0.0).astype(np.int8)
            reference = (np.asarray(arrays["x"][:, vwretd_index]) > 0.0).astype(np.int8)
            permno = arrays["permno"]
            dates = arrays["date"]
            unique_dates, date_index = np.unique(dates, return_inverse=True)
            cand_turn = _turnover_in_path(candidate, permno, dates)
            ref_turn = _turnover_in_path(reference, permno, dates)
            for bps in TRANSACTION_COST_BPS:
                sums, n_events, diff = _daily_costs(
                    arrays["y"],
                    candidate,
                    reference,
                    cand_turn,
                    ref_turn,
                    date_index,
                    len(unique_dates),
                    bps,
                )
                key = f"{split}_{bps}bps"
                row: dict[str, object] = {
                    "split": split,
                    "turnover_cost_bps": bps,
                    "events": len(permno),
                    "permnos": int(np.unique(permno).size),
                    "trading_dates": len(unique_dates),
                    "event_weighted_mean_excess_cost": float(diff.mean()),
                    "date_equal_weighted_mean_excess_cost": float((sums / n_events).mean()),
                    "candidate_long_rate": float(candidate.mean()),
                    "reference_long_rate": float(reference.mean()),
                }
                metrics_by_cost[key] = row
                if bps == PRIMARY_BPS:
                    primary_daily[split] = sums / n_events
                    if split == "test":
                        # Dense date-by-PERMNO matrices are built below for the two-way bootstrap.
                        primary_daily["test_sums"] = sums
                        primary_daily["test_counts"] = n_events
                        primary_daily["test_diff"] = diff
            if split == "test":
                test_features_for_mmd = arrays["x"]
                test_dates_for_mmd = np.asarray(dates).copy()
                test_dates_unique = unique_dates.copy()
                test_permno = np.asarray(permno).copy()
                test_date_index = date_index.copy()
                test_y = np.asarray(arrays["y"]).copy()
                test_pred = pred.copy()
            else:
                cal_features_for_mmd = arrays["x"]
                cal_dates_for_mmd = np.asarray(dates).copy()
                cal_unique_dates = unique_dates.copy()
                cal_y = np.asarray(arrays["y"]).copy()
                cal_candidate = candidate.copy()
                cal_reference = reference.copy()
                cal_cand_turn = cand_turn.copy()
                cal_ref_turn = ref_turn.copy()
                cal_pred = pred.copy()
            del arrays

        # Primary 5 bps inferential summary: two-way cluster/date-block resampling.
        names, name_index = np.unique(test_permno, return_inverse=True)
        matrix_sum = np.zeros((len(test_dates_unique), len(names)), dtype=np.float32)
        matrix_count = np.zeros_like(matrix_sum)
        np.add.at(matrix_sum, (test_date_index, name_index), primary_daily["test_diff"])
        np.add.at(matrix_count, (test_date_index, name_index), 1.0)
        interval = _two_way_block_interval(
            matrix_sum, matrix_count, seed=seed + 711, device=resolved
        )

        # Calibration-period daily means define empirical reference levels only.
        assert cal_dates_for_mmd is not None
        assert test_dates_for_mmd is not None
        assert cal_features_for_mmd is not None
        assert test_features_for_mmd is not None
        cal_5_sum, cal_5_count, _ = _daily_costs(
            cal_y,
            cal_candidate,
            cal_reference,
            cal_cand_turn,
            cal_ref_turn,
            np.unique(cal_dates_for_mmd, return_inverse=True)[1],
            len(cal_unique_dates),
            PRIMARY_BPS,
        )
        cal_cost = cal_5_sum / cal_5_count
        test_cost = primary_daily["test_sums"] / primary_daily["test_counts"]
        cost_mean, cost_scale = float(cal_cost.mean()), float(cal_cost.std(ddof=1))
        cost_cusum = _cusum(test_cost, cost_mean, cost_scale)
        cost_threshold = _bootstrap_cusum_threshold(
            cal_cost, horizon=len(test_cost), seed=seed + 712
        )
        bounded = 0.20 + 4 * (PRIMARY_BPS / 10_000.0)
        eproc = BoundedMeanEProcess(bound=bounded, alpha=ALPHA)
        log_e = np.asarray([eproc.update(float(x)) for x in test_cost], dtype=np.float64)

        # Predictive-loss monitoring uses bounded squared error as a separate endpoint.
        cal_pred_loss = np.square(
            np.clip(cal_pred, -RETURN_CAP, RETURN_CAP) - np.clip(cal_y, -RETURN_CAP, RETURN_CAP)
        )
        test_pred_loss = np.square(
            np.clip(test_pred, -RETURN_CAP, RETURN_CAP) - np.clip(test_y, -RETURN_CAP, RETURN_CAP)
        )
        cal_loss_daily = np.bincount(
            np.unique(cal_dates_for_mmd, return_inverse=True)[1],
            weights=cal_pred_loss,
            minlength=len(cal_unique_dates),
        ) / np.bincount(
            np.unique(cal_dates_for_mmd, return_inverse=True)[1], minlength=len(cal_unique_dates)
        )
        test_loss_daily = np.bincount(
            test_date_index, weights=test_pred_loss, minlength=len(test_dates_unique)
        ) / np.bincount(test_date_index, minlength=len(test_dates_unique))
        loss_mean, loss_scale = float(cal_loss_daily.mean()), float(cal_loss_daily.std(ddof=1))
        loss_cusum = _cusum(test_loss_daily, loss_mean, loss_scale)
        loss_threshold = _bootstrap_cusum_threshold(
            cal_loss_daily, horizon=len(test_loss_daily), seed=seed + 713
        )

        # MMD is a sampled feature-distribution diagnostic, not a decision-harm test.
        cal_x = _impute_standardize(cal_features_for_mmd, medians, means, scales)
        test_x = _impute_standardize(test_features_for_mmd, medians, means, scales)
        rng = np.random.default_rng(seed + 714)
        cal_mmd, cal_mmd_dates = _mmd_windows(cal_x, cal_dates_for_mmd, window=BLOCK_DAYS, rng=rng)
        test_mmd, test_mmd_dates = _mmd_windows(
            test_x, test_dates_for_mmd, window=BLOCK_DAYS, rng=rng
        )
        reference_end_date = np.sort(np.unique(cal_dates_for_mmd))[
            min(BLOCK_DAYS, len(cal_unique_dates)) - 1
        ]
        cal_null_mmd = cal_mmd[cal_mmd_dates > reference_end_date]
        if not len(cal_null_mmd):
            raise ValueError("not enough calibration MMD windows beyond the reference window")
        mmd_threshold = float(np.quantile(cal_null_mmd, 1 - ALPHA, method="higher"))
        mmd_daily = np.full(len(test_dates_unique), np.nan, dtype=np.float64)
        for score, right_edge in zip(test_mmd, test_mmd_dates, strict=True):
            ix = int(np.searchsorted(test_dates_unique, right_edge))
            mmd_daily[ix] = score
        # Carry the most recent window score forward for daily forecast-score comparisons.
        last = np.nan
        for i in range(len(mmd_daily)):
            if np.isfinite(mmd_daily[i]):
                last = mmd_daily[i]
            else:
                mmd_daily[i] = last

        # Hindsight-only target: next 20 trading dates have positive mean paired excess cost.
        harm_labels = np.full(len(test_cost), np.nan)
        for i in range(len(test_cost) - BLOCK_DAYS):
            harm_labels[i] = float(np.mean(test_cost[i + 1 : i + 1 + BLOCK_DAYS]) > 0.0)
        monitor_scores = {
            "paired_cost_cusum": cost_cusum,
            "bounded_excess_cost_log_e": log_e,
            "predictive_loss_cusum": loss_cusum,
            "rbf_mmd_squared": mmd_daily,
        }
        forecasting = {}
        for name, score in monitor_scores.items():
            auc, ap, positives = _auc_ap(score, harm_labels)
            forecasting[name] = {
                "auc_for_next_20_date_harm": auc,
                "average_precision_for_next_20_date_harm": ap,
                "positive_harm_windows": positives,
            }

        monitor_rows = []
        for name, score in monitor_scores.items():
            threshold = {
                "paired_cost_cusum": cost_threshold,
                "bounded_excess_cost_log_e": math.log(1 / ALPHA),
                "predictive_loss_cusum": loss_threshold,
                "rbf_mmd_squared": mmd_threshold,
            }[name]
            finite = np.isfinite(score)
            crossings = np.flatnonzero(finite & (score >= threshold))
            monitor_rows.append(
                {
                    "monitor": name,
                    "threshold": threshold,
                    "first_crossing_date": (
                        str(np.datetime64(int(test_dates_unique[crossings[0]]), "D"))
                        if len(crossings)
                        else None
                    ),
                    "crossing_fraction_of_test_dates": float(
                        np.mean(finite & (score >= threshold))
                    ),
                    "maximum_score": float(np.nanmax(score)),
                    "threshold_status": (
                        "conditional-mean e-process threshold; validity assumptions unverified on CRSP"
                        if name == "bounded_excess_cost_log_e"
                        else "empirical calibration-period diagnostic threshold; no error guarantee"
                    ),
                    **forecasting[name],
                }
            )

        trajectory_rows = []
        for i, day in enumerate(test_dates_unique):
            trajectory_rows.append(
                {
                    "date": str(np.datetime64(int(day), "D")),
                    "mean_paired_excess_cost_5bps": float(test_cost[i]),
                    "mean_capped_squared_prediction_loss": float(test_loss_daily[i]),
                    "paired_cost_cusum": float(cost_cusum[i]),
                    "bounded_excess_cost_log_e": float(log_e[i]),
                    "rbf_mmd_squared": float(mmd_daily[i]) if np.isfinite(mmd_daily[i]) else None,
                    "next_20_date_harm_label": (
                        bool(harm_labels[i]) if np.isfinite(harm_labels[i]) else None
                    ),
                }
            )

        sensitivity = []
        for bps in TRANSACTION_COST_BPS:
            item = metrics_by_cost[f"test_{bps}bps"]
            sensitivity.append(item)

        report = {
            "experiment": "CRSP full-cohort retrospective decision-harm monitor comparison",
            "dataset": panel_manifest["dataset"],
            "dataset_version": panel_manifest["version"],
            "dataset_manifest_sha256": sha256(manifest_path),
            "observations_sha256": expected_hash,
            "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
            "seed": seed,
            "cohort_rule": "all panel test-split observations; one global model fit on all train rows; no test sampling",
            "rows_by_split": counts_by_split,
            "test_permnos": len(names),
            "test_dates": [
                str(np.datetime64(int(test_dates_unique[0]), "D")),
                str(np.datetime64(int(test_dates_unique[-1]), "D")),
            ],
            "model": "standardized Ridge(alpha=1), train-only exact median imputation and scaling",
            "model_device": fit_device,
            "candidate_policy": "long when train-only Ridge next-observed-return prediction is positive",
            "reference_policy": "long when same-date CRSP vwretd is positive",
            "primary_turnover_cost_bps": PRIMARY_BPS,
            "primary_event_weighted_excess_cost": float(primary_daily["test_diff"].mean()),
            "primary_two_way_cluster_date_block_interval_95": interval,
            "uncertainty": {
                "method": "product bootstrap: PERMNO resampling times circular 20-trading-date block resampling",
                "replicates": BOOTSTRAP_REPLICATES,
                "interpretation": "descriptive fixed-policy retrospective interval; does not account for model refitting uncertainty",
            },
            "split_policy_cost_metrics": list(metrics_by_cost.values()),
            "monitor_comparison": monitor_rows,
            "future_harm_forecast_definition": "evaluator-only indicator that mean paired candidate-minus-reference cost over the next 20 test dates is positive; overlapping hindsight labels, not a validated online target",
            "calibration": {
                "split": "2018-2019 calibration rows, with the train-only policy frozen",
                "cusum_threshold": "95th percentile of 2,000 circular 20-date block bootstrap maxima over a test-length horizon; empirical only",
                "mmd_reference": "first 20 calibration dates, uniformly sampled up to 256 rows; threshold is the 95th percentile of nonoverlapping calibration-window MMD² values",
                "eprocess": "bounded daily mean excess cost, epsilon=0, alpha=.05; bound 0.20 + 4*fee from clipped-return and binary-turnover envelope",
            },
            "limitations": [
                "The CRSP panel supplies one retrospective historical path, not independent null or harm episodes.",
                "CUSUM and MMD calibration thresholds are empirical diagnostics; calibration-period stationarity is unverified.",
                "The bounded e-process guarantee requires the stated conditional-on-past harm null, predictable frozen actions, complete outcomes, and correct bound; CRSP dependence and historical release times do not establish these assumptions.",
                "Date order is retrospective close-date order; label release times are not verified.",
                "Future-harm labels use outcomes only for evaluator-side retrospective ranking and cannot support a prospective alarm guarantee.",
                "Utility clips simple returns at 10 percent and applies imposed turnover charges; it is not a brokerage cost model.",
            ],
            "script_sha256": sha256(Path(__file__)),
            "created_utc": datetime.now(UTC).isoformat(),
        }
        import csv

        with (output / "split_cost_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(next(iter(metrics_by_cost.values())).keys())
            )
            writer.writeheader()
            writer.writerows(metrics_by_cost.values())
        with (output / "monitor_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(monitor_rows[0].keys()))
            writer.writeheader()
            writer.writerows(monitor_rows)
        pq.write_table(
            pa.Table.from_pylist(list(metrics_by_cost.values())),
            output / "split_cost_metrics.parquet",
        )
        pq.write_table(pa.Table.from_pylist(monitor_rows), output / "monitor_comparison.parquet")
        pq.write_table(pa.Table.from_pylist(trajectory_rows), output / "monitor_trajectory.parquet")
        with (output / "monitor_trajectory.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(trajectory_rows[0].keys()))
            writer.writeheader()
            writer.writerows(trajectory_rows)
        write_json(output / "report.json", report)
        checksums = [
            f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  {artifact.name}"
            for artifact in sorted(output.iterdir())
            if artifact.name != "checksums.sha256"
        ]
        (output / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        # Explicitly close Windows memory maps before TemporaryDirectory removes their files.
        for mapped in (cal_features_for_mmd, test_features_for_mmd, permno, dates):
            if isinstance(mapped, np.memmap):
                mapped.flush()
                mapped._mmap.close()  # type: ignore[attr-defined]
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--version")
    parser.add_argument("--batch-size", type=int, default=200_000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--output", type=Path, default=Path("outputs/crsp_monitor_comparison_full"))
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    evaluate(
        root=args.root,
        version=args.version,
        batch_size=args.batch_size,
        device_name=args.device,
        output=args.output,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
