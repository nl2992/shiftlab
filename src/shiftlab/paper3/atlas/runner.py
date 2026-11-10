"""Method roster, per-episode metrics (alarm + economic) and cost-identity check for the atlas."""

from __future__ import annotations

import math

import numpy as np

from .cells import Cell, T
from .certificate_stops import DiscernStyleStop, GatedDeploymentStop
from .controls import FixedModel
from .policies import AlarmSwitcher, GatedSwitcher, SpacedAcquisition
from .sim import policy_rng, preds_from_losses, run_episode
from .smcs import SMCSDeploymentPolicy

ALPHA = 0.05
RHO_MAX = 0.95  # C1 ex-ante declared dependence bound (never read from the cell)

MAIN = [
    "never_switch",
    "gated_mope",
    "discern_fixed",
    "smcs_retain",
    "cusum",
    "page_hinkley",
    "edetector",
    "wald_econ",
    "thinned_iid",
    "markov_skeleton",
]
REPAIR = ["c1_gapaware", "c1_gapaware_rho80", "c3_spaced_iid", "c1c3"]
FIDELITY = ["discern_fixed", "discern_legacy"]


def build(name: str, cell_params: dict, seed_base: int, ep: int):
    """Construct a policy using ONLY information a deployer has ex ante: horizon, budget, price,
    switch cost, alpha and the declared RHO_MAX. Never the cell's rho/onset/delta."""
    B, k, d = cell_params["budget"], cell_params["switch_cost"], cell_params["delay"]
    r = policy_rng(seed_base, ep, name)
    if name == "never_switch":
        return FixedModel(0, name=name)
    if name == "gated_mope":
        return GatedDeploymentStop(T, B, ALPHA, rng=r, name=name)
    if name == "discern_fixed":
        return DiscernStyleStop(T, B, ALPHA, 0.0, rng=r, name=name)
    if name == "discern_legacy":
        return DiscernStyleStop(T, B, ALPHA, 0.0, rng=r, name=name, legacy_psi=True)
    if name == "smcs_retain":
        return SMCSDeploymentPolicy(2, r, alpha=ALPHA, name=name)
    if name in ("cusum", "page_hinkley", "edetector", "wald_econ"):
        return AlarmSwitcher(name, T, B, k, r)
    if name == "edetector_cal":  # threshold B/alpha: expected false alarms over B labels <= alpha
        return AlarmSwitcher("edetector", T, B, k, r, alpha=ALPHA / B, name_override=name)
    if name == "cusum_cal":  # h = log(B/alpha): same union-over-labels calibration
        return AlarmSwitcher("cusum", T, B, k, r, h=math.log(B / ALPHA), name_override=name)
    if name == "thinned_iid":
        return GatedSwitcher(name, T, B, r, "thinned")
    if name == "markov_skeleton":
        return GatedSwitcher(name, T, B, r, "skeleton", rho_max=RHO_MAX)
    if name == "iid_gate":
        return GatedSwitcher(name, T, B, r, "iid")
    gmin = max(2, min(math.ceil(math.log(0.25) / math.log(RHO_MAX)), int(0.7 * T / B)))
    pcap = max(2, math.ceil(d / gmin) + 1)
    if name == "c1_gapaware":
        return GatedSwitcher(name, T, B, r, "gapaware", rho_max=RHO_MAX)
    if name == "c1_gapaware_rho80":
        return GatedSwitcher(name, T, B, r, "gapaware", rho_max=0.80)
    if name == "c3_spaced_iid":  # spacing acquisition + dependence-unaware gate (isolates C3)
        return GatedSwitcher(name, T, B, r, "iid", acq=SpacedAcquisition(T, B, gmin, pcap))
    if name == "c1c3":
        return GatedSwitcher(
            name, T, B, r, "gapaware", rho_max=RHO_MAX, acq=SpacedAcquisition(T, B, gmin, pcap)
        )
    raise KeyError(name)


def episode_metrics(out, losses, regime, cell_params, null):
    """Alarm + economic metrics with an exact accounting identity (asserted).

    J = L0 + c_q*n_q + k*n_sw - sum_{dep=1} D   (D = l0 - l1 realised).  Decomposition:
    J = [L0 - sum_good D] + fees + intervention + harm_bad + noise_neutral + forgone_good,
    with  harm_bad = -sum_{dep=1,bad} D, noise_neutral = -sum_{dep=1,neutral} D,
    forgone_good = sum_{good} D - sum_{dep=1,good} D split into certification lag (before the first
    deployment of the challenger inside the first good window) and re-miss (the rest).
    """
    D = losses[:, 0].astype(int) - losses[:, 1].astype(int)
    dep = out.dep.astype(int)
    L0 = float(losses[:, 0].sum())
    price, k = cell_params["price"], cell_params["switch_cost"]
    fees, interv = price * out.n_queries, k * out.n_switches
    J_recon = L0 + fees + interv - float(D[dep == 1].sum())
    assert abs(J_recon - out.cost) < 1e-6, (J_recon, out.cost)
    good, bad, neu = regime > 0, regime < 0, regime == 0
    harm_bad = -float(D[(dep == 1) & bad].sum())
    noise_neu = -float(D[(dep == 1) & neu].sum())
    sum_good = float(D[good].sum())
    taken_good = float(D[(dep == 1) & good].sum())
    forgone = sum_good - taken_good
    lag = 0.0
    if good.any():
        gi = np.flatnonzero(good)
        w0, w1 = gi[0], gi[-1]
        # first deployment inside the first good window
        win = np.arange(w0, w1 + 1)
        first_on = win[dep[win] == 1]
        stop = first_on[0] if len(first_on) else w1 + 1
        lag = float(D[np.arange(w0, stop)][good[w0:stop]].sum())
    parts = {
        "J": float(out.cost),
        "L0": L0,
        "fees": fees,
        "intervention": interv,
        "harm_bad": harm_bad,
        "noise_neutral": noise_neu,
        "forgone_good": forgone,
        "cert_lag": lag,
        "remiss": forgone - lag,
        "sum_good_D": sum_good,
    }
    # identity: J = L0 - sum_good + fees + interv + harm_bad + noise + forgone
    assert abs(L0 - sum_good + fees + interv + harm_bad + noise_neu + forgone - out.cost) < 1e-6
    promoted = dep == 1
    first_prom = int(np.argmax(promoted)) if promoted.any() else -1
    m = {
        **parts,
        "n_q": out.n_queries,
        "n_sw": out.n_switches,
        "max_pending": out.max_pending,
        "first_prom": first_prom,
        "ever_prom": int(promoted.any()),
        "refused": out.n_refused,
    }
    if null:
        m["null_fp"] = int(promoted.any())
    else:
        onset = int(np.argmax(good)) if good.any() else T
        end = int(np.flatnonzero(good)[-1]) + 1 if good.any() else T
        m["false_alarm_pre"] = int(promoted[:onset].any())
        inwin = promoted[onset:end]
        m["detected"] = int(inwin.any())
        m["edd"] = (
            int(np.argmax(inwin)) if inwin.any() else end - onset
        )  # censored at window length
        m["edd_unc"] = int(np.argmax(inwin)) if inwin.any() else -1
        m["missed"] = int(not inwin.any())
        m["avoidable_post_harm"] = harm_bad
    return m


def run_one(cell: Cell, seed: int, methods: list[str], null: bool, seed_base: int):
    """Same realised stream and delays for every method (paired); returns list of metric dicts."""
    rng = np.random.default_rng(np.random.SeedSequence([seed_base, seed, cell.cid, int(null)]))
    losses = cell.sample(rng, null=null)
    preds, labels = preds_from_losses(
        losses, np.random.default_rng(np.random.SeedSequence([seed_base, seed, cell.cid, 7]))
    )
    D = losses[:, 0].astype(int) - losses[:, 1].astype(int)
    delays = cell.delays(D)
    regime = cell.regime(null)
    cp = {
        "budget": cell.budget,
        "switch_cost": cell.switch_cost,
        "delay": cell.delay,
        "price": cell.price,
    }
    rows = []
    for name in methods:
        pol = build(name, cp, seed_base, seed * 1000 + cell.cid)
        out = run_episode(
            pol,
            preds,
            labels,
            delays,
            budget=cell.budget,
            price=cell.price,
            switch_cost=cell.switch_cost,
        )
        assert out.n_queries <= cell.budget
        m = episode_metrics(out, losses, regime, cp, null)
        m.update(method=name, cell=cell.cid, seed=seed, null=int(null))
        rows.append(m)
    return rows
