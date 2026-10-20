import numpy as np
import pandas as pd
import pytest

from shiftlab.data.gpu.benchmarks import _parse_sample
from shiftlab.data.gpu.environment import environment
from shiftlab.data.gpu.torch_backend import _chunk_plan
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import SCENARIOS, conditional_mean, generate_chunks


def test_cpu_backend_portable():
    frame, _ = next(generate_chunks(SyntheticConfig(n=100, device="cpu", dtype="float32")))
    assert np.stack(frame.features).dtype == np.float32


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_cpu_generation_is_repeatable_for_identical_configuration(scenario):
    config = SyntheticConfig(
        n=240,
        d=3,
        seed=2026,
        scenario=scenario,
        device="cpu",
        dtype="float64",
        chunk_size=64,
    )
    first = list(generate_chunks(config))
    repeated = list(generate_chunks(config))
    assert len(first) == len(repeated)
    pd.testing.assert_frame_equal(
        pd.concat([frame for frame, _ in first], ignore_index=True),
        pd.concat([frame for frame, _ in repeated], ignore_index=True),
        check_exact=True,
    )
    pd.testing.assert_frame_equal(
        pd.concat([oracle for _, oracle in first], ignore_index=True),
        pd.concat([oracle for _, oracle in repeated], ignore_index=True),
        check_exact=True,
    )


@pytest.mark.parametrize(("dtype", "expected_chunk"), [("float64", 6), ("float32", 13)])
def test_memory_budget_is_a_strict_chunk_bound(dtype, expected_chunk):
    config = SyntheticConfig(n=100, d=50000, memory_mb=16, chunk_size=1000, dtype=dtype)
    chunk, estimated_bytes_per_row = _chunk_plan(config)
    assert chunk == expected_chunk
    assert chunk * estimated_bytes_per_row <= config.memory_mb * 1024**2
    impossible = SyntheticConfig(n=100, d=500000, memory_mb=16)
    with pytest.raises(ValueError, match="too small for one estimated feature row"):
        next(generate_chunks(impossible))


def test_nvidia_smi_sample_parser():
    assert _parse_sample("17, 2048, 8192\n") == (17, 2048, 8192)
    assert _parse_sample("N/A, 2048, 8192") is None


@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_cpu_dtype_is_preserved(dtype):
    frame, _ = next(
        generate_chunks(SyntheticConfig(n=100, device="cpu", dtype=dtype, chunk_size=16))
    )
    expected = np.float32 if dtype == "float32" else np.float64
    assert np.stack(frame.features.to_numpy()).dtype == expected


@pytest.mark.parametrize("dimension", [2, 16, 64, 256, 1024])
def test_cpu_generation_supports_every_declared_grid_dimension(dimension):
    config = SyntheticConfig(
        n=512,
        d=dimension,
        seed=42,
        scenario="iid_regression",
        device="cpu",
        dtype="float32",
        chunk_size=128,
        memory_mb=16,
    )
    generated = list(generate_chunks(config))
    features = np.concatenate([np.stack(frame.features.to_numpy()) for frame, _ in generated])
    weights = np.concatenate([oracle.weight.to_numpy() for _, oracle in generated])
    targets = np.concatenate([frame.target.to_numpy() for frame, _ in generated])
    oracle_mean = np.concatenate([oracle.conditional_mean.to_numpy() for _, oracle in generated])
    assert features.shape == (config.n, dimension)
    assert features.dtype == np.float32
    assert np.max(np.abs(conditional_mean(config, features, weights) - oracle_mean)) < 1e-5
    assert targets.shape == (config.n,)
    planned_chunk, estimated_row_bytes = _chunk_plan(config)
    assert planned_chunk * estimated_row_bytes <= config.memory_mb * 1024**2


@pytest.mark.skipif(not environment()["cuda_available"], reason="CUDA not available")
@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_gpu_reproducibility_and_statistical_parity(dtype):
    samples = {}
    for device in ["cpu", "cuda"]:
        c = SyntheticConfig(n=10000, d=4, device=device, dtype=dtype)
        a = list(generate_chunks(c))
        b = list(generate_chunks(c))
        assert np.array_equal(np.stack(a[0][0].features), np.stack(b[0][0].features))
        samples[device] = np.concatenate([np.stack(f.features) for f, _ in a])
        assert np.max(abs(samples[device].mean(axis=0))) < 0.05
        assert np.max(abs(samples[device].var(axis=0) - 1)) < 0.06
    assert np.max(abs(samples["cpu"].mean(axis=0) - samples["cuda"].mean(axis=0))) < 0.07

    from shiftlab.data.gpu.preprocessing import transform

    X = samples["cpu"]
    mean, scale = X[:500].mean(axis=0), X[:500].std(axis=0)
    tolerance = 1e-6 if dtype == "float32" else 1e-12
    assert np.allclose(
        transform(X, mean, scale, "cpu"),
        transform(X, mean, scale, "cuda"),
        rtol=tolerance,
        atol=tolerance,
    )


@pytest.mark.skipif(not environment()["cuda_available"], reason="CUDA not available")
@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_gpu_dtype_is_preserved_across_chunks(dtype):
    config = SyntheticConfig(n=100, d=4, device="cuda", dtype=dtype, chunk_size=16)
    frame, _ = next(generate_chunks(config))
    repeat, _ = next(generate_chunks(config))
    expected = np.float32 if dtype == "float32" else np.float64
    assert np.stack(frame.features.to_numpy()).dtype == expected
    assert np.array_equal(np.stack(frame.features.to_numpy()), np.stack(repeat.features.to_numpy()))
    assert np.array_equal(frame.target.to_numpy(), repeat.target.to_numpy())
