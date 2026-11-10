"""Pathwise budget ledger. A query is paid and reserved at request time (pending included)."""

from __future__ import annotations

from .contracts import Costs


class BudgetError(RuntimeError):
    pass


class BudgetLedger:
    def __init__(self, B: int, costs: Costs, compute_budget: int | None = None) -> None:
        if B < 0:
            raise ValueError("B must be >= 0")
        self.B, self.costs, self.compute_budget = int(B), costs, compute_budget
        self.requested = self.released = 0
        self.compute_used = self.switches = self.retrains = 0
        self.deploy_loss = 0.0

    @property
    def labels_remaining(self) -> int:
        return self.B - self.requested

    @property
    def pending(self) -> int:
        return self.requested - self.released

    @property
    def compute_remaining(self) -> int | None:
        return None if self.compute_budget is None else self.compute_budget - self.compute_used

    def request_query(self) -> None:
        if self.requested >= self.B:
            raise BudgetError("label budget exceeded (pending requests count)")
        self.requested += 1

    def release(self, n: int) -> None:
        self.released += n

    def use_compute(self) -> None:
        if self.compute_budget is not None and self.compute_used >= self.compute_budget:
            raise BudgetError("compute budget exceeded")
        self.compute_used += 1

    def fees(self) -> dict:
        c = self.costs
        return {
            "label_fee": c.c_q * self.requested,
            "switch_fee": c.k * self.switches,
            "compute_fee": c.c_compute * self.compute_used,
            "retrain_fee": c.c_retrain * self.retrains,
        }

    def totals(self) -> dict:
        f = self.fees()
        return {
            **f,
            "deploy_loss": self.deploy_loss,
            "J": self.deploy_loss + sum(f.values()),
            "n_queries": self.requested,
            "n_released": self.released,
            "n_pending_end": self.pending,
            "n_switches": self.switches,
        }

    def check(self, queue_pending: int | None = None) -> None:
        """Accounting identities; raises AssertionError on violation."""
        assert 0 <= self.requested <= self.B
        assert 0 <= self.released <= self.requested
        assert self.pending == self.requested - self.released
        if queue_pending is not None:
            assert queue_pending == self.pending
        if self.compute_budget is not None:
            assert self.compute_used <= self.compute_budget
        t = self.totals()
        parts = t["deploy_loss"] + t["label_fee"] + t["switch_fee"] + t["compute_fee"]
        assert abs(t["J"] - parts - t["retrain_fee"]) < 1e-9
