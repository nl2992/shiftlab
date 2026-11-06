"""Sequential promotion tests for predictably activated challenger model versions.

Exploratory candidate. Each challenger version is tested only against the incumbent frozen at its
activation. A deterministic alpha split across the finite, predeclared version set controls the
union of false promotions under the conditional paired-loss null documented in
``docs/sota_sprint/versioned_challenger_candidate.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from model_picker import ModelPickerDeploymentAdapter
from simulator import Event, QueryRequest, ReleasedFeedback


@dataclass
class _VersionTest:
    baseline: int
    alpha: float
    lambdas: np.ndarray
    wealth: np.ndarray = field(init=False)
    n: int = 0
    alarm: bool = False

    def __post_init__(self) -> None:
        self.wealth = np.ones(len(self.lambdas), dtype=float)

    @property
    def e_value(self) -> float:
        return float(self.wealth.mean())

    def update(self, gain: int) -> None:
        if gain not in (-1, 0, 1):
            raise ValueError("version test expects a bounded paired gain in {-1,0,1}")
        self.wealth *= 1.0 + self.lambdas * gain
        self.n += 1
        if self.e_value >= 1.0 / self.alpha:
            self.alarm = True


class VersionIndexedGate:
    """Version-wise e-process gate with a shared hard label budget.

    Event context is the currently available challenger model index (0 means none). Model index 0
    is the original incumbent; every index >=1 is an immutable challenger version. At its first
    event, a version freezes the currently deployed model as its comparison baseline. Each version
    gets alpha / max_versions. The budget is split evenly over the remaining scheduled versions:
    unused labels carry forward, but the policy leaves one share per future version untouched.

    It queries every current-baseline disagreement while its version budget is available. This
    deterministic acquisition rule avoids a separate propensity estimator; validity requires the
    conditional null to hold on disagreement opportunities.
    """

    name = "version_indexed_gate"

    def __init__(
        self,
        max_versions: int,
        budget: int,
        alpha: float,
        *,
        lambdas: tuple[float, ...] = (0.1, 0.3, 0.5),
        version_weights: tuple[float, ...] | None = None,
        rollback_monitor: bool = False,
    ):
        if max_versions < 1 or budget < 0 or not 0.0 < alpha < 1.0:
            raise ValueError("invalid max_versions, budget, or alpha")
        if not lambdas or any(not 0.0 <= lam <= 1.0 for lam in lambdas):
            raise ValueError("lambdas must be a nonempty sequence in [0,1]")
        self.max_versions = int(max_versions)
        self.B = int(budget)
        self.alpha = float(alpha)
        self.rollback_monitor = bool(rollback_monitor)
        self.lambdas = np.asarray(lambdas, dtype=float)
        if version_weights is None:
            version_weights = tuple(1.0 for _ in range(max_versions))
        if len(version_weights) != max_versions or any(w <= 0 for w in version_weights):
            raise ValueError("version_weights must contain one positive weight per version")
        self.version_weights = np.asarray(version_weights, dtype=float)
        self.version_alpha = self.alpha * self.version_weights / self.version_weights.sum()
        # When rollback monitoring is enabled, each version's allocated error budget is split
        # equally between its single promotion test and its single post-promotion rollback test.
        self.alpha_by_version = self.version_alpha * (0.5 if self.rollback_monitor else 1.0)
        self.rollback_alpha_by_version = self.version_alpha * 0.5
        cumulative = np.cumsum(self.version_weights) / self.version_weights.sum()
        boundaries = np.rint(self.B * cumulative).astype(int)
        self.budget_by_version = np.diff(np.r_[0, boundaries]).astype(int)
        self.deployed = 0
        self.current_version = 0
        self.highest_version_seen = 0
        self.tests: dict[int, _VersionTest] = {}
        self.rollback_tests: dict[int, _VersionTest] = {}
        self.issued: dict[int, list[tuple[str, int, int]]] = {}
        self.labels_by_version: dict[int, int] = {}
        self.issued_counts: dict[tuple[str, int], int] = {}
        # Reserve a deterministic per-test share for post-promotion monitoring. Without this
        # reserve, early promotion evidence can exhaust a version's entire label allocation
        # before the rollback monitor is activated.
        self.promotion_label_budget = {
            v: int(self.budget_by_version[v - 1] // 2) for v in range(1, max_versions + 1)
        }
        self.rollback_label_budget = {
            v: int(self.budget_by_version[v - 1] - self.promotion_label_budget[v])
            for v in range(1, max_versions + 1)
        }
        self.promotions: list[tuple[int, int]] = []
        self.rollbacks: list[tuple[int, int, int]] = []
        self.rejected_versions: set[int] = set()

    def _ensure_test(self, version: int) -> _VersionTest:
        if not 1 <= version <= self.max_versions:
            raise ValueError(f"version {version} outside predeclared range")
        if version not in self.tests:
            if version <= self.highest_version_seen:
                raise ValueError("version activations must be strictly increasing and unique")
            self.highest_version_seen = version
            self.tests[version] = _VersionTest(
                baseline=self.deployed,
                alpha=float(self.alpha_by_version[version - 1]),
                lambdas=self.lambdas.copy(),
            )
        return self.tests[version]

    def predict(self, event: Event) -> int:
        version = int(event.context or 0)
        if version < self.highest_version_seen:
            raise ValueError("version context moved backwards after a later activation")
        self.current_version = version
        rollback = self.rollback_tests.get(self.deployed)
        if rollback is not None and rollback.alarm:
            old_deployed = self.deployed
            self.deployed = rollback.baseline
            self.rejected_versions.add(old_deployed)
            self.rollbacks.append((event.t, old_deployed, self.deployed))
        if version > 0:
            test = self._ensure_test(version)
            if (
                version not in self.rejected_versions
                and test.alarm
                and version != self.deployed
                and test.baseline == self.deployed
            ):
                baseline = test.baseline
                self.deployed = version
                self.promotions.append((event.t, version))
                if self.rollback_monitor:
                    self.rollback_tests[version] = _VersionTest(
                        baseline=baseline,
                        alpha=float(self.rollback_alpha_by_version[version - 1]),
                        lambdas=self.lambdas.copy(),
                    )
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        version = self.current_version
        if version <= 0 or remaining_budget <= 0:
            return QueryRequest(requested=False)
        updates: list[tuple[str, int, int]] = []
        if version not in self.rejected_versions and version != self.deployed:
            test = self._ensure_test(version)
            promotion_budget = (
                self.promotion_label_budget[version]
                if self.rollback_monitor
                else self.budget_by_version[version - 1]
            )
            promotion_used = self.issued_counts.get(("promotion", version), 0)
            if (
                not test.alarm
                and test.baseline == self.deployed
                and promotion_used < promotion_budget
            ):
                updates.append(("promotion", version, test.baseline))
        if self.rollback_monitor and self.deployed in self.rollback_tests:
            monitor = self.rollback_tests[self.deployed]
            rollback_used = self.issued_counts.get(("rollback", self.deployed), 0)
            if not monitor.alarm and rollback_used < self.rollback_label_budget[self.deployed]:
                updates.append(("rollback", self.deployed, monitor.baseline))
        active = [
            row
            for row in updates
            if int(event.model_predictions[row[2]]) != int(event.model_predictions[row[1]])
        ]
        if not active:
            return QueryRequest(requested=False)

        if self.rollback_monitor:
            # Per-test quotas sum to at most the global cap; a shared label may update multiple
            # eligible tests but is still charged once by the simulator.
            spendable = int(remaining_budget)
        else:
            allocation_through_version = int(self.budget_by_version[:version].sum())
            already_spent = sum(self.labels_by_version.values())
            spendable = min(int(remaining_budget), allocation_through_version - already_spent)
        if spendable <= 0:
            return QueryRequest(requested=False)
        self.issued[event.event_id] = updates
        for kind, tested, _ in updates:
            key = (kind, tested)
            self.issued_counts[key] = self.issued_counts.get(key, 0) + 1
        self.labels_by_version[version] = self.labels_by_version.get(version, 0) + 1
        return QueryRequest(
            requested=True,
            probability=1.0,
            extra={
                "challenger_version": version,
                "active_pairs": [(kind, tested, baseline) for kind, tested, baseline in updates],
            },
        )

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            pair = self.issued.pop(fb.event_id, None)
            if pair is None:
                continue
            for kind, version, baseline in pair:
                test = (self.tests if kind == "promotion" else self.rollback_tests)[version]
                if test.baseline != baseline:
                    raise RuntimeError("issue-time baseline changed inside a version test")
                gain = int(fb.model_losses[baseline]) - int(fb.model_losses[version])
                test.update(gain if kind == "promotion" else -gain)

    def decision_state(self) -> str:
        return f"deployed={self.deployed};version={self.current_version}"

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "current_version": self.current_version,
            "highest_version_seen": self.highest_version_seen,
            "config": {
                "max_versions": self.max_versions,
                "budget": self.B,
                "alpha": self.alpha,
                "lambdas": self.lambdas.tolist(),
                "version_weights": self.version_weights.tolist(),
                "rollback_monitor": self.rollback_monitor,
            },
            "version_weights": self.version_weights.tolist(),
            "tests": {
                v: {
                    "baseline": t.baseline,
                    "alpha": t.alpha,
                    "wealth": t.wealth.tolist(),
                    "n": t.n,
                    "alarm": t.alarm,
                }
                for v, t in self.tests.items()
            },
            "rollback_tests": {
                v: {
                    "baseline": t.baseline,
                    "alpha": t.alpha,
                    "wealth": t.wealth.tolist(),
                    "n": t.n,
                    "alarm": t.alarm,
                }
                for v, t in self.rollback_tests.items()
            },
            "issued": self.issued.copy(),
            "labels_by_version": self.labels_by_version.copy(),
            "issued_counts": {
                f"{kind}:{version}": count for (kind, version), count in self.issued_counts.items()
            },
            "promotions": list(self.promotions),
            "rollbacks": list(self.rollbacks),
            "rejected_versions": list(self.rejected_versions),
        }

    def load_state_dict(self, state: dict) -> None:
        expected_config = {
            "max_versions": self.max_versions,
            "budget": self.B,
            "alpha": self.alpha,
            "lambdas": self.lambdas.tolist(),
            "version_weights": self.version_weights.tolist(),
            "rollback_monitor": self.rollback_monitor,
        }
        if state.get("config") != expected_config:
            raise ValueError("checkpoint configuration does not match this policy instance")
        self.deployed = int(state["deployed"])
        self.current_version = int(state["current_version"])
        self.highest_version_seen = int(state["highest_version_seen"])
        self.tests = {}
        for v, saved in state["tests"].items():
            t = _VersionTest(int(saved["baseline"]), float(saved["alpha"]), self.lambdas.copy())
            t.wealth = np.asarray(saved["wealth"], dtype=float)
            t.n, t.alarm = int(saved["n"]), bool(saved["alarm"])
            self.tests[int(v)] = t
        self.rollback_tests = {}
        for v, saved in state.get("rollback_tests", {}).items():
            t = _VersionTest(int(saved["baseline"]), float(saved["alpha"]), self.lambdas.copy())
            t.wealth = np.asarray(saved["wealth"], dtype=float)
            t.n, t.alarm = int(saved["n"]), bool(saved["alarm"])
            self.rollback_tests[int(v)] = t
        self.issued = {int(k): [tuple(item) for item in v] for k, v in state["issued"].items()}
        self.labels_by_version = {int(k): int(v) for k, v in state["labels_by_version"].items()}
        self.issued_counts = {}
        for key, count in state.get("issued_counts", {}).items():
            kind, version = key.split(":", 1)
            self.issued_counts[(kind, int(version))] = int(count)
        self.promotions = [tuple(map(int, p)) for p in state["promotions"]]
        self.rollbacks = [tuple(map(int, p)) for p in state.get("rollbacks", [])]
        self.rejected_versions = set(map(int, state.get("rejected_versions", [])))


class VersionIndexedRollbackGate(VersionIndexedGate):
    """Version gate with alpha-split post-promotion evidence for rollback."""

    name = "version_indexed_gate_rollback"

    def __init__(self, max_versions: int, budget: int, alpha: float, **kwargs):
        super().__init__(max_versions, budget, alpha, rollback_monitor=True, **kwargs)


class VersionAwareModelPicker:
    """Model Picker adapter that does not credit a new version for pre-activation labels.

    At activation, the new version's cumulative loss estimate is initialized to the currently
    deployed model's estimate. Labels issued before activation are masked for that version even if
    they arrive later. This is an exploratory, non-certified comparison adapter.
    """

    name = "model_picker_version_reset"

    def __init__(self, max_versions: int, rng: np.random.Generator):
        self.max_versions = int(max_versions)
        self.core = ModelPickerDeploymentAdapter(max_versions + 1, 2, rng)
        self.active_version = 0

    def predict(self, event: Event) -> int:
        version = int(event.context or 0)
        if version > self.active_version:
            if version > self.max_versions:
                raise ValueError("activated version outside predeclared range")
            self.core.loss[version] = self.core.loss[self.core.deployed]
            self.active_version = version
        return self.core.predict(event)

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        req = self.core.request_labels(event, remaining_budget)
        if req.requested:
            extra = dict(req.extra)
            extra["active_version_at_issue"] = self.active_version
            return QueryRequest(True, req.probability, extra)
        return req

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        masked = []
        for fb in feedback:
            losses = np.asarray(fb.model_losses, dtype=np.int8).copy()
            issue_version = int(fb.extra.get("active_version_at_issue", 0))
            losses[issue_version + 1 :] = 0
            masked.append(
                ReleasedFeedback(
                    event_id=fb.event_id,
                    t_requested=fb.t_requested,
                    t_released=fb.t_released,
                    label=fb.label,
                    model_losses=losses,
                    query_probability=fb.query_probability,
                    extra=fb.extra,
                )
            )
        self.core.observe(masked)

    def decision_state(self) -> str:
        return f"deployed={self.core.deployed};version={self.active_version}"

    def state_dict(self) -> dict:
        return {
            "active_version": self.active_version,
            "core_loss": self.core.loss.copy(),
            "core_deployed": self.core.deployed,
            "core_n_observed": self.core.n_observed,
        }

    def load_state_dict(self, state: dict) -> None:
        self.active_version = int(state["active_version"])
        self.core.loss = np.asarray(state["core_loss"], dtype=float)
        self.core.deployed = int(state["core_deployed"])
        self.core.n_observed = int(state["core_n_observed"])
