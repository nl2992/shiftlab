"""Classical sequence-form reference for a finite causal switching game.

This is not a novel algorithm. Full learner histories enforce nonanticipation;
pending outcomes enter evaluator/opponent histories, never learner information.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache
from itertools import product

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from shiftlab.dive.delayed_regime_information import RegimeModel

Choice = tuple[int, int]
History = tuple[Choice, ...]
Outcomes = tuple[tuple[int, int], ...]
Information = tuple[History, Outcomes]
Policy = Callable[[History, Outcomes], tuple[F, ...]]


@dataclass(frozen=True)
class GameConfig:
    horizon: int = 5
    budget: int = 2
    delay: int = 2
    alpha: F = F(1, 10)
    query_cost: F = F(1, 100)
    switch_cost: F = F(1, 10)
    max_nodes: int = 200_000

    def __post_init__(self):
        if any(type(v) is not int for v in (self.horizon, self.budget, self.delay, self.max_nodes)):
            raise ValueError("integer horizon, budget, delay and node limit required")
        if self.horizon < 1 or not 0 <= self.budget <= self.horizon or self.delay < 1:
            raise ValueError("invalid horizon, hard budget or delay")
        if self.max_nodes < 1 or not 0 <= self.alpha <= 1:
            raise ValueError("invalid node limit or risk probability")
        if self.query_cost < 0 or self.switch_cost < 0:
            raise ValueError("costs must be nonnegative")


class SequenceFlow:
    def __init__(self):
        self.count = 1  # Sequence 0 is empty, with realization weight 1.
        self.infos: dict[object, tuple[int, tuple[int, ...], tuple]] = {}

    def add(self, key, parent: int, choices: tuple) -> tuple[int, ...]:
        if key in self.infos:
            saved_parent, children, saved_choices = self.infos[key]
            assert parent == saved_parent and choices == saved_choices, "perfect recall violated"
            return children
        children = tuple(range(self.count, self.count + len(choices)))
        self.count += len(choices)
        self.infos[key] = (parent, children, choices)
        return children

    def matrix(self):
        row, col, data = [0], [0], [1.0]
        for i, (parent, children, _) in enumerate(self.infos.values(), start=1):
            row.extend([i] * (1 + len(children)))
            col.extend([parent, *children])
            data.extend([-1.0, *([1.0] * len(children))])
        matrix = coo_matrix((data, (row, col)), shape=(len(self.infos) + 1, self.count)).tocsr()
        rhs = np.zeros(matrix.shape[0])
        rhs[0] = 1.0
        return matrix, rhs


class CausalSwitchingGame:
    def __init__(self, config: GameConfig, model: RegimeModel):
        self.config, self.model = config, model
        self.learner, self.opponent = SequenceFlow(), SequenceFlow()
        self.cost: dict[int, float] = defaultdict(float)
        self.risk: dict[tuple[int, int], float] = defaultdict(float)
        self.nodes = 0
        self.built = False

    def information(self, history: History, outcomes: Outcomes) -> Information:
        time = len(history) + 1
        return history, tuple((s, y) for s, y in outcomes if s + self.config.delay <= time)

    def choices(self, history: History) -> tuple[Choice, ...]:
        remaining = self.config.budget - sum(q for _, q in history)
        assert remaining >= 0
        return tuple(product((0, 1), (0, 1) if remaining else (0,)))

    def _node(self):
        self.nodes += 1
        if self.nodes > self.config.max_nodes:
            raise RuntimeError("registered tree node limit exceeded")

    def _alternative(self, history, outcomes, sequence, weight, posterior, total_cost):
        self._node()
        time = len(history) + 1
        if time > self.config.horizon:
            self.cost[sequence] += float(weight * total_cost)
            return
        state1 = self.model.propagate(posterior, 1)
        positive = self.model.emission(state1)
        choices = self.choices(history)
        children = self.learner.add(self.information(history, outcomes), sequence, choices)
        old = history[-1][0] if history else 0
        for (action, query), child in zip(choices, children, strict=True):
            cost = positive if action == 0 else 1 - positive
            cost += self.config.query_cost * query + self.config.switch_cost * (action != old)
            next_history = history + ((action, query),)
            if query:
                for y, probability in ((0, 1 - positive), (1, positive)):
                    likelihood1 = self.model.emission1 if y else 1 - self.model.emission1
                    next_posterior = state1 * likelihood1 / probability
                    self._alternative(
                        next_history,
                        outcomes + ((time, y),),
                        child,
                        weight * probability,
                        next_posterior,
                        total_cost + cost,
                    )
            else:
                self._alternative(next_history, outcomes, child, weight, state1, total_cost + cost)

    def _null(self, history, outcomes, sequence, opponent_sequence, weight):
        self._node()
        time = len(history) + 1
        if time > self.config.horizon:
            return
        choices = self.choices(history)
        children = self.learner.add(self.information(history, outcomes), sequence, choices)
        for (action, query), child in zip(choices, children, strict=True):
            if action:
                # The first promotion determines the event; later choices cannot undo it.
                self.risk[child, opponent_sequence] += float(weight)
                continue
            next_history = history + ((action, query),)
            if query:
                # This information includes generated pending labels and past null moves.
                key = (next_history, outcomes, opponent_sequence)
                probabilities = (F(0), F(1, 2))
                opponent_children = self.opponent.add(key, opponent_sequence, probabilities)
                for probability, opponent_child in zip(
                    probabilities, opponent_children, strict=True
                ):
                    for y, mass in ((0, 1 - probability), (1, probability)):
                        if mass:
                            self._null(
                                next_history,
                                outcomes + ((time, y),),
                                child,
                                opponent_child,
                                weight * mass,
                            )
            else:
                self._null(next_history, outcomes, child, opponent_sequence, weight)

    def build(self):
        if self.built:
            return
        self._alternative((), (), 0, F(1), self.model.prior1, F(0))
        self._null((), (), 0, 0, F(1))
        self.built = True

    def promotion_tape_matrix(self) -> tuple[csr_matrix, tuple[tuple[int, ...], ...]]:
        """Linear promotion probabilities on full potential-label tapes.

        For each tape, each coefficient is one when the corresponding learner
        realization sequence is a first-promotion sequence reached on that tape.
        Summing these coefficients against realization weights gives the
        probability of ever promoting under the tape, including learner
        randomization over actions and queries.
        """
        self.build()
        tapes = tuple(product((0, 1), repeat=self.config.horizon))
        rows: list[dict[int, float]] = []
        for tape in tapes:
            coefficients: dict[int, float] = defaultdict(float)

            def visit(history: History, outcomes: Outcomes, sequence: int) -> None:
                time = len(history) + 1
                if time > self.config.horizon:
                    return
                key = self.information(history, outcomes)
                _, children, choices = self.learner.infos[key]
                for choice, child in zip(choices, children, strict=True):
                    action, query = choice
                    if action:
                        coefficients[child] += 1.0  # noqa: B023 - Consumed synchronously within this loop iteration.
                        continue
                    following_outcomes = outcomes + (((time, tape[time - 1]),) if query else ())  # noqa: B023 - Consumed synchronously within this loop iteration.
                    visit(history + (choice,), following_outcomes, child)

            visit((), (), 0)
            rows.append(dict(coefficients))

        index = {tape: i for i, tape in enumerate(tapes)}
        row_ids, col_ids, values = [], [], []
        # Build cover differences directly; each row is g(tape)-g(successor) <= 0.
        cover_count = 0
        for tape in tapes:
            source = index[tape]
            for bit, value in enumerate(tape):
                if value:
                    continue
                successor = tape[:bit] + (1,) + tape[bit + 1 :]
                target = index[successor]
                for column, coefficient in rows[source].items():
                    row_ids.append(cover_count)
                    col_ids.append(column)
                    values.append(coefficient)
                for column, coefficient in rows[target].items():
                    row_ids.append(cover_count)
                    col_ids.append(column)
                    values.append(-coefficient)
                cover_count += 1
        matrix = coo_matrix(
            (values, (row_ids, col_ids)), shape=(cover_count, self.learner.count)
        ).tocsr()
        return matrix, tapes

    def recover(self, realization) -> tuple[Policy, list[dict]]:
        behavior = {}
        records = []
        for key, (_, children, choices) in self.learner.infos.items():
            masses = [F(float(max(0.0, realization[j]))).limit_denominator(10**9) for j in children]
            if sum(masses) == 0:
                # Off-path behavior is still a valid policy, with no further spend.
                history, _ = key
                old = history[-1][0] if history else 0
                fallback = (old, 0)
                if fallback not in choices:
                    fallback = (old, 1)
                masses[choices.index(fallback)] = F(1)
            total = sum(masses)
            weights = tuple(mass / total for mass in masses)
            behavior[key] = weights
            records.append(
                {
                    "history": key[0],
                    "released": key[1],
                    "choices": choices,
                    "probabilities": [str(w) for w in weights],
                }
            )

        def policy(history, outcomes):
            return behavior[self.information(history, outcomes)]

        return policy, records

    def expected_metrics(self, policy: Policy) -> tuple[F, ...]:
        """Independent forward recursion, not sequence-form matrix multiplication."""

        @cache
        def visit(history, outcomes, posterior):
            time = len(history) + 1
            if time > self.config.horizon:
                return (F(0),) * 5
            state1 = self.model.propagate(posterior, 1)
            positive = self.model.emission(state1)
            old = history[-1][0] if history else 0
            result = [F(0)] * 5
            for (action, query), mass in zip(
                self.choices(history), policy(history, outcomes), strict=True
            ):
                if not mass:
                    continue
                stage = (
                    positive if action == 0 else 1 - positive,
                    self.config.query_cost * query,
                    self.config.switch_cost * (action != old),
                    F(query),
                    F(action != old),
                )
                next_history = history + ((action, query),)
                future = [F(0)] * 5
                if query:
                    for y, probability in ((0, 1 - positive), (1, positive)):
                        likelihood1 = self.model.emission1 if y else 1 - self.model.emission1
                        following = visit(
                            next_history,
                            outcomes + ((time, y),),
                            state1 * likelihood1 / probability,
                        )
                        future = [
                            v + probability * w for v, w in zip(future, following, strict=True)
                        ]
                else:
                    future = visit(next_history, outcomes, state1)
                result = [v + mass * (s + f) for v, s, f in zip(result, stage, future, strict=True)]
            return tuple(result)

        return visit((), (), self.model.prior1)

    def null_risk(self, policy: Policy, *, iid_boundary: bool = False) -> F:
        """Causal endpoint best response; pending outcomes are already generated."""

        @cache
        def visit(history, outcomes):
            time = len(history) + 1
            if time > self.config.horizon:
                return F(0)
            result = F(0)
            for (action, query), mass in zip(
                self.choices(history), policy(history, outcomes), strict=True
            ):
                if not mass:
                    continue
                if action:
                    value = F(1)
                else:
                    next_history = history + ((action, query),)
                    if query:
                        zero = visit(next_history, outcomes + ((time, 0),))
                        one = visit(next_history, outcomes + ((time, 1),))
                        value = (zero + one) / 2 if iid_boundary else max(zero, (zero + one) / 2)
                    else:
                        value = visit(next_history, outcomes)
                result += mass * value
            return result

        return visit((), ())

    def solve(self, *, monotone_promotion: bool = False) -> tuple[dict, Policy, list[dict]]:
        self.build()
        e_matrix, e = self.learner.matrix()
        f_matrix, f = self.opponent.matrix()
        n_x, n_y = self.learner.count, self.opponent.count
        indices = list(self.risk)
        null_payoff = coo_matrix(
            ([self.risk[k] for k in indices], ([k[0] for k in indices], [k[1] for k in indices])),
            shape=(n_x, n_y),
        ).tocsr()
        objective = np.zeros(n_x + len(f))
        for key, value in self.cost.items():
            objective[key] = value
        inequality = vstack(
            [
                hstack([null_payoff.T, -f_matrix.T]),
                hstack([csr_matrix((1, n_x)), csr_matrix(f.reshape(1, -1))]),
            ]
        ).tocsr()
        rhs = np.r_[np.zeros(n_y), float(self.config.alpha)]
        if monotone_promotion:
            monotonicity, _tapes = self.promotion_tape_matrix()
            if monotonicity.shape[0]:
                inequality = vstack(
                    [
                        inequality,
                        hstack([monotonicity, csr_matrix((monotonicity.shape[0], len(f)))]),
                    ]
                ).tocsr()
                rhs = np.r_[rhs, np.zeros(monotonicity.shape[0])]
        equality = hstack([e_matrix, csr_matrix((len(e), len(f)))]).tocsr()
        result = linprog(
            objective,
            A_ub=inequality,
            b_ub=rhs,
            A_eq=equality,
            b_eq=e,
            bounds=[(0, None)] * n_x + [(None, None)] * len(f),
            method="highs",
            options={
                "time_limit": 60.0,
                "primal_feasibility_tolerance": 1e-9,
                "dual_feasibility_tolerance": 1e-9,
            },
        )
        if not result.success:
            raise RuntimeError(f"reference LP did not finish optimally: {result.message}")
        policy, records = self.recover(result.x[:n_x])
        metrics = self.expected_metrics(policy)
        recovered_cost = sum(metrics[:3])
        assert abs(float(recovered_cost) - result.fun) <= 1e-7
        risk = self.null_risk(policy)
        activation = min(F(1), self.config.alpha / risk) if risk else F(1)
        continue_metrics = self.expected_metrics(
            lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in self.choices(history))
        )
        calibrated = tuple(
            activation * a + (1 - activation) * b
            for a, b in zip(metrics, continue_metrics, strict=True)
        )
        assert activation * risk <= self.config.alpha
        report = {
            "status": "classical_causal_game_reference_completed_no_novel_method_claim",
            "nodes": self.nodes,
            "learner_sequences": n_x,
            "opponent_sequences": n_y,
            "learner_information_sets": len(self.learner.infos),
            "opponent_information_sets": len(self.opponent.infos),
            "solver_objective": float(result.fun),
            "equality_residual": float(np.max(np.abs(equality @ result.x - e))),
            "inequality_violation": float(max(0, np.max(inequality @ result.x - rhs))),
            "raw_recovered_cost": str(recovered_cost),
            "raw_causal_null_risk": str(risk),
            "iid_boundary_risk": str(self.null_risk(policy, iid_boundary=True)),
            "activation_probability": str(activation),
            "calibrated_risk_bound": str(activation * risk),
            "calibrated_total_cost": str(sum(calibrated[:3])),
            "calibrated_metrics": dict(
                zip(
                    ("decision_cost", "query_cost", "switch_cost", "queries", "switches"),
                    map(str, calibrated),
                    strict=True,
                )
            ),
            "continue_cost": str(sum(continue_metrics[:3])),
            "root_behavior": records[0],
            "scope": "Numerically optimized finite known-model reference; exact recovered-policy risk verification.",
            "monotone_promotion_constraint": monotone_promotion,
        }
        return report, policy, records
