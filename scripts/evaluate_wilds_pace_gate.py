"""Run an offline, article-disjoint PACE commit-gate replay on WILDS CivilComments."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from scipy.stats import binomtest
from sklearn.feature_extraction.text import HashingVectorizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_wilds_candidate_selection as common
from shiftlab.data.gpu.environment import environment

DATASET_DIR = ROOT / "data/processed/wilds/c4f79606707951bcba11"
PROTOCOL = ROOT / "papers/shiftguard_unified/wilds_pace_gate_protocol_v1.md"
OUTPUT_DEFAULT = ROOT / "outputs/shiftguard_unified/real_data_development/wilds_pace_gate_v1"
SCOUT_SEED = 20261027
CERT_ORDER_SEED = 20261028
MODEL_SEED = 20261026
LAMBDA = 0.5
ALPHA = 0.05
BASELINE = (1e-4, 0.5)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pace_gate(
    candidate_correct: np.ndarray,
    incumbent_correct: np.ndarray,
    *,
    alpha: float = ALPHA,
    lam: float = LAMBDA,
) -> dict[str, Any]:
    """Apply PACE's single-bet McNemar e-process to paired Boolean scores."""
    candidate = np.asarray(candidate_correct, dtype=bool)
    incumbent = np.asarray(incumbent_correct, dtype=bool)
    if candidate.ndim != 1 or candidate.shape != incumbent.shape:
        raise ValueError("paired correctness arrays must be matching one-dimensional vectors")
    if not 0 < alpha < 1 or not 0 <= lam < 1:
        raise ValueError("alpha must be in (0, 1) and lambda in [0, 1)")

    log_e = 0.0
    wins = 0
    losses = 0
    discordant = 0
    evaluated = 0
    crossing_at: int | None = None
    threshold = -math.log(alpha)
    log_win = math.log1p(lam)
    log_loss = math.log1p(-lam)
    for candidate_value, incumbent_value in zip(candidate, incumbent, strict=True):
        evaluated += 1
        if candidate_value == incumbent_value:
            continue
        discordant += 1
        if candidate_value:
            wins += 1
            log_e += log_win
        else:
            losses += 1
            log_e += log_loss
        if log_e >= threshold:
            crossing_at = evaluated
            break
    return {
        "promoted": crossing_at is not None,
        "alpha": alpha,
        "lambda": lam,
        "threshold_e": 1.0 / alpha,
        "log_threshold": threshold,
        "log_e_at_stop": log_e,
        "e_at_stop": math.exp(log_e) if log_e < 700 else math.inf,
        "evaluated_instances": evaluated,
        "discordant_pairs": discordant,
        "candidate_wins": wins,
        "incumbent_wins": losses,
        "crossing_at_evaluated_instance": crossing_at,
    }


def fixed_n_mcnemar(
    candidate_correct: np.ndarray, incumbent_correct: np.ndarray, *, alpha: float = ALPHA
) -> dict[str, Any]:
    """One-sided exact McNemar/binomial test after the complete fixed sample."""
    candidate = np.asarray(candidate_correct, dtype=bool)
    incumbent = np.asarray(incumbent_correct, dtype=bool)
    if candidate.ndim != 1 or candidate.shape != incumbent.shape:
        raise ValueError("paired correctness arrays must be matching one-dimensional vectors")
    wins = int(np.count_nonzero(candidate & ~incumbent))
    losses = int(np.count_nonzero(~candidate & incumbent))
    discordant = wins + losses
    p_value = (
        1.0
        if discordant == 0
        else float(binomtest(wins, discordant, 0.5, alternative="greater").pvalue)
    )
    return {
        "promoted": p_value <= alpha,
        "alpha": alpha,
        "p_value_one_sided": p_value,
        "certification_instances": len(candidate),
        "discordant_pairs": discordant,
        "candidate_wins": wins,
        "incumbent_wins": losses,
    }


def one_row_per_article(
    rows: np.ndarray, article_ids: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Uniformly sample one row per article without consulting features or labels."""
    row_array = np.asarray(rows, dtype=np.int64)
    groups: dict[int, list[int]] = {}
    for row in row_array:
        groups.setdefault(int(article_ids[row]), []).append(int(row))
    selected = np.fromiter(
        (int(rng.choice(group)) for _, group in sorted(groups.items())),
        dtype=np.int64,
        count=len(groups),
    )
    return selected


def _candidate_table(
    *,
    probabilities: dict[float, np.ndarray],
    targets: np.ndarray,
    scout_positions: np.ndarray,
) -> tuple[pd.DataFrame, tuple[float, float]]:
    rows: list[dict[str, float | int]] = []
    for penalty in common.PENALTIES:
        for threshold in common.THRESHOLDS:
            prediction = probabilities[penalty][scout_positions] >= threshold
            rows.append(
                {
                    "penalty": float(penalty),
                    "threshold": float(threshold),
                    "scout_accuracy": float(np.mean(prediction == targets[scout_positions])),
                    "scout_articles": len(scout_positions),
                }
            )
    table = pd.DataFrame(rows)
    table["penalty_order"] = table.penalty.map(
        {value: i for i, value in enumerate(common.PENALTIES)}
    )
    table["threshold_order"] = table.threshold.map(
        {value: i for i, value in enumerate(common.THRESHOLDS)}
    )
    table = table.sort_values(
        ["scout_accuracy", "penalty_order", "threshold_order"],
        ascending=[False, True, True],
        kind="stable",
    ).reset_index(drop=True)
    selected = (float(table.loc[0, "penalty"]), float(table.loc[0, "threshold"]))
    return table.drop(columns=["penalty_order", "threshold_order"]), selected


def _metric_row(
    *,
    name: str,
    penalty: float,
    threshold: float,
    probability: np.ndarray,
    targets: np.ndarray,
    incumbent_prediction: np.ndarray,
    article_ids: np.ndarray,
    bootstrap_replicates: int,
) -> dict[str, Any]:
    prediction = probability >= threshold
    gain = (prediction == targets).astype(np.float64) - (incumbent_prediction == targets)
    estimate, low, high, _ = common._cluster_bootstrap(
        gain, article_ids, replicates=bootstrap_replicates, seed=20261029
    )
    return {
        "policy": name,
        "penalty": penalty,
        "threshold": threshold,
        "accuracy": float(np.mean(prediction == targets)),
        "error_rate": float(np.mean(prediction != targets)),
        "brier_score": float(np.mean((probability.astype(np.float64) - targets) ** 2)),
        "paired_accuracy_gain_vs_incumbent": estimate,
        "article_cluster_bootstrap_95_low": low,
        "article_cluster_bootstrap_95_high": high,
        "test_rows": len(targets),
        "test_articles": int(np.unique(article_ids).size),
    }


def run(
    *,
    dataset_dir: Path = DATASET_DIR,
    output_dir: Path = OUTPUT_DEFAULT,
    device: str = "cuda",
    bootstrap_replicates: int = 2000,
) -> dict[str, Any]:
    if device not in {"cuda", "cpu", "auto"}:
        raise ValueError("device must be cuda, cpu, or auto")
    if bootstrap_replicates < 200:
        raise ValueError("use at least 200 article-cluster bootstrap replicates")
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; explicitly rerun with --device cpu")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    device_obj = torch.device(device)
    start_time = time.perf_counter()
    dataset_dir = Path(dataset_dir)
    manifest_path = dataset_dir / "dataset_manifest.json"
    input_path = dataset_dir / "inputs.parquet"
    observation_path = dataset_dir / "observations.parquet"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("version") != "c4f79606707951bcba11":
        raise ValueError("protocol requires WILDS version c4f79606707951bcba11")
    if (
        source_manifest.get("raw_checksums", {}).get(
            "data\\raw\\wilds\\civilcomments-hf\\raw\\train-00000-of-00001.parquet"
        )
        != common.CIVIL_HF_SHA256
    ):
        raise ValueError("WILDS raw source checksum differs from the pinned version")
    if source_manifest.get("files", {}).get("inputs.parquet") != sha256(input_path):
        raise ValueError("inputs.parquet checksum differs from local dataset manifest")
    if source_manifest.get("files", {}).get("observations.parquet") != sha256(observation_path):
        raise ValueError("observations.parquet checksum differs from local dataset manifest")

    raw = common._load_data(dataset_dir)
    split = raw["split"]
    targets = raw["targets"]
    article_ids = raw["article_ids"]
    expected_counts = {"train": 269038, "validation": 45180, "test": 133782}
    split_counts = {name: int(np.count_nonzero(split == name)) for name in expected_counts}
    if split_counts != expected_counts:
        raise ValueError(f"official split counts changed: {split_counts}")

    # Hashing is stateless and text-only. The identity fields returned by the
    # loader are never passed to fitting, selection, certification or scoring.
    inputs = raw["texts"]
    vectorizer = HashingVectorizer(
        n_features=2**18,
        alternate_sign=False,
        norm="l2",
        binary=True,
        ngram_range=(1, 2),
        lowercase=True,
        dtype=np.float32,
    )
    features = vectorizer.transform(inputs).tocsr()
    del inputs, raw
    train_rows = np.flatnonzero(split == "train")
    validation_rows = np.flatnonzero(split == "validation")
    test_rows = np.flatnonzero(split == "test")
    x_train = features[train_rows]
    x_validation = features[validation_rows]
    x_test = features[test_rows]
    y_train = targets[train_rows]
    y_validation = targets[validation_rows]
    y_test = targets[test_rows]

    # Split at article level before selecting or scoring any validation row.
    validation_articles = np.unique(article_ids[validation_rows])
    rng = np.random.default_rng(SCOUT_SEED)
    article_order = rng.permutation(validation_articles)
    scout_article_count = len(article_order) // 2
    scout_articles = article_order[:scout_article_count]
    certification_articles = article_order[scout_article_count:]
    if np.intersect1d(scout_articles, certification_articles).size:
        raise RuntimeError("scout and certification article clusters overlap")
    validation_rng = np.random.default_rng(SCOUT_SEED + 1)
    scout_rows = one_row_per_article(
        validation_rows[np.isin(article_ids[validation_rows], scout_articles)],
        article_ids,
        validation_rng,
    )
    certification_rows = one_row_per_article(
        validation_rows[np.isin(article_ids[validation_rows], certification_articles)],
        article_ids,
        validation_rng,
    )
    certification_rng = np.random.default_rng(CERT_ORDER_SEED)
    certification_rows = certification_rows[certification_rng.permutation(len(certification_rows))]
    if np.intersect1d(article_ids[scout_rows], article_ids[certification_rows]).size:
        raise RuntimeError("sampled scout and certification comments share an article")
    validation_positions = np.full(len(split), -1, dtype=np.int64)
    validation_positions[validation_rows] = np.arange(len(validation_rows), dtype=np.int64)
    scout_positions = validation_positions[scout_rows]
    certification_positions = validation_positions[certification_rows]
    if np.any(scout_positions < 0) or np.any(certification_positions < 0):
        raise RuntimeError("sampled validation row is missing its local position")

    probabilities_validation: dict[float, np.ndarray] = {}
    states: dict[float, tuple[torch.Tensor, torch.Tensor]] = {}
    train_loss_history: dict[str, list[float]] = {}
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        for model_index, penalty in enumerate(common.PENALTIES):
            model = common._fit_model(
                x_train,
                y_train,
                penalty=penalty,
                device=device_obj,
                seed=MODEL_SEED + model_index,
            )
            train_loss_history[f"{penalty:g}"] = model[2]
            probabilities_validation[penalty] = common._predict(
                x_validation, model[:2], device=device_obj
            )
            states[penalty] = model[:2]

    scout_table, selected = _candidate_table(
        probabilities=probabilities_validation,
        targets=y_validation,
        scout_positions=scout_positions,
    )
    selected_penalty, selected_threshold = selected
    incumbent_cert = (
        probabilities_validation[BASELINE[0]][certification_positions] >= BASELINE[1]
    ) == y_validation[certification_positions]
    candidate_cert = (
        probabilities_validation[selected_penalty][certification_positions] >= selected_threshold
    ) == y_validation[certification_positions]
    pace_result = pace_gate(candidate_cert, incumbent_cert, alpha=ALPHA, lam=LAMBDA)
    fixed_result = fixed_n_mcnemar(candidate_cert, incumbent_cert, alpha=ALPHA)

    probabilities_test = {
        penalty: common._predict(x_test, states[penalty], device=device_obj)
        for penalty in common.PENALTIES
    }
    incumbent_prediction = probabilities_test[BASELINE[0]] >= BASELINE[1]
    chosen = {
        "incumbent": BASELINE,
        "greedy_scout": selected if selected is not None else BASELINE,
        "fixed_n_gate": selected if fixed_result["promoted"] else BASELINE,
        "pace_gate": selected if pace_result["promoted"] else BASELINE,
    }
    metrics: list[dict[str, Any]] = []
    for name, (penalty, threshold) in chosen.items():
        probability = probabilities_test[penalty]
        metrics.append(
            _metric_row(
                name=name,
                penalty=penalty,
                threshold=threshold,
                probability=probability,
                targets=y_test,
                incumbent_prediction=incumbent_prediction,
                article_ids=article_ids[test_rows],
                bootstrap_replicates=bootstrap_replicates,
            )
        )

    # Independent checksum of the selected model's test costs and scout/cert IDs.
    output_dir.mkdir(parents=True, exist_ok=True)
    scout_table.to_csv(output_dir / "scout_candidate_scores.csv", index=False)
    pd.DataFrame(metrics).to_csv(output_dir / "test_policy_metrics.csv", index=False)
    certification = {
        "selected_candidate": {"penalty": selected_penalty, "threshold": selected_threshold},
        "incumbent": {"penalty": BASELINE[0], "threshold": BASELINE[1]},
        "scout_articles": len(scout_rows),
        "certification_articles": len(certification_rows),
        "scout_certification_article_overlap": int(
            np.intersect1d(article_ids[scout_rows], article_ids[certification_rows]).size
        ),
        "pace": pace_result,
        "fixed_n_mcnemar": fixed_result,
        "test_metrics": metrics,
    }
    (output_dir / "certification_and_test_summary.json").write_text(
        json.dumps(certification, indent=2, sort_keys=True), encoding="utf-8"
    )
    report_lines = [
        "# WILDS CivilComments PACE gate — exploratory real-data development",
        "",
        f"**Status:** offline article-level PACE adaptation; device `{device_obj}`; one candidate selected on {len(scout_rows):,} scout articles and evaluated on disjoint certification articles.",
        "",
        f"Scout selected penalty `{selected_penalty:g}` at threshold `{selected_threshold:g}`. PACE {'promoted' if pace_result['promoted'] else 'retained the incumbent'} after {pace_result['evaluated_instances']:,} certification instances, {pace_result['discordant_pairs']:,} discordant pairs, and log-e {pace_result['log_e_at_stop']:.4f}; the threshold was log(20)={-math.log(ALPHA):.4f}.",
        f"The fixed-n exact McNemar gate {'promoted' if fixed_result['promoted'] else 'retained the incumbent'} after the full {fixed_result['certification_instances']:,}-article certification sample (one-sided p={fixed_result['p_value_one_sided']:.6g}).",
        "",
        "| Decision rule | Test accuracy | Paired accuracy gain vs incumbent | Article-cluster 95% interval |",
        "|---|---:|---:|---:|",
    ]
    for row in metrics:
        report_lines.append(
            f"| {row['policy']} | {row['accuracy']:.6f} | {row['paired_accuracy_gain_vs_incumbent']:+.6f} | "
            f"[{row['article_cluster_bootstrap_95_low']:+.6f}, {row['article_cluster_bootstrap_95_high']:+.6f}] |"
        )
    report_lines.extend(
        [
            "",
            "This is a PACE-rule adaptation for one paired binary-correctness comparison. It is not a reproduction of the agent self-evolution experiments, does not prove that WILDS article clusters are i.i.d. deployment instances, and uses no authentic timestamp order. The official test partition has prior repository exposure; report its results as exploratory. Labels are offline and all candidate costs are common-label outcomes, so the run does not establish active label-cost savings or real intervention utility.",
            "",
            f"Protocol SHA-256: `{sha256(PROTOCOL)}`. Runner SHA-256: `{sha256(Path(__file__))}`.",
        ]
    )
    (output_dir / "results.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest: dict[str, Any] = {
        "experiment": "wilds_civilcomments_pace_gate_development",
        "status": "exploratory_real_data_test_exposure_not_audited",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "repository_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "dataset": {
            "name": source_manifest["dataset"],
            "version": source_manifest["version"],
            "source_revision": common.CIVIL_HF_REVISION,
            "source_sha256": common.CIVIL_HF_SHA256,
            "manifest_sha256": sha256(manifest_path),
            "inputs_sha256": sha256(input_path),
            "observations_sha256": sha256(observation_path),
            "split_counts": split_counts,
            "validation_article_count": len(validation_articles),
            "test_article_count": int(np.unique(article_ids[test_rows]).size),
        },
        "protocol": {
            "path": PROTOCOL.relative_to(ROOT).as_posix(),
            "sha256": sha256(PROTOCOL),
            "runner_sha256": sha256(Path(__file__)),
            "candidate_selector_sha256": sha256(Path(common.__file__)),
            "scout_seed": SCOUT_SEED,
            "certification_order_seed": CERT_ORDER_SEED,
            "model_seed": MODEL_SEED,
            "candidate_bank": [
                {"penalty": float(p), "threshold": float(t)}
                for p in common.PENALTIES
                for t in common.THRESHOLDS
            ],
            "incumbent": {"penalty": BASELINE[0], "threshold": BASELINE[1]},
            "pace_lambda": LAMBDA,
            "pace_alpha": ALPHA,
            "device": str(device_obj),
            "bootstrap_replicates": bootstrap_replicates,
        },
        "decisions": certification,
        "label_contract": {
            "training_fit": len(train_rows),
            "scout_selection": len(scout_rows),
            "certification": len(certification_rows),
            "test_evaluator_only": len(test_rows),
            "timestamps_used": False,
            "identity_metadata_used": False,
        },
        "training_loss_history": train_loss_history,
        "runtime_seconds": time.perf_counter() - start_time,
        "environment": environment(),
        "runtime_warnings": sorted(str(item.message) for item in captured),
        "limitations": [
            "Official test partition has prior diagnostic exposure that is not fully audited; test estimates are exploratory.",
            "Certification treats one randomly selected comment per article as an independent instance; article-level exchangeability is a working assumption, not verified deployment sampling.",
            "Certification order is seeded random order, not historical chronology; WILDS has no verified row-level availability times.",
            "PACE controls one fixed candidate's per-candidate commit probability under its discordant-pair null; it does not give run-level FWER over a continuing candidate sequence.",
            "Only symmetric binary correctness is used for the PACE reproduction; asymmetric costs and the broader intervention controller are not evaluated.",
            "All data are offline and common-label; no label acquisition cost, causal policy value, or real-world utility is measured.",
        ],
        "artifacts": {},
    }
    for name in (
        "scout_candidate_scores.csv",
        "test_policy_metrics.csv",
        "certification_and_test_summary.json",
        "results.md",
    ):
        manifest["artifacts"][name] = sha256(output_dir / name)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    args = parser.parse_args()
    manifest = run(
        dataset_dir=args.dataset,
        output_dir=args.output,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(
        f"status={manifest['status']}; "
        f"pace_promoted={manifest['decisions']['pace']['promoted']}; "
        f"cert_instances={manifest['decisions']['pace']['evaluated_instances']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
