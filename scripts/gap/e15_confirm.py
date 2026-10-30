"""Phase 12 confirmation: frozen arms (configs/gap_closure/frozen_confirmation_v1.json) on NEW G3-G6 pools, new seeds.
No tuning after this run. Primary metrics and comparisons are fixed in docs/sota_gap_closure/FINAL_SYNTHETIC_CONFIRMATION_PROTOCOL.md."""

import json
import time
from functools import partial

import numpy as np
import pandas as pd

from shiftlab.gap import engine as E
from shiftlab.gap import store as St
from shiftlab.gap import worlds as W

R = W.Regime
T = 2000
SEED0 = 900_000
SPEC = json.load(open("configs/gap_closure/frozen_confirmation_v1.json"))
FRAC = SPEC["frac"]


def lw(name, regs, shape="abrupt", t0=700, delay=5, grp="confirm", P=None, **noise):
    w = W.LogitWorld(regimes=regs, t0=500 if P is not None else 0, name=name, **noise)
    if P is not None:
        return St.WorldSpec(name, partial(W.make_stream, w, P=P), delay, group=grp)
    return St.WorldSpec(
        name,
        lambda S, sd, w=w: W.make_stream(
            w, S, sd, z=np.repeat(W.scheduled_regimes(shape, T, t0)[None], S, 0) * (len(regs) > 1)
        ),
        delay,
        group=grp,
    )


def dl(kind):
    return lambda st: W.delays(kind, *st["loss"].shape, loss=st["loss"], d=5, seed=21)


def fin(name, betas, P, **kw):
    return St.WorldSpec(
        name, partial(W.make_fin_stream, W.FinWorld(betas=betas, **kw), P=P), 5, group="confirm"
    )


def pool():
    from shiftlab.gap import pools as Pl

    harm, null = [], []
    harm += [
        lw(
            "C3|K3_jump_p0.99",
            (R(), R("concept", 2.5), R("cov_benign", 2.5)),
            P=W.transition(3, 0.99),
        ),
        lw(
            "C3|K4_cycle_p0.985",
            (R(), R("cost", fn=15.0), R("concept", 1.6), R("prior", 1.2)),
            P=W.transition(4, 0.985, "cycle"),
        ),
    ]
    null += [lw("C3|K2_null", (R(), R()), P=W.transition(2, 0.99))]
    harm += [
        fin("C4|fin_reversal_cycle", (1.0, -0.6), W.transition(2, 0.985, "cycle"), kappa=0.35),
        fin("C4|fin_K3", (1.0, 0.5, -0.7), W.transition(3, 0.99), a=0.12, b=0.84),
    ]
    null += [fin("C4|fin_null", (1.0, 1.0), W.transition(2, 0.99), a=0.12, b=0.84)]
    for px in ("accurate", "anti", "bias_after_shift", "subgroup", "calibration", "oracle_adapt"):
        harm.append(
            Pl.logit_sched_spec(f"C5|concept2.5|{px}", "concept", 2.5, proxy=px, group="confirm")
        )
    null += [
        Pl.logit_sched_spec(
            "C5|null|static_bias", "none", 0.0, proxy="static_bias", t0=0, group="confirm"
        )
    ]
    for k in ("uniform", "geometric", "outcome", "heavy", "burst"):
        harm.append(lw(f"C6|concept2.5|delay={k}", (R(), R("concept", 2.5)), delay=dl(k)))
    null += [
        lw("C6|null|ar0.9_s1.3", (R(),), ar_rho=0.9, ar_sigma=1.3),
        lw("C6|null|cluster120_s1.3", (R(),), cluster_len=120, cluster_sigma=1.3),
        lw("C6|null|delay=outcome", (R(),), delay=dl("outcome")),
    ]
    return harm, null


def classical(st, frac, delay, mu, sd, kind, param, thr, qseed):
    """Page-Hinkley / CUSUM on queried decision losses (uniform labels), thresholds from a null calibration stream."""
    loss = st["loss"]
    S, Tn = loss.shape
    U = np.random.default_rng(10_000 + qseed).random((Tn, S))
    stat, m, mn = np.zeros(S), np.zeros(S), np.zeros(S)
    first = np.full(S, Tn)
    buf = {}
    d = delay if np.ndim(delay) == 0 else 5
    for t in range(Tn):
        Q = U[t] < frac
        buf[t + d] = (loss[:, t] * Q, Q)
        a = buf.pop(t, None)
        if a is not None:
            v, q = a
            z = (v - mu) / sd
            if kind == "cusum":
                stat = np.where(q, np.maximum(0, stat + z - param), stat)
                cur = stat
            else:
                m = np.where(q, m + z - param, m)
                mn = np.minimum(mn, m)
                cur = m - mn
            first = np.where((cur >= thr) & (first == Tn), t, first)
    return first


def main():
    harm, null = pool()
    arms = {
        a["name"]: E.Cfg(**{**a["cfg"], "frac": FRAC})
        for a in SPEC["engine_arms"]
        if "mix" not in a
    }
    mixes = {
        a["name"]: [E.Cfg(**{**c, "frac": FRAC}) for c in a["mix"]]
        for a in SPEC["engine_arms"]
        if "mix" in a
    }
    rows = []
    t0 = time.time()
    for wi, (sp, S) in enumerate([(s, 400) for s in harm] + [(s, 1000) for s in null]):
        st = sp.make(S, SEED0 + 1000 * wi)
        dly = St._delay_arr(sp, st)
        cal = sp.make(400, SEED0 + 500_000 + 1000 * wi) if sp in null else None
        for name, cfg in arms.items():
            r = St.run_cell(sp, st, cfg, SEED0 + 1000 * wi, qseed=15, exp="confirm", cname=name)
            rows.append(r)
        for name, cfgs in mixes.items():
            res = E.run_mixture(st, cfgs, delay=dly, qseed=15)
            stats = E.alarm_stats(res["alarm"], st["truth"], T)
            rows.append(
                pd.DataFrame(
                    {
                        "exp": "confirm",
                        "T": T,
                        "world": sp.name,
                        "group": sp.group,
                        "config": name,
                        "cfg_hash": "mix",
                        "seed": SEED0 + 1000 * wi + np.arange(S),
                        "qseed": 15,
                        "alarm_t": res["alarm"],
                        "first_harm": stats["first_harm"],
                        "false_alarm": stats["false_alarm"],
                        "detected": stats["detected"],
                        "delay": stats["delay"],
                        "harm_before": stats["harm_before"],
                        "labels": res["labels"],
                        "runtime_s_per_seed": res["runtime_s"] / S,
                    }
                )
            )
        # classical detectors: nominal moments and thresholds from an independent *null* stream of the same family
        nullspec = null[0] if cal is None else sp
        base_name = sp.name.split("|")[0]
        ref = next((n for n in null if n.name.startswith(base_name)), null[0])
        refst = ref.make(400, SEED0 + 700_000 + 1000 * wi)
        mu, sd = float(refst["loss"].mean()), float(refst["loss"].std())
        for kind, param in (("ph", 0.05), ("cusum", 0.25)):
            calres = []
            first_ref = classical(refst, FRAC, 5, mu, sd, kind, param, 1e18, 15)
            del first_ref
            # horizon maximum on the null stream = the threshold: run with infinite threshold and track max by a second pass
            thr = null_threshold(refst, FRAC, mu, sd, kind, param)
            first = classical(st, FRAC, dly, mu, sd, kind, param, thr, 15)
            stats = E.alarm_stats(first, st["truth"], T)
            rows.append(
                pd.DataFrame(
                    {
                        "exp": "confirm",
                        "T": T,
                        "world": sp.name,
                        "group": sp.group,
                        "config": f"{kind}",
                        "cfg_hash": kind,
                        "seed": SEED0 + 1000 * wi + np.arange(S),
                        "qseed": 15,
                        "alarm_t": first,
                        "first_harm": stats["first_harm"],
                        "false_alarm": stats["false_alarm"],
                        "detected": stats["detected"],
                        "delay": stats["delay"],
                        "harm_before": stats["harm_before"],
                        "labels": (np.random.default_rng(10_015).random((T, S)) < FRAC).sum(0),
                        "runtime_s_per_seed": 0.0,
                    }
                )
            )
        print("world done", sp.name, round(time.time() - t0), flush=True)
    df = pd.concat(rows, ignore_index=True)
    (St.ROOT / "e15_confirm").mkdir(parents=True, exist_ok=True)
    df.to_parquet(St.ROOT / "e15_confirm/perseed.parquet", index=False)
    print("rows", len(df))


def null_threshold(refst, frac, mu, sd, kind, param):
    loss = refst["loss"]
    S, Tn = loss.shape
    U = np.random.default_rng(10_000 + 15).random((Tn, S))
    stat, m, mn, peak = np.zeros(S), np.zeros(S), np.zeros(S), np.zeros(S)
    buf = {}
    for t in range(Tn):
        Q = U[t] < frac
        buf[t + 5] = (loss[:, t] * Q, Q)
        a = buf.pop(t, None)
        if a is not None:
            v, q = a
            z = (v - mu) / sd
            if kind == "cusum":
                stat = np.where(q, np.maximum(0, stat + z - param), stat)
                cur = stat
            else:
                m = np.where(q, m + z - param, m)
                mn = np.minimum(mn, m)
                cur = m - mn
            peak = np.maximum(peak, cur)
    return float(np.quantile(peak, 0.95))


if __name__ == "__main__":
    main()
