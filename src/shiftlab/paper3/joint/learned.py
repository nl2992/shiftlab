"""A4: learned continuation value over causal features (numpy inference; torch only in training).

Q(f, a, q) = expected cost-to-go from the current round (relative to never-switch, fees included)
when taking (a, q) now and following the behaviour policy afterwards, regressed on TRAIN seeds.
Features use only PolicyView-derived quantities (belief summary, pending count, budget, time left,
deployed model, costs). Targets use the simulator's realised future losses (training only).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from ..contracts import Paper3Decision, PolicyView
from .belief import BeliefCore
from .policies import QVOI, DualPrice, _JointBase

WEIGHTS = Path(__file__).resolve().parents[4] / "outputs" / "paper3" / "joint" / "a4" / "q_net.npz"
NFEAT = 14
_NET: dict = {}


def features(core: BeliefCore, view: PolicyView, spec, d: int) -> np.ndarray:
    t, T, B, k = view.t, spec.T, max(spec.B, 1), spec.costs.k
    n = T - t + 1
    w, pi = core.weights(), core.pi_at(t)
    r = core.r_hat()
    gL, gH = r * (2 * core.pL - 1), r * (2 * core.pH - 1)
    lam = core.lam
    neff = (1 - lam**n) / np.maximum(1 - lam, 1e-9)
    Bn = n * (gL + (gH - gL) * core.pinf) + (gH - gL) * (pi - core.pinf) * neff
    sd_in = np.abs(gH - gL) * neff * np.sqrt(pi * (1 - pi))
    mean = float(np.sum(w * Bn))
    sd = math.sqrt(float(np.sum(w * sd_in**2) + np.sum(w * (Bn - mean) ** 2))) + 1e-6
    ent = float(-np.sum(w * np.log(np.maximum(w, 1e-12))) / math.log(len(w)))
    sgn = 1.0 if view.prev_action == 0 else -1.0
    marg = sgn * mean - k  # net payoff of switching away from the incumbent
    f = [
        marg / 10.0,
        sd / 10.0,
        marg / sd,
        math.tanh(mean / 10.0),
        view.prev_action,
        view.labels_remaining / B,
        view.labels_pending / B,
        (T - t) / T,
        (T - t - d) / T,
        k / 10.0,
        spec.costs.c_q * 10,
        r,
        ent,
        float(view.event.disagree),
    ]
    return np.array(f, float)


class LearnedContinuation(_JointBase):
    """argmin_(a,q) Q with margins; hold-previous-action unless Q improves by margin_a."""

    def __init__(self, margin_q=0.0, margin_a=0.0, path: str | None = None, name="A4"):
        super().__init__(None, 18, 1.0)
        self.margin_q, self.margin_a, self.name = margin_q, margin_a, name
        self.path = str(path or WEIGHTS)

    def _net(self):
        if self.path not in _NET:
            z = np.load(self.path)
            _NET[self.path] = {k: z[k] for k in z.files}
        return _NET[self.path]

    def q_values(self, f: np.ndarray) -> np.ndarray:
        W = self._net()
        out = np.zeros((2, 2))
        X = np.zeros((4, NFEAT + 2))
        for i, (a, q) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            X[i, :NFEAT], X[i, NFEAT], X[i, NFEAT + 1] = f, a, q
        h = (X - W["mu"]) / W["sd"]
        h = np.maximum(h @ W["w1"] + W["b1"], 0)
        h = np.maximum(h @ W["w2"] + W["b2"], 0)
        y = (h @ W["w3"] + W["b3"])[:, 0] * W["ysd"] + W["ymu"]
        out[0, 0], out[0, 1], out[1, 0], out[1, 1] = y
        return out

    def act(self, view: PolicyView) -> Paper3Decision:
        core = self.core
        core.ingest(view)
        d = core.d_hat()
        Q = self.q_values(features(core, view, self.spec, d))
        dep = view.prev_action
        a = dep
        if Q[1 - dep].min() + self.margin_a < Q[dep].min():
            a = 1 - dep
        q = 0
        if self._can_query(view, d) and Q[a, 1] + self.margin_q < Q[a, 0]:
            q = 1
        return self._finish(view, a, q)


class Recorder(_JointBase):
    """Training-data collector: wraps a behaviour policy, forces random (a,q) with prob eps."""

    def __init__(self, inner: _JointBase, eps: float = 0.1):
        super().__init__(None, 18, 1.0)
        self.inner, self.eps, self.name = inner, eps, "recorder"

    def reset(self, spec, rng):
        self.inner.reset(spec, rng)
        self.spec, self.rng = spec, rng
        self.feats: dict[int, np.ndarray] = {}

    def act(self, view: PolicyView) -> Paper3Decision:
        dec = self.inner.act(view)
        core = self.inner.core
        d = core.d_hat()
        canq = self.inner._can_query(view, d)
        a, q = dec.action, dec.query
        if canq or core.new_obs or view.t == 1:
            self.feats[view.t] = features(core, view, self.spec, d)
            if self.rng.random() < self.eps:
                a = int(self.rng.integers(2))
                q2 = int(self.rng.integers(2)) if canq else 0
                if q and not q2:
                    core.pending.remove(view.t)
                if q2 and not q:
                    core.note_query(view.t)
                q = q2
        return Paper3Decision(a, q)


__all__ = ["QVOI", "DualPrice", "LearnedContinuation", "Recorder", "features"]
