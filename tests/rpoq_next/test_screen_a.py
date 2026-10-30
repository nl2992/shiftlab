import numpy as np

from shiftlab.dive.rpoq_next import screen_a


def test_null_crossing_rate_stays_near_alpha(monkeypatch):
    monkeypatch.setattr(screen_a, "N", 1200)
    sim = screen_a.simulate("null", 0.6, 600, seed=3)
    for arm, (crossed, _, spent) in sim.items():
        assert crossed.mean() <= 0.09, arm
        assert spent.max() <= screen_a.BUDGET, arm
    assert np.isfinite([w.mean() for _, w, _ in sim.values()]).all()
