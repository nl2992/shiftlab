"""Exploratory CRSP replay of exchange-stratified anytime monitor candidates.

The subgroup e-process mixture is valid only under the intersection of the
exchange-specific conditional-mean nulls. This historical replay is descriptive:
its release-time and conditional-mean assumptions are not established.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import torch
from scipy.special import logsumexp
from scipy.stats import rankdata

from shiftlab.data.provenance import sha256, write_json
from shiftlab.dive.eprocess import BoundedMeanEProcess, PredictableStartedMixtureEProcess

if __package__ in {None, ""}:
    from evaluate_crsp_monitor_comparison import (
        PRIMARY_BPS,
        RETURN_CAP,
        _fit_ridge_streaming,
        _nrows,
        _panel_path,
        _predict_streaming,
        _read_split,
        _turnover_in_path,
    )
else:
    from scripts.evaluate_crsp_monitor_comparison import (
        PRIMARY_BPS,
        RETURN_CAP,
        _fit_ridge_streaming,
        _nrows,
        _panel_path,
        _predict_streaming,
        _read_split,
        _turnover_in_path,
    )

EXCHANGES = ("A", "B", "I", "N", "Q", "R")
EXCHANGE_CODES = {name: index for index, name in enumerate(EXCHANGES)}
ALPHA = 0.05
FEE = PRIMARY_BPS / 10_000.0
BOUND = 0.20 + 4 * FEE
BLOCK_DAYS = 20
PROTOCOL = Path("docs/crsp_exchange_stratified_replay_protocol.md")


def _future_harm_labels(daily_costs: np.ndarray, horizon: int = BLOCK_DAYS) -> np.ndarray:
    """Evaluator-only next-window signs; omit groups with too few future dates."""
    labels = np.full(daily_costs.shape, np.nan, dtype=np.float64)
    for group in range(daily_costs.shape[0]):
        for date in range(daily_costs.shape[1]):
            future = daily_costs[group, date + 1 : date + 1 + horizon]
            future = future[np.isfinite(future)]
            if len(future) >= max(5, horizon // 2):
                labels[group, date] = float(future.mean() > 0)
    return labels


def _score_strata(
    daily_costs: np.ndarray,
    *,
    bound: float = BOUND,
    alpha: float = ALPHA,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Return per-exchange log-e paths and equal-weight exchange-mixture paths."""
    if daily_costs.ndim != 2 or daily_costs.shape[0] != len(EXCHANGES):
        raise ValueError("daily_costs must have one row per registered exchange")
    if np.isinf(daily_costs).any() or np.any(np.abs(daily_costs[np.isfinite(daily_costs)]) > bound + 1e-12):
        raise ValueError("daily exchange means must be finite where present and within bound")
    n_dates = daily_costs.shape[1]
    starts = tuple(round(index * n_dates / 8) for index in range(8))
    paths = {
        "fixed_stake_mixture": np.empty((len(EXCHANGES), n_dates), dtype=np.float64),
        "uniform_eight_start_mixture": np.empty((len(EXCHANGES), n_dates), dtype=np.float64),
    }
    aggregate: dict[str, np.ndarray] = {}
    for exchange_index in range(len(EXCHANGES)):
        fixed = BoundedMeanEProcess(bound=bound, alpha=alpha)
        restarted = PredictableStartedMixtureEProcess(alpha=alpha, starts=starts)
        for date_index, value in enumerate(daily_costs[exchange_index]):
            if np.isfinite(value):
                fixed_log = fixed.update(float(value))
                started_log = restarted.update(float(value), bound=bound)
            else:
                fixed_log = fixed.log_e_value
                # A zero increment carries no evidence but advances the fixed calendar starts.
                started_log = restarted.update(0.0, bound=bound)
            paths["fixed_stake_mixture"][exchange_index, date_index] = fixed_log
            paths["uniform_eight_start_mixture"][exchange_index, date_index] = started_log
    for method, group_paths in paths.items():
        aggregate[method] = logsumexp(group_paths - math.log(len(EXCHANGES)), axis=0)
    return paths, aggregate


def _auc_ap(scores: np.ndarray, labels: np.ndarray) -> tuple[float | None, float | None, int]:
    valid = np.isfinite(scores) & np.isfinite(labels)
    score, target = scores[valid], labels[valid].astype(bool)
    positives = int(target.sum())
    if positives == 0 or positives == len(target):
        return None, None, positives
    ranks = rankdata(score, method="average")
    auc = (ranks[target].sum() - positives * (positives + 1) / 2) / (
        positives * (len(target) - positives)
    )
    order = np.argsort(-score, kind="stable")
    cumulative = np.cumsum(target[order])
    precision = cumulative / np.arange(1, len(target) + 1)
    ap = float((precision * target[order]).sum() / positives)
    return float(auc), ap, positives


def replay(
    *, root: Path, version: str | None, batch_size: int, device_name: str, output: Path
) -> Path:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")
    panel = _panel_path(root, version)
    panel_manifest_path = panel / "dataset_manifest.json"
    panel_manifest = json.loads(panel_manifest_path.read_text(encoding="utf-8"))
    observation_path = panel / "observations.parquet"
    expected_hash = panel_manifest["files"]["observations.parquet"]
    if sha256(observation_path) != expected_hash:
        raise ValueError("CRSP observations checksum differs from its dataset manifest")
    dataset = ds.dataset(observation_path, format="parquet")
    feature_names = panel_manifest["feature_names"]
    feature_count = len(feature_names)
    market_index = feature_names.index("vwretd")
    split_counts = {name: _nrows(dataset, name) for name in ("train", "test")}
    device = torch.device(
        "cuda" if device_name == "auto" and torch.cuda.is_available() else "cpu"
        if device_name == "auto" else device_name
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="shiftlab_crsp_exchange_") as temp_name:
        temp = Path(temp_name)
        train = _read_split(
            dataset,
            split="train",
            nrows=split_counts["train"],
            nfeatures=feature_count,
            directory=temp,
            batch_size=batch_size,
        )
        medians, means, scales, y_mean, coefficients, fit_device = _fit_ridge_streaming(
            train["x"], train["y"], device=device, batch_size=batch_size
        )
        del train
        test = _read_split(
            dataset,
            split="test",
            nrows=split_counts["test"],
            nfeatures=feature_count,
            directory=temp,
            batch_size=batch_size,
            include_exchange=True,
        )
        if len(test["exchange"]) != split_counts["test"]:
            raise RuntimeError("exchange field did not align with test rows")
        predictions = _predict_streaming(
            test["x"],
            medians=medians,
            means=means,
            scales=scales,
            y_mean=y_mean,
            coef=coefficients,
            device=device,
            batch_size=batch_size,
        )
        candidate = (predictions > 0).astype(np.int8)
        reference = (np.asarray(test["x"][:, market_index]) > 0).astype(np.int8)
        permno = np.asarray(test["permno"]).copy()
        dates = np.asarray(test["date"]).copy()
        exchanges = np.asarray(test["exchange"], dtype=np.int8).copy()
        if not np.isin(exchanges, range(len(EXCHANGES))).all():
            raise RuntimeError("test data contains an unregistered exchange code")
        candidate_turnover = _turnover_in_path(candidate, permno, dates)
        reference_turnover = _turnover_in_path(reference, permno, dates)
        clipped_return = np.clip(np.asarray(test["y"]), -RETURN_CAP, RETURN_CAP)
        paired_cost = (
            -candidate * clipped_return
            + FEE * candidate_turnover
            - (-reference * clipped_return + FEE * reference_turnover)
        )
        unique_dates, date_index = np.unique(dates, return_inverse=True)
        cell_index = exchanges.astype(np.int64) * len(unique_dates) + date_index
        sums = np.bincount(cell_index, weights=paired_cost, minlength=len(EXCHANGES) * len(unique_dates))
        counts = np.bincount(cell_index, minlength=len(EXCHANGES) * len(unique_dates))
        sums = sums.reshape(len(EXCHANGES), len(unique_dates))
        counts = counts.reshape(len(EXCHANGES), len(unique_dates))
        daily_costs = np.full(sums.shape, np.nan, dtype=np.float64)
        observed = counts > 0
        daily_costs[observed] = sums[observed] / counts[observed]
        paths, composite_paths = _score_strata(daily_costs)
        future_labels = _future_harm_labels(daily_costs)

        trace_rows = []
        exchange_rows = []
        method_rows = []
        threshold_log = math.log(1 / ALPHA)
        subgroup_log_threshold = math.log(len(EXCHANGES) / ALPHA)
        date_strings = np.asarray(unique_dates, dtype="datetime64[D]").astype(str)
        for exchange_index, exchange in enumerate(EXCHANGES):
            group_observed = observed[exchange_index]
            n_events = int(counts[exchange_index].sum())
            n_dates = int(group_observed.sum())
            exchange_rows.append(
                {
                    "exchange": exchange,
                    "events": n_events,
                    "observed_dates": n_dates,
                    "mean_daily_paired_cost": (
                        float(np.nanmean(daily_costs[exchange_index])) if n_dates else None
                    ),
                    "event_weighted_paired_cost": float(
                        paired_cost[exchanges == exchange_index].mean()
                    )
                    if n_events
                    else None,
                    "positive_next_20_date_harm_prevalence": float(
                        np.nanmean(future_labels[exchange_index])
                    )
                    if np.isfinite(future_labels[exchange_index]).any()
                    else None,
                }
            )
            for date_index, date_value in enumerate(date_strings):
                trace_rows.append(
                    {
                        "date": date_value,
                        "exchange": exchange,
                        "daily_mean_paired_cost": daily_costs[exchange_index, date_index],
                        "events": int(counts[exchange_index, date_index]),
                        "future_20_date_positive_harm_label": (
                            None
                            if not np.isfinite(future_labels[exchange_index, date_index])
                            else bool(future_labels[exchange_index, date_index])
                        ),
                        **{
                            f"{method}_log_e": float(path[exchange_index, date_index])
                            for method, path in paths.items()
                        },
                    }
                )
        del test
        for method, score_path in paths.items():
            pooled_score = score_path.reshape(-1)
            pooled_labels = future_labels.reshape(-1)
            auc, average_precision, positives = _auc_ap(pooled_score, pooled_labels)
            composite = composite_paths[method]
            crossings = np.flatnonzero(composite >= threshold_log)
            method_rows.append(
                {
                    "method": method,
                    "exchange_mixture_first_crossing_date": (
                        date_strings[int(crossings[0])] if len(crossings) else None
                    ),
                    "exchange_mixture_crossing_fraction": float(
                        np.mean(composite >= threshold_log)
                    ),
                    "exchange_mixture_max_log_e": float(composite.max()),
                    "first_bonferroni_subgroup_crossing": any(
                        np.any(path >= subgroup_log_threshold) for path in score_path
                    ),
                    "subgroup_log_e_threshold_alpha_over_6": subgroup_log_threshold,
                    "pooled_auroc_next_20_date_harm": auc,
                    "pooled_average_precision_next_20_date_harm": average_precision,
                    "pooled_positive_harm_windows": positives,
                    "updates_per_exchange": len(unique_dates),
                    "interpretation": "exploratory retrospective replay; no CRSP error-control claim",
                }
            )
        for method in paths:
            composite = composite_paths[method]
            for date_index, date_value in enumerate(date_strings):
                trace_rows.append(
                    {
                        "date": date_value,
                        "exchange": "EQUAL_WEIGHT_MIXTURE",
                        "daily_mean_paired_cost": None,
                        "events": 0,
                        "future_20_date_positive_harm_label": None,
                        f"{method}_log_e": float(composite[date_index]),
                    }
                )

    paths_df = pd.DataFrame(trace_rows)
    exchange_df = pd.DataFrame(exchange_rows)
    method_df = pd.DataFrame(method_rows)
    pq.write_table(pa.Table.from_pandas(paths_df, preserve_index=False), output / "exchange_paths.parquet")
    pq.write_table(pa.Table.from_pandas(exchange_df, preserve_index=False), output / "exchange_summary.parquet")
    pq.write_table(pa.Table.from_pandas(method_df, preserve_index=False), output / "method_summary.parquet")
    paths_df.to_csv(output / "exchange_paths.csv", index=False)
    exchange_df.to_csv(output / "exchange_summary.csv", index=False)
    method_df.to_csv(output / "method_summary.csv", index=False)
    manifest = {
        "experiment": "exploratory exchange-stratified CRSP decision-harm monitor replay",
        "input_panel": panel.as_posix(),
        "input_panel_manifest_sha256": sha256(panel_manifest_path),
        "input_observations_sha256": sha256(observation_path),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "source_sha256": sha256(Path(__file__)),
        "monitor_source_sha256": sha256(Path("src/shiftlab/dive/eprocess.py")),
        "policy_source_sha256": sha256(Path("scripts/evaluate_crsp_monitor_comparison.py")),
        "policy": "same train-only standardized Ridge(alpha=1) long/flat policy and same-date VWRETD reference as the full-cohort CRSP comparison",
        "turnover_cost_bps": PRIMARY_BPS,
        "bound": BOUND,
        "alpha_reference": ALPHA,
        "exchange_codes": list(EXCHANGES),
        "aggregation": "equal-weight mixture of six exchange-specific e-processes; subgroup intersection null, separate from the population-average null",
        "future_label": "evaluator-only positive mean paired cost over next 20 test dates, overlapping windows",
        "test_events": len(paired_cost),
        "test_dates": len(unique_dates),
        "test_permnos": int(np.unique(permno).size),
        "device": fit_device,
        "created_utc": datetime.now(UTC).isoformat(),
        "limitations": [
            "The full 2020-2025 CRSP test period was already inspected in earlier analyses; this replay is exploratory, not independent confirmation.",
            "The stratified mixture targets an intersection of exchange-specific conditional-mean nulls and does not test the population-average harm null.",
            "CRSP release times, the conditional-on-past null, temporal dependence and real label availability are unverified; nominal alpha does not establish a CRSP error rate.",
            "The policy uses an imposed clipped-return and turnover utility, not validated market impact or causal deployment outcomes.",
        ],
    }
    write_json(output / "manifest.json", manifest)
    report = [
        "# Exploratory CRSP exchange-stratified monitor replay",
        "",
        f"The frozen train-only policy was replayed on {len(paired_cost):,} test observations, {int(np.unique(permno).size):,} PERMNOs, and {len(unique_dates):,} dates. The exact same-date exchange code `primaryexch` defines six predeclared operational strata.",
        "",
        "## Exchange support and paired costs",
        "",
        exchange_df.to_markdown(index=False, floatfmt=".5f"),
        "",
        "## Monitor comparison",
        "",
        method_df.to_markdown(index=False, floatfmt=".4f"),
        "",
        "The two candidates are the established fixed five-stake bounded-mean e-process and the established uniform eight-start mixture, each run within each exchange. The six per-exchange e-values are combined with fixed equal weights. An exchange-mixture crossing at `log(1/alpha)` is valid only for the intersection of all six exchange-specific nulls; the familywise subgroup threshold `log(6/alpha)` is also reported. Neither is a test of population-average harm.",
        "",
        "All results are retrospective diagnostics on a test period already examined in previous CRSP analyses. Hindsight next-20-date labels are evaluator-only and overlapping. The WRDS close dates do not verify actual label publication times, temporal dependence is not modeled by these standard e-processes, and no CRSP false-alarm guarantee is claimed. Any figure should be separately produced with PaperBanana and validated against these saved metrics.",
        "",
        f"Protocol: `{PROTOCOL.as_posix()}`. Metrics, source hashes, environment details and checksums are saved under `{output.as_posix()}/`.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    checksums = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted(output.iterdir())
        if path.name != "checksums.sha256"
    ]
    (output / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(method_df.to_string(index=False))
    print(exchange_df.to_string(index=False))
    print(f"output={output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--version")
    parser.add_argument("--batch-size", type=int, default=200_000)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/crsp_exchange_stratified_replay")
    )
    args = parser.parse_args()
    replay(
        root=args.root,
        version=args.version,
        batch_size=args.batch_size,
        device_name=args.device,
        output=args.output,
    )


if __name__ == "__main__":
    main()
