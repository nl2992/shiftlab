"""FCG-fast: float inner loop, exact final certificate (FCG scaling protocol v2).

Same cutting-plane scheme as ``frontier_cuts.frontier_cut_generation`` but:

* the learner tree, cost vector and risk rows used inside the loop are floating point
  (the cost vector is the decomposed game's own float cost construction);
* the exact belief DP (``_belief_from_history``) is memoised by learner information,
  because v1 evaluated it twice per promoting node (once in the tree build, once in
  ``exact_costs``);
* each iteration is: LP -> recover policy -> exact best response -> float cut row;
* the exact cost vector, exact rows (only those with a nonzero dual multiplier), exact
  rationalised dual lower bound ``L``, exact root repair, exact ``U`` and exact robust risk
  are computed once, at termination.

See ``docs/paper4/experiments/protocols/FCG_SCALE_PROTOCOL_V2.md``.
"""

from __future__ import annotations

import time
from fractions import Fraction as F

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, vstack

from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.paper4.frontier_cuts import (
    best_response_null,
    exact_costs,
    exact_dual_lower_bound_multi,
    mix_root_never_promote,
    risk_row_for_null,
)

U0_VERIFY_SECONDS_THRESHOLD = 2.0
VIOLATION_FLOOR = 1e-9


class FastGame(FirstPromotionDecomposedGame):
    """Decomposed game whose exact belief reconstruction is memoised by learner information."""

    def __init__(self, config, model) -> None:
        super().__init__(config, model)
        self._belief_cache: dict = {}

    def _belief_from_history(self, history, outcomes):
        key = (history, self.information(history, outcomes)[1])
        belief = self._belief_cache.get(key)
        if belief is None:
            belief = super()._belief_from_history(history, outcomes)
            self._belief_cache[key] = belief
        return belief


def float_risk_row(game, strategy, n: int) -> csr_matrix:
    """Float version of ``risk_row_for_null`` (coefficients are dyadic, hence exact in float)."""
    coefficients = np.zeros(n)
    horizon = game.config.horizon

    def visit(history, outcomes, weight):
        time_ = len(history) + 1
        if time_ > horizon:
            return
        _parent, children, choices = game.learner.infos[game.information(history, outcomes)]
        p = float(strategy.get((history, outcomes), F(1, 2)))
        for (action, query), child in zip(choices, children, strict=True):
            if action:
                coefficients[child] += weight
                continue
            following = history + ((action, query),)
            if query:
                if p:
                    visit(following, outcomes + ((time_, 1),), weight * p)
                if 1.0 - p:
                    visit(following, outcomes + ((time_, 0),), weight * (1.0 - p))
            else:
                visit(following, outcomes, weight)

    visit((), (), 1.0)
    return csr_matrix(coefficients.reshape(1, -1))


def _repair(game, raw_policy, robust_risk, alpha):
    activation = min(F(1), alpha / robust_risk) if robust_risk else F(1)
    if activation < 1:
        repaired, safe_policy = mix_root_never_promote(game, raw_policy, activation)
    else:
        repaired, safe_policy = raw_policy, None
    upper = sum(game.expected_metrics(repaired)[:3])
    if activation < 1:
        raw_cost = sum(game.expected_metrics(raw_policy)[:3])
        safe_cost = sum(game.expected_metrics(safe_policy)[:3])
        if upper != activation * raw_cost + (1 - activation) * safe_cost:
            raise AssertionError("root-mixture cost is not the convex combination")
    return repaired, upper, activation


def frontier_cut_generation_fast(config, model, max_iters: int = 100) -> dict:
    started = time.perf_counter()
    alpha = config.alpha
    alpha_float = float(alpha)

    # ---- build (float): learner tree + float costs from the game's own _alternative ----
    game = FastGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    n = game.learner.count
    flow, flow_rhs = game.learner.matrix()
    objective = np.zeros(n)
    for key, value in game.cost.items():
        objective[key] = value
    strategies: list[dict] = [{}]
    row_matrices = [float_risk_row(game, {}, n)]
    build_seconds = time.perf_counter() - started

    lp_seconds = verify_seconds = row_seconds = 0.0
    u0_seconds = 0.0
    u0 = None
    u0_note = "not computed"
    iterations: list[dict] = []
    final_x_policy = None
    dual_ub = dual_eq = None
    robust_risk = None
    n_lp_failures = 0

    for iteration in range(max_iters):
        t0 = time.perf_counter()
        a_ub = vstack(row_matrices, format="csr")
        result = linprog(
            objective,
            A_ub=a_ub,
            b_ub=np.full(a_ub.shape[0], alpha_float),
            A_eq=flow,
            b_eq=flow_rhs,
            bounds=[(0, None)] * n,
            method="highs",
            options={
                "time_limit": 600.0,
                "primal_feasibility_tolerance": 1e-9,
                "dual_feasibility_tolerance": 1e-9,
            },
        )
        lp_seconds += time.perf_counter() - t0
        if not result.success:
            n_lp_failures += 1
            raise RuntimeError(f"master LP failed: {result.message}")

        t1 = time.perf_counter()
        raw_policy, _records = game.recover(result.x)
        robust_risk, strategy = best_response_null(game, raw_policy)
        iter_verify = time.perf_counter() - t1
        verify_seconds += iter_verify
        final_x_policy = raw_policy
        dual_ub = [F(float(v)).limit_denominator(10**9) for v in result.ineqlin.marginals]
        dual_eq = [F(float(v)).limit_denominator(10**9) for v in result.eqlin.marginals]
        record = {
            "iteration": iteration,
            "rows": len(strategies),
            "lp_objective": float(result.fun),
            "raw_robust_risk_float": float(robust_risk),
            "verify_seconds": iter_verify,
        }
        iterations.append(record)

        if iteration == 0:
            if robust_risk <= alpha:
                u0_note = "iteration 0 already feasible: U0 = U (computed in final certificate)"
            elif iter_verify <= U0_VERIFY_SECONDS_THRESHOLD:
                tu = time.perf_counter()
                _rep, u0, _act = _repair(game, raw_policy, robust_risk, alpha)
                u0_seconds = time.perf_counter() - tu
                u0_note = "computed exactly after iteration 0 (IID LP policy + root repair)"
            else:
                u0_note = (
                    f"not computed: iteration-0 verify took {iter_verify:.2f}s "
                    f"> {U0_VERIFY_SECONDS_THRESHOLD}s cheapness threshold"
                )

        if robust_risk <= alpha:
            break

        t2 = time.perf_counter()
        new_row = float_risk_row(game, strategy, n)
        row_value = float((new_row @ result.x)[0])
        if not row_value > alpha_float + VIOLATION_FLOOR:
            raise AssertionError(
                f"iteration {iteration}: new cut not violated by LP x: "
                f"{row_value!r} <= alpha + {VIOLATION_FLOOR} (exact robust risk {robust_risk})"
            )
        if any(strategy == other for other in strategies):
            raise AssertionError(f"iteration {iteration}: strategy duplicates an existing row")
        strategies.append(strategy)
        row_matrices.append(new_row)
        row_seconds += time.perf_counter() - t2
        record["new_row_float_value"] = row_value
    else:
        raise RuntimeError(f"FCG-fast did not terminate within {max_iters} iterations")

    # ---- final exact certificate ----
    tc = time.perf_counter()
    costs = exact_costs(game)
    float_cost_gap = float(max(abs(float(c) - o) for c, o in zip(costs, objective, strict=True)))
    if float_cost_gap > 1e-12:
        raise AssertionError(f"float cost vector differs from exact by {float_cost_gap}")
    exact_rows: list[list[F] | None] = []
    for strategy, matrix, multiplier in zip(strategies, row_matrices, dual_ub, strict=True):
        if multiplier:
            row = risk_row_for_null(game, strategy)
            if not np.array_equal(np.array([float(v) for v in row]), matrix.toarray()[0]):
                raise AssertionError("float cut row differs from exact row")
            exact_rows.append(row)
        else:
            exact_rows.append(None)
    lower, dual_value, corr_max, corr_sum = exact_dual_lower_bound_multi(
        game, costs, exact_rows, flow, flow_rhs, dual_ub, dual_eq
    )
    repaired, upper, activation = _repair(game, final_x_policy, robust_risk, alpha)
    repaired_risk = game.null_risk(repaired)
    if repaired_risk > alpha:
        raise AssertionError(f"repaired policy risk {repaired_risk} > alpha {alpha}")
    if lower > upper:
        raise AssertionError(f"lower bound {lower} exceeds upper {upper}")
    final_certificate_seconds = time.perf_counter() - tc
    if u0_note.startswith("iteration 0 already feasible"):
        u0 = upper

    total = time.perf_counter() - started
    return {
        "iterations": iterations,
        "n_iterations": len(iterations),
        "n_rows": len(strategies),
        "n_exact_rows_built": sum(r is not None for r in exact_rows),
        "learner_variables": n,
        "builder_nodes": game.nodes,
        "U0": u0,
        "U0_note": u0_note,
        "U": upper,
        "L": lower,
        "gap": upper - lower,
        "dual_value": dual_value,
        "correction_max_times_count": corr_max,
        "correction_residual_sum": corr_sum,
        "activation": activation,
        "final_raw_robust_risk": robust_risk,
        "final_robust_risk": repaired_risk,
        "float_cost_vs_exact_max_abs_diff": float_cost_gap,
        "build_seconds": build_seconds,
        "lp_seconds": lp_seconds,
        "verify_seconds": verify_seconds,
        "row_seconds": row_seconds,
        "u0_seconds": u0_seconds,
        "final_certificate_seconds": final_certificate_seconds,
        "end_to_end_seconds": total,
    }
