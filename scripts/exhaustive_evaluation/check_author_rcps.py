"""Check fixed-target adaptation against original author update code, not all RCPS claims."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import torch

from shiftlab.sota_search.combination_screen import make_world
from shiftlab.sota_search.published_baselines import active_rcps_cost

ROOT = Path(__file__).resolve().parents[2]


def main():
    source = ROOT / "outputs/exhaustive_evaluation/active-rcps/IwUpperMartingale.py"
    spec = importlib.util.spec_from_file_location("original_rcps", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stream = make_world("abrupt", paths=1, horizon=160, seed=776)
    # Original code updates its next bet after every observed event. Delay one
    # matches that filtration; larger issuance delays are a separate adaptation.
    q, delay, seed, B = 0.2, 1, 19, 160

    class Predictor:
        def predict(self, x, beta):
            return np.float64(1 - float(x))

        def min_val(self, beta):
            return torch.ones_like(beta) * (1 - stream["proxy_max"])

    predictor = Predictor()

    def rho(x, betas):
        return torch.ones_like(betas) * (1 - float(x[1]))

    class CompatibleOriginal(module.PartialIwUpperMartingale):
        # Modern NumPy/Torch reject ndarray >= Tensor in the original assert.
        # Type-only boundary shim; the original increment/bet update is unchanged.
        def ximin(self, betas):
            return np.asarray(super().ximin(betas))

    obj = CompatibleOriginal(
        rho=rho, q_min=q, theta=1 - stream["r0"], n_betas=2, alpha=0.05, cv_predictor=predictor
    )
    # Fixed-target component comparison: disable grid truncation/selection.
    obj._thres = float("inf")
    U = np.random.default_rng(seed).random((1, 160))[0]
    issued, flags, expected, largest_error = 0, [], [], 0.0
    for t in range(160):
        flags.append(int(U[t] < q and issued < B))
        issued += flags[-1]
        if t >= delay:
            r = t - delay
            obj.addobs((stream["proxy"][0, r], stream["loss"][0, r]), q, flags[r], predictor)
            # Once the hard budget is exhausted, adaptation freezes future event
            # factors. The original component has no hard-cap contract, so this
            # parity run uses a realization that stays below its cap by horizon.
        expected.append(float(obj._stats[0, 0]))
    if issued >= B:
        raise AssertionError("parity path exhausted hard budget; choose a prospectively larger cap")
    actual = active_rcps_cost(stream, frac=q, budget=B, delay=delay, seed=seed, return_wealth=True)
    largest_error = float(np.max(np.abs(actual["logwealth"][0] - expected)))
    if largest_error >= 1e-5:
        failure = {
            "status": "parity_failed",
            "max_logwealth_error": largest_error,
            "expected": expected,
            "actual": actual["logwealth"][0].tolist(),
        }
        (ROOT / "docs/exhaustive_evaluation/rcps_parity_failure.json").write_text(
            json.dumps(failure), encoding="utf-8"
        )
    assert largest_error < 1e-5, largest_error
    out = {
        "status": "fixed_target_component_parity_pass",
        "max_logwealth_error": largest_error,
        "source_commit": "a67f85d603df2bb3e32ef007f445191923ebd990",
        "delay": delay,
        "not_verified": [
            "full simulation reproduction",
            "RCPS grid inversion",
            "learned query policy",
            "hard-cap extension theorem",
            "original-code parity for delay > 1",
        ],
    }
    (ROOT / "docs/exhaustive_evaluation/rcps_component_parity.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print(json.dumps(out))


if __name__ == "__main__":
    main()
