"""Paper-formula ports of Model Picker and CAMS, plus the matched label-cutoff wrapper.

Scale-25 workstream C2 (docs/paper1_scale25/05_BASELINE_FIDELITY.md).

Provenance. The equations below were transcribed from the PUBLISHED PAPERS this session, not from
the repository's earlier ports (scripts/promising_directions/sota/competitors/{model_picker,cams}.py),
so that a comparison between the two is a genuine two-source check:

* Model Picker: Karimi, Gurel, Karlas, Rausch, Zhang, Krause, AISTATS 2021 (PMLR 130:307-315),
  arXiv:2010.09818v3, Algorithm 1 and Eq. (1): eta_t = sqrt(ln k / (2t)); w_t ~ exp(-eta_t L_{t-1});
  recommend argmax w_t; act by I_t ~ w_t; q_t = max{v(p_t,w_t), eta_t} if v != 0 else 0 with
  v = max_c <w, l^c>(1 - <w, l^c>), l^c_i = 1[p_{t,i} != c]; L_t = L_{t-1} + l_t Q_t / q_t.
* CAMS: Liu, Xia, Stevens, Chen, arXiv:2207.06030v4, Figure 1 and Eq. (4): policy set
  Pi* = Pi + constant policies; eta_t = sqrt(ln|Pi*| / t) (stochastic); q_i ~ exp(-eta_t Ltilde_i);
  w = sum_i q_i pi_i(x); stochastic recommend = argmax w; z_t = max{1/sqrt(t), E(y_hat, w)},
  E = (1/c) sum_{y: lbar^y in (0,1)} lbar^y log_c(1/lbar^y), lbar^y = <w, 1[y_hat != y]>;
  a label is bought only while C_t <= b (hard budget, native to the paper).

Both are context-free here (constant policies only), because the sprint streams carry no features.
That reduces CAMS to a two-expert problem; it is "CAMS with constant policies", not the contextual
method. Labels are delayed: the importance-weighted update is applied at release with the issue-time
probability (the same adaptation the repository's adapters use; the papers assume immediate labels).

Three things the papers fix and that the repository's adapters do not follow, which is why these
classes exist:
  * CAMS rate: paper sqrt(ln m / t), author code sqrt(m / t) (the repo port follows the code).
  * CAMS query floor: paper z_t >= 1/sqrt(t) in every round including the region of agreement;
    code returns 0 in agreement and whenever a class has posterior mass 0 after 6-decimal rounding.
  * Model Picker has no hard budget (the author code only stops RECORDING); CAMS has a hard budget.
``gate_agreement=True`` restores disagreement-only buying for the contract (an adapter choice).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SOTA = ROOT / "scripts/promising_directions/sota"
for _p in (SOTA, SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from simulator import Event, QueryRequest, ReleasedFeedback


# ------------------------------------------------------------------------------------ Model Picker
def mp_eta(k: int, t: int) -> float:
    """Algorithm 1: eta_t = sqrt(ln k / (2 t)), t = 1, 2, ..."""
    return math.sqrt(math.log(k) / (2.0 * t))


def mp_weights(L: np.ndarray, eta: float) -> np.ndarray:
    w = np.exp(-eta * (L - L.min()))  # min shift only for numerical stability
    return w / w.sum()


def mp_v(w: np.ndarray, preds: np.ndarray, n_classes: int) -> float:
    """Eq. (1) variance term: max over hypothetical true labels c of <w, l^c>(1 - <w, l^c>)."""
    best = 0.0
    for c in range(n_classes):
        m = float(w @ (preds != c).astype(float))
        best = max(best, m * (1.0 - m))
    return best


def mp_q(w: np.ndarray, preds: np.ndarray, n_classes: int, eta: float) -> float:
    if (
        len(np.unique(preds)) == 1
    ):  # v = 0 exactly in agreement; guards the 1 - (1 - 1e-16) artefact
        return 0.0
    v = mp_v(w, preds, n_classes)
    return min(1.0, max(v, eta)) if v != 0 else 0.0


class ModelPickerPaper:
    """Model Picker, Algorithm 1, as a simulator policy.

    deploy="recommend": deploy argmax w_t, the paper's own recommendation output (incumbent kept
    on exact ties, our rule). deploy="sample": the paper's prediction action I_t ~ w_t, which pays
    the switch charge whenever the draw changes. budget: the paper has none; the simulator cap is
    the only limit (``request_labels`` stops drawing at zero remaining budget).
    """

    def __init__(self, n_models: int, n_classes: int, rng, deploy: str = "recommend", name=None):
        if deploy not in ("recommend", "sample"):
            raise ValueError(deploy)
        self.k, self.c, self.rng, self.deploy = int(n_models), int(n_classes), rng, deploy
        self.L = np.zeros(self.k)
        self.deployed = 0
        self.name = name or f"mp_paper_{deploy}"

    def _w(self, event: Event) -> np.ndarray:
        return mp_weights(self.L, mp_eta(self.k, event.t + 1))

    def predict(self, event: Event) -> int:
        w = self._w(event)
        if self.deploy == "sample":
            self.deployed = int(self.rng.choice(self.k, p=w))
        elif w[self.deployed] < w.max():
            self.deployed = int(np.argmax(w))
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if remaining_budget <= 0:
            return QueryRequest(requested=False, probability=0.0)
        preds = np.asarray(event.model_predictions)
        q = mp_q(self._w(event), preds, self.c, mp_eta(self.k, event.t + 1))
        if q <= 0.0:
            return QueryRequest(requested=False, probability=0.0)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            self.L = self.L + np.asarray(fb.model_losses, float) / fb.query_probability

    def state_dict(self) -> dict:
        return {"L": self.L.tolist(), "deployed": self.deployed}

    def load_state_dict(self, s: dict) -> None:
        self.L, self.deployed = np.asarray(s["L"], float), int(s["deployed"])


# ------------------------------------------------------------------------------------------ CAMS
def cams_eta(n_policies: int, t: int) -> float:
    """Figure 1 SetRate, stochastic branch: sqrt(ln m / t) with m = |Pi*|."""
    return math.sqrt(math.log(n_policies) / t)


def cams_E(w: np.ndarray, preds: np.ndarray, n_classes: int) -> float:
    """Eq. (4) E(y_hat, w): (1/c) sum over y with lbar^y in (0,1) of lbar^y log_c(1/lbar^y)."""
    tot = 0.0
    for y in range(n_classes):
        lb = float(w @ (preds != y).astype(float))
        if 0.0 < lb < 1.0:
            tot += lb * math.log(1.0 / lb, n_classes)
    return tot / n_classes


class CAMSPaper:
    """CAMS (stochastic branch) with constant policies only: Pi* = {const_0 .. const_{k-1}}.

    With constant policies pi_i(x) = e_i, so w_t = q_t (the policy posterior is the model weight).
    ``gate_agreement=False`` is the paper's rule (z_t >= 1/sqrt(t) in agreement too); True buys only
    on disagreement (contract adaptation). The hard budget is the simulator's.
    """

    def __init__(self, n_models: int, n_classes: int, rng, gate_agreement: bool = False, name=None):
        self.k, self.c, self.rng, self.gate = int(n_models), int(n_classes), rng, gate_agreement
        self.L = np.zeros(self.k)
        self.deployed = 0
        self.name = name or ("cams_paper_gated" if gate_agreement else "cams_paper")

    def _w(self, event: Event) -> np.ndarray:
        eta = cams_eta(self.k, event.t + 1)
        q = np.exp(-eta * (self.L - self.L.min()))
        return q / q.sum()

    def predict(self, event: Event) -> int:
        w = self._w(event)
        if w[self.deployed] < w.max():
            self.deployed = int(np.argmax(w))
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if remaining_budget <= 0:
            return QueryRequest(requested=False, probability=0.0)
        preds = np.asarray(event.model_predictions)
        if self.gate and len(np.unique(preds)) == 1:
            return QueryRequest(requested=False, probability=0.0)
        z = min(1.0, max(1.0 / math.sqrt(event.t + 1), cams_E(self._w(event), preds, self.c)))
        return QueryRequest(requested=bool(self.rng.random() < z), probability=z)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            self.L = self.L + np.asarray(fb.model_losses, float) / fb.query_probability

    def state_dict(self) -> dict:
        return {"L": self.L.tolist(), "deployed": self.deployed}

    def load_state_dict(self, s: dict) -> None:
        self.L, self.deployed = np.asarray(s["L"], float), int(s["deployed"])


# ------------------------------------------------------------------------------ matched cutoff
class CutoffWrapper:
    """Hard label cutoff identical to the frozen method's: no purchase if t + delay > T - H.

    The inner policy is asked first (RNG stream and paced counters stay aligned with the
    uncut run, as the search60 compositor does); a granted request that falls after the cutoff is
    vetoed. Inner request-time bookkeeping is repaired for the one attribute family that exists in
    the panel: ``pending`` (EQSD-style hurdle families) is decremented on a veto. Policies that
    spend internal state at request time in other ways (model_selector pool.pop, the Challenger
    one-shot flag) are NOT repaired; see 05_BASELINE_FIDELITY.md section 5.
    """

    def __init__(self, inner, T: int, delay: int, H: int = 1100, name: str | None = None):
        self.inner, self.T, self.delay, self.H = inner, int(T), int(delay), int(H)
        self.name = name or f"{inner.name}_H{H}"
        self.vetoed = 0

    def closed(self, t: int) -> bool:
        return t + self.delay > self.T - self.H

    def predict(self, event):
        return self.inner.predict(event)

    def request_labels(self, event, remaining_budget):
        req = self.inner.request_labels(event, remaining_budget)
        if req.requested and self.closed(event.t):
            self.vetoed += 1
            if hasattr(self.inner, "pending"):
                self.inner.pending -= 1
            return QueryRequest(requested=False, probability=0.0)
        return req

    def observe(self, feedback):
        return self.inner.observe(feedback)

    def decision_state(self):
        f = getattr(self.inner, "decision_state", None)
        return f() if f else ""

    def state_dict(self):
        return self.inner.state_dict()

    def load_state_dict(self, s):
        return self.inner.load_state_dict(s)

    def __getattr__(self, item):  # delegate unknown attributes (deployed, n, k, ...)
        return getattr(self.inner, item)


# ------------------------------------------------------------------------------------ registry
def registry_entries(H: int = 1100) -> dict:
    """Factories with the suite signature (T, B, cs, cq, alpha, delay, r)."""
    reg = {
        "mp_paper_recommend": lambda T, B, cs, cq, a, d, r: ModelPickerPaper(
            2, 2, r("mp_paper_recommend"), "recommend"
        ),
        "mp_paper_sample": lambda T, B, cs, cq, a, d, r: ModelPickerPaper(
            2, 2, r("mp_paper_sample"), "sample"
        ),
        "cams_paper": lambda T, B, cs, cq, a, d, r: CAMSPaper(2, 2, r("cams_paper"), False),
        "cams_paper_gated": lambda T, B, cs, cq, a, d, r: CAMSPaper(
            2, 2, r("cams_paper_gated"), True, name="cams_paper_gated"
        ),
    }
    for base in list(reg):
        reg[f"{base}_H{H}"] = lambda T, B, cs, cq, a, d, r, _f=reg[base], _n=base: CutoffWrapper(
            _f(T, B, cs, cq, a, d, r), T, d, H, name=f"{_n}_H{H}"
        )
    return reg
