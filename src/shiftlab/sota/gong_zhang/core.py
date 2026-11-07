"""Gong & Zhang, "The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations"
(ICML 2026, PMLR 306). PAPER_RECONSTRUCTION of Algorithms 1-6 (finite policy class) and Algorithm 3 (oracle-efficient).

All constants below were read from RENDERED PAGE IMAGES of the PDF (pdftotext garbles them), not from the text layer:
  Alg 1 (p. 4):  w_t(pi) = exp(-eta_t sum_{s<t} lhat_s(pi(x_s)));  q_t(a) = (1-g) sum_{pi(x_t)=a} w_t / sum w_t + g/|A|;
                 p_t(a) = min{1, sqrt( eta_t q_t(a) / c_t(a) )}   (SQUARE ROOT; the earlier spec had no root);
                 lhat_t(a) = 1{a in O_t} l_t(a)/p_t(a).
  Thm 2.1:       eta_t = 1 / ( ( sum_{s<=t} sqrt(sum_a c_s(a)) / ln|Pi| )^{2/3} + sqrt( t / ln|Pi| ) ),  gamma = 1/T.
  Alg 2 (p. 6):  if B >= 1.5 c^{-2/3} (|A| ln|Pi|)^{1/3} T^{2/3}:  eta_t = (1/T) sqrt( B / (|A| ln|Pi|) ), run Alg 4
                 else:  eta_t = c^{-1/3} |A|^{-1/3} ln^{2/3}(|Pi|) t^{-2/3}, run Alg 6.
  Alg 4 (p. 29): observation sets from Alg 5 (exactly B observations, P(a in O_t) = B/(|A|T)), p_t(a) = B/(|A| T), free.
  Alg 5 (p. 29): m = floor(B/|A|), r = B - m|A|; r random actions get m+1 observation rounds, the rest m; each action's
                 rounds are a uniformly random subset of [T].
  Alg 6 (p. 30): as Alg 1 with uniform cost c; remaining budget B_t; excess observations (|O_t| - B_t)^+ are PAID at c.
  Alg 3 (p. 7):  inverse-gap weighting q_t(a) = 1/(|A| + gamma (fhat(x,a) - fhat(x,a*))) for a != a*, rest on a*;
                 eta_t = ( sum_s sqrt(sum_a c_s(a)) / Reg )^{2/3} + sqrt(t/Reg); p_t(a) = min{1, sqrt( q_t(1-q_t) / (eta_t c_t(a)) )};
                 Thm 4.1: gamma = sqrt( |A| T / (Reg + log(2/delta)) ).

Known inconsistency in the paper as printed (reported, not silently fixed): Alg 2 line 2 prints eta_t = (1/T) sqrt(B / (|A| ln|Pi|)).
Balancing ln|Pi|/eta + eta*T*|A|T/B (Lemma 2.1 with p = B/(|A|T)) gives eta = (1/T) sqrt(B ln|Pi| / |A|) (ln in the NUMERATOR),
which is what Thm 3.2's T sqrt(|A| ln|Pi| / B) needs. ``eta_form='printed'`` (default) follows the PDF; ``'balanced'`` is our own
derivation, labelled as such. Costs are uniform for Algs 2/4/6 (the paper's statement).
Guarantees are ADVERSARIAL-BANDIT REGRET bounds of the paper's game: no null hypothesis, no certificate, no label delay,
no drift. Nothing here transfers those bounds to the ShiftLab contract.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# ------------------------------------------------------------------ schedules


def eta_thm21(t: int, cum_sqrt_cost: float, ln_pi: float) -> float:
    """Theorem 2.1 learning rate; cum_sqrt_cost = sum_{s<=t} sqrt(sum_a c_s(a))."""
    return 1.0 / ((cum_sqrt_cost / ln_pi) ** (2.0 / 3.0) + math.sqrt(t / ln_pi))


def free_budget_threshold(c: float, n_actions: int, n_policies: int, T: int) -> float:
    """B0-type threshold used by Alg 2 line 1: 1.5 c^{-2/3} (|A| ln|Pi|)^{1/3} T^{2/3}."""
    return (
        1.5
        * c ** (-2.0 / 3.0)
        * (n_actions * math.log(n_policies)) ** (1.0 / 3.0)
        * T ** (2.0 / 3.0)
    )


def eta_sufficient(
    T: int, B: float, n_actions: int, n_policies: int, form: str = "printed"
) -> float:
    lnp = math.log(n_policies)
    if form == "printed":  # Alg 2 line 2 as printed
        return math.sqrt(B / (n_actions * lnp)) / T
    if form == "balanced":  # OUR derivation (see module docstring)
        return math.sqrt(B * lnp / n_actions) / T
    raise ValueError(form)


def eta_limited(t: int, c: float, n_actions: int, n_policies: int) -> float:
    """Alg 2 line 5: c^{-1/3} |A|^{-1/3} ln^{2/3}|Pi| t^{-2/3}."""
    return (
        c ** (-1.0 / 3.0)
        * n_actions ** (-1.0 / 3.0)
        * math.log(n_policies) ** (2.0 / 3.0)
        * t ** (-2.0 / 3.0)
    )


def obs_prob_paid(eta: float, q: np.ndarray, c: np.ndarray) -> np.ndarray:
    """p_t(a) = min{1, sqrt(eta q_t(a) / c_t(a))} (Algs 1, 6)."""
    return np.minimum(1.0, np.sqrt(eta * q / np.maximum(c, 1e-300)))


def random_subset_budget(n_actions: int, T: int, B: int, rng: np.random.Generator) -> np.ndarray:
    """Algorithm 5. Returns a boolean (T, |A|) array of observation sets with exactly B ones and P(a in O_t) = B/(|A|T)."""
    if not 0 <= B <= n_actions * T:
        raise ValueError("B must lie in [0, |A| T]")
    m, r = divmod(B, n_actions)
    counts = np.full(n_actions, m)
    counts[rng.permutation(n_actions)[:r]] += 1
    O = np.zeros((T, n_actions), dtype=bool)
    for a in range(n_actions):
        O[rng.permutation(T)[: counts[a]], a] = True
    return O


# ------------------------------------------------------------------ Algorithms 1 / 4 / 6 (finite policy class)


@dataclass
class StepOut:
    action: int
    q: np.ndarray
    p: np.ndarray
    observed: np.ndarray  # bool (|A|,)
    paid: float  # observation cost paid this round


class PaidExp4:
    """Exponential weights over a finite policy class with paid / budgeted loss observation.

    mode='paid'   : Algorithm 1 (costs c_t(a) given each round; observation cost always paid).
    mode='free_I' : Algorithm 4 (observation sets from Algorithm 5, p = B/(|A|T), all within the free budget).
    mode='free_II': Algorithm 6 (uniform cost c; budget counter; excess observations paid).
    Usage per round: ``out = alg.step(pol_actions, costs, rng)``; then ``alg.update(out, losses)`` with the FULL loss vector
    (only observed entries are read).
    """

    def __init__(
        self,
        n_actions,
        n_policies,
        T,
        mode="paid",
        B=None,
        c=None,
        gamma=None,
        eta_form="printed",
        eta_override=None,
        rng=None,
    ):
        self.A, self.P, self.T, self.mode = n_actions, n_policies, T, mode
        self.gamma = 1.0 / T if gamma is None else gamma
        self.B, self.c, self.eta_form, self.eta_override = B, c, eta_form, eta_override
        self.cum_loss = np.zeros(n_policies)  # sum_s lhat_s(pi(x_s)) per policy
        self.t = 0
        self.cum_sqrt_cost = 0.0
        self.B_t = B
        self.ln_pi = math.log(n_policies)
        self.obs_sets = None
        if mode == "free_I":
            self.obs_sets = random_subset_budget(
                n_actions, T, int(B), rng or np.random.default_rng(0)
            )
        self.total_obs = 0

    def eta(self, costs: np.ndarray) -> float:
        if self.eta_override is not None:
            return self.eta_override
        if self.mode == "paid":
            return eta_thm21(self.t, self.cum_sqrt_cost, self.ln_pi)
        if self.mode == "free_I":
            return eta_sufficient(self.T, self.B, self.A, self.P, self.eta_form)
        return eta_limited(self.t, self.c, self.A, self.P)

    def step(self, pol_actions: np.ndarray, costs: np.ndarray, rng: np.random.Generator) -> StepOut:
        self.t += 1
        self.cum_sqrt_cost += math.sqrt(float(np.sum(costs)))
        eta = self.eta(costs)
        w = np.exp(-eta * (self.cum_loss - self.cum_loss.min()))
        mass = np.bincount(pol_actions, weights=w, minlength=self.A)
        q = (1 - self.gamma) * mass / w.sum() + self.gamma / self.A
        a = int(rng.choice(self.A, p=q / q.sum()))
        if self.mode == "free_I":
            p = np.full(self.A, self.B / (self.A * self.T))
            obs = self.obs_sets[self.t - 1].copy()
        else:
            p = obs_prob_paid(eta, q, costs)
            obs = rng.random(self.A) < p
        if self.mode == "paid":
            paid = float(np.sum(costs[obs]))
        elif self.mode == "free_II":
            paid = float(max(int(obs.sum()) - self.B_t, 0) * self.c)
            self.B_t = max(self.B_t - int(obs.sum()), 0)
        else:
            paid = 0.0
        self.total_obs += int(obs.sum())
        self._pol = pol_actions
        return StepOut(a, q, p, obs, paid)

    def update(self, out: StepOut, losses: np.ndarray) -> np.ndarray:
        lhat = np.where(out.observed, np.where(out.observed, losses, 0.0) / out.p, 0.0)
        self.cum_loss += lhat[self._pol]
        return lhat


class MetaController:
    """Algorithm 2: picks Alg 4 or Alg 6 from the free budget B and runs it. Uniform cost c."""

    def __init__(self, n_actions, n_policies, T, B, c, gamma=None, eta_form="printed", rng=None):
        self.threshold = free_budget_threshold(c, n_actions, n_policies, T)
        self.sufficient = B >= self.threshold
        self.mode = "free_I" if self.sufficient else "free_II"
        self.alg = PaidExp4(
            n_actions,
            n_policies,
            T,
            mode=self.mode,
            B=B,
            c=c,
            gamma=gamma,
            eta_form=eta_form,
            rng=rng,
        )

    def step(self, *a, **k):
        return self.alg.step(*a, **k)

    def update(self, *a, **k):
        return self.alg.update(*a, **k)


# ------------------------------------------------------------------ synthetic game (paper's Sec 5 style) + runner


class LinearPolicyGame:
    """Contexts: L2-normalised Gaussians; Pi: |Pi| linear policies pi(x) = argmax_a (W_pi x)_a with N(0,1) weights;
    losses l_t(a) ~ U(0,1) (as in the paper's Alg 1 experiment). Losses are generated by the evaluator; learners see only
    what they observe. Regret is against the best fixed policy in hindsight."""

    def __init__(
        self, T, d, n_actions, n_policies, seed, cost_range=(0.01, 0.5), loss="uniform", bias=0.0
    ):
        r = np.random.default_rng(seed)
        self.T, self.A, self.P = T, n_actions, n_policies
        X = r.normal(size=(T, d))
        self.X = X / np.linalg.norm(X, axis=1, keepdims=True)
        W = r.normal(size=(n_policies, n_actions, d))
        self.pol_actions = np.argmax(np.einsum("pad,td->tpa", W, self.X), axis=2)  # (T, P)
        self.costs = r.uniform(*cost_range, size=(T, n_actions))
        L = r.uniform(size=(T, n_actions))
        if bias:  # make one policy genuinely better so regret rates are visible: policy 0's action is cheaper
            best = self.pol_actions[:, 0]
            L[np.arange(T), best] = np.clip(L[np.arange(T), best] - bias, 0, 1)
        self.L = L
        self.policy_loss = self.L[np.arange(T)[:, None], self.pol_actions].sum(0)  # (P,)
        self.best_policy_loss = float(self.policy_loss.min())


def run_paid(game: LinearPolicyGame, alg, rng) -> dict:
    """Run a PaidExp4/MetaController on a LinearPolicyGame; returns regret decomposition R(T) of Eq. (1)."""
    loss = paid = 0.0
    for t in range(game.T):
        out = alg.step(game.pol_actions[t], game.costs[t], rng)
        loss += game.L[t, out.action]
        paid += out.paid
        alg.update(out, game.L[t])
    return {
        "learning": loss - game.best_policy_loss,
        "obs_cost": paid,
        "regret": loss - game.best_policy_loss + paid,
        "n_obs": alg_obs(alg),
    }


def alg_obs(alg) -> int:
    return (alg.alg if isinstance(alg, MetaController) else alg).total_obs


# ------------------------------------------------------------------ Algorithm 3 (oracle-efficient)


class OnlineRidge:
    """Per-action online ridge regression (recursive least squares): the 'linear function class' oracle of Sec 5."""

    def __init__(self, n_actions: int, d: int, lam: float = 1.0):
        self.Ainv = np.stack([np.eye(d) / lam for _ in range(n_actions)])
        self.b = np.zeros((n_actions, d))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.array([(self.Ainv[a] @ self.b[a]) @ x for a in range(len(self.b))])

    def update(self, x: np.ndarray, a: int, y: float) -> None:
        Ax = self.Ainv[a] @ x
        self.Ainv[a] -= np.outer(Ax, Ax) / (1.0 + x @ Ax)
        self.b[a] += y * x


class OracleEfficientPaid:
    """Algorithm 3. ``reg_sq`` = Reg_Sq(T) of the oracle (paper cites O(d log(T/d)) for linear classes; the constant is OURS)."""

    def __init__(
        self,
        n_actions: int,
        d: int,
        T: int,
        reg_sq: float | None = None,
        delta: float = 0.1,
        oracle=None,
    ):
        self.A, self.T, self.t = n_actions, T, 0
        self.reg = reg_sq if reg_sq is not None else d * math.log(max(T / d, 2.0))
        self.gamma = math.sqrt(n_actions * T / (self.reg + math.log(2.0 / delta)))
        self.oracle = oracle or OnlineRidge(n_actions, d)
        self.cum_sqrt_cost = 0.0
        self.total_obs = 0

    def step(self, x: np.ndarray, costs: np.ndarray, rng) -> StepOut:
        self.t += 1
        self.cum_sqrt_cost += math.sqrt(float(np.sum(costs)))
        f = self.oracle.predict(x)
        astar = int(np.argmin(f))
        q = 1.0 / (self.A + self.gamma * (f - f[astar]))
        q[astar] = 0.0
        q[astar] = 1.0 - q.sum()
        a = int(rng.choice(self.A, p=q / q.sum()))
        eta = (self.cum_sqrt_cost / self.reg) ** (2.0 / 3.0) + math.sqrt(self.t / self.reg)
        p = np.minimum(1.0, np.sqrt(q * (1.0 - q) / (eta * np.maximum(costs, 1e-300))))
        obs = rng.random(self.A) < p
        self.total_obs += int(obs.sum())
        self._x = x
        return StepOut(a, q, p, obs, float(np.sum(costs[obs])))

    def update(self, out: StepOut, losses: np.ndarray) -> None:
        for a in np.flatnonzero(out.observed):
            self.oracle.update(self._x, int(a), float(losses[a]))
