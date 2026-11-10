"""Frontier-cut generation (FCG) on the exact first-promotion decomposed game.

Cutting-plane / constraint-generation scheme (Benders-type, cf. sequence-form double
oracle). Master: learner flow polytope with first-promotion risk rows
``r_nu . x <= alpha`` for a growing set K of pure causal-null strategies ``nu``
(``p in {0, 1/2}`` at each query node).  Separation oracle: the exact causal-null best
response recursion (same as ``CausalSwitchingGame.null_risk``).  See
``docs/paper4/experiments/protocols/FCG_DEV_PROTOCOL_V1.md``.

Helpers ``learner_only_game``, ``exact_dual_lower_bound``, ``realization_flow``,
``exact_risk`` and the LP call follow
``scripts/research_risk_approx/iid_relaxation_certified_pipeline.py``;
``exact_costs`` follows ``scripts/research_risk_approx/cut_certificate_helpers.py``.
"""

from __future__ import annotations

import time
from fractions import Fraction as F
from functools import cache

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

HALF = F(1, 2)


def learner_only_game(config, model) -> FirstPromotionDecomposedGame:
    """Build only the learner tree (no opponent sequences)."""
    game = FirstPromotionDecomposedGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    return game


def exact_costs(game) -> list[F]:
    """Exact linear cost of every learner sequence (promotion continuation included)."""
    costs = [F(0)] * game.learner.count

    def visit(history, outcomes, sequence, weight, posterior, total):
        time_ = len(history) + 1
        if time_ > game.config.horizon:
            costs[sequence] += weight * total
            return
        state1 = game.model.propagate(posterior, 1)
        positive = game.model.emission(state1)
        _, children, choices = game.learner.infos[game.information(history, outcomes)]
        for (action, query), child in zip(choices, children, strict=True):
            if action:
                belief = game._belief_from_history(history, outcomes)
                remaining = game.config.budget - sum(q for _, q in history)
                continuation = game._promote_value(time_, remaining, belief, query)
                costs[child] += weight * (total + continuation)
                continue
            stage = positive + game.config.query_cost * query
            following = history + ((action, query),)
            if query:
                for label, probability in ((0, 1 - positive), (1, positive)):
                    likelihood = game.model.emission1 if label else 1 - game.model.emission1
                    visit(
                        following,
                        outcomes + ((time_, label),),
                        child,
                        weight * probability,
                        state1 * likelihood / probability,
                        total + stage,
                    )
            else:
                visit(following, outcomes, child, weight, state1, total + stage)

    visit((), (), 0, F(1), game.model.prior1, F(0))
    return costs


def best_response_null(game, policy) -> tuple[F, dict]:
    """Exact causal-null best response (non-IID branch of ``null_risk``).

    The null sees pending outcomes (full ``outcomes``).  At a query node it plays
    ``p = 0`` iff ``zero > one`` (strict inversion), else ``p = 1/2``; the node value is
    ``max(zero, (zero + one)/2)`` exactly as in ``CausalSwitchingGame.null_risk``.
    Strategy keys are ``(history, outcomes)`` of the learner decision node at which
    the (action=0, query=1) choice has positive policy mass.
    """
    strategy: dict = {}

    @cache
    def visit(history, outcomes):
        time_ = len(history) + 1
        if time_ > game.config.horizon:
            return F(0)
        result = F(0)
        for (action, query), mass in zip(
            game.choices(history), policy(history, outcomes), strict=True
        ):
            if not mass:
                continue
            if action:
                value = F(1)
            else:
                following = history + ((action, query),)
                if query:
                    zero = visit(following, outcomes + ((time_, 0),))
                    one = visit(following, outcomes + ((time_, 1),))
                    if zero > one:
                        strategy[history, outcomes] = F(0)
                        value = zero
                    else:
                        strategy[history, outcomes] = HALF
                        value = (zero + one) / 2
                else:
                    value = visit(following, outcomes)
            result += mass * value
        return result

    risk = visit((), ())
    return risk, strategy


def risk_row_for_null(game, strategy) -> list[F]:
    """First-promotion probability coefficient per learner sequence under a fixed null.

    Missing strategy keys default to ``p = 1/2``.  At a query node the pending outcome
    is 1 with probability ``p`` and 0 with ``1 - p``.
    """
    coefficients = [F(0)] * game.learner.count

    def visit(history, outcomes, weight):
        time_ = len(history) + 1
        if time_ > game.config.horizon:
            return
        _parent, children, choices = game.learner.infos[game.information(history, outcomes)]
        p = strategy.get((history, outcomes), HALF)
        for (action, query), child in zip(choices, children, strict=True):
            if action:
                coefficients[child] += weight
                continue
            following = history + ((action, query),)
            if query:
                # Every learner path to `child` continues via the same sequence variable:
                # the row coefficient is attached to promotion sequences only.
                if p:
                    visit(following, outcomes + ((time_, 1),), weight * p)
                if 1 - p:
                    visit(following, outcomes + ((time_, 0),), weight * (1 - p))
            else:
                visit(following, outcomes, weight)

    visit((), (), F(1))
    return coefficients


def exact_dual_lower_bound_multi(game, costs, rows, equality, rhs, dual_ub, dual_eq):
    """Exact weak-duality lower bound for ``min c x, R x <= alpha, E x = e, 0 <= x <= 1``.

    ``dual_ub[k] <= 0`` (HiGHS convention).  Returns
    ``(lower, dual_value, correction_max_times_count, residual_sum)``.  The reported
    ``lower`` subtracts the sharper valid correction ``sum_j max(0, lhs_j - c_j)``
    (``x_j <= 1``); the original ``max_j(...) * count`` correction is also returned.
    """
    if any(value > 0 for value in dual_ub):
        raise ValueError("risk-row duals have the wrong sign")
    n = game.learner.count
    exact_lhs = [F(0)] * n
    for row, multiplier in zip(rows, dual_ub, strict=True):
        if multiplier:
            for j, coefficient in enumerate(row):
                if coefficient:
                    exact_lhs[j] += coefficient * multiplier
    matrix = equality.tocoo()
    for r, c, v in zip(matrix.row, matrix.col, matrix.data, strict=True):
        exact_lhs[int(c)] += F(int(v)) * dual_eq[int(r)]
    residuals = [max(F(0), lhs - cost) for lhs, cost in zip(exact_lhs, costs, strict=True)]
    correction = max(residuals, default=F(0))
    residual_sum = sum(residuals, F(0))
    dual_value = game.config.alpha * sum(dual_ub, F(0)) + sum(
        (F(int(v)) * m for v, m in zip(rhs, dual_eq, strict=True)), F(0)
    )
    lower = dual_value - min(residual_sum, correction * n)
    return lower, dual_value, correction * n, residual_sum


def realization_flow(game, policy) -> list[F]:
    values: list[F | None] = [None] * game.learner.count
    values[0] = F(1)
    for (history, released), (parent, children, _c) in game.learner.infos.items():
        if values[parent] is None:
            raise AssertionError("learner realization parent was not initialized")
        for child, probability in zip(children, policy(history, released), strict=True):
            values[child] = values[parent] * probability
    if any(v is None for v in values):
        raise AssertionError("incomplete learner realization flow")
    return [v for v in values if v is not None]


def mix_root_never_promote(game, raw_policy, activation: F):
    """Behavioural realization of the root lottery ``activation * raw + (1-activation) * safe``.

    Done in sequence-form (realization) space, so it is exact for STOCHASTIC raw policies.
    (``eprocess_gated_planner.mix_with_never_promote`` weights consistent plans by their
    prior mixture weight only, which is a valid Kuhn realization for deterministic plans
    but not for stochastic ones; it was observed to return a repaired risk above alpha.)
    """
    raw = realization_flow(game, raw_policy)

    def safe_policy(history, outcomes):
        return tuple(F(choice == (0, 0)) for choice in game.choices(history))

    safe = realization_flow(game, safe_policy)
    mixed = [activation * a + (1 - activation) * b for a, b in zip(raw, safe, strict=True)]
    behavior = {}
    for key, (parent, children, _choices) in game.learner.infos.items():
        if mixed[parent] == 0:
            behavior[key] = raw_policy(*key)
        else:
            behavior[key] = tuple(mixed[c] / mixed[parent] for c in children)

    def policy(history, outcomes):
        if any(action for action, _ in history):
            return raw_policy(history, outcomes)  # post-promotion: only the raw branch gets here
        return behavior[game.information(history, outcomes)]

    return policy, safe_policy


def _iid_risk(game, policy) -> F:
    @cache
    def visit(history, outcomes):
        time_ = len(history) + 1
        if time_ > game.config.horizon:
            return F(0)
        result = F(0)
        for (action, query), mass in zip(
            game.choices(history), policy(history, outcomes), strict=True
        ):
            if not mass:
                continue
            if action:
                value = F(1)
            elif query:
                following = history + ((action, query),)
                value = (
                    visit(following, outcomes + ((time_, 0),))
                    + visit(following, outcomes + ((time_, 1),))
                ) / 2
            else:
                value = visit(history + ((action, query),), outcomes)
            result += mass * value
        return result

    return visit((), ())


def frontier_cut_generation(config, model, max_iters: int = 50) -> dict:
    started = time.perf_counter()
    game = learner_only_game(config, model)
    costs = exact_costs(game)
    n = game.learner.count
    flow, flow_rhs = game.learner.matrix()
    objective = np.array([float(v) for v in costs], dtype=float)
    alpha = config.alpha
    rows: list[list[F]] = [risk_row_for_null(game, {})]
    iid_row = rows[0]
    build_seconds = time.perf_counter() - started
    iterations: list[dict] = []
    upper_best: F | None = None
    final: dict = {}
    for iteration in range(max_iters):
        t0 = time.perf_counter()
        a_ub = csr_matrix(np.array([[float(v) for v in row] for row in rows], dtype=float))
        result = linprog(
            objective,
            A_ub=a_ub,
            b_ub=np.full(len(rows), float(alpha)),
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
        if not result.success:
            raise RuntimeError(f"master LP failed: {result.message}")
        dual_ub = [F(float(v)).limit_denominator(10**9) for v in result.ineqlin.marginals]
        dual_eq = [F(float(v)).limit_denominator(10**9) for v in result.eqlin.marginals]
        lower, dual_value, corr_max, corr_sum = exact_dual_lower_bound_multi(
            game, costs, rows, flow, flow_rhs, dual_ub, dual_eq
        )
        lp_seconds = time.perf_counter() - t0

        t1 = time.perf_counter()
        raw_policy, _records = game.recover(result.x)
        robust_risk, strategy = best_response_null(game, raw_policy)
        if robust_risk != game.null_risk(raw_policy):
            raise AssertionError("best_response_null disagrees with game.null_risk")
        raw_iid_risk = _iid_risk(game, raw_policy)
        new_row = risk_row_for_null(game, strategy)
        realization = realization_flow(game, raw_policy)
        exact_row_value = sum((c * v for c, v in zip(new_row, realization, strict=True)), F(0))
        if exact_row_value != robust_risk:
            raise AssertionError(f"cut row value {exact_row_value} != robust risk {robust_risk}")
        row_float_value = float(np.dot([float(c) for c in new_row], result.x))
        verify_seconds = time.perf_counter() - t1

        t2 = time.perf_counter()
        activation = min(F(1), alpha / robust_risk) if robust_risk else F(1)
        if activation < 1:
            repaired, safe_policy = mix_root_never_promote(game, raw_policy, activation)
        else:
            repaired = raw_policy
        repaired_metrics = game.expected_metrics(repaired)
        upper = sum(repaired_metrics[:3])
        if activation < 1:
            raw_cost = sum(game.expected_metrics(raw_policy)[:3])
            safe_cost = sum(game.expected_metrics(safe_policy)[:3])
            if upper != activation * raw_cost + (1 - activation) * safe_cost:
                raise AssertionError("root-mixture cost is not the convex combination")
        repaired_risk = game.null_risk(repaired)
        if repaired_risk > alpha:
            raise AssertionError(f"repaired policy risk {repaired_risk} > alpha {alpha}")
        repair_seconds = time.perf_counter() - t2

        if lower > upper:
            raise AssertionError(f"lower bound {lower} exceeds upper {upper}")
        record = {
            "iteration": iteration,
            "rows": len(rows),
            "L": lower,
            "U": upper,
            "dual_value": dual_value,
            "correction_max_times_count": corr_max,
            "correction_residual_sum": corr_sum,
            "lp_objective": float(result.fun),
            "raw_robust_risk": robust_risk,
            "raw_iid_risk": raw_iid_risk,
            "repaired_robust_risk": repaired_risk,
            "activation": activation,
            "new_row_float_value": row_float_value,
            "lp_seconds": lp_seconds,
            "verify_seconds": verify_seconds,
            "repair_seconds": repair_seconds,
        }
        iterations.append(record)
        final = {"raw_policy": raw_policy, "repaired_policy": repaired}
        if upper_best is None or upper < upper_best:
            upper_best = upper
        if robust_risk <= alpha:
            break
        if not row_float_value > float(alpha) + 1e-12:
            raise AssertionError(
                f"iteration {iteration}: new cut not violated by LP x: "
                f"{row_float_value!r} <= alpha + 1e-12 (exact robust risk {robust_risk})"
            )
        if any(new_row == row for row in rows):
            raise AssertionError(f"iteration {iteration}: cut duplicates an existing row")
        rows.append(new_row)
    else:
        raise RuntimeError(f"FCG did not terminate within {max_iters} iterations")

    last = iterations[-1]
    first = iterations[0]
    return {
        "iterations": iterations,
        "n_iterations": len(iterations),
        "n_rows": len(rows),
        "learner_variables": n,
        "builder_nodes": game.nodes,
        "build_seconds": build_seconds,
        "U0": first["U"],
        "iid_optimum_robust_risk": first["raw_robust_risk"],
        "iid_optimum_iid_risk": first["raw_iid_risk"],
        "U": last["U"],
        "L": last["L"],
        "gap": last["U"] - last["L"],
        "final_robust_risk": last["repaired_robust_risk"],
        "final_raw_robust_risk": last["raw_robust_risk"],
        "seconds": time.perf_counter() - started,
        "policy": final["repaired_policy"],
        "iid_row": iid_row,
    }
