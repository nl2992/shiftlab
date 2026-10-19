"""Structured evaluator-side DGP formulas and regime parameter values."""

import numpy as np
from scipy.special import expit

from ..schemas import SyntheticConfig
from .generators import CLASSIFICATION, SCENARIOS, schedule


def conditional_mean(
    config: SyntheticConfig,
    features: np.ndarray,
    regime_weight: np.ndarray,
    previous_error: np.ndarray | None = None,
) -> np.ndarray:
    """Evaluate the DGP conditional expectation independently of sample generation.

    For dependent_errors, omit previous_error to obtain E[Y_t|X_t], or supply the
    previous standardized residual to obtain the one-step history-conditional mean.
    """
    x = np.asarray(features, dtype=float)
    weight = np.broadcast_to(np.asarray(regime_weight, dtype=float), (len(x),))
    s = config.severity * weight
    f = x[:, 0] if config.scenario == "irrelevant" and config.d == 2 else x[:, 0] - 0.9 * x[:, 1]
    scenario = config.scenario
    if scenario == "concept":
        return x[:, 0] * (1 - s) - 0.9 * x[:, 1]
    if scenario == "sign_reversal":
        return x[:, 0] * (1 - 2 * np.tanh(config.severity) * weight) - 0.9 * x[:, 1]
    if scenario in {"target_level", "latent_state"}:
        return f + s
    if scenario == "nonlinear_response":
        return f + s * np.sin(x[:, 0])
    if scenario == "interaction":
        return f + s * x[:, 0] * x[:, 1]
    if scenario == "boundary_local":
        return f + s * np.exp(-5 * np.abs(f))
    if scenario == "prediction_only":
        return f * (1 + s)
    if scenario == "nonlinear_classification":
        return expit(x[:, 0] + x[:, 1] ** 2 - 1)
    if scenario == "boundary_rotation":
        return expit(np.cos(s) * x[:, 0] + np.sin(s) * x[:, 1])
    if scenario == "small_decision_covariate":
        return expit(200 * x[:, 0])
    if scenario == "rare_high_cost":
        return 0.0001 + 0.005 * s
    if scenario in {"prior_shift", "imbalance"}:
        logit_prior = np.log(0.1 / 0.9) + s if scenario == "imbalance" else s
        return expit(2 * x[:, 0] + logit_prior)
    if scenario == "label_corruption":
        rate = np.minimum(0.45, s / 5)
        base = expit(x[:, 0] + x[:, 1] ** 2 - 1)
        return rate + (1 - 2 * rate) * base
    if scenario == "dependent_errors" and previous_error is not None:
        return f + config.noise * config.rho * np.broadcast_to(previous_error, (len(x),))
    return f


def conditional_scale(
    config: SyntheticConfig,
    features: np.ndarray,
    regime_weight: np.ndarray,
    *,
    garch_variance: np.ndarray | None = None,
) -> np.ndarray:
    """Evaluate the configured one-step residual scale for each observation."""
    x = np.asarray(features, dtype=float)
    weight = np.broadcast_to(np.asarray(regime_weight, dtype=float), (len(x),))
    scale = np.full(len(x), config.noise, dtype=float)
    if config.scenario in {"target_variance", "hidden_variance"}:
        scale *= 1 + config.severity * weight
    elif config.scenario == "conditional_variance":
        scale *= 1 + config.severity * weight * np.abs(x[:, 0])
    elif config.scenario == "heteroskedastic":
        scale *= 1 + 0.5 * np.abs(x[:, 0])
    elif config.scenario == "garch":
        if garch_variance is None:
            raise ValueError("garch_variance is required for the GARCH scale")
        scale *= np.sqrt(np.broadcast_to(garch_variance, (len(x),)))
    return scale


_CONDITIONAL_MEAN = {
    "concept": "X0*(1-severity*w)-.9*X1",
    "sign_reversal": "X0*(1-2*tanh(severity)*w)-.9*X1",
    "target_level": "X0-.9*X1+severity*w",
    "latent_state": "X0-.9*X1+severity*w; offset is evaluator-hidden",
    "nonlinear_response": "X0-.9*X1+severity*w*sin(X0)",
    "interaction": "X0-.9*X1+severity*w*X0*X1",
    "boundary_local": "f+severity*w*exp(-5*abs(f)); f=X0-.9*X1",
    "prediction_only": "(X0-.9*X1)*(1+severity*w)",
    "nonlinear_classification": "expit(X0+X1^2-1), Bernoulli conditional mean",
    "small_decision_covariate": "expit(200*X0), Bernoulli conditional mean",
    "rare_high_cost": ".0001+.005*severity*w, Bernoulli conditional mean",
    "boundary_rotation": "expit(cos(severity*w)*X0+sin(severity*w)*X1), Bernoulli mean",
    "prior_shift": "expit(2*X0+logit(prior)); prior=expit(severity*w)",
    "imbalance": "expit(2*X0+logit(prior)); prior=expit(logit(.1)+severity*w)",
    "label_corruption": "r+(1-2r)*expit(X0+X1^2-1); r=min(.45,severity*w/5)",
}


def _mean_formula(config: SyntheticConfig) -> str:
    if config.scenario == "irrelevant" and config.d == 2:
        return "X0"
    if config.scenario in _CONDITIONAL_MEAN:
        return _CONDITIONAL_MEAN[config.scenario]
    return "X0-.9*X1"


def _feature_formula(config: SyntheticConfig) -> str:
    return {
        "mean": "X0=Z0+severity*w; other features iid standard normal",
        "feature_variance": "X0=(1+severity*w)*Z0; other features iid standard normal",
        "covariance_rotation": "(X0,X1)=R(severity*w)*(Z0,2*Z1); other features standard normal",
        "correlation": "X1=r*X0+sqrt(1-r^2)*Z1; r=.9*tanh(severity)*w",
        "mixture_weights": "X0=Z0+2 with probability .5+.4*tanh(severity)*w, else Z0-2",
        "new_component": "X0=Z0+4 with probability .3*tanh(severity)*w, else Z0",
        "feature_tail": "X0=(1-a)*N(0,1)+a*t5/sqrt(5/3); a=tanh(severity*w)",
        "feature_skew": "X0=(1-a)*N(0,1)+a*centered-standardized-lognormal; a=tanh(severity*w)",
        "irrelevant": "X[d-1]=Z[d-1]+severity*w; at d=2 beta1=0",
        "small_decision_covariate": "X0=.005*Z0-.01+.02*severity*w; other features standard normal",
        "prior_shift": "X0=Z0+2Y-1; X|Y component means remain fixed",
        "imbalance": "X0=Z0+2Y-1; X|Y component means remain fixed",
    }.get(config.scenario, "iid standard Gaussian features")


def _residual_law(config: SyntheticConfig) -> str:
    scenario = config.scenario
    if scenario in CLASSIFICATION:
        return "Bernoulli(conditional_mean)"
    if scenario == "heavy_tailed":
        return "sigma*t5/sqrt(5/3), conditional mean as above"
    if scenario == "asymmetric_errors":
        return "sigma*(exp(Z)-exp(.5))/sqrt((e-1)*e), Z~N(0,1)"
    if scenario in {"tail_frequency", "extreme_events"}:
        return "(1-p)*N(0,sigma^2)+p*N(0,64*sigma^2); p=.01+.1*tanh(severity)*w"
    if scenario == "dependent_errors":
        return "AR(1): e_t=rho*e_(t-1)+sqrt(1-rho^2)*Z_t; stationary marginal N(0,1)"
    if scenario == "garch":
        return "sigma_t*Z_t; sigma_t=noise*sqrt(h_t); h_t=.05+.1*e_(t-1)^2+.8*h_(t-1)"
    return "Normal(0, sigma(X,w)^2)"


def _scale_formula(config: SyntheticConfig) -> str:
    if config.scenario in {"target_variance", "hidden_variance"}:
        return "noise*(1+severity*w)"
    if config.scenario == "conditional_variance":
        return "noise*(1+severity*w*abs(X0))"
    if config.scenario == "heteroskedastic":
        return "noise*(1+.5*abs(X0))"
    if config.scenario == "garch":
        return "noise*sqrt(h_t), h_t=.05+.1*e_(t-1)^2+.8*h_(t-1)"
    return "noise"


def _probability_formula(config: SyntheticConfig) -> str | None:
    if config.scenario in CLASSIFICATION:
        return _mean_formula(config)
    if config.scenario in {"prior_shift", "imbalance", "label_corruption"}:
        return _mean_formula(config)
    return "NormalCDF(conditional_mean/sigma), except when residual_law specifies another CDF"


def oracle_spec(
    config: SyntheticConfig, weights: np.ndarray | None = None, timing: dict | None = None
) -> dict:
    """Return exact equations, representative regime values and evaluator field scopes."""
    if weights is None or timing is None:
        generated_weights, generated_timing = schedule(config)
        weights = generated_weights if weights is None else weights
        timing = generated_timing if timing is None else timing
    unique = np.unique(weights)
    if len(unique) > 10 and config.pattern in {"linear", "sigmoid", "seasonal"}:
        support = [float(unique[0]), float(np.median(unique)), float(unique[-1])]
        support_kind = "representative minimum, median and maximum; full schedule stored separately"
    else:
        support = [float(value) for value in unique]
        support_kind = "all distinct schedule weights"
    regime_parameters = []
    for weight in support:
        effective = config.severity * weight
        beta = np.zeros(config.d)
        beta[0] = 1.0
        beta[1] = -0.9
        if config.scenario == "concept":
            beta[0] = 1.0 - effective
        elif config.scenario == "sign_reversal":
            beta[0] = 1.0 - 2 * np.tanh(config.severity) * weight
        elif config.scenario == "irrelevant" and config.d == 2:
            beta[1] = 0.0
        mean_offset = effective if config.scenario in {"target_level", "latent_state"} else 0.0
        noise_scale_factor = (
            1.0 + effective if config.scenario in {"target_variance", "hidden_variance"} else 1.0
        )
        false_negative_cost = (
            1.0
            if config.scenario in {"small_decision_covariate", "prediction_only"}
            else 1000.0
            if config.scenario == "rare_high_cost"
            else 5.0 + 100 * effective
            if config.scenario == "rare_cost"
            else 5.0 * (1 + effective)
            if config.scenario in {"cost_change", "hidden_cost"}
            else 5.0
        )
        retrain_cost = 10 * (1 + effective) if config.scenario == "resource_cost" else 10.0
        row = {
            "regime_weight": weight,
            "effective_severity": effective,
            "feature_distribution": _feature_formula(config),
            "conditional_mean": _mean_formula(config),
            "conditional_residual_law": _residual_law(config),
            "residual_scale": _scale_formula(config),
            "positive_probability": _probability_formula(config),
            "false_positive_cost": 1.0,
            "false_negative_cost": false_negative_cost,
            "decision_probability_threshold": 1.0 / (1.0 + false_negative_cost),
            "action_1_feasible": not (config.scenario == "constraints" and weight > 0),
            "label_delay": config.delay
            + (round(20 * effective) if config.scenario == "feedback_change" else 0),
            "label_missing_probability": min(0.95, config.missing + 0.2 * np.tanh(effective))
            if config.scenario == "feedback_change"
            else config.missing,
            "parameter_values": {
                "linear_coefficients": beta.tolist()
                if config.scenario not in CLASSIFICATION
                else None,
                "mean_offset": mean_offset,
                "noise_scale_factor": noise_scale_factor,
                "retrain_cost": retrain_cost,
            },
        }
        if config.scenario == "prior_shift":
            row["class_prior"] = float(1 / (1 + np.exp(-effective)))
        elif config.scenario == "imbalance":
            row["class_prior"] = float(1 / (1 + np.exp(-(np.log(0.1 / 0.9) + effective))))
        elif config.scenario == "mixture_weights":
            row["positive_component_probability"] = float(
                0.5 + 0.4 * np.tanh(config.severity) * weight
            )
        elif config.scenario == "new_component":
            row["new_component_probability"] = float(0.3 * np.tanh(config.severity) * weight)
        elif config.scenario == "correlation":
            row["feature_correlation"] = float(0.9 * np.tanh(config.severity) * weight)
        elif config.scenario == "covariance_rotation":
            angle = config.severity * weight
            rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
            row["covariance_matrix"] = (rotation @ np.diag([1.0, 4.0]) @ rotation.T).tolist()
        elif config.scenario == "label_corruption":
            row["label_flip_probability"] = min(0.45, effective / 5)
        if config.scenario == "tail_frequency":
            row["extreme_component_probability"] = float(
                0.01 + 0.1 * np.tanh(config.severity) * weight
            )
        if config.scenario == "resource_cost":
            row["retrain_cost"] = float(retrain_cost)
        regime_parameters.append(row)
    return {
        "scenario": config.scenario,
        "mathematical_definition": SCENARIOS[config.scenario],
        "conditional_mean_formula": _mean_formula(config),
        "conditional_residual_law": _residual_law(config),
        "conditional_scale_formula": _scale_formula(config),
        "probability_formula": _probability_formula(config),
        "regime_parameter_support": support_kind,
        "regime_parameters": regime_parameters,
        "timing": timing,
        "oracle_field_scopes": {
            "conditional_mean": "marginal given the current feature vector; for dependent_errors use conditional_mean_given_history for the sequential oracle",
            "conditional_mean_given_history": "exact one-step conditional mean when prior residual feedback is observable; otherwise evaluator-only",
            "radius_90": "per-row exact absolute-residual radius; marginal for stationary dependent errors and conditional on row-specific scale/regime where it varies",
            "conditional_radius_90": "exact scale/history-conditional radius where supported; evaluator only",
            "oracle_action": "cost-minimizing feasible binary action using exact DGP probability and evaluator cost",
            "oracle_risk": "expected cost of oracle_action under the DGP",
        },
    }
