from __future__ import annotations

import sqlite3

import pytest

from shiftlab.sota_search.budget import ProgrammeBudget, ProgrammeLimits
from shiftlab.sota_search.registry import Registry
from shiftlab.sota_search.supervisor import Limits, run_batch


def test_budget_reservations_survive_reopen_and_cannot_be_oversubscribed(tmp_path):
    limits = ProgrammeLimits(max_runs=3, wall_seconds=10, cpu_seconds=10)
    first = ProgrammeBudget(tmp_path, limits)
    second = ProgrammeBudget(tmp_path, limits)
    first.reserve("one", wall=6, cpu=6)
    with pytest.raises(RuntimeError, match="programme_budget_limit"):
        second.reserve("two", wall=6, cpu=6)
    first.close()
    assert second.usage()["wall_seconds"] == 6
    second.settle("one", wall=1, cpu=0.5)
    second.reserve("two", wall=6, cpu=6)
    assert second.usage() == {"wall_seconds": 7.0, "cpu_seconds": 6.5, "runs": 2}
    with pytest.raises(sqlite3.IntegrityError):
        second.db.execute("DELETE FROM charges")
    second.close()
    with pytest.raises(ValueError, match="persisted policy"):
        ProgrammeBudget(tmp_path, ProgrammeLimits())


def test_legacy_import_is_idempotent_and_running_job_remains_reserved(tmp_path):
    registry = Registry(tmp_path / "legacy" / "experiments.sqlite")
    _, _ = registry.start({"candidate_algorithm": "crashed"})
    run_id, record = registry.start({"candidate_algorithm": "completed"})
    record.update(execution_status="completed", runtime={"wall_seconds": 2, "cpu_seconds": 1})
    registry.append(run_id, "terminal", record)
    registry.close()
    budget = ProgrammeBudget(tmp_path, ProgrammeLimits())
    budget.import_previous(default_wall=60, default_cpu=60)
    budget.import_previous(default_wall=60, default_cpu=60)
    assert budget.usage() == {"wall_seconds": 62.0, "cpu_seconds": 61.0, "runs": 2}
    budget.close()


def test_rejected_global_budget_is_still_a_recorded_attempt(tmp_path):
    budget = ProgrammeBudget(tmp_path, ProgrammeLimits(wall_seconds=1, cpu_seconds=1))
    result = run_batch(
        tmp_path / "batch",
        [{"metadata": {}, "argv": ["-c", "print('must not run')"]}],
        Limits(),
        tmp_path,
        programme=budget,
    )
    assert result[0]["execution_status"] == "resource_limit"
    assert result[0]["failure_reason"] == "programme_budget_limit"
    assert budget.usage()["runs"] == 0
    assert not (tmp_path / "batch" / result[0]["run_id"] / "worker.log").exists()
    budget.close()
