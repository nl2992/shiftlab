"""Bounded synthetic worlds with separate public events and evaluator truth.

G1 linear logistic, G2 nonlinear heterogeneous, G3 latent Markov/autoregressive,
and G4 clipped synthetic returns. No data files or network are used. All models
are fixed analytic predictors, not fitted with future outcomes. Decision losses
for all models are identifiable from a revealed label in this full-feedback DGP.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import expit
from scipy.stats import t as student_t

from shiftlab.data.decision_tasks import binary_action, binary_risk, bounded_position
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.generators import schedule
from shiftlab.monitoring import rbf_gamma, rbf_mmd_squared


FAMILIES = ("G1", "G2", "G3", "G4")
SCENARIOS = (
    "stationary",
    "benign_covariate",
    "harmful_concept",
    "risk_without_harm",
    "harm_without_accuracy",
    "incumbent_best",
    "transient_challenger",
    "challenger_optimal",
    "tied_models",
    "labels_too_expensive",
    "localized_harm",
    "gradual",
    "recurrent",
)
PROXIES = ("excellent", "moderate", "weak", "miscalibrated", "stale", "anti_informative")


@dataclass(frozen=True)
class WorldConfig:
    family: str = "G1"
    scenario: str = "harmful_concept"
    horizon: int = 512
    dimension: int = 6
    change_fraction: float = 0.4
    severity: float = 1.0
    proxy_quality: str = "stale"
    delay: int = 0
    delay_model: str = "fixed"
    missing_probability: float = 0.0
    label_cost: float = 0.001
    switch_cost: float = 0.01
    persistence: float = 0.97

    def __post_init__(self):
        if self.family not in FAMILIES or self.scenario not in SCENARIOS:
            raise ValueError("unknown generator family or scenario")
        for name, minimum in (("horizon", 100), ("dimension", 4), ("delay", 0)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if self.proxy_quality not in PROXIES:
            raise ValueError("unknown proxy quality")
        if self.delay_model not in ("fixed", "independent_random", "outcome_dependent"):
            raise ValueError("unknown delay model")
        numbers = (
            self.change_fraction,
            self.severity,
            self.missing_probability,
            self.label_cost,
            self.switch_cost,
            self.persistence,
        )
        if not np.isfinite(numbers).all() or any(isinstance(x, bool) for x in numbers):
            raise ValueError("numeric parameters must be finite and non-boolean")
        if not 0 < self.change_fraction < 0.85 or not 0 <= self.severity <= 1:
            raise ValueError("invalid change fraction or severity")
        if int(self.horizon * self.change_fraction) < 2:
            raise ValueError("at least two nominal observations are required")
        if not 0 <= self.missing_probability <= 1 or not 0 <= self.persistence < 1:
            raise ValueError("invalid missingness or persistence")
        if min(self.label_cost, self.switch_cost) < 0:
            raise ValueError("costs must be nonnegative")


@dataclass(frozen=True)
class PublicEvent:
    index: int
    features: tuple[float, ...]
    predictions: tuple[float, ...]
    actions: tuple[float, ...]
    proxy_predictive_losses: tuple[float, ...]
    proxy_decision_losses: tuple[float, ...]
    decision_cost: float
    label_cost: float
    switch_cost: float
    loss_bound: float = 1.0


@dataclass(frozen=True)
class EvaluatorTruth:
    """Never pass this object, its parent world, or its arrays to a learner."""

    outcomes: np.ndarray
    predictive_losses: np.ndarray
    decision_losses: np.ndarray
    expected_predictive_losses: np.ndarray
    expected_decision_losses: np.ndarray
    nominal_predictive_losses: np.ndarray
    nominal_decision_losses: np.ndarray
    regime_weight: np.ndarray
    hidden_state: np.ndarray
    availability: np.ndarray
    missing: np.ndarray
    feature_displacement: np.ndarray
    conditional_outcome_mean: np.ndarray
    nominal_outcome_mean: np.ndarray


@dataclass(frozen=True)
class SyntheticWorld:
    config: WorldConfig
    events: tuple[PublicEvent, ...]
    truth: EvaluatorTruth


def _regime(config: WorldConfig, seed: int) -> np.ndarray:
    pattern = {"transient_challenger": "temporary", "gradual": "linear", "recurrent": "hmm"}.get(
        config.scenario, "abrupt"
    )
    # Reuse the repository's independently tested schedule, without reading data.
    cfg = SyntheticConfig(
        n=config.horizon,
        d=config.dimension,
        seed=seed,
        scenario="concept",
        pattern=pattern,
        change_fraction=config.change_fraction,
        transition_fraction=0.25,
        severity=1,
    )
    weight, _ = schedule(cfg)
    if config.scenario in ("stationary", "tied_models"):
        weight = np.zeros(config.horizon)
    return weight * config.severity


def _markov(rng, size: int, persistence: float) -> np.ndarray:
    states = np.zeros(size, dtype=int)
    for i in range(1, size):
        states[i] = states[i - 1] ^ int(rng.random() > persistence)
    return states


def _binary_losses(predictions, actions, probability, weight):
    expected_prediction = (predictions - probability[:, None]) ** 2
    expected_prediction += (probability * (1 - probability))[:, None]
    expected_decision = binary_risk(
        np.maximum(actions, 0), probability[:, None], weight[:, None], weight[:, None]
    )
    # -1 denotes a fixed abstention action, distinct from a negative prediction.
    expected_decision = np.where(actions == -1, 0.2, expected_decision)
    return expected_prediction, expected_decision


def _return_cost(actions, returns, weight):
    pnl = actions * returns
    return 0.5 - 0.3 * pnl + 0.15 * weight * actions**2 + 0.05 * weight * np.maximum(-pnl, 0)


def make_world(config: WorldConfig, *, seed: int, partition: str = "development") -> SyntheticWorld:
    """Create an evaluator-owned world; confirmation is deliberately unavailable.

    A later freeze-gated entry point must create final confirmation worlds. This
    entry point supports source calibration and development only, with disjoint
    SeedSequence namespaces even when the same numeric seed is used.
    """
    partitions = {"source": 11, "development": 23}
    if partition not in partitions:
        raise ValueError("only source and development worlds are unlocked")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    streams = np.random.SeedSequence([partitions[partition], seed, FAMILIES.index(config.family)])
    feature_rng, label_rng, proxy_rng, delay_rng = [
        np.random.default_rng(s) for s in streams.spawn(4)
    ]
    n = config.horizon
    x = feature_rng.normal(size=(n, config.dimension))
    hidden = _markov(feature_rng, n, config.persistence)
    if config.family in ("G3", "G4"):
        rho = 0.6 if config.family == "G3" else 0.3
        for i in range(1, n):
            x[i, 0] = rho * x[i - 1, 0] + np.sqrt(1 - rho**2) * x[i, 0]
    if config.family == "G2":
        x[:, 2] = (feature_rng.random(n) < 0.1).astype(float)
        score = 2 * np.sin(x[:, 0]) + 0.8 * (x[:, 1] ** 2 - 1) - 0.6 * x[:, 2]
    elif config.family == "G4":
        score = 0.3 * np.tanh(x[:, 0]) - 0.1 * np.tanh(x[:, 1])
    else:
        score = 1.5 * x[:, 0] - 0.6 * x[:, 1]
    regime = _regime(config, seed + partitions[partition])
    # Independent source observations always use the nominal law and costs.
    if partition == "source":
        regime = np.zeros(n)
    feature_displacement = np.zeros(n)
    if config.scenario == "benign_covariate":
        x[:, -1] += 5 * regime
        feature_displacement = 5 * regime
    changed_score = score.copy()
    reversing = {
        "harmful_concept",
        "risk_without_harm",
        "transient_challenger",
        "challenger_optimal",
        "labels_too_expensive",
        "gradual",
        "recurrent",
    }
    if config.scenario in reversing:
        changed_score *= 1 - 2 * regime
    elif config.scenario == "incumbent_best":
        changed_score *= 1 + 0.4 * regime
    elif config.scenario == "localized_harm":
        group = x[:, 2] == 1 if config.family == "G2" else x[:, 2] > 1.645
        changed_score *= 1 - 2 * regime * group
    if config.scenario == "tied_models":
        score[:] = 0
        changed_score[:] = 0
    weight = np.full(n, 0.1)
    if config.scenario == "harm_without_accuracy":
        weight += 0.9 * regime
    if config.scenario == "localized_harm":
        weight = np.where(group, 1.0, 0.02)
    nominal_weight = np.where(config.scenario == "harm_without_accuracy", 0.1, weight)
    if config.family != "G4":
        offset = 0.4 * (2 * hidden - 1) if config.family == "G3" else 0
        probability, nominal = expit(changed_score + offset), expit(score + offset)
        predictions = np.column_stack((expit(score), expit(-score), np.full(n, 0.5)))
        if config.scenario == "tied_models":
            predictions[:] = 0.5
        actions = binary_action(predictions, 1.0, 1.0).astype(float)
        if config.scenario == "risk_without_harm":
            actions[:] = -1
        outcomes = (label_rng.random(n) < probability).astype(float)
        expected_prediction, expected_decision = _binary_losses(
            predictions, actions, probability, weight
        )
        nominal_prediction, nominal_decision = _binary_losses(
            predictions, actions, nominal, nominal_weight
        )
        predictive_losses = (predictions - outcomes[:, None]) ** 2
        decision_losses = np.where(
            actions == -1, 0.2, weight[:, None] * (actions != outcomes[:, None])
        )
        proxy_probability = expit(score)
        if config.proxy_quality in ("excellent", "moderate", "weak", "anti_informative"):
            # A cheap synthetic auxiliary annotator, jointly generated with Y.
            # Its reading arrives before a paid true label. This is explicitly
            # extra observable information, not access to an oracle probability.
            flip_rate = {
                "excellent": 0.05,
                "moderate": 0.25,
                "weak": 0.5,
                "anti_informative": 0.95,
            }[config.proxy_quality]
            reading = np.where(proxy_rng.random(n) < flip_rate, 1 - outcomes, outcomes)
            proxy_probability = 0.05 + 0.9 * reading
        elif config.proxy_quality == "miscalibrated":
            proxy_probability = expit(2 * score + 1)
        proxy_prediction, proxy_decision = _binary_losses(
            predictions, actions, proxy_probability, weight
        )
        conditional_mean, nominal_mean = probability, nominal
    else:
        # Finite quantile approximation is the actual DGP, making oracle moments
        # exact conditional on X and volatility, rather than a Gaussian claim.
        quantiles = student_t.ppf((np.arange(64) + 0.5) / 64, df=3)
        volatility = 0.08 + 0.12 * hidden
        support = np.clip(changed_score[:, None] + volatility[:, None] * quantiles, -1, 1)
        nominal_support = np.clip(score[:, None] + volatility[:, None] * quantiles, -1, 1)
        predictions = np.column_stack((score, -score, np.zeros(n)))
        actions = bounded_position(predictions, 0.04, risk_aversion=3.0, bound=1.0)
        if config.scenario == "risk_without_harm":
            actions[:] = 0
        outcomes = support[np.arange(n), label_rng.integers(64, size=n)]

        def expectation(values, cost):
            loss = ((predictions[:, :, None] - values[:, None, :]) ** 2).mean(axis=2) / 4
            decision = _return_cost(actions[:, :, None], values[:, None, :], cost[:, None, None])
            return loss, decision.mean(axis=2)

        expected_prediction, expected_decision = expectation(support, weight)
        nominal_prediction, nominal_decision = expectation(nominal_support, nominal_weight)
        predictive_losses = (predictions - outcomes[:, None]) ** 2 / 4
        decision_losses = _return_cost(actions, outcomes[:, None], weight[:, None])
        proxy_mean = score.copy()
        if config.proxy_quality in ("excellent", "moderate"):
            noise_scale = 0.03 if config.proxy_quality == "excellent" else 0.2
            proxy_mean = np.clip(outcomes + proxy_rng.normal(0, noise_scale, n), -1, 1)
        elif config.proxy_quality == "weak":
            proxy_mean = proxy_rng.uniform(-1, 1, n)
        elif config.proxy_quality == "miscalibrated":
            proxy_mean = np.clip(2 * proxy_mean + 0.2, -1, 1)
        elif config.proxy_quality == "anti_informative":
            proxy_mean = np.clip(-outcomes + proxy_rng.normal(0, 0.03, n), -1, 1)
        # Fixed nominal volatility, independent of hidden regime and outcomes.
        proxy_support = np.clip(proxy_mean[:, None] + 0.12 * quantiles, -1, 1)
        proxy_prediction, proxy_decision = expectation(proxy_support, weight)
        conditional_mean, nominal_mean = support.mean(axis=1), nominal_support.mean(axis=1)
    # Add small frozen model-estimation noise; never use current true outcomes.
    noise = proxy_rng.normal(0, 0.005, size=proxy_prediction.shape)
    proxy_prediction = np.clip(proxy_prediction + noise, 0, 1)
    proxy_decision = np.clip(proxy_decision + noise, 0, 1)
    delays = np.full(n, config.delay, dtype=int)
    if config.delay_model == "independent_random":
        delays = delay_rng.geometric(1 / (1 + config.delay), size=n) - 1
    elif config.delay_model == "outcome_dependent":
        threshold = 0.0 if config.family == "G4" else 0.5
        delays += (outcomes > threshold).astype(int) * max(1, config.delay)
    missing = delay_rng.random(n) < config.missing_probability
    label_cost = 2.0 if config.scenario == "labels_too_expensive" else config.label_cost
    events = tuple(
        PublicEvent(
            i,
            tuple(x[i]),
            tuple(predictions[i]),
            tuple(actions[i]),
            tuple(proxy_prediction[i]),
            tuple(proxy_decision[i]),
            float(weight[i]),
            label_cost,
            config.switch_cost,
        )
        for i in range(n)
    )
    arrays = (
        outcomes,
        predictive_losses,
        decision_losses,
        expected_prediction,
        expected_decision,
        nominal_prediction,
        nominal_decision,
        regime,
        hidden,
        np.arange(n) + delays,
        missing,
        feature_displacement,
        conditional_mean,
        nominal_mean,
    )
    for array in arrays:
        array.setflags(write=False)
    return SyntheticWorld(config, events, EvaluatorTruth(*arrays))


def summarize_world(world: SyntheticWorld) -> dict:
    """Evaluator-only diagnostics; never use for monitoring or query allocation."""
    truth = world.truth
    cut = int(world.config.horizon * world.config.change_fraction)
    features = np.array([event.features for event in world.events])
    reference, current = features[: min(cut, 128)], features[cut : cut + 128]
    feature_mmd = rbf_mmd_squared(reference, current, rbf_gamma(reference))
    return {
        "family": world.config.family,
        "scenario": world.config.scenario,
        "mean_feature_displacement": float(truth.feature_displacement.mean()),
        "feature_mmd2_unbiased": feature_mmd,
        "feature_mmd_interpretation": "descriptive_pre_post_no_test_calibration",
        "conditional_mean_displacement": float(
            np.abs(truth.conditional_outcome_mean - truth.nominal_outcome_mean).mean()
        ),
        "predictive_deterioration": float(
            (truth.expected_predictive_losses[:, 0] - truth.nominal_predictive_losses[:, 0]).mean()
        ),
        "decision_deterioration": float(
            (truth.expected_decision_losses[:, 0] - truth.nominal_decision_losses[:, 0]).mean()
        ),
        "challenger_benefit": float(
            (truth.expected_decision_losses[:, 0] - truth.expected_decision_losses[:, 1]).mean()
        ),
        "best_model_regret": float(
            (
                truth.expected_decision_losses[:, 0] - truth.expected_decision_losses.min(axis=1)
            ).mean()
        ),
        "proxy_predictive_loss_rmse": float(
            np.sqrt(
                np.mean(
                    (
                        np.array([e.proxy_predictive_losses for e in world.events])
                        - truth.predictive_losses
                    )
                    ** 2
                )
            )
        ),
        "contract": "bounded_full_feedback_no_causal_effect_of_action_on_outcome",
    }
