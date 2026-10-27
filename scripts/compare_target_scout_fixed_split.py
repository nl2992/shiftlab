"""Matched development comparison of Target-Scout and fixed sample-split certification."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate
from shiftlab.dive.budgeted_promotion import (
    BudgetedPromotionConfig,
    _fit_candidate_family,
    _inject_context_heterogeneity,
    _monitor_family,
    _monitor_scout_context_policy,
    _monitor_validation_context_policy,
    _query_uniform_matrix,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/target_scout_fixed_split_protocol.md"
OUTPUT_DEFAULT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_dev_v1"
)
PREVALENCES = (0.10, 0.50, 0.90)
SIGNALS = (0.0, 0.05, 0.10)
PROXY_ERRORS = (0.0, 0.10, 0.25)
METHODS = ("pooled_rank", "fixed_sample_split", "target_scout")
SEED_BOOTSTRAP = 2026102601
BOOTSTRAP_DRAWS = 10_000
ALPHA = 0.05
BUDGET_RATE = 0.40
PRACTICAL_MARGIN = 1.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cell(prevalence: float, signal: float, error: float) -> str:
    return f"context_p{round(100 * prevalence):02d}_delta{round(1000 * signal):03d}_error{round(100 * error):02d}"


def _stream_for_seed(
    *, seed: int, config: BudgetedPromotionConfig, device: str, scenario: SimpleNamespace
) -> tuple[dict[str, object], np.ndarray, np.ndarray, np.ndarray]:
    source_config = ExperimentConfig(
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
        device=device,
    )
    _, frame, oracle, _ = _generate(SCENARIOS[0], seed, source_config)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = (frame.target.to_numpy(dtype=float) > 0).astype(int)
    probability_true = oracle.probability_positive.to_numpy(dtype=float)
    x, y, probability_true = _inject_context_heterogeneity(
        x=x,
        y=y,
        probability_true=probability_true,
        seed=seed,
        config=config,
        device=device,
        fn_cost=float(scenario.fn_cost),
        fp_cost=float(scenario.fp_cost),
    )
    family = _fit_candidate_family(
        x=x,
        y=y,
        probability_true=probability_true,
        scenario=scenario,
        config=config,
    )
    uniforms = _query_uniform_matrix(
        seed=seed + 700_001,
        query_policy_count=1,
        horizon=int(family["monitor_length"]),
        device=device,
        shared=config.shared_query_randomness,
    )[0]
    return family, y, uniforms, x


def _make_config(
    *, n: int, d: int, seed: int, prevalence: float, signal: float, error: float, device: str
) -> BudgetedPromotionConfig:
    return BudgetedPromotionConfig(
        n=n,
        d=d,
        seeds=1,
        seed_offset=seed,
        alpha=ALPHA,
        switching_cost=0.05,
        budget_rates=(BUDGET_RATE,),
        query_policies=("uniform",),
        shared_query_randomness=True,
        alpha_allocations=("rank",),
        estimators=("direct_ipw",),
        monitoring_rules=("fixed_mixture",),
        bound_mode="global",
        context_feature_index=d - 1,
        context_threshold=0.0,
        context_target_prevalence=prevalence,
        context_signal_strength=signal,
        context_proxy_error=error,
        include_validation_context_policy=False,
        include_scout_context_policy=False,
        scenario_subset=("candidate_context_heterogeneity",),
        create_plot=False,
        device=device,
    ).validate()


def _macro_contrasts(detail: pd.DataFrame, *, draws: int) -> pd.DataFrame:
    positive = sorted(detail.loc[detail["signal"].gt(0), "scenario"].unique())
    seeds = np.sort(detail["seed"].unique())
    expected_cells = 18
    if len(positive) != expected_cells or len(seeds) < 2:
        raise ValueError("incomplete positive-signal cell or seed block")
    contrasts = (
        ("target_scout_minus_fixed_sample_split", "fixed_sample_split"),
        ("target_scout_minus_pooled_rank", "pooled_rank"),
    )
    rng = np.random.default_rng(SEED_BOOTSTRAP)
    output: list[dict[str, object]] = []
    for contrast, comparator in contrasts:
        matrix = np.empty((len(positive), len(seeds)), dtype=float)
        for cell_index, scenario in enumerate(positive):
            cell = detail.loc[detail["scenario"].eq(scenario)]
            wide = cell.pivot(
                index="seed", columns="method", values="expected_postpromotion_net_gain"
            )
            wide = wide.reindex(index=seeds)
            if wide[list(METHODS)].isna().any().any():
                raise ValueError(f"unmatched stream rows in {scenario}")
            matrix[cell_index] = wide["target_scout"].to_numpy(dtype=float) - wide[
                comparator
            ].to_numpy(dtype=float)
        boot = np.empty(draws, dtype=float)
        for start in range(0, draws, 100):
            stop = min(draws, start + 100)
            index = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            boot[start:stop] = np.take(matrix, index, axis=1).mean(axis=(0, 2))
        output.append(
            {
                "contrast": contrast,
                "metric": "expected_postpromotion_net_gain",
                "positive_signal_cells": len(positive),
                "matched_seed_blocks": len(seeds),
                "mean_paired_difference": float(matrix.mean()),
                "simultaneous_ci_level": 0.975,
                "bootstrap_ci_low": float(np.quantile(boot, 0.0125)),
                "bootstrap_ci_high": float(np.quantile(boot, 0.9875)),
                "practical_margin": PRACTICAL_MARGIN,
                "bootstrap_draws": draws,
                "bootstrap_seed": SEED_BOOTSTRAP,
            }
        )
    return pd.DataFrame(output)


def run(
    *,
    seeds: int,
    seed_offset: int,
    device: str,
    output: Path,
    n: int = 3200,
    d: int = 16,
    bootstrap_draws: int = BOOTSTRAP_DRAWS,
) -> dict[str, object]:
    if seeds < 2 or seed_offset < 20_265_000 or n < 1000 or d < 3:
        raise ValueError("seed count, fresh seed block, n, or d is invalid")
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    resolved = resolve_device(device, n=n, d=d, chunk_size=2048)
    if resolved != "cuda":
        raise RuntimeError(f"frozen protocol requires CUDA; resolved device is {resolved}")
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / ".partial_streams.parquet"
    state_path = output / ".run_state.json"
    run_signature = {
        "seeds": seeds,
        "seed_offset": seed_offset,
        "device": resolved,
        "n": n,
        "d": d,
        "protocol_sha256": _sha256(PROTOCOL),
        "runner_sha256": _sha256(Path(__file__).resolve()),
    }
    rows: list[dict[str, object]] = []
    completed_cells: set[str] = set()
    existing = {path.name for path in output.iterdir()}
    if existing and not existing.issubset({checkpoint_path.name, state_path.name}):
        raise FileExistsError(f"refusing to overwrite output: {output}")
    if checkpoint_path.exists() or state_path.exists():
        if not (checkpoint_path.is_file() and state_path.is_file()):
            raise RuntimeError("incomplete checkpoint pair; preserve it and inspect manually")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("run_signature") != run_signature:
            raise RuntimeError("checkpoint configuration differs from this frozen run")
        rows = pd.read_parquet(checkpoint_path).to_dict(orient="records")
        saved_cells = set(state.get("completed_cells", []))
        cell_counts = pd.DataFrame(rows)["scenario"].value_counts().to_dict()
        if any(count != seeds * len(METHODS) for count in cell_counts.values()):
            raise RuntimeError("checkpoint contains an incomplete scenario cell")
        completed_cells = set(cell_counts)
        if not saved_cells.issubset(completed_cells):
            raise RuntimeError("checkpoint rows do not match completed-cell metadata")
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    for prevalence in PREVALENCES:
        for signal in SIGNALS:
            for error in PROXY_ERRORS:
                cell = _cell(prevalence, signal, error)
                if cell in completed_cells:
                    continue
                print(f"cell={cell}; seeds={seeds}; device={resolved}", flush=True)
                for seed in range(seed_offset, seed_offset + seeds):
                    base = _make_config(
                        n=n,
                        d=d,
                        seed=seed,
                        prevalence=prevalence,
                        signal=signal,
                        error=error,
                        device=resolved,
                    )
                    family, y, uniforms, _ = _stream_for_seed(
                        seed=seed, config=base, device=resolved, scenario=scenario
                    )
                    pooled = _monitor_family(
                        family=family,
                        y=y,
                        scenario=scenario,
                        config=base,
                        query_name="uniform",
                        budget_rate=BUDGET_RATE,
                        estimator="direct_ipw",
                        query_uniforms=uniforms,
                        bound_mode="global",
                        monitoring_rule="fixed_mixture",
                    )[0]
                    fixed_config = replace(base, include_validation_context_policy=True).validate()
                    fixed = _monitor_validation_context_policy(
                        family=family,
                        y=y,
                        scenario=scenario,
                        config=fixed_config,
                        query_name="uniform",
                        budget_rate=BUDGET_RATE,
                        query_uniforms=uniforms,
                    )
                    scout_config = replace(base, include_scout_context_policy=True).validate()
                    scout = _monitor_scout_context_policy(
                        family=family,
                        y=y,
                        scenario=scenario,
                        config=scout_config,
                        query_name="uniform",
                        budget_rate=BUDGET_RATE,
                        query_uniforms=uniforms,
                    )
                    for method, result in zip(METHODS, (pooled, fixed, scout), strict=True):
                        result = dict(result)
                        result["scenario"] = cell
                        result["method"] = method
                        result["seed"] = seed
                        result["context_target_prevalence"] = prevalence
                        result["context_signal_strength"] = signal
                        result["context_proxy_error"] = error
                        result["signal"] = signal
                        rows.append(result)
                temporary_checkpoint = output / ".partial_streams.parquet.tmp"
                pd.DataFrame(rows).to_parquet(temporary_checkpoint, index=False)
                temporary_checkpoint.replace(checkpoint_path)
                completed_cells.add(cell)
                temporary_state = output / ".run_state.json.tmp"
                temporary_state.write_text(
                    json.dumps(
                        {
                            "run_signature": run_signature,
                            "completed_cells": sorted(completed_cells),
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                temporary_state.replace(state_path)

    detail = pd.DataFrame(rows)
    expected_rows = seeds * len(PREVALENCES) * len(SIGNALS) * len(PROXY_ERRORS) * len(METHODS)
    if len(detail) != expected_rows or detail.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("stream output is incomplete or duplicated")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("a method exceeded its pathwise label cap")
    if not detail["label_budget"].eq(detail["label_budget"].iloc[0]).all():
        raise RuntimeError("methods did not receive common label-budget ceilings")
    summary = detail.groupby(["scenario", "signal", "method"], as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        harmful_promotion_rate=("harmful_postpromotion_promotion", "mean"),
        expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        realized_future_net_gain=("realized_postpromotion_net_gain", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_monitor_events=("monitor_events_processed", "mean"),
        mean_certification_fraction=("certification_fraction_processed", "mean"),
    )
    contrasts = _macro_contrasts(detail, draws=bootstrap_draws)
    detail.to_csv(output / "streams.csv", index=False)
    detail.to_parquet(output / "streams.parquet", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    summary.to_parquet(output / "summary.parquet", index=False)
    contrasts.to_csv(output / "primary_contrasts.csv", index=False)
    contrasts.to_parquet(output / "primary_contrasts.parquet", index=False)
    report = [
        "# Target-Scout versus fixed-split development comparison",
        "",
        f"**Status:** exploratory matched development; {seeds} seeds per 27 cells, seed block {seed_offset}–{seed_offset + seeds - 1}, device `{resolved}`.",
        "",
        "The fixed sample-split selector chooses a context-to-candidate mapping from source validation and tests it on the independent full target monitor. Target-Scout uses the first half of the target monitor to choose the mapping and the second half to certify it. Pooled rank monitors its validation-ranked candidate family. All share the same generated stream, label ceiling, query uniforms, costs, and deployment start. The equal-cell primary estimand averages the 18 positive-signal cells; the zero-signal cells are controls.",
        "",
        "| Target-Scout contrast | Mean paired expected future net gain | Simultaneous 97.5% interval | Margin |",
        "|---|---:|---:|---:|",
    ]
    for row in contrasts.itertuples(index=False):
        report.append(
            f"| {row.contrast} | {row.mean_paired_difference:.3f} | "
            f"[{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}] | {row.practical_margin:.1f} |"
        )
    report.extend(
        [
            "",
            "The registered practical threshold is +1.0 cumulative utility unit. This development run does not establish a new null guarantee or general superiority; no confirmation is authorized by these metrics alone. Compare the paired estimates, intervals, cap use, and promotion harms in the CSV/Parquet outputs.",
            "",
            f"Frozen protocol SHA-256: `{_sha256(PROTOCOL)}`.",
        ]
    )
    (output / "results.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest: dict[str, object] = {
        "experiment": "target_scout_fixed_split_matched_development",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "exploratory_matched_development",
        "protocol": {"path": PROTOCOL.relative_to(ROOT).as_posix(), "sha256": _sha256(PROTOCOL)},
        "configuration": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device_requested": device,
            "device_resolved": resolved,
            "prevalences": PREVALENCES,
            "signals": SIGNALS,
            "proxy_errors": PROXY_ERRORS,
            "methods": METHODS,
            "budget_rate": BUDGET_RATE,
            "alpha": ALPHA,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_seed": SEED_BOOTSTRAP,
            "practical_margin": PRACTICAL_MARGIN,
            "common_stream_and_query_uniforms": True,
        },
        "source_hashes": {
            "runner": _sha256(Path(__file__).resolve()),
            "budgeted_promotion": _sha256(ROOT / "src/shiftlab/dive/budgeted_promotion.py"),
        },
        "environment": environment(),
        "rows": len(detail),
        "primary_contrasts": contrasts.to_dict(orient="records"),
        "artifacts": {},
    }
    for name in (
        "streams.csv",
        "streams.parquet",
        "summary.csv",
        "summary.parquet",
        "primary_contrasts.csv",
        "primary_contrasts.parquet",
        "results.md",
    ):
        manifest["artifacts"][name] = _sha256(output / name)  # type: ignore[index]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    checkpoint_path.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    print(f"rows={len(detail)}; output={output}", flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=20_265_000)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    args = parser.parse_args()
    run(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
        output=args.output,
        n=args.n,
        d=args.d,
        bootstrap_draws=args.bootstrap_draws,
    )


if __name__ == "__main__":
    main()
