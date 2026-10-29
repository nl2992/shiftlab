"""Optimizer-free exact verifier for the registered timing certificates."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel

CELLS = (
    (F(1, 10), F(3, 10), F(1, 2)),
    (F(3, 10), F(1, 10), F(1, 2)),
    (F(1, 10), F(3, 10), F(4, 5)),
    (F(3, 10), F(1, 10), F(1, 5)),
)


def exact_costs(game):
    costs = [F(0)] * game.learner.count

    def visit(history, outcomes, sequence, weight, posterior, accumulated):
        time = len(history) + 1
        if time > game.config.horizon:
            costs[sequence] += weight * accumulated
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
                    visit(
                        following,
                        outcomes + ((time, label),),
                        child,
                        weight * probability,
                        state1 * likelihood / probability,
                        accumulated + stage,
                    )
            else:
                visit(following, outcomes, child, weight, state1, accumulated + stage)

    visit((), (), 0, F(1), game.model.prior1, F(0))
    return costs


def check_cell(game, record):
    cert = record["certificate"]
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count

    risk_by_sequence = {}
    for (learner_seq, opponent_seq), value in game.risk.items():
        rational = F(float(value)).limit_denominator(10**9)
        if float(rational) != value:
            raise AssertionError("risk coefficient did not rationalize exactly")
        risk_by_sequence[learner_seq, opponent_seq] = rational
    dual_ub = [F(x) for x in cert["dual_inequality"]]
    dual_eq = [F(x) for x in cert["dual_equality"]]
    y = [F(x) for x in cert["null_realization"]]
    if len(dual_ub) != ny + 1 or len(y) != ny or len(dual_eq) != len(e_rhs):
        raise AssertionError("dual dimensions do not match rebuilt game")
    if any(value > 0 for value in dual_ub) or any(value < 0 for value in y):
        raise AssertionError("dual sign or realization nonnegativity failed")

    # Exact realization-flow constraints F y = f.
    f_exact = f_matrix.tocsr()
    for row in range(f_matrix.shape[0]):
        lhs = sum(
            F(float(f_exact.data[i])).limit_denominator(1) * y[f_exact.indices[i]]
            for i in range(f_exact.indptr[row], f_exact.indptr[row + 1])
        )
        if lhs != F(int(f_rhs[row])):
            raise AssertionError("null realization violates sequence flow")
    risk_multiplier = dual_ub[-1]
    if dual_ub[:-1] != [risk_multiplier * value for value in y]:
        raise AssertionError("risk dual is inconsistent with null realization")

    # Verify each learner-sequence inequality and free opponent-flow column exactly.
    e_csc = e_matrix.tocsc()
    costs = exact_costs(game)
    residuals = []
    free_residual = F(0)
    for col in range(nx + len(f_rhs)):
        if col < nx:
            lhs = sum(risk_by_sequence.get((col, opp), F(0)) * dual_ub[opp] for opp in range(ny))
        else:
            row = col - nx
            lhs = (
                -sum(
                    F(float(f_matrix[row, seq])).limit_denominator(1) * dual_ub[seq]
                    for seq in range(ny)
                )
                + F(int(f_rhs[row])) * risk_multiplier
            )
        if col < nx:
            lhs += sum(
                F(float(e_csc.data[i])).limit_denominator(1) * dual_eq[e_csc.indices[i]]
                for i in range(e_csc.indptr[col], e_csc.indptr[col + 1])
            )
        if col < nx:
            residuals.append(max(F(0), lhs - costs[col]))
        else:
            free_residual = max(free_residual, abs(lhs))
    if free_residual != 0 or str(free_residual) != cert["free_column_residual"]:
        raise AssertionError("free dual columns are not exactly zero")

    # Every learner realization is in [0,1], so sum of positive residuals is a valid correction.
    correction = sum(residuals)
    correction_upper = F(cert["correction_upper"])
    if correction_upper < correction:
        raise AssertionError("stored correction does not dominate exact residuals")
    alpha = game.config.alpha
    dual_value = risk_multiplier * alpha + sum(
        F(float(rhs)).limit_denominator(1) * value
        for rhs, value in zip(e_rhs, dual_eq, strict=True)
    )
    lower = dual_value - correction_upper
    if str(dual_value) != cert["dual_value"] or str(lower) != cert["certified_lower"]:
        raise AssertionError("dual objective or lower bracket mismatch")

    behavior = {}
    for item in cert["policy_records"]:
        key = (
            tuple(tuple(x) for x in item["history"]),
            tuple(tuple(x) for x in item["released"]),
        )
        behavior[key] = tuple(F(x) for x in item["probabilities"])

    def policy(history, outcomes):
        return behavior[game.information(history, outcomes)]

    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    upper = sum(metrics[:3])
    if [str(v) for v in metrics] != cert["metrics"]:
        raise AssertionError("saved policy metrics differ from independent forward evaluation")
    if str(risk) != cert["risk"] or str(upper) != cert["feasible_upper"]:
        raise AssertionError("saved feasible risk or cost differs from forward evaluation")
    if risk > alpha or lower > upper or str(upper - lower) != cert["gap"]:
        raise AssertionError("invalid primal/dual bracket")
    return lower, upper, upper - lower, risk


def main():
    path = Path("outputs/switching_asymmetric_timing_v1/dual_certificates.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    screen = json.loads(
        Path("outputs/switching_asymmetric_timing_v1/results.json").read_text(encoding="utf-8")
    )
    for source, digest in data["sha256"].items():
        actual = hashlib.sha256(Path(source).read_bytes()).hexdigest()
        if actual != digest:
            raise AssertionError(f"stale source hash: {source}")
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    summaries = []
    for (p01, p10, prior1), record, screen_cell in zip(
        CELLS, data["cells"], screen["cells"], strict=True
    ):
        model = RegimeModel(
            transition01=p01,
            transition10=p10,
            emission0=F(1, 20),
            emission1=F(19, 20),
            prior1=prior1,
        )
        game = CausalSwitchingGame(config, model)
        game.build()
        lower, upper, gap, risk = check_cell(game, record)
        calendar = screen_cell["best_fixed_calendar"]
        if (
            upper != F(calendar["calibrated_cost"])
            or risk != F(calendar["calibrated_risk"])
            or F(record["certificate"]["metrics"][3]) != F(calendar["queries"])
            or F(record["certificate"]["metrics"][4]) != F(calendar["switches"])
        ):
            raise AssertionError("certified primal does not match saved fixed-calendar witness")
        summaries.append((lower, upper, gap, risk))
    print(
        json.dumps(
            {
                "status": "verified_without_optimization",
                "cells": [list(map(str, x)) for x in summaries],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
