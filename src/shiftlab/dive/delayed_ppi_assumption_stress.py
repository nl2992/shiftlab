"""Stress-test delayed PPI e-process assumptions under persistent signs and informative delays.

This is a diagnostic of the existing bounded-mean e-process, not a new algorithm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta

from ..data.gpu.environment import environment

SEED_OFFSET = 20_400_000
SEEDS = 2_000
HORIZON = 2_400
BUDGET = 480
Q = 0.20
ALPHA = 0.05
RHOS = (0.0, 0.50, 0.90, 0.98)
DELAYS = ("fixed12", "positive_fast", "positive_slow")
MONITORS = ("full_stream", "fixed_start_mixture")
STARTS = tuple(range(0, HORIZON, 300))
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
PROTOCOL = Path("docs/delayed_ppi_persistent_sign_stress_protocol.md")


def _upper(k: int, n: int, confidence: float = 0.95) -> float:
    return 1.0 if k == n else float(beta.ppf(confidence, k + 1, n - k))


def _generate(batch: int, *, rho: float, seed: int, device: torch.device):
    generator = torch.Generator(device=device).manual_seed(seed)
    flips = torch.where(
        torch.rand((batch, HORIZON - 1), generator=generator, device=device) < (1.0 - rho) / 2.0,
        -1.0,
        1.0,
    )
    initial = torch.where(
        torch.rand((batch, 1), generator=generator, device=device) < 0.5, -1.0, 1.0
    )
    signs = torch.cat((initial, initial * torch.cumprod(flips, dim=1)), dim=1)
    query_uniforms = torch.rand((batch, HORIZON), generator=generator, device=device)
    queries = query_uniforms < Q
    # Stop at the frozen hard cap, preserving a predictable Bernoulli query until exhausted.
    queries &= queries.to(torch.int32).cumsum(dim=1) <= BUDGET
    return signs, queries


def _log_paths(signs: torch.Tensor, queries: torch.Tensor, *, delay_profile: str):
    batch = signs.shape[0]
    increments = torch.where(queries, signs / Q, torch.zeros_like(signs))
    # B=9 while querying is active; the unit bound after exhaustion is conservative
    # because every subsequent increment is exactly zero.
    queried_before = queries.to(torch.int32).cumsum(dim=1) - queries.to(torch.int32)
    active = queried_before < BUDGET
    bounds = torch.where(active, 2.0 / Q - 1.0, 1.0)
    normalized = increments / bounds
    factors = 1.0 + normalized.unsqueeze(-1) * torch.tensor(
        STAKES, dtype=signs.dtype, device=signs.device
    )
    log_factors = torch.log(factors)

    component_paths = []
    for start in STARTS:
        path = torch.zeros((batch, HORIZON, len(STAKES)), dtype=signs.dtype, device=signs.device)
        if start < HORIZON:
            path[:, start:, :] = torch.cumsum(log_factors[:, start:, :], dim=1)
        component_paths.append(path)
    mixture_path = torch.logsumexp(
        torch.stack(component_paths, dim=0) - np.log(len(STARTS) * len(STAKES)), dim=(0, 3)
    )
    full_path = torch.logsumexp(torch.cumsum(log_factors, dim=1) - np.log(len(STAKES)), dim=2)

    delays_positive, delays_negative = {
        "fixed12": (12, 12),
        "positive_fast": (0, 12),
        "positive_slow": (12, 0),
    }[delay_profile]
    delays = torch.where(signs > 0, delays_positive, delays_negative)
    availability = torch.where(
        queries,
        torch.arange(HORIZON, device=signs.device) + delays,
        torch.arange(HORIZON, device=signs.device),
    )
    prefix_wall = torch.cummax(availability, dim=1).values
    alarm_log_threshold = -np.log(ALPHA)

    rows = []
    for name, path in (("full_stream", full_path), ("fixed_start_mixture", mixture_path)):
        crossed = path >= alarm_log_threshold
        alarm = crossed.any(dim=1)
        first_event = crossed.to(torch.int32).argmax(dim=1)
        first_event = torch.where(alarm, first_event, -1)
        first_wall = torch.gather(prefix_wall, 1, first_event.clamp_min(0).unsqueeze(1)).squeeze(1)
        first_wall = torch.where(alarm, first_wall, -1)
        rows.append((name, alarm, first_event, first_wall))
    return rows


def run(*, device_name: str, output: Path, protocol: Path = PROTOCOL, batch_size: int = 64) -> Path:
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    device = torch.device(
        "cuda"
        if device_name == "cuda" or (device_name == "auto" and torch.cuda.is_available())
        else "cpu"
    )
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = protocol.read_bytes()
    rows: list[dict[str, object]] = []
    for rho in RHOS:
        for batch_start in range(0, SEEDS, batch_size):
            count = min(batch_size, SEEDS - batch_start)
            # Reuse the same underlying uniforms across rho values for paired sensitivity.
            seed = SEED_OFFSET + batch_start
            signs, queries = _generate(count, rho=rho, seed=seed, device=device)
            empirical_corr = (signs[:, 1:] * signs[:, :-1]).mean(dim=1).cpu().numpy()
            query_count = queries.sum(dim=1).cpu().numpy()
            for delay_profile in DELAYS:
                monitored = _log_paths(signs, queries, delay_profile=delay_profile)
                for local_i in range(count):
                    stream_seed = SEED_OFFSET + batch_start + local_i
                    for monitor, alarm, event, wall in monitored:
                        rows.append(
                            {
                                "seed": stream_seed,
                                "rho": rho,
                                "delay_profile": delay_profile,
                                "monitor": monitor,
                                "alarm": bool(alarm[local_i].item()),
                                "alarm_event": int(event[local_i].item()),
                                "alarm_wall_time": int(wall[local_i].item()),
                                "labels_queried": int(query_count[local_i]),
                                "query_schedule_sha256": hashlib.sha256(
                                    np.flatnonzero(queries[local_i].cpu().numpy())
                                    .astype("<i8")
                                    .tobytes()
                                ).hexdigest(),
                                "lag1_sign_correlation": float(empirical_corr[local_i]),
                                "conditional_mean_abs_given_previous": rho,
                            }
                        )
        print(f"completed persistent-sign cells through rho={rho:g}", flush=True)

    frame = pd.DataFrame(rows).sort_values(
        ["rho", "delay_profile", "monitor", "seed"], kind="stable"
    )
    expected = SEEDS * len(RHOS) * len(DELAYS) * len(MONITORS)
    keys = ["seed", "rho", "delay_profile", "monitor"]
    if len(frame) != expected or frame.duplicated(keys).any():
        raise RuntimeError("row/key integrity check failed")
    if frame.labels_queried.gt(BUDGET).any() or frame.labels_queried.lt(0).any():
        raise RuntimeError("hard query cap failed")
    summary = (
        frame.groupby(["rho", "delay_profile", "monitor"], as_index=False)
        .agg(
            streams=("seed", "count"),
            alarms=("alarm", "sum"),
            alarm_rate=("alarm", "mean"),
            mean_alarm_event=("alarm_event", lambda x: x[x >= 0].mean()),
            mean_alarm_wall=("alarm_wall_time", lambda x: x[x >= 0].mean()),
            mean_labels=("labels_queried", "mean"),
            mean_lag1_sign_correlation=("lag1_sign_correlation", "mean"),
            theoretical_conditional_mean_abs=("conditional_mean_abs_given_previous", "first"),
        )
        .sort_values(["rho", "delay_profile", "monitor"], kind="stable")
    )
    summary["alarm_rate_simultaneous_95_one_sided_upper_within_rho"] = [
        _upper(int(k), int(n), 0.975) for k, n in zip(summary.alarms, summary.streams, strict=True)
    ]
    summary.to_csv(output / "cell_summary.csv", index=False)
    summary.to_parquet(output / "cell_summary.parquet", index=False)
    frame.to_parquet(output / "metrics.parquet", index=False)
    frame.to_csv(output / "metrics.csv", index=False)
    # Delay changes only availability: event-time alarms and query paths must match exactly.
    event_pivot = frame.pivot(
        index=["seed", "rho", "monitor"], columns="delay_profile", values="alarm_event"
    )
    labels_pivot = frame.pivot(
        index=["seed", "rho", "monitor"], columns="delay_profile", values="labels_queried"
    )
    schedule_pivot = frame.pivot(
        index=["seed", "rho", "monitor"],
        columns="delay_profile",
        values="query_schedule_sha256",
    )
    monitor_schedule_pivot = frame.pivot(
        index=["seed", "rho", "delay_profile"],
        columns="monitor",
        values="query_schedule_sha256",
    )
    if not all((event_pivot["fixed12"] == event_pivot[p]).all() for p in DELAYS[1:]):
        raise RuntimeError("fully drained event-time alarm changed with delay profile")
    if not all((labels_pivot["fixed12"] == labels_pivot[p]).all() for p in DELAYS[1:]):
        raise RuntimeError("query path changed with delay profile")
    if not all((schedule_pivot["fixed12"] == schedule_pivot[p]).all() for p in DELAYS[1:]):
        raise RuntimeError("query schedule changed with delay profile")
    if not (
        monitor_schedule_pivot["full_stream"] == monitor_schedule_pivot["fixed_start_mixture"]
    ).all():
        raise RuntimeError("monitor variants do not share query schedules")
    manifest = {
        "experiment": "delayed_ppi_persistent_sign_informative_delay_stress",
        "seed_range": [SEED_OFFSET, SEED_OFFSET + SEEDS - 1],
        "seeds_per_cell": SEEDS,
        "horizon": HORIZON,
        "hard_label_cap": BUDGET,
        "query_probability_until_cap": Q,
        "alpha": ALPHA,
        "rho_values": list(RHOS),
        "delay_profiles": list(DELAYS),
        "monitors": list(MONITORS),
        "starts": list(STARTS),
        "stakes": list(STAKES),
        "rows": len(frame),
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "eprocess_reference_sha256": hashlib.sha256(
            Path(__file__).with_name("eprocess.py").read_bytes()
        ).hexdigest(),
        "runtime": environment(),
        "requested_device": device_name,
        "resolved_device": str(device),
        "event_time_and_query_paths_invariant_to_delay": True,
        "summary": summary.to_dict(orient="records"),
        "limitations": [
            "Persistent-sign cells violate the conditional-mean null and are stress cases, not calibration cells.",
            "The IID cell is a finite Monte Carlo implementation control, not a proof of validity.",
            "Outcome-dependent delay affects arrival time only; latency is not used as evidence.",
            "No dependence-aware alternative is proposed or validated by this screen.",
        ],
        "created_utc": datetime.now(UTC).isoformat(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for path in sorted(output.iterdir()):
        if path.name != "checksums.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with (output / "checksums.sha256").open("a", encoding="utf-8") as handle:
                handle.write(f"{digest}  {path.name}\n")
    print(summary.to_string(index=False), flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/delayed_ppi_assumption_stress_2000")
    )
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    run(
        device_name=args.device,
        output=args.output_dir,
        protocol=args.protocol,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
