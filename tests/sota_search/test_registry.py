from __future__ import annotations

import sqlite3

import pytest

from shiftlab.sota_search.registry import Registry
from shiftlab.sota_search.supervisor import Limits, run_batch
from shiftlab.sota_search.smoke_worker import simulate


def test_registry_preserves_start_and_refuses_mutation(tmp_path):
    registry = Registry(tmp_path / "runs.sqlite")
    run_id, record = registry.start({"candidate_algorithm": "test", "random_seed": 1})
    record["execution_status"] = "implementation_defect"
    record["failure_reason"] = "deliberate"
    registry.append(run_id, "terminal", record)
    assert [row["execution_status"] for row in registry.records()] == [
        "running",
        "implementation_defect",
    ]
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        registry.db.execute("DELETE FROM events")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        registry.db.execute("UPDATE events SET payload='{}'")
    with pytest.raises(sqlite3.IntegrityError):
        registry.append(run_id, "terminal", record)
    registry.close()


def test_worker_failure_and_timeout_are_retained(tmp_path):
    jobs = [
        {"metadata": {"candidate_algorithm": "failure"}, "argv": ["-c", "raise ValueError()"]},
        {"metadata": {"candidate_algorithm": "timeout"}, "argv": ["-c", "while True: pass"]},
    ]
    root = tmp_path / "batch"
    results = run_batch(root, jobs, Limits(run_wall_seconds=0.3), tmp_path)
    assert results[0]["execution_status"] == "implementation_defect"
    assert results[1]["failure_reason"] == "run_wall_limit"
    registry = Registry(root / "experiments.sqlite")
    assert len(registry.records()) == 4
    registry.close()
    with pytest.raises(FileExistsError):
        run_batch(root, jobs, Limits(), tmp_path)


@pytest.mark.parametrize("risk", [0.2, 0.5])
def test_constant_nominal_proxy_matches_ipw_with_same_effective_coefficient(risk):
    for seed in range(3):
        ppe = simulate(method="ppe", risk=risk, seed=seed)
        ipw = simulate(method="ipw", risk=risk, seed=seed)
        assert ppe == ipw
