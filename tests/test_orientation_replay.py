from __future__ import annotations

import numpy as np
import pytest

from shiftlab.dive.eprocess import PredictableBoundMeanEProcess
from shiftlab.dive.gated_monitor_comparison import replay_gated
from shiftlab.dive.orientation_replay import ARMS, _scalar_ungated_ht, replay_batch

EPS, ALPHA = 0.1, 0.05


def _path(rng, n, rate, random_tariffs, strong=False):
    active = rng.random(n) < rate
    if strong:
        z = np.where(active, 5.0, 0.0)
    else:
        z = np.where(active, rng.choice([-5.0, -1.0, 0.0, 1.0, 5.0], size=n), 0.0)
    tariffs = rng.uniform(0.5, 2.5, n) if random_tariffs else np.ones(n)
    vn = 400
    v_active = rng.random(vn) < rate
    v_tariffs = rng.uniform(0.5, 2.5, vn) if random_tariffs else np.ones(vn)
    return z, active, tariffs, v_active, v_tariffs


def _scalar_full(z, signs, eps=EPS, alpha=ALPHA, cost_bound=5.0):
    process = PredictableBoundMeanEProcess(alpha=alpha)
    logs = [process.update(float(s * c) - eps, bound=cost_bound + eps) for s, c in zip(signs, z)]
    logs = np.asarray(logs)
    hits = np.flatnonzero(logs >= -np.log(alpha))
    return (int(hits[0]) if len(hits) else -1), 0, 0.0, len(z), float(logs.max())


def _scalar(arm, z, active, tariffs, v_active, v_tariffs, signs, coins, rate):
    if arm == "full_feedback":
        return _scalar_full(z, signs)
    if arm == "ungated_ht":
        return _scalar_ungated_ht(
            paired_cost=signs * z,
            tariffs=tariffs,
            uniforms=coins,
            validation_tariffs=v_tariffs,
            budget_rate=rate,
        )
    out = replay_gated(
        arm=arm,
        x=np.zeros((len(z), 1)),
        paired_cost=signs * z,
        disagreement=active,
        tariffs=tariffs,
        uniforms=coins,
        validation_disagreement=v_active,
        validation_tariffs=v_tariffs,
        budget_rate=rate,
    )
    return (
        -1 if out.first_alarm is None else out.first_alarm,
        int(out.queried.sum()),
        out.dollars,
        len(out.increments),
        float(out.log_e.max()),
    )


def _compare(arm, path, rate, signs, coins):
    z, active, tariffs, v_active, v_tariffs = path
    batch = replay_batch(
        arm,
        paired_cost=z,
        disagreement=active,
        tariffs=tariffs,
        signs=signs,
        uniforms=coins,
        validation_disagreement=v_active,
        validation_tariffs=v_tariffs,
        budget_rate=rate,
    )
    reps = coins.shape[0]
    for r in range(reps):
        s = np.ones(len(z)) if signs is None else signs[r]
        first, labels, dollars, processed, top = _scalar(
            arm, z, active, tariffs, v_active, v_tariffs, s, coins[r], rate
        )
        assert batch.first_alarm[r] == first
        assert batch.labels[r] == labels
        assert batch.processed[r] == processed
        assert batch.dollars[r] == pytest.approx(dollars, abs=1e-9)
        assert batch.max_log_e[r] == pytest.approx(top, abs=1e-9)
    return batch


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("random_tariffs", [False, True])
@pytest.mark.parametrize("rate", [0.1, 0.5, 1.0])
def test_matches_scalar_references(arm, random_tariffs, rate):
    rng = np.random.default_rng(hash((arm, random_tariffs, rate)) % 2**32)
    n = int(rng.integers(300, 600))
    path = _path(rng, n, float(rng.uniform(0.1, 0.4)), random_tariffs)
    signs = rng.choice([-1.0, 1.0], size=(5, n))
    coins = rng.random((5, n))
    _compare(arm, path, rate, signs, coins)


def test_reserve_stop_triggers_and_matches():
    rng = np.random.default_rng(3)
    n = 500
    path = _path(rng, n, 0.4, True)
    signs = rng.choice([-1.0, 1.0], size=(5, n))
    coins = rng.random((5, n))
    for arm in ("ungated_ht", "gated_ht_fixed", "gated_ht_paced", "gated_eb_paced"):
        batch = _compare(arm, path, 0.02, signs, coins)
        assert np.any(batch.processed < n)


@pytest.mark.parametrize("arm", ARMS)
def test_alarm_case_unsigned_stream(arm):
    rng = np.random.default_rng(11)
    n = 500
    path = _path(rng, n, 0.3, True, strong=True)
    coins = rng.random((4, n))
    batch = _compare(arm, path, 1.0, None, coins)
    if arm == "full_feedback":
        assert np.all(batch.first_alarm >= 0)
    else:
        assert np.any(batch.first_alarm >= 0)


def test_random_orientation_null_rate_on_harmful_path():
    rng = np.random.default_rng(5)
    n, reps = 400, 400
    z, active, tariffs, v_active, v_tariffs = _path(rng, n, 0.3, False, strong=True)
    batch = replay_batch(
        "full_feedback",
        paired_cost=z,
        disagreement=active,
        tariffs=tariffs,
        signs=rng.choice([-1.0, 1.0], size=(reps, n)),
        uniforms=rng.random((reps, n)),
        validation_disagreement=v_active,
        validation_tariffs=v_tariffs,
        budget_rate=1.0,
    )
    assert np.mean(batch.first_alarm >= 0) <= 0.10


def _kwargs(rng, n=50):
    z, active, tariffs, v_active, v_tariffs = _path(rng, n, 0.3, True)
    return {
        "paired_cost": z,
        "disagreement": active,
        "tariffs": tariffs,
        "signs": rng.choice([-1.0, 1.0], size=(2, n)),
        "uniforms": rng.random((2, n)),
        "validation_disagreement": v_active,
        "validation_tariffs": v_tariffs,
        "budget_rate": 0.5,
    }


def test_input_validation():
    rng = np.random.default_rng(0)
    base = _kwargs(rng)
    n = 50

    def bad(**changes):
        with pytest.raises(ValueError):
            replay_batch(changes.pop("arm", "gated_ht_paced"), **{**base, **changes})

    bad(arm="nope")
    bad(device="cuda")
    bad(tariffs=np.full(n, 3.0))
    bad(tariffs=np.full(n, np.nan))
    bad(paired_cost=np.full(n, 6.0))
    bad(paired_cost=np.where(base["disagreement"], 1.0, 0.5))
    bad(uniforms=np.ones((2, n)))
    bad(uniforms=np.random.default_rng(1).random((2, n + 1)))
    bad(uniforms=np.random.default_rng(1).random((3, n)))
    bad(signs=np.full((2, n), 0.5))
    bad(budget_rate=0.0)
    bad(cost_bound=4.0)
    bad(validation_tariffs=np.full(10, 9.0))
    bad(disagreement=np.ones(n + 1, dtype=bool))
