"""Shared-path source panel for the frozen WP3 observation-control prescreen.

This module builds one positive-control stream and returns raw evidence arrays for
the WP1 source methods. It performs no seed loops, registered-run orchestration, or
cross-arm interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from numpy.typing import NDArray
from scipy.special import ndtr
from sklearn.linear_model import LogisticRegression

from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from .experiment import _binary_cost, _synthetic_label_costs
from .gated_monitor_comparison import (
    GATED_ARMS,
    feature_adwin_alarm,
    replay_gated,
)
from .hard_budget import HardBudgetConfig, _one_method
from .prediction_powered_evalues import prediction_powered_factor
from .proxy import DecisionLossProxy
from .xu_active_betting import xu_maximum_stake, xu_paired_betting_factor

EPSILON = 0.10
ALPHA = 0.05
MONITOR_START = 800
MONITOR_END = 3200
MONITOR_LENGTH = MONITOR_END - MONITOR_START
SOURCE_UNGATED_ARMS = ("uniform_ppi", "variance_ppi", "uniform_ppi_common96p9")


@dataclass(frozen=True)
class DataEfficientSourcePath:
    """One generated path with learner and evaluator fields kept explicit."""

    seed: int
    onset_fraction: float
    scheduled_onset: int
    device: str
    x: NDArray[np.float64]
    y: NDArray[np.bool_]
    deployed: NDArray[np.int64]
    reference: NDArray[np.int64]
    disagreement: NDArray[np.bool_]
    tariffs: NDArray[np.float64]
    paired_cost: NDArray[np.float64]
    centered_cost: NDArray[np.float64]
    proxy: DecisionLossProxy
    classifier: LogisticRegression
    common_uniforms: NDArray[np.float64]
    expected_paired_cost: NDArray[np.float64]


def build_path(seed: int, onset_fraction: float, device: str) -> DataEfficientSourcePath:
    """Build a boundary-local positive-control path for one onset placement.

    ``onset_fraction`` is measured within the 2,400-event monitor horizon and is
    frozen to 0.75 (primary) or 0.50 (secondary). The oracle expectation is retained
    for evaluator summaries and is never supplied to the gated learner replay.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if onset_fraction not in {0.75, 0.50}:
        raise ValueError("onset_fraction must be the frozen 0.75 or 0.50 monitor fraction")
    if device not in {"cpu", "cuda", "auto"}:
        raise ValueError("device must be cpu, cuda, or auto")
    scenario = next(s for s in SCENARIOS if s.name == "boundary_local_harm")
    change_fraction = (MONITOR_START + int(MONITOR_LENGTH * onset_fraction)) / MONITOR_END
    config = ExperimentConfig(
        n=MONITOR_END,
        d=16,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=MONITOR_START,
        window=64,
        stride=32,
        alpha=ALPHA,
        eprocess_epsilon=EPSILON,
        seed_offset=seed,
        change_fraction=change_fraction,
        device=device,
    )
    _, frame, oracle, _timing = _generate(scenario, seed, config)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    reference = np.asarray(_source_action(x, scenario), dtype=int)
    disagreement = deployed != reference
    tariffs = _synthetic_label_costs(x)
    paired = _binary_cost(deployed, y, scenario.fn_cost, scenario.fp_cost) - _binary_cost(
        reference, y, scenario.fn_cost, scenario.fp_cost
    )
    centered = paired - EPSILON
    proxy = DecisionLossProxy(clip=5.1, seed=seed, update_every=20).fit(
        x[:400],
        centered[:400],
        x[400:MONITOR_START],
        centered[400:MONITOR_START],
    )
    classifier = LogisticRegression(max_iter=500, random_state=seed).fit(x[:400], y[:400])
    uniforms = np.random.default_rng(seed + 9_173).random(MONITOR_END)

    # Evaluator-only expected paired loss; neither observation policy sees this array.
    probability = oracle.probability_positive.to_numpy(dtype=float)
    expected_paired = np.where(
        deployed == 1,
        scenario.fp_cost * (1 - probability),
        scenario.fn_cost * probability,
    ) - np.where(
        reference == 1,
        scenario.fp_cost * (1 - probability),
        scenario.fn_cost * probability,
    )
    scheduled_onset = MONITOR_START + int(MONITOR_LENGTH * onset_fraction)
    return DataEfficientSourcePath(
        seed=seed,
        onset_fraction=onset_fraction,
        scheduled_onset=scheduled_onset,
        device=device,
        x=x,
        y=y,
        deployed=deployed,
        reference=reference,
        disagreement=disagreement,
        tariffs=tariffs,
        paired_cost=paired,
        centered_cost=centered,
        proxy=proxy,
        classifier=classifier,
        common_uniforms=uniforms,
        expected_paired_cost=expected_paired,
    )


def _record(
    *,
    arm: str,
    values: NDArray[np.float64] | None,
    bounds: NDArray[np.float64] | None,
    labels: int,
    dollars: float,
    budget: float | None,
    **extra: object,
) -> dict[str, object]:
    return {
        "arm": arm,
        "values": values,
        "bounds": bounds,
        "labels": int(labels),
        "dollars": float(dollars),
        "budget": None if budget is None else float(budget),
        **extra,
    }


def _source_factor_logs(
    *,
    arm: str,
    traces: list[dict[str, object]],
    values: NDArray[np.float64],
    bound: float,
    minimum_propensity: float,
) -> NDArray[np.float64]:
    base_stake = 0.9 / (2.0 / minimum_propensity - 1.0)
    factors: list[float] = []
    for trace in traces:
        h = float(trace["proxy_prediction"])
        queried = bool(trace["queried"])
        observed = float(trace["learner_observed_excess_cost"]) if queried else None
        if arm == "uniform_ppi":
            factor = prediction_powered_factor(
                proxy_factor=1.0 + base_stake * h / 5.1,
                queried=queried,
                propensity=float(trace["propensity"]),
                lower=1.0 - base_stake,
                upper=1.0 + base_stake,
                observed_factor=(1.0 + base_stake * observed / 5.1) if queried else None,
            )
        else:
            factor = xu_paired_betting_factor(
                proxy_excess_cost=h,
                queried=queried,
                propensity=float(trace["propensity"]),
                stake=0.9 * xu_maximum_stake(minimum_propensity=minimum_propensity),
                bound=5.1,
                observed_excess_cost=observed,
            )
        factors.append(float(factor))
    source_factors = np.asarray(factors, dtype=float)
    np.testing.assert_allclose(source_factors, 1.0 + 0.9 * values / bound, atol=1e-12, rtol=0)
    if np.any(source_factors <= 0):
        raise RuntimeError("source fixed-0.9 factors must be positive")
    return np.cumsum(np.log(source_factors))


def source_panel(path: DataEfficientSourcePath, budget_rate: float) -> list[dict[str, object]]:
    """Return raw one-step evidence and resource records for the frozen WP3 source panel."""
    if budget_rate not in {0.02, 0.05, 0.10, 0.20}:
        raise ValueError("budget_rate must be one of the frozen rates 0.02, 0.05, 0.10, 0.20")
    config = HardBudgetConfig(
        budget_rate=budget_rate,
        q_min=budget_rate / 2.0,
        q_max=0.8,
        device="cpu",
        generate_figure=False,
        record_event_traces=True,
    ).validate()
    target_budget = budget_rate * float(np.mean(path.tariffs[400:MONITOR_START])) * MONITOR_LENGTH
    common = {
        "seed": path.seed,
        "scenario": next(s for s in SCENARIOS if s.name == "boundary_local_harm"),
        "x": path.x,
        "gross_cost_difference": path.paired_cost,
        "centered_cost_difference": path.centered_cost,
        "expected_cost_difference": path.expected_paired_cost,
        "label_costs": path.tariffs,
        "classifier": path.classifier,
        "proxy_template": path.proxy,
        "train_end": 400,
        "monitor_start": MONITOR_START,
        "harm_onset": path.scheduled_onset - MONITOR_START,
        "sample_path_material_harm": True,
        "sample_path_harm_onset": path.scheduled_onset - MONITOR_START,
        "common_uniforms": path.common_uniforms,
        "contrast_zero": _binary_cost(path.deployed, np.zeros_like(path.y), 5.0, 1.0)
        - _binary_cost(path.reference, np.zeros_like(path.y), 5.0, 1.0)
        - EPSILON,
        "contrast_one": _binary_cost(path.deployed, np.ones_like(path.y), 5.0, 1.0)
        - _binary_cost(path.reference, np.ones_like(path.y), 5.0, 1.0)
        - EPSILON,
    }
    records: list[dict[str, object]] = []
    ungated = [("uniform_ppi", "uniform_proxy"), ("variance_ppi", "variance_proxy")]
    if budget_rate == 0.20:
        ungated.append(("uniform_ppi_common96p9", "uniform_proxy"))
    for arm, method in ungated:
        traces: list[dict[str, object]] = []
        local_config = config
        if arm == "uniform_ppi_common96p9":
            local_config = replace(config, common_eprocess_bound=True).validate()
        result = _one_method(method=method, config=local_config, event_trace_rows=traces, **common)
        values = np.asarray([trace["monitor_increment"] for trace in traces], dtype=float)
        bound = float(result["eprocess_support_bound"])
        bounds = np.full(len(values), bound, dtype=float)
        record = _record(
            arm=arm,
            values=values,
            bounds=bounds,
            labels=int(result["labels_queried"]),
            dollars=float(result["realized_label_spend"]),
            budget=float(result["hard_budget"]),
            processed=len(values),
            source_original_logs=None,
            q_min=result["query_propensity_min"],
            q_mean=result["query_propensity_mean"],
            q_max=result["query_propensity_max"],
        )
        records.append(record)
        if arm in {"uniform_ppi", "variance_ppi"}:
            source_logs = _source_factor_logs(
                arm=arm,
                traces=traces,
                values=values,
                bound=bound,
                minimum_propensity=float(result["eprocess_minimum_propensity"]),
            )
            source_alarm = np.flatnonzero(source_logs >= -np.log(ALPHA))
            alias = dict(record)
            alias.update(
                arm="ppe_uniform" if arm == "uniform_ppi" else "xu_active",
                engine="source_fixed0p9",
                algebraic_path_alias=arm,
                source_original_logs=source_logs,
                first_alarm=int(source_alarm[0]) if len(source_alarm) else None,
            )
            records.append(alias)

    for arm in GATED_ARMS:
        result = replay_gated(
            arm=arm,
            x=path.x[MONITOR_START:],
            paired_cost=path.paired_cost[MONITOR_START:],
            disagreement=path.disagreement[MONITOR_START:],
            tariffs=path.tariffs[MONITOR_START:],
            uniforms=path.common_uniforms[:MONITOR_LENGTH],
            validation_disagreement=path.disagreement[400:MONITOR_START],
            validation_tariffs=path.tariffs[400:MONITOR_START],
            budget_rate=budget_rate,
            proxy_template=path.proxy,
            epsilon=EPSILON,
            alpha=ALPHA,
        )
        records.append(
            _record(
                arm=arm,
                values=result.increments,
                bounds=result.bounds,
                labels=int(result.queried.sum()),
                dollars=result.dollars,
                budget=result.budget,
                processed=len(result.increments),
                q_min=float(result.propensities.min()),
                q_mean=float(result.propensities.mean()),
                q_max=float(result.propensities.max()),
                source_original_logs=(result.log_e if arm == "gated_eb_paced" else None),
                first_alarm=result.first_alarm,
            )
        )
        if arm == "gated_ppi_paced":
            source_factors = 1.0 + 0.9 * result.increments / result.bounds
            if np.any(source_factors <= 0):
                raise RuntimeError("PPE support-shrunk factors must remain positive")
            source_logs = np.cumsum(np.log(source_factors))
            source_alarm = np.flatnonzero(source_logs >= -np.log(ALPHA))
            records.append(
                _record(
                    arm="ppe_gated",
                    values=result.increments,
                    bounds=result.bounds,
                    labels=int(result.queried.sum()),
                    dollars=result.dollars,
                    budget=result.budget,
                    processed=len(result.increments),
                    source_original_logs=source_logs,
                    engine="source_fixed0p9",
                    algebraic_path_alias=arm,
                    first_alarm=int(source_alarm[0]) if len(source_alarm) else None,
                )
            )

    full_values = path.centered_cost[MONITOR_START:MONITOR_END]
    full_bounds = np.full(MONITOR_LENGTH, 5.1, dtype=float)
    records.append(
        _record(
            arm="full_feedback",
            values=full_values,
            bounds=full_bounds,
            labels=MONITOR_LENGTH,
            dollars=float(path.tariffs[MONITOR_START:MONITOR_END].sum()),
            budget=None,
            processed=MONITOR_LENGTH,
            label_matched=False,
            label_definition="all monitor events treated as observed labels, including agreements",
        )
    )

    processed_prefix = min(
        int(record["processed"])
        for record in records
        if record["arm"] in {"uniform_ppi", "gated_ht_paced"}
    )
    adwin_alarm = feature_adwin_alarm(path.x, MONITOR_START, processed_prefix)
    records.append(
        _record(
            arm="feature_adwin",
            values=None,
            bounds=None,
            labels=0,
            dollars=0.0,
            budget=0.0,
            processed=processed_prefix,
            first_alarm=adwin_alarm,
            target="feature_mean_shift",
            same_null_harm_comparator=False,
        )
    )

    for record in records:
        record.setdefault("first_alarm", None)
        record.setdefault("engine", "source_original")
        record["budget_rate"] = float(budget_rate)
        record["scheduled_onset"] = path.scheduled_onset
        record["onset_event"] = path.scheduled_onset - MONITOR_START
        record["target_budget"] = target_budget
    return records
