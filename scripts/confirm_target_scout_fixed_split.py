"""Independent paired confirmation gated on the exact-rule null calibration."""

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
from compare_target_scout_fixed_split import (
    ALPHA,
    BUDGET_RATE,
    METHODS,
    PREVALENCES,
    PROXY_ERRORS,
    _make_config,
    _stream_for_seed,
)

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.dive.budgeted_promotion import (
    _monitor_family,
    _monitor_scout_context_policy,
    _monitor_validation_context_policy,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/target_scout_fixed_split_confirmation_protocol.md"
OUTPUT_DEFAULT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_confirmation_v1"
)
SIGNALS = (0.05, 0.10)
PRACTICAL_MARGIN = 1.0
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 2_026_102_699


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def name_cell(prevalence: float, signal: float, error: float) -> str:
    return f"context_p{round(100 * prevalence):02d}_delta{round(1000 * signal):03d}_error{round(100 * error):02d}"


def evaluate(
    seed: int, prevalence: float, signal: float, error: float, device: str, n: int, d: int
) -> list[dict[str, object]]:
    config = replace(
        _make_config(
            n=n, d=d, seed=seed, prevalence=prevalence, signal=signal, error=error, device=device
        ),
        switching_cost=0.05,
    ).validate()
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity", fn_cost=5.0, fp_cost=1.0, harmful_adaptation=False
    )
    family, y, uniforms, _ = _stream_for_seed(
        seed=seed, config=config, device=device, scenario=scenario
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
    fixed = _monitor_validation_context_policy(
        family=family,
        y=y,
        scenario=scenario,
        config=replace(config, include_validation_context_policy=True).validate(),
        query_name="uniform",
        budget_rate=BUDGET_RATE,
        query_uniforms=uniforms,
    )
    scout = _monitor_scout_context_policy(
        family=family,
        y=y,
        scenario=scenario,
        config=replace(config, include_scout_context_policy=True).validate(),
        query_name="uniform",
        budget_rate=BUDGET_RATE,
        query_uniforms=uniforms,
    )
    rows: list[dict[str, object]] = []
    for method, result in zip(METHODS, (pooled, fixed, scout), strict=True):
        row = dict(result)
        row.update(
            {
                "scenario": name_cell(prevalence, signal, error),
                "method": method,
                "seed": seed,
                "context_target_prevalence": prevalence,
                "context_signal_strength": signal,
                "context_proxy_error": error,
                "signal": signal,
            }
        )
        rows.append(row)
    return rows


def contrast_table(detail: pd.DataFrame) -> pd.DataFrame:
    cells = sorted(detail["scenario"].unique())
    seeds = np.sort(detail["seed"].unique())
    if len(cells) != 18 or len(seeds) != 300:
        raise RuntimeError("confirmation requires 18 cells and 300 seed blocks")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    results: list[dict[str, object]] = []
    for label, comparator in (
        ("target_scout_minus_fixed_sample_split", "fixed_sample_split"),
        ("target_scout_minus_pooled_rank", "pooled_rank"),
    ):
        paired = np.empty((len(cells), len(seeds)), dtype=float)
        for ci, cell in enumerate(cells):
            wide = (
                detail.loc[detail["scenario"].eq(cell)]
                .pivot(index="seed", columns="method", values="expected_postpromotion_net_gain")
                .reindex(seeds)
            )
            if wide[list(METHODS)].isna().any().any():
                raise RuntimeError(f"unmatched methods in {cell}")
            paired[ci] = wide["target_scout"].to_numpy() - wide[comparator].to_numpy()
        boot = np.empty(BOOTSTRAP_DRAWS)
        for start in range(0, BOOTSTRAP_DRAWS, 100):
            stop = min(BOOTSTRAP_DRAWS, start + 100)
            sample = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            boot[start:stop] = np.take(paired, sample, axis=1).mean(axis=(0, 2))
        lo, hi = np.quantile(boot, [0.0125, 0.9875])
        results.append(
            {
                "contrast": label,
                "metric": "expected_postpromotion_net_gain",
                "positive_signal_cells": len(cells),
                "matched_seed_blocks": len(seeds),
                "mean_paired_difference": float(paired.mean()),
                "simultaneous_ci_level": 0.975,
                "bootstrap_ci_low": float(lo),
                "bootstrap_ci_high": float(hi),
                "practical_margin": PRACTICAL_MARGIN,
                "material_benefit_confirmed": bool(lo > PRACTICAL_MARGIN),
                "bootstrap_draws": BOOTSTRAP_DRAWS,
                "bootstrap_seed": BOOTSTRAP_SEED,
            }
        )
    return pd.DataFrame(results)


def run(
    *,
    seeds: int,
    seed_offset: int,
    device: str,
    calibration: Path,
    output: Path,
    n: int = 3200,
    d: int = 16,
) -> dict[str, object]:
    if seeds != 300 or seed_offset != 99_010_000:
        raise ValueError("frozen confirmation requires 300 seeds beginning at 99,010,000")
    if not PROTOCOL.is_file() or not calibration.is_file():
        raise FileNotFoundError("protocol or calibration manifest is missing")
    cal = json.loads(calibration.read_text(encoding="utf-8"))
    if cal.get(
        "experiment"
    ) != "target_scout_fixed_split_exact_rule_null_calibration" or not cal.get("inference", {}).get(
        "pass", False
    ):
        raise RuntimeError("exact-rule null calibration did not pass; confirmation is gated off")
    resolved = resolve_device(device, n=n, d=d, chunk_size=2048)
    if resolved != "cuda":
        raise RuntimeError(f"frozen protocol requires CUDA, resolved {resolved}")
    output.mkdir(parents=True, exist_ok=True)
    checkpoint, state_path = output / ".partial_streams.parquet", output / ".run_state.json"
    if {p.name for p in output.iterdir()} - {checkpoint.name, state_path.name}:
        raise FileExistsError(f"refusing to overwrite {output}")
    signature = {
        "seeds": seeds,
        "seed_offset": seed_offset,
        "n": n,
        "d": d,
        "device": resolved,
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "calibration_manifest_sha256": sha256(calibration),
    }
    rows: list[dict[str, object]] = []
    if checkpoint.exists() or state_path.exists():
        if not checkpoint.is_file() or not state_path.is_file():
            raise RuntimeError("incomplete checkpoint pair; inspect manually")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("signature") != signature:
            raise RuntimeError("checkpoint does not match frozen configuration")
        rows = pd.read_parquet(checkpoint).to_dict(orient="records")
    done = len(rows) // len(METHODS)
    for prevalence in PREVALENCES:
        for signal in SIGNALS:
            for error in PROXY_ERRORS:
                cell = name_cell(prevalence, signal, error)
                present = {int(str(r["seed"])) for r in rows if r["scenario"] == cell}
                for i in range(seeds):
                    seed = seed_offset + i
                    if seed in present:
                        continue
                    rows.extend(evaluate(seed, prevalence, signal, error, resolved, n, d))
                    done += 1
                    if done % 25 == 0 or i == seeds - 1:
                        tmp = output / ".partial_streams.parquet.tmp"
                        pd.DataFrame(rows).to_parquet(tmp, index=False)
                        tmp.replace(checkpoint)
                        stmp = output / ".run_state.json.tmp"
                        stmp.write_text(
                            json.dumps({"signature": signature}, indent=2), encoding="utf-8"
                        )
                        stmp.replace(state_path)
                        print(f"completed_seed_cells={done}/{seeds * 18}", flush=True)
    detail = pd.DataFrame(rows)
    if (
        len(detail) != seeds * 18 * len(METHODS)
        or detail.duplicated(["scenario", "seed", "method"]).any()
    ):
        raise RuntimeError("incomplete or duplicate result rows")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("pathwise label cap exceeded")
    label_counts = detail.pivot(
        index=["scenario", "seed"], columns="method", values="labels_queried"
    )
    if label_counts.nunique(axis=1).ne(1).any():
        raise RuntimeError("paired methods used different query counts")
    summary = detail.groupby(["scenario", "signal", "method"], as_index=False).agg(
        streams=("seed", "count"),
        promotion_rate=("promoted", "mean"),
        expected_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        realized_future_net_gain=("realized_postpromotion_net_gain", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_monitor_events=("monitor_events_processed", "mean"),
    )
    contrasts = contrast_table(detail)
    detail.to_csv(output / "streams.csv", index=False)
    detail.to_parquet(output / "streams.parquet", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    summary.to_parquet(output / "summary.parquet", index=False)
    contrasts.to_csv(output / "primary_contrasts.csv", index=False)
    contrasts.to_parquet(output / "primary_contrasts.parquet", index=False)
    report = [
        "# Independent Target-Scout paired confirmation",
        "",
        f"**Status:** complete; {seeds} matched seeds per 18 positive-signal cells; CUDA.",
        "",
        "| Contrast | Mean paired net gain | 97.5% interval | Margin | Confirmed above margin |",
        "|---|---:|---:|---:|:---:|",
    ]
    for r in contrasts.to_dict(orient="records"):
        report.append(
            f"| {r['contrast']} | {r['mean_paired_difference']:.4f} | [{r['bootstrap_ci_low']:.4f}, {r['bootstrap_ci_high']:.4f}] | 1.0 | {r['material_benefit_confirmed']} |"
        )
    report.extend(
        [
            "",
            "Bonferroni allocation across two primary contrasts targets at least 95% familywise coverage, conditional on the matched-seed bootstrap approximation. Scope is limited to this registered synthetic design.",
        ]
    )
    (output / "results.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    source_paths = [
        Path(__file__).resolve(),
        ROOT / "scripts/compare_target_scout_fixed_split.py",
        ROOT / "src/shiftlab/dive/budgeted_promotion.py",
        ROOT / "src/shiftlab/decision_harm_experiment.py",
        ROOT / "src/shiftlab/data/gpu/environment.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        PROTOCOL,
    ]
    artifact_names = (
        "streams.csv",
        "streams.parquet",
        "summary.csv",
        "summary.parquet",
        "primary_contrasts.csv",
        "primary_contrasts.parquet",
        "results.md",
    )
    manifest = {
        "experiment": "target_scout_fixed_split_independent_confirmation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "completed",
        "protocol": {"path": PROTOCOL.relative_to(ROOT).as_posix(), "sha256": sha256(PROTOCOL)},
        "configuration": signature
        | {
            "prevalences": PREVALENCES,
            "signals": SIGNALS,
            "proxy_errors": PROXY_ERRORS,
            "methods": METHODS,
            "budget_rate": BUDGET_RATE,
            "alpha": ALPHA,
            "switching_cost": 0.05,
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "practical_margin": PRACTICAL_MARGIN,
        },
        "calibration_manifest_sha256": sha256(calibration),
        "environment": environment(),
        "rows": len(detail),
        "primary_contrasts": contrasts.to_dict(orient="records"),
        "all_caps_respected": True,
        "paired_label_mismatches": 0,
        "source_hashes": {p.relative_to(ROOT).as_posix(): sha256(p) for p in source_paths},
        "artifacts": {name: sha256(output / name) for name in artifact_names},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    checkpoint.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    print(json.dumps(manifest["primary_contrasts"], indent=2), flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=300)
    parser.add_argument("--seed-offset", type=int, default=99_010_000)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--n", type=int, default=3200)
    parser.add_argument("--d", type=int, default=16)
    args = parser.parse_args()
    run(
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        device=args.device,
        calibration=args.calibration,
        output=args.output,
        n=args.n,
        d=args.d,
    )


if __name__ == "__main__":
    main()
