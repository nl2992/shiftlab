"""Optional interactive policy-induced process, intentionally separate from exogenous DGPs."""

import numpy as np


class PerformativeEnvironment:
    """x[t+1]=rho*x[t]+strength*mean(actions[t])+noise; y=x+strength*mean(actions).

    Constant policies are stable for |rho|<1. Linear feedback a=k*x is stable only
    when |rho+strength*k|<1. Multiple predictors pass one action each. Actions are bounded.
    """

    def __init__(self, seed=42, rho=0.5, strength=0.2, noise=0.1, action_bound=10.0):
        self.rng = np.random.default_rng(seed)
        self.rho, self.strength, self.noise, self.bound = rho, strength, noise, action_bound
        self.state = 0.0

    def step(self, actions):
        if not len(actions) or np.any(np.abs(actions) > self.bound):
            raise ValueError("Nonempty bounded actions required")
        influence = self.strength * float(np.mean(actions))
        target = self.state + influence + self.noise * self.rng.normal()
        self.state = self.rho * self.state + influence + self.noise * self.rng.normal()
        return self.state, target


def indistinguishable_worlds(probability=0.2):
    """Identical X,Y law; undisclosed utilities imply different Bayes actions.

    No test of features or labels can distinguish these worlds. Costs must be revealed
    for a decision monitor to identify the change. This is an analytical construction.
    """
    from ..decision_tasks import binary_action

    return {
        "shared_label_probability": probability,
        "visible_information": "identical X,Y distribution",
        "world_A_action": bool(binary_action(probability, 1.0, 1.0)),
        "world_B_action": bool(binary_action(probability, 10.0, 1.0)),
    }
