"""Shin-Ramdas-Rinaldo e-detectors (bounded-mean e-SR / e-CUSUM), T2 native core + T3 adapter.

Source
------
Jaehyeok Shin, Aaditya Ramdas, Alessandro Rinaldo, "E-detectors: A Nonparametric Framework for
Sequential Change Detection", NEJSDS 2 (2024) 229-260 = arXiv:2203.03532v4. Equation numbers are
given as ``NEJSDS (arXiv v4)``; Sec 2 maps v4 (n) -> NEJSDS (2.n-5), Sec 3 (3.n-19), Appendix B
(94)-(96) -> (B.10)-(B.12). Official code (READ, never executed here): ``shinjaehyeok/stcp@c9ff9a6``
(``build_stcp_bounded``, ``generate_log_bounded_base_fn``, ``update_log_e``), ``stcpR6@9eaafb4``.
Decision record: ``docs/sota_fidelity/LEDGER.md`` (Shin entry); the check overrides the spec:
``docs/sota_fidelity/checks/shin_edetectors.md``.

Tiers
-----
* ``algorithm3_grid``, ``BoundedMeanEDetector``, ``two_sided_bounded_grid``: **T2, audited
  mathematical port** from the printed equations and algorithm boxes, with one numerical
  reproduction (NBA Cavaliers Plus-Minus example, ``tests/sota_fidelity/test_shin_esr.py``).
  Not T1: the R code was not run and no line-by-line numerical port against it was validated.
* ``TwoSidedESRDeploymentAdapter``: **T3, common-contract adaptation**. NOT the authors' algorithm;
  table name "two-sided e-SR, label clock, common-contract adapter (T3)".

Line-by-line trace (T2 core)
----------------------------
* Increment, eq (70) = (5.6): ``L^lambda_n = 1 + lambda (X_n/m - 1)`` for X_n in [0, 1] and pre-change
  ``E[X_n | F_{n-1}] <= m``, ``lambda in (0, 1)``. ``BoundedMeanEDetector._log_increment``.
  The official code (stcp ``generate_log_bounded_base_fn``, stcpR6 ``baseline_increment.h``) runs THIS
  increment, while the lambda grid and weights are built from the eq (72) = (5.8) surrogate
  (``psi*_E(u) = u - log(1+u)``). The checker's independent reproduction shows eq (70) is the one
  that reproduces the paper's NBA alarm (game 378); eq (72) as the increment gives game 427. This
  port follows the code (and therefore the paper's figure), not the paper's prose.
* Grid, Algorithm 3 = App. B.1 eqs (94)-(96) = (B.10)-(B.12): ``algorithm3_grid`` below. With the
  sub-exponential ``psi_E``: ``lambda = grad psi*(Delta) = Delta / (1 + Delta)``,
  ``psi*(u) = u - log(1+u)``, ``v_min = 0`` (stcp; stcpR6 uses ``v_min = 1`` and drops the
  ``lambda_U`` atom: NOT followed).
    - (94): ``g_alpha = inf{g > log(1/alpha): e^{-g} 1(g > v_min D_U) + min_{k<=Kmax} k exp(-g (D_U/D_L)^{-1/k}) <= alpha}``,
      ``D_L = psi*(Delta_L)``, ``D_U = psi*(Delta_U)``; solved by bisection (Algorithm 4, App. C).
    - (95): ``K_alpha = argmin_k k exp(-g_alpha (D_U/D_L)^{-1/k})``, ``eta = (D_U/D_L)^{1/K_alpha}``.
    - lambda points: ``lambda_U`` (atom), interior ``psi*(Delta_k) = D_U eta^{-k}`` for ``k = 1..K-1``,
      ``lambda_L`` (k = K). Weights (96): atom ``e^{-g}`` (only if ``g > v_min D_U``), each of the K
      others ``e^{-g/eta}``, normalised by ``W``.
    - Component count = ``K_alpha`` + atom. The paper's "190 baselines" is K=189 plus the atom
      (the checker found the same counting).
* Recursions (13),(14) = (2.8),(2.9): ``M^SR_n = L_n (M^SR_{n-1} + 1)``,
  ``M^CU_n = L_n max(M^CU_{n-1}, 1)``, initialised at ``M_0 = 0`` (log-space ``-inf``). The paper's
  sentence "M_0^mSR = M_0^mCU := 1" before (3.5)/(3.6) is a typo (contradicts (3.8),(3.9) and
  Algorithm 1 line 4); ``M_0 = 1`` would violate Def 2.2 at tau = 0. NOT followed.
* Mixtures, (24)-(28) = (3.5)-(3.9): ``M^mSR_n = sum_k w_k M^SR_n(k)`` and the same for CUSUM, i.e. a
  mixture of per-lambda detectors (never a max over lambda, Remark 3.1).
* Remark 2.7 (NEJSDS p234; stated WITHOUT proof in the paper, proof in the check file): start weights
  ``pi_s`` with ``sum pi_s <= 1`` give ``sup_P P(tau < inf) <= alpha`` at threshold ``1/alpha``. The
  recursion is ``S_n = L_n (S_{n-1} + pi_n)`` and ``M_n = sum_k w_k S_n(k)``. ``start_weight=1.0``
  recovers Def 2.6 (unit mass, ARL form, Theorem 2.4). ``max_starts`` caps the number of starts.
* Alarm: ``M_n >= 1/alpha`` (paper (7) / Theorem 2.4, ``>=``); the R code uses strict ``>``.
* e-CUSUM: Def 2.6 with the same grid; unit start mass only (Remark 2.7 is for SR).
* Two-sided (stcpR6 ``two.sided``, NOT in the paper): ``two_sided_bounded_grid`` concatenates the
  ``greater`` grid and the ``less`` grid (both built at alpha/2), halves every weight, and sends the
  ``less`` bets to ``-m lambda/(1-m)`` (algebraic flip of ``1 + lambda((1-X)/(1-m) - 1)``). The alarm
  level is the user's ``1/alpha`` on the 50/50 mixture; validity needs the POINT null
  ``E[X | past] = m``.

Deviations of the T2 core: the strict-vs-weak inequality above; log-space recursions (numerically
equal to the printed ones); no Algorithm 2 (adaptive, defaults for r, m, K_0 are not in the paper
text); only the sub-exponential ``psi_E`` (bounded data); Bernoulli ``psi_B`` grid not implemented.

T3 adapter (what is NOT inherited from the paper)
-------------------------------------------------
Stream and clock: LABEL clock, delivery order. For each delivered label
``z = loss(deployed) - loss(other) in {-1, 0, 1}`` and ``X = (z + 1)/2``, ``m = 1/2``; eq (70)
becomes ``1 + lambda z``. ``X > m`` means the non-deployed model was better. The "promote" side
(incumbent deployed) and the "rollback" side (challenger deployed, testing deployed-worse-than-previous)
therefore run the same one-sided statistic with the sign defined by the current deployment. In
deployment only the side against the deployed model triggers action, so the simultaneous stcpR6
50/50 mixture is NOT run; the pair of alternating one-sided detectors is what acts, each at
``alpha * side_alpha_fraction`` (default alpha/2, the stcpR6 split).

Acquisition: shared ``PacedDisagreementAcquisition`` (controls.py), identical to the other
certificate adapters; propensities are NOT used (no IPW), so the tested mean is the
disagreement-conditional mean, whose sign relative to 1/2 equals the sign of the paired gain.

Start at EVERY label (no 10-label spacing), which is the matched-competitor point against RMM
(``scripts/failure_atlas_v2/restart_monitor.py:72-102``, gap = 10). Restart: after any switch BOTH
detectors are rebuilt fresh and labels REQUESTED at or before the switch event are dropped (RMM
clears its ``order``/``queue`` identically), so the restarted statistic sees only post-switch
requests. Dropped in-flight labels still consume budget.

Calibration (``calibration=``):
* ``"rmm_matched"`` (default): the finite-horizon form RMM uses: start weights ``1/B`` over the
  first ``B`` labels (``B`` = hard label budget, so at most B labels can ever arrive), threshold
  ``1/alpha_side`` on the weighted sum, i.e. Remark 2.7 with ``sum pi_s = 1``. The Algorithm 3 grid
  is built for the equivalent unit-mass level ``alpha_side / B``. Null guarantee (this is the
  adapter's proved statement, via Ville on ``V_n = S_n + sum_{j>n} pi_j``, derived in the check file,
  not in the paper): if, in the label-delivery filtration after the last restart, the conditional mean
  of X given the past and given selection is <= m (= challenger-not-better for the promote side),
  then ``P(promote side ever fires within the budget) <= alpha_side``.
* ``"arl"``: Def 2.6 unit start mass, threshold ``1/alpha_side`` (Theorem 2.4, ARL >= 1/alpha_side
  only). Not a finite-horizon error bound: within n labels the Markov/e-detector inequality gives
  only ``P(fire within n) <= n alpha_side``.
Bets (``bets=``): ``"algorithm3"`` (default; Delta range from ``delta_min`` below) or ``"rmm"``
(RMM's fixed lambda in {0.15, 0.3, 0.5}, uniform weights) so the comparison against RMM can be
reduced to spacing/restart/split differences.
Delta range for +-1 outcomes (``v(X) = (X/m - 1)^2 = 1`` on disagreements, so ``Delta_op =
E s / E v = E s <= 1``): ``Delta_L = m delta_min/(1-m)^2 = 2 delta_min`` (eq (75) lower), ``Delta_U =
1`` (largest attainable ``Delta_op``). ``delta_min = 0.05`` is a design constant, not tuned.

Not covered, even under rmm_matched: dependence between outcome signs (the conditional-mean null
needs it given the past; Markov persistence rho > 0 in the Atlas regimes breaks the independence the
simulation tests use, not the supermartingale argument, but no ShiftLab theorem is claimed there);
out-of-order release (the simulator releases at a constant delay, so delivery order = request order);
cumulative error across repeated promote/rollback cycles (each phase has its own level and the
levels add; no joint guarantee). Switching cost and label price do not enter the decision.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

_SOTA = Path(__file__).resolve().parents[1]
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback

_CALIBRATIONS = ("rmm_matched", "arl")
_BETS = ("algorithm3", "rmm")
RMM_LAMBDAS = (0.15, 0.3, 0.5)


# --------------------------------------------------------------------------- Algorithm 3
def psi_star_E(u):
    """Convex conjugate of the sub-exponential ``psi_E``: ``u - log(1+u)`` (eq (72)/(5.8))."""
    u = np.asarray(u, dtype=float)
    return u - np.log1p(u)


def lambda_of_delta(delta):
    """``grad psi*_E(Delta) = Delta/(1+Delta)`` (Def 4.1 / eq (44)-(45))."""
    d = np.asarray(delta, dtype=float)
    return d / (1.0 + d)


def _inv_psi_star(d_target: np.ndarray) -> np.ndarray:
    """Solve ``psi*_E(u) = D`` for u > 0 by vectorised bisection (psi*_E increasing on u > 0)."""
    d_target = np.asarray(d_target, dtype=float)
    lo = np.zeros_like(d_target)
    hi = np.ones_like(d_target)
    while np.any(psi_star_E(hi) < d_target):
        hi = np.where(psi_star_E(hi) < d_target, hi * 2.0, hi)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        below = psi_star_E(mid) < d_target
        lo = np.where(below, mid, lo)
        hi = np.where(below, hi, mid)
    return hi


def eq75_range(m: float, delta: float) -> tuple[float, float]:
    """Eq (75)/(5.11) as used for the NBA example: ``Delta_L = m delta/(1-m)^2``, ``Delta_U = m(1-m)/delta^2``.

    m = 0.494, delta = 0.0125 gives (0.02412, 1599.77); the paper rounds to (0.024, 1600).
    """
    return m * delta / (1.0 - m) ** 2, m * (1.0 - m) / delta**2


@lru_cache(maxsize=256)
def algorithm3_grid(
    alpha: float, delta_lower: float, delta_upper: float, kmax: int = 1000, v_min: float = 0.0
) -> dict:
    """Algorithm 3 / App. B.1 eqs (94)-(96) for the sub-exponential psi_E.

    Returns ``lambdas`` (atom first if present, then interior points from large to small, ending
    with ``lambda_L``), normalised ``weights``, ``g_alpha``, ``K_alpha``, ``eta`` and ``atom``.
    If ``delta_upper <= delta_lower`` or ``log(1/alpha) <= v_min psi*(Delta_L)`` a single baseline
    ``lambda_L`` with weight one is returned (Algorithm 3 step 2).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    if not 0.0 < delta_lower:
        raise ValueError("delta_lower must be positive")
    d_l = float(psi_star_E(delta_lower))
    d_u = float(psi_star_E(max(delta_upper, delta_lower)))
    log_inv_alpha = math.log(1.0 / alpha)
    if delta_upper <= delta_lower or log_inv_alpha <= v_min * d_l:
        lam = float(lambda_of_delta(delta_lower))
        return {
            "lambdas": np.array([lam]),
            "weights": np.array([1.0]),
            "g_alpha": log_inv_alpha,
            "K_alpha": 1,
            "eta": 1.0,
            "atom": False,
        }
    r = d_u / d_l
    ks = np.arange(1, kmax + 1, dtype=float)
    inv_r = r ** (-1.0 / ks)
    log_ks = np.log(ks)

    def excess(g: float) -> float:  # LHS of (94) minus alpha; decreasing in g
        atom = math.exp(-g) if g > v_min * d_u else 0.0
        return atom + math.exp(float(np.min(log_ks - g * inv_r))) - alpha

    lo = log_inv_alpha
    hi = max(10.0 * log_inv_alpha, v_min * d_u + 1.0)
    while excess(hi) > 0.0:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if excess(mid) <= 0.0:
            hi = mid
        else:
            lo = mid
    g = hi
    k_alpha = int(np.argmin(log_ks - g * inv_r)) + 1  # (95)
    eta = r ** (1.0 / k_alpha)
    atom = g > v_min * d_u
    interior = _inv_psi_star(d_u * eta ** (-np.arange(1, k_alpha, dtype=float)))
    lam = np.concatenate(
        [
            [float(lambda_of_delta(max(delta_upper, delta_lower)))] if atom else [],
            lambda_of_delta(interior),
            [float(lambda_of_delta(delta_lower))],
        ]
    )
    w = np.concatenate([[math.exp(-g)] if atom else [], np.full(k_alpha, math.exp(-g / eta))])
    w = w / w.sum()  # (96): normalise by W
    return {
        "lambdas": lam,
        "weights": w,
        "g_alpha": g,
        "K_alpha": k_alpha,
        "eta": eta,
        "atom": atom,
    }


def two_sided_bounded_grid(
    alpha: float,
    m: float,
    delta_lower: float,
    delta_upper: float,
    kmax: int = 1000,
    v_min: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """stcpR6 ``two.sided`` for bounded data: greater + less grids at alpha/2, weights halved.

    The ``less`` bets are sent to ``-m lambda/(1-m)`` so the factor is
    ``1 - (m/(1-m)) lambda (X/m - 1)``. The same Delta range is used for both grids, which is exact
    only for m = 1/2 (the case used here); stcpR6 recomputes the range for the mirrored problem.
    Returns signed ``lambdas`` and weights summing to one.
    """
    up = algorithm3_grid(alpha / 2.0, delta_lower, delta_upper, kmax, v_min)
    dn = algorithm3_grid(alpha / 2.0, delta_lower, delta_upper, kmax, v_min)
    lam = np.concatenate([up["lambdas"], -m * dn["lambdas"] / (1.0 - m)])
    w = np.concatenate([up["weights"] / 2.0, dn["weights"] / 2.0])
    return lam, w


# --------------------------------------------------------------------------- detector
class BoundedMeanEDetector:
    """Mixture e-SR / e-CUSUM with the eq (70) increment, log-space, initialised at M_0 = 0.

    ``kind="sr"``: ``log S_k <- log L_k + logaddexp(log S_k, log pi_n)`` with ``pi_n = start_weight``
    while ``n <= max_starts`` (all n if ``None``), else 0 (Def 2.6 for ``start_weight=1``, Remark 2.7
    otherwise). ``kind="cusum"``: ``log M_k <- log L_k + max(log M_k, 0)`` (unit start only).
    The statistic is ``log sum_k w_k M_k``; the alarm is ``log M >= threshold`` (``>=``, paper (7)).
    """

    def __init__(
        self,
        lambdas,
        weights,
        *,
        m: float = 0.5,
        kind: str = "sr",
        start_weight: float = 1.0,
        max_starts: int | None = None,
        threshold: float,
    ):
        lam = np.asarray(lambdas, dtype=float)
        w = np.asarray(weights, dtype=float)
        if lam.shape != w.shape or lam.ndim != 1 or np.any(w <= 0.0):
            raise ValueError("lambdas and weights must be matching 1-d arrays, weights > 0")
        if not math.isclose(float(w.sum()), 1.0, rel_tol=1e-9):
            raise ValueError("mixture weights must sum to one")
        if not 0.0 < m < 1.0:
            raise ValueError("m must lie in (0, 1)")
        if np.any(lam >= 1.0) or np.any(lam <= -m / (1.0 - m)):
            raise ValueError("bets must satisfy -m/(1-m) < lambda < 1 so the increment is positive")
        if kind not in ("sr", "cusum"):
            raise ValueError("kind must be 'sr' or 'cusum'")
        if kind == "cusum" and (start_weight != 1.0 or max_starts is not None):
            raise ValueError("start weights apply to e-SR only (Remark 2.7)")
        if start_weight <= 0.0:
            raise ValueError("start_weight must be positive")
        self.lam, self.logw, self.m, self.kind = lam, np.log(w), float(m), kind
        self.log_pi = math.log(start_weight)
        self.max_starts = max_starts
        self.threshold = float(threshold)
        self.n = 0
        self.log_m = np.full(lam.shape, -np.inf)  # M_0 = 0, NOT the typo M_0 = 1

    def _log_increment(self, x: float) -> np.ndarray:
        if not 0.0 <= x <= 1.0:
            raise ValueError("observations must lie in [0, 1]")
        return np.log1p(self.lam * (x / self.m - 1.0))  # eq (70)/(5.6)

    def update(self, x: float) -> bool:
        self.n += 1
        log_l = self._log_increment(x)
        if self.kind == "sr":
            if self.max_starts is None or self.n <= self.max_starts:
                self.log_m = log_l + np.logaddexp(self.log_m, self.log_pi)  # (13)/(2.8)
            else:
                self.log_m = log_l + self.log_m
        else:
            self.log_m = log_l + np.maximum(self.log_m, 0.0)  # (14)/(2.9)
        return self.log_stat >= self.threshold

    @property
    def log_stat(self) -> float:
        z = self.log_m + self.logw
        top = float(np.max(z))
        if top == -math.inf:
            return -math.inf
        return top + math.log(float(np.sum(np.exp(z - top))))

    @property
    def stat(self) -> float:
        return math.exp(self.log_stat)


# --------------------------------------------------------------------------- T3 adapter
def _rmm_grid() -> tuple[np.ndarray, np.ndarray]:
    lam = np.array(RMM_LAMBDAS)
    return lam, np.full(len(lam), 1.0 / len(lam))


class TwoSidedESRDeploymentAdapter:
    """T3 adapter: alternating promote/rollback e-SR detectors on the label clock, restart at switch.

    Model 0 is the incumbent (deployed first), model 1 the challenger. See the module docstring for
    every deviation and for the exact scope of the null statement.
    """

    def __init__(
        self,
        horizon: int,
        budget: int,
        alpha: float,
        *,
        rng: np.random.Generator,
        calibration: str = "rmm_matched",
        bets: str = "algorithm3",
        side_alpha_fraction: float = 0.5,
        delta_min: float = 0.05,
        kmax: int = 1000,
        p_min: float = 0.05,
        name: str = "two_sided_esr_label_clock",
    ):
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        if calibration not in _CALIBRATIONS:
            raise ValueError(f"calibration must be one of {_CALIBRATIONS}")
        if bets not in _BETS:
            raise ValueError(f"bets must be one of {_BETS}")
        if not 0.0 < side_alpha_fraction <= 1.0:
            raise ValueError("side_alpha_fraction must lie in (0, 1]")
        self.name = name
        self.budget = int(budget)
        self.alpha_side = alpha * side_alpha_fraction
        self.calibration, self.bets = calibration, bets
        self.delta_min, self.kmax = float(delta_min), int(kmax)
        self.rng = rng
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.deployed = 0
        self.t = -1  # last event time seen (predict)
        self.t_switch = -1  # labels requested at or before this event time are dropped
        self.n_switches = self.n_promotions = self.n_rollbacks = 0
        self.n_labels_used = self.n_dropped_inflight = 0
        self.det = self._new_detector()

    @property
    def phase(self) -> str:
        return "promote" if self.deployed == 0 else "rollback"

    def _new_detector(self) -> BoundedMeanEDetector:
        a = self.alpha_side
        thr = math.log(1.0 / a)
        if self.calibration == "rmm_matched":
            n_starts, a_eff, w0 = self.budget, a / self.budget, 1.0 / self.budget
        else:
            n_starts, a_eff, w0 = None, a, 1.0
        if self.bets == "rmm":
            lam, w = _rmm_grid()
        else:
            g = algorithm3_grid(
                a_eff, 2.0 * self.delta_min, 1.0, self.kmax
            )  # m = 1/2: see docstring
            lam, w = g["lambdas"], g["weights"]
        return BoundedMeanEDetector(
            lam, w, m=0.5, kind="sr", start_weight=w0, max_starts=n_starts, threshold=thr
        )

    # ---- Policy protocol
    def predict(self, event: Event) -> int:
        self.t = event.t
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:  # delivery order is the label clock; never reordered
            if fb.t_requested <= self.t_switch:
                self.n_dropped_inflight += (
                    1  # requested before the restart: not in the new filtration
                )
                continue
            other = 1 - self.deployed
            z = float(fb.model_losses[self.deployed]) - float(fb.model_losses[other])
            self.n_labels_used += 1
            if self.det.update((z + 1.0) / 2.0):
                self._switch()

    def _switch(self) -> None:
        self.n_switches += 1
        if self.deployed == 0:
            self.n_promotions += 1
        else:
            self.n_rollbacks += 1
        self.deployed = 1 - self.deployed
        self.t_switch = self.t
        self.det = self._new_detector()  # both sides restart fresh

    def decision_state(self) -> str:
        return f"{self.phase};n={self.det.n};dep={self.deployed}"

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "t": self.t,
            "t_switch": self.t_switch,
            "n_switches": self.n_switches,
            "n_dis": self.acq.n_disagree,
            "n": self.det.n,
            "log_m": self.det.log_m.tolist(),
            "rng": self.rng.bit_generator.state,
        }

    def load_state_dict(self, s: dict) -> None:
        self.deployed, self.t, self.t_switch = int(s["deployed"]), int(s["t"]), int(s["t_switch"])
        self.n_switches = int(s["n_switches"])
        self.acq.n_disagree = int(s["n_dis"])
        self.det = self._new_detector()
        self.det.n = int(s["n"])
        self.det.log_m = np.asarray(s["log_m"], dtype=float)
        self.rng.bit_generator.state = s["rng"]
