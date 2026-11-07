"""Pluggable components: learners, drift detectors, corruption pre-filter, swappable hooks."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np


# ------------------------------------------------------------------ learners
class Learner(Protocol):
    def predict(self, x: np.ndarray) -> int: ...


class LearnerFactory(Protocol):
    def fit(self, X: np.ndarray, y: np.ndarray) -> Learner: ...


class MajorityLearner:
    def __init__(self, label: int = 0):
        self.label = int(label)

    def predict(self, x):
        return self.label


class MajorityFactory:
    def fit(self, X, y):
        y = np.asarray(y)
        return MajorityLearner(int(np.bincount(y.astype(int)).argmax()) if len(y) else 0)


class StumpLearner:
    """Single-feature threshold classifier (CPU-trivial; used in tests)."""

    def __init__(self, j, thr, left, right):
        self.j, self.thr, self.left, self.right = j, thr, left, right

    def predict(self, x):
        return self.left if x[self.j] <= self.thr else self.right


class StumpFactory:
    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y).astype(int)
        best = (-1.0, 0, 0.0, 0, 0)
        for j in range(X.shape[1]):
            thr = float(np.median(X[:, j]))
            m = X[:, j] <= thr
            for l, r in ((0, 1), (1, 0)):
                acc = (np.where(m, l, r) == y).mean()
                if acc > best[0]:
                    best = (acc, j, thr, l, r)
        return StumpLearner(*best[1:])


class RiverHoeffdingTreeFactory:
    """River HoeffdingTreeClassifier, refit from scratch on each window (paper: Hoeffding-tree learner)."""

    def __init__(self, **kw):
        self.kw = kw

    def fit(self, X, y):
        from river import tree

        m = tree.HoeffdingTreeClassifier(**self.kw)
        for xi, yi in zip(X, y):
            m.learn_one({k: v for k, v in enumerate(xi)}, int(yi))
        return _RiverWrap(m)


class _RiverWrap:
    def __init__(self, m):
        self.m = m

    def predict(self, x):
        p = self.m.predict_one({k: v for k, v in enumerate(x)})
        return 0 if p is None else int(p)


# ------------------------------------------------------------------ detectors
class Detector(Protocol):
    def update(self, err: int) -> bool: ...
    def reset(self) -> None: ...
    @property
    def width(self) -> int: ...


class ADWINDetector:
    def __init__(self, delta: float = 0.002):
        from river import drift

        self._mk = lambda: drift.ADWIN(delta=delta)
        self.d = self._mk()

    def update(self, err):
        self.d.update(float(err))
        return bool(self.d.drift_detected)

    def reset(self):
        self.d = self._mk()

    @property
    def width(self):
        return int(self.d.width)


class ScriptedDetector:
    """Test detector: fires at the listed update counts (1-indexed since last reset-free start)."""

    def __init__(self, fire_at: Sequence[int]):
        self.fire_at = set(fire_at)
        self.n = 0
        self._w = 1

    def update(self, err):
        self.n += 1
        self._w += 1
        return self.n in self.fire_at

    def reset(self):
        self._w = 1

    @property
    def width(self):
        return 1


# ------------------------------------------------------------------ corruption pre-filter q_t
class StepSizeQuality:
    """Step-size check on the mean absolute successive difference (Sec 4.5, reconstruction).

    Baseline scale fitted on a train-only prefix; an instance is 'corrupt' when the rolling mean
    absolute successive difference of standardised features exceeds ratio * baseline.
    NaN/inf instances are always corrupt.
    """

    def __init__(self, window=30, ratio=3.0):
        self.w, self.ratio = window, ratio
        self.scale = None
        self.base = None
        self.buf = deque(maxlen=window)
        self.prev = None

    def fit(self, X):
        X = np.asarray(X, float)
        self.mu = X.mean(0)
        sd = X.std(0)
        self.scale = np.where(
            sd > 1e-6 * (np.abs(self.mu) + 1.0), sd, np.abs(self.mu) + 1.0
        )  # constant-in-prefix features
        d = np.abs(np.diff((X - self.mu) / self.scale, axis=0)).mean(1)
        self.base = float(d.mean()) + 1e-9

    def corrupt(self, x) -> bool:
        x = np.asarray(x, float)
        if not np.all(np.isfinite(x)):
            return True
        if self.scale is None:
            return False
        z = (x - self.mu) / self.scale
        if self.prev is not None:
            self.buf.append(float(np.abs(z - self.prev).mean()))
        self.prev = z
        if len(self.buf) < self.w:
            return False
        return float(np.mean(self.buf)) > self.ratio * self.base

    def reset(self):
        self.buf.clear()
        self.prev = None


# ------------------------------------------------------------------ swappable hooks
@dataclass
class HookContext:
    """Read-only view handed to hooks. Contains no unreleased labels and no oracle information."""

    t: int
    state: str
    tau: int
    cfg: object
    n_labels_released: int
    n_pending: int
    routed_to_new: bool
    canary_stage: int
    labeled_in_window: int  # Gate-2 numerator (labels released in anchored W_train window)
    t_hat_d: int | None
    acc_pre: float | None
    acc_cur: float | None
    rho: float


class LabelRequestPolicy(Protocol):
    """Hook (a): decide at serve time whether to request the label of instance t."""

    def request(self, ctx: HookContext) -> bool: ...


class AllLabelsPolicy:
    """RAR's native assumption: every label eventually arrives (free)."""

    def request(self, ctx):
        return True


class FractionLabelPolicy:
    """Deterministic every-k-th request (example swap-in; also a test helper)."""

    def __init__(self, k: int = 2):
        self.k = k

    def request(self, ctx):
        return ctx.t % self.k == 0


class GateRule(Protocol):
    """Hooks (b): Gate-2 / Gate-3 decision rule. Returns True if the gate passes."""

    def passes(self, ctx: HookContext) -> bool: ...


class ThetaLGate:
    """Native Gate 2: l_t(W_train) >= theta_L."""

    def passes(self, ctx):
        return ctx.labeled_in_window >= ctx.cfg.theta_L * ctx.cfg.W_train - 1e-9


class ThetaRGate:
    """Native Gate 3: A_pre - A_cur >= theta_R."""

    def passes(self, ctx):
        if ctx.acc_pre is None or ctx.acc_cur is None:
            return False
        return (ctx.acc_pre - ctx.acc_cur) >= ctx.cfg.theta_R - 1e-12
