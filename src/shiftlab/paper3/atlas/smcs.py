# PORTED from 8af33afe934c3c5dba03caa55257125941f6df4f:scripts/promising_directions/sota/competitors/smcs.py (origin/main). Imports adjusted to the atlas package;
# semantics unchanged except where marked 'ATLAS PORT CHANGE'.
"""SMCS (Sequential Model Confidence Sets, Arnold, Gavrilopoulos, Schulz, Ziegel) ported as an
INFERENCE component for the SOTA comparison.

Source of truth is the author R code in ``vendor_sota/smcs/`` (clone of the SMCS replication
repository, commit ab0944e7fe0f7c1b25584548deb4e80a75ace251), not the paper's prose. Each ported
block quotes its file and line range. Numerical agreement with the R code, executed under
``Rscript`` on the same input, is established in ``tests/promising_directions/test_sota_smcs.py``.

What SMCS is, and is not
------------------------
SMCS keeps a *time-uniform confidence set of models*: the models not yet rejected as inferior,
using anytime-valid (e-process) evidence about relative predictive performance. It is not a
model-switching policy. Two classes, reported separately:

``SMCSInference``
    The published evidence construction and multiplicity treatment (native, full feedback).
``SMCSDeploymentPolicy``
    OUR deployment rule bolted on top (retain the incumbent until it leaves the set), with the
    same acquisition as the B3+ pacer. Nothing in SMCS prescribes any of this. Results from it
    are "SMCS inference + development-chosen retain-incumbent rule", never "SMCS".

Null formulation chosen (and why)
---------------------------------
Of the formulations in the author repository, ``Simulation_1/SMCS/Simulation1.R`` (and the Covid
case study, which uses the same product) tests the *pairwise conditional* nulls

    H_ij :  E[ L_i,t - L_j,t | F_{t-1} ] <= 0   for all t,

with the test supermartingale ``E_ij,t = prod_s (1 + lambda_ij (L_i,s - L_j,s))``, lambda =
1/(2c), c a bound on |L_i - L_j|. Model i's hypothesis "i is superior to every other model" is the
intersection over j; its e-value is the arithmetic mean over j, and the closure principle
(Vovk-Wang) corrects multiplicity across models. We pick this because (i) we compare two frozen
models on paired 0/1 losses and decide on the sign of the paired difference, which is exactly
this conditional-mean null (the same type as the E[D] <= 0 member of the B3+ margin grid), (ii) it
is an exact product e-process with the bound c = 1 for 0/1 losses, and (iii) it needs no
numerical optimisation.

  * BLOCKED: the other formulation, ``Simulation_3/Sim3.R:73-80`` (null on the time-*averaged*
    expected difference, with a nuisance optimisation by ``fmincon``), requires the R packages
    ``pracma`` and ``NlcOptim``, which are not installed and cannot be installed offline. It is
    not ported and nothing in this module stands in for it. It is the formulation designed for
    non-stationary streams, so its absence matters for the caveat below.

THE caveat: cumulative superiority is not current-regime superiority
---------------------------------------------------------------------
``E_ij`` is a running product that is never discounted or reset, and the set update at
``Simulation1.R:119-120`` intersects with the previous set, so **an excluded model never
returns**. A model that was clearly worse early is excluded for good even if it is better now;
a model that was better early keeps its wealth cushion and stays in the set long after it has
become worse. Our deployment problem asks which model is best *now*. SMCS answers "which models
have not been convincingly shown to be inferior over the whole history". After a regime change it
can therefore (a) fail to admit the newly better model and (b) retain the old one, or even empty
the set when each model has been the worse one at some time. This is a mismatch of estimand, not
a tuning issue, and it is exercised in the tests.

Selective feedback: weighting, and what survives
------------------------------------------------
Native SMCS needs every loss each round. Under selective labels with frozen query probability
``q_s`` (acquisition fixed to the B3+ pacer) the natural unbiased substitute is the
importance-weighted difference ``d~ = Z d / q``, which obeys |d~| <= 1/q, NOT |d| <= 1. Keeping
the native fixed ``lambda = 1/2`` would give factors ``1 + d/(2q)`` that go negative (a
non-nonnegative "e-process") for q < 1/2. The bound the construction relies on is therefore
restored by making the bound predictable and per-round, ``c_s = 1/q_s``, ``lambda_s = 1/(2 c_s)``,
which is exactly the device the authors use in ``Covid/covid_function_eadj.R:42-46`` (a
``c`` computed from information available before the outcome, ``lambda = 1/(K c)``). Then every
factor lies in [1/2, 3/2], and ``E[factor | F] = 1 + q d / 2 <= 1`` under H_ij. The factor reduces
algebraically to ``1 + d/2`` on queried events and 1 on unqueried ones, so the weighting is
bound-preserving at the price of evidence accruing q times more slowly than under full feedback.
Where the models agree, d = 0 is known without a label and the factor is 1.

  * ADAPTER: this selective-feedback construction is ours, not SMCS's. Validity argument: q_s is
    a function of events and past query decisions only (not of labels), so it is predictable, and
    labels enter the product in event order; delayed release only shifts the time at which a
    prefix of that product becomes visible. No result in the SMCS paper covers sampled or
    delayed labels, so this is a development argument, not a published guarantee.
"""

from __future__ import annotations

import numpy as np

from .sim import Event, QueryRequest, ReleasedFeedback

# --------------------------------------------------------------------------------------------
# Ported numerical core
# --------------------------------------------------------------------------------------------


def closure_adjust(e: np.ndarray) -> np.ndarray:
    """Closure-principle e-value adjustment (Vovk and Wang 2021, Sec. 5).

    Source: vendor_sota/smcs/Simulation_1/SMCS/Adjusting.R:5-15 (``adj``; the same function is
    repeated in Simulation_2, MSE_Simulation and Covid). With ``e`` sorted ascending,
    ``e_adj[order[i]] = min_{j < i} (e_(i) + S_j) / (1 + j)`` where ``S_j`` is the sum of the j
    smallest. R's ``[1:(i-1)]`` with i = 1 is ``[1:0] = c(1, 0)`` which selects element 1, giving
    ``(e_(1) + e_(1)) / 2 = e_(1)``; this is reproduced.
    """
    e = np.asarray(e, dtype=float)
    k = len(e)
    order = np.argsort(e, kind="stable")  # R order(): ascending, ties by index
    e_sorted = e[order]
    s = np.cumsum(e_sorted)
    e_adj = np.empty(k)
    for i in range(1, k + 1):
        cand = (e_sorted[i - 1] + s) / (1 + np.arange(1, k + 1))
        idx = slice(0, i - 1) if i > 1 else slice(0, 1)  # R [1:(i-1)], quirk at i = 1
        e_adj[order[i - 1]] = cand[idx].min()
    return e_adj


def arithmetic_mean_evalue(e_pair: np.ndarray) -> np.ndarray:
    """Per-model e-value: arithmetic mean of the pairwise e-processes over the other models.

    Source: vendor_sota/smcs/Simulation_1/SMCS/Simulation1.R:102-104 (``EE[i,] = colMeans(E[i,-i,])``).
    ``e_pair[i, j]`` is E_ij; the diagonal is ignored. (Covid/covid_function_eadj.R:58 writes the
    same quantity as ``m/(m-1) * rowMeans(E)`` with a zero diagonal.)
    """
    m = e_pair.shape[0]
    mask = ~np.eye(m, dtype=bool)
    return np.array([e_pair[i][mask[i]].mean() for i in range(m)])


def confidence_set_step(prev: np.ndarray, e_adj: np.ndarray, alpha: float) -> np.ndarray:
    """One set update: keep models with ``E_adj < 1/alpha``, intersected with the previous set.

    Source: vendor_sota/smcs/Simulation_1/SMCS/Simulation1.R:119-120. The strict inequality and
    the intersection (an excluded model never returns) are both from the source.
    """
    return prev & (e_adj < 1.0 / alpha)


class SMCSInference:
    """Pairwise product e-processes -> arithmetic mean -> closure adjustment -> nested set.

    ``update_pairs`` takes pairwise loss differences ``d[i, j] = L_i - L_j`` and the per-pair
    ``lam`` (Simulation1.R:80, 92: ``E[i,j,] = cumprod(1 + lambda[i,j] * d[i,j,])``).
    ``update_losses`` is the native entry point for full feedback with a loss bound ``c``
    (``lambda = 1/(2c)``, Simulation1.R:72).

    ADAPTER: the first update never excludes anybody, mirroring ``MCS_e[[1]] = 1:m`` and the
    loop starting at t = 2 (Simulation1.R:112, 118): the set at the first time point is the full
    set, whatever the first loss was.
    """

    def __init__(self, n_models: int, alpha: float, first_step_exempt: bool = True):
        if n_models < 2:
            raise ValueError("SMCS needs at least two models")
        if not 0 < alpha < 1:
            raise ValueError("alpha must lie in (0, 1)")
        self.m = int(n_models)
        self.alpha = float(alpha)
        self.first_step_exempt = first_step_exempt
        self.E = np.ones((self.m, self.m))  # Simulation1.R:90-95: cumprod starts from 1
        self.members = np.ones(self.m, dtype=bool)
        self.e_adj = np.ones(self.m)
        self.n_updates = 0
        self.min_factor = np.inf  # smallest 1 + lam*d seen: nonnegativity audit of the bound

    def update_pairs(self, d: np.ndarray, lam: np.ndarray) -> np.ndarray:
        factor = 1.0 + lam * d
        off = ~np.eye(self.m, dtype=bool)
        self.min_factor = min(self.min_factor, float(factor[off].min()))
        self.E = np.where(off, self.E * factor, self.E)
        self.e_adj = closure_adjust(arithmetic_mean_evalue(self.E))
        self.n_updates += 1
        if not (self.first_step_exempt and self.n_updates == 1):
            self.members = confidence_set_step(self.members, self.e_adj, self.alpha)
        return self.members.copy()

    def update_losses(self, losses: np.ndarray, c: float = 1.0) -> np.ndarray:
        """Native full-feedback step. ``c`` bounds |L_i - L_j| (1 for 0/1 losses)."""
        losses = np.asarray(losses, dtype=float)
        d = losses[:, None] - losses[None, :]
        return self.update_pairs(d, np.full((self.m, self.m), 1.0 / (2.0 * c)))

    def state_dict(self) -> dict:
        return {
            "E": self.E.tolist(),
            "members": self.members.tolist(),
            "e_adj": self.e_adj.tolist(),
            "n_updates": self.n_updates,
            "min_factor": self.min_factor,
        }

    def load_state_dict(self, s: dict) -> None:
        self.E = np.array(s["E"], dtype=float)
        self.members = np.array(s["members"], dtype=bool)
        self.e_adj = np.array(s["e_adj"], dtype=float)
        self.n_updates = int(s["n_updates"])
        self.min_factor = float(s["min_factor"])


def run_native(losses: np.ndarray, alpha: float, c: float = 1.0):
    """Run SMCS over a full-feedback loss matrix ``(T, m)``.

    Returns ``(E_adj, members)`` with shapes ``(T, m)``, where row t is the state after seeing
    losses 0..t. Row 0 of ``members`` is the full set (Simulation1.R:112).
    """
    t_len, m = losses.shape
    s = SMCSInference(m, alpha)
    e_adj = np.zeros((t_len, m))
    mem = np.zeros((t_len, m), dtype=bool)
    for t in range(t_len):
        mem[t] = s.update_losses(losses[t], c)
        e_adj[t] = s.e_adj
    return e_adj, mem


# --------------------------------------------------------------------------------------------
# Selective feedback: weighting that keeps the loss bound
# --------------------------------------------------------------------------------------------


def weighted_pair_inputs(model_losses: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    """Importance-weighted differences and the predictable per-round lambda for one queried event.

    ADAPTER (ours; see module docstring): ``d~[i,j] = (L_i - L_j) / q`` has |d~| <= c_s = 1/q, and
    ``lambda_s = 1/(2 c_s) = q/2`` so that ``1 + lambda_s d~ in [1/2, 3/2]``. Predictable-c
    precedent: Covid/covid_function_eadj.R:42-46.
    """
    if not 0 < q <= 1:
        raise ValueError(f"query probability must lie in (0, 1], got {q}")
    losses = np.asarray(model_losses, dtype=float)
    d_tilde = (losses[:, None] - losses[None, :]) / q
    c_s = 1.0 / q
    lam = np.full(d_tilde.shape, 1.0 / (2.0 * c_s))
    return d_tilde, lam


# --------------------------------------------------------------------------------------------
# Acquisition: the B3+ pacer, so that only the inference differs
# --------------------------------------------------------------------------------------------


class PacedDisagreementAcquisition:
    """The B3+ query pacer with the decision-value factor switched off (variant P7a).

    Source: scripts/promising_directions/b3_plus_policy.py ``CertPlus.step``: ``rate`` (line
    ~175), ``pace``, ``q = clip(pace, pmin, 1)``, ``q = 0`` when the budget is spent, ask only on
    disagreement. Verified numerically against ``CertPlus`` (variant P7a, trace) in the tests.

    ADAPTER: B3+'s decision-value factor ``r`` is computed from B3+'s own LCB/UCB margin-grid
    evidence. Using it here would feed our inference into the comparator's acquisition, so this
    class uses the evidence-free pacer (P7a, ``r = 1``). That is the same acquisition our P7a
    uses; it is not the full P7 acquisition, and the comparison must say so.
    """

    def __init__(self, pmin: float = 0.05, prior_rate: float = 0.25, prior_w: float = 20.0):
        self.pmin, self.prior_rate, self.prior_w = pmin, prior_rate, prior_w
        self.ndis = 0  # disagreements strictly before the current event

    def probability(self, t: int, horizon: int, remaining: int) -> float:
        rate = (self.ndis + self.prior_rate * self.prior_w) / (t + self.prior_w)
        h_eff = horizon - t
        pace = remaining / max(rate * h_eff, 1e-9)
        q = float(np.clip(pace, self.pmin, 1.0))
        return q if remaining > 0 else 0.0

    def close_event(self, disagree: bool) -> None:
        self.ndis += int(disagree)


# --------------------------------------------------------------------------------------------
# Deployment: ours, reported separately
# --------------------------------------------------------------------------------------------


class SMCSDeploymentPolicy:
    """SMCS inference + B3+ acquisition + a development-chosen retain-incumbent deployment rule.

    ADAPTER (the whole rule is ours; SMCS defines a set, not an action):
      * deploy the incumbent while it is in the confidence set;
      * once the incumbent is excluded, deploy the member of the set with the smallest
        importance-weighted cumulative loss estimate (ties: lowest index);
      * if the set is empty (possible: each model can be the inferior one at some time), keep the
        current deployment;
      * because the set only shrinks, a model that has left is never redeployed, so there is no
        rollback. That is a property of SMCS inference, not a choice made here.
    Incumbent is model index ``incumbent`` (default 0).
    """

    def __init__(
        self,
        n_models: int,
        rng: np.random.Generator,
        *,
        alpha: float = 0.05,
        incumbent: int = 0,
        acquisition: PacedDisagreementAcquisition | None = None,
        name: str = "SMCS+retain-incumbent",
    ):
        self.name = name
        self.m = n_models
        self.rng = rng
        self.incumbent = incumbent
        self.deployed = incumbent
        self.inference = SMCSInference(n_models, alpha)
        self.acq = acquisition if acquisition is not None else PacedDisagreementAcquisition()
        self.cum_iw_loss = np.zeros(n_models)
        self.n_switches_decided = 0

    # -- Policy protocol ------------------------------------------------------------------
    def predict(self, event: Event) -> int:
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        u = float(self.rng.random())  # exactly one draw per event, so a u-stream can be matched
        disagree = len(np.unique(event.model_predictions)) > 1
        q = self.acq.probability(event.t, event.horizon, remaining_budget)
        ask = bool(disagree and remaining_budget > 0 and u < q)
        self.acq.close_event(disagree)
        return QueryRequest(requested=ask, probability=q if ask else 0.0)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in sorted(feedback, key=lambda f: f.event_id):
            d_tilde, lam = weighted_pair_inputs(fb.model_losses, fb.query_probability)
            self.cum_iw_loss += np.asarray(fb.model_losses, dtype=float) / fb.query_probability
            self.inference.update_pairs(d_tilde, lam)
        self._redeploy()

    def _redeploy(self) -> None:
        members = self.inference.members
        if members[self.incumbent]:
            target = self.incumbent
        elif members.any():
            idx = np.flatnonzero(members)
            target = int(idx[np.argmin(self.cum_iw_loss[idx])])
        else:
            target = self.deployed
        self.n_switches_decided += int(target != self.deployed)
        self.deployed = target

    def decision_state(self) -> str:
        members = self.inference.members
        if not members.any():
            return "set_empty"
        return "incumbent_in_set" if members[self.incumbent] else "incumbent_excluded"

    def state_dict(self) -> dict:
        return {
            "inference": self.inference.state_dict(),
            "deployed": self.deployed,
            "cum_iw_loss": self.cum_iw_loss.tolist(),
            "ndis": self.acq.ndis,
            "n_switches_decided": self.n_switches_decided,
            "rng": self.rng.bit_generator.state,
        }

    def load_state_dict(self, s: dict) -> None:
        self.inference.load_state_dict(s["inference"])
        self.deployed = int(s["deployed"])
        self.cum_iw_loss = np.array(s["cum_iw_loss"], dtype=float)
        self.acq.ndis = int(s["ndis"])
        self.n_switches_decided = int(s["n_switches_decided"])
        self.rng.bit_generator.state = s["rng"]
