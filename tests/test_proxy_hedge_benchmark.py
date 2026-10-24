from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive.proxy_hedge_benchmark import (
    ProxyHedgeBenchmarkConfig,
    _run_stream,
)


def test_cpu_stream_smoke_has_common_queries_budget_and_valid_hedge_updates():
    config = ProxyHedgeBenchmarkConfig(
        n=1200,
        d=4,
        seeds=1,
        seed_offset=20401024,
        query_rate=0.2,
        device="cpu",
        scenario_subset=("stationary", "boundary_local_harm"),
    )
    scenario = next(value for value in SCENARIOS if value.name == "boundary_local_harm")
    rows = _run_stream(scenario, config.seed_offset, config)
    assert {row["method"] for row in rows} == {
        "zero",
        "ridge",
        "forest",
        "risk_model",
        "validation_best",
        "prequential_hedge",
    }
    assert len({row["labels_queried"] for row in rows}) == 1
    assert len({row["events_processed"] for row in rows}) == 1
    assert len({row["realized_label_spend"] for row in rows}) == 1
    assert all(row["budget_respected"] for row in rows)
    hedge = next(row for row in rows if row["method"] == "prequential_hedge")
    assert hedge["hedge_updates"] == hedge["labels_queried"]


def test_proxy_training_and_validation_fractions_keep_disjoint_slices():
    config = ProxyHedgeBenchmarkConfig(
        n=1600,
        d=4,
        device="cpu",
        train_fraction=0.20,
        validation_fraction=0.20,
        scenario_subset=("boundary_local_harm",),
    ).validate()
    scenario = next(value for value in SCENARIOS if value.name == "boundary_local_harm")
    rows = _run_stream(scenario, config.seed_offset, config)
    assert {row["events_processed"] for row in rows} == {800}


def test_proxy_training_and_validation_fractions_reject_overlap():
    config = ProxyHedgeBenchmarkConfig(
        n=1600,
        d=4,
        device="cpu",
        train_fraction=0.6,
        validation_fraction=0.4,
        scenario_subset=("boundary_local_harm",),
    )
    try:
        config.validate()
    except ValueError as exc:
        assert "sum to less than one" in str(exc)
    else:
        raise AssertionError("overlapping training/validation design was accepted")
