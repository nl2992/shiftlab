"""S06: budget-paced delayed query allocation under a hard pathwise budget. Parent HG."""

from shiftlab.gap import engine as E
from shiftlab.gap import pools as P
from shiftlab.gap import store as St
from shiftlab.gap import worlds as W

R = W.Regime


def spec(T, onset, shape, delay):
    t0 = int(onset * T)
    kw = {"length": int(0.2 * T), "period": int(0.3 * T), "ramp": int(0.1 * T)}
    w = W.LogitWorld(regimes=(R(), R("concept", 2.0)), T=T, t0=0, name=f"T{T}")

    def make(S, seed, w=w, shape=shape, t0=t0, kw=kw):
        return P._g_sched(w, shape, S, seed, t0, **kw)

    return St.WorldSpec(f"S06|T{T}|{shape}|on{onset}", make, delay, group=f"T{T}")


def pace_cfgs(frac, T):
    B = round(frac * T)
    base = {"risk": "brier", "gamma": 0.99, "gate_w": 100, "frac": frac}
    base["pace_floor"] = (
        0.5  # v2: corrected propensity floors (v1 confounded pacing with a frac/4 cap floor)
    )
    c = {
        "bernoulli": E.Cfg(**{k: v for k, v in base.items() if k != "pace_floor"}),
        "hard_bern": E.Cfg(budget=B, **{k: v for k, v in base.items() if k != "pace_floor"}),
    }
    for pc in ("const", "remaining", "info_value", "reserve", "two_stage"):
        c[pc] = E.Cfg(budget=B, pacing=pc, alloc="uniform", **base)
    c["growth_pace"] = E.Cfg(budget=B, pacing="growth_pace", alloc="growth", **base)
    return c


if __name__ == "__main__":
    import pandas as pd

    out = []
    for delay in (0, 5, 20):
        for frac in (0.05, 0.10, 0.20):
            specs = [
                spec(2000, on, sh, delay)
                for on in (0.2, 0.5, 0.8)
                for sh in ("abrupt", "gradual", "transient", "recurrent")
            ]
            specs.append(
                St.WorldSpec(
                    "S06|T2000|null",
                    lambda S, sd: P.logit_sched_spec("n", "none", 0.0).make(S, sd),
                    delay,
                    group="null",
                )
            )
            df = St.run_grid(
                f"e5b_s06_T2000_d{delay}_f{frac}",
                specs,
                pace_cfgs(frac, 2000),
                S=100,
                seed0=50000,
                qseed=5,
                note=f"S06 delay {delay} frac {frac}",
            )
            df["delay_cfg"], df["frac_cfg"] = delay, frac
            out.append(df)
            print("done", delay, frac, flush=True)
    for T in (100, 500):
        for frac in (0.05, 0.10, 0.20):
            specs = [
                spec(T, on, sh, 5 if T > 100 else 2)
                for on in (0.5,)
                for sh in ("abrupt", "transient")
            ]
            df = St.run_grid(
                f"e5b_s06_T{T}_f{frac}",
                specs,
                pace_cfgs(frac, T),
                S=100,
                seed0=55000,
                qseed=5,
                note=f"S06 T={T}",
            )
            df["delay_cfg"], df["frac_cfg"] = 5, frac
            out.append(df)
    allp = pd.concat(out, ignore_index=True)
    allp.to_parquet("outputs/gap_closure/e5b_s06_all_perseed.parquet", index=False)
