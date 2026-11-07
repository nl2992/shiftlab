import itertools
import math

import numpy as np
import pytest

from shiftlab.sota.drift2act import (
    BeliefFilter,
    BudgetError,
    Certificate,
    Config,
    Drift2ActController,
    GaussianEvidence,
    LabelStore,
    LeakageError,
    rad,
    rad_fp,
)
from shiftlab.sota.drift2act.belief import estimate_T
from shiftlab.sota.drift2act.synthetic_env import SyntheticStreamEnv


# ---------------- radius / certificate numerics ----------------
def test_radius_formula_numerics():
    for n, d in [(1, 0.05), (10, 0.05), (100, 0.01), (1024, 0.05)]:
        expect = math.sqrt(math.log(math.pi**2 * n * n / (6 * d)) / (2 * n))
        assert rad(n, d) == pytest.approx(expect, rel=1e-12)
        # equals Hoeffding radius at the stitched level delta_n = 6 d /(pi^2 n^2)
        assert rad(n, d) == pytest.approx(
            math.sqrt(math.log(1 / (6 * d / (math.pi**2 * n * n))) / (2 * n))
        )
    assert rad(100, 0.05) == pytest.approx(
        0.2520, abs=5e-4
    )  # hand: sqrt(ln(pi^2*1e4/0.3 = 328987)/200) = sqrt(12.70/200)
    assert rad(0, 0.05) == math.inf and rad(500, 0.05) < rad(50, 0.05)
    assert rad_fp(100, 0.05, 1024) < rad(100, 0.05)


def test_certificate_gate_and_bounds():
    c = Certificate(tau=0.2, delta=0.05, delta_mode="mandate")
    r = c.compute(np.zeros(2000), t=10)
    assert r.U == pytest.approx(rad(2000, 0.05)) and r.gate_ok
    assert not c.compute(np.ones(2000), t=10).gate_ok
    assert not c.compute([], t=1).gate_ok
    with pytest.raises(ValueError):
        c.compute([0.5, 1.5], 1)
    ca = Certificate(0.2, 0.05, "alg1")
    assert ca.delta_t(10) == pytest.approx(6 * 0.05 / (math.pi**2 * 100))


def _coverage_violation_rate(selector, trials=300, N=400, p=0.3, nmax=150, delta=0.05, seed=0):
    rng = np.random.default_rng(seed)
    pop = np.zeros(N)
    pop[: int(p * N)] = 1
    R, viol = pop.mean(), 0
    cert = Certificate(0.2, delta, "mandate")
    for _ in range(trials):
        pop_t = rng.permutation(pop)
        draws = selector(rng, pop_t, nmax)
        bad = any(R > cert.compute(draws[:n], t=1).U for n in range(5, nmax + 1, 5))
        viol += bad
    return viol / trials


def test_certificate_coverage_uniform_iid_sampling():
    uniform = lambda rng, pop, n: pop[
        rng.integers(0, len(pop), n)
    ]  # paper Condition A (with replacement)
    assert _coverage_violation_rate(uniform) <= 0.05
    wor = lambda rng, pop, n: pop[
        rng.permutation(len(pop))[:n]
    ]  # without replacement still valid (Hoeffding)
    assert _coverage_violation_rate(wor, seed=1) <= 0.05


def test_certificate_not_valid_under_informative_selection():
    # selection depends on the loss itself (query only low-loss items): the Condition-A assumption is violated
    biased = lambda rng, pop, n: np.sort(pop)[rng.integers(0, len(pop) // 2, n)]
    assert _coverage_violation_rate(biased) > 0.5


# ---------------- controller-level helpers ----------------
class ConstEvidence:
    def __init__(self, ll):
        self.ll = np.asarray(ll, float)

    def log_lik(self, z, gap=1):
        return self.ll


def _mk(seed=3, L=400, cfg=None, ev=None, policy=None, drift="concept", **kw):
    cfg = cfg or Config(
        label_budget=kw.pop("budget", 3000),
        delay=20,
        N=200,
        cooldown_retrain=100,
        cooldown_rollback=60,
        audit_every=2,
        a3_cooldown=10,
    )
    env = SyntheticStreamEnv(seed, L, drift=drift, onset=100, schedule="step")
    store = LabelStore(env.oracle, cfg.delay, 0, cfg.label_budget)
    ev = ev or ConstEvidence([-5, -5, 0, -5])
    ctrl = Drift2ActController(
        env,
        store,
        BeliefFilter(np.full((4, 4), 0.25), ev),
        cfg,
        policy,
        np.random.default_rng(seed),
        L,
    )
    return env, store, ctrl


def test_budget_never_exceeded_pathwise():
    _env, store, ctrl = _mk(budget=40)
    for t in range(400):
        ctrl.step(t)
        assert store.spent <= 40
    assert store.spent == 40 and ctrl.log[-1]["budget_remaining"] == 0
    free = next(i for i in range(399) if i not in store.release)
    with pytest.raises(BudgetError):
        store.request(free, 399)


def test_no_label_used_before_release(monkeypatch):
    _env, store, ctrl = _mk(
        cfg=Config(delay=30, N=200, label_budget=500, window_mode="current", audit_every=1)
    )
    seen = []
    orig = LabelStore.get

    def spy(self, i, t):
        seen.append((i, t, self.release.get(i)))
        return orig(self, i, t)

    monkeypatch.setattr(LabelStore, "get", spy)
    for t in range(250):
        ctrl.step(t)
    assert seen and all(r is not None and r <= t for i, t, r in seen)
    assert all(r >= i + 30 for i, t, r in seen)  # delay respected
    assert any(
        store.pending(t) > 0 for t in range(250)
    )  # current-window mode really has pending labels
    unreleased = [i for i, r in store.release.items() if r > 249]
    if unreleased:
        with pytest.raises(LeakageError):
            orig(store, unreleased[0], 249)
    with pytest.raises(LeakageError):
        orig(store, 10**6, 249)


def _spacing(ctrl, name):
    ts = [r["t"] for r in ctrl.log if name in r["executed"]]
    return ts, all(
        b - a >= (100 if name == "A4_retrain" else 60) for a, b in itertools.pairwise(ts)
    )


def test_cooldowns_respected_and_evidence_hook_swappable():
    # (a) utility path (lambda=0 so retrain is the argmax), custom evidence model = Q1 hook
    cfg = Config(
        delay=10,
        N=150,
        label_budget=3000,
        cooldown_retrain=100,
        cooldown_rollback=60,
        audit_every=2,
        use_certificate=False,
        eps_noop=0.0,
        a3_cooldown=10**9,
        lam=0.0,
    )
    _, _, ctrl = _mk(cfg=cfg, ev=ConstEvidence([-5, -5, 0, -5]))
    for t in range(400):
        ctrl.step(t)
    ts, ok = _spacing(ctrl, "A4_retrain")
    assert len(ts) >= 2 and ok
    # (b) certificate-failure path (tau tiny => always U>tau): scheduled rollback/retrain also obey cooldowns
    cfg = Config(
        delay=10,
        N=150,
        label_budget=3000,
        cooldown_retrain=100,
        cooldown_rollback=60,
        audit_every=2,
        tau=1e-4,
        fail_schedule="literal",
    )
    _, _, ctrl = _mk(cfg=cfg)
    for t in range(400):
        ctrl.step(t)
    for name in ("A4_retrain", "A5_rollback"):
        ts, ok = _spacing(ctrl, name)
        assert ts and ok, (name, ts)
    assert all(r["abstain"] for r in ctrl.log)


def test_q2_policy_swap_leaves_certificate_unchanged():
    class P1:
        def request_size(self, ctx):
            return 25 if ctx.t % 5 == 0 else 0

    class P2:  # different implementation, same decisions
        def request_size(self, ctx):
            return min(25, ctx.budget_remaining) * int(ctx.t % 5 == 0)

    class P3:  # different decisions -> different n, but certificate must still equal R^ + rad(n)
        def request_size(self, ctx):
            return 60 if ctx.t % 5 == 0 else 0

    outs = {}
    for name, P in [("p1", P1), ("p2", P2), ("p3", P3)]:
        _, _, ctrl = _mk(policy=P())
        for t in range(300):
            ctrl.step(t)
        outs[name] = ctrl.log
    for a, b in zip(outs["p1"], outs["p2"]):
        assert (a["U"], a["n_cert"], a["requested_idx"]) == (
            b["U"],
            b["n_cert"],
            b["requested_idx"],
        )
    for log in outs.values():
        for r in log:
            if r["n_cert"] > 0:
                assert r["U"] == pytest.approx(r["risk_hat"] + rad(r["n_cert"], r["delta_t"]))
    assert any(a["n_cert"] != b["n_cert"] for a, b in zip(outs["p1"], outs["p3"]))


def test_audit_log_fields_and_costs():
    _, store, ctrl = _mk()
    for t in range(150):
        ctrl.step(t)
    for k in [
        "t",
        "belief",
        "n_requested",
        "requested_idx",
        "release_times",
        "budget_remaining",
        "U",
        "executed",
        "action_cost",
        "label_cost",
        "utilities",
    ]:
        assert k in ctrl.log[-1]
    assert sum(r["label_cost"] for r in ctrl.log) == pytest.approx(0.05 * store.spent)
    assert sum(r["n_new_labels"] for r in ctrl.log) == store.spent
    assert all(
        rt >= t_req
        for rec in ctrl.log
        for t_req, rt in [(rec["t"], x) for x in rec["release_times"]]
    )


def test_estimate_T_rows_sum_to_one():
    T = estimate_T([[0, 0, 1, 1], [0, 2, 2]])
    assert np.allclose(T.sum(1), 1)
    ev = GaussianEvidence.fit(np.random.default_rng(0).normal(size=(40, 3)), np.arange(40) % 4)
    assert ev.log_lik(np.zeros(3)).shape == (4,)
