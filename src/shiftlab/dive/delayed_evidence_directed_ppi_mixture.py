"""Grid history-directed querying with PPI monitoring and delayed labels.

This combines established evidence-directed propensities with predictable-bound
PPI e-processes and event-order buffering. It is an algorithm comparison, not a
novelty claim. Every policy has the same realized label cap and matched random
outcomes, query uniforms, and feedback delays.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ..data.gpu.environment import environment
from .delayed_feedback import EventOrderBuffer, ResolvedEvidence
from .eprocess import (
    BoundedMeanEProcess,
    PredictableBoundMeanEProcess,
    PredictableStartedMixtureEProcess,
)
from .query import EvidenceDirectedQueryPolicy

ACTIVATIONS = (0.0, 0.025, 0.05)
URGENCY_POWERS = (0.5, 1.0, 2.0)
SCENARIOS = ("stationary", "benign_variance_shift", "boundary_harm")
ALPHA = 0.05
EPSILON = 0.05
Q_MIN = 0.05
Q_MAX = 0.80
TARGET_RATE = 0.20
AMPLITUDE = 1.0
HARM_SHIFT = 0.20
ONSET_FRACTION = 0.50
MAX_DELAY = 12


def _name(activation: float, power: float) -> str:
    return f"evidence_a{activation:g}_p{power:g}_eventwise".replace(".", "p")


GRID_METHODS = tuple(_name(a, p) for a in ACTIVATIONS for p in URGENCY_POWERS)
METHODS = ("uniform_eventwise", *GRID_METHODS, "evidence_a0p05_p0p5_fixed")


@dataclass(frozen=True)
class Config:
    seeds: int = 30
    seed_offset: int = 20272000
    n_source: int = 1200
    n_target: int = 2400
    budget_rate: float = TARGET_RATE
    alpha: float = ALPHA
    epsilon: float = EPSILON
    q_min: float = Q_MIN
    q_max: float = Q_MAX
    amplitude: float = AMPLITUDE
    harm_shift: float = HARM_SHIFT
    onset_fraction: float = ONSET_FRACTION
    max_delay: int = MAX_DELAY
    benign_amplitude: float = 0.55
    device: str = "auto"

    def validate(self) -> Config:
        if self.seeds < 2 or self.n_source < 100 or self.n_target < 200:
            raise ValueError("seeds >=2, n_source >=100, and n_target >=200 required")
        if not 0 < self.q_min <= self.budget_rate <= self.q_max <= 1:
            raise ValueError("require 0 < q_min <= budget_rate <= q_max <= 1")
        if not 0 < self.alpha < 1 or not 0 <= self.epsilon < 1:
            raise ValueError("alpha and epsilon must be in their valid ranges")
        if not 0 < self.onset_fraction < 1 or self.max_delay < 0:
            raise ValueError("invalid onset fraction or maximum delay")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("invalid amplitude support")
        if self.harm_shift < 0 or self.harm_shift >= 1 - self.amplitude * 0.3:
            raise ValueError("harm shift is too large for the registered outcome model")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        return self


def _device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def _generate(config: Config, *, seed: int, scenario: str):
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario}")
    device = _device(config.device)
    gen = torch.Generator(device=device).manual_seed(seed)
    x_source = torch.where(
        torch.rand(config.n_source, device=device, generator=gen) < 0.5, -1.0, 1.0
    )
    source_probability = (1 + 0.35 * x_source) / 2
    z_source = torch.where(
        torch.rand(config.n_source, device=device, generator=gen) < source_probability,
        1.0,
        -1.0,
    )
    x_target = torch.where(
        torch.rand(config.n_target, device=device, generator=gen) < 0.5, -1.0, 1.0
    )
    onset = int(config.n_target * config.onset_fraction)
    amplitude = torch.full((config.n_target,), config.amplitude, device=device)
    shift = torch.zeros(config.n_target, device=device)
    if scenario == "benign_variance_shift":
        amplitude[onset:] = config.benign_amplitude
    elif scenario == "boundary_harm":
        shift[onset:] = config.harm_shift
    conditional_mean = 0.35 * x_target + shift
    probability_positive = (1 + conditional_mean / amplitude) / 2
    if torch.any((probability_positive < 0) | (probability_positive > 1)):
        raise RuntimeError("registered generator probabilities leave [0,1]")
    z_target = torch.where(
        torch.rand(config.n_target, device=device, generator=gen) < probability_positive,
        amplitude,
        -amplitude,
    )
    delays = (
        torch.randint(
            config.max_delay + 1,
            (config.n_target,),
            device=device,
            generator=gen,
        )
        if config.max_delay
        else torch.zeros(config.n_target, device=device, dtype=torch.int64)
    )
    return (
        x_source.cpu().numpy(),
        z_source.cpu().numpy(),
        x_target.cpu().numpy(),
        z_target.cpu().numpy(),
        delays.cpu().numpy(),
        onset,
        str(device),
    )


def _method_parameters(method: str) -> tuple[str, float, float, float]:
    if method == "uniform_eventwise":
        return "uniform", 0.0, 1.0, 0.0
    if method == "evidence_a0p05_p0p5_fixed":
        return "fixed", 0.05, 0.5, 0.0
    blend_weights = {
        "evidence_blend_25": 0.25,
        "evidence_blend_50": 0.50,
        "evidence_blend_75": 0.75,
    }
    for name, weight in blend_weights.items():
        if method == f"{name}_a0p025_p0p5_eventwise":
            return "eventwise", 0.025, 0.5, weight
    for activation in ACTIVATIONS:
        for power in URGENCY_POWERS:
            if method == _name(activation, power):
                return "eventwise", activation, power, 0.0
    raise ValueError(f"unregistered method: {method}")


def _fit_source_proxy(x: np.ndarray, z: np.ndarray) -> tuple[float, float]:
    design = np.column_stack((np.ones(len(x)), x))
    intercept, slope = np.linalg.lstsq(design, z, rcond=None)[0]
    return float(intercept), float(slope)


def _simulate_method(
    config: Config,
    *,
    seed: int,
    scenario: str,
    method: str,
    x_source: np.ndarray,
    z_source: np.ndarray,
    x_target: np.ndarray,
    z_target: np.ndarray,
    delays: np.ndarray,
    onset: int,
    monitor_variant: str = "full_stream",
    monitor_starts: tuple[int, ...] = (),
    query_driver_variant: str = "monitor",
    continue_after_alarm: bool = False,
) -> dict[str, object]:
    kind, activation, power, uniform_mixture = _method_parameters(method)
    if monitor_variant not in {"full_stream", "fixed_start_mixture"}:
        raise ValueError(f"unregistered monitor variant: {monitor_variant}")
    if query_driver_variant not in {"monitor", "full_stream"}:
        raise ValueError(f"unregistered query driver: {query_driver_variant}")
    if query_driver_variant == "full_stream" and kind == "fixed":
        raise ValueError("full-stream query driving requires a predictable-bound query process")
    if monitor_variant == "fixed_start_mixture" and (kind == "fixed" or not monitor_starts):
        raise ValueError(
            "fixed-start mixture requires a predictable-bound monitor and fixed starts"
        )
    intercept, slope = _fit_source_proxy(x_source, z_source)
    # Frozen source-trained proxy: learner-visible contexts only, clipped to
    # the known paired-cost support. No target outcomes enter proxy formation.
    proxy = np.clip(intercept + slope * x_target, -config.amplitude, config.amplitude)
    budget = math.floor(config.n_target * config.budget_rate)
    remaining = budget
    if kind == "uniform":
        policy = None
        process: (
            BoundedMeanEProcess | PredictableBoundMeanEProcess | PredictableStartedMixtureEProcess
        )
        if monitor_variant == "fixed_start_mixture":
            process = PredictableStartedMixtureEProcess(alpha=config.alpha, starts=monitor_starts)
        else:
            process = PredictableBoundMeanEProcess(alpha=config.alpha)
    else:
        policy = EvidenceDirectedQueryPolicy(
            q_min=config.q_min,
            q_max=config.q_max,
            alpha=config.alpha,
            activation_fraction=activation,
            urgency_power=power,
            budget_taper_power=1.0,
        )
        if kind == "fixed":
            fixed_bound = (config.amplitude + config.epsilon) * (2 / config.q_min - 1)
            process = BoundedMeanEProcess(bound=fixed_bound, alpha=config.alpha)
        else:
            if monitor_variant == "fixed_start_mixture":
                process = PredictableStartedMixtureEProcess(
                    alpha=config.alpha, starts=monitor_starts
                )
            else:
                process = PredictableBoundMeanEProcess(alpha=config.alpha)

    query_process: (
        BoundedMeanEProcess | PredictableBoundMeanEProcess | PredictableStartedMixtureEProcess
    ) = process
    if query_driver_variant == "full_stream" and monitor_variant == "fixed_start_mixture":
        query_process = PredictableBoundMeanEProcess(alpha=config.alpha)

    shared_query_uniforms = np.random.default_rng(seed + 6_512_819).random(config.n_target)
    buffer = EventOrderBuffer()
    arrivals: dict[int, list[int]] = {}
    q_values: list[float] = []
    queried_events: list[int] = []
    event_bounds: dict[int, float] = {}
    processed_events = 0
    first_alarm_event: int | None = None
    first_alarm_wall: int | None = None
    event_count = 0
    query_cost = 0
    final_e_value = 1.0

    def update_rows(wall_time: int, rows: list[ResolvedEvidence]) -> None:
        nonlocal first_alarm_event, first_alarm_wall, processed_events, final_e_value
        for row in rows:
            if kind == "fixed":
                assert isinstance(process, BoundedMeanEProcess)
                final_e_value = process.update(row.value)
            else:
                assert isinstance(
                    process,
                    (PredictableBoundMeanEProcess, PredictableStartedMixtureEProcess),
                )
                final_e_value = process.update(row.value, bound=event_bounds[row.event_index])
                if query_process is not process:
                    assert isinstance(query_process, PredictableBoundMeanEProcess)
                    query_process.update(row.value, bound=event_bounds[row.event_index])
            processed_events += 1
            if first_alarm_event is None and process.alarm:
                first_alarm_event = row.event_index
                first_alarm_wall = wall_time

    for wall in range(config.n_target + config.max_delay + 1):
        # Process arrivals before deciding whether to reveal the next context.
        for event in arrivals.pop(wall, []):
            h = float(proxy[event]) - config.epsilon
            q = q_values[event]
            centered_increment = h + (float(z_target[event]) - float(proxy[event])) / q
            update_rows(
                wall,
                buffer.resolve(event, available_time=float(wall), value=centered_increment),
            )

        if (
            wall >= config.n_target
            or (first_alarm_event is not None and not continue_after_alarm)
            or remaining == 0
        ):
            continue
        remaining_fraction = remaining / budget if budget else 0.0
        if policy is None:
            propensity = config.budget_rate
        else:
            propensity = policy.propensity(
                log_e_value=query_process.log_e_value,
                remaining_fraction=remaining_fraction,
            )
            # A predictable convex combination of the evidence-directed
            # propensity and the fixed uniform rate. The realized q is used
            # below in both the IPW increment and its support bound.
            propensity = (1.0 - uniform_mixture) * propensity + uniform_mixture * config.budget_rate
        if not config.q_min - 1e-12 <= propensity <= config.q_max + 1e-12:
            raise RuntimeError("query propensity is outside the registered support")
        event = wall
        q_values.append(float(propensity))
        centered_proxy = float(proxy[event]) - config.epsilon
        bound = (config.amplitude + config.epsilon + 1e-6) * (2 / propensity - 1)
        event_bounds[event] = bound
        queried = shared_query_uniforms[event] < propensity
        event_count += 1
        if queried:
            if remaining < 1:
                raise RuntimeError("pathwise label budget would be exceeded")
            remaining -= 1
            query_cost += 1
            queried_events.append(event)
            update_rows(
                wall,
                buffer.register(event, float(event), value=None),
            )
            delay = int(delays[event])
            if delay == 0:
                increment = (
                    centered_proxy + (float(z_target[event]) - float(proxy[event])) / propensity
                )
                update_rows(
                    wall,
                    buffer.resolve(event, available_time=float(wall), value=increment),
                )
            else:
                arrivals.setdefault(wall + delay, []).append(event)
        else:
            update_rows(
                wall,
                buffer.register(event, float(event), value=centered_proxy),
            )

    if buffer.pending_count or buffer.buffered_count:
        raise RuntimeError("pending labels did not resolve into a complete event prefix")
    if processed_events != event_count:
        raise RuntimeError("the e-process did not consume every registered event exactly once")
    if query_cost > budget:
        raise RuntimeError("pathwise label cap was exceeded")
    return {
        "seed": seed,
        "scenario": scenario,
        "method": method,
        "harmful_stream": scenario == "boundary_harm",
        "onset_event": onset if scenario == "boundary_harm" else None,
        "alarm": first_alarm_event is not None,
        "alarm_event": first_alarm_event,
        "alarm_wall_time": first_alarm_wall,
        "alarm_after_onset": bool(
            first_alarm_event is not None
            and scenario == "boundary_harm"
            and first_alarm_event >= onset
        ),
        "event_delay_after_onset": (
            first_alarm_event - onset
            if first_alarm_event is not None
            and scenario == "boundary_harm"
            and first_alarm_event >= onset
            else np.nan
        ),
        "wall_delay_after_onset": (
            first_alarm_wall - onset
            if first_alarm_wall is not None
            and scenario == "boundary_harm"
            and first_alarm_event is not None
            and first_alarm_event >= onset
            else np.nan
        ),
        "labels_queried": query_cost,
        "query_schedule_sha256": hashlib.sha256(
            np.asarray(q_values, dtype="<f8").tobytes()
            + np.asarray(queried_events, dtype="<i8").tobytes()
        ).hexdigest(),
        "hard_label_cap": budget,
        "budget_respected": query_cost <= budget,
        "budget_exhausted": remaining == 0,
        "events_registered": event_count,
        "events_updated": processed_events,
        "mean_propensity": float(np.mean(q_values)) if q_values else np.nan,
        "min_propensity": min(q_values) if q_values else np.nan,
        "max_propensity": max(q_values) if q_values else np.nan,
        "final_e_value": final_e_value,
        "proxy_source_intercept": intercept,
        "proxy_source_slope": slope,
        "pending_labels": buffer.pending_count,
        "device": "cuda" if torch.cuda.is_available() and config.device != "cpu" else "cpu",
    }


def simulate_seed(config: Config, *, seed: int, scenario: str) -> list[dict[str, object]]:
    generated = _generate(config, seed=seed, scenario=scenario)
    x_source, z_source, x_target, z_target, delays, onset, _ = generated
    return [
        _simulate_method(
            config,
            seed=seed,
            scenario=scenario,
            method=method,
            x_source=x_source,
            z_source=z_source,
            x_target=x_target,
            z_target=z_target,
            delays=delays,
            onset=onset,
        )
        for method in METHODS
    ]


def _paired_contrasts(frame: pd.DataFrame, *, seed: int, replicates: int = 5000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        reference = frame.loc[
            frame.scenario.eq(scenario) & frame.method.eq("uniform_eventwise")
        ].sort_values("seed")
        for method in METHODS:
            if method == "uniform_eventwise":
                continue
            candidate = frame.loc[
                frame.scenario.eq(scenario) & frame.method.eq(method)
            ].sort_values("seed")
            paired = reference.merge(
                candidate,
                on=["scenario", "seed"],
                suffixes=("_uniform", "_candidate"),
                validate="one_to_one",
            )
            if len(paired) != len(reference) or len(paired) != len(candidate):
                raise RuntimeError("development arms do not share identical seed sets")
            n = len(paired)
            index = rng.integers(0, n, size=(replicates, n))
            endpoints = {
                "alarm": (
                    paired.alarm_candidate.astype(float).to_numpy()
                    - paired.alarm_uniform.astype(float).to_numpy()
                ),
                "post_onset_detection": (
                    paired.alarm_after_onset_candidate.astype(float).to_numpy()
                    - paired.alarm_after_onset_uniform.astype(float).to_numpy()
                ),
                "labels": (
                    paired.labels_queried_candidate.to_numpy(dtype=float)
                    - paired.labels_queried_uniform.to_numpy(dtype=float)
                ),
                "events": (
                    paired.events_updated_candidate.to_numpy(dtype=float)
                    - paired.events_updated_uniform.to_numpy(dtype=float)
                ),
            }
            summary: dict[str, object] = {
                "scenario": scenario,
                "method": method,
                "reference": "uniform_eventwise",
                "paired_streams": n,
            }
            for endpoint, delta in endpoints.items():
                draws = delta[index].mean(axis=1)
                summary[f"{endpoint}_difference"] = float(delta.mean())
                summary[f"{endpoint}_ci_low"] = float(np.quantile(draws, 0.025))
                summary[f"{endpoint}_ci_high"] = float(np.quantile(draws, 0.975))
            rows.append(summary)
    return pd.DataFrame(rows)


def run(config: Config, output: Path) -> Path:
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    rows = [
        row
        for scenario in SCENARIOS
        for i in range(config.seeds)
        for row in simulate_seed(config, seed=config.seed_offset + i, scenario=scenario)
    ]
    frame = pd.DataFrame(rows).sort_values(["scenario", "seed", "method"], kind="stable")
    if frame.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("duplicate scenario/seed/method keys")
    if not frame.budget_respected.astype(bool).all():
        raise RuntimeError("hard label cap failed")
    if frame.pending_labels.ne(0).any() or frame.events_registered.ne(frame.events_updated).any():
        raise RuntimeError("event-prefix integrity check failed")
    if frame.labels_queried.gt(frame.hard_label_cap).any():
        raise RuntimeError("label cap failure in saved metrics")
    output.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output / "metrics.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    summary = frame.groupby(["scenario", "method"], as_index=False).agg(
        streams=("seed", "count"),
        alarm_rate=("alarm", "mean"),
        post_onset_detection=("alarm_after_onset", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_events=("events_updated", "mean"),
        mean_event_delay=("event_delay_after_onset", "mean"),
        mean_wall_delay=("wall_delay_after_onset", "mean"),
        cap_violations=("budget_respected", lambda x: int((~x).sum())),
    )
    summary.to_csv(output / "summary.csv", index=False)
    contrasts = _paired_contrasts(frame, seed=config.seed_offset + 2_917_411)
    contrasts.to_csv(output / "paired_contrasts_vs_uniform.csv", index=False)
    manifest = {
        "experiment": "delayed_feedback_evidence_directed_ppi_grid_development",
        "config": asdict(config),
        "methods": list(METHODS),
        "scenarios": list(SCENARIOS),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "rows": len(frame),
        "summary": summary.to_dict(orient="records"),
        "paired_contrasts": contrasts.to_dict(orient="records"),
        "assumptions": [
            "The PPI proxy is fitted once on pre-monitor source labels and is outcome-free on each target event.",
            "Query propensities depend only on the committed event-prefix e-value and remaining integer label budget.",
            "The e-process null is E[Z_t | G_(t-1)] <= epsilon, with randomized queries conditionally independent of current Z and a frozen policy pair.",
            "Each eventwise PPI bound is (M+epsilon)*(2/q_t-1), predictable because q_t uses only prior committed history and spend.",
            "Alarm checks use only the contiguous resolved event prefix; delays are independent uniform integers from 0 through max_delay in this simulator.",
        ],
        "limitations": [
            "Development grid only: no null-calibration gate or independent-seed confirmation.",
            "The evidence-directed propensity curve and predictable bounded-mean e-process are established constructions; no novelty or optimality claim is made.",
            "Results do not cover informative non-arrival, serially dependent outcomes, changing policies, or real-world costs.",
            "The hard cap counts requested labels; delaying feedback affects when evidence can be used, not query cost.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20272000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/delayed_evidence_directed_ppi_grid_30")
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running delayed evidence-directed PPI grid on {_device(config.device)}", flush=True)
    print(run(config, args.output_dir))


if __name__ == "__main__":
    main()
