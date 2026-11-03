"""Acquisition component of Xu, Karampatziakis and Mineiro (NeurIPS 2024), as a COMPONENT ADAPTER.

Paper: "Active, anytime-valid risk controlling prediction sets", arXiv:2406.10490.
Author code: ``vendor_sota/xu_rcps/`` (gitignored), clone commit
``a67f85d603df2bb3e32ef007f445191923ebd990`` (``neilzxu/active-rcps``).

WHAT THIS IS.  We take their label-acquisition rule and run it inside OUR certification machinery
(a paired, delayed, frozen-bet e-process that promotes the challenger).  This is NOT a
reproduction of their risk-controlling prediction sets; no conformal set, no beta grid, no
theorem of theirs is inherited.  Whatever validity the evidence side has is ours and is stated
in ``docs/promising_directions/B3_PLUS_METHOD.md`` / ``b3_plus_policy.py``, not theirs.

Source ranges (author code)
---------------------------
* ``Player.py`` 168-188 (``RiskPredictorPolicyPrimalPlayer.predict``): the acquisition rule
  ``Q = clip(sqrt(var_predictor) / exp(norm_const), q_min, 1)`` is line 177; ``L = bernoulli(Q)``
  is line 187; ``cons = target_rate - mean(Q)`` is line 186.
* ``Player.py`` 190-216 (``update``): the normaliser loss ``1/c - dual*(target_rate - mean(Q))``
  is lines 196-197; the new propensity floor passed to the martingale is lines 211-216.
* ``OnlineMinimax.py`` 14-27 (``WindowedBeTheLeader``) and 52-58 (``addobs``): the dual variable.
* ``IwUpperMartingale.py`` 161-184 (``PartialIwUpperMartingale.xi``): the control-variate
  estimator ``xi = theta + (l/q)(cv - rho) - cv`` is line 172; 152-159 (``ximin``) and 107-112
  (bet clip ``1/(2|ximin|)``): why wealth stays positive given a propensity floor.
* ``simulation.py`` 124-148: the configurations they compare ("cv only", "optimal" = variance
  predictor + control variate, "oblivious" = constant rate ``target_rate``, Player.py line 76).
* ``simulation.py`` 36-70, 86-96 and ``Predictor.py`` 97-125 (``FalsePositivePredictor``): their
  predictors in the simulation are ORACLE (they know ``P(y=1|x)``); only the "learned"
  configurations fit anything, with ``LinearRiskPredictor`` + COCOB.

The two variants (named separately; the brief requires both be reported separately)
-----------------------------------------------------------------------------------
``acquisition_only``    plain inverse-propensity evidence, no predictor.  For a paired 0/1 loss on
    the disagreement region ``|D| = 1`` so the conditional second moment of the IPW'd quantity is
    constant and their rule reduces to *disagreement-gated uniform sampling at the target rate*,
    i.e. exactly their "oblivious" arm (``Player.py`` line 76).  This is a finding, not a bug in
    the port: with two models and 0/1 loss there is nothing for a predictor-free score to vary
    on.  What still differs from our pacer is the normaliser/floor logic.
``prediction_assisted`` fitted nuisance ``mu_hat(x) ~ E[D|x]``; the evidence uses the control-
    variate (AIPW) increment and the acquisition score is the residual standard deviation
    ``sqrt(1 - mu_hat^2)`` (their "optimal"/"learned" arms).  NOTE this changes the evidence
    statistic as well as the acquisition: in their method the control variate is part of the
    estimator the acquisition is optimised for.  ``control_variate=False`` isolates the
    acquisition (score from the predictor, plain IPW evidence); that ablation is expected to be
    no better than uniform because for plain IPW the optimal score is ``sqrt(E[D^2|x]) = 1``.

Paired-loss mapping
-------------------
Theirs: a risk ``rho(x, beta) in [0, 1]`` tested against a level ``theta`` (null ``E rho >= theta``,
evidence ``xi = theta - rho_hat``).  Ours: ``D = l0 - l1 in [-1, 1]`` (incumbent minus challenger),
null ``E[D] <= m`` (m = 0 here: single-margin null, not b1's margin grid).  Map
``rho = (1 - D)/2`` and ``theta = (1 - m)/2``; then ``xi = (D - m)/2`` and ``E rho >= theta  <=>
E D <= m``.  Their bet is therefore twice ours (``lambda_xu = 2 lambda_ours``); we work in D units
throughout and use OUR bet (``b1.bet_from_stats``, imported through ``b3_plus_policy.b1``), not
their FTL bet.  Assumptions: (1) 0/1 losses so ``D in {-1,0,1}`` and ``D = 0`` whenever the two
models agree; (2) both losses are identifiable from one label (true here: one label reveals every
frozen model's loss); (3) propensities are bounded below by ``q_min`` (their ``q_min``).

Acquisition derivation (reconstructed, NOT checked against the paper text; ``Player.py:177`` is
the authority).  With IPW increments ``xi`` and a bet ``lambda``, a lower bound on
``E log(1 + lambda xi)`` is ``lambda E xi - c lambda^2 E xi^2``; ``E xi^2`` scales as
``E[s(x)^2 / q(x)]`` with ``s^2 = E[(D - cv)^2 | x]``.  Minimising that subject to
``E q = target_rate`` and ``q >= q_min`` gives ``q = clip(s / c, q_min, 1)``, ``c`` the
normaliser.  The score is ``s(x) = sqrt(1 - mu_hat(x)^2)`` (the residual variance of a +-1
variable with mean ``mu_hat``).

Evidence side: re-expressed, not imported.  We import ``b1.bet_from_stats`` and ``b1.Params``
(through ``b3_plus_policy``, which pins b1 to commit 041bc26) and re-express the single-null
wealth update ``log(1 + lam * y)`` with ``lam`` frozen at issue and clipped to ``[0, cap]``,
cap ``= 1/(2 |y_min|)`` (for the plain case this is ``q/2``, identical to ``b3_plus_policy``).
``CertPlus`` itself is vectorised over seeds with a margin grid and cannot be driven one event at a
time through the simulator, so it is mirrored rather than called.

Budget: THEIRS is an expected-proportion constraint ``E[mean Q] = target_rate`` that holds on
average over the stream with no pathwise guarantee.  OURS is a hard per-episode cap enforced by the
simulator.  Imposing the cap on their rule is an adapter, not an inherited theorem.  We set
``target_rate = budget / horizon`` and count how often the cap suppresses a query the rule wanted
(``cap_suppressed``) and the unconstrained expected demand (``expected_demand``), so whether the
cap binds is measured rather than asserted.
"""

from __future__ import annotations

import math
import sys
from collections import deque
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from b3_plus_policy import b1
from simulator import Event, QueryRequest, ReleasedFeedback

VARIANTS = ("acquisition_only", "prediction_assisted")


# --------------------------------------------------------------------------------------------
# Published acquisition arithmetic
# --------------------------------------------------------------------------------------------
def residual_score(mu_hat: float) -> float:
    """Residual standard deviation of a +-1 variable with mean ``mu_hat``: sqrt(1 - mu^2).

    Stands in for ``sqrt(var_predictor)`` of ``Player.py`` line 177 on the disagreement region,
    where ``D = +-1``.  Their oracle analogue is ``FalsePositivePredictor(mode='var')``
    (``Predictor.py`` 108-110): ``P(1-P)``.
    """
    return float(math.sqrt(max(0.0, 1.0 - float(mu_hat) ** 2)))


def rate_from_score(score: float, c: float, q_min: float) -> float:
    """``Player.py`` line 177: ``Q = clip(sqrt(var) / c, q_min, 1)`` (score already a std dev)."""
    return float(np.clip(score / c, q_min, 1.0))


def solve_normaliser(scores: np.ndarray, target_rate: float, q_min: float) -> float:
    """Normaliser ``c`` such that ``mean over the window of Q * 1[score > 0] = target_rate``.

    ADAPTER: the author code finds ``c = exp(z)`` online with COCOB on the Lagrangian
    ``1/c - dual*(target_rate - mean Q)`` (Player.py 196-197).  Reading that loss, its gradient in
    ``z`` is ``-(1/c + dual*Q) < 0`` on the unclipped region, so descent only ever raises ``c``
    and nothing pushes it back down when the rate falls below target.  It could not be run
    (see ``# BLOCKED`` below) so that reading is unverified; rather than port a normaliser we
    cannot test, ``c`` is set to the value that meets the constraint on the recent scores, which
    is the point the Lagrangian is meant to reach.  Eligible = ``score > 0`` (the disagreement
    gate); ineligible events contribute rate 0.  If ``q_min`` alone already exceeds the target the
    floor is infeasible and ``c = inf`` (everything at ``q_min``): the floor, not the budget,
    then sets the rate.  If the target exceeds the eligible fraction, ``c`` is tiny (all ones).
    """
    s = np.asarray(scores, dtype=float)
    elig = s > 0
    n = s.size
    if n == 0 or not elig.any():
        return 1.0
    se = s[elig]

    def mean_rate(c: float) -> float:
        return float(np.clip(se / c, q_min, 1.0).sum() / n)

    lo, hi = 1e-9, 1e9
    if mean_rate(hi) >= target_rate:  # even all-at-floor meets/exceeds target: floor binds
        return float("inf")
    if mean_rate(lo) <= target_rate:  # even all-ones is below target
        return lo
    for _ in range(100):  # mean_rate is non-increasing in c: bisect on log c
        mid = math.sqrt(lo * hi)
        if mean_rate(mid) > target_rate:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def bet_cap(q: float, mu_hat: float, sgn: float, control_variate: bool) -> float:
    """``1/(2 |y_min|)`` over the support of the increment ``y = sgn * x``.

    Their analogue is the clip ``1/(2|ximin|)`` (IwUpperMartingale.py 50-53, 152-159), which keeps
    every factor ``1 + lam*xi >= 1/2``.  Plain IPW: ``x in {0, D/q}`` so ``|y_min| = 1/q`` and the
    cap is ``q/2``, as in ``b3_plus_policy``.  Control variate: ``x = mu + l (D - mu)/q``.
    """
    if not control_variate:
        return q / 2.0
    lo = mu_hat - (1.0 + mu_hat) / q  # l = 1, D = -1
    hi = mu_hat + (1.0 - mu_hat) / q  # l = 1, D = +1
    ymin = min(sgn * lo, sgn * hi, sgn * mu_hat)  # sgn * mu_hat is the l = 0 value
    return 1.0 / (2.0 * max(-ymin, 1e-12))


# --------------------------------------------------------------------------------------------
# Nuisance predictor (prediction_assisted only): fit on PERMITTED data only
# --------------------------------------------------------------------------------------------
class PairedDiffPredictor:
    """``mu_hat(x) ~ E[D | x]`` from a logistic fit of ``1[D = +1]`` on rows with ``D != 0``.

    ADAPTER / BLOCKED: their learned predictor is ``LinearRiskPredictor`` trained online with
    COCOB on labelled events (Predictor.py 128-232).  That file does not parse
    (line 230, ``self._beta_knots. if``) and torch is not installed, so it could not be run.
    This is a frozen, offline-fit stand-in; it is NOT their predictor.

    Permitted data: only a development window that ends no later than the start of the window
    the policy will be scored on.  ``fit`` takes both ends and refuses otherwise; the policy never
    refits, so no episode data, locked or future, ever reaches it.
    """

    def __init__(self, clip: float = 0.95):
        self.clip = float(clip)
        self.model = None
        self.const = 0.0
        self.fit_end: int | None = None

    def fit(self, contexts, d, *, data_end: int, locked_start: int) -> PairedDiffPredictor:
        if data_end > locked_start:
            raise ValueError(
                f"nuisance data ends at {data_end} > locked window start {locked_start}: "
                "fitting on the locked window or the future is not permitted"
            )
        from sklearn.linear_model import LogisticRegression

        x = np.asarray(contexts, dtype=float)
        d = np.asarray(d)
        keep = d != 0
        self.fit_end = int(data_end)
        if keep.sum() == 0 or len(np.unique(d[keep])) < 2:
            self.const = float(np.sign(d[keep].mean())) * self.clip if keep.any() else 0.0
            self.model = None
            return self
        self.model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=200).fit(
            x[keep], (d[keep] > 0).astype(int)
        )
        return self

    def mu_hat(self, context) -> float:
        if self.model is None:
            return float(self.const)
        p = float(self.model.predict_proba(np.asarray(context, dtype=float).reshape(1, -1))[0, 1])
        return float(np.clip(2.0 * p - 1.0, -self.clip, self.clip))


# --------------------------------------------------------------------------------------------
# Deployment adapter
# --------------------------------------------------------------------------------------------
class XuAcquisitionPolicy:
    """Xu et al. acquisition + our single-null paired e-process, as a simulator ``Policy``.

    Model 0 is the incumbent, model 1 the challenger (``ReleasedFeedback.model_losses`` is read at
    those two indices).  Deploys 0 until the challenger's wealth crosses ``log(1/alpha)``, then 1;
    a symmetric crossing on the sign-flipped process rolls back.  Labels bought before a switch
    are discarded (as in ``CertPlus``: ``live = s >= seg``).
    """

    def __init__(
        self,
        variant: str,
        rng: np.random.Generator,
        *,
        delay: int,
        nuisance: PairedDiffPredictor | None = None,
        q_min: float = 0.05,
        target_rate: float | None = None,
        alpha: float = 0.05,
        window: int = 256,
        control_variate: bool | None = None,
    ):
        if variant not in VARIANTS:
            raise ValueError(variant)
        if delay < 1:
            raise ValueError("delay must be >= 1")
        self.variant = variant
        self.name = f"xu_{variant}" + (
            "_nocv" if variant == "prediction_assisted" and control_variate is False else ""
        )
        self.pa = variant == "prediction_assisted"
        if self.pa and nuisance is None:
            raise ValueError("prediction_assisted needs a nuisance predictor fit on dev data")
        if not self.pa and nuisance is not None:
            raise ValueError("acquisition_only uses no predictor")
        self.cv = self.pa if control_variate is None else bool(control_variate)
        if self.cv and not self.pa:
            raise ValueError("control variate needs the nuisance predictor")
        self.nuisance = nuisance
        self.rng = rng
        self.delay = int(delay)
        self.q_min = float(q_min)
        self.target_rate = target_rate
        self.params = b1.Params(delay=self.delay, alpha=alpha)
        self.thr = math.log(1.0 / alpha)
        self.scores: deque[float] = deque(maxlen=int(window))
        # evidence state
        self.dep = 0
        self.seg = 0
        self.logw = 0.0
        self.s1 = self.s2 = self.cnt = 0.0
        self.unasked: list[dict] = []  # disagreement events not queried; their increment is mu_hat
        # diagnostics
        self.min_factor = math.inf
        self.min_q = math.inf
        self.max_q = 0.0
        self.expected_demand = 0.0  # sum of issued q over disagreement events (cap ignored)
        self.cap_suppressed = 0
        self.n_asked = 0
        self.n_discarded = 0
        self.n_switches = 0
        self.floor_infeasible_events = 0

    # ------------------------------------------------------------------ Policy protocol
    def predict(self, event: Event) -> int:
        self._drain_unasked(event.t)
        return self.dep

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        preds = np.asarray(event.model_predictions)
        dis = bool(preds[0] != preds[1])
        if self.target_rate is None:
            # ADAPTER: their constraint is an expected proportion; the hard cap B over horizon T
            # is mapped to target_rate = B/T.
            self.target_rate = float(remaining_budget) / float(event.horizon)
        mu = self.nuisance.mu_hat(event.context) if self.pa else 0.0
        score = (residual_score(mu) if self.pa else 1.0) if dis else 0.0
        self.scores.append(score)
        if not dis:
            return QueryRequest(requested=False, probability=0.0)
        c = solve_normaliser(np.fromiter(self.scores, float), self.target_rate, self.q_min)
        if math.isinf(c):
            self.floor_infeasible_events += 1
            q = self.q_min
        else:
            q = rate_from_score(score, c, self.q_min)
        q = float(min(1.0, max(self.q_min, q)))
        self.min_q, self.max_q = min(self.min_q, q), max(self.max_q, q)
        self.expected_demand += q
        want = bool(self.rng.random() < q)  # drawn before the cap so the stream is cap-invariant
        if remaining_budget <= 0:
            # ADAPTER: hard cap.  Their constraint is in expectation only.
            self.cap_suppressed += int(want)
            return QueryRequest(requested=False, probability=0.0)
        sgn = 1.0 if self.dep == 0 else -1.0
        cap = bet_cap(q, mu, sgn, self.cv)
        lam = float(
            np.clip(b1.bet_from_stats(self.s1, self.s2, self.cnt, self.params, kelly=False), 0, cap)
        )
        extra = {"lam": lam, "mu_hat": mu, "dep": self.dep}
        if want:
            self.n_asked += 1
        elif self.cv:  # a non-queried event still carries the increment mu_hat (l = 0)
            self.unasked.append(
                {"t": event.t, "q": q, "lam": lam, "mu": mu, "due": event.t + self.delay}
            )
        return QueryRequest(requested=want, probability=q, extra=extra)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            q = float(fb.query_probability)  # issue-time propensity; never recomputed
            if not q > 0:
                raise ValueError("feedback with non-positive issue-time propensity")
            d = float(fb.model_losses[0]) - float(fb.model_losses[1])
            self._apply(fb.t_requested, fb.t_released, q, fb.extra["lam"], fb.extra["mu_hat"], d, 1)

    # ------------------------------------------------------------------ evidence
    def evidence_increment(self, q: float, mu: float, d: float, asked: int) -> float:
        """``x = mu + l (d - mu)/q`` with the control variate, else ``l d / q``."""
        if self.cv:
            return mu + asked * (d - mu) / q
        return asked * d / q

    def _drain_unasked(self, t: int) -> None:
        due = [u for u in self.unasked if u["due"] <= t]
        if not due:
            return
        self.unasked = [u for u in self.unasked if u["due"] > t]
        for u in due:
            self._apply(u["t"], t, u["q"], u["lam"], u["mu"], 0.0, 0)

    def _apply(self, t_issue, t_now, q, lam, mu, d, asked) -> None:
        if t_issue < self.seg:  # issued under the previous deployment: discarded
            self.n_discarded += 1
            return
        sgn = 1.0 if self.dep == 0 else -1.0
        y = sgn * self.evidence_increment(q, mu, d, asked)
        factor = 1.0 + lam * y
        self.min_factor = min(self.min_factor, factor)
        if not factor > 0:
            raise AssertionError(f"non-positive wealth factor {factor}")
        self.logw += math.log(factor)
        g = self.params.gamma
        self.s1, self.s2, self.cnt = g * self.s1 + y, g * self.s2 + y * y, g * self.cnt + 1.0
        if self.logw >= self.thr:
            self.dep = 1 - self.dep
            self.seg = int(t_now)
            self.logw = 0.0
            self.s1 = self.s2 = self.cnt = 0.0
            self.n_switches += 1

    # ------------------------------------------------------------------ misc
    def decision_state(self) -> str:
        return f"dep={self.dep} logw={self.logw:.3f}"

    def state_dict(self) -> dict:
        return {
            "dep": self.dep, "seg": self.seg, "logw": self.logw,
            "s1": self.s1, "s2": self.s2, "cnt": self.cnt,
            "scores": list(self.scores), "unasked": [dict(u) for u in self.unasked],
            "target_rate": self.target_rate, "min_factor": self.min_factor,
            "expected_demand": self.expected_demand, "cap_suppressed": self.cap_suppressed,
            "n_asked": self.n_asked, "n_discarded": self.n_discarded,
            "n_switches": self.n_switches, "min_q": self.min_q, "max_q": self.max_q,
            "floor_infeasible_events": self.floor_infeasible_events,
        }  # fmt: skip

    def load_state_dict(self, state: dict) -> None:
        for k, v in state.items():
            if k == "scores":
                self.scores = deque(v, maxlen=self.scores.maxlen)
            elif k == "unasked":
                self.unasked = [dict(u) for u in v]
            else:
                setattr(self, k, v)


# BLOCKED: the author code could not be executed, so no numerical comparison against it exists.
#   (1) ``Predictor.py`` line 230 is a SyntaxError (``self._beta_knots. if self._add_pretrain``),
#       and ``simulation.py`` imports ``Predictor`` at module load, so no entry point in the
#       repository imports as shipped.
#   (2) ``torch`` is not installed in this environment (every author module imports it at top
#       level) and installing it was out of scope for a CPU-sized port.
#   Nothing here substitutes for those runs; the tests check the ported arithmetic against hand
#   computation, not against the author's output.
