"""Exploratory batch-held-out candidate selection on UCI Gas Sensor data."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset

SEED = 20261026
EPOCHS = 300
LEARNING_RATE = 0.05
WEIGHT_DECAYS = (1e-4, 1e-2, 1.0)


def _batch_ids(domain_ids: pd.Series) -> np.ndarray:
    values = domain_ids.astype("string").str.extract(r"^batch-(\d+)$", expand=False)
    if values.isna().any():
        raise ValueError("Every gas-sensor domain_id must be named batch-<integer>")
    return values.astype(int).to_numpy()


def _cost_matrices(classes: np.ndarray) -> dict[str, np.ndarray]:
    base = np.ones((len(classes), len(classes)), dtype=np.float64) - np.eye(
        len(classes), dtype=np.float64
    )
    result = {"symmetric": base.copy()}
    class_six = np.flatnonzero(classes == 6)
    if len(class_six) != 1:
        raise ValueError("The frozen class-6 cost scenarios require source class 6")
    for multiplier in (2.0, 5.0):
        weighted = base.copy()
        weighted[:, class_six[0]] *= multiplier
        result[f"class6_x{int(multiplier)}"] = weighted
    return result


def _fit_softmax(
    x: np.ndarray,
    y: np.ndarray,
    classes: np.ndarray,
    weight_decay: float,
    device: torch.device,
    seed: int,
) -> tuple[torch.nn.Module, np.ndarray, np.ndarray]:
    if not np.isfinite(x).all():
        raise ValueError("Gas Sensor feature rows must be finite under the frozen protocol")
    if not np.isfinite(y).all() or set(np.unique(y)) != set(classes):
        raise ValueError("Each model training pool must contain all six source classes")
    mean = x.mean(axis=0, dtype=np.float64).astype(np.float32)
    scale = x.std(axis=0, dtype=np.float64).astype(np.float32)
    scale[scale < 1e-6] = 1.0
    z = ((x.astype(np.float32) - mean) / scale).astype(np.float32, copy=False)
    class_index = {value: index for index, value in enumerate(classes.tolist())}
    encoded = np.fromiter((class_index[value] for value in y), dtype=np.int64, count=len(y))
    tx = torch.as_tensor(z, device=device)
    ty = torch.as_tensor(encoded, device=device)

    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = torch.nn.Linear(x.shape[1], len(classes), bias=True, device=device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    model.train()
    for _ in range(EPOCHS):
        optimizer.zero_grad(set_to_none=True)
        logits = model(tx)
        penalty = model.weight.square().sum()
        loss = torch.nn.functional.cross_entropy(logits, ty) + 0.5 * weight_decay * penalty
        if not torch.isfinite(loss):
            raise FloatingPointError("Nonfinite softmax training loss")
        loss.backward()
        optimizer.step()
    model.eval()
    return model, mean, scale


def _predict(
    model: torch.nn.Module,
    x: np.ndarray,
    mean: np.ndarray,
    scale: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    z = ((x.astype(np.float32) - mean) / scale).astype(np.float32, copy=False)
    with torch.no_grad():
        logits = model(torch.as_tensor(z, device=device))
        probabilities = torch.softmax(logits, dim=1).detach().cpu().numpy()
    if not np.isfinite(probabilities).all() or not np.allclose(
        probabilities.sum(axis=1), 1.0, atol=1e-5
    ):
        raise FloatingPointError("Model returned invalid class probabilities")
    return probabilities


def _metrics(
    y: np.ndarray, probability: np.ndarray, classes: np.ndarray, costs: np.ndarray
) -> dict:
    class_index = {value: index for index, value in enumerate(classes.tolist())}
    encoded = np.fromiter((class_index[value] for value in y), dtype=np.int64, count=len(y))
    predicted = probability.argmax(axis=1)
    f1_values = []
    for index in range(len(classes)):
        tp = int(np.sum((predicted == index) & (encoded == index)))
        fp = int(np.sum((predicted == index) & (encoded != index)))
        fn = int(np.sum((predicted != index) & (encoded == index)))
        denom = 2 * tp + fp + fn
        f1_values.append((2 * tp / denom) if denom else 0.0)
    action = (probability @ costs.T).argmin(axis=1)
    observed_cost = costs[action, encoded]
    one_hot = np.eye(len(classes), dtype=np.float64)[encoded]
    return {
        "n": len(y),
        "accuracy": float(np.mean(predicted == encoded)),
        "macro_f1": float(np.mean(f1_values)),
        "multiclass_log_loss": float(
            -np.log(np.maximum(probability[np.arange(len(y)), encoded], 1e-15)).mean()
        ),
        "multiclass_brier": float(np.square(probability - one_hot).sum(axis=1).mean()),
        "mean_decision_cost": float(observed_cost.mean()),
    }


def _equal_batch_average(rows: list[dict], *, n_total: int) -> dict:
    metric_names = (
        "accuracy",
        "macro_f1",
        "multiclass_log_loss",
        "multiclass_brier",
        "mean_decision_cost",
    )
    if not rows:
        raise ValueError("At least one batch metric is required")
    return {
        "n": n_total,
        **{name: float(np.mean([row[name] for row in rows])) for name in metric_names},
        "aggregation": "arithmetic mean of batch metrics, batches weighted equally",
    }


def _select_by_validation(rows: list[dict]) -> str:
    if not rows:
        raise ValueError("Validation scores are required to select a model")
    return min(rows, key=lambda row: (row["mean_decision_cost"], row["model"]))["model"]


def run(dataset_path: Path, output_dir: Path, *, force_cpu: bool = False) -> Path:
    started = time.perf_counter()
    validate_dataset(dataset_path)
    manifest_path = dataset_path / "dataset_manifest.json"
    input_path = dataset_path / "observations.parquet"
    protocol_path = (
        Path(__file__).resolve().parents[1]
        / "papers/shiftguard_unified/gas_sensor_candidate_protocol.md"
    )
    data_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        data_manifest.get("dataset") != "gas_sensor"
        or data_manifest.get("version") != "10bbca34ef1b5061a374"
    ):
        raise ValueError("This frozen study accepts only Gas Sensor release 10bbca34ef1b5061a374")
    frame = pd.read_parquet(input_path)
    batch = _batch_ids(frame["domain_id"])
    features = np.stack(frame["features"].to_numpy()).astype(np.float32, copy=False)
    target = frame["target"].to_numpy(dtype=np.float64)
    classes = np.sort(np.unique(target[np.isfinite(target)]))
    if len(frame) != 13_910 or features.shape != (13_910, 128):
        raise ValueError(
            f"Unexpected frozen source dimensions: {features.shape}, rows={len(frame)}"
        )
    if not np.isfinite(features).all() or not np.isfinite(target).all():
        raise ValueError("Source features and targets must be fully finite")
    required = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    if set(np.unique(batch)) != required:
        raise ValueError("Expected all ten source batches")
    device = torch.device("cuda" if torch.cuda.is_available() and not force_cpu else "cpu")
    if device.type == "cpu":
        torch.set_num_threads(min(torch.get_num_threads(), 8))

    x_by_batch = {b: features[batch == b] for b in required}
    y_by_batch = {b: target[batch == b] for b in required}
    train_early_x = np.concatenate([x_by_batch[b] for b in (1, 2, 3)])
    train_early_y = np.concatenate([y_by_batch[b] for b in (1, 2, 3)])
    train_full_x = np.concatenate([x_by_batch[b] for b in (1, 2, 3, 4, 5)])
    train_full_y = np.concatenate([y_by_batch[b] for b in (1, 2, 3, 4, 5)])
    models: dict[str, tuple[torch.nn.Module, np.ndarray, np.ndarray]] = {}
    models["incumbent_batch1_3_wd0.01"] = _fit_softmax(
        train_early_x, train_early_y, classes, 1e-2, device, SEED
    )
    for index, wd in enumerate(WEIGHT_DECAYS):
        name = f"retrained_batch1_5_wd{wd:g}"
        models[name] = _fit_softmax(
            train_full_x, train_full_y, classes, wd, device, SEED + index + 1
        )

    cost_matrices = _cost_matrices(classes)
    validation_x = x_by_batch[6]
    validation_y = y_by_batch[6]
    validation_probs = {
        name: _predict(model, validation_x, mean, scale, device)
        for name, (model, mean, scale) in models.items()
    }
    validation_rows: list[dict] = []
    selected: dict[str, str] = {}
    # The incumbent is an explicit no-adaptation option in the validation selector.
    for cost_name, cost_matrix in cost_matrices.items():
        for name in models:
            score = _metrics(validation_y, validation_probs[name], classes, cost_matrix)
            validation_rows.append({"cost_scenario": cost_name, "model": name, **score})
        eligible_rows = [row for row in validation_rows if row["cost_scenario"] == cost_name]
        selected[cost_name] = _select_by_validation(eligible_rows)

    # Freeze every cost-specific choice before computing any batch 7–10 outcomes.
    test_batches = (7, 8, 9, 10)
    test_x = np.concatenate([x_by_batch[b] for b in test_batches])
    test_y = np.concatenate([y_by_batch[b] for b in test_batches])
    test_batch = np.concatenate([np.full(len(y_by_batch[b]), b) for b in test_batches])
    test_probabilities = {
        name: _predict(model, test_x, mean, scale, device)
        for name, (model, mean, scale) in models.items()
    }
    test_rows: list[dict] = []
    for cost_name, cost_matrix in cost_matrices.items():
        compared = ["incumbent_batch1_3_wd0.01", selected[cost_name]]
        for name in dict.fromkeys(compared):
            probability = test_probabilities[name]
            per_batch_metrics = []
            for b in test_batches:
                mask = test_batch == b
                batch_metrics = _metrics(test_y[mask], probability[mask], classes, cost_matrix)
                per_batch_metrics.append(batch_metrics)
                test_rows.append(
                    {
                        "cost_scenario": cost_name,
                        "selected_model": selected[cost_name],
                        "evaluated_model": name,
                        "test_batch": b,
                        **batch_metrics,
                        "aggregation": "within-batch row average",
                    }
                )
            test_rows.append(
                {
                    "cost_scenario": cost_name,
                    "selected_model": selected[cost_name],
                    "evaluated_model": name,
                    "test_batch": "row_weighted_7_10",
                    **_metrics(test_y, probability, classes, cost_matrix),
                    "aggregation": "all test rows pooled",
                }
            )
            test_rows.append(
                {
                    "cost_scenario": cost_name,
                    "selected_model": selected[cost_name],
                    "evaluated_model": name,
                    "test_batch": "equal_batch_average_7_10",
                    **_equal_batch_average(per_batch_metrics, n_total=len(test_y)),
                }
            )

    # Feature-only diagnostic, computed after policy selection and kept outside the learner.
    ref_mean = train_early_x.mean(axis=0, dtype=np.float64)
    ref_scale = train_early_x.std(axis=0, dtype=np.float64)
    ref_scale[ref_scale < 1e-12] = 1.0
    shift_rows = []
    for b in sorted(required):
        standardized_delta = (x_by_batch[b].mean(axis=0, dtype=np.float64) - ref_mean) / ref_scale
        shift_rows.append(
            {
                "batch": b,
                "n": len(x_by_batch[b]),
                "feature_centroid_distance": float(np.linalg.norm(standardized_delta)),
                "scope": "evaluator-only descriptive feature diagnostic",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(validation_rows).to_csv(output_dir / "validation_scores.csv", index=False)
    pd.DataFrame(test_rows).to_csv(output_dir / "test_metrics.csv", index=False)
    pd.DataFrame(shift_rows).to_csv(output_dir / "feature_shift_diagnostics.csv", index=False)
    elapsed = time.perf_counter() - started
    run_manifest = {
        "study": "gas_sensor_batch_heldout_candidate_selection_v4",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset": data_manifest["dataset"],
        "dataset_version": data_manifest["version"],
        "dataset_source_url": data_manifest.get("source_url"),
        "input_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(input_path),
        "protocol_sha256": sha256(protocol_path),
        "runner_sha256": sha256(Path(__file__)),
        "data_source_code_hash": source_hash(),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "seed": SEED,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "batch_roles": {
            "incumbent_fit": [1, 2, 3],
            "candidate_fit": [1, 2, 3, 4, 5],
            "selection": [6],
            "evaluation": [7, 8, 9, 10],
        },
        "selected_models": selected,
        "weight_decays": list(WEIGHT_DECAYS),
        "cost_scenarios": {
            name: {"matrix_action_by_class": matrix.tolist(), "origin": "imposed research cost"}
            for name, matrix in cost_matrices.items()
        },
        "learner_inputs": "128 sensor features only; batch metadata/labels are evaluator-side",
        "test_access_order": "All candidate choices frozen on batch 6 before batches 7-10 metrics were computed",
        "uncertainty": "Descriptive only; four evaluation domains and unknown within-batch dependence",
        "timing": "Source-ordered coarse batches only; no within-batch sequence or verified label-release time",
        "prior_exposure": "Later batches were inspected by existing repository diagnostics; exploratory, not independent confirmation",
        "runtime_seconds": elapsed,
    }
    write_report(output_dir, validation_rows, test_rows, shift_rows, selected, run_manifest)
    run_manifest["output_sha256"] = {
        name: sha256(output_dir / name)
        for name in (
            "validation_scores.csv",
            "test_metrics.csv",
            "feature_shift_diagnostics.csv",
            "results.md",
        )
    }
    write_json(output_dir / "manifest.json", run_manifest)
    return output_dir


def write_report(
    output_dir: Path,
    validation_rows: list[dict],
    test_rows: list[dict],
    shift_rows: list[dict],
    selected: dict[str, str],
    manifest: dict,
) -> None:
    metrics = pd.DataFrame(test_rows)
    lines = [
        "# Gas Sensor batch-held-out candidate-selection development",
        "",
        "**Status:** exploratory descriptive development run. Later batches have prior repository analysis; no real-time or independent-confirmation claim is made.",
        "",
        f"Device: `{manifest['device']}`; runtime: {manifest['runtime_seconds']:.1f} seconds.",
        "",
        "Validation selected:",
        "",
    ]
    for cost_name, model in selected.items():
        lines.append(f"- `{cost_name}`: `{model}`")
    lines.extend(
        ["", "Test cost comparison (positive gain means the selected policy costs less):", ""]
    )
    for cost_name in selected:
        subset = metrics[metrics.cost_scenario == cost_name]
        for aggregation in ("row_weighted_7_10", "equal_batch_average_7_10"):
            incumbent = float(
                subset.loc[
                    (subset.evaluated_model == "incumbent_batch1_3_wd0.01")
                    & (subset.test_batch == aggregation),
                    "mean_decision_cost",
                ].iloc[0]
            )
            selected_loss = float(
                subset.loc[
                    (subset.evaluated_model == selected[cost_name])
                    & (subset.test_batch == aggregation),
                    "mean_decision_cost",
                ].iloc[0]
            )
            lines.append(
                f"- {cost_name}, {aggregation}: incumbent {incumbent:.5f}; selected "
                f"{selected_loss:.5f}; incumbent-minus-selected gain "
                f"{incumbent - selected_loss:+.5f}."
            )
        batch_gains = []
        for batch_id in (7, 8, 9, 10):
            incumbent = float(
                subset.loc[
                    (subset.evaluated_model == "incumbent_batch1_3_wd0.01")
                    & (subset.test_batch == batch_id),
                    "mean_decision_cost",
                ].iloc[0]
            )
            selected_loss = float(
                subset.loc[
                    (subset.evaluated_model == selected[cost_name])
                    & (subset.test_batch == batch_id),
                    "mean_decision_cost",
                ].iloc[0]
            )
            batch_gains.append(incumbent - selected_loss)
        lines.append(
            f"  Per-batch gains for batches 7–10: "
            f"{', '.join(f'{gain:+.5f}' for gain in batch_gains)}."
        )
    lines.extend(
        [
            "",
            (
                "Feature centroid distances are descriptive and do not imply decision harm. "
                "Only four held-out batches are available; row-level standard errors would "
                "overstate independent replication. Batch 10 is much larger than several "
                "other domains, so both per-batch outcomes and row-weighted aggregation "
                "must be considered. Costs are imposed class-loss scenarios, not observed application utility."
            ),
            "",
            "See `validation_scores.csv`, `test_metrics.csv`, `feature_shift_diagnostics.csv`, and `manifest.json` for aggregate evidence and provenance.",
        ]
    )
    (output_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("data/processed/gas_sensor/10bbca34ef1b5061a374"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/gas_sensor_candidates_v4"),
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU even when CUDA is available")
    args = parser.parse_args()
    print(run(args.dataset_path, args.output_dir, force_cpu=args.cpu))


if __name__ == "__main__":
    main()
