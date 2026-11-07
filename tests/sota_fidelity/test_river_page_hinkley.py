"""river Page-Hinkley adapter: detector reproduction (river docstring example) and adapter smoke."""
import random
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("river", reason="optional extra: uv run --extra drift")

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for p in (SOTA, SOTA / "competitors", ROOT / "scripts/failure_atlas_v2_flq"):
    sys.path.insert(0, str(p))

from regimes import REGIMES
from river.drift import PageHinkley
from river_page_hinkley import RiverPageHinkleyDeploymentAdapter
from simulator import check_budget_feasible, check_no_future_access, policy_rng, run_episode


def test_river_docstring_example_alarm_at_1006_value_5():
    # river docs stream; the independent checker's ports of river and skmultiflow both alarm at (1006, 5)
    rng = random.Random(12345)
    data = rng.choices([0, 1], k=1000) + rng.choices(range(4, 8), k=1000)
    ph, hits = PageHinkley(), []
    for i, v in enumerate(data):
        ph.update(v)
        if ph.drift_detected:
            hits.append((i, v))
    assert hits[0] == (1006, 5)


def _stream(losses, seed):
    r = np.random.default_rng(seed)
    labels = r.integers(0, 2, losses.shape[0])
    return labels[:, None].astype(int) ^ losses.astype(int), labels


def _run(regime, seed, **kw):
    T, delay, budget = 2000, 100, 200
    losses = REGIMES[regime].sample(np.random.default_rng(1000 + seed), T)
    preds, labels = _stream(losses, 500 + seed)
    pol = RiverPageHinkleyDeploymentAdapter(T, budget, rng=policy_rng(seed, 0, "ph"), **kw)
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                      label_price=0.05, switch_cost=5.0)
    return pol, res


def test_adapter_contract_determinism_and_defaults():
    pol, res = _run("F3_reversal_800", 0)
    assert pol.kw == {"min_instances": 30, "delta": 0.005, "threshold": 50.0, "alpha": 0.9999}
    assert check_budget_feasible(res, 200) == [] and check_no_future_access(res, 100) == []
    _, res2 = _run("F3_reversal_800", 0)
    assert [r["deployed_model"] for r in res.records] == [r["deployed_model"] for r in res2.records]


def test_ph_is_a_change_detector_not_a_sign_test():
    # challenger better from the first label: constant positive z, no change, no alarm (documented)
    assert all(_run("F0_better", s)[0].n_switches == 0 for s in range(3))
    # a primed null reference (declared extension) lets the same detector fire on a persistent gap
    assert sum(_run("F0_better", s, prime_null=30, threshold=5.0)[0].n_switches >= 1
               for s in range(3)) >= 2
