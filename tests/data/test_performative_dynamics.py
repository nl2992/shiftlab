import numpy as np
import pytest

from shiftlab.data.synthetic.performative import PerformativeEnvironment


def test_joint_actions_change_both_distributions_causally():
    env = PerformativeEnvironment(noise=0, rho=0.5, strength=0.2)
    env.state = 2
    next_state, target = env.step([1, 3])
    assert next_state == pytest.approx(1.4)
    assert target == pytest.approx(2.4)
    assert env.specification()["causality"].startswith("policy-induced")


def test_stable_feedback_stationary_variance():
    env = PerformativeEnvironment(seed=123, rho=0.4, strength=0.2, noise=0.1)
    values = []
    for _ in range(15000):
        env.step([0.5 * env.state])
        values.append(env.state)
    # Local multiplier .5; Gaussian AR1 stationary variance .01/(1-.25).
    assert np.mean(values[1000:]) == pytest.approx(0, abs=0.005)
    assert np.var(values[1000:]) == pytest.approx(0.01 / 0.75, rel=0.06)


def test_unstable_local_feedback_then_bounded_saturation():
    env = PerformativeEnvironment(noise=0, rho=0.5, strength=0.8, action_bound=1)
    env.state = 0.001
    assert not env.specification(1)["linear_policy_local_stable"]
    env.step([env.state])
    assert env.state == pytest.approx(0.0013)
    for _ in range(200):
        env.step([np.clip(env.state, -1, 1)])
    assert env.state == pytest.approx(1.6)
    # Explicit unstable state dynamics can diverge even with bounded actions.
    unstable = PerformativeEnvironment(noise=0, rho=1.05)
    unstable.state = 1
    for _ in range(100):
        unstable.step([0])
    assert unstable.state == pytest.approx(1.05**100)


@pytest.mark.parametrize("actions", [[], [np.nan], [np.inf], [[1]], [11]])
def test_invalid_actions_rejected_without_state_change(actions):
    env = PerformativeEnvironment()
    with pytest.raises(ValueError):
        env.step(actions)
    assert env.state == 0
