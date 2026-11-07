"""RMM detector: null false-alarm rate, detection of a late change, and wrapper budget safety."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/failure_atlas_v2"))
from regimes import REGIMES
from restart_monitor import FACTORIES, MixtureSRDetector
from suite import build_suite, run_metrics


def _alarm_rate(p, n_labels=200, reps=2000, alpha=0.05, seed=0):
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(reps):
        det = MixtureSRDetector(alpha, n_labels)
        x = np.where(rng.random(n_labels) < p, 1, -1)
        hits += any(det.update(int(v)) for v in x)
    return hits / reps


def test_null_false_alarm_below_alpha():
    assert _alarm_rate(0.5) <= 0.05 + 3 * np.sqrt(0.05 * 0.95 / 2000)


def test_detects_late_change():
    rng = np.random.default_rng(1)
    hits = 0
    for _ in range(300):
        det = MixtureSRDetector(0.05, 200)
        x = np.r_[np.where(rng.random(100) < 0.4, 1, -1), np.where(rng.random(100) < 0.75, 1, -1)]
        hits += any(det.update(int(v)) for v in x)
    assert hits / 300 > 0.8


def test_wrapper_respects_budget():
    R = REGIMES["F1_late_800"]
    L = R.sample(np.random.default_rng(3))
    for pol in build_suite(
        2000,
        200,
        5,
        0.05,
        0.05,
        R.delay,
        0,
        1,
        names=["gated_deployment+RMM", "SMCS+retain-incumbent+RMM"],
        extra=FACTORIES,
    ):
        m = run_metrics(
            pol,
            L,
            R.truth_gain(),
            delay=R.delay,
            budget=200,
            cq=0.05,
            cs=5,
            stream_rng=np.random.default_rng(2),
        )
        assert m["labels"] <= 200
