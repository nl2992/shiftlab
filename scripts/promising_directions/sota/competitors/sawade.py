"""Sawade, Landwehr & Scheffer, "Active Comparison of Prediction Models" (NeurIPS 2012).

Source: https://proceedings.neurips.cc/paper_files/paper/2012/file/
92fb0c6d1758261f10d052e6e2c1123c-Paper.pdf  (text extracted with ``pdftotext -layout``; the
equations below are transcribed from that extraction and the Derivation 4 radicals were
re-derived by hand, see "Derivation 4 check").  No author code was used or is claimed.

WHY THIS FILE EXISTS, AND A CITATION OBLIGATION
-----------------------------------------------
This paper is the *source* of the acquisition degeneracy that our earlier records presented as a
finding.  Section 3.2, directly under Derivation 4, states (verbatim):

    "Instead of using Approximation 13, an uninformative approximation p(y = 1|x) ~ 0.5 may be
    used. In this case q* degenerates to uniform sampling from the subset of the pool where
    f1(x) != f2(x). We denote this baseline as active!=. This baseline coincides with the A^2 as
    well as the IWAL active learning algorithms, applied to the model space {f1, f2}, as can be
    seen from inspection of Algorithm 1 in [1] and Algorithms 1 and 2 in [2]."

Anything we say about disagreement-gated sampling for two models must cite this paper.

Equations ported (numbers are the paper's)
------------------------------------------
Eq. (3)  importance-weighted risk estimate, with W the sum of weights (self-normalised):

    R^_{n,q}[f_j] = (1/W) sum_{i=1..n} p(x_i)/q(x_i) * l(f_j(x_i), y_i),
    (x_i, y_i) ~ q(x) p(y|x),   W = sum_{i=1..n} p(x_i)/q(x_i)

Eq. (13) mixture approximation of the unknown conditional:

    p(y|x) ~ (1/2) p(y|x; theta_1) + (1/2) p(y|x; theta_2)

    The risk difference Delta is replaced by "a difference Delta_theta of introspective risks
    calculated from Equation 1, where the integral over X is replaced by a sum over the pool,
    p(x) = 1/m, and p(y|x) is approximated by Equation 13."

Theorem 1 (optimal sampling distribution), Delta = R[f1] - R[f2] != 0:

    q*(x) ∝ p(x) sqrt( ∫ ( l(f1(x),y) - l(f2(x),y) - Delta )^2 p(y|x) dy )

Derivation 4 (zero-one loss, binary, p(y|x) as in Eq. 13), "for all x in D":

    q*(x) ∝ |Delta_theta|                                          if f1(x) = f2(x)
    q*(x) ∝ sqrt( 1 - 2 Delta_theta (1 - 2 p(y=1|x;theta)) + Delta_theta^2 )   if f1(x) > f2(x)
    q*(x) ∝ sqrt( 1 + 2 Delta_theta (1 - 2 p(y=1|x;theta)) + Delta_theta^2 )   if f1(x) < f2(x)

Algorithm 1: draw x_i ~ q* from the pool WITH replacement for i = 1..n, query y_i ~ p(y|x_i),
compute R^_{n,q}[f1], R^_{n,q}[f2] (Eq. 3), "Determine f* <- argmin_{f in {f1,f2}} R^_{n,q}[f]".

Derivation 4 check (done by hand and re-done in the test file)
-------------------------------------------------------------
With f1(x)=1, f2(x)=0: l1 - l2 = 1 - 2y, so E_y (1-2y-Delta)^2 = p(1+Delta)^2 + (1-p)(1-Delta)^2
= 1 - 2 Delta (1-2p) + Delta^2.  With f1(x)=0, f2(x)=1 the sign flips.  Under agreement
l1 - l2 = 0 and the integrand is Delta^2, so q* ∝ |Delta|.  This matches the extracted text.
The extraction lost the radical glyphs on the first line; the derivation above fixes it:
no square root is needed there because sqrt(Delta^2) = |Delta|.

A CONSEQUENCE WE PROVE AND TEST (not stated in the paper)
---------------------------------------------------------
Since (1 - 2p) lies in [-1, 1], on the disagreement region

    1 - |Delta_theta|  <=  q~(x)  <=  1 + |Delta_theta|,

so for two models with 0/1 loss, a calibrated p(y|x) can move the sampling weight of any two
disagreement points apart by a factor of at most (1+|Delta|)/(1-|Delta|).  Instance information
is real but is bounded by the size of the *introspective* risk gap, which is the quantity the
comparison is trying to resolve.  The test file measures this on our data.

Streaming adaptation (ALL of this is ours, not the paper's)
-----------------------------------------------------------
The paper is a pool-based, fixed-budget, with-replacement, non-sequential design with a Wald test
at the end.  The simulator is a stream with delayed labels and a deployment decision, so:

# ADAPTER: pool-based -> stream.  q* is evaluated on a DEVELOPMENT pool (the paper's "pool D")
#   to fix the shape and normalisation; each arriving event is then included independently with
#   a frozen probability  pi_t = clip(c_t * q~(x_t), p_floor, 1)  on {q~ > 0}.  The with-
#   replacement draw of Algorithm 1 becomes without-replacement Bernoulli (Poisson) inclusion.
# ADAPTER: pacing.  c_t is re-solved at every event so that the expected number of remaining
#   queries over the remaining sampling window equals the remaining budget (mean dev-pool pi
#   times events left = remaining).  The paper has a fixed n and no pacing; without it the hard
#   cap would truncate sampling on a stream whose disagreement rate differs from dev.  pi_t is
#   still a function of the past only and is frozen at issue, so 1/pi_t is the exact weight.
# ADAPTER: propensity floor.  The paper has none (it needs only p(x)>0 => q(x)>0, text before
#   Eq. 13).  We enforce pi >= p_floor wherever q~ > 0 so inverse-propensity weights are bounded.
# ADAPTER: agreement region under active!=.  q~ = 0 there (|Delta_theta| = 0 when p = 0.5), as
#   in the paper.  Both models have loss exactly equal there, so the paired difference is
#   identified without those labels; but the per-model risks of Eq. 3 are NOT estimated by
#   active!= (the paper's own degenerate form has this property).  We deploy on the difference.
# ADAPTER: Eq. 13 needs p(y|x; theta_j) from probabilistic models; ours are hard classifiers.
#   SawadeCalibrated replaces the Eq. 13 mixture by one calibrated p(y=1|x) fitted on
#   DEVELOPMENT data only (``CalibratedPosterior``).  This is Sawade's own stated hedge.
# ADAPTER: deployment rule.  The paper compares risks and reports a p-value; it does not
#   deploy anything.  Ours: stay on the incumbent (index 0) during the sampling window, commit
#   once the window has closed or the budget is spent AND every issued label has been released,
#   then deploy argmin of the Eq. 3 estimates (strict improvement needed to leave index 0).
#   No switching-cost economics are used: that is the point of the comparison.
# ADAPTER: Section 3.2 closing remark on repeated draws ("the loop is continued until the
#   labeling budget is exhausted") is irrelevant here: sampling is without replacement.
# ADAPTER: ``window_frac`` (fraction of the horizon over which the budget is spent) is a free
#   parameter the paper does not have.  Tune it on development data, never on the locked window.
# NOT PORTED: Eq. (4)/(5) Wald statistic and p-value.  They are not used for deployment, and
#   the extraction of Eq. 4 is ambiguous about the weight normalisation, so we do not guess.
# BLOCKED: only two-model comparison is implemented.  Eq. (15) (mixture of pairwise q*_{i,j}
#   for k models) is not ported because the SOTA suite compares one incumbent and one challenger.
# BLOCKED: no author code was available, so nothing here is checked against a reference
#   implementation; fidelity rests on the hand-checked Derivation 4 and the tests.

Estimator facts used by the tests
---------------------------------
With inclusion probability pi_i and weight w_i = 1/pi_i, the Horvitz-Thompson sum
sum_i Z_i w_i (l0_i - l1_i) is exactly unbiased for sum_i (l0_i - l1_i).  Eq. 3 divides by
W = sum Z_i w_i, which is the *same* denominator for both models, so sign(R^[f0] - R^[f1]) equals
the sign of the HT sum.  Eq. 3 itself is only consistent, not unbiased.
"""

from __future__ import annotations

import numpy as np
from simulator import Event, QueryRequest, ReleasedFeedback

_MAX_POOL = 1000


# --------------------------------------------------------------------------- Derivation 4
def zero_one_expected_loss(pred: np.ndarray, p1: np.ndarray) -> np.ndarray:
    """E_{y ~ Bernoulli(p1)} of the zero-one loss of a hard prediction (0 or 1)."""
    pred = np.asarray(pred)
    p1 = np.asarray(p1, dtype=float)
    return np.where(pred == 1, 1.0 - p1, p1)


def introspective_delta(pred0: np.ndarray, pred1: np.ndarray, p1: np.ndarray) -> float:
    """Delta_theta = mean over the pool of E_y[l(f1(x),y)] - E_y[l(f2(x),y)] (p(x)=1/m)."""
    return float(np.mean(zero_one_expected_loss(pred0, p1) - zero_one_expected_loss(pred1, p1)))


def derivation4_weight(pred0, pred1, p1, delta: float) -> np.ndarray:
    """Unnormalised q*(x) of Derivation 4. Model 0 is the paper's f1, model 1 is f2."""
    pred0, pred1 = np.asarray(pred0), np.asarray(pred1)
    p1 = np.asarray(p1, dtype=float)
    s = 2.0 * delta * (1.0 - 2.0 * p1)
    f1_gt = pred0 > pred1
    f1_lt = pred0 < pred1
    out = np.full(np.broadcast(pred0, pred1, p1).shape, abs(delta), dtype=float)
    out = np.where(f1_gt, np.sqrt(np.maximum(1.0 - s + delta**2, 0.0)), out)
    out = np.where(f1_lt, np.sqrt(np.maximum(1.0 + s + delta**2, 0.0)), out)
    return out


def sampling_distribution(pred0, pred1, p1) -> tuple[np.ndarray, float]:
    """The paper's pool-based q* (normalised over the pool) and its Delta_theta."""
    delta = introspective_delta(pred0, pred1, p1)
    w = derivation4_weight(pred0, pred1, p1, delta)
    return w / w.sum(), delta


def propensity(q_tilde: np.ndarray, c: float, p_floor: float) -> np.ndarray:
    """pi = clip(c * q~, p_floor, 1) where q~ > 0, else 0. ADAPTER (floor, scale)."""
    pi = np.minimum(c * q_tilde, 1.0)
    return np.where(q_tilde > 0, np.maximum(pi, p_floor), 0.0)


def solve_scale(q_pool: np.ndarray, p_floor: float, target_per_event: float) -> float:
    """Smallest-effort scale c with mean(pi(q_pool; c)) = target; monotone, solved by bisection."""
    hi_c = 1e8
    if propensity(q_pool, hi_c, p_floor).mean() <= target_per_event:
        return hi_c
    lo, hi = -8.0, 8.0  # log10 c
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if propensity(q_pool, 10.0**mid, p_floor).mean() < target_per_event:
            lo = mid
        else:
            hi = mid
    return 10.0 ** (0.5 * (lo + hi))


# --------------------------------------------------------------------------- calibration
def _features(context, preds: np.ndarray) -> np.ndarray:
    preds = np.asarray(preds, dtype=float).reshape(-1, 2)
    if context is None:
        return preds
    ctx = np.asarray(context, dtype=float).reshape(preds.shape[0], -1)
    return np.concatenate([ctx, preds], axis=1)


class CalibratedPosterior:
    """p(y=1|x) fitted on DEVELOPMENT data only: ridge-logistic, then Platt recalibration.

    Chronological split of the development data (first 60% fit, last 40% recalibrate), per the
    repository rule that preprocessing and fitting are train-only and ordered.  Features are the
    context (if any) and the two models' hard predictions.  Never pass locked-window or future
    labels here.
    """

    def __init__(self, scaler, clf, platt):
        self._mu, self._sd = scaler
        self._clf, self._platt = clf, platt

    @classmethod
    def fit(cls, dev_context, dev_preds, dev_labels, *, C: float = 1.0):
        from sklearn.linear_model import LogisticRegression

        X = _features(dev_context, dev_preds)
        y = np.asarray(dev_labels).astype(int)
        n = len(y)
        k = int(0.6 * n)
        if k < 5 or n - k < 5 or len(np.unique(y[:k])) < 2:
            raise ValueError("development data too small or single-class to fit a posterior")
        mu, sd = X[:k].mean(0), X[:k].std(0) + 1e-9
        clf = LogisticRegression(C=C, max_iter=1000).fit((X[:k] - mu) / sd, y[:k])
        platt = None
        z = clf.decision_function((X[k:] - mu) / sd)
        if len(np.unique(y[k:])) == 2:
            platt = LogisticRegression(C=1e6, max_iter=1000).fit(z[:, None], y[k:])
        return cls((mu, sd), clf, platt)

    def p1(self, context, preds) -> np.ndarray:
        X = _features(context, preds)
        z = self._clf.decision_function((X - self._mu) / self._sd)
        p = self._platt.predict_proba(z[:, None])[:, 1] if self._platt else 1 / (1 + np.exp(-z))
        return np.clip(p, 1e-3, 1 - 1e-3)


# --------------------------------------------------------------------------- policy
class _Sawade:
    """Fixed-budget Sawade sampler + our deployment rule. Subclasses supply ``_p1``."""

    name = "sawade"

    def __init__(
        self,
        horizon: int,
        budget: int,
        *,
        rng,
        delay: int,
        dev_preds,
        dev_context=None,
        window_frac: float = 0.5,
        p_floor: float = 0.02,
        name: str | None = None,
    ):
        if delay < 1:
            raise ValueError("delay must be >= 1")
        if not 0.0 < window_frac <= 1.0:
            raise ValueError("window_frac must lie in (0, 1]")
        if not 0.0 < p_floor <= 1.0:
            raise ValueError("p_floor must lie in (0, 1]")
        if name:
            self.name = name
        self.T, self.B, self.rng, self.delay = int(horizon), int(budget), rng, int(delay)
        self.window = max(1, round(window_frac * horizon))
        self.p_floor = float(p_floor)
        dev_preds = np.asarray(dev_preds)
        if dev_preds.ndim != 2 or dev_preds.shape[1] != 2:
            raise ValueError("Sawade compares exactly two models")
        step = max(1, len(dev_preds) // _MAX_POOL)  # deterministic thinning, order preserved
        self._pool_preds = dev_preds[::step]
        self._pool_ctx = None if dev_context is None else np.asarray(dev_context)[::step]
        p_pool = self._p1(self._pool_ctx, self._pool_preds)
        self.delta = introspective_delta(self._pool_preds[:, 0], self._pool_preds[:, 1], p_pool)
        self._q_pool = derivation4_weight(
            self._pool_preds[:, 0], self._pool_preds[:, 1], p_pool, self.delta
        )
        if not (self._q_pool > 0).any():
            raise ValueError("development pool has no sampleable instance (no disagreement)")
        # deployment state
        self.deployed = 0
        self.committed = False
        self.n_issued = self.n_observed = 0
        self.last_release = -1
        self.sampling_closed = False
        self.ht_diff = 0.0  # sum w (l0 - l1)
        self.w_sum = 0.0
        self.wl = np.zeros(2)  # sum w l_j
        self.truncated = 0  # events with q>0 where the hard cap, not the design, said no
        self.last_pi = 0.0

    # -- to be provided by variants
    def _p1(self, context, preds) -> np.ndarray:
        raise NotImplementedError

    # -- sampling
    def event_weight(self, event: Event) -> float:
        preds = np.asarray(event.model_predictions).reshape(1, 2)
        ctx = None if event.context is None else np.asarray(event.context).reshape(1, -1)
        p = self._p1(ctx, preds)
        return float(derivation4_weight(preds[:, 0], preds[:, 1], p, self.delta)[0])

    def event_propensity(self, event: Event, remaining: int) -> float:
        if event.t >= self.window or remaining <= 0:
            return 0.0
        q = self.event_weight(event)
        if q <= 0.0:
            return 0.0
        left = max(self.window - event.t, 1)
        c = solve_scale(self._q_pool, self.p_floor, min(remaining / left, 1.0))
        return float(propensity(np.array([q]), c, self.p_floor)[0])

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if event.t >= self.window or remaining_budget <= 0:
            self.sampling_closed = True
        pi = self.event_propensity(event, remaining_budget)
        self.last_pi = pi
        if pi <= 0.0:
            if remaining_budget <= 0 and self.event_weight(event) > 0 and event.t < self.window:
                self.truncated += 1
            return QueryRequest(requested=False)
        if self.rng.random() < pi:
            self.n_issued += 1
            self.last_release = max(self.last_release, event.t + self.delay)
            return QueryRequest(requested=True, probability=pi)
        return QueryRequest(requested=False)

    # -- evidence (Eq. 3)
    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            pi = float(fb.query_probability)  # frozen at issue time, never recomputed
            if not pi > 0.0:
                raise ValueError("released label with non-positive issue-time propensity")
            w = 1.0 / pi
            l = np.asarray(fb.model_losses, dtype=float)
            self.n_observed += 1
            self.w_sum += w
            self.wl += w * l
            self.ht_diff += w * (l[0] - l[1])

    def risk_estimates(self) -> np.ndarray:
        """Eq. 3 for both models: (1/W) sum w_i l_j(x_i, y_i)."""
        if self.w_sum <= 0:
            return np.full(2, np.nan)
        return self.wl / self.w_sum

    # -- deployment (ADAPTER: ours)
    def predict(self, event: Event) -> int:
        if not self.committed:
            window_over = event.t >= self.window or self.sampling_closed
            all_in = self.n_observed >= self.n_issued and event.t >= self.last_release
            if window_over and all_in:
                self.committed = True
                r = self.risk_estimates()
                if self.n_observed > 0 and r[1] < r[0]:
                    self.deployed = 1
        return self.deployed

    def decision_state(self) -> str:
        return f"dep={self.deployed};n={self.n_observed}/{self.n_issued};delta={self.delta:.3f}"

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "committed": self.committed,
            "n_issued": self.n_issued,
            "n_observed": self.n_observed,
            "last_release": self.last_release,
            "sampling_closed": self.sampling_closed,
            "ht_diff": self.ht_diff,
            "w_sum": self.w_sum,
            "wl": self.wl.tolist(),
            "truncated": self.truncated,
            "rng": self.rng.bit_generator.state,
        }

    def load_state_dict(self, s: dict) -> None:
        self.deployed, self.committed = int(s["deployed"]), bool(s["committed"])
        self.n_issued, self.n_observed = int(s["n_issued"]), int(s["n_observed"])
        self.last_release, self.sampling_closed = int(s["last_release"]), bool(s["sampling_closed"])
        self.ht_diff, self.w_sum = float(s["ht_diff"]), float(s["w_sum"])
        self.wl, self.truncated = np.asarray(s["wl"], dtype=float), int(s["truncated"])
        self.rng.bit_generator.state = s["rng"]


class SawadeActiveNeq(_Sawade):
    """``active!=``: p(y=1|x) ~ 0.5, so Delta_theta = 0 and q* is uniform on {f1(x) != f2(x)}."""

    name = "sawade_active_neq"

    def _p1(self, context, preds) -> np.ndarray:
        return np.full(np.asarray(preds).shape[0], 0.5)


class SawadeCalibrated(_Sawade):
    """Derivation 4 with a calibrated p(y=1|x) fitted on development data only."""

    name = "sawade_calibrated"

    def __init__(
        self,
        horizon,
        budget,
        *,
        rng,
        delay,
        dev_preds,
        posterior: CalibratedPosterior,
        dev_context=None,
        **kw,
    ):
        self.posterior = posterior  # must exist before the base class evaluates the dev pool
        super().__init__(
            horizon,
            budget,
            rng=rng,
            delay=delay,
            dev_preds=dev_preds,
            dev_context=dev_context,
            **kw,
        )

    def _p1(self, context, preds) -> np.ndarray:
        return self.posterior.p1(context, preds)
