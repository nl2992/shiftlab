"""Apply training-fitted affine preprocessing on CPU or CUDA without refitting."""

import numpy as np


def transform(X: np.ndarray, mean: np.ndarray, scale: np.ndarray, device="cpu") -> np.ndarray:
    if np.any(np.asarray(scale) <= 0):
        raise ValueError("Scale must be strictly positive")
    if device == "cpu":
        return (X - mean) / scale
    if device != "cuda":
        raise ValueError("device must be cpu or cuda")
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    values = torch.as_tensor(X, device="cuda")
    result = (values - torch.as_tensor(mean, device="cuda", dtype=values.dtype)) / torch.as_tensor(
        scale, device="cuda", dtype=values.dtype
    )
    return result.cpu().numpy()
