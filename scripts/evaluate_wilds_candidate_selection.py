"""Offline, sample-split candidate-threshold evaluation on WILDS CivilComments.

Only text is used by the learner. Official train labels fit the models,
validation labels select a model/threshold, and test labels are read only for
post-selection aggregate evaluation. Outputs contain aggregates, not text or
row-level predictions. This is an exploratory offline study, not a live
monitor or a formal sequential certificate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import time
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
import torch.nn.functional as F
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import HashingVectorizer

from shiftlab.data.gpu.environment import environment
from shiftlab.data.real.wilds import CIVIL_HF_REVISION, CIVIL_HF_SHA256

DATASET_DIR = Path("data/processed/wilds/c4f79606707951bcba11")
PROTOCOL = Path("papers/shiftguard_unified/wilds_candidate_selection_protocol.md")
OUTPUT = Path(
    "outputs/shiftguard_unified/real_data_development/wilds_civilcomments_candidate_selection_v1"
)
PENALTIES = (1e-5, 1e-4, 1e-3)
THRESHOLDS = (0.25, 0.35, 0.50, 0.65, 0.75)
COSTS = {
    "symmetric": (1.0, 1.0),
    "false_negative_sensitive": (1.0, 2.0),
    "false_positive_sensitive": (2.0, 1.0),
}
IDENTITY_FIELDS = (
    "male",
    "female",
    "LGBTQ",
    "christian",
    "muslim",
    "other_religion",
    "black",
    "white",
    "other_race_or_ethnicity",
)


class CandidateScore(TypedDict):
    setting: str
    penalty: float
    threshold: float
    validation_cost: float
    validation_accuracy: float
    validation_rows: int


def _metadata_float(value: object) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return -1.0
    return number if math.isfinite(number) else -1.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _load_data(dataset_dir: Path):
    observations_path = dataset_dir / "observations.parquet"
    inputs_path = dataset_dir / "inputs.parquet"
    observations = pq.read_table(
        observations_path,
        columns=["sample_id", "target", "split", "metadata"],
    ).to_pandas()
    texts = pq.read_table(inputs_path, columns=["text"]).column("text").to_pylist()
    if len(observations) != len(texts):
        raise ValueError("observation/input row counts differ")
    sample_rows = np.fromiter(
        (int(value.rsplit(":", 1)[-1]) for value in observations.sample_id),
        dtype=np.int64,
        count=len(observations),
    )
    if not np.array_equal(sample_rows, np.arange(len(observations), dtype=np.int64)):
        raise ValueError("sample_id order does not match the aligned input table")

    targets = observations.target.to_numpy(dtype=np.int8)
    if not np.isin(targets, [0, 1]).all():
        raise ValueError("WILDS target must be binary")
    split = observations.split.astype(str).to_numpy()
    allowed = {"train", "validation", "test"}
    if not set(split).issubset(allowed) or set(split) != allowed:
        raise ValueError(f"unexpected official WILDS splits: {set(split)}")

    article_ids = np.empty(len(observations), dtype=np.int64)
    identity = np.zeros((len(observations), len(IDENTITY_FIELDS)), dtype=bool)
    identity_any = np.zeros(len(observations), dtype=bool)
    metadata_keys: set[str] = set()
    for index, serialized in enumerate(observations.metadata):
        item = json.loads(serialized) if serialized else {}
        metadata_keys.update(item)
        article_id = item.get("article_id")
        article_value = _metadata_float(article_id)
        if article_value < 0:
            article_ids[index] = 1_000_000_000_000 + index
        else:
            article_ids[index] = int(article_value)
        identity[index] = [_metadata_float(item.get(key)) >= 0.5 for key in IDENTITY_FIELDS]
        identity_any[index] = _metadata_float(item.get("identity_any")) >= 0.5

    article_sets = {name: set(article_ids[split == name].tolist()) for name in sorted(allowed)}
    overlaps = {
        f"{left}_{right}": len(article_sets[left] & article_sets[right])
        for left, right in (
            ("train", "validation"),
            ("train", "test"),
            ("validation", "test"),
        )
    }
    if any(overlaps.values()):
        raise ValueError(f"article-level split leakage detected: {overlaps}")

    return {
        "texts": texts,
        "targets": targets,
        "split": split,
        "article_ids": article_ids,
        "identity": identity,
        "identity_any": identity_any,
        "metadata_keys": sorted(metadata_keys),
        "article_overlaps": overlaps,
    }


def _torch_csr(matrix: csr_matrix, device: torch.device):
    return torch.sparse_csr_tensor(
        torch.as_tensor(matrix.indptr, dtype=torch.int64, device=device),
        torch.as_tensor(matrix.indices, dtype=torch.int64, device=device),
        torch.as_tensor(matrix.data, dtype=torch.float32, device=device),
        size=matrix.shape,
        device=device,
    )


def _fit_model(
    features: csr_matrix,
    targets: np.ndarray,
    *,
    penalty: float,
    device: torch.device,
    seed: int,
    epochs: int = 3,
    batch_size: int = 8192,
    learning_rate: float = 0.05,
) -> tuple[torch.Tensor, torch.Tensor, list[float]]:
    torch.manual_seed(seed)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    n_features = features.shape[1]
    weights = torch.zeros((n_features, 1), device=device, requires_grad=True)
    prevalence = float(targets.mean())
    bias = torch.tensor(
        [math.log(prevalence / (1 - prevalence))],
        device=device,
        requires_grad=True,
    )
    optimizer = torch.optim.Adam([weights, bias], lr=learning_rate)
    epoch_losses: list[float] = []
    for _epoch in range(epochs):
        permutation = torch.randperm(len(targets), generator=generator).numpy()
        loss_sum = 0.0
        seen = 0
        for start in range(0, len(targets), batch_size):
            rows = permutation[start : start + batch_size]
            batch = _torch_csr(features[rows], device)
            y = torch.as_tensor(targets[rows], dtype=torch.float32, device=device)
            logits = torch.sparse.mm(batch, weights).reshape(-1) + bias
            loss = F.binary_cross_entropy_with_logits(logits, y)
            loss = loss + (0.5 * penalty) * torch.sum(weights.square())
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach().item()) * len(rows)
            seen += len(rows)
        epoch_losses.append(loss_sum / seen)
    return weights.detach(), bias.detach(), epoch_losses


def _predict(
    features: csr_matrix,
    model: tuple[torch.Tensor, torch.Tensor],
    *,
    device: torch.device,
    batch_size: int = 8192,
) -> np.ndarray:
    weights, bias = model
    output = np.empty(features.shape[0], dtype=np.float32)
    with torch.inference_mode():
        for start in range(0, features.shape[0], batch_size):
            stop = min(start + batch_size, features.shape[0])
            batch = _torch_csr(features[start:stop], device)
            logits = torch.sparse.mm(batch, weights).reshape(-1) + bias
            output[start:stop] = torch.sigmoid(logits).cpu().numpy()
    return output


def _cost(y: np.ndarray, probability: np.ndarray, threshold: float, fp: float, fn: float):
    prediction = probability >= threshold
    return np.where(prediction & (y == 0), fp, np.where(~prediction & (y == 1), fn, 0.0))


def _binary_metrics(y: np.ndarray, probability: np.ndarray, threshold: float) -> dict[str, float]:
    clipped = np.clip(probability.astype(np.float64), 1e-7, 1 - 1e-7)
    prediction = probability >= threshold
    return {
        "accuracy": float(np.mean(prediction == y)),
        "brier_score": float(np.mean((probability - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(clipped) + (1 - y) * np.log(1 - clipped))),
    }


def _cluster_bootstrap(
    gains: np.ndarray,
    article_ids: np.ndarray,
    *,
    replicates: int,
    seed: int,
) -> tuple[float, float, float, float]:
    _, inverse = np.unique(article_ids, return_inverse=True)
    n_clusters = int(inverse.max()) + 1
    cluster_sum = np.bincount(inverse, weights=gains, minlength=n_clusters)
    cluster_size = np.bincount(inverse, minlength=n_clusters).astype(np.int64)
    point = float(gains.mean())
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=np.float64)
    chunk_size = 50
    for start in range(0, replicates, chunk_size):
        count = min(chunk_size, replicates - start)
        sampled = rng.integers(0, n_clusters, size=(count, n_clusters), dtype=np.int32)
        numerator = cluster_sum[sampled].sum(axis=1)
        denominator = cluster_size[sampled].sum(axis=1)
        draws[start : start + count] = numerator / denominator
    low, high = np.quantile(draws, [0.025, 0.975])
    centered_draws = draws - point
    p_one_sided = (1 + np.count_nonzero(centered_draws >= point)) / (replicates + 1)
    return point, float(low), float(high), float(p_one_sided)


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.ones(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def _group_metrics(
    *,
    y: np.ndarray,
    probability: np.ndarray,
    threshold: float,
    identity: np.ndarray,
    article_ids: np.ndarray,
    policy: str,
) -> list[dict]:
    predictions = probability >= threshold
    rows: list[dict] = []
    for identity_index, identity_name in enumerate(IDENTITY_FIELDS):
        for label in (0, 1):
            mask = identity[:, identity_index] & (y == label)
            count = int(mask.sum())
            if count == 0:
                continue
            rows.append(
                {
                    "policy": policy,
                    "group": identity_name,
                    "target_label": label,
                    "rows": count,
                    "articles": int(np.unique(article_ids[mask]).size),
                    "accuracy": float(np.mean(predictions[mask] == y[mask])),
                }
            )
    return rows


def run(
    *,
    dataset_dir: Path = DATASET_DIR,
    output_dir: Path | None = None,
    device: str = "cuda",
    bootstrap_replicates: int = 2000,
) -> dict:
    if device not in {"cuda", "cpu", "auto"}:
        raise ValueError("device must be cuda, cpu, or auto")
    if bootstrap_replicates < 200:
        raise ValueError("use at least 200 article-cluster bootstrap replicates")
    if output_dir is None:
        output_dir = OUTPUT
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA requested but unavailable; rerun with --device cpu to label a fallback"
        )
    torch_device = torch.device(device)

    started = time.perf_counter()
    dataset_dir = Path(dataset_dir)
    observations_path = dataset_dir / "observations.parquet"
    inputs_path = dataset_dir / "inputs.parquet"
    manifest_path = dataset_dir / "dataset_manifest.json"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("version") != "c4f79606707951bcba11":
        raise ValueError("protocol is frozen for WILDS version c4f79606707951bcba11")
    if (
        source_manifest.get("raw_checksums", {}).get(
            "data\\raw\\wilds\\civilcomments-hf\\raw\\train-00000-of-00001.parquet"
        )
        != CIVIL_HF_SHA256
    ):
        raise ValueError("processed WILDS version does not match the pinned raw-source checksum")
    if source_manifest.get("files", {}).get("inputs.parquet") != _sha256(
        dataset_dir / "inputs.parquet"
    ):
        raise ValueError("processed inputs.parquet checksum does not match its dataset manifest")
    if source_manifest.get("files", {}).get("observations.parquet") != _sha256(
        dataset_dir / "observations.parquet"
    ):
        raise ValueError(
            "processed observations.parquet checksum does not match its dataset manifest"
        )

    data = _load_data(dataset_dir)
    split = data["split"]
    targets = data["targets"]
    split_counts = {
        name: int(np.count_nonzero(split == name)) for name in ("train", "validation", "test")
    }
    expected = {"train": 269038, "validation": 45180, "test": 133782}
    if split_counts != expected:
        raise ValueError(f"official WILDS split counts changed: {split_counts}")
    labels_by_split = {name: int(targets[split == name].sum()) for name in ("train", "validation")}

    vectorizer = HashingVectorizer(
        n_features=2**18,
        alternate_sign=False,
        norm="l2",
        binary=True,
        ngram_range=(1, 2),
        lowercase=True,
        dtype=np.float32,
    )
    features = vectorizer.transform(data["texts"]).tocsr()
    del data["texts"]
    train_mask = split == "train"
    validation_mask = split == "validation"
    test_mask = split == "test"
    x_train = features[train_mask]
    x_validation = features[validation_mask]
    x_test = features[test_mask]
    y_train = targets[train_mask]
    y_validation = targets[validation_mask]
    y_test = targets[test_mask]
    meta_identity = data["identity"]
    meta_article = data["article_ids"]
    identity_test = meta_identity[test_mask]
    article_test = meta_article[test_mask]

    model_predictions_validation: dict[float, np.ndarray] = {}
    model_states: dict[float, tuple[torch.Tensor, torch.Tensor]] = {}
    train_loss_history: dict[str, list[float]] = {}
    cuda_sparse_warnings: set[str] = set()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        for model_index, penalty in enumerate(PENALTIES):
            model = _fit_model(
                x_train,
                y_train,
                penalty=penalty,
                device=torch_device,
                seed=20261026 + model_index,
            )
            train_loss_history[f"{penalty:g}"] = model[2]
            model_predictions_validation[penalty] = _predict(
                x_validation, model[:2], device=torch_device
            )
            model_states[penalty] = model[:2]
    cuda_sparse_warnings.update(str(item.message) for item in captured)

    candidate_rows: list[CandidateScore] = []
    selection_rows: list[dict[str, object]] = []
    baseline_penalty = 1e-4
    baseline_threshold = 0.5
    for setting, (fp_cost, fn_cost) in COSTS.items():
        candidates: list[CandidateScore] = []
        for penalty in PENALTIES:
            probability = model_predictions_validation[penalty]
            for threshold in THRESHOLDS:
                observed_cost = _cost(y_validation, probability, threshold, fp_cost, fn_cost)
                candidates.append(
                    {
                        "setting": setting,
                        "penalty": penalty,
                        "threshold": threshold,
                        "validation_cost": float(observed_cost.mean()),
                        "validation_accuracy": float(
                            np.mean((probability >= threshold) == y_validation)
                        ),
                        "validation_rows": len(y_validation),
                    }
                )
        candidates.sort(
            key=lambda row: (
                row["validation_cost"],
                PENALTIES.index(row["penalty"]),
                row["threshold"],
            )
        )
        selected = candidates[0]
        candidate_rows.extend(candidates)
        selection_rows.append(
            {
                **selected,
                "false_positive_cost": fp_cost,
                "false_negative_cost": fn_cost,
            }
        )

    # All model/threshold choices are frozen from train and validation before
    # any test target or test-group outcome is evaluated.
    y_test = targets[test_mask]
    labels_by_split["test"] = int(y_test.sum())
    identity_test = meta_identity[test_mask]
    article_test = meta_article[test_mask]
    model_predictions_test = {
        penalty: _predict(x_test, model_states[penalty], device=torch_device)
        for penalty in PENALTIES
    }
    metrics_rows: list[dict] = []
    group_rows: list[dict] = []
    test_p_values: list[float] = []
    baseline_probability = model_predictions_test[baseline_penalty]
    baseline_prediction = baseline_probability >= baseline_threshold
    baseline_accuracy = float(np.mean(baseline_prediction == y_test))
    baseline_metrics = _binary_metrics(y_test, baseline_probability, baseline_threshold)
    metrics_rows.append(
        {
            "policy": "fixed_incumbent",
            "setting": "all",
            "penalty": baseline_penalty,
            "threshold": baseline_threshold,
            **baseline_metrics,
        }
    )
    group_rows.extend(
        _group_metrics(
            y=y_test,
            probability=baseline_probability,
            threshold=baseline_threshold,
            identity=identity_test,
            article_ids=article_test,
            policy="fixed_incumbent",
        )
    )

    for setting_index, selected_policy in enumerate(selection_rows):
        setting = str(selected_policy["setting"])
        fp_cost = cast(float, selected_policy["false_positive_cost"])
        fn_cost = cast(float, selected_policy["false_negative_cost"])
        selected_penalty = cast(float, selected_policy["penalty"])
        candidate_threshold = cast(float, selected_policy["threshold"])
        candidate_probability = model_predictions_test[selected_penalty]
        baseline_cost = _cost(y_test, baseline_probability, baseline_threshold, fp_cost, fn_cost)
        candidate_cost = _cost(y_test, candidate_probability, candidate_threshold, fp_cost, fn_cost)
        gain = baseline_cost - candidate_cost
        estimate, ci_low, ci_high, p_value = _cluster_bootstrap(
            gain,
            article_test,
            replicates=bootstrap_replicates,
            seed=20261026 + setting_index,
        )
        test_p_values.append(p_value)
        metrics_rows.append(
            {
                "policy": "validation_selected_candidate",
                "setting": setting,
                "penalty": selected_penalty,
                "threshold": candidate_threshold,
                **_binary_metrics(y_test, candidate_probability, candidate_threshold),
            }
        )
        group_rows.extend(
            _group_metrics(
                y=y_test,
                probability=candidate_probability,
                threshold=candidate_threshold,
                identity=identity_test,
                article_ids=article_test,
                policy=f"candidate_{setting}",
            )
        )
        selected_policy.update(
            {
                "test_rows": len(y_test),
                "incumbent_test_cost": float(baseline_cost.mean()),
                "candidate_test_cost": float(candidate_cost.mean()),
                "incumbent_minus_candidate_gain": estimate,
                "cluster_bootstrap_95_low": ci_low,
                "cluster_bootstrap_95_high": ci_high,
                "cluster_bootstrap_p_one_sided": p_value,
                "n_test_articles": int(np.unique(article_test).size),
            }
        )

    adjusted = _holm(test_p_values)
    for row, adjusted_p in zip(selection_rows, adjusted, strict=True):
        row["holm_adjusted_p_one_sided"] = adjusted_p

    group_frame = pd.DataFrame(group_rows)
    # WILDS CivilComments official accuracy and worst identity-by-label-group
    # accuracy are summarized from evaluator-only metadata and the incumbent.
    group_accuracy_values = [
        row["accuracy"]
        for row in group_rows
        if row["policy"] == "fixed_incumbent" and row["rows"] >= 20
    ]
    group_accuracy_values = [
        row["accuracy"]
        for row in group_rows
        if row["policy"] == "fixed_incumbent" and row["rows"] >= 20
    ]
    scored_group_frame = group_frame[group_frame.rows >= 20]
    group_summary = {
        "identity_any_test_rows": int(data["identity_any"][test_mask].sum()),
        "identity_any_test_prevalence": float(data["identity_any"][test_mask].mean()),
        "incumbent_accuracy": baseline_accuracy,
        "incumbent_worst_identity_by_label_group_accuracy_min_20": min(group_accuracy_values)
        if group_accuracy_values
        else None,
        "identity_groups": list(IDENTITY_FIELDS),
        "group_minimum_rows": 20,
        "worst_identity_by_label_group_accuracy_by_policy": {
            str(policy): float(group["accuracy"].min())
            for policy, group in scored_group_frame.groupby("policy", sort=True)
        },
        "identity_by_label_group_count_by_policy": {
            str(policy): len(group)
            for policy, group in scored_group_frame.groupby("policy", sort=True)
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_frame = pd.DataFrame(candidate_rows)
    selection_frame = pd.DataFrame(selection_rows)
    metrics_frame = pd.DataFrame(metrics_rows)
    group_frame = pd.DataFrame(group_rows)
    candidate_frame.to_csv(output_dir / "validation_policy_scores.csv", index=False)
    selection_frame.to_csv(output_dir / "selected_test_comparisons.csv", index=False)
    metrics_frame.to_csv(output_dir / "test_predictive_metrics.csv", index=False)
    group_frame.to_csv(output_dir / "test_identity_group_metrics.csv", index=False)

    report = {
        "title": "WILDS CivilComments offline sample-split threshold and model selection",
        "status": "exploratory_real_data_development_test_exposure_not_audited",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "repository_head": _git_head(),
        "data": {
            "dataset": source_manifest["dataset"],
            "version": source_manifest["version"],
            "source_mirror_revision": CIVIL_HF_REVISION,
            "raw_source_sha256": CIVIL_HF_SHA256,
            "source_url": source_manifest["source_url"],
            "rows": len(split),
            "split_counts": split_counts,
            "positive_counts": labels_by_split,
            "article_id_overlap_counts": data["article_overlaps"],
            "article_id_clusters_test": int(np.unique(article_test).size),
            "identity_metadata_used_as_model_input": False,
            "timestamps_used": False,
            "input_file_sha256": _sha256(inputs_path),
            "observation_file_sha256": _sha256(observations_path),
            "dataset_manifest_sha256": _sha256(manifest_path),
        },
        "protocol": {
            "path": str(PROTOCOL),
            "sha256": _sha256(PROTOCOL),
            "source_sha256": _sha256(Path(__file__)),
            "device": str(torch_device),
            "epochs": 3,
            "batch_size": 8192,
            "learning_rate": 0.05,
            "penalties": PENALTIES,
            "thresholds": THRESHOLDS,
            "baseline": {"penalty": baseline_penalty, "threshold": baseline_threshold},
            "costs": {
                key: {"false_positive": value[0], "false_negative": value[1]}
                for key, value in COSTS.items()
            },
            "bootstrap": {
                "unit": "article_id cluster",
                "replicates": bootstrap_replicates,
                "seed": 20261026,
                "holm_family_size": len(COSTS),
            },
        },
        "learner_label_counts": {
            "training": split_counts["train"],
            "validation_selection": split_counts["validation"],
            "test_evaluator_only": split_counts["test"],
        },
        "validation_selected_policies": selection_frame.to_dict(orient="records"),
        "test_predictive_metrics": metrics_frame.to_dict(orient="records"),
        "group_summary": group_summary,
        "training_loss_by_penalty": train_loss_history,
        "runtime_seconds": time.perf_counter() - started,
        "environment": environment(),
        "sparse_runtime_warnings": sorted(cuda_sparse_warnings),
        "limitations": [
            "Official test split is kept separate from this run's validation selection, but prior test-metric use is not fully audited; treat all test results as exploratory.",
            "WILDS rows have no verified individual event/feature/label availability time; no streaming or DIVE e-process was run.",
            "Costs are imposed classification sensitivities, not observed application utility.",
            "A sample-split test comparison is not an anytime-valid certificate; bootstrap uncertainty is descriptive for one domain and clustered by article.",
            "No shift-monitoring, delayed-feedback, causal policy, or resource-allocation claim follows from this benchmark.",
        ],
        "interpretation": "This is one real-data common-label sample-split candidate-policy evaluation, useful for Q2 development only. It does not close the required real-data monitoring/intervention or final confirmation gates.",
    }
    for name in (
        "validation_policy_scores.csv",
        "selected_test_comparisons.csv",
        "test_predictive_metrics.csv",
        "test_identity_group_metrics.csv",
    ):
        report.setdefault("artifact_sha256", {})[name] = _sha256(output_dir / name)
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output_dir / "results.md").write_text(_render_report(report), encoding="utf-8")
    report["artifact_sha256"]["results.md"] = _sha256(output_dir / "results.md")
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _render_report(report: dict) -> str:
    lines = [
        "# WILDS CivilComments candidate-selection development results",
        "",
        "**Status:** exploratory real-data development; test prior-exposure audit incomplete.",
        "",
        "This offline study fits hashed-text logistic models on official train, selects model/threshold pairs on validation, and evaluates selected policies on the official test split. It does not use timestamps, identity metadata as a learner input, or any test outcomes during selection. Costs are imposed classification-loss sensitivities.",
        "",
        f"Data version `{report['data']['version']}`: {report['data']['rows']:,} observations; split counts {report['data']['split_counts']}; positive labels {report['data']['positive_counts']}; article-ID overlaps {report['data']['article_id_overlap_counts']}. The test set contains {report['data']['article_id_clusters_test']:,} article clusters.",
        "",
        "## Selected policies and held-out test costs",
        "",
        "Positive incumbent-minus-candidate gain favors the validation-selected candidate.",
        "",
        "| Cost setting | Penalty | Threshold | Incumbent cost | Candidate cost | Gain | Article-cluster 95% interval | Holm p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["validation_selected_policies"]:
        lines.append(
            f"| {row['setting']} | {row['penalty']:.0e} | {row['threshold']:.2f} | {row['incumbent_test_cost']:.5f} | {row['candidate_test_cost']:.5f} | {row['incumbent_minus_candidate_gain']:+.5f} | [{row['cluster_bootstrap_95_low']:+.5f}, {row['cluster_bootstrap_95_high']:+.5f}] | {row['holm_adjusted_p_one_sided']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Test predictive metrics",
            "",
            "| Policy | Setting | Penalty | Threshold | Accuracy | Brier | Log loss |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["test_predictive_metrics"]:
        lines.append(
            f"| {row['policy']} | {row['setting']} | {row['penalty']:.0e} | {row['threshold']:.2f} | {row['accuracy']:.5f} | {row['brier_score']:.5f} | {row['log_loss']:.5f} |"
        )
    lines.extend(
        [
            "",
            "## Evaluator-only identity-group diagnostics",
            "",
            "| Policy | Worst identity-by-label-group accuracy (groups with >=20 rows) | Groups scored |",
            "|---|---:|---:|",
        ]
    )
    for policy, worst_accuracy in report["group_summary"][
        "worst_identity_by_label_group_accuracy_by_policy"
    ].items():
        count = report["group_summary"]["identity_by_label_group_count_by_policy"][policy]
        lines.append(f"| {policy} | {worst_accuracy:.5f} | {count} |")
    lines.extend(
        [
            "",
            f"The official test partition has {report['group_summary']['identity_any_test_rows']:,} rows ({report['group_summary']['identity_any_test_prevalence']:.1%}) with an identity annotation. These metadata are evaluator-only.",
        ]
    )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "The article-cluster intervals describe this single offline domain, not independent deployment episodes. The official test set has appeared in prior repository diagnostics and is not accepted as untouched confirmation. WILDS does not supply row-level online availability clocks, actual application-specific decision costs, or action-dependent policy outcomes. This result supports only a sample-split candidate-policy comparison under the named imposed losses.",
            "",
            "Full aggregate tables, data/protocol/source hashes, runtime environment, and the exact warnings are in the adjacent manifest and CSV files.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    args = parser.parse_args()
    report = run(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    for row in report["validation_selected_policies"]:
        print(
            row["setting"],
            "penalty=",
            row["penalty"],
            "threshold=",
            row["threshold"],
            "test_gain=",
            row["incumbent_minus_candidate_gain"],
            "cluster_ci=",
            (row["cluster_bootstrap_95_low"], row["cluster_bootstrap_95_high"]),
            "holm_p=",
            row["holm_adjusted_p_one_sided"],
        )
    print(f"device={report['protocol']['device']}; output={args.output_dir}")


if __name__ == "__main__":
    main()
