import numpy as np

from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.streaming import Request, replay
from shiftlab.data.synthetic import generate_chunks


def test_small_covariate_movement_changes_optimal_decisions():
    frame, oracle = next(
        generate_chunks(SyntheticConfig(n=10000, scenario="small_decision_covariate"))
    )
    X = np.stack(frame.features)
    assert 0.018 < X[5000:, 0].mean() - X[:5000, 0].mean() < 0.022
    assert oracle.oracle_action.iloc[:5000].mean() < 0.04
    assert oracle.oracle_action.iloc[5000:].mean() > 0.96
    from scipy.special import expit

    assert np.allclose(oracle.probability_positive, expit(200 * X[:, 0]))


def test_rare_high_cost_change_is_decision_relevant_with_tiny_brier_change():
    _, oracle = next(generate_chunks(SyntheticConfig(n=1000, scenario="rare_high_cost")))
    p = oracle.probability_positive.to_numpy()
    # Risk of frozen probability=.0001 changes by only the squared mean error under Brier loss.
    assert ((p[500:] - 0.0001) ** 2).max() < 0.0001
    assert oracle.oracle_action.iloc[:500].eq(False).all()
    assert oracle.oracle_action.iloc[500:].eq(True).all()
    frozen_decision_risk = 1000 * p[500:]
    assert np.min(frozen_decision_risk - oracle.oracle_risk.iloc[500:]) > 4


def test_generated_worlds_are_indistinguishable_without_labels():
    streams = []
    for severity in [0, 1]:
        frame, oracle = next(
            generate_chunks(
                SyntheticConfig(n=100, scenario="rare_high_cost", severity=severity, missing=1)
            )
        )
        events = list(replay(frame))
        assert all(isinstance(event, Request) for event in events)
        streams.append((events, oracle))
    assert streams[0][0] == streams[1][0]
    assert not np.array_equal(streams[0][1].oracle_action, streams[1][1].oracle_action)


def test_two_dimensional_irrelevant_control_has_a_true_nuisance_feature():
    frame, oracle = next(generate_chunks(SyntheticConfig(n=1000, d=2, scenario="irrelevant")))
    X = np.stack(frame.features)
    assert np.allclose(oracle.conditional_mean, X[:, 0])
