"""COMMON_CONTRACT_PORT core for Gong & Zhang: label acquisition + candidate-vs-incumbent selection.

STATUS: a PORT, not the paper's algorithm. It re-uses the paper's observation-probability rules inside a different game.
Mapping (ours): A = {serve incumbent, serve candidate} (|A| = 2), Pi = {constant-incumbent, constant-candidate} (|Pi| = 2),
"observe a loss" = request ONE label whose shadow losses reveal both models' losses at once; observation cost c = c_q.
  * q_t(a) = (1 - gamma) w_a / (w_inc + w_cand) + gamma/2 from exponential weights on importance-weighted released losses
    (Alg 1 lines 4-5; gamma = 1/T as in Thm 2.1).
  * per-action probability p_t(a) = min{1, sqrt(eta_t q_t(a) / c)} (Alg 1/6 line 7); because one label reveals both losses the
    port requests a label with p_t = 1 - prod_a (1 - p_t(a)) and importance-weights BOTH losses by 1/p_t (declared propensity).
  * regime choice by Alg 2: sufficient budget (label cap B >= 1.5 c^{-2/3} (2 ln 2)^{1/3} T^{2/3}) -> uniform pacing p_t = (B - used)/(T - t + 1)
    (our replacement for Alg 5's pre-drawn random subset: the propensity must be a verifiable Bernoulli(u < p) for the contract
    audit; it keeps the cap pathwise and the marginal rate ~ B/T); else Alg-6-style rule above. The contract's label cap is
    HARD (the paper's Alg 6 would pay for excess observations): requests stop at the cap.
  * the paper has no switching action and no delay. The port switches to the candidate when q_cand > 1/2 on released labels
    only; the candidate's IW loss is shifted by the contract hurdle h (candidate must beat the incumbent by h). Labels are
    used at RELEASE; the propensity recorded at request is used (no re-computation).
The paper's regret bounds do NOT transfer (non-adversarial drift, delayed labels, non-stationary best arm, switching costs).
"""

from __future__ import annotations

import numpy as np

from .core import eta_limited, eta_sufficient, free_budget_threshold


class PaidLabelAcquirer:
    def __init__(
        self,
        T: int,
        c_q: float,
        label_cap: int,
        hurdle: float = 0.0,
        eta_form: str = "printed",
        seed: int = 0,
    ) -> None:  # seed unused (kept for API stability)
        self.T, self.c, self.B, self.h = T, c_q, int(label_cap), hurdle
        self.A = self.P = 2
        self.gamma = 1.0 / T
        self.threshold = free_budget_threshold(c_q, self.A, self.P, T)
        self.sufficient = self.B >= self.threshold
        self.eta_form = eta_form
        self.cum_loss = np.zeros(2)  # [incumbent, candidate] IW cumulative losses
        self.used = 0

    # ---- policy distribution over {incumbent, candidate}
    def q(self) -> np.ndarray:
        eta = self._eta(max(1, self._t))
        w = np.exp(-eta * (self.cum_loss - self.cum_loss.min()))
        return (1 - self.gamma) * w / w.sum() + self.gamma / self.A

    _t = 1

    def _eta(self, t: int) -> float:
        if self.sufficient:
            return eta_sufficient(self.T, self.B, self.A, self.P, self.eta_form)
        return eta_limited(t, self.c, self.A, self.P)

    def request_probability(self, t: int) -> float:
        """Declared propensity for a label request at round t (before the hard cap)."""
        self._t = t
        if (
            self.sufficient
        ):  # budget pacing: honest predictable propensity, hard cap respected pathwise
            return max(self.B - self.used, 0) / (self.T - t + 1)
        pa = np.minimum(1.0, np.sqrt(self._eta(t) * self.q() / self.c))
        return float(1.0 - np.prod(1.0 - pa))

    def decide(self, t: int, u: float) -> tuple[bool, float | None]:
        """(request?, declared propensity). ``u`` is a shared Uniform(0,1) draw; request iff u < p (audit-verifiable)."""
        if self.used >= self.B:
            return False, None
        p = min(max(self.request_probability(t), 1e-9), 1.0)
        hit = u < p
        if hit:
            self.used += 1
        return hit, p

    def on_release(self, loss_inc: float, loss_cand: float, propensity: float | None) -> None:
        p = propensity if propensity else 1.0
        self.cum_loss[0] += loss_inc / p
        self.cum_loss[1] += (
            loss_cand + self.h
        ) / p  # candidate must beat the incumbent by the hurdle (port choice)

    def q_candidate(self) -> float:
        return float(self.q()[1])

    def prefers_candidate(self) -> bool:
        return self.q_candidate() > 0.5
