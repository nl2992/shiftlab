"""CAMS (Contextual Active Model Selection, Liu et al., NeurIPS 2024) ported for the SOTA comparison.

Source of truth is the author code in ``vendor_sota/cams/`` (clone of
``xuefeng-cs/Contextual-Active-Model-Selection``, commit 6cbcc62fa289983d10c77637e4bd49f13c2248ed),
not the paper's prose. Each ported block quotes its source file and line range.

Two classes, reported separately:

``CAMSNative``
    The published algorithm under its own assumptions: the label of event t is available before
    event t+1 (run it in the simulator with ``delay=1``; the simulator now rejects ``delay=0``, which never released
    a label, see the report), and no deployment-switch charge (run with ``switch_cost=0``). Its
    prediction action is the author's: sample ``I_t ~ w_t`` every round. This is the fidelity
    reference.

``CAMSDeploymentAdapter``
    The same update and query rule inside our task: delayed labels via ``observe``, a hard
    budget, and a charge per deployment switch. CAMS has a *prediction action* (its combined
    recommendation ``w_t``, a distribution over models) and *never defines a switching cost*.
    Here ``predict`` returns the deployed model index. By default the recommendation is mapped to
    a deployment by ``argmax_m w_t[m]``, keeping the currently deployed model on exact ties. This
    is an adapter choice made so that sampling noise does not buy a switch charge every round; it
    is not part of CAMS. ``deploy="sample"`` instead keeps the author's sampled prediction (and
    pays for every change it makes). Charging for switches is likewise our choice.

Variants present in the author code and ported separately:
  * ``CAMS``     = ``CAMS_identity`` (src/methods/CAMS_identity.py), weights ``w_t = Q^T E_t``.
  * ``CAMS-MAX`` = ``CAMS_test``     (src/methods/CAMS_test.py), weights ``w_t = E_t[argmax Q]``.
    The author comment at CAMS_test.py:8 labels it "CAMS-MAX".

Not ported (reasons recorded, nothing substituted under the CAMS name):
  * BLOCKED: the author's *policy training* is not in the repository. The contextual policies are
    shipped as precomputed ``advice_matrix_*.npz`` files (and ``policy_list.txt`` names MLP
    checkpoints that are not shipped). This module therefore takes the advice matrix as an input.
    ``KNNCorrectnessPolicy`` below is OUR development-trained contextual policy, not the author's;
    results using it are "CAMS with our policies", and that must be stated wherever they appear.
  * BLOCKED: ``advice_matrix_random_policy.npz`` rows (soft random policies appended in
    experiments/base/set_data.py) come from a generator that is not in the repository.
  * task7 branch (context-free, ``eta_0/sqrt(t)``, max-variance query) and the task9 scaling
    parameter (CAMS_identity.py:98-123, dataset-specific constants 9/8/1.2/1.5) are experiment
    variants, not the main algorithm, and are not ported. ``utils.max_w_c_t`` only fills a log
    list (``w_c_set``) that is never returned or used in a decision, so it is not ported.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np
from simulator import Event, QueryRequest, ReleasedFeedback

AdviceFn = Callable[[Event], np.ndarray]


# --------------------------------------------------------------------------------------------
# Ported numerical core. Each function below is a line-for-line port of the cited author code.
# --------------------------------------------------------------------------------------------


def normalise_advice(advice_matrix_t: np.ndarray) -> np.ndarray:
    """Row-normalise one event's raw advice (n_policies, n_models) and apply the NaN guard.

    Source: vendor_sota/cams/utils.py:6-9 (``real_policy``) for the row normalisation;
    src/methods/CAMS_identity.py:47-50 (and CAMS_test.py:10-12 of the loop) for the NaN guard,
    which replaces *every* NaN entry (rows with zero sum) by ``1/num_models``.
    """
    n_models = advice_matrix_t.shape[1]
    e = advice_matrix_t / advice_matrix_t.sum(axis=1, keepdims=True)  # utils.py:8-9
    if np.isnan(np.sum(e)):  # CAMS_identity.py:48-50
        e[np.isnan(e)] = 1 / n_models
    return e


def smooth_advice(e: np.ndarray) -> np.ndarray:
    """The per-row smoothing of the advice matrix, applied for every non-task7 run.

    Source: vendor_sota/cams/src/methods/CAMS_identity.py:61-65 (identical in CAMS_test.py:23-26).
    ``e_0`` is the sum (not the mean) of squared deviations of the row from its mean.
    """
    e = e.copy()
    for item in range(len(e)):  # CAMS_identity.py:62
        e_0 = np.sum(np.square(e[item] - np.mean(e[item])))  # :63
        e[item] = (e[item] + e_0) / np.sum(e[item] + e_0)  # :64
    return e


def policy_posterior(loss_tilde: np.ndarray, eta: float) -> np.ndarray:
    """Exponential-weights posterior over policies.

    Source: vendor_sota/cams/src/methods/CAMS_identity.py:57-58:
    ``q = exp(-eta * Loss_t_tilde); Q = q / sum(q)``.
    NUMERICS: the author code has no guard against underflow (``eta = sqrt(P/t)`` is large). If the
    plain formula underflows to all zeros or non-finite values we fall back to the identical
    quantity computed with the minimum subtracted (same ratio, no information changed).
    """
    q = np.exp(-eta * loss_tilde)  # :57
    s = np.sum(q)
    if not np.isfinite(s) or s <= 0:
        z = eta * loss_tilde
        q = np.exp(-(z - np.min(z)))
        s = np.sum(q)
    return q / s  # :58


def learning_rate(n_policies: int, t: int) -> float:
    """``eta_t = sqrt(num_policies / t)``. Source: CAMS_identity.py:46 (non-task7 branch).

    Note this is the author's schedule and it is NOT the paper-style ``sqrt(ln P / t)``.
    """
    return math.sqrt(n_policies / t)


def weighted_entropy_query(n_classes: int, w: np.ndarray, predictions: np.ndarray) -> float:
    """CAMS's query score ``v_t`` (the "weighted entropy" rule).

    Source: vendor_sota/cams/utils.py:35-58 (``_compute_weighted_entropy_t``). Returns 0 inside the
    region of agreement (:41-43) and also returns 0 as soon as ANY class has zero posterior mass
    on the models that disagree with it (:52-53). The mean over classes divides by ``n_classes``
    (:57), so for two classes ``v_t <= 1/2``.
    """
    u_t_list = np.zeros(n_classes)
    dist_t = len(np.unique(predictions))
    if dist_t == 1:  # :41-43
        return 0.0
    for c in range(n_classes):
        loss_c = np.array(predictions != c) * 1  # :48
        term1 = np.round(np.inner(w, loss_c), decimals=6)  # :51
        if term1 == 0:  # :52-53
            return 0.0
        u_t_list[c] = -1 * term1 * math.log(term1, n_classes)  # :54
    return float(np.sum(u_t_list) / n_classes)  # :56


def query_probability(n_classes: int, w: np.ndarray, predictions: np.ndarray, t: int) -> float:
    """Query probability ``u_t`` (0 means: do not query and do not draw a random number).

    Source: vendor_sota/cams/src/methods/CAMS_identity.py:87-143 (identical in CAMS_test.py):
    clip ``v_t`` to [0,1] with NaN/negative -> 0 (:88-93); region of agreement or ``v_t == 0``
    -> ``u_t = 0`` and no draw (:126-130); else ``u_t = max(v_t, 1/sqrt(t))`` capped at 1
    (:132-139, non-task7 branch :136).
    """
    v_t = weighted_entropy_query(n_classes, w, predictions)
    if v_t > 1:  # :88-93
        v_t = 1.0
    elif np.logical_and(v_t >= 0, v_t <= 1):
        # Faithful port of the author's no-op clamp branch (see :88-93); kept so the control
        # flow matches the reference line for line rather than being "tidied" into divergence.
        v_t = v_t  # noqa: PLW0127
    else:
        v_t = 0.0
    dist_t = len(np.unique(predictions))  # :96
    if dist_t == 1 or v_t == 0:  # :126
        return 0.0
    u_t = float(np.maximum(v_t, 1 / np.sqrt(t)))  # :136
    if u_t > 1:  # :138-139
        u_t = 1.0
    return u_t


def loss_increment(e: np.ndarray, model_losses: np.ndarray, u_t: float) -> np.ndarray:
    """Importance-weighted loss propagated to every policy.

    Source: vendor_sota/cams/src/methods/CAMS_identity.py:145-153: ``loss_hat = loss / u_t``;
    ``Loss_t_tilde += E @ loss_hat`` where ``E`` is the smoothed advice matrix of the labelled
    event and ``u_t`` is its query probability.
    """
    loss_hat = np.asarray(model_losses, dtype=float) / u_t  # :150
    return np.matmul(e, loss_hat)  # :152


class _CAMSCore:
    """Shared state and decision rule for CAMS / CAMS-MAX. Not a Policy by itself."""

    def __init__(
        self,
        *,
        n_models: int,
        n_classes: int,
        advice_fn: AdviceFn,
        variant: str,
        rng: Any,
    ) -> None:
        if variant not in ("CAMS", "CAMS-MAX"):
            raise ValueError("variant must be 'CAMS' or 'CAMS-MAX'")
        self.n_models = int(n_models)
        self.n_classes = int(n_classes)
        self.advice_fn = advice_fn
        self.variant = variant
        self.rng = rng
        self.loss_tilde: np.ndarray | None = None  # Loss_t_tilde, CAMS_identity.py:29
        self.n_updates = 0
        self.trace: list[dict] = []
        self._cache: dict | None = None

    # ---- per-event computation -------------------------------------------------------------
    def _prepare(self, event: Event) -> dict:
        if self._cache is not None and self._cache["event_id"] == event.event_id:
            return self._cache
        raw = np.asarray(self.advice_fn(event), dtype=float)
        if raw.ndim != 2 or raw.shape[1] != self.n_models:
            raise ValueError("advice_fn must return (n_policies, n_models)")
        if self.loss_tilde is None:
            self.loss_tilde = np.zeros(raw.shape[0])
        if raw.shape[0] != self.loss_tilde.shape[0]:
            raise ValueError("number of policies changed between events")
        t = event.t + 1  # the author's t runs 1..T
        eta = learning_rate(raw.shape[0], t)
        e = normalise_advice(raw)
        q = policy_posterior(self.loss_tilde, eta)
        e = smooth_advice(e)
        if self.variant == "CAMS":
            w = np.matmul(q, e)  # CAMS_identity.py:67
        else:
            w = e[int(np.argmax(q))]  # CAMS_test.py: w = E[argmax Q]
        w = w / np.sum(w)  # :68
        self._cache = {"event_id": event.event_id, "t": t, "e": e, "q": q, "w": w}
        return self._cache

    def recommendation(self, event: Event) -> np.ndarray:
        return self._prepare(event)["w"]

    def sample_model(self, event: Event) -> int:
        """Author's prediction action: ``I_t ~ w_t`` (CAMS_identity.py:71)."""
        w = self._prepare(event)["w"]
        return int(self.rng.choice(list(range(self.n_models)), p=w))

    def decide(self, event: Event, *, draw: bool) -> tuple[float, bool, dict]:
        """Return (u_t, U_t, frozen extras). ``draw=False`` skips the Bernoulli draw."""
        c = self._prepare(event)
        u_t = query_probability(self.n_classes, c["w"], np.asarray(event.model_predictions), c["t"])
        if u_t == 0.0:
            return 0.0, False, {}
        if not draw:
            return u_t, False, {}
        u = int(self.rng.binomial(size=1, n=1, p=u_t)[0])  # CAMS_identity.py:142
        return u_t, bool(u), {"E": c["e"].copy()}

    def apply_label(self, e: np.ndarray, model_losses: np.ndarray, u_t: float) -> None:
        if self.loss_tilde is None:
            self.loss_tilde = np.zeros(e.shape[0])
        self.loss_tilde = self.loss_tilde + loss_increment(e, model_losses, u_t)
        self.n_updates += 1

    # ---- persistence -----------------------------------------------------------------------
    def core_state(self) -> dict:
        rng = self.rng
        if hasattr(rng, "bit_generator"):
            rng_state: Any = rng.bit_generator.state
        else:
            rng_state = rng.get_state()
        return {
            "loss_tilde": None if self.loss_tilde is None else self.loss_tilde.tolist(),
            "n_updates": self.n_updates,
            "rng": rng_state,
        }

    def load_core_state(self, state: dict) -> None:
        lt = state["loss_tilde"]
        self.loss_tilde = None if lt is None else np.asarray(lt, dtype=float)
        self.n_updates = int(state["n_updates"])
        if hasattr(self.rng, "bit_generator"):
            self.rng.bit_generator.state = state["rng"]
        else:
            self.rng.set_state(state["rng"])
        self._cache = None


# --------------------------------------------------------------------------------------------
# Advice: constant policies plus development-trained contextual policies.
# --------------------------------------------------------------------------------------------


def constant_policy_advice(n_models: int) -> np.ndarray:
    """One constant model-selection policy per model: policy m always recommends model m.

    This matches the one-hot "classifier" rows (rows 6-11 for VERTEBRAL) of the author's
    ``advice_matrix_identity.npz``, which is what the author's code names ``identity``.
    """
    return np.eye(n_models)


class KNNCorrectnessPolicy:
    """OUR development-trained contextual policy (not the author's; their training is BLOCKED).

    The author's stored contextual advice rows are multi-hot vectors marking which models a
    learned policy believes will be correct on the event (verified on VERTEBRAL: row entries are
    0/1 and agree with realised model correctness in 53-71% of events, so they are predictions,
    not labels). This class produces the same kind of object from development data: the models
    that were correct on at least half of the ``k`` nearest development points.
    """

    def __init__(self, dev_x: np.ndarray, dev_correct: np.ndarray, k: int = 15) -> None:
        self.x = np.asarray(dev_x, dtype=float)
        self.correct = np.asarray(dev_correct, dtype=float)  # (n_dev, n_models) in {0,1}
        self.k = int(min(k, len(self.x)))

    def __call__(self, context: Any) -> np.ndarray:
        d = np.sum((self.x - np.asarray(context, dtype=float)) ** 2, axis=1)
        nn = np.argsort(d, kind="stable")[: self.k]
        return (self.correct[nn].mean(axis=0) >= 0.5).astype(float)


def stack_advice(
    n_models: int,
    contextual_policies: list[Callable[[Any], np.ndarray]],
    *,
    include_constant: bool = True,
) -> AdviceFn:
    """Build the per-event advice matrix: contextual policies first, constant policies after."""

    def advice(event: Event) -> np.ndarray:
        rows = [np.asarray(p(event.context), dtype=float) for p in contextual_policies]
        if include_constant:
            rows.extend(constant_policy_advice(n_models))
        return np.vstack(rows)

    return advice


# --------------------------------------------------------------------------------------------
# Policy classes
# --------------------------------------------------------------------------------------------


class CAMSNative:
    """Published CAMS under its own assumptions. Fidelity reference, not a competitor entry.

    Use with the simulator at ``delay=1`` (label of event t is usable at t+1; ``delay=0`` is rejected, not
    supported by the simulator) and ``switch_cost=0``. ``predict`` samples ``I_t ~ w_t`` exactly as
    the author does. The author keeps drawing query decisions after the budget is spent but
    ignores them (CAMS_identity.py:145,156); here the draw is kept (so the random stream matches)
    and the request is simply not issued when ``remaining_budget == 0``.
    """

    def __init__(
        self,
        *,
        n_models: int,
        n_classes: int,
        advice_fn: AdviceFn,
        rng: Any,
        variant: str = "CAMS",
        name: str | None = None,
    ) -> None:
        self.core = _CAMSCore(
            n_models=n_models, n_classes=n_classes, advice_fn=advice_fn, variant=variant, rng=rng
        )
        self.name = name or ("cams_native" if variant == "CAMS" else "cams_max_native")

    def predict(self, event: Event) -> int:
        return self.core.sample_model(event)

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        u_t, drawn, extra = self.core.decide(event, draw=True)
        self.core.trace.append(
            {"t": event.t, "w": self.core.recommendation(event).copy(), "u": u_t, "U": drawn}
        )
        if not drawn or remaining_budget <= 0:
            return QueryRequest(requested=False, probability=0.0)
        return QueryRequest(requested=True, probability=u_t, extra=extra)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for f in feedback:
            self.core.apply_label(f.extra["E"], f.model_losses, f.query_probability)

    def state_dict(self) -> dict:
        return self.core.core_state()

    def load_state_dict(self, state: dict) -> None:
        self.core.load_core_state(state)


class CAMSDeploymentAdapter:
    """CAMS inside our task: delayed labels, hard budget, switch charge.

    Deviations from ``CAMSNative`` (all are adapter choices, none is in the paper):

    * ADAPTER: ``predict`` returns ``argmax_m w_t[m]`` (current model kept on exact ties) instead
      of sampling ``I_t ~ w_t``. Sampling would switch the deployment at random every round and
      pay the switch charge each time; the recommendation is the nearest thing CAMS has to a
      deployment decision. ``deploy="sample"`` restores the author's sampled prediction.
    * ADAPTER: labels reach the learner through ``observe`` after ``delay`` events. The update uses
      the query probability and the smoothed advice matrix ``E`` frozen at issue time (carried in
      ``QueryRequest.extra``); the author never needs this because feedback is immediate.
    * ADAPTER: the hard budget is enforced on the request: when ``remaining_budget == 0`` no
      query decision is drawn. The author keeps drawing and ignores the result, so the random
      stream (not the information state) differs after the cap.
    * ADAPTER: deployment-switch charge is applied by the simulator; CAMS defines none, and the
      adapter does nothing to avoid switches beyond the tie rule above.
    """

    def __init__(
        self,
        *,
        n_models: int,
        n_classes: int,
        advice_fn: AdviceFn,
        rng: Any,
        variant: str = "CAMS",
        deploy: str = "argmax",
        initial_model: int = 0,
        name: str | None = None,
    ) -> None:
        if deploy not in ("argmax", "sample"):
            raise ValueError("deploy must be 'argmax' or 'sample'")
        self.core = _CAMSCore(
            n_models=n_models, n_classes=n_classes, advice_fn=advice_fn, variant=variant, rng=rng
        )
        self.deploy = deploy
        self.deployed = int(initial_model)
        base = "cams_adapter" if variant == "CAMS" else "cams_max_adapter"
        self.name = name or base

    def predict(self, event: Event) -> int:
        if self.deploy == "sample":
            self.deployed = self.core.sample_model(event)
            return self.deployed
        w = self.core.recommendation(event)
        best = float(np.max(w))
        if w[self.deployed] < best:  # keep the current model on exact ties
            self.deployed = int(np.argmax(w))
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if remaining_budget <= 0:  # ADAPTER: hard cap, no draw
            return QueryRequest(requested=False, probability=0.0)
        u_t, drawn, extra = self.core.decide(event, draw=True)
        self.core.trace.append(
            {"t": event.t, "w": self.core.recommendation(event).copy(), "u": u_t, "U": drawn}
        )
        if not drawn:
            return QueryRequest(requested=False, probability=0.0)
        return QueryRequest(requested=True, probability=u_t, extra=extra)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for f in feedback:
            # ADAPTER: frozen issue-time E and u_t, applied at release time
            self.core.apply_label(f.extra["E"], f.model_losses, f.query_probability)

    def decision_state(self) -> str:
        return f"updates={self.core.n_updates}"

    def state_dict(self) -> dict:
        s = self.core.core_state()
        s["deployed"] = self.deployed
        return s

    def load_state_dict(self, state: dict) -> None:
        self.core.load_core_state(state)
        self.deployed = int(state["deployed"])
