"""Failure Atlas v2 competitor suite and per-run metrics on the common streaming simulator.

Every policy is the existing implementation in ``scripts/promising_directions/sota/competitors``;
nothing here re-implements a competitor. Names follow the fidelity record in
``docs/promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md``: an entry is called by its
published name only where that document allows, otherwise it carries an adapter suffix.

Not run on loss-only streams (no features exist to fit their nuisance models): Sawade et al.
calibrated, Xu prediction-assisted, CAMS with contextual policies. CAMS is run with constant
policies only, and variance minimisation with a uniform class prior, which in the binary
two-model task is exact because its surrogate cancels (validation round 2).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for _p in (SOTA, SOTA / "competitors", SOTA.parent, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from cams import CAMSDeploymentAdapter, stack_advice
from certificate_stops import DiscernStyleStop, GatedDeploymentStop
from controls import EconomicReplacement, FixedModel
from model_picker import ModelPickerDeploymentAdapter
from model_selector import ModelSelectorCausalAdapter
from online_llm_picker import OnlineLLMPicker
from simulator import policy_rng, run_episode
from smcs import SMCSDeploymentPolicy
from variance_min import VarianceMinStreamingIPW
from xu_acquisition import XuAcquisitionPolicy

# Display name -> (published-name status, family). "family" groups independently developed
# approaches so that a shared failure can be counted across distinct lines of work.
SUITE_INFO = {
    "gated_deployment": (
        "Gated Deployment / off-policy CS adapter (Karampatziakis+21)",
        "anytime-CS",
    ),
    "discern_style": ("DISCERN-style certificate stop (no author code)", "anytime-CS"),
    "SMCS+retain-incumbent": ("SMCS inference + retain-incumbent rule", "e-value-elimination"),
    "model_picker_adapter": ("Model Picker deployment adapter", "online-bayes-selection"),
    "model_selector_causal": (
        "Model Selector, causal record-gate adapter",
        "pool-active-selection",
    ),
    "online_llm_picker": ("Online LLM Picker (eps ours)", "online-bandit-selection"),
    "xu_acquisition_only": ("Xu et al. acquisition-only adapter", "active-testing-betting"),
    "cams_adapter": ("CAMS with constant policies only (adapter)", "expert-advice-selection"),
    "variance_min_ipw": ("variance-min score + streaming IPW (not LURE)", "active-risk-estimation"),
    "P7s_settled": ("P7s settled acquisition (ours, B3+)", "ours-prior"),
    "CONTROL_never_switch": ("control", "control"),
    "economic_replacement": ("control: development-tuned economic rule", "control"),
}


def build_suite(T, budget, cs, cq, alpha, delay, ep, seed_base, *, names=None, extra=None):
    def r(nm):
        return policy_rng(seed_base, ep, nm)

    def p7s():
        from b3_plus_policy import b1
        from b3_plus_policy_adapter import P7sPolicy

        return P7sPolicy(
            horizon=T,
            budget=budget,
            delay=delay,
            switch_cost=cs,
            label_price=cq,
            rng=r("P7s"),
            params=b1.Params(T=T, delay=delay, cq=cq, alpha=alpha),
        )

    makers = {
        "gated_deployment": lambda: GatedDeploymentStop(
            T, budget, alpha, rng=r("gated_deployment")
        ),
        "discern_style": lambda: DiscernStyleStop(T, budget, alpha, 0.0, rng=r("discern_style")),
        "SMCS+retain-incumbent": lambda: SMCSDeploymentPolicy(2, r("smcs"), alpha=alpha),
        "model_picker_adapter": lambda: ModelPickerDeploymentAdapter(2, 2, r("model_picker")),
        "model_selector_causal": lambda: ModelSelectorCausalAdapter(2, 2, r("model_selector")),
        "online_llm_picker": lambda: OnlineLLMPicker(2, 2, rng=r("online_llm_picker")),
        "xu_acquisition_only": lambda: XuAcquisitionPolicy(
            "acquisition_only", r("xu"), delay=delay
        ),
        "cams_adapter": lambda: CAMSDeploymentAdapter(
            n_models=2, n_classes=2, advice_fn=stack_advice(2, []), rng=r("cams")
        ),
        "variance_min_ipw": lambda: VarianceMinStreamingIPW(
            2, 2, r("vmin"), rate=budget / T, class_prior=np.array([0.5, 0.5])
        ),
        "P7s_settled": p7s,
        "CONTROL_never_switch": lambda: FixedModel(0, name="CONTROL_never_switch"),
        "economic_replacement": lambda: EconomicReplacement(T, budget, cs, rng=r("econ")),
    }
    if extra:
        makers.update(
            {k: (lambda f=f: f(T, budget, cs, cq, alpha, delay, r)) for k, f in extra.items()}
        )
    names = names or list(makers)
    out = []
    for n in names:
        pol = makers[n]()
        pol.name = n
        out.append(pol)
    return out


def stream_from_losses(losses: np.ndarray, rng) -> tuple[np.ndarray, np.ndarray]:
    """Balanced labels with predictions = label XOR loss: reproduces the loss stream exactly."""
    labels = rng.integers(0, 2, losses.shape[0])
    preds = labels[:, None].astype(int) ^ losses.astype(int)
    return preds, labels


def run_metrics(
    pol, losses, gain, *, delay, budget, cq, cs, stream_rng, oracle_cost=None, exp_path=None
) -> dict:
    preds, labels = stream_from_losses(losses, stream_rng)
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=delay,
        budget=budget,
        label_price=cq,
        switch_cost=cs,
        trace=True,
    )
    if res.requested_labels > budget:
        raise AssertionError(f"{pol.name} exceeded budget")
    dep = np.fromiter((r["deployed_model"] for r in res.records), int, len(res.records))
    req = np.fromiter((r["requested"] for r in res.records), int, len(res.records))
    Tn = len(dep)
    req_t = np.flatnonzero(req)
    first1 = int(np.argmax(dep == 1)) if (dep == 1).any() else -1
    better = gain > 0
    worse = gain < 0
    on_wrong = ((dep == 1) & worse) | ((dep == 0) & better)
    m = {
        "net": res.net_cost,
        "loss": res.prediction_loss,
        "labels": res.requested_labels,
        "switches": res.deployment_switches,
        "first_deploy": first1,
        "final": int(dep[-1]),
        "ever_promote": int(first1 >= 0),
        "frac_on_better_when_better": float((dep[better] == 1).mean()) if better.any() else np.nan,
        "frac_on_wrong": float(on_wrong.mean()),
        "label_mean_t": float(req_t.mean()) if len(req_t) else np.nan,
        "labels_by_500": int((req_t < 500).sum()),
        "labels_after_1000": int((req_t >= 1000).sum()),
        "exhaust_t": int(req_t[budget - 1]) if len(req_t) >= budget else Tn,
        "excess_vs_expected_G": float(np.sum(np.where(dep == 1, -gain, 0.0))),
    }
    if oracle_cost is not None:
        m["regret_hindsight"] = res.net_cost - oracle_cost
    if exp_path is not None:
        exp_cost = float(
            np.sum(losses[np.arange(Tn), exp_path]) + cs * np.sum(np.diff(np.r_[0, exp_path]) != 0)
        )
        m["regret_expected_oracle"] = res.net_cost - exp_cost
    return m
