"""Development benchmark combining delayed labels and history-adaptive querying.

The query heuristic is a predictable Neyman-style allocation based on the
recently observed scale of paired costs. The method is deliberately treated as
a candidate heuristic, not a new algorithm or theorem. Inference uses the
registered event-time conditional-mean null and per-event inverse-propensity
bounds; delayed labels are released only through the contiguous event prefix.
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
from .eprocess import PredictableBoundMeanEProcess

SCENARIOS = ("stationary", "benign_variance_shift", "boundary_harm")


@dataclass(frozen=True)
class Config:
    seeds: int = 60
    seed_offset: int = 20271000
    n_source: int = 1000
    n_target: int = 3000
    base_query_rate: float = 0.25
    q_min: float = 0.10
    q_max: float = 0.40
    alpha: float = 0.05
    epsilon: float = 0.02
    onset_fraction: float = 0.4
    harm_increase: float = 0.12
    base_amplitude: float = 0.6
    benign_amplitude: float = 0.25
    delay_max: int = 12
    variance_window: int = 64
    device: str = "auto"

    def validate(self) -> Config:
        if self.seeds < 2 or self.n_source < 100 or self.n_target < 100:
            raise ValueError("seeds >=2 and source/target lengths >=100 required")
        if not 0 < self.q_min <= self.base_query_rate <= self.q_max <= 1:
            raise ValueError("require 0 < q_min <= base rate <= q_max <= 1")
        if not 0 < self.alpha < 1 or not 0 <= self.epsilon < 1:
            raise ValueError("alpha and epsilon are outside their valid ranges")
        if not 0 < self.onset_fraction < 1 or self.variance_window < 2:
            raise ValueError("invalid onset fraction or variance window")
        if not 0 < self.benign_amplitude <= self.base_amplitude <= 1:
            raise ValueError("invalid paired-cost amplitude")
        if self.harm_increase >= 2 * self.base_amplitude or self.delay_max < 0:
            raise ValueError("invalid harm effect or delay")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be auto, cpu, or cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        return self


def _device(name: str) -> torch.device:
    return torch.device(
        "cuda"
        if name == "auto" and torch.cuda.is_available()
        else ("cpu" if name == "auto" else name)
    )


def _stream(
    config: Config, seed: int, scenario: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    device = _device(config.device)
    gen = torch.Generator(device=device).manual_seed(seed)
    source_sign = torch.where(
        torch.rand(config.n_source, device=device, generator=gen) < 0.5, -1.0, 1.0
    )
    source = config.base_amplitude * source_sign
    onset = int(config.n_target * config.onset_fraction)
    amp = torch.full((config.n_target,), config.base_amplitude, device=device)
    prob = torch.full((config.n_target,), 0.5, device=device)
    if scenario == "benign_variance_shift":
        amp[onset:] = config.benign_amplitude
    elif scenario == "boundary_harm":
        prob[onset:] = 0.5 + config.harm_increase / (2 * config.base_amplitude)
    y = (
        torch.where(torch.rand(config.n_target, device=device, generator=gen) < prob, 1.0, -1.0)
        * amp
    )
    delay = (
        torch.randint(config.delay_max + 1, (config.n_target,), device=device, generator=gen)
        if config.delay_max
        else torch.zeros(config.n_target, device=device, dtype=torch.int64)
    )
    return source.cpu().numpy(), y.cpu().numpy(), delay.cpu().numpy(), onset


def _run_arm(
    config: Config,
    *,
    seed: int,
    scenario: str,
    policy: str,
    outcomes: np.ndarray,
    delays: np.ndarray,
    source_var: float,
    onset: int,
) -> dict[str, object]:
    # Reuse query uniforms across arms for paired policy comparisons.
    uniforms = np.random.default_rng(seed + 8_110_317).random(config.n_target)
    buffer = EventOrderBuffer()
    process = PredictableBoundMeanEProcess(alpha=config.alpha)
    q_path = np.empty(config.n_target, dtype=float)
    query_path = np.zeros(config.n_target, dtype=bool)
    known: list[float] = []
    released: list[tuple[int, ResolvedEvidence]] = []
    alarm_event: int | None = None
    alarm_wall: int | None = None
    labels_at_alarm = 0
    arrivals_by_time: dict[int, list[int]] = {}

    def record_released(wall: int, rows: list[ResolvedEvidence]) -> None:
        for row in rows:
            released.append((wall, row))
            if query_path[row.event_index]:
                known.append(float(outcomes[row.event_index]))

    for t in range(config.n_target + config.delay_max + 1):
        # Process feedback first: only labels that arrived strictly before the
        # current event can affect this event's propensity.
        for event in arrivals_by_time.get(t, []):
            record_released(
                t,
                buffer.resolve(
                    event, available_time=float(t), value=float(outcomes[event] - config.epsilon)
                ),
            )
        if t >= config.n_target:
            continue
        recent = known[-config.variance_window :]
        if policy == "uniform" or len(recent) < 8:
            q = config.base_query_rate
        else:
            observed_var = max(float(np.mean(np.square(recent))), source_var * 0.05)
            q = float(
                np.clip(
                    config.base_query_rate * math.sqrt(observed_var / source_var),
                    config.q_min,
                    config.q_max,
                )
            )
        q_path[t] = q
        queried = uniforms[t] < q
        query_path[t] = queried
        if queried:
            record_released(t, buffer.register(t, float(t), value=None))
            if int(delays[t]) == 0:
                record_released(
                    t,
                    buffer.resolve(
                        t, available_time=float(t), value=float(outcomes[t] - config.epsilon)
                    ),
                )
            else:
                arrivals_by_time.setdefault(t + int(delays[t]), []).append(t)
        else:
            record_released(t, buffer.register(t, float(t), value=0.0))
            # Unqueried events have no new label to drive the query policy.
    for wall, row in released:
        i = row.event_index
        ht = float(outcomes[i] - config.epsilon) / q_path[i] if query_path[i] else 0.0
        # Torch's float32 generator can exceed the nominal amplitude by a few
        # ulps; include that numerical slack in the declared support bound.
        bound = (config.base_amplitude + config.epsilon + 1e-6) / q_path[i]
        process.update(ht, bound=bound)
        if alarm_event is None and process.alarm:
            alarm_event = i
            alarm_wall = wall
            labels_at_alarm = int(query_path[: i + 1].sum())
    label_count = int(query_path.sum())
    return {
        "seed": seed,
        "scenario": scenario,
        "query_policy": policy,
        "labels_queried": label_count,
        "query_rate_realized": label_count / config.n_target,
        "mean_propensity": float(q_path.mean()),
        "min_propensity": float(q_path.min()),
        "max_propensity": float(q_path.max()),
        "alarm": alarm_event is not None,
        "alarm_event": alarm_event,
        "alarm_wall_time": alarm_wall,
        "alarm_latency_after_onset": (alarm_event - onset)
        if alarm_event is not None and alarm_event >= onset
        else np.nan,
        "labels_at_alarm": labels_at_alarm if alarm_event is not None else np.nan,
        "processed_events": len(released),
        "pending_at_end": buffer.pending_count,
        "propensities_in_range": bool(np.all((q_path >= config.q_min) & (q_path <= config.q_max))),
        "material_harm": scenario == "boundary_harm",
        "device": "cuda" if torch.cuda.is_available() and config.device != "cpu" else "cpu",
    }


def simulate(config: Config, *, seed: int, scenario: str) -> list[dict[str, object]]:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario}")
    source, outcomes, delays, onset = _stream(config, seed, scenario)
    source_var = max(float(np.mean(np.square(source))), 1e-8)
    return [
        _run_arm(
            config,
            seed=seed,
            scenario=scenario,
            policy=policy,
            outcomes=outcomes,
            delays=delays,
            source_var=source_var,
            onset=onset,
        )
        for policy in ("uniform", "variance_adaptive")
    ]


def run(config: Config, output: Path) -> Path:
    config.validate()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    rows = [
        row
        for scenario in SCENARIOS
        for j in range(config.seeds)
        for row in simulate(config, seed=config.seed_offset + j, scenario=scenario)
    ]
    frame = pd.DataFrame(rows)
    if frame.duplicated(["scenario", "seed", "query_policy"]).any():
        raise RuntimeError("duplicate stream-policy keys")
    if not frame.propensities_in_range.all() or frame.pending_at_end.ne(0).any():
        raise RuntimeError("propensity or delay-buffer integrity check failed")
    output.joinpath("metrics.parquet").parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output / "metrics.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    report = {
        "title": "Delayed feedback with predictable variance-adaptive querying: development screen",
        "config": asdict(config),
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime": environment(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rows": len(frame),
        "device": str(_device(config.device)),
        "summary": frame.groupby(["scenario", "query_policy"], as_index=False)
        .agg(
            streams=("seed", "count"),
            alarm_rate=("alarm", "mean"),
            labels=("labels_queried", "mean"),
            mean_propensity=("mean_propensity", "mean"),
            alarm_latency=("alarm_latency_after_onset", "mean"),
            pending=("pending_at_end", "max"),
            propensity_violations=("propensities_in_range", lambda x: int((~x).sum())),
        )
        .to_dict(orient="records"),
        "limitations": [
            "Development-only synthetic screen; no independent calibration or confirmation.",
            "The variance-adaptive propensity is a standard heuristic, not a claimed novel method or optimal policy.",
            "Validity requires the stated event-history conditional-mean null, randomized queries, correct propensities, predictable support bounds, and alarms based only on the resolved event prefix.",
            "The reported query cap is a loose q_max pathwise ceiling, not an equal realized-budget comparison; compare labels explicitly.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=20271000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/delayed_adaptive_query_development")
    )
    args = parser.parse_args()
    config = Config(seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)
    print(f"running delayed adaptive-query development on {_device(config.device)}", flush=True)
    print(run(config, args.output_dir))


if __name__ == "__main__":
    main()
