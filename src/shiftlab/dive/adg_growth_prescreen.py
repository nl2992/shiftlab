"""Analytic log-growth pre-screen for anchored, disagreement-gated harm monitors (G1).

The pre-screen computes the exact expected log-growth of fixed-stake betting factors over the
query coin and a working outcome law. It runs no monitor and draws no query or outcome. All inputs
come from the learner-visible train and validation slices of the hard-budget generator: actions,
the train-fitted classifier and ridge proxy, and the known label tariff. Oracle probabilities and
monitor-window events are never read. See ``docs/anchored_gated_harm_monitor_development_protocol.md``
Section 6.1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr
from sklearn.linear_model import LogisticRegression

from ..decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action
from .experiment import _binary_cost, _synthetic_label_costs
from .proxy import DecisionLossProxy

STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
GAMMAS = (0.0, 0.25, 0.5, 1.0)
PPE_LAMBDA = 0.1
DIAGNOSTIC_BOUND = 96.9


@dataclass(frozen=True)
class PrescreenConfig:
    n: int = 3200
    d: int = 16
    seeds: int = 20
    seed_offset: int = 58_000_000
    harm_margin: float = 0.10
    change_fraction: float = 0.5
    budget_rates: tuple[float, ...] = (0.02, 0.04, 0.06, 0.10, 0.20)
    primary_budget: float = 0.20
    target_excesses: tuple[float, ...] = (0.10, 0.178, 0.277)
    primary_excess: float = 0.277
    scenarios: tuple[str, ...] = ("boundary_local_harm", "stationary")
    primary_scenario: str = "boundary_local_harm"
    device: str = "cpu"

    def validate(self) -> PrescreenConfig:
        if self.n < 1000 or self.d < 2 or self.seeds < 1:
            raise ValueError("n must be >=1000, d >=2, and seeds >=1")
        if self.primary_budget not in self.budget_rates:
            raise ValueError("primary_budget must be one of budget_rates")
        if self.primary_excess not in self.target_excesses:
            raise ValueError("primary_excess must be one of target_excesses")
        if any(not 0 < rate <= 1 for rate in self.budget_rates):
            raise ValueError("budget rates must lie in (0, 1]")
        names = {scenario.name for scenario in SCENARIOS}
        if any(name not in names for name in self.scenarios):
            raise ValueError("scenarios must be registered scenario names")
        return self


@dataclass(frozen=True)
class LearnerSlice:
    """Learner-visible validation-slice quantities for one stream."""

    deployed: np.ndarray
    reference: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    probability_unfavourable: np.ndarray
    ridge_centered: np.ndarray
    residual_second_moment: np.ndarray
    tariff: np.ndarray
    fn: float
    fp: float

    @property
    def disagreement(self) -> np.ndarray:
        return self.deployed != self.reference


def conditional_support(
    deployed: np.ndarray, reference: np.ndarray, fn: float, fp: float
) -> tuple[np.ndarray, np.ndarray]:
    """Pre-outcome support ``[l, u]`` of the binary-cost paired difference ``c(a,Y)-c(b,Y)``."""
    deployed = np.asarray(deployed, dtype=int)
    reference = np.asarray(reference, dtype=int)
    if deployed.shape != reference.shape or not np.isin(deployed, [0, 1]).all():
        raise ValueError("actions must be binary arrays of equal shape")
    if not np.isin(reference, [0, 1]).all():
        raise ValueError("actions must be binary arrays of equal shape")
    difference_if_zero = fp * (deployed - reference).astype(float)
    difference_if_one = fn * (reference - deployed).astype(float)
    return (
        np.minimum(difference_if_zero, difference_if_one),
        np.maximum(difference_if_zero, difference_if_one),
    )


def unfavourable_outcome_is_positive(deployed: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """True where ``Y=1`` attains the upper support, i.e. is unfavourable to the deployed action."""
    return (np.asarray(deployed) == 0) & (np.asarray(reference) == 1)


def _increments(
    *,
    lower: np.ndarray,
    upper: np.ndarray,
    propensity: np.ndarray,
    anchor: np.ndarray,
    gated: bool,
    disagreement: np.ndarray,
    epsilon: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return centred increments indexed ``[event, D, Q]`` and query probabilities per event."""
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    q = np.asarray(propensity, dtype=float)
    anchor = np.asarray(anchor, dtype=float)
    active = np.ones_like(q, dtype=bool) if not gated else np.asarray(disagreement, dtype=bool)
    if np.any(active & ~((q > 0) & (q <= 1))):
        raise ValueError("queried events require propensities in (0, 1]")
    q_effective = np.where(active, q, 0.0)
    outcome = np.stack([lower, upper], axis=1) - epsilon
    centred_anchor = (anchor - epsilon)[:, None]
    safe_q = np.where(active, q, 1.0)[:, None]
    queried = centred_anchor + (outcome - centred_anchor) / safe_q
    unqueried = np.broadcast_to(centred_anchor, outcome.shape)
    values = np.stack([unqueried, queried], axis=2)
    values = np.where(active[:, None, None], values, -epsilon)
    return values, q_effective


def expected_increment_mean(
    *,
    lower: np.ndarray,
    upper: np.ndarray,
    probability_unfavourable: np.ndarray,
    propensity: np.ndarray,
    anchor: np.ndarray,
    gated: bool,
    disagreement: np.ndarray,
    epsilon: float,
) -> np.ndarray:
    """Exact per-event mean of the centred increment over outcome and query coins."""
    values, q = _increments(
        lower=lower,
        upper=upper,
        propensity=propensity,
        anchor=anchor,
        gated=gated,
        disagreement=disagreement,
        epsilon=epsilon,
    )
    weights = _joint_weights(probability_unfavourable, q)
    return np.sum(weights * values, axis=(1, 2))


def _joint_weights(probability_unfavourable: np.ndarray, q: np.ndarray) -> np.ndarray:
    p = np.asarray(probability_unfavourable, dtype=float)
    if np.any((p < 0) | (p > 1)):
        raise ValueError("probabilities must lie in [0, 1]")
    outcome_weights = np.stack([1 - p, p], axis=1)
    query_weights = np.stack([1 - q, q], axis=1)
    return outcome_weights[:, :, None] * query_weights[:, None, :]


def expected_log_growth(
    *,
    lower: np.ndarray,
    upper: np.ndarray,
    probability_unfavourable: np.ndarray,
    propensity: np.ndarray,
    anchor: np.ndarray,
    gated: bool,
    disagreement: np.ndarray,
    epsilon: float,
    bound: float,
    stakes: tuple[float, ...] = STAKES,
) -> np.ndarray:
    """Mean over events of ``E log(1 + s Hhat / bound)`` for each stake ``s``.

    Raises if any reachable factor is negative, i.e. if ``bound`` does not cover the lower tail
    of the increment for the given anchors and propensities.
    """
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError("bound must be finite and positive")
    values, q = _increments(
        lower=lower,
        upper=upper,
        propensity=propensity,
        anchor=anchor,
        gated=gated,
        disagreement=disagreement,
        epsilon=epsilon,
    )
    weights = _joint_weights(probability_unfavourable, q)
    reachable = weights > 0
    growth = []
    for stake in stakes:
        factors = 1 + stake * values / bound
        if np.any(reachable & (factors < -1e-12)):
            raise ValueError("bound does not cover the increment's lower tail")
        logs = np.log(np.where(reachable, np.maximum(factors, 1e-300), 1.0))
        growth.append(float(np.mean(np.sum(weights * logs, axis=(1, 2)))))
    return np.asarray(growth)


def solve_tilt(
    *,
    lower: np.ndarray,
    upper: np.ndarray,
    probability_unfavourable: np.ndarray,
    disagreement: np.ndarray,
    epsilon: float,
    target_excess: float,
) -> float:
    """Return ``eta`` such that ``p' = p + eta(1-p)`` on disagreements gives mean excess target.

    Agreement events have ``Z = 0``. A value above one means the target is unreachable by this
    working alternative.
    """
    active = np.asarray(disagreement, dtype=bool)
    width = np.asarray(upper, dtype=float) - np.asarray(lower, dtype=float)
    p = np.asarray(probability_unfavourable, dtype=float)
    base = float(np.mean(np.where(active, lower + width * p, 0.0))) - epsilon
    slope = float(np.mean(np.where(active, width * (1 - p), 0.0)))
    if slope <= 0:
        return float("inf")
    return (target_excess - base) / slope


def tilted_probability(
    probability_unfavourable: np.ndarray, disagreement: np.ndarray, eta: float
) -> np.ndarray:
    p = np.asarray(probability_unfavourable, dtype=float)
    return np.where(np.asarray(disagreement, dtype=bool), p + eta * (1 - p), p)


def spend_matched_propensity(
    score: np.ndarray,
    tariff: np.ndarray,
    *,
    target_spend: float,
    floor: float,
    ceiling: float = 1.0,
) -> np.ndarray:
    """Scale ``score`` so ``mean(q * tariff) = target_spend`` with ``q`` clipped to bounds."""
    score = np.asarray(score, dtype=float)
    tariff = np.asarray(tariff, dtype=float)
    if np.any(score < 0) or not 0 < floor <= ceiling <= 1:
        raise ValueError("scores must be nonnegative and 0 < floor <= ceiling <= 1")

    def spend(scale: float) -> float:
        return float(np.mean(np.clip(scale * score, floor, ceiling) * tariff))

    if spend(0.0) > target_spend + 1e-12:
        raise ValueError("propensity floor alone exceeds the target spend")
    high = 1.0
    while spend(high) < target_spend and high < 1e12:
        high *= 2
    low = 0.0
    for _ in range(200):
        middle = (low + high) / 2
        if spend(middle) < target_spend:
            low = middle
        else:
            high = middle
    return np.clip(high * score, floor, ceiling)


def learner_slice(scenario_name: str, seed: int, config: PrescreenConfig) -> LearnerSlice:
    """Rebuild the hard-budget generator's pre-monitor fits and return validation quantities."""
    scenario = next(item for item in SCENARIOS if item.name == scenario_name)
    base = ExperimentConfig(
        n=config.n,
        d=config.d,
        evaluation_seeds=1,
        calibration_seeds=2,
        calibration_start=max(800, int(config.n * 0.25)),
        window=64,
        stride=32,
        eprocess_epsilon=config.harm_margin,
        seed_offset=seed,
        change_fraction=config.change_fraction,
        device=config.device,
    )
    _, frame, _, _ = _generate(scenario, seed, base)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    fn, fp = float(scenario.fn_cost), float(scenario.fp_cost)
    train_end = max(100, int(config.n * 0.125))
    validation_end = max(800, int(config.n * 0.25))
    learner = slice(0, validation_end)
    x, y = x[learner], y[learner]
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    reference = _source_action(x, scenario)
    centred = _binary_cost(deployed, y, fn, fp) - _binary_cost(reference, y, fn, fp)
    centred = centred - config.harm_margin
    proxy = DecisionLossProxy(clip=max(fn, fp) + config.harm_margin, seed=seed, update_every=20)
    proxy.fit(x[:train_end], centred[:train_end], x[train_end:], centred[train_end:])
    classifier = LogisticRegression(max_iter=500, random_state=seed).fit(
        x[:train_end], y[:train_end]
    )
    validation = slice(train_end, validation_end)
    xv = x[validation]
    deployed_v, reference_v = deployed[validation], reference[validation]
    lower, upper = conditional_support(deployed_v, reference_v, fn, fp)
    p_positive = classifier.predict_proba(xv)[:, 1]
    positive_unfavourable = unfavourable_outcome_is_positive(deployed_v, reference_v)
    return LearnerSlice(
        deployed=deployed_v,
        reference=reference_v,
        lower=lower,
        upper=upper,
        probability_unfavourable=np.where(positive_unfavourable, p_positive, 1 - p_positive),
        ridge_centered=proxy.predict(xv),
        residual_second_moment=proxy.predict_residual_second_moment(xv),
        tariff=_synthetic_label_costs(xv),
        fn=fn,
        fp=fp,
    )


def arm_specifications(stream: LearnerSlice, budget: float, epsilon: float) -> dict[str, dict]:
    """Registered arms at matched expected label-dollar spend ``budget * mean(tariff)``."""
    n = len(stream.tariff)
    disagreement = stream.disagreement
    big_m = max(stream.fn, stream.fp) + epsilon
    max_abs = max(stream.fn, stream.fp)
    width = stream.upper - stream.lower
    # Registered constants: L = max(fn, fp) and W = fn + fp bound every action pair's support.
    support_drop = max(stream.fn, stream.fp)
    support_width = stream.fn + stream.fp
    target_spend = budget * float(np.mean(stream.tariff))
    gated_spend = float(np.mean(np.where(disagreement, stream.tariff, 0.0)))
    q_gated = 1.0 if gated_spend <= 0 else min(1.0, target_spend / gated_spend)
    uniform = np.full(n, budget)
    gated_q = np.full(n, q_gated)
    ridge_anchor = stream.ridge_centered + epsilon
    action_aware = stream.lower + width * stream.probability_unfavourable
    xu_floor = budget / 2
    xu_q = spend_matched_propensity(
        np.sqrt(stream.residual_second_moment),
        stream.tariff,
        target_spend=target_spend,
        floor=xu_floor,
    )
    arms: dict[str, dict] = {
        "a1_ppi_symmetric": {
            "propensity": uniform,
            "anchor": ridge_anchor,
            "gated": False,
            "bound": big_m * (2 / budget - 1),
        },
        "a1_ppi_symmetric_b96p9": {
            "propensity": uniform,
            "anchor": ridge_anchor,
            "gated": False,
            "bound": max(DIAGNOSTIC_BOUND, big_m * (2 / budget - 1)),
        },
        "a3_discern_gated": {
            "propensity": gated_q,
            "anchor": np.zeros(n),
            "gated": True,
            "bound": max_abs / q_gated + epsilon,
        },
        "a4_xu_active": {
            "propensity": xu_q,
            "anchor": ridge_anchor,
            "gated": False,
            "bound": big_m * (2 / xu_floor - 1),
        },
        "gated_ppi_symmetric": {
            "propensity": gated_q,
            "anchor": ridge_anchor,
            "gated": True,
            "bound": big_m * (2 / q_gated - 1),
        },
        "a10_ungated_gamma0": {
            "propensity": uniform,
            "anchor": stream.lower.copy(),
            "gated": False,
            "bound": support_drop + epsilon,
        },
    }
    ppe_floor = 2 * PPE_LAMBDA / (1 + PPE_LAMBDA)
    if budget >= ppe_floor:
        arms["a2_ppe_fixed_stake"] = {
            "propensity": uniform,
            "anchor": ridge_anchor,
            "gated": False,
            "bound": big_m * (2 / budget - 1),
            "stakes": (PPE_LAMBDA * (2 / budget - 1),),
        }
    for gamma in GAMMAS:
        arms[f"adg_gamma{gamma:g}"] = {
            "propensity": gated_q,
            "anchor": stream.lower + gamma * (action_aware - stream.lower),
            "gated": True,
            "bound": support_drop + gamma * support_width * (1 / q_gated - 1) + epsilon,
        }
    for spec in arms.values():
        spec.setdefault("stakes", STAKES)
        spec["q_gated"] = q_gated
    return arms


def prescreen_stream(scenario_name: str, replicate: int, config: PrescreenConfig) -> list[dict]:
    """Rows of exact expected growth for every budget, working alternative, and arm."""
    seed = config.seed_offset + replicate
    stream = learner_slice(scenario_name, seed, config)
    epsilon = config.harm_margin
    disagreement = stream.disagreement
    rows = []
    laws: list[tuple[str, float | None, float]] = [("natural", None, 0.0)]
    for excess in config.target_excesses:
        eta = solve_tilt(
            lower=stream.lower,
            upper=stream.upper,
            probability_unfavourable=stream.probability_unfavourable,
            disagreement=disagreement,
            epsilon=epsilon,
            target_excess=excess,
        )
        laws.append(("alternative", excess, eta))
    for budget in config.budget_rates:
        arms = arm_specifications(stream, budget, epsilon)
        for law, target, eta in laws:
            feasible = bool(0 <= eta <= 1) if law == "alternative" else True
            probability = tilted_probability(
                stream.probability_unfavourable, disagreement, min(max(eta, 0.0), 1.0)
            )
            for arm, spec in arms.items():
                common = {
                    "lower": stream.lower,
                    "upper": stream.upper,
                    "probability_unfavourable": probability,
                    "propensity": spec["propensity"],
                    "anchor": spec["anchor"],
                    "gated": spec["gated"],
                    "disagreement": disagreement,
                    "epsilon": epsilon,
                }
                growth = expected_log_growth(**common, bound=spec["bound"], stakes=spec["stakes"])
                mean_increment = float(np.mean(expected_increment_mean(**common)))
                queried = np.where(disagreement | (not spec["gated"]), spec["propensity"], 0.0)
                best = int(np.argmax(growth))
                rows.append(
                    {
                        "scenario": scenario_name,
                        "seed": seed,
                        "budget_rate": budget,
                        "law": law,
                        "target_excess": target,
                        "eta": eta,
                        "feasible": feasible,
                        "arm": arm,
                        "bound": float(spec["bound"]),
                        "best_growth": float(growth[best]),
                        "best_stake": float(spec["stakes"][best]),
                        "stake_at_cap": bool(best == len(spec["stakes"]) - 1),
                        "mean_increment": mean_increment,
                        "expected_labels_per_event": float(np.mean(queried)),
                        "expected_spend_per_event": float(np.mean(queried * stream.tariff)),
                        "target_spend_per_event": budget * float(np.mean(stream.tariff)),
                        "disagreement_rate": float(np.mean(disagreement)),
                        "q_gated": float(spec["q_gated"]),
                        "positive_unfavourable_share": float(
                            np.mean(
                                unfavourable_outcome_is_positive(
                                    stream.deployed[disagreement], stream.reference[disagreement]
                                )
                            )
                        )
                        if disagreement.any()
                        else float("nan"),
                        "mean_probability_unfavourable_disagreement": float(
                            np.mean(stream.probability_unfavourable[disagreement])
                        )
                        if disagreement.any()
                        else float("nan"),
                    }
                )
    return rows


def mixture_rows(rows: list[dict]) -> list[dict]:
    """Add ``adg_gamma_mix``: a fixed mixture's asymptotic growth is its best component's."""
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        if row["arm"].startswith("adg_gamma"):
            key = (
                row["scenario"],
                row["seed"],
                row["budget_rate"],
                row["law"],
                row["target_excess"],
            )
            groups.setdefault(key, []).append(row)
    added = []
    for members in groups.values():
        best = max(members, key=lambda item: item["best_growth"])
        mixture = dict(best)
        mixture["arm"] = "adg_gamma_mix"
        mixture["best_gamma_component"] = best["arm"]
        added.append(mixture)
    return rows + added
