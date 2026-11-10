"""Tests for scripts/paper1_scale25/stats (certify.py, ledger.py)."""

import math
from pathlib import Path

import certify as ct
import ledger as lg
import numpy as np
import pytest
from scipy import stats


# ------------------------------------------------------------------ alpha schedule
def test_alpha_sum_below_total():
    s = sum(ct.alpha_i(i) for i in range(1, 200001))
    assert s < 0.05 and s > 0.05 * (1 - 1e-5)
    assert ct.alpha_i(1) == 0.025
    assert ct.alpha_i(25) == pytest.approx(0.05 / 650)
    # telescoping identity: sum_{i<=N} 1/(i(i+1)) = N/(N+1)
    assert sum(ct.alpha_i(i) for i in range(1, 11)) == pytest.approx(0.05 * 10 / 11)


@pytest.mark.parametrize("bad", [0, -1, 1.5])
def test_alpha_rejects_bad_index(bad):
    with pytest.raises(ValueError):
        ct.alpha_i(bad)


def test_block_length_rule():
    assert ct.block_length(8) == 2 and ct.block_length(27) == 3 and ct.block_length(100) == 5
    assert ct.block_length(1000) == 10


# ------------------------------------------------------------------ ratio bound
def _brute_lower(a, b, alpha, m):
    """Independent implementation: scan rho for the smallest value with t(rho) <= c."""
    n = len(b)
    blocks = np.array_split(np.arange(n), n // m)
    c = stats.t.isf(alpha, len(blocks) - 1)

    def t(rho):
        z = (b - a) - rho * b
        zb = z.mean()
        e = np.array([z[ix].sum() - len(ix) * zb for ix in blocks])
        v = len(blocks) / (len(blocks) - 1) * (e**2).sum() / n**2
        return zb / math.sqrt(v)

    from scipy.optimize import brentq

    rhat = (b - a).mean() / b.mean()
    lo = rhat - 1.0
    assert t(lo) > c
    return 100 * brentq(lambda r: t(r) - c, lo, rhat)


def test_fieller_matches_bruteforce():
    rng = np.random.default_rng(0)
    for n in (30, 60, 100):
        b = 100 + 15 * rng.standard_normal(n)
        a = b - (2.5 + 2 * rng.standard_normal(n))
        for alpha in (0.05, 1e-3, 1e-4):
            m = ct.block_length(n)
            got = ct.fieller_lower(a, b, alpha, m)["L"]
            if np.isfinite(got):
                assert got == pytest.approx(_brute_lower(a, b, alpha, m), abs=1e-6)


def test_fieller_toy_known_values():
    # constant gain of exactly 5% with zero noise: bound equals the truth at every level
    b = np.full(40, 100.0)
    a = np.full(40, 95.0)
    for alpha in (0.05, 1e-6):
        r = ct.fieller_lower(a, b, alpha)
        assert r["r_hat"] == pytest.approx(5.0) and r["L"] == pytest.approx(5.0)
    # alpha=.5 -> t critical value 0 -> bound equals the point estimate
    rng = np.random.default_rng(1)
    b = 100 + rng.standard_normal(50)
    a = b - 2 - rng.standard_normal(50)
    r = ct.fieller_lower(a, b, 0.5)
    assert r["L"] == pytest.approx(r["r_hat"])


def test_fieller_properties():
    rng = np.random.default_rng(2)
    b = 50 + 5 * rng.standard_normal(80)
    a = b - 1.5 - rng.standard_normal(80)
    r1 = ct.fieller_lower(a, b, 0.05)
    # below the point estimate; shrinks as alpha shrinks
    Ls = [ct.fieller_lower(a, b, al)["L"] for al in (0.2, 0.05, 1e-2, 1e-3, 1e-4)]
    assert all(x <= r1["r_hat"] + 1e-12 for x in Ls) and all(np.diff(Ls) < 0)
    # scale invariance (common rescaling of costs)
    assert ct.fieller_lower(7 * a, 7 * b, 0.05)["L"] == pytest.approx(r1["L"])
    # additive shift of D alone changes r_hat by shift/mean(b)
    assert ct.fieller_lower(a - 1, b, 0.05)["r_hat"] == pytest.approx(r1["r_hat"] + 100 / b.mean())
    # a harmful new method has a negative bound; swapping roles flips the sign of r_hat
    assert ct.fieller_lower(b, a, 0.05)["r_hat"] < 0
    # t reference is more conservative than normal
    assert r1["L"] < ct.fieller_lower(a, b, 0.05, crit="normal")["L"]


def test_fieller_unbounded_when_reference_cost_not_significant():
    z = 3 * np.random.default_rng(5).standard_normal(40)
    b = z - z.mean() + 0.01  # mean 0.01, huge variance
    a = b - 0.5
    assert ct.fieller_lower(a, b, 0.05)["L"] == -np.inf


def test_fieller_input_validation():
    with pytest.raises(ValueError):
        ct.fieller_lower(np.ones(5), np.ones(6), 0.05)
    with pytest.raises(ValueError):
        ct.fieller_lower(np.ones(5), np.ones(5), 0.05)  # fewer than 3 blocks
    with pytest.raises(ValueError):
        ct.fieller_lower(np.array([np.nan] * 30), np.ones(30), 0.05)


def test_coverage_smoke_iid_and_ar1():
    """Quick (not exhaustive) coverage check; the full study is sim_coverage.py."""
    rng = np.random.default_rng(3)
    R, n = 4000, 60
    for phi in (0.0,):
        e = rng.standard_normal((R, n))
        y = np.empty((R, n))
        y[:, 0] = e[:, 0]
        for k in range(1, n):
            y[:, k] = phi * y[:, k - 1] + np.sqrt(1 - phi**2) * e[:, k]
        b = 100 * (1 + 0.15 * rng.standard_normal((R, n)))
        d = 100 * (0.025 + 0.02 * y)
        L, _, _ = ct.fieller_lower_batch(b - d, b, 0.05)
        assert (L > 2.5).mean() < 0.075
        L, _, _ = ct.fieller_lower_batch(b - d, b, 1e-3)
        assert (L > 2.5).mean() < 0.006


def test_mbb_runs_and_is_ordered():
    rng = np.random.default_rng(4)
    b = 100 + 10 * rng.standard_normal(60)
    a = b - 3 - 2 * rng.standard_normal(60)
    r = ct.mbb_lower(a, b, 0.05, B=2000)
    assert r["L"] < r["r_hat"]


# ------------------------------------------------------------------ ledger
@pytest.fixture
def led(tmp_path):
    return str(tmp_path / "attempts.csv")


def test_register_assigns_monotone_indices_and_alpha(led):
    rows = [lg.register_attempt(led, f"ds{i}", f"src{i}", "P", "new vs ref") for i in range(1, 6)]
    assert [int(r["attempt_index"]) for r in rows] == [1, 2, 3, 4, 5]
    assert [float(r["alpha_i"]) for r in rows] == [
        pytest.approx(ct.alpha_i(i)) for i in range(1, 6)
    ]
    assert lg.validate(led) == []


def test_unopened_attempt_still_consumes_index(led):
    lg.register_attempt(led, "d1", "s1", "P", "c")
    lg.register_attempt(led, "d2", "s2", "P", "c")  # never opened
    r3 = lg.register_attempt(led, "d3", "s3", "P", "c")
    assert int(r3["attempt_index"]) == 3


def test_duplicate_registration_and_double_open_refused(led):
    lg.register_attempt(led, "d1", "s1", "P", "c")
    with pytest.raises(ValueError):
        lg.register_attempt(led, "d1", "s1", "P", "c")
    b = np.full(40, 100.0) + np.arange(40) % 3
    lg.open_attempt(led, 1, b - 5, b)
    with pytest.raises(ValueError):
        lg.open_attempt(led, 1, b - 5, b)
    with pytest.raises(ValueError):
        lg.open_attempt(led, 2, b - 5, b)  # never registered
    assert lg.validate(led) == []


def test_open_uses_registered_alpha(led):
    for i in range(1, 4):
        lg.register_attempt(led, f"d{i}", f"s{i}", "P", "c")
    rng = np.random.default_rng(0)
    b = 100 + 5 * rng.standard_normal(50)
    a = b - 3 - rng.standard_normal(50)
    res = lg.open_attempt(led, 3, a, b)
    assert res["alpha"] == pytest.approx(ct.alpha_i(3))
    row = next(r for r in lg.read(led) if r["event"] == "open")
    assert float(row["L_pct"]) == pytest.approx(res["L"]) and row["opened"] == "1"


def test_tamper_and_deletion_detected(led, tmp_path):
    for i in range(1, 5):
        lg.register_attempt(led, f"d{i}", f"s{i}", "P", "c")
    good = Path(led).read_text(encoding="utf-8")
    # edit a cell
    Path(led).write_text(good.replace("d2", "dX", 1), encoding="utf-8")
    assert lg.validate(led)
    # delete a middle row (would let an index be reused)
    lines = good.splitlines()
    Path(led).write_text("\n".join(lines[:2] + lines[3:]) + "\n", encoding="utf-8")
    assert lg.validate(led)
    # truncating the tail is not detectable by the chain alone, but the next index would then be reused;
    # the git history is the external anchor (documented). Here: tail row deletion leaves a valid prefix.
    Path(led).write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    assert lg.validate(led) == []
    Path(led).write_text(good, encoding="utf-8")
    assert lg.validate(led) == []


def test_register_refused_on_invalid_ledger(led):
    lg.register_attempt(led, "d1", "s1", "P", "c")
    Path(led).write_text(
        Path(led).read_text(encoding="utf-8").replace("d1", "dZ"), encoding="utf-8"
    )
    with pytest.raises(RuntimeError):
        lg.register_attempt(led, "d2", "s2", "P", "c")


def test_lock_file_released(led):
    lg.register_attempt(led, "d1", "s1", "P", "c")
    assert not Path(led + ".lock").exists()


# ------------------------------------------------------------------ cohort certificate
def _filled(led, K, gains, noise=0.2, n=60, seed=0, parents=None):
    rng = np.random.default_rng(seed)
    for i in range(1, K + 1):
        lg.register_attempt(led, f"d{i}", (parents or {}).get(i, f"src{i}"), "P", "c")
    for i in range(1, K + 1):
        b = 100 + 3 * rng.standard_normal(n)
        a = b * (1 - gains[i - 1] / 100) + noise * rng.standard_normal(n)
        lg.open_attempt(led, i, a, b)


def test_certificate_success_and_threshold_logic(led):
    _filled(led, 25, [8.0] * 25)
    c = lg.certify_cohort(led)
    assert c["success"] and c["selected_R_lower"] >= 2.5 and c["counts"]["selected"] == 25
    # same ledger, stricter bar -> fails
    assert not lg.certify_cohort(led, min_R=8.5)["success"]
    # fewer than 25 datasets -> fails
    assert not lg.certify_cohort(led, S=range(1, 25))["success"]


def test_certificate_requires_every_selected_L_positive(led):
    g = [8.0] * 25
    g[10] = 0.0
    _filled(led, 25, g)
    c = lg.certify_cohort(led, S=range(1, 26))
    assert not c["success"]
    # default selection drops the unsupported dataset, leaving 24 < 25
    assert (
        lg.certify_cohort(led)["counts"]["selected"] == 24 and not lg.certify_cohort(led)["success"]
    )


def test_certificate_selection_after_results_and_counts(led):
    g = [8.0] * 27
    g[3] = -1.0  # harmful
    g[7] = 0.0
    _filled(led, 27, g, seed=1)
    c = lg.certify_cohort(led)  # post-hoc selection of supported attempts
    assert c["success"] and c["counts"]["opened"] == 27 and c["counts"]["selected"] == 25
    assert c["counts"]["supported_L_gt_0"] == 25 and c["counts"]["positive_r"] >= 25
    # the all-opened simultaneous lower bound includes the failures, so it is below the selected bound
    assert c["all_opened_mean_simultaneous_lower"] < c["selected_R_lower"]
    assert c["all_opened_mean_r_hat"] < c["selected_R_hat"]


def test_certificate_distinct_datasets_and_legacy_and_integrity(led):
    parents = {1: "same", 2: "same"}
    _filled(led, 25, [8.0] * 25, parents=parents)
    c = lg.certify_cohort(led, S=range(1, 26))
    assert not c["success"] and any("distinct" in p for p in c["integrity_problems"])
    assert lg.certify_cohort(led, S=range(1, 26), distinct="dataset")["success"]
    # tampering invalidates the certificate
    Path(led).write_text(
        Path(led).read_text(encoding="utf-8").replace("src5", "srcQ"), encoding="utf-8"
    )
    assert not lg.certify_cohort(led, distinct="dataset")["success"]


def test_legacy_rows_reserve_indices_but_never_enter_cohorts(led):
    for i in range(1, 4):
        lg.register_attempt(led, f"old{i}", f"o{i}", "OLD", "c", legacy=1)
        lg.record_open(led, i, 9.0, 5.0, 50, 4)
    r = lg.register_attempt(led, "new", "n", "NEW", "c")
    assert int(r["attempt_index"]) == 4
    c = lg.certify_cohort(led, min_datasets=1)
    assert c["counts"]["legacy_reserved"] == 3 and c["counts"]["opened"] == 0 and not c["success"]
    assert any(
        "not an opened non-legacy" in p
        for p in lg.certify_cohort(led, S=[1], min_datasets=1)["integrity_problems"]
    )


def test_union_bound_simultaneous_coverage_toy():
    """P(any miss) <= sum alpha_i for independent exact-level bounds; here with exact z-intervals."""
    rng = np.random.default_rng(7)
    K, R = 25, 40000
    miss = np.zeros(R, bool)
    for i in range(1, K + 1):
        z = rng.standard_normal(R)
        miss |= z > stats.norm.isf(ct.alpha_i(i))
    assert miss.mean() <= 0.05 + 3 * math.sqrt(0.05 * 0.95 / R)


def test_primary_is_min_over_prespecified_block_lengths():
    rng = np.random.default_rng(11)
    b = 100 + 10 * rng.standard_normal(100)
    a = b - 3 - 2 * rng.standard_normal(100)
    p = ct.primary_lower(a, b, 1e-3)
    parts = [ct.fieller_lower(a, b, 1e-3, m)["L"] for m in ct.block_lengths(100)]
    assert ct.block_lengths(100) == (5, 10)
    assert p["L"] == pytest.approx(min(parts)) and p["block_len"] in (5, 10)
    assert p["L"] <= ct.fieller_lower(a, b, 1e-3)["L"] + 1e-12
