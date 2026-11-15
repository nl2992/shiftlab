import json
from pathlib import Path

import numpy as np
import pytest

from shiftlab.paper3.riskbudget import BennettMixture
from shiftlab.paper3.riskbudget.bounds_v2 import CoinMixture

REC = Path(__file__).resolve().parents[3] / "outputs" / "paper3" / "riskbudget" / "test_records"


def _record(name, obj):
    try:
        REC.mkdir(parents=True, exist_ok=True)
        (REC / name).write_text(json.dumps(obj, indent=1, default=float))
    except OSError:
        pass


def test_basics():
    m = CoinMixture(0.05)
    assert m.D() == 0.0
    assert np.all(m.psi(1.0) == 0.0)
    m.add(1.0)
    assert m.D() == 0.0  # pi = 1 rounds never create width
    assert len(m.lams) == 5 and np.all(np.diff(m.lams) < 0)
    for pi in (0.05, 0.25, 0.5, 0.9):
        assert np.all(m.psi(pi) > 0)
    with pytest.raises(ValueError):
        CoinMixture(0.0)
    with pytest.raises(ValueError):
        m.psi(0.0)


def test_psi_matches_direct_formula_and_is_stable():
    m = CoinMixture(0.05, lams=[0.1, 0.5, 1.0])
    for pi in (0.2, 0.5, 0.8):
        r = 1 / pi - 1
        for i, lam in enumerate(m.lams):
            f1 = pi * np.exp(-lam * r) + (1 - pi) * np.exp(lam)
            f2 = pi * np.exp(lam * r) + (1 - pi) * np.exp(-lam)
            assert m.psi(pi)[i] == pytest.approx(np.log(max(f1, f2)), rel=1e-10)
    big = CoinMixture(0.05, lams=[50.0, 200.0])
    assert np.all(np.isfinite(big.psi(1e-3)))
    # psi bounds E exp(lam x (1 - q/pi)) for every x in [-1, 1] (checked on a grid)
    for pi in (0.2, 0.6):
        for lam in (0.3, 1.2):
            for x in np.linspace(-1, 1, 41):
                e = pi * np.exp(lam * x * (1 - 1 / pi)) + (1 - pi) * np.exp(lam * x)
                assert np.log(e) <= CoinMixture(0.05, lams=[lam]).psi(pi)[0] + 1e-12


def test_d_with_lookahead_and_monotone():
    a, b = CoinMixture(0.05), CoinMixture(0.05)
    for _ in range(7):
        a.add(0.5)
        b.add(0.5)
    ex = a.psi(0.25) + a.psi(0.5)
    la = a.D_with(ex, CoinMixture.cap_of(0.25) + CoinMixture.cap_of(0.5))
    b.add(0.25)
    b.add(0.5)
    assert la == pytest.approx(b.D())
    assert a.D_with(ex) >= la  # dropping the cap can only enlarge
    assert a.D_with(np.zeros(5)) == a.D()
    ds = []
    c = CoinMixture(0.05)
    for _ in range(60):
        c.add(0.5)
        ds.append(c.D())
    assert np.all(np.diff(ds) >= 0)


def _D_paths(delta, pis):
    """Deterministic pi path -> arrays of D_t (with cap) after each round."""
    m = CoinMixture(delta)
    psis = np.array([m.psi(p) for p in pis])
    caps = np.cumsum([CoinMixture.cap_of(p) for p in pis])
    Psi = np.cumsum(psis, 0)
    d = np.min(m._c[None, :] + Psi / m.lams[None, :], 1)
    return np.minimum(d, caps)


def _x_patterns(n, rng):
    t = np.arange(n)
    return {
        "all+1": np.ones(n),
        "all-1": -np.ones(n),
        "alternating": np.where(t % 2 == 0, 1.0, -1.0),
        "random": rng.choice([-1.0, 1.0], n),
        "blocks": np.where((t // 50) % 2 == 0, 1.0, -1.0),
        "uniform": rng.uniform(-1, 1, n),
    }


def test_monte_carlo_validity_and_width_improvement():
    reps, n = 4000, 600
    rng = np.random.default_rng(7)
    rates, worst = {}, 0.0
    for delta in (0.05, 0.1):
        tol = 3 * np.sqrt(delta * (1 - delta) / reps)
        pi_sets = {
            "pi=0.25": np.full(n, 0.25),
            "pi=0.5": np.full(n, 0.5),
            "pi=0.8": np.full(n, 0.8),
            "mixed": np.where(
                np.arange(n) % 3 == 0, 0.25, np.where(np.arange(n) % 3 == 1, 0.5, 1.0)
            ),
        }
        for pname, pis in pi_sets.items():
            D = _D_paths(delta, pis)
            for xname, x in _x_patterns(n, rng).items():
                q = rng.random((reps, n)) < pis[None, :]
                xi = x[None, :] * (1 - q / pis[None, :])
                M = np.cumsum(xi, 1)
                rate = float((M > D[None, :] + 1e-12).any(1).mean())
                rates[f"d={delta}|{pname}|{xname}"] = rate
                worst = max(worst, rate - delta)
                assert rate <= delta + tol, (delta, pname, xname, rate)
    # adaptive (predictable) pi: lower pi when the running martingale is positive
    m = CoinMixture(0.05)
    for xname in ("all+1", "all-1", "alternating"):
        x = _x_patterns(n, rng)[xname]
        Psi = np.zeros((reps, 5))
        cap = np.zeros(reps)
        M = np.zeros(reps)
        bad = np.zeros(reps, bool)
        for s in range(n):
            pi = np.where(M > 0, 0.25, 0.8)
            q = rng.random(reps) < pi
            M = M + x[s] * (1 - q / pi)
            lq, r = np.log1p(-pi), 1 / pi - 1
            lp = np.log(pi)
            a1 = np.logaddexp(lp[:, None] - m.lams * r[:, None], lq[:, None] + m.lams)
            a2 = np.logaddexp(lp[:, None] + m.lams * r[:, None], lq[:, None] - m.lams)
            Psi += np.maximum(a1, a2)
            cap += np.maximum(1.0, r)
            D = np.minimum(np.min(m._c + Psi / m.lams, 1), cap)
            bad |= M > D + 1e-12
        rates[f"adaptive|{xname}"] = float(bad.mean())
        assert bad.mean() <= 0.05 + 3 * np.sqrt(0.05 * 0.95 / reps)
    _record("bounds_v2_mc.json", {"reps": reps, "n": n, "crossing_rates": rates})
    print("max crossing rate over cells:", max(rates.values()))


def test_width_vs_v1():
    out = {}
    for delta in (0.05, 0.1):
        for pi in (0.25, 0.5, 0.8):
            for V in (16, 64, 256):
                n = V / (1 / pi - 1)
                m = CoinMixture(delta)
                m.Psi = m.psi(pi) * n
                m.cap = n * CoinMixture.cap_of(pi)
                g = np.sqrt(2 * V * np.log(1 / delta))
                v1 = BennettMixture(delta, pi).D(V)
                out[f"d={delta}|pi={pi}|V={V}"] = {
                    "n_rounds": n,
                    "gauss_ref": g,
                    "v2_over_ref": m.D() / g,
                    "v1_over_ref": v1 / g,
                    "v2_over_v1": m.D() / v1,
                }
                assert m.D() <= v1 + 1e-9, (delta, pi, V)
    _record("bounds_v2_width.json", out)
    r = [v["v2_over_v1"] for v in out.values()]
    print(f"v2/v1 width ratio: min {min(r):.3f} mean {np.mean(r):.3f} max {max(r):.3f}")
