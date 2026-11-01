from dataclasses import dataclass
from fractions import Fraction

import pytest

from shiftlab.dive.risk_preserving_approx.controller_risk_lp import verify_controller_lp
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk


@dataclass(frozen=True)
class Controller:
    threshold: int = 2
    initial_state: int = 0

    def step(self, memory, time, released, previous_action, remaining_queries):
        for y in released:
            memory = memory + 1 if y else 0
        if memory >= self.threshold:
            return 1, 0, memory
        return 0, int(remaining_queries > 0), memory


@pytest.mark.parametrize(("T", "B", "d"), [(2, 1, 1), (5, 3, 1), (6, 4, 2), (8, 4, 3)])
def test_standard_lp_matches_exact_causal_bellman_response(T, B, d):
    controller = Controller()
    exact = verify_causal_null_risk(controller, horizon=T, budget=B, delay=d)
    lp = verify_controller_lp(controller, horizon=T, budget=B, delay=d)
    assert lp.risk == pytest.approx(float(exact.risk), abs=1e-10)
    assert lp.nonterminal_states == exact.visited_states
    assert lp.max_constraint_violation < 1e-9


def test_lp_fixed_controller_boundary_cases():
    assert verify_controller_lp(Controller(), horizon=4, budget=0, delay=1).risk == 0
    assert verify_causal_null_risk(
        Controller(threshold=1), horizon=2, budget=1, delay=1
    ).risk == Fraction(1, 2)


def test_lp_rejects_invalid_resource_contract():
    with pytest.raises(ValueError):
        verify_controller_lp(Controller(), horizon=0, budget=0, delay=1)
