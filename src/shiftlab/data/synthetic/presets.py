"""Named, reviewable scenario catalogues for decision and conformal stress tests."""

from collections.abc import Mapping
from dataclasses import dataclass

from ..schemas import SyntheticConfig
from .generators import SCENARIOS


def _config(
    scenario: str, *, n: int, seed: int, parameters: Mapping[str, object]
) -> SyntheticConfig:
    values: dict[str, object] = {"scenario": scenario, "n": n, "seed": seed}
    values.update(parameters)
    return SyntheticConfig.model_validate(values)


@dataclass(frozen=True)
class DecisionStressPreset:
    name: str
    config: SyntheticConfig
    policy_class: str
    loss: str
    oracle_policy: str
    learner_visible_context: str
    expected_relation: str


@dataclass(frozen=True)
class ConformalStressPreset:
    name: str
    config: SyntheticConfig
    calibration_target_scope: str
    oracle_radius_scope: str
    residual_law: str
    stress: str


def decision_stress_catalogue(*, seed: int = 42, n: int = 12000):
    """Return all ten required decision-relevant versus irrelevant shift cases."""
    definitions: list[tuple[str, str, dict[str, object], str, str, str, str]] = [
        (
            "large_feature_shift_preserves_decisions",
            "irrelevant",
            {"d": 2, "severity": 5.0},
            "Binary action on a regression threshold",
            "FN/FP weighted zero-one loss; equal costs for this nuisance-only case",
            "Choose action 1 when the oracle event probability exceeds the disclosed cost threshold.",
            "X1 moves strongly; it has zero outcome coefficient and decisions remain fixed.",
        ),
        (
            "small_feature_shift_changes_decisions",
            "small_decision_covariate",
            {"d": 2, "severity": 1.0},
            "Binary classification action",
            "Symmetric zero-one loss",
            "Choose action 1 when P(Y=1|X) exceeds 0.5.",
            "A small X0 displacement crosses the steep logistic decision boundary.",
        ),
        (
            "shift_concentrated_near_decision_boundary",
            "boundary_local",
            {"d": 2, "severity": 2.0},
            "Binary action on a regression threshold",
            "FN/FP weighted zero-one loss with disclosed costs",
            "Choose the lower expected-cost action from the conditional outcome law.",
            "The response changes most near the original zero-mean decision boundary.",
        ),
        (
            "shift_in_low_importance_features",
            "irrelevant",
            {"d": 8, "severity": 4.0},
            "Binary action on a regression threshold",
            "FN/FP weighted zero-one loss with disclosed costs",
            "Choose the lower expected-cost action from the conditional outcome law.",
            "The last feature moves while its true outcome coefficient is zero.",
        ),
        (
            "rare_but_high_cost_outcomes",
            "rare_high_cost",
            {"d": 2, "severity": 0.2},
            "Binary classification action",
            "FN=1000, FP=1 weighted zero-one loss",
            "The cost matrix is disclosed in decision_context; action uses the exact event probability.",
            "Rare positive outcomes receive a large false-negative cost.",
        ),
        (
            "asymmetric_false_positive_false_negative_costs",
            "cost_change",
            {"d": 2, "severity": 2.0},
            "Binary action on a regression threshold",
            "Regime-varying FN cost and unit FP cost",
            "The current cost matrix is disclosed at prediction time.",
            "A changed, declared asymmetric cost changes the preferred decision threshold.",
        ),
        (
            "optimal_decision_threshold_changes",
            "cost_change",
            {"d": 2, "severity": 3.0},
            "Binary action on a regression threshold",
            "Regime-varying FN cost and unit FP cost",
            "The cost matrix is disclosed at prediction time; use the exact conditional law.",
            "The oracle threshold changes because the false-negative cost changes.",
        ),
        (
            "feasible_action_constraints_change",
            "constraints",
            {"d": 2, "severity": 1.0},
            "Binary action with a hard feasibility constraint",
            "Minimum expected cost over feasible actions only",
            "Action-1 feasibility is disclosed in decision_context.",
            "Action 1 becomes infeasible after activation, regardless of its unconstrained risk.",
        ),
        (
            "prediction_degradation_without_decision_degradation",
            "prediction_only",
            {"d": 2, "severity": 2.0},
            "Binary action on a regression threshold",
            "Symmetric FN/FP weighted zero-one loss",
            "Choose action 1 when the oracle event probability exceeds 0.5.",
            "Positive rescaling worsens probability accuracy while preserving the sign threshold.",
        ),
        (
            "decision_degradation_with_small_global_prediction_change",
            "rare_high_cost",
            {"d": 2, "severity": 1.0},
            "Binary classification action",
            "FN=1000, FP=1 weighted zero-one loss",
            "The asymmetric cost matrix is disclosed and the oracle uses exact event probabilities.",
            "Rare-event changes can raise decision regret with a small global probability-score change.",
        ),
    ]
    return tuple(
        DecisionStressPreset(
            name=name,
            config=_config(scenario, n=n, seed=seed, parameters=parameters),
            policy_class=policy,
            loss=loss,
            oracle_policy=oracle,
            learner_visible_context="The generated request exposes only declared decision_context; evaluator oracle stays separate.",
            expected_relation=relation,
        )
        for name, scenario, parameters, policy, loss, oracle, relation in definitions
    )


def conformal_stress_catalogue(*, seed: int = 42, n: int = 12000):
    """Return named conformal stress cases with explicit marginal/conditional targets."""
    definitions: list[tuple[str, str, dict[str, object], str, str, str]] = [
        (
            "homoskedastic_residuals",
            "iid_regression",
            {},
            "marginal",
            "constant marginal Gaussian residual radius",
            "Gaussian errors with fixed variance.",
        ),
        (
            "abrupt_residual_variance_increase",
            "target_variance",
            {"severity": 2.0, "pattern": "abrupt"},
            "conditional",
            "per-time conditional Gaussian radius",
            "Variance increases abruptly at the configured regime boundary.",
        ),
        (
            "gradual_residual_variance_increase",
            "target_variance",
            {"severity": 2.0, "pattern": "linear"},
            "conditional",
            "per-time conditional Gaussian radius",
            "Variance changes over the recorded linear transition interval.",
        ),
        (
            "abrupt_concept_coefficient_change",
            "concept",
            {"severity": 2.0, "pattern": "abrupt"},
            "conditional",
            "per-time conditional Gaussian residual radius",
            "The conditional mean coefficient changes abruptly while Gaussian noise variance stays fixed.",
        ),
        (
            "conditional_heteroskedasticity",
            "conditional_variance",
            {"severity": 1.0},
            "conditional",
            "radius conditional on observed X0",
            "Gaussian scale depends on the absolute first feature.",
        ),
        (
            "heavy_tailed_residuals",
            "heavy_tailed",
            {},
            "marginal",
            "marginal standardized Student-t(5) radius",
            "Stationary finite-variance Student-t(5) errors.",
        ),
        (
            "asymmetric_residuals",
            "asymmetric_errors",
            {},
            "marginal",
            "marginal centered-lognormal absolute-residual radius",
            "Stationary centered, variance-normalized lognormal errors.",
        ),
        (
            "time_dependent_residuals",
            "dependent_errors",
            {},
            "marginal",
            "stationary marginal Gaussian radius; dependence-aware inference required",
            "Stationary AR(1) errors with configured rho.",
        ),
        (
            "hidden_regime_variance_switching",
            "hidden_variance",
            {"severity": 1.5},
            "marginal",
            "report global marginal target and evaluator-only regime-conditional radii separately",
            "The regime is hidden from the learner while conditional scale changes by regime.",
        ),
        (
            "intermittent_extreme_events",
            "extreme_events",
            {"severity": 2.0, "pattern": "temporary"},
            "conditional",
            "per-regime exact Gaussian-mixture radius",
            "Extreme-error probability rises only over the temporary regime.",
        ),
        (
            "recurring_high_low_noise_periods",
            "target_variance",
            {"severity": 1.5, "pattern": "recurring", "regimes": 4},
            "conditional",
            "per-regime conditional Gaussian radius",
            "Noise alternates across recurring high and low regimes.",
        ),
        (
            "delayed_calibration_labels",
            "feedback_change",
            {"severity": 1.0, "delay": 25},
            "conditional",
            "current-regime Gaussian radius; labels are usable only at availability time",
            "Label delay grows after the regime change; purge unavailable calibration labels.",
        ),
        (
            "missing_calibration_labels",
            "feedback_change",
            {"severity": 1.0, "missing": 0.35},
            "conditional",
            "current-regime Gaussian radius; missing labels remain unavailable",
            "Calibration outcomes are selectively unavailable at the configured MCAR rate.",
        ),
    ]
    return tuple(
        ConformalStressPreset(
            name=name,
            config=_config(scenario, n=n, seed=seed, parameters=parameters),
            calibration_target_scope=target_scope,
            oracle_radius_scope=radius_scope,
            residual_law=SCENARIOS[scenario],
            stress=stress,
        )
        for name, scenario, parameters, target_scope, radius_scope, stress in definitions
    )
