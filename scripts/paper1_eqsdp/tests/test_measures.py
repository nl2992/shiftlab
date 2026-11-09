"""Toy-record checks of each measure formula (T=2000, cs=5, cq=.05)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matrix
import measures as M

import data

T = data.T


def rec(stream, ep, seed, policy, loss, labels, switches, first, final, wrong, gain, promote=None):
    net = loss + 0.05 * labels + 5.0 * switches
    return dict(  # noqa: C408
        stream=stream, ep=ep, seed=seed, policy=policy, delay=100, net=net, loss=loss,
        switches=switches, labels=labels,
        ever_promote=int(first >= 0) if promote is None else promote,
        first_deploy=first, final=final, frac_on_wrong=wrong, mean_gain=gain,
    )  # fmt: skip


@pytest.fixture
def toy():
    # ep0: challenger better (gain .01 => L0 - L1 = 20). never loss 400 -> L1 = 380.
    # ep1: challenger worse (gain -.01). never loss 300.  ep2: tie (gain 0), never loss 200.
    rows = []
    for ep, (l0, g) in enumerate([(400.0, 0.01), (300.0, -0.01), (200.0, 0.0)]):
        rows.append(rec("s", ep, 0, data.NEVER, l0, 0, 0, -1, 0, 1.0 if g > 0 else 0.0, g))
    # pol: ep0 promotes at t=500 and ends on 1 (loss 385, 10 labels, 1 switch)
    rows.append(rec("s", 0, 0, "pol", 385.0, 10, 1, 500, 1, 0.25, 0.01))
    # ep1 false promotion, ends on 1 (loss 310, 20 labels, 3 switches, wrong 0.5)
    rows.append(rec("s", 1, 0, "pol", 310.0, 20, 3, 100, 1, 0.5, -0.01))
    # ep2 tie: never promotes
    rows.append(rec("s", 2, 0, "pol", 200.0, 0, 0, -1, 0, 0.0, 0.0))
    return pd.DataFrame(rows)


def val(d, pol, k):
    ec = M.episode_components(d).xs(pol, level="policy")
    return ec[f"{k}__num"].sum() / ec[f"{k}__den"].sum()


def test_invariants_and_hindsight(toy):
    x = M.seed_level(toy)
    p = x[(x.policy == "pol")].set_index("ep")
    assert p.Jnever.tolist() == [400.0, 300.0, 200.0]
    assert p.Jhind.tolist() == [400.0 - T * 0.01, 300.0, 200.0]  # 380, 300, 200


def test_harm_and_capture(toy):
    # net: ep0 385+.5+5 = 390.5 ; ep1 310+1+15 = 326 ; ep2 200
    assert val(toy, "pol", "harm_all") == pytest.approx(((390.5 - 400) + (326 - 300) + 0) / 3)
    assert val(toy, "pol", "harm_C") == pytest.approx(-9.5)
    assert val(toy, "pol", "harm_N") == pytest.approx((26 + 0) / 2)
    assert val(toy, "pol", "capture") == pytest.approx(9.5 / 20)
    assert val(toy, "pol", "regret_hind") == pytest.approx(((390.5 - 380) + 26 + 0) / 3)


def test_wrong_exposure_and_terminal(toy):
    assert val(toy, "pol", "wrong_exposure") == pytest.approx((0.25 + 0.5) / 2)  # tie excluded
    assert val(toy, "pol", "wrong_exposure_C") == pytest.approx(0.25)
    assert val(toy, "pol", "wrong_exposure_S") == pytest.approx(0.5)
    assert val(toy, "pol", "terminal_correct") == pytest.approx(0.5)  # ep0 yes, ep1 no
    assert val(toy, "pol", "terminal_correct_C") == 1.0
    assert val(toy, "pol", "terminal_correct_S") == 0.0


def test_time_to_correct_censoring(toy):
    assert val(toy, "pol", "ttc_rmst") == 500.0
    assert val(toy, "pol", "promoted_C") == 1.0
    assert val(toy, "pol", "ttc_given_promoted") == 500.0
    # never_switch is censored at T on the C episode
    assert val(toy, data.NEVER, "ttc_rmst") == T
    assert val(toy, data.NEVER, "promoted_C") == 0.0
    assert np.isnan(M._ratio(np.array([0.0]), np.array([0.0]))[0])  # empty-class ratio is NaN


def test_false_promotion(toy):
    assert val(toy, "pol", "false_promo_N") == pytest.approx(0.5)  # ep1 yes, tie no
    assert val(toy, "pol", "false_promo_S") == pytest.approx(1.0)


def test_churn_shares_and_label_efficiency(toy):
    assert val(toy, "pol", "switches") == pytest.approx(4 / 3)
    assert val(toy, "pol", "switch_cost_share") == pytest.approx(
        (5 * 1 + 5 * 3 + 0) / (390.5 + 326 + 200)
    )
    assert val(toy, "pol", "label_cost_share") == pytest.approx(0.05 * 30 / (390.5 + 326 + 200))
    # gross: (400-385)+(300-310)+0 = 5 over 30 labels ; net: 9.5 - 26 = -16.5 over 30 labels
    assert val(toy, "pol", "label_eff_gross") == pytest.approx(5 / 30)
    assert val(toy, "pol", "label_eff_net") == pytest.approx(-16.5 / 30)
    assert np.isnan(val(toy, data.NEVER, "label_eff_net"))  # no labels paid


def test_paired_bootstrap_difference_is_exact_on_constant_gap(toy):
    ec = M.episode_components(toy)
    b = M.bootstrap_dataset(ec, "s", ["pol", data.NEVER], nboot=50)
    diff = b["harm_all"]["boot"][0] - b["harm_all"]["boot"][1]
    # never_switch harm is identically 0, so the difference equals pol's own harm draws
    assert np.allclose(diff, b["harm_all"]["boot"][0])


def test_matrix_bootstrap_matches_manual():
    x = np.array([-1.0, -2.0, -3.0, 0.5])
    u = matrix.upper(x, np.random.default_rng(0))
    idx = np.random.default_rng(0).integers(0, 4, (2000, 4))
    assert u == pytest.approx(np.quantile(x[idx].mean(1), 0.95))
