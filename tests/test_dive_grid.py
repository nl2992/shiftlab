import numpy as np
import pytest

from shiftlab.dive.allocation_grid import (
    AllocationGridConfig,
    _fit_allocation,
    run_allocation_grid,
    run_rate_stabilized_grid,
)


def test_neyman_power_minimizes_query_variance_at_fixed_budget():
    residual_second_moment = np.linspace(0.05, 3.0, 500)
    proxy = np.zeros_like(residual_second_moment)
    uncertainty = np.zeros_like(proxy)
    objectives = {}
    for power in (0.0, 0.25, 0.5, 0.75, 1.0):
        policy = _fit_allocation(
            power,
            0.2,
            1e-5,
            0.999,
            proxy,
            residual_second_moment,
        )
        probability = policy.probabilities(
            proxy=proxy,
            residual_second_moment=residual_second_moment,
            uncertainty=uncertainty,
        )
        assert probability.mean() == pytest.approx(0.2, abs=1e-8)
        objectives[power] = float(np.mean(residual_second_moment * (1 / probability - 1)))
    assert objectives[0.5] == pytest.approx(min(objectives.values()))


def test_allocation_grid_smoke_writes_forward_test_artifacts(tmp_path):
    config = AllocationGridConfig(
        n=1000,
        d=8,
        seeds=1,
        label_budgets=(0.1,),
        variance_powers=(0.0, 0.5, 1.0),
        device="cpu",
    )
    output = run_allocation_grid(config, tmp_path)
    assert output.is_file()
    report = (tmp_path / "reports/allocation_grid.md").read_text()
    assert "classical Neyman allocation" in report
    assert "95% Wilson" in report
    assert (tmp_path / "figures/allocation_grid.png").is_file()


def test_rate_stabilized_grid_records_theoretical_drift_bound(tmp_path):
    config = AllocationGridConfig(
        n=1000,
        d=8,
        seeds=1,
        label_budgets=(0.1,),
        rate_drift_tolerances=(0.0, 0.05),
        device="cpu",
    )
    output = run_rate_stabilized_grid(config, tmp_path)
    assert output.is_file()
    report = (tmp_path / "reports/rate_stabilized_grid.md").read_text(encoding="utf-8")
    assert "worst-case bound on expected query-rate drift" in report
    assert "hard realized label cap" in report
    assert "0.00 [0.00,0.79]" in report
    assert (tmp_path / "figures/rate_stabilized_grid.png").is_file()
