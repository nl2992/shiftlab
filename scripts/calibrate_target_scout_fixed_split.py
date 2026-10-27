"""Fresh null calibration for the fixed-split, Target-Scout, and pooled-rank rules."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from compare_target_scout_fixed_split import (
    ALPHA,
    BUDGET_RATE,
    METHODS,
    PREVALENCES,
    PROXY_ERRORS,
    _make_config,
    _stream_for_seed,
)
from scipy.stats import beta

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.dive.budgeted_promotion import (
    _monitor_family,
    _monitor_scout_context_policy,
    _monitor_validation_context_policy,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/target_scout_fixed_split_null_calibration_protocol.md"
OUT_DEFAULT = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1"
)
SIGNAL = 0.0
SWITCHING_COST = 0.05
FAMILYWISE_ALPHA = 0.05
STRATA = len(PREVALENCES) * len(PROXY_ERRORS) * len(METHODS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_name(prevalence: float, error: float) -> str:
    return f"context_p{round(100 * prevalence):02d}_delta000_error{round(100 * error):02d}"


def evaluate(
    seed: int, prevalence: float, error: float, device: str, n: int, d: int
) -> list[dict[str, object]]:
    config = _make_config(
        n=n, d=d, seed=seed, prevalence=prevalence, signal=SIGNAL, error=error, device=device
    )
    config = config.__class__(**{**config.__dict__, "switching_cost": SWITCHING_COST}).validate()
    family, y, uniforms, _ = _stream_for_seed(
        seed=seed,
        config=config,
        device=device,
        scenario=SimpleNamespace(
            name="candidate_context_heterogeneity",
            fn_cost=5.0,
            fp_cost=1.0,
            harmful_adaptation=False,
        ),
    )
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    pooled = _monitor_family(
        family=family,
        y=y,
        scenario=scenario,
        config=config,
        query_name="uniform",
        budget_rate=BUDGET_RATE,
        estimator="direct_ipw",
        query_uniforms=uniforms,
        bound_mode="global",
        monitoring_rule="fixed_mixture",
    )[0]
    fixed_config = config.__class__(
        **{**config.__dict__, "include_validation_context_policy": True}
    ).validate()
    fixed = _monitor_validation_context_policy(
        family=family,
        y=y,
        scenario=scenario,
        config=fixed_config,
        query_name="uniform",
        budget_rate=BUDGET_RATE,
        query_uniforms=uniforms,
    )
    scout_config = config.__class__(
        **{**config.__dict__, "include_scout_context_policy": True}
    ).validate()
    scout = _monitor_scout_context_policy(
        family=family,
        y=y,
        scenario=scenario,
        config=scout_config,
        query_name="uniform",
        budget_rate=BUDGET_RATE,
        query_uniforms=uniforms,
    )
    rows: list[dict[str, object]] = []
    for method, raw in zip(METHODS, (pooled, fixed, scout), strict=True):
        row = dict(raw)
        row.update(
            {
                "scenario": cell_name(prevalence, error),
                "method": method,
                "seed": seed,
                "context_target_prevalence": prevalence,
                "context_signal_strength": SIGNAL,
                "context_proxy_error": error,
                "signal": SIGNAL,
                "null_expected_gain_nonpositive": True,
            }
        )
        rows.append(row)
    return rows


def upper_cp(events: int, trials: int, alpha: float) -> float:
    if trials < 1 or events < 0 or events > trials:
        raise ValueError("invalid binomial counts")
    return 1.0 if events == trials else float(beta.ppf(1 - alpha, events + 1, trials - events))


def run(
    *, seeds: int, seed_offset: int, device: str, output: Path, n: int, d: int, smoke: bool
) -> dict[str, object]:
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    if smoke:
        if seeds != 2:
            raise ValueError("smoke mode is fixed at two seeds")
    elif seeds != 1000 or seed_offset != 99_000_000:
        raise ValueError("frozen calibration requires exactly 1,000 seeds from 99,000,000")
    resolved = resolve_device(device, n=n, d=d, chunk_size=2048)
    if resolved != "cuda":
        raise RuntimeError(f"frozen calibration requires CUDA, resolved {resolved}")
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / ".partial_streams.parquet"
    state_path = output / ".run_state.json"
    allowed = {checkpoint.name, state_path.name}
    existing = {path.name for path in output.iterdir()}
    if existing and not existing.issubset(allowed):
        raise FileExistsError(f"refusing to overwrite output directory {output}")
    signature = {
        "seeds": seeds,
        "seed_offset": seed_offset,
        "n": n,
        "d": d,
        "device": resolved,
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "smoke": smoke,
    }
    rows: list[dict[str, object]] = []
    completed: set[str] = set()
    if checkpoint.exists() or state_path.exists():
        if not (checkpoint.is_file() and state_path.is_file()):
            raise RuntimeError("incomplete checkpoint pair; inspect manually")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("signature") != signature:
            raise RuntimeError("checkpoint does not match frozen configuration")
        rows = pd.read_parquet(checkpoint).to_dict(orient="records")
        completed = set(state.get("completed_cells", []))
        if any(
            len([r for r in rows if r["scenario"] == cell]) != seeds * len(METHODS)
            for cell in completed
        ):
            raise RuntimeError("checkpoint has incomplete completed-cell records")

    total_done = len(rows) // len(METHODS)
    for prevalence in PREVALENCES:
        for error in PROXY_ERRORS:
            cell = cell_name(prevalence, error)
            if cell in completed:
                continue
            existing_seeds = {int(str(row["seed"])) for row in rows if row["scenario"] == cell}
            for offset in range(seeds):
                seed = seed_offset + offset
                if seed in existing_seeds:
                    continue
                rows.extend(evaluate(seed, prevalence, error, resolved, n, d))
                total_done += 1
                if total_done % 25 == 0 or offset == seeds - 1:
                    temp = output / ".partial_streams.parquet.tmp"
                    pd.DataFrame(rows).to_parquet(temp, index=False)
                    temp.replace(checkpoint)
                    state = {"signature": signature, "completed_cells": sorted(completed)}
                    state_temp = output / ".run_state.json.tmp"
                    state_temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
                    state_temp.replace(state_path)
                    print(
                        f"completed_seed_cells={total_done}/{seeds * len(PREVALENCES) * len(PROXY_ERRORS)}",
                        flush=True,
                    )
            completed.add(cell)
            temp = output / ".partial_streams.parquet.tmp"
            pd.DataFrame(rows).to_parquet(temp, index=False)
            temp.replace(checkpoint)
            state_path.write_text(
                json.dumps(
                    {"signature": signature, "completed_cells": sorted(completed)}, indent=2
                ),
                encoding="utf-8",
            )

    detail = pd.DataFrame(rows)
    expected = seeds * len(PREVALENCES) * len(PROXY_ERRORS) * len(METHODS)
    if len(detail) != expected or detail.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("incomplete or duplicate calibration rows")
    if set(detail["method"].unique()) != set(METHODS):
        raise RuntimeError("unexpected method set")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("pathwise label cap exceeded")
    label_matrix = detail.pivot(
        index=["scenario", "seed"], columns="method", values="labels_queried"
    )
    if label_matrix.nunique(axis=1).ne(1).any():
        raise RuntimeError("methods did not share queried-label counts")
    promoted = detail["promoted"].astype(bool)
    gains = detail.loc[promoted, "expected_postpromotion_net_gain"].to_numpy(dtype=float)
    if np.any(gains > 1e-9):
        raise RuntimeError("evaluator found a positive net-gain promotion under the null")
    if detail.loc[promoted, "harmful_postpromotion_promotion"].astype(bool).ne(True).any():
        raise RuntimeError("promotion harmfulness flag contradicts evaluator-known gain")

    per_stratum_alpha = FAMILYWISE_ALPHA / STRATA
    summary_rows: list[dict[str, object]] = []
    for (scenario_name, method), group in detail.groupby(["scenario", "method"], sort=True):
        count = int(group["promoted"].astype(bool).sum())
        upper = upper_cp(count, len(group), per_stratum_alpha)
        summary_rows.append(
            {
                "scenario": scenario_name,
                "method": method,
                "streams": len(group),
                "false_promotions": count,
                "promotion_rate": count / len(group),
                "one_sided_cp_upper": upper,
                "per_stratum_alpha": per_stratum_alpha,
                "calibration_cell_pass": bool(upper <= 0.05),
                "max_promoted_expected_net_gain": float(gains.max()) if len(gains) else 0.0,
            }
        )
    summary = pd.DataFrame(summary_rows)
    calibration_pass = bool(
        not smoke
        and summary["calibration_cell_pass"].all()
        and (detail["labels_queried"] <= detail["label_budget"]).all()
        and np.all(gains <= 1e-9)
    )
    status = "smoke_only" if smoke else ("passed" if calibration_pass else "failed")
    detail.to_csv(output / "streams.csv", index=False)
    detail.to_parquet(output / "streams.parquet", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    summary.to_parquet(output / "summary.parquet", index=False)
    report_lines = [
        "# Exact-rule Target-Scout null calibration",
        "",
        f"**Status:** `{status}`; {seeds} seeds per 9 cells; 27 method-by-cell strata; device `{resolved}`.",
        "",
        f"One-sided exact Clopper–Pearson upper limits use Bonferroni per-stratum alpha {per_stratum_alpha:.8f}.",
        "",
        "| Cell | Method | Promotions / streams | Rate | Simultaneous upper limit | Pass ≤ 0.05 |",
        "|---|---|---:|---:|---:|:---:|",
    ]
    for row in summary.to_dict(orient="records"):
        report_lines.append(
            f"| {row['scenario']} | {row['method']} | {row['false_promotions']} / {row['streams']} | "
            f"{row['promotion_rate']:.4f} | {row['one_sided_cp_upper']:.4f} | {row['calibration_cell_pass']} |"
        )
    report_lines.extend(
        [
            "",
            "The eventwise target probability equals the FN/FP Bayes threshold (1/6), so every candidate action has zero gross expected gain; the 0.05 switch charge makes any promoted policy nonpositive in evaluator-known net gain. This finite calibration applies only to the registered stationary DGP and monitor rules.",
            "",
            "No power or comparative superiority claim is supported by this calibration.",
        ]
    )
    report_path = output / "results.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    source_files = [
        Path(__file__).resolve(),
        ROOT / "scripts/compare_target_scout_fixed_split.py",
        ROOT / "src/shiftlab/dive/budgeted_promotion.py",
        ROOT / "src/shiftlab/decision_harm_experiment.py",
        ROOT / "src/shiftlab/data/gpu/environment.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        PROTOCOL,
    ]
    artifacts = {
        name: sha256(output / name)
        for name in (
            "streams.csv",
            "streams.parquet",
            "summary.csv",
            "summary.parquet",
            "results.md",
        )
    }
    manifest = {
        "experiment": "target_scout_fixed_split_exact_rule_null_calibration",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "configuration": signature
        | {
            "prevalences": PREVALENCES,
            "signals": [SIGNAL],
            "proxy_errors": PROXY_ERRORS,
            "methods": METHODS,
            "budget_rate": BUDGET_RATE,
            "alpha": ALPHA,
            "switching_cost": SWITCHING_COST,
            "familywise_alpha": FAMILYWISE_ALPHA,
            "simultaneous_strata": STRATA,
        },
        "inference": {
            "pass": calibration_pass,
            "all_cells_pass": bool(summary["calibration_cell_pass"].all()),
            "all_caps_respected": bool((detail["labels_queried"] <= detail["label_budget"]).all()),
            "positive_net_gain_promotions": int(np.sum(gains > 1e-9)),
            "conditional_null_analytically_verified": True,
        },
        "environment": environment(),
        "rows": len(detail),
        "source_hashes": {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_files},
        "artifacts": artifacts,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    checkpoint.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    print(json.dumps(manifest["inference"], indent=2), flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--seed-offset", type=int, default=99_000_000)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    parser.add_argument("--output", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument(
        "--smoke", action="store_true", help="run two seeds per cell; never counts as calibration"
    )
    args = parser.parse_args()
    run(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
        output=args.output,
        n=args.n,
        d=args.d,
        smoke=args.smoke,
    )


if __name__ == "__main__":
    main()
