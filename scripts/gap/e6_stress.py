"""Phase 8 statistical stress matrix: 14 mandated experiments, empirical validity + power. Synthetic only.

Arms: pprm (Brier e-process), HG, cost-only e-process, each with the repaired cap and in-order release ('prefix'),
plus naive 'arrived' release for the delay experiments. The null-class and mathematical scope per experiment is
written in docs/sota_gap_closure/NULL_CLASS_SPECIFICATIONS.md.
"""

from functools import partial

import numpy as np

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St
from shiftlab.gap import worlds as W

R = W.Regime
S = 2000


def lw(name, regs=(R(),), t0=800, shape="abrupt", delay=5, family="G1", **noise):
    w = W.LogitWorld(regimes=regs, family=family, t0=0, name=name, **noise)
    z_fn = lambda Sx, T: np.repeat(W.scheduled_regimes(shape, T, t0)[None], Sx, 0) * (len(regs) > 1)
    return St.WorldSpec(
        name,
        lambda Sx, sd, w=w: W.make_stream(w, Sx, sd, z=z_fn(Sx, w.T)),
        delay,
        group=name.split("|")[0],
    )


def dl(kind, d=5):
    return lambda st, kind=kind: W.delays(kind, *st["loss"].shape, loss=st["loss"], d=d, seed=11)


class AdaptiveCov:
    """History-adaptive covariate process: P(x=1 | last loss) depends on the previous loss; P(loss|x) is calibrated."""

    def __init__(self, sign, h=(0.05, 0.35), T=2000):
        self.sign, self.h, self.T = sign, h, T

    def make(self, S_, seed):
        rng = np.random.default_rng(seed)
        T, h = self.T, self.h

        def gen(Sx, rng):
            x = np.zeros((Sx, T), dtype=bool)
            loss = np.zeros((Sx, T))
            prev = np.zeros(Sx)
            u1, u2 = rng.random((Sx, T)), rng.random((Sx, T))
            for t in range(T):
                px = np.clip(0.5 + self.sign * 0.4 * (prev - 0.2), 0.02, 0.98)
                x[:, t] = u1[:, t] < px
                loss[:, t] = (u2[:, t] < np.where(x[:, t], h[1], h[0])).astype(float)
                prev = loss[:, t]
            return x, loss

        x, loss = gen(S_, rng)
        _x0, l0 = gen(400, np.random.default_rng(seed + 1))
        r0 = float(l0.mean())
        proxy = np.where(x, h[1], h[0])
        return {
            "x": x[..., None].astype(np.float32),
            "y": loss.astype(np.int8),
            "p": proxy,
            "score": proxy,
            "loss": loss,
            "brier": loss,
            "proxy_cost": proxy,
            "proxy_brier": proxy,
            "r0": {"cost": r0, "brier": r0},
            "pmax": {"cost": max(h), "brier": max(h)},
            "truth": {
                "harm": np.zeros(T),
                "discrepancy": np.zeros(T),
                "predictive": np.zeros(T),
                "thr": 0.1,
            },
        }


def adaptive(name, sign):
    return St.WorldSpec(name, AdaptiveCov(sign).make, 5, group="X05")


def hetero(name, shifted):
    hn = W.HeteroNull()
    return St.WorldSpec(
        name, lambda Sx, sd: W.make_hetero_stream(hn, Sx, sd, shifted), 5, group="X06"
    )


def extreme_cost(name, fn):
    w = W.LogitWorld(regimes=(R(), R("cost", fn=fn)), t0=0, name=name)
    return St.WorldSpec(
        name,
        lambda Sx, sd, w=w: W.make_stream(w, Sx, sd, z=np.zeros((Sx, w.T), dtype=np.int64)),
        5,
        group="X14",
    )


def fin(name, betas, P_):
    return St.WorldSpec(
        name, partial(W.make_fin_stream, W.FinWorld(betas=betas), P=P_), 5, group="X14"
    )


def specs():
    out = []
    # 1 fixed vs random independent delay (null)
    for k in ("fixed", "uniform", "geometric"):
        out.append(lw(f"X01|null|delay={k}", delay=dl(k)))
    # 2 outcome-dependent delay (null)
    for k in ("outcome", "outcome_rev", "heavy", "burst"):
        out.append(lw(f"X02|null|delay={k}", delay=dl(k)))
    # 3 autocorrelated outcomes (null marginal law unchanged)
    for rho, sg in ((0.5, 1.0), (0.9, 1.0), (0.98, 1.5)):
        out.append(lw(f"X03|null|ar{rho}_s{sg}", ar_rho=rho, ar_sigma=sg))
    # 4 clustered observations
    for L, sg in ((20, 1.0), (100, 1.5), (400, 1.5)):
        out.append(lw(f"X04|null|cluster{L}_s{sg}", cluster_len=L, cluster_sigma=sg))
    # 5 history-adaptive covariate process (marginal null holds, conditional null does not)
    out += [adaptive("X05|null|adaptive_pos", +1), adaptive("X05|null|adaptive_neg", -1)]
    # 6 heterogeneous conditional risk, unchanged marginal risk
    out += [hetero("X06|null|hetero_calibrated", False), hetero("X06|null|hetero_rearranged", True)]
    # 7 severe proxy bias (null)
    for px in ("static_bias", "calibration", "anti"):
        sp = P.logit_sched_spec(f"X07|null|proxy={px}", "none", 0.0, proxy=px, t0=0, group="X07")
        out.append(sp)
    # 8 no shift
    out += [lw("X08|null|G1"), lw("X08|null|G2", family="G2")]
    out += [s for s in P.g3_specs() if "null" in s.name] + [
        s for s in P.g4_specs() if "null" in s.name
    ]
    # 9 benign covariate shift
    for kind, d in (("cov_benign", 3.0), ("cov_inform", 2.0), ("prior", 1.0)):
        out.append(lw(f"X09|{kind}{d:g}", regs=(R(), R(kind, d))))
    # 10 transient harm ; 11 multiple recurrent shifts (power + validity of pre-harm period)
    for d in (1.5, 2.0, 3.0):
        out.append(
            lw(f"X10|concept{d:g}_transient", regs=(R(), R("concept", d)), shape="transient")
        )
    out.append(lw("X11|concept2_recurrent", regs=(R(), R("concept", 2.0)), shape="recurrent"))
    # 14 extreme but bounded losses
    out += [
        extreme_cost("X14|null|cost_fn=5", 5.0),
        fin("X14|null|fin_heavy_tail_clip", (1.0, 1.0), W.transition(2, 0.99)),
    ]
    return out


def arms(frac=0.2):
    b = {"risk": "brier", "frac": frac}
    return {
        "pprm": E.Cfg(**b),
        "HG": E.Cfg(gamma=0.99, gate_w=100, **b),
        "cost": E.Cfg(**{**b, "risk": "cost"}),
        "HG_arrived": E.Cfg(gamma=0.99, gate_w=100, release="arrived", **b),
        "HG_xcap_legacy": E.Cfg(gamma=0.99, gate_w=100, cap_mode="x", **b),
    }


if __name__ == "__main__":
    allsp = specs()
    df = St.run_grid(
        "e6_stress_main",
        allsp,
        arms(0.2),
        S=S,
        seed0=60000,
        qseed=6,
        note="14 stress experiments, frac .2",
    )
    # 12 very low label availability ; 13 hard budget exhaustion (null + harm worlds)
    low = [lw("X12|null"), lw("X12|concept2", regs=(R(), R("concept", 2.0)))]
    cf = {}
    for f in (0.002, 0.005, 0.01, 0.02):
        cf[f"HG|f{f}"] = E.Cfg(risk="brier", frac=f, gamma=0.99, gate_w=100)
        cf[f"pprm|f{f}"] = E.Cfg(risk="brier", frac=f)
    St.run_grid(
        "e6_stress_lowlabel", low, cf, S=S, seed0=61000, qseed=6, note="X12 very low labels"
    )
    hb = [lw("X13|null"), lw("X13|concept2", regs=(R(), R("concept", 2.0)))]
    cf = {}
    for B in (5, 10, 25, 100):
        cf[f"HG|bern_f0.5_B{B}"] = E.Cfg(
            risk="brier", frac=0.5, gamma=0.99, gate_w=100, budget=B
        )  # exhausts early on most paths
        cf[f"HG|const_B{B}"] = E.Cfg(
            risk="brier", frac=0.2, gamma=0.99, gate_w=100, budget=B, pacing="const"
        )
        cf[f"HG|remaining_B{B}"] = E.Cfg(
            risk="brier", frac=0.2, gamma=0.99, gate_w=100, budget=B, pacing="remaining"
        )
    St.run_grid(
        "e6_stress_hardbudget", hb, cf, S=S, seed0=62000, qseed=6, note="X13 hard budget exhaustion"
    )
    sm = St.summarise(df)
    sm.to_csv("outputs/gap_closure/e6_stress_main/summary_by_world.csv", index=False)
    print(sm[["config", "world", "n", "fa", "power", "role"]].round(3).to_string())
