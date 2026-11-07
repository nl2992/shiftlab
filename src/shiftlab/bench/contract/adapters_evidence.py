"""Contract-native promoter shell for evidence-only comparisons (Q1 hook (b)).

``EvidencePromoterPolicy`` does exactly three things and nothing else: (1) query on a schedule it DECLARES, (2) pass every
released outcome to an evidence object through :class:`evidence_seam.OutcomeSeam`, (3) switch incumbent -> candidate the first
round the evidence alarms (``log e >= log(1/alpha)``). No rollback, retrain, abstain or alert, so any difference between two
shells is the evidence process.

Query schedules (selection regime declared to the evidence, so validity claims can be checked):
  ``calendar``     deterministic equally spaced calendar (constant gaps), propensity 1.0       -> 'predictable'
  ``cyclic_gaps``  deterministic calendar with a fixed cyclic gap pattern (irregular gaps)     -> 'predictable'
  ``bernoulli``    query at round t iff ``state.u[0] < q`` (q = B/T by default), propensity q   -> 'exogenous'
Every query carries its declared propensity; the simulator verifies it against the shared uniforms.

The shell never reads evaluator objects; the evidence sees only ``ObservableState.H`` through the seam. Requires
``obs_mode='shadow'`` (the paired difference must be identifiable from one label).
"""

from __future__ import annotations

from .evidence_seam import OutcomeSeam
from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState

SCHEDULES = ("calendar", "cyclic_gaps", "bernoulli")


class EvidencePromoterPolicy(BasePolicy):
    name = "evidence_promoter"

    def __init__(
        self,
        evidence,
        alpha: float = 0.1,
        schedule: str = "calendar",
        gaps: tuple[int, ...] = (1, 3, 2, 6),
        q: float | None = None,
    ) -> None:
        if schedule not in SCHEDULES:
            raise ValueError(f"schedule must be one of {SCHEDULES}")
        self.evidence, self.alpha, self.schedule, self.gaps, self.q = (
            evidence,
            alpha,
            schedule,
            gaps,
            q,
        )
        self.first_alarm_t: int | None = None

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        if env.obs_mode != "shadow":
            raise NotImplementedError("evidence promoter needs obs_mode='shadow'")
        B, T = env.budget.label_cap, env.T
        self.seam = OutcomeSeam()
        self.evidence.bind(env)
        self.first_alarm_t = None
        if self.schedule == "calendar":
            self.calendar = {max(1, -(-j * T // B)) for j in range(1, B + 1)} if B else set()
        elif self.schedule == "cyclic_gaps":
            t, cal, k = 0, set(), 0
            while len(cal) < B:
                t += self.gaps[k % len(self.gaps)]
                k += 1
                if t > T:
                    break
                cal.add(t)
            self.calendar = cal
        else:
            self.calendar = set()
            self.q_eff = self.q if self.q is not None else min(1.0, B / max(1, T))
        self.evidence.declare_selection(
            "exogenous" if self.schedule == "bernoulli" else "predictable"
        )

    def _query(self, state: ObservableState) -> Action | None:
        env = self.env
        if state.b.label_remaining <= 0 or (
            env.budget.pending_cap is not None and state.b.pending >= env.budget.pending_cap
        ):
            return None
        if self.schedule == "bernoulli":
            if state.u and state.u[0] < self.q_eff:
                return Action("query", propensity=self.q_eff, u_index=0)
            return None
        return Action("query", propensity=1.0) if state.t in self.calendar else None

    def act(self, state: ObservableState):
        self.evidence.observe(self.seam.feed(state))
        acts = []
        q = self._query(state)
        if q is not None:
            acts.append(q)
        if state.m == INCUMBENT and self.evidence.alarm(self.alpha):
            if self.first_alarm_t is None:
                self.first_alarm_t = state.t
            acts.append(Action("switch", target=CANDIDATE))
        return acts or Action("continue")


class _EvidencePromoterAdapter:
    vocabulary = ("query", "continue", "switch")
    port_status = "CONTRACT_NATIVE_EVIDENCE_SHELL"

    def __init__(self, name: str, make_evidence, claimed_null: str, **kw) -> None:
        self.name, self.make_evidence, self.claimed_null, self.kw = (
            name,
            make_evidence,
            claimed_null,
            kw,
        )

    def build(self, env: EnvSpec) -> EvidencePromoterPolicy:
        pol = EvidencePromoterPolicy(self.make_evidence(), **self.kw)
        pol.name = self.name
        pol.reset(env)
        return pol


def promoter_adapter(
    identity: dict, *, alpha: float = 0.1, schedule: str = "calendar", **kw
) -> _EvidencePromoterAdapter:
    """Evidence-only promoter for a registry Q1 identity (see ``evidence_q1.build_evidence``)."""
    from .evidence_q1 import build_evidence

    return _EvidencePromoterAdapter(
        f"promoter[{identity['family']}.{identity['variant']}|{identity['target_null']}]",
        lambda: build_evidence(identity),
        identity["target_null"],
        alpha=alpha,
        schedule=schedule,
        **kw,
    )
