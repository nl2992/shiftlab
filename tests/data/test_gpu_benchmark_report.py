import json
from pathlib import Path

import numpy as np
import pandas as pd


def test_sustained_gpu_benchmark_report_has_complete_repeats_and_telemetry():
    root = Path(__file__).parents[2] / "data" / "reports"
    report = pd.read_csv(root / "gpu_benchmark.csv")
    manifest = json.loads((root / "gpu_benchmark.manifest.json").read_text(encoding="utf-8"))
    configuration = manifest["configuration"]

    assert configuration["n"] == 200000
    assert configuration["memory_mb"] == 128
    assert len(report) == 36
    assert set(report.device) == {"cpu", "cuda"}
    assert report.groupby(["device", "dtype", "chunk_size"]).size().eq(3).all()
    assert np.isfinite(report[["seconds", "observations_per_second"]].to_numpy()).all()

    cuda = report.loc[report.device == "cuda"]
    assert cuda.gpu_utilization_sample_count.ge(20).all()
    assert cuda.gpu_utilization_mean_percent.between(0, 100).all()
    assert cuda.gpu_peak_allocated_bytes.max() <= configuration["memory_mb"] * 1024**2
    assert manifest["commit"]
    assert manifest["environment"]["gpu_name"]
