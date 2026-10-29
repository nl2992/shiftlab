"""Rational primal/dual certificates for four registered asymmetric timing cells."""

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

CELLS = (
    (F(1, 10), F(3, 10), F(1, 2)),
    (F(3, 10), F(1, 10), F(1, 2)),
    (F(1, 10), F(3, 10), F(4, 5)),
    (F(3, 10), F(1, 10), F(1, 5)),
)


def rationalize(value: float, denominator: int = 10**9) -> F:
    return F(float(value)).limit_denominator(denominator)


def rationalize_dual(value: float) -> F:
    return F(float(value)).limit_denominator(10**9)


def ceil_fraction(value: F, denominator: int) -> F:
    numerator = (value.numerator * denominator + value.denominator - 1) // value.denominator
    return F(numerator, denominator)


def opponent_realization_from_dual(game, null_dual, risk_dual):
    """Recover a feasible exact null realization plan for free-column dual equalities."""
    if risk_dual == 0:
        approximate = [0.0] * game.opponent.count
    else:
        approximate = [max(0.0, value / float(risk_dual)) for value in null_dual]
    realization = [F(0)] * game.opponent.count
    realization[0] = F(1)
    for parent, children, _choices in game.opponent.infos.values():
        masses = [F(str(approximate[child])) for child in children]
        total = sum(masses)
        if total:
            behavior = [rationalize(float(mass / total)) for mass in masses]
            normalizer = sum(behavior)
            behavior = [weight / normalizer for weight in behavior]
        else:
            behavior = [F(1)] + [F(0)] * (len(children) - 1)
        for child, weight in zip(children, behavior, strict=True):
            realization[child] = realization[parent] * weight
    return realization


def exact_costs(game: CausalSwitchingGame) -> list[F]:
    costs = [F(0)] * game.learner.count

    def visit(history, outcomes, sequence, weight, posterior, total_cost):
        time = len(history) + 1
        if time > game.config.horizon:
            costs[sequence] += weight * total_cost
            return
        state1 = game.model.propagate(posterior, 1)
        positive = game.model.emission(state1)
        old = history[-1][0] if history else 0
        _, children, choices = game.learner.infos[game.information(history, outcomes)]
        for (action, query), child in zip(choices, children, strict=True):
            stage = positive if action == 0 else 1 - positive
            stage += game.config.query_cost * query
            stage += game.config.switch_cost * (action != old)
            following = history + ((action, query),)
            if query:
                for label, probability in ((0, 1 - positive), (1, positive)):
                    likelihood = game.model.emission1 if label else 1 - game.model.emission1
                    next_posterior = state1 * likelihood / probability
                    visit(
                        following,
                        outcomes + ((time, label),),
                        child,
                        weight * probability,
                        next_posterior,
                        total_cost + stage,
                    )
            else:
                visit(following, outcomes, child, weight, state1, total_cost + stage)

    visit((), (), 0, F(1), game.model.prior1, F(0))
    return costs


def solve_and_certify(config, model):
    game = CausalSwitchingGame(config, model)
    game.build()
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    risk_rows, risk_cols, risk_data = [], [], []
    for (learner_seq, opponent_seq), value in game.risk.items():
        risk_rows.append(opponent_seq)
        risk_cols.append(learner_seq)
        risk_data.append(rationalize(value))
    exact_payoff = coo_matrix(
        (np.array([float(v) for v in risk_data]), (risk_rows, risk_cols)),
        shape=(ny, nx),
    ).tocsr()
    exact_cost = exact_costs(game)
    objective = np.r_[[float(c) for c in exact_cost], np.zeros(len(f_rhs))]
    inequality = vstack(
        [
            hstack([exact_payoff, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    rhs = np.r_[np.zeros(ny), float(config.alpha)]
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=rhs,
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
        raise RuntimeError(f"registered LP failed: {result.message}")
    proposed_ub = [rationalize_dual(x) for x in result.ineqlin.marginals]
    dual_eq = [rationalize_dual(x) for x in result.eqlin.marginals]
    if any(y > 0 for y in proposed_ub):
        raise RuntimeError("rationalized dual has a positive inequality multiplier")
    risk_dual = proposed_ub[-1]
    null_realization = opponent_realization_from_dual(game, proposed_ub[:-1], risk_dual)
    dual_ub = [risk_dual * value for value in null_realization] + [risk_dual]

    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    residuals, free_residual = [], F(0)
    for column in range(nx + len(f_rhs)):
        lhs = sum(
            rationalize(a_csc.data[i]) * dual_ub[a_csc.indices[i]]
            for i in range(a_csc.indptr[column], a_csc.indptr[column + 1])
        )
        lhs += sum(
            rationalize(e_csc.data[i]) * dual_eq[e_csc.indices[i]]
            for i in range(e_csc.indptr[column], e_csc.indptr[column + 1])
        )
        if column < nx:
            residuals.append(max(F(0), lhs - exact_cost[column]))
        else:
            free_residual = max(free_residual, abs(lhs))
    if free_residual:
        raise RuntimeError(f"dual not exact on free columns: {free_residual}")

    dual_rhs = [F(0)] * ny + [config.alpha]
    dual_value = sum(y * b for y, b in zip(dual_ub, dual_rhs, strict=True))
    dual_value += sum(rationalize(float(b)) * y for b, y in zip(e_rhs, dual_eq, strict=True))
    correction = sum(residuals)
    correction_upper = ceil_fraction(correction, 10**12)
    lower = dual_value - correction_upper
    policy, policy_records = game.recover(result.x[:nx])
    metrics = game.expected_metrics(policy)
    upper = sum(metrics[:3])
    risk = game.null_risk(policy)
    if risk > config.alpha or lower > upper:
        raise RuntimeError("certificate or recovered primal failed exact check")
    return {
        "nodes": game.nodes,
        "learner_sequences": nx,
        "opponent_sequences": ny,
        "solver_objective": float(result.fun),
        "dual_value": str(dual_value),
        "correction_upper": str(correction_upper),
        "certified_lower": str(lower),
        "feasible_upper": str(upper),
        "gap": str(upper - lower),
        "risk": str(risk),
        "metrics": [str(v) for v in metrics],
        "free_column_residual": str(free_residual),
        "max_exact_column_violation": str(max(residuals, default=F(0))),
        "dual_inequality": [str(value) for value in dual_ub],
        "dual_equality": [str(value) for value in dual_eq],
        "null_realization": [str(value) for value in null_realization],
        "policy_records": policy_records,
    }


def main():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    cells = []
    for p01, p10, prior1 in CELLS:
        model = RegimeModel(
            transition01=p01,
            transition10=p10,
            emission0=F(1, 20),
            emission1=F(19, 20),
            prior1=prior1,
        )
        cells.append(
            {
                "model": {
                    "transition01": str(p01),
                    "transition10": str(p10),
                    "prior1": str(prior1),
                },
                "certificate": solve_and_certify(config, model),
            }
        )
    output = {
        "status": "exact_rational_dual_certificates_for_registered_four_cells",
        "protocol": "docs/switching_asymmetric_timing_certificate_protocol_v1.md",
        "cells": cells,
        "sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                "scripts/certify_switching_asymmetric_timing.py",
                "scripts/verify_switching_asymmetric_timing_certificates.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "docs/switching_asymmetric_timing_protocol_v1.md",
                "docs/switching_asymmetric_timing_certificate_protocol_v1.md",
            )
        },
    }
    target = Path("outputs/switching_asymmetric_timing_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "dual_certificates.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": output["status"], "cells": cells}, indent=2))
    return output


if __name__ == "__main__":
    main()
