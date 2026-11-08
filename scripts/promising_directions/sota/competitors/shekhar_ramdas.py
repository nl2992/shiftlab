"""Shekhar & Ramdas RCS-Detector (repeated confidence sequences), T2 native core + T3 adapter.

Source
------
Shubhanshu Shekhar and Aaditya Ramdas, "Reducing sequential change detection to sequential
estimation", ICML 2024 (PMLR 235:44628-44642). Version read: PMLR camera-ready PDF (15 pages),
cross-read against arXiv:2309.09111v2. Page numbers below are PMLR pages ("P"). Official code:
``sshekhar17/SCDtoCS`` commit ``c3a7eceaf9fa8e2756105c233a791592916c57d1``. The code was READ, NOT
PORTED and not executed: it departs from the printed CS (see deviations), so a line-by-line port
would reproduce the code, not the paper. Provenance: ``docs/sota_fidelity/specs/`` and
``docs/sota_fidelity/checks/shekhar_ramdas_cs_change_detection.md`` (the check overrides the spec).

Tiers
-----
* ``HoeffdingCS`` and ``RCSDetector``: **T2, audited mathematical port** of Definition 2.1 and the
  Appendix C Hoeffding CS as printed. No author-native claim (T1) is available.
* ``ShekharRamdasDeploymentAdapter``: **T3, common-contract adaptation**. It is NOT the authors'
  algorithm; table name "Shekhar-Ramdas RCS, common-contract adapter (T3)".

Line-by-line trace
------------------
* Hoeffding CS (Section 2.4, P6 main text; Appendix C, P14): midpoint
  ``sum_i lam_i X_i / sum_i lam_i``, half-width ``(log(2/alpha) + sum_i lam_i^2 / 8) / sum_i lam_i``
  (``lam_i`` deterministic; validity is the Ville argument for a sub-Gaussian proxy 1/8 martingale).
  ``schedule="main"``: ``lam_i = min(1, sqrt(8 log(2/alpha) / (i log(i+1))))`` (P6, default);
  ``schedule="appendix"``: ``lam_i = min(1, sqrt(8 log(2/alpha) / (i (i+1))))`` (P14). The two
  printed schedules disagree; both carry the printed ``min(., 1)`` cap (check item 12).
* Remark 1.5 (P2): nested CS by running intersection; implemented as running max of lower and
  running min of upper endpoint. Intervals are also intersected with [0, 1] (bounded-mean setting).
* Definition 2.1 (P3): ``C^(m)`` is started at ``m`` and uses ``X_m, X_{m+1}, ...`` (the CS started at
  ``n`` includes ``X_n``); stop at the first ``n`` where ``cap_{m=0..n} C^(m)_n`` is empty, with
  ``C^(0) = Theta`` (Problem 1.1, non-partitioned, ``theta0=(0, 1)``) or ``Theta0`` (Problem 1.2,
  partitioned, ``theta0=(a, b)``, an interval). Non-nested form (P3 last paragraph) is covered by
  the running intersection of each CS. This is joint emptiness, not "any CS excludes Theta0"
  (check item 8); for singleton Theta0 the two coincide, which is Proposition 3.1 (Lorden form, P6),
  tested.
* ``level="constant"``: every CS at ``1 - alpha`` (paper default; Theorem 2.4, ARL >= 1/alpha, which
  is a mean-run-length statement and no finite-horizon false-alarm bound; the derived union bound
  is ``P(tau <= N) <= N alpha``, check item 20). ``level="spending"``: Remark 2.5 (P4), the CS
  started at ``n`` has level ``1 - 6 alpha / (pi^2 n^2)``; ``P_inf(tau < inf) <= alpha``.
* ``window``: Remark 2.3 (P3) suggests keeping only the ``w`` most recent CSs, no ``w`` chosen. Here
  ``window=None`` (all CSs) by default. ARL/PFA validity is preserved (fewer intersected CSs stop
  later, P8-9); delay guarantees are not claimed.

Deviations from the paper (native core, T2)
-------------------------------------------
1. Schedule choice: the paper prints two schedules; ``main`` is default, ``appendix`` selectable.
2. The paper's Figure 1 uses a width shrunk by an unstated factor < 1 and checks stopping every 10 or
   20 steps (Appendix C heuristics, P14). NOT reproduced: widths here are the guaranteed ones and the
   stop is checked every observation.
3. Only the Hoeffding CS. Betting and empirical-Bernstein RCS are not implemented (bet schedule
   unspecified in the paper; check item 31).
4. Differences from the official code (documented, not ported): code skips the first observation of
   each new CS, starts from an initial pseudo-weight ``sum lam = 1`` at value 0, does not apply the
   ``min(., 1)`` cap, and defaults to a window of 500. The T2 core has none of these.

Deviations of the T3 contract adapter
-------------------------------------
* Label clock: stream index ``n`` is the order labels are DELIVERED by the simulator (``observe``),
  not event time. Delay is honoured exactly; the paper's "no delay, every X_n observed" setting is
  replaced. Event-time change points map to label-clock change points only approximately.
* Rescale: simulator losses are 0/1 so ``D = l_challenger - l_incumbent`` lies in {-1, 0, 1} (model
  index 0 = incumbent, 1 = challenger); ``Y = (D + 1)/2`` lies in [0, 1] (verified in
  ``simulator.run_episode``: ``loss = float(pred != label)``). Under the shared acquisition below only
  disagreement events are queried, where exactly one model is wrong (two-class streams) and
  ``Y in {0, 1}``.
* Acquisition: the shared ``PacedDisagreementAcquisition`` (``controls.py``) under the simulator's
  hard budget, identical to the other certificate and control adapters. It is not part of the paper.
* Promotion: partitioned RCS (Problem 1.2) with ``Theta0 = {E[Y] >= 1/2}`` (challenger not better,
  i.e. ``E[D] >= 0``) as the interval ``[1/2, 1]``; promote when the intersection of all CSs with
  ``Theta0`` is empty. Rollback: after promotion a FRESH partitioned RCS on labels delivered after the
  promotion with deployed-minus-previous orientation, ``Theta0 = {E[Y] <= 1/2}`` (deployed not
  worse), interval ``[0, 1/2]``; roll back on detection. After rollback the adapter stays on the
  incumbent (``rearm=False`` default); ``rearm=True`` restarts promotion and then the error rates of
  separate arms add up across cycles (no combined guarantee is claimed).
* Level: ``alpha`` from the contract with Remark 2.5 spending for each arm. The promotion and the
  rollback arm are separate tests with separate nulls; neither bound is a bound on the other.
* The Remark 2.5 delay claim ("logarithmic in T") is unproven in the paper and unused here; the
  delay bounds of Theorem 2.7 and Proposition 2.10 are vacuous at B=200 (check item 33). Delay is
  measured, never claimed.
* No cost awareness: switching cost ``cs`` and query price ``cq`` do not enter the decision.

ShiftLab deviation ``stop_rule="any_excludes"`` (RCSDetector and adapter)
-----------------------------------------------------------------------
Definition 2.1's joint rule is proved for Problem 1.2 where pre-change data are i.i.d. with theta0
in Theta0. ShiftLab's null is composite and non-stationary: conditional means may drift WITHIN
Theta0 (e.g. Y-mean 0.85 for 100 labels, then 0.55, both in [1/2, 1]). Each CS covers its own
running average, all >= 1/2, yet two CSs can be disjoint from each other while both lie inside
Theta0, so the joint rule can fire falsely. ``any_excludes`` stops only when one CS is disjoint from
Theta0; under the composite conditional-mean null each CS (started at m, level 1 - 6 alpha/(pi^2 m^2)
under ``level="spending"``) contains its own average, which lies in Theta0, so a union bound over
Remark 2.5 levels gives false-alarm probability <= alpha. The check uses each CS's instantaneous
interval (not its running intersection, Remark 1.5, which presumes a constant theta). Relation to Proposition 3.1 (Lorden form,
P6): for singleton Theta0 the two rules coincide (and the test checks it); for an interval Theta0
``any_excludes`` is the "Theta0 cap C_n empty per CS" rule of Remark 3.2, which the paper does not
analyse jointly. Every ``any_excludes`` alarm is also a ``joint`` alarm (a CS disjoint from Theta0 empties the
intersection), since running intersections only shrink the instantaneous intervals. Adapter names: ``shekhar_ramdas_rcs_t3`` (joint, default) and
``shekhar_ramdas_rcs_t3_anyexcl`` (``stop_rule="any_excludes"``).

Null validity and the label-order filtration (what the adapter does NOT inherit)
-------------------------------------------------------------------------------
The filtration is the label-delivery order. Theorem 2.4 and Remark 2.5 need each CS to be a valid
time-uniform CS for the same ``theta0`` under the null in THAT filtration. The Hoeffding CS is valid
for bounded observations whose conditional mean (given the label-order past) lies in Theta0. This
holds here only when the query decision is history-independent on the labelled subsequence, i.e.
selection does not depend on the labelled outcomes or on a property correlated with them beyond the
queried event itself, and the labelled signs are independent (or martingale-difference) given the
past. The pacer uses only predictions and past query counts, never labels, so selection is
label-independent, but:
* Disagreement-only querying changes the estimand: ``Y`` is observed only on disagreements, so the
  tested mean is the DISAGREEMENT-CONDITIONAL mean ``E[Y | disagree]``, not the all-event mean
  ``E[(D+1)/2]``. Its sign relative to 1/2 equals the sign of the overall expected gain, so the null
  "challenger not better" is the same, but the magnitude is a different quantity. Agreement events
  carry ``D = 0`` and are not used. (The other certificate adapters use IPW over all events instead.)
* The query probability depends on the paced budget history; it is predictable with respect to the
  past, and no weights are applied. Serially dependent outcome signs (Markov persistence in the
  Atlas regimes with ``rho > 0``) break independence; no theorem covers that, and the null validity
  statement is not claimed there.
* Out-of-order or selectively delayed delivery would change the label order; with the simulator's
  constant delay the delivery order equals the request order.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_SOTA = Path(__file__).resolve().parents[1]
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback

_SCHEDULES = ("main", "appendix")
_LEVELS = ("constant", "spending")
_STOP_RULES = ("joint", "any_excludes")


def hoeffding_lambda(i: int, alpha: float, schedule: str = "main") -> float:
    """Printed bet weight for the i-th observation (i >= 1), capped at 1 (P6 / P14)."""
    if i < 1:
        raise ValueError("i must be >= 1")
    if schedule == "main":
        denom = i * math.log(i + 1.0)
    elif schedule == "appendix":
        denom = i * (i + 1.0)
    else:
        raise ValueError(f"schedule must be one of {_SCHEDULES}")
    return min(1.0, math.sqrt(8.0 * math.log(2.0 / alpha) / denom))


def spending_alpha(alpha: float, n: int) -> float:
    """Remark 2.5: error budget ``6 alpha / (pi^2 n^2)`` of the CS started at ``n`` (n >= 1)."""
    return 6.0 * alpha / (math.pi**2 * n * n)


class HoeffdingCS:
    """Appendix C Hoeffding confidence sequence for the mean of [0, 1]-valued data.

    ``update(x)`` consumes the next observation (the first call uses X_n of a CS started at n;
    nothing is skipped and there is no pseudo-weight) and returns the running-intersected interval
    ``(lo, hi)`` clipped to [0, 1] (Remark 1.5). ``lo > hi`` means the CS is empty.
    """

    def __init__(self, alpha: float, schedule: str = "main"):
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        if schedule not in _SCHEDULES:
            raise ValueError(f"schedule must be one of {_SCHEDULES}")
        self.alpha, self.schedule = float(alpha), schedule
        self.n = 0
        self.sum_lam = 0.0
        self.sum_lam_x = 0.0
        self.sum_lam_sq = 0.0
        self.lo, self.hi = 0.0, 1.0
        self.mid = float("nan")
        self.half_width = float("inf")

    def update(self, x: float) -> tuple[float, float]:
        if not 0.0 <= x <= 1.0:
            raise ValueError("observations must lie in [0, 1]")
        self.n += 1
        lam = hoeffding_lambda(self.n, self.alpha, self.schedule)
        self.sum_lam += lam
        self.sum_lam_x += lam * x
        self.sum_lam_sq += lam * lam
        self.mid = self.sum_lam_x / self.sum_lam
        self.half_width = (math.log(2.0 / self.alpha) + self.sum_lam_sq / 8.0) / self.sum_lam
        self.lo = max(self.lo, self.mid - self.half_width)
        self.hi = min(self.hi, self.mid + self.half_width)
        return self.lo, self.hi


class RCSDetector:
    """Definition 2.1 with Hoeffding CSs (T2).

    One CS per start time ``m = 1, 2, ...``; ``C^(0)`` is the interval ``theta0`` (``(0, 1)`` for
    the non-partitioned Problem 1.1, the known interval Theta0 for the partitioned Problem 1.2).
    ``stop_rule="joint"`` (default): Definition 2.1, detection at the first ``n`` where the
    intersection of ``theta0`` and every active CS is empty. ``stop_rule="any_excludes"``: SHIFTLAB
    DEVIATION, detection when some single active CS is disjoint from ``theta0`` (see module docstring).
    State is held in arrays so the O(n) per-step update is vectorised; ``HoeffdingCS`` is the scalar
    reference and the tests check that CS ``m`` here equals ``HoeffdingCS`` started at ``m``.
    """

    def __init__(
        self,
        alpha: float,
        *,
        theta0: tuple[float, float] = (0.0, 1.0),
        level: str = "constant",
        schedule: str = "main",
        window: int | None = None,
        stop_rule: str = "joint",
    ):
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        if stop_rule not in _STOP_RULES:
            raise ValueError(f"stop_rule must be one of {_STOP_RULES}")
        if level not in _LEVELS:
            raise ValueError(f"level must be one of {_LEVELS}")
        if schedule not in _SCHEDULES:
            raise ValueError(f"schedule must be one of {_SCHEDULES}")
        if not 0.0 <= theta0[0] <= theta0[1] <= 1.0:
            raise ValueError("theta0 must be an interval inside [0, 1]")
        if window is not None and window < 1:
            raise ValueError("window must be >= 1 or None")
        self.alpha, self.level, self.schedule = float(alpha), level, schedule
        self.theta0 = (float(theta0[0]), float(theta0[1]))
        self.window = window
        self.stop_rule = stop_rule
        self.n = 0
        self.tau: int | None = None
        self._cap = 64
        self._alloc(self._cap)

    def _alloc(self, cap: int) -> None:
        self._a = np.zeros(cap)  # per-CS alpha
        self._log2a = np.zeros(cap)
        self._s = np.zeros(cap)  # sum lam
        self._sx = np.zeros(cap)  # sum lam x
        self._s2 = np.zeros(cap)  # sum lam^2
        self._lo = np.zeros(cap)
        self._hi = np.ones(cap)
        self._clo = np.zeros(cap)  # instantaneous (not running-intersected) interval
        self._chi = np.ones(cap)

    def _grow(self) -> None:
        old = (
            self._a,
            self._log2a,
            self._s,
            self._sx,
            self._s2,
            self._lo,
            self._hi,
            self._clo,
            self._chi,
        )
        self._cap *= 2
        self._alloc(self._cap)
        for new, o in zip(
            (
                self._a,
                self._log2a,
                self._s,
                self._sx,
                self._s2,
                self._lo,
                self._hi,
                self._clo,
                self._chi,
            ),
            old,
            strict=True,
        ):
            new[: len(o)] = o

    def _cs_alpha(self, m: int) -> float:
        return spending_alpha(self.alpha, m) if self.level == "spending" else self.alpha

    @property
    def active(self) -> slice:
        first = 0 if self.window is None else max(0, self.n - self.window)
        return slice(first, self.n)

    def update(self, x: float) -> bool:
        """Feed X_n; return True iff the detector has stopped (at this or an earlier step)."""
        if not 0.0 <= x <= 1.0:
            raise ValueError("observations must lie in [0, 1]")
        if self.n >= self._cap:
            self._grow()
        m = self.n + 1  # start index of the CS initialised now, 1-based as in Definition 2.1
        self._a[self.n] = self._cs_alpha(m)
        self._log2a[self.n] = math.log(2.0 / self._a[self.n])
        self._s[self.n] = self._sx[self.n] = self._s2[self.n] = 0.0
        self._lo[self.n], self._hi[self.n] = 0.0, 1.0
        self._clo[self.n], self._chi[self.n] = 0.0, 1.0
        self.n = m
        sl = self.active
        k = np.arange(self.n - sl.start, 0, -1, dtype=float)  # observations seen by CS: n-m+1
        if self.schedule == "main":
            denom = k * np.log(k + 1.0)
        else:
            denom = k * (k + 1.0)
        lam = np.minimum(1.0, np.sqrt(8.0 * self._log2a[sl] / denom))
        self._s[sl] += lam
        self._sx[sl] += lam * x
        self._s2[sl] += lam * lam
        mid = self._sx[sl] / self._s[sl]
        hw = (self._log2a[sl] + self._s2[sl] / 8.0) / self._s[sl]
        self._clo[sl], self._chi[sl] = mid - hw, mid + hw
        self._lo[sl] = np.maximum(self._lo[sl], mid - hw)
        self._hi[sl] = np.minimum(self._hi[sl], mid + hw)
        if self.tau is None and self._stop_now():
            self.tau = self.n
        return self.tau is not None

    def _stop_now(self) -> bool:
        if self.stop_rule == "joint":
            lo, hi = self.interval
            return lo > hi
        # any_excludes: some single CS is disjoint from theta0 at the current time. The INSTANTANEOUS
        # interval is used, not the running intersection: under drifting conditional means a CS covers
        # the lambda-weighted average of the means at each time (inside Theta0 by convexity), but a
        # running intersection over time would not (early narrow lower bounds survive a later drift).
        sl = self.active
        a, b = self.theta0
        return bool(np.any((self._clo[sl] > b) | (self._chi[sl] < a)))

    @property
    def interval(self) -> tuple[float, float]:
        """Intersection of theta0 and all active running-intersected CSs (empty iff lo > hi)."""
        sl = self.active
        lo = max(self.theta0[0], float(self._lo[sl].max())) if self.n else self.theta0[0]
        hi = min(self.theta0[1], float(self._hi[sl].min())) if self.n else self.theta0[1]
        return lo, hi

    def cs_interval(self, m: int) -> tuple[float, float]:
        """Running-intersected interval of the CS started at ``m`` (1-based), for tests."""
        return float(self._lo[m - 1]), float(self._hi[m - 1])

    def state_dict(self) -> dict:
        n = self.n
        return {
            "n": n,
            "tau": self.tau,
            "a": self._a[:n].tolist(),
            "log2a": self._log2a[:n].tolist(),
            "s": self._s[:n].tolist(),
            "sx": self._sx[:n].tolist(),
            "s2": self._s2[:n].tolist(),
            "lo": self._lo[:n].tolist(),
            "hi": self._hi[:n].tolist(),
            "clo": self._clo[:n].tolist(),
            "chi": self._chi[:n].tolist(),
        }

    def load_state_dict(self, st: dict) -> None:
        n = int(st["n"])
        self._cap = max(64, 1 << max(0, n - 1).bit_length())
        self._alloc(self._cap)
        for name, key in (
            ("_a", "a"),
            ("_log2a", "log2a"),
            ("_s", "s"),
            ("_sx", "sx"),
            ("_s2", "s2"),
            ("_lo", "lo"),
            ("_hi", "hi"),
            ("_clo", "clo"),
            ("_chi", "chi"),
        ):
            getattr(self, name)[:n] = np.asarray(st[key], dtype=float)
        self.n = n
        self.tau = None if st["tau"] is None else int(st["tau"])


class ShekharRamdasDeploymentAdapter:
    """T3 common-contract adapter: partitioned RCS promotion trigger and rollback trigger.

    Model 0 is the incumbent (deployed first), model 1 the challenger. See the module docstring for
    every deviation and for the scope of null validity.
    """

    def __init__(
        self,
        horizon: int,
        budget: int,
        alpha: float,
        *,
        rng: np.random.Generator,
        level: str = "spending",
        schedule: str = "main",
        window: int | None = None,
        p_min: float = 0.05,
        rearm: bool = False,
        stop_rule: str = "joint",
        name: str = "shekhar_ramdas_rcs_t3",
    ):
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        self.name = name
        self.alpha, self.level, self.schedule, self.window = alpha, level, schedule, window
        self.rearm = bool(rearm)
        self.stop_rule = stop_rule
        self.rng = rng
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.deployed = 0
        self.phase = "promotion"  # "promotion" -> "rollback" -> "done" (or back, if rearm)
        self.promoted_at_label = -1
        self.rolled_back_at_label = -1
        self.n_labels = 0
        self.rcs = self._new_rcs()

    # Theta0 as interval on Y: promotion {E[Y] >= 1/2}; rollback {E[Y] <= 1/2}.
    def _new_rcs(self) -> RCSDetector:
        theta0 = (0.5, 1.0) if self.phase == "promotion" else (0.0, 0.5)
        return RCSDetector(
            self.alpha,
            theta0=theta0,
            level=self.level,
            schedule=self.schedule,
            window=self.window,
            stop_rule=self.stop_rule,
        )

    # ---- Policy protocol
    def predict(self, event: Event) -> int:
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        # Delivery order is the label clock; never reordered.
        for fb in feedback:
            if self.phase == "done":
                break
            d = float(fb.model_losses[1]) - float(fb.model_losses[0])  # challenger - incumbent
            y = (d + 1.0) / 2.0  # promotion and rollback share the orientation (see below)
            self.n_labels += 1
            # Rollback orientation: deployed(challenger) - previous(incumbent) = the same D, with
            # Theta0 = {E[Y] <= 1/2}; detection means the deployed model is worse.
            if self.rcs.update(y):
                self._fire()

    def _fire(self) -> None:
        if self.phase == "promotion":
            self.deployed = 1
            self.promoted_at_label = self.n_labels
            self.phase = "rollback"
        else:
            self.deployed = 0
            self.rolled_back_at_label = self.n_labels
            self.phase = "promotion" if self.rearm else "done"
        self.rcs = self._new_rcs()

    def decision_state(self) -> str:
        return f"{self.phase};n={self.rcs.n};dep={self.deployed}"

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "phase": self.phase,
            "n_labels": self.n_labels,
            "promoted_at_label": self.promoted_at_label,
            "rolled_back_at_label": self.rolled_back_at_label,
            "n_dis": self.acq.n_disagree,
            "rcs": self.rcs.state_dict(),
            "rng": self.rng.bit_generator.state,
        }

    def load_state_dict(self, s: dict) -> None:
        self.deployed, self.phase = int(s["deployed"]), str(s["phase"])
        self.n_labels = int(s["n_labels"])
        self.promoted_at_label = int(s["promoted_at_label"])
        self.rolled_back_at_label = int(s["rolled_back_at_label"])
        self.acq.n_disagree = int(s["n_dis"])
        self.rcs = self._new_rcs()
        self.rcs.load_state_dict(s["rcs"])
        self.rng.bit_generator.state = s["rng"]
