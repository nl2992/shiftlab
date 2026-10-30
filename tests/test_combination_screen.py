from dataclasses import replace

import numpy as np
import pytest

from shiftlab.sota_search.combination_screen import Combination, combinations, make_world, screen


def test_registration_has_540_distinct_active_configs():
    configs = combinations()
    assert len(configs) == len(set(configs)) == 540


def test_hard_budget_and_release_causality():
    stream = make_world("abrupt", paths=8, horizon=90, seed=2)
    cfg = Combination(0.5, 0.95, 0.5, "uniform", False)
    a = screen(stream, [cfg], budget=3, frac=0.5, delay=5, seed=3, return_wealth=True)
    assert a["labels"].max() <= 3
    assert np.all(a["logwealth"][:, :, :5] == 0)
    # A loss not yet released cannot change visible evidence or learned bets.
    changed = {**stream, "loss": stream["loss"].copy(), "brier": stream["brier"].copy()}
    changed["loss"][:, 20:] = 1 - changed["loss"][:, 20:]
    changed["brier"][:, 20:] = 1 - changed["brier"][:, 20:]
    b = screen(changed, [cfg], budget=50, frac=0.5, delay=5, seed=3, return_wealth=True)
    c = screen(stream, [cfg], budget=50, frac=0.5, delay=5, seed=3, return_wealth=True)
    assert np.array_equal(b["logwealth"][:, :, :25], c["logwealth"][:, :, :25])
    assert not np.array_equal(b["logwealth"][:, :, 30:], c["logwealth"][:, :, 30:])


def test_vectorization_matches_single_configuration_and_query_randomness():
    stream = make_world("abrupt", paths=5, horizon=60, seed=5)
    configs = [
        Combination(0, 0.9, 0.5, "uniform", False),
        Combination(1, 0.95, 0.75, "boundary", True),
    ]
    batch = screen(stream, configs, seed=7, return_wealth=True)
    for i, c in enumerate(configs):
        single = screen(stream, [c], seed=7, return_wealth=True)
        for key in single:
            np.testing.assert_array_equal(batch[key][i], single[key][0])


def test_zero_budget_has_unit_wealth_and_restart_capital_is_conserved():
    stream = make_world("null", paths=3, horizon=80, seed=11)
    cfg = Combination(1, 0.9, 0.75, "uniform", True)
    result = screen(stream, [cfg, replace(cfg, restart=False)], budget=0, return_wealth=True)
    assert result["labels"].max() == 0
    np.testing.assert_allclose(result["logwealth"], 0, atol=1e-15)


def test_exact_one_step_unbiased_increment_and_nonnegative_factor():
    # Finite support enumeration: q depends on context, the bet does not.
    p = np.array([0.1, 0.3, 0.6, 0.9])
    q = 0.05 + 0.3 * 4 * p * (1 - p)
    r0 = np.mean(np.where(p >= 1 / 6, (1 - p) / 5, p))
    bound = (1 / 6) * (1 / 0.05 - 1) + r0
    for cap in (0.25, 0.5, 0.75):
        expected = 0
        for i, prob in enumerate(p):
            proxy = (1 - prob) / 5 if prob >= 1 / 6 else prob
            for y in (0, 1):
                loss = (1 - y) / 5 if prob >= 1 / 6 else y
                for queried in (0, 1):
                    factor = 1 + cap / bound * (proxy + queried / q[i] * (loss - proxy) - r0)
                    assert factor > 0
                    expected += (
                        0.25 * (prob if y else 1 - prob) * (q[i] if queried else 1 - q[i]) * factor
                    )
        assert expected == pytest.approx(1, abs=1e-12)


def test_invalid_configuration_is_rejected():
    stream = make_world("null", paths=2, horizon=20, seed=0)
    with pytest.raises(ValueError):
        screen(stream, [Combination(2, 0.9, 0.5, "uniform", False)])


def test_evaluator_harm_is_zero_on_null_and_localized_after_shift():
    for kind in ("null", "nuisance"):
        s = make_world(kind, paths=4, horizon=90, seed=22)
        np.testing.assert_array_equal(s["evaluator"]["harm"], 0)
    s = make_world("abrupt", paths=4, horizon=90, seed=22)
    assert np.all(s["evaluator"]["harm"][:, :30] == 0)
    assert np.all(s["evaluator"]["harm"][:, 30:] > 0)
