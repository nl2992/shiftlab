"""K-model policies for the BCR feasibility pilot (01_BASELINES.md, 04_METHOD_DESIGN.md).

Shared evidence (all Wald-family policies): on each released label, every model's 0/1 loss is
observed. With weight w = 1/q (q = frozen issue-time propensity) and label-clock discount lam,
discounted sums give, for each pair (i, j), the self-normalised IPW mean m_ij of l_i - l_j over
the *query region* R and its standard error (effective n = (sum w)^2 / sum w^2). Per-event
advantage = r_R * m_ij, with r_R the observed fraction of events in R (R = events where not all
models agree, or all events for uniform acquisition). Self-normalised IPW makes the estimate
consistent under any acquisition rule with q > 0 on R.

Deployment (KWald): at each release, V_j = (m_ij - z * se_ij) * r_R * (T - t) - c_s for the
deployed i; switch to argmax_j V_j if it is > 0. Acquisition modes:
  uniform : q = remaining / (T - t) on every event;
  anydis  : budget-paced over R events (the standard disagreement baseline);
  mp      : Model Picker's query probability (Karimi et al. 2021 port) on R events;
  bcr     : economic challenger set + decision-relevant acquisition (prototype, below).

BCR prototype. Plausible set P = {j != i : (m_ij + z_u * se_ij) * r_R * (T - t) > c_s}, i.e.
challengers whose optimistic remaining-horizon payback covers the switching cost. An R event is
*decision-relevant* if the models in {i} | P do not all agree. Relevant events are queried at a
budget-paced rate over the estimated number of remaining relevant events; non-relevant R events
at rate rho_mon times the base pacer (monitoring floor; keeps q > 0 so IPW stays valid). During
warm-up (fewer than n_warm released labels) BCR uses anydis.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
for _p in (
    ROOT / "scripts/promising_directions/sota",
    ROOT / "scripts/promising_directions/sota/competitors",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from model_picker import ModelPickerDeploymentAdapter, eta_t, posterior, query_probability
from simulator import QueryRequest


class KWald:
    def __init__(
        self,
        T,
        B,
        cs,
        K,
        rng,
        *,
        lam=0.85,
        gamma=0.15,
        acq="anydis",
        name="kwald",
        z_u=None,
        rho_mon=0.2,
        n_warm=20,
        p_min=0.02,
    ):
        self.name, self.T, self.B, self.cs, self.K, self.rng = name, T, B, cs, K, rng
        self.lam, self.z = lam, float(norm.ppf(1 - gamma))
        self.z_u = self.z if z_u is None else float(z_u)
        self.acq, self.rho_mon, self.n_warm, self.p_min = acq, rho_mon, n_warm, p_min
        self.deployed = 0
        self.t = 0
        self.Sw = self.Sw2 = 0.0
        self.Sl = np.zeros(K)
        self.Sll = np.zeros((K, K))
        self.n_lab = 0
        self.n_R = 0  # events in the query region so far
        self.n_rel = 0  # decision-relevant events so far (bcr)
        self.mp_loss = np.zeros(K)  # Model Picker IPW cumulative loss (acq="mp")
        self.switches = 0

    # ---------------------------------------------------------------- evidence
    def _pair(self, i, j):
        if self.Sw <= 0:
            return 0.0, 1.0
        m = (self.Sl[i] - self.Sl[j]) / self.Sw
        d2 = (self.Sl[i] + self.Sl[j] - 2 * self.Sll[i, j]) / self.Sw
        var = max(d2 - m * m, 1e-6)
        neff = self.Sw**2 / max(self.Sw2, 1e-12)
        return m, math.sqrt(var / (neff + 1.0))

    def _rate(self):
        if self.acq == "uniform":
            return 1.0
        return (self.n_R + 5.0) / (self.t + 10.0)

    def _values(self, zz):
        i, rem = self.deployed, self.T - self.t
        out = np.full(self.K, -np.inf)
        for j in range(self.K):
            if j != i:
                m, se = self._pair(i, j)
                out[j] = (m + zz * se) * self._rate() * rem - self.cs
        return out

    def plausible(self):
        return [j for j, v in enumerate(self._values(self.z_u)) if v > 0]

    # ---------------------------------------------------------------- policy API
    def predict(self, event):
        self.t = event.t
        return self.deployed

    def _base_q(self, remaining, region_rate):
        exp_left = max(region_rate * (self.T - self.t), 1e-9)
        return float(min(max(remaining / exp_left, self.p_min), 1.0))

    def request_labels(self, event, remaining):
        preds = np.asarray(event.model_predictions)
        inR = len(np.unique(preds)) > 1
        if self.acq == "uniform":
            q = min(1.0, remaining / max(self.T - self.t, 1))
        else:
            self.n_R += int(inR)
            if not inR or remaining <= 0:
                return QueryRequest(requested=False)
            if self.acq == "anydis" or (self.acq == "bcr" and self.n_lab < self.n_warm):
                q = self._base_q(remaining, self._rate())
            elif self.acq == "mp" or (self.acq == "emp" and self.n_lab < self.n_warm):
                eta = eta_t(self.K, event.t + 1)
                q = query_probability(posterior(self.mp_loss, eta), preds, 1.0, 2, eta)
                q = max(q, self.p_min)
            elif self.acq == "emp":
                # economic Model Picker: MP's posterior-disagreement probability computed only over
                # the economically plausible set S = {deployed} + plausible challengers; outside
                # S-disagreements, monitor at rho_mon x MP's full-set probability (q > 0 on R).
                eta = eta_t(self.K, event.t + 1)
                q_full = query_probability(posterior(self.mp_loss, eta), preds, 1.0, 2, eta)
                S = [self.deployed, *self.plausible()]
                if len(S) > 1 and len(np.unique(preds[S])) > 1:
                    eS = eta_t(len(S), event.t + 1)
                    q = query_probability(posterior(self.mp_loss[S], eS), preds[S], 1.0, 2, eS)
                else:
                    q = self.rho_mon * q_full
                q = max(q, self.p_min)
            else:  # bcr
                S = [self.deployed, *self.plausible()]
                rel = len(np.unique(preds[S])) > 1 if len(S) > 1 else False
                self.n_rel += int(rel)
                rel_rate = (self.n_rel + 2.0) / (self.t + 10.0)
                if rel:
                    q = self._base_q(remaining, rel_rate)
                else:
                    q = max(self.p_min, self.rho_mon * self._base_q(remaining, self._rate()))
        if remaining <= 0 or q <= 0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            l = np.asarray(fb.model_losses, dtype=float)
            w = 1.0 / fb.query_probability
            lam = self.lam
            self.Sw = lam * self.Sw + w
            self.Sw2 = lam * lam * self.Sw2 + w * w
            self.Sl = lam * self.Sl + w * l
            self.Sll = lam * self.Sll + w * np.outer(l, l)
            self.mp_loss = self.mp_loss + l * w
            self.n_lab += 1
            self.t = fb.t_released
            v = self._values(-self.z)
            j = int(np.argmax(v))
            if v[j] > 0:
                self.deployed = j
                self.switches += 1

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


class Never:
    def __init__(self, T, B, cs, K, rng, name="never"):
        self.name = name

    def predict(self, event):
        return 0

    def request_labels(self, event, remaining):
        return QueryRequest(requested=False)

    def observe(self, feedback):
        pass

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


class MPAdapter(ModelPickerDeploymentAdapter):
    """B3: the repo's fidelity-audited Model Picker deployment adapter (argmin IPW loss)."""

    def __init__(self, T, B, cs, K, rng, name="model_picker"):
        super().__init__(K, 2, rng)
        self.name = name


def _kw(**kw):
    def make(T, B, cs, K, r):
        return KWald(T, B, cs, K, r, **kw)

    return make


def registry(stage="pilot"):
    R = {"never": lambda T, B, cs, K, r: Never(T, B, cs, K, r)}
    R["model_picker"] = lambda T, B, cs, K, r: MPAdapter(T, B, cs, K, r)
    for lam in (0.85, 0.9, 0.95):
        for g in (0.05, 0.1, 0.15, 0.25):
            for acq in ("uniform", "anydis", "mp"):
                n = f"kw_{acq}_l{lam}_g{g}"
                R[n] = _kw(lam=lam, gamma=g, acq=acq, name=n)
            for zu in (0.5, 1.5):
                for rm in (0.1, 0.3):
                    n = f"bcr_l{lam}_g{g}_zu{zu}_rm{rm}"
                    R[n] = _kw(lam=lam, gamma=g, acq="bcr", z_u=zu, rho_mon=rm, name=n)
                    n = f"emp_l{lam}_g{g}_zu{zu}_rm{rm}"
                    R[n] = _kw(lam=lam, gamma=g, acq="emp", z_u=zu, rho_mon=rm, name=n)
    return R
