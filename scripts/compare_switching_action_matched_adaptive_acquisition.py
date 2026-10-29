"""Action-matched acquisition ablation for the finite causal switching game."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack

from scripts.compare_switching_fixed_calendar_action_oracle import certify_game
from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


class TerminalAdaptiveAcquisition(CausalSwitchingGame):
    """Adaptive query choices; the only possible promotion is at the horizon."""

    def choices(self, history):
        time = len(history) + 1
        remaining = self.config.budget - sum(q for _, q in history)
        queries = (0, 1) if remaining and time + self.config.delay <= self.config.horizon else (0,)
        actions = (0, 1) if time == self.config.horizon else (0,)
        return tuple(product(actions, queries))


class TerminalFixedCalendar(TerminalAdaptiveAcquisition):
    """A deterministic, mandatory query calendar with the same terminal action."""

    def __init__(self, config, model, calendar):
        super().__init__(config, model)
        self.calendar = frozenset(calendar)

    def choices(self, history):
        time = len(history) + 1
        action_choices = (0, 1) if time == self.config.horizon else (0,)
        query = int(time in self.calendar)
        return tuple((action, query) for action in action_choices)


def solve_safely(game):
    """Solve the causal LP, then exactly evaluate root activation calibration."""
    game.build()
    e_matrix, e_rhs = game.learner.matrix()
    f_matrix, f_rhs = game.opponent.matrix()
    nx, ny = game.learner.count, game.opponent.count
    keys = list(game.risk)
    payoff = csr_matrix(
        ([game.risk[k] for k in keys], ([k[0] for k in keys], [k[1] for k in keys])),
        shape=(nx, ny),
    )
    objective = np.zeros(nx + len(f_rhs))
    for sequence, value in game.cost.items():
        objective[sequence] = value
    constraints = vstack(
        [
            hstack([payoff.T, -f_matrix.T]),
            hstack([csr_matrix((1, nx)), csr_matrix(f_rhs.reshape(1, -1))]),
        ]
    ).tocsr()
    rhs = np.r_[np.zeros(ny), float(game.config.alpha)]
    equality = hstack([e_matrix, csr_matrix((len(e_rhs), len(f_rhs)))]).tocsr()
    result = linprog(
        objective,
        A_ub=constraints,
        b_ub=rhs,
        A_eq=equality,
        b_eq=e_rhs,
        bounds=[(0, None)] * nx + [(None, None)] * len(f_rhs),
        method="highs",
        options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9},
    )
    if not result.success:
        raise RuntimeError(result.message)
    policy, records = game.recover(result.x[:nx])
    raw_metrics = game.expected_metrics(policy)
    raw_risk = game.null_risk(policy)

    def continuation(history, outcomes):
        choices = game.choices(history)
        preferred = (0, 0)
        if preferred not in choices:
            preferred = (0, 1)
        return tuple(F(choice == preferred) for choice in choices)

    continuation_metrics = game.expected_metrics(continuation)
    activation = min(F(1), game.config.alpha / raw_risk) if raw_risk else F(1)
    calibrated_metrics = tuple(
        activation * x + (1 - activation) * y
        for x, y in zip(raw_metrics, continuation_metrics, strict=True)
    )
    assert activation * raw_risk <= game.config.alpha
    return {
        "solver_objective": float(result.fun),
        "nodes": game.nodes,
        "raw_policy_cost": str(sum(raw_metrics[:3])),
        "raw_policy_risk": str(raw_risk),
        "activation_probability": str(activation),
        "calibrated_cost": str(sum(calibrated_metrics[:3])),
        "calibrated_risk": str(activation * raw_risk),
        "calibrated_queries": str(calibrated_metrics[3]),
        "calibrated_switches": str(calibrated_metrics[4]),
        "continuation_cost": str(sum(continuation_metrics[:3])),
        "policy_records": records,
    }


def positive_prefix_futility_policy(game):
    """Query after a positive prefix; promote only after three released positives."""

    def policy(history, outcomes):
        time = len(history) + 1
        released = dict(game.information(history, outcomes)[1])
        if time == 3:
            query_probability = F(4, 5)
        elif time == 4:
            query_probability = F(released.get(3) == 1)
        elif time == 5:
            query_probability = F(released.get(3) == released.get(4) == 1)
        else:
            query_probability = F(0)
        promote = F(
            time == game.config.horizon and all(released.get(event) == 1 for event in (3, 4, 5))
        )
        probs = []
        for action, query in game.choices(history):
            action_mass = promote if action else 1 - promote
            query_mass = query_probability if query else 1 - query_probability
            probs.append(action_mass * query_mass)
        assert sum(probs) == 1
        return tuple(probs)

    return policy


def static_cohort_lottery_policy(game):
    """Choose no cohort with 1/5 or the fixed (3,4,5) cohort with 4/5."""

    def policy(history, outcomes):
        time = len(history) + 1
        released = dict(game.information(history, outcomes)[1])
        active = len(history) >= 3 and history[2][1] == 1
        if time == 3:
            query_probability = F(4, 5)
        elif time in (4, 5):
            query_probability = F(active)
        else:
            query_probability = F(0)
        promote = F(
            time == game.config.horizon
            and active
            and all(released.get(event) == 1 for event in (3, 4, 5))
        )
        probabilities = []
        for action, query in game.choices(history):
            action_mass = promote if action else 1 - promote
            query_mass = query_probability if query else 1 - query_probability
            probabilities.append(action_mass * query_mass)
        assert sum(probabilities) == 1
        return tuple(probabilities)

    return policy


def main():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=200_000,
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    adaptive_game = TerminalAdaptiveAcquisition(config, model)
    adaptive = solve_safely(adaptive_game)
    explicit_policy = positive_prefix_futility_policy(adaptive_game)
    explicit_metrics = adaptive_game.expected_metrics(explicit_policy)
    explicit_risk = adaptive_game.null_risk(explicit_policy)
    static_lottery_policy = static_cohort_lottery_policy(adaptive_game)
    static_lottery_metrics = adaptive_game.expected_metrics(static_lottery_policy)
    static_lottery_risk = adaptive_game.null_risk(static_lottery_policy)
    eligible = range(1, config.horizon - config.delay + 1)
    calendars = [cal for size in range(config.budget + 1) for cal in combinations(eligible, size)]
    fixed = []
    for calendar in calendars:
        game = TerminalFixedCalendar(config, model, calendar)
        row = solve_safely(game)
        certificate = certify_game(game)
        fixed.append({"calendar": list(calendar), **row, "certificate": certificate})
    best = min(fixed, key=lambda row: F(row["calibrated_cost"]))
    gap = F(best["calibrated_cost"]) - F(adaptive["calibrated_cost"])
    best_certified_lower = min(F(row["certificate"]["lower_bound"]) for row in fixed)
    adaptive_upper = sum(explicit_metrics[:3])
    result = {
        "status": "completed_action_matched_finite_acquisition_ablation",
        "protocol": "docs/switching_action_matched_adaptive_acquisition_v1.md",
        "contract": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "terminal_action_only": True,
            "fixed_calendar_query_is_mandatory": True,
            "causal_endpoint_null": True,
        },
        "adaptive_acquisition": adaptive,
        "explicit_positive_prefix_futility_rule": {
            "query_rule": "lottery 4/5 at event 3; query at event 4 iff label 3 is positive; query at event 5 iff labels 3 and 4 are positive",
            "promotion_rule": "promote at event 6 iff labels 3, 4 and 5 are all positive",
            "expected_cost": str(sum(explicit_metrics[:3])),
            "expected_queries": str(explicit_metrics[3]),
            "false_promotion_risk": str(explicit_risk),
            "matches_adaptive_optimum_recovered_policy": sum(explicit_metrics[:3])
            == F(adaptive["calibrated_cost"]),
        },
        "static_cohort_lottery_baseline": {
            "rule": "with probability 1/5 make no query; otherwise query at events 3, 4 and 5 and promote iff all three labels are positive",
            "expected_cost": str(sum(static_lottery_metrics[:3])),
            "expected_queries": str(static_lottery_metrics[3]),
            "false_promotion_risk": str(static_lottery_risk),
            "futility_savings_cost": str(
                sum(static_lottery_metrics[:3]) - sum(explicit_metrics[:3])
            ),
            "futility_savings_queries": str(static_lottery_metrics[3] - explicit_metrics[3]),
        },
        "best_fixed_calendar": best,
        "fixed_calendar_count": len(fixed),
        "adaptive_minus_best_fixed_cost": str(
            F(adaptive["calibrated_cost"]) - F(best["calibrated_cost"])
        ),
        "best_fixed_minus_adaptive_cost": str(gap),
        "certified_best_fixed_lower_bound": str(best_certified_lower),
        "explicit_adaptive_feasible_upper_bound": str(adaptive_upper),
        "certified_fixed_class_gap_lower_bound": str(best_certified_lower - adaptive_upper),
        "all_fixed_calendars": fixed,
        "interpretation": "All 26 terminal fixed-calendar policies have independently checked rational dual lower bounds. The explicit adaptive positive-prefix policy is feasible with exactly evaluated cost/risk, proving a finite class gap. The reported adaptive LP optimizer remains numerical; this is not a scalable method or novelty result.",
        "claim_scope": "Certified finite separation from every deterministic calendar with terminal-only action, using rational dual lower bounds and an explicit adaptive feasible policy; not a certified adaptive optimum and not a separation from all randomized calendar mixtures.",
        "sha256": {
            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in (
                "scripts/compare_switching_action_matched_adaptive_acquisition.py",
                "scripts/verify_switching_action_matched_adaptive_acquisition.py",
                "src/shiftlab/dive/causal_switching_game.py",
                "src/shiftlab/dive/delayed_regime_information.py",
                "scripts/certify_switching_reversal_lp_bound.py",
                "docs/switching_action_matched_adaptive_acquisition_v1.md",
            )
        },
    }
    target = Path("outputs/switching_action_matched_adaptive_acquisition_v1")
    target.mkdir(parents=True, exist_ok=True)
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
