import torch

from scripts.calibrate_history_predictable_query_bounds import (
    HARM_SCENARIOS,
    generate_common_random_numbers,
)
from scripts.validate_delayed_history_predictable_bounds import (
    simulate_delayed_arm,
    simulate_delayed_arm_gpu_reference,
)


def test_delayed_history_bound_runner_reserves_budget_and_flushes_event_prefix():
    streams, horizon, seed, delay = 32, 80, 27199111, 7
    device = torch.device("cpu")
    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )

    fixed = simulate_delayed_arm(
        scenario=HARM_SCENARIOS[-1],
        streams=streams,
        horizon=horizon,
        seed=seed,
        data=data,
        device=device,
        delay=delay,
        bound_mode="fixed",
    )
    predictable = simulate_delayed_arm(
        scenario=HARM_SCENARIOS[-1],
        streams=streams,
        horizon=horizon,
        seed=seed,
        data=data,
        device=device,
        delay=delay,
        bound_mode="predictable",
    )

    assert len(fixed) == len(predictable) == streams
    for arm in (fixed, predictable):
        assert all(row["budget_respected"] for row in arm)
        assert all(row["labels_queried"] <= row["hard_label_budget"] for row in arm)
        assert all(row["events_processed"] <= horizon for row in arm)
        for row in arm:
            event = row["first_alarm_event"]
            wall = row["first_alarm_wall_time"]
            if event is not None:
                assert wall is not None
                assert event <= wall <= event + delay


def test_delayed_runner_uses_registered_eventwise_bound_and_reports_null_alarms():
    streams, horizon, seed = 32, 100, 27199112
    device = torch.device("cpu")
    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    rows = simulate_delayed_arm(
        scenario="mixed_sign_exact_marginal_null",
        streams=streams,
        horizon=horizon,
        seed=seed,
        data=data,
        device=device,
        delay=5,
        bound_mode="predictable",
    )
    assert len(rows) == streams
    assert all(row["bound_mode"] == "predictable" for row in rows)
    assert all(row["false_escalation"] == (row["first_alarm_event"] is not None) for row in rows)
    assert all(row["budget_respected"] for row in rows)


def test_numpy_runner_matches_torch_event_order_reference():
    streams, horizon, seed, delay = 8, 80, 27199113, 5
    device = torch.device("cpu")
    data = generate_common_random_numbers(
        streams=streams, horizon=horizon, seed=seed, device=device
    )
    for scenario, bound_mode in (
        ("mixed_sign_exact_marginal_null", "fixed"),
        (HARM_SCENARIOS[-1], "predictable"),
    ):
        args = {
            "scenario": scenario,
            "streams": streams,
            "horizon": horizon,
            "seed": seed,
            "data": data,
            "device": device,
            "delay": delay,
            "bound_mode": bound_mode,
        }
        fast = simulate_delayed_arm(**args)
        reference = simulate_delayed_arm_gpu_reference(**args)
        for fast_row, reference_row in zip(fast, reference, strict=True):
            for key in (
                "events_processed",
                "labels_queried",
                "first_alarm_event",
                "first_alarm_wall_time",
                "false_escalation",
                "post_onset_detection",
            ):
                assert fast_row[key] == reference_row[key]
