"""Event-driven simulator with pathwise budgets, pending-label queue, audit log and J accounting.

Per-round order (all clocks in rounds):
 1. due retrain completion -> retrained model becomes ready (and deploys if deploy_on_complete,
    charged to the retrain action already paid; no switch charge)
 2. due deployments (switch/rollback with lag) are applied
 3. labels with release_t == t are delivered (sorted by (release_t, request_t)); delivery order may
    differ from request order
 4. policy.act(ObservableState) runs inside the leak guard
 5. actions are validated, performed or refused, in the fixed order rollback, switch, route,
    retrain, [lag-0 deployments applied and the serving model for round t drawn], alert, abstain,
    query, continue. Charges are made ONLY for performed actions
 6. the round's loss is charged for the model that served it (or ``fallback_loss`` if abstained)

Charging rule (no double counting): every model change is attributed to exactly one initiating
action. switch -> c_s, rollback -> c_b, retrain -> c_r (the deployment on completion is free).
``route`` (canary traffic split) is free: losses are charged per routed model.

Retrospective queries: ``query(round=s)`` with s in [t - max_lookback, t] is charged at request time,
released at ``t + delay_s`` (= max(t, s) + delay), and reveals the loss of the model that SERVED
round s (plus every other existing model in ``shadow`` mode).
"""
# ruff: noqa: B023  (finalize() is defined and called within the same round)

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

from .audit import AuditLog
from .guards import LabelNotReleased, LeakError, policy_context
from .streams import Stream, retrain_loss_rate
from .types import (
    ACTION_KINDS,
    CANDIDATE,
    COUNT_KEY,
    FREE_KINDS,
    INCUMBENT,
    RETRAINED,
    Action,
    ActionNotAllowed,
    BudgetExceeded,
    BudgetView,
    CostVector,
    EnvSpec,
    ObservableState,
    PendingView,
    ReleasedLabel,
)


class Policy(Protocol):
    name: str

    def reset(self, env: EnvSpec) -> None: ...

    def act(self, state: ObservableState) -> Action | Iterable[Action] | None: ...


@dataclass
class Ledger:
    costs: CostVector
    loss: float = 0.0
    counts: dict[str, int] = field(default_factory=lambda: {k: 0 for k in COUNT_KEY.values()})
    parts: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in COUNT_KEY.values()})
    charged_actions: set[int] = field(default_factory=set)

    def charge(self, action_id: int, kind: str, amount: float) -> None:
        if action_id in self.charged_actions:
            raise RuntimeError(f"action {action_id} charged twice")
        self.charged_actions.add(action_id)
        self.counts[COUNT_KEY[kind]] += 1
        self.parts[COUNT_KEY[kind]] += amount

    @property
    def J(self) -> float:
        return self.loss + sum(self.parts.values())

    def breakdown(self) -> dict[str, float]:
        return {"loss": self.loss, **{f"cost_{k}": v for k, v in self.parts.items()}, "J": self.J}


@dataclass
class RunResult:
    policy: str
    seed: int
    stream_fingerprint: str
    spec_id: str
    J: float
    breakdown: dict[str, float]
    counts: dict[str, int]
    audit: AuditLog
    model_path: np.ndarray  # model in force (primary) at each round (evaluator-side record)
    served_path: np.ndarray  # model that served each round (differs from primary when routed)
    loss_path: np.ndarray
    env: EnvSpec
    null_holds: dict[str, bool]
    leak_attempts: list[str]
    routed: dict[str, dict[int, int]] = field(default_factory=dict)


ORDER = {
    "rollback": 0,
    "switch": 1,
    "route": 2,
    "retrain": 3,
    "alert": 4,
    "abstain": 5,
    "query": 6,
    "continue": 7,
}


class Simulator:
    def __init__(self, stream: Stream, env: EnvSpec, on_violation: str = "raise") -> None:
        if on_violation not in ("raise", "refuse"):
            raise ValueError("on_violation must be 'raise' or 'refuse'")
        if stream.T != env.T:
            raise ValueError("stream and env horizon differ")
        self.stream, self.env, self.on_violation = stream, env, on_violation

    # ---- hooks (overridden by fault-injection tests; production path uses only these)
    def _charge(self, ledger: Ledger, aid: int, kind: str) -> float:
        amt = self.env.costs.price(kind)
        ledger.charge(aid, kind, amt)
        return amt

    def _release_time(self, request_t: int, label_round: int | None = None) -> int | None:
        s = self.stream
        lr = request_t if label_round is None else label_round
        if s.missing[lr - 1]:
            return None
        return request_t + int(s.delay[lr - 1])

    # ---- main loop
    def run(self, policy: Policy) -> RunResult:
        env, s, clocks, bud = self.env, self.stream, self.env.clocks, self.env.budget
        T = env.T
        regime = s.truth.regime
        audit = AuditLog(
            run_id=f"{policy.name}|{s.spec.spec_id}|{s.seed}",
            meta={
                "policy": policy.name,
                "seed": s.seed,
                "fingerprint": s.fingerprint,
                "spec_id": s.spec.spec_id,
                "T": T,
                "costs": env.costs.name,
            },
        )
        ledger = Ledger(env.costs)
        policy.reset(env)

        model, prev_m = INCUMBENT, None
        route: tuple[int, float] | None = None
        retrained_ready = False
        retrain_ready_t: int | None = None
        retrain_done_t: int | None = None
        retrain_action_id: int | None = None
        q_pending = q_active = None
        last_retrain_start = -(10**9)
        last_switch_t = -(10**9)
        n_retrain = n_switch = n_rollback = 0
        deployments: list[tuple[int, int, str, int | None]] = []  # (effective_t, to, cause, aid)
        pending: dict[int, list[tuple]] = {}
        outstanding: dict[int, tuple[int, int | None]] = {}
        requested_rounds: set[int] = set()
        history: list[ReleasedLabel] = []
        released_by_served: dict[int, int] = {}
        requested_by_served: dict[int, int] = {}
        rounds_by_served: dict[int, int] = {}
        label_used = 0
        next_label_id = 0
        next_action_id = 0
        model_path = np.zeros(T, dtype=np.int8)
        served_path = np.zeros(T, dtype=np.int8)
        loss_path = np.zeros(T)
        xro = s.x.view()
        xro.setflags(write=False)
        sro = served_path.view()
        sro.setflags(write=False)

        def model_loss(m: int, rnd: int) -> float:
            if m == INCUMBENT:
                return float(s.loss_inc[rnd - 1])
            if m == CANDIDATE:
                return float(s.loss_cand[rnd - 1])
            return float(s.retrain_u[rnd - 1] < q_active)

        def deploy(t_eff: int, to: int, cause: str, aid: int | None, t_now: int) -> None:
            nonlocal model, prev_m, route
            if to == model:
                return
            frm = model
            prev_m = None if cause == "rollback" else model
            model = to
            route = None  # a model change cancels any standing canary route
            audit.add(
                "deploy",
                t_now,
                effective_t=t_eff,
                from_model=frm,
                to_model=to,
                cause=cause,
                charged_to=aid,
            )

        for t in range(1, T + 1):
            if retrain_done_t == t:
                retrained_ready, retrain_ready_t, q_active = True, t, q_pending
                audit.add("retrain_done", t, charged_to=retrain_action_id, q=q_active)
                if clocks.deploy_on_complete:
                    deploy(t, RETRAINED, "retrain_complete", retrain_action_id, t)
                retrain_done_t = None
            for dep in [d for d in deployments if d[0] <= t]:
                deployments.remove(dep)
                deploy(dep[0], dep[1], dep[2], dep[3], t)
            for rq, lid, lr, served_m, prop, obs in sorted(
                pending.pop(t, []), key=lambda r: (r[0], r[1])
            ):
                history.append(ReleasedLabel(lid, rq, t, obs, served_m, prop, lr))
                outstanding.pop(lid, None)
                released_by_served[served_m] = released_by_served.get(served_m, 0) + 1
                audit.add(
                    "release",
                    t,
                    label_id=lid,
                    request_t=rq,
                    label_round=lr,
                    release_t=t,
                    delivered_t=t,
                )
            budget_view = BudgetView(
                label_used=label_used,
                label_cap=bud.label_cap,
                pending=len(outstanding),
                retrain_used=n_retrain,
                switch_used=n_switch,
                rollback_used=n_rollback,
                retrain_busy_until=retrain_done_t,
                retrain_cooldown_left=max(0, last_retrain_start + bud.retrain_cooldown - t + 1)
                if n_retrain
                else 0,
                switch_cooldown_left=max(0, last_switch_t + bud.switch_cooldown - t + 1)
                if n_switch + n_rollback
                else 0,
            )
            state = ObservableState(
                t=t,
                T=T,
                m=model,
                prev_m=prev_m,
                retrained_ready=retrained_ready,
                b=budget_view,
                Q=tuple(
                    PendingView(lid, rq, rel if env.delay_info == "exact" else None)
                    for lid, (rq, rel) in sorted(outstanding.items())
                ),
                H=tuple(history),
                x=float(s.x[t - 1]),
                x_hist=xro[: t - 1],
                u=tuple(float(v) for v in s.query_u[t - 1]),
                served_hist=sro[: t - 1],
                route=route,
                routed_labels=tuple(sorted(released_by_served.items())),
            )
            with policy_context() as leaks:
                try:
                    out = policy.act(state)
                except LeakError:
                    out = None
            if leaks:
                audit.add("leak", t, attempts=list(leaks))
                exc = (
                    LabelNotReleased
                    if any(a.startswith("PendingView") for a in leaks)
                    else LeakError
                )
                raise exc(f"policy {policy.name} attempted evaluator access: {leaks}")

            abstained = False
            changed_this_round = False
            finalized = False
            served_t = model
            seen: set[str] = set()

            def finalize() -> None:
                nonlocal finalized, served_t
                for dep in [d for d in deployments if d[0] <= t]:
                    deployments.remove(dep)
                    deploy(dep[0], dep[1], dep[2], dep[3], t)
                served_t = model
                if route is not None:
                    hit = bool(s.route_u[t - 1] < route[1])
                    served_t = route[0] if hit else model
                    audit.add(
                        "route",
                        t,
                        target=route[0],
                        fraction=route[1],
                        primary=model,
                        served=served_t,
                    )
                finalized = True

            for a in sorted(_normalise(out), key=lambda a: ORDER[a.kind]):
                if a.kind not in env.allowed_actions:
                    raise ActionNotAllowed(f"{policy.name}: {a.kind} not in declared vocabulary")
                if ORDER[a.kind] > ORDER["retrain"] and not finalized:
                    finalize()
                aid = next_action_id
                next_action_id += 1
                if a.kind == "continue":
                    audit.add(
                        "action",
                        t,
                        action_id=aid,
                        kind="continue",
                        performed=False,
                        reason="noop",
                        charge=0.0,
                    )
                    continue
                reason = None
                if a.kind in seen and a.kind != "query":
                    reason = "duplicate_kind_in_round"
                seen.add(a.kind)
                over = None
                lbl_round = t
                if reason is None:
                    if a.kind == "query":
                        lbl_round = t if a.round is None else int(a.round)
                        if lbl_round < 1 or lbl_round > t or t - lbl_round > clocks.max_lookback:
                            reason = "round_out_of_lookback"
                        elif lbl_round in requested_rounds:
                            reason = "round_already_requested"
                        elif a.propensity is not None and not 0.0 < a.propensity <= 1.0:
                            reason = "bad_propensity"
                        elif label_used >= bud.label_cap:
                            over = f"label budget {bud.label_cap} exhausted at t={t}"
                        elif bud.pending_cap is not None and len(outstanding) >= bud.pending_cap:
                            over = f"pending cap {bud.pending_cap} reached at t={t}"
                    elif a.kind == "route":
                        if a.target not in (INCUMBENT, CANDIDATE, RETRAINED):
                            reason = "bad_target"
                        elif a.fraction is None or not 0.0 <= a.fraction <= 1.0:
                            reason = "bad_fraction"
                        elif a.fraction > 0 and a.target == model:
                            reason = "already_deployed"
                        elif a.target == RETRAINED and not retrained_ready:
                            reason = "retrained_not_ready"
                    elif a.kind == "retrain":
                        if retrain_done_t is not None:
                            reason = "retrain_in_progress"
                        elif n_retrain and t < last_retrain_start + bud.retrain_cooldown:
                            reason = "retrain_cooldown"
                        elif bud.retrain_cap is not None and n_retrain >= bud.retrain_cap:
                            over = f"retrain cap {bud.retrain_cap} at t={t}"
                    elif a.kind in ("switch", "rollback"):
                        if changed_this_round:
                            reason = "one_model_change_per_round"
                        elif deployments:
                            reason = "deployment_in_flight"
                        elif (n_switch + n_rollback) and t < last_switch_t + bud.switch_cooldown:
                            reason = "switch_cooldown"
                        elif a.kind == "switch":
                            if a.target not in (INCUMBENT, CANDIDATE, RETRAINED):
                                reason = "bad_target"
                            elif a.target == model:
                                reason = "already_deployed"
                            elif a.target == RETRAINED and not retrained_ready:
                                reason = "retrained_not_ready"
                            elif bud.switch_cap is not None and n_switch >= bud.switch_cap:
                                over = f"switch cap {bud.switch_cap} at t={t}"
                        else:
                            if prev_m is None:
                                reason = "nothing_to_roll_back_to"
                            elif bud.rollback_cap is not None and n_rollback >= bud.rollback_cap:
                                over = f"rollback cap {bud.rollback_cap} at t={t}"
                if over is not None:
                    if self.on_violation == "raise":
                        audit.add(
                            "action",
                            t,
                            action_id=aid,
                            kind=a.kind,
                            performed=False,
                            reason="budget_violation",
                            charge=0.0,
                        )
                        raise BudgetExceeded(over)
                    reason = "budget_refused"
                if reason is not None:
                    audit.add(
                        "action",
                        t,
                        action_id=aid,
                        kind=a.kind,
                        performed=False,
                        reason=reason,
                        charge=0.0,
                    )
                    continue
                # ---- performed
                amt = 0.0 if a.kind in FREE_KINDS else self._charge(ledger, aid, a.kind)
                audit.add(
                    "action",
                    t,
                    action_id=aid,
                    kind=a.kind,
                    performed=True,
                    target=a.target,
                    reason="ok",
                    charge=amt,
                    propensity=a.propensity,
                    u_index=a.u_index,
                    label_round=lbl_round if a.kind == "query" else None,
                    fraction=a.fraction,
                )
                if a.kind == "query":
                    label_used += 1
                    requested_rounds.add(lbl_round)
                    lid = next_label_id
                    next_label_id += 1
                    served_m = served_t if lbl_round == t else int(served_path[lbl_round - 1])
                    requested_by_served[served_m] = requested_by_served.get(served_m, 0) + 1
                    rel = self._release_time(t, lbl_round)
                    has_rt = retrain_ready_t is not None and lbl_round >= retrain_ready_t
                    if env.obs_mode == "shadow":
                        obs = [
                            (INCUMBENT, model_loss(INCUMBENT, lbl_round)),
                            (CANDIDATE, model_loss(CANDIDATE, lbl_round)),
                        ]
                        if has_rt:
                            obs.append((RETRAINED, model_loss(RETRAINED, lbl_round)))
                    else:
                        obs = [(served_m, model_loss(served_m, lbl_round))]
                    in_h = rel is not None and rel <= T
                    audit.add(
                        "request",
                        t,
                        label_id=lid,
                        action_id=aid,
                        label_round=lbl_round,
                        propensity=a.propensity,
                        release_t=rel if in_h else None,
                        missing=rel is None,
                        beyond_horizon=rel is not None and rel > T,
                        served=served_m,
                    )
                    outstanding[lid] = (t, rel if in_h else None)
                    if in_h:
                        pending.setdefault(rel, []).append(
                            (t, lid, lbl_round, served_m, a.propensity, tuple(obs))
                        )
                elif a.kind == "switch":
                    n_switch += 1
                    changed_this_round = True
                    last_switch_t = t
                    deployments.append((t + clocks.deploy_lag, a.target, "switch", aid))
                elif a.kind == "rollback":
                    n_rollback += 1
                    changed_this_round = True
                    last_switch_t = t
                    deployments.append((t + clocks.rollback_lag, prev_m, "rollback", aid))
                elif a.kind == "route":
                    route = (a.target, float(a.fraction)) if a.fraction > 0 else None
                elif a.kind == "retrain":
                    n_retrain += 1
                    last_retrain_start = t
                    retrain_action_id = aid
                    retrain_done_t = t + max(1, clocks.retrain_duration)
                    lo = max(1, t - clocks.w_train + 1)
                    in_win = [lab for lab in history if lo <= lab.label_round <= t]
                    clean = [lab for lab in in_win if regime[lab.label_round - 1] == regime[t - 1]]
                    f_lab = len(in_win) / clocks.w_train
                    e_clean = len(clean) / clocks.w_train
                    q_pending = retrain_loss_rate(s.spec, e_clean)
                    audit.add(
                        "retrain_start",
                        t,
                        action_id=aid,
                        completes_t=retrain_done_t,
                        label_fraction=f_lab,
                        clean_fraction=e_clean,
                        q=q_pending,
                    )
                elif a.kind == "abstain":
                    abstained = True
            if not finalized:
                finalize()
            l_t = clocks.fallback_loss if abstained else model_loss(served_t, t)
            ledger.loss += l_t
            loss_path[t - 1] = l_t
            model_path[t - 1] = model
            served_path[t - 1] = served_t
            rounds_by_served[served_t] = rounds_by_served.get(served_t, 0) + 1

        audit.add("final", T, breakdown=ledger.breakdown(), counts=dict(ledger.counts))
        return RunResult(
            policy=policy.name,
            seed=s.seed,
            stream_fingerprint=s.fingerprint,
            spec_id=s.spec.spec_id,
            J=ledger.J,
            breakdown=ledger.breakdown(),
            counts=dict(ledger.counts),
            audit=audit,
            model_path=model_path,
            served_path=served_path,
            loss_path=loss_path,
            env=env,
            null_holds=dict(s.truth.null_holds),
            leak_attempts=[],
            routed={
                "rounds": rounds_by_served,
                "labels_requested": requested_by_served,
                "labels_released": released_by_served,
            },
        )


def _normalise(out: Any) -> list[Action]:
    if out is None:
        return []
    if isinstance(out, Action):
        return [out]
    acts = list(out)
    for a in acts:
        if not isinstance(a, Action):
            raise TypeError(f"policy returned non-Action {a!r}; valid kinds {ACTION_KINDS}")
    return acts
