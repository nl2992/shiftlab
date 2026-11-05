"""Compare the contextual scout with finite-class OPI on IID-context streams."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.dive.budgeted_promotion import BudgetedPromotionConfig, _run_seed
from shiftlab.dive.experiment import finalize_manifest

PREVALENCES = (0.10, 0.50, 0.90)
SIGNALS = (0.0, 0.05, 0.10)
PROXY_ERRORS = (0.0, 0.25)
BUDGET_RATES = (0.20, 0.40)
SCENARIO = SimpleNamespace(
    name="candidate_context_heterogeneity", fn_cost=5.0, fp_cost=1.0, harmful_adaptation=False
)
METHODS = {
    "rank",
    "rank_context_volume",
    "scout_context_policy_eventwise_propensity_bound",
}
SEED_BLOCK_START = 22_000_000
MIN_SEEDS = 60


def _cell_name(prevalence: float, signal: float, proxy_error: float) -> str:
    return (
        f"iid_p{round(100 * prevalence):02d}_delta{round(1000 * signal):03d}_"
        f"error{round(100 * proxy_error):02d}"
    )


def _run_profile(
    args: tuple[int, BudgetedPromotionConfig, str, float, float, float],
) -> list[dict[str, object]]:
    seed, config, device, prevalence, signal, proxy_error = args
    rows = _run_seed(
        scenario=SCENARIO,
        seed=seed,
        config=config,
        device=device,
        scout_bound_modes=("eventwise_propensity",),
    )
    selected = [row for row in rows if row["alpha_allocation"] in METHODS]
    if len(selected) != len(METHODS) * len(BUDGET_RATES):
        raise RuntimeError("IID OPI stream is missing a selection method or budget")
    scenario_name = _cell_name(prevalence, signal, proxy_error)
    for row in selected:
        row["scenario"] = scenario_name
        row["context_target_prevalence"] = prevalence
        row["context_persistence"] = 0.0
        row["context_signal_strength"] = signal
        row["context_proxy_error"] = proxy_error
        row["seed"] = seed
    return selected


def run(
    *,
    output: Path,
    protocol: Path,
    seeds: int,
    seed_offset: int,
    n: int,
    d: int,
    device: str,
    workers: int,
) -> Path:
    if seeds < MIN_SEEDS or seed_offset < SEED_BLOCK_START or n < 1000 or d < 3 or workers < 1:
        raise ValueError(
            "full IID OPI development requires >=60 seeds, a fresh block, n>=1000, d>=3, workers>=1"
        )
    if not protocol.is_file():
        raise FileNotFoundError(protocol)
    resolved_device = resolve_device(device, n=n, d=d, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    children = list(output.iterdir())
    if any(
        child.name not in {"metrics", "reports"} or not child.is_dir() or any(child.iterdir())
        for child in children
    ):
        raise FileExistsError(f"refusing to overwrite nonempty output {output}")
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    thread_variables = (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    )
    previous = {key: os.environ.get(key) for key in thread_variables}
    if workers > 1:
        os.environ.update({key: "1" for key in thread_variables})
    jobs: list[tuple[int, BudgetedPromotionConfig, str, float, float, float]] = []
    for prevalence in PREVALENCES:
        for signal in SIGNALS:
            for proxy_error in PROXY_ERRORS:
                config = BudgetedPromotionConfig(
                    n=n,
                    d=d,
                    seeds=1,
                    seed_offset=seed_offset,
                    switching_cost=0.05,
                    budget_rates=BUDGET_RATES,
                    query_policies=("uniform",),
                    alpha_allocations=("rank", "rank_context_volume"),
                    estimators=("direct_ipw",),
                    monitoring_rules=("fixed_mixture",),
                    bound_mode="global",
                    context_feature_index=d - 1,
                    context_threshold=0.0,
                    context_target_prevalence=prevalence,
                    context_signal_strength=signal,
                    context_proxy_error=proxy_error,
                    context_persistence=0.0,
                    include_scout_context_policy=True,
                    include_scout_opi=True,
                    exact_uniform_propensity_floor=True,
                    scout_ope_reward_predictor="constant_half",
                    scenario_subset=("candidate_context_heterogeneity",),
                    create_plot=False,
                    device=resolved_device,
                ).validate()
                for replicate in range(seeds):
                    jobs.append(
                        (
                            seed_offset + replicate,
                            config,
                            resolved_device,
                            prevalence,
                            signal,
                            proxy_error,
                        )
                    )

    records: list[dict[str, object]] = []
    pool_context = ProcessPoolExecutor(max_workers=workers) if workers > 1 else nullcontext(None)
    try:
        with pool_context as executor:
            if executor is None:
                for job in jobs:
                    records.extend(_run_profile(job))
            else:
                futures = [executor.submit(_run_profile, job) for job in jobs]
                for done, future in enumerate(as_completed(futures), start=1):
                    records.extend(future.result())
                    if done % 100 == 0 or done == len(futures):
                        print(f"scout-opi-iid progress={done}/{len(futures)}", flush=True)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    detail = pd.DataFrame.from_records(records)
    expected_rows = (
        seeds
        * len(PREVALENCES)
        * len(SIGNALS)
        * len(PROXY_ERRORS)
        * len(BUDGET_RATES)
        * len(METHODS)
    )
    if len(detail) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows, received {len(detail)}")
    key = ["scenario", "budget_rate", "seed", "alpha_allocation"]
    if detail.duplicated(key).any():
        raise RuntimeError("duplicate method/cell/seed rows")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("hard label budget exceeded")
    scout = detail.loc[
        detail["alpha_allocation"].eq("scout_context_policy_eventwise_propensity_bound")
    ]
    if (
        scout[["opi_lil_promoted", "opi_lil_candidate_count", "opi_lil_labels_used"]]
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError("missing OPI fields on scout rows")
    detail.to_parquet(metrics_dir / "scout_opi_iid_streams.parquet", index=False)
    protocol_hash = hashlib.sha256(protocol.read_bytes()).hexdigest()
    report = [
        "# Finite-class OPI versus contextual scout on IID contexts",
        "",
        f"Exploratory development only. Seeds {seed_offset}–{seed_offset + seeds - 1}; rows {len(detail):,}; device {resolved_device}.",
        "",
        f"Protocol SHA-256: `{protocol_hash}`. Hard-cap violations: 0.",
        "",
        "The four-policy OPI class contains incumbent, pooled rank, validation-context, and scout-context mappings, with duplicate mappings removed per stream. OPI deploys only after a unique policy is identified. The finite-value theorem is applied only to IID-context profiles.",
        "",
        "The generated `metrics/scout_opi_iid_streams.parquet` retains the full matched rows; the paired analysis script supplies promotion and utility contrasts.",
    ]
    report_path = reports_dir / "scout_opi_iid_development.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {
        "experiment": "scout_vs_finite_class_opi_iid_context_development",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "exploratory_development",
        "protocol": {"path": protocol.as_posix(), "sha256": protocol_hash},
        "configuration": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "seed_end_inclusive": seed_offset + seeds - 1,
            "n": n,
            "d": d,
            "device": resolved_device,
            "workers": workers,
            "prevalences": PREVALENCES,
            "persistence": 0.0,
            "signals": SIGNALS,
            "proxy_errors": PROXY_ERRORS,
            "budget_rates": BUDGET_RATES,
            "alpha": 0.05,
            "query_policy": "uniform",
            "exact_uniform_propensity_floor": True,
            "opi_candidate_class": "deduplicated incumbent/rank/validation-context/scout-context mappings",
            "opi_candidate_count_range": [
                int(scout.opi_lil_candidate_count.min()),
                int(scout.opi_lil_candidate_count.max()),
            ],
        },
        "inference": {
            "expected_rows": expected_rows,
            "actual_rows": len(detail),
            "duplicate_keys": 0,
            "cap_violations": 0,
            "null_streams": int(scout.context_signal_strength.eq(0).sum()),
            "positive_streams": int(scout.context_signal_strength.gt(0).sum()),
            "confirmatory": False,
            "null_calibration": False,
        },
        "artifacts": [
            "metrics/scout_opi_iid_streams.parquet",
            "reports/scout_opi_iid_development.md",
        ],
        "environment": environment(),
    }
    (reports_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(output)
    print(report_path, flush=True)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/scout_opi_iid_development_v1"))
    parser.add_argument(
        "--protocol", type=Path, default=Path("docs/scout_opi_iid_development_protocol_v1.md")
    )
    parser.add_argument("--seeds", type=int, default=MIN_SEEDS)
    parser.add_argument("--seed-offset", type=int, default=SEED_BLOCK_START)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cpu")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    print(
        run(
            output=args.output,
            protocol=args.protocol,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            n=args.n,
            d=args.d,
            device=args.device,
            workers=args.workers,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
