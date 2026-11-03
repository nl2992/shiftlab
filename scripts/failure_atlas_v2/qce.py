"""Query-conditional evidence (QCE): an attachable evidence correction for paid-label SOTA methods.

Weakness addressed
------------------
Gated deployment (off-policy CS), DISCERN and Xu et al. form a Horvitz-Thompson increment on
EVERY event, ``w_t d_t`` with ``w_t = L_t / q_t`` and ``d_t = l0_t - l1_t``. An anytime-valid
betting CS must keep wealth positive for the WORST possible increment, so the bet is capped by the
declared weight range ``1/p_min`` (Gated: ``l1 (1 - wmax) + l2 <= 1/2``; DISCERN: ``c = B/pi_min``;
Xu: ``lambda <= q/2`` on ``d/q``). When a hard budget forces ``q_t < 1`` the realised increments
are far inside that range, the cap binds, and the certificate needs many more events than the
labels' information warrants. SMCS avoids the range (its ``lambda_s d/q_s = d/2`` cancels the
weight) but bets a fixed ``1/2``, which is mis-sized for a small advantage. Both are failures to
turn a bought label into evidence at the rate its information allows.

Rule
----
Let ``s_1 < s_2 < ...`` be the queried disagreement events, issued with a predictable propensity
``q_{s_k}`` that does not read the label. Their outcomes ``Y_k = d_{s_k} in {-1, +1}`` are ingested
in request order with weight 1. For the pointwise conditional promotion null

    H0:  E[d_t | F_{t-1}, predictions_t, d_t != 0] <= 0   for every t

(the challenger is never better on any event; equivalently ``G_t = dis_t (2 p_t - 1) <= 0`` for
all ``t`` since ``dis_t >= 0``), the query decision is conditionally independent of ``Y_k`` given
the past, so ``E[Y_k | G_{k-1}] <= 0`` and ANY bounded-mean e-process/CS over ``[-1, 1]`` is valid
on the ``Y`` stream. QCE hands the host method's own CS (MOPE, PrPl-EB, the Xu product, the SMCS
product) this stream with range 1 instead of ``1/p_min``, and replaces a fixed bet by the host's
predictable plug-in (SMCS: aGRAPA, clipped to ``[0, 1/2]``).

What is preserved: the host's acquisition (unless ``front=True``), stopping rule, deployment rule,
delay handling (request-order ingestion, bets fixed from released data) and level ``alpha``.
What changes: the evidence estimand moves from the event average of ``G_t`` to the query-average
of ``2 p_t - 1``. Both are <= 0 under H0, so false-promotion control under H0 is the same
anytime level ``alpha``; under nonstationary alternatives the two averages weight time differently
(recorded as a limitation, measured in the atlas reversal/transient cells).

``front=True`` is the separate acquisition ablation: query every disagreement (q = 1) while the
host is undecided. It is valid for the same reason (q predictable) and is reported separately.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (SOTA, SOTA / "competitors", SOTA.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from certificate_stops import (  # noqa: E402
    DiscernStyleStop,
    GatedDeploymentStop,
    MopeCS,
    PrPlEBCS,
    _Rec,
)
from simulator import QueryRequest  # noqa: E402
from smcs import SMCSDeploymentPolicy  # noqa: E402
from xu_acquisition import XuAcquisitionPolicy  # noqa: E402


# ------------------------------------------------------------------ certificate-stop hosts
class _QCECertMixin:
    """Record only queried disagreements, with weight 1, in request order."""

    front = False

    def request_labels(self, event, remaining_budget):
        if self.stopped or self.exhausted:
            return QueryRequest(requested=False)
        self._on_event_start(event)
        if self.stopped:
            return QueryRequest(requested=False)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        if self.front and dis and remaining_budget > 0:
            q = 1.0
        self.acq.note_event(dis)
        if not dis or q <= 0.0:
            if dis and remaining_budget <= 0:
                self.exhausted = True
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        if take:
            rec = _Rec(event.t, False, 1.0, 0)
            self._queue.append(rec)
            self._pending[event.t] = rec
        return QueryRequest(requested=take, probability=q)

    def observe(self, feedback):
        if self.stopped:
            return
        for fb in feedback:
            rec = self._pending.pop(fb.event_id, None)
            if rec is None:
                continue
            rec.w = 1.0  # QCE: the label enters with weight 1, not 1/q
            rec.d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            rec.resolved = True
        self._flush()


class GatedQCE(_QCECertMixin, GatedDeploymentStop):
    """Gated deployment + QCE: the paper's MOPE betting CS on ``r = (Y + 1)/2``, ``w = 1``."""

    def __init__(self, horizon, budget, alpha, *, rng, p_min=0.05, front=False,
                 name="gated_deployment+QCE"):  # fmt: skip
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name)
        self.cs = MopeCS(alpha, 2.0)  # every w = 1 <= wmax; wmax only bounds the unused l1 bet
        self.front = front


class DiscernQCE(_QCECertMixin, DiscernStyleStop):
    """DISCERN-style + QCE: PrPl-EB CS on ``Y in [-1, 1]`` (``c = 1`` instead of ``1/p_min``)."""

    def __init__(self, horizon, budget, alpha, eps=0.0, *, rng, p_min=0.05, front=False,
                 name="discern_style+QCE"):  # fmt: skip
        super().__init__(horizon, budget, alpha, eps, rng=rng, p_min=p_min, name=name)
        self.c = 1.0
        self.cs1 = PrPlEBCS(alpha)
        self.front = front


class GatedFrontOnly(GatedDeploymentStop):
    """Ablation: the original HT evidence with front-loaded (q = 1) acquisition."""

    def __init__(self, horizon, budget, alpha, *, rng, p_min=0.05, name="gated+front_only"):
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name)
        base = self.acq.propensity

        def prop(t, remaining, disagree, _b=base):
            return 1.0 if (disagree and remaining > 0) else _b(t, remaining, disagree)

        self.acq.propensity = prop


# ------------------------------------------------------------------ SMCS host
class SMCSQCE(SMCSDeploymentPolicy):
    """SMCS + QCE: same product e-process and set, predictable aGRAPA bet instead of 1/2.

    For pair (i, j) the bet uses the released history of ``Y_ij = L_i - L_j`` on queried events:
    ``lam = clip(m / (v + m^2), 0, 1/2)`` with ``m, v`` the running mean and second moment
    (prior pseudo-observation 0), computed BEFORE the new outcome is added, so it is predictable
    in the query-indexed filtration. ``1 + lam * Y >= 1/2`` keeps wealth positive.
    """

    def __init__(self, n_models, rng, *, alpha=0.05, name="SMCS+QCE", **kw):
        super().__init__(n_models, rng, alpha=alpha, name=name, **kw)
        self.s1 = np.zeros((n_models, n_models))
        self.s2 = np.ones((n_models, n_models))  # prior: one pseudo-observation of |Y| = 1
        self.n = np.ones((n_models, n_models))

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            losses = np.asarray(fb.model_losses, dtype=float)
            y = losses[:, None] - losses[None, :]
            m = self.s1 / self.n
            lam = np.clip(m / np.maximum(self.s2 / self.n, 1e-12), 0.0, 0.5)
            self.cum_iw_loss += losses / fb.query_probability
            self.inference.update_pairs(y, lam)
            self.s1 += y
            self.s2 += y * y
            self.n += 1.0
        self._redeploy()


# ------------------------------------------------------------------ Xu host
class XuQCE(XuAcquisitionPolicy):
    """Xu et al. acquisition-only + QCE: increment ``d`` (not ``d/q``) on asked events, cap 1/2."""

    def __init__(self, rng, *, delay, alpha=0.05, name="xu_acquisition_only+QCE", **kw):
        super().__init__("acquisition_only", rng, delay=delay, alpha=alpha, **kw)
        self.name = name

    def evidence_increment(self, q, mu, d, asked):
        return asked * d

    def request_labels(self, event, remaining_budget):
        req = super().request_labels(event, remaining_budget)
        if req.requested:
            lam = float(np.clip(
                __import__("b3_plus_policy").b1.bet_from_stats(
                    self.s1, self.s2, self.cnt, self.params, kelly=False), 0.0, 0.5))
            req.extra["lam"] = lam
        return req


EXTRA = {
    "gated_deployment+QCE": lambda T, B, cs, cq, a, d, r: GatedQCE(T, B, a, rng=r("gated_deployment")),
    "discern_style+QCE": lambda T, B, cs, cq, a, d, r: DiscernQCE(T, B, a, rng=r("discern_style")),
    "SMCS+QCE": lambda T, B, cs, cq, a, d, r: SMCSQCE(2, r("smcs"), alpha=a),
    "xu_acquisition_only+QCE": lambda T, B, cs, cq, a, d, r: XuQCE(r("xu"), delay=d, alpha=a),
    "gated_deployment+QCE+front": lambda T, B, cs, cq, a, d, r: GatedQCE(
        T, B, a, rng=r("gated_deployment"), front=True, name="gated_deployment+QCE+front"),
    "gated+front_only": lambda T, B, cs, cq, a, d, r: GatedFrontOnly(T, B, a, rng=r("gated_deployment")),
}


# ------------------------------------------------------------------ front-loading ablations
class DiscernFrontOnly(DiscernStyleStop):
    """Ablation: the original HT evidence (c = 1/p_min) with q = 1 while undecided."""

    def __init__(self, horizon, budget, alpha, eps=0.0, *, rng, p_min=0.05,
                 name="discern+front_only"):  # fmt: skip
        super().__init__(horizon, budget, alpha, eps, rng=rng, p_min=p_min, name=name)
        base = self.acq.propensity
        self.acq.propensity = lambda t, rem, dis, _b=base: 1.0 if (dis and rem > 0) else _b(t, rem, dis)


def _smcs_front(pol):
    """q = 1 while the incumbent is still in the SMCS set (the undecided state)."""
    base = pol.acq.probability

    def prob(t, horizon, remaining, _b=base, _p=pol):
        if remaining > 0 and _p.inference.members[_p.incumbent]:
            return 1.0
        return _b(t, horizon, remaining)

    pol.acq.probability = prob
    return pol


def _xu_front(pol):
    """Xu has no terminal verdict (it keeps betting for rollback); eager = q_min of 1."""
    pol.q_min = 1.0
    return pol


EXTRA.update({
    "discern_style+QCE+front": lambda T, B, cs, cq, a, d, r: DiscernQCE(
        T, B, a, rng=r("discern_style"), front=True, name="discern_style+QCE+front"),
    "discern+front_only": lambda T, B, cs, cq, a, d, r: DiscernFrontOnly(T, B, a, rng=r("discern_style")),
    "SMCS+QCE+front": lambda T, B, cs, cq, a, d, r: _smcs_front(
        SMCSQCE(2, r("smcs"), alpha=a, name="SMCS+QCE+front")),
    "SMCS+front_only": lambda T, B, cs, cq, a, d, r: _smcs_front(
        SMCSDeploymentPolicy(2, r("smcs"), alpha=a, name="SMCS+front_only")),
    "xu_acquisition_only+QCE+front": lambda T, B, cs, cq, a, d, r: _xu_front(
        XuQCE(r("xu"), delay=d, alpha=a, name="xu_acquisition_only+QCE+front")),
    "xu+front_only": lambda T, B, cs, cq, a, d, r: _xu_front(
        _named(XuAcquisitionPolicy("acquisition_only", r("xu"), delay=d, alpha=a), "xu+front_only")),
})


def _named(pol, name):
    pol.name = name
    return pol
