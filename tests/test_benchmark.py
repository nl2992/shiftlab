import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from shiftlab.benchmark import run
from shiftlab.core.config import Config, load_config
from shiftlab.diagnostics import CUSUM, ks_test
from shiftlab.learner import Learner, decision_losses
from shiftlab.methods import (
    exponentially_weighted_conformal_quantile,
    weighted_conformal_quantile,
)
from shiftlab.streaming import Feedback, Observation, simulate
from shiftlab.synthetic import generate


def test_controls():
    c = Config()
    null = generate(c.model_copy(update={"shift": "none"}), 9)
    benign = generate(c.model_copy(update={"shift": "benign"}), 9)
    concept = generate(c, 9)
    variance = generate(c.model_copy(update={"shift": "variance"}), 9)
    assert np.array_equal(concept.y, generate(c, 9).y)
    assert not null.regime.any()
    assert np.array_equal(null.y, benign.y)
    assert np.array_equal(null.X, concept.X)
    assert np.array_equal(null.y[: c.change_at], concept.y[: c.change_at])
    assert concept.regime[c.change_at - 1] == 0 and concept.regime[c.change_at] == 1
    assert np.all(variance.sigma[c.change_at :] == 0.3 * (1 + c.strength))


def test_delay_and_visibility():
    class Spy:
        def __init__(self):
            self.now = -1
            self.received = []

        def predict(self, obs):
            assert not hasattr(obs, "target") and not hasattr(obs, "regime")
            self.now = obs.time
            return 0.0, 1.0

        def observe(self, feedback):
            assert feedback.available_at == self.now
            assert feedback.time + 2 == self.now
            self.received.append(feedback.time)

    spy = Spy()
    simulate(np.zeros((8, 2)), np.arange(8), spy, 0, delay=2)
    assert spy.received == list(range(6))
    spy = Spy()
    simulate(np.zeros((8, 2)), np.arange(8), spy, 0, delay=2, missing=1.0)
    assert not spy.received


def test_quantile_and_cost():
    assert np.isinf(weighted_conformal_quantile([1, 2], 0.1))
    assert weighted_conformal_quantile(np.arange(1, 10), 0.2) == 8
    assert decision_losses(np.array([1, -1]), np.array([-1, 1])).tolist() == [5, 1]


def test_radius_updates_are_decoupled_from_predictor_update_method():
    X = np.arange(80, dtype=float).reshape(40, 2)
    y = np.zeros(40)
    settings = SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=10, budget=2)
    frozen = Learner(X[:20], y[:20], X[20:], y[20:], settings, "frozen", "fixed")
    rolling = Learner(X[:20], y[:20], X[20:], y[20:], settings, "frozen", "rolling")
    for now in (50, 51):
        feedback = Feedback(
            time=now - 1,
            available_at=now,
            features=tuple(X[0]),
            target=100.0,
            prediction=0.0,
        )
        frozen.observe(feedback)
        rolling.observe(feedback)
    _, fixed_radius = frozen.predict(Observation(52, tuple(X[1])))
    _, rolling_radius = rolling.predict(Observation(52, tuple(X[1])))
    assert fixed_radius == 0
    assert rolling_radius == 100
    assert frozen.interventions == rolling.interventions == []


def test_default_radius_mode_preserves_legacy_rolling_behavior():
    X = np.arange(80, dtype=float).reshape(40, 2)
    y = np.zeros(40)
    settings = SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=10, budget=2)
    rolling = Learner(X[:20], y[:20], X[20:], y[20:], settings, "rolling")
    fixed = Learner(X[:20], y[:20], X[20:], y[20:], settings, "frozen")
    assert rolling.radius_method == "rolling"
    assert fixed.radius_method == "fixed"


def test_triggered_recalibration_uses_arrived_residual_without_refitting():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=10, budget=2)
    learner = Learner(X[:20], y[:20], X[20:], y[20:], settings, "recalibration")
    training_seconds = learner.training_seconds
    learner.error_detector.update = lambda _: True
    learner.observe(
        Feedback(time=20, available_at=21, features=(0.0, 0.0), target=8.0, prediction=0.0)
    )
    prediction, _ = learner.predict(Observation(22, (0.0, 0.0)))
    assert prediction == 8.0
    assert learner.training_seconds == training_seconds
    assert learner.interventions == [21]
    assert learner.intervention_audit == [
        {
            "available_at": 21,
            "arrived_feedback_count": 1,
            "method": "recalibration",
            "action": "residual_bias_recalibration",
            "resource_cost": 1.0,
            "resource_spent": 1.0,
            "bias_correction": 8.0,
        }
    ]


def test_periodic_recalibration_uses_only_arrived_residuals():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=2, budget=2)
    learner = Learner(X[:20], y[:20], X[20:], y[20:], settings, "periodic_recalibration")
    for index, target in enumerate((4.0, 6.0), start=1):
        learner.observe(
            Feedback(
                time=20 + index,
                available_at=20 + index,
                features=(0.0, 0.0),
                target=target,
                prediction=0.0,
            )
        )
    assert learner.bias_correction == 5.0
    assert learner.intervention_audit[-1]["action"] == "residual_bias_recalibration"


def test_triggered_partial_update_changes_parameters_without_refitting():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=10, budget=2)
    learner = Learner(X[:20], y[:20], X[20:], y[20:], settings, "partial_update")
    training_seconds = learner.training_seconds
    learner.error_detector.update = lambda _: True
    learner.observe(
        Feedback(time=20, available_at=21, features=(1.0, 0.0), target=8.0, prediction=0.0)
    )
    assert learner.training_seconds == training_seconds
    assert learner.model.coef_[0] == pytest.approx(0.4)
    assert learner.model.intercept_ == pytest.approx(0.4)
    assert learner.intervention_audit[-1]["action"] == "normalized_sgd_partial_update"


def test_resource_budget_rejects_an_action_atomically():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=10, budget=2)
    learner = Learner(
        X[:20],
        y[:20],
        X[20:],
        y[20:],
        settings,
        "partial_update",
        resource_budget=1.0,
    )
    before = learner.model.coef_.copy()
    learner.error_detector.update = lambda _: True
    learner.observe(
        Feedback(time=20, available_at=21, features=(1.0, 0.0), target=8.0, prediction=0.0)
    )
    np.testing.assert_array_equal(learner.model.coef_, before)
    assert learner.interventions == []
    assert learner.resource_spent == 0


def test_validation_loss_trigger_uses_pretest_threshold_and_arrived_feedback():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=2, alpha=0.1, threshold=5.0, period=10, budget=1)
    learner = Learner(
        X[:20],
        y[:20],
        X[20:30],
        y[20:30],
        settings,
        "validation_triggered",
        validation_X=X[30:],
        validation_y=y[30:],
    )
    assert learner.validation_loss_threshold == 0.0
    learner.error_detector.update = lambda _: False
    for time in (40, 41):
        learner.observe(
            Feedback(
                time=time - 1, available_at=time, features=(0.0, 0.0), target=9.0, prediction=0.0
            )
        )
    assert learner.interventions == [41]
    assert learner.intervention_audit[-1]["action"] == "refit"
    assert learner.alarms["validation_loss"] == [41]


def test_validation_trigger_requires_a_separate_pretest_validation_set():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=2, alpha=0.1, threshold=5.0, period=10, budget=1)
    with pytest.raises(ValueError, match="validation_X and validation_y"):
        Learner(X[:20], y[:20], X[20:30], y[20:30], settings, "validation_triggered")


def test_exponential_conformal_quantile_downweights_stale_scores():
    scores = np.array([1.0] * 14 + [100.0])
    ordinary = weighted_conformal_quantile(scores, alpha=0.1)
    recent = exponentially_weighted_conformal_quantile(
        scores, [0.0] * 14 + [10.0], alpha=0.1, half_life=10
    )
    assert ordinary == 100
    assert recent == 1


def test_exponential_radius_excludes_feedback_at_the_request_timestamp():
    X = np.zeros((40, 2))
    y = np.zeros(40)
    settings = SimpleNamespace(window=40, alpha=0.1, threshold=5.0, period=10, budget=2)
    learner = Learner(
        X[:20],
        y[:20],
        X[20:],
        y[20:],
        settings,
        "frozen",
        "exponential",
        cal_score_times=np.full(20, 19.0),
        radius_half_life=10,
    )
    for _ in range(3):
        learner.observe(
            Feedback(time=19, available_at=20, features=(0.0, 0.0), target=100.0, prediction=0.0)
        )
    _, radius = learner.predict(Observation(20, (0.0, 0.0)))
    assert radius == 0


def test_config():
    with pytest.raises(ValidationError):
        Config(train_end=700)
    with pytest.raises(ValidationError):
        Config(unknown=1)
    assert load_config("configs/experiments/diagnostics.yaml").paper == 1


def test_detectors_replicated():
    null, shifted = [], []
    for seed in range(40):
        rng = np.random.default_rng(seed)
        a, b = rng.normal(size=(2, 150))
        null.append(ks_test(a, b) < 0.05)
        shifted.append(ks_test(a, b + 1) < 0.05)
    assert np.mean(null) < 0.2
    assert np.mean(shifted) > 0.9
    detector = CUSUM(0, 1, 5)
    assert not any(detector.update(0) for _ in range(20))
    assert any(detector.update(3) for _ in range(20))


@pytest.mark.parametrize("paper", [1, 2, 3])
def test_end_to_end(tmp_path, paper):
    c = Config(
        paper=paper,
        n=220,
        train_end=40,
        calibration_end=80,
        change_at=140,
        window=20,
        seeds=[9],
        output=str(tmp_path),
        period=25,
        budget=2,
    )
    a, b = run(c), run(c)
    x, y = pd.read_csv(a / "metrics.csv"), pd.read_csv(b / "metrics.csv")
    pd.testing.assert_frame_equal(
        x.drop(columns=["training_seconds", "inference_seconds"]),
        y.drop(columns=["training_seconds", "inference_seconds"]),
    )
    assert (x.adaptation_cost == x.num_interventions * c.retrain_cost).all()
    assert (x.num_interventions <= 2).all()
    assert json.loads((a / "metadata.json").read_text())["status"] == "complete"
    for checkpoint in a.glob("model-*.npz"):
        with np.load(checkpoint) as saved:
            assert saved["coef"].shape == (4,)
    assert (a / "summary.png").exists()


def test_future_targets_cannot_change_past_predictions():
    from shiftlab.learner import Learner

    c = Config(n=220, train_end=40, calibration_end=80, change_at=140, window=20)
    stream = generate(c, 7)
    outputs = []
    for perturb in [False, True]:
        targets = stream.y.copy()
        if perturb:
            targets[150:] += 100
        learner = Learner(
            stream.X[:40], targets[:40], stream.X[40:80], targets[40:80], c, "rolling"
        )
        assert not hasattr(learner.config, "change_at")
        assert not hasattr(learner.config, "shift")
        outputs.append(simulate(stream.X, targets, learner, 80, delay=3, seed=1))
    for left, right in zip(outputs[0], outputs[1]):
        if left["time"] <= 153:
            assert left["prediction"] == right["prediction"]
            assert left["radius"] == right["radius"]


def test_empirical_dgp_moments():
    c = Config(n=12000, change_at=6000)
    means = []
    variances = []
    for seed in range(5):
        benign = generate(c.model_copy(update={"shift": "benign"}), seed)
        variance = generate(c.model_copy(update={"shift": "variance"}), seed)
        means.append(benign.X[6000:, 3].mean() - benign.X[:6000, 3].mean())
        residual = variance.y - variance.mean
        variances.append(np.var(residual[6000:]) / np.var(residual[:6000]))
    assert abs(np.mean(means) - c.strength) < 0.05
    assert abs(np.mean(variances) - (1 + c.strength) ** 2) < 0.3
