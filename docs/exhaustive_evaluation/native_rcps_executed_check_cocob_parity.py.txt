"""Verify a vectorized numerical port against the pinned author's optimizer."""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch

from shiftlab.sota_search.active_rcps_learning import Cocob

ROOT = Path(__file__).resolve().parents[2]


def main():
    path = ROOT / "outputs/exhaustive_evaluation/active-rcps/cocob.py"
    spec = importlib.util.spec_from_file_location("author_cocob_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rng = np.random.default_rng(202650000)
    initial = rng.normal(size=(7, 13))
    parameter = torch.nn.Parameter(torch.tensor(initial, dtype=torch.float64))
    native = module.COCOB([parameter])
    port = Cocob(initial)
    maximum_error = 0.0
    for t in range(200):
        gradient = rng.normal(size=initial.shape) * (10.0 ** ((t % 7) - 3))
        gradient[t % 7] = 0
        if t % 11 == 0:
            gradient[:] = 0
        parameter.grad = torch.tensor(gradient, dtype=torch.float64)
        native.step()
        value = port.step(gradient)
        error = float(np.max(np.abs(value - parameter.detach().numpy())))
        maximum_error = max(maximum_error, error)
        np.testing.assert_allclose(value, parameter.detach().numpy(), rtol=1e-12, atol=1e-12)
    result = {
        "status": "passed",
        "updates": 200,
        "independent_rows": 7,
        "coordinates_per_row": 13,
        "maximum_absolute_error": maximum_error,
        "includes": "zero gradients, independent masked rows, signed gradients across seven orders of magnitude",
        "scope": "optimizer component parity only; no learned-query/risk guarantee claimed",
        "sha256": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                path,
                Path(__file__),
                ROOT / "src/shiftlab/sota_search/active_rcps_learning.py",
            ]
        },
    }
    output = ROOT / "docs/exhaustive_evaluation/cocob_component_parity.json"
    if output.exists():
        raise FileExistsError("retain original parity evidence")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
