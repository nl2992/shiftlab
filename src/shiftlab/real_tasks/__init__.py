"""Lane B real-data replay tasks (R1 frozen specs): OPSD reserve and Binance momentum.

Each task builds, per decision round, a public event (features available at decision time,
deployed = incumbent action, reference = candidate action), an evaluator-side outcome stream
(losses, paired cost ``Z = l(incumbent) - l(candidate)`` and the time/round at which that label is
released), and imposed cost parameters. Oracle/outcome values never enter ``PublicEvent``: ``x`` holds calendar fields only (Amendment A-R3);
the two policies' actions are a deliberate public channel (they depend on public data).

Window guard: only development windows may be touched. The locked holdouts (OPSD from
2020-01-01 local = 2019-12-31T23:00 UTC, Binance from 2026-01-01) raise ``HoldoutAccessError`` before any file is opened.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

import numpy as np

from ..contract.interface import PublicEvent, TaskSpec

# Local midnight of 2020-01-01 in CET is 2019-12-31T23:00 UTC: the first holdout delivery hour.
OPSD_HOLDOUT_START = np.datetime64("2019-12-31T23:00:00")
BINANCE_HOLDOUT_START = np.datetime64("2026-01-01T00:00:00")


# Release round of a label that is never released inside the stream (not a delay, not delivered).
UNRELEASED = int(np.iinfo(np.int64).max // 4)


class HoldoutAccessError(RuntimeError):
    """A locked-holdout timestamp was requested."""


def guard_timestamps(timestamps, holdout_start: np.datetime64, what: str) -> None:
    """Raise if any timestamp lies at or after ``holdout_start`` (UTC, naive datetime64)."""
    stamps = np.asarray(timestamps).astype("datetime64[ns]")
    if stamps.size and stamps.max() >= holdout_start.astype("datetime64[ns]"):
        raise HoldoutAccessError(f"{what}: timestamps at or after {holdout_start} are locked")


@dataclass(frozen=True)
class CostParams:
    """Imposed (not observed) budget, query cost and switch cost, all in normalised loss units."""

    budget_fractions: tuple[float, ...]
    primary_budget: float
    query_costs: tuple[float, ...]
    primary_query_cost: float
    switch_costs: tuple[float, ...]
    primary_switch_cost: float
    description: str = ""


@dataclass(frozen=True)
class PublicRounds:
    """Public side: nothing here depends on an outcome of the same or a later round."""

    round_time: np.ndarray  # event time (datetime64[ns], UTC)
    decision_time: np.ndarray  # instant at which the action is chosen
    x: np.ndarray  # (n, p) features available at decision_time
    deployed_action: np.ndarray  # int64 (OPSD: 24-bit mask of hourly reserve decisions)
    reference_action: np.ndarray
    disagreement_units: np.ndarray  # secondary count (OPSD: hours differing; Binance: 0/1)
    adjacent_to_previous: np.ndarray  # True iff the previous round is the immediately preceding one

    @property
    def disagreement(self) -> np.ndarray:
        return self.deployed_action != self.reference_action

    def __len__(self) -> int:
        return len(self.round_time)


@dataclass(frozen=True)
class EvaluatorOutcomes:
    """Evaluator side only. ``release_round[t]`` is the first round whose decision time is at or
    after ``label_available_time[t]`` (``n`` when it is never released inside the stream)."""

    loss_incumbent: np.ndarray
    loss_candidate: np.ndarray
    paired_cost: np.ndarray
    label_available_time: np.ndarray
    release_round: np.ndarray
    # False: the label is missing at release (no Z); paired_cost/losses are NaN there.
    label_observed: np.ndarray | None = None
    # Evaluator diagnostic only (standalone-policy turnover fee); NOT part of the switch cost k.
    diagnostic_turnover_fee_incumbent: np.ndarray | None = None
    diagnostic_turnover_fee_candidate: np.ndarray | None = None

    @property
    def observed(self) -> np.ndarray:
        if self.label_observed is None:
            return np.ones(len(self.paired_cost), dtype=bool)
        return self.label_observed

    @property
    def released(self) -> np.ndarray:
        """True where the label is released inside the stream (False: never delivered)."""
        return self.release_round < UNRELEASED

    def delay_rounds(self) -> np.ndarray:
        """Release round minus event round for released labels; -1 marks never-released labels."""
        rounds = np.arange(len(self.release_round))
        return np.where(self.released, self.release_round - rounds, -1)

    def visible_at_round(self, t: int) -> np.ndarray:
        """Indices of rounds whose labels are visible when the action of round ``t`` is chosen."""
        return np.flatnonzero(self.release_round <= t)


@dataclass(frozen=True)
class RealTask:
    name: str
    public: PublicRounds
    outcomes: EvaluatorOutcomes
    costs: CostParams
    cost_bound: float = 1.0
    price_unit: float = 1.0  # harness budget accounting: one label = one price unit
    exclusions: dict[str, int] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.public)

    def public_events(self) -> Iterator[PublicEvent]:
        """Yield contract events. ``t``, ``disagreement``-consistency, ``price`` and
        ``remaining_budget`` are re-assigned by the harness; placeholders are given here."""
        pub = self.public
        for i in range(len(pub)):
            yield PublicEvent(
                t=i,
                x=pub.x[i],
                deployed_action=int(pub.deployed_action[i]),
                reference_action=int(pub.reference_action[i]),
                disagreement=bool(pub.deployed_action[i] != pub.reference_action[i]),
                price=self.price_unit,
                remaining_budget=0.0,
            )

    def evaluator_outcomes(self) -> EvaluatorOutcomes:
        return self.outcomes

    def task_spec(self, budget_fraction: float, *, alpha: float = 0.05, epsilon: float = 0.0):
        return TaskSpec(
            cost_bound=self.cost_bound,
            epsilon=epsilon,
            alpha=alpha,
            horizon=len(self),
            label_budget=float(budget_fraction) * len(self) * self.price_unit,
            price_range=(self.price_unit, self.price_unit),
        )

    def harness_paired_costs(self) -> tuple[np.ndarray, int]:
        """Paired costs for ``run_monitor``; missing labels (no Z) become 0 and are counted.

        The v1 harness cannot represent missing feedback at release, so this is a smoke-only
        approximation; the count of affected disagreement rounds is returned."""
        cost = self.outcomes.paired_cost
        missing = ~self.outcomes.observed
        affected = int((missing & self.public.disagreement).sum())
        return np.where(missing, 0.0, cost), affected

    def slice(self, start: int, stop: int) -> RealTask:
        sl = slice(start, stop)
        pub, out = self.public, self.outcomes
        public = PublicRounds(
            pub.round_time[sl],
            pub.decision_time[sl],
            pub.x[sl],
            pub.deployed_action[sl],
            pub.reference_action[sl],
            pub.disagreement_units[sl],
            pub.adjacent_to_previous[sl],
        )
        raw = out.release_round[sl]
        inside = raw < min(stop, len(out.release_round))
        release = np.where(inside & (raw < UNRELEASED), np.clip(raw - start, 0, None), UNRELEASED)
        outcomes = EvaluatorOutcomes(
            out.loss_incumbent[sl],
            out.loss_candidate[sl],
            out.paired_cost[sl],
            out.label_available_time[sl],
            release,
            None if out.label_observed is None else out.label_observed[sl],
            None
            if out.diagnostic_turnover_fee_incumbent is None
            else out.diagnostic_turnover_fee_incumbent[sl],
            None
            if out.diagnostic_turnover_fee_candidate is None
            else out.diagnostic_turnover_fee_candidate[sl],
        )
        return RealTask(
            self.name,
            public,
            outcomes,
            self.costs,
            self.cost_bound,
            self.price_unit,
            dict(self.exclusions),
            dict(self.meta),
        )


def release_rounds(decision_time: np.ndarray, available: np.ndarray) -> np.ndarray:
    """First round whose decision time is >= the label availability time (release, then act).

    A label available only after the last decision is ``UNRELEASED`` (never delivered)."""
    rounds = np.searchsorted(decision_time, available, side="left").astype(np.int64)
    return np.where(rounds >= len(decision_time), UNRELEASED, rounds)


def run_length_summary(flags: np.ndarray, adjacent: np.ndarray) -> dict:
    """Runs of consecutive disagreement rounds; a non-adjacent round (calendar gap) breaks a run."""
    flags = np.asarray(flags, dtype=bool)
    runs: list[int] = []
    length = 0
    for i, flag in enumerate(flags):
        if flag and (length == 0 or adjacent[i]):
            length += 1
        else:
            if length:
                runs.append(length)
            length = 1 if flag else 0
    if length:
        runs.append(length)
    arr = np.asarray(runs, dtype=float)
    n = len(flags)
    p = float(flags.mean()) if n else float("nan")
    prev = flags[:-1] & adjacent[1:]
    p_stay = float(flags[1:][prev].mean()) if prev.any() else float("nan")
    if not len(arr):
        return {"n_runs": 0, "disagreement_rate": p}
    return {
        "disagreement_rate": p,
        "n_disagreement_rounds": int(flags.sum()),
        "n_runs": len(runs),
        "run_length_mean": float(arr.mean()),
        "run_length_median": float(np.median(arr)),
        "run_length_p90": float(np.quantile(arr, 0.9)),
        "run_length_max": int(arr.max()),
        "iid_expected_mean_run": float(1.0 / (1.0 - p)) if p < 1 else float("inf"),
        "p_disagree_given_prev_disagree": p_stay,
        "share_of_disagreement_rounds_in_runs_ge3": float(arr[arr >= 3].sum() / arr.sum()),
        "share_of_disagreement_rounds_in_runs_ge10": float(arr[arr >= 10].sum() / arr.sum()),
    }


def public_stream_audit(task: RealTask, history: int = 3) -> dict:
    """Is Z a deterministic function of the public stream? Disagreement rounds with labels are
    grouped by (i) a *full* key (x rounded and the actions at t and the previous ``history``
    rounds; nearly unique by construction) and (ii) a *coarse* key (differing-unit count and the
    two actions' bit counts, i.e. what the action pair says about direction and size). Z varying
    inside a repeated key shows the stream does not determine Z."""
    pub, out = task.public, task.outcomes
    mask = pub.disagreement & out.observed
    full: dict[tuple, list[float]] = {}
    coarse: dict[tuple, list[float]] = {}
    for i in np.flatnonzero(mask):
        lo = max(0, i - history)
        z = float(out.paired_cost[i])
        full.setdefault(
            (
                tuple(np.round(pub.x[i], 6)),
                tuple(pub.deployed_action[lo : i + 1]),
                tuple(pub.reference_action[lo : i + 1]),
            ),
            [],
        ).append(z)
        coarse.setdefault(
            (
                int(pub.disagreement_units[i]),
                int(pub.deployed_action[i]).bit_count(),
                int(pub.reference_action[i]).bit_count(),
            ),
            [],
        ).append(z)

    def summarise(groups):
        repeated = [v for v in groups.values() if len(v) >= 2]
        varying = [v for v in repeated if np.ptp(v) > 1e-12]
        return {
            "n_keys": len(groups),
            "n_repeated_keys": len(repeated),
            "n_repeated_keys_with_varying_Z": len(varying),
            "share_of_rounds_in_repeated_keys": float(
                sum(len(v) for v in repeated) / max(mask.sum(), 1)
            ),
        }

    return {
        "n_rounds": len(task),
        "n_labelled_disagreement_rounds": int(mask.sum()),
        "full_key": summarise(full),
        "coarse_key": summarise(coarse),
    }
