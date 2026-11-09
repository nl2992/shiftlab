"""Parity and sanity tests for paper_ports.py.

What the parity tests establish (and what they do not). They compare formulas transcribed from the
published papers (paper_ports.py) against the repository's earlier ports, which were written from
the authors' code. Agreement is a PAPER-vs-CODE-PORT cross-check (tier T2). It is not a run of the
authors' own code (tier T1): that needs a download of third-party code and its execution, which
was not done in this workstream. See 05_BASELINE_FIDELITY.md section 4.

Run: python -m pytest scripts/paper1_scale25/baselines/test_paper_ports.py -q
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paper_ports as pp
from cams import learning_rate as repo_cams_rate
from cams import weighted_entropy_query as repo_cams_E
from model_picker import ModelPickerNative
from model_picker import eta_t as repo_eta
from model_picker import posterior as repo_post
from model_picker import query_probability as repo_q
from simulator import run_episode


@pytest.mark.parametrize("k,C", [(2, 2), (5, 2), (4, 4), (8, 3)])
def test_model_picker_formulas_match_repo_port(k, C):
    rng = np.random.default_rng(k * 10 + C)
    for t in (1, 2, 17, 500, 1999):
        L = rng.uniform(0, 40, k) * rng.integers(0, 2, k)
        preds = rng.integers(0, C, k)
        eta = pp.mp_eta(k, t)
        assert eta == pytest.approx(repo_eta(k, t), rel=1e-12)
        w = pp.mp_weights(L, eta)
        assert np.allclose(w, repo_post(L, eta), atol=1e-12)
        assert pp.mp_q(w, preds, C, eta) == pytest.approx(repo_q(w, preds, 1.0, C, eta), abs=1e-12)


def test_model_picker_closed_form_toy():
    """Hand-computed: k=2, preds (0,1), uniform w. l^0=(0,1), l^1=(1,0) -> v = .25, eta_1 = sqrt(ln2/2)."""
    w = np.array([0.5, 0.5])
    preds = np.array([0, 1])
    assert pp.mp_v(w, preds, 2) == pytest.approx(0.25)
    assert pp.mp_eta(2, 1) == pytest.approx(math.sqrt(math.log(2) / 2))
    assert pp.mp_q(w, preds, 2, pp.mp_eta(2, 1)) == pytest.approx(
        math.sqrt(math.log(2) / 2)
    )  # floor binds
    assert pp.mp_q(w, np.array([1, 1]), 2, 0.5) == 0.0  # agreement region


def test_model_picker_native_trajectory_replay():
    """Replay the repo's native run with the same query indicators through the paper formulas."""
    rng = np.random.default_rng(3)
    n, k, C = 300, 4, 3
    preds = rng.integers(0, C, (n, k))
    oracle = rng.integers(0, C, n)
    out = ModelPickerNative(k, C).run(preds, oracle, budget=10**9, rng=np.random.default_rng(5))
    L = np.zeros(k)
    for t in range(1, n + 1):
        eta = pp.mp_eta(k, t)
        w = pp.mp_weights(L, eta)
        assert np.allclose(w, out["posterior_log"][t - 1], atol=1e-12)
        q = pp.mp_q(w, preds[t - 1], C, eta)
        assert q == pytest.approx(out["u_log"][t - 1], abs=1e-12)
        if out["z_t_log"][t - 1]:
            L = L + (preds[t - 1] != oracle[t - 1]) / q
    assert np.allclose(L, out["final_loss"], atol=1e-9)


def test_model_picker_identifies_best_on_easy_stochastic_stream():
    """Theorem-level sanity (not a proof): the recommendation is the best model w.h.p."""
    hits = 0
    for s in range(20):
        r = np.random.default_rng(s)
        T, acc = 1500, np.array([0.7, 0.8, 0.9, 0.75])
        labels = r.integers(0, 2, T)
        preds = np.where(r.random((T, 4)) < acc, labels[:, None], 1 - labels[:, None])
        pol = pp.ModelPickerPaper(4, 2, np.random.default_rng(100 + s))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=1,
            budget=10**9,
            label_price=0.0,
            switch_cost=0.0,
        )
        hits += int(np.argmin(pol.state_dict()["L"]) == 2)
        assert res.requested_labels <= T
    assert hits >= 17


def test_cams_E_matches_repo_for_two_classes():
    rng = np.random.default_rng(0)
    for _ in range(50):
        w = rng.dirichlet(np.ones(2))
        preds = np.array([0, 1])
        assert pp.cams_E(w, preds, 2) == pytest.approx(repo_cams_E(2, w, preds), abs=1e-5)
    assert pp.cams_E(np.array([0.5, 0.5]), np.array([0, 1]), 2) == pytest.approx(0.5)


def test_cams_documented_gaps_paper_vs_code():
    """These are DIFFERENCES the audit reports; asserting them keeps the report honest."""
    # (a) learning rate: paper sqrt(ln m / t) vs author code sqrt(m / t)
    assert pp.cams_eta(2, 100) == pytest.approx(math.sqrt(math.log(2) / 100))
    assert repo_cams_rate(2, 100) == pytest.approx(math.sqrt(2 / 100))
    assert repo_cams_rate(2, 100) / pp.cams_eta(2, 100) == pytest.approx(math.sqrt(2 / math.log(2)))
    # (b) near-zero posterior mass: code rounds to 6 decimals and returns 0, paper keeps E > 0
    w = np.array([1 - 1e-8, 1e-8])
    preds = np.array([0, 1])
    assert repo_cams_E(2, w, preds) == 0.0
    assert pp.cams_E(w, preds, 2) > 0.0


def _stream(T=400, seed=0):
    r = np.random.default_rng(seed)
    labels = r.integers(0, 2, T)
    l0 = (r.random(T) < 0.25).astype(int)
    l1 = (r.random(T) < 0.15).astype(int)
    preds = np.stack([labels ^ l0, labels ^ l1], 1)
    return preds, labels


@pytest.mark.parametrize(
    "make",
    [
        lambda r: pp.ModelPickerPaper(2, 2, r, "recommend"),
        lambda r: pp.ModelPickerPaper(2, 2, r, "sample"),
        lambda r: pp.CAMSPaper(2, 2, r, False),
        lambda r: pp.CAMSPaper(2, 2, r, True),
    ],
)
def test_policies_run_in_simulator_with_hard_cap_and_delay(make):
    preds, labels = _stream()
    pol = make(np.random.default_rng(1))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=20,
        budget=30,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert res.requested_labels <= 30
    assert all(r["release_time"] - r["request_time"] == 20 for r in res.records if r["requested"])


def test_cutoff_wrapper_inert_when_h_negative_and_blocks_late_purchases():
    preds, labels = _stream(T=600)
    kw = {
        "model_predictions": preds,
        "labels": labels,
        "delay": 20,
        "budget": 200,
        "label_price": 0.05,
        "switch_cost": 5.0,
    }
    base = run_episode(pp.CAMSPaper(2, 2, np.random.default_rng(2), False), **kw)
    inert = run_episode(
        pp.CutoffWrapper(pp.CAMSPaper(2, 2, np.random.default_rng(2), False), 600, 20, H=-(10**9)),
        **kw,
    )
    assert [r["requested"] for r in base.records] == [r["requested"] for r in inert.records]
    cut = run_episode(
        pp.CutoffWrapper(pp.CAMSPaper(2, 2, np.random.default_rng(2), False), 600, 20, H=300), **kw
    )
    late = [r for r in cut.records if r["requested"] and r["event_id"] + 20 > 600 - 300]
    assert not late
    assert cut.requested_labels < base.requested_labels or base.requested_labels == 0
