"""Registered disagreement-gating comparison; learner replay has no oracle inputs."""

from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass, replace

import numpy as np
from river import drift
from scipy.special import ndtr
from sklearn.linear_model import LogisticRegression

from ..decision_harm_experiment import (
    SCENARIOS,
    ExperimentConfig,
    _generate,
    _source_action,
    statistical_harm_onset,
)
from .comparison_betting_engines import replay_engine
from .eprocess import (
    PredictableBoundMeanEProcess,
    PredictablePlugInEmpiricalBernsteinEProcess,
)
from .experiment import _binary_cost, _material_harm_onset, _synthetic_label_costs
from .hard_budget import HardBudgetConfig, _one_method
from .predictable_bound_replay import DEFAULT_STAKES, replay_mixture_log_e
from .prediction_powered_evalues import prediction_powered_factor
from .proxy import DecisionLossProxy
from .xu_active_betting import xu_maximum_stake, xu_paired_betting_factor

GATED_ARMS = ("gated_ht_paced", "gated_ht_fixed", "gated_ppi_paced", "gated_eb_paced")
COMPARISON_ENGINES = ("fixed1", "plugin", "timans_approx_grapa", "timans_grapa")


def feature_adwin_alarm(x: np.ndarray, monitor_start: int, processed: int) -> int | None:
    """Label-free feature-mean sentinel; its target is not paired decision harm.

    Use the existing River ADWIN family on bounded Gaussian-CDF feature transforms,
    with a prespecified conservative nominal delta across coordinates/calendar positions.
    Empirical stationary-null calibration remains required; delta alone is not a proof.
    """
    values = np.asarray(x, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).all() or values.shape[1] < 1:
        raise ValueError("features must be a finite matrix")
    if not 0 <= monitor_start < len(values) or not 0 <= processed <= len(values) - monitor_start:
        raise ValueError("invalid sentinel monitoring prefix")
    detectors = [
        drift.ADWIN(delta=0.05 / (values.shape[1] * len(values))) for _ in range(values.shape[1])
    ]
    for index, row in enumerate(ndtr(values[: monitor_start + processed])):
        alarmed = False
        for detector, feature in zip(detectors, row, strict=True):
            detector.update(float(feature))
            alarmed |= detector.drift_detected
        if index >= monitor_start and alarmed:
            return index - monitor_start
    return None


def gated_increment(
    *,
    disagreement: bool,
    observed_cost: float | None,
    propensity: float,
    anchor: float = 0.0,
    epsilon: float = 0.1,
) -> float:
    """A missing label contributes the anchor; agreements have exactly known cost zero."""
    if not 0 < propensity <= 1 or not np.isfinite(anchor) or not np.isfinite(epsilon):
        raise ValueError("propensity, anchor, and epsilon must be finite and in range")
    if not disagreement:
        if observed_cost is not None:
            raise ValueError("agreement events must not query a label")
        return -epsilon
    if observed_cost is not None and not np.isfinite(observed_cost):
        raise ValueError("observed cost must be finite")
    return (
        anchor
        - epsilon
        + ((observed_cost - anchor) / propensity if observed_cost is not None else 0.0)
    )


class DisagreementPacer:
    """The registered 200-event past-only tariff window, seeded from validation."""

    def __init__(self, validation_disagreement, validation_tariffs, budget_rate: float):
        costs = np.asarray(validation_tariffs, dtype=float)
        active = np.asarray(validation_disagreement, dtype=bool)
        if costs.ndim != 1 or active.shape != costs.shape or not len(costs):
            raise ValueError("validation actions and tariffs must be matching nonempty vectors")
        if not np.isfinite(costs).all() or np.any((costs < 0.5) | (costs > 2.5)):
            raise ValueError("tariffs must lie in [0.5, 2.5]")
        if not np.isfinite(budget_rate) or not 0 < budget_rate <= 1:
            raise ValueError("budget rate must lie in (0,1]")
        self.target = budget_rate * float(costs.mean())
        self.window = deque((active * costs)[-200:], maxlen=200)
        self.fixed = float(min(1.0, self.target / max(float(np.mean(active * costs)), 1e-6)))

    @property
    def propensity(self) -> float:
        return float(np.clip(self.target / max(float(np.mean(self.window)), 1e-6), 0.10, 1))

    def observe(self, disagreement: bool, tariff: float) -> None:
        if not np.isfinite(tariff) or not 0.5 <= tariff <= 2.5:
            raise ValueError("tariff must lie in [0.5, 2.5]")
        self.window.append(float(disagreement) * tariff)


@dataclass
class GatedReplay:
    increments: np.ndarray
    bounds: np.ndarray
    propensities: np.ndarray
    queried: np.ndarray
    log_e: np.ndarray
    component_log_gains: np.ndarray
    dollars: float
    budget: float
    first_alarm: int | None


def paired_growth(first: np.ndarray, second: np.ndarray, onset: int | None) -> dict:
    """Best fixed-stake growth for both arms on their common post-onset prefix."""
    end = min(len(first), len(second))
    available = onset is not None and end > onset
    return {
        "prefix": end,
        "first": float(np.max(first[onset:end].mean(axis=0))) if available else None,
        "second": float(np.max(second[onset:end].mean(axis=0))) if available else None,
    }


def replay_gated(
    *,
    arm: str,
    x: np.ndarray,
    paired_cost: np.ndarray,
    disagreement: np.ndarray,
    tariffs: np.ndarray,
    uniforms: np.ndarray,
    validation_disagreement: np.ndarray,
    validation_tariffs: np.ndarray,
    budget_rate: float,
    proxy_template: DecisionLossProxy | None = None,
    epsilon: float = 0.1,
    alpha: float = 0.05,
) -> GatedReplay:
    """Replay one arm with a predictable reserve stop and immediate queried feedback.

    Cost entries are accessed only on queried disagreements. Current outcomes never enter
    pacing, support bounds, or query decisions. Evaluator diagnostics belong to the caller.
    """
    if arm not in GATED_ARMS:
        raise ValueError("unknown gated arm")
    features = np.asarray(x, dtype=float)
    costs, active, prices, coins = (
        np.asarray(paired_cost, dtype=float),
        np.asarray(disagreement, dtype=bool),
        np.asarray(tariffs, dtype=float),
        np.asarray(uniforms, dtype=float),
    )
    if features.ndim != 2 or not len(features) or not np.isfinite(features).all():
        raise ValueError("features must be a nonempty finite matrix")
    if any(a.shape != (len(features),) for a in (costs, active, prices, coins)):
        raise ValueError("event arrays must match features")
    if not np.isfinite(prices).all() or np.any((prices < 0.5) | (prices > 2.5)):
        raise ValueError("tariffs must lie in [0.5,2.5]")
    if not np.isfinite(coins).all() or np.any((coins < 0) | (coins >= 1)):
        raise ValueError("query uniforms must lie in [0,1)")
    if not np.isfinite(epsilon) or epsilon < 0:
        raise ValueError("epsilon must be finite and nonnegative")
    pacer = DisagreementPacer(validation_disagreement, validation_tariffs, budget_rate)
    proxy = copy.deepcopy(proxy_template) if arm == "gated_ppi_paced" else None
    if arm == "gated_ppi_paced" and proxy is None:
        raise ValueError("PPI requires a fitted proxy")
    if proxy is not None and proxy.clip > 5 + epsilon:
        raise ValueError("proxy clip exceeds the registered support bound")
    process = PredictableBoundMeanEProcess(alpha=alpha)
    # Applying the existing fixed [−1,1] engine to H/B gives the registered affine map.
    eb = PredictablePlugInEmpiricalBernsteinEProcess(bound=1.0, alpha=alpha)
    budget = pacer.target * len(features)
    spent = 0.0
    increments, bounds, propensities, queried, log_e, gains = [], [], [], [], [], []
    for i in range(len(features)):
        if budget - spent + 1e-12 < 2.5:
            break
        q = pacer.fixed if arm == "gated_ht_fixed" else pacer.propensity
        bound = ((5 + epsilon) * (2 / q - 1)) if proxy is not None else (5 / q + epsilon)
        anchor = float(proxy.predict(features[i : i + 1])[0]) + epsilon if proxy else 0.0
        query = bool(active[i] and coins[i] < q)
        observed = float(costs[i]) if query else None
        if query and (not np.isfinite(observed) or abs(observed) > 5):
            raise ValueError("observed paired cost must lie in [−5,5]")
        value = gated_increment(
            disagreement=bool(active[i]),
            observed_cost=observed,
            propensity=q,
            anchor=anchor,
            epsilon=epsilon,
        )
        # A clipped PPI anchor makes the support bound exactly tight; snap pure rounding only.
        if abs(value) > bound:
            if abs(value) - bound > 1e-9 * bound:
                raise ValueError("increment exceeds its predictable support bound")
            value = float(np.copysign(bound, value))
        current_log_e = (
            eb.update(value / bound)
            if arm == "gated_eb_paced"
            else process.update(value, bound=bound)
        )
        if query:
            spent += float(prices[i])
            if proxy is not None:
                proxy.observe(features[i], observed - epsilon)
        increments.append(value)
        bounds.append(bound)
        propensities.append(q)
        queried.append(query)
        log_e.append(current_log_e)
        gains.append(np.log1p(np.asarray(DEFAULT_STAKES) * value / bound))
        pacer.observe(bool(active[i]), float(prices[i]))
    hits = np.flatnonzero(np.asarray(log_e) >= -np.log(alpha))
    return GatedReplay(
        np.asarray(increments),
        np.asarray(bounds),
        np.asarray(propensities),
        np.asarray(queried, dtype=bool),
        np.asarray(log_e),
        np.asarray(gains),
        spent,
        budget,
        int(hits[0]) if len(hits) else None,
    )


def comparison_seed(scenario_name: str, seed: int, budget_rate: float, device: str) -> list[dict]:
    """Generate one shared path; evaluator truth is used only for summary endpoints."""
    scenario = next(s for s in SCENARIOS if s.name == scenario_name)
    config = HardBudgetConfig(
        budget_rate=budget_rate,
        q_min=budget_rate / 2,
        q_max=0.8,
        device=device,
        generate_figure=False,
    ).validate()
    base = ExperimentConfig(
        n=3200,
        d=16,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=800,
        window=64,
        stride=32,
        alpha=0.05,
        eprocess_epsilon=0.1,
        seed_offset=seed,
        change_fraction=0.5,
        device=device,
    )
    _, frame, oracle, timing = _generate(scenario, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    if scenario.harmful_adaptation:
        deployed[1600:] = 1
    reference = _source_action(x, scenario)
    active = deployed != reference
    tariffs = _synthetic_label_costs(x)
    fn, fp = scenario.fn_cost, scenario.fp_cost
    paired = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centered = paired - 0.1
    proxy = DecisionLossProxy(clip=5.1, seed=seed, update_every=20).fit(
        x[:400],
        centered[:400],
        x[400:800],
        centered[400:800],
    )
    classifier = LogisticRegression(max_iter=500, random_state=seed).fit(x[:400], y[:400])
    uniforms = np.random.default_rng(seed + 9_173).random(3200)
    # These quantities stay in this evaluator; no oracle field enters replay_gated.
    probability = oracle.probability_positive.to_numpy(dtype=float)
    expected = np.where(deployed == 1, fp * (1 - probability), fn * probability) - np.where(
        reference == 1,
        fp * (1 - probability),
        fn * probability,
    )
    path_onset = _material_harm_onset(
        expected,
        0.1,
        change_times=timing["change_times"],
        monitor_start=800,
    )
    onset = statistical_harm_onset(scenario_name, path_onset)
    paths: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    records = []
    common = {
        "seed": seed,
        "scenario": scenario,
        "x": x,
        "gross_cost_difference": paired,
        "centered_cost_difference": centered,
        "expected_cost_difference": expected,
        "label_costs": tariffs,
        "classifier": classifier,
        "proxy_template": proxy,
        "train_end": 400,
        "monitor_start": 800,
        "harm_onset": onset,
        "sample_path_material_harm": path_onset is not None,
        "sample_path_harm_onset": path_onset,
        "common_uniforms": uniforms,
        "contrast_zero": _binary_cost(deployed, np.zeros_like(y), fn, fp)
        - _binary_cost(reference, np.zeros_like(y), fn, fp)
        - 0.1,
        "contrast_one": _binary_cost(deployed, np.ones_like(y), fn, fp)
        - _binary_cost(reference, np.ones_like(y), fn, fp)
        - 0.1,
    }
    ungated = [("uniform_ppi", "uniform_proxy"), ("variance_ppi", "variance_proxy")]
    if budget_rate == 0.2:
        ungated.append(("uniform_ppi_common96p9", "uniform_proxy"))
    for name, method in ungated:
        traces = []
        local = replace(config, common_eprocess_bound=name.endswith("common96p9"))
        result = _one_method(method=method, config=local, event_trace_rows=traces, **common)
        values = np.asarray([t["monitor_increment"] for t in traces])
        bound = float(result["eprocess_support_bound"])
        gains = np.log1p(values[:, None] * np.asarray(DEFAULT_STAKES) / bound)
        paths[name] = (values, np.full(len(values), bound), gains)
        records.append(
            {
                "arm": name,
                "first_alarm": result["single_e_alarm_time"],
                "labels": result["labels_queried"],
                "dollars": result["realized_label_spend"],
                "budget": result["hard_budget"],
                "processed": len(values),
                "q_min": result["query_propensity_min"],
                "q_mean": result["query_propensity_mean"],
                "q_max": result["query_propensity_max"],
            }
        )
        if name in {"uniform_ppi", "variance_ppi"}:
            floor = float(result["eprocess_minimum_propensity"])
            base_stake = 0.9 / (2 / floor - 1)
            source_factors = []
            for trace in traces:
                h = float(trace["proxy_prediction"])
                queried = bool(trace["queried"])
                observed = trace["learner_observed_excess_cost"] if queried else None
                if name == "uniform_ppi":
                    factor = prediction_powered_factor(
                        proxy_factor=1 + base_stake * h / 5.1,
                        queried=queried,
                        propensity=trace["propensity"],
                        lower=1 - base_stake,
                        upper=1 + base_stake,
                        observed_factor=1 + base_stake * observed / 5.1 if queried else None,
                    )
                else:
                    factor = xu_paired_betting_factor(
                        proxy_excess_cost=h,
                        queried=queried,
                        propensity=trace["propensity"],
                        stake=0.9 * xu_maximum_stake(minimum_propensity=floor),
                        bound=5.1,
                        observed_excess_cost=observed,
                    )
                source_factors.append(factor)
            np.testing.assert_allclose(source_factors, 1 + 0.9 * values / bound, atol=1e-12)
            logs = np.cumsum(np.log(source_factors))
            hits = np.flatnonzero(logs >= -np.log(0.05))
            alias = dict(records[-1])
            alias.update(
                arm="ppe_uniform" if name == "uniform_ppi" else "xu_active",
                engine="source_fixed0p9",
                first_alarm=int(hits[0]) if len(hits) else None,
                algebraic_path_alias=name,
            )
            records.append(alias)
    for name in GATED_ARMS:
        result = replay_gated(
            arm=name,
            x=x[800:],
            paired_cost=paired[800:],
            disagreement=active[800:],
            tariffs=tariffs[800:],
            uniforms=uniforms[:2400],
            validation_disagreement=active[400:800],
            validation_tariffs=tariffs[400:800],
            budget_rate=budget_rate,
            proxy_template=proxy,
        )
        paths[name] = (result.increments, result.bounds, result.component_log_gains)
        records.append(
            {
                "arm": name,
                "first_alarm": result.first_alarm,
                "labels": int(result.queried.sum()),
                "dollars": result.dollars,
                "budget": result.budget,
                "processed": len(result.increments),
                "q_min": float(result.propensities.min()),
                "q_mean": float(result.propensities.mean()),
                "q_max": float(result.propensities.max()),
            }
        )
        if name == "gated_ppi_paced":
            source_factors = 1 + 0.9 * result.increments / result.bounds
            if np.any(source_factors <= 0):
                raise RuntimeError("PPE support-shrunk factors must remain positive")
            hits = np.flatnonzero(np.cumsum(np.log(source_factors)) >= -np.log(0.05))
            alias = dict(records[-1])
            alias.update(
                arm="ppe_gated",
                engine="source_fixed0p9",
                algebraic_path_alias=name,
                first_alarm=int(hits[0]) if len(hits) else None,
            )
            records.append(alias)
    full = replay_mixture_log_e(centered[800:], 5.1, alpha=0.05)
    paths["full_feedback"] = (
        centered[800:],
        np.full(2400, 5.1),
        np.log1p(centered[800:, None] * np.asarray(DEFAULT_STAKES) / 5.1),
    )
    hits = np.flatnonzero(full >= -np.log(0.05))
    records.append(
        {
            "arm": "full_feedback",
            "first_alarm": int(hits[0]) if len(hits) else None,
            "labels": 2400,
            "dollars": float(tariffs[800:].sum()),
            "budget": None,
            "processed": 2400,
            "q_min": 1.0,
            "q_mean": 1.0,
            "q_max": 1.0,
        }
    )
    for original in list(records):
        original.setdefault("engine", "pm_eb" if original["arm"] == "gated_eb_paced" else "fixed08")
        name = original["arm"]
        if name not in paths or name == "gated_eb_paced":
            continue
        values, bounds, _ = paths[name]
        for engine in COMPARISON_ENGINES:
            logs = replay_engine(values, bounds, engine)
            hits = np.flatnonzero(logs >= -np.log(0.05))
            variant = dict(original)
            variant.update(
                arm=f"{name}__{engine}",
                base_arm=name,
                engine=engine,
                first_alarm=int(hits[0]) if len(hits) else None,
            )
            records.append(variant)
    records.append(
        {
            "arm": "no_action",
            "engine": "none",
            "first_alarm": None,
            "labels": 0,
            "dollars": 0.0,
            "budget": config.budget_rate * float(tariffs[400:800].mean()) * 2400,
            "processed": 2400,
            "q_min": 0.0,
            "q_mean": 0.0,
            "q_max": 0.0,
        }
    )
    sentinel_prefix = min(
        r["processed"] for r in records if r["arm"] in {"uniform_ppi", "gated_ht_paced"}
    )
    sentinel_alarm = feature_adwin_alarm(x, 800, sentinel_prefix)
    records.append(
        {
            "arm": "feature_adwin",
            "engine": "river_adwin",
            "first_alarm": sentinel_alarm,
            "labels": 0,
            "dollars": 0.0,
            "budget": 0.0,
            "processed": sentinel_prefix,
            "q_min": 0.0,
            "q_mean": 0.0,
            "q_max": 0.0,
            "nominal_delta": 0.05 / (16 * 3200),
            "target": "feature_mean_shift",
            "same_null_harm_comparator": False,
        }
    )
    for row in records:
        alarm = row["first_alarm"]
        processed = row["processed"]
        detected = alarm is not None and onset is not None and alarm >= onset
        end = alarm + 1 if alarm is not None else processed
        row.update(
            scenario=scenario_name,
            seed=seed,
            budget_rate=budget_rate,
            onset=onset,
            detected=detected,
            false_alarm=alarm is not None and (onset is None or alarm < onset),
            censored_delay=(alarm - onset if detected else max(0, 2400 - onset))
            if onset is not None
            else None,
            excess_cost_before_alarm=float(centered[800 : 800 + end].sum()),
            disagreement_pre=float(active[800:1600].mean()),
            disagreement_post=float(active[1600:].mean()),
        )
        if row["arm"] == "feature_adwin":
            feature_onset = 800 if scenario_name == "benign_nuisance" else None
            row["harm_alarm_coincidence"] = row["detected"]
            row["feature_detected"] = (
                alarm is not None and feature_onset is not None and alarm >= feature_onset
            )
            row["feature_false_alarm"] = alarm is not None and (
                feature_onset is None or alarm < feature_onset
            )
            row["detected"] = row["feature_detected"]
            row["false_alarm"] = row["feature_false_alarm"]
            row["onset"] = feature_onset
            row["censored_delay"] = (
                (alarm - feature_onset if row["feature_detected"] else max(0, 2400 - feature_onset))
                if feature_onset is not None
                else None
            )
        if row["arm"] in paths and row["arm"] != "gated_eb_paced":
            for other, (_, _, gains) in paths.items():
                if other == "gated_eb_paced":
                    continue
                pair = paired_growth(paths[row["arm"]][2], gains, onset)
                row[f"growth_vs_{other}"] = pair["first"]
                row[f"comparator_growth_{other}"] = pair["second"]
                row[f"common_prefix_{other}"] = pair["prefix"]
    return records
