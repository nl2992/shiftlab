import numpy as np
import pytest

from shiftlab.data.gpu.environment import environment
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks


def test_cpu_backend_portable():
    frame, _ = next(generate_chunks(SyntheticConfig(n=100, device="cpu", dtype="float32")))
    assert np.stack(frame.features).dtype == np.float32


@pytest.mark.skipif(not environment()["cuda_available"], reason="CUDA not available")
def test_gpu_reproducibility_and_statistical_parity():
    samples = {}
    for device in ["cpu", "cuda"]:
        c = SyntheticConfig(n=10000, d=4, device=device, dtype="float64")
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
    assert np.allclose(
        transform(X, mean, scale, "cpu"), transform(X, mean, scale, "cuda"), rtol=1e-12, atol=1e-12
    )
