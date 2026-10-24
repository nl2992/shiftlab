"""Independent null calibration for delayed paired-cost e-processes."""

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
from scipy.special import logsumexp
from scipy.stats import beta

from ..data.gpu.environment import environment
from ..monitoring import HoeffdingExcessEProcess

NULL_SCENARIOS = ("stationary", "benign_variance_shift")
CALIBRATION_METHODS = (
    "paired_cost_eprocess",
    "paired_cost_betting",
    "restart_mixture_8",
)


@dataclass(frozen=True)
class DelayedCalibrationConfig:
    """Independent calibration seeds; query rates are analyzed as separate cells."""

    streams_per_cell: int = 2000
    seed_offset: int = 20264000
    n_events: int = 3000
    query_rates: tuple[float, ...] = (0.10, 0.25, 0.50)
    alpha: float = 0.05
    margin: float = 0.02
    amplitude: float = 0.60
    benign_amplitude: float = 0.25
    onset_fraction: float = 0.40
    delay_scheme: str = "uniform_0_6"
    device: str = "cuda"

    def validate(self) -> DelayedCalibrationConfig:
        if self.streams_per_cell < 1 or self.n_events < 100:
            raise ValueError("streams_per_cell must be positive and n_events at least 100")
        if not self.query_rates or any(not 0 < q <= 1 for q in self.query_rates):
            raise ValueError("query_rates must be nonempty and lie in (0, 1]")
        if len(set(self.query_rates)) != len(self.query_rates):
            raise ValueError("query_rates must be unique")
        if not 0 < self.alpha < 1 or not 0 <= self.margin < 1:
            raise ValueError("alpha and margin are invalid")
        if not 0 < self.benign_amplitude <= self.amplitude <= 1:
            raise ValueError("amplitudes must satisfy 0 < benign <= amplitude <= 1")
        if not 0 < self.onset_fraction < 1:
            raise ValueError("onset_fraction must lie in (0, 1)")
        if self.delay_scheme not in {"fixed_3", "uniform_0_6"}:
            raise ValueError("delay_scheme must be fixed_3 or uniform_0_6")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA was requested but is not available")
        return self


def _resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def _generate_null_stream(
    config: DelayedCalibrationConfig, *, seed: int, scenario: str, device: torch.device
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    generator = torch.Generator(device=device).manual_seed(seed)
    amplitude = torch.full((config.n_events,), config.amplitude, device=device)
    onset = int(config.n_events * config.onset_fraction)
    if scenario == "benign_variance_shift":
        amplitude[onset:] = config.benign_amplitude
    sign_uniform = torch.rand(config.n_events, device=device, generator=generator)
    contrast = amplitude * torch.where(sign_uniform < 0.5, -1.0, 1.0)
    query_uniform = torch.rand(config.n_events, device=device, generator=generator)
    if config.delay_scheme == "fixed_3":
        delays = torch.full((config.n_events,), 3, dtype=torch.int64, device=device)
    else:
        delays = torch.randint(0, 7, (config.n_events,), generator=generator, device=device)
    return contrast.cpu().numpy(), query_uniform.cpu().numpy(), delays.cpu().numpy()


def _first_crossing(log_values: np.ndarray, threshold: float) -> int | None:
    crossed = np.flatnonzero(log_values >= threshold)
    return int(crossed[0]) if len(crossed) else None


def _restart_log_e_values(
    centered_values: np.ndarray, *, bound: float, starts: tuple[int, ...]
) -> np.ndarray:
    """Vectorized values of the finite equal-weight start/stake mixture."""
    stakes = np.asarray((0.05, 0.10, 0.20, 0.40, 0.80), dtype=float)
    log_factors = np.log1p(centered_values[:, None] * stakes[None, :] / bound)
    cumulative = np.vstack((np.zeros((1, len(stakes))), np.cumsum(log_factors, axis=0)))
    component_logs = np.zeros((len(centered_values), len(starts), len(stakes)), dtype=float)
    for component, start in enumerate(starts):
        if start < len(centered_values):
            component_logs[start:, component, :] = cumulative[start + 1 :, :] - cumulative[start, :]
    return logsumexp(component_logs.reshape(len(centered_values), -1), axis=1) - math.log(
        len(starts) * len(stakes)
    )


def calibration_alarm_indices(
    contrasts: np.ndarray,
    event_times: np.ndarray,
    arrival_times: np.ndarray,
    *,
    query_rate: float,
    n_events: int,
    margin: float,
    alpha: float,
    amplitude: float,
) -> dict[str, tuple[int | None, int | None]]:
    """Compute event- and wall-time alarms using the three registered e-processes.

    Inputs are already ordered by prediction event. The wall-time for an alarm is
    the first arrival time by which its complete event-order prefix is available.
    Vectorized calculations are checked against the online classes in unit tests.
    """
    values = np.asarray(contrasts, dtype=float)
    events = np.asarray(event_times, dtype=int)
    arrivals = np.asarray(arrival_times, dtype=int)
    if values.ndim != 1 or events.shape != values.shape or arrivals.shape != values.shape:
        raise ValueError("contrasts and event/arrival times must be matching vectors")
    if not len(values):
        return dict.fromkeys(CALIBRATION_METHODS, (None, None))
    if not np.isfinite(values).all() or np.any(arrivals < events):
        raise ValueError("contrasts must be finite and arrivals cannot precede events")
    threshold = math.log(1 / alpha)
    centered = values - margin
    wall_prefix = np.maximum.accumulate(arrivals)

    hoeffding = HoeffdingExcessEProcess(epsilon=margin, alpha=alpha, lower=-1.0, upper=1.0)
    lambdas = np.asarray(hoeffding.lambdas)
    hoeffding_increments = centered[:, None] * lambdas[None, :] - (
        lambdas[None, :] ** 2 * 4.0 / 8.0
    )
    hoeffding_log_e = logsumexp(np.cumsum(hoeffding_increments, axis=0), axis=1) - math.log(
        len(lambdas)
    )

    bound = amplitude + margin + 1e-6
    stakes = np.asarray((0.05, 0.10, 0.20, 0.40, 0.80), dtype=float)
    betting_increments = np.log1p(centered[:, None] * stakes[None, :] / bound)
    betting_log_e = logsumexp(np.cumsum(betting_increments, axis=0), axis=1) - math.log(len(stakes))

    expected_query_horizon = max(1, round(query_rate * n_events))
    starts = tuple(
        sorted({round(expected_query_horizon * component / 8) for component in range(8)})
    )
    restart_log_e = _restart_log_e_values(centered, bound=bound, starts=starts)
    logs = {
        "paired_cost_eprocess": hoeffding_log_e,
        "paired_cost_betting": betting_log_e,
        "restart_mixture_8": restart_log_e,
    }
    results = {}
    for method, log_e in logs.items():
        index = _first_crossing(log_e, threshold)
        results[method] = (
            (int(events[index]), int(wall_prefix[index])) if index is not None else (None, None)
        )
    return results


def _exact_interval(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    lower = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, trials - successes + 1))
    upper = (
        1.0
        if successes == trials
        else float(beta.ppf(1 - alpha / 2, successes + 1, trials - successes))
    )
    return lower, upper


def run_calibration(
    config: DelayedCalibrationConfig, output_dir: str | Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run independent null streams and write exact finite-sample intervals."""
    config.validate()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    device = _resolve_device(config.device)
    rows: list[dict[str, object]] = []
    for scenario in NULL_SCENARIOS:
        for seed in range(config.seed_offset, config.seed_offset + config.streams_per_cell):
            contrasts, query_uniforms, delays = _generate_null_stream(
                config, seed=seed, scenario=scenario, device=device
            )
            for query_rate in config.query_rates:
                event_indices = np.flatnonzero(query_uniforms < query_rate)
                values = contrasts[event_indices]
                event_times = event_indices.astype(int)
                arrival_times = event_times + delays[event_indices]
                alarms = calibration_alarm_indices(
                    values,
                    event_times,
                    arrival_times,
                    query_rate=query_rate,
                    n_events=config.n_events,
                    margin=config.margin,
                    alpha=config.alpha,
                    amplitude=config.amplitude,
                )
                for method, (alarm_event, alarm_wall) in alarms.items():
                    rows.append(
                        {
                            "scenario": scenario,
                            "query_rate": query_rate,
                            "seed": seed,
                            "method": method,
                            "n_events": config.n_events,
                            "labels_queried": len(event_indices),
                            "alarm_event": alarm_event,
                            "alarm_wall_time": alarm_wall,
                            "false_escalation": alarm_event is not None,
                            "labels_processed_at_alarm": (
                                int(np.searchsorted(event_indices, alarm_event, side="right"))
                                if alarm_event is not None
                                else len(event_indices)
                            ),
                        }
                    )
    frame = pd.DataFrame(rows)
    summaries = []
    for (scenario, query_rate, method), group in frame.groupby(
        ["scenario", "query_rate", "method"], sort=True
    ):
        successes, trials = int(group.false_escalation.sum()), len(group)
        lower, upper = _exact_interval(successes, trials)
        summaries.append(
            {
                "scenario": scenario,
                "query_rate": query_rate,
                "method": method,
                "false_escalations": successes,
                "streams": trials,
                "false_escalation_rate": successes / trials,
                "cp95_lower": lower,
                "cp95_upper": upper,
                "max_observed_wall_alarm": group.alarm_wall_time.max(),
            }
        )
    summary = pd.DataFrame(summaries)
    metrics_path = output / "delayed_null_calibration.parquet"
    frame.to_parquet(metrics_path, index=False)
    frame.to_csv(output / "delayed_null_calibration.csv", index=False)
    summary.to_csv(output / "calibration_summary.csv", index=False)
    source_dir = Path(__file__).parent
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config": asdict(config),
        "config_validated": True,
        "resolved_device": str(device),
        "environment": environment(),
        "null_scenarios": list(NULL_SCENARIOS),
        "methods": list(CALIBRATION_METHODS),
        "streams_per_scenario_query_rate": config.streams_per_cell,
        "independent_seed_interval": [
            config.seed_offset,
            config.seed_offset + config.streams_per_cell - 1,
        ],
        "metric_rows": len(frame),
        "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "code_sha256": {
            "delayed_calibration.py": hashlib.sha256(
                (source_dir / "delayed_calibration.py").read_bytes()
            ).hexdigest(),
            "eprocess.py": hashlib.sha256((source_dir / "eprocess.py").read_bytes()).hexdigest(),
            "monitoring.py": hashlib.sha256(
                (source_dir.parent / "monitoring.py").read_bytes()
            ).hexdigest(),
        },
        "inference": (
            "Exact Clopper-Pearson intervals are per method, null scenario and query-rate cell. "
            "No outcomes are pooled across query rates or null scenarios. Calibration evaluates "
            "the complete event-order monitor under outcome-independent query and delay sampling; "
            "it does not prove assumptions beyond this simulator."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Delayed decision-harm null calibration",
        "",
        "Independent null calibration with disjoint seeds from both development runs. Every method",
        "receives the same outcomes and query random numbers within a scenario/seed/query-rate cell.",
        "The 95% intervals are exact two-sided Clopper–Pearson intervals; cells are reported",
        "separately and are not pooled.",
        "",
        f"- Seeds: `{config.seed_offset}`–`{config.seed_offset + config.streams_per_cell - 1}` per scenario.",
        f"- Query rates: `{', '.join(map(str, config.query_rates))}`; horizon: `{config.n_events}`.",
        f"- Delay: `{config.delay_scheme}`; resolved generator device: `{device}`.",
        f"- Independent stream cells: `{len(NULL_SCENARIOS) * len(config.query_rates) * config.streams_per_cell}`.",
        "",
        summary.to_markdown(index=False, floatfmt=".5f"),
        "",
        "These finite-sample rates are calibration evidence for the registered synthetic nulls, not",
        "a substitute for the e-process proof. The betting and restart mixture must satisfy the",
        "bounded eventwise conditional-mean null; queries and delays are generated independently of",
        "the current outcome. The result does not cover informative delay, serial dependence,",
        "selective query rules that violate the stated filtration, or policy-induced outcomes.",
        "",
        "No figure is included because project guidance requires PaperBanana for visuals, and no",
        "PaperBanana tool is available in this session.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return frame, summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/delayed_null_calibration_2000")
    parser.add_argument("--streams-per-cell", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=20264000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    config = DelayedCalibrationConfig(
        streams_per_cell=args.streams_per_cell,
        seed_offset=args.seed_offset,
        device=args.device,
    )
    _frame, summary, manifest = run_calibration(config, args.output_dir)
    print(summary.to_string(index=False))
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
