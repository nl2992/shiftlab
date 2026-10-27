"""Run the frozen PPRM predictive-risk development benchmark on CPU or CUDA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy.integrate import quad
from scipy.special import expit
from scipy.stats import norm

from shiftlab.data.gpu.environment import environment
from shiftlab.dive.eprocess import BoundedMeanEProcess
from shiftlab.dive.pprm_risk_monitor import (
    PPRMBatchEstimate,
    PPRMRiskMonitor,
    PredictableReliance,
    prediction_powered_batch_risk,
    source_prediction_powered_values,
    source_risk_upper_bound_betting,
)

SCENARIOS = ("stationary", "benign_nuisance", "predictive_harm", "decision_cost_shift")
PROTOCOL = Path("papers/shiftguard_unified/pprm_predictive_risk_development_protocol.md")
DEFAULT_OUTPUT = Path("outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_dev_v1")
SOURCE_N = 2048
SOURCE_UNLABELED_PER_LABEL = 15
ROUNDS = 1200
ONSET = 400
PREDICTIVE_TOLERANCE = 0.05
DECISION_MARGIN = 0.05
ALPHA_SOURCE = 0.025
ALPHA_TEST = 0.025
PREDICTIVE_HARM_FLIP = 0.30


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@cache
def _risk_and_cost_truth(*, flip: float, false_negative_cost: float) -> tuple[float, float]:
    def integrand(x: float) -> tuple[float, float]:
        p = float(expit(2.0 * x))
        p = p * (1.0 - flip) + (1.0 - p) * flip
        density = float(norm.pdf(x))
        candidate = int(x > 0.0)
        reference = int(x > -0.5)

        def expected_cost(action: int) -> float:
            if action == 0:
                return false_negative_cost * p
            return 1.0 - p

        risk = p if candidate == 0 else 1.0 - p
        paired_cost = expected_cost(candidate) - expected_cost(reference)
        return risk * density, paired_cost * density

    intervals = ((-10.0, -0.5), (-0.5, 0.0), (0.0, 10.0))
    risk = sum(quad(lambda x: integrand(x)[0], lo, hi, epsabs=1e-11)[0] for lo, hi in intervals)
    paired_cost = sum(
        quad(lambda x: integrand(x)[1], lo, hi, epsabs=1e-11)[0] for lo, hi in intervals
    )
    return float(risk), float(paired_cost)


def _device(requested: str) -> torch.device:
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available")
        return torch.device("cuda")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device("cpu")


def _sample(
    *,
    count: int,
    generator: torch.Generator,
    device: torch.device,
    nuisance_shift: float,
    flip_probability: float,
    with_labels: bool,
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None, np.ndarray]:
    x = torch.randn((count, 4), generator=generator, device=device)
    if nuisance_shift:
        x[:, 1] += nuisance_shift
    model_prediction = x[:, 0] > 0.0
    auxiliary_prediction = x[:, 0] > -0.25
    proxy_loss = (model_prediction != auxiliary_prediction).to(torch.float64)
    labels_np: np.ndarray | None = None
    true_loss_np: np.ndarray | None = None
    if with_labels:
        probability = torch.sigmoid(2.0 * x[:, 0])
        if flip_probability:
            probability = (
                probability * (1.0 - flip_probability) + (1.0 - probability) * flip_probability
            )
        labels = torch.bernoulli(probability, generator=generator).bool()
        labels_np = labels.to(torch.float64).cpu().numpy()
        true_loss_np = (model_prediction != labels).to(torch.float64).cpu().numpy()
    return x.cpu().numpy(), labels_np, true_loss_np, proxy_loss.cpu().numpy()


def _paired_cost_difference(
    x: np.ndarray,
    labels: np.ndarray,
    *,
    false_negative_cost: float,
) -> np.ndarray:
    x0 = x[:, 0]
    candidate = x0 > 0.0
    reference = x0 > -0.5
    candidate_cost = np.where(
        candidate,
        np.where(labels == 0, 1.0, 0.0),
        np.where(labels == 1, false_negative_cost, 0.0),
    )
    reference_cost = np.where(
        reference,
        np.where(labels == 0, 1.0, 0.0),
        np.where(labels == 1, false_negative_cost, 0.0),
    )
    return candidate_cost - reference_cost


def _run_stream(seed: int, scenario: str, device: torch.device) -> list[dict]:
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    _, _, source_loss, source_proxy_l = _sample(
        count=SOURCE_N,
        generator=generator,
        device=device,
        nuisance_shift=0,
        flip_probability=0,
        with_labels=True,
    )
    _, _, _, source_proxy_u = _sample(
        count=SOURCE_N * SOURCE_UNLABELED_PER_LABEL,
        generator=generator,
        device=device,
        nuisance_shift=0,
        flip_probability=0,
        with_labels=False,
    )
    assert source_loss is not None
    source_pprm_values = source_prediction_powered_values(
        source_loss,
        source_proxy_l,
        source_proxy_u,
        reliance=1.0,
    )
    if len(source_pprm_values) != SOURCE_N:
        raise RuntimeError("source PPI pairing did not produce one value per labeled sample")
    source_upper_pprm = source_risk_upper_bound_betting(
        source_pprm_values,
        max_reliance=1.0,
        alpha_source=ALPHA_SOURCE,
    )
    source_upper_srm = source_risk_upper_bound_betting(
        source_loss,
        max_reliance=0.0,
        alpha_source=ALPHA_SOURCE,
    )
    if not source_upper_pprm + PREDICTIVE_TOLERANCE <= 1:
        raise RuntimeError("PPRM source upper bound plus tolerance exceeds bounded risk support")
    if not source_upper_srm + PREDICTIVE_TOLERANCE <= 1:
        raise RuntimeError("SRM source upper bound plus tolerance exceeds bounded risk support")

    pprm = PPRMRiskMonitor(
        source_upper_bound=source_upper_pprm,
        tolerance=PREDICTIVE_TOLERANCE,
        max_reliance=1.0,
        alpha_test=ALPHA_TEST,
        lambda_count=64,
    )
    srm = PPRMRiskMonitor(
        source_upper_bound=source_upper_srm,
        tolerance=PREDICTIVE_TOLERANCE,
        max_reliance=0.0,
        alpha_test=ALPHA_TEST,
        lambda_count=64,
    )
    reliance = PredictableReliance(
        window_rounds=60,
        max_reliance=1.0,
        initial_reliance=1.0,
    )
    paired_process = BoundedMeanEProcess(bound=4.05, alpha=0.05)
    first_crossing: dict[str, int | None] = {
        "pprm": None,
        "srm": None,
        "paired_cost": None,
    }
    expected_risk_path: list[float] = []
    expected_cost_path: list[float] = []
    observed_predictive_losses: list[float] = []
    observed_pprm_estimates: list[float] = []
    observed_paired_costs: list[float] = []
    predictive_flip = PREDICTIVE_HARM_FLIP if scenario == "predictive_harm" else 0.0
    risk_pre, cost_pre = _risk_and_cost_truth(flip=0, false_negative_cost=1)
    risk_post, cost_post = _risk_and_cost_truth(
        flip=predictive_flip,
        false_negative_cost=4 if scenario == "decision_cost_shift" else 1,
    )

    for round_index in range(ROUNDS):
        post_onset = round_index >= ONSET
        nuisance_shift = 2.0 if scenario == "benign_nuisance" and post_onset else 0.0
        flip = predictive_flip if post_onset else 0.0
        false_negative_cost = 4.0 if scenario == "decision_cost_shift" and post_onset else 1.0
        # Draw L and U independently; no true labels are materialized for U.
        x_labeled, labels_l, true_loss_l, proxy_labeled = _sample(
            count=1,
            generator=generator,
            device=device,
            nuisance_shift=nuisance_shift,
            flip_probability=flip,
            with_labels=True,
        )
        _, _, _, proxy_unlabeled = _sample(
            count=SOURCE_UNLABELED_PER_LABEL,
            generator=generator,
            device=device,
            nuisance_shift=nuisance_shift,
            flip_probability=flip,
            with_labels=False,
        )
        assert labels_l is not None and true_loss_l is not None
        eta = reliance.choose(labeled_count=1, unlabeled_count=SOURCE_UNLABELED_PER_LABEL)
        pprm_batch = prediction_powered_batch_risk(
            true_loss_l[:1],
            proxy_labeled,
            proxy_unlabeled,
            reliance=eta,
        )
        if pprm.update(pprm_batch) and first_crossing["pprm"] is None:
            first_crossing["pprm"] = round_index
        if (
            srm.update(
                PPRMBatchEstimate(
                    estimate=float(true_loss_l[0]),
                    reliance=0.0,
                    labeled_count=1,
                    unlabeled_count=1,
                )
            )
            and first_crossing["srm"] is None
        ):
            first_crossing["srm"] = round_index
        reliance.update(true_loss_l[:1], proxy_labeled, proxy_unlabeled)
        observed_predictive_losses.append(float(true_loss_l[0]))
        observed_pprm_estimates.append(pprm_batch.estimate)

        paired_cost = float(
            _paired_cost_difference(
                x_labeled,
                labels_l,
                false_negative_cost=false_negative_cost,
            )[0]
        )
        observed_paired_costs.append(paired_cost)
        if (
            paired_process.update(paired_cost - DECISION_MARGIN) >= -math.log(0.05)
            and first_crossing["paired_cost"] is None
        ):
            first_crossing["paired_cost"] = round_index

        expected_risk_path.append(risk_post if post_onset else risk_pre)
        expected_cost_path.append(cost_post if post_onset else cost_pre)

    mean_cost_path = float(np.mean(expected_cost_path))
    method_alternatives = {
        "pprm_predictive_risk": scenario == "predictive_harm",
        "srm_predictive_risk": scenario == "predictive_harm",
        "dive_paired_cost": scenario == "decision_cost_shift",
    }
    rows: list[dict] = []
    horizon = {
        "rounds": ROUNDS,
        "onset": ONSET,
        "source_n": SOURCE_N,
        "source_u_n": SOURCE_N * SOURCE_UNLABELED_PER_LABEL,
        "test_labeled": ROUNDS,
        "test_unlabeled": ROUNDS * SOURCE_UNLABELED_PER_LABEL,
    }
    for method in ("pprm_predictive_risk", "srm_predictive_risk", "dive_paired_cost"):
        crossing = (
            first_crossing[method.split("_")[0]]
            if method != "dive_paired_cost"
            else first_crossing["paired_cost"]
        )
        positive_alternative = method_alternatives[method]
        rows.append(
            {
                "scenario": scenario,
                "seed": seed,
                "method": method,
                "target": "paired_decision_cost"
                if method == "dive_paired_cost"
                else "predictive_risk",
                "registered_alternative": positive_alternative,
                "alarm": crossing is not None,
                "first_crossing_round": crossing,
                "post_onset_detection": (
                    bool(crossing is not None and crossing >= ONSET)
                    if positive_alternative
                    else None
                ),
                "pre_onset_alarm": bool(crossing is not None and crossing < ONSET),
                "delay_after_onset": (
                    int(crossing - ONSET)
                    if positive_alternative and crossing is not None and crossing >= ONSET
                    else None
                ),
                "alarm_under_method_null": bool(
                    crossing is not None and (not positive_alternative or crossing < ONSET)
                ),
                "source_upper_bound_pprm": source_upper_pprm,
                "source_upper_bound_srm": source_upper_srm,
                "source_predictive_risk_truth": risk_pre,
                "pre_onset_predictive_risk_truth": risk_pre,
                "post_onset_predictive_risk_truth": risk_post,
                "pre_onset_paired_cost_truth": cost_pre,
                "post_onset_paired_cost_truth": cost_post,
                "mean_running_predictive_risk_truth": float(np.mean(expected_risk_path)),
                "mean_running_paired_cost_truth": mean_cost_path,
                "observed_mean_predictive_loss": float(np.mean(observed_predictive_losses)),
                "observed_post_onset_predictive_loss": float(
                    np.mean(observed_predictive_losses[ONSET:])
                ),
                "observed_mean_pprm_estimate": float(np.mean(observed_pprm_estimates)),
                "observed_mean_paired_cost": float(np.mean(observed_paired_costs)),
                "observed_post_onset_paired_cost": float(np.mean(observed_paired_costs[ONSET:])),
                "mean_processed_rounds": ROUNDS,
                **horizon,
                "generator_device": str(device),
            }
        )
    return rows


def run(
    *,
    seeds: int = 30,
    seed_offset: int = 70_000_000,
    device: str = "cuda",
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict:
    if seeds < 2:
        raise ValueError("seeds must be at least two")
    resolved_device = _device(device)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    rows: list[dict] = []
    for scenario in SCENARIOS:
        for seed in range(seed_offset, seed_offset + seeds):
            rows.extend(_run_stream(seed, scenario, resolved_device))

    metrics = pd.DataFrame(rows)
    summary = (
        metrics.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            alarms=("alarm", "sum"),
            alarm_rate=("alarm", "mean"),
            method_null_alarms=("alarm_under_method_null", "sum"),
            method_null_alarm_rate=("alarm_under_method_null", "mean"),
            post_onset_detections=("post_onset_detection", "sum"),
            post_onset_detection_rate=("post_onset_detection", "mean"),
            pre_onset_alarms=("pre_onset_alarm", "sum"),
            mean_delay=("delay_after_onset", "mean"),
            mean_pprm_source_upper=("source_upper_bound_pprm", "mean"),
            mean_srm_source_upper=("source_upper_bound_srm", "mean"),
            predictive_risk_truth=("post_onset_predictive_risk_truth", "mean"),
            paired_cost_truth=("post_onset_paired_cost_truth", "mean"),
            observed_predictive_loss=("observed_mean_predictive_loss", "mean"),
            observed_post_onset_predictive_loss=("observed_post_onset_predictive_loss", "mean"),
            observed_pprm_estimate=("observed_mean_pprm_estimate", "mean"),
            observed_paired_cost=("observed_mean_paired_cost", "mean"),
            observed_post_onset_paired_cost=("observed_post_onset_paired_cost", "mean"),
        )
        .reset_index()
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    metrics.to_parquet(output_dir / "metrics.parquet", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    summary.to_parquet(output_dir / "summary.parquet", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    time = np.arange(ROUNDS)
    for scenario in SCENARIOS:
        predictive_flip = PREDICTIVE_HARM_FLIP if scenario == "predictive_harm" else 0.0
        risk_pre, _ = _risk_and_cost_truth(flip=0, false_negative_cost=1)
        risk_post, _ = _risk_and_cost_truth(flip=predictive_flip, false_negative_cost=1)
        path = np.where(time >= ONSET, risk_post, risk_pre)
        axes[0].plot(time, path, label=scenario)
    axes[0].axvline(ONSET, color="black", linestyle="--", linewidth=1)
    axes[0].set(title="Evaluator-known 0–1 risk", xlabel="Round", ylabel="Expected risk")
    axes[0].legend(frameon=False, fontsize=8)

    pivot = summary.pivot(index="scenario", columns="method", values="alarm_rate")
    pivot.plot(kind="bar", ax=axes[1], width=0.78)
    axes[1].set(
        title="Development alarm rates (30 seeds)",
        xlabel="Scenario",
        ylabel="Fraction of streams with an alarm",
        ylim=(0, 1),
    )
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    figure_path = output_dir / "pprm_predictive_risk_development.png"
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    manifest = {
        "experiment": "pprm_predictive_risk_development",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": (
            "exploratory_development_30_seed"
            if seeds == 30 and seed_offset == 70_000_000
            else "smoke_or_nonprotocol_run"
        ),
        "protocol": str(PROTOCOL),
        "config": {
            "seeds": seeds,
            "seed_offset": seed_offset,
            "scenarios": list(SCENARIOS),
            "device_requested": device,
            "device_resolved": str(resolved_device),
            "source_n": SOURCE_N,
            "source_unlabeled_per_label": SOURCE_UNLABELED_PER_LABEL,
            "rounds": ROUNDS,
            "onset": ONSET,
            "predictive_tolerance": PREDICTIVE_TOLERANCE,
            "decision_margin": DECISION_MARGIN,
            "alpha_source": ALPHA_SOURCE,
            "alpha_test": ALPHA_TEST,
            "predictive_harm_flip_probability": PREDICTIVE_HARM_FLIP,
            "methods": ["PPRM predictive risk", "SRM predictive risk", "DIVE paired cost"],
        },
        "results": summary.to_dict(orient="records"),
        "limitations": [
            "Thirty streams per cell are a development screen, not independent confirmation or a Monte Carlo proof of error control.",
            "PPRM/SRM predictive-risk and DIVE paired-cost nulls differ; alarm rates are not interchangeable.",
            "Synthetic decision costs are imposed and do not represent application revenue or observed operational utility.",
            "The experiment does not evaluate candidate promotion, adaptation, or delayed feedback.",
        ],
        "source_hashes": {
            "script": _sha256(Path(__file__).resolve()),
            "protocol": _sha256(PROTOCOL),
            "pprm_module": _sha256(Path("src/shiftlab/dive/pprm_risk_monitor.py")),
            "eprocess_module": _sha256(Path("src/shiftlab/dive/eprocess.py")),
        },
        "environment": environment(),
        "rows": len(metrics),
        "artifact_sha256": {},
    }
    for name in (
        "metrics.csv",
        "metrics.parquet",
        "summary.csv",
        "summary.parquet",
        figure_path.name,
    ):
        manifest["artifact_sha256"][name] = _sha256(output_dir / name)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    report = [
        "# PPRM predictive-risk development results",
        "",
        "**Status:** exploratory 30-seed development; not confirmation or evidence of type-I control.",
        "",
        "PPRM and SRM monitor running predictive risk relative to source risk. DIVE monitors the paired decision-cost contrast. Their nulls differ, so the alarm rates below are descriptive and not head-to-head error or power comparisons.",
        "",
        summary.to_markdown(index=False),
        "",
        "The decision-cost-only scenario changes evaluator costs while preserving the label distribution; it is included to show the endpoint distinction. The specified expected risk/cost values and per-seed traces are in the Parquet and CSV artifacts.",
        "",
        "![PPRM development results](pprm_predictive_risk_development.png)",
        "",
        "See `manifest.json` for configuration, source hashes, environment, and checksums.",
    ]
    (output_dir / "results.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest["artifact_sha256"]["results.md"] = _sha256(output_dir / "results.md")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=70_000_000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = run(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
        output_dir=args.output_dir,
    )
    print(pd.DataFrame(manifest["results"]).to_string(index=False))
    print(f"rows={manifest['rows']}; output={args.output_dir}")


if __name__ == "__main__":
    main()
