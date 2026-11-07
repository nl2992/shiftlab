"""CPU-sized synthetic drift stream (NOT the paper's SyntheticDrift-CIFAR; see docs).  Evaluator-side
truth (drift type/onset, true risk) lives in ``truth_*`` methods and is never passed to the controller."""

from __future__ import annotations

import numpy as np

from .belief import DRIFTS

D_FEAT = 8
MU = 1.6


def _fit_logreg(X, y, l2=1e-2, iters=15):
    Xb = np.hstack([X, np.ones((len(X), 1))])
    w = np.zeros(Xb.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Xb @ w, -30, 30)))
        g = Xb.T @ (p - y) + l2 * w
        H = (Xb * (p * (1 - p))[:, None]).T @ Xb + l2 * np.eye(len(w))
        w = w - np.linalg.solve(H, g)
    return w


class Model:
    def __init__(self, w, off):
        self.w, self.off = np.array(w, float), np.array(off, float)

    def proba(self, X):
        return 1 / (1 + np.exp(-np.clip((X - self.off) @ self.w[:-1] + self.w[-1], -30, 30)))

    def copy(self):
        return Model(self.w, self.off)


class SyntheticStreamEnv:
    def __init__(self, seed: int, L=1500, drift=None, schedule=None, onset=None, theta_sel=0.6):
        rng = np.random.default_rng(seed)
        self.L, self.theta_sel = L, theta_sel
        d = DRIFTS[int(rng.integers(1, 4))]
        self.drift = d if drift is None else drift  # hidden
        o = int(rng.integers(300, 601))
        self.onset = o if onset is None else onset  # hidden
        sch = ("step", "logistic", "periodic")[int(rng.integers(0, 3))]
        self.schedule = sch if schedule is None else schedule
        self.period = int(rng.integers(300, 600))
        self.u = np.zeros(D_FEAT)
        self.u[0] = 1
        self.wdir = np.zeros(D_FEAT)
        self.wdir[1] = 1
        self.y = rng.integers(0, 2, L)
        self.g = (rng.random(L) < 0.15).astype(int)
        self.noise = rng.standard_normal((L, D_FEAT))
        self.X = np.concatenate(
            [self._gen(self.noise[t], self.y[t], self.g[t], t) for t in range(L)]
        )
        self.ev_n = rng.standard_normal((600, D_FEAT))
        self.ev_y = rng.integers(0, 2, 600)
        self.ev_g = np.r_[np.zeros(300, int), np.ones(300, int)]
        Xtr, ytr = self._clean(2000, rng)
        self.model = Model(_fit_logreg(Xtr, ytr), np.zeros(D_FEAT))
        self.safe = self.model.copy()
        self.initial = self.model.copy()
        self.Xref, self.yref = self._clean(2048, rng)
        self.ref_mean = self.Xref.mean(0)
        self.H_ref = self._entropy(self.model.proba(self.Xref)).mean()
        self.ece_ref = self._ece(self.model.proba(self.Xref), self.yref)
        self.abstain = False

    def alpha(self, t):
        s = t - self.onset
        if s < 0:
            return 0.0
        if self.schedule == "step":
            return 1.0
        if self.schedule == "logistic":
            return float(1 / (1 + np.exp(-(s - 100) / 25)))
        return float(0.5 * (1 - np.cos(2 * np.pi * s / self.period)))

    def _gen(self, n, y, g, t, alpha=None):
        """Vectorised: n (k,D), y (k,), g (k,) arrays or scalars."""
        a = self.alpha(t) if alpha is None else alpha
        n = np.atleast_2d(n)
        y = np.atleast_1d(y)
        g = np.atleast_1d(g)
        sgn = (2 * y - 1)[:, None].astype(float)
        if self.drift == "concept":
            phi = a * np.deg2rad(70)
            m = sgn * MU * (np.cos(phi) * self.u + np.sin(phi) * self.wdir)
        elif self.drift == "subgroup":
            m = sgn * MU * (1 - 2 * 0.9 * a * g)[:, None] * self.u
        else:
            m = sgn * MU * self.u
        x = m + n
        if self.drift == "covariate":
            x = x + a * 2.0 * self.u
        return x

    def _clean(self, n, rng):
        y = rng.integers(0, 2, n)
        return (2 * y - 1)[:, None] * MU * self.u + rng.standard_normal((n, D_FEAT)), y

    @staticmethod
    def _entropy(p):
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return -(p * np.log(p) + (1 - p) * np.log(1 - p))

    @staticmethod
    def _ece(p, y, bins=10):
        conf = np.maximum(p, 1 - p)
        pred = (p > 0.5).astype(int)
        e = 0.0
        edges = np.linspace(0.5, 1.0, bins + 1)
        k = np.clip(np.digitize(conf, edges) - 1, 0, bins - 1)
        for j in range(bins):
            m = k == j
            if m.any():
                e += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
        return e

    # ---- controller-facing API ----
    def oracle(self, i):  # only reachable via LabelStore
        return int(self.y[i])

    def predict(self, idx):
        return (self.model.proba(self.X[np.asarray(idx)]) > 0.5).astype(int)

    def monitor(self, t, labels):
        R = self.X[max(0, t - 255) : t + 1]
        rng = np.random.default_rng(t)
        r = R[rng.choice(len(R), min(len(R), 96), replace=False)]
        f = self.Xref[rng.choice(len(self.Xref), 192, replace=False)]

        def k(a, b):
            return np.exp(-((a[:, None, :] - b[None]) ** 2).sum(-1) / (2 * D_FEAT))

        mmd = k(r, r).mean() + k(f, f).mean() - 2 * k(r, f).mean()
        dH = self._entropy(self.model.proba(R)).mean() - self.H_ref
        ids = [i for i in labels if i >= t - 511]
        dece = 0.0
        if len(ids) >= 150:
            dece = (
                self._ece(self.model.proba(self.X[ids]), np.array([labels[i] for i in ids]))
                - self.ece_ref
            )
        return np.array([mmd, dH, dece])

    def has_distinct_checkpoint(self):
        return not (
            np.allclose(self.safe.w, self.model.w) and np.allclose(self.safe.off, self.model.off)
        )

    def mark_safe(self):
        self.safe = self.model.copy()

    def apply(self, a, t, labels):
        ids = [i for i in labels if i >= t - 599]
        if a == 1:  # recalibrate intercept on released labels (last 512 steps)
            ids = [i for i in ids if i >= t - 511]
            if len(ids) >= 20:
                y = np.array([labels[i] for i in ids])
                z = (self.X[ids] - self.model.off) @ self.model.w[:-1]
                b = float(self.model.w[-1])
                for _ in range(15):
                    p = 1 / (1 + np.exp(-np.clip(z + b, -30, 30)))
                    b -= float((p - y).sum() / max(1e-6, (p * (1 - p)).sum()))
                self.model.w[-1] = b
        elif a == 2:  # TTA: re-centre inputs using unlabeled recent buffer
            self.model.off = self.X[max(0, t - 255) : t + 1].mean(0) - self.ref_mean
        elif a == 4:  # retrain on released labels (last 600 steps)
            y = np.array([labels[i] for i in ids])
            if len(ids) >= 30 and 0 < y.mean() < 1:
                self.model = Model(_fit_logreg(self.X[ids], y, l2=1.0), np.zeros(D_FEAT))
        elif a == 5:
            self.model = self.safe.copy()

    # ---- evaluator-side truth ----
    def truth_state(self, t):
        return 0 if t < self.onset else DRIFTS.index(self.drift)

    def truth_eval(self, t, abstain=False):
        a = self.alpha(t)
        X = self._gen(self.ev_n, self.ev_y, self.ev_g, t, a)
        p = self.model.proba(X)
        correct = (p > 0.5).astype(int) == self.ev_y
        if abstain:
            correct = correct | (np.maximum(p, 1 - p) < self.theta_sel)
        acc = [float(correct[self.ev_g == g].mean()) for g in (0, 1)]
        # stream prevalence of the minority group is 0.15 (the eval sample is stratified 300/300 -> reweight)
        return 1 - (0.85 * acc[0] + 0.15 * acc[1]), min(acc)
