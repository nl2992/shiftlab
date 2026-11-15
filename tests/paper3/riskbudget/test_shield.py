import numpy as np
import pytest

from shiftlab.paper3.baselines import AlwaysChallenger, NeverSwitch, WaldEconomic
from shiftlab.paper3.contracts import Costs, Paper3Decision, PolicyAdapter, ProblemSpec
from shiftlab.paper3.riskbudget import RiskBudgetShield, harm_path, harm_summary
from shiftlab.paper3.simulation import (
    CONFIG_DIR,
    Tape,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
    seeds_for,
)

T = 300
K = 3.0
RS = (8, 12, 20)


def _all_regimes():
    regs = dict(load_regimes())
    regs.update(load_regimes(str(CONFIG_DIR / "regimes_f3_v1.json")))
    return regs


REGIMES = _all_regimes()


def _inners():
    return {
        "always": AlwaysChallenger(),
        "wald": WaldEconomic(0.98, 0.3, "paced", 45),
    }


def hand_tape(z, delay, T=T, disagree=None):
    """z in {-1,0,1} per round (challenger favoured if +1); z != 0 implies disagreement."""
    z = np.asarray(z, float)
    dis = (z != 0) if disagree is None else np.asarray(disagree, bool)
    ell0 = np.where(z > 0, 1.0, 0.0)
    ell1 = np.where(z < 0, 1.0, 0.0)
    return Tape(
        np.column_stack([ell0, ell1]),
        dis,
        np.zeros((T, 2)),
        np.full(T, delay) if np.isscalar(delay) else np.asarray(delay),
        {},
    )


def hand_spec(T=T, B=60, k=K, d=5):
    return ProblemSpec(T=T, B=B, costs=Costs(c_q=0.05, k=k, c_compute=0.0), delay_known=d)


def hand_tapes():
    rng = np.random.default_rng(0)
    harm = -np.ones(T)
    dense = np.where(rng.random(T) < 0.5, -1.0, 0.0)
    bait = np.r_[np.ones(40), -np.ones(T - 40)]
    bait_sparse = np.where(np.arange(T) % 3 == 0, bait, 0.0)
    return {
        "all_harm_d5": hand_tape(harm, 5),
        "all_harm_never_arrive": hand_tape(harm, T + 1),
        "dense_harm_d3": hand_tape(dense, 3),
        "bait_then_harm_d5": hand_tape(bait, 5),
        "bait_then_harm_d30": hand_tape(bait, 30),
        "bait_sparse_never": hand_tape(bait_sparse, T + 1),
    }


# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("inner", ["always", "wald"])
def test_deterministic_guarantee_all_regimes(inner):
    seeds = seeds_for("smoke", 5)
    worst = {R: 0.0 for R in RS}
    for reg in REGIMES.values():
        spec = make_spec(reg, T)
        for s in seeds:
            tape, _ = generate_tape(reg, s, T)
            for R in RS:
                sh = RiskBudgetShield(_inners()[inner], R, delta=0.0)
                rec = run_policy(sh, tape, spec, s)
                hs = harm_summary(tape, rec, reg.costs.k)
                worst[R] = max(worst[R], hs["sup_harm"])
                assert hs["sup_harm"] <= R + 1e-9, (reg.id, s, R, hs)
                assert sh.I_max <= R + 1e-9  # the proof's invariant itself holds
    assert max(worst.values()) > 0  # shield does promote somewhere


@pytest.mark.parametrize("inner", ["always", "wald"])
def test_deterministic_guarantee_hand_tapes(inner):
    for name, tape in hand_tapes().items():
        for R in RS:
            for ride in (True, False):
                sh = RiskBudgetShield(_inners()[inner], R, delta=0.0, ride_out=ride)
                rec = run_policy(sh, tape, hand_spec(), 1)
                hs = harm_summary(tape, rec, K)
                assert hs["sup_harm"] <= R + 1e-9, (name, R, ride, hs)


def test_no_promotion_when_budget_below_two_fees():
    for name, tape in hand_tapes().items():
        for R in (0, 3, 5.99):
            sh = RiskBudgetShield(AlwaysChallenger(), R, delta=0.0)
            rec = run_policy(sh, tape, hand_spec(), 1)
            assert rec.a.sum() == 0, (name, R)
            assert sh.n_vetoed_promotions > 0
    reg = REGIMES["stationary_better"]
    tape, _ = generate_tape(reg, seeds_for("smoke", 1)[0], T)
    rec = run_policy(
        RiskBudgetShield(AlwaysChallenger(), 5.0, delta=0.0), tape, make_spec(reg, T), 1
    )
    assert rec.a.sum() == 0


def test_randomised_violation_rate():
    delta = 0.1
    # one harmful tape; labels return slowly so early exposure is mostly unresolved
    z = np.where(np.arange(T) % 2 == 0, -1.0, 0.0)
    tape = hand_tape(z, 4)
    spec = hand_spec(B=100)
    R, n_seeds, viol = 12, 2000, 0
    for s in range(n_seeds):
        sh = RiskBudgetShield(AlwaysChallenger(), R, delta=delta, pi_menu=(0.5, 1.0))
        rec = run_policy(sh, tape, spec, s)
        viol += harm_summary(tape, rec, K)["sup_harm"] > R + 1e-9
    rate = viol / n_seeds
    assert rate <= delta + 3 * np.sqrt(delta * (1 - delta) / n_seeds), rate


def test_shield_is_useful_when_challenger_good():
    seeds = seeds_for("smoke", 20)
    for rid in ("stationary_better", "long_persistent"):
        reg = REGIMES[rid]
        spec = make_spec(reg, T)
        for iname in ("always", "wald"):
            frac, dj = [], []
            for s in seeds:
                tape, _ = generate_tape(reg, s, T)
                rec = run_policy(RiskBudgetShield(_inners()[iname], 12, delta=0.0), tape, spec, s)
                frac.append(rec.a.mean())
                dj.append(rec.J - run_policy(NeverSwitch(), tape, spec, s).J)
            assert np.mean(dj) < 0, (rid, iname, np.mean(dj))
            assert np.mean(frac) > (0.5 if iname == "always" or rid == "stationary_better" else 0.3)
            print(f"[useful] {rid} {iname}: frac_deployed={np.mean(frac):.3f} dJ={np.mean(dj):.2f}")


def test_ablations_break_guarantee():
    tape = hand_tapes()["all_harm_d5"]
    R = 12
    full = RiskBudgetShield(AlwaysChallenger(), R, delta=0.0)
    assert harm_summary(tape, run_policy(full, tape, hand_spec(), 1), K)["sup_harm"] <= R
    for flag in ("use_pending_reserve", "use_rollback_reserve"):
        sh = RiskBudgetShield(AlwaysChallenger(), R, delta=0.0, **{flag: False})
        hs = harm_summary(tape, run_policy(sh, tape, hand_spec(), 1), K)
        assert hs["sup_harm"] > R, (flag, hs)
    # conf-width ablation: with pi<1 the missing width breaks the (probabilistic) guarantee
    z = np.where(np.arange(T) % 2 == 0, -1.0, 0.0)
    tape2 = hand_tape(z, 4)
    viol = 0
    for s in range(300):
        sh = RiskBudgetShield(
            AlwaysChallenger(), R, delta=0.1, pi_menu=(0.25, 1.0), use_conf_width=False
        )
        rec = run_policy(sh, tape2, hand_spec(B=100), s)
        viol += harm_summary(tape2, rec, K)["sup_harm"] > R
    assert viol > 0


@pytest.mark.parametrize("B", [0, 6])
def test_budget_semantics(B):
    for rid in ("stationary_better", "abrupt_harmful", "label_dropout"):
        reg = REGIMES[rid]
        spec = make_spec(reg, T)
        spec = ProblemSpec(
            T=T, B=B, costs=spec.costs, delay_known=spec.delay_known, delay_kind=spec.delay_kind
        )
        for pm in ((1.0,), (0.25, 1.0)):
            for iname in ("always", "wald"):
                tape, _ = generate_tape(reg, seeds_for("smoke", 1)[0], T)
                sh = RiskBudgetShield(
                    _inners()[iname], 12, delta=0.05 if pm[0] < 1 else 0.0, pi_menu=pm
                )
                rec = run_policy(sh, tape, spec, 3)  # raises BudgetError on violation
                assert rec.q.sum() <= B
                if B == 0:  # fully blind: deterministic guarantee still holds
                    assert (
                        harm_summary(tape, rec, spec.costs.k)["sup_harm"] <= 12 + 1e-9 or pm[0] < 1
                    )


class _LeaveAtEnd(PolicyAdapter):
    name = "leave_at_end"

    def reset(self, spec, rng):
        self.T = spec.T

    def act(self, view):
        return Paper3Decision(int(view.t <= self.T - 6))


def test_ride_out_avoids_pointless_rollback():
    Tn = 80
    tape = hand_tape(np.ones(Tn), 1, T=Tn)  # challenger strictly better: A very negative
    spec = hand_spec(T=Tn, d=1)
    a = RiskBudgetShield(_LeaveAtEnd(), 12, delta=0.0, ride_out=True)
    b = RiskBudgetShield(_LeaveAtEnd(), 12, delta=0.0, ride_out=False)
    ra, rb = run_policy(a, tape, spec, 1), run_policy(b, tape, spec, 1)
    assert a.rode_out and not b.rode_out
    assert ra.ledger["n_switches"] == 1 and rb.ledger["n_switches"] == 2
    assert ra.J < rb.J
    assert harm_summary(tape, ra, K)["sup_harm"] <= 12


def test_harm_path_matches_evaluator_and_diagnostics():
    reg = REGIMES["abrupt_harmful"]
    spec = make_spec(reg, T)
    tape, _ = generate_tape(reg, seeds_for("smoke", 1)[0], T)
    sh = RiskBudgetShield(AlwaysChallenger(), 12, delta=0.0)
    rec = run_policy(sh, tape, spec, 0)
    h = harm_path(tape, rec, spec.costs.k)
    assert h.shape == (T,)
    a = rec.a
    manual = 0.0
    prev, mx = 0, 0.0
    for t in range(T):
        manual += K * (a[t] != prev) - a[t] * (tape.ell[t, 0] - tape.ell[t, 1])
        prev = a[t]
        assert abs(manual - h[t]) < 1e-9
        mx = max(mx, manual)
    assert harm_summary(tape, rec, K)["sup_harm"] == pytest.approx(mx)
    assert sh.n_forced_rollbacks + sh.n_vetoed_promotions > 0
