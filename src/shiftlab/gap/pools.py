"""Named synthetic world pools (G1-G6) used by the gap-closure experiments. Seeds are assigned by the runner."""

from __future__ import annotations

from functools import partial

import numpy as np

from shiftlab.gap import store as St
from shiftlab.gap import worlds as W
from shiftlab.sota_search import generators as g

R = W.Regime
T0 = 800


def _zsched(shape: str, S: int, T: int, t0: int, **kw):
    return np.repeat(W.scheduled_regimes(shape, T, t0, **kw)[None], S, 0)


def _g_sched(w: W.LogitWorld, shape: str, S: int, seed: int, t0: int = T0, **kw):
    return W.make_stream(w, S, seed, z=_zsched(shape, S, w.T, t0, **kw))


def logit_sched_spec(name, kind, delta, shape="abrupt", t0=T0, family="G1", proxy="accurate", delay=5, group="G5", T=2000, fn=g.FN_COST, **noise):
    w = W.LogitWorld(regimes=(R(), R(kind, delta, fn)), family=family, T=T, t0=0, name=name, **noise)

    def make(S, seed, w=w, shape=shape, t0=t0, proxy=proxy):
        st = _g_sched(w, shape, S, seed, t0)
        return W.apply_proxy(st, proxy, t0=t0) if proxy != "accurate" else st

    return St.WorldSpec(name, make, delay, group=group)


def g5_pool(delay=5) -> list[St.WorldSpec]:
    """Proxy-misspecification pool. Harm worlds (concept shift) and non-harm worlds (benign shift / null)."""
    out = []
    for px in ("accurate", "bias_after_shift", "anti", "subgroup", "calibration", "oracle_adapt"):
        out.append(logit_sched_spec(f"G5|concept2|{px}", "concept", 2.0, proxy=px, delay=delay))
    for px in ("accurate", "anti", "bias_after_shift"):
        out.append(logit_sched_spec(f"G5|cov_benign3|{px}", "cov_benign", 3.0, proxy=px, delay=delay))
    for px in ("static_bias", "calibration", "recover"):
        out.append(logit_sched_spec(f"G5|null|{px}", "none", 0.0, proxy=px, delay=delay))
    return out


def g3_specs(delay=5) -> list[St.WorldSpec]:
    """Markov-switching regimes: persistence, structure, regime-dependent accuracy and decision cost."""
    defs = {
        "G3|K3_jump_p0.995": ((R(), R("concept", 2.0), R("cov_benign", 3.0)), W.transition(3, 0.995)),
        "G3|K3_jump_p0.98": ((R(), R("concept", 2.0), R("cov_benign", 3.0)), W.transition(3, 0.98)),
        "G3|K3_cycle_p0.99": ((R(), R("concept", 2.0), R("cost", fn=20.0)), W.transition(3, 0.99, "cycle")),
        "G3|K4_costshift_p0.995": ((R(), R("cost", fn=20.0), R("cov_benign", 3.0), R("prior", 1.0)), W.transition(4, 0.995)),
        "G3|K5_mixed_p0.99": (
            (R(), R("concept", 1.5), R("cov_benign", 3.0), R("prior", 1.5), R("cost", fn=20.0)),
            W.transition(5, 0.99),
        ),
        "G3|K2_null": ((R(), R()), W.transition(2, 0.99)),
    }
    out = []
    for nm, (regs, P) in defs.items():
        w = W.LogitWorld(regimes=regs, t0=500, name=nm)
        out.append(St.WorldSpec(nm, partial(W.make_stream, w, P=P), delay, group="G3"))
    return out


def g4_specs(delay=5) -> list[St.WorldSpec]:
    out = []
    defs = {
        "G4|fin_K3_p0.995": (W.FinWorld(betas=(1.0, 0.3, -1.0)), W.transition(3, 0.995)),
        "G4|fin_reversal_cycle": (W.FinWorld(betas=(1.0, -1.0)), W.transition(2, 0.99, "cycle")),
        "G4|fin_null": (W.FinWorld(betas=(1.0, 1.0)), W.transition(2, 0.99)),
    }
    for nm, (w, P) in defs.items():
        out.append(St.WorldSpec(nm, partial(W.make_fin_stream, w, P=P), delay, group="G4"))
    return out


def g6_specs(base_delay=5) -> list[St.WorldSpec]:
    """Feedback/dependence stress on a harmful concept shift (power) and on the null (validity)."""
    out = []
    for kind in ("fixed", "uniform", "geometric", "outcome", "outcome_rev", "heavy", "burst"):
        dl = (lambda st, kind=kind: W.delays(kind, *st["loss"].shape, loss=st["loss"], d=base_delay, seed=3))
        out.append(logit_sched_spec(f"G6|concept2|delay={kind}", "concept", 2.0, delay=dl, group="G6"))
    return out


def g1_g2_extra() -> list[St.WorldSpec]:
    w = [
        g.World(kind="concept", delta=2.0, shape="abrupt", t0=T0, family="G2"),
        g.World(kind="cov_benign", delta=3.0, shape="abrupt", t0=T0, family="G2"),
    ]
    return [St.WorldSpec(f"G2|{x.kind}|{x.shape}|{x.delta:g}", partial(St.g1_stream, x), 5, group="G2") for x in w]
