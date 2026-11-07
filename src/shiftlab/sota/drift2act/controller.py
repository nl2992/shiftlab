"""Drift2Act controller (Alg. 1, App. B), PAPER_RECONSTRUCTION.  Env protocol (hidden-oracle safe):
env.monitor(t, labels: dict[int,int]) -> z ; env.predict(idx)->yhat ; env.apply(a, t, labels) ; env.mark_safe() ;
env.has_distinct_checkpoint() -> bool.   Labels only reach the controller through LabelStore."""

from __future__ import annotations

import numpy as np

from .actions import ACTIONS, COST, GAIN, LABEL_COST, Config
from .audit import (
    HeuristicQueryPolicy,
    LabelRequestPolicy,
    LabelStore,
    QueryContext,
    WindowedAuditor,
)
from .belief import BeliefFilter
from .certificate import Certificate


class Drift2ActController:
    def __init__(
        self,
        env,
        store: LabelStore,
        belief: BeliefFilter,
        cfg: Config | None = None,
        policy: LabelRequestPolicy | None = None,
        rng=None,
        horizon: int | None = None,
    ):
        self.env, self.store, self.belief, self.cfg = env, store, belief, cfg or Config()
        c = self.cfg
        self.policy = policy or HeuristicQueryPolicy(
            c.k_max, c.k_high, c.k_low, c.m_low, c.audit_every
        )
        self.auditor = WindowedAuditor(store, c.N, c.window_mode, c.pool)
        self.cert = Certificate(c.tau, c.delta, c.delta_mode)
        self.rng = rng or np.random.default_rng(0)
        self.horizon = horizon
        self.last_rt = self.last_rb = self.last_a3 = -(10**9)
        self.boost = 0
        self.prev = {"U": np.inf, "risk": np.nan, "rad": np.nan}
        self.prev_a = 0
        self.log: list[dict] = []
        self.total_action_cost = 0.0
        self.total_label_cost = 0.0

    def step(self, t: int) -> dict:
        c = self.cfg
        recent = {i: self.store.get(i, t) for i in self.store.released(t, max(0, t - 512), t)}
        z = self.env.monitor(t, recent)
        b = self.belief.update(z)
        lo, hi = self.auditor.window(t)
        ctx = QueryContext(
            t,
            b.copy(),
            self.prev["U"],
            self.prev["risk"],
            self.prev["rad"],
            c.tau,
            self.store.remaining,
            self.horizon,
            self.store.pending(t),
            max(0, hi - lo + 1),
        )
        n_t = self.policy.request_size(ctx)
        if self.boost:
            n_t, self.boost = max(n_t, c.k_high), 0
        n_t = min(max(int(n_t), 0), self.store.remaining) if n_t > 0 else 0
        spent0 = self.store.spent
        _Q, J = self.auditor.sample(t, n_t, self.rng)
        assert self.store.spent - spent0 == len(J) <= n_t and self.store.spent <= self.store.budget
        losses, _idx = self.auditor.losses(t, self.env.predict)
        cr = self.cert.compute(losses, t, ctx.window_size)
        self.prev = {"U": cr.U, "risk": cr.risk_hat, "rad": cr.radius}
        gate_ok = cr.gate_ok or not c.use_certificate
        labels = {i: self.store.get(i, t) for i in self.store.released(t)}  # released only

        delta_a = b @ GAIN  # Delta_t(a)
        feasible = [0, 1, 2, 6]
        if self.store.remaining > 0 and t - self.last_a3 >= c.a3_cooldown:
            feasible.append(3)
        if t - self.last_rt >= c.cooldown_retrain and len(labels) >= c.min_retrain_labels:
            feasible.append(4)
        if t - self.last_rb >= c.cooldown_rollback and self.env.has_distinct_checkpoint():
            feasible.append(5)
        feasible.sort()
        util = {}
        for a in feasible:
            viol = (
                max(0.0, cr.U - c.sigma_U * delta_a[a] - c.tau)
                if (c.use_certificate and np.isfinite(cr.U))
                else (1.0 if (c.use_certificate and not np.isfinite(cr.U)) else 0.0)
            )
            util[a] = float(delta_a[a] - c.lam * COST[a] / c.cost_norm - c.gamma * viol)

        executed = []
        if not gate_ok:  # U_t > tau: abstain/handoff + scheduled rollback/retrain
            executed = [6]
            risk_ev = bool(np.isfinite(cr.risk_hat) and cr.risk_hat > c.tau)
            evidence = {
                "literal": True,
                "risk_evidence": risk_ev,
                "belief_or_risk": risk_ev or (1.0 - b[0]) > 0.5,
            }[c.fail_schedule]
            if evidence:
                if 5 in feasible:
                    executed.append(5)
                elif 4 in feasible:
                    executed.append(4)
            a_t = executed[-1] if len(executed) > 1 else 6
        else:
            best = max(feasible, key=lambda a: util[a])
            a_t = best if (best != 0 and util[best] >= c.eps_noop) else 0
            executed = [a_t] if a_t else []
        info = {}
        for a in executed:
            if a == 3:
                self.boost, self.last_a3 = c.k_high, t
            else:
                info[a] = self.env.apply(a, t, labels)
            if a == 4:
                self.last_rt = t
            if a == 5:
                self.last_rb = t
        if gate_ok and cr.gate_ok:
            self.env.mark_safe()
        # cost: A6 charged on activation only (documented); labels at 0.05 each
        act_cost = sum(COST[a] for a in executed if not (a == 6 and self.prev_a == 6))
        lab_cost = LABEL_COST * len(J)
        self.total_action_cost += act_cost
        self.total_label_cost += lab_cost
        self.prev_a = 6 if 6 in executed else (a_t if executed else 0)
        rec = {
            "t": t,
            "z": np.asarray(z).tolist(),
            "belief": b.tolist(),
            "n_requested": int(n_t),
            "n_new_labels": len(J),
            "requested_idx": J,
            "release_times": [self.store.release[i] for i in J],
            "budget_remaining": self.store.remaining,
            "pending": self.store.pending(t),
            "n_cert": cr.n,
            "risk_hat": cr.risk_hat,
            "radius": cr.radius,
            "U": cr.U,
            "delta_t": cr.delta_used,
            "gate_ok": bool(cr.gate_ok),
            "feasible": [ACTIONS[a] for a in feasible],
            "utilities": {ACTIONS[a]: u for a, u in util.items()},
            "executed": [ACTIONS[a] for a in executed],
            "action": ACTIONS[executed[-1]] if executed else ACTIONS[0],
            "abstain": 6 in executed,
            "action_cost": float(act_cost),
            "label_cost": float(lab_cost),
        }
        self.log.append(rec)
        return rec
