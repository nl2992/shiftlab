from shiftlab.dive.rpoq_exact import Evaluator, Instance
from shiftlab.dive.rpoq_next.approx_dp import SnappedEvaluator, certify

SMALL = Instance(horizon=5, delay=2, budget=2, grid=(0.5, 1.0))


def test_fine_grid_recovers_exact_and_no_policy_beats_exact():
    exact = Evaluator(SMALL, SMALL.p_alt, SMALL.budget).value()
    fine = certify(SMALL, 1e-6)
    coarse = certify(SMALL, 0.5)
    assert abs(fine["policy_power"] - exact) < 1e-9
    assert coarse["policy_power"] <= exact + 1e-9
    assert coarse["policy_null_alarm"] <= SMALL.alpha + 1e-9
    assert coarse["states"] <= fine["states"]


def test_snap_is_idempotent():
    ev = SnappedEvaluator(SMALL, SMALL.p_alt, SMALL.budget, delta=0.25)
    w = ev._snap(1.37)
    assert abs(ev._snap(w) - w) < 1e-12 and ev._snap(1.0) == 1.0


def test_threshold_adaptive_grid_is_never_better_than_exact_and_finer_near_threshold():
    exact = Evaluator(SMALL, SMALL.p_alt, SMALL.budget).value()
    r = certify(SMALL, 0.5, fine_delta=0.02)
    assert r["policy_power"] <= exact + 1e-9
    ev = SnappedEvaluator(SMALL, SMALL.p_alt, SMALL.budget, delta=0.5, fine_delta=0.02)
    w = 3.0
    assert abs(ev._snap(w) - w) / w < 0.011  # fine grid near the alarm threshold (5)
