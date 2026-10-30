"""Second-round fixes F1-F3 on NEW development worlds (see docs/sota_gap_closure/SECOND_ROUND_FIX_CANDIDATES.md)."""

from functools import partial

import numpy as np

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St
from shiftlab.gap import worlds as W

R = W.Regime
T = 2000


def lw(name, regs, shape="abrupt", t0=700, delay=5, grp="dev2", **noise):
    w = W.LogitWorld(regimes=regs, t0=0, name=name, **noise)
    return St.WorldSpec(
        name,
        lambda S, sd, w=w: W.make_stream(
            w, S, sd, z=np.repeat(W.scheduled_regimes(shape, T, t0)[None], S, 0) * (len(regs) > 1)
        ),
        delay,
        group=grp,
    )


def specs():
    out = []
    # dependence nulls (validity)
    out += [
        lw("D2|null|ar0.8_s1.2", (R(),), ar_rho=0.8, ar_sigma=1.2),
        lw("D2|null|ar0.97_s1.2", (R(),), ar_rho=0.97, ar_sigma=1.2),
    ]
    out += [
        lw("D2|null|cluster50_s1.2", (R(),), cluster_len=50, cluster_sigma=1.2),
        lw("D2|null|cluster200_s1.2", (R(),), cluster_len=200, cluster_sigma=1.2),
    ]
    out += [
        St.WorldSpec(
            "D2|null|fin_garch_a.15b.8",
            partial(
                W.make_fin_stream,
                W.FinWorld(betas=(1.0, 1.0), a=0.15, b=0.80, kappa=0.3),
                P=W.transition(2, 0.99),
            ),
            5,
            group="dev2",
        )
    ]
    out += [
        St.WorldSpec(
            "D2|null|fin_garch_a.10b.88",
            partial(
                W.make_fin_stream,
                W.FinWorld(betas=(1.0, 1.0), a=0.10, b=0.88, kappa=0.4),
                P=W.transition(2, 0.99),
            ),
            5,
            group="dev2",
        )
    ]
    # iid nulls / benign
    out += [lw("D2|null|iid", (R(),)), lw("D2|benign|cov_benign2.5", (R(), R("cov_benign", 2.5)))]
    # iid harm worlds (power)
    out += [
        lw("D2|harm|concept1.8_abrupt", (R(), R("concept", 1.8))),
        lw("D2|harm|concept1.8_gradual", (R(), R("concept", 1.8)), shape="gradual"),
        lw("D2|harm|cost_regime_fn20", (R(), R("cost", fn=20.0))),
    ]
    out += [
        St.WorldSpec(
            "D2|harm|fin_K3",
            partial(
                W.make_fin_stream,
                W.FinWorld(betas=(1.0, 0.0, -0.8), kappa=0.35),
                P=W.transition(3, 0.995),
            ),
            5,
            group="dev2",
        )
    ]
    # transient / recurrent harm (F3 targets)
    out += [
        lw("D2|trans|concept2_transient", (R(), R("concept", 2.0)), shape="transient"),
        lw("D2|trans|concept1.8_recurrent", (R(), R("concept", 1.8)), shape="recurrent"),
        lw("D2|trans|cost_fn20_transient", (R(), R("cost", fn=20.0)), shape="transient"),
    ]
    return out


def cfgs(frac=0.2):
    c = {}
    for pn, pk in (
        ("pprm", dict(risk="brier")),
        ("HG", dict(risk="brier", gamma=0.99, gate_w=100)),
        ("cost", dict(risk="cost", gamma=0.99)),
    ):
        b = dict(frac=frac, **pk)
        c[f"{pn}|parent"] = E.Cfg(**b)
        c[f"{pn}|F1_var_floor.5"] = E.Cfg(alloc="variance", qmin=frac / 2, **b)
        c[f"{pn}|F1_var_unfloored"] = E.Cfg(alloc="variance", **b)
        c[f"{pn}|F2_lrv100"] = E.Cfg(lrv=True, lrv_lags=100, **b)
        c[f"{pn}|F2_lrv30"] = E.Cfg(lrv=True, lrv_lags=30, **b)
    return c


if __name__ == "__main__":
    sp = specs()
    cf = cfgs()
    # F3 handled below (mixture of three e-processes per parent)
    df = St.run_grid(
        "e14_fixes_dev2",
        sp,
        cf,
        S=400,
        seed0=80000,
        qseed=14,
        note="second-round fixes F1/F2 on new dev worlds",
    )
    import pandas as pd

    rows = []
    for i, s in enumerate(sp):
        st = s.make(400, 80000 + 1000 * i)
        for pn, pk in (
            ("pprm", dict(risk="brier")),
            ("HG", dict(risk="brier", gamma=0.99, gate_w=100)),
            ("cost", dict(risk="cost", gamma=0.99)),
        ):
            base = dict(frac=0.2, **pk)
            mix = [E.Cfg(**{**base, "gamma": g_}) for g_ in (1.0, 0.99, 0.95)]
            for i2 in range(len(mix)):
                if pn == "HG":
                    mix[i2] = E.Cfg(**{**base, "gamma": (1.0, 0.99, 0.95)[i2], "gate_w": 100})
            res = E.run_mixture(st, mix, delay=St._delay_arr(s, st), qseed=14)
            stats = E.alarm_stats(res["alarm"], st["truth"], T)
            rows.append(
                pd.DataFrame(
                    {
                        "exp": "e14_fixes_dev2",
                        "T": T,
                        "world": s.name,
                        "group": s.group,
                        "config": f"{pn}|F3_multiwindow",
                        "cfg_hash": "mix3",
                        "seed": 80000 + 1000 * i + np.arange(400),
                        "qseed": 14,
                        "alarm_t": res["alarm"],
                        "first_harm": stats["first_harm"],
                        "false_alarm": stats["false_alarm"],
                        "detected": stats["detected"],
                        "delay": stats["delay"],
                        "harm_before": stats["harm_before"],
                        "labels": res["labels"],
                        "runtime_s_per_seed": res["runtime_s"] / 400,
                    }
                )
            )
    df = pd.concat([df, *rows], ignore_index=True)
    df.to_parquet("outputs/gap_closure/e14_fixes_dev2/perseed.parquet", index=False)
    sm = St.summarise(df)
    sm.to_csv("outputs/gap_closure/e14_fixes_dev2/summary_by_world.csv", index=False)
    print("done", len(df))
