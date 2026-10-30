"""Numerical formula pilot of Saha-Ramdas Eq3/6, not certified optimization."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def log_point_sum(mean, lengths, averages, horizon):
    # sigma^2=rho^2=1, paper Eq6; finite support pi_s=1/H.
    terms = -0.5 * np.log1p(lengths) + lengths**2 * (averages - mean) ** 2 / (2 * (1 + lengths))
    return float(logsumexp(terms) - np.log(horizon))


def main():
    regpath = DOC / "nonpartitioned_pfa_registration.json"
    if regpath.exists():
        raise FileExistsError("retain numerical pilot evidence")
    source = ROOT / "outputs/exhaustive_evaluation/sources/nonpartitioned_edetectors.html"
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "source_url": "https://arxiv.org/html/2607.28322v1",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "stage": "Eq3/6 numerical formula pilot, not author-code or complete experiment reproduction",
        "horizon": 120,
        "weights": "pi_s=1/120 for starts1..120, zero beyond horizon; finite support specialization",
        "sigma_squared": 1,
        "rho_squared": 1,
        "alpha": 0.05,
        "cases": ["constant0", "constant2", "normal_null", "normal_change"],
        "seed": 202670000,
        "optimization": "convex logsumexp of quadratics, scalar bounded minimization over hull of segment means; numerical result is an upper approximation to infimum, no certified PFA guarantee from numerical crossing",
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    rng = np.random.default_rng(reg["seed"])
    horizon = 120
    paths = {
        "constant0": np.zeros(horizon),
        "constant2": np.full(horizon, 2.0),
        "normal_null": rng.normal(size=horizon),
        "normal_change": np.r_[rng.normal(size=60), rng.normal(2, 1, size=60)],
    }
    rows = []
    for name, x in paths.items():
        prefix = np.r_[0, x.cumsum()]
        composite = []
        point = []
        checks = []
        for t in range(1, horizon + 1):
            lengths = np.arange(t, 0, -1)
            averages = (prefix[t] - prefix[:t]) / lengths
            lo, hi = float(averages.min()), float(averages.max())
            if hi - lo < 1e-14:
                fit = lo
            else:
                opt = minimize_scalar(
                    log_point_sum,
                    bounds=(lo, hi),
                    args=(lengths, averages, horizon),
                    method="bounded",
                    options={"xatol": 1e-12},
                )
                assert opt.success
                fit = float(opt.x)
            value = log_point_sum(fit, lengths, averages, horizon)
            known = log_point_sum(0, lengths, averages, horizon)
            assert value <= known + 1e-8
            # Direct sum formula and a dense feasible grid independently check arithmetic/minimization.
            direct = np.log(
                np.mean(
                    np.exp(
                        -0.5 * np.log1p(lengths)
                        + lengths**2 * (averages - fit) ** 2 / (2 * (1 + lengths))
                    )
                )
            ) + np.log(t / horizon)
            np.testing.assert_allclose(value, direct, atol=1e-12)
            if t in [30, 60, 120]:
                grid = min(
                    log_point_sum(m, lengths, averages, horizon) for m in np.linspace(lo, hi, 1001)
                )
                assert value <= grid + 1e-8
                checks.append(
                    {
                        "t": t,
                        "fitted_mean": fit,
                        "log_infimum_numerical": value,
                        "dense_grid_log_minimum": grid,
                    }
                )
            composite.append(value)
            point.append(known)
        if name.startswith("constant"):
            expected = float(np.sum(1 / np.sqrt(1 + np.arange(1, horizon + 1))) / horizon)
            np.testing.assert_allclose(np.exp(composite[-1]), expected, rtol=1e-12)

        def first(values):
            hits = np.flatnonzero(np.asarray(values) >= np.log(20))
            return int(hits[0] + 1) if len(hits) else None

        rows.append(
            {
                "case": name,
                "numerical_composite_first_crossing": first(composite),
                "known_zero_mean_first_crossing": first(point),
                "final_composite_log_statistic": composite[-1],
                "final_known_zero_log_statistic": point[-1],
                "optimizer_checks": checks,
            }
        )
    result = {
        "status": "completed",
        "rows": rows,
        "limits": "one path per case; numerical infimum is not certified lower bound, no experimental PFA validation or deployed detector guarantee",
    }
    (DOC / "nonpartitioned_pfa_results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
