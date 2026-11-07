import numpy as np
from fam_e import HOSTS
from simulator import run_episode

from scripts.sota_sprint.wp1_clock_ablation import TimestampIndexedRMM, TimestampStartMixture


def test_timestamp_start_mixture_activates_starts_by_elapsed_time():
    det = TimestampStartMixture(
        alpha=0.05, max_labels=20, cycle_start=0, episode_end=100, gap=10, lambdas=(0.5,)
    )
    assert det.starts == [0, 50]
    det.update(+1, 0)
    assert len(det.products) == 1
    det.update(-1, 49)
    assert len(det.products) == 1
    det.update(+1, 50)
    assert len(det.products) == 2


def test_timestamp_indexed_rmm_replays_and_respects_budget():
    T, B = 200, 30
    losses = np.zeros((T, 2), dtype=np.int8)
    losses[20:120, 1] = 1
    labels = np.random.default_rng(11).integers(0, 2, T)
    predictions = labels[:, None] ^ losses
    timestamps = np.arange(T, dtype=np.int64) * 60_000_000_000
    make_base, _ = HOSTS["gated_deployment"]
    policy = TimestampIndexedRMM(
        make_base,
        T,
        B,
        0.05,
        rng=np.random.default_rng(7),
        episode_end=int(timestamps[-1]),
        name="clock_test",
    )
    result = run_episode(
        policy,
        model_predictions=predictions,
        labels=labels,
        contexts=timestamps,
        delay=2,
        budget=B,
        label_price=0.05,
        switch_cost=5.0,
        trace=True,
    )
    assert result.requested_labels <= B
    assert result.net_cost >= 0
