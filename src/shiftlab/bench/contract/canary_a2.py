"""Amendment A2 RAR-arm policies (NEW module; ``adapters_rar.py`` is untouched).

Registered in docs/d2a_rar/AUTORESEARCH_PROGRAM.md section 3b (draft: docs/d2a_rar/drafts/A2_DRAFT.md section 2).

* ``RARCanaryA2Policy(mode=...)``: RAR ``calibrated_v1`` with one stage-logic change.
    - ``k2_skip``   (CANDIDATE K2): at retrain-ready, if the released-label degradation ``A_pre - A_cur >= 2 theta_R``
                    (RAR's own Delta_crit) skip Canary-1: ``switch(RETRAINED)`` and verify in stage 2 (paired z, rollback on
                    failure); otherwise the normal Canary-1. Reads only released labels.
    - ``k1_p1``     (ABLATION K1): full-traffic stage 1 (p1 = 1.0), same W1/W2.
    - ``L_routed``  (ABLATION L): during Canary-1 labels are requested retrospectively (``query(round=t-1)``) only for
                    rounds ``served_hist`` shows were routed to the retrained model (needs ``ClockSpec.max_lookback >= 1``).
    - ``nocanary``  (CONTROL): retrain gates/holds/alerts intact, retrained model deployed on completion
                    (``deploy_on_complete=True`` clocks) with NO verification stage. RAR's own "canary removal" ablation.
* ``rollback_only()``: RAR with pass-through Gate 2 / Gate 3 and alerts disallowed (``allowed_actions`` without ``alert``),
  canary and holds on = the paper's Binary + canary + holds.
* ``CABHorizonPolicy``: Cost-Aware Binary with H_hat = T - t (remaining horizon) instead of the floored mean inter-detection
  interval; PAPER_RECONSTRUCTION_VARIANT. The paper's definition (floor W_train = 100) cannot fire at contract scale because
  ``drop * 100 < c_r + c_s`` for every drop <= 1 (ledger: CAB host N_r = 0 on S2a).
Fidelity guard (tested): no candidate uses a RETRAINED loss from an incumbent-served round before commit (canary evidence
comes from ``_stats`` which keeps only routed labels).
"""

from __future__ import annotations

from shiftlab.sota.rar.components import HookContext

from .adapters_rar import (
    CANARY1,
    PROFILES,
    SERVING,
    SWITCHING,
    BinaryPolicy,
    RARPolicy,
    canary_clocks,
)
from .types import RETRAINED, Action, ClockSpec, EnvSpec, ObservableState

MODES = ("k2_skip", "k1_p1", "L_routed", "nocanary", "host")
PROFILE = "calibrated_v1"
assert PROFILE in PROFILES
MAX_LOOKBACK = 10


class PassGate:
    """Pass-through Gate 2 / Gate 3 (Rollback-Only = Binary + canary + holds)."""

    def passes(self, ctx: HookContext) -> bool:
        return True


def a2_clocks(kind: str, retrain_duration: int = 20, w_train: int = 100) -> ClockSpec:
    """Family clocks: ``canary`` (deploy_on_complete=False) or ``default``; both allow retrospective queries."""
    kw = {"retrain_duration": retrain_duration, "w_train": w_train, "max_lookback": MAX_LOOKBACK}
    return canary_clocks(**kw) if kind == "canary" else ClockSpec(**kw)


class RARCanaryA2Policy(RARPolicy):
    name = "rar_a2"

    def __init__(self, mode: str = "host", **kw) -> None:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        kw.setdefault("profile", PROFILE)
        if mode == "k1_p1":
            kw["cfg_overrides"] = {**kw.get("cfg_overrides", {}), "p1": 1.0}
        super().__init__(**kw)
        self.mode = mode
        self.name = f"rar_{mode}"

    def reset(self, env: EnvSpec) -> None:
        if self.mode == "nocanary" and not env.clocks.deploy_on_complete:
            raise ValueError("nocanary needs deploy_on_complete=True clocks")
        if self.mode in ("k2_skip", "k1_p1", "L_routed", "host") and env.clocks.deploy_on_complete:
            raise ValueError(f"{self.mode} needs canary clocks (deploy_on_complete=False)")
        if self.mode == "L_routed" and env.clocks.max_lookback < 1:
            raise ValueError("L_routed needs ClockSpec.max_lookback >= 1")
        super().reset(env)
        self.skipped_stage1 = 0

    # ------------------------------------------------------------------ K2 / nocanary
    def _degradation(self, t: int) -> float | None:
        if self.last_t_d is None:
            return None
        a_pre, a_cur = self._acc_pre(self.last_t_d), self._acc_cur(t)
        if a_pre is None or a_cur is None:
            return None
        return float(a_pre - a_cur)

    def _retraining(self, state: ObservableState, acts: list[Action]) -> None:
        t = state.t
        if self.mode == "nocanary":
            r = self._poll_retrain(state)
            if r == "pending":
                return
            if r == "refused":
                self.st = SERVING
                self._log(t, "retrain_refused")
                return
            self._log(t, "commit_nocanary")
            self.st = SERVING
            self._rebirth(t, "commit_nocanary")
            self.c = {}
            return
        if self.mode == "k2_skip":
            r = self._poll_retrain(state)
            if r == "done" and state.m != RETRAINED:
                d = self._degradation(t)
                if d is not None and d >= 2.0 * self.cfg.theta_R - 1e-12:
                    self._start_stage(t, 1)
                    acts.append(Action("switch", target=RETRAINED))
                    self.c["switch_t"] = t
                    self.c["switch_tries"] = 1
                    self.st = SWITCHING
                    self.skipped_stage1 += 1
                    self._log(t, "stage1_skipped", degradation=d)
                    return
        super()._retraining(state, acts)

    # ------------------------------------------------------------------ L: routed-only retrospective labels
    def _query(self, state: ObservableState, acts: list[Action]) -> None:
        if self.mode != "L_routed" or self.st != CANARY1:
            super()._query(state, acts)
            return
        b, t, sh = state.b, state.t, state.served_hist
        if b.label_remaining <= 0 or t < 2 or sh is None or len(sh) < t - 1:
            return
        if self.env.budget.pending_cap is not None and b.pending >= self.env.budget.pending_cap:
            return
        if int(sh[t - 2]) == RETRAINED:
            acts.append(Action("query", round=t - 1))


def rollback_only(**kw) -> RARCanaryA2Policy:
    """Binary + canary + holds: pass-through gates; pair with an env whose ``allowed_actions`` excludes ``alert``."""
    return RARCanaryA2Policy("host", gate2=PassGate(), gate3=PassGate(), **kw)


NO_ALERT_ACTIONS = ("query", "continue", "switch", "retrain", "rollback", "abstain", "route")


class CABHorizonPolicy(BinaryPolicy):
    """Cost-Aware Binary with H_hat = T - t (remaining horizon). PAPER_RECONSTRUCTION_VARIANT (strengthened comparator)."""

    name = "cab_horizon"

    def __init__(self, **kw) -> None:
        kw.setdefault("profile", PROFILE)
        super().__init__(cost_aware=True, **kw)
        self.name = "cab_horizon"

    def _evaluate_flag(self, state: ObservableState, acts: list[Action]) -> None:
        t, env = state.t, self.env
        if not self._can_retrain(state):
            return
        self.flag["evaluated"] = True
        a_pre, a_cur = self._acc_pre(self.flag["t_d"]), self._acc_cur(t)
        d_hat = 0.0 if (a_pre is None or a_cur is None) else max(0.0, a_pre - a_cur)
        H = float(max(0, env.T - t))
        cost = float(env.costs.c_r) + (
            0.0 if env.clocks.deploy_on_complete else float(env.costs.c_s)
        )
        ok = d_hat * H >= cost
        self._log(t, "cost_gate", d_hat=d_hat, H=H, cost=cost, passes=ok)
        if not ok:
            self.flag = None
            return
        self._retrain_used0 = state.b.retrain_used
        acts.append(Action("retrain"))
        self.flag = None
        self.st = "RETRAINING"
        self._log(t, "retrain_issued", reason="cab_horizon")


__all__ = [
    "MAX_LOOKBACK",
    "NO_ALERT_ACTIONS",
    "CABHorizonPolicy",
    "PassGate",
    "RARCanaryA2Policy",
    "a2_clocks",
    "rollback_only",
]
