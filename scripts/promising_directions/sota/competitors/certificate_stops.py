"""Certificate-triggered stopping comparators: DISCERN-style and gated deployment.

These are the two comparators the narrowed protocol (``docs/promising_directions/sota/
SOTA_NARROWED_PROTOCOL.md``) must beat. They hold ACQUISITION fixed (the shared
``PacedDisagreementAcquisition``) and differ only in the STOPPING RULE: acquisition stops the
moment a statistical certificate fires at level ``alpha``. They are not economic: neither knows the
switching cost or the remaining horizon, which is exactly what the protocol tests.

Sources (papers read for the relevant sections; author-code status audited 2026-11-05)
-------------------------------------------------------------------------------------------
**DISCERN**: arXiv:2609.17560, "Pay Only for Disagreement: Certified No-Regression Verdicts for
Model Updates with Matching Label-Complexity Bounds".
* Section 3: paired difference ``D_t = l(g(X_t),Y_t) - l(f(X_t),Y_t)``, ``Delta = E[D_t]`` (eq. 2;
  ``Delta > 0`` means the candidate is WORSE), Assumption 1 (prediction-determined loss, so
  ``D_t = 0`` on agreement), Lemma 2 (``Delta = E[D_t A_t]``). Verdicts: ``Safe(eps)`` asserts
  ``Delta < eps``; ``Regression`` asserts ``Delta > 0``.
* Section 4.1 Tier 0: a CS on the disagreement rate ``rho``; ``B * rho_upper < eps`` implies
  ``|Delta| < eps`` (eq. 3) and issues ``Safe(eps)`` with zero labels.
* Section 4.2 Tier 1: label requested on disagreements with a predictable probability
  ``pi_t in [pi_min, 1]`` that never consults ``Y_t``; Horvitz-Thompson increment
  ``Z_t = (L_t / pi_t) * A_t * D_t in [-c, c]``, ``c = B / pi_min`` (eq. 4);
  ``E[Z_t | F_{t-1}] = Delta`` (Lemma 3). Verdicts: ``Safe(eps)`` when the CS upper bound is
  ``< eps``; ``Regression`` when its lower bound is ``> 0``. ``delta_0 + delta_1 = delta`` makes
  the combined procedure sound (Theorem 4).
* Appendix A: the predictable-plug-in empirical-Bernstein CS of Waudby-Smith and Ramdas (2024),
  ``M_t(m) = prod_i exp(lambda_i (W_i - m) - v_i psi_E(lambda_i))``, ``psi_E(l) = -log(1-l) - l``,
  CS ``{m : M_t(m) < 2/delta}`` intersected over time; increments in ``[-c, c]`` are mapped to
  ``[0, 1]`` by ``z -> (z + c)/(2c)``; ``lambda_t = sqrt(2 log(2/delta) / (sigma2_{t-1} t
  log(t+1))) ^ lambda_max``.

**Gated deployment**: arXiv:2102.09540, Karampatziakis, Mineiro and Ramdas, "Off-policy Confidence
Sequences" (ICML 2021).
* Section 3 (Theorem 1): ``K_t(v) = prod (1 + l1_i (w_i - 1) + l2_i (w_i r_i - v))`` is a
  nonnegative martingale at ``v = V(pi)`` for predictable bets; ``{v : K_t(v) <= 1/alpha}``
  (running intersection) is a CS.
* Section 4.2 Lemma 1: ``ln(1+x) >= x + psi x^2`` for ``x >= -1/2``, ``psi = 2 - 4 ln 2``.
  Section 4.3 eq. (12): the hedged process ``K^pm = (K^+ + K^-)/2`` with ``r' = 1 - r``,
  ``v' = 1 - v``; Theorem 2. Section 4.4: the bet set
  ``C = {l2 >= 0, l1 + l2 <= 1/2, l1 (1 - wmax) + l2 <= 1/2}`` (common to all ``v``), the bet
  ``lambda_t = argmax_{lambda in C} psi lambda^T A lambda + lambda^T b`` (eq. 13) computed at the
  current CS endpoint, Algorithm 1 (its exact solution over the triangle ``C``), the endpoint
  update by the largest root of the quadratic lower bound on log wealth (eq. 14, with the
  ``ln(2/alpha)`` from hedging), and Algorithm 2 (MOPE).
* Section 5.3 "Gated Deployment": the lower CS crossing 0 triggers deployment, while the upper CS
  crossing 0 triggers discard; stopping need not be fixed in advance.
* Public author code: https://github.com/n17s/mope (pinned review checkout
  `a4b8584b622f3a8296932568c520c1bb3e1957f0`). Native numerical parity has not been checked.

Common event semantics (both classes)
-------------------------------------
Both models' losses are observed from one label, so the paired difference is identifiable. We
write ``d = l0 - l1`` (incumbent minus challenger; ``d = +1`` means the challenger is right and
the incumbent wrong). ``G = E[d]`` is the challenger's per-event gain. DISCERN's ``Delta = -G``.
The CS is over EVERY event, not only labelled ones: agreement events contribute exact zeros,
unqueried disagreements contribute ``w = 0``, queried ones ``w = 1/q`` with ``q`` the FROZEN
issue-time propensity carried by ``ReleasedFeedback.query_probability``. Increments are consumed
in event order and only once resolved, so every bet is measurable with respect to the past.

ADAPTER (delay): neither paper has delayed labels. We process increments in event order and block
on the earliest unresolved one, so the bet for increment ``t`` uses only increments ``< t`` that
have been released. This preserves predictability under delay at the price of lag. After the
budget is exhausted no further events are recorded (the propensity of a disagreement is then 0,
so including later zeros would bias the mean); the CS simply freezes and never fires afterwards.

ADAPTER (stopping and deployment): once a verdict fires, acquisition stops permanently and the
CS is frozen. The challenger is "in staging" (shadow-scored, free) until a deploy verdict; the
incumbent (model 0) is deployed before that. The deployment decision is a pure function of the
verdict, never of the switching cost.
"""

from __future__ import annotations

import math
import sys
from collections import deque
from pathlib import Path

import numpy as np

_SOTA = Path(__file__).resolve().parents[1]
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback

PSI_MOPE = 2.0 - 4.0 * math.log(2.0)  # Karampatziakis et al. Lemma 1


# =============================================================================== PrPl-EB CS
class PrPlEBCS:
    """Predictable-plug-in empirical-Bernstein CS for the mean of ``W in [0, 1]``.

    Source: DISCERN Appendix A (eq. 6), which recalls Waudby-Smith and Ramdas (2024), Thm. 2.

    ``M_t(m) = prod_i exp(lambda_i (W_i - m) - v_i psi_E(lambda_i))`` rejects small ``m``;
    the mirrored process ``prod_i exp(lambda_i (m - W_i) - v_i psi_E(lambda_i))`` rejects large
    ``m``. Each is compared to ``2/delta`` (so ``delta`` is the total miscoverage). Because the
    bet ``lambda_i`` does not depend on ``m``, ``log M_t(m)`` is LINEAR in ``m`` and the
    endpoints are available in closed form; the CS is the running intersection.

    ``v_i = 4 (W_i - mu_hat_{i-1})^2`` and ``psi_E(lambda) =
    (-log(1-lambda)-lambda)/4`` follow Waudby-Smith and Ramdas Thm. 2. Their product is exactly
    ``(W_i - mu_hat_{i-1})^2 * (-log(1-lambda)-lambda)``, matching the variance-penalty term
    printed in DISCERN Appendix A. The previous local port omitted the ``/4`` from ``psi_E`` while
    retaining the factor 4 in ``v_i``; that was a local fidelity bug, not a discrepancy in DISCERN.
    ``mu_hat_t = (1/2 +
    sum W) / (t+1)`` and ``sigma2_hat_t = (1/4 + sum (W_i - mu_hat_i)^2) / (t+1)`` are the
    Waudby-Smith and Ramdas plug-ins; DISCERN does not print them. ``lambda_max`` is not
    stated by DISCERN; 1/2 is the Waudby-Smith and Ramdas default.
    """

    def __init__(self, delta: float, lam_max: float = 0.5):
        if not 0.0 < delta < 1.0:
            raise ValueError("delta must lie in (0, 1)")
        if not 0.0 < lam_max < 1.0:
            raise ValueError("lam_max must lie in (0, 1) for psi_E to be finite")
        self.delta, self.lam_max = float(delta), float(lam_max)
        self.log_thr = math.log(2.0 / self.delta)
        self.t = 0
        self.sum_w = 0.0
        self.ss = 0.0
        self.sum_lam = 0.0
        self.sum_lam_w = 0.0
        self.sum_vpsi = 0.0
        self.lo = 0.0
        self.hi = 1.0
        self.last_lam = 0.0

    def update(self, w: float) -> None:
        if not -1e-12 <= w <= 1.0 + 1e-12:
            raise ValueError(f"increment {w} outside [0, 1]")
        w = min(max(w, 0.0), 1.0)
        t = self.t + 1
        sigma2_prev = (0.25 + self.ss) / t  # sigma2_hat_{t-1}
        mu_prev = (0.5 + self.sum_w) / t  # mu_hat_{t-1}
        lam = min(
            math.sqrt(2.0 * self.log_thr / (sigma2_prev * t * math.log(1.0 + t))), self.lam_max
        )
        # FIDELITY FIX 2026-11-03 (Failure Atlas v2): WSR eq. (14) defines
        # psi_E(l) = (-log(1-l) - l)/4 together with v_i = 4(W_i - mu)^2. The earlier port kept the
        # factor 4 in v_i but dropped the /4 in psi_E, inflating the variance penalty fourfold and
        # weakening this comparator. Verified against the arXiv:2010.09686 text.
        psi_e = (-math.log1p(-lam) - lam) / 4.0
        self.sum_lam += lam
        self.sum_lam_w += lam * w
        self.sum_vpsi += 4.0 * (w - mu_prev) ** 2 * psi_e
        self.last_lam = lam
        self.t = t
        self.sum_w += w
        mu_t = (0.5 + self.sum_w) / (t + 1)
        self.ss += (w - mu_t) ** 2
        lo_new = (self.sum_lam_w - self.sum_vpsi - self.log_thr) / self.sum_lam
        hi_new = (self.log_thr + self.sum_lam_w + self.sum_vpsi) / self.sum_lam
        self.lo = max(self.lo, lo_new)
        self.hi = min(self.hi, hi_new)

    def state(self) -> dict:
        return {k: getattr(self, k) for k in (
            "t", "sum_w", "ss", "sum_lam", "sum_lam_w", "sum_vpsi", "lo", "hi", "last_lam")}  # fmt: skip

    def load(self, s: dict) -> None:
        for k, v in s.items():
            setattr(self, k, int(v) if k == "t" else float(v))


# =============================================================================== MOPE CS
def _argmax_triangle(a_mat: np.ndarray, b: np.ndarray, wmax: float) -> tuple[float, float]:
    """``argmax_{lambda in C} psi lambda^T A lambda + b^T lambda`` (eq. 13, Algorithm 1).

    ``C`` is the triangle with vertices ``(1/(2(1-wmax)), 0)``, ``(1/2, 0)``, ``(0, 1/2)``,
    which are Algorithm 1's vertex list. Algorithm 1 tries the unconstrained maximiser, one
    candidate per face and the vertices; so do we. ADAPTER: the face candidates are found by a
    1-D concave maximisation along each edge segment rather than by the Lagrange formula, which
    is equivalent; the origin is always a candidate and wins ties (no bet is the safe default).
    """
    h = 2.0 * PSI_MOPE * a_mat  # Hessian of f; negative semidefinite since psi < 0
    verts = [(1.0 / (2.0 * (1.0 - wmax)), 0.0), (0.5, 0.0), (0.0, 0.5)]
    scale = max(1.0, float(np.abs(h).max()), float(np.abs(b).max()))
    tol = 1e-12 * scale

    def f(lam: np.ndarray) -> float:
        return float(0.5 * lam @ h @ lam + b @ lam)

    def feasible(lam: np.ndarray) -> bool:
        e = 1e-9
        return bool(
            lam[1] >= -e
            and lam[0] + lam[1] <= 0.5 + e
            and (1.0 - wmax) * lam[0] + lam[1] <= 0.5 + e
        )

    cands = [np.zeros(2)] + [np.array(v, dtype=float) for v in verts]
    det = float(h[0, 0] * h[1, 1] - h[0, 1] * h[1, 0])
    if h[0, 0] < -tol and h[1, 1] < -tol and det > 1e-9 * h[0, 0] * h[1, 1]:
        lam = np.array(
            [-(h[1, 1] * b[0] - h[0, 1] * b[1]) / det, -(h[0, 0] * b[1] - h[1, 0] * b[0]) / det]
        )  # -H^{-1} b by Cramer's rule; skipped when H is near-singular (edges/vertices cover it)
        if feasible(lam):
            cands.append(lam)
    for i in range(3):
        p = np.array(verts[i], dtype=float)
        q = np.array(verts[(i + 1) % 3], dtype=float)
        dvec = q - p
        f1 = float((h @ p + b) @ dvec)
        f2 = float(dvec @ h @ dvec)
        if f2 < -tol:
            s = min(max(-f1 / f2, 0.0), 1.0)
            cands.append(p + s * dvec)
    best, best_val = cands[0], f(cands[0])
    for c in cands[1:]:
        if not feasible(c):
            continue
        val = f(c)
        if val > best_val + 1e-15:
            best, best_val = c, val
    return float(best[0]), float(best[1])


class MopeLowerCS:
    """``LCS(Z)`` of Karampatziakis et al. Algorithm 2: a lower CS for ``V = E[w r]``.

    Wealth ``K^+_t(v) = prod (1 + l1_i (w_i - 1) + l2_i (w_i r_i - v))`` with a COMMON predictable
    bet in ``C`` (Section 4.4). The quadratic lower bound on log wealth (Lemma 1) gives an
    endpoint by the largest root of eq. (14). Everything is O(1) per step.
    """

    def __init__(self, alpha: float, wmax: float):
        if wmax <= 1.0:
            raise ValueError("wmax must exceed 1")
        self.alpha, self.wmax = float(alpha), float(wmax)
        # The half-initialized wealth is represented by the threshold 2/alpha on the
        # accumulated log factors: (1/2) * product > 1/alpha iff product > 2/alpha.
        self.log_thr = math.log(2.0 / self.alpha)
        self.keys = ("n", "s_aa", "s_as", "s_ss", "s_a", "s_s", "p11", "p12", "p22", "s1", "s2",
                     "v", "lam1", "lam2")  # fmt: skip
        for k in self.keys:
            setattr(self, k, 0.0)
        self.n = 0
        self._bet()

    def factor(self, w: float, r: float, v: float) -> float:
        """The wealth multiplier the NEXT observation would apply at test value ``v``."""
        return 1.0 + self.lam1 * (w - 1.0) + self.lam2 * (w * r - v)

    def update(self, w: float, r: float) -> None:
        a = self.lam1 * (w - 1.0) + self.lam2 * w * r  # lambda^T b_i(v) = a - s v
        s = self.lam2
        self.s_aa += a * a
        self.s_as += a * s
        self.s_ss += s * s
        self.s_a += a
        self.s_s += s
        self.p11 += (w - 1.0) ** 2
        self.p12 += (w - 1.0) * w * r
        self.p22 += (w * r) ** 2
        self.s1 += w - 1.0
        self.s2 += w * r
        self.n += 1
        # eq. (14): psi * sum lambda^T A lambda + sum lambda^T b = ln(2/alpha), as a quadratic in v.
        qa = PSI_MOPE * self.s_ss
        qb = -2.0 * PSI_MOPE * self.s_as - self.s_s
        qc = PSI_MOPE * self.s_aa + self.s_a - self.log_thr
        root = None
        if abs(qa) < 1e-14:
            if qb < -1e-14:
                root = -qc / qb
        else:
            disc = qb * qb - 4.0 * qa * qc
            if disc >= 0.0:
                sq = math.sqrt(disc)
                root = max((-qb + sq) / (2 * qa), (-qb - sq) / (2 * qa))
        if root is not None:
            self.v = min(max(self.v, root), 1.0)
        self._bet()

    def _bet(self) -> None:
        v = self.v
        a_mat = np.array(
            [[self.p11, self.p12 - v * self.s1], [self.p12 - v * self.s1,
             self.p22 - 2.0 * v * self.s2 + self.n * v * v]]
        )  # fmt: skip
        b = np.array([self.s1, self.s2 - v * self.n])
        self.lam1, self.lam2 = _argmax_triangle(a_mat, b, self.wmax)

    def state(self) -> dict:
        return {k: getattr(self, k) for k in self.keys}

    def load(self, s: dict) -> None:
        for k in self.keys:
            setattr(self, k, int(s[k]) if k == "n" else float(s[k]))


class MopeCS:
    """Two-sided hedged MOPE CS for ``V = E[w r]`` (Theorem 2): ``[v_lo, v_hi]``.

    The upper end is ``1 - LCS`` on the reflected stream ``r' = 1 - r`` (Algorithm 2's ``Z'``).
    """

    def __init__(self, alpha: float, wmax: float):
        self.plus, self.minus = MopeLowerCS(alpha, wmax), MopeLowerCS(alpha, wmax)

    def update(self, w: float, r: float) -> None:
        old_lo, old_hi = self.v_lo, self.v_hi
        self.plus.update(w, r)
        self.minus.update(w, 1.0 - r)
        # Algorithm 2 intersects the two one-sided bounds and enforces lo <= hi after
        # every event (opebet.wealth_lb_2d). Without this coupling, a lower endpoint can
        # exceed the reflected upper endpoint, unlike the published MOPE interval update.
        new_lo = min(old_hi, max(old_lo, self.plus.v))
        new_hi = max(new_lo, min(old_hi, 1.0 - self.minus.v))
        self.plus.v = new_lo
        self.minus.v = 1.0 - new_hi
        # Bets for the next increment use the intersected endpoint, as in Algorithm 2;
        # the one-sided updates above initially optimized at their uncoupled endpoints.
        self.plus._bet()
        self.minus._bet()

    @property
    def v_lo(self) -> float:
        return self.plus.v

    @property
    def v_hi(self) -> float:
        return 1.0 - self.minus.v

    def state(self) -> dict:
        return {"plus": self.plus.state(), "minus": self.minus.state()}

    def load(self, s: dict) -> None:
        self.plus.load(s["plus"])
        self.minus.load(s["minus"])


# =============================================================================== shared policy
class _Rec:
    """One event's increment slot: ``w`` is the HT weight, ``d = l0 - l1`` (0 until known)."""

    __slots__ = ("d", "eid", "resolved", "w")

    def __init__(self, eid: int, resolved: bool, w: float, d: int):
        self.eid, self.resolved, self.w, self.d = eid, resolved, w, d

    def as_list(self) -> list:
        return [self.eid, int(self.resolved), self.w, self.d]


class _CertificateStop:
    """Paced disagreement acquisition + ordered, delay-safe increment stream + a stopping rule.

    Subclasses implement ``_ingest`` (consume one resolved increment) and ``_check`` (return a
    verdict string or ``""``). A verdict stops acquisition for good and fixes the deployment.
    """

    deploy_verdicts: tuple[str, ...] = ()

    def __init__(self, horizon: int, budget: int, alpha: float, *, rng: np.random.Generator,
                 p_min: float = 0.05, name: str):  # fmt: skip
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        if not 0.0 < p_min <= 1.0:
            raise ValueError("p_min must lie in (0, 1]")
        self.name = name
        self.alpha = float(alpha)
        self.p_min = float(p_min)
        self.rng = rng
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.deployed = 0
        self.stopped = False
        self.exhausted = False
        self.verdict = ""
        self.stop_event = -1
        self.n_ingested = 0
        self._queue: deque[_Rec] = deque()
        self._pending: dict[int, _Rec] = {}

    # ---- subclass hooks
    def _ingest(self, w: float, d: int, event_ref: int) -> None:
        raise NotImplementedError

    def _check(self) -> str:
        raise NotImplementedError

    def _extra_state(self) -> dict:
        return {}

    def _load_extra(self, s: dict) -> None:
        pass

    def _on_acquisition_propensity(self, event: Event, q: float, disagree: bool) -> None:
        """Observe q before its Bernoulli draw or any synchronous queue flush."""
        pass

    # ---- Policy protocol
    def predict(self, event: Event) -> int:
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if self.stopped:
            return QueryRequest(requested=False)
        self._on_event_start(event)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self._on_acquisition_propensity(event, q, dis)
        self.acq.note_event(dis)
        if self.stopped:  # a zero-label verdict (Tier 0) may have fired on this event
            return QueryRequest(requested=False)
        if self.exhausted:
            return QueryRequest(requested=False)
        if not dis:
            self._queue.append(_Rec(event.t, True, 1.0, 0))
            self._flush()
            return QueryRequest(requested=False)
        if q <= 0.0:  # disagreement with no budget left: propensity 0, so stop recording
            self.exhausted = True
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        rec = _Rec(event.t, not take, 0.0, 0)  # unqueried disagreement is an exact w = 0
        self._queue.append(rec)
        if take:
            self._pending[event.t] = rec
        else:
            self._flush()
        return QueryRequest(requested=take, probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        if self.stopped:
            return
        for fb in feedback:
            rec = self._pending.pop(fb.event_id, None)
            if rec is None:
                continue
            if not fb.query_probability > 0.0:
                raise ValueError("released feedback must carry its positive issue-time propensity")
            rec.w = 1.0 / float(fb.query_probability)  # FROZEN issue-time propensity
            rec.d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            rec.resolved = True
        self._flush()

    def _on_event_start(self, event: Event) -> None:
        pass

    def _flush(self) -> None:
        while self._queue and self._queue[0].resolved and not self.stopped:
            rec = self._queue.popleft()
            self._ingest(rec.w, rec.d, rec.eid)
            self.n_ingested += 1
            self._after_ingest(rec.eid)

    def _after_ingest(self, ref: int) -> None:
        v = self._check()
        if v:
            self._fire(v, ref)

    def _fire(self, verdict: str, ref: int) -> None:
        self.verdict = verdict
        self.stopped = True
        self.stop_event = int(ref)
        self.deployed = 1 if verdict in self.deploy_verdicts else 0
        self._queue.clear()
        self._pending.clear()

    # ---- bookkeeping
    def decision_state(self) -> str:
        return f"{self.verdict or 'open'};dep={self.deployed}"

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "stopped": self.stopped,
            "exhausted": self.exhausted,
            "verdict": self.verdict,
            "stop_event": self.stop_event,
            "n_ingested": self.n_ingested,
            "n_dis": self.acq.n_disagree,
            "queue": [r.as_list() for r in self._queue],
            "pending": sorted(self._pending),
            "rng": self.rng.bit_generator.state,
            "extra": self._extra_state(),
        }

    def load_state_dict(self, s: dict) -> None:
        self.deployed, self.stopped = int(s["deployed"]), bool(s["stopped"])
        self.exhausted, self.verdict = bool(s["exhausted"]), str(s["verdict"])
        self.stop_event, self.n_ingested = int(s["stop_event"]), int(s["n_ingested"])
        self.acq.n_disagree = int(s["n_dis"])
        self._queue = deque(_Rec(int(e), bool(r), float(w), int(d)) for e, r, w, d in s["queue"])
        by_id = {r.eid: r for r in self._queue}
        self._pending = {int(e): by_id[int(e)] for e in s["pending"]}
        self.rng.bit_generator.state = s["rng"]
        self._load_extra(s["extra"])


# =============================================================================== DISCERN-style
class DiscernStyleStop(_CertificateStop):
    """DISCERN-style certificate stop: HT-weighted PrPl-EB CS, stop at ``Safe(eps)``/``Regression``.

    Tier 1 (DISCERN Section 4.2): increment ``Z_t = w_t * A_t * d_t`` with ``w_t = L_t/q_t`` and
    ``q_t`` the frozen issue-time propensity, mapped to ``[0,1]`` by ``(Z + c)/(2c)``,
    ``c = 1/p_min`` (``B = 1`` for 0/1 loss). Verdicts, in OUR sign (``G = -Delta``):

    * ``safe``       : ``G_lower > -eps``   (DISCERN ``Delta_upper < eps``)  -> deploy challenger
    * ``regression`` : ``G_upper < 0``      (DISCERN ``Delta_lower > 0``)    -> keep incumbent

    ADAPTER: with ``eps = 0`` ``safe`` is the strict "challenger certified better" verdict and
    the rule coincides with gated deployment's thresholds (different CS, same crossing). With
    ``eps > 0`` a challenger certified only "not worse by more than eps" is promoted, which is
    DISCERN's own semantics; ``eps`` must be fixed on development data, not tuned per dataset.

    ``tier0=True`` adds DISCERN's zero-label certificate (Section 4.1, eq. 3): a PrPl-EB CS on
    the disagreement rate; ``rho_upper < eps`` issues ``safe`` having bought nothing and promotes
    (DISCERN's "promote" semantics). Off by default because with a switching cost it makes the
    comparator switch to an equivalent model; we expose it so the strongest-reading variant can
    be run and reported. Level split ``delta_0 = delta_1 = alpha/2`` when on (Theorem 4).
    ADAPTER: Tier 0 needs no labels, so it is updated on every event including after the
    budget is exhausted.

    BLOCKED: this is built from the printed construction only; author code is now known to be
    available at https://github.com/n17s/mope, but native numerical parity has not been checked.
    DISCERN's learned judge routing is not used (acquisition is the shared paced rule).
    """

    deploy_verdicts = ("safe",)

    def __init__(self, horizon: int, budget: int, alpha: float, eps: float, *,
                 rng: np.random.Generator, p_min: float = 0.05, tier0: bool = False,
                 lam_max: float = 0.5, name: str = "discern_style"):  # fmt: skip
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name)
        if eps < 0.0:
            raise ValueError("eps must be >= 0 (0 is the strict 'better' limit)")
        self.eps, self.tier0 = float(eps), bool(tier0)
        self.c = 1.0 / self.p_min
        d1 = alpha / 2.0 if tier0 else alpha
        self.cs1 = PrPlEBCS(d1, lam_max)
        self.cs0 = PrPlEBCS(alpha / 2.0, lam_max) if tier0 else None

    @property
    def gain_bounds(self) -> tuple[float, float]:
        """Current CS for ``G = E[l0 - l1]`` per event (``[-c, c]``-scaled)."""
        return self.c * (2.0 * self.cs1.lo - 1.0), self.c * (2.0 * self.cs1.hi - 1.0)

    def _on_event_start(self, event: Event) -> None:
        if self.cs0 is not None:
            dis = float(event.model_predictions[0] != event.model_predictions[1])
            self.cs0.update(dis)
            if self.cs0.hi < self.eps:  # B * rho_upper < eps with B = 1  (eq. 3)
                self._fire("safe", event.t)

    def _ingest(self, w: float, d: int, event_ref: int) -> None:
        z = w * d
        self.cs1.update((z + self.c) / (2.0 * self.c))

    def _check(self) -> str:
        g_lo, g_hi = self.gain_bounds
        if g_lo > -self.eps:
            return "safe"
        if g_hi < 0.0:
            return "regression"
        return ""

    def _extra_state(self) -> dict:
        return {"cs1": self.cs1.state(), "cs0": None if self.cs0 is None else self.cs0.state()}

    def _load_extra(self, s: dict) -> None:
        self.cs1.load(s["cs1"])
        if self.cs0 is not None:
            self.cs0.load(s["cs0"])


# =============================================================================== gated deployment
class GatedDeploymentStop(_CertificateStop):
    """Gated deployment (Karampatziakis et al. Section 5.3) on the paired difference.

    "If we can reject all negative values (i.e. the lower CS crosses 0) then pi should be
    deployed. Conversely, rejecting all positive values (i.e. the upper CS crosses 0) means pi
    should be discarded." We deploy the challenger when the lower CS on ``G`` exceeds 0, discard
    (stop, keep incumbent) when the upper CS falls below 0, and stop acquiring on either.

    ADAPTER (the mapping onto MOPE): the paper's gated CS targets ``V(pi) - V(h)`` from logged
    ``(w, r)`` of a behaviour policy ``h``. Here the "importance weight" is the query indicator's
    HT weight ``w = L/q`` on disagreements and ``w = 1`` on agreements (``E[w | F] = 1``, the
    identity MOPE's second bet ``l1 (w - 1)`` exploits), and the "reward" is ``r = (d + 1)/2``
    (``r = 1/2`` on agreement), so ``E[w r] = V = (G + 1)/2`` and the CS for ``G`` is
    ``2V - 1``. This is the same IPS mean-estimation primitive, but it is not the paper's
    ``K^gd`` process (which differences ``w r - r``); the paired loss already is the difference.
    ``wmax = 1/p_min``. We use the paper's Algorithm 2 betting (two-dimensional bet in ``C``,
    hedged, endpoint from eq. 14) rather than a generic CS, so the control variate ``w - 1`` is
    exploited as in the paper. No reward predictor (Section 5.1) is used.

    BLOCKED: the paper's appendices C-E (exact gated-deployment constraint set, the scalar
    betting variant) were not ported; we use the main-text bet set ``C`` of Section 4.4, which is
    valid for every ``v`` and wealth-positive, at some loss of tightness.
    """

    deploy_verdicts = ("deploy",)

    def __init__(self, horizon: int, budget: int, alpha: float, *, rng: np.random.Generator,
                 p_min: float = 0.05, name: str = "gated_deployment"):  # fmt: skip
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name)
        self.cs = MopeCS(alpha, 1.0 / self.p_min)

    @property
    def gain_bounds(self) -> tuple[float, float]:
        return 2.0 * self.cs.v_lo - 1.0, 2.0 * self.cs.v_hi - 1.0

    def _ingest(self, w: float, d: int, event_ref: int) -> None:
        self.cs.update(w, (d + 1.0) / 2.0)

    def _check(self) -> str:
        g_lo, g_hi = self.gain_bounds
        if g_lo > 0.0:
            return "deploy"
        if g_hi < 0.0:
            return "discard"
        return ""

    def _extra_state(self) -> dict:
        return {"cs": self.cs.state()}

    def _load_extra(self, s: dict) -> None:
        self.cs.load(s["cs"])
