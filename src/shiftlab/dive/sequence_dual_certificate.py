"""Exact weak-duality check for the classical causal switching game's LP.

Known LP certification, not a novel planning bound. Coefficients must be built
as Fractions from the scientific model, never rationalized floating matrices.
"""

from fractions import Fraction as F


def flow_columns(flow):
    columns = [{} for _ in range(flow.count)]
    columns[0][0] = F(1)
    for row, (parent, children, _choices) in enumerate(flow.infos.values(), start=1):
        columns[parent][row] = F(-1)
        for child in children:
            columns[child][row] = F(1)
    return columns


def verify_dual(game, inequalities, equalities):
    if not game.exact_coefficients or not game.built:
        raise ValueError("exact model coefficients must be built first")
    y, z = tuple(map(F, inequalities)), tuple(map(F, equalities))
    nx, ny = game.learner.count, game.opponent.count
    if len(y) != ny + 1 or len(z) != len(game.learner.infos) + 1 or any(v > 0 for v in y):
        raise ValueError("dual dimensions or inequality signs invalid")
    if any(not isinstance(v, F) for v in list(game.cost.values()) + list(game.risk.values())):
        raise ValueError("non-rational model coefficients")
    lhs = [F(0)] * nx
    for (i, j), risk in game.risk.items():
        lhs[i] += risk * y[j]
    for i, column in enumerate(flow_columns(game.learner)):
        lhs[i] += sum(coef * z[j] for j, coef in column.items())
    slack = [game.cost.get(i, F(0)) - lhs[i] for i in range(nx)]
    if min(slack) < 0:
        raise ValueError("negative exact dual slack")
    # Free opponent potential columns require exact equality, no tolerance.
    free = [F(0)] * (len(game.opponent.infos) + 1)
    for j, column in enumerate(flow_columns(game.opponent)):
        for row, coef in column.items():
            free[row] -= coef * y[j]
    free[0] += y[-1]
    if any(free):
        raise ValueError("free-variable dual equality violated")
    return {
        "lower_bound": z[0] + game.config.alpha * y[-1],
        "minimum_exact_slack": min(slack),
        "checked_nonnegative_columns": nx,
        "checked_free_columns": len(free),
    }
