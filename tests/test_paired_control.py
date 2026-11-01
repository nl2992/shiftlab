from dataclasses import replace

import numpy as np
import pytest

from shiftlab.dive.promotion import CandidatePromotionTest, CandidateVersion
from shiftlab.sota_search.paired_control import (
    PairedConfig,
    paired_configurations,
    paired_screen,
    paired_world,
)
from shiftlab.sota_search.paired_references import paired_fixed_mixture, paired_paper_reference


def test_registered_dimensions_are_active_and_unique():
    configs = paired_configurations()
    assert len(configs) == len(set(configs)) == 648
    assert all(0 < c.cap < 1 and 0 < c.gamma <= 1 for c in configs)


def test_harmful_and_tie_nulls_match_frozen_common_outcome_contract():
    for kind in ("harmful", "tie"):
        s = paired_world(kind, paths=10, horizon=120, seed=3)
        if kind == "harmful":
            assert np.all(s["evaluator"]["mean_gain"] <= 0)
        else:
            np.testing.assert_allclose(s["evaluator"]["mean_gain"], 0, atol=1e-15)
        np.testing.assert_array_equal(s["loss"] == s["candidate_loss"], ~s["disagree"])
    s = paired_world("identical", paths=4, horizon=120, seed=4)
    np.testing.assert_array_equal(s["loss"], s["candidate_loss"])


def test_new_harmful_challenger_control_has_incumbent_harm_but_negative_benefit():
    p = np.array([0.1, 0.3, 0.6, 0.9])
    a = p >= 1 / 6
    for truth in (p, np.clip(p + np.where(a, -0.15, 0.15), 0, 1)):
        incumbent = np.where(a, (1 - truth) / 5, truth)
        challenger = np.where(~a, (1 - truth) / 5, truth)
        assert (incumbent - challenger).mean() < 0
    source = np.where(a, (1 - p) / 5, p).mean()
    assert incumbent.mean() > source
    stream = paired_world("harmful_after_shift", paths=2, horizon=120, seed=4)
    assert stream["disagree"].all()


def test_no_hidden_future_feedback_and_hard_budget():
    s = paired_world("useful", paths=5, horizon=120, seed=9)
    cfgs = paired_configurations()[::50]
    a = paired_screen(s, cfgs, budget=15, delay=5, seed=7, return_wealth=True)
    assert a["labels"].max() <= 15
    changed = {**s, "loss": s["loss"].copy(), "candidate_loss": s["candidate_loss"].copy()}
    changed["loss"][:, 40:] = 1 - changed["loss"][:, 40:]
    changed["candidate_loss"][:, 40:] = 1 - changed["candidate_loss"][:, 40:]
    b = paired_screen(changed, cfgs, budget=15, delay=5, seed=7, return_wealth=True)
    np.testing.assert_array_equal(a["logwealth"][:, :, :45], b["logwealth"][:, :, :45])


def test_zero_budget_and_identical_candidate_never_promote():
    s = paired_world("identical", paths=3, horizon=100, seed=4)
    cfgs = paired_configurations()[::60]
    a = paired_screen(s, cfgs, budget=0, return_wealth=True)
    assert np.all(a["labels"] == 0) and np.all(a["first"] == 100)
    np.testing.assert_allclose(a["logwealth"], 0, atol=1e-15)
    b = paired_screen(s, cfgs, budget=20)
    assert np.all(b["first"] == 100)


def test_post_alarm_does_not_reuse_pending_pretrigger_labels():
    s = paired_world("useful", paths=3, horizon=150, seed=2)
    cfg = PairedConfig("after_alarm", "uniform", 0.9, 0.75, False, "none", "kelly")
    out = paired_screen(s, [cfg], budget=120, frac=0.8, delay=4, seed=5, return_wealth=True)
    for i, alarm in enumerate(out["cost_alarm"][0]):
        np.testing.assert_allclose(out["logwealth"][0, i, : min(alarm + 4, 150)], 0, atol=1e-15)


def test_scalar_vectorized_execution_and_realized_cost_accounting():
    s = paired_world("useful_initial", paths=2, horizon=200, seed=1)
    c = PairedConfig("direct", "uniform", 0.98, 0.75, False, "none", "kelly")
    both = paired_screen(s, [c, replace(c, bet="ftl")], budget=150, frac=0.8, seed=8)
    one = paired_screen(s, [c], budget=150, frac=0.8, seed=8)
    for key in one:
        np.testing.assert_array_equal(both[key][0], one[key][0])
    for i, t in enumerate(one["first"][0]):
        expected = (
            s["loss"][i, :t].sum()
            + s["candidate_loss"][i, t:].sum()
            + 0.001 * one["labels"][0, i]
            + (t < 200)
        )
        assert one["total_cost"][0, i] == pytest.approx(expected)


def test_finite_support_ipw_certificate_step_is_unbiased_at_null_boundary():
    # D = Y - .5, p(Y=1)=.5. Any predictable positive bet preserves null expectation.
    for q in (0.05, 0.2, 0.8):
        for cap in (0.5, 0.75):
            expectation = 0
            for y in (0, 1):
                for label in (0, 1):
                    factor = 1 + cap * q * (label / q * (y - 0.5))
                    assert factor > 0
                    expectation += 0.5 * (q if label else 1 - q) * factor
            assert expectation == pytest.approx(1, abs=1e-15)


def test_existing_promotion_component_is_fixed_mixture_reference():
    version = CandidateVersion("fixed", "incumbent", 0, 1)
    test = CandidatePromotionTest(version, alpha_i=0.05, max_event_cost=1, switching_cost=0.01)
    gains = [0.2, -0.1, 0.6, 0.4, -0.3]
    components = np.ones(5)
    stakes = np.array([0.05, 0.1, 0.2, 0.4, 0.8])
    for i, gain in enumerate(gains):
        inc, cand = max(gain, 0), max(-gain, 0)
        components *= 1 + stakes * (gain - 0.01) / 1.01
        value = test.update(event_index=i + 1, incumbent_cost=inc, candidate_cost=cand)
        assert value == pytest.approx(np.log(components.mean()), abs=1e-14)


def test_ipw_mixture_adapter_matches_existing_full_feedback_promotion():
    s = paired_world("useful_initial", paths=1, horizon=100, seed=7)
    out = paired_fixed_mixture(
        s, frac=1, budget=100, delay=1, margin=0.01, switch_cost=0, return_wealth=True
    )
    test = CandidatePromotionTest(
        CandidateVersion("fixed", "inc", 0, 1), alpha_i=0.05, max_event_cost=1, switching_cost=0.01
    )
    for t in range(99):
        expected = test.update(
            event_index=t + 1,
            incumbent_cost=s["loss"][0, t],
            candidate_cost=s["candidate_loss"][0, t],
        )
        assert out["logwealth"][0, t + 1] == pytest.approx(expected, abs=1e-12)


def test_direct_references_respect_hard_budget_and_zero_gain():
    s = paired_world("identical", paths=3, horizon=120, seed=6)
    for name in ("mixture", "pr", "rcps"):
        if name == "mixture":
            result = paired_fixed_mixture(s, budget=10)
        else:
            result = paired_paper_reference(s, method=name, budget=10)
        assert np.all(result["first"] == 120)
        assert result["labels"].max() <= 10


def test_known_zero_pair_cost_needs_no_label_and_no_switch():
    s = paired_world("identical", paths=4, horizon=120, seed=12)
    c = PairedConfig("direct", "uniform", 0.98, 0.75, False, "none", "kelly")
    result = paired_screen(s, [c], skip_known_zero=True)
    assert np.all(result["labels"] == 0)
    np.testing.assert_allclose(result["delta_vs_incumbent"], 0, atol=1e-12)
    with pytest.raises(ValueError):
        paired_screen(s, [replace(c, mode="and_alarm")], skip_known_zero=True)


def test_known_zero_removal_preserves_evidence_when_budget_does_not_bind():
    s = paired_world("useful", paths=4, horizon=200, seed=11)
    c = PairedConfig("direct", "uniform", 0.98, 0.75, False, "none", "kelly")
    full = paired_screen(s, [c], budget=200, seed=3, return_wealth=True)
    reduced = paired_screen(s, [c], budget=200, seed=3, return_wealth=True, skip_known_zero=True)
    np.testing.assert_array_equal(full["logwealth"], reduced["logwealth"])
    assert np.all(reduced["labels"] <= full["labels"])
