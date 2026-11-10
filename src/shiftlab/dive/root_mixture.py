"""Root lottery between an arbitrary behavioural policy and a safe deterministic plan.

With probability ``q`` the learner commits at time 0 to the behavioural policy ``pi``; with
probability ``1 - q`` it commits to the safe plan.  By Kuhn's theorem (perfect recall) this
lottery has a behavioural realization.  At learner information ``I`` and choice ``a``::

    mix(I, a) = [q rho_pi(I) pi(I, a) + (1-q) rho_safe(I) safe(I, a)]
                / [q rho_pi(I) + (1-q) rho_safe(I)]

where ``rho(I)`` is the plan's own realization probability of reaching ``I``: the product of the
learner's own action probabilities along the public history, with no label probabilities.  If
neither plan reaches ``I`` the raw policy is used.

Unlike ``eprocess_gated_planner.mix_with_never_promote`` (valid only for deterministic plans),
this is exact for stochastic ``pi``.
"""

from __future__ import annotations

from fractions import Fraction as F

from shiftlab.dive.causal_switching_game import History, Outcomes


def mix_root_lottery(game, policy, q: F, safe_choice=(0, 0)):
    """Return the behavioural policy realizing ``q * policy + (1 - q) * safe`` at the root."""
    q = F(q)
    if not 0 <= q <= 1:
        raise ValueError("q must lie in [0, 1]")

    def safe(history: History, outcomes: Outcomes):
        return tuple(F(choice == safe_choice) for choice in game.choices(history))

    if q == 1:
        return policy

    reach_cache: dict = {}

    def reach(plan_id: int, plan, history: History, outcomes: Outcomes) -> F:
        """Own-action realization probability of the learner information of ``history``."""
        key = (plan_id, game.information(history, outcomes))
        if key in reach_cache:
            return reach_cache[key]
        if not history:
            value = F(1)
        else:
            parent = history[:-1]
            probabilities = plan(parent, game.information(parent, outcomes)[1])
            index = game.choices(parent).index(history[-1])
            value = reach(plan_id, plan, parent, outcomes) * probabilities[index]
        reach_cache[key] = value
        return value

    def mixture(history: History, outcomes: Outcomes):
        choices = game.choices(history)
        raw = policy(history, outcomes)
        if q == 0:
            return safe(history, outcomes)
        w_raw = q * reach(0, policy, history, outcomes)
        w_safe = (1 - q) * reach(1, safe, history, outcomes)
        total = w_raw + w_safe
        if not total:
            return raw
        safe_probabilities = safe(history, outcomes)
        probabilities = tuple(
            (w_raw * a + w_safe * b) / total for a, b in zip(raw, safe_probabilities, strict=True)
        )
        assert len(probabilities) == len(choices)
        return probabilities

    return mixture
