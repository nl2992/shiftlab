"""Supervise a synthetic worker with explicit resource caps.

Limits are sampled every 50 ms, so a worker can briefly overshoot. No process
is allowed to survive a limit breach. Output snapshots use unique directories.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

from .registry import Registry
from .budget import ProgrammeBudget


@dataclass(frozen=True)
class Limits:
    max_runs: int = 1500
    batch_wall_seconds: float = 3600
    run_wall_seconds: float = 60
    run_cpu_seconds: float = 60
    memory_bytes: int = 2 * 1024**3
    storage_bytes: int = 512 * 1024**2

    def __post_init__(self):
        if any(
            isinstance(value, bool) or not math.isfinite(value) or value <= 0
            for value in asdict(self).values()
        ):
            raise ValueError("all resource limits must be finite and positive")
        if any(
            not isinstance(value, int)
            for value in (self.max_runs, self.memory_bytes, self.storage_bytes)
        ):
            raise ValueError("run-count, memory and storage limits must be integers")


def directory_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def stop_tree(process: psutil.Process) -> None:
    try:
        children = process.children(recursive=True)
    except psutil.NoSuchProcess:
        children = []
    for child in [*reversed(children), process]:
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass


def run_batch(
    root: Path,
    jobs: list[dict],
    limits: Limits,
    repo: Path,
    *,
    programme: ProgrammeBudget | None = None,
) -> list[dict]:
    if root.exists():
        raise FileExistsError("batch snapshots must not overwrite existing directories")
    production_archive = (repo / "outputs/sota_search").resolve()
    if root.resolve().parent == production_archive and programme is None:
        raise ValueError("production batches require programme-wide budget accounting")
    if len(jobs) > limits.max_runs:
        raise ValueError("manifest exceeds run-count limit")
    if programme is not None and root.resolve().parent != programme.root.resolve():
        raise ValueError("batch must be a direct child of the programme archive")
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "limits": asdict(limits),
                "jobs": jobs,
                "programme_limits": asdict(programme.limits) if programme else None,
                "programme_usage_before": programme.usage() if programme else None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    registry = Registry(root / "experiments.sqlite")
    batch_started = time.monotonic()
    results = []
    try:
        for job in jobs:
            metadata = dict(job["metadata"])
            metadata["component_configuration"] = {
                "declared": metadata.get("component_configuration"),
                "argv": job["argv"],
            }
            run_id, record = registry.start(metadata)
            run_root = root / run_id
            run_root.mkdir()
            started = time.monotonic()
            status, reason = "completed", None
            peak_memory, cpu = 0, 0.0
            process = None
            reserved = False
            try:
                if time.monotonic() - batch_started >= limits.batch_wall_seconds:
                    raise RuntimeError("batch_wall_limit")
                if directory_bytes(root) >= limits.storage_bytes:
                    raise RuntimeError("storage_limit")
                if programme is not None:
                    if directory_bytes(programme.root) >= programme.limits.storage_bytes:
                        raise RuntimeError("programme_storage_limit")
                    programme.reserve(
                        run_id, wall=limits.run_wall_seconds, cpu=limits.run_cpu_seconds
                    )
                    reserved = True
                result_path = (run_root / "result.json").resolve()
                env = {
                    **os.environ,
                    "PYTHONPATH": str(repo / "src"),
                    "OMP_NUM_THREADS": "1",
                    "OPENBLAS_NUM_THREADS": "1",
                    "MKL_NUM_THREADS": "1",
                    "NUMEXPR_NUM_THREADS": "1",
                    "SOTA_RESULT_PATH": str(result_path),
                }
                with (run_root / "worker.log").open("wb") as log:
                    process = psutil.Popen(
                        [sys.executable, *job["argv"]],
                        cwd=repo,
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                    while process.poll() is None:
                        try:
                            members = [process, *process.children(recursive=True)]
                            rss = sum(p.memory_info().rss for p in members)
                            cpu = sum(p.cpu_times().user + p.cpu_times().system for p in members)
                            peak_memory = max(peak_memory, rss)
                        except psutil.NoSuchProcess:
                            continue
                        checks = {
                            "run_wall_limit": time.monotonic() - started > limits.run_wall_seconds,
                            "batch_wall_limit": (
                                time.monotonic() - batch_started > limits.batch_wall_seconds
                            ),
                            "cpu_limit": cpu > limits.run_cpu_seconds,
                            "memory_limit": rss > limits.memory_bytes,
                            "storage_limit": directory_bytes(root) > limits.storage_bytes,
                            "programme_storage_limit": (
                                programme is not None
                                and directory_bytes(programme.root) > programme.limits.storage_bytes
                            ),
                        }
                        exceeded = next((name for name, hit in checks.items() if hit), None)
                        if exceeded:
                            raise RuntimeError(exceeded)
                        time.sleep(0.05)
                    if process.returncode:
                        status, reason = "implementation_defect", f"exit_code={process.returncode}"
                    elif result_path.exists():
                        result = json.loads(result_path.read_text(encoding="utf-8"))
                        required = {
                            "primary_metric",
                            "secondary_metrics",
                            "uncertainty_estimates",
                            "labels_used",
                            "validity_status",
                        }
                        if not isinstance(result, dict) or not required <= result.keys():
                            raise ValueError("incomplete worker result artifact")
                        # A worker cannot replace supervisor provenance or status.
                        for key in (
                            "primary_metric",
                            "secondary_metrics",
                            "uncertainty_estimates",
                            "labels_used",
                            "validity_status",
                        ):
                            if key in result:
                                record[key] = result[key]
                    else:
                        status, reason = "implementation_defect", "missing_result_artifact"
            except KeyboardInterrupt:
                status, reason = "aborted", "supervisor_interrupted"
                raise
            except Exception as exc:
                reason = str(exc)
                status = "resource_limit" if reason.endswith("limit") else "implementation_defect"
            finally:
                if process is not None:
                    stop_tree(process)
                    process.wait()
                record.update(
                    execution_status=status,
                    failure_reason=reason,
                    runtime={"wall_seconds": time.monotonic() - started, "cpu_seconds": cpu},
                    peak_memory=peak_memory,
                    artifacts=[str(path) for path in run_root.iterdir() if path.is_file()],
                )
                registry.append(run_id, "terminal", record)
                results.append({"run_id": run_id, **record})
                if programme is not None and reserved:
                    programme.settle(
                        run_id,
                        wall=record["runtime"]["wall_seconds"],
                        cpu=cpu if cpu > 0 else record["runtime"]["wall_seconds"],
                    )
    finally:
        registry.close()
    return results
