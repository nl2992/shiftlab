"""Tests for the Gong & Zhang (ICML 2026) PAPER_RECONSTRUCTION and its label-acquisition port."""

import math

import numpy as np
import pytest

from shiftlab.sota.gong_zhang import (
    LinearPolicyGame,
    MetaController,
    OracleEfficientPaid,
    PaidExp4,
    PaidLabelAcquirer,
    eta_limited,
    eta_sufficient,
    eta_thm21,
    free_budget_threshold,
    obs_prob_paid,
    random_subset_budget,
    run_paid,
)

A, P, T = 3, 10, 2000


def test_observation_probability_formula_and_cost_limits():
    q, c = np.array([0.2, 0.5, 0.3]), np.array([0.1, 0.4, 2.0])
    eta = 0.7
    p = obs_prob_paid(eta, q, c)
    assert p == pytest.approx(
        np.minimum(1.0, np.sqrt(eta * q / c))
    )  # SQUARE ROOT form (Alg 1 line 7, read from page image)
    assert ((p >= 0) & (p <= 1)).all()
    assert (obs_prob_paid(eta, q, np.full(3, 1e-9)) == 1.0).all()  # c -> 0: full information


def test_schedules_match_printed_formulas():
    T_, c, A_, P_ = 1000, 0.3, 3, 10
    ln = math.log(P_)
    assert eta_thm21(100, 50.0, ln) == pytest.approx(
        1 / ((50.0 / ln) ** (2 / 3) + math.sqrt(100 / ln))
    )
    assert eta_limited(64, c, A_, P_) == pytest.approx(
        c ** (-1 / 3) * A_ ** (-1 / 3) * ln ** (2 / 3) * 64 ** (-2 / 3)
    )
    assert eta_sufficient(T_, 500, A_, P_, "printed") == pytest.approx(
        math.sqrt(500 / (A_ * ln)) / T_
    )
    assert eta_sufficient(T_, 500, A_, P_, "balanced") == pytest.approx(
        math.sqrt(500 * ln / A_) / T_
    )
    assert free_budget_threshold(c, A_, P_, T_) == pytest.approx(
        1.5 * c ** (-2 / 3) * (A_ * ln) ** (1 / 3) * T_ ** (2 / 3)
    )


def test_meta_controller_switches_at_threshold():
    thr = free_budget_threshold(0.3, A, P, T)
    lo = MetaController(A, P, T, int(thr) - 1, 0.3, rng=np.random.default_rng(0))
    hi = MetaController(A, P, T, math.ceil(thr), 0.3, rng=np.random.default_rng(0))
    assert (lo.mode, hi.mode) == ("free_II", "free_I")


def test_algorithm5_exact_budget_and_uniform_marginals():
    rng = np.random.default_rng(1)
    O = random_subset_budget(3, 50, 20, rng)
    assert O.sum() == 20 and O.shape == (50, 3)
    per = O.sum(0)
    assert per.max() - per.min() <= 1  # m or m+1 rounds per action
    marg = np.mean([random_subset_budget(3, 40, 17, rng) for _ in range(3000)], axis=0)
    assert np.abs(marg - 17 / (3 * 40)).max() < 0.03  # P(a in O_t) = B/(|A|T)
    with pytest.raises(ValueError):
        random_subset_budget(3, 10, 31, rng)


def test_importance_weighted_estimator_unbiased_and_expected_cost():
    rng = np.random.default_rng(2)
    q, c, loss = np.array([0.1, 0.6, 0.3]), np.array([0.3, 0.8, 0.2]), np.array([0.9, 0.2, 0.5])
    p = obs_prob_paid(0.5, q, c)
    obs = rng.random((200000, 3)) < p
    lhat = np.where(obs, loss / p, 0.0)
    se = lhat.std(0, ddof=1) / math.sqrt(len(lhat))
    assert (np.abs(lhat.mean(0) - loss) < 4 * se).all()
    cost = (obs * c).sum(1)
    assert abs(cost.mean() - float(np.sum(p * c))) < 4 * cost.std(ddof=1) / math.sqrt(len(cost))


def test_alg4_budget_exact_and_alg6_excess_is_paid():
    g = LinearPolicyGame(600, 4, A, P, seed=0, cost_range=(0.3, 0.3))
    rng = np.random.default_rng(3)
    a4 = PaidExp4(A, P, 600, mode="free_I", B=250, c=0.3, rng=rng)
    r4 = run_paid(g, a4, rng)
    assert (
        r4["n_obs"] == 250 and r4["obs_cost"] == 0.0
    )  # never exceeds the free budget, nothing paid
    rng = np.random.default_rng(4)
    a6 = PaidExp4(A, P, 600, mode="free_II", B=40, c=0.3, rng=rng)
    r6 = run_paid(g, a6, rng)
    assert r6["obs_cost"] == pytest.approx(
        0.3 * max(r6["n_obs"] - 40, 0)
    )  # only the excess is charged
    assert r6["n_obs"] > 40


def test_c_to_zero_recovers_full_information():
    g = LinearPolicyGame(300, 4, A, P, seed=1, cost_range=(1e-9, 1e-9))
    rng = np.random.default_rng(5)
    r = run_paid(g, PaidExp4(A, P, 300, mode="paid"), rng)
    assert r["n_obs"] == 300 * A and r["obs_cost"] < 1e-5


def test_paid_regret_sublinear_with_exponent_near_two_thirds():
    """Loose: log-log slope of cost-inclusive regret vs T in a wide band around 2/3 (paper rate T^{2/3} upper bound)."""
    Ts, R = [500, 1000, 2000, 4000], []
    for T_ in Ts:
        vals = []
        for s in range(4):
            g = LinearPolicyGame(T_, 4, A, P, seed=s, cost_range=(0.3, 0.3), bias=0.3)
            vals.append(
                run_paid(g, PaidExp4(A, P, T_, mode="paid"), np.random.default_rng(s))["regret"]
            )
        R.append(np.mean(vals))
    slope = np.polyfit(np.log(Ts), np.log(R), 1)[0]
    assert 0.5 <= slope <= 0.85, slope


def test_free_budget_phase_transition_qualitative():
    """Qualitative reproduction of the paper's Fig. 1 on a small synthetic instance (not a quantitative claim).
    Below B0: regret = R(0) - c*B (observations inside the budget are free). Above B0 (balanced eta): regret keeps falling,
    roughly like B^{-1/2}."""
    c, T_ = 0.3, 2000
    thr = free_budget_threshold(c, A, P, T_)

    def reg(B, form="balanced", n=3):
        out = []
        for s in range(n):
            g = LinearPolicyGame(T_, 4, A, P, seed=s, cost_range=(c, c), bias=0.3)
            rng = np.random.default_rng(100 + s)
            alg = (
                PaidExp4(A, P, T_, mode="free_II", B=0, c=c, rng=rng)
                if B == 0
                else MetaController(A, P, T_, B, c, eta_form=form, rng=rng)
            )
            r = run_paid(g, alg, rng)
            out.append((r["regret"], r["learning"]))
        return np.mean(out, 0)

    r0, r300 = reg(0), reg(300)
    assert r0[0] - r300[0] == pytest.approx(c * 300, rel=1e-6)  # slope -c below the threshold
    assert 300 < thr < 2000
    r2k, r6k = reg(2000), reg(6000)
    assert r6k[0] < r2k[0] < r300[0]  # keeps improving past the threshold
    assert r6k[0] / r2k[0] == pytest.approx(math.sqrt(2000 / 6000), abs=0.2)  # ~ B^{-1/2} (loose)


def test_oracle_efficient_algorithm3_runs_sublinear_and_probabilities_valid():
    rng = np.random.default_rng(7)
    d, A_, T_ = 4, 3, 1500
    Wt = rng.normal(size=(A_, d))
    X = rng.normal(size=(T_, d))
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    Lm = np.clip(0.5 + 0.3 * X @ Wt.T, 0, 1)
    costs = np.full((T_, A_), 0.3)
    alg = OracleEfficientPaid(A_, d, T_)
    loss = paid = 0.0
    best = Lm.min(1).sum()
    cum = []
    for t in range(T_):
        out = alg.step(X[t], costs[t], rng)
        assert (
            abs(out.q.sum() - 1) < 1e-9
            and (out.q >= 0).all()
            and ((out.p >= 0) & (out.p <= 1)).all()
        )
        y = np.clip(Lm[t] + 0.1 * rng.normal(size=A_), 0, 1)
        loss += Lm[t, out.action]
        paid += out.paid
        alg.update(out, y)
        cum.append(loss - Lm[: t + 1].min(1).sum())
    assert cum[-1] / T_ < cum[T_ // 3] / (T_ // 3)  # per-round learning regret decreases
    assert loss - best >= -1e-9


def test_label_acquirer_port_pacing_and_cap():
    acq = PaidLabelAcquirer(T=400, c_q=0.01, label_cap=30)  # cheap labels, small cap
    rng = np.random.default_rng(8)
    n = 0
    for t in range(1, 401):
        hit, p = acq.decide(t, float(rng.random()))
        assert p is None or 0 < p <= 1
        n += hit
        assert acq.used <= 30  # hard cap
    assert n <= 30
    sufficient = PaidLabelAcquirer(T=400, c_q=1.0, label_cap=400)
    assert sufficient.sufficient is True
    assert sufficient.request_probability(1) == pytest.approx(1.0)  # pacing: (B-0)/(T-1+1)


def test_label_acquirer_prefers_better_candidate_after_released_labels():
    acq = PaidLabelAcquirer(T=500, c_q=0.05, label_cap=100, hurdle=0.05)
    for _ in range(40):
        acq.on_release(0.8, 0.2, 0.5)  # candidate much better
    assert acq.prefers_candidate()
    bad = PaidLabelAcquirer(T=500, c_q=0.05, label_cap=100, hurdle=0.05)
    for _ in range(40):
        bad.on_release(0.2, 0.8, 0.5)
    assert not bad.prefers_candidate()


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
    from shiftlab.bench.contract.adapters_gong_zhang import GongZhangAdapter

    spec = load_family("iid_shift_d10")
    env = EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()["balanced"],
        budget=BudgetSpec(label_cap=50),
        clocks=ClockSpec(retrain_duration=20),
    )
    assert GongZhangAdapter.port_status == "COMMON_CONTRACT_PORT"
    assert set(GongZhangAdapter.vocabulary) <= set(env.allowed_actions)
    pr = run_paired(
        {"m": lambda: GongZhangAdapter.build(env)}, spec, env, seeds=range(110_900_000, 110_900_002)
    )  # verify_run inside
    assert len(pr.runs["m"]) == 2
