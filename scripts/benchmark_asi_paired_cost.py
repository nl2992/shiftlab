"""Matched fixed-horizon ASI allocation benchmark for paired policy costs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.dive.active_inference import (
    active_inference_propensities,
    prediction_powered_mean,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/asi_paired_cost_protocol.md"
SEED_OFFSET = 2026102800
SEED_COUNT = 30
N_SOURCE = 800
N_TARGET = 3200
LABEL_BUDGET = 640
ALPHA = 0.05
FN_COST = 2.0
FP_COST = 1.0
UNIFORM_MIXTURE = 0.5


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _outcome_probability(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-(1.2 * x[:, 0] - 0.9 * x[:, 1] + 0.5 * x[:, 2])))


def _actions(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    reference = (x[:, 0] > 0.0).astype(np.int8)
    candidate = (x[:, 0] + 0.35 * x[:, 1] > 0.25).astype(np.int8)
    return reference, candidate


def _paired_score(reference: np.ndarray, candidate: np.ndarray, y: np.ndarray) -> np.ndarray:
    reference_cost = np.where(reference == 1, FP_COST * (1 - y), FN_COST * y)
    candidate_cost = np.where(candidate == 1, FP_COST * (1 - y), FN_COST * y)
    return reference_cost - candidate_cost


def _conditional_score_moments(
    x: np.ndarray, probability: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    reference, candidate = _actions(x)
    score_y0 = _paired_score(reference, candidate, np.zeros(len(x), dtype=np.int8))
    score_y1 = _paired_score(reference, candidate, np.ones(len(x), dtype=np.int8))
    mean = (1 - probability) * score_y0 + probability * score_y1
    variance = probability * (1 - probability) * (score_y1 - score_y0) ** 2
    return mean, np.sqrt(np.maximum(variance, 0.0))


def _simulate(seed: int, device: str) -> list[dict[str, object]]:
    source_x_generator = torch.Generator(device=device).manual_seed(seed * 5 + 11)
    source_y_generator = torch.Generator(device=device).manual_seed(seed * 5 + 13)
    target_x_generator = torch.Generator(device=device).manual_seed(seed * 5 + 17)
    target_y_generator = torch.Generator(device=device).manual_seed(seed * 5 + 19)
    query_generator = torch.Generator(device=device).manual_seed(seed * 5 + 23)
    source_x_tensor = torch.randn((N_SOURCE, 4), generator=source_x_generator, device=device)
    source_probability_tensor = torch.sigmoid(
        1.2 * source_x_tensor[:, 0] - 0.9 * source_x_tensor[:, 1] + 0.5 * source_x_tensor[:, 2]
    )
    source_y_tensor = torch.bernoulli(source_probability_tensor, generator=source_y_generator)
    target_x_tensor = torch.randn((N_TARGET, 4), generator=target_x_generator, device=device)
    target_x_tensor[:, 0] += 0.5
    target_probability_tensor = torch.sigmoid(
        1.2 * target_x_tensor[:, 0] - 0.9 * target_x_tensor[:, 1] + 0.5 * target_x_tensor[:, 2]
    )
    target_y_tensor = torch.bernoulli(target_probability_tensor, generator=target_y_generator)
    uniforms = torch.rand(N_TARGET, generator=query_generator, device=device)
    source_x = source_x_tensor.cpu().numpy()
    source_y = source_y_tensor.cpu().numpy().astype(np.int8)
    target_x = target_x_tensor.cpu().numpy()
    target_y = target_y_tensor.cpu().numpy().astype(np.int8)
    probability_true = target_probability_tensor.cpu().numpy()
    uniforms_np = uniforms.cpu().numpy()

    model = LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")
    model.fit(source_x, source_y)
    probability_model = model.predict_proba(target_x)[:, 1]
    fitted_mean, fitted_uncertainty = _conditional_score_moments(target_x, probability_model)
    true_mean, oracle_uncertainty = _conditional_score_moments(target_x, probability_true)
    true_gain = float(true_mean.mean())
    asi_q = active_inference_propensities(
        fitted_uncertainty,
        expected_budget=LABEL_BUDGET,
        uniform_mixture=UNIFORM_MIXTURE,
    )
    uniform_matched_q = np.full(N_TARGET, float(asi_q.mean()))
    uniform_full_budget_q = np.full(N_TARGET, LABEL_BUDGET / N_TARGET)
    oracle_q = active_inference_propensities(
        oracle_uncertainty,
        expected_budget=LABEL_BUDGET,
        uniform_mixture=UNIFORM_MIXTURE,
    )
    target_score = _paired_score(*_actions(target_x), target_y)

    results: list[dict[str, object]] = []
    for method, propensities, predictions in (
        ("uniform_ppi_matched", uniform_matched_q, fitted_mean),
        ("uniform_ppi_full_budget", uniform_full_budget_q, fitted_mean),
        ("asi_residual_scale", asi_q, fitted_mean),
        ("oracle_asi", oracle_q, true_mean),
    ):
        queried = uniforms_np < propensities
        observed = np.full(N_TARGET, np.nan)
        observed[queried] = target_score[queried]
        estimate = prediction_powered_mean(
            predictions,
            queried,
            observed,
            propensities,
            alpha=ALPHA,
        )
        results.append(
            {
                "seed": seed,
                "method": method,
                "device": device,
                "true_target_gain": true_gain,
                "estimate": estimate["estimate"],
                "error": estimate["estimate"] - true_gain,
                "standard_error": estimate["standard_error"],
                "ci_lower": estimate["lower"],
                "ci_upper": estimate["upper"],
                "ci_covered": estimate["lower"] <= true_gain <= estimate["upper"],
                "ci_width": estimate["upper"] - estimate["lower"],
                "labels_queried": int(estimate["labels_queried"]),
                "expected_labels": estimate["expected_labels"],
                "expected_budget": LABEL_BUDGET,
                "propensity_min": float(propensities.min()),
                "propensity_max": float(propensities.max()),
                "propensity_ess": float(propensities.sum() ** 2 / np.square(propensities).sum()),
            }
        )
    return results


def run(*, output: Path, device: str, seed_count: int = SEED_COUNT) -> Path:
    if seed_count < 1:
        raise ValueError("seed_count must be positive")
    device = resolve_device(device, n=N_SOURCE + N_TARGET, d=4, chunk_size=2048)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    protocol_snapshot = output / "protocol_snapshot.md"
    protocol_snapshot.write_bytes(PROTOCOL.read_bytes())
    source_path = Path(__file__).resolve()
    implementation_path = ROOT / "src/shiftlab/dive/active_inference.py"
    source_snapshots = {}
    for path in (source_path, implementation_path):
        relative = path.relative_to(ROOT)
        snapshot = output / "execution_sources" / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(path.read_bytes())
        source_snapshots[str(relative)] = snapshot
    metrics = [
        row
        for seed in range(SEED_OFFSET, SEED_OFFSET + seed_count)
        for row in _simulate(seed, device)
    ]
    detail = pd.DataFrame(metrics)
    detail_path = output / "asi_paired_cost_streams.parquet"
    detail.to_parquet(detail_path, index=False)
    summary = detail.groupby("method", as_index=False).agg(
        streams=("seed", "count"),
        mean_absolute_error=("error", lambda x: float(np.abs(x).mean())),
        rmse=("error", lambda x: float(np.sqrt(np.square(x).mean()))),
        mean_ci_width=("ci_width", "mean"),
        empirical_95_ci_coverage=("ci_covered", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_expected_labels=("expected_labels", "mean"),
        median_effective_sample_size=("propensity_ess", "median"),
    )
    summary_path = output / "asi_paired_cost_summary.csv"
    summary.to_csv(summary_path, index=False)
    enriched = detail.assign(
        abs_error=detail["error"].abs(),
        squared_error=detail["error"] ** 2,
    )
    rng = np.random.default_rng(2026102899)
    contrast_rows = []
    for reference in ("uniform_ppi_matched", "uniform_ppi_full_budget"):
        for metric in ("abs_error", "squared_error", "ci_width", "ci_covered"):
            values = enriched.pivot(index="seed", columns="method", values=metric)
            if metric == "ci_covered":
                paired = values["asi_residual_scale"].astype(float) - values[reference].astype(
                    float
                )
            else:
                paired = values["asi_residual_scale"] - values[reference]
            reported_metric = metric
            if metric == "squared_error":
                reported_metric = "mean_squared_error"
            draws = rng.integers(0, len(paired), size=(20_000, len(paired)))
            boot = paired.to_numpy()[draws].mean(axis=1)
            contrast_rows.append(
                {
                    "treatment": "asi_residual_scale",
                    "reference": reference,
                    "metric": reported_metric,
                    "seeds": len(paired),
                    "mean_paired_difference": float(paired.mean()),
                    "bootstrap_ci_level": 0.95,
                    "bootstrap_ci_low": float(np.quantile(boot, 0.025)),
                    "bootstrap_ci_high": float(np.quantile(boot, 0.975)),
                    "bootstrap_draws": 20_000,
                    "bootstrap_seed": 2026102899,
                }
            )
    contrasts = pd.DataFrame(contrast_rows)
    contrasts_path = output / "asi_paired_contrasts.csv"
    contrasts.to_csv(contrasts_path, index=False)
    manifest = {
        "experiment": "asi_fixed_horizon_paired_cost_allocation",
        "status": "development_not_confirmation",
        "supersedes": (
            "asi_paired_cost_dev_v1 (budget mismatch); dev_v2/dev_v3 (same seeds; v4 uses component-specific RNG streams)"
        ),
        "created_utc": datetime.now(UTC).isoformat(),
        "device": device,
        "hardware": environment(),
        "seeds": {"offset": SEED_OFFSET, "count": seed_count},
        "n_source": N_SOURCE,
        "n_target": N_TARGET,
        "expected_label_budget": LABEL_BUDGET,
        "random_streams": {
            "per_seed": "dedicated torch.Generator streams: seed*5 + 11/13/17/19/23 for source features/source labels/target features/target labels/query uniforms",
            "deterministic_algorithms": "GPU generation is keyed by per-stream generators; model fitting uses deterministic CPU LogisticRegression lbfgs",
        },
        "uniform_mixture": UNIFORM_MIXTURE,
        "alpha": ALPHA,
        "source_sha256": {key: _sha256(path) for key, path in source_snapshots.items()},
        "source_snapshot_directory": "execution_sources",
        "protocol_snapshot_sha256": _sha256(protocol_snapshot),
        "metrics_sha256": _sha256(detail_path),
        "summary_sha256": _sha256(summary_path),
        "paired_contrasts_sha256": _sha256(contrasts_path),
        "limitations": [
            "ASI is evaluated here as a fixed-horizon mean-estimation and allocation baseline, not a sequential monitor.",
            "The 95% intervals are asymptotic; the development seed count does not calibrate coverage.",
            "The Bernoulli design matches expected labels, not a pathwise hard cap.",
            "The oracle allocation is evaluator-only and is an upper-bound diagnostic.",
            "The imposed costs are synthetic units and the labels are immediate.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = output / "results.md"
    report.write_text(
        "# ASI paired-cost development benchmark\n\n"
        f"This is a {seed_count}-seed fixed-horizon development comparison. The primary comparison matches ASI and uniform sampling at the same expected label count within each seed. A secondary uniform baseline uses the full 640 expected-label allowance. It evaluates asymptotic mean intervals and does not test sequential alarm validity.\n\n"
        + summary.to_string(index=False, float_format=lambda value: f"{value:.4f}")
        + "\n\n## Paired seed-block contrasts (descriptive percentile bootstrap)\n\n"
        + contrasts.to_string(index=False, float_format=lambda value: f"{value:.4f}")
        + "\n\nThe primary ASI and uniform methods have equal expected label counts within each seed; the secondary uniform method targets 640 expected labels. Actual Bernoulli label counts vary and are reported in the Parquet stream table. The oracle row is evaluator-only. These results do not support a superiority or real-utility claim.\n",
        encoding="utf-8",
    )
    manifest["report_sha256"] = _sha256(report)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return detail_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--seeds", type=int, default=SEED_COUNT)
    args = parser.parse_args()
    result = run(output=args.output, device=args.device, seed_count=args.seeds)
    print(f"wrote {result.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
