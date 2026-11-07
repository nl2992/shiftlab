"""Sprint-2 WP1 (Agent E): RMM extensions for real late-improvement and reversal validation.

* ``E_rb:<host>``: RMM with B2-style certified rollback on each of RMM's four certificate hosts.
  It reuses ``fam_b.RecoveryMonitor(rollback=True)`` unchanged; fam_b only registered the gated host
  (``B2``). Rollback detector: restart-mixture SR e-detector at alpha_rb = .10 over a start grid on
  the budget left at promotion, horizon gate h_min = ceil(c_s / .1); re-promotions after a rollback
  spend halving shares. Error accounting is fam_b's: under the iid conditional null (challenger right
  w.p. <= 1/2 on queried disagreements, independently of the past) P(any promotion) <= alpha; a false
  rollback is a cost, not a safety error. Not covered: serial dependence, time-varying advantage.
* ``E_swcert``: a sliding-window certificate (no sliding-window or discounted certificate was
  registered). Paced disagreement acquisition (the shared uniform pacer); every ``every`` labels
  after ``min_n`` it runs the exact binomial test of "challenger right w.p. <= 1/2" on the last
  ``window`` label-clock outcomes (unweighted, signed so +1 = non-deployed model right) at level
  alpha_k = a * 6 / (pi^2 k^2) for the k-th test since the last switch. By the union bound over k,
  under the iid conditional null P(first false alarm) <= a, whatever the overlap between windows.
  a = alpha for the first promotion, alpha / 2^j for the j-th re-promotion, alpha for rollbacks.
  Valid null: V1 (iid conditional). Not covered: persistence.
* ``E_srr:<host>`` / ``E_srrSR:<host>``: the "host + off-the-shelf e-detector" competitor
  (novelty audit, docs/sprint2/novelty/NOVELTY.md section 1). Identical to RMM (same alpha split,
  same continued acquisition, same restart rule, same label-clock outcomes and bet grid) except the
  detector is a Shin-Ramdas-Rinaldo e-detector with a start at EVERY label and unit mass per start:
  e-CUSUM  M_n = max_{s<=n} mean_lambda prod_{k=s}^n (1 + lambda X_k), or
  e-SR     M_n = sum_{s<=n} mean_lambda prod_{k=s}^n (1 + lambda X_k),
  alarm at M_n >= 1/alpha_k. SRR guarantee: average run length to false alarm >= 1/alpha (in labels);
  the probability of ANY false alarm is NOT controlled (RMM's grid has total prior mass one, SRR's
  has mass one per start). The `edetect` CRAN package is R-only, so this is a Python
  re-implementation of the Bernoulli/bounded betting e-detector. Track V: none (ARL only).
* ``E_glr:<host>``: uncertified Bernoulli GLR restart reference (GLR-klUCB style, Besson et al.
  2022): alarm when max_s [s kl(mu_1:s, mu) + (n-s) kl(mu_s+1:n, mu)] >= log(3 n^1.5 / alpha_k) and
  the post-change mean favours the non-deployed model. Track V: none.
"""

from __future__ import annotations

import math

import fam_b  # loads the RMM module and the certificate hosts' import path
import numpy as np
from certificate_stops import DiscernStyleStop, GatedDeploymentStop
from controls import PacedDisagreementAcquisition
from scipy.stats import binom
from simulator import QueryRequest
from smcs import SMCSDeploymentPolicy
from strong_hosts import GatedAdaptiveRange

RecoveryMonitor = fam_b.RecoveryMonitor

# host name -> (base factory make(T, B, alpha, rng), private rng stream name used by registry RMM)
HOSTS = {
    "gated_deployment": (
        lambda T, B, a, r: GatedDeploymentStop(T, B, a, rng=r),
        "gated_deployment",
    ),
    "discern_style": (lambda T, B, a, r: DiscernStyleStop(T, B, a, 0.0, rng=r), "discern_style"),
    "SMCS+retain-incumbent": (lambda T, B, a, r: SMCSDeploymentPolicy(2, r, alpha=a), "smcs"),
    "gated_adaptive_range": (
        lambda T, B, a, r: GatedAdaptiveRange(T, B, a, rng=r),
        "gated_adaptive_range",
    ),
}


_RMM = fam_b._rmm


class SRRDetector:
    """Shin-Ramdas-Rinaldo betting e-detector (start at every label, mixture over lambda)."""

    def __init__(self, alpha, kind="cusum", lambdas=fam_b.HOST_LAMBDAS):
        self.alpha, self.kind = float(alpha), kind
        self.lams = np.asarray(lambdas, float)
        self.sr = np.zeros(len(self.lams))  # e-SR recursion per lambda
        self.prods = np.zeros((0, len(self.lams)))  # e-CUSUM: one row per start
        self.n = 0

    def update(self, x: int) -> bool:
        f = 1.0 + self.lams * x
        self.n += 1
        if self.kind == "sr":
            self.sr = (self.sr + 1.0) * f
            return self.stat >= 1.0 / self.alpha
        self.prods = np.vstack([self.prods, np.ones(len(self.lams))]) * f
        return self.stat >= 1.0 / self.alpha

    @property
    def stat(self) -> float:
        if self.kind == "sr":
            return float(self.sr.mean())
        return float(self.prods.mean(axis=1).max()) if len(self.prods) else 0.0


def _kl(p, q):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    q = np.clip(q, 1e-12, 1 - 1e-12)
    return p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))


class GLRDetector:
    """Bernoulli GLR change detector on z = 1[x > 0] (uncertified restart reference)."""

    def __init__(self, alpha, min_seg=5):
        self.alpha, self.min_seg = float(alpha), int(min_seg)
        self.z: list[int] = []
        self.n = 0

    def update(self, x: int) -> bool:
        self.z.append(int(x > 0))
        self.n += 1
        n = self.n
        if n < 2 * self.min_seg:
            return False
        z = np.asarray(self.z, float)
        c = np.cumsum(z)
        s = np.arange(self.min_seg, n - self.min_seg + 1)
        mu, m1, m2 = c[-1] / n, c[s - 1] / s, (c[-1] - c[s - 1]) / (n - s)
        g = s * _kl(m1, mu) + (n - s) * _kl(m2, mu)
        i = int(np.argmax(g))
        return bool(g[i] >= np.log(3 * n**1.5 / self.alpha) and m2[i] > 0.5)


class DetectorSwapMonitor(_RMM.RestartMixtureMonitor):
    """RMM with its restart-mixture detector replaced (everything else identical)."""

    def __init__(self, make_base, horizon, budget, alpha, *, rng, detector="cusum", **kw):
        self.detector = detector
        super().__init__(make_base, horizon, budget, alpha, rng=rng, name="", **kw)

    def _new_detector(self):
        a = self.alpha_det / (2.0**self.n_promotions) if self.deployed == 0 else self.alpha_rb
        if self.detector == "glr":
            return GLRDetector(a)
        return SRRDetector(a, kind=self.detector)


def _swap(host: str, detector: str, **kw):
    mk, sn = HOSTS[host]
    return lambda T, B, cs, cq, alpha, delay, r: DetectorSwapMonitor(
        mk, T, B, alpha, rng=r(sn), detector=detector, **kw
    )


def _rb(host: str, **kw):
    mk, sn = HOSTS[host]

    def f(T, B, cs, cq, alpha, delay, r):
        return RecoveryMonitor(mk, T, B, alpha, rng=r(sn), delay=delay, cs=cs, rollback=True, **kw)

    return f


class SlidingWindowCert:
    """Sliding-window binomial certificate with union-bound alpha spending (see module doc)."""

    def __init__(
        self,
        horizon,
        budget,
        alpha,
        *,
        rng,
        window=50,
        every=10,
        min_n=20,
        p_min=0.05,
        name="E_swcert",
    ):
        self.name = name
        self.T, self.B, self.alpha = int(horizon), int(budget), float(alpha)
        self.rng = rng
        self.window = None if window is None else int(window)
        self.every, self.min_n = int(every), int(min_n)
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.deployed = 0
        self.n_promotions = 0
        self.n_switches = 0
        self._reset()

    def _reset(self):
        self.x: list[int] = []
        self.k = 0
        self.order: list[int] = []
        self.queue: dict[int, int] = {}
        if self.deployed == 0:
            self.a = self.alpha / (2.0**self.n_promotions)
        else:
            self.a = self.alpha

    def predict(self, event) -> int:
        return self.deployed

    def request_labels(self, event, remaining_budget) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q > 0.0 and self.rng.random() < q:
            self.order.append(event.t)
            return QueryRequest(requested=True, probability=q)
        return QueryRequest(requested=False)

    def _test(self) -> bool:
        self.k += 1
        a_k = self.a * 6.0 / (math.pi**2 * self.k**2)
        w = self.x if self.window is None else self.x[-self.window :]
        s = sum(1 for v in w if v > 0)
        return float(binom.sf(s - 1, len(w), 0.5)) <= a_k  # P(S >= s) under p = 1/2

    def observe(self, feedback) -> None:
        for fb in feedback:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            self.queue[fb.event_id] = d
        alarm = False
        while self.order and self.order[0] in self.queue:
            d = self.queue.pop(self.order.pop(0))
            if d == 0:
                continue
            self.x.append(d if self.deployed == 0 else -d)
            n = len(self.x)
            if n >= self.min_n and n % self.every == 0 and self._test():
                alarm = True
                break
        if alarm:
            self.deployed = 1 - self.deployed
            self.n_switches += 1
            if self.deployed == 1:
                self.n_promotions += 1
            self._reset()

    def decision_state(self) -> str:
        return f"dep={self.deployed};sw={self.n_switches}"

    def state_dict(self) -> dict:
        return {}

    def load_state_dict(self, s: dict) -> None:
        pass


def _sw(**kw):
    return lambda T, B, cs, cq, alpha, delay, r: SlidingWindowCert(
        T, B, alpha, rng=r("E_swcert"), **kw
    )


EXTRA = {f"E_rb:{h}": _rb(h) for h in HOSTS}


def _rb_front_gated_adaptive_range(T, B, cs, cq, alpha, delay, r):
    """E_rb with the same correctly ranged Gated host and front-loaded acquisition."""

    def make_base(t, b, a, rng):
        return GatedAdaptiveRange(t, b, a, rng=rng, front=True, name="gated_adaptive_range+front")

    return RecoveryMonitor(
        make_base,
        T,
        B,
        alpha,
        rng=r("gated_adaptive_range"),
        delay=delay,
        cs=cs,
        rollback=True,
        name="E_rb:gated_adaptive_range+front",
    )


EXTRA["E_rb:gated_adaptive_range+front"] = _rb_front_gated_adaptive_range
EXTRA.update({f"E_srr:{h}": _swap(h, "cusum") for h in HOSTS})
EXTRA.update(
    {
        "E_srrSR:gated_deployment": _swap("gated_deployment", "sr"),
        "E_srr_noacq:gated_deployment": _swap("gated_deployment", "cusum", keep_acquiring=False),
        "E_srr_noacq:gated_adaptive_range": _swap(
            "gated_adaptive_range", "cusum", keep_acquiring=False
        ),
        "E_glr:gated_deployment": _swap("gated_deployment", "glr"),
        "E_glr:gated_adaptive_range": _swap("gated_adaptive_range", "glr"),
    }
)
EXTRA.update(
    {
        # rollback mechanism ablations (gated and gated_adaptive_range hosts)
        "E_rb:gated_deployment-nogate": _rb("gated_deployment", g_ref=1e9),
        "E_rb:gated_deployment-a05": _rb("gated_deployment", alpha_rb_new=0.05),
        "E_rb:gated_adaptive_range-nogate": _rb("gated_adaptive_range", g_ref=1e9),
        "E_swcert": _sw(),
        "E_swcert-W25": _sw(window=25),
        "E_swcert-W100": _sw(window=100),
        "E_swcert-cum": _sw(window=None),
    }
)

# Scoped budget-allocation ablation: keep total alpha and the detector fixed, but move 90% of
# the promotion budget to the faster restart detector. This is a configuration screen, not a
# new detector or a claim of anytime validity for SRR.
EXTRA["E_srrSR:split90:gated_deployment"] = _swap("gated_deployment", "sr", alpha_split=0.90)

# Track V: which null each candidate's promotion guarantee concerns (bench2.NULL_TESTED convention).
NULL_TESTED = {k: ("none" if k.startswith(("E_srr", "E_glr")) else "V1") for k in EXTRA}
