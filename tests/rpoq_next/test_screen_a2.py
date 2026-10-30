from shiftlab.dive.rpoq_next import screen_a, screen_a2


def test_a2_null_calibration_and_cap(monkeypatch):
    for mod in (screen_a, screen_a2):
        monkeypatch.setattr(mod, "N", 1600)
    sim = screen_a2.simulate("null", 0.6, 300, seed=5)
    for arm, (crossed, _, spent) in sim.items():
        assert crossed.mean() <= 0.10, arm
        assert spent.max() <= screen_a2.BUDGET, arm


def test_placebo_and_common_bet_respect_cap_and_null(monkeypatch):
    for mod in (screen_a, screen_a2):
        monkeypatch.setattr(mod, "N", 1600)
    sim = screen_a2.simulate("null", 0.0, 300, seed=6, arms=("random_conc",), bet="common")
    crossed, _, spent = sim["random_conc"]
    assert crossed.mean() <= 0.10 and spent.max() <= screen_a2.BUDGET


def test_nonstationary_settings_run_and_flip_changes_signal(monkeypatch):
    for mod in (screen_a, screen_a2):
        monkeypatch.setattr(mod, "N", 1600)
    for setting in ("het_onset", "het_flip"):
        crossed, _, spent = screen_a2.simulate(setting, 0.6, 200, seed=8, arms=("uniform",))[
            "uniform"
        ]
        assert spent.max() <= screen_a2.BUDGET and 0.0 <= crossed.mean() <= 1.0
