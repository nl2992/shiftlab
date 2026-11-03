"""Variance-minimising active model selection (Hara et al., ACML 2024 / Mach. Learn. 2024),
ported from the authors' code.

Source: ``vendor_sota/variance_min/`` (gitignored, not committed), clone commit
``33f6fab5f50d470bc2957a3ed1c4e86d94d82f5d``. Line ranges ported:

* ``src/query.py`` lines 4-14 (``q_by_loss_diff_sub``) and 16-21 (``q_by_loss_diff``): the
  proposed query score, the sum over model pairs i<j and classes c of
  ``|loss[i,v,c] - loss[j,v,c]| * p_est[v,c]``, then ``+ eps`` (eps=1e-2) and optional
  normalisation. This is the paper's Equation 8; the *form* here is taken from the code.
* ``src/query.py`` lines 53-65 (``sample_from_p``): rejection sampler on the normalised pool
  distribution.
* ``src/estimator.py`` lines 4-11 (``LURE``): the unbiased estimator for sequential sampling
  without replacement from a pool.
* ``Sec5/config.py`` lines 13-17 (``'proposed': (q_by_loss_diff, LURE, False)``: no replacement)
  and ``Sec5/test.py`` lines 42-75 (``run_model_selection``): the whole-pool loop, in which
  ``q_full`` is computed once unnormalised (line 53), renormalised over the *remaining* pool at
  every step (lines 57-58), one point drawn (61-62), its normalised probability recorded (66) and
  LURE evaluated on all draws so far with N = pool size (69). ``Sec6/test.py`` is the same loop
  with an ``n_query`` cap.
* Loss tables: ``Sec5/test.py`` lines 17-27 and ``src/loss.py`` lines 6-7 (0/1 loss of every
  model under every hypothetical true class).

Three classes, deliberately not interchangeable:

* ``VarianceMinNative``: the published pool algorithm, whole pool visible, no delay.
* ``VarianceMinCausalAdapter``: our streaming task, LURE evaluated on the actual realised
  sampling probabilities. LURE is exact only for pool sampling; see the BLOCKED note below.
* ``VarianceMinStreamingIPW``: same sampler, estimator replaced by Horvitz-Thompson IPW. This is a
  DIFFERENT estimator from the published method and must not be reported under its name.

Degeneracy (derived and tested, see ``binary_zero_one_score_is_disagreement``): with hard
predictions, 0/1 loss and TWO classes, ``|l_1(c) - l_2(c)| = 1[pred_1 != pred_2]`` for every c, so
the score is ``1[disagree] * sum_c p_c = 1[disagree]`` whatever the surrogate says. The surrogate
drops out and the method is "sample proportionally to disagree + eps", i.e. disagreement-only
sampling with a 1% floor on agreeing points (Model Picker has a hard zero there). With C>2 classes
the score is ``p(pred_1) + p(pred_2)`` on disagreeing points, so the surrogate matters only then.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulator import Event, QueryRequest, ReleasedFeedback

EPS = 1e-2  # src/query.py line 16 default


# --------------------------------------------------------------------------------------------
# Shared published arithmetic
# --------------------------------------------------------------------------------------------
def zero_one_loss_table(predictions: np.ndarray, num_classes: int) -> np.ndarray:
    """(K, N, C) table, entry [i, v, c] = loss of model i on point v if the true class is c.

    Mirrors ``Sec5/test.py`` ``load_train`` (``Lte``) with ``src/loss.py`` ``zero_one_loss`` for
    one-hot (hard) predictions: 1 where the class is not the predicted one.
    """
    preds = np.asarray(predictions)  # (N, K)
    classes = np.arange(num_classes)
    return (preds.T[:, :, None] != classes[None, None, :]).astype(np.float64)


def pair_score(loss_clfs: np.ndarray, p_est: np.ndarray, idx: np.ndarray | None = None) -> np.ndarray:
    """``q_by_loss_diff_sub`` (query.py lines 4-14), vectorised: for each point in ``idx``,
    sum over pairs i<j and classes c of ``|loss[i,v,c]-loss[j,v,c]| * p_est[v,c]``."""
    K, N, _ = loss_clfs.shape
    if idx is None:
        idx = np.arange(N)
    out = np.zeros(len(idx))
    for i in range(K):
        for j in range(i + 1, K):
            out += np.sum(np.abs(loss_clfs[i, idx] - loss_clfs[j, idx]) * p_est[idx], axis=1)
    return out


def query_weights(
    loss_clfs: np.ndarray, p_est: np.ndarray, idx: np.ndarray | None = None, eps: float = EPS,
    normalize: bool = False,
) -> np.ndarray:
    """``q_by_loss_diff`` (query.py lines 16-21): score + eps, optionally normalised."""
    q = pair_score(loss_clfs, p_est, idx) + eps
    return q / np.sum(q) if normalize else q


def lure(loss: np.ndarray, q: np.ndarray, N: int) -> np.ndarray:
    """``LURE`` (estimator.py lines 4-11), vectorised, including its ``1e-8`` guard.

    ``loss`` is (M, K) losses of the M sampled points in draw order; ``q`` the (M,) probability with
    which each was drawn *from the then-remaining pool of N-m+1 points*."""
    M = len(q)
    m = np.arange(1, M + 1, dtype=np.float64)
    v = 1 + (1 / ((N - m + 1) * q) - 1) * (N - M) / (N - m + 1e-8)
    return (v[:, None] * loss).sum(axis=0) / M


def sample_from_p_numpy(p: np.ndarray, rng: np.random.Generator) -> int:
    """``sample_from_p`` (query.py lines 53-65): propose indices uniformly in blocks of 10000 and
    accept the first whose uniform draw is below ``p[j]``. Acceptance probability is proportional
    to p[j] under a uniform proposal, so the accepted index is distributed as ``p`` normalised.
    The author's version seeds numba's own generator; this one uses the supplied numpy Generator,
    so draws are NOT bit-identical (the test injects the author's sampler to compare the rest)."""
    while True:
        j = rng.integers(0, p.size, 10000)
        t = rng.random(j.size)
        k = np.flatnonzero(t < p[j])
        if k.size:
            return int(j[k[0]])


# --------------------------------------------------------------------------------------------
# Native, as published
# --------------------------------------------------------------------------------------------
class VarianceMinNative:
    """The published pool-based procedure (``Sec5/test.py`` ``run_model_selection``).

    The full pool of N points and their surrogate probabilities are visible up front and points
    are drawn without replacement with probability proportional to ``score + eps`` renormalised
    over the points still in the pool. Labels are available immediately. This is not a simulator
    ``Policy``."""

    name = "variance_min_native"

    def __init__(self, num_classes: int, eps: float = EPS):
        self.num_classes = int(num_classes)
        self.eps = float(eps)

    def run(
        self,
        predictions: np.ndarray,  # (N, K) hard predictions
        labels: np.ndarray,  # (N,) labels, read only for the points the procedure draws
        p_est: np.ndarray,  # (N, C) surrogate class probabilities (NOT from the locked window)
        n_steps: int | None = None,
        rng: np.random.Generator | None = None,
        sampler: Callable[[np.ndarray, int], int] | None = None,
    ) -> dict:
        """Mirror of ``run_model_selection`` lines 42-75. ``sampler(q_now, step)`` returns the
        position in the remaining pool; it defaults to the numpy rejection sampler."""
        N, _K = predictions.shape
        n_steps = N if n_steps is None else int(n_steps)
        loss_clfs = zero_one_loss_table(predictions, self.num_classes)
        l_true = (predictions != labels[:, None]).astype(np.float64)  # (N, K), line 26 analogue
        q_full = query_weights(loss_clfs, p_est, None, self.eps, normalize=False)  # line 53
        idx_u = list(range(N))
        L: list[np.ndarray] = []
        q: list[float] = []
        hat = []
        order = []
        for i in range(n_steps):
            q_now = q_full[idx_u]
            q_now = q_now / np.sum(q_now)  # lines 57-58
            if sampler is not None:
                k = sampler(q_now, i)
            else:
                k = sample_from_p_numpy(q_now, rng)  # type: ignore[arg-type]
            j = idx_u[k]
            L.append(l_true[j])
            q.append(float(q_now[k]))
            hat.append(lure(np.array(L), np.array(q), N))  # line 69
            idx_u.pop(k)  # replace=False for 'proposed' (Sec5/config.py line 16)
            order.append(j)
        return {"hat": np.array(hat), "queried": np.array(order), "q": np.array(q)}

    @staticmethod
    def recommendation(hat: np.ndarray) -> int:
        """argmin of the final estimated loss row (the quantity ``Sec5/test.py`` lines 102-105
        scores for success). Lowest index on ties."""
        return int(np.argmin(hat[-1]))


# --------------------------------------------------------------------------------------------
# Streaming adapters
# --------------------------------------------------------------------------------------------
def fit_class_prior(dev_labels: np.ndarray, num_classes: int) -> np.ndarray:
    """Surrogate from development data ONLY (Laplace-smoothed class frequencies). The locked
    window must never be passed here."""
    counts = np.bincount(np.asarray(dev_labels, dtype=int), minlength=num_classes) + 1.0
    return counts / counts.sum()


class VarianceMinCausalAdapter:
    """Variance-minimising score on a stream, with LURE on the realised probabilities.

    ADAPTER summary: the published method draws from a pool that includes future points; here only
    the event that has just arrived can be queried (the simulator's request is for the current
    event), so the draw is a per-arrival Bernoulli. See the per-line markers.
    """

    name = "variance_min_adapter"

    def __init__(
        self,
        num_models: int,
        num_classes: int,
        rng: np.random.Generator,
        rate: float,
        class_prior: np.ndarray | None = None,
        surrogate: Callable[[Event], np.ndarray] | None = None,
        eps: float = EPS,
        initial_model: int = 0,
    ):
        if class_prior is None and surrogate is None:
            raise ValueError("a surrogate from development data is required")
        self.num_models = int(num_models)
        self.num_classes = int(num_classes)
        self.rng = rng
        self.rate = float(rate)  # target labels per arrival, e.g. budget / horizon
        self.class_prior = None if class_prior is None else np.asarray(class_prior, float)
        self.surrogate = surrogate
        self.eps = float(eps)
        self.deployed = int(initial_model)
        self.n_arrived = 0
        self.sum_weights = 0.0
        self.horizon = 0
        self.losses: list[np.ndarray] = []
        self.props: list[float] = []

    # -- scoring (published) ------------------------------------------------------------------
    def score(self, event: Event) -> float:
        p = self.surrogate(event) if self.surrogate is not None else self.class_prior
        table = zero_one_loss_table(np.asarray(event.model_predictions)[None, :], self.num_classes)
        return float(pair_score(table, np.asarray(p, float)[None, :])[0])

    # -- estimator ----------------------------------------------------------------------------
    def estimate(self) -> np.ndarray:
        if not self.losses:
            return np.zeros(self.num_models)
        N = self.horizon
        m = np.arange(1, len(self.props) + 1)
        # ADAPTER / BLOCKED: LURE needs q_m = probability of drawing the m-th point from the
        # remaining pool of N-m+1; a uniform draw gives q_m = 1/(N-m+1) and weight v = 1. A stream
        # has no such pool. We read the realised per-arrival propensity RELATIVE to the target
        # rate as the pool draw probability times the remaining pool size, q_m = (p_t/rate) /
        # (N-m+1), so that uniform sampling at the target rate recovers v = 1. (Using q_m =
        # p_t/(N-m+1) was tried first and is biased by about 1/rate; see the test.) LURE's
        # unbiasedness proof does NOT cover this sampler; the Monte Carlo bias check in the test
        # file measures the residual bias.
        q = np.array(self.props) / (self.rate * (N - m + 1))
        return lure(np.array(self.losses), q, N)

    # -- Policy -------------------------------------------------------------------------------
    def predict(self, event: Event) -> int:
        h = self.estimate()
        best = np.flatnonzero(h == np.min(h))
        if self.deployed not in best:  # ties keep the incumbent: no charged switch
            self.deployed = int(best[0])
        return self.deployed

    def propensity(self, event: Event) -> float:
        s = self.score(event) + self.eps
        # ADAPTER: published q is normalised over a known pool. Here the normaliser is the running
        # mean of (score + eps) over events that have ARRIVED (including this one); no future
        # events. p_t = rate * (s / mean) is capped at 1.
        self.n_arrived += 1
        self.sum_weights += s
        return float(min(1.0, self.rate * s / (self.sum_weights / self.n_arrived)))

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        self.horizon = int(event.horizon)
        p = self.propensity(event)  # arrival statistics are updated even with no budget
        # ADAPTER: hard cap enforced here as well as by the simulator; nothing is drawn at 0.
        if remaining_budget <= 0:
            return QueryRequest(requested=False, probability=0.0)
        z = bool(self.rng.random() < p)
        return QueryRequest(requested=z, probability=p)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            # ADAPTER: delayed arrival; the weight uses the frozen issue-time propensity.
            if fb.query_probability <= 0:
                raise ValueError("feedback with non-positive issue-time propensity")
            self.losses.append(np.asarray(fb.model_losses, dtype=float))
            self.props.append(float(fb.query_probability))

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "n_arrived": self.n_arrived,
            "sum_weights": self.sum_weights,
            "horizon": self.horizon,
            "losses": [x.tolist() for x in self.losses],
            "props": list(self.props),
        }

    def load_state_dict(self, state: dict) -> None:
        self.deployed = int(state["deployed"])
        self.n_arrived = int(state["n_arrived"])
        self.sum_weights = float(state["sum_weights"])
        self.horizon = int(state["horizon"])
        self.losses = [np.asarray(x, float) for x in state["losses"]]
        self.props = [float(x) for x in state["props"]]


class VarianceMinStreamingIPW(VarianceMinCausalAdapter):
    """NOT the published method. Same score and sampler as the adapter, but LURE is replaced by
    the Horvitz-Thompson estimator ``(1/N) sum_m l_m / p_m``, which is unbiased for the stream's
    mean loss under independent per-arrival Bernoulli sampling when the cap never binds. Report
    it under this name only."""

    name = "variance_min_streaming_ipw"

    def estimate(self) -> np.ndarray:
        if not self.losses:
            return np.zeros(self.num_models)
        loss = np.array(self.losses)
        return (loss / np.array(self.props)[:, None]).sum(axis=0) / self.horizon


def binary_zero_one_score_is_disagreement(preds: np.ndarray, p_est: np.ndarray) -> bool:
    """True if, for these (N, 2) predictions over 2 classes, the published score equals the
    disagreement indicator for every point (it does for any ``p_est`` summing to 1)."""
    table = zero_one_loss_table(preds, 2)
    score = pair_score(table, p_est)
    return bool(np.allclose(score, (preds[:, 0] != preds[:, 1]).astype(float)))
