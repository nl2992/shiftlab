"""Sprint 2 Family P: targeted performance repairs (configurations P1-P6).

Every policy keeps the common simulator protocol (propensities frozen at issue, labels after the
delay, hard budget enforced by the simulator). Evaluator-side truth (sign paths, gains) is only used
by the analysis functions at the bottom of this file, never by a policy.

P1  A5b power.  Evidence objects with a stated null:
    * ``RenewalEvidence`` (conditional run-length / Markov-regeneration test). Null class H+_R: the
      queried sign sequence is a homogeneous two-state chain "keep w.p. a_k, else redraw Bernoulli(p)"
      with p <= 1/2, ANY persistence, and per-step persistence factors a_k that are i.i.d. and
      independent of the signs (true when the sign chain runs in event time and queries are issued by a
      data-independent spacing rule on an i.i.d. disagreement process). Proof in
      docs/sprint2/family_p/P1_power.md: a completed cycle (1-run of length L1 then 0-run of length L0)
      has L1 ~ Geom(h1), L0 ~ Geom(h0) independent, h1 = (1-abar)(1-p), h0 = (1-abar)p, so given
      n = L1 + L0, P(L1 = l | n) is proportional to r^l on {1..n-1} with r = (1-h1)/(1-h0) <= 1 under
      H+. The factor e(l) = r'^l / mean_{l'} r'^{l'} (r' > 1) is increasing in l, and a distribution
      with r <= 1 is MLR-dominated by the uniform one, so E[e | n, past] <= 1.
    * ``CapMixture``: max_i w_i SUI_{rho <= c_i}. Shown INVALID for the free-rho null (P1 doc):
      a union bound only covers components whose cap is >= the true rho.
    * Spacing variants of A5b (c_corr): SUI conditions on the realised gaps, so any predictable
      spacing keeps A5b's bound unchanged.
P2/P3  Analysis only (``p2p3`` CLI): conditional vs marginal targets and the realised harm of
    erroneous promotions; ``FollowLeader`` is an uncertified aggressive-switching control.
P4  Misspecified dependence generators (``PRegime``), registered into bench.SPRINT_REGIMES.
P5  ``KGate``: D2's deploy-or-abstain gate generalised to K models (CAMS host over K constant
    policies, pairwise started-mixture certificates vs the current incumbent, Bonferroni over the K-1
    challengers). K-model regimes and a K-model runner (``kscreen`` CLI).
P6  ``ReservedRestartMonitor``: RMM architecture on the A5b host with (i) a label reserve the host
    cannot spend, (ii) a Markov-SUI detector with a UNIFORM prior over a bounded start grid instead of
    fam_a's w_first=.75 / 1/(m(m+1)) prior that charges late starts 6-8 nats.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_SOTA = ROOT / "scripts/promising_directions/sota"
for _p in (ROOT / "scripts/failure_atlas_v2_flq", HERE, _SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fam_a
from bench import SPRINT_REGIMES, _r
from controls import FixedModel, PacedDisagreementAcquisition
from qsg import StartedMixture
from simulator import QueryRequest, ReleasedFeedback

LOG0 = -1e9


def _lse(x) -> float:
    x = np.asarray(x, float)
    m = float(np.max(x))
    return m + math.log(float(np.sum(np.exp(x - m))))


# ================================================================================================
# P4: misspecified dependence generators (same interface as ooc_regimes.OOCNull)
# ================================================================================================
@dataclass(frozen=True)
class PRegime:
    """Sign process ``s_t`` (True = challenger right on a disagreement) of a given dependence class.

    kind: 'order2' (copy s_{t-1} w.p. c1, s_{t-2} w.p. c2, else Bernoulli(p)); 'semimarkov'
    (Pareto(1.5)+1 run lengths, each run's sign Bernoulli(p)); 'hmm' (hidden two-state chain with
    switch prob ``sw``, signs i.i.d. Bernoulli(p_h) given the state, p_h in ``hmm_p``); 'piecerho'
    (first-order chain whose persistence follows the schedule ``rho_sched``).
    Marginal P(s=1) = p in every class (hmm: mean of hmm_p), so G_t = dis (2p-1) is constant.
    """

    name: str
    kind: str
    p: float = 0.5
    dis: float = 0.2
    delay: int = 100
    err_agree: float = 0.1
    c: tuple = (0.5, 0.4)
    hmm_p: tuple = (0.3, 0.7)
    sw: float = 0.01
    rho_sched: tuple = ((0, 0.2), (700, 0.95), (1400, 0.5))
    tags: tuple = ("null", "dep", "misspec")
    family: str = "misspec"

    def marginal(self) -> float:
        return float(np.mean(self.hmm_p)) if self.kind == "hmm" else self.p

    def truth_gain(self, horizon: int = 2000) -> np.ndarray:
        return np.full(horizon, self.dis * (2.0 * self.marginal() - 1.0))

    def signs(self, rng: np.random.Generator, horizon: int = 2000) -> np.ndarray:
        s = np.empty(horizon, dtype=bool)
        if self.kind == "order2":
            c1, c2 = self.c
            s[:2] = rng.random(2) < self.p
            u, v = rng.random(horizon), rng.random(horizon)
            for t in range(2, horizon):
                s[t] = s[t - 1] if u[t] < c1 else (s[t - 2] if u[t] < c1 + c2 else v[t] < self.p)
        elif self.kind == "semimarkov":
            t = 0
            while t < horizon:
                run = int(np.floor(rng.pareto(1.5) + 1.0))
                s[t : t + run] = rng.random() < self.p
                t += run
        elif self.kind == "hmm":
            h = int(rng.random() < 0.5)
            u, v = rng.random(horizon), rng.random(horizon)
            ph = np.asarray(self.hmm_p)
            for t in range(horizon):
                if u[t] < self.sw:
                    h = 1 - h
                s[t] = v[t] < ph[h]
        elif self.kind == "piecerho":
            rho = np.empty(horizon)
            for i, (st, val) in enumerate(self.rho_sched):
                en = self.rho_sched[i + 1][0] if i + 1 < len(self.rho_sched) else horizon
                rho[st:en] = val
            u, v = rng.random(horizon), rng.random(horizon)
            s[0] = v[0] < self.p
            for t in range(1, horizon):
                s[t] = s[t - 1] if u[t] < rho[t] else v[t] < self.p
        else:
            raise ValueError(self.kind)
        return s

    def sample_state(self, rng: np.random.Generator, horizon: int = 2000):
        on = rng.random(horizon) < self.dis
        sign = self.signs(rng, horizon)
        both_wrong = rng.random(horizon) < self.err_agree
        l0 = np.where(on, sign, both_wrong).astype(np.int8)
        l1 = np.where(on, ~sign, both_wrong).astype(np.int8)
        return np.stack([l0, l1], axis=1), sign

    def sample(self, rng: np.random.Generator, horizon: int = 2000) -> np.ndarray:
        return self.sample_state(rng, horizon)[0]


_ALT = ("alt", "dep", "misspec")
P_REGIMES: dict = {
    r.name: r
    for r in [
        PRegime("P_order2_null", "order2"),
        PRegime("P_order2_better", "order2", p=0.65, tags=_ALT),
        PRegime("P_semimarkov_better", "semimarkov", p=0.65, tags=_ALT),
        PRegime("P_hmm_null", "hmm", hmm_p=(0.3, 0.7)),
        PRegime("P_hmm_better", "hmm", hmm_p=(0.45, 0.85), tags=_ALT),
        PRegime("P_piecerho_null", "piecerho"),
        PRegime("P_piecerho_better", "piecerho", p=0.65, tags=_ALT),
    ]
}
# first-order Markov null with bursty (non-i.i.d.) disagreements: breaks RenewalEvidence's i.i.d.-gap
# premise while staying inside A5b's class (FLQ Regime object)
P_REGIMES["P_bursty_null_r8"] = _r(
    "P_bursty_null_r8", "dependence", [(0, 0.5)], rho=0.8, burst=0.9, tags=("null", "dep")
)
P_REGIMES["P_markov_null_r98"] = _r(
    "P_markov_null_r98", "dependence", [(0, 0.5)], rho=0.98, tags=("null", "dep")
)
for _k, _v in P_REGIMES.items():  # idempotent: harmless when imported twice
    SPRINT_REGIMES.setdefault(_k, _v)


# ================================================================================================
# P1: evidence objects
# ================================================================================================
R_GRID = np.array([1.05, 1.1, 1.25, 1.6, 2.0, 3.0])


class RenewalEvidence:
    """Conditional run-length (regeneration) e-process; ``update(hit, gap, prev)`` like MarkovSUI.

    Cycles start at an observed 0 -> 1 entry (a regeneration time of the chain). A cycle closes at
    the next 0 -> 1 entry with (L1, L0); its factor is r'^L1 / mean_{l=1..n-1} r'^l (n = L1 + L0),
    mixed over ``grid`` with a started mixture over cycles (weights 1/(k(k+1)), as QSG). ``reset``
    drops the in-progress cycle (used when the query regime changes, so a cycle never mixes two
    gap distributions).
    """

    def __init__(self, grid=R_GRID, started=True):
        self.lg = np.log(np.asarray(grid, float))
        self.pi = np.full(len(self.lg), 1.0 / len(self.lg))
        self.S = np.zeros(len(self.lg))
        self.started = started
        self.k = 0
        self.state = None
        self.in_cycle = False
        self.l1 = self.l0 = 0

    def reset(self):
        self.state, self.in_cycle, self.l1, self.l0 = None, False, 0, 0

    def factor(self, l1: int, l0: int) -> np.ndarray:
        n = l1 + l0
        ls = np.arange(1, n)
        logm = np.array([_lse(g * ls) for g in self.lg]) - math.log(n - 1)
        return np.exp(self.lg * l1 - logm)

    def _close(self):
        self.k += 1
        f = self.factor(self.l1, self.l0)
        if self.started:
            self.S = (self.S + 1.0 / (self.k * (self.k + 1))) * f
        else:
            self.S = (np.ones_like(self.S) if self.k == 1 else self.S) * f

    def update(self, hit: int, gap: int = 0, prev=None) -> float:
        h = int(hit)
        if self.state is None:
            self.state = h
            return self.value
        if not self.in_cycle:
            if self.state == 0 and h == 1:
                self.in_cycle, self.l1, self.l0 = True, 1, 0
        elif h == 1:
            if self.state == 1:
                self.l1 += 1
            else:
                self._close()
                self.l1, self.l0 = 1, 0
        else:
            self.l0 += 1
        self.state = h
        return self.value

    @property
    def value(self) -> float:
        return float(self.pi @ self.S)


class CapMixture:
    """max_i w_i E_i over SUIs with declared caps (the configuration requested in P1). NOT valid
    for the free-rho null: components with cap < true rho are not supermartingales."""

    def __init__(self, caps=(0.5, 0.8, 0.95, 1.0), **kw):
        self.w = 1.0 / len(caps)
        self.parts = [fam_a.MarkovSUI(rho_max=c, **kw) for c in caps]
        self.value = 0.0

    def update(self, hit, gap, prev):
        self.value = max(self.w * p.update(hit, gap, prev) for p in self.parts)
        return self.value


class UnionEvidence:
    """Union of SUI and renewal at alpha/2 each: reported value min-scaled so that crossing the
    caller's threshold thr means SUI >= 2 thr or renewal >= 2 thr (Bonferroni)."""

    def __init__(self, sui_kw=None, grid=R_GRID):
        self.sui = fam_a.MarkovSUI(**(sui_kw or {}))
        self.ren = RenewalEvidence(grid)
        self.value = 0.0

    def reset(self):
        self.ren.reset()

    def update(self, hit, gap, prev):
        a = self.sui.update(hit, gap, prev)
        b = self.ren.update(hit, gap, prev)
        self.value = 0.5 * max(a, b)
        return self.value


class FamP1(fam_a.FamA):
    """FamA skeleton with P1 evidence. ``discard=False`` removes the discard verdict, so the only
    pre-promotion query regime is front-loading under the spacing rule (needed for RenewalEvidence's
    i.i.d.-gap premise). A regime change (verdict) resets any in-progress renewal cycle."""

    def __init__(self, *a, discard=True, **kw):
        self.discard = discard
        super().__init__(*a, **kw)

    def _mk(self):
        if self.evidence == "renewal":
            return RenewalEvidence()
        if self.evidence == "union":
            return UnionEvidence(self.sui_kw)
        if self.evidence == "capmix":
            return CapMixture(**self.sui_kw)
        return super()._mk()

    def observe(self, feedback):
        if self.discard:
            return super().observe(feedback)
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            z, e, t = int(d > 0), fb.event_id, fb.t_released
            self.n_processed += 1
            self.rel_z.append(z)
            self.rel_t.append(e)
            if fb.event_id >= self.seg:
                self.seg_k += 1
                self.seg_hits += z
                if self.deployed == 0:
                    if self._upd(self.e_up, +1, z, e) >= 2.0**self.cycle / self.alpha:
                        self.deployed, self.decided, self.seg = 1, True, t
                        self.last = (z, e)
                        self._new_tests()
                        continue
                elif self.rollback and self._upd(self.e_dn, -1, z, e) >= 1.0 / self.alpha_r:
                    self.deployed, self.decided, self.cycle = 0, False, self.cycle + 1
                    self.seg = t
                    self.last = (z, e)
                    self._new_tests()
                    continue
            self.last = (z, e)
        if self.density == "adaptive" and len(self.rel_z) >= self.min_pairs + 1:
            self.rho_hat = fam_a.rho_mle(
                np.array(self.rel_z[-150:]), np.array(self.rel_t[-150:]), sig=self.rho_sig
            )


def _p1(name, **kw):
    return lambda T, B, cs, cq, a, d, r: FamP1(T, B, a, rng=r("QSG"), name=name, **kw)


RENEW_GAP = (
    7  # fixed spacing for renewal evidence: chosen from the P1 diagnostic (not screen seeds)
)


# ================================================================================================
# P3: aggressive (uncertified) switching control
# ================================================================================================
class FollowLeader:
    """Deploy the model that won the last ``k`` released queried disagreements (all k agree);
    queries paced evenly over disagreements. No false-promotion guarantee (Track V: none)."""

    def __init__(self, T, B, *, rng, k=2, name="P3_follow"):
        self.name, self.k, self.rng = name, int(k), rng
        self.acq = PacedDisagreementAcquisition(T, B)
        self.deployed = 0
        self.recent: list[int] = []

    def predict(self, event):
        return self.deployed

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.recent = (self.recent + [int(d > 0)])[-self.k :]
            if len(self.recent) == self.k and len(set(self.recent)) == 1:
                self.deployed = self.recent[0]

    def decision_state(self):
        return f"dep={self.deployed}"

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


# ================================================================================================
# P5: K-model deploy gate (D2 generalised) and K-model regimes
# ================================================================================================
class KGate:
    """CAMS host over K constant policies ranks and queries; promotion of challenger j away from the
    current incumbent i requires a started-mixture certificate on (i, j) disagreement outcomes
    (z = 1[j right]) to cross (K-1) 2^cycle / alpha AND the host to rank j first.

    Validity (V1): under H+ "no challenger is ever better than the incumbent on their disagreements,
    conditionally on the query-time information", each pairwise certificate is a test supermartingale
    (query decisions are predictable; one label reveals all K losses), so a cycle-c false promotion has
    probability <= sum_j alpha / ((K-1) 2^c) = alpha / 2^c, and <= alpha over cycles.
    acq: 'host_pref' front-loads (i, pref) disagreements while the host prefers an uncertified
    challenger; 'host_only' adds no gate queries (ablation)."""

    def __init__(self, K, T, B, alpha, *, rng, host_rng, acq="host_pref", host="cams", name="K_D2"):
        from cams import CAMSDeploymentAdapter, stack_advice
        from model_picker import ModelPickerDeploymentAdapter

        self.K, self.T, self.B, self.alpha, self.rng = K, T, B, alpha, rng
        self.name, self.acq, self.kind = name, acq, host
        self.host = (
            CAMSDeploymentAdapter(
                n_models=K, n_classes=2, advice_fn=stack_advice(K, []), rng=host_rng
            )
            if host == "cams"
            else ModelPickerDeploymentAdapter(K, 2, host_rng)
        )
        self.inc, self.cycle, self.seg, self.pref = 0, 1, 0, 0
        self._req: dict[int, tuple[bool, float, float]] = {}
        self._new_tests()

    def _new_tests(self):
        self.tests = {j: StartedMixture(+1) for j in range(self.K) if j != self.inc}
        self.cert: set[int] = set()

    def predict(self, event):
        self.pref = int(self.host.predict(event))
        if self.pref != self.inc and self.pref in self.cert:
            self.inc, self.cycle, self.seg = self.pref, self.cycle + 1, event.t
            self._new_tests()
        return self.inc

    def _host_u(self, event, hreq):
        if hreq.requested or self.kind != "cams":
            return float(hreq.probability)
        return float(self.host.core.decide(event, draw=False)[0])

    def request_labels(self, event, remaining_budget):
        hreq = self.host.request_labels(event, remaining_budget)
        if remaining_budget <= 0:
            return QueryRequest(requested=False)
        mp = event.model_predictions
        q_g = 0.0
        if (
            self.acq == "host_pref"
            and self.pref != self.inc
            and self.pref not in self.cert
            and mp[self.pref] != mp[self.inc]
        ):
            q_g = 1.0
        u = self._host_u(event, hreq)
        take = bool(hreq.requested) or (q_g > 0 and bool(self.rng.random() < q_g))
        if not take:
            return QueryRequest(requested=False)
        q_comb = u + (1.0 - u) * q_g
        if hreq.requested:
            extra = dict(hreq.extra)
        elif self.kind == "cams":
            extra = {"E": self.host.core._prepare(event)["e"].copy()}
        else:
            extra = {}
        self._req[event.t] = (bool(hreq.requested), u, q_comb)
        return QueryRequest(requested=True, probability=q_comb, extra=extra)

    def observe(self, feedback):
        fbs = sorted(feedback, key=lambda f: f.event_id)
        host_fb = []
        for fb in fbs:
            _, _, q_comb = self._req.pop(
                fb.event_id, (True, fb.query_probability, fb.query_probability)
            )
            host_fb.append(
                ReleasedFeedback(
                    fb.event_id,
                    fb.t_requested,
                    fb.t_released,
                    fb.label,
                    fb.model_losses,
                    float(q_comb),
                    fb.extra,
                )
            )
        if host_fb:
            self.host.observe(host_fb)
        thr = (self.K - 1) * 2.0**self.cycle / self.alpha
        for fb in fbs:
            if fb.event_id < self.seg:
                continue
            li = int(fb.model_losses[self.inc])
            for j, m in self.tests.items():
                lj = int(fb.model_losses[j])
                if li != lj and j not in self.cert and m.update(int(li > lj)) >= thr:
                    self.cert.add(j)

    def decision_state(self):
        return f"inc={self.inc};cert={sorted(self.cert)};pref={self.pref}"

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


@dataclass(frozen=True)
class KRegime:
    """K-model loss streams. Incumbent loss l0 ~ Bernoulli(e0). Challenger j disagrees with the
    incumbent at rate ``dis`` and, on a disagreement, is the right one w.p. p_j(t) (piecewise
    schedule), challengers conditionally independent given l0. truth_gain() -> (T, K) per-event
    advantage of each model over the incumbent (column 0 = 0)."""

    name: str
    p: tuple  # per challenger: ((start, p), ...)
    dis: float = 0.2
    e0: float = 0.3
    delay: int = 100
    tags: tuple = ()

    @property
    def K(self):
        return len(self.p) + 1

    def _sched(self, spec, horizon):
        out = np.empty(horizon)
        for i, (s, v) in enumerate(spec):
            e = spec[i + 1][0] if i + 1 < len(spec) else horizon
            out[s:e] = v
        return out

    def truth_gain(self, horizon=2000):
        g = np.zeros((horizon, self.K))
        for j, spec in enumerate(self.p, start=1):
            g[:, j] = self.dis * (2.0 * self._sched(spec, horizon) - 1.0)
        return g

    def sample(self, rng, horizon=2000):
        l0 = rng.random(horizon) < self.e0
        cols = [l0]
        for spec in self.p:
            pj = self._sched(spec, horizon)
            a = self.dis * pj / self.e0  # P(j right | incumbent wrong)
            b = self.dis * (1.0 - pj) / (1.0 - self.e0)  # P(j wrong | incumbent right)
            u = rng.random(horizon)
            cols.append(np.where(l0, ~(u < a), u < b))
        return np.stack(cols, axis=1).astype(np.int8)


K_REGIMES = {
    r.name: r
    for r in [
        KRegime("K3_best1", (((0, 0.65),), ((0, 0.5),)), tags=("alt",)),
        KRegime("K4_mixed", (((0, 0.6),), ((0, 0.45),), ((0, 0.68),)), tags=("alt",)),
        KRegime("K3_null", (((0, 0.5),), ((0, 0.4),)), tags=("null",)),
        KRegime("K4_null", (((0, 0.5),), ((0, 0.45),), ((0, 0.5),)), tags=("null",)),
        KRegime(
            "K4_late", (((0, 0.45),), ((0, 0.55),), ((0, 0.4), (800, 0.72))), tags=("alt", "change")
        ),
        KRegime("K3_near", (((0, 0.57),), ((0, 0.55),)), tags=("alt",)),
    ]
}


def k_policies(K, T, B, alpha, r):
    """K-model policy panel (names -> instances)."""
    from cams import CAMSDeploymentAdapter, stack_advice
    from model_picker import ModelPickerDeploymentAdapter

    return {
        "K_D2": KGate(K, T, B, alpha, rng=r("D_gate"), host_rng=r("cams"), name="K_D2"),
        "K_D2-host_only": KGate(
            K,
            T,
            B,
            alpha,
            rng=r("D_gate"),
            host_rng=r("cams"),
            acq="host_only",
            name="K_D2-host_only",
        ),
        "K_D1": KGate(
            K, T, B, alpha, rng=r("D_gate"), host_rng=r("model_picker"), host="mp", name="K_D1"
        ),
        "K_cams": CAMSDeploymentAdapter(
            n_models=K, n_classes=2, advice_fn=stack_advice(K, []), rng=r("cams")
        ),
        "K_model_picker": ModelPickerDeploymentAdapter(K, 2, r("model_picker")),
        "K_never": FixedModel(0, name="K_never"),
    }


# ================================================================================================
# P6: reserved-label restart monitor with a uniform-start Markov-SUI detector
# ================================================================================================
def _rmm_module():
    name = "atlas_v2_restart_monitor"
    if name not in sys.modules:  # registry normally loads it first; replicate for direct imports
        path = ROOT / "scripts/failure_atlas_v2/restart_monitor.py"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        saved = list(sys.path)
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.path[:] = saved
    return sys.modules[name]


class UniformStartSUI(fam_a.MarkovSUI):
    """MarkovSUI with prior mass 1/n_starts on each of at most n_starts starts (every ``stride``
    outcomes); no starts after the grid is exhausted. Sum of weights = 1, so the Ville argument of
    fam_a.MarkovSUI applies unchanged (valid under the free-rho stationary Markov null)."""

    def __init__(self, n_starts: int, **kw):
        super().__init__(**kw)
        self.n_starts = max(1, int(n_starts))

    def update(self, hit, gap, prev):
        self.k += 1
        if (self.k - 1) % self.stride == 0 and len(self.starts) < self.n_starts:
            self.starts.append((self.cum.copy(), self.acum.copy()))
        self.cum = np.maximum(self.cum + self._null_factor(hit, gap, prev), LOG0)
        self.acum = np.maximum(self.acum + self._alt_factor(hit, gap, prev), LOG0)
        w = math.log(1.0 / self.n_starts)
        terms = [
            w + _lse(self.alogpi + self.acum - a0) - float(np.max(self.cum - c0))
            for c0, a0 in self.starts
        ]
        self.log_value = _lse(np.array(terms))
        self.value = float(math.exp(min(self.log_value, 700.0)))
        return self.value


class _Det:
    def __init__(self, ev, alpha):
        self.ev, self.alpha = ev, float(alpha)

    def update_at(self, hit, gap, prev) -> bool:
        return self.ev.update(hit, gap, prev) >= 1.0 / self.alpha


def _make_p6():
    import fam_m

    class ReservedRestartMonitor(fam_m.RMMSUI):
        """fam_m.RMMSUI (host A5b never restarted; detector overrides deployment on alarm) plus:
        reserve: fraction of B only the detector may spend (host sees remaining - unspent reserve);
        det: 'uniform' (UniformStartSUI) | 'b' (fam_a._B prior, = fam_m) | 'renewal'."""

        def __init__(
            self,
            make_base,
            T,
            B,
            alpha,
            *,
            rng,
            reserve=0.25,
            det="uniform",
            stride=10,
            name="",
            **kw,
        ):
            self.res_B = round(reserve * B)
            self.n_own = 0
            self.det_kind, self.stride_d = det, stride
            super().__init__(make_base, T, B, alpha, rng=rng, name=name, **kw)

        def _new_detector(self):
            a = self.alpha_det / (2.0**self.n_promotions) if self.deployed == 0 else self.alpha_rb
            if self.det_kind == "uniform":
                ev = UniformStartSUI(
                    n_starts=math.ceil(self.B / self.stride_d),
                    stride=self.stride_d,
                    rho_prior=fam_a._B["rho_prior"],
                )
            elif self.det_kind == "renewal":
                ev = RenewalEvidence()
            else:
                ev = fam_a.MarkovSUI(**fam_a._B)
            return _Det(ev, a)

        def request_labels(self, event, remaining_budget):
            self.remaining = remaining_budget
            dis = bool(event.model_predictions[0] != event.model_predictions[1])
            res_left = max(0, self.res_B - self.n_own)
            host_b = max(0, remaining_budget - res_left)
            req = self.base.request_labels(self.view.event(event), host_b)
            if self.res_B == 0 or host_b == 0:  # no reserve (= RMM), or host budget exhausted
                own_b = remaining_budget
            else:
                own_b = min(res_left, remaining_budget)
            q_own = self.acq.propensity(event.t, own_b, dis)
            self.acq.note_event(dis)
            if req.requested and host_b > 0:
                self.base_owned.add(event.t)
                if dis:
                    self.order.append(event.t)
                return req
            if self.keep and dis and own_b > 0 and q_own > 0.0 and self.rng.random() < q_own:
                self.own.add(event.t)
                self.order.append(event.t)
                self.n_own += 1
                return QueryRequest(requested=True, probability=q_own)
            return QueryRequest(requested=False)

    return ReservedRestartMonitor


def _a5b_host(T, B, a, r):
    return fam_a.FamA(
        T,
        B,
        a,
        rng=r,
        name="A5b-host",
        evidence="sui",
        density="adaptive",
        rho_sig=2.0,
        sui_kw=fam_a._B,
    )


def _p6(name, **kw):
    def f(T, B, cs, cq, a, d, r):
        _rmm_module()
        cls = _make_p6()
        return cls(_a5b_host, T, B, a, rng=r("QSG"), name=name, **kw)

    return f


def _p6_lrmd(name, **kw):
    def f(T, B, cs, cq, a, d, r):
        _rmm_module()
        cls = _make_p6()
        return cls(
            lambda T_, B_, a_, r_: FixedModel(0, name="fixed"),
            T,
            B,
            a,
            rng=r("lrmd"),
            name=name,
            alpha_split=1.0,
            **kw,
        )

    return f


# ================================================================================================
# Registry
# ================================================================================================
EXTRA = {
    # P1: A5b power repairs
    "P1_A5b_c10": _p1(
        "P1_A5b_c10", evidence="sui", density="adaptive", rho_sig=2.0, sui_kw=fam_a._B, c_corr=0.10
    ),
    "P1_A5b_c05": _p1(
        "P1_A5b_c05", evidence="sui", density="adaptive", rho_sig=2.0, sui_kw=fam_a._B, c_corr=0.05
    ),
    "P1_renew": _p1(
        "P1_renew", evidence="renewal", density="fixedgap", fixed_gap=RENEW_GAP, discard=False
    ),
    "P1_union": _p1(
        "P1_union",
        evidence="union",
        density="fixedgap",
        fixed_gap=RENEW_GAP,
        sui_kw=fam_a._B,
        discard=False,
    ),
    "P1_sui_fixedgap": _p1(
        "P1_sui_fixedgap",
        evidence="sui",
        density="fixedgap",
        fixed_gap=RENEW_GAP,
        sui_kw=fam_a._B,
        discard=False,
    ),  # union ablation
    "P1_cap95": _p1(
        "P1_cap95",
        evidence="sui",
        density="adaptive",
        rho_sig=2.0,
        sui_kw=dict(fam_a._B, rho_max=0.95),
    ),
    "P1_capmix": _p1(
        "P1_capmix", evidence="capmix", density="adaptive", rho_sig=2.0, sui_kw=dict(fam_a._B)
    ),
    # P3: aggressive uncertified switching control
    "P3_follow": lambda T, B, cs, cq, a, d, r: FollowLeader(T, B, rng=r("p3_follow")),
    # P6: reserved-label restart monitor on A5b, uniform-start SUI detector
    "P6_RRD": _p6("P6_RRD", reserve=0.25, det="uniform"),
    "P6_RRD-nores": _p6("P6_RRD-nores", reserve=0.0, det="uniform"),
    "P6_RRD-bprior": _p6("P6_RRD-bprior", reserve=0.25, det="b"),
    "P6_RRD-renewal": _p6("P6_RRD-renewal", reserve=0.25, det="renewal"),
    "P6_LRMD_U": _p6_lrmd("P6_LRMD_U", reserve=0.0, det="uniform"),
}


# ================================================================================================
# Analyses (CLI).  uv run python scripts/sota_sprint/fam_p.py <p1diag|p2p3|kbuild|kscreen|p4sum> ...
# ================================================================================================
def _trans(p, a):
    """Transition matrix P[prev, cur] of the 'keep w.p. a else redraw Bernoulli(p)' chain."""
    return np.array([[1 - (1 - a) * p, (1 - a) * p], [(1 - a) * (1 - p), a + (1 - a) * p]])


def fisher_efficiency(p, a, eps=1e-5):
    """Per-step Fisher information for p with a known vs a unknown (efficient information)."""

    def ll_grad(pp, aa):
        P = _trans(pp, aa)
        return np.log(P)

    L = ll_grad(p, a)
    dp = (ll_grad(p + eps, a) - ll_grad(p - eps, a)) / (2 * eps)
    da = (ll_grad(p, min(a + eps, 1 - 1e-9)) - ll_grad(p, max(a - eps, 0.0))) / (
        min(a + eps, 1 - 1e-9) - max(a - eps, 0.0)
    )
    P = np.exp(L)
    pi = np.array([1 - p, p])
    w = pi[:, None] * P
    Ipp, Iaa, Ipa = (
        float(np.sum(w * dp * dp)),
        float(np.sum(w * da * da)),
        float(np.sum(w * dp * da)),
    )
    eff = Ipp - Ipa**2 / Iaa if Iaa > 0 else Ipp
    return Ipp, eff


def _chain_queries(rng, p, rho, dis, gap_min, n_q, horizon=200000):
    """Simulate the event-time sign chain and the queried (z, event) sequence under 'query the first
    disagreement at least gap_min events after the last query'."""
    out_z, out_t = [], []
    s = rng.random() < p
    last = -(10**9)
    for t in range(horizon):
        if t > 0:
            s = s if rng.random() < rho else (rng.random() < p)
        if rng.random() < dis and t - last >= gap_min:
            out_z.append(int(s))
            out_t.append(t)
            last = t
            if len(out_z) >= n_q:
                break
    return np.array(out_z), np.array(out_t)


def _cond_ll(z, t, p, rho):
    g = np.diff(t)
    a = rho**g
    m = a * z[:-1] + (1 - a) * p
    ll = math.log(p if z[0] else 1 - p)
    return ll + float(np.sum(np.log(np.where(z[1:] == 1, m, 1 - m))))


def p1_diag(reps=200, n_q=100, seed=2026110790):
    rng = np.random.default_rng(seed)
    rows = []
    for p, rho in [(0.65, 0.8), (0.65, 0.95), (0.65, 0.5), (0.65, 0.0), (0.6, 0.8)]:
        for G in (1, 4, 7, 12):
            acc = []
            for _ in range(reps):
                z, t = _chain_queries(rng, p, rho, 0.2, G, n_q)
                sui = fam_a.MarkovSUI(started=False, **fam_a._B)
                ren = RenewalEvidence(started=False)
                prev, last_t = None, None
                for zi, ti in zip(z, t):
                    sui.update(int(zi), 0 if last_t is None else int(ti - last_t), prev)
                    ren.update(int(zi))
                    prev, last_t = int(zi), ti
                logQ = _lse(sui.alogpi + sui.acum)
                logU = float(np.max(sui.cum))
                la, l0 = _cond_ll(z, t, p, rho), _cond_ll(z, t, 0.5, rho)
                acc.append(
                    {
                        "oracle": la - l0,
                        "sui": logQ - logU,
                        "absorbed": logU - l0,
                        "alt_loss": la - logQ,
                        "renewal": math.log(max(ren.value, 1e-300)),
                        "cycles": ren.k,
                        "events": int(t[-1] - t[0]),
                    }
                )
            m = {k: float(np.mean([a[k] for a in acc])) for k in acc[0]}
            m.update(
                p=p,
                rho=rho,
                G=G,
                a_mean=float(np.mean(rho ** np.maximum(np.diff(t), 1))),
                sui_cross_20=float(np.mean([a["sui"] >= math.log(40) for a in acc])),
                ren_cross_20=float(np.mean([a["renewal"] >= math.log(40) for a in acc])),
            )
            rows.append(m)
    fish = []
    for a in (0.0, 0.1, 0.25, 0.5, 0.8, 0.9, 0.95):
        Ipp, eff = fisher_efficiency(0.6, a)
        fish.append({"a": a, "I_known": Ipp, "I_free": eff, "ratio": eff / Ipp})
    return {"sim": rows, "fisher_p0.6": fish, "reps": reps, "n_q": n_q, "seed": seed}


def _main(argv=None):
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=200)
    a, rest = ap.parse_known_args(argv)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.cmd == "p1diag":
        res = p1_diag(reps=a.reps)
    else:
        res = ANALYSES[a.cmd](rest)
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps(res, indent=1, default=float)[:6000])


ANALYSES: dict = {}


# ---------------------------------------------------------------- P2 / P3: path-level analysis
P23_POLICIES = [
    "A5b",
    "D2",
    "QSG",
    "rmm:gated_deployment+RMM",
    "gated_adaptive_range+front",
    "P3_follow",
    "CONTROL_never_switch",
]
TWIN_POLICIES = P23_POLICIES + [
    "P1_renew",
    "P1_union",
    "P1_A5b_c10",
    "P6_RRD",
    "P6_LRMD_U",
    "M_LRMD_SUI",
]


def _paths_job(args):
    """One synthetic Markov episode (evaluator keeps the sign path) x P23 policies."""
    (p, rho, delay, seed) = args
    import registry  # noqa: F401  (loads every policy)

    reg = PRegime("tmp", "piecerho", p=p, rho_sched=((0, rho),), delay=delay)
    rng = np.random.default_rng([2026110701, int(p * 1000), int(rho * 1000), delay, seed])
    losses, sign = reg.sample_state(rng)
    return _paths_eval(
        losses,
        delay,
        seed,
        {"p": p, "rho": rho, "delay": delay, "seed": seed, "dis": reg.dis, "sign": sign},
    )


def _paths_eval(losses, delay, seed, meta, names=None):
    import registry
    from simulator import run_episode
    from suite import build_suite, stream_from_losses

    T = losses.shape[0]
    d = losses[:, 0].astype(int) - losses[:, 1]
    out = []
    for pol in build_suite(
        T,
        200,
        5.0,
        0.05,
        0.05,
        delay,
        seed,
        2026110701,
        names=names or P23_POLICIES,
        extra=registry.EXTRA,
    ):
        preds, labels = stream_from_losses(losses, np.random.default_rng([seed, 7]))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=delay,
            budget=200,
            label_price=0.05,
            switch_cost=5.0,
            trace=True,
        )
        dep = np.array([r["deployed_model"] for r in res.records])
        req = np.array([r["requested"] for r in res.records])
        tr = np.diff(np.r_[0, dep])
        proms = []
        for tau in np.flatnonzero(tr == 1):
            nxt = np.flatnonzero(tr[tau + 1 :] != 0)
            end = tau + 1 + nxt[0] if len(nxt) else T
            q = np.flatnonzero(req[: max(tau - delay + 1, 0)] & (d[: max(tau - delay + 1, 0)] != 0))
            rec = {
                "tau": int(tau),
                "spell": int(end - tau),
                "A_spell": int(d[tau:end].sum()),
                "rolled_back": bool(len(nxt)),
            }
            for H in (100, 500):
                rec[f"A{H}"] = int(d[tau : tau + H].sum())
                h = np.arange(min(H, T - tau))
                if "rho" in meta:
                    p, rho, dis = meta["p"], meta["rho"], meta["dis"]
                    s0 = float(meta["sign"][tau])
                    rec[f"M{H}"] = float(dis * (2 * p - 1) * len(h))
                    rec[f"Cstate{H}"] = float(
                        dis * np.sum(2 * (rho**h * s0 + (1 - rho**h) * p) - 1)
                    )
                    if len(q):
                        zl, gl = float(d[q[-1]] > 0), tau - q[-1]
                        rec[f"Cpol{H}"] = float(
                            dis * np.sum(2 * (rho ** (h + gl) * zl + (1 - rho ** (h + gl)) * p) - 1)
                        )
                    else:
                        rec[f"Cpol{H}"] = rec[f"M{H}"]
                lo = max(tau - delay - 200, 0)  # realised advantage on the last 200 released events
                rec["recent200"] = float(d[lo : max(tau - delay, lo + 1)].mean())
            proms.append(rec)
        out.append(
            dict(
                {k: v for k, v in meta.items() if k != "sign"},
                policy=pol.name,
                net=res.net_cost,
                loss=res.prediction_loss,
                labels=res.requested_labels,
                switches=res.deployment_switches,
                promotions=proms,
            )
        )
    return out


def _twin_job(args):
    name, ep = args
    z = np.load(ROOT / f"data/sprint_twin_losses/{name}.npz")
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    import screen

    return _paths_eval(losses, screen._delay(name), ep, {"twin": name, "ep": ep}, TWIN_POLICIES)


def p2p3(argv):
    import argparse
    import multiprocessing as mp

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--twin-eps", type=int, default=40)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args(argv)
    grid = [(p, rho, dl) for p in (0.5, 0.65) for rho in (0.0, 0.8, 0.95) for dl in (1, 100)]
    grid += [(0.45, 0.8, 1), (0.45, 0.8, 100), (0.45, 0.95, 1), (0.45, 0.95, 100)]
    jobs = [g + (s,) for g in grid for s in range(a.seeds)]
    tj = []
    for n in ("appliances", "beijing_pm25", "bike_hour", "household_power", "metro"):
        E = np.load(ROOT / f"data/sprint_twin_losses/twin_{n}.npz")["l0"].shape[0]
        tj += [(f"twin_{n}", int(e)) for e in np.unique(np.linspace(0, E - 1, a.twin_eps).round())]
    with mp.Pool(a.workers) as pool:
        syn = [r for rows in pool.imap_unordered(_paths_job, jobs, chunksize=2) for r in rows]
        twin = [r for rows in pool.imap_unordered(_twin_job, tj, chunksize=2) for r in rows]
    return {"synthetic": syn, "twin": twin, "seeds": a.seeds, "twin_eps": a.twin_eps}


ANALYSES["p2p3"] = p2p3


# ---------------------------------------------------------------- P5: K-model streams and screen
def kbuild(argv):
    """K=4 real loss streams from the fresh UCI raw data (fresh_real loaders, same windows and
    train-only preprocessing): m0 LR[0,.15n), m1 HGB[0,.30n) (= the 2-model pair), m2 LR[0,.30n),
    m3 shallow HGB on the recent window [.15n,.30n)."""
    import hashlib

    import fresh_real as fr
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression

    outdir = ROOT / "outputs/sprint2/P/kstreams"
    outdir.mkdir(parents=True, exist_ok=True)
    stats = []
    for name in fr.LOADERS:
        x, yraw, _ts = fr.LOADERS[name]()
        cat = fr.CATEGORICAL.get(name, [])
        for c in cat:
            x[c] = x[c].astype(str)
        n = len(x)
        n15, n30 = int(0.15 * n), int(0.30 * n)
        y = (yraw.to_numpy() > float(np.median(yraw.to_numpy()[:n30]))).astype(int)
        f = fr.prep(x.iloc[:n30], cat)
        X30, X15 = f(x.iloc[:n30]), f(x.iloc[:n15])
        ms = [
            LogisticRegression(max_iter=300, C=1.0).fit(X15, y[:n15]),
            HistGradientBoostingClassifier(
                max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
            ).fit(X30, y[:n30]),
            LogisticRegression(max_iter=300, C=1.0).fit(X30, y[:n30]),
            HistGradientBoostingClassifier(
                max_iter=50, max_depth=2, learning_rate=0.1, random_state=0
            ).fit(X30[n15:], y[n15:n30]),
        ]
        k = min(fr.MAX_EPS, (n - n30) // fr.T_EP)
        end = n30 + k * fr.T_EP
        xe = f(x.iloc[n30:end])
        L = np.stack(
            [(m.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, fr.T_EP) for m in ms], axis=2
        )
        ref = np.load(ROOT / f"data/sprint_fresh_losses/{name}.npz")
        same = bool(np.array_equal(L[:, :, 0], ref["l0"]) and np.array_equal(L[:, :, 1], ref["l1"]))
        np.savez(outdir / f"{name}.npz", L=L)
        stats.append(
            {
                "dataset": name,
                "K": 4,
                "episodes": int(k),
                "err": [float(L[..., j].mean()) for j in range(4)],
                "matches_2model_cache": same,
                "delay": fr.DELAYS[name],
                "sha": hashlib.sha256(L.tobytes()).hexdigest()[:16],
            }
        )
    return {"streams": stats}


def _k_job(args):
    kind, name, ep, seed = args
    from simulator import policy_rng, run_episode
    from suite import stream_from_losses

    if kind == "syn":
        reg = K_REGIMES[name]
        losses = reg.sample(np.random.default_rng([2026110701, _h(name), seed]))
        gain, delay = reg.truth_gain(), reg.delay
    else:
        import fresh_real as fr

        L = np.load(ROOT / f"outputs/sprint2/P/kstreams/{name}.npz")["L"]
        losses = L[ep]
        gain = np.tile(losses[:, [0]].mean() - losses.mean(axis=0), (losses.shape[0], 1))
        delay = fr.DELAYS[name]
    T, K = losses.shape
    r = lambda nm: policy_rng(2026110701 + _h(name) % 1000, ep * 100_000 + seed, nm)
    rows = []
    for pname, pol in k_policies(K, T, 200, 0.05, r).items():
        preds, labels = stream_from_losses(losses, np.random.default_rng([seed, ep, 7]))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=delay,
            budget=200,
            label_price=0.05,
            switch_cost=5.0,
            trace=True,
        )
        assert res.requested_labels <= 200
        dep = np.array([x["deployed_model"] for x in res.records])
        g = gain[np.arange(T), dep]
        rows.append(
            {
                "kind": kind,
                "regime": name,
                "ep": ep,
                "seed": seed,
                "policy": pname,
                "net": res.net_cost,
                "labels": res.requested_labels,
                "switches": res.deployment_switches,
                "ever_switch": int((dep != 0).any()),
                "final": int(dep[-1]),
                "frac_on_harmful": float((g < 0).mean()),
                "ever_harmful": int((g < 0).any()),
                "ever_nonbetter": int((g <= 0)[dep != 0].any()) if (dep != 0).any() else 0,
            }
        )
    return rows


def _h(s):
    import hashlib

    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big")


def kscreen(argv):
    import argparse
    import multiprocessing as mp

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args(argv)
    jobs = [("syn", n, 0, s) for n in K_REGIMES for s in range(a.seeds)]
    if a.real:
        for f in sorted((ROOT / "outputs/sprint2/P/kstreams").glob("*.npz")):
            E = np.load(f)["L"].shape[0]
            jobs += [("real", f.stem, e, 0) for e in range(E)]
    with mp.Pool(a.workers) as pool:
        rows = [r for rr in pool.imap_unordered(_k_job, jobs, chunksize=2) for r in rr]
    return {"rows": rows}


ANALYSES["kbuild"] = kbuild
ANALYSES["kscreen"] = kscreen

if __name__ == "__main__":
    _main()
