"""Shin-Ramdas-Rinaldo e-detectors: T2 core identities, NBA reproduction, T3 adapter smoke tests."""
import csv
import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for p in (SOTA, SOTA / "competitors", ROOT / "scripts/failure_atlas_v2_flq"):
    sys.path.insert(0, str(p))

from regimes import REGIMES
from shin_esr import (
    BoundedMeanEDetector,
    TwoSidedESRDeploymentAdapter,
    algorithm3_grid,
    eq75_range,
    lambda_of_delta,
    psi_star_E,
    two_sided_bounded_grid,
)
from simulator import (
    ReleasedFeedback,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

# The NBA Cavaliers game log is third-party data (Saha-Ramdas repo CSV, same games as the paper). It is
# not vendored; the test reads it as DATA only if a local copy exists (env var or the checker scratch).
_DEFAULT_CAV = Path("/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-"
                    "shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/"
                    "check_edet/nonsep/cav.csv")
CAV = Path(os.environ.get("SHIFTLAB_NBA_CAV_CSV", _DEFAULT_CAV))


# ------------------------------------------------------------------ recursions, by hand
def _det(lams, w, kind="sr", **kw):
    return BoundedMeanEDetector(lams, w, m=0.5, kind=kind, threshold=1e9, **kw)


def test_recursions_hand_checked():
    # lambda 0.5, m 1/2, outcomes z = +1, -1, +1 -> increments 1.5, 0.5, 1.5 (eq (70): 1 + lam z)
    xs = [1.0, 0.0, 1.0]
    sr = _det([0.5], [1.0])
    seen = []
    for x in xs:
        sr.update(x)
        seen.append(sr.stat)
    assert seen == pytest.approx([1.5, 0.5 * 2.5, 1.5 * 2.25])  # (13): M_n = L_n (M_{n-1} + 1), M_0 = 0
    cu = _det([0.5], [1.0], kind="cusum")
    seen = []
    for x in xs:
        cu.update(x)
        seen.append(cu.stat)
    assert seen == pytest.approx([1.5, 0.75, 1.5])  # (14): M_n = L_n max(M_{n-1}, 1)
    # Remark 2.7 start weights pi = 1/4 on the first two starts only: S_n = L_n (S_{n-1} + pi_n)
    w = _det([0.5], [1.0], start_weight=0.25, max_starts=2)
    seen = []
    for x in xs:
        w.update(x)
        seen.append(w.stat)
    assert seen == pytest.approx([1.5 * 0.25, 0.5 * (0.375 + 0.25), 1.5 * 0.3125])


def test_initialisation_is_zero_not_one():
    d = _det([0.5], [1.0])
    assert d.log_stat == -math.inf  # M_0 = 0 (the paper's "M_0 := 1" sentence is a typo)
    d.update(0.5)  # x = m: increment 1, M_1 = 1 * (0 + 1) = 1
    assert d.stat == pytest.approx(1.0)


def test_mixture_equals_brute_force_sum_over_starts_and_lambdas():
    rng = np.random.default_rng(0)
    lams, w = np.array([0.5, 0.2, -0.3]), np.array([0.4, 0.35, 0.25])
    x = rng.random(40)
    det = _det(lams, w)
    cu = _det(lams, w, kind="cusum")
    for n in range(1, len(x) + 1):
        det.update(x[n - 1])
        cu.update(x[n - 1])
        inc = 1.0 + lams[:, None] * (x[None, :n] / 0.5 - 1.0)  # (lam, i)
        prods = np.array([np.prod(inc[:, j:], axis=1) for j in range(n)])  # (start, lam) = (12)
        assert det.stat == pytest.approx(float(w @ prods.sum(axis=0)))  # (10) SR, mixed as in (3.5)
        assert cu.stat == pytest.approx(float(w @ prods.max(axis=0)))  # (10) CUSUM, mixture of CUSUMs


def test_trivial_e_process_identities():
    # Lambda == 1 (lambda = 0): M^SR_n = n and M^CU_n = 1  (v4 p10)
    sr, cu = _det([0.0], [1.0]), _det([0.0], [1.0], kind="cusum")
    for n in range(1, 8):
        sr.update(0.9)
        cu.update(0.1)
        assert sr.stat == pytest.approx(n) and cu.stat == pytest.approx(1.0)


def test_argument_validation():
    with pytest.raises(ValueError):
        BoundedMeanEDetector([1.0], [1.0], threshold=1.0)
    with pytest.raises(ValueError):
        BoundedMeanEDetector([0.5], [0.9], threshold=1.0)
    with pytest.raises(ValueError):
        BoundedMeanEDetector([0.5], [1.0], kind="cusum", start_weight=0.5, threshold=1.0)
    with pytest.raises(ValueError):
        _det([0.5], [1.0]).update(1.2)


# ------------------------------------------------------------------ Algorithm 3
def test_eq75_numbers():
    dl, du = eq75_range(0.494, 0.0125)
    assert dl == pytest.approx(0.0241177, abs=1e-6) and du == pytest.approx(1599.77, abs=0.01)


def test_algorithm3_nba_grid():
    g = algorithm3_grid(1e-3, 0.024, 1600.0, 1000)
    lam, w = g["lambdas"], g["weights"]
    assert g["atom"] and g["K_alpha"] == 189 and len(lam) == 190  # paper: 190 baselines = K + atom
    assert g["g_alpha"] == pytest.approx(13.1928, abs=1e-3) and g["g_alpha"] > math.log(1e3)
    assert w.sum() == pytest.approx(1.0) and np.all(np.diff(lam) < 0)
    assert lam[0] == pytest.approx(1600 / 1601) and lam[-1] == pytest.approx(0.024 / 1.024)
    # interior points satisfy psi*(Delta_k) = D_U eta^{-k}; weights are equal on the interior (96)
    d_u = float(psi_star_E(1600.0))
    k = np.arange(1, 190)
    delta_k = lam[1:] / (1 - lam[1:])
    np.testing.assert_allclose(psi_star_E(delta_k), d_u * g["eta"] ** (-k), rtol=1e-8)
    assert np.allclose(w[1:], w[1]) and w[0] < w[1]


def test_algorithm3_single_baseline_and_monotone_in_alpha():
    g = algorithm3_grid(0.05, 0.1, 0.1)
    assert list(g["lambdas"]) == [pytest.approx(lambda_of_delta(0.1))] and g["weights"].tolist() == [1.0]
    assert algorithm3_grid(1e-4, 0.1, 1.0)["g_alpha"] > algorithm3_grid(1e-2, 0.1, 1.0)["g_alpha"]


# ------------------------------------------------------------------ NBA reproduction (data read only)
@pytest.mark.skipif(not CAV.exists(), reason="NBA Cavaliers CSV not available locally")
def test_nba_cavaliers_plus_minus_reproduction():
    rows = list(csv.DictReader(CAV.open()))
    assert len(rows) == 640
    x = (np.array([float(r["plus_minus"]) for r in rows]) + 80.0) / 160.0
    out = {}
    for kind in ("sr", "cusum"):
        g = algorithm3_grid(1e-3, 0.024, 1600.0, 1000)
        det = BoundedMeanEDetector(g["lambdas"], g["weights"], m=0.494, kind=kind,
                                   threshold=math.log(1e3))
        for i, xi in enumerate(x, 1):
            fired = det.update(xi)
            if kind == "cusum" and i == 444:
                out["cu444"] = det.stat
            if fired:
                out[kind] = (i, rows[i - 1]["date"])
                break
    assert out["sr"] == (378, "2015-03-10")  # paper Fig 3 (e-SR): game 378
    # Paper reports e-CUSUM at game 444 (2016-02-06). This port crosses one game later, as the
    # independent checker's port did (cause unidentified: data revision or g_alpha tolerance).
    assert out["cu444"] == pytest.approx(963.9, abs=0.1) and out["cu444"] < 1e3
    assert out["cusum"] == (445, "2016-02-08")


# ------------------------------------------------------------------ two-sided mixture (stcpR6)
def test_two_sided_mixture_detects_both_directions_symmetrically():
    lam, w = two_sided_bounded_grid(0.05, 0.5, 0.1, 1.0)
    assert w.sum() == pytest.approx(1.0) and (lam > 0).any() and (lam < 0).any()
    rng = np.random.default_rng(1)
    for p in (0.8, 0.2):
        d = BoundedMeanEDetector(lam, w, m=0.5, threshold=math.log(20))
        n = next((i for i in range(1, 400) if d.update(float(rng.random() < p))), None)
        assert n is not None and n < 150
    a, b = (BoundedMeanEDetector(lam, w, m=0.5, threshold=1e9) for _ in range(2))
    for x in rng.random(30) < 0.5:
        a.update(float(x))
        b.update(1.0 - float(x))
    assert a.stat == pytest.approx(b.stat)  # m = 1/2: the mixture is invariant to X -> 1 - X


# ------------------------------------------------------------------ adapter: statistics
def _fb(deployed, other_better, t_req=10, t_rel=10):
    l = np.zeros(2, dtype=np.int8)
    l[deployed] = int(other_better)
    l[1 - deployed] = int(not other_better)
    return ReleasedFeedback(event_id=t_req, t_requested=t_req, t_released=t_rel, label=0,
                            model_losses=l, query_probability=0.5)


def _adapter(**kw):
    kw.setdefault("calibration", "rmm_matched")
    return TwoSidedESRDeploymentAdapter(2000, 200, 0.05, rng=np.random.default_rng(0), **kw)


def _feed(ad, p_other_better, n, rng, t0=0):
    """Feed up to n labels; return the number consumed when the adapter switched, else None."""
    for i in range(n):
        ad.t = t0 + i
        before = ad.n_switches
        ad.observe([_fb(ad.deployed, rng.random() < p_other_better, t_req=t0 + i)])
        if ad.n_switches > before:
            return i + 1
    return None


@pytest.mark.parametrize("side", [0, 1])  # 0: promote side (incumbent deployed), 1: rollback side
def test_null_false_alarm_rate_rmm_matched_finite_horizon(side):
    reps, n = 800, 200
    rng = np.random.default_rng(10 + side)
    hits = 0
    for _ in range(reps):
        ad = _adapter()
        ad.deployed = side
        ad.det = ad._new_detector()
        hits += _feed(ad, 0.5, n, rng) is not None
    alpha_side = 0.025
    se = math.sqrt(alpha_side * (1 - alpha_side) / reps)
    assert hits / reps <= alpha_side + 3 * se


@pytest.mark.parametrize("side", [0, 1])
def test_null_false_alarm_rate_arl_calibration_short_horizon(side):
    # ARL calibration only bounds P(fire within n) by n * alpha_side (Markov on the e-detector).
    reps, n, alpha = 600, 15, 0.01
    rng = np.random.default_rng(20 + side)
    hits = 0
    for _ in range(reps):
        ad = TwoSidedESRDeploymentAdapter(2000, 200, alpha, rng=np.random.default_rng(0),
                                          calibration="arl")
        ad.deployed = side
        ad.det = ad._new_detector()
        hits += _feed(ad, 0.5, n, rng) is not None
    bound = n * alpha * 0.5
    assert hits / reps <= bound + 3 * math.sqrt(bound * (1 - bound) / reps)


def test_detects_large_change_on_both_sides_and_restarts():
    rng = np.random.default_rng(3)
    delays = []
    for _ in range(60):
        ad = _adapter()
        k = _feed(ad, 0.85, 200, rng)  # challenger better from the start: promote
        assert k is not None and ad.deployed == 1 and ad.n_promotions == 1
        delays.append(k)
        k2 = _feed(ad, 0.85, 200, rng, t0=500)  # now the deployed model is worse: rollback
        assert k2 is not None and ad.deployed == 0 and ad.n_rollbacks == 1
    assert np.median(delays) < 40


def test_restart_at_switch_resets_state_and_drops_inflight_labels():
    ad = _adapter()
    rng = np.random.default_rng(5)
    assert _feed(ad, 0.95, 100, rng) is not None
    assert ad.deployed == 1 and ad.det.n == 0 and np.all(np.isneginf(ad.det.log_m))
    assert ad.det.threshold == pytest.approx(math.log(1 / 0.025))
    t_sw = ad.t_switch
    ad.observe([_fb(1, True, t_req=t_sw)])  # requested at/before the switch event: dropped
    assert ad.det.n == 0 and ad.n_dropped_inflight == 1
    ad.observe([_fb(1, True, t_req=t_sw + 1)])
    assert ad.det.n == 1


def test_calibration_constants_and_options():
    m = _adapter(calibration="rmm_matched")
    assert m.det.max_starts == 200 and m.det.log_pi == pytest.approx(math.log(1 / 200))
    a = _adapter(calibration="arl")
    assert a.det.max_starts is None and a.det.log_pi == 0.0
    r = _adapter(bets="rmm")
    assert r.det.lam.tolist() == [0.15, 0.3, 0.5]
    with pytest.raises(ValueError):
        _adapter(calibration="x")
    with pytest.raises(ValueError):
        _adapter(bets="x")
    assert _adapter(side_alpha_fraction=1.0).det.threshold == pytest.approx(math.log(20))


# ------------------------------------------------------------------ adapter: simulator contract
def _stream(losses, seed):
    r = np.random.default_rng(seed)
    labels = r.integers(0, 2, losses.shape[0])
    return labels[:, None].astype(int) ^ losses.astype(int), labels


def _run(regime, seed, *, T=2000, budget=200, delay=100, **kw):
    losses = REGIMES[regime].sample(np.random.default_rng(1000 + seed), T)
    preds, labels = _stream(losses, 500 + seed)
    pol = TwoSidedESRDeploymentAdapter(T, budget, 0.05, rng=policy_rng(seed, 0, "esr"), **kw)
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                      label_price=0.05, switch_cost=5.0)
    return pol, res


@pytest.mark.parametrize("regime", ["F0_null", "F0_better", "F3_reversal_800"])
def test_adapter_budget_delay_determinism(regime):
    for seed in range(2):
        _pol, res = _run(regime, seed)
        assert check_budget_feasible(res, 200) == [] and check_no_future_access(res, 100) == []
        assert res.refused_requests == 0
        _pol2, res2 = _run(regime, seed)
        assert [r["deployed_model"] for r in res.records] == [r["deployed_model"] for r in res2.records]
        assert [r["requested"] for r in res.records] == [r["requested"] for r in res2.records]


def test_adapter_decisions_do_not_depend_on_future_events():
    T, t0 = 1200, 700
    base = REGIMES["F3_reversal_800"].sample(np.random.default_rng(42), T)
    other = base.copy()
    other[t0:] = REGIMES["F0_worse"].sample(np.random.default_rng(43), T)[t0:]
    pa, pb = _stream(base, 9), _stream(other, 9)
    runs = []
    for preds, labels in (pa, pb):
        pol = TwoSidedESRDeploymentAdapter(T, 200, 0.05, rng=policy_rng(3, 0, "esr"))
        runs.append(run_episode(pol, model_predictions=preds, labels=labels, delay=100, budget=200,
                                label_price=0.05, switch_cost=5.0))
    for key, upto in (("deployed_model", t0 + 1), ("requested", t0)):
        assert [r[key] for r in runs[0].records[:upto]] == [r[key] for r in runs[1].records[:upto]]


def test_adapter_null_promotion_rate_smoke_under_exact_null():
    # F0_null: both models equally good. rmm_matched promote side level 0.025; smoke-size check only.
    reps, hits = 150, 0
    for s in range(reps):
        pol, _ = _run("F0_null", s, T=800, budget=80, delay=20)
        hits += pol.n_promotions > 0
    p = 0.025
    assert hits / reps <= p + 3 * math.sqrt(p * (1 - p) / reps) + 0.02


def test_adapter_promotes_clear_advantage():
    wins = 0
    for s in range(5):
        pol, _ = _run("F0_better", s, T=2000, budget=200, delay=100)
        wins += pol.n_promotions >= 1
    assert wins >= 4  # qualitative smoke, not evidence of performance


def test_adapter_state_dict_roundtrip():
    pol, _ = _run("F3_reversal_800", 1, T=1000, delay=50)
    clone = TwoSidedESRDeploymentAdapter(1000, 200, 0.05, rng=policy_rng(9, 9, "esr"))
    clone.load_state_dict(pol.state_dict())
    assert (clone.deployed, clone.det.n) == (pol.deployed, pol.det.n)
    np.testing.assert_array_equal(clone.det.log_m, pol.det.log_m)
