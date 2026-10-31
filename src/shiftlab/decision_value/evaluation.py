"""Episode-batch engine. ``simulate`` is the operational loop and takes NO truth; ``score`` is the
evaluator-side scoring. All n episodes advance in lockstep.

Step s (0-indexed decision/event time):
  1. labels released at s-1 (event e = s-1-d, if queried) are shown to the monitor;
  2. monitor statistic -> alarm; controller picks a_s (F_{s-1}-measurable);
  3. event s then realises losses l_{a_s}; its label (if queried) is released at s+d.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .contracts import CostContract, EpisodeBatch, EvaluatorTruth, FeedbackContract
from .feedback import LabelQueue, clocks
from .monitors import Target

POWER_HORIZONS = (100, 200, 400)


@dataclass
class SimResult:
    actions: np.ndarray  # (n, T) int8
    alarm: np.ndarray  # (n, T) bool: monitor alarm at the decision step
    n_queries: np.ndarray  # (n,) paid queries
    traces: dict = field(default_factory=dict)


def simulate(
    batch: EpisodeBatch, feedback: FeedbackContract, monitor, controller, trace_idx=()
) -> SimResult:
    """Operational loop. ``monitor`` may be None (reference controllers); ``batch`` holds no truth."""
    n, T = batch.n, batch.T
    queue = LabelQueue(batch, feedback.d)
    target = Target(monitor.target, n, monitor.cal) if monitor is not None else None
    actions = np.zeros((n, T), dtype=np.int8)
    alarms = np.zeros((n, T), dtype=bool)
    tr = {int(i): {"update_steps": [], "alarm_steps": [], "switch_steps": []} for i in trace_idx}
    prev = np.zeros(n, dtype=np.int8)
    for s in range(T):
        rel = queue.at(s)
        if monitor is not None:
            x, valid = target.transform(rel)
            monitor.update(x, valid)
            al = monitor.alarm()
            alarms[:, s] = al
        else:
            valid, al = rel.valid, np.zeros(n, bool)
        a, reset = controller.step(s, al, rel)
        if monitor is not None and reset.any():
            monitor.reset(reset)
        actions[:, s] = a
        for i, r in tr.items():
            if monitor is not None and valid[i]:
                r["update_steps"].append(s)
            if al[i]:
                r["alarm_steps"].append(s)
            if a[i] != prev[i]:
                r["switch_steps"].append(s)
        prev = a.copy()
    for i, r in tr.items():
        r.update(clocks(batch.mask[i], feedback.d, T))
    nq = batch.mask.sum(axis=1) if controller.acquires else np.zeros(n, dtype=np.int64)
    return SimResult(actions, alarms, nq, tr)


def count_switches(actions: np.ndarray) -> np.ndarray:
    """Switches incl. the initial move from the incumbent (a_{-1} = 0); either direction counts."""
    return (actions[:, 0] != 0).astype(np.int64) + (actions[:, 1:] != actions[:, :-1]).sum(axis=1)


def score(sim: SimResult, batch: EpisodeBatch, truth: EvaluatorTruth, cost: CostContract) -> dict:
    """Per-episode records (dict of (n,) arrays)."""
    a = sim.actions.astype(bool)
    _, T = a.shape
    mu_a = np.where(a, truth.mu1, truth.mu0)
    l_a = np.where(a, batch.l1, batch.l0).astype(float)
    ns = count_switches(sim.actions)
    nq = sim.n_queries
    extra = cost.c_q * nq + cost.c_s * ns
    opp = truth.opportunity
    adv = truth.advantage
    first_sw = np.where(a.any(axis=1), a.argmax(axis=1), T)
    before = np.arange(T)[None, :] < first_sw[:, None]
    al = sim.alarm
    any_al = al.any(axis=1)
    first_al = np.where(any_al, al.argmax(axis=1), np.nan)
    tau = truth.tau
    has_tau = ~np.isnan(tau)
    tau_i = np.where(has_tau, tau, T).astype(int)
    post = np.arange(T)[None, :] >= tau_i[:, None]
    al_post = al & post
    det = np.where(al_post.any(axis=1), al_post.argmax(axis=1), np.nan)
    delay = det - tau
    delay_cens = np.where(np.isnan(det), T - tau, np.minimum(delay, T - tau))
    rec = {
        "cost_exp": mu_a.sum(axis=1) + extra,
        "cost_real": l_a.sum(axis=1) + extra,
        "loss_exp": mu_a.sum(axis=1),
        "N_s": ns,
        "N_q": nq,
        "first_alarm": first_al,
        "n_alarms": (al[:, 1:] & ~al[:, :-1]).sum(axis=1) + al[:, 0],
        "any_alarm": any_al,
        "first_switch": np.where(a.any(axis=1), first_sw, np.nan),
        "t_chal_in_opp": (a & opp).sum(axis=1),
        "t_chal_out_opp": (a & ~opp).sum(axis=1),
        "harm_before_switch": (np.maximum(adv, 0) * before).sum(axis=1),
        "tau": tau,
        "false_alarm_pre_tau": np.where(has_tau, (al & ~post).any(axis=1), any_al),
        "det_time": det,
        "delay": delay,
        "delay_cens": delay_cens,
        "power_T": ~np.isnan(det),
        "power_opp": (al_post & opp).any(axis=1),
    }
    for h in POWER_HORIZONS:
        rec[f"power_h{h}"] = ~np.isnan(delay) & (delay < h)
    return rec


def run_episode_batch(batch, truth, feedback, cost, monitor, controller, trace_idx=()) -> dict:
    sim = simulate(batch, feedback, monitor, controller, trace_idx)
    rec = score(sim, batch, truth, cost)
    rec["_traces"] = sim.traces
    return rec
