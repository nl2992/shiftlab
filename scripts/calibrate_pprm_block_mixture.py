"""Stress-test block e-process false alarms on bounded i.i.d. null streams."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.dive.hard_budget import PPRM_MIXTURE_WEIGHTS


def _endpoint_stream_crossings(
    upper_draws: np.ndarray,
    *,
    threshold: float,
    max_reliance: float,
    alpha: float,
    device: str,
) -> dict[str, np.ndarray]:
    """Vectorized CM-EB, hedged, and fixed-mixture paths for endpoint streams."""
    target_device = torch.device(device)
    draws = torch.as_tensor(upper_draws, dtype=torch.bool, device=target_device)
    lower = torch.tensor(-max_reliance, dtype=torch.float64, device=target_device)
    upper = torch.tensor(1 + max_reliance, dtype=torch.float64, device=target_device)
    values = torch.where(draws, upper, lower)
    n_streams, n_blocks = values.shape

    support_width = 1 + 2 * max_reliance
    cm_threshold = (threshold + max_reliance) / support_width
    normalized = (values + max_reliance) / support_width
    lambdas = torch.as_tensor(
        np.geomspace(1e-4, 0.99, 64), dtype=torch.float64, device=target_device
    )
    log_lambda_weights = torch.full_like(lambdas, -np.log(len(lambdas)))
    psi = -torch.log1p(-lambdas) - lambdas
    cm_sum = torch.zeros(n_streams, dtype=torch.float64, device=target_device)
    cm_sse = torch.zeros_like(cm_sum)
    cm_prediction = torch.full_like(cm_sum, 0.5)

    centered_bound = max(threshold + max_reliance, 1 + max_reliance - threshold)
    betting_observations = 0.5 * ((values - threshold) / centered_bound + 1)
    betting_sum = torch.zeros_like(cm_sum)
    betting_sse = torch.zeros_like(cm_sum)
    betting_prediction = torch.full_like(cm_sum, 0.5)
    betting_variance = torch.full_like(cm_sum, 0.25)
    betting_log_wealth = torch.zeros_like(cm_sum)

    threshold_log = -np.log(alpha)
    cm_crossed = torch.zeros(n_streams, dtype=torch.bool, device=target_device)
    betting_crossed = torch.zeros_like(cm_crossed)
    mixture_crossed = torch.zeros(
        (n_streams, len(PPRM_MIXTURE_WEIGHTS)), dtype=torch.bool, device=target_device
    )
    weights = torch.as_tensor(PPRM_MIXTURE_WEIGHTS, dtype=torch.float64, device=target_device)
    log_weights = torch.log(weights)
    log_complements = torch.log1p(-weights)
    betting_numerator = 2 * np.log(2 / alpha)

    for index in range(n_blocks):
        time = index + 1
        observation = normalized[:, index]
        cm_sse += (observation - cm_prediction) ** 2
        cm_sum += observation
        cm_prediction = cm_sum / time
        cm_excess = cm_sum - time * cm_threshold
        cm_log_value = torch.logsumexp(
            log_lambda_weights + cm_excess[:, None] * lambdas - cm_sse[:, None] * psi,
            dim=1,
        )
        cm_crossed |= cm_log_value >= threshold_log

        stake = torch.clamp(
            torch.sqrt(betting_numerator / (betting_variance * time * np.log1p(time))),
            max=1.0,
        )
        betting_observation = betting_observations[:, index]
        betting_factor = 1 + stake * (betting_observation - 0.5)
        betting_log_wealth += torch.log(betting_factor)
        betting_sum += betting_observation
        betting_prediction = (0.5 + betting_sum) / (time + 1)
        betting_sse += (betting_observation - betting_prediction) ** 2
        betting_variance = (0.25 + betting_sse) / (time + 1)
        betting_crossed |= betting_log_wealth >= threshold_log

        mixture_log_values = torch.logaddexp(
            cm_log_value[:, None] + log_weights[None, :],
            betting_log_wealth[:, None] + log_complements[None, :],
        )
        mixture_crossed |= mixture_log_values >= threshold_log

    result = {"CM-EB": cm_crossed.cpu().numpy(), "positive_betting": betting_crossed.cpu().numpy()}
    result.update(
        {
            f"mixture_w={weight:g}": mixture_crossed[:, index].cpu().numpy()
            for index, weight in enumerate(PPRM_MIXTURE_WEIGHTS)
        }
    )
    return result


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0:
        return float("nan"), float("nan")
    rate = successes / trials
    denom = 1 + z**2 / trials
    center = (rate + z**2 / (2 * trials)) / denom
    radius = z * math.sqrt(rate * (1 - rate) / trials + z**2 / (4 * trials**2)) / denom
    return center - radius, center + radius


def _calibrate_cell(
    *,
    null_name: str,
    mean: float,
    replicates: int,
    blocks: int,
    seed: int,
    threshold: float,
    max_reliance: float,
    alpha: float,
    device: str,
) -> list[dict[str, object]]:
    lower = -max_reliance
    upper = 1 + max_reliance
    upper_probability = (mean - lower) / (upper - lower)
    rng = np.random.default_rng(seed)
    upper_draws = rng.random((replicates, blocks)) < upper_probability
    crossing_flags = _endpoint_stream_crossings(
        upper_draws,
        threshold=threshold,
        max_reliance=max_reliance,
        alpha=alpha,
        device=device,
    )

    rows = []
    for method, did_cross in crossing_flags.items():
        count = int(did_cross.sum())
        lower_ci, upper_ci = _wilson(count, replicates)
        rows.append(
            {
                "null": null_name,
                "conditional_mean": mean,
                "method": method,
                "streams": replicates,
                "horizon_blocks": blocks,
                "false_escalations": count,
                "false_escalation_rate": count / replicates,
                "wilson_95_low": lower_ci,
                "wilson_95_high": upper_ci,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/pprm_block_mixture_calibration_v1")
    )
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument("--blocks", type=int, default=240)
    parser.add_argument("--seed", type=int, default=20373123)
    parser.add_argument("--threshold", type=float, default=0.51)
    parser.add_argument("--max-reliance", type=float, default=0.1)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if args.replicates < 1 or args.blocks < 1:
        parser.error("replicates and blocks must be positive")
    if not 0 <= args.threshold <= 1 or args.max_reliance < 0:
        parser.error("threshold must be in [0, 1] and max-reliance nonnegative")

    # For a bounded variable, endpoint support gives a demanding two-point null.
    means = (("boundary", args.threshold), ("below_boundary", max(0.0, args.threshold - 0.02)))
    resolved_device = args.device if args.device == "cpu" or torch.cuda.is_available() else "cpu"
    rows: list[dict[str, object]] = []
    for cell_index, (name, mean) in enumerate(means):
        rows.extend(
            _calibrate_cell(
                null_name=name,
                mean=mean,
                replicates=args.replicates,
                blocks=args.blocks,
                seed=args.seed + cell_index,
                threshold=args.threshold,
                max_reliance=args.max_reliance,
                alpha=args.alpha,
                device=resolved_device,
            )
        )

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "mixture_null_calibration.csv"
    report_path = output / "mixture_null_calibration.md"
    summary = pd.DataFrame(rows)
    summary.to_csv(summary_path, index=False)
    report_lines = [
        "# PPI block e-process null stress calibration",
        "",
        f"This Monte Carlo stress test used {args.replicates} independent streams per cell and {args.blocks} completed blocks per stream. Each block estimate was drawn i.i.d. from the two endpoints of the declared support, with the upper-endpoint probability chosen to give the listed conditional mean. It tests the sharp boundary and a null 0.02 below it. The experiment checks implementation-level false-escalation behavior; it does not prove the e-process theorem or cover serially dependent block estimates.",
        "",
        "|Null|Conditional mean|Method|Streams|False escalations|Rate|Wilson 95% interval|",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        report_lines.append(
            f"|{row['null']}|{row['conditional_mean']:.3f}|{row['method']}|{row['streams']}|{row['false_escalations']}|{row['false_escalation_rate']:.4f}|[{row['wilson_95_low']:.4f}, {row['wilson_95_high']:.4f}]|"
        )
    report_lines.extend(["", "Development-only calibration; power is not evaluated here.", ""])
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "experiment": "pprm_block_eprocess_endpoint_null_stress_calibration",
        "classification": "development_null_calibration",
        "configuration": {
            "replicates_per_cell": args.replicates,
            "blocks_per_stream": args.blocks,
            "seed": args.seed,
            "alpha": args.alpha,
            "threshold": args.threshold,
            "max_reliance": args.max_reliance,
            "support": [-args.max_reliance, 1 + args.max_reliance],
            "mixture_weights": list(PPRM_MIXTURE_WEIGHTS),
            "null_means": {name: mean for name, mean in means},
            "distribution": "i.i.d. two-point endpoint distribution on declared support",
            "requested_device": args.device,
            "resolved_device": resolved_device,
        },
        "sha256": {
            "source": sha256(Path(__file__)),
            "summary_csv": sha256(summary_path),
            "report": sha256(report_path),
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(report_path)


if __name__ == "__main__":
    main()
