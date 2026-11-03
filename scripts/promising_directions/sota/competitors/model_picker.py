"""Model Picker (Karimi et al., AISTATS 2021), ported from the authors' reference code.

Source: ``vendor_sota/model_picker/src/methods/model_picker.py`` (gitignored, not committed).
Line ranges ported: ``model_picker`` lines 13 (eta_0), 38 (eta_t), 41-44 (posterior), 50-58
(u_t and its sanity checks), 61-74 (disagreement gate, floor, Bernoulli draw), 77-80 (importance
weighted update), 82 (posterior sampling), 89-90 (budget bookkeeping); ``_compute_u_t`` lines
103-120. The recommendation rule is not in that file: it is in
``src/evaluation/evaluation_pipeline/evaluate_realizations.py`` lines 64-65, where the winner is
the argmax of the *last logged* posterior row (``posterior_real[-1, :]``), i.e. the posterior
computed at the start of the final round, before that round's update.

Two classes are exposed and they are deliberately not interchangeable:

* ``ModelPickerNative``: the published stream procedure. Immediate feedback, the action each round
  is a sample from the posterior, no switching charge, and the reference code's budget behaviour
  (it never stops querying or updating; it only stops *recording* queries).
* ``ModelPickerDeploymentAdapter``: our task. Delayed labels through ``observe``, importance weight
  from the frozen issue-time propensity, the simulator's hard cap, and deployment by the
  recommendation instead of posterior sampling. Every deviation is marked ``# ADAPTER:``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulator import Event, QueryRequest, ReleasedFeedback  # noqa: E402


# --------------------------------------------------------------------------------------------
# Shared published arithmetic
# --------------------------------------------------------------------------------------------
def eta_zero(num_models: int) -> float:
    """model_picker.py line 13."""
    return float(np.sqrt(np.log(num_models) / 2))


def eta_t(num_models: int, t: int) -> float:
    """model_picker.py line 38. ``t`` starts at 1."""
    return eta_zero(num_models) / float(np.sqrt(t))


def posterior(loss: np.ndarray, eta: float) -> np.ndarray:
    """model_picker.py lines 41-44: exp(-eta (loss - min loss)), normalised."""
    p = np.exp(-eta * (loss - np.min(loss)))
    return p / np.sum(p)


def compute_u_t(post: np.ndarray, preds: np.ndarray, tuning_par: float, num_classes: int) -> float:
    """``_compute_u_t`` (lines 103-120): tuning * max_c (p.loss_c)(1 - p.loss_c)."""
    vals = np.zeros(num_classes)
    for c in range(num_classes):
        loss_c = np.array(preds != c) * 1
        term1 = np.inner(post, loss_c)
        vals[c] = term1 * (1 - term1)
    return float(tuning_par * np.max(vals))


def query_probability(
    post: np.ndarray, preds: np.ndarray, tuning_par: float, num_classes: int, eta: float
) -> float:
    """Lines 50-72 up to (not including) the Bernoulli draw. Returns the final ``u_t``."""
    u_t = compute_u_t(post, preds, tuning_par, num_classes)
    if u_t > 1:
        u_t = 1.0
    if not (0 <= u_t <= 1):  # also catches NaN, as in the reference (line 55-58)
        u_t = 0.0
    if len(np.unique(preds)) == 1:  # agreement region: never query (lines 64-68)
        return 0.0
    if u_t > 0:
        u_t = float(np.maximum(u_t, eta))  # floor (lines 70-71)
    if u_t > 1:
        u_t = 1.0
    return float(u_t)


# --------------------------------------------------------------------------------------------
# Native, as published
# --------------------------------------------------------------------------------------------
class ModelPickerNative:
    """Published stream-based Model Picker. Not a simulator ``Policy`` (it has no delay, no
    switch charge, and acts by sampling), so it is run over a whole stream with ``run``."""

    name = "model_picker_native"

    def __init__(self, num_models: int, num_classes: int, tuning_par: float = 1.0):
        self.num_models = int(num_models)
        self.num_classes = int(num_classes)
        self.tuning_par = float(tuning_par)

    def run(
        self,
        predictions: np.ndarray,
        oracle: np.ndarray,
        budget: int,
        rng: Any,
    ) -> dict:
        """Mirror of ``model_picker`` lines 13-98. ``rng`` needs ``binomial`` and ``choice``
        (a ``numpy`` Generator or ``RandomState``). Returns the reference's five outputs."""
        n = predictions.shape[0]
        loss_t = np.zeros(self.num_models)
        z_t_log = np.zeros(n, dtype=int)
        z_t_budget = np.zeros(n, dtype=int)
        posterior_log = np.zeros((n, self.num_models))
        u_log = np.zeros(n)
        hidden_loss_log = np.zeros(n, dtype=int)
        for t in range(1, n + 1):
            eta = eta_t(self.num_models, t)
            post = posterior(loss_t, eta)
            posterior_log[t - 1] = post
            u_t = query_probability(
                post, predictions[t - 1], self.tuning_par, self.num_classes, eta
            )
            u_log[t - 1] = u_t
            if len(np.unique(predictions[t - 1])) == 1:
                z_t = 0  # no draw in the agreement region (line 64-68)
            else:
                z_t = int(np.asarray(rng.binomial(n=1, p=u_t)).reshape(-1)[0])
            z_t_log[t - 1] = z_t
            if z_t == 1:
                loss_t = loss_t + (np.array((predictions[t - 1] != oracle[t - 1]) * 1) / u_t)
            m_star = int(rng.choice(list(range(self.num_models)), p=post))
            hidden_loss_log[t - 1] = int(predictions[t - 1, m_star] != oracle[t - 1])
            # Reference behaviour: the budget only gates RECORDING, never querying or updating.
            # Note the sum already includes this round, so at most budget-1 queries are recorded.
            if np.sum(z_t_log) < budget:
                z_t_budget[t - 1] = z_t_log[t - 1]
        return {
            "z_t_log": z_t_log,
            "z_t_budget": z_t_budget,
            "hidden_loss_log": hidden_loss_log,
            "posterior_log": posterior_log,
            "u_log": u_log,
            "final_loss": loss_t,
        }

    @staticmethod
    def recommendation(posterior_log: np.ndarray) -> int:
        """evaluate_realizations.py lines 64-65: argmax of the last logged posterior row. The
        reference keeps *all* maximisers on a tie; the lowest index is returned here."""
        return int(np.argmax(posterior_log[-1]))


# --------------------------------------------------------------------------------------------
# Deployment adapter
# --------------------------------------------------------------------------------------------
class ModelPickerDeploymentAdapter:
    """Model Picker as a simulator ``Policy``.

    Deployment rule (documented, ADAPTER): deploy the *recommendation*, the argmax of the current
    posterior, which equals the argmin of the importance-weighted loss because eta_t > 0. Ties are
    broken in favour of the currently deployed model, then the lowest index, so that a tie never
    causes a charged switch. The initial deployment is model 0 until a model has strictly lower
    estimated loss.
    """

    name = "model_picker_adapter"

    def __init__(
        self,
        num_models: int,
        num_classes: int,
        rng: np.random.Generator,
        tuning_par: float = 1.0,
        initial_model: int = 0,
    ):
        self.num_models = int(num_models)
        self.num_classes = int(num_classes)
        self.tuning_par = float(tuning_par)
        self.rng = rng
        self.loss = np.zeros(self.num_models)
        self.deployed = int(initial_model)
        self.n_observed = 0

    def predict(self, event: Event) -> int:
        # ADAPTER: the published action samples m_star ~ posterior every round. Doing that here
        # would incur a switching charge nearly every round, which the method never contemplates,
        # so the deployed model is the recommendation (argmax posterior = argmin estimated loss).
        best = np.flatnonzero(self.loss == np.min(self.loss))
        if self.deployed not in best:
            self.deployed = int(best[0])
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        t = event.t + 1  # t starts at 1 (line 35); counts rounds, not received labels
        # ADAPTER: hard cap. The reference keeps querying and updating after the budget is spent
        # and only stops recording. Here no query is made, and nothing is drawn, at zero budget.
        if remaining_budget <= 0:
            return QueryRequest(requested=False, probability=0.0)
        eta = eta_t(self.num_models, t)
        post = posterior(self.loss, eta)
        preds = np.asarray(event.model_predictions)
        u_t = query_probability(post, preds, self.tuning_par, self.num_classes, eta)
        if len(np.unique(preds)) == 1:
            return QueryRequest(requested=False, probability=0.0)
        z = int(self.rng.binomial(n=1, p=u_t))
        return QueryRequest(requested=bool(z), probability=u_t)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            # ADAPTER: delayed arrival; the importance weight is the frozen issue-time u_t carried
            # on the feedback, not a recomputation from the posterior at release time.
            if fb.query_probability <= 0:
                raise ValueError("feedback with non-positive issue-time propensity")
            self.loss = self.loss + np.asarray(fb.model_losses, dtype=float) / fb.query_probability
            self.n_observed += 1

    def state_dict(self) -> dict:
        return {
            "loss": self.loss.tolist(),
            "deployed": self.deployed,
            "n_observed": self.n_observed,
        }

    def load_state_dict(self, state: dict) -> None:
        self.loss = np.asarray(state["loss"], dtype=float)
        self.deployed = int(state["deployed"])
        self.n_observed = int(state["n_observed"])
