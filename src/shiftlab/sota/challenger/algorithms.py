"""GSE, OSE and LSE/LSEc of The Challenger (arXiv 2512.18390, Sec 4): PAPER_RECONSTRUCTION.

Inputs per epoch k: time-step t_k (sample count N_k = n t_k) and a holdout gap estimate G_hat_k obtained by
the caller (the paper trains on (1-rho) N_k samples and estimates the gap on rho N_k holdout samples).
All deciders are causal: the decision at epoch k reads only epochs 0..k (plus the known schedule).

Transcribed from the paper:
  delta_k = gamma / sqrt(rho N_k);  V^LB/UB_switch(t_k) = V_switch(t_k, G_hat_k -/+ delta_k)
  GSE  (Alg 1): V^LB_switch>0 -> SWITCH; elif V^UB_switch<0 -> (SWITCH if DeltaV^LB>0 else DISCARD); else CONTINUE;
                last epoch: SWITCH iff DeltaV_hat>0.
  OSE  (Alg 2): SWITCH iff DeltaV_hat(t_OSE)>0.
  LSE  (Alg 3): stop at epoch k iff max{V_sw(t_k), V_disc(t_k)} >= max_{k'>k} V^UB_switch(t_k'), with
                G^UB(t_k') = G_hat_k + (1-rho)(N_k' - N_k) s_k; then SWITCH iff DeltaV_hat(t_k)>0.
        LSE  (w=3): monotonicity correction (gaps decreasing -> replaced by their average), least-squares slope.
        LSEc (w=2): if G_k-G_{k-1}<0: s_k = 2 delta_k/((1-rho)(N_k-N_{k-1}));
                    else s_k = [(G_k+delta_k)-(G_{k-1}-delta_k)]/((1-rho)(N_k-N_{k-1})).
UNVERIFIED interpretations (the text did not pin these down):
 (a) LSE regresses gaps on training counts (1-rho)N so the slope is per training sample (consistent with the
     projection formula); (b) "gaps decrease" = net decrease over the window (last < first); (c) LSEc uses
 delta_k for both endpoints, as printed; (d) with fewer than 2 observed epochs LSE continues; (e) no slope floor.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from shiftlab.sota.challenger.values import Economics

SWITCH, DISCARD, CONTINUE = "switch", "discard", "continue"


@dataclass(frozen=True)
class Outcome:
    decision: str  # SWITCH | DISCARD
    epoch_idx: int  # index of the epoch at which the decision was taken


def _delta(rho: float, gamma: float, N: float) -> float:
    return gamma / float(np.sqrt(rho * N))


def gse_decide(
    econ: Economics, t_k: float, g_hat: float, gamma: float, rho: float, *, last: bool
) -> str:
    d = _delta(rho, gamma, econ.n * t_k)
    if last:
        return SWITCH if econ.delta_v(t_k, g_hat) > 0 else DISCARD
    if econ.v_switch(t_k, g_hat - d) > 0:
        return SWITCH
    if econ.v_switch(t_k, g_hat + d) < 0:
        return SWITCH if econ.delta_v(t_k, g_hat - d) > 0 else DISCARD
    return CONTINUE


def run_gse(
    econ: Economics, epochs: Sequence[float], gaps: Sequence[float], gamma: float, rho: float = 0.5
) -> Outcome:
    K = len(epochs)
    for k in range(K):
        d = gse_decide(econ, epochs[k], gaps[k], gamma, rho, last=(k == K - 1))
        if d != CONTINUE:
            return Outcome(d, k)
    raise AssertionError("unreachable")


def ose_decide(econ: Economics, t: float, g_hat: float) -> str:
    return SWITCH if econ.delta_v(t, g_hat) > 0 else DISCARD


def run_ose(econ: Economics, epochs: Sequence[float], gaps: Sequence[float], k_ose: int) -> Outcome:
    return Outcome(ose_decide(econ, epochs[k_ose], gaps[k_ose]), k_ose)


def _lse_slope(econ, epochs, gaps, k, *, variant: str, gamma: float, rho: float, w: int):
    N = econ.n * np.asarray(epochs, float)
    if variant == "LSEc":
        if k < 1:
            return None
        dk = _delta(rho, gamma, N[k])
        dN = (1 - rho) * (N[k] - N[k - 1])
        if gaps[k] - gaps[k - 1] < 0:
            return 2 * dk / dN
        return ((gaps[k] + dk) - (gaps[k - 1] - dk)) / dN
    lo = max(0, k - w + 1)
    if k - lo + 1 < 2:
        return None
    g = np.asarray(gaps[lo : k + 1], float)
    x = (1 - rho) * N[lo : k + 1]
    if g[-1] < g[0]:
        g = np.full_like(g, g.mean())
    xc = x - x.mean()
    return float(np.dot(xc, g - g.mean()) / np.dot(xc, xc))


def lse_decide(
    econ: Economics,
    epochs: Sequence[float],
    gaps: Sequence[float],
    k: int,
    *,
    variant: Literal["LSE", "LSEc"] = "LSEc",
    gamma: float = 0.1,
    rho: float = 0.5,
    w: int | None = None,
) -> str:
    """Decision at epoch k using only gaps[:k+1] (the epoch schedule is known in advance)."""
    K = len(epochs)
    if k == K - 1:
        return SWITCH if econ.delta_v(epochs[k], gaps[k]) > 0 else DISCARD
    w = w or (2 if variant == "LSEc" else 3)
    s = _lse_slope(econ, epochs, gaps[: k + 1], k, variant=variant, gamma=gamma, rho=rho, w=w)
    if s is None:
        return CONTINUE
    N = econ.n * np.asarray(epochs, float)
    ub = max(
        econ.v_switch(epochs[j], gaps[k] + (1 - rho) * (N[j] - N[k]) * s) for j in range(k + 1, K)
    )
    stop = max(econ.v_switch(epochs[k], gaps[k]), econ.v_discard(epochs[k])) >= ub
    if not stop:
        return CONTINUE
    return SWITCH if econ.delta_v(epochs[k], gaps[k]) > 0 else DISCARD


def run_lse(econ: Economics, epochs: Sequence[float], gaps: Sequence[float], **kw) -> Outcome:
    for k in range(len(epochs)):
        d = lse_decide(econ, epochs, gaps, k, **kw)
        if d != CONTINUE:
            return Outcome(d, k)
    raise AssertionError("unreachable")
