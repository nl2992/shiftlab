"""Family C (SOTA sprint): label acquisition and economics on certified hosts (Agent C).

Every candidate here changes ONLY the acquisition rule of an existing certified host; the host's
confidence sequence (CS), stopping rule and deployment rule are untouched.

Hosts
-----
* ``gated_adaptive_range`` (MOPE off-policy CS, per-step ``wmax_t = 1/q_t``), and its ``+front``.
* ``discern_design_floor`` (corrected DISCERN PrPl-EB CS, ``pi_min = .25``, ``c = 4``) and
  ``discern_style`` (``pi_min = .05``).
* ``QSG`` (query-conditional started mixture; no importance weights).

Acquisition actions
-------------------
At each event a controller returns ``(pi, q)``: the event is *recorded* in the host CS with
probability ``pi`` (a predictable coin from the host's private generator, drawn before the label
exists) and, if recorded and a disagreement, its label is requested with propensity ``q``. The
issue-time ``q`` travels with the request (``QueryRequest.probability``) and the host uses
``1/q`` from ``ReleasedFeedback.query_probability`` as the importance weight; for the gated host the
per-step range ``wmax_t = max(1/q, 2)`` is also fixed at issue. An unrecorded event never enters
the CS (no increment, no block on the ordered queue).

The cheapest valid "skip" differs by host and is declared (``skip_action``):
* gated (adaptive range): skip = unrecorded (``pi = 0``). A recorded low-``q`` event would set
  ``wmax_t = 1/q`` and an exact zero for most such events, which costs wealth.
* DISCERN (fixed range ``c = 1/pi_min``): skip = record with ``q = pi_min`` (the CS is
  event-clock-limited under ``lam_max``, so dropping events slows it; ``q = pi_min`` keeps
  ``|Z| <= c``).

Validity (stated per candidate in docs/sota_sprint/family_c/README.md)
----------------------------------------------------------------------
For the propensity-weighted hosts the false-promotion guarantee needs (i) ``q_t`` predictable
(it reads only the past released labels, the pending count, predictions of event t and the
budget), (ii) ``q_t >= 1/wmax_t`` where the CS needs it (gated: ``wmax_t = 1/q_t`` exactly;
DISCERN: ``q_t >= pi_min``, enforced by clamping), and (iii) the recorded subsequence chosen by a
predictable coin. (iii) is optional skipping of a test supermartingale: under the pointwise
promotion null ``E[l0 - l1 | F_{t-1}, predictions_t] <= 0`` every recorded increment has
conditional mean on the null side, so Ville's inequality still applies. Under a non-stationary
alternative the CS then targets the average over *recorded* events, not over all events (the
same estimand change QCE records). No candidate reads the label of the event it decides on.

Factories have the sprint signature ``f(T, B, cs, cq, alpha, delay, r) -> Policy``.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (
    ROOT / "scripts/failure_atlas_v2_flq",
    ROOT / "scripts/promising_directions/sota",
    ROOT / "scripts/promising_directions/sota/competitors",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from certificate_stops import _Rec
from qsg import QSG
from simulator import QueryRequest
from strong_hosts import DiscernStyleStop, GatedAdaptiveRange

PRIOR_RATE, PRIOR_W = 0.25, 20.0  # same disagreement-rate prior as PacedDisagreementAcquisition


# =============================================================================== controller
class Controller:
    """Acquisition controller. One class, flags select the mechanism (so ablations are exact).

    base:
      ``uniform``   q = remaining / expected remaining disagreements (the host pacer)
      ``k``         horizon-weighted pacing, q = k * remaining / expected remaining (k-pacer)
      ``frontfrac`` q = 1 until ``f*B`` labels are spent, then uniform (tuned-baseline family)
      ``front``     q = 1 while undecided (the ``+front`` repair)
      ``verdict``   C4: pace the remaining budget to the *projected verdict time* rather than T
    mechanisms (applied on top of the base; a gated-off event takes the host's skip action):
      ``credit``    C1 pending-label credit
      ``shadow``    C2 value-of-label vs adaptive shadow price of budget
      ``deadline``  C6 deadline-aware value (release t+delay must precede the last useful moment)
      ``two_stage`` C3/C6 phase 1 base up to ``f2*B`` labels, then protected uniform phase
    """

    def __init__(self, base="front", *, k=1.0, f=1.0, credit=False, kappa=1.0, shadow=False,
                 gamma=1.0, zeta=0.5, deadline=False, two_stage=None, n0=10,
                 explore=0.0, skip_action=None, beta=None):  # fmt: skip
        self.base, self.k, self.f = base, float(k), float(f)
        self.credit, self.kappa = credit, float(kappa)
        self.shadow, self.gamma, self.zeta = shadow, float(gamma), float(zeta)
        self.deadline, self.two_stage, self.n0 = deadline, two_stage, int(n0)
        self.explore = float(explore)
        self.skip_action = skip_action  # None -> host default
        self.beta = beta  # C4 width-decay exponent override (None -> host default)
        self.n_gated_off = 0

    # ---- estimates the controller may use (all from released labels / past events only)
    @staticmethod
    def stats(pol, t):
        rate = (pol.acq.n_disagree + PRIOR_RATE * PRIOR_W) / (t + PRIOR_W)
        p_hat = (pol.c_sum_z + 1.0) / (pol.c_n_rel + 2.0)
        g_hat = rate * (2.0 * p_hat - 1.0)  # per-event advantage estimate
        g_lo, g_hi = pol.gain_bounds
        return rate, g_hat, g_lo, g_hi

    def decide(self, pol, t, rem, dis):
        T, B = pol.c_T, pol.c_B
        rate = (pol.acq.n_disagree + PRIOR_RATE * PRIOR_W) / (t + PRIOR_W)
        exp_left = max(rate * (T - t), 1e-9)
        uni = min(max(rem / exp_left, pol.p_min), 1.0)
        spent = B - rem
        phase2 = self.two_stage is not None and spent >= self.two_stage * B
        # ---- base intensity (pi, q)
        if phase2:
            base = pol.c_phase2(rem, exp_left)
        elif self.base == "uniform":
            base = (1.0, uni)
        elif self.base == "k":
            base = (1.0, min(max(self.k * rem / exp_left, pol.p_min), 1.0))
        elif self.base == "frontfrac":
            base = (1.0, 1.0) if spent < self.f * B else (1.0, uni)
        elif self.base == "front":
            base = (1.0, 1.0)
        elif self.base == "verdict":
            base = (1.0, self._verdict_q(pol, t, rem, rate))
        else:
            raise ValueError(self.base)
        if not (self.credit or self.shadow or self.deadline):
            return base
        if not self._value_gate(pol, t, rem, rate, base, phase2):
            self.n_gated_off += 1
            return pol.c_skip(self.skip_action, self.explore)
        return base

    def _value_gate(self, pol, t, rem, rate, base, phase2) -> bool:
        if pol.c_n_rel < self.n0:
            return True  # warm-up: no estimate yet
        T, cs, cq, delay = pol.c_T, pol.c_cs, pol.c_cq, pol.c_delay
        _, g_hat, g_lo, g_hi = self.stats(pol, t)
        hw = max((g_hi - g_lo) / 2.0, 1e-9)
        n = pol.c_n_rel
        P = len(pol._pending)
        # C1: will the labels already requested settle the verdict? (point estimate, safety kappa)
        if self.credit and g_hat > 0:
            n_tot_pt = n * (hw / g_hat) ** 2
            if n + P >= self.kappa * n_tot_pt:
                return False
        if not (self.shadow or self.deadline):
            return True
        g_eff = max(0.0, (1.0 - self.zeta) * max(g_hat, 0.0) + self.zeta * max(g_hi, 0.0))
        if g_eff <= 0.0:
            return False
        n_tot = n * (hw / g_eff) ** 2
        n_rem = max(n_tot - n - (P if self.credit else 0), 1.0)
        horizon = T - t
        if self.deadline:
            pi_hi = base[0] * base[1]
            collect = n_rem / max(rate * pi_hi, 1e-9)
            horizon = T - t - delay - collect
            if horizon * g_eff <= cs:
                return False  # its release comes after the last moment a verdict is worth c_s
        if not self.shadow:
            return True
        value = max(0.0, g_eff * horizon - cs) / n_rem
        spend_rate = (pol.c_B - rem + PRIOR_W * pol.c_B / T) / (t + PRIOR_W)
        demand = spend_rate * (T - t)
        lam = cq * max(1.0, demand / max(rem, 1)) ** self.gamma
        return value >= lam

    def _verdict_q(self, pol, t, rem, rate):
        """C4: spend the remaining budget evenly up to the projected verdict time, not up to T."""
        T = pol.c_T
        if pol.c_n_rel < self.n0:
            tau = T
        else:
            _, g_hat, g_lo, g_hi = self.stats(pol, t)
            hw = max((g_hi - g_lo) / 2.0, 1e-9)
            g_eff = abs(g_hat)  # either verdict ends acquisition
            n_ev = max(pol.n_ingested, 1)
            if g_eff <= 1e-9:
                tau = T
            else:
                ev_tot = n_ev * (hw / g_eff) ** (1.0 / (self.beta or pol.c_beta))
                tau = min(T, t + pol.c_delay + self.k * max(ev_tot - n_ev, 0.0))
        left = max(rate * max(tau - t, 1.0), 1e-9)
        return float(min(max(rem / left, pol.p_min), 1.0))


# =============================================================================== host mixin
class _Ctl:
    """Mixin over a ``_CertificateStop`` host: controller-driven (pi, q), frozen at issue."""

    c_beta = 0.5  # assumed CS width decay exponent in recorded events (C4 projection)

    def _c_init(self, T, B, cs, cq, delay, ctl):
        self.c_T, self.c_B, self.c_cs, self.c_cq, self.c_delay = T, B, cs, cq, delay
        self.ctl = ctl
        self.c_n_rel = 0
        self.c_sum_z = 0.0
        self.c_issue_q: dict[int, float] = {}  # event -> issue-time q (test hook)

    def request_labels(self, event, remaining_budget):
        if self.stopped:
            return QueryRequest(requested=False)
        self._on_event_start(event)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        t = event.t
        pi, q = self.ctl.decide(self, t, remaining_budget, dis)
        self.acq.note_event(dis)
        if self.stopped or self.exhausted:
            return QueryRequest(requested=False)
        if dis and remaining_budget <= 0:  # same freeze as the host
            self.exhausted = True
            return QueryRequest(requested=False)
        if pi < 1.0 and not (pi > 0.0 and self.rng.random() < pi):
            return QueryRequest(requested=False)  # unrecorded event (predictable coin)
        if not dis:
            self._c_record_agree(t)
            self._queue.append(_Rec(t, True, 1.0, 0))
            self._flush()
            return QueryRequest(requested=False)
        q = float(min(max(q, self.c_qfloor()), 1.0))
        self._c_record_dis(t, q)  # freeze any host bet range before drawing the query indicator
        take = bool(self.rng.random() < q)
        rec = _Rec(t, not take, 0.0, 0)
        self._queue.append(rec)
        if take:
            self._pending[t] = rec
            self.c_issue_q[t] = q
        else:
            self._flush()
        return QueryRequest(requested=take, probability=q)

    def observe(self, feedback):
        for fb in feedback:
            if fb.event_id in self._pending:
                d = int(fb.model_losses[0]) - int(fb.model_losses[1])
                self.c_n_rel += 1
                self.c_sum_z += (d + 1) / 2.0
        super().observe(feedback)

    # host-specific hooks
    def c_qfloor(self):
        return 1e-9

    def _c_record_agree(self, t):
        pass

    def _c_record_dis(self, t, q):
        pass

    def c_phase2(self, rem, exp_left):
        raise NotImplementedError

    def c_skip(self, action, explore):
        raise NotImplementedError


class GatedC(_Ctl, GatedAdaptiveRange):
    def __init__(self, T, B, alpha, cs, cq, delay, ctl, *, rng, name):
        GatedAdaptiveRange.__init__(self, T, B, alpha, rng=rng, name=name)
        self._c_init(T, B, cs, cq, delay, ctl)

    def _c_record_agree(self, t):
        self._wmax[t] = 2.0  # agreement: w = 1 exactly

    def _c_record_dis(self, t, q):
        self._wmax[t] = max(1.0 / q, 2.0)  # frozen at issue, used by the CS bet for this step

    def c_phase2(self, rem, exp_left):
        return (min(rem / exp_left, 1.0), 1.0)  # protected phase: thin uniformly, q = 1

    def c_skip(self, action, explore):
        if (action or "unrecorded") == "unrecorded":
            return (explore, 1.0)
        return (1.0, self.p_min)


class DiscernC(_Ctl, DiscernStyleStop):
    c_beta = 1.0  # PrPl-EB with lam_max binding: width ~ 1/t

    def __init__(self, T, B, alpha, cs, cq, delay, ctl, *, rng, name, p_min=0.25):
        DiscernStyleStop.__init__(self, T, B, alpha, 0.0, rng=rng, p_min=p_min, name=name)
        self._c_init(T, B, cs, cq, delay, ctl)

    def c_qfloor(self):
        return self.p_min  # |Z| <= c = 1/pi_min must hold

    def c_phase2(self, rem, exp_left):
        return (1.0, min(max(rem / exp_left, self.p_min), 1.0))

    def c_skip(self, action, explore):
        if (action or "floor") == "floor":
            return (1.0, self.p_min)
        return (explore, 1.0)


# =============================================================================== C3 on QSG
class QSGTwoStage(QSG):
    """C3: QSG with a concentrated first phase (q = 1 on disagreements while undecided, at most
    ``f*B`` labels and only before ``tau*T``) and a protected monitoring phase that paces the
    remainder uniformly over the rest of the horizon (verdict or not). QSG ingests queried
    outcomes with weight one, so any predictable q is valid (QCE null)."""

    def __init__(self, T, B, alpha, *, rng, f=0.75, tau=1.0, name="C3"):
        super().__init__(T, B, alpha, rng=rng, reserve=1.0 - f, name=name)
        self.f, self.tau = f, tau

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        spent = self.B - remaining_budget
        if not self.decided and spent < self.f * self.B and event.t < self.tau * self.T:
            q = 1.0
        take = bool(self.rng.random() < q)
        return QueryRequest(requested=take, probability=q if take else 0.0)


# =============================================================================== registry
def _g(ctl_kw, name):
    return lambda T, B, cs, cq, a, d, r: GatedC(
        T, B, a, cs, cq, d, Controller(**ctl_kw), rng=r("gated_deployment"), name=name
    )


def _dz(ctl_kw, name, p_min=0.25):
    return lambda T, B, cs, cq, a, d, r: DiscernC(
        T, B, a, cs, cq, d, Controller(**ctl_kw), rng=r("discern_style"), name=name, p_min=p_min
    )


def _q(f, tau, name):
    return lambda T, B, cs, cq, a, d, r: QSGTwoStage(T, B, a, rng=r("QSG"), f=f, tau=tau, name=name)


# ---- tuned values (declared; chosen on DEV_SEED_BASE=2026110501, 20 seeds, see tuning.json)
TUNED = {
    "gated_pace": {"base": "frontfrac", "f": 1.0},  # placeholder, overwritten after tuning
    "discern_pace": {"base": "k", "k": 1.0},
    "C1_kappa": 1.0,
    "C2_gamma": 1.0,
    "C2_zeta": 0.5,
    "C3_f": 0.75,
    "C3_tau": 1.0,
    "C4_k": 1.0,
    "C6_f2": 0.75,
}
try:  # tuned values are written by the tuning step (docs/sota_sprint/family_c/tuned.json)
    import json as _json

    _tf = ROOT / "docs/sota_sprint/family_c/tuned.json"
    if _tf.exists():
        TUNED.update(_json.loads(_tf.read_text()))
except (OSError, _json.JSONDecodeError) as exc:  # pragma: no cover
    warnings.warn(
        f"Could not read optional Family C tuning file: {exc}", RuntimeWarning, stacklevel=2
    )

EXTRA: dict = {}

# ---- non-uniform pacing grids (tuning) and the tuned baselines
for _k in (1.5, 2.0, 3.0, 4.0, 6.0):
    EXTRA[f"gated_adaptive_range+pace_k{_k:g}"] = _g(
        {"base": "k", "k": _k}, f"gated_adaptive_range+pace_k{_k:g}"
    )
    EXTRA[f"discern_design_floor+pace_k{_k:g}"] = _dz(
        {"base": "k", "k": _k}, f"discern_design_floor+pace_k{_k:g}"
    )
for _f in (0.25, 0.5, 0.75):
    EXTRA[f"gated_adaptive_range+frontfrac{_f:g}"] = _g(
        {"base": "frontfrac", "f": _f}, f"gated_adaptive_range+frontfrac{_f:g}"
    )
    EXTRA[f"discern_design_floor+frontfrac{_f:g}"] = _dz(
        {"base": "frontfrac", "f": _f}, f"discern_design_floor+frontfrac{_f:g}"
    )
EXTRA["gated_adaptive_range+pace_tuned"] = _g(
    TUNED["gated_pace"], "gated_adaptive_range+pace_tuned"
)
EXTRA["discern_design_floor+pace_tuned"] = _dz(
    TUNED["discern_pace"], "discern_design_floor+pace_tuned"
)
# exact re-implementations of host acquisition (tests: must equal the host)
EXTRA["Cchk:gated_uniform"] = _g({"base": "uniform"}, "Cchk:gated_uniform")
EXTRA["Cchk:gated_front"] = _g({"base": "front"}, "Cchk:gated_front")
EXTRA["Cchk:discern_uniform"] = _dz({"base": "uniform"}, "Cchk:discern_uniform")

_kap, _gam, _zet = TUNED["C1_kappa"], TUNED["C2_gamma"], TUNED["C2_zeta"]
# ---- C1: front + pending-label credit
EXTRA["C1"] = _g({"base": "front", "credit": True, "kappa": _kap}, "C1")
EXTRA["C1-uniformbase"] = _g({"base": "uniform", "credit": True, "kappa": _kap}, "C1-uniformbase")
for _kk in (1.0, 1.5, 2.0, 3.0, 4.0):
    EXTRA[f"C1-k{_kk:g}"] = _g({"base": "front", "credit": True, "kappa": _kk}, f"C1-k{_kk:g}")
# ---- C2: front + shadow price
EXTRA["C2"] = _g({"base": "front", "shadow": True, "gamma": _gam, "zeta": _zet}, "C2")
EXTRA["C2-noadapt"] = _g(
    {"base": "front", "shadow": True, "gamma": 0.0, "zeta": _zet}, "C2-noadapt"
)
EXTRA["C2-floorskip"] = _g(
    {"base": "front", "shadow": True, "gamma": _gam, "zeta": _zet, "skip_action": "floor"},
    "C2-floorskip",
)
for _gg in (0.0, 1.0, 2.0, 3.0):
    for _zz in (0.1, 0.25, 0.5, 1.0):
        EXTRA[f"C2-g{_gg:g}z{_zz:g}"] = _g(
            {"base": "front", "shadow": True, "gamma": _gg, "zeta": _zz}, f"C2-g{_gg:g}z{_zz:g}"
        )
# ---- C3: QSG two-stage
EXTRA["C3"] = _q(TUNED["C3_f"], TUNED["C3_tau"], "C3")
for _f in (0.4, 0.6, 0.75, 1.0):
    for _tau in (0.3, 0.5, 1.0):
        EXTRA[f"C3-f{_f:g}t{_tau:g}"] = _q(_f, _tau, f"C3-f{_f:g}t{_tau:g}")
# ---- C4: corrected DISCERN + verdict-horizon pacing
EXTRA["C4"] = _dz({"base": "verdict", "k": TUNED["C4_k"], "beta": TUNED.get("C4_beta")}, "C4")
for _kk in (0.5, 1.0, 2.0):
    EXTRA[f"C4-k{_kk:g}"] = _dz({"base": "verdict", "k": _kk}, f"C4-k{_kk:g}")
for _kk in (0.5, 1.0, 2.0):
    EXTRA[f"C4-b0.5k{_kk:g}"] = _dz({"base": "verdict", "k": _kk, "beta": 0.5}, f"C4-b0.5k{_kk:g}")
EXTRA["C4-style"] = _dz({"base": "verdict", "k": TUNED["C4_k"]}, "C4-style", p_min=0.05)
# ---- C5 = C1 + C2
EXTRA["C5"] = _g(
    {"base": "front", "credit": True, "kappa": _kap, "shadow": True, "gamma": _gam, "zeta": _zet},
    "C5",
)
# ---- C6 = shadow price + two-stage + deadline-aware value (gated), and transfer to DISCERN
_c6 = {
    "base": "front",
    "shadow": True,
    "gamma": _gam,
    "zeta": _zet,
    "deadline": True,
    "two_stage": TUNED["C6_f2"],
}
EXTRA["C6"] = _g(_c6, "C6")
EXTRA["C6@discern"] = _dz(_c6, "C6@discern")
EXTRA["C6@discern-unrecorded"] = _dz({**_c6, "skip_action": "unrecorded"}, "C6@discern-unrecorded")
EXTRA["C6-no_deadline"] = _g({**_c6, "deadline": False}, "C6-no_deadline")
EXTRA["C6-no_shadow"] = _g({**_c6, "shadow": False}, "C6-no_shadow")
EXTRA["C6-no_two_stage"] = _g({**_c6, "two_stage": None}, "C6-no_two_stage")
for _f2 in (0.5, 0.75, 0.9):
    EXTRA[f"C6-f{_f2:g}"] = _g({**_c6, "two_stage": _f2}, f"C6-f{_f2:g}")


# =============================================================================== tuning CLI
_GRIDS = {  # tuned key -> (policy-name prefix(es), parser of the grid point)
    "gated_pace": (("gated_adaptive_range+pace_k", "gated_adaptive_range+frontfrac"), None),
    "discern_pace": (("discern_design_floor+pace_k", "discern_design_floor+frontfrac"), None),
    "C1": (("C1-k",), None),
    "C2": (("C2-g",), None),
    "C3": (("C3-f",), None),
    "C4": (("C4-k", "C4-b"), None),
    "C6": (("C6-f",), None),
}


_HOST_POINTS = {
    "gated_pace": {
        "gated_adaptive_range": {"base": "uniform"},
        "gated_adaptive_range+front": {"base": "front"},
    },
    "discern_pace": {
        "discern_design_floor": {"base": "uniform"},
        "discern_design_floor+front": {"base": "front"},
    },
}


def _point(name: str) -> dict:
    import re

    for pts in _HOST_POINTS.values():
        if name in pts:
            return dict(pts[name])
    if "+pace_k" in name:
        return {"base": "k", "k": float(name.split("+pace_k")[1])}
    if "+frontfrac" in name:
        return {"base": "frontfrac", "f": float(name.split("+frontfrac")[1])}
    m = re.fullmatch(r"C1-k([\d.]+)", name)
    if m:
        return {"C1_kappa": float(m[1])}
    m = re.fullmatch(r"C2-g([\d.]+)z([\d.]+)", name)
    if m:
        return {"C2_gamma": float(m[1]), "C2_zeta": float(m[2])}
    m = re.fullmatch(r"C3-f([\d.]+)t([\d.]+)", name)
    if m:
        return {"C3_f": float(m[1]), "C3_tau": float(m[2])}
    m = re.fullmatch(r"C4-k([\d.]+)", name)
    if m:
        return {"C4_k": float(m[1]), "C4_beta": None}
    m = re.fullmatch(r"C4-b([\d.]+)k([\d.]+)", name)
    if m:
        return {"C4_k": float(m[2]), "C4_beta": float(m[1])}
    m = re.fullmatch(r"C6-f([\d.]+)", name)
    if m:
        return {"C6_f2": float(m[1])}
    raise ValueError(name)


def tune(records_dir: str, out: str) -> dict:
    """Pick each grid's point minimising the mean (over regimes) of mean net cost, dev seeds only.

    Host pacing grids also include the host's own uniform pacing (k = 1) as a grid point, so a
    tuned baseline can never be worse in-sample than its host on the tuning set.
    """
    import json

    import pandas as pd

    df = pd.concat(
        [pd.read_json(Path(d) / "records.jsonl", lines=True) for d in records_dir.split(",")],
        ignore_index=True,
    )
    score = df.groupby(["policy", "regime"]).net.mean().groupby("policy").mean()
    tuned, table = {}, {}
    for key, (prefixes, _) in _GRIDS.items():
        cand = [p for p in score.index if p.startswith(prefixes) or p in _HOST_POINTS.get(key, {})]
        if not cand:
            continue
        best = min(cand, key=lambda p: score[p])
        table[key] = {p: round(float(score[p]), 2) for p in sorted(cand)}
        pt = _point(best)
        if key in ("gated_pace", "discern_pace"):
            tuned[key] = pt
        else:
            tuned.update(pt)
        table[key]["_selected"] = best
    meta = {
        "tuned": tuned,
        "grid_scores_mean_net_over_regimes": table,
        "regimes": sorted(df.regime.unique()),
        "seeds": int(df.seed.nunique()),
        "seed_base": "DEV_SEED_BASE=2026110501",
        "source": records_dir,
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(tuned, indent=1) + "\n")
    Path(out).with_name("tuning.json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


CONTRASTS = {  # candidate -> named comparators for paired contrasts
    "C1": {
        "host": "gated_adaptive_range+front",
        "uniform_host": "gated_adaptive_range",
        "tuned_pacing": "gated_adaptive_range+pace_tuned",
        "QSG": "QSG",
    },
    "C2": {
        "host": "gated_adaptive_range",
        "front": "gated_adaptive_range+front",
        "tuned_pacing": "gated_adaptive_range+pace_tuned",
        "QSG": "QSG",
    },
    "C3": {"host": "QSG", "tuned_pacing": "QSG-r25", "front": "gated_adaptive_range+front"},
    "C4": {
        "host": "discern_design_floor",
        "front": "discern_design_floor+front",
        "tuned_pacing": "discern_design_floor+pace_tuned",
        "style": "discern_style",
    },
    "C5": {
        "host": "gated_adaptive_range",
        "front": "gated_adaptive_range+front",
        "tuned_pacing": "gated_adaptive_range+pace_tuned",
        "C2": "C2",
        "QSG": "QSG",
    },
    "C6": {
        "host": "gated_adaptive_range",
        "front": "gated_adaptive_range+front",
        "tuned_pacing": "gated_adaptive_range+pace_tuned",
        "C2": "C2",
        "QSG": "QSG",
    },
    "C6@discern": {
        "host": "discern_design_floor",
        "front": "discern_design_floor+front",
        "tuned_pacing": "discern_design_floor+pace_tuned",
        "C4": "C4",
    },
}
ABLATIONS = {
    "C1": ["C1-k1", "C1-k1.5", "C1-k2", "C1-uniformbase"],
    "C2": ["C2-noadapt", "C2-floorskip", "C2-g0z0.1", "C2-g1z0.5", "C2-g3z1"],
    "C3": ["C3-f0.4t0.3", "C3-f0.6t0.5", "C3-f0.75t1", "C3-f1t0.3", "QSG-r25"],
    "C4": ["C4-k0.5", "C4-k1", "C4-k2", "C4-b0.5k0.5", "C4-style"],
    "C5": ["C1", "C2"],
    "C6": ["C6-no_deadline", "C6-no_shadow", "C6-no_two_stage"],
    "C6@discern": ["C6@discern-unrecorded"],
}


def report(dirs: str, out: str) -> dict:
    """Paired contrasts (candidate - comparator) per regime and pooled; gain-source diagnostics."""
    import json

    import pandas as pd

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bench import CERTIFIED_PUBLISHED

    df = pd.concat(
        [pd.read_json(Path(d) / "records.jsonl", lines=True) for d in dirs.split(",")],
        ignore_index=True,
    )
    df = df.drop_duplicates(["regime", "ep", "seed", "policy"])
    piv = df.pivot_table(index=["regime", "ep", "seed"], columns="policy", values="net")

    def pc(a, b, regs=None):
        if a not in piv or b not in piv:
            return None
        x = piv if regs is None else piv.loc[piv.index.get_level_values(0).isin(regs)]
        d = (x[a] - x[b]).dropna().to_numpy()
        if len(d) < 2:
            return None
        se = d.std(ddof=1) / np.sqrt(len(d))
        return [
            round(float(d.mean()), 2),
            round(float(d.mean() - 1.96 * se), 2),
            round(float(d.mean() + 1.96 * se), 2),
            len(d),
        ]

    regs = sorted(df.regime.unique())
    means = df.groupby(["regime", "policy"]).net.mean()
    res = {}
    for c, comps in CONTRASTS.items():
        if c not in piv:
            continue
        r = {"pooled": {}, "by_regime": {}, "diagnostics": {}, "ablations": {}}
        for k, b in comps.items():
            r["pooled"][k] = pc(c, b)
        for reg in regs:
            cert = [p for p in CERTIFIED_PUBLISHED if (reg, p) in means.index]
            best = min(cert, key=lambda p: means[(reg, p)])
            cell = {k: pc(c, b, [reg]) for k, b in comps.items()}
            cell["best_certified_published"] = [best] + (pc(c, best, [reg]) or [])
            r["by_regime"][reg] = cell
            g = df[(df.regime == reg) & (df.policy == c)]
            r["diagnostics"][reg] = {
                "net": round(float(g.net.mean()), 2),
                "promote": round(float(g.ever_promote.mean()), 3),
                "labels": round(float(g.labels.mean()), 1),
                "labels_by_500": round(float(g.labels_by_500.mean()), 1),
                "labels_after_1000": round(float(g.labels_after_1000.mean()), 1),
                "exhaust_t": round(float(g.exhaust_t.mean()), 0),
                "max_pending": round(float(g.max_pending.mean()), 1),
                "first_deploy_median": (
                    float(g.first_deploy[g.first_deploy >= 0].median())
                    if (g.first_deploy >= 0).any()
                    else -1
                ),
            }
        for a in ABLATIONS.get(c, []):
            r["ablations"][a] = pc(c, a)
        res[c] = r
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    return res


if __name__ == "__main__":
    import json

    if len(sys.argv) >= 4 and sys.argv[1] == "report":
        r = report(sys.argv[2], sys.argv[3])
        for c, v in r.items():
            print(c, json.dumps(v["pooled"]), json.dumps(v["ablations"]))

    if len(sys.argv) >= 3 and sys.argv[1] == "tune":
        print(
            json.dumps(
                tune(
                    sys.argv[2],
                    sys.argv[3]
                    if len(sys.argv) > 3
                    else str(ROOT / "docs/sota_sprint/family_c/tuned.json"),
                ),
                indent=1,
            )
        )
