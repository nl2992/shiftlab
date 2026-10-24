"""Screen predictable stake rebalancing on matched delayed-feedback streams."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.special import logsumexp

try:
    from scripts.calibrate_history_predictable_query_bounds import (
        ALPHA,
        HARM_ONSET_FRACTION,
        HIGH_COST,
        LABEL_BUDGET_RATE,
        Q_MAX,
        STAKES,
        M,
        scenario_harm_effect,
    )
    from scripts.confirm_history_predictable_query_bounds import paired_bootstrap_interval
    from scripts.run_matched_path_bound_ablation import SCHEDULES, build_schedule
    from scripts.validate_markov_predictable_query_bounds import (
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )
except ModuleNotFoundError:  # Direct execution puts scripts/ on sys.path.
    from calibrate_history_predictable_query_bounds import (
        ALPHA,
        HARM_ONSET_FRACTION,
        HIGH_COST,
        LABEL_BUDGET_RATE,
        Q_MAX,
        STAKES,
        M,
        scenario_harm_effect,
    )
    from confirm_history_predictable_query_bounds import paired_bootstrap_interval
    from run_matched_path_bound_ablation import SCHEDULES, build_schedule
    from validate_markov_predictable_query_bounds import (
        MARKOV_HARM_SCENARIOS,
        MARKOV_NEGATIVE_SCENARIO,
        MARKOV_NULL_SCENARIO,
        generate_markov_dependent_data,
        verify_dgp_algebra,
    )

DEFAULT_SEED = 28704027
DEFAULT_OUTPUT = Path("outputs/predictable_stake_portfolio_development")
HORIZON = 2400
DELAY = 12
SCHEDULE = next(item for item in SCHEDULES if item[0] == "periodic_q080")
ETAS = np.asarray((0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0), dtype=np.float64)
SCENARIOS = (MARKOV_NULL_SCENARIO, MARKOV_NEGATIVE_SCENARIO, *MARKOV_HARM_SCENARIOS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def predictable_weights(log_wealth: np.ndarray, eta: float) -> np.ndarray:
    """Weights measurable from prior component wealth, before the next increment."""
    values = np.asarray(log_wealth, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] < 1 or not np.isfinite(values).all():
        raise ValueError("log_wealth must be a finite streams-by-stakes matrix")
    if not np.isfinite(eta) or eta < 0:
        raise ValueError("eta must be finite and nonnegative")
    log_prior = np.full(values.shape[1], -math.log(values.shape[1]))
    logits = eta * values + log_prior
    return np.exp(logits - logsumexp(logits, axis=1, keepdims=True))


def _simulate(
    *,
    scenario: str,
    propensity: np.ndarray,
    data: dict[str, torch.Tensor | float],
) -> list[dict[str, object]]:
    horizon, streams = propensity.shape
    arrays = {
        key: value.detach().cpu().numpy() if torch.is_tensor(value) else value
        for key, value in data.items()
    }
    expected_shape = (horizon, streams)
    for key in ("context", "outcome_uniform", "query_uniform", "p_low", "p_high"):
        if np.shape(arrays[key]) != expected_shape:
            raise ValueError(f"{key} has wrong shape")
    if np.any(propensity <= 0) or np.any(propensity > Q_MAX):
        raise ValueError("propensities must lie in (0, q_max]")

    stakes = np.asarray(STAKES, dtype=np.float64)
    log_prior = np.full(len(stakes), -math.log(len(stakes)), dtype=np.float64)
    component_log_wealth = np.zeros((streams, len(stakes)), dtype=np.float64)
    portfolio_log_wealth = np.zeros((streams, len(ETAS)), dtype=np.float64)
    threshold = -math.log(ALPHA)
    budget = math.floor(LABEL_BUDGET_RATE * horizon)
    onset = math.floor(HARM_ONSET_FRACTION * horizon)
    effect = scenario_harm_effect(scenario)
    remaining = np.full(streams, budget, dtype=np.int64)
    labels = np.zeros(streams, dtype=np.int64)
    registered = np.zeros(streams, dtype=np.int64)
    cursor = np.zeros(streams, dtype=np.int64)
    processed = np.zeros(streams, dtype=np.int64)
    first_alarm = np.full((streams, len(ETAS)), -1, dtype=np.int64)
    alarm_wall = np.full((streams, len(ETAS)), -1, dtype=np.int64)
    known = np.zeros((horizon, streams), dtype=bool)
    queried = np.zeros_like(known)
    included = np.zeros_like(known)
    proxy = np.zeros((horizon, streams), dtype=np.float64)
    estimate = np.zeros_like(proxy)
    bound = np.zeros_like(proxy)
    bound_violations = np.zeros(streams, dtype=bool)

    def release_ready_prefix(wall_time: int) -> None:
        nonlocal component_log_wealth, portfolio_log_wealth, cursor, processed
        while True:
            idx = np.minimum(cursor, horizon - 1)
            ready = (cursor < registered) & known[idx, np.arange(streams)]
            if not ready.any():
                return
            update = ready & included[idx, np.arange(streams)]
            x = estimate[idx, np.arange(streams)]
            b = bound[idx, np.arange(streams)]
            bound_violations[:] |= update & (np.abs(x) > b + 1e-9)
            normalized = np.divide(x, b, out=np.zeros_like(x), where=b > 0)
            factors = 1 + normalized[:, None] * stakes[None, :]
            if np.any(update[:, None] & (factors <= 0)):
                raise RuntimeError("nonpositive component betting factor")
            log_factors = np.log(factors)
            pre_weights = np.stack(
                [predictable_weights(component_log_wealth, eta) for eta in ETAS], axis=1
            )
            portfolio_increment = logsumexp(np.log(pre_weights) + log_factors[:, None, :], axis=2)
            portfolio_log_wealth += np.where(update[:, None], portfolio_increment, 0.0)
            component_log_wealth += np.where(update[:, None], log_factors, 0.0)

            log_e = portfolio_log_wealth
            if np.any(~np.isfinite(log_e)):
                raise RuntimeError("nonfinite portfolio evidence")
            crossed = update[:, None] & (first_alarm < 0) & (log_e >= threshold)
            first_alarm[crossed] = np.broadcast_to(idx[:, None], crossed.shape)[crossed]
            alarm_wall[crossed] = np.broadcast_to(
                np.full((streams, 1), wall_time, dtype=np.int64), crossed.shape
            )[crossed]
            processed += update.astype(np.int64)
            cursor += ready.astype(np.int64)

    def outcome_probability(event: int) -> np.ndarray:
        context = arrays["context"][event]
        high = context == 1
        p_high = arrays["p_high"][event].astype(np.float64, copy=True)
        if effect is not None and event >= onset:
            p_high -= float(arrays["effect_probability_shift_per_unit"]) * effect
        return np.where(high, p_high, arrays["p_low"][event])

    def release_label(event: int) -> None:
        if event < 0 or event >= horizon:
            return
        mask = queried[event]
        if not mask.any():
            return
        context = arrays["context"][event]
        high = context == 1
        y = arrays["outcome_uniform"][event] < outcome_probability(event)
        contrast = np.where(high, HIGH_COST, 1.0) * (1 - 2 * y.astype(np.float64))
        q = propensity[event, mask]
        estimate[event, mask] = proxy[event, mask] + (contrast[mask] - proxy[event, mask]) / q
        known[event, mask] = True

    for wall_time in range(horizon):
        release_label(wall_time - DELAY)
        release_ready_prefix(wall_time)
        active = remaining > 0
        q = propensity[wall_time]
        query = active & (arrays["query_uniform"][wall_time] < q)
        context = arrays["context"][wall_time]
        h = np.where(context == 1, arrays["h_high"], arrays["h_low"]).astype(np.float64)
        proxy[wall_time, active] = h[active]
        estimate[wall_time, active] = h[active]
        queried[wall_time] = query
        included[wall_time] = active
        known[wall_time] = ~query | ~active
        bound[wall_time, active] = M * (2 / q[active] - 1)
        remaining -= query.astype(np.int64)
        labels += query.astype(np.int64)
        registered += active.astype(np.int64)

    for wall_time in range(horizon, horizon + DELAY):
        release_label(wall_time - DELAY)
        release_ready_prefix(wall_time)
    if np.any(cursor != registered):
        raise RuntimeError("not every registered event was released in event order")
    if np.any(labels > budget):
        raise RuntimeError("hard query cap exceeded")
    if bound_violations.any():
        raise RuntimeError("support-bound invariant failed")

    static_log_e = logsumexp(component_log_wealth + log_prior, axis=1)
    static_index = int(np.flatnonzero(ETAS == 1.0)[0])
    if not np.allclose(portfolio_log_wealth[:, static_index], static_log_e, rtol=0, atol=1e-12):
        raise RuntimeError("eta=1 failed fixed-mixture identity")

    states = arrays["regime_state"]
    coefficient = np.where(states == 0, 4 / 3, 2 / 3)
    rows: list[dict[str, object]] = []
    for stream in range(streams):
        for eta_index, eta in enumerate(ETAS):
            alarm = int(first_alarm[stream, eta_index])
            harmful = effect is not None and effect > 0
            detected = bool(harmful and alarm >= onset)
            false = bool(alarm >= 0 and (alarm < onset if harmful else True))
            stopped_at = alarm if alarm >= 0 else int(cursor[stream]) - 1
            exposure = (
                float(effect * coefficient[onset : stopped_at + 1, stream].sum())
                if harmful and stopped_at >= onset
                else 0.0
            )
            rows.append(
                {
                    "scenario": scenario,
                    "eta": float(eta),
                    "stream_id": stream,
                    "stream_seed_id": int(data.get("seed", 0)) + stream,
                    "feedback_delay": DELAY,
                    "q_min": float(propensity.min()),
                    "q_max": float(propensity.max()),
                    "hard_label_budget": budget,
                    "labels_queried": int(labels[stream]),
                    "events_processed": int(processed[stream]),
                    "registered_events": int(registered[stream]),
                    "budget_respected": bool(labels[stream] <= budget),
                    "first_alarm_event": alarm if alarm >= 0 else None,
                    "first_alarm_wall_time": int(alarm_wall[stream, eta_index])
                    if alarm >= 0
                    else None,
                    "false_escalation": false,
                    "onset_reached": bool(processed[stream] > onset) if harmful else None,
                    "post_onset_detection": detected,
                    "detection_delay_event_time": float(alarm - onset) if detected else None,
                    "detection_delay_wall_time": float(alarm_wall[stream, eta_index] - onset)
                    if detected
                    else None,
                    "evaluator_cumulative_expected_harm_cost": exposure,
                    "bound_violations": int(bound_violations[stream]),
                }
            )
    return rows


def analyze(metrics: pd.DataFrame, *, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = (
        metrics.groupby(["scenario", "eta"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            detection_rate=("post_onset_detection", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_processed_events=("events_processed", "mean"),
            mean_event_delay=("detection_delay_event_time", "mean"),
            mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_expected_exposure=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    harms = metrics[metrics["scenario"].isin(MARKOV_HARM_SCENARIOS)]
    wide = harms.pivot(
        index=["scenario", "stream_id"],
        columns="eta",
        values=[
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ],
    )
    contrasts: list[dict[str, object]] = []
    for eta in ETAS:
        if eta == 1.0:
            continue
        for metric in (
            "post_onset_detection",
            "labels_queried",
            "evaluator_cumulative_expected_harm_cost",
        ):
            per_dose: list[np.ndarray] = []
            for scenario in MARKOV_HARM_SCENARIOS:
                part = wide.loc[scenario]
                per_dose.append(
                    part[(metric, float(eta))].to_numpy(dtype=float)
                    - part[(metric, 1.0)].to_numpy(dtype=float)
                )
            macro = np.stack(per_dose, axis=1).mean(axis=1)
            interval = paired_bootstrap_interval(macro, seed=seed + 91537 + len(contrasts))
            contrasts.append(
                {
                    "metric": metric,
                    "candidate_eta": float(eta),
                    "reference_eta": 1.0,
                    "mean_difference": float(macro.mean()),
                    "bootstrap_95_low": interval[0],
                    "bootstrap_95_high": interval[1],
                    "paired_seed_count": len(macro),
                }
            )
    return summary, pd.DataFrame(contrasts)


def nominate_candidate(metrics: pd.DataFrame, contrasts: pd.DataFrame) -> dict[str, object]:
    """Apply the frozen development-only nomination gate."""
    harms = metrics[metrics["scenario"].isin(MARKOV_HARM_SCENARIOS)]
    dose_rates = harms.groupby(["scenario", "eta"])["post_onset_detection"].mean().unstack()
    candidates: list[dict[str, object]] = []
    for eta in ETAS:
        if eta == 1.0:
            continue
        contrast = contrasts[
            (contrasts["metric"] == "post_onset_detection")
            & np.isclose(contrasts["candidate_eta"], eta)
        ].iloc[0]
        dose_differences = [
            float(dose_rates.loc[scenario, eta] - dose_rates.loc[scenario, 1.0])
            for scenario in MARKOV_HARM_SCENARIOS
        ]
        passes = (
            contrast["mean_difference"] >= 0.03
            and contrast["bootstrap_95_low"] > 0
            and min(dose_differences) >= -0.05
        )
        candidates.append(
            {
                "eta": float(eta),
                "macro_detection_gain": float(contrast["mean_difference"]),
                "bootstrap_95_low": float(contrast["bootstrap_95_low"]),
                "minimum_dose_detection_difference": min(dose_differences),
                "dose_detection_differences": dose_differences,
                "passes_nomination_gate": bool(passes),
            }
        )
    passing = [candidate for candidate in candidates if candidate["passes_nomination_gate"]]
    selected = max(passing, key=lambda item: item["macro_detection_gain"]) if passing else None
    return {
        "status": "development_nomination_only",
        "selected_eta": selected["eta"] if selected else None,
        "candidates": candidates,
        "interpretation": (
            "Any nomination requires fresh independent null calibration and disjoint confirmation; "
            "this development block does not establish validity or performance."
        ),
    }


def run(*, streams: int, seed: int, device_name: str, output: Path, horizon: int = HORIZON) -> Path:
    if streams < 30 or horizon < 100:
        raise ValueError("development screen requires at least 30 streams and horizon 100")
    if seed != DEFAULT_SEED:
        raise ValueError(f"development seed root is frozen at {DEFAULT_SEED}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output: {output}")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    verify_dgp_algebra()
    device = torch.device(device_name)
    started = time.monotonic()
    data = generate_markov_dependent_data(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    data["seed"] = seed
    schedule_name, low, high, high_slots = SCHEDULE
    propensity = build_schedule(
        name=schedule_name,
        low=low,
        high=high,
        high_slots=high_slots,
        horizon=horizon,
        streams=streams,
    )
    rows = [
        row
        for scenario in SCENARIOS
        for row in _simulate(scenario=scenario, propensity=propensity, data=data)
    ]
    metrics = pd.DataFrame(rows)
    expected_rows = streams * len(SCENARIOS) * len(ETAS)
    if len(metrics) != expected_rows or metrics.duplicated(["scenario", "eta", "stream_id"]).any():
        raise RuntimeError("stream grid is incomplete or duplicated")
    if not metrics["budget_respected"].all() or metrics["bound_violations"].sum() != 0:
        raise RuntimeError("budget or support invariant failed")
    paths = metrics.pivot(
        index=["scenario", "stream_id"],
        columns="eta",
        values=["labels_queried", "events_processed", "registered_events"],
    )
    for field in ("labels_queried", "events_processed", "registered_events"):
        reference = paths[(field, 1.0)]
        if any(not reference.equals(paths[(field, float(eta))]) for eta in ETAS):
            raise RuntimeError(f"portfolio weights changed the shared path field {field}")
    summary, contrasts = analyze(metrics, seed=seed)
    selection = nominate_candidate(metrics, contrasts)
    output.mkdir(parents=True, exist_ok=True)
    metrics_dir, reports_dir = output / "metrics", output / "reports"
    metrics_dir.mkdir()
    reports_dir.mkdir()
    metrics_path = metrics_dir / "stream_metrics.parquet"
    metrics.to_parquet(metrics_path, index=False)
    summary_path = metrics_dir / "summary.csv"
    summary.to_csv(summary_path, index=False)
    contrasts_path = metrics_dir / "paired_detection_contrasts.csv"
    contrasts.to_csv(contrasts_path, index=False)
    selection_path = reports_dir / "selection.json"
    selection_path.write_text(json.dumps(selection, indent=2, sort_keys=True), encoding="utf-8")
    report_path = reports_dir / "development_results.md"
    report = [
        "# Predictable stake portfolio development screen",
        "",
        f"- Streams per scenario and eta: {streams}; horizon: {horizon}; delay: {DELAY}.",
        f"- Query schedule: `{schedule_name}` (`q_low={low}`, `q_high={high}`, {high_slots}/10 high slots); hard cap: {math.floor(LABEL_BUDGET_RATE * horizon)} labels.",
        f"- Generation device: {device}; sequential delayed-feedback replay: CPU NumPy.",
        f"- Candidate eta grid: `{ETAS.tolist()}`; eta=1 matches the fixed equal-weight stake mixture algebraically and numerically to 1e-12.",
        "- All candidates share identical query, label, event-prefix, and budget paths. Null cells are descriptive (60 streams), not calibration.",
        "- No figure was generated; the project requires PaperBanana for visuals and none is available in this session.",
        "",
        "## Cell summaries",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired detection contrasts versus fixed eta=1",
        "",
        contrasts.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Frozen development nomination gate",
        "",
        f"Selected eta: `{selection['selected_eta']}`.",
        "",
        "This is a development-only nomination; any candidate needs fresh calibration and disjoint confirmation.",
        "",
        "## Interpretation",
        "",
        "This is a development screen for a standard predictable convex portfolio of bounded betting factors. The supermartingale argument requires predictable weights and the registered event-time conditional-mean null. Any nonidentity candidate needs independent calibration and disjoint confirmation. No novelty claim is made.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    source_paths = [
        Path(__file__),
        Path("docs/predictable_stake_portfolio_protocol.md"),
        Path("scripts/run_matched_path_bound_ablation.py"),
        Path("scripts/calibrate_history_predictable_query_bounds.py"),
        Path("scripts/confirm_history_predictable_query_bounds.py"),
        Path("scripts/validate_markov_predictable_query_bounds.py"),
        Path("docs/delayed_event_prefix_validity.md"),
    ]
    artifact_paths = [metrics_path, summary_path, contrasts_path, report_path, selection_path]
    manifest = {
        "experiment": "predictable_stake_portfolio_development",
        "status": "development_only_not_calibration_or_confirmation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_revision": git_revision(),
        "seed_root": seed,
        "streams_per_scenario_eta": streams,
        "horizon": horizon,
        "delay": DELAY,
        "budget_rate": LABEL_BUDGET_RATE,
        "schedule": {
            "name": schedule_name,
            "low": low,
            "high": high,
            "high_slots_per_10": high_slots,
        },
        "stakes": [float(value) for value in STAKES],
        "etas": ETAS.tolist(),
        "scenarios": list(SCENARIOS),
        "device_requested": device_name,
        "device_resolved": str(device),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "python_version": platform.python_version(),
        "runtime_seconds": time.monotonic() - started,
        "rows": len(metrics),
        "selection": selection,
        "source_sha256": {str(path): sha256(path) for path in source_paths},
        "artifact_sha256": {str(path.relative_to(output)): sha256(path) for path in artifact_paths},
        "checks": {
            "eta_one_equals_fixed_mixture": True,
            "shared_paths_across_eta": True,
            "all_label_budgets_respected": True,
            "no_support_bound_violations": True,
        },
        "limitations": [
            "60-stream development only; no false-alarm calibration",
            "two-state Markov-volatility DGP only",
            "fixed complete outcome-independent delay of 12 events",
            "fixed policy pair and source-trained proxy",
            "predictable convex factor portfolio is a standard construction; no novelty claim",
        ],
    }
    manifest_path = reports_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--streams", type=int, default=60)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(
        run(
            streams=args.streams,
            seed=args.seed,
            horizon=args.horizon,
            device_name=args.device,
            output=args.output,
        )
    )


if __name__ == "__main__":
    main()
