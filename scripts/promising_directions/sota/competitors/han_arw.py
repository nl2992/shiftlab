"""Adaptive rolling window (ARW) model comparison (Han, Huang & Wang, ICML 2024), re-implemented
from the printed equations.

Source: E. Han, C. Huang, K. Wang, "Model Assessment and Selection under Temporal Distribution
Shift", ICML 2024, PMLR 235:17374-17392. Two versions of the same mathematics were read and the
numbering differs, so every citation carries a version label:

* ``[arXiv v2]`` = arXiv 2402.08672v2 (3 Jun 2024), equations (3.1)-(3.8), Algorithms 1-3,
  Theorem 3.1, Theorem 4.1.
* ``[PMLR]`` = camera-ready proceedings PDF, equations (1)-(8), Algorithms 1-3, Theorem 3.8,
  Theorem 4.2 (the two-model comparison bound).

Fidelity record: ``docs/sota_fidelity/{specs,checks}/han_rolling_window.md`` and the Han entry of
``docs/sota_fidelity/LEDGER.md``. The author repository (``eliselyhan/ARW@c48f830``) carries NO
licence, so nothing here is copied from it. It is a re-implementation from the paper only; the
repository's behaviour is used only as a reference for the differences listed below, never as
source text.

Tiers (see ``docs/sota_fidelity/README.md``)
--------------------------------------------
* **T2 audited mathematical port**, ``window_statistics`` / ``arw_window`` /
  ``pairwise_compare``: the window mean, variance, variance proxy, bias proxy, window argmin and
  the two-model comparison, each tied to a printed equation. Not validated numerically against
  the author code (no licence, and the harness does not execute it).
* **T3 common-contract adaptation**, ``HanARWDeploymentAdapter``: the paper's rule mapped onto the
  ShiftLab deployment contract (two frozen models, sparse paid delayed labels, hard budget,
  switching). It is NOT the authors' algorithm and must be reported as "label-clock ARW, common
  contract adapter (T3)", never as "Han et al.".

Line-to-equation map (T2 core)
------------------------------
* Window k = the k most recent periods; ``B_{t,k} = sum_{j=t-k+1}^{t} B_j``.
* ``mu_hat_{t,k}``: [arXiv v2] Eq. (3.1) in the summary-statistic form (3.7) / [PMLR] Eq. (1),(7).
* ``v_hat^2_{t,k}``: [arXiv v2] Eq. (3.2) in the summary form (3.8) / [PMLR] Eq. (2),(8):
  ``B/(B-1) * (B^{-1} sum_j B_j omega_j - mu^2)`` with ``omega_j`` the period's second moment.
* ``psi_hat``: [arXiv v2] Eq. (3.3) / [PMLR] Eq. (3): ``M`` if ``B_{t,k} = 1``, else
  ``v sqrt(2 log(2/d') / B) + 8 M log(2/d') / (3 (B-1))``.
* ``phi_hat``: [arXiv v2] Eq. (3.5) / [PMLR] Eq. (5), the Goldenshluger-Lepski style bias proxy
  ``max_{i in [k]} [ |mu_k - mu_i| - (psi_k + psi_i) ]_+``.
* ``arw_window``: [arXiv v2] / [PMLR] Algorithm 1, ``k_hat in argmin_k phi_hat + psi_hat``. The
  paper says "any" minimiser; this port returns the SMALLEST (most recent, first) minimiser, the
  same choice as the author code (spec item 33), within a float tolerance ``argmin_tol``.
* ``pairwise_compare``: [arXiv v2] / [PMLR] Algorithm 2 on ``u = l(f1) - l(f2)``: output ``f1``
  if ``Delta_hat <= 0`` else ``f2``. For two models the tournament (Algorithm 3, ``m-1`` matches)
  is exactly one match, so Algorithm 3 is not implemented separately.

Constant sets (a deviation question the paper leaves open, so both are named)
-----------------------------------------------------------------------------
* ``theory`` (default): ``M = b - a`` and ``d' = delta / (3 t)``, the setting under which
  [arXiv v2] Theorem 3.1 / [PMLR] Theorem 3.8 is stated (for ONE fixed ``t``).
* ``paper_experiments``: ``M = 0`` and ``d' = 0.1``, the setting of the paper's Section 5
  experiments ([arXiv v2] p.11). It lies outside the theorem: ``d' = 0.1`` corresponds to a
  nominal ``delta = 0.3 t``, which exceeds 1 for ``t >= 4`` (check item M2). Reported numbers
  under this set carry no stated probability guarantee.

Deviations from the paper (complete list)
-----------------------------------------
1. Tie rule. Algorithm 2 prints ``<= 0 -> f1``; the author code returns ``f1`` only if
   ``Delta_hat < 0``. Default here is the paper rule (``tie_rule="paper"``, incumbent on ties);
   ``tie_rule="code"`` reproduces the code. With 0/1 losses ties are common (check item M1).
2. Negative variance from round-off is clamped to 0 (the author synthetic code does, the housing
   copy does not; the paper is silent).
3. Window minimiser: first (smallest) k within ``argmin_tol=1e-12`` of the minimum; the paper
   allows any.
4. Numpy ``Generator`` only; no global RNG reseeding (the author tournament reseeds globally).
5. Periods must have ``B_j >= 1`` (Problem 3.1 of [arXiv v2] / Problem 3.2 of [PMLR]); the core
   raises on ``B_j = 0`` rather than producing NaN as the author code would.

T3 adapter contract and deviations
----------------------------------
* Label clock. ARW needs a labelled batch every period. Under sparse paid delayed labels the
  adapter defines one "period" per delivered label, ``B_j = 1`` (the bounded-drift case of
  [arXiv v2] Example 3.2), ordered by delivery. Windows are therefore counts of labels, not
  calendar windows, and are not comparable to the paper's window lengths. The alternative
  (fixed wall-clock bins with ``B_j`` = labels released in the bin, empty bins skipped) was NOT
  chosen: with a 100-round delay and 200 labels most bins would be empty and skipping them
  already changes "k most recent periods" semantics.
* Observation ``u = l_incumbent - l_candidate`` on the queried event (models 0 and 1), taken from
  ``ReleasedFeedback.model_losses`` exactly as delivered and in the order delivered. Delayed
  labels are therefore attributed to their delivery position, not the event time they describe:
  the estimand is the gap "as of the most recently delivered labels", which lags the true
  current gap by the unknown delay. [arXiv v2] Theorem 3.1 has no delay term.
* Acquisition: ARW has none. The adapter reuses the shared ``PacedDisagreementAcquisition`` (same
  pacer as the other controls), hard budget enforced by the simulator. So this pairs ARW's
  estimator with ShiftLab's acquisition. Because only disagreement events are queried,
  ``u in {-1,+1}`` and the estimand is the gap CONDITIONAL on disagreement, a positive multiple
  of the unconditional gap with the same sign; the decision uses only the sign. Query
  propensities vary with the pacer and are IGNORED by ARW (no inverse-propensity weighting, so
  the labelled gaps are not i.i.d. draws of the period distribution as the paper assumes).
* Decision: deploy the candidate iff ``Delta_hat_{k_hat} > margin`` (paper tie rule) or
  ``>= margin`` (code tie rule); otherwise the incumbent; before any label is delivered, the
  incumbent. The rule is memoryless in the deployed model, so it can roll back. ``margin``
  defaults to 0 because the paper has no switch margin or switching cost; it is an exposed
  extension, not part of the method. At ``switch_cost=5`` the unmodified rule switches on any
  positive point estimate.
* ``delta`` defaults to 0.05 only to give ``theory`` a ``d'``; no alpha-level test is performed.

NO FALSE-PROMOTION GUARANTEE. The paper proves an oracle inequality for estimating ``mu_t`` at
one fixed ``t`` under independent i.i.d. batches, bounded loss, full unselected feedback and no
delay. It has no null hypothesis, no Type I error control, no time-uniform statement, and no
coverage of delayed, selectively sampled or dependent feedback. Nothing in this module should be
read as a validity claim for the adapter.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback

CONSTANT_SETS = ("theory", "paper_experiments")
TIE_RULES = ("paper", "code")


# --------------------------------------------------------------------------------------------
# T2 core
# --------------------------------------------------------------------------------------------
def resolve_constants(
    constants: str, t: int, delta: float = 0.05, value_range: float = 2.0
) -> tuple[float, float]:
    """Return ``(M, d')`` for the named constant set at ``t`` periods.

    ``theory``: ``M = value_range = b - a`` (2 for a 0/1 loss gap), ``d' = delta / (3 t)``
    ([arXiv v2] Thm 3.1 / [PMLR] Thm 3.8). ``paper_experiments``: ``M = 0``, ``d' = 0.1``
    ([arXiv v2] Sec. 5, p.11)."""
    if constants == "theory":
        if not 0.0 < delta < 1.0:
            raise ValueError("delta must lie in (0, 1)")
        return float(value_range), float(delta) / (3.0 * max(int(t), 1))
    if constants == "paper_experiments":
        return 0.0, 0.1
    raise ValueError(f"constants must be one of {CONSTANT_SETS}, got {constants!r}")


def period_summaries(periods: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(B_j, mean_j, omega_j)`` for a list of per-period sample arrays, oldest first.

    ``omega_j`` is the within-period second moment used by [arXiv v2] Eq. (3.8)."""
    B = np.array([len(p) for p in periods], dtype=float)
    if (B < 1).any():
        raise ValueError("every period needs B_j >= 1 (Problem 3.1 / 3.2)")
    mean = np.array([np.mean(p) for p in periods], dtype=float)
    omega = np.array([np.mean(np.square(np.asarray(p, dtype=float))) for p in periods])
    return B, mean, omega


def window_statistics(
    B: np.ndarray, mean: np.ndarray, omega: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(B_{t,k}, mu_hat_{t,k}, v_hat_{t,k})`` for k = 1..t (index k-1), periods oldest first.

    Summary-statistic form: [arXiv v2] Eq. (3.7), (3.8) / [PMLR] Eq. (7), (8). Window k holds the
    k newest periods, so the sums run over the reversed arrays."""
    B = np.asarray(B, dtype=float)
    if (B < 1).any():
        raise ValueError("every period needs B_j >= 1 (Problem 3.1 / 3.2)")
    Bk = np.cumsum(B[::-1])
    s1 = np.cumsum((B * mean)[::-1])
    s2 = np.cumsum((B * omega)[::-1])
    mu = s1 / Bk
    denom = np.where(Bk > 1.0, Bk - 1.0, 1.0)
    var = np.where(Bk > 1.0, Bk / denom * (s2 / Bk - mu**2), 0.0)
    return Bk, mu, np.sqrt(np.maximum(var, 0.0))  # deviation 2: clamp round-off negatives


def variance_proxy(Bk: np.ndarray, v: np.ndarray, M: float, d_prime: float) -> np.ndarray:
    """``psi_hat`` of [arXiv v2] Eq. (3.3) / [PMLR] Eq. (3)."""
    L = math.log(2.0 / d_prime)
    denom = np.where(Bk > 1.0, Bk - 1.0, 1.0)
    full = v * np.sqrt(2.0 * L / Bk) + 8.0 * M * L / (3.0 * denom)
    return np.where(Bk <= 1.0, float(M), full)


def bias_proxy(mu: np.ndarray, psi: np.ndarray) -> np.ndarray:
    """``phi_hat`` of [arXiv v2] Eq. (3.5) / [PMLR] Eq. (5), for every k at once."""
    D = np.abs(mu[:, None] - mu[None, :]) - (psi[:, None] + psi[None, :])
    mask = np.tril(np.ones_like(D, dtype=bool))  # i <= k
    return np.maximum(np.where(mask, D, -np.inf).max(axis=1), 0.0)


@dataclass(frozen=True)
class ArwResult:
    k_hat: int  # selected window length in periods (1-based)
    mu_hat: float  # window mean at k_hat
    M: float
    d_prime: float
    B: np.ndarray  # B_{t,k}, k = 1..t
    mu: np.ndarray
    psi: np.ndarray
    phi: np.ndarray


def arw_window(
    B: np.ndarray,
    mean: np.ndarray,
    omega: np.ndarray,
    *,
    M: float,
    d_prime: float,
    argmin_tol: float = 1e-12,
) -> ArwResult:
    """Algorithm 1 ([arXiv v2] / [PMLR]): ``k_hat in argmin_k phi_hat + psi_hat``; smallest
    minimiser within ``argmin_tol`` (deviation 3)."""
    Bk, mu, v = window_statistics(B, mean, omega)
    psi = variance_proxy(Bk, v, M, d_prime)
    phi = bias_proxy(mu, psi)
    crit = phi + psi
    k_idx = int(np.flatnonzero(crit <= crit.min() + argmin_tol)[0])
    return ArwResult(k_idx + 1, float(mu[k_idx]), M, d_prime, Bk, mu, psi, phi)


def arw_window_from_samples(
    u: np.ndarray,
    *,
    constants: str = "theory",
    delta: float = 0.05,
    value_range: float = 2.0,
    argmin_tol: float = 1e-12,
) -> ArwResult:
    """ARW with one sample per period (``B_j = 1``), ``u`` ordered oldest to newest."""
    u = np.asarray(u, dtype=float)
    if u.size == 0:
        raise ValueError("need at least one observation")
    M, dp = resolve_constants(constants, u.size, delta, value_range)
    return arw_window(np.ones(u.size), u, u**2, M=M, d_prime=dp, argmin_tol=argmin_tol)


def pairwise_compare(
    u: np.ndarray,
    *,
    constants: str = "theory",
    delta: float = 0.05,
    value_range: float = 2.0,
    tie_rule: str = "paper",
    margin: float = 0.0,
) -> tuple[int, float, ArwResult]:
    """Algorithm 2 for ``u = l(f1) - l(f2)`` (one sample per period). Returns
    ``(selected, Delta_hat, details)`` with ``selected`` 0 for ``f1`` and 1 for ``f2``.

    ``tie_rule="paper"``: ``f1`` iff ``Delta_hat <= margin`` (Alg. 2 at ``margin = 0``).
    ``tie_rule="code"``: ``f1`` iff ``Delta_hat < margin`` (the author code's rule at 0).
    ``margin`` is an extension (the paper has none)."""
    if tie_rule not in TIE_RULES:
        raise ValueError(f"tie_rule must be one of {TIE_RULES}")
    res = arw_window_from_samples(u, constants=constants, delta=delta, value_range=value_range)
    d = res.mu_hat
    cand = d > margin if tie_rule == "paper" else d >= margin
    return int(cand), d, res


# --------------------------------------------------------------------------------------------
# T3 adapter
# --------------------------------------------------------------------------------------------
class HanARWDeploymentAdapter:
    """Label-clock ARW, common-contract adapter (T3). See the module docstring for the list of
    deviations; this is not the authors' algorithm and carries no false-promotion guarantee."""

    def __init__(
        self,
        horizon: int,
        budget: int,
        *,
        rng: np.random.Generator,
        constants: str = "theory",
        delta: float = 0.05,
        tie_rule: str = "paper",
        margin: float = 0.0,
        name: str = "han_arw_label_clock",
    ):
        if constants not in CONSTANT_SETS:
            raise ValueError(f"constants must be one of {CONSTANT_SETS}")
        if tie_rule not in TIE_RULES:
            raise ValueError(f"tie_rule must be one of {TIE_RULES}")
        self.name = name
        self.rng = rng
        self.constants, self.delta = constants, float(delta)
        self.tie_rule, self.margin = tie_rule, float(margin)
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.u: list[float] = []  # delivered paired gaps, delivery order
        self.deployed = 0
        self.k_hat = 0
        self.delta_hat = 0.0
        self._dirty = False

    def _refresh(self) -> None:
        if not self._dirty:
            return
        sel, d, res = pairwise_compare(
            np.array(self.u), constants=self.constants, delta=self.delta,
            tie_rule=self.tie_rule, margin=self.margin,
        )
        self.deployed, self.delta_hat, self.k_hat = sel, d, res.k_hat
        self._dirty = False

    def predict(self, event: Event) -> int:
        self._refresh()
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            # float, not int: real-data streams can carry non-0/1 bounded losses.
            self.u.append(float(fb.model_losses[0]) - float(fb.model_losses[1]))
            self._dirty = True

    def decision_state(self) -> str:
        self._refresh()
        return f"n={len(self.u)};k={self.k_hat};d={self.delta_hat:.3f};dep={self.deployed}"

    def state_dict(self) -> dict:
        return {"u": list(self.u), "deployed": self.deployed, "n_dis": self.acq.n_disagree}

    def load_state_dict(self, s: dict) -> None:
        self.u = [float(x) for x in s["u"]]
        self.deployed, self.acq.n_disagree = int(s["deployed"]), int(s["n_dis"])
        self._dirty = bool(self.u)
        self._refresh()
