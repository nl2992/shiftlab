"""Checks for the FLQ two-tier re-test regimes and registered analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in ("scripts/promising_directions/sota", "scripts/sota_sprint", "scripts/p2_benchmark"):
    sys.path.insert(0, str(ROOT / p))

import analyze_two_tier as A


def test_new_regimes_register_and_differ():
    import bench
    import two_tier_regimes as R

    assert set(R.NEW) <= set(bench.SPRINT_REGIMES)
    keys = ("p", "dis", "rho", "burst", "delay")
    old = {
        tuple(getattr(r, a) for a in keys)
        for k, r in bench.SPRINT_REGIMES.items()
        if k not in R.NEW and all(hasattr(r, a) for a in keys)
    }
    for r in R.NEW.values():
        assert (r.p, r.dis, r.rho, r.burst, r.delay) not in old, r.name
    # nulls have zero marginal advantage; alternatives favour the challenger
    for name in ("N_null", "N_null_dep_r7", "N_null_dep_r9"):
        assert np.allclose(R.NEW[name].truth_gain(), 0.0)
    for name in A.REGION:
        assert R.NEW[name].truth_gain().min() > 0


def test_simultaneous_upper_covers_and_is_wider_than_pointwise():
    rng = np.random.default_rng(0)
    cover = 0
    for _ in range(200):
        d = rng.normal(0.0, 1.0, size=(200, 6))
        ub = A.simultaneous_upper(d, np.random.default_rng(1))
        cover += bool((ub >= 0).all())
        se = d.std(0, ddof=1) / np.sqrt(200)
        assert (ub >= d.mean(0) + 1.64 * se - 1e-9).all()
    assert cover / 200 >= 0.9


def _write(tmp: Path, plan: dict, net_fn, promo_fn) -> Path:
    tmp.mkdir()
    with open(tmp / "records.jsonl", "w") as f:
        for rg, n in plan.items():
            for s in range(n):
                f.writelines(json.dumps({"regime": rg, "seed": s, "policy": pol,
                                        "net": net_fn(rg, s, pol),
                                        "ever_promote": promo_fn(rg, s, pol)}) + "\n" for pol in A.POLICIES)  # fmt: skip
    return tmp


def test_analysis_rules_end_to_end(tmp_path, monkeypatch):
    small = {k: 40 for k in A.TIER_A}
    monkeypatch.setattr(A, "TIER_A", small)
    for name in ("TIER_B", "REGION", "REPLICATION", "OUTSIDE"):
        monkeypatch.setattr(A, name, {k: 30 for k in getattr(A, name)})
    rng = np.random.default_rng(3)
    noise = {}

    def net(rg, s, pol):
        key = (rg, s, pol)
        noise.setdefault(key, rng.normal(0, 1))
        better = pol in A.CANDIDATES and rg in A.REGION
        return 400.0 + noise[key] - (20.0 if better else 0.0)

    plan = {**A.TIER_A, **A.TIER_B, **A.REGION, **A.REPLICATION, **A.OUTSIDE}
    d = _write(tmp_path / "r", plan, net, lambda rg, s, pol: 0)
    cells = A.load([d])
    A.check(cells, plan)
    res = A.analyse(cells)
    prim = res["candidates"][A.PRIMARY]
    assert prim["tier_a_pass"] and prim["tier_b_pass"]
    assert prim["region_wins"] == 6 and prim["replication_wins"] == 0
    assert res["primary_verdict"] == "SUPPORTED"
    assert "SUPPORTED" in A.markdown(res)


def test_check_fails_closed_on_missing_policy(tmp_path):
    plan = {"V_null": 2}
    d = _write(tmp_path / "r", plan, lambda *a: 1.0, lambda *a: 0)
    lines = (d / "records.jsonl").read_text().splitlines()[:-1]
    (d / "records.jsonl").write_text("\n".join(lines) + "\n")
    with pytest.raises(SystemExit):
        A.check(A.load([d]), plan)
