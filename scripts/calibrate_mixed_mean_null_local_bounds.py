"""Test decision-local betting against a nonpositive aggregate mean with mixed strata."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import norm
from scipy.stats import t as student_t

ALPHA = 0.05
STAKES = torch.tensor([0.05, 0.1, 0.2, 0.4, 0.8])


def _wilson(successes: int, total: int) -> tuple[float, float]:
    z = float(norm.ppf(0.975))
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def _simulate_cell(
    *,
    streams: int,
    horizon: int,
    high_cost: float,
    query_rate: float,
    seed: int,
    device: torch.device,
) -> list[dict[str, float | int | bool | str]]:
    # Low-cost context is beneficial and high-cost context is harmful, but the
    # equal-probability aggregate expected paired gain is exactly zero.
    p_low = 0.56
    p_high = 0.5 - 0.06 / high_cost
    aggregate_mean_gain = 0.5 * (2 * p_low - 1) + 0.5 * high_cost * (2 * p_high - 1)
    if abs(aggregate_mean_gain) > 1e-12:
        raise RuntimeError("mixed-stratum null is not mean-zero")

    generator = torch.Generator(device=device).manual_seed(seed)
    covariate = torch.randint(0, 2, (horizon, streams), generator=generator, device=device)
    query_uniform = torch.rand((horizon, streams), generator=generator, device=device)
    outcome_uniform = torch.rand((horizon, streams), generator=generator, device=device)
    cost = torch.where(covariate == 0, 1.0, high_cost).to(torch.float32)
    probability = torch.where(covariate == 0, p_low, p_high)
    outcomes = outcome_uniform < probability
    cap = int(np.floor(query_rate * horizon))
    labels = torch.zeros(streams, dtype=torch.int32, device=device)
    active_count = torch.zeros_like(labels)
    log_wealth = {
        mode: torch.zeros((streams, len(STAKES)), device=device)
        for mode in ("global", "decision_local")
    }
    crossed = {mode: torch.zeros(streams, dtype=torch.bool, device=device) for mode in log_wealth}
    stakes = STAKES.to(device)
    log_weights = torch.full((len(stakes),), -np.log(len(stakes)), device=device)
    for event in range(horizon):
        active = labels < cap
        if not bool(active.any()):
            break
        queried = active & (query_uniform[event] < query_rate)
        labels += queried.to(torch.int32)
        active_count += active.to(torch.int32)
        gain = torch.where(outcomes[event], cost[event], -cost[event])
        estimate = torch.where(queried, gain / query_rate, 0.0)
        bounds = {
            "global": torch.full_like(cost[event], high_cost / query_rate),
            "decision_local": cost[event] / query_rate,
        }
        for mode, bound in bounds.items():
            factor = 1 + estimate[:, None] * stakes[None, :] / bound[:, None]
            log_wealth[mode] += torch.log(factor)
            log_e = torch.logsumexp(log_wealth[mode] + log_weights[None, :], dim=1)
            crossed[mode] |= log_e >= -np.log(ALPHA)

    rows = []
    for mode in log_wealth:
        for stream in range(streams):
            rows.append(
                {
                    "bound_mode": mode,
                    "stream": stream,
                    "high_cost": high_cost,
                    "query_rate": query_rate,
                    "label_cap": cap,
                    "labels_queried": int(labels[stream].item()),
                    "events_processed": int(active_count[stream].item()),
                    "p_low_cost": p_low,
                    "p_high_cost": p_high,
                    "aggregate_expected_gain": aggregate_mean_gain,
                    "crossed": bool(crossed[mode][stream].item()),
                }
            )
    return rows


def run(
    *,
    output: Path,
    streams: int = 2000,
    horizon: int = 600,
    seed: int = 27102026,
    device_name: str = "cuda",
) -> None:
    if streams < 100 or horizon < 100:
        raise ValueError("streams and horizon must each be at least 100")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    device = torch.device(device_name)
    metric_dir = output / "metrics"
    report_dir = output / "reports"
    metric_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metric_dir / "mixed_mean_null_streams.parquet"
    summary_path = metric_dir / "mixed_mean_null_summary.parquet"
    if detail_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")

    rows = []
    for ratio in (2.0, 5.0):
        for q in (0.10, 0.20, 0.30):
            rows.extend(
                _simulate_cell(
                    streams=streams,
                    horizon=horizon,
                    high_cost=ratio,
                    query_rate=q,
                    seed=seed + int(ratio * 1000) + int(q * 10000),
                    device=device,
                )
            )
    detail = pd.DataFrame(rows)
    detail.to_parquet(detail_path, index=False)
    summary_rows = []
    for (ratio, q, mode), group in detail.groupby(
        ["high_cost", "query_rate", "bound_mode"], sort=False
    ):
        low, high = _wilson(int(group.crossed.sum()), len(group))
        summary_rows.append(
            {
                "high_cost": ratio,
                "query_rate": q,
                "bound_mode": mode,
                "streams": len(group),
                "crossings": int(group.crossed.sum()),
                "crossing_rate": float(group.crossed.mean()),
                "wilson_ci_low": low,
                "wilson_ci_high": high,
                "mean_labels": float(group.labels_queried.mean()),
                "label_cap": int(group.label_cap.iloc[0]),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_parquet(summary_path, index=False)
    paired_rows = []
    for (ratio, q), group in detail.groupby(["high_cost", "query_rate"], sort=False):
        paired = group.pivot(index="stream", columns="bound_mode", values="crossed")
        differences = paired["decision_local"].to_numpy(dtype=float) - paired["global"].to_numpy(
            dtype=float
        )
        radius = float(
            student_t.ppf(0.975, len(differences) - 1)
            * differences.std(ddof=1)
            / np.sqrt(len(differences))
        )
        paired_rows.append(
            {
                "high_cost": ratio,
                "query_rate": q,
                "streams": len(differences),
                "global_crossings": int(paired["global"].sum()),
                "local_crossings": int(paired["decision_local"].sum()),
                "local_minus_global": float(differences.mean()),
                "paired_ci_low": float(differences.mean() - radius),
                "paired_ci_high": float(differences.mean() + radius),
            }
        )
    paired_path = metric_dir / "mixed_mean_null_paired.parquet"
    pd.DataFrame(paired_rows).to_parquet(paired_path, index=False)

    lines = [
        "# Mixed-sign conditional gains under an aggregate promotion null",
        "",
        f"This CUDA/CPU experiment uses {streams} independent streams per cell, a {horizon}-event horizon, one frozen candidate, and a pathwise label cap. It constructs an aggregate expected paired gain of exactly zero while conditional gains have opposite signs across two equally likely covariate strata.",
        "",
        "The incumbent chooses action 0 and the candidate action 1. In the low-cost stratum the false-positive and false-negative cost is 1 and P(Y=1)=0.56, so candidate gain is +0.12. In the high-cost stratum the symmetric cost is 2 or 5 and its outcome probability is set so expected gain is -0.12 in cost units. Averaging the two strata gives zero overall gain. Thus the candidate is non-improving in the aggregate but violates the pointwise conditional null.",
        "",
        "The global process has the aggregate-mean null as its target and uses max_cost/q. The decision-local process divides each queried contrast by the revealed stratum cost/q; this weights low-cost positive gains more heavily and therefore does not test the same aggregate estimand. Both use identical query draws and stop at the same hard cap.",
        "",
        "| High cost | Query cap | Bound | Crossings / streams (95% Wilson CI) | Mean labels / cap |",
        "|---:|---:|---|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.high_cost:.0f} | {row.query_rate:.0%} | {row.bound_mode} | {row.crossings}/{row.streams} ({row.wilson_ci_low:.3f}, {row.wilson_ci_high:.3f}) | {row.mean_labels:.1f}/{row.label_cap} |"
        )
    lines.extend(
        [
            "",
            "Under the aggregate null, a decision-local crossing is an erroneous promotion for the stated mean-net-benefit objective, even though it may be valid evidence against the stronger pointwise null. This is a direct falsification check of using local scaling as an aggregate promotion certificate; the Monte Carlo rate does not replace the proof-level estimand argument.",
            "",
            f"Reproduce with `uv run python scripts/calibrate_mixed_mean_null_local_bounds.py --streams {streams} --horizon {horizon} --seed {seed} --device {device_name} --output {output.as_posix()}`.",
        ]
    )
    report_path = report_dir / "mixed_mean_null_calibration.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    artifacts = [detail_path, summary_path, paired_path, report_path]
    manifest = {
        "experiment": "mixed_sign_conditional_gains_aggregate_mean_null",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": {
            "streams_per_cell": streams,
            "horizon": horizon,
            "seed": seed,
            "device": str(device),
            "alpha": ALPHA,
            "query_rates": [0.1, 0.2, 0.3],
            "high_costs": [2.0, 5.0],
            "aggregate_expected_gain": 0.0,
            "low_stratum_outcome_probability": 0.56,
        },
        "artifacts": [p.relative_to(output).as_posix() for p in artifacts],
        "reproduction_script": "scripts/calibrate_mixed_mean_null_local_bounds.py",
        "reproduction_script_sha256": hashlib.sha256(
            Path("scripts/calibrate_mixed_mean_null_local_bounds.py").read_bytes()
        ).hexdigest(),
        "sha256": {
            "artifacts": {
                p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in artifacts
            }
        },
    }
    (report_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--horizon", type=int, default=600)
    parser.add_argument("--seed", type=int, default=27102026)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--output", type=Path, default=Path("outputs/mixed_mean_null_local_bound"))
    args = parser.parse_args()
    run(
        output=args.output,
        streams=args.streams,
        horizon=args.horizon,
        seed=args.seed,
        device_name=args.device,
    )


if __name__ == "__main__":
    main()
