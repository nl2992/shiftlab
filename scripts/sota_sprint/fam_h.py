"""Sprint-2 Family H: A5b x D2 hybrids (CAMS ranking + deploy gate + dependence-robust evidence).

Central question: can D2's economic advantage (CAMS host ranks and queries; an anytime certificate
gates promotion) coexist with A5b-style dependence control (gap-aware Markov SUI evidence, adaptive
observation spacing)? Diagnosis of why D5 lost power: docs/sprint2/family_h/diagnosis.md.

``HGate`` extends ``fam_d.DeployGate`` with switchable mechanisms (one class, flags select the
mechanism so every ablation is exact):

* ``evidence``: ``"iid"`` (QSG StartedMixture, D2's certificate) or ``"sui"`` (fam_a.MarkovSUI with
  ``sui_kw``, default A5b's ``fam_a._B``; the ``last`` outcome of the whole stream is carried).
* ``single_cycle``: when promotion is absorbing (no rollback) only one promotion cycle can ever run,
  so the promotion threshold is ``1/alpha`` instead of DeployGate's cycle-1 ``2/alpha``. With
  rollback the cycle-j threshold is ``2^j/alpha`` (sum over cycles <= alpha).
* ``spacing``: A5b adaptive observation spacing. While the promotion test is open, a disagreement
  is queried (host draw or gate draw) only if the event gap since the last issued query is at least
  ``g* = ceil(log c / log rho_hat)``, ``rho_hat`` = fam_a.rho_mle (sig = 2 nats shrinkage) on the
  last 150 released outcomes. Deterministic in released labels and issue times: predictable.
* ``shadow``: C2-style value-of-label vs adaptive shadow price of budget (fam_c Controller logic,
  re-expressed on the gate's own released outcomes). A pre-decision query is issued only if
  ``max(0, g_eff (T - t - delay) - c_s) / n_rem >= c_q max(1, demand/remaining)^gamma``.
* ``dualclock``: event / request / release times kept separate. (i) In-flight awareness: gate
  front-loading pauses while issued-but-unreleased outcomes already exceed ``margin x`` the
  projected number of further outcomes the open test needs. (ii) Deadline: no query whose release
  time ``t + delay`` leaves fewer than ``c_s / g_hi`` events (a promotion released later cannot repay
  the switch); a label released at or after T is never requested. (iii) Segment semantics: a new
  test after a verdict starts at the next outcome in event (issue) order, not at the release time,
  so in-flight outcomes are used (each new test is a fresh e-process from that index).
* ``rollback`` / ``reserve`` / ``alpha_r``: after promotion a mirrored test (H-) on outcomes issued
  after the promotion verdict, at level ``alpha_r`` per cycle, rolls back; the next promotion cycle
  runs at ``alpha / 2^cycle``. ``reserve`` withholds a fraction of the budget from all
  pre-promotion queries for post-promotion monitoring.

Validity (stated per null; nothing beyond this is claimed)
---------------------------------------------------------
Every query decision is predictable: the CAMS host's u_t is a function of labels released before t
and of event t's predictions; the gate's decisions (front-load, spacing, shadow price, in-flight,
deadline, reserve) read only released labels, issue times, pending counts, predictions and the
budget. None reads the label of event t.

* evidence="iid" tests V1: ``P(z_k = 1 | F_{k-1}) <= 1/2`` on queried disagreements.
* evidence="sui" tests V2: the event-time sign process is a stationary first-order two-state Markov
  chain with ``p <= 1/2`` and ANY persistence rho, independent of the disagreement process (fam_a
  docstring). The SUI e-process uses the gap since the most recent observed outcome; the gate passes
  that outcome even across verdicts, so the conditional bound is the one the null class implies.
* Promotion: P(any false promotion | null holds throughout) <= sum_j alpha_j with alpha_1 = alpha
  (single cycle) or alpha_j = alpha / 2^j (rollback), by Ville applied to each cycle's test from its
  (stopping-time) start. Host agreement, spacing, shadow and in-flight gates only remove queries or
  promotions.
* Rollback: given a promotion, if the mirrored null (challenger at least as good, same model class)
  holds after it, P(false rollback in that cycle) <= alpha_r. This is per cycle, not family-wise.
* Not covered: non-Markov dependence, time-varying p_t (late change, reversal), the twin-null
  marginal hypothesis on real data, and any economic statement.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fam_a  # noqa: E402
import fam_d  # noqa: E402
from fam_d import DeployGate, _A1Cert, _host_extra, _host_u, make_host, started_mixture  # noqa: E402
from simulator import QueryRequest  # noqa: E402

GAMMA_C2, ZETA_C2 = 3.0, 0.25  # fam_c TUNED C2 values (docs/sota_sprint/family_c/tuned.json)


def _val(cert) -> float:
    m = getattr(cert, "m", None)
    return float(m.value) if m is not None else 0.0


class UniformStartSUI(fam_a.MarkovSUI):
    """MarkovSUI with at most ``n_starts`` starts (every ``stride`` outcomes) at equal weight 1/n.

    For the rollback (reversal) test: a change after promotion is detected from a late start, and
    fam_a's 1/(m(m+1)) start weights make late starts cost ~2 log m nats. The number of outcomes a
    policy can observe is at most B, so ``n_starts = ceil(B / stride)`` starts suffice; weights are
    fixed in advance and sum to 1, so E_k is dominated by a test supermartingale exactly as in
    fam_a (Ville: P(sup E >= 1/a) <= a under every member of the Markov null class)."""

    def __init__(self, n_starts=20, **kw):
        super().__init__(**kw)
        self.n_starts = int(n_starts)

    def update(self, hit: int, gap: int, prev) -> float:
        self.k += 1
        if (self.k - 1) % self.stride == 0 and len(self.starts) < self.n_starts:
            self.starts.append((self.cum.copy(), self.acum.copy()))
        self.cum = np.maximum(self.cum + self._null_factor(hit, gap, prev), fam_a.LOG0)
        self.acum = np.maximum(self.acum + self._alt_factor(hit, gap, prev), fam_a.LOG0)
        lw = -math.log(self.n_starts)
        terms = []
        for c0, a0 in self.starts:
            num = fam_a._lse(self.alogpi + self.acum - a0)
            den = float(np.max(self.cum - c0))
            terms.append(lw + num - den)
        self.log_value = fam_a._lse(np.array(terms))
        self.value = float(math.exp(min(self.log_value, 700.0)))
        return self.value


def sui_cert(sui_kw=None):
    kw = fam_a._B if sui_kw is None else sui_kw
    return lambda side: _A1Cert(side, fam_a.MarkovSUI, **kw)


class HGate(DeployGate):
    """D2's deploy gate with dependence-robust evidence and A5b / C2 / dual-clock acquisition."""

    def __init__(self, host, T, B, alpha, *, rng, delay=100, cs=5.0, cq=0.05, evidence="sui",
                 sui_kw=None, single_cycle=False, spacing=False, space_host=True, c_corr=0.25,
                 min_pairs=8, rho_sig=2.0, shadow=False, shadow_host=True, gamma=GAMMA_C2,
                 zeta=ZETA_C2, n0=10, dualclock=False, inflight_margin=2.0, rollback=False,
                 reserve=0.0, alpha_r=0.05, rb_uniform=True, trace=False, name="H"):
        cert = started_mixture if evidence == "iid" else sui_cert(sui_kw)
        self.evidence = evidence
        self.rb_cert = (lambda side: _A1Cert(side, UniformStartSUI, n_starts=-(-B // 10),
                                             **fam_a._B)) \
            if (rb_uniform and evidence == "sui") else cert
        self.single_cycle = single_cycle and not rollback
        self.delay, self.cs, self.cq = int(delay), float(cs), float(cq)
        self.spacing, self.space_host = spacing, space_host
        self.c_corr, self.min_pairs, self.rho_sig = c_corr, min_pairs, rho_sig
        self.shadow, self.shadow_host = shadow, shadow_host
        self.gamma, self.zeta, self.n0 = gamma, zeta, n0
        self.dualclock, self.inflight_margin = dualclock, inflight_margin
        self.rel_z: list[int] = []
        self.rel_t: list[int] = []
        self.rho_hat = None
        self.last_issue = -10**9
        self.n_issued = self.n_processed = 0
        self.seg_k = self.seg_hits = 0
        self.cross_event = None  # event id of the outcome whose release crossed the threshold
        self._buf: list[tuple[int, int]] = []  # dualclock: outcomes released between cross & promote
        self.trace = trace
        self._t_now = 0
        self.tr: dict[str, list] = {"req": [], "ev": [], "veto": []}
        self.n_veto = {"spacing": 0, "shadow": 0, "inflight": 0, "deadline": 0, "reserve": 0}
        super().__init__(host, T, B, alpha, rng=rng, cert=cert, acq="host_pref", and_host=True,
                         rollback=rollback, reserve=reserve, alpha_r=alpha_r, share=True,
                         stop_when_final=True, monitor=True, name=name)

    # ------------------------------------------------------------------ thresholds
    def _thr_up(self) -> float:
        return (1.0 if self.single_cycle else 2.0 ** self.cycle) / self.alpha

    def _new_tests(self):
        super()._new_tests()
        if self.deployed == 1 and self.rollback:
            self.e_dn = self.rb_cert(-1)  # independently started reversal test
        self.seg_k = self.seg_hits = 0

    # ------------------------------------------------------------------ estimates (released only)
    def _gmin(self) -> int:
        if not self.spacing or self.rho_hat is None or self.rho_hat <= 0:
            return 0
        if self.rho_hat >= 1:
            return 10**9
        return int(math.ceil(math.log(self.c_corr) / math.log(self.rho_hat)))

    def _eff(self) -> float:
        """Effective-sample factor (1-a)/(1+a) at the current spacing, a = rho_hat^gap."""
        if not self.rel_t or self.rho_hat is None or self.rho_hat <= 0:
            return 1.0
        gaps = np.diff(self.rel_t[-50:]) if len(self.rel_t) > 1 else np.array([1.0])
        a = float(self.rho_hat ** max(float(np.median(gaps)), 1.0))
        return max((1.0 - a) / (1.0 + a), 0.02)

    def _p_stats(self):
        n = self.seg_k
        ph = (self.seg_hits + 1.0) / (n + 2.0)
        neff = max(n * self._eff(), 1.0)
        hw = 2.0 * math.sqrt(ph * (1.0 - ph) / neff)
        return n, ph, min(ph + hw, 0.999), neff

    def _need(self, p_eff: float) -> float:
        """Projected further outcomes the open promotion test needs at the effective p."""
        if p_eff <= 0.52:
            return float("inf")
        kl = p_eff * math.log(2 * p_eff) + (1 - p_eff) * math.log(2 * (1 - p_eff))
        logv = math.log(max(_val(self.e_up), 1e-300)) if self.e_up is not None else 0.0
        return max(math.log(self._thr_up()) - logv, 0.0) / (kl * self._eff())

    def _rate(self, t) -> float:
        return (self.pacer.n_disagree + 0.25 * 20.0) / (t + 20.0)

    def _shadow_ok(self, t, rem) -> bool:
        if self.seg_k < self.n0:
            return True
        n, ph, phi, _ = self._p_stats()
        p_eff = (1.0 - self.zeta) * ph + self.zeta * phi
        g_eff = self._rate(t) * max(2.0 * p_eff - 1.0, 0.0)
        if g_eff <= 0.0:
            return False
        pending = self.n_issued - self.n_processed
        n_rem = max(self._need(p_eff) - pending, 1.0)
        if not math.isfinite(n_rem):
            return False
        horizon = self.T - t - self.delay
        value = max(0.0, g_eff * horizon - self.cs) / n_rem
        spend = (self.B - rem + 20.0 * self.B / self.T) / (t + 20.0)
        lam = self.cq * max(1.0, spend * (self.T - t) / max(rem, 1)) ** self.gamma
        return value >= lam

    def _inflight_enough(self) -> bool:
        if not self.dualclock or self.seg_k < 20:
            return False
        pending = self.n_issued - self.n_processed
        _, ph, _, _ = self._p_stats()
        need = min(self._need(ph), self._need_dn(1.0 - ph))
        return math.isfinite(need) and pending >= self.inflight_margin * need + 5

    def _need_dn(self, q):
        if q <= 0.52 or self.e_dn is None:
            return float("inf")
        kl = q * math.log(2 * q) + (1 - q) * math.log(2 * (1 - q))
        return max(math.log(1.0 / self.alpha) - math.log(max(_val(self.e_dn), 1e-300)), 0.0) / (
            kl * self._eff())

    def _deadline_ok(self, t) -> bool:
        if not self.dualclock:
            return True
        left = self.T - t - self.delay  # events the released label can still influence
        if left <= 0:
            return False
        if self.seg_k < self.n0:
            return left * self._rate(t) * 1.0 > self.cs
        _, _, phi, _ = self._p_stats()
        side_hi = max(2.0 * phi - 1.0, 2.0 * (1.0 - (self.seg_hits + 1.0) / (self.seg_k + 2.0)) - 1.0)
        return left * self._rate(t) * max(side_hi, 1e-6) > self.cs

    # ------------------------------------------------------------------ deployment
    def predict(self, event):
        self.host_pref = int(self.host.predict(event))
        if self.deployed == 0 and self.cert_ok and self.host_pref == 1:
            self.deployed, self.decided, self.n_promotions = 1, True, self.n_promotions + 1
            self.seg = (self.cross_event + 1) if (self.dualclock and self.cross_event is not None) \
                else event.t
            self._new_tests()
            if self.dualclock and self.rollback:  # replay in-flight outcomes into the H- test
                for z, e in self._buf:
                    if e >= self.seg:
                        self._update_dn_post(z, e, None)
            self._buf = []
        return self.deployed

    # ------------------------------------------------------------------ acquisition
    def _veto(self, why, t):
        self.n_veto[why] += 1
        if self.trace:
            self.tr["veto"].append((t, why))
        return QueryRequest(requested=False)

    def request_labels(self, event, remaining_budget):
        t = event.t
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q_pace = self.pacer.propensity(t, remaining_budget, dis)
        self.pacer.note_event(dis)
        final = self.deployed == 1 and not self.rollback
        hreq = self.host.request_labels(event, remaining_budget)
        if final or not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        pre = self.deployed == 0
        if pre and remaining_budget <= self.reserve:
            return self._veto("reserve", t)
        if self.dualclock and not self._deadline_ok(t):
            return self._veto("deadline", t)
        open_test = pre and not self.cert_ok
        spaced_out = False
        if self.spacing and (open_test or self.deployed == 1) and t - self.last_issue < self._gmin():
            if self.space_host or not hreq.requested:
                return self._veto("spacing", t)
            spaced_out = True  # host draw kept (space_host=False); the gate's own draw is vetoed
        u = _host_u(self.host, event, hreq)
        if spaced_out:
            q_g = 0.0
        elif pre and not self.decided and self.host_pref == 1:
            q_g = 1.0
            if self._inflight_enough():
                q_g = 0.0
                self.n_veto["inflight"] += 1
        elif self.deployed == 1 and self.rollback:
            q_g = q_pace
        else:
            q_g = 0.0
        host_take = bool(hreq.requested)
        if self.shadow and open_test and not self._shadow_ok(t, remaining_budget):
            q_g = 0.0
            if self.shadow_host:
                host_take = False
            self.n_veto["shadow"] += 1
        take = host_take or (q_g > 0 and bool(self.rng.random() < q_g))
        if not take:
            return QueryRequest(requested=False)
        u_eff = u if host_take or not (self.shadow and self.shadow_host) else 0.0
        q_comb = max(u_eff + (1.0 - u_eff) * q_g, 1e-6)  # frozen issue-time union propensity
        extra = dict(hreq.extra) if hreq.requested else _host_extra(self.host, event)
        self._req[t] = (host_take, u_eff, q_comb)
        self.last_issue = t
        self.n_issued += 1
        if self.trace:
            self.tr["req"].append((t, int(host_take), self.deployed, self.host_pref,
                                   int(self.decided), int(self.cert_ok)))
        return QueryRequest(requested=True, probability=q_comb, extra=extra)

    # ------------------------------------------------------------------ feedback
    def _update_dn_post(self, z, e, last):
        if self.e_dn.update(z, e, last if last is not None else self._last_before(e)) \
                >= 1.0 / self.alpha_r:
            self.deployed, self.decided, self.cycle = 0, False, self.cycle + 1
            self.cert_ok, self.cross_event = False, None
            self.seg = e + 1 if self.dualclock else self._t_now
            self._new_tests()
            return True
        return False

    def _last_before(self, e):
        # most recent observed outcome strictly before issue event e (for buffered replays)
        for z_, e_ in zip(reversed(self.rel_z), reversed(self.rel_t)):
            if e_ < e:
                return (z_, e_)
        return None

    def observe(self, feedback):
        from simulator import ReleasedFeedback  # noqa: PLC0415

        fbs = sorted(feedback, key=lambda f: f.event_id)
        host_fb = []
        for fb in fbs:
            drew, u, q_comb = self._req.pop(fb.event_id, (True, fb.query_probability,
                                                          fb.query_probability))
            host_fb.append(ReleasedFeedback(fb.event_id, fb.t_requested, fb.t_released,
                                            fb.label, fb.model_losses, float(q_comb), fb.extra))
        if host_fb:
            self.host.observe(host_fb)
        for fb in fbs:
            self.n_processed += 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self._t_now = fb.t_released
            z, e, last = int(d > 0), fb.event_id, self.last
            self.last = (z, e)
            self.rel_z.append(z)
            self.rel_t.append(e)
            if e < self.seg:
                continue
            if self.deployed == 0:
                if self.cert_ok:
                    if self.dualclock and self.rollback and e > (self.cross_event or -1):
                        self._buf.append((z, e))
                    continue
                self.seg_k += 1
                self.seg_hits += z
                up = self.e_up.update(z, e, last)
                dn = self.e_dn.update(z, e, last)
                if self.trace:
                    self.tr["ev"].append((e, fb.t_released, z, up, dn, self.host_pref))
                if up >= self._thr_up():
                    self.cert_ok, self.decided, self.cross_event = True, True, e
                elif dn >= 1.0 / self.alpha:
                    self.decided = True
            elif self.rollback:
                self.seg_k += 1
                self.seg_hits += z
                self._update_dn_post(z, e, last)
        if self.spacing and len(self.rel_z) >= self.min_pairs + 1:
            self.rho_hat = fam_a.rho_mle(np.array(self.rel_z[-150:]), np.array(self.rel_t[-150:]),
                                         sig=self.rho_sig)

    def decision_state(self):
        return (f"dep={self.deployed};cycle={self.cycle};cert={int(self.cert_ok)};"
                f"pref={self.host_pref};gmin={self._gmin()}")


# ------------------------------------------------------------------------------------------------
# Registry entries (all CAMS host, same generator names as D2 so host randomness is paired).
# ------------------------------------------------------------------------------------------------
def _h(name, **kw):
    def f(T, B, cs, cq, a, d, r):
        return HGate(make_host("cams", r), T, B, a, rng=r("D_gate"), delay=d, cs=cs, cq=cq,
                     name=name, **kw)
    return f


H2_KW = dict(evidence="sui", single_cycle=True, spacing=True)

EXTRA = {
    # H1: D2 + A5b certificate (MarkovSUI with fam_a._B) + single-cycle threshold 1/alpha
    "H1": _h("H1", evidence="sui", single_cycle=True),
    "H1-twocycle": _h("H1-twocycle", evidence="sui"),  # = D5 with _B kwargs (isolates the prior)
    "H1-iid1": _h("H1-iid1", evidence="iid", single_cycle=True),  # D2 + single-cycle threshold
    # H2: H1 + A5b adaptive observation spacing (host and gate queries)
    "H2": _h("H2", **H2_KW),
    "H2-gateonly": _h("H2-gateonly", **H2_KW, space_host=False),
    "H2-iid_space": _h("H2-iid_space", evidence="iid", single_cycle=True, spacing=True),
    # (SUI evidence with D2 acquisition = H1)
    # H3: H2 + C2 shadow-price label allocation
    "H3": _h("H3", **H2_KW, shadow=True),
    "H3-gateonly": _h("H3-gateonly", **H2_KW, shadow=True, shadow_host=False),
    # H4: H2 + dual clock (in-flight awareness, deadline, event-order segments)
    "H4": _h("H4", **H2_KW, dualclock=True),
    # H5: H2 + rollback (promotion alpha/2^cycle, rollback alpha_r = .05 per cycle)
    "H5": _h("H5", evidence="sui", spacing=True, rollback=True),
    "H5-decay": _h("H5-decay", evidence="sui", spacing=True, rollback=True, rb_uniform=False),
    "H5-dc": _h("H5-dc", evidence="sui", spacing=True, rollback=True, dualclock=True),
    # H6: H5 + monitoring reserve
    **{f"H6-r{int(100 * rv)}": _h(f"H6-r{int(100 * rv)}", evidence="sui", spacing=True,
                                  rollback=True, reserve=rv) for rv in (0.10, 0.15, 0.25)},
}
EXTRA["H6-r0"] = EXTRA["H5"]
# exact re-implementations (tests: must replay D2 / D5 episode-for-episode)
EXTRA["Hchk:D2"] = _h("Hchk:D2", evidence="iid")
EXTRA["Hchk:D5"] = _h("Hchk:D5", evidence="sui", sui_kw={})

NULL_TESTED = {k: ("V1" if "iid" in k else "V2") for k in EXTRA}


# ------------------------------------------------------------------------------------------------
# Diagnosis (docs/sprint2/family_h/diagnosis.md): traced episodes + counterfactual evidence replay.
#   uv run python scripts/sota_sprint/fam_h.py diagnose --regimes F0_better,... --seeds 20 \
#       --out outputs/sprint2/H/diagnosis.json
# ------------------------------------------------------------------------------------------------
def _replay(z, e, kind, thr):
    """Outcomes needed by evidence ``kind`` to reach ``thr`` on a fixed (z, issue event) sequence."""
    if kind == "iid":
        m = fam_d.StartedMixture(+1)
        for k, x in enumerate(z, 1):
            if m.update(int(x)) >= thr:
                return k
        return None
    m = fam_a.MarkovSUI(**({} if kind == "sui_def" else fam_a._B))
    prev, pe = None, None
    for k, (x, ee) in enumerate(zip(z, e), 1):
        if m.update(int(x), 0 if prev is None else int(ee - pe), prev) >= thr:
            return k
        prev, pe = int(x), ee
    return None


def _episode(name, regime, seed, seed_base):
    import screen  # noqa: PLC0415
    from bench import parse_regime  # noqa: PLC0415
    from simulator import policy_rng, run_episode  # noqa: PLC0415
    from suite import stream_from_losses  # noqa: PLC0415

    R, _ = parse_regime(regime)
    losses = R.sample(np.random.default_rng(np.random.SeedSequence([seed_base, screen._h(R.name),
                                                                    seed])))
    def r(nm):
        return policy_rng(seed_base + screen._h(regime) % 1000, seed, nm)
    pol = EXTRA[name](2000, 200, 5.0, 0.05, 0.05, R.delay, r)
    pol.trace = True
    preds, labels = stream_from_losses(losses, np.random.default_rng(
        [seed_base, screen._h(regime), 0, seed, 7]))
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=R.delay, budget=200,
                      label_price=0.05, switch_cost=5.0, trace=True)
    dep = np.array([x["deployed_model"] for x in res.records])
    rq = np.array(pol.tr["req"]) if pol.tr["req"] else np.zeros((0, 6), int)
    ev = pol.tr["ev"]
    z = np.array([x[2] for x in ev], int)
    e = np.array([x[0] for x in ev], int)
    gaps = np.diff(e) if len(e) > 1 else np.array([0])
    pre = rq[:, 2] == 0 if len(rq) else np.zeros(0, bool)
    open_ = pre & (rq[:, 5] == 0) if len(rq) else pre
    out = {
        "policy": name, "regime": regime, "seed": seed, "net": res.net_cost,
        "promote": int((dep == 1).any()), "first": int(np.argmax(dep == 1)) if (dep == 1).any() else -1,
        "labels": len(rq), "labels_open": int(open_.sum()),
        "labels_open_host": int((open_ & (rq[:, 1] == 1)).sum()) if len(rq) else 0,
        "labels_open_pref0": int((open_ & (rq[:, 3] == 0)).sum()) if len(rq) else 0,
        "labels_after_discard": int((pre & (rq[:, 4] == 1) & (rq[:, 5] == 0)).sum()) if len(rq) else 0,
        "exhaust_t": int(rq[199, 0]) if len(rq) >= 200 else -1,
        "n_evidence": len(z), "mean_z": float(z.mean()) if len(z) else float("nan"),
        "median_gap": float(np.median(gaps)), "sign_changes": int(np.sum(z[1:] != z[:-1])) if len(z) > 1 else 0,
        "rho_true_at_gap": float(R.rho ** max(float(np.median(gaps)), 1.0)) if R.rho > 0 else 0.0,
        "log_e_up_max": float(np.log(max(max((x[3] for x in ev), default=1.0), 1e-300))),
        "cross_event": pol.cross_event if pol.cross_event is not None else -1,
        "gmin_final": pol._gmin(), "rho_hat_final": pol.rho_hat,
        "veto": dict(pol.n_veto), "runtime_events": len(res.records),
    }
    for kind in ("iid", "sui_def", "sui_B"):
        for thr in (20.0, 40.0):
            out[f"k_{kind}_{int(thr)}"] = _replay(z, e, kind, thr)
    return out


def _diag_job(a):
    return _episode(*a)


def diagnose(regimes, policies, seeds, seed_base, out, workers=2):
    import json  # noqa: PLC0415
    import multiprocessing as mp  # noqa: PLC0415

    jobs = [(p, rg, s, seed_base) for rg in regimes for p in policies for s in range(seeds)]
    with mp.Pool(workers) as pool:
        rows = pool.map(_diag_job, jobs, chunksize=2)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(rows, indent=1, default=float) + "\n")
    return rows


LEGACY_SUMMARY_COMPARATOR_POOL = [
    "xu_acquisition_only", "gated_adaptive_range+front", "choe_ramdas_eb+front",
    "SMCS+retain-incumbent",
]


def summarize(dirs, out, refs=("D2", "D5", "A5b", "cams_adapter"), *,
              legacy_comparator_pool=False):
    """Per-regime mean net / promotion / labels and paired net differences (candidate - ref,
    95% t-interval over seeds x episodes) vs D2, D5, A5b, CAMS and the lowest-cost tested
    certified-method port. The current pool comes from bench.CERTIFIED_PUBLISHED (which excludes
    Xu's acquisition adapter and non-native Choe-Ramdas port). Set legacy_comparator_pool only to
    reproduce the historical mislabeled summary. Writes JSON + a compact markdown table."""
    import json  # noqa: PLC0415

    import pandas as pd  # noqa: PLC0415
    from bench import CERTIFIED_PUBLISHED  # noqa: PLC0415

    d = pd.concat([pd.read_json(Path(x) / "records.jsonl", lines=True) for x in dirs])
    d = d.drop_duplicates(["regime", "ep", "seed", "policy", "alpha"], keep="last")
    piv = d.pivot_table(index=["regime", "ep", "seed"], columns="policy", values="net")
    res = {}
    for (rg, pol), g in d.groupby(["regime", "policy"]):
        row = {"net": g.net.mean(), "promote": g.ever_promote.mean(), "labels": g.labels.mean(),
               "rollbacks": g.n_rollbacks.mean(), "n": len(g), "runtime_max": g.runtime_s.max(),
               "runtime_mean": g.runtime_s.mean()}
        P = piv.loc[rg]
        cmp_pool = LEGACY_SUMMARY_COMPARATOR_POOL if legacy_comparator_pool else CERTIFIED_PUBLISHED
        cert = [c for c in cmp_pool if c in P]
        best = min(cert, key=lambda c: P[c].mean()) if cert else None
        for ref in [*refs, best]:
            if ref is None or ref not in P or ref == pol:
                continue
            x = (P[pol] - P[ref]).dropna()
            se = x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else float("nan")
            key = "best_cert" if ref == best and ref not in refs else ref
            row[f"d_{key}"] = [round(x.mean(), 2), round(x.mean() - 1.96 * se, 2),
                               round(x.mean() + 1.96 * se, 2)]
            if key == "best_cert":
                row["best_cert"] = best
                if not legacy_comparator_pool:
                    row["best_cert_pool"] = cert
        res.setdefault(pol, {})[rg] = row
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(res, indent=1, default=float) + "\n")
    return res


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["diagnose", "summarize"])
    ap.add_argument("--dirs", default="")
    ap.add_argument("--regimes", default="")
    ap.add_argument("--policies", default="Hchk:D2,Hchk:D5,H1-twocycle,H1,H2")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed-base", type=int, default=2026110701)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--legacy-comparator-pool", action="store_true",
                    help="reproduce historical Family-H summaries with the mislabeled comparator pool")
    a = ap.parse_args()
    import registry  # noqa: F401,PLC0415  (pins the FLQ module paths exactly as screen.py does)

    if a.cmd == "summarize":
        summarize(a.dirs.split(","), a.out, legacy_comparator_pool=a.legacy_comparator_pool)
    else:
        diagnose(a.regimes.split(","), a.policies.split(","), a.seeds, a.seed_base, a.out,
                 a.workers)
