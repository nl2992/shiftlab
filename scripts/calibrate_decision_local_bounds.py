"""Calibrate fixed and decision-local bounded e-processes under a hard label cap."""

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

STAKES = torch.tensor([0.05, 0.1, 0.2, 0.4, 0.8])
ALPHA = 0.05


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if total == 0:
        return float("nan"), float("nan")
    z = float(norm.ppf(0.975))
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def _paired_contrasts(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (high_cost, query_rate, probability), group in detail.groupby(
        ["high_cost", "query_rate", "outcome_probability"], sort=False
    ):
        paired = group.pivot(index="stream", columns="bound_mode", values="crossed")
        if not {"global", "decision_local"}.issubset(paired.columns) or paired.isna().any().any():
            raise ValueError("bound modes must contain the same matched stream ids")
        difference = paired["decision_local"].to_numpy(dtype=float) - paired["global"].to_numpy(
            dtype=float
        )
        n = len(difference)
        radius = float(student_t.ppf(0.975, n - 1) * difference.std(ddof=1) / np.sqrt(n))
        rows.append(
            {
                "high_cost": high_cost,
                "query_rate": query_rate,
                "outcome_probability": probability,
                "streams": n,
                "global_crossings": int(paired["global"].sum()),
                "decision_local_crossings": int(paired["decision_local"].sum()),
                "paired_crossing_rate_difference": float(difference.mean()),
                "paired_ci_low": float(difference.mean() - radius),
                "paired_ci_high": float(difference.mean() + radius),
            }
        )
    return pd.DataFrame(rows)


def refresh_analysis(output: Path) -> None:
    """Regenerate matched contrasts and artifact hashes from saved stream rows."""
    detail_path = output / "metrics/decision_local_bound_streams.parquet"
    summary_path = output / "metrics/decision_local_bound_summary.parquet"
    report_path = output / "reports/decision_local_bound_calibration.md"
    paired_path = output / "metrics/decision_local_bound_paired_contrasts.parquet"
    if not detail_path.exists() or not report_path.exists():
        raise FileNotFoundError("expected calibration stream table and report in output directory")
    paired = _paired_contrasts(pd.read_parquet(detail_path))
    paired.to_parquet(paired_path, index=False)
    report = report_path.read_text(encoding="utf-8")
    marker = "## Paired bound-mode contrasts"
    if marker in report:
        report = report.split(marker, maxsplit=1)[0].rstrip()
    lines = [
        "",
        marker,
        "",
        "Each row compares both bound modes on the same generated streams. Intervals are paired t intervals over independent streams and are unadjusted across all 27 cells.",
        "",
        "| High cost | Query cap | Outcome probability | Global crossings | Local crossings | Paired difference (95% CI) |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in paired.itertuples(index=False):
        lines.append(
            f"| {row.high_cost:.0f} | {row.query_rate:.0%} | {row.outcome_probability:.2f} | {row.global_crossings}/{row.streams} | {row.decision_local_crossings}/{row.streams} | {row.paired_crossing_rate_difference:.4f} [{row.paired_ci_low:.4f}, {row.paired_ci_high:.4f}] |"
        )
    lines.extend(
        [
            "",
            "The pointwise-null rows assess type-I behavior under the stronger conditional null. Alternatives assess power; these exploratory intervals are descriptive and do not establish uniform superiority or account for selecting a favorable cell.",
        ]
    )
    report_path.write_text(report + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = [detail_path, summary_path, paired_path, report_path]
    manifest["artifacts"] = [p.relative_to(output).as_posix() for p in artifacts]
    manifest["sha256"] = {
        p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in artifacts
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _cell(
    *,
    streams: int,
    horizon: int,
    query_rate: float,
    high_cost: float,
    outcome_probability: float,
    seed: int,
    device: torch.device,
) -> list[dict[str, float | int | bool | str]]:
    generator = torch.Generator(device=device).manual_seed(seed)
    queries = torch.rand((horizon, streams), generator=generator, device=device)
    strata = torch.randint(0, 2, (horizon, streams), generator=generator, device=device)
    outcomes = (
        torch.rand((horizon, streams), generator=generator, device=device) < outcome_probability
    )
    costs = torch.where(strata == 0, 1.0, high_cost).to(torch.float32)
    labels_cap = int(np.floor(query_rate * horizon))
    labels = torch.zeros(streams, dtype=torch.int32, device=device)
    processed = torch.zeros(streams, dtype=torch.int32, device=device)
    crossed = {
        mode: torch.zeros(streams, dtype=torch.bool, device=device)
        for mode in ("global", "decision_local")
    }
    crossing_time = {
        mode: torch.full((streams,), -1, dtype=torch.int32, device=device)
        for mode in ("global", "decision_local")
    }
    log_wealth = {
        mode: torch.zeros((streams, len(STAKES)), dtype=torch.float32, device=device)
        for mode in ("global", "decision_local")
    }
    stakes = STAKES.to(device)
    log_weights = torch.full((len(stakes),), -np.log(len(stakes)), device=device)
    threshold = -np.log(ALPHA)

    for t in range(horizon):
        active = labels < labels_cap
        if not bool(active.any()):
            break
        queried = active & (queries[t] < query_rate)
        labels += queried.to(torch.int32)
        processed += active.to(torch.int32)
        gain = torch.where(outcomes[t], costs[t], -costs[t])
        estimate = torch.where(queried, gain / query_rate, 0.0)
        bounds = {
            "global": torch.full_like(costs[t], high_cost / query_rate),
            "decision_local": costs[t] / query_rate,
        }
        for mode, bound in bounds.items():
            factors = 1 + estimate[:, None] * stakes[None, :] / bound[:, None]
            log_wealth[mode] += torch.log(factors)
            log_e = torch.logsumexp(log_wealth[mode] + log_weights[None, :], dim=1)
            new_crossings = (~crossed[mode]) & (log_e >= threshold)
            crossing_time[mode][new_crossings] = t + 1
            crossed[mode] |= new_crossings

    rows = []
    for mode in ("global", "decision_local"):
        final_log_e = torch.logsumexp(log_wealth[mode] + log_weights[None, :], dim=1)
        for i in range(streams):
            rows.append(
                {
                    "bound_mode": mode,
                    "stream": i,
                    "query_rate": query_rate,
                    "label_cap": labels_cap,
                    "labels_queried": int(labels[i].item()),
                    "horizon_processed": int(processed[i].item()),
                    "high_cost": high_cost,
                    "outcome_probability": outcome_probability,
                    "crossed": bool(crossed[mode][i].item()),
                    "crossing_time": int(crossing_time[mode][i].item()),
                    "final_log_e": float(final_log_e[i].item()),
                }
            )
    return rows


def run_calibration(
    *,
    output: Path,
    streams: int = 2000,
    horizon: int = 600,
    seed: int = 26102026,
    device_name: str = "cuda",
) -> None:
    if streams < 100 or horizon < 100:
        raise ValueError("streams and horizon must each be at least 100")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    device = torch.device(device_name)
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    reports_dir = output / "reports"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    detail_path = metrics_dir / "decision_local_bound_streams.parquet"
    summary_path = metrics_dir / "decision_local_bound_summary.parquet"
    if detail_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite existing calibration output: {output}")

    rows = []
    for cost_ratio in (1.0, 2.0, 5.0):
        for query_rate in (0.10, 0.20, 0.30):
            for p in (0.50, 0.53, 0.56):
                cell_seed = (
                    seed + int(cost_ratio * 1000) + int(query_rate * 10000) + int(p * 100000)
                )
                rows.extend(
                    _cell(
                        streams=streams,
                        horizon=horizon,
                        query_rate=query_rate,
                        high_cost=cost_ratio,
                        outcome_probability=p,
                        seed=cell_seed,
                        device=device,
                    )
                )
    detail = pd.DataFrame(rows)
    detail.to_parquet(detail_path, index=False)
    summary_rows = []
    for key, group in detail.groupby(
        ["high_cost", "query_rate", "outcome_probability", "bound_mode"], sort=False
    ):
        high_cost, query_rate, p, mode = key
        low, high = _wilson(int(group.crossed.sum()), len(group))
        summary_rows.append(
            {
                "high_cost": high_cost,
                "query_rate": query_rate,
                "outcome_probability": p,
                "bound_mode": mode,
                "streams": len(group),
                "crossings": int(group.crossed.sum()),
                "crossing_rate": float(group.crossed.mean()),
                "crossing_ci_low": low,
                "crossing_ci_high": high,
                "mean_labels": float(group.labels_queried.mean()),
                "label_cap": int(group.label_cap.iloc[0]),
                "mean_horizon_processed": float(group.horizon_processed.mean()),
                "mean_log_e_at_horizon": float(group.final_log_e.mean()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_parquet(summary_path, index=False)

    report_lines = [
        "# Decision-local betting-bound calibration",
        "",
        f"This CUDA/CPU simulation compares fixed global and predictable decision-local bounds over {streams} independent streams in each cell, horizon {horizon}, and query caps 10%, 20%, and 30%. It uses a single frozen candidate against a fixed reference, so alpha is 0.05 without a candidate-family correction.",
        "",
        "Each event reveals a cost stratum before label acquisition. Both policies choose different actions. Conditional on either stratum, the outcome probability 0.50 makes the paired cost gain have mean zero; this is a nondegenerate pointwise null. Costs are 1 in the low stratum and 1, 2, or 5 in the high stratum. Under alternatives, the outcome probability is 0.53 or 0.56 in both strata, producing positive conditional benefit. The queried-label indicator is Bernoulli with the displayed rate until the pathwise cap is reached; monitoring stops at that point.",
        "",
        "The global direct-IPW bound is max_cost/q. The local bound is the revealed event cost divided by q. Because the bound is predictable from information available before the current outcome and the null holds conditional on that information, each bounded betting factor has conditional expectation at most one. If only the history-conditional average null held, this data-dependent scaling would not in general preserve the sign of the expected betting increment. This experiment tests one candidate and independent streams; it is not a familywise-calibration claim for repeated promotion.",
        "",
        "## Results",
        "",
        "| High cost | Query cap | Outcome probability | Bound | Crossed / streams (95% Wilson CI) | Mean labels / cap | Mean events processed |",
        "|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        report_lines.append(
            f"| {row.high_cost:.0f} | {row.query_rate:.0%} | {row.outcome_probability:.2f} | {row.bound_mode} | {row.crossings}/{row.streams} ({row.crossing_ci_low:.3f}, {row.crossing_ci_high:.3f}) | {row.mean_labels:.1f} / {row.label_cap} | {row.mean_horizon_processed:.1f} |"
        )
    report_lines.extend(
        [
            "",
            "The null rows (outcome probability 0.50) are the calibration check; alternatives are power diagnostics. Wilson intervals describe Monte Carlo uncertainty and do not replace the betting-process proof. Results are reported for every registered cell without selecting a best cost ratio or query cap.",
            "",
            f"Reproduce with `uv run python scripts/calibrate_decision_local_bounds.py --streams {streams} --horizon {horizon} --seed {seed} --device {device_name} --output {output.as_posix()}`.",
        ]
    )
    report_path = reports_dir / "decision_local_bound_calibration.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest = {
        "experiment": "decision_local_bounded_eprocess_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": {
            "streams_per_cell": streams,
            "horizon": horizon,
            "seed": seed,
            "device": str(device),
            "alpha": ALPHA,
            "query_rates": [0.1, 0.2, 0.3],
            "high_costs": [1.0, 2.0, 5.0],
            "outcome_probabilities": [0.5, 0.53, 0.56],
        },
        "artifacts": [],
        "sha256": {},
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    refresh_analysis(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=2000)
    parser.add_argument("--horizon", type=int, default=600)
    parser.add_argument("--seed", type=int, default=26102026)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--analyze-existing", action="store_true")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/decision_local_bound_calibration")
    )
    args = parser.parse_args()
    if args.analyze_existing:
        refresh_analysis(args.output)
    else:
        run_calibration(
            output=args.output,
            streams=args.streams,
            horizon=args.horizon,
            seed=args.seed,
            device_name=args.device,
        )


if __name__ == "__main__":
    main()
