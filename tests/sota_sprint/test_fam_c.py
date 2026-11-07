"""Family C unit tests: budget, issue-time propensities, exact host reproduction, null promotion."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import screen  # noqa: E402  (sets up all paths)
from bench import parse_regime  # noqa: E402
from simulator import check_budget_feasible, check_no_future_access, run_episode  # noqa: E402
from suite import stream_from_losses  # noqa: E402

import fam_c  # noqa: E402

CANDS = ["C1", "C2", "C3", "C4", "C5", "C6", "C6@discern", "gated_adaptive_range+pace_tuned",
         "discern_design_floor+pace_tuned"]


def _make(name, T=2000, B=200, delay=100, seed=0):
    from simulator import policy_rng

    return fam_c.EXTRA[name](T, B, 5.0, 0.05, 0.05, delay, lambda nm: policy_rng(7, seed, nm))


def _stream(regime, seed):
    R, _ = parse_regime(regime)
    losses = R.sample(np.random.default_rng(seed))
    preds, labels = stream_from_losses(losses, np.random.default_rng(seed + 1))
    return preds, labels, R.delay


@pytest.mark.parametrize("name", CANDS)
@pytest.mark.parametrize("budget", [30, 200])
def test_budget_respected(name, budget):
    preds, labels, delay = _stream("F9_highdis_better", 3)
    pol = _make(name, B=budget, delay=delay)
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                      label_price=0.05, switch_cost=5.0)
    assert res.requested_labels <= budget
    assert not check_budget_feasible(res, budget)
    assert not check_no_future_access(res, delay)


@pytest.mark.parametrize("name", ["C1", "C2", "C5", "C6", "gated_adaptive_range+pace_tuned",
                                  "C4", "C6@discern"])
def test_issue_time_propensity_used(name):
    """The CS ingests w = 1/q_issue for every queried event; gated also uses wmax = 1/q_issue."""
    preds, labels, delay = _stream("F0_better", 5)
    pol = _make(name, delay=delay)
    seen = []
    orig = pol._ingest

    def spy(w, d, ref):
        wm = getattr(pol, "_wmax", {}).get(ref)
        seen.append((ref, w, wm))
        orig(w, d, ref)

    pol._ingest = spy
    run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=200,
                label_price=0.05, switch_cost=5.0)
    queried = [(ref, w, wm) for ref, w, wm in seen if ref in pol.c_issue_q]
    assert queried, "no queried increment was ingested"
    for ref, w, wm in queried:
        q = pol.c_issue_q[ref]
        assert w == pytest.approx(1.0 / q)
        if wm is not None:
            assert wm == pytest.approx(max(1.0 / q, 2.0))
        if isinstance(pol, fam_c.DiscernC):
            assert q >= pol.p_min - 1e-12


@pytest.mark.parametrize("mine,host", [("Cchk:gated_front", "gated_adaptive_range+front"),
                                       ("Cchk:gated_uniform", "gated_adaptive_range"),
                                       ("Cchk:discern_uniform", "discern_design_floor")])
def test_controller_reproduces_host(mine, host):
    from registry import EXTRA

    preds, labels, delay = _stream("F0_better", 11)
    out = []
    for nm in (mine, host):
        pol = EXTRA[nm](2000, 200, 5.0, 0.05, 0.05, delay,
                        lambda x: __import__("simulator").policy_rng(3, 0, x))
        res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=200,
                          label_price=0.05, switch_cost=5.0)
        out.append((res.net_cost, res.requested_labels,
                    [r["deployed_model"] for r in res.records]))
    assert out[0] == out[1]


@pytest.mark.parametrize("name", ["C2", "C5", "C6", "C3", "C4"])
def test_null_promotion_small(name):
    rows = []
    for s in range(25):
        rows += screen._job(("synthetic", "F0_null", 0, s, 99_000_001, [name]))
    rate = np.mean([r["ever_promote"] for r in rows])
    assert rate <= 0.12, rate


def test_skip_actions_declared():
    g, d = _make("C2"), _make("C6@discern")
    assert g.c_skip(None, 0.0) == (0.0, 1.0)  # gated: unrecorded
    assert d.c_skip(None, 0.0) == (1.0, d.p_min)  # DISCERN: record at the design floor
