"""GPU diagnostic for whether CUVET treatment is predictable from released features.

Reads deterministic train-only CSV byte ranges into bounded memory, fits
feature-only multinomial models on CUDA when available, and writes aggregate
metrics only. This is a diagnostic for observed-feature assignment dependence,
not proof of randomization or a formal test of the assignment mechanism.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

REPO_ID = "anonadata/CUVET-policy"
REVISION = "36583ac60379ed83fd375c84d2bf8ce1c73869c1"
TRAIN_FILE = "cuvet_policy_train.csv"
TRAIN_BYTES = 10_317_675_360
TRAIN_OID = "f3700741375c68a267de6ed8eae6b05652766ec8"
BASE_URL = f"https://huggingface.co/datasets/{REPO_ID}/resolve/{REVISION}/{TRAIN_FILE}"
RANGE_BYTES = 1024 * 1024
RANGE_COUNT = 128
SEED = 20261026
ARMS = [0.8, 0.9, 1.0, 1.1, 1.2]
FEATURES = ["f0", "f1", "f2", "f3", "f4"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def sample_train_ranges() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    request = urllib.request.Request(
        BASE_URL,
        method="HEAD",
        headers={"User-Agent": "ShiftLab-CUVET-assignment-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        actual_size = int(response.headers.get("Content-Length", "0"))
        etag = response.headers.get("ETag")
    if actual_size != TRAIN_BYTES:
        raise RuntimeError(f"Pinned train size mismatch: {actual_size} != {TRAIN_BYTES}")

    rng = random.Random(SEED)
    offsets: set[int] = set()
    while len(offsets) < RANGE_COUNT:
        offsets.add(rng.randrange(1, actual_size - RANGE_BYTES))

    features: list[list[float]] = []
    labels: list[int] = []
    range_groups: list[int] = []
    malformed = 0
    start = time.monotonic()
    expected_header: list[str] | None = None
    for range_number, offset in enumerate(sorted(offsets), start=1):
        range_request = urllib.request.Request(
            BASE_URL,
            headers={
                "Accept-Encoding": "identity",
                "Range": f"bytes={offset}-{offset + RANGE_BYTES - 1}",
                "User-Agent": "ShiftLab-CUVET-assignment-audit/1.0",
            },
        )
        with urllib.request.urlopen(range_request, timeout=60) as response:
            if response.status != 206:
                raise RuntimeError(f"Expected HTTP 206, got {response.status}")
            chunk = response.read(RANGE_BYTES)
        lines = chunk.split(b"\n")
        if len(lines) < 3:
            malformed += 1
            continue
        text = b"\n".join(lines[1:-1]).decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text, newline=""))
        for row in reader:
            if not row:
                continue
            if expected_header is None:
                # Range reads start in the middle of a row; use the known schema.
                expected_header = [
                    "",
                    "f3",
                    "f0",
                    "f1",
                    "f4",
                    "f2",
                    "policy",
                    "spend",
                    "value",
                    "is_val",
                ]
            if len(row) != len(expected_header):
                malformed += 1
                continue
            try:
                x = [float(row[expected_header.index(feature)]) for feature in FEATURES]
                policy = float(row[expected_header.index("policy")])
                arm = min(range(len(ARMS)), key=lambda index: abs(ARMS[index] - policy))
                if abs(ARMS[arm] - policy) > 1e-8:
                    malformed += 1
                    continue
            except (ValueError, IndexError):
                malformed += 1
                continue
            features.append(x)
            labels.append(arm)
            range_groups.append(range_number - 1)
        if range_number % 32 == 0:
            print(
                json.dumps(
                    {
                        "stage": "range_sampling",
                        "ranges_read": range_number,
                        "rows_in_memory": len(labels),
                        "elapsed_seconds": round(time.monotonic() - start, 1),
                    }
                ),
                flush=True,
            )

    audit = {
        "source_revision": REVISION,
        "train_file": TRAIN_FILE,
        "train_bytes": actual_size,
        "train_git_oid": TRAIN_OID,
        "etag": etag,
        "ranges_read": len(offsets),
        "range_bytes": RANGE_BYTES,
        "bytes_read_upper_bound": len(offsets) * RANGE_BYTES,
        "rows_sampled": len(labels),
        "malformed_or_boundary_rows_skipped": malformed,
        "elapsed_seconds": round(time.monotonic() - start, 1),
        "raw_rows_persisted": False,
        "uses_outcome_columns": False,
    }
    return (
        np.asarray(features, dtype=np.float32),
        np.asarray(labels, dtype=np.int64),
        np.asarray(range_groups, dtype=np.int64),
        audit,
    )


class MultinomialLogit(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(len(FEATURES), len(ARMS))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


class FeatureMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(len(FEATURES), 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, len(ARMS)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


def fit_model(
    model: nn.Module,
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_validation: torch.Tensor,
    y_validation: torch.Tensor,
    *,
    epochs: int,
    patience: int,
    seed: int,
) -> tuple[nn.Module, int, float]:
    torch.manual_seed(seed)
    model = model.to(x_train.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    best_state: dict[str, torch.Tensor] | None = None
    best_loss = float("inf")
    best_epoch = 0
    stale = 0
    batch_size = 4096
    for epoch in range(1, epochs + 1):
        model.train()
        order = torch.randperm(len(y_train), device=x_train.device)
        for start in range(0, len(order), batch_size):
            batch = order[start : start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.cross_entropy(model(x_train[batch]), y_train[batch])
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            validation_loss = float(
                nn.functional.cross_entropy(model(x_validation), y_validation).item()
            )
        if validation_loss < best_loss - 1e-6:
            best_loss = validation_loss
            best_epoch = epoch
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    if best_state is None:
        raise RuntimeError("Model training did not produce a validation checkpoint")
    model.load_state_dict(best_state)
    return model, best_epoch, best_loss


def summarize_predictions(probabilities: torch.Tensor, labels: torch.Tensor) -> dict[str, Any]:
    probabilities = probabilities.clamp_min(1e-8)
    loss_rows = -torch.log(probabilities.gather(1, labels[:, None]).squeeze(1))
    predictions = probabilities.argmax(dim=1)
    confusion = torch.bincount(labels * len(ARMS) + predictions, minlength=len(ARMS) ** 2).reshape(
        len(ARMS), len(ARMS)
    )
    recalls = confusion.diag() / confusion.sum(dim=1).clamp_min(1)
    return {
        "multiclass_log_loss": float(loss_rows.mean().item()),
        "accuracy": float((predictions == labels).float().mean().item()),
        "balanced_accuracy": float(recalls.mean().item()),
        "per_arm_recall": {
            str(ARMS[index]): float(recalls[index].item()) for index in range(len(ARMS))
        },
        "per_row_log_loss": loss_rows,
    }


def main() -> None:
    torch.set_num_threads(4)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    x_numpy, y_numpy, group_numpy, sample_manifest = sample_train_ranges()
    if len(y_numpy) < 50_000:
        raise RuntimeError(f"Sample too small for the registered diagnostic: {len(y_numpy)}")

    # Split by disjoint byte-range blocks to limit adjacent-row leakage across folds.
    split_rng = np.random.default_rng(SEED)
    observed_groups = np.unique(group_numpy)
    permuted_groups = split_rng.permutation(observed_groups)
    n_train_groups = int(0.70 * len(permuted_groups))
    n_validation_groups = int(0.15 * len(permuted_groups))
    train_groups = permuted_groups[:n_train_groups]
    validation_groups = permuted_groups[n_train_groups : n_train_groups + n_validation_groups]
    test_groups = permuted_groups[n_train_groups + n_validation_groups :]
    train_indices = np.flatnonzero(np.isin(group_numpy, train_groups))
    validation_indices = np.flatnonzero(np.isin(group_numpy, validation_groups))
    test_indices = np.flatnonzero(np.isin(group_numpy, test_groups))

    mean = x_numpy[train_indices].mean(axis=0)
    scale = x_numpy[train_indices].std(axis=0)
    scale[scale < 1e-6] = 1.0
    x_numpy = (x_numpy - mean) / scale
    x = torch.as_tensor(x_numpy, device=device)
    y = torch.as_tensor(y_numpy, device=device)
    index_train = torch.as_tensor(train_indices, device=device)
    index_validation = torch.as_tensor(validation_indices, device=device)
    index_test = torch.as_tensor(test_indices, device=device)
    group_test = torch.as_tensor(group_numpy[test_indices], device=device)
    x_train, y_train = x[index_train], y[index_train]
    x_validation, y_validation = x[index_validation], y[index_validation]
    x_test, y_test = x[index_test], y[index_test]

    train_counts = torch.bincount(y_train, minlength=len(ARMS)).float()
    baseline_probabilities = (train_counts / train_counts.sum()).expand(len(y_test), -1)
    baseline = summarize_predictions(baseline_probabilities, y_test)

    results: dict[str, Any] = {
        "prevalence_only": {k: v for k, v in baseline.items() if k != "per_row_log_loss"}
    }
    trained: dict[str, tuple[nn.Module, int, float]] = {}
    for name, model, max_epochs, patience in [
        ("linear_multinomial", MultinomialLogit(), 80, 8),
        ("nonlinear_mlp", FeatureMLP(), 80, 8),
    ]:
        fit, best_epoch, validation_loss = fit_model(
            model,
            x_train,
            y_train,
            x_validation,
            y_validation,
            epochs=max_epochs,
            patience=patience,
            seed=SEED,
        )
        fit.eval()
        with torch.no_grad():
            probabilities = torch.softmax(fit(x_test), dim=1)
        metrics = summarize_predictions(probabilities, y_test)
        loss_rows = metrics.pop("per_row_log_loss")
        baseline_rows = baseline["per_row_log_loss"]
        difference = baseline_rows - loss_rows
        group_means = torch.stack(
            [difference[group_test == group].mean() for group in torch.unique(group_test)]
        )
        overall_gain = float(difference.mean().item())
        group_weights = torch.stack(
            [(group_test == group).float().mean() for group in torch.unique(group_test)]
        )
        cluster_variance = (
            len(group_means)
            / (len(group_means) - 1)
            * torch.sum(group_weights.square() * (group_means - overall_gain).square())
        )
        cluster_standard_error = float(torch.sqrt(cluster_variance).item())
        cluster_critical_value = 2.093  # t_(0.975, 19); 20 held-out range blocks
        metrics["paired_log_loss_gain_vs_prevalence_only"] = overall_gain
        metrics["paired_range_block_se_descriptive"] = cluster_standard_error
        metrics["paired_range_block_t_95_interval_descriptive"] = [
            overall_gain - cluster_critical_value * cluster_standard_error,
            overall_gain + cluster_critical_value * cluster_standard_error,
        ]
        results[name] = {
            **metrics,
            "selected_epoch": best_epoch,
            "best_validation_log_loss": validation_loss,
        }
        trained[name] = (fit, best_epoch, validation_loss)

    manifest: dict[str, Any] = {
        "audit": "cuvet_feature_only_assignment_predictability",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_head": current_commit(),
        "script_sha256": sha256_file(Path(__file__)),
        "source": sample_manifest,
        "information_contract": {
            "predictors": FEATURES,
            "target": "randomized treatment arm (policy)",
            "outcomes_used": False,
            "source_test_accessed": False,
            "source_test_rows_used": False,
            "raw_rows_persisted": False,
            "row_id_used_as_predictor": False,
        },
        "split": {
            "method": "seeded 70/15/15 split by disjoint train-only byte-range blocks",
            "seed": SEED,
            "n_train": len(train_indices),
            "n_validation": len(validation_indices),
            "n_test": len(test_indices),
            "range_blocks_train": len(train_groups),
            "range_blocks_validation": len(validation_groups),
            "range_blocks_test": len(test_groups),
            "training_arm_counts": {
                str(ARMS[index]): int(train_counts[index].item()) for index in range(len(ARMS))
            },
        },
        "training": {
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
            "torch_version": torch.__version__,
            "models": [
                {
                    "name": "linear_multinomial",
                    "architecture": "linear 5->5",
                    "early_stopping": True,
                },
                {
                    "name": "nonlinear_mlp",
                    "architecture": "5->32 ReLU ->32 ReLU ->5",
                    "early_stopping": True,
                },
            ],
        },
        "heldout_train_sample_metrics": results,
        "interpretation": (
            "This train-only prediction diagnostic asks whether released features predict treatment "
            "better than a train-prevalence-only model. Improvement is evidence of observed-feature "
            "assignment dependence; lack of improvement does not prove randomization, rule out hidden "
            "confounding, or validate the experiment's design probabilities. Intervals are descriptive "
            "cluster-based t intervals over held-out byte ranges; they assume "
            "independent sampled ranges and are not tests of the randomization design."
        ),
    }
    output = Path("data/reports/cuvet_assignment_predictability.json")
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
