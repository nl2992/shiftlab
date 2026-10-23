"""Sequential full-feedback certification for frozen shadow candidates."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .eprocess import BoundedMeanEProcess


@dataclass(frozen=True)
class CandidateVersion:
    candidate_id: str
    parent_version: str
    training_cutoff: int
    candidate_index: int


class CandidatePromotionTest:
    """Certify a frozen candidate against an incumbent on fresh paired outcomes.

    The e-process tests whether the candidate's mean net cost improvement is at most
    zero. Candidate ``i`` receives alpha_i=alpha_total/[i(i+1)], whose sum is at
    most alpha_total over an unbounded sequence of candidate tests. Candidate
    selection may use past data, but the candidate must be frozen before the tested
    events and each tested event must provide valid paired costs.
    """

    def __init__(
        self,
        version: CandidateVersion,
        *,
        alpha_total: float = 0.05,
        max_event_cost: float = 1.0,
        switching_cost: float = 0.0,
    ):
        if not version.candidate_id or not version.parent_version:
            raise ValueError("candidate and parent versions must be nonempty")
        if isinstance(version.training_cutoff, bool) or version.training_cutoff < 0:
            raise ValueError("training_cutoff must be a nonnegative event index")
        if isinstance(version.candidate_index, bool) or version.candidate_index < 1:
            raise ValueError("candidate_index must be a positive integer")
        if not np.isfinite(alpha_total) or not 0 < alpha_total < 1:
            raise ValueError("alpha_total must lie in (0, 1)")
        if not np.isfinite(max_event_cost) or max_event_cost <= 0:
            raise ValueError("max_event_cost must be finite and positive")
        if not np.isfinite(switching_cost) or switching_cost < 0:
            raise ValueError("switching_cost must be finite and nonnegative")
        alpha_i = alpha_total / (version.candidate_index * (version.candidate_index + 1))
        self.version = version
        self.alpha_total = float(alpha_total)
        self.alpha_i = float(alpha_i)
        self.max_event_cost = float(max_event_cost)
        self.switching_cost = float(switching_cost)
        self.process = BoundedMeanEProcess(
            bound=max_event_cost + switching_cost,
            alpha=alpha_i,
        )
        self.last_event = version.training_cutoff

    @property
    def certified(self) -> bool:
        return self.process.alarm

    @property
    def log_e_value(self) -> float:
        return self.process.log_e_value

    def update(
        self,
        *,
        event_index: int,
        incumbent_cost: float,
        candidate_cost: float,
    ) -> float:
        """Add a fresh paired observation and return log evidence for net benefit."""
        if isinstance(event_index, bool) or event_index <= self.last_event:
            raise ValueError("evaluation events must be strictly after training and ordered")
        for value, name in (
            (incumbent_cost, "incumbent_cost"),
            (candidate_cost, "candidate_cost"),
        ):
            if not np.isfinite(value) or not 0 <= value <= self.max_event_cost:
                raise ValueError(f"{name} must lie in [0, max_event_cost]")
        gain = incumbent_cost - candidate_cost - self.switching_cost
        self.last_event = int(event_index)
        return self.process.update(gain)
