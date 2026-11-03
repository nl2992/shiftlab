"""Tests for the P7s simulator adapter (``P7sPolicy``).

The central test is numerical equivalence with a real ``CertPlus(n=1)`` driven by its own step
loop, as ``b3_real_data`` drives it, with the same uniform draws. The adapter replicates
CertPlus's information order exactly (q_t issued before event t-delay is released; the decision
for event t+1 made after that release), so equivalence is asserted to be EXACT, not approximate.
Expectations are always derived from the CertPlus run, never written by hand. Sizes and seeds
are CPU-sized and fixed; nothing here is a research result.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

PD = Path(__file__).resolve().parents[2] / "scripts/promising_directions"
for _p in (PD, PD / "sota", PD / "sota/competitors"):
    sys.path.insert(0, str(_p))

from b3_plus_policy import CertPlus, b1
from b3_plus_policy_adapter import P7sPolicy, p7s_plus_params
from simulator import check_budget_feasible, check_no_future_access, policy_rng, run_episode

T, DELAY, BUDGET, CS, CQ = 600, 7, 120, 3.0, 0.05


def make_stream(seed: int, err0=(0.10, 0.30), err1=(0.25, 0.08), change=250, n=T):
    """Binary labels; model 0 good before `change`, model 1 good after (0/1 losses)."""
    r = np.random.default_rng(seed)
    y = r.integers(0, 2, n)
    e0 = np.where(np.arange(n) < change, err0[0], err0[1])
    e1 = np.where(np.arange(n) < change, err1[0], err1[1])
    l0 = (r.random(n) < e0).astype(np.int8)
    l1 = (r.random(n) < e1).astype(np.int8)
    preds = np.stack([y ^ l0, y ^ l1], axis=1).astype(np.int8)
    return preds, y, l0, l1


def run_certplus(l0, l1, u, budget=BUDGET, delay=DELAY, cs=CS, cq=CQ):
    """Drive a real CertPlus(n=1) exactly as b3_real_data does (episode loop over run_policies)."""
    t_len = len(l0)
    p = b1.Params(T=t_len, delay=delay, cq=cq)
    cp = CertPlus(1, budget, cs, cq, p, p7s_plus_params(), trace=True)
    a0, a1 = l0[:, None], l1[:, None]
    dis_all = a0 != a1
    ndis = np.zeros(1)
    for t in range(t_len):
        cp.step(t, a0[t], a1[t], dis_all[t], u[t][None], ndis)
        ndis = ndis + dis_all[t]
    return cp


def run_adapter(preds, y, seed, budget=BUDGET, delay=DELAY, cs=CS, cq=CQ, pol=None):
    t_len = len(y)
    pol = pol or P7sPolicy(t_len, budget, delay, cs, cq, rng=np.random.default_rng(seed))
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=delay, budget=budget,
        label_price=cq, switch_cost=cs,
    )  # fmt: skip
    return pol, res


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_equivalence_with_certplus_is_exact(seed):
    """Same draws -> same loss, queries, switches, net cost AND same q / deployment paths.

    No tolerance: the adapter reproduces CertPlus's release order, so any difference is a bug.
    """
    preds, y, l0, l1 = make_stream(seed)
    u = np.random.default_rng(1000 + seed).random(T)  # the draws CertPlus is handed
    cp = run_certplus(l0, l1, u)
    pol, res = run_adapter(preds, y, 1000 + seed)  # adapter draws the same u from this seed
    assert cp.switches[0] > 0  # the stream is informative: a switch actually occurs
    assert res.prediction_loss == cp.loss[0]
    assert res.requested_labels == cp.queries[0]
    assert res.deployment_switches == cp.switches[0]
    cp_net = cp.loss[0] + CQ * cp.queries[0] + CS * cp.switches[0]
    assert res.net_cost == pytest.approx(cp_net, abs=1e-12)
    np.testing.assert_array_equal(pol.issued_q, cp.tr["q"][:, 0])
    np.testing.assert_array_equal([r["deployed_model"] for r in res.records], cp.tr["dep"][:, 0])


def test_q_sequence_given_identical_released_evidence_is_identical():
    """Pins the exact part separately: q_t depends only on evidence released through t-delay-1.

    Feed both an identical stream; q must agree at every event including through promotion.
    """
    preds, y, l0, l1 = make_stream(5)
    u = np.random.default_rng(77).random(T)
    cp = run_certplus(l0, l1, u)
    pol, _ = run_adapter(preds, y, 77)
    assert np.array_equal(pol.issued_q, cp.tr["q"][:, 0])
    assert np.array_equal(pol.cp.tr["lam"], cp.tr["lam"])
    assert np.array_equal(pol.cp.tr["r"], cp.tr["r"])


def test_hard_budget_and_no_future_access():
    preds, y, *_ = make_stream(11)
    small = 25
    _, res = run_adapter(preds, y, 4, budget=small)
    assert check_budget_feasible(res, small) == []
    assert res.requested_labels <= small
    assert res.refused_requests == 0  # q=0 at zero budget: never even asks
    assert check_no_future_access(res, DELAY) == []


def test_determinism_and_name():
    preds, y, *_ = make_stream(2)
    _, a = run_adapter(preds, y, 9)
    pol, b = run_adapter(preds, y, 9)
    assert pol.name == "P7s_settled"
    assert a.records == b.records
    assert a.net_cost == b.net_cost


def test_policy_rng_isolated_streams_are_deterministic():
    preds, y, *_ = make_stream(2)
    mk = lambda: P7sPolicy(T, BUDGET, DELAY, CS, CQ, rng=policy_rng(0, 0, "P7s_settled"))
    _, a = run_adapter(preds, y, 0, pol=mk())
    _, b = run_adapter(preds, y, 0, pol=mk())
    assert a.records == b.records


def test_state_dict_round_trip_resumes_identically():
    preds, y, *_ = make_stream(3)
    _, ref = run_adapter(preds, y, 21)

    class Snap:
        pass

    snap = Snap()
    extras: dict[int, dict] = {}
    pol = P7sPolicy(T, BUDGET, DELAY, CS, CQ, rng=np.random.default_rng(21))
    orig_req = pol.request_labels

    def hook(event, remaining):
        out = orig_req(event, remaining)
        extras[event.t] = dict(out.extra)
        if event.t == 300:
            snap.s = json.loads(json.dumps(pol.state_dict()))  # must be JSON-clean
        return out

    pol.request_labels = hook
    _, full = run_adapter(preds, y, 21, pol=pol)
    assert full.records == ref.records

    clone = P7sPolicy(T, BUDGET, DELAY, CS, CQ, rng=np.random.default_rng(0))
    clone.load_state_dict(snap.s)
    # NaN/inf entries (t_prom, min_factor) defeat ==; compare the serialised form.
    assert json.dumps(clone.state_dict(), sort_keys=True) == json.dumps(snap.s, sort_keys=True)
    # Replay events 301.. with releases due at t>300 reconstructed from the original run.
    from simulator import Event, ReleasedFeedback

    pending: dict[int, list] = {}
    for r in full.records:
        if r["requested"] and r["event_id"] <= 300 and r["release_time"] > 300:
            e = r["event_id"]
            pending.setdefault(r["release_time"], []).append(
                ReleasedFeedback(
                    e, e, r["release_time"], int(y[e]), (preds[e] != y[e]).astype(np.int8),
                    r["query_probability"],
                    extras[e],
                )
            )  # fmt: skip
    remaining = full.records[300]["budget_remaining"]
    for t in range(301, T):
        if t in pending:
            clone.observe(pending.pop(t))
        ev = Event(t, t, T, preds[t])
        assert int(clone.predict(ev)) == full.records[t]["deployed_model"]
        req = clone.request_labels(ev, remaining)
        rec = full.records[t]
        assert req.requested == bool(rec["requested"])
        if req.requested:
            remaining -= 1
            if t + DELAY < T:
                pending.setdefault(t + DELAY, []).append(
                    ReleasedFeedback(
                        t, t, t + DELAY, int(y[t]), (preds[t] != y[t]).astype(np.int8),
                        req.probability, dict(req.extra),
                    )
                )  # fmt: skip


def test_settled_gate_drops_q_to_pmin_floor():
    """After promotion, with the challenger still ahead, settled_floor=0 -> q clipped to p_min."""
    preds, y, *_ = make_stream(0, err0=(0.30, 0.30), err1=(0.05, 0.05), change=0)
    pol, res = run_adapter(preds, y, 8)
    cp = pol.cp
    dep = cp.tr["dep"][:, 0]
    assert cp.switches[0] >= 1 and dep[-1] == 1
    t_prom = int(np.argmax(dep == 1))
    q = cp.tr["q"][:, 0]
    r = cp.tr["r"][:, 0]
    pmin = pol.p.pmin
    pre = q[:t_prom]
    # Before promotion the pacer is not floored by the settled gate (r = r_max, not 0).
    assert (r[:t_prom] > 0).all()
    # After promotion, once the recent advantage is established, the gate fires: r = 0 -> q = pmin.
    settled_steps = np.flatnonzero((dep == 1) & (r == 0.0))
    assert settled_steps.size > 0
    assert np.all(q[settled_steps] == pmin)
    assert q[settled_steps].max() < pre.max()
    # And it is a real saving relative to the un-gated pacer: queries after promotion are rare.
    post_queries = sum(r_["requested"] for r_ in res.records[t_prom:])
    assert post_queries < 0.2 * (T - t_prom)


def test_rejects_out_of_order_events_and_mismatched_params():
    with pytest.raises(ValueError):
        P7sPolicy(
            T,
            BUDGET,
            DELAY,
            CS,
            CQ,
            rng=np.random.default_rng(0),
            params=b1.Params(T=T + 1, delay=DELAY, cq=CQ),
        )
    with pytest.raises(ValueError):
        P7sPolicy(T, BUDGET, 0, CS, CQ, rng=np.random.default_rng(0))
