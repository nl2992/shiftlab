"""Development comparison with the official ComparingForecasters e-process.

The upstream package pins ``confseq`` as an install dependency. Its Windows
build requires a C++ toolchain that may not be available. This script imports
only the upstream e-process path and supplies an import-only stub for the
unused confidence-sequence boundary module; if that boundary is called, it
raises immediately. The e-process implementation itself is loaded unchanged
from the pinned upstream checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
import types
import warnings
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.data.gpu.environment import environment
from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive.eprocess import BoundedMeanEProcess
from shiftlab.dive.risk_proxy_monitor_grid import (
    ALTERNATIVE_SCENARIOS,
    NULL_SCENARIOS,
    RiskProxyMonitorGridConfig,
    _prepare_stream,
)

ALPHA = 0.05
SEED_OFFSET = 30_325_000
PROTOCOL = Path("papers/shiftguard_unified/comparecast_paired_cost_protocol.md")
OUTPUT = Path("outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_dev_v1")


def _load_upstream_eprocess(source_dir: Path):
    package_dir = source_dir / "comparecast"
    if not (package_dir / "eprocess.py").is_file():
        raise FileNotFoundError(f"expected comparecast/eprocess.py in {source_dir}")

    # Avoid upstream __init__ imports for plotting/data helpers. The e-process
    # module needs this boundary name at import time, but never calls it on the
    # e-process-only path; a call indicates that the protocol changed.
    package = types.ModuleType("comparecast")
    package.__path__ = [str(package_dir)]
    sys.modules["comparecast"] = package

    try:
        confseq_spec = importlib.util.find_spec("confseq")
    except (ImportError, ValueError):
        confseq_spec = None
    if confseq_spec is None:
        confseq = types.ModuleType("confseq")
        boundaries = types.ModuleType("confseq.boundaries")

        def unused_boundary(*_args, **_kwargs):
            raise RuntimeError(
                "the confidence-sequence boundary shim was called; this run only supports the upstream e-process"
            )

        boundaries.normal_log_mixture = unused_boundary
        confseq.boundaries = boundaries
        sys.modules["confseq"] = confseq
        sys.modules["confseq.boundaries"] = boundaries

    return importlib.import_module("comparecast.eprocess").eprocess_expm


def _upstream_commit(source_dir: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"], text=True
    ).strip()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _available_output_path(base: Path) -> Path:
    """Return an unused path, preserving every previous development run."""
    if not base.exists():
        return base
    index = 1
    while True:
        candidate = base.with_name(f"{base.name}_run{index:03d}")
        if not candidate.exists():
            return candidate
        index += 1


def _monitor(increments: np.ndarray, *, bound: float, alpha: float, comparecast_eprocess):
    local = BoundedMeanEProcess(bound=bound, alpha=alpha)
    local_crossing = None
    for index, value in enumerate(increments):
        local.update(float(value))
        if local_crossing is None and local.alarm:
            local_crossing = index

    # Comparecast's argument c is the total width of the score-difference
    # support. The paired cost contrast is in [-bound, bound], so c=2*bound.
    # It tests the weak running-average null; do not interpret it as the
    # conditional-mean null tested by BoundedMeanEProcess.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        e_values = comparecast_eprocess(
            increments,
            alpha_opt=alpha,
            c=2 * bound,
            compute_p=False,
        )
    warning_messages = sorted({str(item.message) for item in caught})
    upstream_crossings = np.flatnonzero(e_values >= 1 / alpha)
    upstream_crossing = int(upstream_crossings[0]) if len(upstream_crossings) else None
    return local_crossing, upstream_crossing, float(np.max(e_values)), warning_messages


def run(
    *,
    source_dir: Path,
    output_dir: Path | None = None,
    seeds: int = 30,
    seed_offset: int = SEED_OFFSET,
    n: int = 2400,
    d: int = 16,
    device: str = "cuda",
) -> dict:
    if seeds < 2 or n < 1000 or d < 2:
        raise ValueError("seeds must be >=2, n>=1000, and d>=2")
    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu, or cuda")
    if output_dir is None:
        output_dir = _available_output_path(OUTPUT)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")

    comparecast_eprocess = _load_upstream_eprocess(source_dir)
    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    resolved_device = device
    if resolved_device == "auto":
        import torch

        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
    config = RiskProxyMonitorGridConfig(
        n=n,
        d=d,
        null_seeds=seeds,
        alternative_seeds=seeds,
        seed_offset=seed_offset,
        alpha=ALPHA,
        device=resolved_device,
    ).validate()

    rows: list[dict] = []
    upstream_warning_messages: set[str] = set()
    for scenario_name in (*NULL_SCENARIOS, *ALTERNATIVE_SCENARIOS):
        scenario = scenarios[scenario_name]
        for seed in range(seed_offset, seed_offset + seeds):
            prepared = _prepare_stream(scenario, seed, config)
            centered = np.asarray(prepared[3], dtype=float)
            expected = np.asarray(prepared[4], dtype=float)
            monitor_start = int(prepared[7])
            onset = prepared[9]
            bound = float(prepared[10])
            increments = centered[monitor_start:]
            if not np.isfinite(increments).all() or np.any(np.abs(increments) > bound + 1e-12):
                raise ValueError(
                    f"paired-cost increment violated support for {scenario_name}/{seed}"
                )

            local_crossing, upstream_crossing, max_e, warning_messages = _monitor(
                increments, bound=bound, alpha=ALPHA, comparecast_eprocess=comparecast_eprocess
            )
            upstream_warning_messages.update(warning_messages)
            for method, crossing in (
                ("shiftlab_conditional_bounded_mean", local_crossing),
                ("comparecast_weak_running_score", upstream_crossing),
            ):
                rows.append(
                    {
                        "scenario": scenario_name,
                        "seed": seed,
                        "method": method,
                        "events_processed": len(increments),
                        "alarm": crossing is not None,
                        "first_crossing_relative": crossing,
                        "harm_onset_relative": onset,
                        "post_onset_detection": bool(
                            crossing is not None and onset is not None and crossing >= onset
                        ),
                        "pre_onset_alarm": bool(
                            crossing is not None and (onset is None or crossing < onset)
                        ),
                        "max_e_value": max_e
                        if method == "comparecast_weak_running_score"
                        else np.nan,
                        "upstream_warning_count": len(warning_messages)
                        if method == "comparecast_weak_running_score"
                        else 0,
                        "mean_expected_margin_excess": float(
                            (expected[monitor_start:] - 0.10).mean()
                        ),
                        "generator_device": config.device,
                    }
                )

    metrics = pd.DataFrame(rows)
    summary = (
        metrics.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            alarms=("alarm", "sum"),
            alarm_rate=("alarm", "mean"),
            post_onset_detections=("post_onset_detection", "sum"),
            post_onset_detection_rate=("post_onset_detection", "mean"),
            pre_onset_alarms=("pre_onset_alarm", "sum"),
            mean_events=("events_processed", "mean"),
            mean_margin_excess=("mean_expected_margin_excess", "mean"),
        )
        .reset_index()
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    metrics.to_parquet(output_dir / "metrics.parquet", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    summary.to_parquet(output_dir / "summary.parquet", index=False)

    source_hashes = {
        str(path.relative_to(source_dir)).replace("\\", "/"): _hash(path)
        for path in (
            source_dir / "comparecast/eprocess.py",
            source_dir / "comparecast/cgfs.py",
            source_dir / "comparecast/scoring.py",
            source_dir / "comparecast/utils.py",
        )
    }
    report = {
        "experiment": "comparecast_paired_cost_development_comparison",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "development_smoke_not_calibration_or_confirmation",
        "config": {
            "seeds": seeds,
            "seed_offset": seed_offset,
            "n": n,
            "d": d,
            "alpha": ALPHA,
            "device": config.device,
            "scenarios": [*NULL_SCENARIOS, *ALTERNATIVE_SCENARIOS],
            "paired_cost_margin": 0.10,
            "output_dir": str(output_dir),
        },
        "hypotheses": {
            "shiftlab": "eventwise conditional mean of paired excess cost <= 0",
            "comparecast": "weak running-average mean score difference <= 0",
        },
        "source": {
            "repository": "https://github.com/yjchoe/ComparingForecasters",
            "commit": _upstream_commit(source_dir),
            "source_sha256": source_hashes,
            "import_note": "Only comparecast.eprocess is called; confseq boundary import is shimmed and raises if called because its compiled Windows dependency could not be built.",
        },
        "shiftlab_source_sha256": {
            "script": _hash(Path(__file__).resolve()),
            "protocol": _hash(PROTOCOL),
            "eprocess": _hash(Path("src/shiftlab/dive/eprocess.py")),
            "generator": _hash(Path("src/shiftlab/decision_harm_experiment.py")),
            "monitor_runner": _hash(Path("src/shiftlab/dive/risk_proxy_monitor_grid.py")),
        },
        "rows": len(metrics),
        "upstream_runtime_warnings": {
            "unique_messages": sorted(upstream_warning_messages),
            "warning_count_per_stream_mean": float(
                metrics.loc[
                    metrics.method == "comparecast_weak_running_score",
                    "upstream_warning_count",
                ].mean()
            ),
            "handling": "captured and recorded in metrics/manifest; not suppressed or altered in upstream source",
        },
        "results": summary.to_dict(orient="records"),
        "environment": environment(),
        "interpretation": [
            "The two methods test different nulls and their alarms must not be interpreted as interchangeable evidence.",
            "Thirty streams per cell are a development screen, not a calibration of alpha=0.05.",
            "Both methods consume the same full-feedback paired-cost sequence; this does not benchmark label acquisition.",
            "No real-data or deployment claim follows from this run.",
        ],
    }
    for name in ("metrics.csv", "metrics.parquet", "summary.csv", "summary.parquet"):
        report.setdefault("artifact_sha256", {})[name] = _hash(output_dir / name)
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparecast-source", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="fresh output directory; if omitted, an unused _runNNN path is chosen",
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    result = run(
        source_dir=args.comparecast_source,
        output_dir=args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        d=args.d,
        device=args.device,
    )
    print(pd.DataFrame(result["results"]).to_string(index=False))
    print(f"rows={result['rows']}; output={result['config']['output_dir']}")


if __name__ == "__main__":
    main()
