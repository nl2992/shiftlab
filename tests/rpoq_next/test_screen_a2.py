from shiftlab.dive.rpoq_next import screen_a, screen_a2


def test_a2_null_calibration_and_cap(monkeypatch):
    for mod in (screen_a, screen_a2):
        monkeypatch.setattr(mod, "N", 1600)
    sim = screen_a2.simulate("null", 0.6, 300, seed=5)
    for arm, (crossed, _, spent) in sim.items():
        assert crossed.mean() <= 0.10, arm
        assert spent.max() <= screen_a2.BUDGET, arm
