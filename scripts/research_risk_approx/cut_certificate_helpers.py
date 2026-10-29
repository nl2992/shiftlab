"""Exact arithmetic helpers for first-promotion restricted-master certificates."""

from __future__ import annotations

from fractions import Fraction as F

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame


def game_for(horizon):
    config = GameConfig(horizon=horizon, budget=3, delay=1, alpha=F(1, 10))
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    game = FirstPromotionDecomposedGame(config, model)
    game.build()
    return game


def exact_costs(game):
    costs = [F(0)] * game.learner.count

    def visit(history, outcomes, sequence, weight, posterior, total):
        time = len(history) + 1
        if time > game.config.horizon:
            costs[sequence] += weight * total
            return
        state1 = game.model.propagate(posterior, 1)
        positive = game.model.emission(state1)
        _, children, choices = game.learner.infos[game.information(history, outcomes)]
        for (action, query), child in zip(choices, children, strict=True):
            if action:
                belief = game._belief_from_history(history, outcomes)
                remaining = game.config.budget - sum(q for _, q in history)
                continuation = game._promote_value(time, remaining, belief, query)
                costs[child] += weight * (total + continuation)
                continue
            stage = positive + game.config.query_cost * query
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
                        total + stage,
                    )
            else:
                visit(following, outcomes, child, weight, state1, total + stage)

    visit((), (), 0, F(1), game.model.prior1, F(0))
    return costs


def exact_payoff(game):
    payoff = {}
    for key, value in game.risk.items():
        exact = F(float(value))
        if exact.denominator > 2**game.config.budget:
            raise ValueError("Null payoff is not an expected dyadic coefficient")
        payoff[key] = exact
    return payoff


def null_cut(game, payoff, selected):
    n_y = game.opponent.count
    if any(type(i) is not int or not 0 <= i < n_y for i in selected):
        raise ValueError("Invalid null sequence")
    if len(set(selected)) != len(selected):
        raise ValueError("Repeated null sequence")
    y = [int(i in set(selected)) for i in range(n_y)]
    matrix, rhs = game.opponent.matrix()
    if any(int(v) != int(w) for v, w in zip(matrix @ y, rhs, strict=True)):
        raise ValueError("Null sequence flow is invalid")
    result = [F(0)] * game.learner.count
    for (i, j), value in payoff.items():
        if y[j]:
            result[i] += value
    return result


def lower_bound(game, costs, cuts, dual_eq, dual_ub):
    matrix, rhs = game.learner.matrix()
    if len(dual_eq) != len(rhs) or len(dual_ub) != len(cuts):
        raise ValueError("Dual dimensions do not match")
    if any(mu > 0 for mu in dual_ub):
        raise ValueError("Dual inequality multiplier has wrong sign")
    lhs = [F(0)] * game.learner.count
    coo = matrix.tocoo()
    for row, col, value in zip(coo.row, coo.col, coo.data, strict=True):
        lhs[int(col)] += F(int(value)) * dual_eq[int(row)]
    for cut, multiplier in zip(cuts, dual_ub, strict=True):
        for i, value in enumerate(cut):
            lhs[i] += value * multiplier
    correction = sum(
        (max(F(0), value - cost) for value, cost in zip(lhs, costs, strict=True)), F(0)
    )
    dual_value = sum((F(int(r)) * value for r, value in zip(rhs, dual_eq, strict=True)), F(0))
    dual_value += game.config.alpha * sum(dual_ub, F(0))
    return dual_value - correction, dual_value, correction


def restore_policy(game, records):
    behavior = {}
    for row in records:
        history = tuple(tuple(x) for x in row["history"])
        released = tuple(tuple(x) for x in row["released"])
        choices = tuple(tuple(x) for x in row["choices"])
        weights = tuple(F(x) for x in row["probabilities"])
        if choices != game.choices(history) or sum(weights) != 1 or any(x < 0 for x in weights):
            raise ValueError("Invalid saved policy")
        key = (history, released)
        if key in behavior:
            raise ValueError("Duplicate information set")
        behavior[key] = weights
    if set(behavior) != set(game.learner.infos):
        raise ValueError("Saved policy does not cover all learner information sets")

    def policy(history, outcomes):
        if any(action for action, _ in history):
            time = len(history) + 1
            remaining = game.config.budget - sum(query for _, query in history)
            belief = game._belief_from_history(history, outcomes)
            key = (time, history[-1][0], remaining, belief)
            if key not in game._continuation_actions:
                game._decision_value(time, history[-1][0], remaining, belief)
            action, query = game._continuation_actions[key]
            return tuple(F(choice == (action, query)) for choice in game.choices(history))
        return behavior[game.information(history, outcomes)]

    return policy
