"""Model Selector (Okanovic et al., AISTATS 2025, PMLR v258, arXiv:2410.13609), ported from the
authors' reference code.

Source clone: ``vendor_sota/model_selector/`` (gitignored, not committed), commit
``6aa57e5750153bccb04c9e96946b726d14f5d3f1``.

**The method is registered under the name ``model_picker`` in the author repository** (the paper
calls it Model Selector; ``type: "model_picker"`` is what every ``method_comparison`` config and
the epsilon grid-search configs use). It must not be confused with the *other* repository
``vendor_sota/model_picker`` (Karimi et al. 2021), which is a different algorithm.

Line ranges ported (all under ``vendor_sota/model_selector/src/``):

* ``model_selection/methods/model_picker.py``
  - 12-14, 24: ``epsilon`` default 0.46 and ``gamma = (1-epsilon)/epsilon`` (the noise model);
  - 35-36: uniform prior over models;
  - 44-60: greedy loop, argmin of expected posterior entropy, uniform random tie-break
    (lines 50-52), posterior update (line 58);
  - 68-95: ``compute_entropies``: hypothetical posterior per class ``c``, scipy base-2 entropy,
    averaged with a uniform ``1/num_classes`` class weight (lines 77-94);
  - 97-107: ``update_posterior``.
* ``model_selection/model_selector.py`` 17-55: drops examples on which all models agree (23-29),
  runs the strategy on the rest with ``min(budget, len(filtered))`` labels (31), the **final
  selection rule = model with highest labeled-set accuracy, ties broken uniformly at random**
  (33-43), and back-fills the budget with random agreement-region examples (46-52).
* ``epsilon_optimization/gridsearch_config.py`` 46-52 (grid ``arange(0.35, 0.49+step/2, 0.01)``;
  the extra 0.49 is appended only when the experiment name lacks ``finegrained``),
  ``gridsearch.py`` 18-48 and ``gridsearch_results.py`` 24-48 (``fastest``) and 76-93
  (``success_avg``), ``utils/math_utils.py`` 3-16 (``smooth_data``) and 164-200 (the ``vote``
  noisy oracle), ``benchmark/bechmark_results.py`` 63-83 (success = chosen model is among the
  best-accuracy models).

Paper: Algorithm 1 and Eq. (4)-(7), Section 3.3 (epsilon from noisy labels) and Appendix D.

Two things are exposed and they are deliberately not interchangeable:

* ``ModelSelectorNative``: the published pool-based procedure, immediate oracle, no delay, no
  switching charge, run over a fixed pool that contains every example it may label.
* ``ModelSelectorCausalAdapter``: a simulator ``Policy`` for our streaming task. **It is not the
  published algorithm.** The simulator can only label the *current* event, so the pool cannot be
  queried retrospectively; see the class docstring. ``run_block_pool_experiment`` is the separate
  compatible experiment in which the pool method does run on a pool of already-arrived events.

Degeneracy (material, see ``expected_entropy_is_instance_blind``): with two models the expected
posterior entropy is the same for every disagreement example, for any number of classes, any
posterior and any epsilon. The acquisition then reduces to uniform random sampling of the
disagreement region.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulator import Event, QueryRequest, ReleasedFeedback

# model_picker.py line 12 / gridsearch_config.py lines 48-52.
DEFAULT_EPSILON = 0.46
EPSILON_GRID_MIN, EPSILON_GRID_MAX, EPSILON_GRID_STEP = 0.35, 0.49, 0.01
SMOOTH_KERNEL = 5  # gridsearch_results.py line 27 (smooth_data(..., kernel_size=5))
FASTEST_THRESHOLD = 0.9  # gridsearch_config.py line 56 (epsilon_metric_threshold default)


# --------------------------------------------------------------------------------------------
# Shared published arithmetic
# --------------------------------------------------------------------------------------------
def gamma_from_epsilon(epsilon: float) -> float:
    """model_picker.py line 24. A correct prediction multiplies a model's weight by gamma."""
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must lie in (0, 1)")
    return (1 - epsilon) / epsilon


def update_posterior(
    posterior: np.ndarray, preds_row: np.ndarray, label: int, gamma: float
) -> np.ndarray:
    """model_picker.py lines 97-107 (Eq. 7): multiply by gamma where correct, renormalise."""
    agreements = (np.asarray(preds_row) == label) * 1
    nxt = np.multiply(posterior, np.power(gamma, agreements))
    return np.squeeze(np.asarray(nxt / np.sum(nxt)))


def hypothetical_entropies(
    posterior: np.ndarray, preds: np.ndarray, num_classes: int, gamma: float
) -> np.ndarray:
    """model_picker.py ``compute_entropies`` lines 68-95. ``preds`` is (N, M).

    For each class c the hypothetical posterior assumes label c, then the base-2 entropy is
    averaged with weight 1/num_classes. Same operations, same order, as the reference so that
    exact ties are exact ties.
    """
    preds = np.asarray(preds)
    n, m = preds.shape
    post_rep = np.tile(np.asarray(posterior, dtype=float).reshape(1, m), (n, 1))
    entropies = 0
    for c in np.arange(num_classes):
        agreements_c = (preds == c) * 1
        new_post = np.multiply(post_rep, np.power(gamma, agreements_c))
        norm = np.sum(new_post, axis=1)
        new_post = np.divide(new_post, np.tile(norm.reshape(n, 1), (1, m)))
        cond = stats.entropy(new_post.T, base=2)
        entropies = entropies + cond / num_classes
    return np.asarray(entropies, dtype=float).reshape(n)


def expected_entropy_is_instance_blind(preds: np.ndarray, num_classes: int) -> bool:
    """Static structural check behind the degeneracy finding.

    With exactly two models every disagreement example shows the same two hypothetical
    posteriors up to relabelling (label a rewards model 0, label b rewards model 1, any other
    label rewards neither), so the uniform-class-weight expected entropy is a constant. Returns
    True when the setting is two models, which is what makes the score instance-blind.
    """
    return np.asarray(preds).shape[1] == 2 and num_classes >= 2


def final_model_by_labeled_accuracy(correct_counts: np.ndarray, rng: Any) -> int:
    """Published final rule (paper Algorithm 1 line 12; model_selector.py lines 39-43): the model
    with the highest accuracy on the labeled set, ties uniform at random. NOT argmax posterior."""
    best = np.argwhere(correct_counts == np.max(correct_counts)).flatten()
    return int(rng.choice(best))


# --------------------------------------------------------------------------------------------
# Native, as published (pool-based)
# --------------------------------------------------------------------------------------------
class ModelSelectorNative:
    """Pool-based Model Selector. Mirrors ``ModelSelector.run`` + ``ModelPicker.__call__``.

    ``rng`` needs ``choice`` (a ``RandomState`` reproduces ``np.random`` global-state draws in the
    reference exactly, including draw order: all acquisition tie-breaks first, then one
    final-rule draw per prefix, then the back-fill draw).
    """

    name = "model_selector_native"

    def __init__(self, num_classes: int, epsilon: float = DEFAULT_EPSILON):
        self.num_classes = int(num_classes)
        self.epsilon = float(epsilon)
        self.gamma = gamma_from_epsilon(epsilon)

    def run(self, predictions: np.ndarray, oracle: Any, budget: int, rng: Any) -> dict:
        predictions = np.asarray(predictions)
        n, m = predictions.shape
        budget = min(int(budget), n)
        # model_selector.py lines 23-25: only disagreement examples are eligible.
        disagree = np.where((predictions != predictions[:, [0]]).any(axis=1))[0]
        filt = predictions[disagree]
        n_filt = min(budget, len(filt))

        posterior = np.ones(m) / m  # line 35-36
        unlabelled = list(range(len(filt)))
        chosen: list[int] = []  # positions in the filtered pool
        labels: list[int] = []
        posterior_log: list[np.ndarray] = []
        score_log: list[float] = []
        for _ in range(n_filt):
            ent = hypothetical_entropies(posterior, filt[unlabelled], self.num_classes, self.gamma)
            posterior_log.append(posterior.copy())
            mn = np.min(ent)
            ties = np.where(ent.reshape(len(unlabelled), 1) == mn)[0]  # line 51
            j = int(rng.choice(np.size(ties), 1)[0])  # line 52
            pos = unlabelled[int(ties[j])]
            y = int(np.asarray(oracle[int(disagree[pos])]).reshape(-1)[0])
            posterior = update_posterior(posterior, filt[pos], y, self.gamma)
            chosen.append(pos)
            labels.append(y)
            score_log.append(float(mn))
            del unlabelled[int(ties[j])]

        # model_selector.py lines 33-43: final rule after every prefix.
        counts = np.zeros(m)
        ranking: list[int] = []
        for pos, y in zip(chosen, labels, strict=True):
            counts += (filt[pos] == y) * 1
            ranking.append(final_model_by_labeled_accuracy(counts, rng))

        idx = [int(disagree[p]) for p in chosen]
        # model_selector.py lines 46-52: back-fill with agreement-region labels. They carry no
        # information about which model is best (all models are right or wrong together).
        backfill: list[int] = []
        if len(idx) < budget:
            rest = np.where((predictions == predictions[:, [0]]).all(axis=1))[0]
            backfill = [int(i) for i in rng.choice(rest, size=(budget - len(idx),), replace=False)]
            ranking.extend([ranking[-1]] * (budget - len(idx)) if ranking else [])
        return {
            "model_ranking_t": np.asarray(ranking, dtype=int),
            "labelled_indices": idx + backfill,
            "n_informative": len(idx),
            "labels": labels,
            "posterior_log": np.asarray(posterior_log),
            "score_log": np.asarray(score_log),
            "final_posterior": posterior,
            "final_correct_counts": counts,
            # ADAPTER: the reference raises IndexError (model_ranking_t[-1]) if no example is a
            # disagreement example. Here the final model is then a uniform draw over all models.
            "final_model": ranking[-1] if ranking else int(rng.choice(m)),
        }


# --------------------------------------------------------------------------------------------
# Epsilon selection (paper Section 3.3 / Appendix D; author gridsearch)
# --------------------------------------------------------------------------------------------
def epsilon_grid(include_extra_049: bool = False) -> np.ndarray:
    """gridsearch_config.py lines 50-52. ``include_extra_049`` is True for experiments whose name
    lacks ``finegrained`` (the shipped noisy-label configs all contain it, so it is False)."""
    g = np.arange(EPSILON_GRID_MIN, EPSILON_GRID_MAX + 0.5 * EPSILON_GRID_STEP, EPSILON_GRID_STEP)
    return np.append(g, 0.49) if include_extra_049 else g


def vote_noisy_oracle(predictions: np.ndarray, num_classes: int) -> np.ndarray:
    """math_utils.py lines 164-200, measure ``vote``: the most-predicted class (first on ties)."""
    return np.array([np.argmax(np.bincount(row, minlength=num_classes)) for row in predictions])


def smooth_data(x: np.ndarray, kernel_size: int = SMOOTH_KERNEL) -> np.ndarray:
    """math_utils.py lines 3-16."""
    kernel = np.ones(kernel_size) / kernel_size
    pad = len(kernel) // 2
    xp = np.pad(x, (pad, pad), "constant", constant_values=(x[0], x[-1]))
    return np.convolve(xp, kernel, "valid")


def select_epsilon(
    predictions: np.ndarray,
    num_classes: int,
    realisations: np.ndarray,
    budget: int,
    *,
    grid: np.ndarray | None = None,
    metric: str = "success_avg",
    threshold: float = FASTEST_THRESHOLD,
    seed0: int = 0,
) -> dict:
    """Choose epsilon with no true labels: noisy ``vote`` oracle, run the pool method for every
    grid value on each realisation, score identification of the best model under the noisy
    oracle, pick the best epsilon.

    Reference RNG protocol reproduced: one ``RandomState(seed0 + i)`` per realisation ``i`` shared
    across the grid *in grid order* (benchmark.py ``run_realisation`` seeds once, then runs every
    method), so epsilons are not independent draws, exactly as in the reference.
    """
    grid = epsilon_grid() if grid is None else np.asarray(grid)
    pools = np.asarray(realisations)
    n_real = len(pools)
    succ = np.zeros((len(grid), n_real, int(min(budget, pools.shape[1]))))
    for i, r in enumerate(pools):
        pr = predictions[r]
        noisy = vote_noisy_oracle(pr, num_classes)
        acc = (pr == noisy.reshape(-1, 1)).sum(axis=0) / len(noisy)  # calculate_model_ranking
        best = set(np.flatnonzero(acc == acc.max()).tolist())
        rng = np.random.RandomState(seed0 + i)
        for k, eps in enumerate(grid):
            res = ModelSelectorNative(num_classes, float(eps)).run(pr, noisy, budget, rng)
            rank = res["model_ranking_t"]
            succ[k, i, : len(rank)] = [int(x) in best for x in rank]
    success_mean = succ.mean(axis=1)  # (grid, T)
    # gridsearch_results.py lines 76-93
    avg = success_mean.mean(axis=1)
    out: dict[str, Any] = {"grid": grid, "success_mean": success_mean, "success_avg": avg}
    # gridsearch_results.py lines 24-48
    fastest = []
    for row in success_mean:
        sm = smooth_data(row)
        i = int(np.argmax(sm > threshold))
        fastest.append(np.inf if i == 0 else i)  # reference treats index 0 as "never"
    out["fastest"] = fastest
    # BLOCKED: the rule that turned grid-search output into the per-dataset epsilons of the
    # paper's Table 4 / the method_comparison configs is not in the repository. The shipped
    # gridsearch configs use metric "all", which returns the `fastest` and `success_avg` answers
    # separately, and the code default (success_diff) needs a competitor list the noisy-label
    # configs do not contain (np.max over an empty list). `metric` therefore selects one rule.
    if metric == "success_avg":
        out["epsilon"] = float(grid[int(np.argmax(avg))])
    elif metric == "fastest":
        out["epsilon"] = float(grid[int(np.argmin(fastest))])
    else:
        raise ValueError("metric must be 'success_avg' or 'fastest'")
    return out


# --------------------------------------------------------------------------------------------
# Causal streaming adapter
# --------------------------------------------------------------------------------------------
class ModelSelectorCausalAdapter:
    """Model Selector as a simulator ``Policy``.  NOT the published algorithm.

    **What cannot be represented faithfully.** Algorithm 1 argmins expected posterior entropy over
    an unlabeled *pool* and labels the winner, whichever example it is. In our task only
    already-arrived examples may be labelled, but ``run_episode`` only grants a label for the
    event currently being processed (``QueryRequest`` has no target event id). Retrospective
    querying of an earlier pool member is therefore impossible without a simulator change
    (``QueryRequest.target_event_id`` plus release bookkeeping). Until then the pool is
    approximated by a *record gate* (below) and the faithful pool algorithm is exercised only in
    ``run_block_pool_experiment``.

    Adapter choices (each marked ``# ADAPTER:`` where applied):

    * eligible set = disagreement events among the last ``window`` arrivals not yet requested;
    * gate: request the current event iff its expected posterior entropy is no worse than every
      other eligible event's (ties pass; the reference's random tie-break among ties is not
      available because older events cannot be labelled);
    * pacing: at most ``ceil(budget * (t+1) / horizon)`` requests by event ``t`` so the hard cap
      is not spent in the first few disagreements;
    * pending labels: a requested event leaves the eligible set at issue time, and the posterior
      and labeled-set accuracy change only when its label is released (no hallucinated label);
    * deployment: the published final rule (highest labeled-set accuracy) with ties resolved in
      favour of the incumbent then lowest index (the published rule breaks ties at random, which
      would charge a switch at random);
    * the importance weight is not used (the method has none); ``probability`` is reported as 1.
    """

    name = "model_selector_adapter"

    def __init__(
        self,
        num_models: int,
        num_classes: int,
        rng: np.random.Generator | None = None,
        epsilon: float = DEFAULT_EPSILON,
        window: int = 50,
        initial_model: int = 0,
        pace: bool = True,
    ):
        self.num_models = int(num_models)
        self.num_classes = int(num_classes)
        self.rng = rng  # unused: the gate is deterministic; kept for the common constructor
        self.epsilon = float(epsilon)
        self.gamma = gamma_from_epsilon(epsilon)
        self.window = int(window)
        self.pace = bool(pace)
        self.posterior = np.ones(self.num_models) / self.num_models
        self.correct = np.zeros(self.num_models)
        self.deployed = int(initial_model)
        self.pool: deque = deque(maxlen=self.window)
        self.n_issued = 0
        self.n_observed = 0
        self.budget0: int | None = None

    def predict(self, event: Event) -> int:
        # ADAPTER: published final rule, incumbent-sticky tie-break (see class docstring).
        best = np.flatnonzero(self.correct == np.max(self.correct))
        if self.deployed not in best:
            self.deployed = int(best[0])
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if self.budget0 is None:
            self.budget0 = int(remaining_budget)
        preds = np.asarray(event.model_predictions)
        if len(np.unique(preds)) == 1:
            return QueryRequest(requested=False, probability=0.0)  # agreement region: never
        # ADAPTER: bounded window of already-arrived, unrequested disagreement events.
        self.pool.append((event.event_id, preds))
        if remaining_budget <= 0:
            return QueryRequest(requested=False, probability=0.0)
        if self.pace:
            # ADAPTER: even pacing of the hard cap over the horizon.
            allowed = int(np.ceil(self.budget0 * (event.t + 1) / event.horizon))
            if self.n_issued >= allowed:
                return QueryRequest(requested=False, probability=0.0)
        mat = np.stack([p for _, p in self.pool])
        ent = hypothetical_entropies(self.posterior, mat, self.num_classes, self.gamma)
        # ADAPTER: record gate. The current event is the last row.
        if ent[-1] != np.min(ent):
            return QueryRequest(requested=False, probability=0.0)
        self.pool.pop()  # ADAPTER: leaves the eligible set at issue time (label still pending)
        self.n_issued += 1
        return QueryRequest(requested=True, probability=1.0)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            correct = 1 - np.asarray(fb.model_losses, dtype=float)
            nxt = self.posterior * np.power(self.gamma, correct)  # Eq. 7
            self.posterior = nxt / nxt.sum()
            self.correct = self.correct + correct
            self.n_observed += 1

    def state_dict(self) -> dict:
        return {
            "posterior": self.posterior.tolist(),
            "correct": self.correct.tolist(),
            "deployed": self.deployed,
            "pool": [(int(i), np.asarray(p).tolist()) for i, p in self.pool],
            "n_issued": self.n_issued,
            "n_observed": self.n_observed,
            "budget0": self.budget0,
        }

    def load_state_dict(self, state: dict) -> None:
        self.posterior = np.asarray(state["posterior"], dtype=float)
        self.correct = np.asarray(state["correct"], dtype=float)
        self.deployed = int(state["deployed"])
        self.pool = deque(((i, np.asarray(p)) for i, p in state["pool"]), maxlen=self.window)
        self.n_issued = int(state["n_issued"])
        self.n_observed = int(state["n_observed"])
        self.budget0 = state["budget0"]


# --------------------------------------------------------------------------------------------
# Separate compatible pool experiment
# --------------------------------------------------------------------------------------------
class _BlockOracle:
    """Oracle view that refuses to reveal any label outside the allowed (already arrived) range
    and records every access, so tests can prove the pool method read only its own pool."""

    def __init__(self, labels: np.ndarray, lo: int, hi: int):
        self._labels, self.lo, self.hi = labels, lo, hi
        self.accessed: list[int] = []

    def __getitem__(self, i: int):
        i = int(i)
        if not self.lo <= i < self.hi:
            raise IndexError(f"label {i} outside the arrived pool [{self.lo}, {self.hi})")
        self.accessed.append(i)
        return self._labels[i]


def run_block_pool_experiment(
    model_predictions: np.ndarray,
    labels: np.ndarray,
    *,
    block: int,
    budget_per_block: int,
    delay: int,
    label_price: float,
    switch_cost: float,
    epsilon: float = DEFAULT_EPSILON,
    num_classes: int | None = None,
    budget: int | None = None,
    initial_model: int = 0,
    rng: Any = None,
) -> dict:
    """The published pool algorithm on pools made only of already-arrived events.

    The stream is cut into blocks of ``block`` events. When block ``k`` has fully arrived the pool
    method runs on exactly that block (retrospective labelling allowed *within the block*), with
    a fresh posterior per block. Algorithm 1 is adaptive (each query depends on the previous
    label), so ``b`` sequential queries with feedback delay ``delay`` finish ``b * delay`` events
    after the batch starts; the selected model is deployable from then on (never, if that is past
    the horizon). Deployed model before the first selection is ``initial_model``. Cost accounting
    matches ``run_episode``: loss + label_price * labels + switch_cost * switches.
    """
    if delay < 1:
        raise ValueError("delay must be >= 1")
    t_total = model_predictions.shape[0]
    k = int(num_classes) if num_classes is not None else int(np.max(model_predictions)) + 1
    rng = np.random.RandomState(0) if rng is None else rng
    n_blocks = t_total // block
    cap = n_blocks * budget_per_block if budget is None else int(budget)
    sel = ModelSelectorNative(k, epsilon)
    ready: list[tuple[int, int]] = []  # (time deployable, model)
    labels_used = 0
    accessed_all: list[int] = []
    for b in range(n_blocks):
        lo, hi = b * block, (b + 1) * block
        b_budget = min(budget_per_block, cap - labels_used)
        if b_budget <= 0:
            break
        view = _BlockOracle(labels, lo, hi)
        # Only informative (disagreement) labels are bought: back-fill labels are agreement-region
        # labels that cannot change the answer, so they are neither bought nor charged here.
        res = sel.run(model_predictions[lo:hi], _Offset(view, lo), b_budget, rng)
        n_inf = res["n_informative"]
        labels_used += n_inf
        accessed_all.extend(view.accessed)
        t_ready = hi + n_inf * delay
        if n_inf > 0 and t_ready < t_total:
            ready.append((t_ready, int(res["final_model"])))
    deployed, switches, loss = int(initial_model), 0, 0.0
    ri = 0
    for t in range(t_total):
        while ri < len(ready) and ready[ri][0] <= t:
            new = ready[ri][1]
            ri += 1
            if new != deployed:
                deployed = new
                switches += 1
        loss += float(model_predictions[t, deployed] != labels[t])
    return {
        "net_cost": loss + label_price * labels_used + switch_cost * switches,
        "prediction_loss": loss,
        "labels": labels_used,
        "switches": switches,
        "accessed": accessed_all,
        "n_blocks": n_blocks,
    }


class _Offset:
    """Translate block-local indices to stream indices for the guarded oracle."""

    def __init__(self, view: _BlockOracle, lo: int):
        self.view, self.lo = view, lo

    def __getitem__(self, i: int):
        return self.view[int(i) + self.lo]
