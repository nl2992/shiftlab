"""Standard product-MDP reachability LP for the same fixed-controller null.

This is an algorithmic reference, not the authors' robust-FSC synthesis code.
For each endpoint response a, v(s)>=E_a[v(next)]. Minimize sum(v) with
promotion=1 and horizon-end=0. Finite acyclicity makes the minimal feasible
majorant equal to the Bellman maximum; HiGHS solves its floating-point LP.
"""

from collections import deque
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from .controller_risk_verifier import DeterministicController


@dataclass(frozen=True)
class LPRiskVerification:
    risk: float
    states: int
    nonterminal_states: int
    constraints: int
    max_constraint_violation: float


def verify_controller_lp(
    controller: DeterministicController,
    *,
    horizon: int,
    budget: int,
    delay: int,
    max_states: int = 100000,
    time_limit: float = 60,
) -> LPRiskVerification:
    if (
        any(type(x) is not int for x in (horizon, budget, delay, max_states))
        or horizon < 1
        or not 0 <= budget <= horizon
        or delay < 1
        or max_states < 1
    ):
        raise ValueError("invalid finite controller contract")
    initial = (1, controller.initial_state, 0, budget, ())
    indices = {initial: 0}
    todo = deque([initial])
    bounds = []
    constraints = []
    nonterminal = 0

    def index(state):
        if state not in indices:
            if len(indices) >= max_states:
                raise RuntimeError("registered product-state cap exceeded")
            indices[state] = len(indices)
            todo.append(state)
        return indices[state]

    while todo:
        state = todo.popleft()
        i = indices[state]
        time, memory, old, remaining, pending = state
        assert len(bounds) == i
        if time > horizon:
            bounds.append((0, 0))
            continue
        nonterminal += 1
        released = tuple(x[2] for x in sorted(pending, key=lambda x: x[1]) if x[0] == time)
        rest = tuple(x for x in pending if x[0] != time)
        action, query, nxt = controller.step(memory, time, released, old, remaining)
        if action not in (0, 1) or query not in (0, 1):
            raise ValueError("binary action/query required")
        if query and remaining == 0:
            raise ValueError("controller violates pathwise query budget")
        if action:
            bounds.append((1, 1))
            continue
        bounds.append((0, 1))
        if not query:
            child = index((time + 1, nxt, action, remaining, rest))
            constraints.append([(i, -1), (child, 1)])
        else:
            zero = index(
                (
                    time + 1,
                    nxt,
                    action,
                    remaining - 1,
                    tuple(sorted(rest + ((time + delay, time, 0),))),
                )
            )
            one = index(
                (
                    time + 1,
                    nxt,
                    action,
                    remaining - 1,
                    tuple(sorted(rest + ((time + delay, time, 1),))),
                )
            )
            constraints.extend([[(i, -1), (zero, 1)], [(i, -1), (zero, 0.5), (one, 0.5)]])
    row = []
    col = []
    data = []
    for j, items in enumerate(constraints):
        for i, value in items:
            row.append(j)
            col.append(i)
            data.append(value)
    matrix = coo_matrix((data, (row, col)), shape=(len(constraints), len(indices))).tocsr()
    result = linprog(
        np.ones(len(indices)),
        A_ub=matrix,
        b_ub=np.zeros(len(constraints)),
        bounds=bounds,
        method="highs",
        options={"time_limit": time_limit},
    )
    if not result.success:
        raise RuntimeError(f"HiGHS reachability LP failed: {result.message}")
    violation = float(max(0, np.max(matrix @ result.x))) if len(constraints) else 0.0
    return LPRiskVerification(
        float(result.x[0]), len(indices), nonterminal, len(constraints), violation
    )
