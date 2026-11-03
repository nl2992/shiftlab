"""Online LLM Picker (Turrin, Okanovic, Hoefler, Gurel; arXiv:2610.01592).

Ported from the paper's full text (Eq. 10 and the surrounding algorithm box), because no author
implementation was located. Every formula below is quoted in the comment above it; nothing is
reconstructed from the abstract, which carries none of the method.

The published method:

    l^k_{t,i} = 1 - d(f_i(x_t), f_k(x_t))        loss of model i if model k's output were truth
    Var_k     = Var_{i ~ p_t}[ l^k_{t,i} ]       variance over models drawn from the posterior
    Hbar(p)   = H(p) / log m                     normalised posterior entropy
    q_t       = max{ max_k Var_k * Hbar(p_t), eta_t }   if max_k Var_k != 0, else 0
    Q_t       ~ Bernoulli(q_t)
    lhat_{t,i}= l^y_{t,i} * Q_t / q_t            importance weighted by the ISSUE-TIME q_t
    Lhat_t    = Lhat_{t-1} + lhat_t
    p_{t,i}   ∝ exp(-eta_t * Lhat_{t-1,i})
    eta_t     = sqrt(log m / (t * (Vhat_t + eps)))
    Vhat_t    = V_t / (1 - beta^t)               bias-corrected EMA, updated only on annotation
    recommendation = argmax_i p_{t,i}            one rule; no separate prediction rule

ADAPTER NOTES, all recorded in `SOTA_APPLICABILITY_REPORTS.md`:

* **Loss type.** The published loss is similarity-based (ROUGE-L / BERTScore). In a binary
  classification task `d` becomes exact agreement, so `l^k_i = 1{f_i != f_k}`. This is a
  legitimate specialisation of their definition but not the regime they built or tuned for.
* **Budget.** The paper enforces an *expected proportion*, not a hard cap, and is itself
  inconsistent about this. Our hard cap is imposed by the simulator and is an adapter decision.
* **Scale.** Formally valid at m = 2 (log m > 0), but the paper only evaluates collections of
  130+ models, so behaviour at m = 2 is untested by its authors.

BLOCKED: the numerical value of `eps` in `eta_t = sqrt(log m / (t (Vhat_t + eps)))` was not
recoverable from the text and no author implementation was located, so `eps = 1e-8` here is OUR
choice, not theirs. It matters: until the first annotation `Vhat = 0`, so `eta_t` is enormous and
`q_t` clips to 1, and the method queries every disagreement during burn-in. Under the paper's
expected-proportion budget that is harmless; under our hard cap it spends the whole budget in the
opening events (measured in `test_budget_is_spent_early_under_the_cap`). Any result for this
comparator must carry that caveat, because a different `eps` would change it.

DEGENERACY, derived and verified by test: with two models and a binary label, on disagreement
`l^0 = (0,1)` and `l^1 = (1,0)`, so `Var_0 = Var_1 = p(1-p)` and
`q_t = max{p(1-p) * H(p)/log 2, eta_t}`; on agreement both variances are zero and `q_t = 0`. The
score therefore carries **no instance information** and the method reduces to disagreement-gated
sampling at a posterior-balance rate. This is the same collapse measured for Model Picker and must
be disclosed wherever this comparator appears.
"""

from __future__ import annotations

import numpy as np
from simulator import Event, QueryRequest, ReleasedFeedback


def _entropy(p: np.ndarray) -> float:
    """Shannon entropy in nats, with the 0 log 0 = 0 convention."""
    q = p[p > 0]
    return float(-np.sum(q * np.log(q)))


def pseudo_loss_matrix(predictions: np.ndarray, n_classes: int) -> np.ndarray:
    """`l^k_i = 1{f_i != k}` for every hypothetical label k. Shape (n_classes, n_models).

    This is the binary/classification specialisation of `1 - d(f_i, f_k)`: exact agreement in
    place of a similarity score. The paper's `k` ranges over candidate *outputs*; with a finite
    label set the candidate outputs are the classes.
    """
    return np.stack([(predictions != k).astype(float) for k in range(n_classes)])


class OnlineLLMPicker:
    """Online LLM Picker adapted to a budgeted, delayed, two-model deployment stream."""

    def __init__(
        self,
        n_models: int,
        n_classes: int = 2,
        *,
        rng: np.random.Generator,
        beta: float = 0.9,
        eps: float = 1e-8,
        name: str = "online_llm_picker",
        enforce_cap: bool = True,
    ):
        if n_models < 2:
            raise ValueError("log m normalisation is undefined for m < 2")
        self.name = name
        self.m = int(n_models)
        self.n_classes = int(n_classes)
        self.rng = rng
        self.beta = float(beta)
        self.eps = float(eps)
        self.enforce_cap = bool(enforce_cap)
        self.Lhat = np.zeros(self.m)  # cumulative importance-weighted loss estimate
        self.V = 0.0  # EMA of the acquisition variance signal
        self.n_annotated = 0  # EMA bias correction counts annotations, as published
        self._deployed = 0
        self._last_q = 0.0

    # ---------------------------------------------------------------- published quantities
    def eta(self, t: int) -> float:
        """eta_t = sqrt(log m / (t * (Vhat_t + eps))), with Vhat the bias-corrected EMA."""
        vhat = self.V / (1.0 - self.beta**self.n_annotated) if self.n_annotated > 0 else 0.0
        return float(np.sqrt(np.log(self.m) / max(t * (vhat + self.eps), 1e-12)))

    def posterior(self, t: int) -> np.ndarray:
        """p_{t,i} ∝ exp(-eta_t * Lhat_{t-1,i}); min-subtracted only to avoid underflow."""
        z = -self.eta(t) * (self.Lhat - self.Lhat.min())
        w = np.exp(z)
        s = w.sum()
        return w / s if s > 0 else np.full(self.m, 1.0 / self.m)

    def query_probability(self, predictions: np.ndarray, t: int) -> tuple[float, float]:
        """Eq. 10. Returns (q_t, max_k Var_k)."""
        p = self.posterior(t)
        L = pseudo_loss_matrix(predictions, self.n_classes)  # (n_classes, m)
        # Var_{i ~ p}[l^k_i] = E_p[(l^k)^2] - (E_p[l^k])^2
        mean = L @ p
        var = (L**2) @ p - mean**2
        max_var = float(np.max(var))
        if max_var <= 0.0:  # all models agree: no hypothetical label separates them
            return 0.0, 0.0
        hbar = _entropy(p) / np.log(self.m)
        q = max(max_var * hbar, self.eta(t))
        return float(min(max(q, 0.0), 1.0)), max_var

    # ---------------------------------------------------------------- Policy protocol
    def predict(self, event: Event) -> int:
        # ADAPTER: the published recommendation is argmax posterior; we deploy it directly and
        # keep the incumbent on an exact tie, so a tie does not pay a switch charge. The paper
        # has no deployment notion and no switching cost.
        p = self.posterior(event.t + 1)
        best = int(np.argmax(p))
        if np.isclose(p[best], p[self._deployed]):
            best = self._deployed
        self._deployed = best
        return best

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        # ADAPTER: the published budget is an expected proportion; the hard cap is ours. When the
        # cap is exhausted we draw nothing, which also keeps the random stream interpretable.
        if self.enforce_cap and remaining_budget <= 0:
            self._last_q = 0.0
            return QueryRequest(requested=False)
        q, _ = self.query_probability(event.model_predictions, event.t + 1)
        self._last_q = q
        if q <= 0.0:
            return QueryRequest(requested=False)
        drew = bool(self.rng.random() < q)
        return QueryRequest(requested=drew, probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            q = fb.query_probability  # ADAPTER: issue-time propensity, never recomputed
            if q <= 0:
                raise ValueError("released feedback carries a non-positive issue-time propensity")
            # lhat_{t,i} = l^y_{t,i} / q_t, with l^y the 0/1 loss against the true label
            self.Lhat = self.Lhat + fb.model_losses.astype(float) / q
            # V updates only on annotation, as published
            self.n_annotated += 1
            signal = float(np.var(fb.model_losses.astype(float)))
            self.V = self.beta * self.V + (1.0 - self.beta) * signal

    def decision_state(self) -> str:
        return f"q={self._last_q:.4f};dep={self._deployed}"

    def state_dict(self) -> dict:
        return {
            "Lhat": self.Lhat.tolist(),
            "V": self.V,
            "n_annotated": self.n_annotated,
            "deployed": self._deployed,
        }

    def load_state_dict(self, state: dict) -> None:
        self.Lhat = np.asarray(state["Lhat"], dtype=float)
        self.V = float(state["V"])
        self.n_annotated = int(state["n_annotated"])
        self._deployed = int(state["deployed"])
