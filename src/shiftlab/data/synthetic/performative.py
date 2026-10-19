"""Optional interactive policy-induced process, intentionally separate from exogenous DGPs."""

import numpy as np


class PerformativeEnvironment:
    """x[t+1]=rho*x[t]+strength*mean(actions[t])+noise; y=x+strength*mean(actions).

    Constant policies are stable for |rho|<1. Before action clipping, linear feedback
    a=k*x has local multiplier rho+strength*k. A multiplier above one means local
    instability, not global divergence when |rho|<1 and actions remain bounded.
    Multiple predictors pass one action each; the returned target refers to the old state.
    """

    def __init__(self, seed=42, rho=0.5, strength=0.2, noise=0.1, action_bound=10.0):
        if not np.isfinite([rho, strength, noise, action_bound]).all():
            raise ValueError("Environment parameters must be finite")
        if noise < 0 or action_bound <= 0:
            raise ValueError("Require nonnegative noise and positive action_bound")
        self.rng = np.random.default_rng(seed)
        self.rho, self.strength, self.noise, self.bound = rho, strength, noise, action_bound
        self.state = 0.0

    def step(self, actions):
        actions = np.asarray(actions, dtype=float)
        if (
            actions.ndim != 1
            or not actions.size
            or not np.isfinite(actions).all()
            or np.any(np.abs(actions) > self.bound)
        ):
            raise ValueError("Nonempty bounded actions required")
        influence = self.strength * float(np.mean(actions))
        target = self.state + influence + self.noise * self.rng.normal()
        self.state = self.rho * self.state + influence + self.noise * self.rng.normal()
        return self.state, target

    def specification(self, linear_policy_slope=0.0):
        """Evaluator specification; the agent chooses actions before both innovations."""
        if not np.isfinite(linear_policy_slope):
            raise ValueError("Policy slope must be finite")
        multiplier = self.rho + self.strength * linear_policy_slope
        return {
            "causality": "policy-induced; not exogenous drift",
            "next_state_mean": "rho*old_state + strength*mean(actions)",
            "current_target_mean": "old_state + strength*mean(actions)",
            "innovation_variance": self.noise**2,
            "innovation_independence": "target and next-state innovations independent",
            "linear_policy_local_multiplier": multiplier,
            "linear_policy_local_stable": abs(multiplier) < 1,
            "stability_scope": "local before action clipping; bounded actions can saturate growth",
            "rho": self.rho,
            "strength": self.strength,
            "action_bound": self.bound,
        }


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
