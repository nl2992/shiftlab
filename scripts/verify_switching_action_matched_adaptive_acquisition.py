"""Independently replay recovered action-matched acquisition policies."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

from scipy.sparse import csr_matrix, hstack, vstack

from scripts.certify_switching_reversal_lp_bound import exact_alternative_costs, matrix_fraction
from scripts.compare_switching_action_matched_adaptive_acquisition import (
    TerminalAdaptiveAcquisition,
    TerminalFixedCalendar,
    positive_prefix_futility_policy,
    static_cohort_lottery_policy,
)
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def verify_dual(game, certificate):
    game.build()
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    keys = list(game.risk)
    payoff = csr_matrix(
        ([game.risk[k] for k in keys], ([k[0] for k in keys], [k[1] for k in keys])),
        shape=(nx, ny),
    )
    inequality = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    dual_ub = [F(value) for value in certificate["dual_inequality"]]
    dual_eq = [F(value) for value in certificate["dual_equality"]]
    assert all(value <= 0 for value in dual_ub)
    a_csc, e_csc = inequality.tocsc(), equality.tocsc()
    objective = exact_alternative_costs(game)
    violations = []
    free_residual = F(0)
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
            violations.append(max(F(0), lhs - objective[column]))
        else:
            free_residual = max(free_residual, abs(lhs))
    assert free_residual == 0
    rhs_exact = [F(0)] * ny + [game.config.alpha]
    dual_value = sum(a * b for a, b in zip(rhs_exact, dual_ub, strict=True)) + sum(
        matrix_fraction(a) * b for a, b in zip(e_rhs, dual_eq, strict=True)
    )
    lower = dual_value - sum(violations)
    assert lower == F(certificate["lower_bound"])
    return lower


def policy_from_records(game, records):
    table = {}
    for row in records:
        key = (tuple(tuple(x) for x in row["history"]), tuple(tuple(x) for x in row["released"]))
        table[key] = (
            tuple(tuple(choice) for choice in row["choices"]),
            tuple(F(probability) for probability in row["probabilities"]),
        )

    def policy(history, outcomes):
        choices, probabilities = table[game.information(history, outcomes)]
        assert choices == game.choices(history)
        return probabilities

    return policy


def verify_one(game: CausalSwitchingGame, row):
    game.build()
    policy = policy_from_records(game, row["policy_records"])
    metrics = game.expected_metrics(policy)
    risk = game.null_risk(policy)
    assert sum(metrics[:3]) == F(row["raw_policy_cost"])
    assert risk == F(row["raw_policy_risk"])
    assert F(row["calibrated_cost"]) == F(row["raw_policy_cost"])
    assert F(row["calibrated_risk"]) == risk
    assert risk <= game.config.alpha
    assert metrics[3] == F(row["calibrated_queries"])
    for key, (_, _, choices) in game.learner.infos.items():
        history = key[0]
        assert sum(q for _, q in history) <= game.config.budget
        if len(history) + 1 < game.config.horizon:
            assert all(action == 0 for action, _ in choices)
        else:
            assert len(history) + 1 == game.config.horizon
    for key, (_, _, choices) in game.learner.infos.items():
        time = len(key[0]) + 1
        assert all(
            not query or time + game.config.delay <= game.config.horizon for _, query in choices
        )
    return metrics, risk


def main():
    path = Path("outputs/switching_action_matched_adaptive_acquisition_v1/results.json")
    result = json.loads(path.read_text(encoding="utf-8"))
    for source, digest in result["sha256"].items():
        assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == digest
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    model = RegimeModel(F(1, 4), F(1, 4), F(1, 20), F(19, 20), F(1, 2))
    adaptive_game = TerminalAdaptiveAcquisition(config, model)
    adaptive_metrics, adaptive_risk = verify_one(adaptive_game, result["adaptive_acquisition"])
    adaptive_lower = verify_dual(adaptive_game, result["adaptive_certificate"])
    explicit_policy = positive_prefix_futility_policy(adaptive_game)
    explicit_metrics = adaptive_game.expected_metrics(explicit_policy)
    explicit_risk = adaptive_game.null_risk(explicit_policy)
    explicit = result["explicit_positive_prefix_futility_rule"]
    assert sum(explicit_metrics[:3]) == F(explicit["expected_cost"])
    assert explicit_metrics[3] == F(explicit["expected_queries"])
    assert explicit_risk == F(explicit["false_promotion_risk"])
    assert tuple(explicit_metrics) == tuple(adaptive_metrics)
    assert explicit_risk == adaptive_risk
    static_policy = static_cohort_lottery_policy(adaptive_game)
    static_metrics = adaptive_game.expected_metrics(static_policy)
    static_risk = adaptive_game.null_risk(static_policy)
    static = result["static_cohort_lottery_baseline"]
    assert sum(static_metrics[:3]) == F(static["expected_cost"])
    assert static_metrics[3] == F(static["expected_queries"])
    assert static_risk == F(static["false_promotion_risk"])
    assert sum(static_metrics[:3]) - sum(explicit_metrics[:3]) == F(static["futility_savings_cost"])
    assert static_metrics[3] - explicit_metrics[3] == F(static["futility_savings_queries"])
    costs = []
    certified_lowers = []
    for row in result["all_fixed_calendars"]:
        game = TerminalFixedCalendar(config, model, row["calendar"])
        metrics, _risk = verify_one(game, row)
        certified_lowers.append(verify_dual(game, row["certificate"]))
        costs.append((F(row["calibrated_cost"]), tuple(row["calendar"])))
        assert metrics[3] == len(row["calendar"])
    best_cost, best_calendar = min(costs)
    assert best_cost == F(result["best_fixed_calendar"]["calibrated_cost"])
    assert list(best_calendar) == result["best_fixed_calendar"]["calendar"]
    assert F(result["adaptive_acquisition"]["calibrated_cost"]) == sum(adaptive_metrics[:3])
    gap = best_cost - sum(adaptive_metrics[:3])
    assert gap == F(result["best_fixed_minus_adaptive_cost"])
    assert adaptive_risk == config.alpha
    adaptive_upper = sum(explicit_metrics[:3])
    assert adaptive_lower <= adaptive_upper
    assert adaptive_upper - adaptive_lower == F(result["adaptive_optimum_bracket_width"])
    certified_best_lower = min(certified_lowers)
    explicit_adaptive_cost = sum(explicit_metrics[:3])
    assert certified_best_lower == F(result["certified_best_fixed_lower_bound"])
    assert explicit_adaptive_cost == F(result["explicit_adaptive_feasible_upper_bound"])
    assert certified_best_lower - explicit_adaptive_cost == F(
        result["certified_fixed_class_gap_lower_bound"]
    )
    assert certified_best_lower > explicit_adaptive_cost
    print(
        json.dumps(
            {
                "status": "recovered_policies_verified_by_exact_forward_recursions",
                "fixed_calendars_checked": len(costs),
                "rational_dual_certificates_checked": len(certified_lowers),
                "adaptive_cost": str(sum(adaptive_metrics[:3])),
                "adaptive_null_risk": str(adaptive_risk),
                "adaptive_certified_lower_bound": str(adaptive_lower),
                "adaptive_feasible_upper_bound": str(adaptive_upper),
                "adaptive_optimum_bracket_width": str(adaptive_upper - adaptive_lower),
                "randomized_calendar_mixtures_covered_by_adaptive_oracle": True,
                "explicit_rule_matches_adaptive_recovered_policy": True,
                "static_lottery_cost": str(sum(static_metrics[:3])),
                "static_lottery_queries": str(static_metrics[3]),
                "static_lottery_null_risk": str(static_risk),
                "adaptive_futility_savings": str(F(static["futility_savings_cost"])),
                "best_fixed_calendar": list(best_calendar),
                "best_fixed_cost": str(best_cost),
                "fixed_null_risk": str(config.alpha),
                "best_fixed_minus_adaptive": str(gap),
                "certified_best_fixed_lower_bound": str(certified_best_lower),
                "explicit_adaptive_feasible_upper_bound": str(explicit_adaptive_cost),
                "certified_gap_lower_bound": str(certified_best_lower - explicit_adaptive_cost),
                "claim_scope": "The adaptive terminal-action optimum is bracketed by an independently checked rational dual lower bound and an exact feasible policy upper bound; this includes every randomized calendar mixture. No scalable method or novelty claim.",
                "source_hashes_match": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
