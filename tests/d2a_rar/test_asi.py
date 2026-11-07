"""Tests for the ASI (Zrnic & Candes 2024) mean-estimation PAPER_RECONSTRUCTION and its streaming port."""

import math

import numpy as np
import pytest

from shiftlab.sota.asi import (
    PrPlEB,
    SequentialRule,
    StreamingASI,
    active_mean,
    batch_active_inference,
    batch_rule,
    classical_mean,
    ipw_increments,
    oracle_rule,
    uncertainty_binary,
    uncertainty_multiclass,
    uniform_ppi,
)


def _population(n, rng, noise=0.0):
    """Binary labels from a logistic truth; the model sees p (optionally noisy) and predicts the likely class."""
    x = rng.normal(size=n)
    p_true = 1 / (1 + np.exp(-2.0 * x))
    y = (rng.random(n) < p_true).astype(float)
    p_model = np.clip(p_true + noise * rng.normal(size=n), 0.01, 0.99)
    f = (p_model > 0.5).astype(float)
    return y, f, p_model


def test_uncertainty_measures():
    assert uncertainty_binary(np.array([0.5, 0.0, 1.0, 0.25])) == pytest.approx(
        [1.0, 0.0, 0.0, 0.5]
    )
    p = np.array([[1 / 3, 1 / 3, 1 / 3], [1.0, 0.0, 0.0]])
    assert uncertainty_multiclass(p) == pytest.approx([1.0, 0.0])
    assert uncertainty_multiclass(np.array([[0.5, 0.5]])) == pytest.approx(
        uncertainty_binary(np.array([0.5]))
    )


def test_ipw_unbiased_over_labelling_randomness():
    """E_xi[theta_hat] = mean(Y) exactly, whatever f and pi>0 (Sec 3 / Eq. 5)."""
    rng = np.random.default_rng(0)
    y, f, pm = _population(300, rng, noise=0.2)
    u = uncertainty_binary(pm)
    pi = batch_rule(u, n_b=40, tau=0.3)
    assert (pi > 0).all() and (pi <= 1).all()
    ests = []
    for _ in range(6000):
        xi = (rng.random(len(pi)) < pi).astype(float)
        ests.append(ipw_increments(f, y, xi, pi).mean())
    ests = np.array(ests)
    se = ests.std(ddof=1) / math.sqrt(len(ests))
    assert abs(ests.mean() - y.mean()) < 4 * se


def test_unlabelled_y_never_used():
    f, pi = np.array([0.2, 0.7]), np.array([0.5, 0.5])
    a = ipw_increments(f, np.array([1.0, 1.0]), np.array([0.0, 1.0]), pi)
    b = ipw_increments(f, np.array([-99.0, 1.0]), np.array([0.0, 1.0]), pi)
    assert np.allclose(a, b)
    with pytest.raises(ValueError):
        ipw_increments(f, f, np.array([1, 1]), np.array([0.0, 0.5]))


def test_batch_budget_and_positivity():
    rng = np.random.default_rng(1)
    _, _, pm = _population(2000, rng)
    u = uncertainty_binary(pm)
    for tau in (0.0, 0.5, 1.0):
        pi = batch_rule(u, 200, tau)
        assert pi.sum() <= 200 + 1e-9
        assert (pi >= tau * 200 / 2000 - 1e-12).all()
    assert (batch_rule(u, 200, 0.5) > 0).all()


def test_batch_coverage_and_width_ordering():
    """Coverage ~ 1-alpha (Prop 1, asymptotic) and width ordering active <= uniform-PPI <= classical when f is informative."""
    rng = np.random.default_rng(2)
    n, n_b, alpha, trials = 3000, 300, 0.1, 500
    y, f, pm = _population(n, rng, noise=0.05)
    u = uncertainty_binary(pm)
    truth = y.mean()  # finite-population target; randomness is the labelling decisions
    cov = {"active": 0, "ppi": 0, "classical": 0}
    wid = {"active": [], "ppi": [], "classical": []}
    for _ in range(trials):
        for name, r in (
            ("active", batch_active_inference(f, y, u, n_b, 0.3, rng, alpha)),
            ("ppi", uniform_ppi(f, y, n_b, rng, alpha)),
            ("classical", classical_mean(y, n_b, rng, alpha)),
        ):
            cov[name] += r.ci[0] <= truth <= r.ci[1]
            wid[name].append(r.ci[1] - r.ci[0])
    for name in ("active", "ppi"):
        assert 0.85 <= cov[name] / trials <= 0.95, (name, cov[name] / trials)
    assert np.mean(wid["active"]) <= np.mean(wid["ppi"]) <= np.mean(wid["classical"])


def test_uniform_pi_recovers_ppi_variance():
    rng = np.random.default_rng(3)
    n, n_b = 2000, 200
    y, f, _ = _population(n, rng, noise=0.1)
    ests = [uniform_ppi(f, y, n_b, rng).estimate for _ in range(3000)]
    p = n_b / n
    theory = (
        np.mean((y - f) ** 2) * (1 / p - 1)
    ) / n  # finite-population variance of the labelling randomness
    assert np.var(ests, ddof=1) == pytest.approx(theory, rel=0.12)


def test_oracle_rule_minimises_variance_proxy():
    rng = np.random.default_rng(4)
    g = rng.uniform(0.01, 1.0, size=500)  # E[(Y-f)^2 | X]
    budget = 50.0
    pi_or = oracle_rule(g, budget)
    assert pi_or.sum() == pytest.approx(budget)
    v = lambda pi: float(np.sum(g / pi))
    uni = np.full(500, budget / 500)
    assert v(pi_or) < v(uni)
    assert (
        v(pi_or) <= v(np.clip(g * budget / g.sum(), 1e-6, 1)) + 1e-9
    )  # proportional-to-g is worse than sqrt(g)
    assert (pi_or <= 1).all()


def test_sequential_unbiased_covering_and_budget():
    rng = np.random.default_rng(5)
    n, n_b, alpha, trials = 1500, 150, 0.1, 400
    cover, nl = 0, []
    ests = []
    for _ in range(trials):
        x = rng.normal(size=n)
        p = 1 / (1 + np.exp(-2.0 * x))
        y = (rng.random(n) < p).astype(float)
        pm = np.clip(p + 0.05 * rng.normal(size=n), 0.01, 0.99)
        f = (pm > 0.5).astype(float)
        u = uncertainty_binary(pm)
        rule = SequentialRule(n=n, n_b=n_b, tau=0.5, fill_every=100)
        pis, xis = np.empty(n), np.empty(n)
        for t in range(n):
            pis[t] = rule.propose(u[t])
            xis[t] = float(rng.random() < pis[t])
            rule.record(int(xis[t]), u[t])
        assert (pis >= 0.5 * n_b / n - 1e-12).all()
        r = active_mean(f, y, xis, pis, alpha)
        theta = (
            p.mean()
        )  # E[Y_t] is p_t; target = mean of the superpopulation conditional probabilities
        cover += r.ci[0] <= p.mean() <= r.ci[1]
        ests.append(r.estimate - theta)
        nl.append(r.n_labelled)
    assert 0.84 <= cover / trials <= 0.96, cover / trials
    se = np.std(ests, ddof=1) / math.sqrt(trials)
    assert abs(np.mean(ests)) < 4 * se
    assert np.mean(nl) <= n_b * 1.1  # expected-budget rule, not a pathwise cap


# ---------------------------------------------------------------- streaming port


def test_prpleb_cs_time_uniform_coverage():
    """WSR Thm 2 two-sided CS: P(exists t: mu not in C_t) <= alpha (MC over horizon 300)."""
    rng = np.random.default_rng(6)
    alpha, trials, T = 0.1, 400, 300
    miss = 0
    for _ in range(trials):
        proc = PrPlEB(alpha)
        mu = 0.3
        bad = False
        for x in (rng.random(T) < mu).astype(float):
            proc.update(x)
            lo, hi = proc.cs()
            if not lo <= mu <= hi:
                bad = True
                break
        miss += bad
    assert miss / trials <= alpha + 3 * math.sqrt(alpha * 0.9 / trials)


def test_streaming_null_validity_with_delays_and_conditional_drift():
    """One-sided H0_cond: E[d_t | past] <= h. True conditional mean DRIFTS BELOW the hurdle (still null). Random delays;
    queries at propensity pi_t, f_t = causal running mean of released labels."""
    rng = np.random.default_rng(7)
    alpha, trials, T, h = 0.1, 300, 400, 0.1
    alarms = 0
    for _ in range(trials):
        mon = StreamingASI(d_lo=-1.0, d_hi=1.0, pi_min=0.1, alpha=alpha, hurdle=h)
        released: list[float] = []
        pending: list[tuple[int, int, float]] = []  # (release_round, round, d)
        for t in range(1, T + 1):
            for r in [p for p in pending if p[0] <= t]:
                mon.resolve(r[1], r[2])
                released.append(r[2])
                pending.remove(r)
            mean_t = h - 0.2 * (t / T)  # conditional mean <= h
            d = float(np.clip(mean_t + rng.choice([-0.5, 0.5]), -1, 1))
            f = float(np.mean(released)) if released else 0.0
            pi = 0.1 + 0.3 * rng.random()
            q = rng.random() < pi
            mon.register(t, f, pi, q)
            if q:
                pending.append((t + int(rng.integers(0, 15)), t, d))
        alarms += mon.alarm()
    assert alarms / trials <= alpha + 3 * math.sqrt(alpha * 0.9 / trials)


def test_streaming_power_and_in_order_consumption():
    rng = np.random.default_rng(8)
    mon = StreamingASI(d_lo=-1.0, d_hi=1.0, pi_min=0.2, alpha=0.05, hurdle=0.0)
    # round 1 queried but unreleased blocks later rounds
    mon.register(1, 0.0, 0.5, True)
    for t in range(2, 6):
        mon.register(t, 0.0, 0.5, False)
    assert mon.n_consumed == 0
    mon.resolve(1, 0.4)
    assert mon.n_consumed == 5
    # power: mean gain 0.5 >> hurdle
    for t in range(6, 3000):
        q = rng.random() < 0.5
        mon.register(t, 0.3, 0.5, q)
        if q:
            mon.resolve(t, float(np.clip(0.5 + rng.choice([-0.4, 0.4]), -1, 1)))
        if mon.alarm():
            break
    assert mon.alarm()
    lo, hi = mon.cs()
    assert lo < 0.5 < hi


def test_streaming_rejects_bad_propensity():
    mon = StreamingASI(d_lo=-1, d_hi=1, pi_min=0.2)
    with pytest.raises(ValueError):
        mon.register(1, 0.0, 0.05, True)


def test_common_contract_adapter_runs_and_passes_audit():
    """COMMON_CONTRACT_PORT smoke: audited paired run on a dev family (integrity only, no performance claim)."""
    from shiftlab.bench.contract import (
        BudgetSpec,
        ClockSpec,
        EnvSpec,
        load_cost_vectors,
        load_family,
        run_paired,
    )
    from shiftlab.bench.contract.adapters_asi import ASIAdapter

    spec = load_family("iid_shift_d10")
    env = EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()["balanced"],
        budget=BudgetSpec(label_cap=50),
        clocks=ClockSpec(retrain_duration=20),
    )
    assert ASIAdapter.port_status == "COMMON_CONTRACT_PORT"
    assert set(ASIAdapter.vocabulary) <= set(env.allowed_actions)
    pr = run_paired(
        {"m": lambda: ASIAdapter.build(env)}, spec, env, seeds=range(110_900_000, 110_900_002)
    )  # verify_run inside
    assert len(pr.runs["m"]) == 2
