"""Explicit DGPs; pattern schedules compose with mechanisms, not misleading drift labels."""

import json

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm
from scipy.stats import t as student_t

from ..decision_tasks import binary_action, binary_risk
from ..schemas import SyntheticConfig

SCENARIOS = {
    "iid_regression": "Y=X0-.9X1+sigma*epsilon; iid standard Gaussian X,epsilon",
    "nonlinear_classification": "P(Y=1|X)=sigmoid(X0+X1^2-1)",
    "ar1": "stationary X0[t]=rho*X0[t-1]+sqrt(1-rho^2)*epsilon[t]",
    "arma": "stationary ARMA(1,1), theta=.3; burn-in 1000",
    "garch": "epsilon[t]=sqrt(h[t])*z[t]; h=.05+.1*epsilon[t-1]^2+.8*h[t-1]; burn-in 1000",
    "heavy_tailed": "Y=X beta+sigma*t_5/sqrt(5/3)",
    "heteroskedastic": "sigma(X)=noise*(1+.5*abs(X0)); stationary conditional mechanism",
    "mean": "X0 mean += severity*w; P(Y|X) fixed",
    "feature_variance": "X0 scale *= 1+severity*w; P(Y|X) fixed",
    "covariance_rotation": "rotate diag(1,4) covariance by severity*w radians; P(Y|X) fixed",
    "correlation": "X1=r*X0+sqrt(1-r^2)*Z1, r=.9*tanh(severity)*w; P(Y|X) fixed",
    "mixture_weights": "X0 += +/-2; positive component probability=.5+.4*tanh(severity)*w",
    "new_component": "X0 += 4 with probability .3*tanh(severity)*w",
    "feature_tail": "X0 interpolates standard normal and unit-variance t5",
    "feature_skew": "X0 interpolates normal and centered standardized lognormal",
    "irrelevant": "X[d-1] += severity*w; beta[d-1]=0; at d=2 use Y=X0+noise so the second feature is a true nuisance",
    "prior_shift": "Y~Bernoulli(pi), X0|Y~N(2Y-1,1); logit(pi)=severity*w",
    "imbalance": "same label-prior mechanism, baseline pi=.1",
    "label_corruption": "flip Bernoulli logistic labels with probability min(.45,severity*w/5)",
    "target_level": "E[Y|X] += severity*w; not pure regression label shift",
    "target_variance": "sigma *= 1+severity*w",
    "tail_frequency": "epsilon mixes N(0,1) and 8*N(0,1), rare probability .01+.1*tanh(severity)*w",
    "concept": "beta0=1-severity*w; P(X) fixed",
    "boundary_rotation": "logit P(Y=1|X)=cos(s*w)*X0+sin(s*w)*X1",
    "nonlinear_response": "E[Y|X]=X beta+severity*w*sin(X0)",
    "interaction": "E[Y|X]=X beta+severity*w*X0*X1",
    "sign_reversal": "beta0=1-2*tanh(severity)*w",
    "latent_state": "unobserved mean offset severity*w; P(X) fixed",
    "conditional_variance": "sigma=noise*(1+severity*w*abs(X0))",
    "boundary_local": "mean += severity*w*exp(-5*abs(X0-.9X1))",
    "rare_cost": "FP cost=1; FN=5+100*severity*w; costs are disclosed at prediction",
    "cost_change": "FP cost=1; FN=5*(1+severity*w); disclosed, imposed research utility",
    "constraints": "action 1 forbidden after regime activation; disclosed",
    "prediction_only": "positive rescaling of conditional mean by 1+severity*w preserves mean sign",
    "hidden_cost": "same observable X,Y as iid, hidden FN=5*(1+severity*w); not identifiable from feedback",
    "asymmetric_errors": "epsilon=(exp(Z)-exp(.5))/sqrt((e-1)*e)",
    "dependent_errors": "stationary AR1 errors with rho; conditional oracle depends on past error",
    "hidden_variance": "sigma=noise*(1+severity*w), regime withheld from learner",
    "extreme_events": "tail_frequency mixture; no normal-quantile oracle claimed",
    "feedback_change": "delay becomes delay+round(20*severity*w), MCAR missingness increases",
    "resource_cost": "record imposed retrain cost 10*(1+severity*w) and configured action budget",
    "small_decision_covariate": "X0=.005*Z0-.01+.02*severity*w; fixed P(Y=1|X)=sigmoid(200*X0); symmetric costs",
    "rare_high_cost": "P(Y=1|X)=.0001+.005*severity*w; X unchanged; FN=1000, FP=1; small Brier change can cause large decision regret",
}
STATIONARY = {
    "iid_regression",
    "nonlinear_classification",
    "ar1",
    "arma",
    "garch",
    "heavy_tailed",
    "heteroskedastic",
    "asymmetric_errors",
    "dependent_errors",
}
CLASSIFICATION = {
    "nonlinear_classification",
    "prior_shift",
    "imbalance",
    "label_corruption",
    "boundary_rotation",
    "small_decision_covariate",
    "rare_high_cost",
}


def schedule(c: SyntheticConfig):
    """Return regime weights and exact transitions, including gradual intervals."""
    n, tau = c.n, int(c.n * c.change_fraction)
    t = np.arange(n)
    if c.regimes == 1:
        return np.zeros(n), {"change_times": [], "transition_intervals": []}
    width = max(1, int(n * c.transition_fraction))
    transition = []
    if c.pattern in ["linear", "sigmoid"]:
        u = np.clip((t - tau) / width, 0, 1)
        w = (
            u
            if c.pattern == "linear"
            else (expit(12 * (u - 0.5)) - expit(-6)) / (expit(6) - expit(-6))
        )
        transition = [[tau, min(n - 1, tau + width)]]
    elif c.pattern == "seasonal":
        w = np.where(t < tau, 0.0, 0.5 * (1 - np.cos(2 * np.pi * (t - tau) / width)))
        transition = [[tau, n - 1]]
    elif c.pattern == "temporary":
        w = ((t >= tau) & (t < tau + width)).astype(float)
    elif c.pattern in ["multiple", "recurring", "variable_dwell"]:
        cuts = np.linspace(0, n, c.regimes + 1, dtype=int)[1:-1]
        if c.pattern == "variable_dwell":
            cuts = np.sort(
                np.random.default_rng(c.seed + 900).choice(
                    np.arange(1, n), c.regimes - 1, replace=False
                )
            )
        r = np.searchsorted(cuts, t, side="right")
        w = r % 2 if c.pattern != "multiple" else r / max(1, c.regimes - 1)
    elif c.pattern == "oblivious_adversarial":
        from .adaptation import oblivious_change_times

        cuts = oblivious_change_times(n, c.review_period, tau)
        w = np.searchsorted(cuts, t, side="right") % 2
    elif c.pattern == "hmm":
        rng = np.random.default_rng(c.seed + 901)
        switches = rng.random(n) < 1 / max(10, width)
        switches[:tau] = False
        w = np.cumsum(switches) % 2
    else:
        w = (t >= tau).astype(float)
    if c.scenario in STATIONARY or c.severity == 0:
        w = np.zeros(n)
        transition = []
    changes = [] if transition else (np.flatnonzero(np.diff(w) != 0) + 1).tolist()
    return w, {"change_times": changes, "transition_intervals": transition}


def generate_chunks(c: SyntheticConfig):
    """Yield observation/evaluator DataFrames with bounded feature allocations.

    Backend RNG sequences differ; chunk size is part of the reproducibility configuration.
    Stateful temporal recurrences run on CPU; CUDA handles vectorized iid transforms.
    """
    if c.scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {c.scenario!r}; choices={list(SCENARIOS)}")
    from ..gpu.torch_backend import random_chunks

    w_all, _ = schedule(c)
    rng = np.random.default_rng(c.seed + 701)
    previous, previous_error, previous_innovation, h = rng.normal(), 0.0, 0.0, 0.5
    has_observed_error = False
    if c.scenario == "dependent_errors":
        previous_error = float(rng.normal())
    # Burn in only stateful processes.
    if c.scenario in ["arma", "garch"]:
        for z in rng.normal(size=1000):
            previous = c.rho * previous + z + 0.3 * previous_innovation
            previous_innovation = z
            previous_error = np.sqrt(h) * z
            h = 0.05 + 0.1 * previous_error**2 + 0.8 * h
    for start, X, z, uniform, backend in random_chunks(c):
        m = len(X)
        t = np.arange(start, start + m)
        w = w_all[t]
        s = c.severity * w
        sigma = np.full(m, c.noise)
        beta = np.zeros((m, c.d))
        beta[:, 0], beta[:, 1] = 1.0, -0.9
        name = c.scenario
        if name == "mean":
            X[:, 0] += s
        if name == "feature_variance":
            X[:, 0] *= 1 + s
        if name == "irrelevant":
            X[:, -1] += s
            if c.d == 2:
                beta[:, 1] = 0
        if name == "small_decision_covariate":
            X[:, 0] = 0.005 * X[:, 0] - 0.01 + 0.02 * s
        if name == "covariance_rotation":
            a, b = X[:, 0].copy(), 2 * X[:, 1].copy()
            X[:, 0], X[:, 1] = np.cos(s) * a - np.sin(s) * b, np.sin(s) * a + np.cos(s) * b
        if name == "correlation":
            r = 0.9 * np.tanh(c.severity) * w
            X[:, 1] = r * X[:, 0] + np.sqrt(1 - r * r) * X[:, 1]
        if name == "mixture_weights":
            X[:, 0] += np.where(uniform < 0.5 + 0.4 * np.tanh(c.severity) * w, 2.0, -2.0)
        if name == "new_component":
            X[:, 0] += 4 * (uniform < 0.3 * np.tanh(c.severity) * w)
        if name in ["feature_tail", "feature_skew"]:
            alt = (
                student_t.ppf(np.clip(uniform, 1e-10, 1 - 1e-10), 5) / np.sqrt(5 / 3)
                if name == "feature_tail"
                else (np.exp(z) - np.exp(0.5)) / np.sqrt((np.e - 1) * np.e)
            )
            fraction = np.tanh(s)
            X[:, 0] = (1 - fraction) * X[:, 0] + fraction * alt
            # Independent response noise avoids changing P(Y|X).
            z = rng.normal(size=m)
        if name in ["ar1", "arma"]:
            for i in range(m):
                innovation = X[i, 0]
                previous = c.rho * previous + (
                    np.sqrt(1 - c.rho**2) * innovation
                    if name == "ar1"
                    else innovation + 0.3 * previous_innovation
                )
                previous_innovation = innovation
                X[i, 0] = previous
        if name in ["concept", "sign_reversal"]:
            beta[:, 0] -= s if name == "concept" else 2 * np.tanh(c.severity) * w
        mean = np.sum(X * beta, axis=1)
        if name in ["target_level", "latent_state"]:
            mean += s
        if name == "nonlinear_response":
            mean += s * np.sin(X[:, 0])
        if name == "interaction":
            mean += s * X[:, 0] * X[:, 1]
        if name == "boundary_local":
            mean += s * np.exp(-5 * abs(mean))
        if name == "prediction_only":
            mean *= 1 + s
        if name in ["target_variance", "hidden_variance"]:
            sigma *= 1 + s
        if name == "conditional_variance":
            sigma *= 1 + s * abs(X[:, 0])
        if name == "heteroskedastic":
            sigma *= 1 + 0.5 * abs(X[:, 0])
        quantile_kind = "normal"
        history_conditional_mean = mean.copy()
        history_conditional_scale = sigma.copy()
        if name == "heavy_tailed":
            z = student_t.ppf(np.clip(uniform, 1e-10, 1 - 1e-10), 5) / np.sqrt(5 / 3)
            quantile_kind = "student_t5"
        if name == "asymmetric_errors":
            z = (np.exp(z) - np.exp(0.5)) / np.sqrt((np.e - 1) * np.e)
            quantile_kind = "centered_lognormal"
        if name in ["tail_frequency", "extreme_events"]:
            z *= np.where(uniform < 0.01 + 0.1 * np.tanh(c.severity) * w, 8.0, 1.0)
            quantile_kind = "normal_mixture"
        if name in ["dependent_errors", "garch"]:
            conditional_noise_mean = np.zeros(m)
            for i in range(m):
                if name == "garch":
                    h = 0.05 + 0.1 * previous_error**2 + 0.8 * h
                    sigma[i] *= np.sqrt(h)
                    previous_error = np.sqrt(h) * z[i]
                else:
                    if has_observed_error:
                        conditional_noise_mean[i] = c.rho * previous_error
                        history_conditional_scale[i] = sigma[i] * np.sqrt(1 - c.rho**2)
                    previous_error = c.rho * previous_error + np.sqrt(1 - c.rho**2) * z[i]
                    z[i] = previous_error
                    has_observed_error = True
            if name == "dependent_errors":
                history_conditional_mean = mean + sigma * conditional_noise_mean
            if name == "dependent_errors":
                quantile_kind = "marginal_normal_dependent"
        target = mean + sigma * z
        probability = norm.cdf(mean / sigma)
        if quantile_kind == "student_t5":
            probability = student_t.cdf(mean / sigma * np.sqrt(5 / 3), 5)
        elif quantile_kind == "centered_lognormal":
            boundary = np.exp(0.5) - mean / sigma * np.sqrt((np.e - 1) * np.e)
            probability = np.where(
                boundary <= 0, 1.0, 1 - norm.cdf(np.log(np.maximum(boundary, 1e-300)))
            )
        elif quantile_kind == "normal_mixture":
            rate = 0.01 + 0.1 * np.tanh(c.severity) * w
            probability = (1 - rate) * norm.cdf(mean / sigma) + rate * norm.cdf(mean / (8 * sigma))
        if name in CLASSIFICATION:
            probability = expit(X[:, 0] + X[:, 1] ** 2 - 1)
            if name == "boundary_rotation":
                probability = expit(np.cos(s) * X[:, 0] + np.sin(s) * X[:, 1])
            if name == "small_decision_covariate":
                probability = expit(200 * X[:, 0])
            if name == "rare_high_cost":
                probability = 0.0001 + 0.005 * s
            if name in ["prior_shift", "imbalance"]:
                prior = expit(s + (np.log(0.1 / 0.9) if name == "imbalance" else 0))
                target = (uniform < prior).astype(float)
                X[:, 0] += 2 * target - 1
                probability = expit(2 * X[:, 0] + np.log(prior / (1 - prior)))
            else:
                if name == "label_corruption":
                    rate = np.minimum(0.45, s / 5)
                    probability = rate + (1 - 2 * rate) * probability
                target = (uniform < probability).astype(float)
            mean = probability
        fn = np.full(m, 5.0)
        if name == "small_decision_covariate":
            fn[:] = 1.0
        if name == "prediction_only":
            fn[:] = 1.0
        if name == "rare_high_cost":
            fn[:] = 1000.0
        if name in ["rare_cost", "cost_change", "hidden_cost"]:
            fn += 100 * s if name == "rare_cost" else 5 * s
        action = binary_action(probability, fn, 1.0)
        feasible = np.ones(m, dtype=bool)
        if name == "constraints":
            feasible = w == 0
            action &= feasible
        delay = np.full(m, c.delay)
        missing_rate = np.full(m, c.missing)
        if name == "feedback_change":
            delay += np.rint(20 * s).astype(int)
            missing_rate = np.minimum(0.95, c.missing + 0.2 * np.tanh(s))
        available = (t + delay).astype(float)
        available[rng.random(m) < missing_rate] = np.nan
        context: list[str | None] = [
            json.dumps(
                {
                    "fn": float(f),
                    "fp": 1.0,
                    "action_1_feasible": bool(a),
                    "utility_origin": "synthetically imposed",
                }
            )
            for f, a in zip(fn, feasible)
        ]
        if name == "hidden_cost":
            context = [None] * m
        boundaries = np.floor(
            c.n * np.cumsum([c.train_fraction, c.validation_fraction, c.calibration_fraction])
            + 1e-8
        ).astype(int)
        splits = np.select(
            [t < boundaries[0], t < boundaries[1], t < boundaries[2]],
            ["train", "validation", "calibration"],
            default="test",
        )
        # Purge fit/calibration labels that would arrive after the next partition begins.
        # Use global boundaries so this also works when a boundary equals a chunk edge.
        for split_name, fraction in zip(["train", "validation", "calibration"], boundaries):
            splits[(splits == split_name) & np.isfinite(available) & (available >= fraction)] = (
                "unassigned"
            )
        frame = pd.DataFrame(
            {
                "sample_id": [f"{c.seed}:{i}" for i in t],
                "entity_id": "stream-0",
                "event_time": t,
                "feature_available_time": t,
                "prediction_time": t,
                "label_event_time": t,
                "label_available_time": available,
                "features": list(X),
                "target": target,
                "domain_id": "synthetic",
                "regime_id": None,
                "decision_context": context,
                "sample_weight": 1.0,
                "split": splits,
                "metadata": json.dumps({"clock": "simulation index", "backend": backend}),
            }
        )
        q90 = sigma * norm.ppf(0.95)
        if quantile_kind == "student_t5":
            q90 = sigma * student_t.ppf(0.95, 5) / np.sqrt(5 / 3)
        if quantile_kind in ["centered_lognormal", "normal_mixture"]:
            # Vectorized bisection of the exact absolute-residual CDF; no simulated quantile claims.
            lower, upper = np.zeros(m), np.full(m, 100.0)
            for _ in range(55):
                middle = (lower + upper) / 2
                if quantile_kind == "normal_mixture":
                    rate = 0.01 + 0.1 * np.tanh(c.severity) * w
                    cdf = (1 - rate) * (2 * norm.cdf(middle) - 1) + rate * (
                        2 * norm.cdf(middle / 8) - 1
                    )
                else:
                    center, scale = np.exp(0.5), np.sqrt((np.e - 1) * np.e)
                    hi, lo = center + scale * middle, center - scale * middle
                    cdf = norm.cdf(np.log(hi)) - np.where(
                        lo > 0, norm.cdf(np.log(np.maximum(lo, 1e-300))), 0.0
                    )
                lower = np.where(cdf < 0.9, middle, lower)
                upper = np.where(cdf >= 0.9, middle, upper)
            q90 = sigma * (lower + upper) / 2
        conditional_q90 = q90.copy()
        if name == "dependent_errors":
            conditional_q90 = history_conditional_scale * norm.ppf(0.95)
        if name in CLASSIFICATION:
            q90[:] = np.nan
            conditional_q90[:] = np.nan
        oracle = pd.DataFrame(
            {
                "sample_id": frame.sample_id,
                "weight": w,
                "conditional_mean": mean,
                "conditional_mean_given_history": history_conditional_mean,
                "sigma": sigma,
                "probability_positive": probability,
                "oracle_action": action,
                "oracle_risk": binary_risk(action, probability, fn, 1.0),
                "fn_cost": fn,
                "radius_90": q90,
                "conditional_radius_90": conditional_q90,
                "quantile_kind": quantile_kind,
                "retrain_cost": 10 * (1 + s) if name == "resource_cost" else 10.0,
                "regime_id": np.where(
                    w == 0, "baseline", np.where(w == 1, "shifted", "transition")
                ),
            }
        )
        yield frame, oracle
