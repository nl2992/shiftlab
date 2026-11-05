"""WP2 (sprint 2, Agent F): synthetic exchangeable-twin analogues with richer sign dependence.

Policies (``EXTRA``): one marginal-null baseline added at the lead's request (2026-11-04, after the
novelty audit, before any WP2 policy run): ``DM_HAC_monitor``, an ADAPTATION of the sequential
Diebold-Mariano / Chu-Stinchcombe-White (1996) monitoring idea to the label-budgeted contract (see
``DMHACMonitor``). It has at most asymptotic, mixing-based size; it is NOT anytime-valid. Importing this module
registers the ``WP2_*`` synthetic regimes in ``bench.SPRINT_REGIMES`` so that both screen.py and
wp2_run.py can run them (registry.py autoloads fam_f).

Every regime draws, per episode (= per seed), an exchangeable role coin U in {-1,+1} and sets the
episode's base challenger-win probability on a disagreement to p_e = p_base + U * delta:

* ``delta = 0``                      -> a pure dependent null (marginal and episode-level advantage 0);
* ``delta > 0, p_base = .5`` (twin)  -> a synthetic exchangeable-twin null: marginal advantage 0 over U,
  but a persistent episode-level effect (one twin is better in this episode), as in the real twins;
* ``p_base = .65`` (better)          -> a dependent alternative.

The sign process s_t (True = challenger right on a disagreement) has marginal P(s_t) = p_e and
dependence structure:

* ``iid``        s_t ~ Bern(p_e)
* ``markov1``    keep s_{t-1} w.p. rho, else Bern(p_e)
* ``order2``     copy s_{t-1} w.p. .50, copy s_{t-2} w.p. .40, else Bern(p_e)   (second-order Markov)
* ``semimarkov`` runs with discrete Pareto(1.5)+1 lengths in event time, run sign Bern(p_e)
* ``hidden``     hidden h_t in {-1,+1}, switching w.p. 1/500 per event, s_t ~ Bern(p_e + .2 h_t)

Disagreements arrive iid with probability ``dis`` (.2); agreements are both wrong w.p. .1, as in the
locked FLQ regimes. ``truth_gain`` returns the MARGINAL gain dis*(2 p_base - 1) (evaluator-side
diagnostic only); episode-level and conditional advantages are measured from realised losses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bench import SPRINT_REGIMES

from simulator import QueryRequest  # noqa: E402  (path set by bench/suite importers)


def newey_west_var(z: np.ndarray, lag: int | None = None) -> float:
    """Bartlett-kernel HAC long-run variance of z (Newey-West 1987; lag = floor(4 (n/100)^(2/9)))."""
    n = len(z)
    if lag is None:
        lag = int(np.floor(4 * (n / 100) ** (2 / 9)))
    x = z - z.mean()
    v = float(x @ x) / n
    for k in range(1, min(lag, n - 1) + 1):
        v += 2 * (1 - k / (lag + 1)) * float(x[k:] @ x[:-k]) / n
    return max(v, 1e-12)


class DMHACMonitor:
    """Sequential DM-type monitor for the MARGINAL null E[d] <= 0 (adaptation; asymptotic only).

    * Acquisition: only disagreements carry information (on agreements d_t = 0 is known without a
      label). Each disagreement is queried with probability q_t = min(1, remaining / expected
      remaining disagreements), the disagreement rate estimated online (uniform pacing, frozen at
      issue).
    * Evidence: z_i = l0 - l1 in {-1, +1} on the i-th released queried disagreement (query order).
    * Statistic: W_n = sum z_i / (sigma_HAC sqrt(N)), N = B the planned evidence count, sigma_HAC^2 the
      Newey-West long-run variance of z_1..z_n (not demeaned under the null; recomputed each release).
    * Boundary: one-sided linear CUSUM boundary a (1 + n/N) with exp(-2 a^2) = alpha, the Brownian
      first-passage level for sup_s W(s) - a(1 + s) (CSW 1996 use boundaries of this type for
      monitoring). Promotion is allowed after ``burn`` released evidence points; it is absorbing.
      Querying stops at the decision.
    Validity: none in finite samples. Under a stationary mixing marginal null the boundary has
    asymptotic level alpha over the first N evidence points; with episode-level heterogeneity (twins)
    the null holds only marginally over episodes, so a per-episode test is not controlled.
    """

    def __init__(self, T, B, alpha, rng, name="DM_HAC_monitor", burn=30, lag=None):
        self.name, self.T, self.B, self.alpha, self.rng = name, T, B, alpha, rng
        self.burn, self.lag = burn, lag
        self.a = float(np.sqrt(np.log(1 / alpha) / 2))
        self.z: list[float] = []
        self.deployed, self.decided = 0, False
        self.n_dis, self.t_seen = 0, 0
        self.stat = 0.0

    def predict(self, event):
        return self.deployed

    def request_labels(self, event, remaining_budget):
        self.t_seen += 1
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        self.n_dis += dis
        if self.decided or not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        rate = (self.n_dis + 1) / (self.t_seen + 2)
        exp_rem = max(1.0, rate * (event.horizon - event.t))
        q = float(min(1.0, remaining_budget / exp_rem))
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback):
        for fb in feedback:
            d = float(fb.model_losses[0]) - float(fb.model_losses[1])
            if d != 0:
                self.z.append(d)
        n = len(self.z)
        if self.decided or n < self.burn:
            return
        z = np.asarray(self.z)
        self.stat = float(z.sum() / np.sqrt(newey_west_var(z, self.lag) * self.B))
        if self.stat >= self.a * (1 + n / self.B):
            self.deployed, self.decided = 1, True

    def decision_state(self):
        return f"dep={self.deployed};n={len(self.z)};W={self.stat:.2f}"

    def state_dict(self):
        return {"z": list(self.z), "deployed": self.deployed, "decided": self.decided,
                "n_dis": self.n_dis, "t_seen": self.t_seen}

    def load_state_dict(self, state):
        self.z = list(state["z"])
        self.deployed, self.decided = state["deployed"], state["decided"]
        self.n_dis, self.t_seen = state["n_dis"], state["t_seen"]


EXTRA: dict = {
    "DM_HAC_monitor": lambda T, B, cs, cq, a, d, r: DMHACMonitor(T, B, a, rng=r("DM_HAC")),
    # ablation: iid variance (lag 0) = the same monitor with no dependence correction
    "DM_HAC_monitor-iid": lambda T, B, cs, cq, a, d, r: DMHACMonitor(
        T, B, a, rng=r("DM_HAC"), lag=0, name="DM_HAC_monitor-iid"),
}


@dataclass(frozen=True)
class DepTwin:
    name: str
    structure: str
    p_base: float = 0.5
    delta: float = 0.0
    rho: float = 0.8
    dis: float = 0.2
    delay: int = 100
    err_agree: float = 0.1
    switch_q: float = 1 / 500
    hidden_a: float = 0.2
    family: str = "wp2_dependence"
    tags: tuple = ()

    def truth_gain(self, horizon: int = 2000) -> np.ndarray:
        return np.full(horizon, self.dis * (2.0 * self.p_base - 1.0))

    def episode_p(self, rng: np.random.Generator) -> float:
        u = 1.0 if rng.random() < 0.5 else -1.0
        return float(np.clip(self.p_base + u * self.delta, 0.0, 1.0))

    def signs(self, rng: np.random.Generator, p: float, horizon: int) -> np.ndarray:
        s = np.empty(horizon, dtype=bool)
        k = self.structure
        if k == "iid":
            s[:] = rng.random(horizon) < p
        elif k == "markov1":
            s[0] = rng.random() < p
            keep, fresh = rng.random(horizon) < self.rho, rng.random(horizon) < p
            for t in range(1, horizon):
                s[t] = s[t - 1] if keep[t] else fresh[t]
        elif k == "order2":
            s[:2] = rng.random(2) < p
            u, fresh = rng.random(horizon), rng.random(horizon) < p
            for t in range(2, horizon):
                s[t] = s[t - 1] if u[t] < 0.5 else (s[t - 2] if u[t] < 0.9 else fresh[t])
        elif k == "semimarkov":
            t = 0
            while t < horizon:
                run = int(np.floor(rng.pareto(1.5) + 1.0))
                s[t:t + run] = rng.random() < p
                t += run
        elif k == "hidden":
            h = np.empty(horizon)
            h[0] = 1.0 if rng.random() < 0.5 else -1.0
            sw = rng.random(horizon) < self.switch_q
            for t in range(1, horizon):
                h[t] = -h[t - 1] if sw[t] else h[t - 1]
            s[:] = rng.random(horizon) < np.clip(p + self.hidden_a * h, 0.0, 1.0)
        else:
            raise ValueError(k)
        return s

    def sample(self, rng: np.random.Generator, horizon: int = 2000) -> np.ndarray:
        p = self.episode_p(rng)
        on = rng.random(horizon) < self.dis
        sign = self.signs(rng, p, horizon)
        both_wrong = rng.random(horizon) < self.err_agree
        l0 = np.where(on, sign, both_wrong).astype(np.int8)
        l1 = np.where(on, ~sign, both_wrong).astype(np.int8)
        return np.stack([l0, l1], axis=1)


TWIN_DELTA = 0.05  # p_e in {.45, .55}: per-event episode advantage +-.02 (real twins: .002-.02)


def _regs() -> list[DepTwin]:
    out = [DepTwin("WP2_iid_twin", "iid", delta=TWIN_DELTA, tags=("null", "twin")),
           DepTwin("WP2_m8_twin", "markov1", delta=TWIN_DELTA, tags=("null", "twin", "dep"))]
    for k, short in (("order2", "o2"), ("semimarkov", "sm"), ("hidden", "hs")):
        out += [DepTwin(f"WP2_{short}_null", k, tags=("null", "dep")),
                DepTwin(f"WP2_{short}_twin", k, delta=TWIN_DELTA, tags=("null", "twin", "dep")),
                DepTwin(f"WP2_{short}_better", k, p_base=0.65, tags=("alt", "dep"))]
    return out


WP2_REGIMES = {r.name: r for r in _regs()}
SPRINT_REGIMES.update(WP2_REGIMES)
