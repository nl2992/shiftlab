"""Validate predictable-query monitoring under a martingale-null volatility regime."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        HARM_EFFECTS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_common_random_numbers,
        scenario_harm_effect,
        simulate_arm,
    )
    from scripts.confirm_history_predictable_query_bounds import (
        ARMS,
        build_dose_results,
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )
except SyntaxError as exc:  # pragma: no cover - protects accidental invalid import edits
    raise RuntimeError("fix the module import list") from exc
except ModuleNotFoundError:  # Direct execution sets sys.path to scripts/.
    from calibrate_history_predictable_query_bounds import (
        HARM_EFFECTS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_common_random_numbers,
        scenario_harm_effect,
        simulate_arm,
    )
    from confirm_history_predictable_query_bounds import (
        ARMS,
        build_dose_results,
        exact_one_sided_upper,
        paired_bootstrap_interval,
    )

DEFAULT_SEED = 27108027
DEFAULT_STREAMS = 4000
HORIZON = 2400
MARKOV_FLIP_PROBABILITY = 0.05
MARKOV_HARM_SCENARIOS = tuple(f"markov_volatility_harm_d{effect:.2f}" for effect in HARM_EFFECTS)
NULL_SCENARIOS = (MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO)
SCENARIOS = (*NULL_SCENARIOS, *MARKOV_HARM_SCENARIOS)
TRAINING_EVENTS = 512
HIGH_CONTEXT_PROBABILITY = {0: 0.50, 1: 0.25}
LOW_PROBABILITY = {0: 0.56, 1: 0.55}
HIGH_PROBABILITY = {0: 0.488, 1: 0.47}
EFFECT_PROBABILITY_SHIFT_PER_UNIT = 1 / 3.75
ORACLE_HARM_MEAN_PER_UNIT = {0: 4 / 3, 1: 2 / 3}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sample_markov_states(
    *, streams: int, steps: int, seed: int, device: torch.device
) -> torch.Tensor:
    if streams < 1 or steps < 1:
        raise ValueError("streams and steps must be positive")
    generator = torch.Generator(device=device).manual_seed(seed)
    initial = torch.randint(0, 2, (streams,), generator=generator, device=device)
    flip = torch.rand((steps - 1, streams), generator=generator, device=device)
    flip_parity = (flip < MARKOV_FLIP_PROBABILITY).to(torch.int64).cumsum(dim=0).remainder_(2)
    states = torch.cat([initial.unsqueeze(0), initial.unsqueeze(0) ^ flip_parity], dim=0)
    return states


def _empirical_training_proxy(
    *, streams: int, seed: int, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator(device=device).manual_seed(seed)
    states = sample_markov_states(
        streams=streams, steps=TRAINING_EVENTS, seed=seed + 101, device=device
    )
    high_context_probability = torch.where(
        states == 0, HIGH_CONTEXT_PROBABILITY[0], HIGH_CONTEXT_PROBABILITY[1]
    )
    context = (
        torch.rand((TRAINING_EVENTS, streams), generator=generator, device=device)
        < high_context_probability
    ).to(torch.int64)
    low_p = torch.where(states == 0, LOW_PROBABILITY[0], LOW_PROBABILITY[1])
    high_p = torch.where(states == 0, HIGH_PROBABILITY[0], HIGH_PROBABILITY[1])
    probability = torch.where(context == 1, high_p, low_p)
    outcome = (
        torch.rand((TRAINING_EVENTS, streams), generator=generator, device=device) < probability
    )
    cost = torch.where(context == 1, 5.0, 1.0)
    z = cost * (1 - 2 * outcome.to(torch.float32))
    low_mask = context == 0
    high_mask = ~low_mask
    low_count = low_mask.sum(dim=0)
    high_count = high_mask.sum(dim=0)
    if torch.any(low_count == 0) or torch.any(high_count == 0):
        raise RuntimeError("Markov training sample omitted a context stratum")
    return (
        ((z * low_mask).sum(dim=0) / low_count).clamp(-5, 5),
        ((z * high_mask).sum(dim=0) / high_count).clamp(-5, 5),
    )


def generate_markov_dependent_data(
    *, streams: int, horizon: int, seed: int, device: torch.device
) -> dict[str, torch.Tensor | float]:
    """Create dependent states/context/outcomes with a statewise zero-mean null."""
    data: dict[str, torch.Tensor | float] = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    states = sample_markov_states(
        streams=streams, steps=horizon, seed=seed + 900_000_000, device=device
    )
    context_generator = torch.Generator(device=device).manual_seed(seed + 910_000_000)
    high_probability_by_state = torch.where(
        states == 0,
        HIGH_CONTEXT_PROBABILITY[0],
        HIGH_CONTEXT_PROBABILITY[1],
    )
    context = (
        torch.rand((horizon, streams), generator=context_generator, device=device)
        < high_probability_by_state
    ).to(torch.int64)
    p_low = torch.where(states == 0, LOW_PROBABILITY[0], LOW_PROBABILITY[1]).to(torch.float32)
    p_high = torch.where(states == 0, HIGH_PROBABILITY[0], HIGH_PROBABILITY[1]).to(torch.float32)
    h_low, h_high = _empirical_training_proxy(
        streams=streams, seed=seed + 920_000_000, device=device
    )
    data.update(
        {
            "context": context,
            "p_low": p_low,
            "p_high": p_high,
            "regime_state": states,
            "oracle_harm_mean_per_unit": torch.where(
                states == 0,
                ORACLE_HARM_MEAN_PER_UNIT[0],
                ORACLE_HARM_MEAN_PER_UNIT[1],
            ).to(torch.float32),
            "effect_probability_shift_per_unit": EFFECT_PROBABILITY_SHIFT_PER_UNIT,
            "h_low": h_low,
            "h_high": h_high,
        }
    )
    return data


def verify_dgp_algebra() -> None:
    state0_null = (1 - HIGH_CONTEXT_PROBABILITY[0]) * (
        1 - 2 * LOW_PROBABILITY[0]
    ) + HIGH_CONTEXT_PROBABILITY[0] * 5 * (1 - 2 * HIGH_PROBABILITY[0])
    state1_null = (1 - HIGH_CONTEXT_PROBABILITY[1]) * (
        1 - 2 * LOW_PROBABILITY[1]
    ) + HIGH_CONTEXT_PROBABILITY[1] * 5 * (1 - 2 * HIGH_PROBABILITY[1])
    if abs(state0_null) > 1e-12 or abs(state1_null) > 1e-12:
        raise RuntimeError("each Markov state must have exactly zero conditional mean")
    if abs(0.5 * ORACLE_HARM_MEAN_PER_UNIT[0] + 0.5 * ORACLE_HARM_MEAN_PER_UNIT[1] - 1) > 1e-12:
        raise RuntimeError("stationary Markov state mixture must preserve unit aggregate harm")
    for effect in HARM_EFFECTS:
        if min(HIGH_PROBABILITY.values()) - effect * EFFECT_PROBABILITY_SHIFT_PER_UNIT <= 0:
            raise RuntimeError("registered harm effect puts an outcome probability below zero")


def run_markov_validation(*, streams: int, seed: int, device_name: str, output: Path) -> Path:
    if streams < 100:
        raise ValueError("validation requires at least 100 paired streams")
    if seed < DEFAULT_SEED:
        raise ValueError(f"dependent validation seeds must start at {DEFAULT_SEED} or later")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    verify_dgp_algebra()
    device = torch.device(device_name)
    data = generate_markov_dependent_data(
        streams=streams, horizon=HORIZON, seed=seed, device=device
    )
    oracle_coeff_cpu = data["oracle_harm_mean_per_unit"].cpu().numpy()
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        for query_policy, q_min, bound_mode in ARMS:
            arm_rows = simulate_arm(
                scenario=scenario,
                streams=streams,
                horizon=HORIZON,
                seed=seed,
                data=data,
                device=device,
                query_policy=query_policy,
                q_min=q_min,
                bound_mode=bound_mode,
            )
            effect = scenario_harm_effect(scenario)
            if effect is not None and effect > 0:
                for row in arm_rows:
                    stop_event = row["first_alarm_event"]
                    last_active = (
                        int(stop_event)
                        if stop_event is not None
                        else int(row["events_processed"]) - 1
                    )
                    start_event = HORIZON // 2
                    if last_active >= start_event:
                        stream_id = int(row["stream_id"])
                        row["evaluator_cumulative_expected_harm_cost"] = float(
                            effect
                            * oracle_coeff_cpu[start_event : last_active + 1, stream_id].sum()
                        )
            rows.extend(arm_rows)

    metrics = pd.DataFrame(rows)
    expected_rows = streams * len(SCENARIOS) * len(ARMS)
    if len(metrics) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows, got {len(metrics)}")
    if metrics.duplicated(["scenario", "arm", "stream_id"]).any():
        raise RuntimeError("duplicate scenario-arm-stream metrics")
    if not metrics["budget_respected"].all():
        raise RuntimeError("hard label budget violated")

    calibration_cells = len(NULL_SCENARIOS) * len(ARMS)
    per_cell_alpha = 0.05 / calibration_cells
    calibration_rows = []
    for scenario in NULL_SCENARIOS:
        for arm, group in metrics[metrics["scenario"] == scenario].groupby("arm", sort=True):
            false_count = int(group["false_escalation"].sum())
            upper = exact_one_sided_upper(false_count, len(group), per_cell_alpha)
            calibration_rows.append(
                {
                    "scenario": scenario,
                    "arm": arm,
                    "streams": len(group),
                    "false_escalations": false_count,
                    "false_rate": false_count / len(group),
                    "simultaneous_one_sided_95_upper": upper,
                    "passes_5pct_upper_limit": upper <= 0.05,
                    "mean_labels": float(group["labels_queried"].mean()),
                    "mean_events_processed": float(group["events_processed"].mean()),
                }
            )
    calibration = pd.DataFrame(calibration_rows)
    dose = build_dose_results(
        metrics,
        seed=seed,
        harm_scenarios=MARKOV_HARM_SCENARIOS,
        harm_effects=HARM_EFFECTS,
    )

    by_stream = metrics[
        metrics["arm"].isin(["evidence_qmin_0.05_fixed", "evidence_qmin_0.05_predictable"])
        & metrics["scenario"].isin(MARKOV_HARM_SCENARIOS)
    ].pivot(
        index="stream_id",
        columns=["scenario", "arm"],
        values=[
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ],
    )
    differences: dict[str, list[np.ndarray]] = {
        "detection": [],
        "labels": [],
        "evaluator_cost": [],
    }
    for scenario in MARKOV_HARM_SCENARIOS:
        for metric_name, column in (
            ("detection", "post_onset_detection"),
            ("labels", "labels_queried"),
            ("evaluator_cost", "evaluator_cumulative_expected_harm_cost"),
        ):
            dynamic = by_stream[(column, scenario, "evidence_qmin_0.05_predictable")].to_numpy(
                dtype=float
            )
            fixed = by_stream[(column, scenario, "evidence_qmin_0.05_fixed")].to_numpy(dtype=float)
            differences[metric_name].append(dynamic - fixed)
    macro = {
        name: np.mean(np.stack(values, axis=1), axis=1) for name, values in differences.items()
    }
    detection_ci = paired_bootstrap_interval(macro["detection"], seed=seed + 81001)
    labels_ci = paired_bootstrap_interval(macro["labels"], seed=seed + 81002)
    exposure_ci = paired_bootstrap_interval(macro["evaluator_cost"], seed=seed + 81003)
    primary = {
        "estimand": "equal-weight mean post-onset detection difference across four Markov-regime harm doses; predictable minus fixed bound; paired by stream ID",
        "paired_mean_detection_difference": float(macro["detection"].mean()),
        "paired_bootstrap_95_ci": list(detection_ci),
        "retention_practical_margin": 0.02,
        "passes_primary_detection_rule": bool(detection_ci[0] > 0.02),
        "paired_mean_label_difference": float(macro["labels"].mean()),
        "paired_bootstrap_95_ci_labels": list(labels_ci),
        "passes_no_extra_labels_rule": bool(labels_ci[1] <= 0),
        "paired_mean_evaluator_exposure_cost_difference": float(macro["evaluator_cost"].mean()),
        "paired_bootstrap_95_ci_evaluator_exposure_cost": list(exposure_ci),
        "passes_all_calibration_cells": bool(calibration["passes_5pct_upper_limit"].all()),
        "overall_retention_rule_passes": bool(
            detection_ci[0] > 0.02
            and labels_ci[1] <= 0
            and calibration["passes_5pct_upper_limit"].all()
        ),
    }

    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    paths = {
        "metrics": metrics_dir / "stream_metrics.parquet",
        "calibration": metrics_dir / "null_calibration.csv",
        "dose": metrics_dir / "harm_dose_results.csv",
        "primary": reports_dir / "primary_result.json",
        "report": reports_dir / "validation_results.md",
    }
    metrics.to_parquet(paths["metrics"], index=False)
    calibration.to_csv(paths["calibration"], index=False)
    dose.to_csv(paths["dose"], index=False)
    paths["primary"].write_text(json.dumps(primary, indent=2, sort_keys=True), encoding="utf-8")
    report = [
        "# Markov volatility validation of history-predictable query bounds",
        "",
        f"This CUDA synthetic validation used {streams:,} streams per scenario, seed range {seed}–{seed + streams - 1}, a 2,400-event horizon, alpha 0.05, and a 480-label hard cap. The persistent latent volatility state flips with probability 0.05 per event and is stationary with equal state probabilities.",
        "",
        "The null preserves the conditional-mean assumption in each latent state, not only on average: state 0 has low/high context probabilities 0.5/0.5 and conditional cost contrasts -0.12/+0.12; state 1 has probabilities 0.75/0.25 and contrasts -0.10/+0.30. Each state therefore has exactly zero expected paired cost. The high-cost-event frequency and squared-cost variance persist in Markov regimes. Training proxies are estimated from a separate sample of the stationary regime mixture. The latent state and conditional probabilities are evaluator-only and never enter query or monitor inputs.",
        "",
        "The strict-negative control has state-conditional post-onset mean contrasts -0.2667 and -0.1333, both nonpositive; its stationary average is -0.20. Each harm dose shifts the high-cost outcome probability by delta/3.75, giving stationary aggregate expected harm delta. The monitor's history-only query propensities preserve the marginal past-conditional null under the stated martingale construction.",
        "",
        "Calibration family: two nonpositive controls crossed with three arms; exact one-sided Clopper-Pearson upper bounds use Bonferroni alpha 0.05/6. The primary harm contrast is the equal-weight four-dose paired detection difference. The same +2 percentage-point lower-bound threshold, no-extra-label upper-bound threshold, and simultaneous calibration gate as the independent confirmation are applied. Dose-level bootstrap intervals are secondary and unadjusted.",
        "",
        "## Calibration",
        "",
        calibration.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Harm doses",
        "",
        dose.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Primary result",
        "",
        f"- Mean paired detection difference: {primary['paired_mean_detection_difference']:.4f} (95% CI {detection_ci}).",
        f"- Mean paired label difference: {primary['paired_mean_label_difference']:.2f} (95% CI {labels_ci}).",
        f"- Evaluator exposure-cost difference: {primary['paired_mean_evaluator_exposure_cost_difference']:.2f} (95% CI {exposure_ci}). This sums state-conditional expected paired costs along the evaluator-known latent path until the alarm or stopping time.",
        f"- Calibration gate: {primary['passes_all_calibration_cells']}; full retention rule: {primary['overall_retention_rule_passes']}.",
        "",
        "This test is limited to the registered two-state Markov volatility process, immediate randomized feedback, a fixed action pair, and history-predictable q. It does not validate arbitrary serial dependence, delayed or informative labels, changing policies, or interventions. A pass supports the stated martingale-null case only; no novelty or universal robustness claim follows.",
        "",
        "No figure was generated because PaperBanana was unavailable; project instructions require PaperBanana for research visuals.",
        "",
        "Reproduce with:",
        "",
        "```powershell",
        f"uv run python scripts/validate_markov_predictable_query_bounds.py --streams {streams} --seed {seed} --device {device_name} --output {output.as_posix()}",
        "```",
        "",
    ]
    paths["report"].write_text("\n".join(report), encoding="utf-8")

    source_paths = [
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("src/shiftlab/dive/eprocess.py"),
        Path("src/shiftlab/dive/estimators.py"),
        Path("docs/markov_predictable_bound_validation_protocol.md"),
    ]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    manifest = {
        "experiment": "markov_volatility_predictable_query_bound_validation",
        "classification": "independent_dependent_stream_validation",
        "complete": True,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "configuration": {
            "streams_per_scenario": streams,
            "horizon": HORIZON,
            "seed_root": seed,
            "seed_range_inclusive": [seed, seed + streams - 1],
            "device_requested": device_name,
            "device_resolved": str(device),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
            "scenarios": list(SCENARIOS),
            "arms": [f"{policy}:{floor:.2f}:{bound}" for policy, floor, bound in ARMS],
            "markov_flip_probability": MARKOV_FLIP_PROBABILITY,
            "stationary_state_probabilities": [0.5, 0.5],
            "high_context_probabilities_by_state": [0.5, 0.25],
            "conditional_null_mean_by_state": [0.0, 0.0],
            "null_squared_cost_mean_by_state": [13.0, 7.0],
            "training_events": TRAINING_EVENTS,
            "hard_label_budget": int(metrics["hard_label_budget"].max()),
            "calibration_family_cells": calibration_cells,
            "calibration_per_cell_alpha": per_cell_alpha,
            "primary_harm_effects": list(HARM_EFFECTS),
            "primary_detection_margin": 0.02,
            "oracle_boundary": "latent regime and conditional laws used only for outcome generation and evaluator accounting; learner receives sampled training data, observed context, and queried labels",
        },
        "primary_result": primary,
        "source_sha256": {str(path): sha256(path) for path in source_paths},
        "artifact_sha256": {str(path.relative_to(output)): sha256(path) for path in paths.values()},
        "rows": len(metrics),
        "visuals_generated": False,
    }
    (reports_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=DEFAULT_STREAMS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/markov_predictable_bound_validation")
    )
    args = parser.parse_args()
    path = run_markov_validation(
        streams=args.streams, seed=args.seed, device_name=args.device, output=args.output
    )
    print(f"Completed Markov dependence validation on {args.device}: {path}")


if __name__ == "__main__":
    main()
