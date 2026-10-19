"""Measure end-to-end chunk construction including host transfer; no assumed speedup."""

import subprocess
import threading
import time
from pathlib import Path

import pandas as pd
import psutil

from ..provenance import commit, source_hash, write_json
from ..schemas import SyntheticConfig
from ..synthetic import generate_chunks
from .environment import environment


def _parse_sample(line: str) -> tuple[int, int, int] | None:
    try:
        utilization, used_mib, total_mib = (int(value.strip()) for value in line.split(","))
    except (TypeError, ValueError):
        return None
    return utilization, used_mib, total_mib


class _GpuSampler:
    """Sample device-wide NVML-backed nvidia-smi telemetry during benchmark repeats."""

    def __init__(self):
        self.samples: list[tuple[int, int, int]] = []
        self.process = None
        self.thread = None
        self.error = None

    def start(self):
        try:
            self.process = subprocess.Popen(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                    "--loop-ms=100",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except OSError as exc:
            self.error = str(exc)
            return

        def read_samples():
            assert self.process is not None and self.process.stdout is not None
            for line in self.process.stdout:
                parsed = _parse_sample(line)
                if parsed is not None:
                    self.samples.append(parsed)

        self.thread = threading.Thread(target=read_samples, daemon=True)
        self.thread.start()

    def stop(self) -> dict:
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
            if self.thread is not None:
                self.thread.join(timeout=3)
        if not self.samples:
            return {
                "gpu_utilization_sample_count": 0,
                "gpu_utilization_mean_percent": None,
                "gpu_utilization_max_percent": None,
                "gpu_device_memory_used_peak_bytes": None,
                "gpu_telemetry_error": self.error or "nvidia-smi produced no samples",
            }
        utilization = [sample[0] for sample in self.samples]
        used = [sample[1] for sample in self.samples]
        return {
            "gpu_utilization_sample_count": len(self.samples),
            "gpu_utilization_mean_percent": float(sum(utilization) / len(utilization)),
            "gpu_utilization_max_percent": max(utilization),
            "gpu_device_memory_used_peak_bytes": max(used) * 1024**2,
            "gpu_telemetry_error": None,
        }


def benchmark(root: Path, configuration: dict):
    env = environment()
    rows = []
    config = dict(configuration)
    repeats = config.pop("repeats", 3)
    base = {"n": 20000, "d": 64, "chunk_size": 5000, **config}
    devices = ["cpu", "cuda"] if env["cuda_available"] else ["cpu"]
    for device in devices:
        sampler = None
        if device == "cuda":
            import torch

            sampler = _GpuSampler()
            sampler.start()
        device_rows = []
        for repeat in range(repeats):
            if device == "cuda":
                torch.cuda.reset_peak_memory_stats()
            start = time.perf_counter()
            count = sum(
                len(frame)
                for frame, _ in generate_chunks(
                    SyntheticConfig(**{**base, "device": device, "seed": 42 + repeat})
                )
            )
            elapsed = time.perf_counter() - start
            row = {
                "device": device,
                "repeat": repeat,
                "n": count,
                "d": base["d"],
                "seconds": elapsed,
                "observations_per_second": count / elapsed,
                "cpu_rss_bytes": psutil.Process().memory_info().rss,
                "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated()
                if device == "cuda"
                else 0,
                "gpu_status": env.get("nvidia_smi"),
                "scope": "generation incl host transfers and dataframe assembly; excludes disk",
            }
            rows.append(row)
            device_rows.append(row)
        if sampler is not None:
            telemetry = sampler.stop()
            for row in device_rows:
                row.update(telemetry)
            for row in device_rows:
                row["gpu_telemetry_scope"] = (
                    "device-wide samples across all repeats for this device"
                )
    root.joinpath("reports").mkdir(parents=True, exist_ok=True)
    path = root / "reports/gpu_benchmark.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    write_json(
        root / "reports/gpu_benchmark.manifest.json",
        {
            "configuration": base,
            "repeats": repeats,
            "source_hash": source_hash(),
            "commit": commit(),
            "environment": env,
            "gpu_telemetry": "CSV includes nvidia-smi device-wide utilization and used-memory samples at 100 ms interval across all CUDA repeats; samples are not process-specific and short workloads may be below telemetry resolution.",
            "memory_budget": "memory_mb limits estimated per-chunk feature/intermediate workspace; full process RSS includes Python, pandas and O(n) schedule memory and may exceed this estimate.",
            "interpretation": "First run includes CUDA initialization; warmed comparisons are exploratory, not guaranteed speedups.",
        },
    )
    return path
