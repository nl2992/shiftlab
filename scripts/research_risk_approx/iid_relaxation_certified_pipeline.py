"""Solve the IID-null relaxation, then certify/repair under the full null."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction as F
from functools import cache
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/research_risk_approx"))

PROTOCOL = ROOT / "docs/risk_preserving_approx/IID_RELAXATION_CERTIFIED_PIPELINE_PROTOCOL_V1.md"
GRID = ROOT / "docs/risk_preserving_approx/t8_b4_calendar_v1.json"
PORTFOLIO = ROOT / "docs/risk_preserving_approx/t8_b4_calendar_portfolio_v1.json"
OUTPUT = ROOT / "docs/risk_preserving_approx/iid_relaxation_certified_pipeline_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def learner_only_game(config, model):
    from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

    game = FirstPromotionDecomposedGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    return game


def iid_risk_coefficients(game) -> list[F]:
    coefficients = [0] * game.learner.count
    for tape in product((0, 1), repeat=game.config.horizon):

        def visit(history, outcomes, sequence, tape=tape):
            time = len(history) + 1
            if time > game.config.horizon:
                return
            information = game.information(history, outcomes)
            _parent, children, choices = game.learner.infos[information]
            for (action, query), child in zip(choices, children, strict=True):
                if action:
                    coefficients[child] += 1
                    continue
                following = history + ((action, query),)
                if query:
                    visit(following, outcomes + ((time, tape[time - 1]),), child)
                else:
                    visit(following, outcomes, child)

        visit((), (), 0)
    denominator = 2**game.config.horizon
    return [F(value, denominator) for value in coefficients]


def exact_dual_lower_bound(game, costs, risk, equality, rhs, dual_ub, dual_eq):
    if dual_ub > 0:
        raise ValueError("IID risk dual has the wrong sign")
    matrix = equality.tocoo()
    exact_lhs = [risk[index] * dual_ub for index in range(game.learner.count)]
    for row, column, value in zip(matrix.row, matrix.col, matrix.data, strict=True):
        exact_lhs[int(column)] += F(int(value)) * dual_eq[int(row)]
    correction = max(
        (max(F(0), lhs - cost) for lhs, cost in zip(exact_lhs, costs, strict=True)),
        default=F(0),
    )
    dual_value = game.config.alpha * dual_ub + sum(
        (F(int(value)) * multiplier for value, multiplier in zip(rhs, dual_eq, strict=True)),
        F(0),
    )
    # Every learner realization variable lies in [0,1]; this is a valid uniform
    # correction for any positive exact reduced-cost residual after rationalization.
    lower = dual_value - correction * game.learner.count
    return lower, dual_value, correction


def realization_flow(game, policy):
    values = [None] * game.learner.count
    values[0] = F(1)
    for (history, released), (parent, children, choices) in game.learner.infos.items():
        if values[parent] is None:
            raise AssertionError("learner realization parent was not initialized")
        probabilities = policy(history, released)
        for child, probability in zip(children, probabilities, strict=True):
            values[child] = values[parent] * probability
    if any(value is None for value in values):
        raise AssertionError("incomplete learner realization flow")
    return [value for value in values if value is not None]


def exact_risk(game, policy, iid: bool):
    @cache
    def visit(history, outcomes):
        time = len(history) + 1
        if time > game.config.horizon:
            return F(0)
        result = F(0)
        probabilities = policy(history, outcomes)
        for (action, query), action_mass in zip(game.choices(history), probabilities, strict=True):
            if not action_mass:
                continue
            if action:
                continuation = F(1)
            elif query:
                following = history + ((action, query),)
                zero = visit(following, outcomes + ((time, 0),))
                one = visit(following, outcomes + ((time, 1),))
                continuation = (zero + one) / 2 if iid else max(zero, (zero + one) / 2)
            else:
                continuation = visit(history + ((action, query),), outcomes)
            result += action_mass * continuation
        return result

    return visit((), ()), visit.cache_info().currsize


def main() -> None:
    from cut_certificate_helpers import exact_costs

    from shiftlab.dive.causal_switching_game import GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel
    from shiftlab.dive.eprocess_gated_planner import mix_with_never_promote

    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    import psutil

    started = time.perf_counter()
    process = psutil.Process()
    baseline_rss = process.memory_info().rss
    config = GameConfig(
        horizon=8,
        budget=4,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 50),
        emission1=F(49, 50),
        prior1=F(1, 2),
    )
    game = learner_only_game(config, model)
    exact_cost = exact_costs(game)
    risk = iid_risk_coefficients(game)
    flow, flow_rhs = game.learner.matrix()
    objective = np.array([float(value) for value in exact_cost], dtype=float)
    risk_row = csr_matrix(np.array([[float(value) for value in risk]], dtype=float))
    result = linprog(
        objective,
        A_ub=risk_row,
        b_ub=np.array([float(config.alpha)]),
        A_eq=flow,
        b_eq=flow_rhs,
        bounds=[(0, None)] * game.learner.count,
        method="highs",
        options={
            "time_limit": 60.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success:
        raise RuntimeError(f"IID relaxation LP failed: {result.message}")

    dual_ub = F(float(result.ineqlin.marginals[0])).limit_denominator(10**9)
    dual_eq = [F(float(value)).limit_denominator(10**9) for value in result.eqlin.marginals]
    lower, dual_value, correction = exact_dual_lower_bound(
        game, exact_cost, risk, flow, flow_rhs, dual_ub, dual_eq
    )

    raw_policy, records = game.recover(result.x)
    raw_metrics = game.expected_metrics(raw_policy)
    raw_cost = sum(raw_metrics[:3])
    raw_iid_risk, iid_states = exact_risk(game, raw_policy, iid=True)
    raw_robust_risk, robust_states = exact_risk(game, raw_policy, iid=False)
    framework_raw_risk = game.null_risk(raw_policy)
    realization = realization_flow(game, raw_policy)
    primal_iid_risk = sum(
        (coefficient * value for coefficient, value in zip(risk, realization, strict=True)), F(0)
    )
    if raw_iid_risk != primal_iid_risk:
        raise AssertionError(f"IID risk row mismatch: {raw_iid_risk} != {primal_iid_risk}")
    if raw_robust_risk != framework_raw_risk:
        raise AssertionError(
            f"independent null recursion mismatch: {raw_robust_risk} != {framework_raw_risk}"
        )

    activation = min(F(1), config.alpha / raw_robust_risk) if raw_robust_risk else F(1)
    repaired_policy = mix_with_never_promote(game, raw_policy, activation)
    safe_metrics = game.expected_metrics(
        lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    )
    repaired_metrics = game.expected_metrics(repaired_policy)
    repaired_cost = sum(repaired_metrics[:3])
    repaired_risk, repaired_states = exact_risk(game, repaired_policy, iid=False)
    framework_repaired_risk = game.null_risk(repaired_policy)
    safe_cost = sum(safe_metrics[:3])
    if repaired_risk != framework_repaired_risk or repaired_risk > config.alpha:
        raise AssertionError("repaired policy failed exact causal-null certification")
    if lower > repaired_cost:
        raise AssertionError("dual lower bound exceeds verified feasible upper policy")

    grid = json.loads(GRID.read_text(encoding="utf-8"))
    cell = next(
        row
        for row in grid["cells"]
        if row["transition"] == "1/10" and row["emissions"] == ["1/50", "49/50"]
    )
    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    reference = cell["methods"]["reference"]
    result_data = {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "input_hashes": {"calendar_grid": sha(GRID), "calendar_portfolio": sha(PORTFOLIO)},
        "config": {
            "horizon": config.horizon,
            "budget": config.budget,
            "delay": config.delay,
            "alpha": str(config.alpha),
            "query_cost": str(config.query_cost),
            "switch_cost": str(config.switch_cost),
            "transition": str(model.transition01),
            "emissions": [str(model.emission0), str(model.emission1)],
        },
        "master": {
            "status": result.message,
            "numeric_objective": float(result.fun),
            "learner_variables": game.learner.count,
            "flow_equalities": flow.shape[0],
            "risk_rows": 1,
            "opponent_variables": 0,
            "builder_nodes": game.nodes,
            "exact_dual_risk_multiplier": str(dual_ub),
            "exact_dual_value": str(dual_value),
            "exact_reduced_cost_correction": str(correction),
            "iid_relaxation_lower_bound": str(lower),
        },
        "raw_policy": {
            "cost": str(raw_cost),
            "iid_risk": str(raw_iid_risk),
            "robust_risk": str(raw_robust_risk),
            "framework_robust_risk": str(framework_raw_risk),
            "expected_metrics": [str(value) for value in raw_metrics],
            "iid_verifier_states": iid_states,
            "robust_verifier_states": robust_states,
            "behavior_records": records,
        },
        "repair": {
            "activation": str(activation),
            "safe_cost": str(safe_cost),
            "cost": str(repaired_cost),
            "robust_risk": str(repaired_risk),
            "framework_robust_risk": str(framework_repaired_risk),
            "expected_metrics": [str(value) for value in repaired_metrics],
            "verifier_states": repaired_states,
            "certified_gap_upper": str(repaired_cost - lower),
        },
        "baselines": {
            "best_calendar_cost": cell["best_calendar_cost"],
            "best_calendar": cell["best_calendar"],
            "full_decomposed_cost": reference["calibrated_cost"],
            "full_decomposed_risk": reference["calibrated_risk"],
            "full_decomposed_nodes": reference["nodes"],
            "full_decomposed_learner_sequences": reference["learner_sequences"],
            "full_decomposed_opponent_sequences": reference["null_sequences"],
            "full_decomposed_solve_seconds": reference["solve_seconds"],
            "calendar_portfolio_cost": portfolio["portfolio_exact_cost"],
        },
        "resources": {
            "elapsed_seconds": time.perf_counter() - started,
            "rss_delta_bytes": process.memory_info().rss - baseline_rss,
        },
        "status": "PASS",
    }
    OUTPUT.write_text(json.dumps(result_data, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "lower": str(lower),
                "raw_cost": str(raw_cost),
                "raw_iid_risk": str(raw_iid_risk),
                "raw_robust_risk": str(raw_robust_risk),
                "activation": str(activation),
                "repaired_cost": str(repaired_cost),
                "repaired_risk": str(repaired_risk),
                "gap": str(repaired_cost - lower),
                "best_calendar_cost": cell["best_calendar_cost"],
                "status": "PASS",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
