"""Lane B D2: small Monte Carlo for split-clock (fast biased surrogate + slow gold) switching.

DEVELOPMENT CHECK ONLY. Not confirmatory. The model constants (T, Delta, delays, prices, B,
qualities, shifts) were fixed before the first run. Detector details (n_ref, n_cal_min, the lagged
reference, h calibration, post-promotion pacing) were revised after two smoke runs on the first
100 and 200 seeds of each evaluation cell; this forking path is disclosed in
docs/lane_b_burst_allocation/D2_split_clock_mechanism.md, section 6.

Model (one reversal, two policies):
  * rounds t = 0..T-1; candidate gain mu_t = +Delta for t < nu, -Delta for t >= nu,
    nu ~ Uniform{NU_LO..NU_HI}; null worlds have mu_t = 0 for all t and no shift;
  * gold label Z_t in {-1,+1}, P(Z_t=+1) = (1+mu_t)/2 (unbiased), delay d_g, price c_g;
  * fast label S_t = beta Z_t + b_t + sigma_f eta_t, eta_t ~ N(0,1), delay d_f, price c_f,
    b_t = b0 + delta_b 1{t >= nu}; sigma_f = beta / Phi^{-1}(q), so q is the sign agreement
    P(sign S = sign Z) at zero bias;
  * hard budget B, charged at request (pending labels count); at most one query per channel
    per round; switch cost k; A_0 = 0; one promotion and at most one rollback (no re-promotion);
  * promotion (0 -> 1) of every valid arm is gated by the same gold betting e-process with a
    constant stake fixed at query time, multiplied in release order (fixed delay => release
    order = query order). Fast labels never enter it.

Arms (identical B, delays, prices, k, alpha, and identical knowledge of Delta, beta, sigma_f):
  gold_only      gold at constant rate B/(c_g T); gold e-process promotion; gold CUSUM rollback.
  surrogate_only fast every round; promotes on a betting process over clip(S) as if it were
                 unbiased (INVALID: the invalid-promotion control); fast change-CUSUM rollback.
  cstar_r        D0's composition C*: stationary split (gold rate r, paired fast on gold rounds,
                 extra fast at the rate the remaining budget allows), gold e-process promotion,
                 fast rollback CUSUM on bias-corrected increments (S - b_hat_plus)/beta with
                 b_hat_plus a pooled paired-calibration upper confidence bound, plus a gold CUSUM
                 backstop. The best r on {0.15, 0.25, 0.35} per cell is reported (oracle-tuned).
  cstarchg_r     the same stationary split, but the fast detector is a standard change CUSUM
                 against a lagged fast reference mean (labels >= base_lag rounds old; no
                 calibration). The decisive standard
                 composition for the equivalence test.
  twophase_f     phase-dependent schedule: gold 0.6 + fast 0.5 per round before promotion (capped
                 at B/2); after promotion fast rate f in {0.25, 0.5, 1} and the remaining budget
                 paced evenly on gold; change CUSUM + gold backstop. Standard composition.
  adaptive_f     the D2 candidate: twophase_f + a fast-evidence-triggered gold burst (40 rounds
                 of gold, reserved in the pacing; bias re-calibration / verification) when the
                 fast change statistic reaches h/2.
  Every arm's CUSUM threshold h is calibrated to false-rollback <= 0.05 in a separate
  always-good world (calibrate_h); tuned families report the best member per cell by mean net
  cost on the evaluation seeds (oracle selection, equally generous to every tuned family).

Seeds: registry block lane_b_d2_split_clock_development (100900000-100919999);
seed id = 100900000 + cell_index*1000 + replicate. Common random numbers across arms.

Usage: python scripts/lane_b/split_clock_small.py [out.json] [--n 1000]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import asdict, dataclass, field, replace
from statistics import NormalDist

import numpy as np

SEED_BLOCK = (100900000, 100919999)
SEEDS_PER_CELL = 1000


@dataclass(frozen=True)
class Params:
    T: int = 600
    nu_lo: int = 250
    nu_hi: int = 400
    delta: float = 0.4
    beta: float = 1.0
    b0: float = 0.2
    d_f: int = 1
    d_g: int = 48
    c_g: float = 1.0
    c_f: float = 0.125
    B: float = 240.0
    alpha: float = 0.05
    lam_g: float = 0.36
    lam_s: float = 0.3
    h: float = 4.6
    k_switch: float = 2.0
    c_unit: float = 0.02
    n_ref: int = 40
    base_lag: int = 50
    n_cal_min: int = 30
    target_false_rollback: float = 0.05
    n_calib: int = 500


QUALITIES = (0.55, 0.65, 0.80)
SHIFTS = (
    ("none", 0.0),
    ("moderate", 0.5),
    ("large", 0.8),
)  # 0.5 = 1.25 beta Delta; 0.8 = 2 beta Delta


def cells() -> list[dict]:
    out = []
    for q in QUALITIES:
        for name, db in SHIFTS:
            out.append({"world": "reversal", "q": q, "shift": name, "delta_b": db})
    for q in QUALITIES:
        out.append({"world": "null", "q": q, "shift": "none", "delta_b": 0.0})
    for i, c in enumerate(out):
        c["index"] = i
    return out


def sigma_f_for(q: float, beta: float) -> float:
    return beta / NormalDist().inv_cdf(q)


@dataclass
class Env:
    mu: np.ndarray  # (N, T)
    Z: np.ndarray  # (N, T) in {-1, +1}
    S: np.ndarray  # (N, T)
    nu: np.ndarray  # (N,), T for null worlds
    sigma_f: float
    seeds: np.ndarray


def make_env(cell: dict, p: Params, n: int, seed_start: int | None = None) -> Env:
    start = SEED_BLOCK[0] + cell["index"] * SEEDS_PER_CELL if seed_start is None else seed_start
    seeds = np.arange(start, start + n, dtype=np.int64)
    if seed_start is None:
        assert seeds[-1] <= SEED_BLOCK[1] and n <= SEEDS_PER_CELL
    sf = sigma_f_for(cell["q"], p.beta)
    T = p.T
    mu = np.zeros((n, T))
    Z = np.zeros((n, T))
    S = np.zeros((n, T))
    nu = np.full(n, T, dtype=np.int64)
    tt = np.arange(T)
    for i, sd in enumerate(seeds):
        rng = np.random.default_rng(int(sd))
        u = rng.random(T)
        eta = rng.standard_normal(T)
        v = int(rng.integers(p.nu_lo, p.nu_hi + 1))
        if cell["world"] == "good":
            m = np.full(T, p.delta)
            b = np.full(T, p.b0)
        elif cell["world"] == "reversal":
            nu[i] = v
            m = np.where(tt < v, p.delta, -p.delta)
            b = p.b0 + cell["delta_b"] * (tt >= v)
        else:
            m = np.zeros(T)
            b = np.full(T, p.b0)
        z = np.where(u < (1.0 + m) / 2.0, 1.0, -1.0)
        mu[i] = m
        Z[i] = z
        S[i] = p.beta * z + b + sf * eta
    return Env(mu=mu, Z=Z, S=S, nu=nu, sigma_f=sf, seeds=seeds)


@dataclass(frozen=True)
class Spec:
    name: str
    gold_pre: float
    gold_post: float
    fast_pre: float
    fast_post: float
    pre_cap: float | None = None  # fraction of B spendable before promotion
    pair: bool = False  # fast query forced on every gold round (paired calibration)
    fast_detector: str | None = None  # "level" | "change" | None
    gold_backstop: bool = True
    promote_channel: str = "gold"  # "gold" (valid) | "fast" (invalid control)
    burst_len: int = 0
    burst_frac: float = 0.5
    post_paced: bool = (
        False  # post-promotion gold rate = budget left after fast + burst reserve, spread evenly
    )
    extra: dict = field(default_factory=dict)


def cstar_spec(r: float, p: Params, detector: str) -> Spec:
    fast = (p.B - r * p.T * (p.c_g + p.c_f)) / (p.c_f * p.T)
    fast = float(min(1.0, max(0.0, fast)))
    tag = "cstar" if detector == "level" else "cstarchg"
    return Spec(f"{tag}_{r:.2f}", r, r, fast, fast, pair=True, fast_detector=detector)


def arm_specs(p: Params) -> list[Spec]:
    specs = [
        Spec("gold_only", p.B / (p.c_g * p.T), p.B / (p.c_g * p.T), 0.0, 0.0),
        Spec(
            "surrogate_only",
            0.0,
            0.0,
            1.0,
            1.0,
            fast_detector="change",
            gold_backstop=False,
            promote_channel="fast",
        ),
    ]
    for r in (0.15, 0.25, 0.35):
        specs.append(cstar_spec(r, p, "level"))
    for r in (0.15, 0.25, 0.35):
        specs.append(cstar_spec(r, p, "change"))
    for f in POST_FAST:
        two = Spec(
            f"twophase_{f:.2f}",
            0.6,
            1.0,
            0.5,
            f,
            pre_cap=0.5,
            fast_detector="change",
            post_paced=True,
        )
        specs.append(two)
        specs.append(replace(two, name=f"adaptive_{f:.2f}", burst_len=40, burst_frac=0.5))
    return specs


POST_FAST = (0.25, 0.5, 1.0)
H_GRID = tuple(float(x) for x in np.arange(3.0, 14.01, 0.5))
CALIB_SEED_START = SEED_BLOCK[0] + 15000  # 100915000 + qi*1000 + i, i < n_calib (<= 1000)


def calibrate_h(spec: Spec, q: float, p: Params) -> tuple[float, float]:
    """Smallest h on H_GRID whose false-rollback rate in an always-good world is <= target.

    Uses a separate calibration world (candidate good for all T, bias b0, no shift) and seeds
    disjoint from every evaluation cell, so every arm is matched on false-rollback probability.
    """
    qi = QUALITIES.index(q)
    env = make_env(
        {"world": "good", "q": q, "delta_b": 0.0, "index": -1},
        p,
        p.n_calib,
        seed_start=CALIB_SEED_START + qi * 1000,
    )
    last = (H_GRID[-1], float("nan"))
    for h in H_GRID:
        o = simulate(env, spec, p, h)
        fr = float(o["rolled"].mean())
        last = (h, fr)
        if fr <= p.target_false_rollback:
            return h, fr
    return last


def simulate(env: Env, spec: Spec, p: Params, h: float | None = None) -> dict[str, np.ndarray]:
    h = p.h if h is None else h
    N, T = env.Z.shape
    Z, S, mu = env.Z, env.S, env.mu
    Qg = np.zeros((N, T), bool)
    Qf = np.zeros((N, T), bool)
    spent = np.zeros(N)
    acc_g = np.zeros(N)
    acc_f = np.zeros(N)
    promoted = np.zeros(N, bool)
    rolled = np.zeros(N, bool)
    blocked = np.zeros(N, bool)
    t_promo = np.full(N, -1)
    t_roll = np.full(N, -1)
    t_trig = np.full(N, -1)
    logW = np.zeros(N)
    Wg = np.zeros(N)
    Wf = np.zeros(N)
    cal_n = np.zeros(N)
    cal_s = np.zeros(N)
    cal_ss = np.zeros(N)
    base_n = np.zeros(N)
    base_s = np.zeros(N)
    gold_post = np.full(N, spec.gold_post)
    burst_left = np.zeros(N, dtype=np.int64)
    triggered = np.zeros(N, bool)
    regret = np.zeros(N)
    switches = np.zeros(N)
    A_prev = np.zeros(N, bool)
    coef_g = math.log((1 + p.delta) / (1 - p.delta))
    v_f = p.beta**2 * (1 - p.delta**2) + env.sigma_f**2  # Var(S | mu = +-Delta)
    v_mu = v_f / p.beta**2
    s_d = p.beta * p.delta  # designed downward shift of the change CUSUM (S units)
    thr = math.log(1 / p.alpha)
    for t in range(T):
        # ---- releases (start of round t) ----
        s = t - p.d_g
        if s >= 0:
            m = Qg[:, s]
            z = Z[:, s]
            if spec.promote_channel == "gold":
                logW[m] += np.log1p(p.lam_g * z[m])
            if spec.gold_backstop:
                Wg[m] = np.maximum(0.0, Wg[m] - z[m] * coef_g)
            if spec.pair:
                mm = m & Qf[:, s]
                r = S[mm, s] - p.beta * z[mm]
                cal_n[mm] += 1
                cal_s[mm] += r
                cal_ss[mm] += r * r
        s = t - p.d_f
        if s >= 0:
            m = Qf[:, s]
            x = S[:, s]
            if spec.promote_channel == "fast":
                logW[m] += np.log1p(p.lam_s * np.clip(x[m], -1.0, 1.0))
            if spec.fast_detector == "level":
                act = m & promoted & ~rolled & (cal_n >= p.n_cal_min)
                if act.any():
                    n_ = cal_n[act]
                    mean = cal_s[act] / n_
                    var = np.maximum(cal_ss[act] / n_ - mean**2, 1e-9)
                    bplus = mean + 1.645 * np.sqrt(var / n_)
                    xx = (x[act] - bplus) / p.beta
                    Wf[act] = np.maximum(0.0, Wf[act] - 2 * p.delta * xx / v_mu)
            elif spec.fast_detector == "change":
                act = m & promoted & ~rolled & (base_n >= p.n_ref)
                if act.any():
                    m0 = base_s[act] / base_n[act]
                    Wf[act] = np.maximum(0.0, Wf[act] + (s_d / v_f) * (m0 - x[act] - s_d / 2))
        if spec.fast_detector == "change":
            # lagged reference sample: fast labels from rounds <= t - base_lag (all long released)
            sl = t - p.base_lag
            if sl >= 0:
                mb = Qf[:, sl]
                base_n[mb] += 1
                base_s[mb] += S[mb, sl]
        # ---- decisions ----
        if spec.gold_backstop:
            blocked |= (~promoted) & (Wg >= h)
        newp = (~promoted) & (~blocked) & (logW >= thr)
        promoted |= newp
        t_promo[newp] = t
        if spec.post_paced and newp.any():
            t_rem = T - t
            left = p.B - spent[newp] - spec.fast_post * p.c_f * t_rem - spec.burst_len * p.c_g
            gold_post[newp] = np.clip(left / (p.c_g * t_rem), 0.0, 1.0)
        alarm = promoted & ~rolled & (Wf >= h)
        if spec.gold_backstop:
            alarm |= promoted & ~rolled & (Wg >= h)
        rolled |= alarm
        t_roll[alarm] = t
        if spec.burst_len > 0:
            trig = promoted & ~rolled & ~triggered & (Wf >= h * spec.burst_frac)
            triggered |= trig
            t_trig[trig] = t
            burst_left[trig] = spec.burst_len
        A = promoted & ~rolled
        # ---- queries (charged at request) ----
        live = ~rolled & ~blocked
        rg = np.where(promoted, gold_post, spec.gold_pre) * live
        rf = np.where(promoted, spec.fast_post, spec.fast_pre) * live
        cap = np.full(N, p.B)
        if spec.pre_cap is not None:
            cap = np.where(promoted, p.B, spec.pre_cap * p.B)
        acc_g += rg
        fire_g = acc_g >= 1.0
        acc_g[fire_g] -= 1.0
        want_g = (fire_g | (burst_left > 0)) & live
        ok_g = want_g & (spent + p.c_g <= cap + 1e-9)
        Qg[:, t] = ok_g
        spent += p.c_g * ok_g
        burst_left = np.maximum(0, burst_left - 1)
        acc_f += rf
        fire_f = acc_f >= 1.0
        acc_f[fire_f] -= 1.0
        want_f = fire_f.copy()
        if spec.pair:
            want_f |= ok_g
        want_f &= live
        ok_f = want_f & (spent + p.c_f <= cap + 1e-9)
        Qf[:, t] = ok_f
        spent += p.c_f * ok_f
        # ---- loss ----
        mt = mu[:, t]
        regret += np.maximum(mt, 0.0) - mt * A
        switches += A != A_prev
        A_prev = A
    net = regret + p.k_switch * switches + p.c_unit * spent
    return {
        "regret": regret,
        "switches": switches,
        "spent": spent,
        "net": net,
        "t_promo": t_promo,
        "t_roll": t_roll,
        "t_trig": t_trig,
        "promoted": promoted,
        "rolled": rolled,
        "Qg": Qg,
        "Qf": Qf,
    }


def summarise(env: Env, out: dict, world: str) -> dict:
    nu = env.nu
    prom = out["promoted"]
    res = {
        "net_mean": float(out["net"].mean()),
        "net_se": float(out["net"].std(ddof=1) / math.sqrt(len(nu))),
        "regret_mean": float(out["regret"].mean()),
        "spent_mean": float(out["spent"].mean()),
        "spent_max": float(out["spent"].max()),
        "p_promoted": float(prom.mean()),
    }
    if world == "reversal":
        pre = prom & (out["t_promo"] < nu)
        res["promo_time_mean"] = float(out["t_promo"][prom].mean()) if prom.any() else float("nan")
        unsafe = out["rolled"] & (out["t_roll"] < nu)
        res["p_unsafe_rollback"] = float(unsafe.mean())
        caught = pre & out["rolled"] & (out["t_roll"] >= nu)
        res["rollback_delay_mean"] = (
            float((out["t_roll"][caught] - nu[caught]).mean()) if caught.any() else float("nan")
        )
        res["p_missed_rollback"] = float((pre & ~out["rolled"]).sum() / max(1, pre.sum()))
    return res


def run(n: int = SEEDS_PER_CELL, p: Params | None = None) -> dict:
    p = p or Params()
    specs = arm_specs(p)
    hcache: dict = {}
    results = []
    for cell in cells():
        env = make_env(cell, p, n)
        row = {"cell": cell, "sigma_f": env.sigma_f, "arms": {}}
        for spec in specs:
            key = (spec.name, cell["q"])
            if key not in hcache:
                hcache[key] = calibrate_h(spec, cell["q"], p)
            h, fr = hcache[key]
            row["arms"][spec.name] = summarise(env, simulate(env, spec, p, h), cell["world"])
            row["arms"][spec.name].update(h=h, calib_false_rollback=fr)
        for tag in ("cstar", "cstarchg", "twophase", "adaptive"):
            cand = {k: v for k, v in row["arms"].items() if k.startswith(tag + "_")}
            best = min(cand, key=lambda k: cand[k]["net_mean"])
            row["arms"][tag + "_best"] = dict(cand[best], chosen=best)
        results.append(row)
    return {"params": asdict(p), "seed_block": SEED_BLOCK, "n_per_cell": n, "cells": results}


def _fmt(rows: list[dict]) -> str:
    arms = [
        "gold_only",
        "surrogate_only",
        "cstar_best",
        "cstarchg_best",
        "twophase_best",
        "adaptive_best",
    ]
    lines = []
    for r in rows:
        c = r["cell"]
        lines.append(
            f"\n[{c['index']}] {c['world']} q={c['q']} shift={c['shift']} (sigma_f={r['sigma_f']:.2f})"
        )
        for a in arms:
            s = r["arms"][a]
            extra = (
                f" ({s['chosen'].split('_')[-1]},h{s['h']:g})"
                if "chosen" in s
                else f" (h{s['h']:g})"
            )
            if c["world"] == "reversal":
                lines.append(
                    f"  {a:15s}{extra:16s} net {s['net_mean']:7.2f}±{s['net_se']:.2f} promo_t {s['promo_time_mean']:6.1f}"
                    f" unsafe {s['p_unsafe_rollback']:.3f} delay {s['rollback_delay_mean']:6.1f}"
                    f" missed {s['p_missed_rollback']:.3f} spent {s['spent_mean']:6.1f}"
                )
            else:
                lines.append(
                    f"  {a:15s}{extra:16s} false_promotion {s['p_promoted']:.3f} spent {s['spent_mean']:6.1f}"
                )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?")
    ap.add_argument("--n", type=int, default=SEEDS_PER_CELL)
    a = ap.parse_args(argv)
    t0 = time.time()
    res = run(a.n)
    res["runtime_s"] = time.time() - t0
    print(_fmt(res["cells"]))
    print(f"\nruntime {res['runtime_s']:.1f}s")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
