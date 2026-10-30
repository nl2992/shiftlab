"""Append-only experiment registry (SQLite). Every attempted run is recorded, including failures."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path

FIELDS = [
    "run_id",
    "parent_algorithm",
    "candidate_algorithm",
    "modification_id",
    "component_configuration",
    "hyperparameters",
    "generator_family",
    "shift_type",
    "shift_magnitude",
    "predictive_degradation",
    "decision_harm",
    "proxy_quality",
    "delay_model",
    "label_budget",
    "cost_configuration",
    "random_seed",
    "code_commit",
    "source_hash",
    "configuration_hash",
    "baseline_version",
    "execution_status",
    "failure_reason",
    "validity_status",
    "primary_metric",
    "secondary_metrics",
    "uncertainty_estimates",
    "runtime",
    "peak_memory",
    "labels_used",
    "artifacts",
]
STATUSES = {
    "ok",
    "negative",
    "inconclusive",
    "numerically_invalid",
    "inference_invalid",
    "timeout",
    "implementation_defect",
    "unsupported_contract",
}


def _commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


class Registry:
    def __init__(self, path: str | Path = "outputs/sota_search/registry.sqlite"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        cols = ", ".join(f"{f} TEXT" for f in FIELDS[1:])
        self.con.execute(
            f"CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, ts REAL, batch TEXT, {cols})"
        )
        self.commit = _commit()

    def record(self, batch: str, **kw) -> str:
        """Insert one run. Unknown keys are rejected so the schema cannot silently drift."""
        extra = set(kw) - set(FIELDS)
        if extra:
            raise KeyError(f"unknown registry fields: {sorted(extra)}")
        status = kw.setdefault("execution_status", "ok")
        if status not in STATUSES:
            raise ValueError(f"execution_status must be one of {sorted(STATUSES)}")
        kw.setdefault("code_commit", self.commit)
        kw["configuration_hash"] = hashlib.sha256(
            json.dumps(
                {
                    k: kw.get(k)
                    for k in (
                        "candidate_algorithm",
                        "hyperparameters",
                        "generator_family",
                        "shift_type",
                        "shift_magnitude",
                        "label_budget",
                        "delay_model",
                    )
                },
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()[:16]
        rid = kw.pop("run_id", None) or uuid.uuid4().hex
        vals = [json.dumps(kw.get(f), default=str) for f in FIELDS[1:]]
        self.con.execute(
            f"INSERT INTO runs VALUES ({', '.join('?' * (len(FIELDS) + 2))})",
            [rid, time.time(), batch, *vals],
        )
        return rid

    def flush(self) -> None:
        self.con.commit()

    def rows(self, where: str = "1=1") -> list[dict]:
        cur = self.con.execute(f"SELECT * FROM runs WHERE {where}")
        names = [d[0] for d in cur.description]
        return [
            {
                n: (json.loads(v) if n not in ("run_id", "ts", "batch") and v is not None else v)
                for n, v in zip(names, r, strict=True)
            }
            for r in cur.fetchall()
        ]

    def count(self) -> int:
        return self.con.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
