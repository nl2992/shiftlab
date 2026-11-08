# Ported verbatim from origin/claude/shiftlab-methods-strategy-dba13e@9493a6cd:scripts/promising_directions/sota/competitors/upf_style_switch_timing.py
# (only this comment added; see that branch for spec/check docs).
"""UPF-style cost-aware switch timing on the ShiftLab common contract (tier T3).

T3 common-contract adaptation; not UPF / not Regol et al.'s algorithm; no harm guarantee.

Source idea: Regol, Schwinn, Sprague, Coates & Markovich, "When to retrain a machine learning
model", ICML 2025 (PMLR 267:51369-51404; arXiv:2505.14903). No official code was found, so no T1
claim is possible. The native, fully-labelled, retraining-creates-a-new-model algorithm is ported
at tier T2 in ``src/shiftlab/dive/upf_retraining.py``; this file does NOT call it, because its
recursion is over (model-index, time) states for non-reversible retraining. Spec and independent
check: ``docs/sota_fidelity/specs|checks/regol_when_to_retrain.md`` (section 6 is the mapping
implemented here; the check's corrections apply). Reused from the T2 port: the Beta moment
conversion and clipping rules (re-stated in ``beta_parameters`` and cross-checked against
``BetaPerformanceForecaster.predict_beta_parameters`` in the tests), the strict ``<``
delta-quantile comparison, the shared-draws Monte Carlo backward recursion, ElasticNetCV.

What the rule is (spec section 6 steps 1-5)
-------------------------------------------
1. The stream is cut into periods of ``m`` rounds. ``m`` is a free parameter of the adaptation
   (the native method has dataset-sized periods) and MUST be locked before any evaluation run;
   the default ``m=100`` (20 periods for T=2000) is the pre-run value, not tuned.
2. Two arms (0 incumbent, 1 challenger). A cell ``A[k, j]`` is the period-j mean over rounds of
   ``1[models disagree] * loss_k``. It is estimated by Horvitz-Thompson inverse-propensity
   weighting from labels *released* by the decision round, using the issue-time propensities
   carried by ``ReleasedFeedback``. The common loss on agreement rounds is identical for both
   arms, never labelled by the shared pacer, and cancels in every keep-vs-switch comparison, so
   it is dropped (deviation; it also keeps cells in [0, 1] and IPW-identifiable).
3. Forecaster: ElasticNetCV on ``[k, j, z_shift]`` fitted on the cells that are *complete and
   released* (period ended, all its labels released, and no disagreement round had zero
   propensity). The native ``i`` and ``j-i`` collapse to arm and time (models are frozen), so
   this is a time-trend-plus-arm regressor and weaker than native UPF. ``z_shift`` is the L1
   change in the mean context vector between consecutive periods when contexts exist, else the
   absolute change in the (public, label-free) disagreement rate. Future periods use the latest
   observed z (the paper's "latest available" convention, A.7).
   Gaussian variance: ``sigma^2 = in-sample residual MSE + mean over training cells and arms of
   the Horvitz-Thompson variance estimator sum y^2 (1-q)/q^2 / m^2``. The IPW term is an added,
   declared deviation (check, fairness concern (a)); because the residual already contains some
   of that noise the sum is conservative (double counts), which widens the Beta spread.
   Beta parameters by Eq. 51-52 with the T2 port's clipping (mean clipped to [eps, 1-eps],
   variance capped at 0.99 mu(1-mu), alpha, beta floored at eps=1e-5). The paper only says
   "appropriate clipping", so this is a named choice. IPW cell estimates are clipped to [0, 1]
   before fitting (Beta support).
4. Cost-to-go (Eq. 17-20) in per-round-mean units. State (arm a, period j). "Keep" costs
   ``A[a, j]`` plus the value of (a, j+1); "switch" costs ``c_s/m + A[1-a, j]`` plus the value of
   (1-a, j+1), because switching is reversible and the other arm's cell replaces the native
   ``A[t, t]``. Cells are sampled independently from their Betas with ``draws`` Monte Carlo
   draws shared across states (as in the T2 port); the recursion stores, per state, the draw
   vector of the chosen branch. Switch iff the delta-quantile (default 0.95, Eq. 16) of the
   switch branch is strictly below that of the keep branch. Label price is ignored: the shared
   pacer spends the budget identically under every decision.
5. Only the first action is applied, at a period boundary. The forecaster is refitted and the plan
   recomputed at every boundary from whatever cells have matured (delayed labels mean the most
   recent ``ceil(delay/m)`` or so periods are not yet usable).

Warm-up: until ``min_periods`` (default 3) usable periods exist the policy stays with the
incumbent. With delay 100 and m=100 the first possible switch is therefore at round 400 (period 2 is complete at round 399).

Every deviation from the native method: reversible switching over two frozen models; periodization
with a free ``m``; sparse, delayed IPW cell estimates with no offline w=7 table; cells restricted
to disagreement rounds; exogenous shared labelling (``PacedDisagreementAcquisition``, same
rule as ``EconomicReplacement``); label price and switch cost mapped to ``c_s/m``; feature set
[k, j, z]; sigma with an IPW term; numpy instead of torch sampling; decisions only at period
boundaries; ``T`` must be a multiple of ``m``. Known limitation: once the budget is exhausted the
pacer gives disagreement rounds propensity 0, those periods violate IPW positivity and are
excluded, so the forecaster stops learning (it keeps extrapolating from earlier cells).
No type-I or harm control; nested delta-quantiles are not a coherent risk measure (spec sec. 3).
It belongs in the uncertified class and must not be labelled "UPF" or "Regol et al." in tables.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.linear_model import ElasticNetCV

for _p in (Path(__file__).resolve().parents[1], Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback

EPS = 1e-5  # same clipping constant as upf_retraining.BetaPerformanceForecaster


def beta_parameters(mean, sigma2: float, eps: float = EPS):
    """Eq. 51-52 with the T2 port's clipping (see module docstring)."""
    mu = np.clip(np.asarray(mean, dtype=np.float64), eps, 1 - eps)
    var = np.minimum(max(float(sigma2), eps**2), mu * (1 - mu) * 0.99)
    conc = np.maximum(mu * (1 - mu) / var - 1, eps)
    return np.maximum(mu * conc, eps), np.maximum((1 - mu) * conc, eps)


def plan_switch(
    alpha: np.ndarray,
    beta: np.ndarray,
    current_arm: int,
    switch_cost_per_round: float,
    *,
    delta: float = 0.95,
    draws: int = 2000,
    rng: np.random.Generator,
) -> tuple[bool, float]:
    """Backward recursion (Eq. 17-20, reversible) over Beta cells of shape (2, P).

    Column 0 is the period being decided; P is the number of periods left. Returns
    ``(switch_now, margin)`` with ``margin = q_delta(keep) - q_delta(switch)`` for the first
    period (switch iff margin > 0, i.e. strict ``<`` on quantiles as in Eq. 16).
    """
    if alpha.shape != beta.shape or alpha.ndim != 2 or alpha.shape[0] != 2:
        raise ValueError("alpha and beta must have shape (2, P)")
    if not 0 < delta < 1:
        raise ValueError("delta must lie in (0, 1)")
    P = alpha.shape[1]
    cells = rng.beta(alpha[:, :, None], beta[:, :, None], size=(2, P, draws))
    value = np.zeros((2, draws))  # V[a] for period j+1; V at P is zero
    margin = 0.0
    for j in range(P - 1, -1, -1):
        new_value = np.empty_like(value)
        for a in (0, 1):
            keep = cells[a, j] + value[a]
            switch = switch_cost_per_round + cells[1 - a, j] + value[1 - a]
            qk, qs = np.quantile(keep, delta), np.quantile(switch, delta)
            go = qs < qk
            new_value[a] = switch if go else keep
            if j == 0 and a == current_arm:
                margin = float(qk - qs)
        value = new_value
    return bool(margin > 0.0), margin


class UPFStyleSwitchTimingT3:
    """Simulator ``Policy``; see the module docstring for the full contract and deviations."""

    def __init__(
        self,
        horizon: int,
        budget: int,
        switch_cost: float,
        delay: int,
        *,
        rng: np.random.Generator,
        m: int = 100,
        delta: float = 0.95,
        draws: int = 2000,
        min_periods: int = 3,
        name: str = "upf_style_switch_timing_T3",
    ):
        if m < 1 or horizon % m != 0:
            raise ValueError("horizon must be a positive multiple of m")
        if min_periods < 2:
            raise ValueError("min_periods must be >= 2")
        self.name = name
        self.T, self.m, self.P = int(horizon), int(m), int(horizon) // int(m)
        self.cs = float(switch_cost)
        self.delay = int(delay)
        self.delta, self.draws, self.min_periods = float(delta), int(draws), int(min_periods)
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.rng = rng
        self._plan_seed = int(rng.integers(2**31 - 1))
        self.deployed = 0
        self.t = 0
        self._last_margin = float("nan")
        # per-period IPW accumulators: sum (2,), HT variance (2,), max release time, flags
        P = self.P
        self._sum = np.zeros((P, 2))
        self._var = np.zeros((P, 2))
        self._max_release = np.full(P, -1, dtype=np.int64)
        self._n_labels = np.zeros(P, dtype=np.int64)
        self._unlabelable = np.zeros(P, dtype=bool)  # a disagreement round had propensity 0
        self._n_dis = np.zeros(P, dtype=np.int64)
        self._ctx_sum: dict[int, np.ndarray] = {}
        self._n_events = np.zeros(P, dtype=np.int64)
        self.fit_log: list[dict] = []  # one entry per planning call, for audit/tests

    # ------------------------------------------------------------------ policy interface
    def predict(self, event: Event) -> int:
        self.t = event.t
        j = event.t // self.m
        self._n_events[j] += 1
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        self._n_dis[j] += int(dis)
        if event.context is not None:
            c = np.asarray(event.context, dtype=np.float64)
            self._ctx_sum[j] = self._ctx_sum.get(j, 0.0) + c
        if event.t > 0 and event.t % self.m == 0:
            self._replan(event.t)
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if dis and q <= 0.0:
            self._unlabelable[event.t // self.m] = True
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            j = fb.event_id // self.m
            q = float(fb.query_probability)
            if q <= 0.0:
                continue
            loss = np.asarray(fb.model_losses, dtype=np.float64)[:2]
            self._sum[j] += loss / q / self.m
            self._var[j] += loss**2 * (1.0 - q) / q**2 / self.m**2
            self._n_labels[j] += 1
            self._max_release[j] = max(self._max_release[j], int(fb.t_released))

    # ------------------------------------------------------------------ cells, forecast, plan
    def usable_periods(self, now: int) -> list[int]:
        """Periods that are over, fully released by ``now`` and IPW-positive."""
        cur = now // self.m
        return [
            j
            for j in range(cur)
            if (j + 1) * self.m - 1 + self.delay <= now and not self._unlabelable[j]
        ]

    def cell_estimates(self) -> np.ndarray:
        """(P, 2) IPW period-mean estimates accumulated so far."""
        return self._sum.copy()

    def _z(self, j: int) -> float:
        if j == 0 or self._n_events[j] == 0 or self._n_events[j - 1] == 0:
            return 0.0
        if self._ctx_sum:
            a = self._ctx_sum[j] / self._n_events[j]
            b = self._ctx_sum[j - 1] / self._n_events[j - 1]
            return float(np.sum(np.abs(a - b)))
        return abs(self._n_dis[j] / self._n_events[j] - self._n_dis[j - 1] / self._n_events[j - 1])

    def _replan(self, now: int) -> None:
        used = self.usable_periods(now)
        if len(used) < self.min_periods:
            self.fit_log.append({"t": now, "n_periods": len(used), "action": "warmup"})
            return
        cur = now // self.m
        X = np.array([[k, j, self._z(j)] for j in used for k in (0, 1)], dtype=np.float64)
        y = np.clip(np.array([self._sum[j, k] for j in used for k in (0, 1)]), 0.0, 1.0)
        ipw_var = float(np.mean([self._var[j, k] for j in used for k in (0, 1)]))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # convergence chatter on near-constant cells
            model = ElasticNetCV(cv=min(5, len(y)), random_state=0, max_iter=50_000).fit(X, y)
        resid = float(np.mean((y - model.predict(X)) ** 2))
        sigma2 = resid + ipw_var
        z_future = self._z(cur - 1)
        future = np.array(
            [[k, j, z_future] for k in (0, 1) for j in range(cur, self.P)], dtype=np.float64
        )
        mean = model.predict(future).reshape(2, self.P - cur)
        a, b = beta_parameters(mean, sigma2)
        rng = np.random.default_rng([self._plan_seed, cur])
        switch, margin = plan_switch(
            a, b, self.deployed, self.cs / self.m, delta=self.delta, draws=self.draws, rng=rng
        )
        self._last_margin = margin
        self.fit_log.append(
            {
                "t": now,
                "n_periods": len(used),
                "used_periods": used,
                "max_release_used": int(max(self._max_release[j] for j in used)),
                "sigma2": sigma2,
                "ipw_var": ipw_var,
                "margin": margin,
                "action": "switch" if switch else "stay",
            }
        )
        if switch:
            self.deployed = 1 - self.deployed

    # ------------------------------------------------------------------ bookkeeping
    def decision_state(self) -> str:
        return f"dep={self.deployed};margin={self._last_margin:.4g}"

    def state_dict(self) -> dict:
        return {
            "deployed": self.deployed,
            "t": self.t,
            "sum": self._sum.copy(),
            "var": self._var.copy(),
            "max_release": self._max_release.copy(),
            "n_labels": self._n_labels.copy(),
            "unlabelable": self._unlabelable.copy(),
            "n_dis": self._n_dis.copy(),
            "n_events": self._n_events.copy(),
            "n_disagree_acq": self.acq.n_disagree,
            "ctx_sum": {k: np.copy(v) for k, v in self._ctx_sum.items()},
            "rng": self.rng.bit_generator.state,
        }

    def load_state_dict(self, s: dict) -> None:
        self.deployed, self.t = int(s["deployed"]), int(s["t"])
        self._sum, self._var = s["sum"].copy(), s["var"].copy()
        self._max_release, self._n_labels = s["max_release"].copy(), s["n_labels"].copy()
        self._unlabelable, self._n_dis = s["unlabelable"].copy(), s["n_dis"].copy()
        self._n_events = s["n_events"].copy()
        self.acq.n_disagree = int(s["n_disagree_acq"])
        self._ctx_sum = {k: np.copy(v) for k, v in s["ctx_sum"].items()}
        self.rng.bit_generator.state = s["rng"]


def make_upf_style_switch_timing(T, budget, cs, cq, alpha, delay, r, **kw):
    """Factory with the ``extra=`` signature of ``suite.build_suite`` (``r`` = policy_rng)."""
    return UPFStyleSwitchTimingT3(T, budget, cs, delay, rng=r("upf_style_switch_timing_T3"), **kw)
