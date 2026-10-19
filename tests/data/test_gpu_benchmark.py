import pandas as pd

from shiftlab.data.gpu import benchmarks


def test_benchmark_runs_configured_dtype_and_chunk_matrix_on_cpu(tmp_path, monkeypatch):
    monkeypatch.setattr(
        benchmarks,
        "environment",
        lambda: {"cuda_available": False, "nvidia_smi": None},
    )
    path = benchmarks.benchmark(
        tmp_path,
        {
            "n": 100,
            "d": 2,
            "scenario": "iid_regression",
            "repeats": 1,
            "dtypes": ["float32", "float64"],
            "chunk_sizes": [16, 32],
        },
    )
    result = pd.read_csv(path)
    assert len(result) == 4
    assert set(result["dtype"]) == {"float32", "float64"}
    assert set(result.chunk_size) == {16, 32}
    assert (result.n == 100).all()
