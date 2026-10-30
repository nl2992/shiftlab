"""Append-only experiment event registry; a start survives a worker crash.

One attempted configuration has a start event and at most one terminal event.
Never update the start row to record completion: that would discard provenance.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


FIELDS = """parent_algorithm candidate_algorithm modification_id component_configuration
hyperparameters generator_family shift_type shift_magnitude predictive_degradation
decision_harm proxy_quality delay_model label_budget cost_configuration random_seed
code_commit source_hash configuration_hash baseline_version execution_status failure_reason
validity_status primary_metric secondary_metrics uncertainty_estimates runtime peak_memory
labels_used artifacts""".split()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Registry:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                phase TEXT NOT NULL CHECK(phase IN ('start', 'terminal')),
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL,
                UNIQUE(run_id, phase)
            );
            CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON events
            BEGIN SELECT RAISE(ABORT, 'append-only registry'); END;
            CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON events
            BEGIN SELECT RAISE(ABORT, 'append-only registry'); END;
        """)

    def append(self, run_id: str, phase: str, record: dict) -> None:
        missing = set(FIELDS) - record.keys()
        if missing:
            raise ValueError(f"missing registry fields: {sorted(missing)}")
        if (
            phase == "terminal"
            and not self.db.execute(
                "SELECT 1 FROM events WHERE run_id=? AND phase='start'", (run_id,)
            ).fetchone()
        ):
            raise ValueError("terminal event requires an existing start")
        with self.db:
            self.db.execute(
                "INSERT INTO events(run_id, phase, timestamp, payload) VALUES (?, ?, ?, ?)",
                (run_id, phase, datetime.now(timezone.utc).isoformat(), canonical(record)),
            )

    def start(self, metadata: dict) -> tuple[str, dict]:
        record = dict.fromkeys(FIELDS)
        record.update(metadata)
        record["execution_status"] = "running"
        record["configuration_hash"] = digest(metadata)
        run_id = uuid.uuid4().hex
        self.append(run_id, "start", record)
        return run_id, record

    def records(self) -> list[dict]:
        return [
            {"run_id": run_id, "phase": phase, **json.loads(payload)}
            for run_id, phase, payload in self.db.execute(
                "SELECT run_id, phase, payload FROM events ORDER BY sequence"
            )
        ]

    def close(self) -> None:
        self.db.close()
