"""Run monitors on tapes and score them (PROTOCOL section 7). Columns match ``stats.COLUMNS``.

alarm_X: first alarm step, -1 = no alarm, -2 = track not produced by the monitor. n_queries counts
labels issued up to the stopping time (the monitor's primary-track alarm, else T-1). runtime_s is the
monitor's wall time for the whole (possibly cell-batched) tape divided by the number of rows.
J_cost = excess cost over [tau, stop] in harm worlds + c_q * n_queries + c_FA * 1{alarm where the
track's null holds}; track J sums the B and C excess terms and uses the joint null.
"""

from __future__ import annotations

import time

import pandas as pd
import torch

from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.baselines import REGISTRY

C_Q, C_FA, C_I, C_S = 0.02, 50.0, 5.0, 2.0


def _excess(cs, theta, harm_world, tau, stop):
    """sum_{t=tau}^{stop} (x_t - theta) from the padded cumulative sum cs [S, T+1]."""
    tau = tau.clamp(min=0, max=cs.shape[1] - 1)
    tot = (
        cs.gather(1, (stop + 1)[:, None])[:, 0]
        - cs.gather(1, tau[:, None])[:, 0]
        - theta * (stop + 1 - tau)
    )
    return torch.where(harm_world & (stop >= tau), tot, torch.zeros_like(tot))


def score(res, tape, track, k, mid):
    """Per-seed DataFrame for candidate k of a Result."""
    T = tape["B"].shape[1]
    ev = tape["eval"]
    tau, nB, nC = ev["tau"], ev["null_B"], ev["null_C"]
    if "cs" not in tape:  # padded cumulative sums, computed once per tape
        tape["cs"] = {
            c: torch.cat([torch.zeros_like(tape[c][:, :1]), tape[c].cumsum(1)], 1) for c in "BC"
        }
    csB, csC = tape["cs"]["B"], tape["cs"]["C"]
    al = {t: res.alarm[t][k] for t in res.alarm}
    stop = torch.where(al[track] >= T, torch.full_like(al[track], T - 1), al[track])
    nq = res.nq_at[track][k].double()
    tauv = torch.where(tau >= 0, tau, torch.full_like(tau, T))
    eB = _excess(csB, tape["theta"]["B"], ~nB & (tau >= 0), tauv, stop)
    eC = _excess(csC, tape["theta"]["C"], ~nC & (tau >= 0), tauv, stop)
    exc, null = {"B": (eB, nB), "C": (eC, nC), "J": (eB + eC, nB & nC)}[track]
    fa = ((al[track] < T) & null).double()
    hit = (al[track] < T).double()
    nint, nsw = (
        hit,
        hit,
    )  # one alarm-triggered intervention and one switch to the fallback; no restart in stage 2
    jc = exc + C_Q * nq + C_FA * fa + C_I * nint + C_S * nsw
    sB, sC = csB.gather(1, (stop + 1)[:, None])[:, 0], csC.gather(1, (stop + 1)[:, None])[:, 0]
    loss = {"B": sB, "C": sC, "J": sB + sC}[track]
    lossC = sC
    nan = torch.full_like(tau, float("nan"), dtype=torch.float64)
    cols = {}
    for t in "BCJ":
        a = al.get(t)
        cols[f"alarm_{t}"] = (
            torch.full_like(tau, -2)
            if a is None
            else torch.where(a >= T, torch.full_like(a, -1), a)
        )
    cell_ids = [c.cell_id for c, n in zip(tape["cells"], tape["sizes"]) for _ in range(n)]
    fam = [c.family for c, n in zip(tape["cells"], tape["sizes"]) for _ in range(n)]
    df = pd.DataFrame(dict(
        method_id=mid, cell_id=cell_ids, family=fam, seed=tape["seeds"].cpu().numpy(), partition=tape["partition"],
        tau=tau.cpu().numpy(), **{c: v.cpu().numpy() for c, v in cols.items()},
        n_queries=nq.cpu().numpy(), J_cost=jc.cpu().numpy(), excess_cost_before_alarm=exc.cpu().numpy(),
        null_B=nB.cpu().numpy(), null_C=nC.cpu().numpy(),
        loss_before_alarm=loss.cpu().numpy(), cumulative_decision_cost=lossC.cpu().numpy(),
        n_interventions=nint.cpu().numpy(), n_switches=nsw.cpu().numpy(),
        intervention_cost=(C_I * nint).cpu().numpy(), switching_cost=(C_S * nsw).cpu().numpy(),
        info_cost=(C_Q * nq).cpu().numpy(),
        **{f"mean_logW_{t}": res.lw_mean.get(t, nan[None].expand(k + 1, -1))[k].cpu().numpy() for t in "BCJ"},
    ))  # fmt: skip
    return df


def run(monitors, cell, partition="dev", n_seeds=256, device="cuda", seed0=0, tracks=None):
    """monitors: registry names or {method_id: monitor} or [(method_id, monitor)]; cell: one cell or a list
    (cells of equal T are batched into one tape). Returns the per-seed DataFrame."""
    cells = list(cell) if isinstance(cell, (list, tuple)) else [cell]
    tape = TP.cat_tapes([TP.generate(c, partition, n_seeds, device, seed0) for c in cells])
    items = monitors.items() if isinstance(monitors, dict) else monitors
    out = []
    for it in items:
        if isinstance(it, str):
            ctor, trk, _, _ = REGISTRY[it]
            mon, name, track = ctor(), it, trk
        else:
            name, mon = it
            track = (tracks or {}).get(name) or (REGISTRY[name][1] if name in REGISTRY else None)
        if torch.cuda.is_available() and str(device).startswith("cuda"):
            torch.cuda.synchronize()
        if torch.cuda.is_available() and str(device).startswith("cuda"):
            torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        res = mon.run(tape)
        if str(device).startswith("cuda"):
            torch.cuda.synchronize()
        dt = (time.perf_counter() - t0) / tape["B"].shape[0]
        peak = torch.cuda.max_memory_allocated() / 2**20 if str(device).startswith("cuda") else 0.0
        for k, mid in enumerate(res.ids if len(res.ids) > 1 else [name]):
            tk = track or ("J" if "J" in res.alarm else next(iter(res.alarm)))
            df = score(res, tape, tk, k, mid)
            df["runtime_s"] = dt
            df["peak_mem_mb"] = peak
            out.append(df)
    return pd.concat(out, ignore_index=True)
