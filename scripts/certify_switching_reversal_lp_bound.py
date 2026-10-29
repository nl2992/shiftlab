"""Rationally certify a narrow optimality bracket for the registered T=6 LP.

The LP solver is used only to propose a dual vector. This script converts that
vector to rationals and verifies the dual equations/inequalities exactly. Tiny
positive dual inequality residuals are charged against x_j <= 1 for learner
realization weights, yielding a rigorous lower bound despite rational rounding.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def rationalize(value: float, denominator: int = 10**7) -> F:
    return F(float(value)).limit_denominator(denominator)


def matrix_fraction(value: float) -> F:
    return F(float(value)).limit_denominator(10**9)


def fixed_graph_policy(game: CausalSwitchingGame, activation: F):
    def policy(history, outcomes):
        time = len(history) + 1
        visible = dict(game.information(history, outcomes)[1])
        active = bool(history and history[0][1])
        old = history[-1][0] if history else 0
        if time == 1:
            weights = {(0, 1): activation, (0, 0): 1 - activation}
        elif time == 2:
            q = int(active and visible.get(1) == 1)
            weights = {(0, q): F(1)}
        elif time == 3:
            a = int(active and visible.get(1) == 1 and visible.get(2) == 1)
            weights = {(a, 0): F(1)}
        elif time == 4:
            weights = {(1, 1): F(1)} if old else {(0, 0): F(1)}
        elif time == 5:
            rollback = old == 1 and visible.get(4) == 0
            weights = {(0 if rollback else old, 0): F(1)}
        else:
            weights = {(old, 0): F(1)}
        return tuple(weights.get(choice, F(0)) for choice in game.choices(history))

    return policy


def encode_vector(values) -> list[str]:
    return [str(value) for value in values]


def floor_decimal(value: F, places: int = 12) -> str:
    scale = 10**places
    integer = (value.numerator * scale) // value.denominator
    return f"{integer // scale}.{integer % scale:0{places}d}"


def ceil_decimal(value: F, places: int = 12) -> str:
    scale = 10**places
    integer = (value.numerator * scale + value.denominator - 1) // value.denominator
    return f"{integer // scale}.{integer % scale:0{places}d}"


def ceil_fraction(value: F, denominator: int) -> F:
    numerator = (value.numerator * denominator + value.denominator - 1) // value.denominator
    return F(numerator, denominator)


def exact_alternative_costs(game: CausalSwitchingGame) -> list[F]:
    """Rebuild sequence-flow cost coefficients with Fraction arithmetic."""
    costs = [F(0)] * game.learner.count

    def visit(history, outcomes, sequence, weight, posterior, total_cost):
        time = len(history) + 1
        if time > game.config.horizon:
            costs[sequence] += weight * total_cost
            return
        state1 = game.model.propagate(posterior, 1)
        positive = game.model.emission(state1)
        old = history[-1][0] if history else 0
        key = game.information(history, outcomes)
        _, children, choices = game.learner.infos[key]
        for (action, query), child in zip(choices, children, strict=True):
            stage = (
                (positive if action == 0 else 1 - positive)
                + game.config.query_cost * query
                + game.config.switch_cost * (action != old)
            )
            following_history = history + ((action, query),)
            if query:
                for label, probability in ((0, 1 - positive), (1, positive)):
                    likelihood1 = game.model.emission1 if label else 1 - game.model.emission1
                    following_posterior = state1 * likelihood1 / probability
                    visit(
                        following_history,
                        outcomes + ((time, label),),
                        child,
                        weight * probability,
                        following_posterior,
                        total_cost + stage,
                    )
            else:
                visit(following_history, outcomes, child, weight, state1, total_cost + stage)

    visit((), (), 0, F(1), game.model.prior1, F(0))
    return costs


def main() -> dict:
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    game = CausalSwitchingGame(config, model)
    game.build()
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    risk_indices = list(game.risk)
    payoff = coo_matrix(
        (
            [float(game.risk[key]) for key in risk_indices],
            ([key[0] for key in risk_indices], [key[1] for key in risk_indices]),
        ),
        shape=(nx, ny),
    ).tocsr()
    objective = np.zeros(nx + len(f_rhs))
    exact_cost = exact_alternative_costs(game)
    for sequence, cost in enumerate(exact_cost):
        objective[sequence] = float(cost)
    inequality = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    upper_rhs = np.r_[np.zeros(ny), float(config.alpha)]
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()

    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=upper_rhs,
        A_eq=equality,
        b_eq=e_rhs,
        bounds=[(0, None)] * nx + [(None, None)] * len(f_rhs),
        method="highs",
        options={
            "time_limit": 60.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(result.message)

    dual_ub = [rationalize(x) for x in result.ineqlin.marginals]
    dual_eq = [rationalize(x) for x in result.eqlin.marginals]
    if any(value > 0 for value in dual_ub):
        raise AssertionError("rationalized inequality dual has a positive component")

    # Verify A_ub^T y + A_eq^T z = 0 on free columns, and bound violations
    # on nonnegative learner realization columns exactly.
    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    violations = [F(0)] * nx
    free_column_residual = F(0)
    for column in range(nx + len(f_rhs)):
        lhs = sum(
            matrix_fraction(a_csc.data[i]) * dual_ub[a_csc.indices[i]]
            for i in range(a_csc.indptr[column], a_csc.indptr[column + 1])
        )
        lhs += sum(
            matrix_fraction(e_csc.data[i]) * dual_eq[e_csc.indices[i]]
            for i in range(e_csc.indptr[column], e_csc.indptr[column + 1])
        )
        if column < nx:
            violations[column] = max(F(0), lhs - exact_cost[column])
        else:
            free_column_residual = max(free_column_residual, abs(lhs))
    if free_column_residual:
        raise AssertionError(f"dual equality residual is nonzero: {free_column_residual}")

    exact_ub_rhs = [F(0)] * ny + [config.alpha]
    dual_value = sum(a * b for a, b in zip(exact_ub_rhs, dual_ub, strict=True))
    dual_value += sum(
        matrix_fraction(value) * multiplier
        for value, multiplier in zip(e_rhs, dual_eq, strict=True)
    )
    correction = sum(violations)
    correction_upper = ceil_fraction(correction, 10**12)
    certified_lower = dual_value - correction_upper
    lower_decimal = floor_decimal(certified_lower)

    policy = fixed_graph_policy(game, F(2, 5))
    metrics = game.expected_metrics(policy)
    upper = sum(metrics[:3])
    risk = game.null_risk(policy)
    if risk > config.alpha:
        raise AssertionError("fixed-graph upper-bound policy violates risk constraint")
    if certified_lower > upper:
        raise AssertionError("certified lower bound exceeds feasible policy cost")

    cert_payload = {
        "dual_inequality": encode_vector(dual_ub),
        "dual_equality": encode_vector(dual_eq),
        "dual_value": str(dual_value),
        "rounding_correction_upper": str(correction_upper),
        "certified_lower_bound_decimal_rounded_down": lower_decimal,
        "feasible_policy_upper_bound": str(upper),
        "free_column_residual": str(free_column_residual),
    }
    encoded = json.dumps(cert_payload, sort_keys=True, separators=(",", ":")).encode()
    output = {
        "status": "exact_rational_dual_lower_bound_and_feasible_policy_upper_bound",
        "contract": {
            "horizon": config.horizon,
            "hard_budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "alternative": "registered recurrent HMM with transition 1/4 and emissions 1/20, 19/20",
            "null": "full-history conditional success probability at most 1/2",
        },
        "solver_proposal": float(result.fun),
        "exact_bound": {
            "lower": lower_decimal,
            "upper": str(upper),
            "gap_upper": ceil_decimal(upper - F(lower_decimal)),
            "upper_policy_risk": str(risk),
            "upper_policy_metrics": encode_vector(metrics),
            "claim": "The robust sequence-form LP optimum is enclosed by these exact rational bounds.",
        },
        "certificate": cert_payload,
        "certificate_sha256": hashlib.sha256(encoded).hexdigest(),
        "scripts": {
            "this_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "oracle_source_sha256": hashlib.sha256(
                Path("src/shiftlab/dive/causal_switching_game.py").read_bytes()
            ).hexdigest(),
        },
    }
    out_path = Path("outputs/switching_reversal_lp_certificate_v1/results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: output[k]
                for k in ("status", "solver_proposal", "exact_bound", "certificate_sha256")
            },
            indent=2,
        )
    )
    return output


if __name__ == "__main__":
    main()
