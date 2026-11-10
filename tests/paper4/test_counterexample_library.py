"""Paper 4 counterexample library (items A-L of the WP1.3 attack list).

Every test carries an INDEPENDENT expected value: a hand-derived ``Fraction`` written in the
test, or a second computation (brute force over endpoint null strategies, an explicit
state-sequence enumeration, or a scipy sequence-form LP) that does not call the code under
test.  All arithmetic is exact unless an LP is explicitly named.

Item map
--------
A posterior aliasing                B hidden pending outcomes     C nonmonotone promotion
D monotone-class loss               E randomisation leakage       F signed continuation values
G budget saturation                 H out-of-order labels         J symbolic blow-up
K unsafe approximation              L no-promotion optimum        I weak IID lower bound (added by lead)

H is NOT expressible: the game releases every label after the same fixed delay ``d`` in query
order.  The H test documents that rule instead of faking asynchronous release.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from fractions import Fraction as F
from itertools import product

import numpy as np
import pytest
from scipy.optimize import linprog

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.paper4.counterexamples import (
    all_tapes,
    alias_example,
    behavior_policy,
    causal_risk,
    deterministic_policy,
    iid_risk,
    residual_counts,
)
from shiftlab.paper4.frontier_cuts import frontier_cut_generation
from shiftlab.paper4.frontier_cuts_fast import frontier_cut_generation_fast

ALPHA = F(1, 10)


# --------------------------------------------------------------------------------------
# Independent oracle: brute force over every endpoint null strategy
# --------------------------------------------------------------------------------------
def brute_causal_risk(horizon: int, weights: Mapping[tuple, F]) -> F:
    """``max over p in {0,1/2}^(2^T-1)`` of ``sum_tape weights[tape] * P_p(tape)``.

    A null strategy assigns ``p = q/2`` (``q`` in ``{0,1}``) to every proper prefix; it
    conditions on the whole generated prefix.  Integer arithmetic on ``q`` keeps it fast.
    """
    prefixes = [h for t in range(horizon) for h in product((0, 1), repeat=t)]
    index = {h: i for i, h in enumerate(prefixes)}
    best = F(0)
    for q in product((0, 1), repeat=len(prefixes)):
        total = F(0)
        for tape, weight in weights.items():
            numerator = 1
            for t in range(horizon):
                bit = q[index[tape[:t]]]
                numerator *= bit if tape[t] else 2 - bit
            total += weight * numerator
        best = max(best, total)
    return best / 2**horizon


def brute_event_risk(horizon: int, event) -> F:
    return brute_causal_risk(horizon, {tape: F(1) for tape in event})


def make_game(horizon, budget, delay, model=None, **kwargs):
    config = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=delay,
        alpha=kwargs.pop("alpha", ALPHA),
        query_cost=kwargs.pop("query_cost", F(1, 100)),
        switch_cost=kwargs.pop("switch_cost", F(1, 10)),
    )
    return CausalSwitchingGame(config, model or RegimeModel())


# --------------------------------------------------------------------------------------
# A. Posterior aliasing
# --------------------------------------------------------------------------------------
def test_A_posterior_aliasing_destroys_value():
    """Two histories, one alternative posterior, different causal-risk continuation.

    Contract of ``docs/switching_alt_belief_risk_alias_counterexample_v1.md``: T=5, B=2, d=1,
    c=1/100, k=1/10, alpha=1/10, promotion earns 3 rounds, so ``G = 3 - k = 29/10``.  The
    alternative is binary with ``P(S_1=0)=9/10`` and ``S_2=S_3=0``, so the tapes are 11
    (prob 9/10) and 01 (prob 1/10), both with ``P(S_3=0 | tape) = 1``.  This test reproduces the
    document's numbers without running the switching game (the game has no forced-incumbent
    window); the risk side is an independent brute force over all 2^3 endpoint nulls.
    """
    joint = alias_example()
    assert joint == {(1, 1): (F(9, 10), F(1)), (0, 1): (F(1, 10), F(1))}  # hand-derived
    assert joint[(1, 1)][1] == joint[(0, 1)][1]  # equal alternative posterior

    # Different causal-risk continuations (hand: max P(11)=1/2*1/2, max P(01)=1*1/2).
    risk_11 = brute_event_risk(2, {(1, 1)})
    risk_01 = brute_event_risk(2, {(0, 1)})
    assert (risk_11, risk_01) == (F(1, 4), F(1, 2))
    assert risk_11 != risk_01

    gross = 3 - F(1, 10)
    fee = 2 * F(1, 100)
    assert gross == F(29, 10)

    # Full-history safe policy: promote w.p. min(1, 4 alpha) = 2/5 on tape 11 only.
    activation = min(F(1), 4 * ALPHA)
    assert activation == F(2, 5)
    assert brute_causal_risk(2, {(1, 1): activation}) == ALPHA
    full_value = joint[(1, 1)][0] * activation * gross - fee
    assert full_value == F(128, 125)  # hand: 9/10 * 2/5 * 29/10 - 1/50

    # Posterior-only policy: the same promotion probability beta on both supported tapes.
    both = {(1, 1): F(1), (0, 1): F(1)}
    assert brute_causal_risk(2, both) == F(1, 2)  # risk is linear in beta, so beta/2 <= alpha
    beta = ALPHA / F(1, 2)
    assert beta == F(1, 5)
    assert brute_causal_risk(2, {t: beta for t in both}) == ALPHA
    # Granting extra off-support promotion can only raise the risk.
    assert brute_causal_risk(2, {**{t: beta for t in both}, (0, 0): F(1, 10)}) > ALPHA
    posterior_value = sum(m for m, _ in joint.values()) * beta * gross - fee
    assert posterior_value == F(14, 25)

    assert full_value - posterior_value == F(58, 125)  # the document's gap


# --------------------------------------------------------------------------------------
# B. Hidden pending outcomes
# --------------------------------------------------------------------------------------
def _walk_promotion(game, chooser, null_p, restricted):
    """Promotion probability of a deterministic policy against a null strategy ``null_p``.

    ``null_p[key]`` is the null's ``P(Y=1)`` at a query.  ``key = (history incl. the query,
    information)``; the information is the whole generated outcome list for the full null and
    only the outcomes released to the learner for the restricted null.  Returns the promotion
    probability, filling ``null_p`` with keys if it is a ``set`` collector.
    """
    horizon = game.config.horizon

    def visit(history, outcomes, weight):
        time = len(history) + 1
        if time > horizon:
            return F(0)
        released = game.information(history, outcomes)[1]
        action, query = chooser(history, released)
        if action:
            return weight
        following = history + ((action, query),)
        if not query:
            return visit(following, outcomes, weight)
        key = (following, released if restricted else outcomes)
        if isinstance(null_p, set):
            null_p.add(key)
            probability = F(1, 2)
        else:
            probability = null_p[key]
        return sum(
            visit(
                following, outcomes + ((time, y),), weight * (probability if y else 1 - probability)
            )
            for y in (0, 1)
        )

    return visit((), (), F(1))


def _bruteforce_null(game, chooser, restricted):
    keys: set = set()
    _walk_promotion(game, chooser, keys, restricted)
    ordered = sorted(keys, key=repr)
    best = F(0)
    for values in product((F(0), F(1, 2)), repeat=len(ordered)):
        best = max(best, _walk_promotion(game, chooser, dict(zip(ordered, values)), restricted))
    return best


def test_B_pending_outcome_conditioning_raises_risk():
    """Null conditioning on a pending label vs a null restricted to released information.

    In the tiny game T=3, d=2 a pending label can never matter: the only label the learner has
    seen at its last decision is Y1, and Y2 (released after the horizon) cannot influence
    promotion, so the null's conditioning of ``p_2`` on ``Y1`` is irrelevant.  We verify this over
    all 512 deterministic policies that query/hold and promote at most at round 3.  A policy for
    which the conditioning matters needs two labels released before the decision with the second
    queried while the first is still pending: T=4, d=2, B=2, queries at rounds 1 and 2, promote
    at round 4 iff ``Y1 xor Y2 = 1``.  Hand derivation: the full null chooses ``p_1 = 1/2``,
    ``p_2(0)=1/2``, ``p_2(1)=0`` giving ``P(01)+P(10) = 1/4 + 1/2 = 3/4``.  Restricted to
    released information ``p_2`` cannot depend on ``Y_1`` and every choice gives at most 1/2.
    """
    # ---- the tiny game T=3, d=2, B=2: no policy distinguishes the two nulls ----------
    tiny = make_game(3, 2, 2)
    r2_histories = [((0, 0),), ((0, 1),)]
    r3_infos = [
        (((0, 0), (0, 0)), ()),
        (((0, 0), (0, 1)), ()),
        (((0, 1), (0, 0)), ((1, 0),)),
        (((0, 1), (0, 0)), ((1, 1),)),
        (((0, 1), (0, 1)), ((1, 0),)),
        (((0, 1), (0, 1)), ((1, 1),)),
    ]
    count = positive = 0
    for q1, q2a, q2b, *promote in product((0, 1), (0, 1), (0, 1), *([(0, 1)] * len(r3_infos))):
        q2 = {r2_histories[0]: q2a, r2_histories[1]: q2b}
        table = dict(zip(r3_infos, promote, strict=True))

        def chooser(history, released, q1=q1, q2=q2, table=table):
            if len(history) == 0:
                return (0, q1)
            if len(history) == 1:
                return (0, q2[history])
            return (table[history, released], 0)

        policy = deterministic_policy(tiny, chooser)
        code_risk = tiny.null_risk(policy)
        full = _bruteforce_null(tiny, chooser, restricted=False)
        restricted = _bruteforce_null(tiny, chooser, restricted=True)
        assert code_risk == full == restricted
        count += 1
        positive += code_risk > 0
    assert count == 512
    assert positive > 0  # not a vacuous sweep

    # ---- T=4, d=2, B=2: the pending Y1 matters for the null's p_2 ----------------------
    game = make_game(4, 2, 2)

    def xor_chooser(history, released):
        if len(history) < 2:
            return (0, 1)
        if len(history) == 2:
            return (0, 0)
        if len(history) == 3 and history == ((0, 1), (0, 1), (0, 0)):
            y = dict(released)
            return (int(y[1] != y[2]), 0)
        return (0, 0)

    policy = deterministic_policy(game, xor_chooser)
    assert game.null_risk(policy) == F(3, 4)  # null sees pending outcomes (hand: 1/4 + 1/2)
    assert _bruteforce_null(game, xor_chooser, restricted=False) == F(3, 4)
    restricted = _bruteforce_null(game, xor_chooser, restricted=True)
    assert restricted == F(1, 2)  # hand derivation in the docstring
    assert game.null_risk(policy) > restricted
    assert game.null_risk(policy, iid_boundary=True) == F(1, 2)  # fair coin


# --------------------------------------------------------------------------------------
# C. Nonmonotone promotion event
# --------------------------------------------------------------------------------------
def test_C_nonmonotone_promotion_event_iid_vs_causal():
    """Event ``{010, 101}``: IID 1/4, causal 1/2 (hand: p1=0, p2(0)=1/2, p3(01)=0 gives 010 w.p. 1/2).

    The brute force over all 2^7 endpoint strategies is independent of ``causal_risk``; the game
    cross-check queries three labels (T=4, B=3, d=1) and promotes at round 4 on the event.
    """
    event = {(0, 1, 0), (1, 0, 1)}
    assert brute_event_risk(3, event) == F(1, 2)
    assert F(len(event), 8) == F(1, 4)
    assert causal_risk(3, event) == F(1, 2)
    assert iid_risk(3, event) == F(1, 4)

    game = make_game(4, 3, 1)

    def chooser(history, released):
        if len(history) < 3:
            return (0, 1)
        if history == ((0, 1), (0, 1), (0, 1)):
            y = dict(released)
            return (int((y[1], y[2], y[3]) in event), 0)
        return (0, 0)

    policy = deterministic_policy(game, chooser)
    assert game.null_risk(policy) == F(1, 2)
    assert game.null_risk(policy, iid_boundary=True) == F(1, 4)


# --------------------------------------------------------------------------------------
# D. Loss from restricting to monotone promotion events
# --------------------------------------------------------------------------------------
def _d_model():
    tapes = all_tapes(2)
    alt = {(0, 1): F(1, 2), (1, 1): F(1, 2)}
    payoff = {(0, 1): F(1), (1, 1): F(-2)}
    switch = F(1, 20)

    def net(event):
        return sum(alt.get(t, F(0)) * (payoff.get(t, F(0)) - switch) for t in event)

    return tapes, net


def test_D_monotone_restriction_loses_all_safe_value():
    """Best monotone value 0; the unrestricted safe mixture earns at least 19/200.

    Reproduces ``docs/switching_monotone_class_separation_v1.md`` (k=1/20, alpha=1/10) by exhaustive
    enumeration of the 16 Boolean events and an LP over randomised maps.  Hand: ``net({01}) =
    (1/2)(1 - 1/20) = 19/40``; its causal risk is 1/2, so activation ``(1/10)/(1/2) = 1/5`` gives
    ``19/200``.
    """
    tapes, net = _d_model()
    events = [
        frozenset(t for t, bit in zip(tapes, bits, strict=True) if bit)
        for bits in product((0, 1), repeat=len(tapes))
    ]
    assert len(events) == 16

    def increasing(event):
        return all(
            y in event
            for x in event
            for y in tapes
            if all(a <= b for a, b in zip(x, y, strict=True))
        )

    monotone = [e for e in events if increasing(e)]
    assert len(monotone) == 6
    assert max(net(e) for e in monotone) == 0
    assert [e for e in monotone if net(e) == 0] == [frozenset()]

    assert net({(0, 1)}) == F(19, 40)
    risk = brute_event_risk(2, {(0, 1)})
    assert risk == F(1, 2)
    activation = ALPHA / risk
    assert activation == F(1, 5)
    safe_value = activation * net({(0, 1)})
    assert safe_value == F(19, 200)
    assert safe_value > 0

    # Randomised maps q(tape) in [0,1]: LP over all 8 endpoint nulls, with/without monotonicity.
    index = {t: i for i, t in enumerate(tapes)}
    risk_rows = []
    for p1, p2a, p2b in product((F(0), F(1, 2)), repeat=3):
        row = [F(0)] * 4
        for y1, y2 in tapes:
            probability = (p1 if y1 else 1 - p1) * (
                (p2b if y1 else p2a) if y2 else 1 - (p2b if y1 else p2a)
            )
            row[index[y1, y2]] = probability
        risk_rows.append([float(v) for v in row])
    objective = -np.array(
        [float(net({t}) if t in ((0, 1), (1, 1)) else 0) for t in tapes], dtype=float
    )
    base = dict(
        A_ub=np.array(risk_rows),
        b_ub=np.full(8, float(ALPHA)),
        bounds=[(0, 1)] * 4,
        method="highs",
    )
    unrestricted = linprog(objective, **base)
    assert unrestricted.success and -unrestricted.fun >= float(F(19, 200)) - 1e-9
    # monotone: q(00) <= q(01) <= q(11), q(00) <= q(10) <= q(11)
    rows = []
    for lo, hi in (((0, 0), (0, 1)), ((0, 1), (1, 1)), ((0, 0), (1, 0)), ((1, 0), (1, 1))):
        row = np.zeros(4)
        row[index[lo]], row[index[hi]] = 1.0, -1.0
        rows.append(row)
    restricted = linprog(
        objective,
        A_ub=np.vstack([np.array(risk_rows), np.array(rows)]),
        b_ub=np.r_[np.full(8, float(ALPHA)), np.zeros(4)],
        bounds=[(0, 1)] * 4,
        method="highs",
    )
    assert restricted.success and abs(restricted.fun) < 1e-9  # best monotone value is zero
    assert abs(-unrestricted.fun - float(F(19, 200))) < 1e-9


# --------------------------------------------------------------------------------------
# E. Randomisation leakage
# --------------------------------------------------------------------------------------
def test_E_randomisation_leakage_true_risk_exceeds_marginal_certificate():
    """Fair private coin U, public query pattern: true robust risk 3/4, marginal certificate 1/2.

    U=0: query events 1 and 2, promote iff Y2=0.  U=1: query only event 2, promote iff Y2=1.
    The null sees the query pattern (hence U) and answers each branch separately.  Hand: branch 0
    is beaten by ``p_2 = 0`` (risk 1); branch 1 by ``p_2 = 1/2`` (risk 1/2); average 3/4.  The
    marginal promotion map is the constant 1/2, whose causal risk is 1/2.  The null's best
    response is solved independently as a sequence-form LP over its information sets (perfect
    recall: each set remembers the null's own earlier move).
    """
    game = make_game(3, 2, 1)

    def chooser(history, released):
        if len(history) == 0:
            return {(0, 1): F(1, 2), (0, 0): F(1, 2)}  # U = 0 queries event 1; U = 1 does not
        if len(history) == 1:
            return {(0, 1): F(1)}
        y = dict(released)
        if history == ((0, 1), (0, 1)):
            return {((1 if y[2] == 0 else 0), 0): F(1)}
        if history == ((0, 0), (0, 1)):
            return {((1 if y[2] == 1 else 0), 0): F(1)}
        return {(0, 0): F(1)}

    policy = behavior_policy(game, chooser)
    assert game.null_risk(policy) == F(3, 4)
    assert game.null_risk(policy, iid_boundary=True) == F(1, 2)

    # Sequence-form LP for the null's best response (independent of the game code).
    # Null information sets: I1 (branch 0, event 1 queried), I2(a1, y1) in branch 0, J2 in branch 1.
    actions = (F(0), F(1, 2))  # the null's P(Y = 1)
    var = {}
    for a1 in range(2):
        var["I1", a1] = len(var)
    for a1, y1, a2 in product(range(2), (0, 1), range(2)):
        var["I2", a1, y1, a2] = len(var)
    for a2 in range(2):
        var["J2", a2] = len(var)

    def prob(action, y):
        return actions[action] if y else 1 - actions[action]

    objective = np.zeros(len(var))
    for a1, y1, a2 in product(range(2), (0, 1), range(2)):
        # branch 0 promotes iff Y2 = 0
        objective[var["I2", a1, y1, a2]] += float(F(1, 2) * prob(a1, y1) * prob(a2, 0))
    for a2 in range(2):
        # branch 1 promotes iff Y2 = 1
        objective[var["J2", a2]] += float(F(1, 2) * prob(a2, 1))
    equalities, rhs = [], []
    row = np.zeros(len(var))
    for a1 in range(2):
        row[var["I1", a1]] = 1
    equalities.append(row), rhs.append(1.0)
    for a1, y1 in product(range(2), (0, 1)):
        row = np.zeros(len(var))
        row[var["I1", a1]] = -1
        for a2 in range(2):
            row[var["I2", a1, y1, a2]] = 1
        equalities.append(row), rhs.append(0.0)
    row = np.zeros(len(var))
    for a2 in range(2):
        row[var["J2", a2]] = 1
    equalities.append(row), rhs.append(1.0)
    result = linprog(
        -objective,
        A_eq=np.array(equalities),
        b_eq=np.array(rhs),
        bounds=[(0, None)] * len(var),
        method="highs",
    )
    assert result.success
    assert F(-result.fun).limit_denominator(1000) == F(3, 4)
    assert abs(-result.fun - 0.75) < 1e-9

    # Marginal promotion map: average of the two branches' maps on the (Y1, Y2) tape.
    marginal = {tape: F(1, 2) * (tape[1] == 0) + F(1, 2) * (tape[1] == 1) for tape in all_tapes(2)}
    assert set(marginal.values()) == {F(1, 2)}
    certificate = brute_causal_risk(2, marginal)
    assert certificate == F(1, 2)
    assert certificate < F(3, 4)


# --------------------------------------------------------------------------------------
# F. Signed continuation values (expressible: the game's promotion value is signed)
# --------------------------------------------------------------------------------------
def test_F_signed_nonmonotone_continuation_values_in_the_game():
    """In the real game the net value of promoting is signed and not monotone in the labels.

    Anti-persistent regime (flip prob 9/10, emissions 1/10 and 9/10, prior 1/2), T=4, B=2, d=1:
    query rounds 1 and 2, decide at round 3.  The per-tape advantage ``stay - promote`` of rounds
    3-4 (``promote`` includes the switch cost) is recovered from the game by differencing the
    expected total cost of "promote iff tape == y" against never promoting, then compared with an
    explicit enumeration of the hidden-state sequences ``S_1..S_4`` (second computation).
    """
    flip, e0, e1, k = F(9, 10), F(1, 10), F(9, 10), F(1, 10)
    model = RegimeModel(flip, flip, e0, e1, F(1, 2))
    game = make_game(4, 2, 1, model, switch_cost=k)
    emission = (e0, e1)

    def total_cost(promote_on):
        def chooser(history, released):
            if len(history) < 2:
                return (0, 1)
            if len(history) == 2:
                y = dict(released)
                return (int((y[1], y[2]) in promote_on), 0)
            return (history[-1][0], 0)  # hold whatever action was taken at round 3

        metrics = game.expected_metrics(deterministic_policy(game, chooser))
        return sum(metrics[:3])

    never = total_cost(set())

    # Independent enumeration over (S_1..S_4); S_1 ~ stationary (1/2, 1/2).
    enumerated, mass = {}, {}
    for y in product((0, 1), repeat=2):
        total = stay = promote = F(0)
        for s in product((0, 1), repeat=4):
            w = F(1, 2)
            for a, b in zip(s, s[1:], strict=False):
                w *= flip if a != b else 1 - flip
            for t in (0, 1):
                w *= emission[s[t]] if y[t] else 1 - emission[s[t]]
            total += w
            stay += w * sum(emission[s[t]] for t in (2, 3))
            promote += w * sum(1 - emission[s[t]] for t in (2, 3))
        mass[y] = total
        enumerated[y] = stay / total - (promote / total + k)
    assert sum(mass.values()) == 1
    assert enumerated == {
        (0, 0): F(-177, 3050),
        (0, 1): F(-233, 1050),
        (1, 0): F(23, 1050),
        (1, 1): F(-433, 3050),
    }

    from_game = {}
    for y in product((0, 1), repeat=2):
        delta = total_cost({y}) - never  # = P(y) * (promote - stay)
        from_game[y] = -delta / mass[y]
    assert from_game == enumerated

    # Signed: exactly one tape has positive promotion value, and it is not an up-set.
    beneficial = {y for y, v in enumerated.items() if v > 0}
    assert beneficial == {(1, 0)}
    assert (1, 1) > (1, 0) and (1, 1) not in beneficial  # coordinatewise successor is harmful

    # Every increasing event containing (1,0) contains (1,1): its gross value is negative.
    gain = {y: mass[y] * v for y, v in enumerated.items()}
    assert gain[(1, 0)] > 0
    assert gain[(1, 0)] + gain[(1, 1)] < 0
    assert gain[(1, 0)] + gain[(1, 1)] + gain[(0, 1)] < 0
    assert max(0, gain[(1, 0)]) == gain[(1, 0)]  # the nonmonotone event {10} strictly profits


# --------------------------------------------------------------------------------------
# G. Budget saturation
# --------------------------------------------------------------------------------------
def test_G_no_query_action_at_zero_budget():
    game = make_game(4, 1, 1)
    full = ((0, 0), (0, 1), (1, 0), (1, 1))
    assert game.choices(()) == full
    assert game.choices(((0, 0),)) == full  # nothing spent yet
    spent = ((0, 1),)
    assert game.choices(spent) == ((0, 0), (1, 0))  # hand-derived: no query action at budget 0
    assert game.choices(spent + ((0, 0),)) == ((0, 0), (1, 0))
    assert game.choices(spent + ((1, 0),)) == ((0, 0), (1, 0))
    with pytest.raises(AssertionError):  # a history over budget is not even a game state
        game.choices(((0, 1), (0, 1)))
    with pytest.raises(ValueError):
        GameConfig(horizon=4, budget=5)  # budget cannot exceed the horizon

    # Every learner information set of the built tree respects the hard budget.
    game.build()
    assert game.learner.infos
    for (history, _released), (_parent, _children, choices) in game.learner.infos.items():
        used = sum(q for _, q in history)
        assert used <= 1
        assert all(used + query <= 1 for _action, query in choices)
        if used == 1:
            assert all(query == 0 for _action, query in choices)

    # A policy that tries to query at budget 0 cannot be expressed.
    with pytest.raises(ValueError):
        behavior_policy(game, lambda h, r: {(0, 1): F(1)})(spent, ())
    with pytest.raises(ValueError):
        deterministic_policy(game, lambda h, r: (1, 1) if h == spent else (0, 0))(spent, ())

    def raw(history, outcomes):
        """Query at round 1, then a 4-vector with mass on query (0,1) at the exhausted node."""
        if history == ():
            return (F(0), F(1), F(0), F(0))
        if history == spent:
            return (F(0), F(1), F(0), F(0))  # 4 entries but only 2 legal choices
        return tuple(F(i == 0) for i in range(len(game.choices(history))))

    with pytest.raises(ValueError):
        game.null_risk(raw)
    with pytest.raises(ValueError):
        game.expected_metrics(raw)


# --------------------------------------------------------------------------------------
# H. Out-of-order labels (NOT expressible; documents the fixed-delay release rule)
# --------------------------------------------------------------------------------------
def test_H_fixed_delay_release_rule_documented():
    """The game cannot express out-of-order or stochastic label release; this documents why.

    ``information`` releases the label requested at ``s`` exactly at round ``s + d`` for one
    global integer ``d``.  Releases are therefore FIFO (never reordered, never dropped, never
    delayed by different amounts).  Asynchronous or out-of-order feedback would need a different
    model, so no counterexample is claimed here.
    """
    game = make_game(6, 3, 2)
    outcomes = ((1, 1), (2, 0), (3, 1))
    for time, expected in {
        1: (),
        2: (),
        3: ((1, 1),),
        4: ((1, 1), (2, 0)),
        5: ((1, 1), (2, 0), (3, 1)),
        6: ((1, 1), (2, 0), (3, 1)),
    }.items():  # hand-derived: label s is visible iff s + 2 <= time
        history = tuple((0, 0) for _ in range(time - 1))
        assert game.information(history, outcomes) == (history, expected)

    # FIFO closure for every subset of query times and every round.
    for mask in product((0, 1), repeat=5):
        queried = [s for s, bit in zip(range(1, 6), mask, strict=True) if bit]
        outs = tuple((s, s % 2) for s in queried)
        for time in range(1, 7):
            released = game.information(tuple((0, 0) for _ in range(time - 1)), outs)[1]
            assert released == tuple(o for o in outs if o[0] + 2 <= time)
            assert list(released) == sorted(released)  # query order is preserved
    # Only a single deterministic integer delay exists in the config; no stochastic-delay field.
    assert {f.name for f in dataclasses.fields(GameConfig)} == {
        "horizon",
        "budget",
        "delay",
        "alpha",
        "query_cost",
        "switch_cost",
        "max_nodes",
    }
    for bad in (0, -1, 1.5):
        with pytest.raises(ValueError):
            GameConfig(horizon=4, budget=1, delay=bad)


# --------------------------------------------------------------------------------------
# J. Symbolic blow-up
# --------------------------------------------------------------------------------------
def test_J_parity_causal_risk_exact_and_order_sensitive_residuals():
    """Parity has width 2 per level yet causal risk ``1 - 2^-T``; AND-OR width depends on order.

    Hand derivation for parity (promote iff the number of 1s is odd): at depth T-1, ``v(h)=1``
    if ``h`` has odd parity and 1/2 otherwise; going up, an even-parity prefix gets
    ``max(v_even', (v_even' + 1)/2)`` with ``v_even' -> 1 - 2^-j``, so the root is ``1 - 2^-T`` against IID 1/2.
    """
    for horizon in (1, 2, 3, 4):
        parity = {t for t in all_tapes(horizon) if sum(t) % 2 == 1}
        expected = 1 - F(1, 2**horizon)  # hand-derived
        assert causal_risk(horizon, parity) == expected
        assert brute_event_risk(horizon, parity) == expected
        assert iid_risk(horizon, parity) == F(1, 2)
        widths = residual_counts(lambda t: sum(t) % 2 == 1, horizon, list(range(horizon)))
        assert max(widths) <= 2  # reduced-OBDD width 2 at every level

    # f = x1x2 or x3x4 or ... ; natural order vs interleaved (odd variables first).
    def f(tape):
        return any(tape[i] and tape[i + 1] for i in range(0, len(tape), 2))

    interleaved_widths = {}
    for horizon in (4, 6, 8):
        natural = residual_counts(f, horizon, list(range(horizon)))
        interleaved = residual_counts(
            f, horizon, list(range(0, horizon, 2)) + list(range(1, horizon, 2))
        )
        assert max(natural) <= 3  # linear size: constant width
        assert max(interleaved) == 2 ** (horizon // 2)  # hand: one class per subset of pairs
        interleaved_widths[horizon] = max(interleaved)
    assert interleaved_widths == {4: 4, 6: 8, 8: 16}
    assert max(residual_counts(f, 8, list(range(8)))) == 3  # hand: {done, mid-pair x=1, rest}

    # The risk of f is exact whatever the variable order (T=4 brute force).
    event = {t for t in all_tapes(4) if f(t)}
    assert causal_risk(4, event) == brute_event_risk(4, event)


# --------------------------------------------------------------------------------------
# K. Unsafe approximation (pruning by alternative probability)
# --------------------------------------------------------------------------------------
def test_K_dropping_alternative_rare_history_is_unsafe():
    """Ignoring a history with tiny alternative mass hides a causal-null risk of 1/2.

    Construction: alternative regime absorbing in state 0 with ``P(Y=1) = 1/200``; query round 1
    and promote at round 2 iff ``Y1 = 1``.  The alternative reaches the promoting history with
    probability 1/200, so an approximation that prunes histories of alternative mass below 1/100
    drops it (never-promote there).  The null can set ``p_1 = 1/2`` and promote with probability
    1/2.  The pruned policy has risk 0 <= alpha = 1/10 (it would be certified) while the policy
    that actually promotes has risk 1/2 > alpha.  Alternative cost changes by only
    ``(1/200)(2*(199/200 - 1/200) + 1/10) = 13/1250``.
    """
    model = RegimeModel(F(0), F(0), F(1, 200), F(199, 200), F(0))
    game = make_game(3, 1, 1, model)

    def chooser_with(drop):
        def chooser(history, released):
            if len(history) == 0:
                return (0, 1)
            if len(history) == 1:
                return (int(dict(released)[1] == 1 and not drop), 0)
            return (history[-1][0], 0)

        return chooser

    keep = deterministic_policy(game, chooser_with(drop=False))
    drop = deterministic_policy(game, chooser_with(drop=True))

    alt_mass = F(1, 200)  # hand: P(Y_1 = 1) under the absorbing state-0 alternative
    assert game.expected_metrics(keep)[4] == alt_mass  # one switch exactly on the promoting tape
    assert game.expected_metrics(drop)[4] == 0
    assert alt_mass < F(1, 100)

    assert game.null_risk(keep) == F(1, 2)
    assert game.null_risk(drop) == 0
    assert game.null_risk(keep) - game.null_risk(drop) >= F(1, 10)
    assert game.null_risk(drop) <= ALPHA < game.null_risk(keep)  # pruned certificate is false

    delta = sum(game.expected_metrics(keep)[:3]) - sum(game.expected_metrics(drop)[:3])
    assert delta == F(13, 1250)


# --------------------------------------------------------------------------------------
# L. Never-promote optimum
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("label", "model", "switch", "expected"),
    [
        # Absorbing state 0 with P(Y=1) = 1/20: incumbent costs 1/20 per round, challenger 19/20.
        ("strong_incumbent", RegimeModel(F(0), F(0), F(1, 20), F(19, 20), F(0)), F(1, 10), F(1, 4)),
        # Fair-mixing anti-persistent regime but switch cost 10 > the largest possible saving 5.
        (
            "large_switch_cost",
            RegimeModel(F(9, 10), F(9, 10), F(1, 10), F(9, 10), F(1, 2)),
            F(10),
            F(5, 2),
        ),
    ],
)
def test_L_never_promote_is_optimal_and_fcg_returns_it(label, model, switch, expected):
    """Never-promote cost is ``T * E[P(Y=1)]``: hand 5/20 = 1/4 and 5 * 1/2 = 5/2.

    FCG (exact loop), FCG-fast and the reference all return it with zero promotion and zero
    queries.  A fresh game evaluates the FCG policy.
    """
    game = make_game(5, 2, 1, model, switch_cost=switch)
    config = game.config
    reference_report, _policy, _records = FirstPromotionDecomposedGame(config, model).solve()
    assert F(reference_report["calibrated_total_cost"]) == expected

    v1 = frontier_cut_generation(config, model)
    assert v1["U"] == expected
    assert v1["n_rows"] == 1 and v1["final_robust_risk"] == 0
    metrics = game.expected_metrics(v1["policy"])
    assert metrics[4] == 0  # expected switches: never promotes
    assert metrics[3] == 0  # expected queries: never queries
    assert game.null_risk(v1["policy"]) == 0

    fast = frontier_cut_generation_fast(config, model)
    assert fast["U"] == expected
    assert fast["n_rows"] == 1 and fast["final_robust_risk"] == 0
    assert fast["final_raw_robust_risk"] == 0
    assert float(fast["gap"]) <= 1e-9


def test_I_iid_relaxation_lower_bound_is_loose_on_reversal_cell():
    """I: weak lower bound. On anti-persistent cell C2 the IID-relaxed LP bound L0 sits well below the
    unrestricted optimum, so IID relaxation + repair alone cannot certify near-optimality; FCG's cuts close it.

    Independent oracle: V_ref from the exact decomposed sequence-form reference solve (full null tree),
    which does not use the FCG code. Expected values from docs/paper4/experiments/results/fcg_dev_v1.json:
    L0 ~= 2.4002176, V* = 76309/31250 = 2.441888, IID+repair U0 = 765659/312500.
    """
    from shiftlab.paper4.frontier_cuts import frontier_cut_generation

    config = GameConfig(
        horizon=5, budget=2, delay=1, alpha=F(1, 10), query_cost=F(1, 100), switch_cost=F(1, 10)
    )
    model = RegimeModel(
        transition01=F(9, 10),
        transition10=F(9, 10),
        emission0=F(1, 10),
        emission1=F(9, 10),
        prior1=F(1, 2),
    )
    v_ref = F(FirstPromotionDecomposedGame(config, model).solve()[0]["calibrated_total_cost"])
    assert v_ref == F(76309, 31250)
    out = frontier_cut_generation(config, model)
    lower_iid = F(out["iterations"][0]["L"])
    upper_iid_repair = F(out["U0"])
    assert upper_iid_repair == F(765659, 312500)
    assert v_ref - lower_iid > F(4, 100)  # IID bound is loose by > 0.04
    assert upper_iid_repair - lower_iid > F(49, 1000)  # IID-only certificate gap > 2% of cost
    assert abs(F(out["U"]) - v_ref) <= F(1, 10**6)  # cuts close the gap to the reference optimum
