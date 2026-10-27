"""One-step binary-reward specialization of Wang (2026)'s projected Kelly certifier.

This is a transparent research adaptation, not the paper's general logged-tree
implementation. It assumes a known uniform two-action logger and a fixed
deterministic target action. Feasibility is checked on all four action/reward
leaves, including leaves not yet observed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _leaf_arrays(target_action: int) -> tuple[IntArray, IntArray, FloatArray]:
    actions = np.array([0, 0, 1, 1], dtype=np.int64)
    rewards = np.array([0, 1, 0, 1], dtype=np.int64)
    signs = np.where(actions == target_action, 1.0, -1.0)
    return actions, rewards, signs


def feasible_leaf_factors(lambda_: float, hedge: float, *, target_action: int) -> FloatArray:
    """Return factors on every `(action, reward)` leaf, in fixed order."""
    if target_action not in (0, 1):
        raise ValueError("target_action must be 0 or 1")
    actions, rewards, signs = _leaf_arrays(target_action)
    del actions
    if lambda_ < 0.0:
        raise ValueError("lambda_ must be nonnegative")
    return 1.0 + signs * (lambda_ * rewards + hedge)


def _projected_mle_bet(
    actions: IntArray, rewards: IntArray, *, target_action: int
) -> tuple[float, float]:
    """Fit the finite-tree plug-in bet; return the trivial bet on sparse support.

    The logged-law projection fixes the action probabilities at (1/2, 1/2)
    and estimates each arm's Bernoulli reward law by its empirical conditional
    frequency. Before both arms have appeared, we use the feasible zero bet.
    That conservative warm-up is a documented one-step implementation detail.
    """
    counts = np.bincount(actions, minlength=2)
    if np.any(counts == 0):
        return 0.0, 0.0
    success = np.bincount(actions, weights=rewards.astype(np.float64), minlength=2)
    reward_rates = success / counts

    _, leaf_rewards, signs = _leaf_arrays(target_action)
    # The projected logged law assigns logger mass 1/2 to each action and the
    # empirical conditional reward frequencies to that action's two leaves.
    leaf_prob = np.empty(4, dtype=np.float64)
    for i, (action, reward) in enumerate(zip((0, 0, 1, 1), leaf_rewards, strict=True)):
        p = reward_rates[action]
        leaf_prob[i] = 0.5 * (p if reward else 1.0 - p)

    def objective(theta: FloatArray) -> float:
        lambda_, hedge = theta
        factors = 1.0 + signs * (lambda_ * leaf_rewards + hedge)
        if np.any((leaf_prob > 0.0) & (factors <= 1e-14)):
            return 1e100
        positive = leaf_prob > 0.0
        return float(-np.dot(leaf_prob[positive], np.log(factors[positive])))

    def gradient(theta: FloatArray) -> FloatArray:
        lambda_, hedge = theta
        factors = 1.0 + signs * (lambda_ * leaf_rewards + hedge)
        if np.any((leaf_prob > 0.0) & (factors <= 1e-14)):
            return np.zeros(2, dtype=np.float64)
        positive = leaf_prob > 0.0
        weights = leaf_prob[positive] / factors[positive]
        return -np.array(
            [
                np.dot(weights, signs[positive] * leaf_rewards[positive]),
                np.dot(weights, signs[positive]),
            ],
            dtype=np.float64,
        )

    # In two arms, the fair-action bet is h*(+1 for target, -1 otherwise).
    # Requiring nonnegative wealth on all four leaves is equivalent to
    # -1 <= h <= 1 and -1 <= lambda+h <= 1.
    constraints = (
        {"type": "ineq", "fun": lambda x: 1.0 - x[0] - x[1]},
        {"type": "ineq", "fun": lambda x: 1.0 + x[0] + x[1]},
        {"type": "ineq", "fun": lambda x: 1.0 - x[1]},
        {"type": "ineq", "fun": lambda x: 1.0 + x[1]},
    )
    fit = minimize(
        objective,
        np.zeros(2, dtype=np.float64),
        jac=gradient,
        method="SLSQP",
        bounds=((0.0, 2.0), (-1.0, 1.0)),
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 200, "disp": False},
    )
    theta = np.asarray(fit.x, dtype=np.float64)
    # Soundness needs feasibility, not exact optimizer convergence. Reject a
    # numerically infeasible result; the zero bet remains a valid fallback.
    factors = feasible_leaf_factors(float(theta[0]), float(theta[1]), target_action=target_action)
    if np.any(factors < -1e-10) or not np.isfinite(theta).all():
        return 0.0, 0.0
    return max(0.0, float(theta[0])), float(theta[1])


@dataclass(frozen=True)
class OneStepUpdate:
    event: int
    fitted_lambda: float
    fitted_hedge: float
    shrinkage: float
    factor: float
    wealth: float
    certified: bool


class ProjectedKellyOneStep:
    """Predictable projected-Kelly e-process for a two-arm uniform logger."""

    def __init__(self, *, target_action: int, alpha: float = 0.05) -> None:
        if target_action not in (0, 1):
            raise ValueError("target_action must be 0 or 1")
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        self.target_action = target_action
        self.alpha = alpha
        self.actions: list[int] = []
        self.rewards: list[int] = []
        self.wealth = 1.0
        self._lambda = 0.0
        self._hedge = 0.0
        self._refit_times = self._make_refit_times()

    @staticmethod
    def _make_refit_times() -> set[int]:
        # Source Algorithm 1 uses ceil(1.15**k), with R1=2 in Theorem 5.2.
        times: set[int] = set()
        k = 1
        while len(times) < 1_000_000:
            value = int(np.ceil(1.15**k))
            if value > 100_000_000:
                break
            times.add(value)
            k += 1
        return times

    @property
    def certified(self) -> bool:
        return self.wealth >= 1.0 / self.alpha

    def update(self, action: int, reward: int) -> OneStepUpdate:
        """Consume one completed episode in event order and update wealth."""
        if action not in (0, 1) or reward not in (0, 1):
            raise ValueError("action and reward must each be binary")
        t = len(self.actions) + 1
        if t - 1 in self._refit_times:
            self._lambda, self._hedge = _projected_mle_bet(
                np.asarray(self.actions, dtype=np.int64),
                np.asarray(self.rewards, dtype=np.int64),
                target_action=self.target_action,
            )
        sign = 1.0 if action == self.target_action else -1.0
        advantage = sign * float(reward)
        shrinkage = 1.0 - t**-0.5
        factor = 1.0 + shrinkage * (self._lambda * advantage + self._hedge * sign)
        if factor < -1e-10:
            raise ArithmeticError("projected-Kelly update violated leafwise nonnegativity")
        factor = max(0.0, factor)
        self.wealth *= factor
        self.actions.append(action)
        self.rewards.append(reward)
        return OneStepUpdate(
            event=t,
            fitted_lambda=self._lambda,
            fitted_hedge=self._hedge,
            shrinkage=shrinkage,
            factor=factor,
            wealth=self.wealth,
            certified=self.certified,
        )
