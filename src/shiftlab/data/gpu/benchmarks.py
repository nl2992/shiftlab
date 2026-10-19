"""Measure end-to-end chunk construction including host transfer; no assumed speedup."""

import time
from pathlib import Path

import pandas as pd
import psutil

from ..provenance import commit, source_hash, write_json
from ..schemas import SyntheticConfig
from ..synthetic import generate_chunks
from .environment import environment


def benchmark(root: Path, configuration: dict):
    env = environment()
    rows = []
    config = dict(configuration)
    repeats = config.pop("repeats", 3)
    base = {"n": 20000, "d": 64, "chunk_size": 5000, **config}
    devices = ["cpu", "cuda"] if env["cuda_available"] else ["cpu"]
    for device in devices:
        if device == "cuda":
            import torch

            torch.cuda.reset_peak_memory_stats()
        for repeat in range(repeats):
            start = time.perf_counter()
            count = sum(
                len(frame)
                for frame, _ in generate_chunks(
                    SyntheticConfig(**{**base, "device": device, "seed": 42 + repeat})
                )
            )
            elapsed = time.perf_counter() - start
            rows.append(
                {
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
            "interpretation": "First run includes CUDA initialization; warmed comparisons are exploratory, not guaranteed speedups.",
        },
    )
    return path
