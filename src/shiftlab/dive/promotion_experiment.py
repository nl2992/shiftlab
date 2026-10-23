"""Forward-time shadow-candidate certification experiment."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate
from .experiment import _binary_cost, finalize_manifest
from .promotion import CandidatePromotionTest, CandidateVersion


def _plot_promotion_summary(summary: pd.DataFrame, figure_path: Path) -> None:
    scenario_order = [scenario.name for scenario in SCENARIOS]
    candidate_order = ["incumbent_snapshot", "recalibrated_candidate"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for candidate in candidate_order:
        group = (
            summary[summary.candidate == candidate].set_index("scenario").reindex(scenario_order)
        )
        axes[0].plot(scenario_order, group.certification_rate, marker="o", label=candidate)
    positions = np.arange(len(scenario_order))
    width = 0.38
    for index, candidate in enumerate(candidate_order):
        group = (
            summary[summary.candidate == candidate].set_index("scenario").reindex(scenario_order)
        )
        offset = (index - (len(candidate_order) - 1) / 2) * width
        axes[1].bar(positions + offset, group.true_net_gain, width, label=candidate)
    axes[0].set(ylabel="Certification rate", xlabel="Synthetic regime")
    axes[0].tick_params(axis="x", rotation=40)
    axes[0].set_ylim(-0.03, 1.03)
    axes[1].set(
        xlabel="Synthetic regime",
        ylabel="Mean evaluator-known net candidate gain",
    )
    axes[1].set_xticks(positions, scenario_order, rotation=40, ha="right")
    axes[1].axhline(0, color="black", linestyle="--", linewidth=0.8)
    axes[1].set_ylim(
        min(-0.08, float(summary.true_net_gain.min()) - 0.02),
        float(summary.true_net_gain.max()) + 0.03,
    )
    for axis in axes:
        axis.grid(axis="y", alpha=0.25)
        axis.legend(fontsize=7)
    fig.suptitle("Fresh forward-time shadow candidate tests (full immediate feedback)")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)


@dataclass(frozen=True)
class PromotionExperimentConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 30
    seed_offset: int = 20361022
    alpha: float = 0.05
    switching_cost: float = 0.05
    device: str = "auto"


def _evaluate_stream(scenario, seed: int, config: PromotionExperimentConfig) -> list[dict]:
    source = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        window=64,
        stride=32,
        alpha=config.alpha,
        eprocess_epsilon=0.1,
        seed_offset=seed,
        device=config.device,
    )
    _, frame, oracle, _ = _generate(scenario, seed, source)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    p = oracle.probability_positive.to_numpy(dtype=float)
    fn, fp = scenario.fn_cost, scenario.fp_cost

    # This is the frozen pre-intervention policy and is available before the monitor slice.
    snapshot = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    incumbent = snapshot.copy()
    if scenario.harmful_adaptation:
        incumbent[config.n // 2 :] = 1

    train_end = max(100, int(config.n * 0.125))
    monitor_start = max(800, int(config.n * 0.25))
    classifier = LogisticRegression(max_iter=500, random_state=seed).fit(
        x[:train_end], y[:train_end]
    )
    threshold = fp / (fn + fp)
    recalibrated = (classifier.predict_proba(x)[:, 1] >= threshold).astype(int)
    candidates = {
        "incumbent_snapshot": snapshot,
        "recalibrated_candidate": recalibrated,
    }
    current_probability_cost = np.where(incumbent == 1, fp * (1 - p), fn * p)
    rows = []
    for candidate_index, (candidate_name, actions) in enumerate(candidates.items(), start=1):
        certifier = CandidatePromotionTest(
            CandidateVersion(
                candidate_id=f"{scenario.name}:{seed}:{candidate_name}",
                parent_version="deployed-policy-v1",
                training_cutoff=train_end - 1,
                candidate_index=candidate_index,
            ),
            alpha_total=config.alpha,
            max_event_cost=max(fn, fp),
            switching_cost=config.switching_cost,
        )
        candidate_probability_cost = np.where(actions == 1, fp * (1 - p), fn * p)
        true_net_gain = float(
            np.mean(
                current_probability_cost[monitor_start:]
                - candidate_probability_cost[monitor_start:]
                - config.switching_cost
            )
        )
        alarm_time = None
        for event_index in range(monitor_start, config.n):
            incumbent_cost = _binary_cost(
                incumbent[event_index : event_index + 1], y[event_index : event_index + 1], fn, fp
            )[0]
            candidate_cost = _binary_cost(
                actions[event_index : event_index + 1], y[event_index : event_index + 1], fn, fp
            )[0]
            log_e_value = certifier.update(
                event_index=event_index,
                incumbent_cost=float(incumbent_cost),
                candidate_cost=float(candidate_cost),
            )
            if alarm_time is None and log_e_value >= -np.log(certifier.alpha_i):
                alarm_time = event_index - monitor_start
        null_applicable = candidate_name == "incumbent_snapshot" and not scenario.harmful_adaptation
        rows.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "candidate": candidate_name,
                "candidate_index": candidate_index,
                "training_cutoff": train_end - 1,
                "evaluation_start": monitor_start,
                "alpha_i": certifier.alpha_i,
                "switching_cost": config.switching_cost,
                "true_mean_net_gain": true_net_gain,
                "certified": certifier.certified,
                "certificate_time": alarm_time,
                "null_applicable": null_applicable,
                "false_promotion_under_pointwise_null": bool(
                    null_applicable and certifier.certified
                ),
            }
        )
    return rows


def run_promotion_experiment(
    config: PromotionExperimentConfig, output: Path = Path("outputs/promotion_experiment_corrected")
) -> Path:
    if config.n < 1000 or config.d < 2 or config.seeds < 1:
        raise ValueError("n must be >=1000, d >=2, and seeds >=1")
    if not 0 < config.alpha < 1 or config.switching_cost < 0:
        raise ValueError("alpha must lie in (0,1) and switching cost must be nonnegative")
    device = resolve_device(config.device, n=config.n, d=config.d, chunk_size=5000)
    config = PromotionExperimentConfig(**{**asdict(config), "device": device})
    metrics_dir = output / "metrics"
    figures_dir = output / "figures"
    reports_dir = output / "reports"
    for directory in (metrics_dir, figures_dir, reports_dir):
        directory.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / "promotion_comparison.parquet"
    if metrics_path.exists():
        raise FileExistsError(f"refusing to overwrite existing promotion results: {metrics_path}")
    rows = []
    for scenario in SCENARIOS:
        for replicate in range(config.seeds):
            seed = config.seed_offset + replicate
            print(
                f"promotion scenario={scenario.name} replicate={replicate + 1}/{config.seeds}",
                flush=True,
            )
            rows.extend(_evaluate_stream(scenario, seed, config))
    metrics = pd.DataFrame(rows)
    metrics.to_parquet(metrics_path, index=False)
    summary = metrics.groupby(["scenario", "candidate"], as_index=False).agg(
        certification_rate=("certified", "mean"),
        certifications=("certified", "sum"),
        streams=("certified", "size"),
        true_net_gain=("true_mean_net_gain", "mean"),
        certificate_delay=("certificate_time", "median"),
        false_promotion_rate=("false_promotion_under_pointwise_null", "mean"),
        null_applicable=("null_applicable", "first"),
    )

    figure_path = figures_dir / "adaptation_promotion.png"
    _plot_promotion_summary(summary, figure_path)

    null_rows = metrics[metrics.null_applicable]

    def wilson(successes: int, trials: int) -> tuple[float, float]:
        z = float(norm.ppf(0.975))
        rate = successes / trials
        denominator = 1 + z**2 / trials
        center = (rate + z**2 / (2 * trials)) / denominator
        radius = z * np.sqrt(rate * (1 - rate) / trials + z**2 / (4 * trials**2)) / denominator
        return max(0.0, center - radius), min(1.0, center + radius)

    text_report = [
        "# Shadow candidate promotion experiment",
        "",
        f"Evaluated {config.seeds} paired streams per scenario using `{config.device}` synthetic generation and full immediate feedback. Candidates were frozen using only the early training slice; evaluation began at the forward-time monitor boundary.",
        "",
        f"`incumbent_snapshot` is an exact copy of the deployed policy in all scenarios except the deliberately harmful-adaptation scenario. With switching cost {config.switching_cost:g}, its pointwise expected net gain is negative in the unchanged-policy scenarios, so those rows provide the null certification check. `recalibrated_candidate` is a cost-threshold logistic model trained on the early slice. Candidate i receives alpha_i=alpha/[i(i+1)].",
        "",
        "This evaluates certification behavior, not an integrated intervention controller. The candidate comparison assumes paired potential costs are observable from the same outcome; it is unsuitable when actions change outcomes without a randomized/off-policy design. The recalibrated candidate can see changing regime conditions, so its descriptive false-certification rate is not interpreted as a validity check unless the conditional null holds at every event.",
        "",
        f"False certifications of the exact-copy candidate under its pointwise null: {int(null_rows.false_promotion_under_pointwise_null.sum())}/{len(null_rows)} across applicable streams. This finite simulation is a diagnostic, not the guarantee; the guarantee follows only under the documented assumptions.",
        "",
        "| Scenario | Candidate | Mean true net gain | Certification rate (95% Wilson) | Median delay | Null applicable |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in summary.itertuples(index=False):
        delay = "—" if pd.isna(row.certificate_delay) else f"{row.certificate_delay:.0f}"
        low, high = wilson(int(row.certifications), int(row.streams))
        text_report.append(
            f"| {row.scenario} | {row.candidate} | {row.true_net_gain:.4f} | "
            f"{row.certification_rate:.3f} [{low:.3f},{high:.3f}] | {delay} | {bool(row.null_applicable)} |"
        )
    (reports_dir / "promotion_comparison.md").write_text("\n".join(text_report), encoding="utf-8")
    manifest_path = reports_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    )
    manifest["promotion_experiment"] = {
        "configuration": asdict(config),
        "environment": environment(),
        "candidates": ["incumbent_snapshot", "recalibrated_candidate"],
        "metric_path": str(metrics_path),
        "figure_path": str(figure_path),
        "report_path": str(reports_dir / "promotion_comparison.md"),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return figure_path


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/promotion_experiment_corrected")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args(argv)
    config = PromotionExperimentConfig(
        n=args.n,
        d=args.d,
        seeds=args.seeds,
        device=args.device,
    )
    print(run_promotion_experiment(config, args.output), flush=True)


if __name__ == "__main__":
    main()
