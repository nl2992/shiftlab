"""Transactional programme-wide budget reservations across batch snapshots.

Reserve each worker's maximum wall/CPU allowance before launch. Settle to its
sampled usage after termination. A crashed supervisor leaves a full reservation
charged, so a later batch cannot quietly reset or reclaim its allocation.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProgrammeLimits:
    max_runs: int = 20000
    wall_seconds: float = 14400
    cpu_seconds: float = 14400
    storage_bytes: int = 2 * 1024**3

    def __post_init__(self):
        if any(
            isinstance(x, bool) or not math.isfinite(x) or x <= 0 for x in asdict(self).values()
        ):
            raise ValueError("programme limits must be finite and positive")
        if not isinstance(self.max_runs, int) or not isinstance(self.storage_bytes, int):
            raise ValueError("count and storage limits must be integers")


class ProgrammeBudget:
    def __init__(self, root: Path, limits: ProgrammeLimits):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.limits = limits
        self.db = sqlite3.connect(root / "programme_budget.sqlite", timeout=30)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS policy (limits_json TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS charges (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                phase TEXT NOT NULL CHECK(phase IN ('reserve', 'settle')),
                wall REAL NOT NULL, cpu REAL NOT NULL,
                UNIQUE(run_id, phase)
            );
            CREATE TRIGGER IF NOT EXISTS charges_no_update BEFORE UPDATE ON charges
            BEGIN SELECT RAISE(ABORT, 'append-only budget'); END;
            CREATE TRIGGER IF NOT EXISTS charges_no_delete BEFORE DELETE ON charges
            BEGIN SELECT RAISE(ABORT, 'append-only budget'); END;
            CREATE TRIGGER IF NOT EXISTS policy_no_update BEFORE UPDATE ON policy
            BEGIN SELECT RAISE(ABORT, 'immutable budget policy'); END;
            CREATE TRIGGER IF NOT EXISTS policy_no_delete BEFORE DELETE ON policy
            BEGIN SELECT RAISE(ABORT, 'immutable budget policy'); END;
        """)
        policy = json.dumps(asdict(limits), sort_keys=True)
        different_policy = False
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            existing = self.db.execute("SELECT limits_json FROM policy").fetchone()
            if existing is None:
                self.db.execute("INSERT INTO policy VALUES (?)", (policy,))
            elif existing[0] != policy:
                different_policy = True
        if different_policy:
            self.db.close()
            raise ValueError("programme budget policy differs from the persisted policy")

    def usage(self) -> dict:
        wall, cpu, runs = self.db.execute(
            "SELECT COALESCE(SUM(wall),0), COALESCE(SUM(cpu),0), "
            "COALESCE(SUM(phase='reserve'),0) FROM charges"
        ).fetchone()
        return {"wall_seconds": wall, "cpu_seconds": cpu, "runs": runs}

    def reserve(self, run_id: str, *, wall: float, cpu: float) -> None:
        if any(not math.isfinite(x) or x <= 0 for x in (wall, cpu)):
            raise ValueError("reservation must be finite and positive")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            usage = self.usage()
            if (
                usage["runs"] >= self.limits.max_runs
                or usage["wall_seconds"] + wall > self.limits.wall_seconds
                or usage["cpu_seconds"] + cpu > self.limits.cpu_seconds
            ):
                raise RuntimeError("programme_budget_limit")
            self.db.execute(
                "INSERT INTO charges(run_id,phase,wall,cpu) VALUES (?, 'reserve', ?, ?)",
                (run_id, wall, cpu),
            )

    def settle(self, run_id: str, *, wall: float, cpu: float) -> None:
        if any(not math.isfinite(x) or x < 0 for x in (wall, cpu)):
            raise ValueError("usage must be finite and nonnegative")
        with self.db:
            reserved = self.db.execute(
                "SELECT wall,cpu FROM charges WHERE run_id=? AND phase='reserve'", (run_id,)
            ).fetchone()
            if reserved is None:
                raise ValueError("settlement requires an existing reservation")
            self.db.execute(
                "INSERT INTO charges(run_id,phase,wall,cpu) VALUES (?, 'settle', ?, ?)",
                (run_id, wall - reserved[0], cpu - reserved[1]),
            )

    def import_previous(self, *, default_wall: float, default_cpu: float) -> None:
        """Account prior snapshots without opening their DBs for writing.

        For an unclosed start, retain a full default reservation. For completed
        short processes with no CPU sample, conservatively charge their wall time.
        """
        for path in self.root.glob("*/experiments.sqlite"):
            with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as previous:
                events = previous.execute("SELECT run_id,phase,payload FROM events").fetchall()
            grouped = {}
            for run_id, phase, payload in events:
                grouped.setdefault(run_id, {})[phase] = json.loads(payload)
            for run_id, phases in grouped.items():
                if self.db.execute("SELECT 1 FROM charges WHERE run_id=?", (run_id,)).fetchone():
                    continue
                terminal = phases.get("terminal")
                runtime = terminal.get("runtime") if terminal else None
                wall = max(float(runtime["wall_seconds"]), 1e-9) if runtime else default_wall
                cpu = (
                    max(float(runtime.get("cpu_seconds") or wall), 1e-9) if runtime else default_cpu
                )
                self.reserve(run_id, wall=wall, cpu=cpu)
                if terminal:
                    self.settle(run_id, wall=wall, cpu=cpu)

    def close(self) -> None:
        self.db.close()
