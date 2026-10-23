"""Bounded random feature generation. CPU/GPU use independent backend RNG sequences."""

import numpy as np


def _chunk_plan(c):
    itemsize = 8 if c.dtype == "float64" else 4
    budget_bytes = c.memory_mb * 1024**2
    estimated_bytes_per_row = itemsize * (c.d * 6 + 64)
    if estimated_bytes_per_row > budget_bytes:
        raise ValueError(
            "memory_mb is too small for one estimated feature row; increase memory_mb or lower d"
        )
    chunk = min(c.chunk_size, budget_bytes // estimated_bytes_per_row)
    return int(chunk), int(estimated_bytes_per_row)


def random_chunks(c):
    device = c.device
    if device == "auto":
        from .environment import resolve_device

        device = resolve_device(c.device, n=c.n, d=c.d, chunk_size=c.chunk_size)
    # Include output arrays, feature copies and intermediate transformations.
    chunk, estimated_bytes_per_row = _chunk_plan(c)
    rng = np.random.default_rng(c.seed)
    if device == "cuda":
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "CUDA requested; install the neural extra and CUDA-compatible PyTorch"
            ) from exc
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA requested but torch.cuda.is_available() is false; check driver/runtime"
            )
        generator = torch.Generator(device="cuda").manual_seed(c.seed)
        dtype = getattr(torch, c.dtype)
        free, _ = torch.cuda.mem_get_info()
        if chunk * estimated_bytes_per_row > free * 0.8:
            raise RuntimeError("GPU memory budget exceeds free memory; lower memory_mb/chunk_size")
    for start in range(0, c.n, chunk):
        m = min(chunk, c.n - start)
        if device == "cuda":
            try:
                latent = torch.randn((m, c.d + 1), device="cuda", dtype=dtype, generator=generator)
                uniform = torch.rand(m, device="cuda", dtype=dtype, generator=generator)
                array = latent.cpu().numpy()
                u = uniform.cpu().numpy()
                del latent, uniform
            except torch.cuda.OutOfMemoryError as exc:
                raise RuntimeError(
                    "CUDA OOM: lower chunk_size or memory_mb, or select --device cpu"
                ) from exc
        else:
            array = rng.normal(size=(m, c.d + 1)).astype(c.dtype)
            u = rng.random(m).astype(c.dtype)
        yield start, array[:, : c.d].copy(), array[:, c.d].copy(), u, device
