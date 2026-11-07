"""Label-outcome evidence seam (Q1 hook, ``d2a.evidence_log_lik`` successor; contract-native promoter shell shares it).

Why: the legacy hook ``EvidenceModel.log_lik(z, gap)`` only sees three standardised monitor proxies, never the
binary label-chain outcomes that exact-gap Markov evidence, envelopes, hazards and restarts need. The seam delivers
RELEASED labelled observations, and only those, as a stream of :class:`ReleasedOutcome`.

What an outcome carries (everything is read from ``ObservableState.H`` at release time; no evaluator object):
  request_round  round at which the label was requested        label_round   round t_i whose outcome it reveals
  release_round  round at which the label became visible       losses        ((model, loss), ...) as released
  d              paired loss difference ``loss(other) - loss(base)`` (default other=CANDIDATE, base=INCUMBENT; negative =
                 candidate better) or ``None`` when both losses are not identifiable from this label (obs_mode='deployed')
  gap            ``g_i = t_i - t_{i-1}`` in LABEL (event) rounds against the previous in-order identified outcome
                 (``None`` for the first outcome or an out-of-order one)
  order          'first' | 'in_order' | 'out_of_order' (label_round <= the largest label_round already delivered)
  selection      :class:`SelectionRecord` (declared propensity, model that served the round, delay)

Released order is delivery order; out-of-order outcomes keep their own label_round but get ``gap=None`` because the
forward Markov chain over event rounds cannot absorb an observation that lies BEFORE one already used (conditioning on a
later observation would break the Markov factorisation). Consumers decide (the Q1 processes drop them and count them).

Selection / predictability: P^{g_i} evidence is valid only if the choice of ``t_i`` carries no information about the
outcome ``Z_i`` beyond what the evidence has already conditioned on (F_{i-1}-measurable or exogenous randomisation). The seam
exposes the *record* (propensity) that lets a consumer CHECK a declaration; it never infers predictability.

Default-off: :class:`OutcomeAugmentedEvidence` is opt-in; the Drift2Act host only calls the seam when its evidence object has
an ``outcome_sink`` attribute, so the default ``ProxyEvidence`` host path is untouched (golden test in test_q1_evidence.py).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .types import CANDIDATE, INCUMBENT, EnvSpec, ObservableState, ReleasedLabel

SELECTION_REGIMES = ("predictable", "exogenous", "monitor_adaptive", "informative", "undeclared")
IN_CONTRACT_REGIMES = ("predictable", "exogenous")


@dataclass(frozen=True)
class SelectionRecord:
    """What the policy itself declared about how this label was selected (nothing evaluator-side)."""

    propensity: (
        float | None
    )  # declared randomisation probability (1.0 = deterministic rule); None = undeclared
    model_at_request: int
    delay: int  # release_round - request_round (observable once released)


@dataclass(frozen=True)
class ReleasedOutcome:
    label_id: int
    request_round: int
    label_round: int
    release_round: int
    losses: tuple[tuple[int, float], ...]
    d: float | None
    gap: int | None
    order: str
    selection: SelectionRecord

    @property
    def z(self) -> int | None:
        """Favourable indicator ``1[d < 0]`` (candidate strictly better); ``None`` if ``d`` is not identifiable."""
        return None if self.d is None else int(self.d < 0)


class OutcomeSeam:
    """Turns the growing ``state.H`` into :class:`ReleasedOutcome` records, once each, in delivery order."""

    def __init__(self, base: int = INCUMBENT, other: int = CANDIDATE) -> None:
        self.base, self.other = base, other
        self.reset()

    def reset(self) -> None:
        self._seen = 0
        self._max_round = 0  # largest label_round among identified, delivered outcomes
        self.n_delivered = self.n_unidentified = self.n_out_of_order = 0

    def _convert(self, lab: ReleasedLabel) -> ReleasedOutcome:
        a, b = lab.loss(self.base), lab.loss(self.other)
        d = None if a is None or b is None else float(b - a)
        rnd = lab.label_round or lab.request_t
        gap, order = None, "first"
        if d is None:
            self.n_unidentified += 1
            order = "unidentified"
        elif self._max_round == 0:
            self._max_round = rnd
        elif rnd > self._max_round:
            gap, order = rnd - self._max_round, "in_order"
            self._max_round = rnd
        else:
            order = "out_of_order"
            self.n_out_of_order += 1
        self.n_delivered += 1
        return ReleasedOutcome(
            lab.label_id,
            lab.request_t,
            rnd,
            lab.release_t,
            lab.obs,
            d,
            gap,
            order,
            SelectionRecord(lab.propensity, lab.model_at_request, lab.release_t - lab.request_t),
        )

    def feed(self, state: ObservableState) -> list[ReleasedOutcome]:
        """New outcomes since the previous call (``state.H`` is append-only in release order)."""
        new = state.H[self._seen :]
        self._seen = len(state.H)
        return [self._convert(lab) for lab in new]


class OutcomeEvidence(Protocol):
    """Consumer of the seam (see ``evidence_q1.GapEvidence``)."""

    def bind(self, env: EnvSpec) -> None: ...
    def observe(self, outcomes: Sequence[ReleasedOutcome]) -> None: ...
    def belief_increment(self) -> float: ...


class OutcomeAugmentedEvidence:
    """Drift2Act ``EvidenceModel`` = legacy proxy evidence + released-outcome evidence (hook (a)).

    ``log_lik(z, gap)`` returns ``base.log_lik(z, gap) + beta * [0, d, d, d]`` where ``d`` is the increment of the outcome
    process' log e-value since the previous call (evidence of drift vs 'none' contributed by the label chain; the three
    drift types are not separated by a binary paired outcome). The host calls ``bind_env`` at reset and ``outcome_sink(state)``
    each round before the belief update. Mapping an e-process increment to a belief likelihood is a modelling choice of
    this seam, NOT a validity claim: the belief filter is not an e-process.
    """

    def __init__(
        self,
        base,
        outcome: OutcomeEvidence,
        beta: float = 1.0,
        clip: float = 5.0,
        seam: OutcomeSeam | None = None,
        selection: str = "monitor_adaptive",
    ) -> None:
        self.base, self.outcome, self.beta, self.clip = base, outcome, beta, clip
        self.selection = selection  # the Drift2Act host picks request sizes from belief/certificate state that uses x_t
        self.seam = seam or OutcomeSeam()
        self.last_outcomes: list[ReleasedOutcome] = []

    def bind_env(self, env: EnvSpec) -> None:
        self.seam.reset()
        self.outcome.bind(env)
        declare = getattr(self.outcome, "declare_selection", None)
        if declare is not None:
            declare(self.selection)

    def outcome_sink(self, state: ObservableState) -> None:
        self.last_outcomes = self.seam.feed(state)
        self.outcome.observe(self.last_outcomes)

    def log_lik(self, z, gap: int = 1) -> np.ndarray:
        inc = float(np.clip(self.outcome.belief_increment(), -self.clip, self.clip))
        return self.base.log_lik(z, gap) + self.beta * np.array([0.0, inc, inc, inc])


__all__ = [
    "IN_CONTRACT_REGIMES",
    "SELECTION_REGIMES",
    "OutcomeAugmentedEvidence",
    "OutcomeEvidence",
    "OutcomeSeam",
    "ReleasedOutcome",
    "SelectionRecord",
]
