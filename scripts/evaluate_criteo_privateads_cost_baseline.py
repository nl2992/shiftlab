"""Stream the CriteoPrivateAds cost-sensitive logistic development benchmark.

The runner follows the daily-block task contract, uses CUDA for fitting when
available, and writes only aggregate metrics and provenance. No transformed
dataset or impression-level predictions are persisted.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/raw/criteo_privatead/data"
DEFAULT_OUTPUT = (
    ROOT / "outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v1"
)
SOURCE_REVISION = "343645889b157f104ac23d0d07afa6a18115eb30"
SOURCE_AUDIT = ROOT / "data/reports/criteo_privatead_snapshot_audit.json"
DELAY_AUDIT = ROOT / "data/reports/criteo_privatead_delay_audit.json"
TASK_CONTRACT = ROOT / "papers/shiftguard_unified/criteo_privateads_task_contract.md"
BASE_DAYS = tuple(range(1, 14))
UPDATE_END_BY_DELAY = {2: 18, 1: 19, 0: 20}
EVALUATION_DAYS = tuple(range(21, 26))
TARGET_CTR = 0.005
COST_RATIOS = (1.0, 5.0, 20.0)
HASH_BUCKETS_PER_FIELD = 1 << 18
DEFAULT_BATCH_SIZE = 16_384
CALIBRATION_SAMPLE_CAP = 100_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_artifact_checksums(output: Path) -> dict[str, Any]:
    """Hash generated aggregate artifacts without recursively hashing this file."""
    files = [
        path
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "artifact_checksums.json"
    ]
    result = {
        "scope": "aggregate-only result artifacts; no row-level predictions or raw observations",
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in files
        },
    }
    (output / "artifact_checksums.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def feature_contract(schema: pa.Schema) -> tuple[list[str], list[str], str]:
    """Infer source-available features from publisher group names and types."""
    prefixes = (
        "features_kv_bits_constrained_",
        "features_kv_not_constrained_",
        "features_browser_bits_constrained_",
        "features_ctx_not_constrained_",
    )
    eligible = [field for field in schema if field.name.startswith(prefixes)]
    unavailable = [field for field in schema if field.name.startswith("features_not_available_")]
    numeric = [field.name for field in eligible if pa.types.is_floating(field.type)]
    categorical = [field.name for field in eligible if pa.types.is_int64(field.type)]
    list_fields = [
        field
        for field in eligible
        if pa.types.is_list(field.type) and pa.types.is_int64(field.type.value_type)
    ]
    unsupported = [
        field.name
        for field in eligible
        if field.name not in numeric and field.name not in categorical and field not in list_fields
    ]
    if len(eligible) != 58 or len(unavailable) != 80:
        raise ValueError(
            f"unexpected groups: eligible={len(eligible)}, unavailable={len(unavailable)}"
        )
    if (len(numeric), len(categorical), len(list_fields), unsupported) != (44, 13, 1, []):
        raise ValueError(
            f"unexpected types: continuous={len(numeric)}, integer={len(categorical)}, "
            f"list={len(list_fields)}, unsupported={unsupported}"
        )
    return numeric, categorical, list_fields[0].name


def negative_case_control_weight(sample_ctr: float, target_ctr: float = TARGET_CTR) -> float:
    """Negative-example weight that maps sample CTR to the target CTR."""
    if not 0 < sample_ctr < 1 or not 0 < target_ctr < 1:
        raise ValueError("sample and target CTR must be strictly between zero and one")
    return sample_ctr * (1 - target_ctr) / (target_ctr * (1 - sample_ctr))


def _splitmix64(values: np.ndarray, field_id: int) -> np.ndarray:
    """Stable field-specific hashing for anonymized integer categories."""
    value = np.asarray(values, dtype=np.uint64).copy()
    salt = np.uint64(((field_id + 1) * 0x9E3779B97F4A7C15) & ((1 << 64) - 1))
    value ^= salt
    value += np.uint64(0x9E3779B97F4A7C15)
    value = (value ^ (value >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    value = (value ^ (value >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    value ^= value >> np.uint64(31)
    return (value % np.uint64(HASH_BUCKETS_PER_FIELD - 1) + 1).astype(np.int64)


def _filled_numpy(column: pa.Array, fill_value: float = 0) -> np.ndarray:
    return pc.fill_null(column, fill_value).to_numpy(zero_copy_only=False)


def prepare_batch(
    batch: pa.RecordBatch,
    numeric_fields: list[str],
    categorical_fields: list[str],
    list_field: str,
    means: np.ndarray,
    scales: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Encode an Arrow batch; null masks are explicit and list categories are multi-hot."""
    size = batch.num_rows
    numeric = np.empty((size, len(numeric_fields) * 2), dtype=np.float32)
    for index, name in enumerate(numeric_fields):
        column = batch.column(batch.schema.get_field_index(name))
        missing = np.asarray(column.is_null().to_numpy(zero_copy_only=False), dtype=bool)
        values = np.asarray(_filled_numpy(column, 0.0), dtype=np.float64)
        numeric[:, index] = np.clip((values - means[index]) / scales[index], -10.0, 10.0)
        numeric[:, len(numeric_fields) + index] = missing

    row_ids = np.arange(size, dtype=np.int64)
    codes_by_field: list[np.ndarray] = []
    rows_by_field: list[np.ndarray] = []
    for field_id, name in enumerate(categorical_fields):
        column = batch.column(batch.schema.get_field_index(name))
        missing = np.asarray(column.is_null().to_numpy(zero_copy_only=False), dtype=bool)
        values = np.asarray(_filled_numpy(column, 0), dtype=np.int64).astype(np.uint64)
        buckets = _splitmix64(values, field_id)
        buckets[missing] = 0
        codes_by_field.append(field_id * HASH_BUCKETS_PER_FIELD + buckets)
        rows_by_field.append(row_ids)

    list_column = batch.column(batch.schema.get_field_index(list_field))
    lengths = np.asarray(
        pc.fill_null(pc.list_value_length(list_column), 0).to_numpy(), dtype=np.int64
    )
    flat_values = np.asarray(
        pc.list_flatten(list_column).to_numpy(zero_copy_only=False), dtype=np.int64
    )
    list_field_id = len(categorical_fields)
    if flat_values.size:
        codes_by_field.append(
            list_field_id * HASH_BUCKETS_PER_FIELD + _splitmix64(flat_values, list_field_id)
        )
        rows_by_field.append(np.repeat(row_ids, lengths))
    empty = lengths == 0
    if empty.any():
        codes_by_field.append(
            list_field_id * HASH_BUCKETS_PER_FIELD + np.zeros(int(empty.sum()), dtype=np.int64)
        )
        rows_by_field.append(row_ids[empty])

    codes = np.concatenate(codes_by_field).astype(np.int64, copy=False)
    rows = np.concatenate(rows_by_field).astype(np.int64, copy=False)
    labels = np.asarray(
        batch.column(batch.schema.get_field_index("is_clicked")).to_numpy(), dtype=np.float32
    )
    return numeric, codes, rows, labels


def count_days(dataset: ds.Dataset, days: range, batch_size: int) -> dict[int, dict[str, int]]:
    """Count rows and positive labels by day, retaining no observations."""
    result: dict[int, dict[str, int]] = {}
    for day in days:
        rows = positives = 0
        scanner = dataset.scanner(
            columns=["is_clicked"], filter=ds.field("day_int") == day, batch_size=batch_size
        )
        for batch in scanner.to_batches():
            labels = np.asarray(batch.column(0).to_numpy(), dtype=np.int8)
            rows += labels.size
            positives += int(labels.sum())
        result[day] = {"rows": rows, "positive_rows": positives}
        print(f"counted day={day} rows={rows} positives={positives}", flush=True)
    return result


def estimate_numeric_scaler(
    data_path: Path,
    numeric_fields: list[str],
    seed: int,
    shards_per_day: int,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Estimate continuous scaling from deterministic shards in training days only."""
    rng = np.random.default_rng(seed)
    sums = np.zeros(len(numeric_fields), dtype=np.float64)
    squares = np.zeros(len(numeric_fields), dtype=np.float64)
    counts = np.zeros(len(numeric_fields), dtype=np.int64)
    for day in BASE_DAYS:
        shards = sorted((data_path / f"day_int={day}").glob("*.parquet"))
        if not shards:
            raise FileNotFoundError(f"no Parquet shards for training day {day}")
        selected = rng.choice(len(shards), size=min(shards_per_day, len(shards)), replace=False)
        for shard_index in sorted(selected.tolist()):
            parquet = pq.ParquetFile(shards[shard_index])
            for batch in parquet.iter_batches(batch_size=batch_size, columns=numeric_fields):
                for field_index, name in enumerate(numeric_fields):
                    column = batch.column(batch.schema.get_field_index(name))
                    missing = np.asarray(
                        column.is_null().to_numpy(zero_copy_only=False), dtype=bool
                    )
                    values = np.asarray(_filled_numpy(column, 0.0), dtype=np.float64)
                    valid = values[~missing]
                    sums[field_index] += valid.sum(dtype=np.float64)
                    squares[field_index] += np.square(valid).sum(dtype=np.float64)
                    counts[field_index] += valid.size
    means = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0)
    variances = np.divide(squares, counts, out=np.zeros_like(squares), where=counts > 0) - means**2
    scales = np.sqrt(np.maximum(variances, 0.0))
    scales[scales < 1e-8] = 1.0
    return means, scales, counts


class HashedLogistic(nn.Module):
    def __init__(self, numeric_width: int, category_fields: int) -> None:
        super().__init__()
        self.linear = nn.Linear(numeric_width, 1, bias=True)
        self.categories = nn.Embedding(category_fields * HASH_BUCKETS_PER_FIELD, 1, sparse=True)
        nn.init.zeros_(self.linear.weight)
        nn.init.zeros_(self.categories.weight)
        with torch.no_grad():
            self.linear.bias.fill_(math.log(TARGET_CTR / (1 - TARGET_CTR)))

    def forward(
        self, numeric: torch.Tensor, category_indices: torch.Tensor, category_rows: torch.Tensor
    ) -> torch.Tensor:
        category_logits = self.categories(category_indices).squeeze(-1)
        summed = torch.zeros(numeric.shape[0], device=numeric.device, dtype=numeric.dtype)
        summed.index_add_(0, category_rows, category_logits)
        return self.linear(numeric).squeeze(-1) + summed


def make_optimizers(model: HashedLogistic, learning_rate: float) -> tuple[Any, Any]:
    return (
        torch.optim.AdamW(model.linear.parameters(), lr=learning_rate, weight_decay=1e-5),
        torch.optim.SparseAdam(model.categories.parameters(), lr=learning_rate),
    )


def train_day(
    dataset: ds.Dataset,
    day: int,
    model: HashedLogistic,
    optimizers: tuple[Any, Any],
    numeric_fields: list[str],
    categorical_fields: list[str],
    list_field: str,
    means: np.ndarray,
    scales: np.ndarray,
    sample_ctr: float,
    device: torch.device,
    batch_size: int,
    max_batches: int | None,
) -> int:
    columns = [*numeric_fields, *categorical_fields, list_field, "is_clicked"]
    scanner = dataset.scanner(
        columns=columns, filter=ds.field("day_int") == day, batch_size=batch_size
    )
    dense_optimizer, sparse_optimizer = optimizers
    batches = 0
    model.train()
    neg_weight = negative_case_control_weight(sample_ctr)
    for batch in scanner.to_batches():
        # Fragmented Hive scans can yield zero-row batches for a partition.
        # They must not count toward --max-batches or enter an optimizer step.
        if batch.num_rows == 0:
            continue
        num_np, codes_np, rows_np, y_np = prepare_batch(
            batch, numeric_fields, categorical_fields, list_field, means, scales
        )
        num = torch.from_numpy(num_np).to(device)
        codes = torch.from_numpy(codes_np).to(device)
        row_ids = torch.from_numpy(rows_np).to(device)
        labels = torch.from_numpy(y_np).to(device)
        weights = torch.where(labels > 0.5, 1.0, neg_weight)
        dense_optimizer.zero_grad(set_to_none=True)
        sparse_optimizer.zero_grad(set_to_none=True)
        logits = model(num, codes, row_ids)
        loss = (
            F.binary_cross_entropy_with_logits(logits, labels, reduction="none") * weights
        ).sum()
        loss = loss / weights.sum().clamp_min(1.0)
        loss = loss + 0.5e-5 * model.linear.weight.square().sum()
        loss = loss + 0.5e-5 * model.categories(torch.unique(codes)).square().sum()
        loss.backward()
        dense_optimizer.step()
        sparse_optimizer.step()
        batches += 1
        if max_batches is not None and batches >= max_batches:
            break
    return batches


@torch.no_grad()
def batch_logits(
    model: HashedLogistic,
    batch: pa.RecordBatch,
    numeric_fields: list[str],
    categorical_fields: list[str],
    list_field: str,
    means: np.ndarray,
    scales: np.ndarray,
    device: torch.device,
    offset: float = 0.0,
) -> tuple[torch.Tensor, torch.Tensor]:
    num_np, codes_np, rows_np, y_np = prepare_batch(
        batch, numeric_fields, categorical_fields, list_field, means, scales
    )
    num = torch.from_numpy(num_np).to(device)
    codes = torch.from_numpy(codes_np).to(device)
    rows = torch.from_numpy(rows_np).to(device)
    model.eval()
    return model(num, codes, rows) + offset, torch.from_numpy(y_np).to(device)


def fit_intercept(logits: np.ndarray, labels: np.ndarray, weights: np.ndarray) -> float:
    """Fit an intercept-only weighted logistic recalibration."""
    if logits.size == 0:
        raise ValueError("no mature update examples sampled for recalibration")
    offset = 0.0
    for _ in range(40):
        probability = 1.0 / (1.0 + np.exp(-np.clip(logits + offset, -35, 35)))
        grad = np.sum(weights * (probability - labels), dtype=np.float64)
        hess = np.sum(weights * probability * (1 - probability), dtype=np.float64)
        if hess <= 1e-12:
            break
        step = float(np.clip(grad / hess, -2.0, 2.0))
        offset = float(np.clip(offset - step, -12.0, 12.0))
        if abs(step) < 1e-8:
            break
    return offset


def model_digest(model: HashedLogistic, offset: float = 0.0) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    digest.update(float(offset).hex().encode())
    return digest.hexdigest()


def evaluate(
    dataset: ds.Dataset,
    day_counts: dict[int, dict[str, int]],
    models: dict[str, tuple[HashedLogistic, float]],
    numeric_fields: list[str],
    categorical_fields: list[str],
    list_field: str,
    means: np.ndarray,
    scales: np.ndarray,
    device: torch.device,
    batch_size: int,
    max_batches: int | None,
) -> pd.DataFrame:
    """Evaluate with paired source rows and only aggregate metrics retained."""
    metric_names = [
        "n_rows",
        "n_positive",
        "unweighted_logloss",
        "unweighted_brier",
        "weighted_logloss",
        "weighted_brier",
        "weighted_prediction_sum",
        "weight_sum",
        *[f"weighted_cost_fn_over_fp_{ratio:g}" for ratio in COST_RATIOS],
    ]
    totals = {
        (day, name): torch.zeros(len(metric_names), dtype=torch.float64, device=device)
        for day in EVALUATION_DAYS
        for name in models
    }
    columns = [*numeric_fields, *categorical_fields, list_field, "is_clicked"]
    for day in EVALUATION_DAYS:
        sample_ctr = day_counts[day]["positive_rows"] / day_counts[day]["rows"]
        negative_weight = negative_case_control_weight(sample_ctr)
        scanner = dataset.scanner(
            columns=columns,
            filter=ds.field("day_int") == day,
            batch_size=batch_size,
        )
        batches = 0
        for batch in scanner.to_batches():
            if batch.num_rows == 0:
                continue
            for model_name, (model, intercept) in models.items():
                logits, labels = batch_logits(
                    model,
                    batch,
                    numeric_fields,
                    categorical_fields,
                    list_field,
                    means,
                    scales,
                    device,
                    intercept,
                )
                probability = torch.sigmoid(logits)
                weights = torch.where(labels > 0.5, 1.0, negative_weight)
                loss = F.binary_cross_entropy_with_logits(logits, labels, reduction="none")
                brier = (probability - labels).square()
                row = totals[(day, model_name)]
                row[0] += labels.numel()
                row[1] += labels.sum().double()
                row[2] += loss.sum().double()
                row[3] += brier.sum().double()
                row[4] += (loss * weights).sum().double()
                row[5] += (brier * weights).sum().double()
                row[6] += (probability * weights).sum().double()
                row[7] += weights.sum().double()
                for index, ratio in enumerate(COST_RATIOS):
                    threshold = 1.0 / (1.0 + ratio)
                    positive = probability >= threshold
                    fp = (positive & (labels < 0.5)).double() * weights
                    fn = ((~positive) & (labels > 0.5)).double() * weights
                    row[8 + index] += (fp.sum() + ratio * fn.sum()).double()
            batches += 1
            if max_batches is not None and batches >= max_batches:
                break
        print(f"evaluated day={day} batches={batches}", flush=True)

    rows: list[dict[str, Any]] = []
    for day in EVALUATION_DAYS:
        for model_name in models:
            sums = totals[(day, model_name)].cpu().numpy()
            n_rows = float(sums[0])
            weight_sum = float(sums[7])
            row: dict[str, Any] = {
                "day_int": day,
                "model": model_name,
                "n_rows": int(n_rows),
                "n_positive_sample": int(sums[1]),
                "sample_ctr": float(sums[1] / n_rows),
                "unweighted_logloss": float(sums[2] / n_rows),
                "unweighted_brier": float(sums[3] / n_rows),
                "weighted_logloss_target_0_005": float(sums[4] / weight_sum),
                "weighted_brier_target_0_005": float(sums[5] / weight_sum),
                "weighted_calibration_ratio_target_0_005": float(
                    sums[6] / (TARGET_CTR * weight_sum)
                ),
                "weight_sum": weight_sum,
            }
            for index, ratio in enumerate(COST_RATIOS):
                row[f"weighted_decision_cost_fn_over_fp_{ratio:g}"] = float(
                    sums[8 + index] / weight_sum
                )
            rows.append(row)
    return pd.DataFrame(rows)


def run(args: argparse.Namespace) -> dict[str, Any]:
    data_path = args.data.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output}")
    if not data_path.exists():
        raise FileNotFoundError(data_path)
    for required in (SOURCE_AUDIT, DELAY_AUDIT, TASK_CONTRACT):
        if not required.exists():
            raise FileNotFoundError(f"required source audit/contract missing: {required}")

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    use_cuda = args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available())
    device = torch.device("cuda" if use_cuda else "cpu")
    parquet_files = sorted(data_path.rglob("*.parquet"))
    if len(parquet_files) != 288:
        raise ValueError(f"expected 288 source Parquet files, found {len(parquet_files)}")
    dataset = ds.dataset(
        parquet_files,
        format="parquet",
        partitioning="hive",
        partition_base_dir=str(data_path),
    )
    numeric_fields, categorical_fields, list_field = feature_contract(dataset.schema)
    print(
        f"feature contract continuous={len(numeric_fields)} "
        f"hashed_integer={len(categorical_fields)} hashed_list=1 device={device}",
        flush=True,
    )

    started = time.perf_counter()
    day_counts = count_days(dataset, range(1, 26), args.batch_size)
    means, scales, scaler_counts = estimate_numeric_scaler(
        data_path, numeric_fields, args.seed, args.stats_shards_per_day, args.batch_size
    )
    numeric_width = 2 * len(numeric_fields)
    category_fields = len(categorical_fields) + 1

    incumbent = HashedLogistic(numeric_width, category_fields).to(device)
    incumbent_optimizers = make_optimizers(incumbent, args.learning_rate)
    base_batches = 0
    for day in BASE_DAYS:
        sample_ctr = (day_counts[day]["positive_rows"] + 0.5) / (day_counts[day]["rows"] + 1)
        base_batches += train_day(
            dataset,
            day,
            incumbent,
            incumbent_optimizers,
            numeric_fields,
            categorical_fields,
            list_field,
            means,
            scales,
            sample_ctr,
            device,
            args.batch_size,
            args.max_batches,
        )
        print(f"trained incumbent day={day} cumulative_batches={base_batches}", flush=True)

    update_model = copy.deepcopy(incumbent)
    update_optimizers = make_optimizers(update_model, args.learning_rate)
    update_rows = {
        delay: sum(day_counts[day]["rows"] for day in range(14, end + 1))
        for delay, end in UPDATE_END_BY_DELAY.items()
    }
    sample_rates = {}
    for delay, count in update_rows.items():
        planned = count
        if args.max_batches is not None:
            n_days = UPDATE_END_BY_DELAY[delay] - 13
            planned = min(count, n_days * args.max_batches * args.batch_size)
        sample_rates[delay] = min(1.0, CALIBRATION_SAMPLE_CAP / max(1, planned))
    calibration_rng = {
        delay: np.random.default_rng(args.seed + 10_000 + delay) for delay in UPDATE_END_BY_DELAY
    }
    calibration: dict[int, list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = {
        delay: [] for delay in UPDATE_END_BY_DELAY
    }
    snapshots: dict[int, dict[str, torch.Tensor]] = {}
    update_batches = 0
    for day in range(14, 21):
        columns = [*numeric_fields, *categorical_fields, list_field, "is_clicked"]
        scanner = dataset.scanner(
            columns=columns, filter=ds.field("day_int") == day, batch_size=args.batch_size
        )
        batches = 0
        for batch in scanner.to_batches():
            if batch.num_rows == 0:
                continue
            num_np, codes_np, rows_np, labels_np = prepare_batch(
                batch, numeric_fields, categorical_fields, list_field, means, scales
            )
            num = torch.from_numpy(num_np).to(device)
            codes = torch.from_numpy(codes_np).to(device)
            row_ids = torch.from_numpy(rows_np).to(device)
            labels = torch.from_numpy(labels_np).to(device)
            with torch.no_grad():
                incumbent_logits = incumbent(num, codes, row_ids).cpu().numpy()
            for delay, end in UPDATE_END_BY_DELAY.items():
                if day <= end:
                    selected = calibration_rng[delay].random(labels_np.size) < sample_rates[delay]
                    if selected.any():
                        sample_ctr = (day_counts[day]["positive_rows"] + 0.5) / (
                            day_counts[day]["rows"] + 1
                        )
                        weight = negative_case_control_weight(sample_ctr)
                        y_sample = labels_np[selected]
                        weights = np.where(y_sample > 0.5, 1.0, weight)
                        calibration[delay].append((incumbent_logits[selected], y_sample, weights))

            sample_ctr = (day_counts[day]["positive_rows"] + 0.5) / (day_counts[day]["rows"] + 1)
            negative_weight = negative_case_control_weight(sample_ctr)
            weights = torch.where(
                labels > 0.5,
                torch.ones_like(labels),
                torch.full_like(labels, negative_weight),
            )
            dense_optimizer, sparse_optimizer = update_optimizers
            dense_optimizer.zero_grad(set_to_none=True)
            sparse_optimizer.zero_grad(set_to_none=True)
            update_model.train()
            logits = update_model(num, codes, row_ids)
            loss = (
                F.binary_cross_entropy_with_logits(logits, labels, reduction="none") * weights
            ).sum()
            loss = loss / weights.sum().clamp_min(1.0)
            loss = loss + 0.5e-5 * update_model.linear.weight.square().sum()
            loss = loss + 0.5e-5 * update_model.categories(torch.unique(codes)).square().sum()
            loss.backward()
            dense_optimizer.step()
            sparse_optimizer.step()
            batches += 1
            update_batches += 1
            if args.max_batches is not None and batches >= args.max_batches:
                break
        for delay, end in UPDATE_END_BY_DELAY.items():
            if day == end:
                snapshots[delay] = copy.deepcopy(update_model.state_dict())
        print(f"updated candidate day={day} batches={batches}", flush=True)

    candidates: dict[int, HashedLogistic] = {}
    for delay in UPDATE_END_BY_DELAY:
        candidate = HashedLogistic(numeric_width, category_fields).to(device)
        candidate.load_state_dict(snapshots[delay])
        candidates[delay] = candidate

    offsets: dict[int, float] = {}
    sampled_calibration_rows: dict[int, int] = {}
    for delay, parts in calibration.items():
        logits = np.concatenate([part[0] for part in parts]) if parts else np.empty(0)
        labels = np.concatenate([part[1] for part in parts]) if parts else np.empty(0)
        weights = np.concatenate([part[2] for part in parts]) if parts else np.empty(0)
        if logits.size > CALIBRATION_SAMPLE_CAP:
            keep = np.random.default_rng(args.seed + delay).choice(
                logits.size, size=CALIBRATION_SAMPLE_CAP, replace=False
            )
            logits, labels, weights = logits[keep], labels[keep], weights[keep]
        offsets[delay] = fit_intercept(logits, labels, weights)
        sampled_calibration_rows[delay] = int(logits.size)

    models: dict[str, tuple[HashedLogistic, float]] = {
        "frozen_days_1_13": (incumbent, 0.0),
        "updated_2day": (candidates[2], 0.0),
        "updated_1day": (candidates[1], 0.0),
        "updated_immediate": (candidates[0], 0.0),
        "recalibrated_2day": (incumbent, offsets[2]),
        "recalibrated_1day": (incumbent, offsets[1]),
        "recalibrated_immediate": (incumbent, offsets[0]),
    }
    metrics = evaluate(
        dataset,
        day_counts,
        models,
        numeric_fields,
        categorical_fields,
        list_field,
        means,
        scales,
        device,
        args.batch_size,
        args.max_batches,
    )

    summary_rows: list[dict[str, Any]] = []
    for model_name, group in metrics.groupby("model", sort=False):
        row: dict[str, Any] = {
            "model": model_name,
            "n_rows": int(group["n_rows"].sum()),
            "n_positive_sample": int(group["n_positive_sample"].sum()),
            "unweighted_logloss": float(
                np.average(group["unweighted_logloss"], weights=group["n_rows"])
            ),
            "unweighted_brier": float(
                np.average(group["unweighted_brier"], weights=group["n_rows"])
            ),
            "weighted_logloss_target_0_005": float(
                np.average(group["weighted_logloss_target_0_005"], weights=group["weight_sum"])
            ),
            "weighted_brier_target_0_005": float(
                np.average(group["weighted_brier_target_0_005"], weights=group["weight_sum"])
            ),
            "weighted_calibration_ratio_target_0_005": float(
                np.average(
                    group["weighted_calibration_ratio_target_0_005"],
                    weights=group["weight_sum"],
                )
            ),
            "weight_sum": float(group["weight_sum"].sum()),
        }
        for ratio in COST_RATIOS:
            key = f"weighted_decision_cost_fn_over_fp_{ratio:g}"
            row[key] = float(np.average(group[key], weights=group["weight_sum"]))
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    contrast_rows: list[dict[str, Any]] = []
    for _, metric_row in metrics.iterrows():
        for ratio in COST_RATIOS:
            key = f"weighted_decision_cost_fn_over_fp_{ratio:g}"
            frozen_cost = float(
                metrics.loc[
                    (metrics["day_int"] == metric_row["day_int"])
                    & (metrics["model"] == "frozen_days_1_13"),
                    key,
                ].iloc[0]
            )
            if metric_row["model"] != "frozen_days_1_13":
                contrast_rows.append(
                    {
                        "day_int": int(metric_row["day_int"]),
                        "model": metric_row["model"],
                        "fn_over_fp": ratio,
                        "frozen_cost_minus_candidate_cost": (frozen_cost - float(metric_row[key])),
                    }
                )
    contrasts = pd.DataFrame(contrast_rows)

    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)
    metrics.to_parquet(output / "daily_metrics.parquet", index=False)
    summary.to_csv(output / "summary_metrics.csv", index=False)
    contrasts.to_csv(output / "paired_cost_contrasts.csv", index=False)
    elapsed = time.perf_counter() - started
    source_files = (Path(__file__), SOURCE_AUDIT, DELAY_AUDIT, TASK_CONTRACT)
    manifest = {
        "schema_version": "1.0.0",
        "status": "development_only" if args.max_batches is None else "smoke_not_research",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "dataset": "CriteoPrivateAds",
        "source_revision": SOURCE_REVISION,
        "source_license": "CC BY-SA 4.0",
        "counts_by_day": day_counts,
        "protocol": {
            "task": "is_clicked prediction with non-performative cost-sensitive classification decisions",
            "feature_counts": {
                "continuous": len(numeric_fields),
                "hashed_scalar_categories": len(categorical_fields),
                "hashed_list_categories": 1,
                "publisher_unavailable_features_excluded": 80,
                "identifiers_as_predictors": False,
                "delay_fields_as_predictors": False,
            },
            "base_fit_days": list(BASE_DAYS),
            "updated_model_last_mature_day": {
                str(delay): end for delay, end in UPDATE_END_BY_DELAY.items()
            },
            "evaluation_days": list(EVALUATION_DAYS),
            "publisher_validation_days_excluded": list(range(26, 31)),
            "feedback_model": "label from day d is available at the start of day d + delay_days + 1",
            "delays_days": list(UPDATE_END_BY_DELAY),
            "target_ctr": TARGET_CTR,
            "negative_weight_formula": "p_sample * (1 - target_ctr) / (target_ctr * (1 - p_sample))",
            "cost_ratios_fn_over_fp": list(COST_RATIOS),
            "decision_threshold": "1 / (1 + C_FN/C_FP)",
            "scaler": "training-only means and standard deviations from deterministic source shards",
            "categorical_encoder": {
                "algorithm": "field-specific SplitMix64 hashing",
                "buckets_per_field": HASH_BUCKETS_PER_FIELD,
                "seed": args.seed,
            },
            "recalibration": {
                "method": "intercept-only weighted logistic fit on mature update-block predictions",
                "sample_rows_by_delay": {str(k): v for k, v in sampled_calibration_rows.items()},
                "offsets_by_delay": {str(k): v for k, v in offsets.items()},
            },
            "resource_use": {
                "device": str(device),
                "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
                "batch_size": args.batch_size,
                "scaler_valid_values_by_feature": {
                    name: int(count)
                    for name, count in zip(numeric_fields, scaler_counts, strict=True)
                },
                "base_batches": base_batches,
                "update_batches": update_batches,
                "max_batches_per_day_smoke_limit": args.max_batches,
                "elapsed_seconds": elapsed,
            },
            "model_sha256": {
                "frozen_days_1_13": model_digest(incumbent),
                "updated_2day": model_digest(candidates[2]),
                "updated_1day": model_digest(candidates[1]),
                "updated_immediate": model_digest(candidates[0]),
                "recalibrated_2day": model_digest(incumbent, offsets[2]),
                "recalibrated_1day": model_digest(incumbent, offsets[1]),
                "recalibrated_immediate": model_digest(incumbent, offsets[0]),
            },
            "label_rows_used_for_fitting": int(
                sum(day_counts[day]["rows"] for day in BASE_DAYS)
                + sum(day_counts[day]["rows"] for day in range(14, 21))
            ),
        },
        "outputs": {
            "daily_metrics": "daily_metrics.parquet",
            "aggregate_metrics": "summary_metrics.csv",
            "paired_cost_differences": "paired_cost_contrasts.csv",
            "artifact_checksums": "artifact_checksums.json",
            "row_level_predictions_written": 0,
            "transformed_dataset_copy_written": False,
        },
        "input_artifact_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in source_files
        },
        "limitations": [
            "Retrospective development only. Days 26-30 were publisher baseline validation and are excluded.",
            "The within-day sequence is not a verified global event clock; all evaluation is daily-block aggregate.",
            "Delay variants are explicit maturity assumptions, not observed per-row label releases.",
            "Costs are imposed normalized scenarios; no auction, bid, revenue, or causal policy value is identified.",
            "Five evaluation blocks are insufficient for reliable cluster uncertainty or online false-alarm calibration.",
            "This regularized hashed-feature logistic baseline is not a reproduction of the publisher's complete training pipeline.",
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    report = [
        "# CriteoPrivateAds cost-sensitive logistic development run",
        "",
        f"Status: {manifest['status']}. Source revision: {SOURCE_REVISION}.",
        "",
        "The run compares the frozen day-1–13 model, incremental candidates trained through the last mature day under 2-day/1-day/immediate feedback assumptions, and intercept-recalibrated incumbent variants. Days 21–25 are internal chronological evaluation; publisher validation days 26–30 are excluded.",
        "",
        "Metrics use publisher case-control weights for a target CTR of 0.5%, and also report the sampled distribution. False-negative/false-positive ratios 1, 5, and 20 are imposed research scenarios, not monetary costs.",
        "",
        f"Training labels used: {manifest['protocol']['label_rows_used_for_fitting']:,}.",
        f"Rows scored per model: {int(metrics['n_rows'].sum() / len(models)):,}.",
        f"Compute device: {device}. Elapsed: {elapsed:.1f} seconds.",
        "",
        "## Aggregate metrics",
        "",
        summary.to_markdown(index=False),
        "",
        "## Paired decision-cost differences",
        "",
        "Positive values favor the candidate over the frozen incumbent.",
        "",
        contrasts.groupby(["model", "fn_over_fp"], as_index=False)[
            "frozen_cost_minus_candidate_cost"
        ]
        .mean()
        .to_markdown(index=False),
        "",
        "The five day blocks support descriptive comparisons only, not reliable cluster intervals. The manifest records hashes, timing assumptions, and excluded information.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    write_artifact_checksums(output)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--stats-shards-per-day", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--max-batches", type=int, default=None)
    args = parser.parse_args()
    if args.batch_size < 1 or args.stats_shards_per_day < 1:
        parser.error("batch size and scaler shard count must be positive")
    if args.learning_rate <= 0 or (args.max_batches is not None and args.max_batches < 1):
        parser.error("learning rate and max-batches must be positive")
    result = run(args)
    print(
        json.dumps(
            {
                "status": result["status"],
                "device": result["protocol"]["resource_use"]["device"],
                "elapsed_seconds": result["protocol"]["resource_use"]["elapsed_seconds"],
                "output": str(args.output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
