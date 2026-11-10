"""Root-lottery mixing: regression for the stochastic-plan defect (RESEARCH_LEDGER CP5)."""

from __future__ import annotations

from fractions import Fraction as F

import numpy as np
import pytest
from scipy.optimize import linprog

from shiftlab.dive.eprocess_gated_planner import mix_with_never_promote
from shiftlab.dive.root_mixture import mix_root_lottery
from shiftlab.paper4.frontier_cuts import (
    best_response_null,
    exact_costs,
    learner_only_game,
    mix_root_never_promote,
    risk_row_for_null,
)
from shiftlab.paper4.iid_tightness import make_cell

ALPHA = F(1, 10)


def fcg_policy(name, iteration=0):
    """Raw LP policy of FCG iteration ``iteration`` (0 = IID-relaxed optimum, one risk row)."""
    config, model = make_cell(name)
    game = learner_only_game(config, model)
    costs = np.array([float(c) for c in exact_costs(game)])
    flow, rhs = game.learner.matrix()
    rows = [risk_row_for_null(game, {})]
    for step in range(iteration + 1):
        result = linprog(
            costs,
            A_ub=np.array([[float(v) for v in row] for row in rows]),
            b_ub=np.full(len(rows), float(config.alpha)),
            A_eq=flow,
            b_eq=rhs,
            bounds=[(0, None)] * game.learner.count,
            method="highs",
            options={"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9},
        )
        assert result.success
        raw, _ = game.recover(result.x)
        if step < iteration:
            risk, strategy = best_response_null(game, raw)
            assert risk > config.alpha
            rows.append(risk_row_for_null(game, strategy))
    return game, raw


def iid_lp_policy(name):
    return fcg_policy(name, 0)


def never(game):
    return lambda h, o: tuple(F(c == (0, 0)) for c in game.choices(h))


def cost(game, policy):
    return sum(game.expected_metrics(policy)[:3])


def reachable(game, policy):
    """All learner information sets reachable under positive-probability play."""
    out, stack = {}, [((), ())]
    while stack:
        h, o = stack.pop()
        info = game.information(h, o)
        if info in out or len(h) + 1 > game.config.horizon:
            continue
        out[info] = (h, o)
        for (a, qy), m in zip(game.choices(h), policy(h, o), strict=True):
            if not m:
                continue
            t = len(h) + 1
            if qy:
                stack += [(h + ((a, qy),), o + ((t, y),)) for y in (0, 1)]
            else:
                stack.append((h + ((a, qy),), o))
    return list(out.values())


@pytest.fixture(scope="module", params=[0, 6], ids=["iid_iter0", "cut_iter6"])
def c2(request):
    game, raw = fcg_policy("C2", request.param)
    robust = game.null_risk(raw)
    return game, raw, robust, ALPHA / robust, request.param


def test_regression_stochastic_c2(c2):
    game, raw, robust, q, iteration = c2
    assert robust > ALPHA and 0 < q < 1
    old = mix_with_never_promote(game, raw, q, _allow_stochastic=True)
    if iteration == 6:
        # The observed defect (ledger CP5 value): robust risk 13/100, q = 10/13.
        assert (robust, q) == (F(13, 100), F(10, 13))
        assert game.null_risk(old) == F(280952, 2779205)
        assert game.null_risk(old) > ALPHA
    with pytest.raises(ValueError, match="mix_root_lottery"):
        mix_with_never_promote(game, raw, q)

    new = mix_root_lottery(game, raw, q)
    assert game.null_risk(new) == q * robust == ALPHA
    c_new = cost(game, new)
    assert c_new == q * cost(game, raw) + (1 - q) * cost(game, never(game))


def test_deterministic_old_and_new_identical():
    game, raw = iid_lp_policy("C2")
    # Deterministic plan: always continue with one query at time 1, then promote if label seen 1.

    def det(history, outcomes):
        choices = game.choices(history)
        if not history:
            pick = (0, 1)
        elif history[-1] == (0, 1) and any(y for _, y in outcomes):
            pick = (1, 0)
        else:
            pick = (0, 0)
        if pick not in choices:
            pick = (history[-1][0] if history else 0, 0)
        return tuple(F(c == pick) for c in choices)

    for q in (F(1, 3), F(1, 2), F(7, 10)):
        old = mix_with_never_promote(game, det, q)  # guard must not fire
        new = mix_root_lottery(game, det, q)
        for h, o in reachable(game, new):
            assert old(h, o) == new(h, o)
        assert game.null_risk(old) == game.null_risk(new)
        assert game.expected_metrics(old) == game.expected_metrics(new)


def test_budget_never_offers_query_when_exhausted(c2):
    game, raw, _, q, _ = c2
    mixed = mix_root_lottery(game, raw, q)
    seen = 0
    for h, o in reachable(game, mixed):
        probabilities = mixed(h, o)
        assert len(probabilities) == len(game.choices(h))
        assert sum(probabilities) == 1
        if sum(qy for _, qy in h) == game.config.budget:
            seen += 1
            assert all(qy == 0 for (_, qy), _p in zip(game.choices(h), probabilities, strict=True))
    assert seen


def test_unreachable_information_falls_back_to_raw(c2):
    game, raw, _, q, _ = c2

    # q=1/2 on a policy that never plays (0,1) at the root; state after (0,1) is reached by
    # neither the raw plan nor the safe plan.
    def no_query(h, o):
        return tuple(F(c == (0, 0)) for c in game.choices(h))

    def raw_alt(h, o):
        return tuple(F(c == (1, 0)) for c in game.choices(h))

    mixed = mix_root_lottery(game, raw_alt, F(1, 2))
    h = ((0, 1),)
    o = ((1, 1),)
    assert mixed(h, o) == raw_alt(h, o)
    assert mixed((), ()) == tuple(
        F(1, 2) if c in ((1, 0), (0, 0)) else F(0) for c in game.choices(())
    )
    # q in {0, 1}
    assert mix_root_lottery(game, raw, F(1)) is raw
    zero = mix_root_lottery(game, raw, F(0))
    assert zero((), ()) == no_query((), ())
    with pytest.raises(ValueError):
        mix_root_lottery(game, raw, F(3, 2))


@pytest.mark.parametrize(("cell", "iteration"), [("C2", 0), ("C3", 0), ("C2", 6), ("C3", 7)])
def test_agrees_with_frontier_cuts_realization_mixing(cell, iteration):
    game, raw = fcg_policy(cell, iteration)
    robust = game.null_risk(raw)
    q = min(F(1), ALPHA / robust)
    assert q < 1
    ours = mix_root_lottery(game, raw, q)
    theirs, _safe = mix_root_never_promote(game, raw, q)
    assert cost(game, ours) == cost(game, theirs)
    assert game.null_risk(ours) == game.null_risk(theirs) <= ALPHA
    for h, o in reachable(game, theirs):
        assert ours(h, o) == theirs(h, o)
