"""Exact finite-support null checks for the cap-dependent bet (docs/hg_validation/02_*)."""

import json
from pathlib import Path

import numpy as np

q, r0 = 0.1, 0.4
PZ, RISK = np.array([0.5, 0.5]), np.array([0.6, 0.2])  # marginal risk = r0 exactly


def drift(proxy, lam0, uniform):
    """Exact E[lambda(Z) X] per step; > 0 means the product is not a supermartingale under the marginal null."""
    bound = proxy * (1 / q - 1) + r0
    if uniform:
        bound = np.full(2, 0.25 * (1 / q - 1) + r0)
    lam = np.minimum(lam0, 0.5 / bound)
    return float((PZ * lam * (RISK - r0)).sum()), lam


def crossing(proxy, lam0, uniform, n=4000, T=400, seed=0):
    rng = np.random.default_rng(seed)
    bound = proxy * (1 / q - 1) + r0 if not uniform else np.full(2, 0.25 * (1 / q - 1) + r0)
    lam = np.minimum(lam0, 0.5 / bound)
    z = rng.integers(0, 2, (n, T))
    r = (rng.random((n, T)) < RISK[z]).astype(float)
    qq = rng.random((n, T)) < q
    x = proxy[z] + qq / q * (r - proxy[z]) - r0
    logw = np.cumsum(np.log1p(lam[z] * x), 1)
    return float((logw.max(1) >= np.log(20)).mean())


out = {}
for name, proxy in (("anti_informative", np.array([0.05, 0.35])), ("calibrated", RISK.copy())):
    for uniform in (False, True):
        d, lam = drift(proxy, 1.0, uniform)
        out[f"{name}/{'uniform_cap' if uniform else 'context_cap'}"] = {
            "exact_drift_per_step": d,
            "lambda_by_context": lam.tolist(),
            "mc_crossing_prob_alpha_0.05": crossing(proxy, 1.0, uniform),
        }
        print(
            name,
            "uniform" if uniform else "context",
            out[f"{name}/{'uniform_cap' if uniform else 'context_cap'}"],
        )
Path("outputs/hg_validation").mkdir(parents=True, exist_ok=True)
Path("outputs/hg_validation/02_EXACT_NULL_TESTS.json").write_text(json.dumps(out, indent=2))
