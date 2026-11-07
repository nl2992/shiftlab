"""Active statistical inference for the MEAN (Zrnic & Candes, ICML 2024, arXiv 2403.03208). PAPER_RECONSTRUCTION.

Read: main text Secs 1-8 and appendix A (proofs, Assumptions 1-3), appendix C (non-asymptotic results), from the PDF.
No author code was run. Only the mean-estimation case is implemented (M-estimation is NOT).

Native (paper) objects:
  Batch estimator     theta_hat = 1/n sum_i [ f(X_i) + (Y_i - f(X_i)) xi_i / pi(X_i) ],  xi_i ~ Bern(pi(X_i))   (Eq. 5)
  Sampling rule       pi(x) = eta * u(x), eta_hat = max{eta in H: eta sum_i u(X_i) <= n_b}                    (Eq. 4)
                      mixture  pi^(tau) = (1 - tau) pi + tau n_b/n                                             (Sec 7.2)
  tau tuning (hist.)  argmin_tau sum_h (Y_h - f(X_h))^2 / pi^(tau)(X_h)                                        (Eq. 12)
  Sequential          Delta_t = f_t(X_t) + (Y_t - f_t(X_t)) xi_t / pi_t(X_t), theta_hat = mean_t Delta_t        (Eq. 7)
                      pi_t(x) = clip_[0,1]( min{ eta_t u_t(x), n_{Delta,t} } ),
                      eta_t = n_b / (n * Ehat[u_t(X)]), n_{b,t} = t n_b / n, n_{Delta,t} = n_{b,t} - n_lab,t-1  (Eq. 8)
  CI                  theta_hat +- z_{1-alpha/2} sigma_hat / sqrt(n), sigma_hat^2 = empirical variance of the increments.
Guarantee (asymptotic ONLY): Prop 1 (batch): requires P(eta_hat = eta*) -> 1 for some eta* in H; Prop 2 (sequential):
requires (1/n) sum_t sigma_t^2 -> sigma^2 in probability for a fixed (f, pi) limit, and the Lindeberg condition
(Ass. 2); then coverage -> 1 - alpha as n -> infinity. Finite-sample unbiasedness of Delta_t needs pi_t > 0,
predictable (F_{t-1}-measurable given X_t) and logged.

Choices NOT fixed by the paper (labelled design parameters): the frequency of the 'budget-fill' rounds
(pi_t = clip(n_Delta,t)) is unspecified in the text; ``fill_every`` is ours. Ehat[u_t(X)] is computed as the running
mean of the u values observed so far (a causal empirical approximation). n_b is an expected budget, not a pathwise cap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import norm

# ---------------------------------------------------------------- uncertainty measures (Sec 4, Eq. 3)


def uncertainty_multiclass(p: np.ndarray) -> np.ndarray:
    """u(x) = K/(K-1) (1 - max_i p_i(x)); p has shape (n, K)."""
    p = np.asarray(p, float)
    K = p.shape[-1]
    return K / (K - 1.0) * (1.0 - p.max(-1))


def uncertainty_binary(p: np.ndarray) -> np.ndarray:
    """u(x) = 2 min{p, 1-p} (Eq. 3 with K = 2)."""
    p = np.asarray(p, float)
    return 2.0 * np.minimum(p, 1.0 - p)


# ---------------------------------------------------------------- sampling rules


def budget_scale(u: np.ndarray, n_b: float) -> float:
    """eta_hat = n_b / sum_i u(X_i) (H = R_+, the largest eta with eta sum u <= n_b, Eq. 4)."""
    s = float(np.sum(u))
    if s <= 0:
        raise ValueError("sum of uncertainties is zero")
    return n_b / s


def batch_rule(u: np.ndarray, n_b: float, tau: float = 0.0) -> np.ndarray:
    """pi^(tau)(X_i) = (1 - tau) clip(eta_hat u(X_i)) + tau n_b/n. With clipping, E[n_lab] <= n_b still holds."""
    n = len(u)
    pi = np.clip(budget_scale(u, n_b) * np.asarray(u, float), 0.0, 1.0)
    return (1.0 - tau) * pi + tau * (n_b / n)


def tune_tau(u_hist: np.ndarray, err2_hist: np.ndarray, n_b_hist: float, grid=None) -> float:
    """Eq. (12): tau = argmin_tau sum_h (Y_h - f(X_h))^2 / pi^(tau)(X_h), on a held-out historical sample."""
    grid = np.linspace(0.0, 1.0, 21) if grid is None else grid
    best = min(grid, key=lambda t: float(np.sum(err2_hist / batch_rule(u_hist, n_b_hist, t))))
    return float(best)


def oracle_rule(cond_err2: np.ndarray, n_b: float) -> np.ndarray:
    """Oracle rule minimising Var under E[pi] = n_b/n: pi(x) proportional to sqrt(E[(Y-f)^2 | X = x]) (Sec 7.1, Eq. 9)."""
    r = np.sqrt(np.asarray(cond_err2, float))
    return np.clip(r * n_b / r.sum(), 0.0, 1.0)


# ---------------------------------------------------------------- estimators


@dataclass(frozen=True)
class ActiveMeanResult:
    estimate: float
    sigma_hat: float
    ci: tuple[float, float]
    n: int
    n_labelled: int


def ipw_increments(f: np.ndarray, y: np.ndarray, xi: np.ndarray, pi: np.ndarray) -> np.ndarray:
    """Delta_i = f_i + (y_i - f_i) xi_i / pi_i; y is read only where xi_i = 1."""
    f, xi, pi = (np.asarray(a, float) for a in (f, xi, pi))
    if (pi <= 0).any() or (pi > 1).any():
        raise ValueError("propensities must lie in (0, 1]")
    y = np.where(xi > 0, np.asarray(y, float), 0.0)  # unlabelled y never enters
    return f + (y - f) * xi / pi


def active_mean(f, y, xi, pi, alpha: float = 0.1) -> ActiveMeanResult:
    """Batch/sequential active mean estimate with the Wald CI (asymptotic). sigma_hat = std of the increments."""
    d = ipw_increments(f, y, xi, pi)
    n = len(d)
    est = float(d.mean())
    sig = float(d.std(ddof=1))
    half = float(norm.ppf(1 - alpha / 2)) * sig / math.sqrt(n)
    return ActiveMeanResult(est, sig, (est - half, est + half), n, int(np.sum(xi)))


def batch_active_inference(f, y_oracle, u, n_b, tau, rng, alpha=0.1) -> ActiveMeanResult:
    """Algorithm 1 for the mean. ``y_oracle`` is the hidden label array; only entries with xi = 1 are used."""
    pi = batch_rule(u, n_b, tau)
    xi = (rng.random(len(pi)) < pi).astype(float)
    return active_mean(f, y_oracle, xi, pi, alpha)


def uniform_ppi(f, y_oracle, n_b, rng, alpha=0.1) -> ActiveMeanResult:
    """Uniform-sampling baseline with predictions: pi = n_b/n (prediction-powered inference, as in the paper)."""
    n = len(f)
    return batch_active_inference(f, y_oracle, np.ones(n), n_b, 0.0, rng, alpha)


def classical_mean(y_oracle, n_b, rng, alpha=0.1) -> ActiveMeanResult:
    """Classical inference from a uniform labelled subsample only (no predictions)."""
    n = len(y_oracle)
    idx = rng.choice(n, size=int(n_b), replace=False)
    ys = np.asarray(y_oracle, float)[idx]
    est, sig = float(ys.mean()), float(ys.std(ddof=1))
    half = float(norm.ppf(1 - alpha / 2)) * sig / math.sqrt(len(ys))
    return ActiveMeanResult(est, sig, (est - half, est + half), len(ys), len(ys))


# ---------------------------------------------------------------- sequential rule (Eq. 8)


@dataclass
class SequentialRule:
    """Causal sampling-probability generator for sequential active inference.

    ``propose(u_t)`` returns pi_t for the current unlabelled X_t given its uncertainty u_t = u_t(X_t) from the model at t.
    ``record(xi, u_t)`` must be called after the labelling decision. pi_t depends only on X_t and past decisions.
    """

    n: int
    n_b: float
    tau: float = 0.5  # paper default in the sequential setting
    fill_every: int = 0  # 0 = never use the budget-fill round; otherwise every fill_every-th round (OURS, unspecified in paper)
    t: int = field(default=0, init=False)
    n_lab: int = field(default=0, init=False)
    u_sum: float = field(default=0.0, init=False)

    def propose(self, u_t: float) -> float:
        t = self.t + 1
        u_mean = (self.u_sum + u_t) / t
        eta_t = self.n_b / (self.n * max(u_mean, 1e-12))
        n_bt = t * self.n_b / self.n
        n_delta = n_bt - self.n_lab
        if self.fill_every and t % self.fill_every == 0:
            base = float(np.clip(n_delta, 0.0, 1.0))
        else:
            base = float(np.clip(min(eta_t * u_t, n_delta), 0.0, 1.0))
        return (1.0 - self.tau) * base + self.tau * (self.n_b / self.n)

    def record(self, xi: int, u_t: float) -> None:
        self.t += 1
        self.n_lab += int(xi)
        self.u_sum += float(u_t)
