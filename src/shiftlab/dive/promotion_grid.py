"""Forward-time model-grid selection with simultaneous promotion gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..data.gpu.environment import environment, resolve_device
from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate
from .experiment import _binary_cost, finalize_manifest
from .promotion import CandidatePromotionTest, CandidateVersion


@dataclass(frozen=True)
class PromotionGridConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 30
    seed_offset: int = 20381023
    alpha: float = 0.05
    switching_cost: float = 0.05
    regularization: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
    threshold_scales: tuple[float, ...] = (0.75, 1.0, 1.25)
    scenario_subset: tuple[str, ...] = ()
    device: str = "auto"

    def validate(self) -> PromotionGridConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds >=1")
        if not np.isfinite(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError("alpha must lie in (0, 1)")
        if not np.isfinite(self.switching_cost) or self.switching_cost < 0:
            raise ValueError("switching_cost must be finite and nonnegative")
        if not self.regularization or any(
            not np.isfinite(value) or value <= 0 for value in self.regularization
        ):
            raise ValueError("regularization grid must contain finite positive values")
        if not self.threshold_scales or any(
            not np.isfinite(value) or value <= 0 for value in self.threshold_scales
        ):
            raise ValueError("threshold scales must contain finite positive values")
        if len(set(self.regularization)) != len(self.regularization):
            raise ValueError("regularization values must be unique")
        if len(set(self.threshold_scales)) != len(self.threshold_scales):
            raise ValueError("threshold scales must be unique")
        known = {scenario.name for scenario in SCENARIOS}
        if len(set(self.scenario_subset)) != len(self.scenario_subset) or any(
            scenario not in known for scenario in self.scenario_subset
        ):
            raise ValueError("scenario_subset must contain unique registered scenarios")
        return self


def _expected_cost(
    actions: np.ndarray, probability: np.ndarray, fn: float, fp: float
) -> np.ndarray:
    return np.where(actions == 1, fp * (1 - probability), fn * probability)


def _time_splits(n: int) -> tuple[int, int, int]:
    train_end = max(100, int(n * 0.125))
    validation_end = max(800, int(n * 0.25))
    monitor_end = max(validation_end + 1, int(n * 0.75))
    if not train_end < validation_end < monitor_end < n:
        raise ValueError(
            "n must provide disjoint train, validation, monitor, and deployment slices"
        )
    return train_end, validation_end, monitor_end


def _candidate_models(
    *,
    x: np.ndarray,
    y: np.ndarray,
    train_end: int,
    validation_end: int,
    incumbent: np.ndarray,
    fn: float,
    fp: float,
    deployment_horizon: int,
    config: PromotionGridConfig,
) -> list[dict[str, object]]:
    base_threshold = fp / (fn + fp)
    candidates: list[dict[str, object]] = [
        {"candidate_id": "incumbent_snapshot", "actions": incumbent.copy()}
    ]
    for c_value in config.regularization:
        model = LogisticRegression(C=c_value, max_iter=500)
        model.fit(x[:train_end], y[:train_end])
        probability = model.predict_proba(x)[:, 1]
        for scale in config.threshold_scales:
            threshold = float(np.clip(base_threshold * scale, 0.01, 0.99))
            candidates.append(
                {
                    "candidate_id": f"logistic_C={c_value:g}_threshold_scale={scale:g}",
                    "actions": (probability >= threshold).astype(int),
                }
            )
    val_slice = slice(train_end, validation_end)
    incumbent_val_cost = _binary_cost(incumbent[val_slice], y[val_slice], fn, fp)
    switch_rate = config.switching_cost / deployment_horizon
    for candidate in candidates:
        actions = np.asarray(candidate["actions"], dtype=int)
        candidate_val_cost = _binary_cost(actions[val_slice], y[val_slice], fn, fp)
        candidate["validation_gain"] = float(
            np.mean(incumbent_val_cost - candidate_val_cost) - switch_rate
        )
    candidates.sort(
        key=lambda item: (-cast(float, item["validation_gain"]), str(item["candidate_id"]))
    )
    return candidates


def _fixed_horizon_gate(gains: np.ndarray, *, bound: float, alpha: float) -> bool:
    """One-sided Azuma-Hoeffding test for a bounded conditional-mean null."""
    values = np.asarray(gains, dtype=float).reshape(-1)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("fixed-horizon gains must be a nonempty finite vector")
    threshold = bound * np.sqrt(2 * np.log(1 / alpha) / len(values))
    return bool(float(values.mean()) >= threshold)


def _evaluate_stream(
    scenario,
    seed: int,
    config: PromotionGridConfig,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
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
    probability = oracle.probability_positive.to_numpy(dtype=float)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    incumbent = (x[:, 0] - 0.9 * x[:, 1] >= 0).astype(int)
    if scenario.harmful_adaptation:
        incumbent[config.n // 2 :] = 1

    train_end, validation_end, monitor_end = _time_splits(config.n)
    monitor = slice(validation_end, monitor_end)
    deployment = slice(monitor_end, config.n)
    post_length = deployment.stop - deployment.start
    per_event_switch_cost = config.switching_cost / post_length
    candidates = _candidate_models(
        x=x,
        y=y,
        train_end=train_end,
        validation_end=validation_end,
        incumbent=incumbent,
        fn=fn,
        fp=fp,
        deployment_horizon=post_length,
        config=config,
    )

    incumbent_monitor_cost = _binary_cost(incumbent[monitor], y[monitor], fn, fp)
    incumbent_deployment_cost = _binary_cost(incumbent[deployment], y[deployment], fn, fp)
    incumbent_monitor_expected = _expected_cost(incumbent[monitor], probability[monitor], fn, fp)
    incumbent_deployment_expected = _expected_cost(
        incumbent[deployment], probability[deployment], fn, fp
    )
    candidate_rows: list[dict[str, object]] = []
    fixed_certified: list[str] = []
    sequential_certified: list[str] = []
    validation_positive_ids: list[str] = []

    max_event_cost = max(fn, fp)
    for candidate_index, candidate in enumerate(candidates, start=1):
        candidate_id = str(candidate["candidate_id"])
        actions = np.asarray(candidate["actions"], dtype=int)
        validation_gain = cast(float, candidate["validation_gain"])
        if validation_gain > 0:
            validation_positive_ids.append(candidate_id)

        candidate_monitor_cost = _binary_cost(actions[monitor], y[monitor], fn, fp)
        gains = incumbent_monitor_cost - candidate_monitor_cost - per_event_switch_cost
        candidate_monitor_expected = _expected_cost(actions[monitor], probability[monitor], fn, fp)
        expected_gains = (
            incumbent_monitor_expected - candidate_monitor_expected - per_event_switch_cost
        )
        candidate_version = CandidateVersion(
            candidate_id=f"{scenario.name}:{seed}:{candidate_id}",
            parent_version="deployed-policy-v1",
            training_cutoff=train_end - 1,
            candidate_index=candidate_index,
        )
        certifier = CandidatePromotionTest(
            candidate_version,
            alpha_total=config.alpha,
            max_event_cost=max_event_cost,
            switching_cost=per_event_switch_cost,
        )
        certificate_time = None
        for relative_index, _ in enumerate(gains):
            log_e = certifier.update(
                event_index=validation_end + relative_index,
                incumbent_cost=float(incumbent_monitor_cost[relative_index]),
                candidate_cost=float(candidate_monitor_cost[relative_index]),
            )
            if certificate_time is None and log_e >= -np.log(certifier.alpha_i):
                certificate_time = relative_index
        fixed_bound = max_event_cost + per_event_switch_cost
        fixed_gate = _fixed_horizon_gate(gains, bound=fixed_bound, alpha=certifier.alpha_i)
        if fixed_gate:
            fixed_certified.append(candidate_id)
        if certifier.certified:
            sequential_certified.append(candidate_id)

        candidate_deploy_cost = _binary_cost(actions[deployment], y[deployment], fn, fp)
        candidate_deploy_expected = _expected_cost(
            actions[deployment], probability[deployment], fn, fp
        )
        same_as_incumbent_monitor = bool(np.array_equal(actions[monitor], incumbent[monitor]))
        candidate_rows.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "candidate_id": candidate_id,
                "candidate_index_validation_rank": candidate_index,
                "alpha_i": certifier.alpha_i,
                "training_cutoff": train_end - 1,
                "validation_end": validation_end,
                "monitor_start": validation_end,
                "monitor_end": monitor_end,
                "validation_mean_net_gain": validation_gain,
                "monitor_realized_mean_net_gain": float(gains.mean()),
                "monitor_oracle_mean_net_gain": float(expected_gains.mean()),
                "monitor_pointwise_null_path": bool(np.all(expected_gains <= 1e-12)),
                "exact_policy_copy_null": same_as_incumbent_monitor,
                "sequential_certified": certifier.certified,
                "sequential_certificate_time": certificate_time,
                "fixed_horizon_certified": fixed_gate,
                "post_expected_net_gain_total": float(
                    np.sum(incumbent_deployment_expected - candidate_deploy_expected)
                    - config.switching_cost
                ),
                "post_realized_net_gain_total": float(
                    np.sum(incumbent_deployment_cost - candidate_deploy_cost)
                    - config.switching_cost
                ),
                "null_candidate_false_certificate": bool(
                    same_as_incumbent_monitor and certifier.certified
                ),
            }
        )

    candidate_by_id = {str(row["candidate_id"]): row for row in candidate_rows}
    top_validation = (
        validation_positive_ids[0] if validation_positive_ids else None
    )  # candidates are already sorted by validation gain
    fixed_choice = next(
        (
            str(candidate["candidate_id"])
            for candidate in candidates
            if str(candidate["candidate_id"]) in fixed_certified
            and cast(float, candidate["validation_gain"]) > 0
        ),
        None,
    )
    sequential_choice = next(
        (
            str(candidate["candidate_id"])
            for candidate in candidates
            if str(candidate["candidate_id"]) in sequential_certified
            and cast(float, candidate["validation_gain"]) > 0
        ),
        None,
    )
    strategies = {
        "never_promote": None,
        "validation_always_promote": top_validation,
        "fixed_horizon_grid_gate": fixed_choice,
        "sequential_grid_gate": sequential_choice,
    }
    strategy_rows: list[dict[str, object]] = []
    for strategy, selected_id in strategies.items():
        if selected_id is None:
            expected_gain = realized_gain = 0.0
            promoted = False
            post_cost_expected = float(incumbent_deployment_expected.mean())
            post_cost_realized = float(incumbent_deployment_cost.mean())
        else:
            selected = candidate_by_id[selected_id]
            expected_gain = cast(float, selected["post_expected_net_gain_total"])
            realized_gain = cast(float, selected["post_realized_net_gain_total"])
            promoted = True
            candidate_actions = np.asarray(
                next(c["actions"] for c in candidates if c["candidate_id"] == selected_id),
                dtype=int,
            )
            post_cost_expected = float(
                _expected_cost(
                    candidate_actions[deployment], probability[deployment], fn, fp
                ).mean()
            )
            post_cost_realized = float(
                _binary_cost(candidate_actions[deployment], y[deployment], fn, fp).mean()
            )
        strategy_rows.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "strategy": strategy,
                "promoted": promoted,
                "selected_candidate": selected_id,
                "validation_selected_gain": (
                    np.nan
                    if selected_id is None
                    else cast(float, candidate_by_id[selected_id]["validation_mean_net_gain"])
                ),
                "post_expected_net_gain_total": expected_gain,
                "post_realized_net_gain_total": realized_gain,
                "post_mean_expected_cost": post_cost_expected,
                "post_mean_realized_cost": post_cost_realized,
                "false_promotion_post_nongain": bool(promoted and expected_gain <= 0),
                "deployment_events": post_length,
                "monitor_events": monitor.stop - monitor.start,
                "candidate_count": len(candidates),
                "monitor_label_count": monitor.stop - monitor.start,
            }
        )
    return candidate_rows, strategy_rows


def _wilson(successes: int, total: int) -> tuple[float, float]:
    z = float(norm.ppf(0.975))
    rate = successes / total
    denominator = 1 + z**2 / total
    center = (rate + z**2 / (2 * total)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / total + z**2 / (4 * total**2)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _write_figures(strategy_summary: pd.DataFrame, figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    scenarios = [scenario.name for scenario in SCENARIOS]
    strategies = [
        "never_promote",
        "validation_always_promote",
        "fixed_horizon_grid_gate",
        "sequential_grid_gate",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    width = 0.18
    positions = np.arange(len(scenarios))
    for offset, strategy in enumerate(strategies):
        rows = strategy_summary[strategy_summary.strategy.eq(strategy)].set_index("scenario")
        rows = rows.reindex(scenarios)
        x_pos = positions + (offset - (len(strategies) - 1) / 2) * width
        axes[0].bar(x_pos, rows.expected_net_gain, width, label=strategy)
        axes[1].bar(x_pos, rows.promotion_rate, width, label=strategy)
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_ylabel("Expected net gain on untouched deployment slice")
    axes[1].set_ylabel("Promotion rate")
    for axis in axes:
        axis.set_xticks(positions, scenarios, rotation=35, ha="right")
        axis.grid(axis="y", alpha=0.25)
        axis.legend(fontsize=7)
    fig.suptitle("Grid-selected shadow candidates: deployment value and promotion rate")
    fig.tight_layout()
    fig.savefig(figure_dir / "promotion_grid_outcomes.png", dpi=170)
    plt.close(fig)


def run_promotion_grid(config: PromotionGridConfig, output: Path) -> Path:
    config.validate()
    requested_device = config.device
    device = resolve_device(config.device, n=config.n, d=config.d, chunk_size=5000)
    config = PromotionGridConfig(**{**asdict(config), "device": device})
    candidate_path = output / "metrics/promotion_grid_candidates.parquet"
    strategy_path = output / "metrics/promotion_grid_strategies.parquet"
    if candidate_path.exists() or strategy_path.exists():
        raise FileExistsError(f"refusing to overwrite existing promotion grid: {output}")
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    (output / "reports").mkdir(parents=True, exist_ok=True)
    candidate_rows: list[dict[str, object]] = []
    strategy_rows: list[dict[str, object]] = []
    scenarios = tuple(
        scenario
        for scenario in SCENARIOS
        if not config.scenario_subset or scenario.name in config.scenario_subset
    )
    for scenario in scenarios:
        for replicate in range(config.seeds):
            seed = config.seed_offset + replicate
            print(
                f"promotion-grid scenario={scenario.name} replicate={replicate + 1}/{config.seeds} "
                f"seed={seed} device={config.device}",
                flush=True,
            )
            candidates, strategies = _evaluate_stream(scenario, seed, config)
            candidate_rows.extend(candidates)
            strategy_rows.extend(strategies)
    candidates_frame = pd.DataFrame(candidate_rows)
    strategies_frame = pd.DataFrame(strategy_rows)
    candidates_frame.to_parquet(candidate_path, index=False)
    strategies_frame.to_parquet(strategy_path, index=False)
    strategy_summary = strategies_frame.groupby(["scenario", "strategy"], as_index=False).agg(
        promotion_rate=("promoted", "mean"),
        expected_net_gain=("post_expected_net_gain_total", "mean"),
        realized_net_gain=("post_realized_net_gain_total", "mean"),
        false_post_nongain_rate=("false_promotion_post_nongain", "mean"),
        post_expected_cost=("post_mean_expected_cost", "mean"),
    )
    _write_figures(strategy_summary, output / "figures")

    report = [
        "# Forward-time certified candidate grid",
        "",
        f"Evaluated {len(scenarios)} synthetic scenarios with {config.seeds} independent streams each using `{config.device}` generation. The candidate grid contains one exact copy of the incumbent policy plus {len(config.regularization) * len(config.threshold_scales)} logistic-regression candidates per stream. Logistic candidates are fitted on the initial training slice, ranked by labeled validation net gain, frozen before a later shadow-evaluation slice, and only deployed on the final untouched slice.",
        "",
        f"The one-time switching charge is `{config.switching_cost:g}`. For certification against its value over the fixed {config.n - _time_splits(config.n)[2]}-event deployment horizon, it is amortized as `{config.switching_cost / (config.n - _time_splits(config.n)[2]):.8f}` per candidate evaluation event. The deployment metric subtracts the full one-time charge once. Candidate index `i` receives `alpha_i=alpha/[i(i+1)]`; because the grid is ordered by validation score before monitoring and every candidate is tested on fresh feedback, the sum of test levels is at most `alpha` for every realized candidate ordering. The fixed-horizon comparison uses a one-sided Azuma-Hoeffding threshold with the same candidate-specific alpha allocation.",
        "",
        "The sequential certificate is absorbing: after the first `e_t >= 1/alpha_i` crossing it remains certified even if later e-values decline. The statistical gate certifies a mean shadow-period improvement under its conditional-mean and bounded-cost assumptions. It does not guarantee benefit on the later deployment slice if the regime changes. `false_post_nongain` explicitly measures such deployment reversals and is not the same as a false statistical certification. Both action costs are observable on the same synthetic outcome; settings where actions affect outcomes require randomized or off-policy evaluation.",
        "",
        "## Untouched deployment performance by controller",
        "",
        "Positive net gain means lower decision cost than retaining the incumbent, after the one-time switching charge. Rates and averages use independent seeds as the unit.",
        "",
        "| Scenario | Strategy | Promotion rate | Mean expected net gain | Mean realized net gain | Post-promotion nongain rate |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in strategy_summary.itertuples(index=False):
        report.append(
            f"| {row.scenario} | {row.strategy} | {row.promotion_rate:.3f} | {row.expected_net_gain:.4f} | {row.realized_net_gain:.4f} | {row.false_post_nongain_rate:.3f} |"
        )

    exact_null = candidates_frame[candidates_frame.exact_policy_copy_null]
    false_exact = int(exact_null.null_candidate_false_certificate.sum())
    if len(exact_null):
        false_low, false_high = _wilson(false_exact, len(exact_null))
        exact_text = f"{false_exact}/{len(exact_null)} [{false_low:.3f},{false_high:.3f}]"
    else:
        exact_text = "not observed in selected scenarios"
    report.extend(
        [
            "",
            f"Exact-copy null candidate certificates: `{exact_text}` over candidate-stream tests where the tested action exactly matches the incumbent throughout the shadow interval; its net gain is pointwise negative from the positive switching charge. This simulation is a diagnostic; the familywise guarantee follows from valid candidate e-processes and alpha spending under their stated assumptions.",
            "",
            "## Reproduction",
            "",
            f"`uv run shiftlab-dive-promotion-grid --seeds {config.seeds} --seed-offset {config.seed_offset} --device {config.device} --output {output.as_posix()}`",
            "",
            "The candidate-level Parquet preserves validation ranking, candidate alpha, sequential and fixed-horizon certification, evaluator-known shadow gain, exact-copy null status, and untouched post-promotion outcomes. The strategy-level Parquet contains the paired deployment outcomes for no promotion, unconditional promotion, fixed-horizon certification, and sequential certification.",
        ]
    )
    report_path = output / "reports/promotion_grid_comparison.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "forward_time_certified_candidate_grid",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": asdict(config),
        "requested_device": requested_device,
        "resolved_device": config.device,
        "environment": environment(),
        "scenarios": [scenario.name for scenario in scenarios],
        "candidate_count_per_stream": 1 + len(config.regularization) * len(config.threshold_scales),
        "strategies": [
            "never_promote",
            "validation_always_promote",
            "fixed_horizon_grid_gate",
            "sequential_grid_gate",
        ],
        "information_protocol": [
            "candidate models fitted on training labels only",
            "candidate ranking and alpha-spending order frozen on validation before monitor",
            "shadow test uses immediate full feedback and paired common-outcome costs",
            "sequential certification persists after its first threshold crossing",
            "deployment outcomes use a later untouched slice",
        ],
    }
    (output / "reports/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/promotion_grid_corrected"))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20381023)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--switching-cost", type=float, default=0.05)
    parser.add_argument("--scenarios", nargs="+", choices=[s.name for s in SCENARIOS])
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args(argv)
    config = PromotionGridConfig(
        n=args.n,
        d=args.d,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        switching_cost=args.switching_cost,
        scenario_subset=tuple(args.scenarios or ()),
        device=args.device,
    )
    print(run_promotion_grid(config, args.output), flush=True)


if __name__ == "__main__":
    main()
