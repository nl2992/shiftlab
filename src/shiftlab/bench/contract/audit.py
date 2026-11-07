"""Audit log schema and independent verification of a finished run.

Schema v1 (one JSON object per record, evaluator-side; never shown to policies):
  common      : run_id, seq, t, event
  request     : label_id, action_id, label_round (<= t, >= t - max_lookback), propensity,
                release_t|null, missing, beyond_horizon, served (model that served label_round)
  route       : target, fraction, primary, served  (one per round with a standing canary route)
  release     : label_id, request_t, label_round, release_t, delivered_t
  action      : action_id, kind, performed, reason, charge, [target]
                (performed=False <=> charge == 0; reason in {ok, noop, duplicate_kind_in_round,
                 budget_refused, budget_violation, retrain_in_progress, retrain_cooldown,
                 switch_cooldown, already_deployed, retrained_not_ready, bad_target,
                 nothing_to_roll_back_to, one_model_change_per_round,
                 deployment_in_flight})
  deploy      : effective_t, from_model, to_model, cause {switch, rollback, retrain_complete},
                charged_to (action_id that pays; one payer per model change)
  retrain_start / retrain_done : action_id|charged_to, completes_t
  leak        : attempts
  final       : breakdown, counts
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .types import COMPONENT, COUNT_KEY, FREE_KINDS, CostVector

AUDIT_SCHEMA_VERSION = "1.0"
REQUIRED = {
    "request": {"label_id", "action_id", "label_round", "missing"},
    "route": {"target", "fraction", "primary", "served"},
    "release": {"label_id", "request_t", "label_round", "release_t", "delivered_t"},
    "action": {"action_id", "kind", "performed", "reason", "charge"},
    "deploy": {"effective_t", "from_model", "to_model", "cause", "charged_to"},
    "final": {"breakdown", "counts"},
}


class AuditViolation(AssertionError):
    """The audit log is inconsistent with the contract."""


@dataclass
class AuditLog:
    run_id: str
    meta: dict[str, Any] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)

    def add(self, event: str, t: int, **kw: Any) -> None:
        self.records.append(
            {"run_id": self.run_id, "seq": len(self.records), "t": t, "event": event, **kw}
        )

    def of(self, event: str) -> list[dict[str, Any]]:
        return [r for r in self.records if r["event"] == event]

    def to_jsonl(self) -> str:
        head = {"schema": AUDIT_SCHEMA_VERSION, "run_id": self.run_id, **self.meta}
        return "\n".join(json.dumps(r, default=_j) for r in [head, *self.records])


def _j(o: Any):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def validate_schema(log: AuditLog) -> None:
    for r in log.records:
        for k in ("run_id", "seq", "t", "event"):
            if k not in r:
                raise AuditViolation(f"record missing {k}: {r}")
        miss = REQUIRED.get(r["event"], set()) - set(r)
        if miss:
            raise AuditViolation(f"{r['event']} record missing {sorted(miss)}")


def verify_run(result, stream) -> None:
    """Independently recompute counts/J from the audit log and check the contract invariants.

    ``stream`` is the evaluator-side stream the run used (needed for delay/loss ground truth).
    Raises ``AuditViolation`` on any inconsistency.
    """
    log: AuditLog = result.audit
    costs: CostVector = result.env.costs
    validate_schema(log)

    # 1. costs only for performed actions, once each, at the declared price
    actions = log.of("action")
    ids = [a["action_id"] for a in actions]
    if len(ids) != len(set(ids)):
        raise AuditViolation("duplicate action ids")
    counts = {k: 0 for k in COUNT_KEY.values()}
    parts = {k: 0.0 for k in COUNT_KEY.values()}
    for a in actions:
        if a["performed"]:
            if a["kind"] in FREE_KINDS:
                if a["charge"] != 0.0:
                    raise AuditViolation(f"free action {a['kind']} was charged")
                continue
            if a["kind"] not in COMPONENT:
                raise AuditViolation(f"performed non-chargeable action {a}")
            price = costs.price(a["kind"])
            if abs(a["charge"] - price) > 1e-12:
                raise AuditViolation(f"action {a['action_id']} charged {a['charge']} != {price}")
            counts[COUNT_KEY[a["kind"]]] += 1
            parts[COUNT_KEY[a["kind"]]] += price
        elif a["charge"] != 0.0:
            raise AuditViolation(f"non-performed action {a['action_id']} was charged")
    if counts != result.counts:
        raise AuditViolation(f"ledger counts {result.counts} != audit-derived {counts}")
    loss = float(np.sum(result.loss_path))
    J = loss + sum(parts.values())
    if abs(J - result.J) > 1e-9 or abs(loss - result.breakdown["loss"]) > 1e-9:
        raise AuditViolation(f"J mismatch: ledger {result.J} vs recomputed {J}")
    for k, v in parts.items():
        if abs(result.breakdown[f"cost_{k}"] - v) > 1e-9:
            raise AuditViolation(f"component {k} mismatch")

    # 2. one payer per model change; deploy attributed to a performed action; no extra charge
    performed = {a["action_id"]: a for a in actions if a["performed"]}
    payers: list[int] = []
    for d in log.of("deploy"):
        aid = d["charged_to"]
        if aid not in performed:
            raise AuditViolation(f"deploy charged_to unperformed action {aid}")
        want = {"switch": "switch", "rollback": "rollback", "retrain_complete": "retrain"}[
            d["cause"]
        ]
        if performed[aid]["kind"] != want:
            raise AuditViolation(f"deploy cause {d['cause']} paid by {performed[aid]['kind']}")
        payers.append(aid)
    if len(payers) != len(set(payers)):
        raise AuditViolation("a single action paid for more than one model change")

    # 3. labels: release exactly at request + potential delay, never before; missing never released
    s = stream
    T = result.env.T
    req = {r["label_id"]: r for r in log.of("request")}
    rel = {r["label_id"]: r for r in log.of("release")}
    nq = sum(1 for a in actions if a["performed"] and a["kind"] == "query")
    if len(req) != nq:
        raise AuditViolation("query count != request records (charged without request or v.v.)")
    for lid, r in rel.items():
        lr = r["label_round"]
        want = r["request_t"] + int(s.delay[lr - 1])  # = max(request, round) + delay
        if r["release_t"] != want or r["delivered_t"] != r["release_t"]:
            raise AuditViolation(
                f"label {lid} released at {r['release_t']} != request+delay {want}"
            )
        if s.missing[lr - 1]:
            raise AuditViolation(f"missing label {lid} was released")
        if r["delivered_t"] < r["request_t"] + 1:
            raise AuditViolation(f"label {lid} delivered before it could exist")
    max_lb = result.env.clocks.max_lookback
    rounds_seen: set[int] = set()
    for lid, q in req.items():
        lr = q["label_round"]
        if not (1 <= lr <= q["t"] and q["t"] - lr <= max_lb) or lr in rounds_seen:
            raise AuditViolation(f"label {lid}: round {lr} outside lookback or requested twice")
        rounds_seen.add(lr)
        due = q["t"] + int(s.delay[lr - 1])
        should_release = (not s.missing[lr - 1]) and due <= T
        if should_release and lid not in rel:
            raise AuditViolation(f"label {lid} due at {due} never released")

    # 3b. propensities: a declared propensity p < 1 is a randomisation claim that must be honoured
    #     by the shared uniform state.u[u_index] of the request round (state.u[i] == stream.query_u)
    for a in actions:
        if a["performed"] and a["kind"] == "query" and a.get("propensity") is not None:
            p = a["propensity"]
            if not 0.0 < p <= 1.0:
                raise AuditViolation(f"action {a['action_id']}: propensity {p} outside (0,1]")
            if not 0 <= a["u_index"] < s.query_u.shape[1]:
                raise AuditViolation(f"action {a['action_id']}: bad u_index")
            if s.query_u[a["t"] - 1, a["u_index"]] >= p:
                raise AuditViolation(
                    f"action {a['action_id']}: declared propensity {p} but state.u="
                    f"{s.query_u[a['t'] - 1, a['u_index']]:.4f} >= p (selection not randomised as claimed)"
                )

    # 3c. routing: served model must equal the draw implied by the declared fraction
    routes = {r["t"]: r for r in log.of("route")}
    for t, r in routes.items():
        want = r["target"] if s.route_u[t - 1] < r["fraction"] else r["primary"]
        if (
            not 0.0 < r["fraction"] <= 1.0
            or r["served"] != want
            or result.served_path[t - 1] != want
        ):
            raise AuditViolation(
                f"round {t}: served {r['served']} inconsistent with fraction "
                f"{r['fraction']} and draw {s.route_u[t - 1]:.4f}"
            )
    for t in range(1, T + 1):
        if t not in routes and result.served_path[t - 1] != result.model_path[t - 1]:
            raise AuditViolation(f"round {t}: served != primary without a logged route")

    # 3d. retrain quality model and per-round loss recomputed independently
    from .streams import retrain_loss_rate

    W = result.env.clocks.w_train
    for r in log.of("retrain_start"):
        want_q = retrain_loss_rate(s.spec, r["clean_fraction"])
        if (
            abs(want_q - r["q"]) > 1e-12
            or r["clean_fraction"] > r["label_fraction"] + 1e-12
            or r["label_fraction"] * W > W + 1e-9
        ):
            raise AuditViolation(f"retrain at t={r['t']}: q/fractions inconsistent")
    q_by_t = sorted((r["t"], r["q"]) for r in log.of("retrain_done"))
    abst = {a["t"] for a in actions if a["performed"] and a["kind"] == "abstain"}
    for t in range(1, T + 1):
        m = int(result.served_path[t - 1])
        if t in abst:
            want_l = result.env.clocks.fallback_loss
        elif m == 0:
            want_l = s.loss_inc[t - 1]
        elif m == 1:
            want_l = s.loss_cand[t - 1]
        else:
            q = [qq for (tt, qq) in q_by_t if tt <= t]
            want_l = float(s.retrain_u[t - 1] < q[-1]) if q else None
        if want_l is None or abs(result.loss_path[t - 1] - want_l) > 1e-12:
            raise AuditViolation(f"round {t}: charged loss != loss of the serving model")

    # 4. final record agrees
    fin = log.of("final")
    if len(fin) != 1 or abs(fin[0]["breakdown"]["J"] - result.J) > 1e-9:
        raise AuditViolation("final record disagrees with J")
    if log.of("leak"):
        raise AuditViolation("run contains leak attempts")
