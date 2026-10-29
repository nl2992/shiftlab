"""Numerical occupancy LP for a known-onset sequential-test reference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog


def states(budget: int) -> list[tuple[int, int]]:
    return [(n, s) for n in range(budget + 1) for s in range(n + 1)]


def beta_alpha(alpha: float, divergence: float) -> float:
    def kl(p: float) -> float:
        return p * np.log(p / alpha) + (1 - p) * np.log((1 - p) / (1 - alpha))

    low, high = alpha, 1.0
    for _ in range(100):
        mid = (low + high) / 2
        if kl(mid) <= divergence:
            low = mid
        else:
            high = mid
    return low


def lower_bound(horizon: int, onset: int, budget: int, delay: int, epsilon: float, alpha: float):
    p = 0.5 + epsilon
    kappa = p * np.log(p / 0.5) + (1 - p) * np.log((1 - p) / 0.5)
    return (
        2
        * epsilon
        * sum(
            1 - beta_alpha(alpha, min(budget, max(0, j - delay + 1)) * kappa)
            for j in range(horizon - onset + 1)
        )
    )


def solve(delay: int) -> dict[str, object]:
    horizon, onset, budget = 120, 61, 20
    epsilon, alpha, query_cost, switch_cost = 0.1, 0.05, 0.01, 0.1
    p_alt = 0.5 + epsilon
    ss = states(budget)
    idx = {state: i for i, state in enumerate(ss)}
    nstate = len(ss)
    iy, ix, iz = 0, nstate, 2 * nstate
    nvar = 3 * nstate

    objective = np.zeros(nvar)
    for (n, s), i in idx.items():
        if n == 0:
            continue
        decision_time = onset + n + delay - 1
        saved = 2 * epsilon * max(0, horizon - decision_time + 1)
        likelihood_ratio = (p_alt / 0.5) ** s * ((1 - p_alt) / 0.5) ** (n - s)
        objective[ix + i] = -likelihood_ratio * (saved - switch_cost)
    objective[iy + idx[(0, 0)]] = query_cost * budget

    a_eq, b_eq = [], []
    root = np.zeros(nvar)
    root[iy + idx[(0, 0)]] = 1
    a_eq.append(root)
    b_eq.append(1)  # activation mass at most one, represented by a slack variable below
    # Replace equality with root occupancy variable plus explicit inactive mass.
    # Use an equality root=activation and constrain activation<=1 through its bound.
    a_eq.pop()
    b_eq.pop()
    for n in range(1, budget + 1):
        for s in range(n + 1):
            row = np.zeros(nvar)
            row[iy + idx[(n, s)]] = 1
            if s <= n - 1:
                row[iz + idx[(n - 1, s)]] -= 0.5
            if s > 0:
                row[iz + idx[(n - 1, s - 1)]] -= 0.5
            a_eq.append(row)
            b_eq.append(0)

    a_ub, b_ub = [], []
    for i in range(nstate):
        row = np.zeros(nvar)
        row[ix + i], row[iz + i], row[iy + i] = 1, 1, -1
        a_ub.append(row)
        b_ub.append(0)
    risk = np.zeros(nvar)
    risk[ix : ix + nstate] = 1
    a_ub.append(risk)
    b_ub.append(alpha)

    bounds = [(0, None)] * nvar
    bounds[iy + idx[(0, 0)]] = (0, 1)
    bounds[ix + idx[(0, 0)]] = (0, 0)  # no evidence is available before the first release
    for s in range(budget + 1):
        bounds[iz + idx[(budget, s)]] = (0, 0)

    result = linprog(
        objective,
        A_ub=np.asarray(a_ub),
        b_ub=np.asarray(b_ub),
        A_eq=np.asarray(a_eq),
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    y = result.x[iy : iy + nstate]
    x = result.x[ix : ix + nstate]
    z = result.x[iz : iz + nstate]
    risk_value = float(x.sum())
    activation = float(y[idx[(0, 0)]])
    lp_eq_residual = float(np.max(np.abs(np.asarray(a_eq) @ result.x - b_eq)))
    lp_ineq_violation = float(max(0, np.max(np.asarray(a_ub) @ result.x - b_ub)))
    assert risk_value <= alpha + 1e-8
    assert activation <= 1 + 1e-8
    assert lp_eq_residual <= 1e-8 and lp_ineq_violation <= 1e-8

    # Independently propagate the recovered behavioral rule under the alternative.
    alt_live: dict[tuple[int, int], float] = {(0, 0): activation}
    null_live: dict[tuple[int, int], float] = {(0, 0): activation}
    alt_stop = 0.0
    null_stop = 0.0
    saved_alt = 0.0
    for n in range(budget + 1):
        for s in range(n + 1):
            state = (n, s)
            i = idx[state]
            if y[i] <= 1e-11:
                continue
            stop_prob = x[i] / y[i]
            continue_prob = z[i] / y[i]
            mass = alt_live.get(state, 0.0)
            stop_mass = mass * stop_prob
            alt_stop += stop_mass
            decision_time = onset + n + delay - 1
            saved_alt += stop_mass * 2 * epsilon * (horizon - decision_time + 1)
            if n == budget:
                continue
            continuing = mass * continue_prob
            alt_live[(n + 1, s)] = alt_live.get((n + 1, s), 0.0) + continuing * (1 - p_alt)
            alt_live[(n + 1, s + 1)] = alt_live.get((n + 1, s + 1), 0.0) + continuing * p_alt
            null_mass = null_live.get(state, 0.0)
            null_stop += null_mass * stop_prob
            null_continuing = null_mass * continue_prob
            null_live[(n + 1, s)] = null_live.get((n + 1, s), 0.0) + null_continuing * 0.5
            null_live[(n + 1, s + 1)] = null_live.get((n + 1, s + 1), 0.0) + null_continuing * 0.5
        if n == budget:
            for s in range(n + 1):
                state = (n, s)
                i = idx[state]
                if y[i] > 1e-11:
                    null_stop += null_live.get(state, 0.0) * (x[i] / y[i])

    # Check the induced probability of eventual promotion on every binary label word.
    stop_prob = {
        (n, s): float(x[idx[(n, s)]] / y[idx[(n, s)]]) if y[idx[(n, s)]] > 1e-11 else 0.0
        for n in range(1, budget + 1)
        for s in range(n + 1)
    }
    words = range(1 << budget)
    promotion_probability = []
    for word in words:
        survival = 1.0
        positives = 0
        for n in range(1, budget + 1):
            positives += (word >> (n - 1)) & 1
            survival *= 1 - stop_prob[(n, positives)]
        promotion_probability.append(activation * (1 - survival))
    monotone = True
    max_monotonicity_violation = 0.0
    for word, probability in enumerate(promotion_probability):
        for bit in range(budget):
            if (word >> bit) & 1:
                continue
            higher = word | (1 << bit)
            violation = probability - promotion_probability[higher]
            max_monotonicity_violation = max(max_monotonicity_violation, violation)
            if violation > 1e-7:
                monotone = False

    # The first decision is after d rounds: t=nu+d; subsequent releases arrive each round.
    gross_regret = 2 * epsilon * (horizon - onset + 1) - saved_alt
    net_excess = gross_regret + query_cost * budget * activation - switch_cost * (1 - alt_stop)
    lp_net_excess = 2 * epsilon * (horizon - onset + 1) - switch_cost + float(result.fun)
    assert monotone
    assert abs(null_stop - risk_value) <= 1e-8
    assert abs(net_excess - lp_net_excess) <= 1e-8
    assert budget * activation <= budget + 1e-8
    return {
        "delay": delay,
        "solver_status": result.message,
        "activation_probability": activation,
        "null_promotion_risk": risk_value,
        "independent_null_forward_risk": null_stop,
        "null_risk_slack": alpha - risk_value,
        "alternative_promotion_probability": alt_stop,
        "alternative_gross_decision_regret": gross_regret,
        "expected_query_charge": query_cost * budget * activation,
        "net_cost_excess": net_excess,
        "lp_objective_implied_net_cost_excess": lp_net_excess,
        "no_query_net_excess": 2 * epsilon * (horizon - onset + 1) - switch_cost,
        "noisy_information_net_lower_bound": lower_bound(
            horizon, onset, budget, delay, epsilon, alpha
        )
        - switch_cost,
        "gap_net_upper_minus_lower": net_excess
        - (lower_bound(horizon, onset, budget, delay, epsilon, alpha) - switch_cost),
        "coordinatewise_monotone_promotion_probability": monotone,
        "max_coordinatewise_monotonicity_violation": max_monotonicity_violation,
        "lp_max_equality_residual": lp_eq_residual,
        "lp_max_inequality_violation": lp_ineq_violation,
        "behavioral_policy": [
            {
                "n_arrived": n,
                "positives": s,
                "promote_probability": float(x[idx[(n, s)]] / y[idx[(n, s)]])
                if y[idx[(n, s)]] > 1e-11
                else 0.0,
                "continue_probability": float(z[idx[(n, s)]] / y[idx[(n, s)]])
                if y[idx[(n, s)]] > 1e-11
                else 0.0,
            }
            for n in range(budget)
            for s in range(n + 1)
        ],
    }


def run() -> dict[str, object]:
    return {
        "status": "known_onset_sequential_test_reference_numerical_lp",
        "contract": {
            "horizon": 120,
            "onset_revealed_to_learner": 61,
            "budget": 20,
            "epsilon": 0.1,
            "alpha": 0.05,
            "query_cost": 0.01,
            "switch_cost": 0.1,
            "alternative": "iid Bernoulli(0.6) from onset",
            "null": "iid Bernoulli(0.5); conditional-null validity requires monotone action audit",
            "query_schedule": "fixed cohort at event times onset through onset+budget-1",
            "release": "label queried at s is available at start of s+delay",
        },
        "delays": [solve(delay) for delay in (1, 5, 20)],
        "scope": "Numerical constrained optimal-stopping reference with onset revealed; not a new method or unknown-onset result.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    report = run()
    target = Path("outputs/switching_known_onset_sequential_test_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            [
                {
                    key: row[key]
                    for key in (
                        "delay",
                        "activation_probability",
                        "null_promotion_risk",
                        "net_cost_excess",
                        "noisy_information_net_lower_bound",
                        "gap_net_upper_minus_lower",
                        "coordinatewise_monotone_promotion_probability",
                    )
                }
                for row in report["delays"]
            ],
            indent=2,
        )
    )
