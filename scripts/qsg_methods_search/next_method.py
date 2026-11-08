"""Next-method candidates beyond tuned fixed-discount Wald-LCB EQSDp (NEXT_METHOD_PLAN.md).

Every class shares EQSDp's contract: paced disagreement-only acquisition (``stake=False``), the
label clock (evidence updates only on released, disagreeing labels), and the remaining-horizon
payback rule ``adv(p) * r * (T - t) > c_s`` with a Wald confidence bound on
``p = P(challenger correct | disagreement)``. Only the evidence memory or the hurdle changes.

* ``MultiScale`` (Candidate A3, ``mode="select"``): keeps discounted counts at a fast factor
  ``lam_f`` and a slow factor ``lam_s``. If the two estimates are inconsistent,
  ``|p_f - p_s| > zc * sqrt(p_s (1 - p_s) / (n_f + 1))``, the hurdle uses the fast counts; else
  the slow ones.
* ``MultiScale`` (Candidate A1, ``mode="restart"``): one slow memory; when the same
  inconsistency test fires, the slow counts are replaced by the fast counts (two-state
  forgetting: forget the pre-change history once, then accumulate slowly again).
* ``MultiScale`` (Candidate A4, ``mode="leader"``): counts at several factors; the hurdle uses
  the factor whose discounted one-step predictive log-likelihood of the released outcomes is
  highest (follow-the-leader over fixed discounts; ``eta`` discounts the score).
* ``Asym`` (Candidate B1): fixed-discount Wald with separate confidence levels for promotion
  (deployed = incumbent) and rollback (deployed = challenger).

All decisions depend only on released labels and predictions. No future label, regime
identity or change time is used.
"""

from __future__ import annotations

import math

from hurdles import WaldLCB


def _p(k, n):
    return (k + 0.5) / (n + 1.0)


class MultiScale(WaldLCB):
    def __init__(self, *a, lams=(0.85, 0.97), zc=2.0, mode="select", eta=0.98, **kw):
        super().__init__(*a, lam=lams[-1], **kw)
        self.lams, self.zc, self.mode, self.eta = tuple(lams), float(zc), mode, float(eta)
        self.ks = [0.0] * len(self.lams)
        self.ns = [0.0] * len(self.lams)
        self.score = [0.0] * len(self.lams)
        self.use_fast = 0  # diagnostic: number of decisions that used the fast memory

    def _update(self, z):
        for j, lam in enumerate(self.lams):
            if self.mode == "leader":
                pj = _p(self.ks[j], self.ns[j])
                self.score[j] = self.eta * self.score[j] + math.log(pj if z else 1.0 - pj)
            self.ns[j] = lam * self.ns[j] + 1.0
            self.ks[j] = lam * self.ks[j] + z
        if self.mode == "leader":
            j = max(range(len(self.lams)), key=lambda i: self.score[i])
            self.k, self.n = self.ks[j], self.ns[j]
            self.use_fast += int(j < len(self.lams) - 1)
            return
        kf, nf, ks, ns = self.ks[0], self.ns[0], self.ks[-1], self.ns[-1]
        pf, ps = _p(kf, nf), _p(ks, ns)
        incons = abs(pf - ps) > self.zc * math.sqrt(ps * (1.0 - ps) / (nf + 1.0))
        if self.mode == "restart":
            if incons:
                self.ks[-1], self.ns[-1] = kf, nf
                self.use_fast += 1
            self.k, self.n = self.ks[-1], self.ns[-1]
        else:  # select
            self.use_fast += int(incons)
            self.k, self.n = (kf, nf) if incons else (ks, ns)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self._update(float(d > 0))
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs + self.margin:
                self.deployed = 1 - self.deployed


class Asym(WaldLCB):
    def __init__(self, *a, g_pro=0.2, g_rb=0.2, **kw):
        super().__init__(*a, gamma=g_pro, **kw)
        self.g_pro, self.g_rb = float(g_pro), float(g_rb)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + float(d > 0)
            self.t = fb.t_released
            g = self.g_pro if self.deployed == 0 else self.g_rb
            if self._gain_away(g) > self.cs + self.margin:
                self.deployed = 1 - self.deployed


def _mk(cls, nm, **kw):
    return lambda T, B, cs, cq, a, d, r: cls(T, B, cs, rng=r("EQSD"), name=nm, stake=False, **kw)


# --- Stage-2 development registry -------------------------------------------------------------
WALD = {}  # widened fixed-discount Wald grid (the primary comparator family)
for _l in (0.8, 0.85, 0.9, 0.93, 0.95, 0.97):
    for _g in (0.1, 0.15, 0.2, 0.3):
        WALD[f"wald_l{_l}_g{_g}"] = _mk(WaldLCB, f"wald_l{_l}_g{_g}", lam=_l, gamma=_g)

CAND = {}
for _mode, _tag in (("select", "ms"), ("restart", "rs")):
    for _lf in (0.8, 0.85):
        for _ls in (0.95, 0.97):
            for _zc in (1.5, 2.0, 2.5):
                for _g in (0.15, 0.2, 0.3):
                    _n = f"{_tag}_f{_lf}_s{_ls}_z{_zc}_g{_g}"
                    CAND[_n] = _mk(MultiScale, _n, lams=(_lf, _ls), zc=_zc, mode=_mode, gamma=_g)
for _eta in (0.95, 0.99):
    for _g in (0.15, 0.2, 0.3):
        _n = f"ld_e{_eta}_g{_g}"
        CAND[_n] = _mk(
            MultiScale, _n, lams=(0.8, 0.9, 0.95, 0.98), mode="leader", eta=_eta, gamma=_g
        )
for _l in (0.9, 0.93):
    for _gp in (0.1, 0.2, 0.3):
        for _gr in (0.1, 0.2, 0.3, 0.4):
            if _gp != _gr:
                _n = f"asym_l{_l}_p{_gp}_r{_gr}"
                CAND[_n] = _mk(Asym, _n, lam=_l, g_pro=_gp, g_rb=_gr)

EXTRA = {**WALD, **CAND}

from d3_extra import EXTRA as _D3

EXTRA.update(
    {
        k: _D3[k]
        for k in ("EQSDp_l0.9_g0.2", "EQSDp_l0.95_g0.2", "gongT_w100_m10", "qiu_delayed_movement")
    }
)


# --- Stage 2: principled change-adaptive memory and an evaluator-side ceiling ------------------
class BOCPD(WaldLCB):
    """Candidate A5: Bayesian online change-point posterior over p (Adams & MacKay 2007).

    Per-segment Beta(1, 1) prior, constant hazard ``h`` per released disagreement label. The
    hurdle uses a moment-matched quantile of the run-length mixture posterior of the current p:
    ``m + z_lev * sqrt(v)``. Memory length therefore adapts to the evidence: long on stable
    streams, collapsing after a credible change.
    """

    def __init__(self, *a, h=0.02, rmax=400, **kw):
        super().__init__(*a, **kw)
        self.h, self.rmax = float(h), int(rmax)
        self.ra, self.rb, self.rw = [1.0], [1.0], [1.0]

    def _update(self, z):
        h, ra, rb, rw = self.h, self.ra, self.rb, self.rw
        pred = [(a if z else b) / (a + b) for a, b in zip(ra, rb, strict=True)]
        grow = [w * (1 - h) * p for w, p in zip(rw, pred, strict=True)]
        cp = sum(w * h * p for w, p in zip(rw, pred, strict=True))
        na = [1.0 + z] + [a + z for a in ra]
        nb = [2.0 - z] + [b + 1 - z for b in rb]
        nw = [cp] + grow
        if len(nw) > self.rmax:
            na, nb, nw = na[: self.rmax], nb[: self.rmax], nw[: self.rmax]
        s = sum(nw)
        self.ra, self.rb, self.rw = na, nb, [w / s for w in nw]
        m = sum(w * a / (a + b) for w, a, b in zip(self.rw, na, nb, strict=True))
        e2 = sum(
            w * (a * b / ((a + b) ** 2 * (a + b + 1)) + (a / (a + b)) ** 2)
            for w, a, b in zip(self.rw, na, nb, strict=True)
        )
        self.m, self.sd = m, math.sqrt(max(e2 - m * m, 1e-12))
        self.n += 1.0  # diagnostic only

    def _q(self, lev):
        if not hasattr(self, "m"):
            return 0.5
        from scipy.stats import norm

        return min(1.0, max(0.0, self.m + norm.ppf(lev) * self.sd))

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self._update(float(d > 0))
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs + self.margin:
                self.deployed = 1 - self.deployed


class OracleRestart(WaldLCB):
    """EVALUATOR-SIDE DIAGNOSTIC, NOT A METHOD: Wald that resets its counts at the first released
    label whose event time is past a true change time. Bounds what adaptive memory could gain."""

    def __init__(self, *a, cps=(), **kw):
        super().__init__(*a, **kw)
        self.cps, self.last_t = tuple(cps), -1

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            et = int(fb.event_id)
            if any(self.last_t < c <= et for c in self.cps):
                self.n = self.k = 0.0
            self.last_t = max(self.last_t, et)
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + float(d > 0)
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs + self.margin:
                self.deployed = 1 - self.deployed


STAGE2 = {}
for _h in (0.005, 0.01, 0.02, 0.05):
    for _g in (0.1, 0.15, 0.2, 0.3):
        STAGE2[f"bocpd_h{_h}_g{_g}"] = _mk(BOCPD, f"bocpd_h{_h}_g{_g}", h=_h, gamma=_g)

ORACLE = {}


def _oracle_names():
    import sys as _s
    from pathlib import Path as _P

    _s.path.insert(0, str(_P(__file__).resolve().parents[1] / "failure_atlas_v2_flq"))
    from regimes import ALL_REGIMES

    for rn, R in ALL_REGIMES.items():
        cps = tuple(s for s, _ in R.p[1:])
        if not cps:
            continue
        for _l in (0.85, 0.95, 1.0):
            for _g in (0.15, 0.3):
                nm = f"orc_{rn}_l{_l}_g{_g}"
                ORACLE[nm] = _mk(OracleRestart, nm, cps=cps, lam=_l, gamma=_g)


_oracle_names()
EXTRA.update(STAGE2)
EXTRA.update(ORACLE)


# --- Stage 3: evidence windows cut at an estimated change point ---------------------------------
def _ll(k, n):
    if n <= 0 or k <= 0 or k >= n:
        return 0.0
    p = k / n
    return k * math.log(p) + (n - k) * math.log(1.0 - p)


class GLRWin(WaldLCB):
    """Candidate A6: change-point-cut evidence window.

    Keeps the released disagreement outcomes since the last cut. After each label, the Bernoulli
    GLR statistic for one change at any split with both sides >= ``mseg`` labels is computed;
    if it exceeds ``c``, the window is cut at the maximising split, so the hurdle afterwards
    uses exactly the labels estimated to be post-change. Inside the window outcomes are
    discounted by ``lam`` per label (lam=1: plain counts). The hurdle is the same Wald bound.
    """

    def __init__(self, *a, c=3.0, mseg=3, wmax=400, **kw):
        super().__init__(*a, **kw)
        self.c, self.mseg, self.wmax = float(c), int(mseg), int(wmax)
        self.buf = []
        self.cuts = 0

    def _recount(self):
        n = k = 0.0
        for z in self.buf:
            n = self.lam * n + 1.0
            k = self.lam * k + z
        self.n, self.k = n, k

    def _update(self, z):
        self.buf.append(z)
        if len(self.buf) > self.wmax:
            self.buf.pop(0)
        L = len(self.buf)
        if L >= 2 * self.mseg:
            tot = sum(self.buf)
            ll_all = _ll(tot, L)
            best, arg, kl = 0.0, None, 0.0
            for s in range(1, L):
                kl += self.buf[s - 1]
                if s < self.mseg or L - s < self.mseg:
                    continue
                g = _ll(kl, s) + _ll(tot - kl, L - s) - ll_all
                if g > best:
                    best, arg = g, s
            if arg is not None and best > self.c:
                self.buf = self.buf[arg:]
                self.cuts += 1
        self._recount()

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self._update(float(d > 0))
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs + self.margin:
                self.deployed = 1 - self.deployed


class BOCPDMap(BOCPD):
    """Candidate A5b: BOCPD, hurdle from the Wald bound on the MAP run-length segment."""

    def _update(self, z):
        super()._update(z)
        j = max(range(len(self.rw)), key=lambda i: self.rw[i])
        a, b = self.ra[j], self.rb[j]
        self.k, self.n = a - 1.0, a + b - 2.0

    def _q(self, lev):
        return WaldLCB._q(self, lev)


STAGE3 = {}
for _c in (2.0, 3.0, 4.0, 6.0):
    for _l in (1.0, 0.97):
        for _g in (0.15, 0.2, 0.3):
            _n = f"glr_c{_c}_l{_l}_g{_g}"
            STAGE3[_n] = _mk(GLRWin, _n, c=_c, lam=_l, gamma=_g)
for _h in (0.01, 0.02, 0.05):
    for _g in (0.15, 0.2, 0.3):
        _n = f"bmap_h{_h}_g{_g}"
        STAGE3[_n] = _mk(BOCPDMap, _n, h=_h, gamma=_g)
for _l in (0.97, 1.0):  # long-memory Wald references (what the window degenerates to)
    for _g in (0.15, 0.2, 0.3):
        STAGE3[f"wald_l{_l}_g{_g}"] = _mk(WaldLCB, f"wald_l{_l}_g{_g}", lam=_l, gamma=_g)
EXTRA.update(STAGE3)


# --- Stage 4: decision-ambiguity acquisition (Candidate D) -------------------------------------
class AmbiguityBurst(WaldLCB):
    """Candidate D1: buy labels when they can flip the economic decision.

    The decision is *ambiguous* when the point estimate of p favours switching away from the
    deployed model by more than ``m`` (``p_hat_dir > 0.5 + m``) but the Wald bound does not yet
    pay back. Then every disagreement is queried (q=1); otherwise the shared budget pacer's
    propensity is multiplied by ``rho`` (<=1 builds a reserve; the pacer re-spreads whatever is
    left, so the hard budget always holds). Same evidence, hurdle and payback as Wald.
    """

    def __init__(self, *a, m=0.1, rho=0.8, **kw):
        super().__init__(*a, **kw)
        self.m, self.rho = float(m), float(rho)
        self.bursts = 0

    def _ambiguous(self):
        p = (self.k + 0.5) / (self.n + 1.0)
        pd_ = p if self.deployed == 0 else 1.0 - p
        return pd_ > 0.5 + self.m and self._gain_away(self.gamma) <= self.cs + self.margin

    def request_labels(self, event, remaining_budget):
        from simulator import QueryRequest

        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if self._ambiguous():
            q, self.bursts = 1.0, self.bursts + 1
        else:
            q = min(1.0, q * self.rho)
        if q <= 0.0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        self.pending += int(take)
        return QueryRequest(requested=take, probability=q if take else 0.0)


STAGE4 = {}
for _l in (0.85, 0.9):
    for _g in (0.15, 0.2):
        for _m in (0.0, 0.1, 0.2):
            for _r in (0.6, 0.8, 1.0):
                _n = f"amb_l{_l}_g{_g}_m{_m}_r{_r}"
                STAGE4[_n] = _mk(AmbiguityBurst, _n, lam=_l, gamma=_g, m=_m, rho=_r)
EXTRA.update(STAGE4)


# --- Stage 5: label-free sentinel-gated evidence reset and label burst (Candidate S) -----------
class Sentinel(WaldLCB):
    """Candidate S: SGR, sentinel-gated reset.

    A label-free sentinel watches the disagreement indicator on *every* event (predictions are
    observable before any label). It alarms when the disagreement rate in the last ``W`` events
    differs from the rate since the previous alarm (excluding those ``W``) by more than
    ``z`` binomial standard errors; after an alarm it waits ``W`` events before testing again.
    On an alarm: (i) the discounted evidence counts are shrunk, ``(n, k) <- s * (n, k)``
    (s=0: full reset); (ii) the next ``L`` disagreements are queried with q=1 (the budget pacer
    re-spreads what is left, so the hard budget holds). The switching decision is unchanged
    Wald payback on labels: an alarm alone never switches the deployed model.

    ``random_rate`` > 0 replaces the sentinel by alarms at random times with that per-event
    probability (ablation: does sentinel *timing* matter?).
    """

    def __init__(self, *a, W=150, z=4.0, s=0.0, L=20, random_rate=0.0, **kw):
        super().__init__(*a, **kw)
        self.W, self.z, self.s, self.L = int(W), float(z), float(s), int(L)
        self.random_rate = float(random_rate)
        self.ind = []
        self.ref0 = 0  # index where the current reference segment starts
        self.cool = 0
        self.burst_left = 0
        self.alarms = 0

    def _sentinel(self, dis):
        self.ind.append(int(dis))
        if self.random_rate > 0:
            return bool(self.rng.random() < self.random_rate)
        if self.cool > 0:
            self.cool -= 1
            return False
        i = len(self.ind)
        nref = i - self.W - self.ref0
        if nref < self.W:
            return False
        rw = sum(self.ind[i - self.W :]) / self.W
        rr = sum(self.ind[self.ref0 : i - self.W]) / nref
        pp = min(max(rr, 0.02), 0.98)
        se = math.sqrt(pp * (1 - pp) * (1.0 / self.W + 1.0 / nref))
        if abs(rw - rr) > self.z * se:
            self.ref0, self.cool = i - self.W, self.W
            return True
        return False

    def request_labels(self, event, remaining_budget):
        from simulator import QueryRequest

        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        if self._sentinel(dis):
            self.alarms += 1
            self.n, self.k = self.s * self.n, self.s * self.k
            self.burst_left = self.L
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        if self.burst_left > 0:
            q, self.burst_left = 1.0, self.burst_left - 1
        if q <= 0.0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        self.pending += int(take)
        return QueryRequest(requested=take, probability=q if take else 0.0)


def _register_sentinel_regimes():
    """S-family: label-free sentinel informative (coupled), misleading (false) or silent."""
    import sys as _s
    from pathlib import Path as _P

    _s.path.insert(0, str(_P(__file__).resolve().parents[1] / "failure_atlas_v2_flq"))
    import regimes as _rg

    R = _rg.Regime
    new = [
        R(
            "S1_late_cpl",
            "late",
            ((0, 0.4), (800, 0.7)),
            dis=((0, 0.2), (800, 0.3)),
            tags=("alt", "change", "cpl"),
        ),
        R(
            "S2_rev_cpl",
            "reversal",
            ((0, 0.7), (1000, 0.3)),
            dis=((0, 0.2), (1000, 0.3)),
            tags=("change", "cpl"),
        ),
        R(
            "S3_rec_cpl",
            "recurrent",
            ((0, 0.7), (500, 0.32), (1000, 0.7), (1500, 0.32)),
            dis=((0, 0.2), (500, 0.3), (1000, 0.2), (1500, 0.3)),
            tags=("change", "cpl"),
        ),
        R(
            "S4_trans_cpl",
            "transient",
            ((0, 0.4), (300, 0.72), (1100, 0.4)),
            dis=((0, 0.2), (300, 0.3), (1100, 0.2)),
            tags=("change", "cpl"),
        ),
        R(
            "S5_late_cpl_dn",
            "late",
            ((0, 0.4), (600, 0.7)),
            dis=((0, 0.25), (600, 0.15)),
            tags=("alt", "change", "cpl"),
        ),
        R(
            "S6_false_null",
            "stationary",
            ((0, 0.5),),
            dis=((0, 0.2), (700, 0.3)),
            tags=("null", "false"),
        ),
        R(
            "S7_false_better",
            "stationary",
            ((0, 0.65),),
            dis=((0, 0.2), (700, 0.3)),
            tags=("alt", "false"),
        ),
        R(
            "S8_false_worse",
            "stationary",
            ((0, 0.4),),
            dis=((0, 0.2), (600, 0.3), (1300, 0.2)),
            tags=("null", "false"),
        ),
        R("S9_silent_rev", "reversal", ((0, 0.7), (1000, 0.3)), tags=("change", "silent")),
        R("S10_silent_late", "late", ((0, 0.4), (800, 0.7)), tags=("alt", "change", "silent")),
    ]
    for r in new:
        _rg.ALL_REGIMES.setdefault(r.name, r)
    return [r.name for r in new]


S_REGIMES = _register_sentinel_regimes()

STAGE5 = {}
for _l in (0.85, 0.9, 0.95):
    for _g in (0.15, 0.2):
        for _W in (150, 300):
            for _z in (2.5, 3.5):
                for _L in (0, 20):
                    _n = f"sgr_l{_l}_g{_g}_W{_W}_z{_z}_L{_L}"
                    STAGE5[_n] = _mk(Sentinel, _n, lam=_l, gamma=_g, W=_W, z=_z, s=0.0, L=_L)
EXTRA.update(STAGE5)


# --- Stage 6: dependence-adjusted Wald hurdle (Candidate M4-ESS) --------------------------------
class DepWald(WaldLCB):
    """Candidate E: effective-sample-size Wald hurdle.

    Estimates the lag-1 autocorrelation r of successive released disagreement outcomes from
    discounted pair counts (factor ``lam_r``, prior ``r_prior`` pseudo-pairs at r=0) and widens
    the Wald standard error by sqrt((1+r)/(1-r)) for r in [0, r_cap]. With independent outcomes
    r ~ 0 and the rule is the plain Wald rule (ablation: r forced to 0).
    """

    def __init__(self, *a, lam_r=0.98, r_cap=0.9, r_prior=10.0, **kw):
        super().__init__(*a, **kw)
        self.lam_r, self.r_cap, self.r_prior = float(lam_r), float(r_cap), float(r_prior)
        self.prev = None
        self.c11 = self.c1x = self.cx1 = self.cp = 0.0
        self.r = 0.0

    def _q(self, lev):
        from scipy.stats import norm

        n = max(self.n, 1e-9)
        p = (self.k + 0.5) / (n + 1.0)
        f = (1.0 + self.r) / (1.0 - self.r)
        se = math.sqrt(f * p * (1 - p) / (n + 1.0))
        return min(1.0, max(0.0, p + norm.ppf(lev) * se))

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            z = float(d > 0)
            if self.prev is not None:
                lr = self.lam_r
                self.cp = lr * self.cp + 1.0
                self.c11 = lr * self.c11 + self.prev * z
                self.c1x = lr * self.c1x + self.prev
                self.cx1 = lr * self.cx1 + z
                pa, pb = self.c1x / self.cp, self.cx1 / self.cp
                cov = self.c11 / self.cp - pa * pb
                var = math.sqrt(max(pa * (1 - pa) * pb * (1 - pb), 1e-9))
                r = (cov / var) * self.cp / (self.cp + self.r_prior)
                self.r = min(self.r_cap, max(0.0, r))
            self.prev = z
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + z
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs + self.margin:
                self.deployed = 1 - self.deployed


STAGE6 = {}
for _l in (0.85, 0.9):
    for _g in (0.15, 0.2):
        for _lr in (0.97, 0.99):
            for _rp in (5.0, 20.0):
                _n = f"dep_l{_l}_g{_g}_lr{_lr}_rp{_rp}"
                STAGE6[_n] = _mk(DepWald, _n, lam=_l, gamma=_g, lam_r=_lr, r_prior=_rp)
EXTRA.update(STAGE6)


# --- Stage 7: Bayes-filter payback (hazard-aware horizon; Bayes-myopic benchmark) ---------------
class BayesPay(BOCPD):
    """Candidate F: BOCPD posterior on p with a hazard-aware payback horizon.

    Per-event change hazard ``h_ev``; per-label hazard h = h_ev * T / B (labels arrive at about
    B/T per event). After a change p is redrawn with prior mean 1/2 (advantage 0), so the
    expected remaining-horizon advantage is adv * H_eff with
    H_eff = (1 - (1 - h_ev)^(T - t)) / h_ev. ``gamma=0.5`` is the risk-neutral Bayes rule.
    """

    def __init__(self, *a, h_ev=0.002, **kw):
        T, B = a[0], a[1]
        super().__init__(*a, h=min(0.5, h_ev * T / B), **kw)
        self.h_ev = float(h_ev)

    def _gain_away(self, lev):
        p = self._q(lev if self.deployed == 0 else 1.0 - lev)
        adv = (2 * p - 1) if self.deployed == 0 else (1 - 2 * p)
        rem = self.T - self.t
        H = (1.0 - (1.0 - self.h_ev) ** rem) / self.h_ev
        return adv * self._rate() * H


STAGE7 = {}
for _h in (0.001, 0.002, 0.004):
    for _g in (0.5, 0.35, 0.2):
        _n = f"bpay_h{_h}_g{_g}"
        STAGE7[_n] = _mk(BayesPay, _n, h_ev=_h, gamma=_g)
EXTRA.update(STAGE7)


# --- Stage 8: off-policy-evaluated selection over shadow switchers (Candidate G) ----------------
class OPESelect(WaldLCB):
    """Candidate G: OPE-selected switching.

    Runs a grid of shadow Wald payback switchers (different evidence memories ``lams``) on the
    shared label stream. Acquisition is the shared budget pacer, which does not depend on any
    deployment decision, so every queried disagreement has a known, decision-independent
    propensity q. For each shadow j the realised economic cost to date is estimated without
    bias: each released queried disagreement adds loss(model deployed by j at that event) / q,
    and each shadow switch adds c_s exactly (agreements add the same to every shadow and are
    dropped). Scores are discounted by ``eta`` per release. The deployed model is the current
    leader's deployment; the leader changes only when another shadow's score is lower by more
    than ``m`` (hysteresis). Only released labels and logged propensities are used.
    """

    def __init__(self, *a, lams=(0.85, 0.9, 0.95, 0.97), m=5.0, eta=1.0, start=None, **kw):
        super().__init__(*a, **kw)
        T, B, cs = a[0], a[1], a[2]
        self.sh = [
            WaldLCB(T, B, cs, rng=self.rng, lam=lam, gamma=self.gamma, stake=False) for lam in lams
        ]
        self.score = [0.0] * len(lams)
        self.m, self.eta = float(m), float(eta)
        self.lead = len(lams) // 2 if start is None else int(start)
        self.log = {}  # event_id -> (q, shadow deployments at the event)

    def predict(self, event):
        self.t = event.t
        for s in self.sh:
            s.t = event.t
        return self.sh[self.lead].deployed

    def request_labels(self, event, remaining_budget):
        from simulator import QueryRequest

        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        for s in self.sh:
            s.acq.note_event(dis)
        if not dis or remaining_budget <= 0 or q <= 0.0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        if take:
            self.pending += 1
            self.log[event.event_id] = (q, tuple(s.deployed for s in self.sh))
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def observe(self, feedback):
        fbs = sorted(feedback, key=lambda f: f.event_id)
        for fb in fbs:
            self.pending -= 1
            q, deps = self.log.pop(fb.event_id, (None, None))
            if q is not None:
                for j, dj in enumerate(deps):
                    self.score[j] = self.eta * self.score[j] + float(fb.model_losses[dj]) / q
            for j, s in enumerate(self.sh):
                before = s.deployed
                s.observe([fb])
                if s.deployed != before:
                    self.score[j] += self.cs
        best = min(range(len(self.sh)), key=lambda j: self.score[j])
        if self.score[self.lead] - self.score[best] > self.m:
            self.lead = best
        self.deployed = self.sh[self.lead].deployed


STAGE8 = {}
for _set, _lams in (("A", (0.85, 0.9, 0.95, 0.97)), ("B", (0.85, 0.9, 0.93, 0.95, 0.97, 0.99))):
    for _g in (0.15, 0.2):
        for _m in (0.0, 5.0, 15.0):
            _n = f"ope{_set}_g{_g}_m{_m}"
            STAGE8[_n] = _mk(OPESelect, _n, lams=_lams, gamma=_g, m=_m)
EXTRA.update(STAGE8)
