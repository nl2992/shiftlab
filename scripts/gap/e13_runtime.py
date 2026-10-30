"""Phase 10: runtime / memory scaling on one machine, repeated runs. Run only when nothing else is executing.
cold = first call in the process for that case (includes import / first-touch effects); warm = median of repeats."""

import gc
import itertools
import platform
import subprocess
import sys
import time
import tracemalloc

import numpy as np
import pandas as pd

from shiftlab.dive.rpoq_exact import Instance
from shiftlab.dive.rpoq_next.approx_dp import certify
from shiftlab.gap import dist_tests as DT
from shiftlab.gap import engine as E
from shiftlab.gap import q2
from shiftlab.gap import worlds as W
from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

REPS = 5
R = W.Regime


def stream(T, S, seed=1):
    w = W.LogitWorld(regimes=(R(), R("concept", 2.0)), T=T, t0=0)
    z = np.repeat(W.scheduled_regimes("abrupt", T, int(0.4 * T))[None], S, 0)
    t0 = time.perf_counter()
    st = W.make_stream(w, S, seed, z=z)
    return st, time.perf_counter() - t0


def engine_methods(frac):
    b = {"risk": "brier", "frac": frac}
    return {
        "pprm_parent(engine)": lambda st: E.run(st, E.Cfg(**b), delay=5),
        "HG": lambda st: E.run(st, E.Cfg(gamma=0.99, gate_w=100, **b), delay=5),
        "discount_only": lambda st: E.run(st, E.Cfg(gamma=0.99, **b), delay=5),
        "costgate_only": lambda st: E.run(st, E.Cfg(gate_w=100, **b), delay=5),
        "multiwindow(3)": lambda st: E.run_mixture(
            st, [E.Cfg(gamma=g_, gate_w=100, **b) for g_ in (1.0, 0.99, 0.95)], delay=5
        ),
        "HG_growth_alloc": lambda st: E.run(
            st, E.Cfg(gamma=0.99, gate_w=100, alloc="growth", **b), delay=5
        ),
        "HG_robustmix": lambda st: E.run(
            st, E.Cfg(gamma=0.99, gate_w=100, alloc="mix", mix=(0.5, 0.5, 0.0), mix_mode="conservative", **b), delay=5
        ),
        "cost_discount": lambda st: E.run(st, E.Cfg(risk="cost", frac=frac, gamma=0.99), delay=5),
        "HG_lrv100": lambda st: E.run(
            st, E.Cfg(gamma=0.99, gate_w=100, lrv=True, lrv_lags=100, **b), delay=5
        ),
    }


def legacy_methods(frac):
    kw = {"frac": frac, "delay": 5, "lseed": 1}
    return {
        "pprm_tight(legacy cumsum)": lambda sim: det.pprm_tight(sim, tol=0.0, **kw),
        "HG(legacy cumsum)": lambda sim: det.fix_brier(sim, tol=0.0, gamma=0.99, gate_w=100, **kw),
        "page_hinkley": lambda sim: det.page_hinkley(sim, delta=0.05, **kw),
        "cusum": lambda sim: det.cusum(sim, slack=0.25, **kw),
    }


def timeit(fn, arg, reps=REPS):
    """Clean wall-clock timing (no tracing), then ONE separate traced run for the numpy allocation peak."""
    ts = []
    for _ in range(reps):
        gc.collect()
        t0 = time.perf_counter()
        fn(arg)
        ts.append(time.perf_counter() - t0)
    gc.collect()
    tracemalloc.start()
    fn(arg)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return ts[0], float(np.median(ts[1:])), float(np.std(ts[1:])), peak / 1e6


def main():
    rows = []
    hw = {
        "machine": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "nproc": __import__("os").cpu_count(),
    }
    # (1) horizon x streams x label budget for e-process engines + legacy detectors + classical
    for T, S, frac in [
        (500, 100, 0.1),
        (2000, 100, 0.1),
        (8000, 100, 0.1),
        (2000, 1, 0.1),
        (2000, 1000, 0.1),
        (2000, 100, 0.01),
        (2000, 100, 0.5),
    ]:
        st, gen = stream(T, S)
        sim = g.simulate(
            g.World(kind="concept", delta=2.0, shape="abrupt", t0=int(0.4 * T), T=T), S, 5
        )
        t0 = time.perf_counter()
        E.ensure_stream(sim)
        prep = time.perf_counter() - t0
        for name, fn in {**engine_methods(frac)}.items():
            cold, warm, sd, peak = timeit(fn, st)
            rows.append(
                {
                    "case": "detector",
                    "method": name,
                    "T": T,
                    "S": S,
                    "frac": frac,
                    "cold_s": cold,
                    "warm_s": warm,
                    "warm_sd_s": sd,
                    "us_per_obs": 1e6 * warm / (T * S),
                    "tracemalloc_peak_mb": peak,
                    "gen_s": gen,
                    "prep_s": 0.0,
                }
            )
        for name, fn in legacy_methods(frac).items():
            cold, warm, sd, peak = timeit(fn, sim)
            rows.append(
                {
                    "case": "detector",
                    "method": name,
                    "T": T,
                    "S": S,
                    "frac": frac,
                    "cold_s": cold,
                    "warm_s": warm,
                    "warm_sd_s": sd,
                    "us_per_obs": 1e6 * warm / (T * S),
                    "tracemalloc_peak_mb": peak,
                    "gen_s": gen,
                    "prep_s": prep,
                }
            )
        print("detector case", T, S, frac, flush=True)
    # (2) number of candidate models x certification method
    for K in (2, 5, 10):
        stq = q2.make(q2.Q2World(K=K, gap="moderate"), 50, 3)
        for m in ("paired_e_bonf", "cams", "seqmcs", "S09d_budget"):
            cold, warm, sd, peak = timeit(lambda s, m=m: q2.run(s, m, frac=0.1, delay=5), stq)
            rows.append(
                {
                    "case": "certification",
                    "method": m,
                    "T": 2000,
                    "S": 50,
                    "K": K,
                    "cold_s": cold,
                    "warm_s": warm,
                    "warm_sd_s": sd,
                    "us_per_obs": 1e6 * warm / (2000 * 50),
                    "tracemalloc_peak_mb": peak,
                }
            )
    # (3) streaming drift tests: feature dimension
    for d, wlen in itertools.product((5, 20, 100), (128,)):
        rng = np.random.default_rng(0)
        ref, win = rng.standard_normal((512, d)), rng.standard_normal((wlen, d))
        sw = np.zeros(d)
        sw[0] = 1.0
        for name in DT.METHODS:
            ts, pk = [], []
            for _ in range(REPS * 4):
                t0_ = time.perf_counter()
                DT.METHODS[name](ref, win, rng, score_w=sw)
                ts.append(time.perf_counter() - t0_)
            pk.append(DT.time_method(name, ref, win, rng, sw)[2])  # one traced run, memory only
            rows.append(
                {
                    "case": "drift_test",
                    "method": name,
                    "d": d,
                    "window": wlen,
                    "cold_s": ts[0],
                    "warm_s": float(np.median(ts[1:])),
                    "warm_sd_s": float(np.std(ts[1:])),
                    "tracemalloc_peak_mb": max(pk) / 1e6,
                    "us_per_obs": 1e6 * float(np.median(ts[1:])) / wlen,
                }
            )
    # (4) approximate DP (exact RPOQ solver snapping) vs horizon
    for hz in (6, 8, 10):
        inst = Instance(horizon=hz, delay=2, budget=4)
        ts = []
        for _ in range(3):
            t0 = time.perf_counter()
            certify(inst, delta=0.25)
            ts.append(time.perf_counter() - t0)
        rows.append(
            {
                "case": "approx_dp",
                "method": "approx_dp(delta=.25)",
                "T": hz,
                "cold_s": ts[0],
                "warm_s": float(np.median(ts[1:])),
                "warm_sd_s": float(np.std(ts[1:])),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv("outputs/gap_closure/RUNTIME_SCALING.csv", index=False)
    mem = df[["case", "method", "T", "S", "K", "d", "window", "frac", "tracemalloc_peak_mb"]].copy()
    # (5) clean-process peak RSS for the horizon cases
    rss = []
    code = (
        "import resource,sys,numpy as np\nfrom shiftlab.gap import engine as E, worlds as W\n"
        "T,S,m=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]\nR=W.Regime\nw=W.LogitWorld(regimes=(R(),R('concept',2.0)),T=T,t0=0)\n"
        "z=np.repeat(W.scheduled_regimes('abrupt',T,int(.4*T))[None],S,0)\nst=W.make_stream(w,S,1,z=z)\n"
        "b=dict(risk='brier',frac=.1)\ncfg=E.Cfg(**b) if m=='pprm' else E.Cfg(gamma=.99,gate_w=100,**b)\nE.run(st,cfg,delay=5)\n"
        "print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)\n"
    )
    for T, S in [(500, 100), (2000, 100), (8000, 100), (2000, 1), (2000, 1000)]:
        for m in ("pprm", "HG"):
            out = subprocess.run(
                [sys.executable, "-I", "-c", code, str(T), str(S), m],
                capture_output=True,
                text=True,
                env={**__import__("os").environ, "PYTHONPATH": "src"},
            )
            rss.append(
                {
                    "method": m,
                    "T": T,
                    "S": S,
                    "peak_rss_mb": float(out.stdout.strip().split()[-1])
                    if out.returncode == 0
                    else np.nan,
                }
            )
    pd.DataFrame(rss).to_csv("outputs/gap_closure/MEMORY_SCALING.csv", index=False)
    mem.to_csv("outputs/gap_closure/MEMORY_TRACEMALLOC.csv", index=False)
    pd.Series(hw).to_json("outputs/gap_closure/runtime_hardware.json")
    print(hw)


if __name__ == "__main__":
    main()
