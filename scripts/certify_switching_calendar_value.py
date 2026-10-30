"""Certify the registered six-cell fixed-calendar/unrestricted LP comparison.

HiGHS proposes dual vectors only. The saved lower bounds are checked with
Fraction arithmetic by this script's --verify mode, which does not optimize.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import numpy as np
from certify_switching_reversal_lp_bound import (
    ceil_fraction,
    exact_alternative_costs,
    matrix_fraction,
    rationalize,
)
from decompose_switching_calendar_gap import CalendarOpportunityGame
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/switching_calendar_exact_cert_v1/results.json"
TOLERANCE = F(1, 10**8)


def make_config() -> GameConfig:
    return GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )


def models():
    for transition, emissions in product(
        (F(1, 10), F(1, 4), F(9, 20)),
        ((F(1, 10), F(9, 10)), (F(1, 50), F(49, 50))),
    ):
        yield RegimeModel(
            transition01=transition,
            transition10=transition,
            emission0=emissions[0],
            emission1=emissions[1],
            prior1=F(1, 2),
        )


def matrices(game: CausalSwitchingGame):
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    n_x, n_y = game.learner.count, game.opponent.count
    risk_indices = list(game.risk)
    payoff = coo_matrix(
        (
            [float(game.risk[key]) for key in risk_indices],
            ([key[0] for key in risk_indices], [key[1] for key in risk_indices]),
        ),
        shape=(n_x, n_y),
    ).tocsr()
    inequality = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, n_x)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    upper_rhs = [F(0)] * n_y + [game.config.alpha]
    return inequality, equality, upper_rhs, list(e_rhs), n_x, n_y, len(f_rhs)


def encode(values) -> list[str]:
    return [str(value) for value in values]


def exact_opponent_dual(game: CausalSwitchingGame, raw_dual: np.ndarray) -> list[F]:
    """Project float null-flow duals to an exactly feasible scaled realization plan."""
    game.build()
    n_sequences = game.opponent.count
    raw_mu = np.asarray(raw_dual[:-1], dtype=float)
    raw_lambda = float(raw_dual[-1])
    if abs(raw_lambda) <= 1e-14:
        return [F(0)] * (n_sequences + 1)
    if raw_lambda > 0:
        raise AssertionError(f"risk-constraint dual must be negative, got {raw_lambda}")
    z_float = raw_mu / raw_lambda
    sequence = [F(0)] * n_sequences
    sequence[0] = F(1)
    for parent, children, _choices in game.opponent.infos.values():
        parent_value = sequence[parent]
        if parent_value == 0 or z_float[parent] <= 1e-12:
            probabilities = [F(0)] * len(children)
            probabilities[0] = F(1)
        else:
            weights = [max(0.0, float(z_float[child])) for child in children]
            total = sum(weights)
            if total <= 1e-12:
                probabilities = [F(0)] * len(children)
                probabilities[0] = F(1)
            else:
                approximations = [rationalize(weight / total) for weight in weights]
                approximation_total = sum(approximations)
                probabilities = [value / approximation_total for value in approximations]
        for child, probability in zip(children, probabilities, strict=True):
            sequence[child] = parent_value * probability
    exact_lambda = rationalize(raw_lambda)
    return [exact_lambda * value for value in sequence] + [exact_lambda]


def verify_cell(game: CausalSwitchingGame, row: dict) -> tuple[F, F, F]:
    game.build()
    inequality, equality, upper_rhs, equality_rhs, n_x, _n_y, n_dual = matrices(game)
    dual_ub = [F(value) for value in row["dual_inequality"]]
    dual_eq = [F(value) for value in row["dual_equality"]]
    if len(dual_ub) != inequality.shape[0] or len(dual_eq) != equality.shape[0]:
        raise AssertionError("saved dual vector has the wrong dimension")
    if any(value > 0 for value in dual_ub):
        raise AssertionError("minimization inequality dual has a positive component")

    exact_cost = exact_alternative_costs(game)
    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    correction = F(0)
    free_residual = F(0)
    for column in range(n_x + n_dual):
        lhs = sum(
            matrix_fraction(a_csc.data[i]) * dual_ub[a_csc.indices[i]]
            for i in range(a_csc.indptr[column], a_csc.indptr[column + 1])
        )
        lhs += sum(
            matrix_fraction(e_csc.data[i]) * dual_eq[e_csc.indices[i]]
            for i in range(e_csc.indptr[column], e_csc.indptr[column + 1])
        )
        if column < n_x:
            correction += max(F(0), lhs - exact_cost[column])
        else:
            free_residual = max(free_residual, abs(lhs))
    if free_residual:
        raise AssertionError(f"free-column dual residual is nonzero: {free_residual}")

    dual_value = sum(a * b for a, b in zip(upper_rhs, dual_ub, strict=True))
    dual_value += sum(
        matrix_fraction(rhs) * value for rhs, value in zip(equality_rhs, dual_eq, strict=True)
    )
    correction_upper = ceil_fraction(correction, 10**12)
    lower = dual_value - correction_upper
    calendar_game = CalendarOpportunityGame(game.config, game.model, (1, 2, 3))
    behavior = {}
    for record in row["fixed_calendar_policy_records"]:
        history = tuple(tuple(pair) for pair in record["history"])
        released = tuple(tuple(pair) for pair in record["released"])
        choices = tuple(tuple(choice) for choice in record["choices"])
        probabilities = tuple(F(value) for value in record["probabilities"])
        behavior[(history, released)] = (choices, probabilities)

    def fixed_policy(history, outcomes):
        key = calendar_game.information(history, outcomes)
        choices, probabilities = behavior[key]
        if choices != calendar_game.choices(history):
            raise AssertionError("saved policy action set disagrees with calendar game")
        return probabilities

    metrics = calendar_game.expected_metrics(fixed_policy)
    raw_cost = sum(metrics[:3])
    raw_risk = calendar_game.null_risk(fixed_policy)
    activation = F(row["fixed_calendar_activation_probability"])
    no_query_metrics = calendar_game.expected_metrics(
        lambda history, outcomes: tuple(
            F(choice == (0, 0)) for choice in calendar_game.choices(history)
        )
    )
    upper = activation * raw_cost + (1 - activation) * sum(no_query_metrics[:3])
    feasible_risk = activation * raw_risk
    if raw_cost != F(row["fixed_calendar_raw_cost"]):
        raise AssertionError("saved fixed-calendar policy cost does not verify")
    if raw_risk != F(row["fixed_calendar_raw_risk"]):
        raise AssertionError("saved fixed-calendar policy risk does not verify")
    if upper != F(row["fixed_calendar_feasible_cost"]):
        raise AssertionError("saved fixed-calendar lottery cost does not verify")
    if feasible_risk != F(row["fixed_calendar_feasible_risk"]):
        raise AssertionError("saved fixed-calendar lottery risk does not verify")
    if feasible_risk > game.config.alpha:
        raise AssertionError("fixed-calendar upper policy violates the risk constraint")
    gap = upper - lower
    if gap < 0 or gap > TOLERANCE:
        raise AssertionError(f"oracle gap {gap} exceeds tolerance {TOLERANCE}")
    if F(row["dual_value"]) != dual_value:
        raise AssertionError("saved dual objective does not match exact recomputation")
    if F(row["rounding_correction_upper"]) != correction_upper:
        raise AssertionError("saved dual correction does not match exact recomputation")
    for key, value in (
        ("certified_unrestricted_lower", lower),
        ("fixed_calendar_upper", upper),
        ("certified_gap_upper", gap),
    ):
        if key in row and F(row[key]) != value:
            raise AssertionError(f"saved {key} does not match exact recomputation")
    return lower, upper, gap


def fit_cell(model: RegimeModel) -> dict:
    config = make_config()
    game = CausalSwitchingGame(config, model)
    game.build()
    inequality, equality, upper_rhs, equality_rhs, n_x, n_y, n_dual = matrices(game)
    exact_cost = exact_alternative_costs(game)
    objective = np.zeros(n_x + n_dual)
    objective[:n_x] = np.asarray([float(value) for value in exact_cost])
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=np.asarray([float(value) for value in upper_rhs]),
        A_eq=equality,
        b_eq=np.asarray(equality_rhs, dtype=float),
        bounds=[(0, None)] * n_x + [(None, None)] * n_dual,
        method="highs",
        options={
            "time_limit": 120.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(result.message)

    calendar = CalendarOpportunityGame(config, model, (1, 2, 3))
    calendar_report, _policy, records = calendar.solve()
    row = {
        "model": {
            "transition": str(model.transition01),
            "emission0": str(model.emission0),
            "emission1": str(model.emission1),
            "prior1": str(model.prior1),
        },
        "solver_objective_proposal": float(result.fun),
        "nodes": game.nodes,
        "learner_sequences": n_x,
        "opponent_sequences": n_y,
        "fixed_calendar": [1, 2, 3],
        "fixed_calendar_feasible_cost": calendar_report["calibrated_total_cost"],
        "fixed_calendar_feasible_risk": calendar_report["calibrated_risk_bound"],
        "fixed_calendar_raw_cost": calendar_report["raw_recovered_cost"],
        "fixed_calendar_raw_risk": calendar_report["raw_causal_null_risk"],
        "fixed_calendar_activation_probability": calendar_report["activation_probability"],
        "fixed_calendar_policy_records": records,
        "dual_inequality": encode(exact_opponent_dual(game, result.ineqlin.marginals)),
        "dual_equality": encode(rationalize(x) for x in result.eqlin.marginals),
    }
    inequality_dual = [F(value) for value in row["dual_inequality"]]
    equality_dual = [F(value) for value in row["dual_equality"]]
    if any(value > 0 for value in inequality_dual):
        raise AssertionError("rationalized inequality dual has a positive component")
    dual_value = sum(a * b for a, b in zip(upper_rhs, inequality_dual, strict=True)) + sum(
        matrix_fraction(rhs) * value for rhs, value in zip(equality_rhs, equality_dual, strict=True)
    )
    row["dual_value"] = str(dual_value)

    # Compute the exact learner-column correction once for serialization; the verifier
    # reconstructs it independently below.
    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    correction = F(0)
    for column in range(n_x):
        lhs = sum(
            matrix_fraction(a_csc.data[i]) * inequality_dual[a_csc.indices[i]]
            for i in range(a_csc.indptr[column], a_csc.indptr[column + 1])
        )
        lhs += sum(
            matrix_fraction(e_csc.data[i]) * equality_dual[e_csc.indices[i]]
            for i in range(e_csc.indptr[column], e_csc.indptr[column + 1])
        )
        correction += max(F(0), lhs - exact_cost[column])
    row["rounding_correction_upper"] = str(ceil_fraction(correction, 10**12))
    return row


def main(verify_only: bool = False) -> dict:
    if verify_only:
        saved = json.loads(OUTPUT.read_text(encoding="utf-8"))
        rows = saved["cells"]
    else:
        rows = [fit_cell(model) for model in models()]
        for row in rows:
            model = RegimeModel(
                transition01=F(row["model"]["transition"]),
                transition10=F(row["model"]["transition"]),
                emission0=F(row["model"]["emission0"]),
                emission1=F(row["model"]["emission1"]),
                prior1=F(row["model"]["prior1"]),
            )
            lower, upper, gap = verify_cell(CausalSwitchingGame(make_config(), model), row)
            row["certified_unrestricted_lower"] = str(lower)
            row["fixed_calendar_upper"] = str(upper)
            row["certified_gap_upper"] = str(gap)
        payload = {
            "status": "rational_dual_certificates_for_registered_calendar_comparison",
            "protocol": "docs/switching_calendar_exact_cert_protocol_v1.md",
            "tolerance": str(TOLERANCE),
            "cells": rows,
            "source_sha256": {
                path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                for path in (
                    "scripts/certify_switching_calendar_value.py",
                    "scripts/decompose_switching_calendar_gap.py",
                    "scripts/screen_switching_episode_composition_grid.py",
                    "src/shiftlab/dive/causal_switching_game.py",
                    "src/shiftlab/dive/delayed_regime_information.py",
                    "docs/switching_calendar_exact_cert_protocol_v1.md",
                )
            },
            "scope": "Six registered finite instances only; no method novelty, scaling, or efficacy claim.",
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        saved = payload

    verified = []
    for row in rows:
        model = RegimeModel(
            transition01=F(row["model"]["transition"]),
            transition10=F(row["model"]["transition"]),
            emission0=F(row["model"]["emission0"]),
            emission1=F(row["model"]["emission1"]),
            prior1=F(row["model"]["prior1"]),
        )
        game = CausalSwitchingGame(make_config(), model)
        lower, upper, gap = verify_cell(game, row)
        verified.append(
            {
                "model": row["model"],
                "unrestricted_lower": str(lower),
                "fixed_calendar_upper": str(upper),
                "certified_gap_upper": str(gap),
            }
        )
    return {"verified_cells": verified, "verified_count": len(verified)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify", action="store_true", help="check saved certificates without LP solves"
    )
    args = parser.parse_args()
    print(json.dumps(main(verify_only=args.verify), indent=2))
