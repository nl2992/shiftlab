"""B1: does paired-benefit certification improve net switching cost?

Runs the registered protocol docs/promising_directions/protocols/B1-certified-switching.md
(self-contained vectorised numpy simulator; development study, not confirmatory evidence).
Design notes are in docs/promising_directions/results/b1/IMPLEMENTATION_NOTES.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.stats import beta as beta_dist

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/promising_directions/protocols/B1-certified-switching.md"
PROTOCOL_SHA256 = "98f85250a95ae6e31857760ca33f2ebe1dc0c042762469b7d8f84cd557a82757"
PROTOCOL_B2 = ROOT / "docs/promising_directions/protocols/B2-propensity-cap.md"
PROTOCOL_B2_SHA256 = "533a529ddda537ce8b925fdaf6b0b503cce46797ade2c7ca0d5a9b95202b6844"
DEFAULT_OUT = ROOT / "docs/promising_directions/results/b1"

WORLDS = ("W1", "W2", "W3", "W4")
BUDGETS = (200, 400)
SWITCH_COSTS = (5, 20)
POLICIES = ("P0", "P1", "P2", "P3", "P4", "P4w", "P5")  # P4w is exploratory, not registered
B2_POLICIES = ("P0", "P1", "P2", "P3", "P3b", "P5")  # --b2: P3b added, P4/P4w dropped
SIMPLE = ("P0", "P1", "P2")
BOOT = 2000


@dataclass(frozen=True)
class Params:
    T: int = 2000
    delay: int = 5
    cq: float = 0.05
    alpha: float = 0.05
    pmin: float = 0.05
    tau: int = 600
    hazard_mean: float = 150.0  # declared persistence, also mean of W3 reversal time R
    eps: float = 0.05
    base_err: float = 0.10
    gamma: float = 0.99  # discount for bet-selection statistics only
    n0: float = 10.0  # pseudo-observations in the bet statistics
    s2_prior: float = 1.0
    kelly_cap: float = 3.0
    prior_rate: float = 0.25  # prior disagreement rate used by the pacer
    prior_w: float = 20.0
    lb_step: float = 0.01
    lb_M: int = 31
    lb_offset: int = 150
    lb_K: int = 10


# regime id -> (error f0, error f1). Disagreement rate is DELTA in every regime.
DELTA = 0.25
REGIMES = {
    0: (0.10, 0.20),  # pre-change
    1: (0.30, 0.12),  # W1 / W3 post-change
    2: (0.30, 0.35),  # W2 post-change
    3: (0.10, 0.30),  # W3 after reversal
    4: (0.15, 0.15),  # exact null (E[D] = 0), used by tests only
}
BEST_MODEL = {0: 0, 1: 1, 2: 0, 3: 0, 4: 0}


def joint_probs(e0: float, e1: float, delta: float = DELTA) -> tuple[float, float, float, float]:
    """(both wrong, only f0 wrong, only f1 wrong, neither) with P(exactly one wrong) = delta."""
    both = (e0 + e1 - delta) / 2
    p10, p01 = e0 - both, e1 - both
    p00 = 1 - e0 - e1 + both
    if min(both, p10, p01, p00) < -1e-12:
        raise ValueError(f"infeasible joint law for e0={e0}, e1={e1}, delta={delta}")
    return both, p10, p01, p00


def regime_paths(
    world: str, p: Params, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluator-side regime id (T, n) and reversal time R (n,)."""
    t = np.arange(p.T)[:, None]
    reg = np.zeros((p.T, n), dtype=np.int8)
    reversal = np.full(n, -1)
    post = t >= p.tau
    if world == "W1":
        reg = np.where(post, 1, 0).astype(np.int8)
    elif world == "W2":
        reg = np.where(post, 2, 0).astype(np.int8)
    elif world == "W3":
        reversal = rng.geometric(1.0 / p.hazard_mean, size=n)
        reg = np.where(post, np.where(t >= p.tau + reversal[None, :], 3, 1), 0).astype(np.int8)
    elif world == "W4":
        pass
    elif world == "NULL":
        reg = np.full((p.T, n), 4, dtype=np.int8)
    else:
        raise ValueError(world)
    return np.broadcast_to(reg, (p.T, n)).copy(), reversal


def draw_losses(reg: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Realised 0/1 losses (l0, l1) from the per-regime joint law."""
    c1 = np.zeros(max(REGIMES) + 1)
    c2 = np.zeros_like(c1)
    c3 = np.zeros_like(c1)
    for rid, (e0, e1) in REGIMES.items():
        both, p10, p01, _ = joint_probs(e0, e1)
        c1[rid], c2[rid], c3[rid] = both, both + p10, both + p10 + p01
    v = rng.random(reg.shape)
    l0 = v < c2[reg]
    l1 = (v < c1[reg]) | ((v >= c2[reg]) & (v < c3[reg]))
    return l0.astype(np.int8), l1.astype(np.int8)


def make_stream(world: str, p: Params, n: int, seed_base: int, world_index: int) -> dict:
    ss = np.random.SeedSequence([seed_base, world_index])
    r_reg, r_loss, r_u = (np.random.default_rng(s) for s in ss.spawn(3))
    reg, reversal = regime_paths(world, p, n, r_reg)
    l0, l1 = draw_losses(reg, r_loss)
    return {"l0": l0, "l1": l1, "u": r_u.random((p.T, n)), "regime": reg, "reversal": reversal}


def bet_from_stats(s1, s2, cnt, p: Params, kelly: bool) -> np.ndarray:
    mu = s1 / (cnt + p.n0)
    var = (s2 + p.n0 * p.s2_prior) / (cnt + p.n0)
    return mu / (var if kelly else var + mu * mu)


class Cert:
    """P3 / P4 / P4w: disagreement-only IPW paired e-process with delayed, frozen bets."""

    def __init__(self, n, budget, cs, kind, p: Params, trace=False):
        self.n, self.kind, self.p, self.cs, self.budget = n, kind, p, cs, budget
        self.dep = np.zeros(n, dtype=np.int8)
        self.rem = np.full(n, budget)
        self.seg = np.zeros(n, dtype=np.int64)
        self.logw = np.zeros(n)
        self.s1, self.s2, self.cnt = np.zeros(n), np.zeros(n), np.zeros(n)
        self.xbuf, self.lbuf = np.zeros((p.delay, n)), np.zeros((p.delay, n))
        self.queries = np.zeros(n, dtype=np.int64)
        self.switches = np.zeros(n, dtype=np.int64)
        self.rollbacks = np.zeros(n, dtype=np.int64)
        self.t_prom = np.full(n, np.nan)
        self.loss = np.zeros(n)
        self.k = 0 if kind in ("P3", "P3b") else (1 if kind == "P4" else p.lb_K)
        if self.k:
            self.mgrid = np.arange(p.lb_M) * p.lb_step
            self.offs = np.arange(self.k) * p.lb_offset
            self.lbw = np.zeros((n, self.k, p.lb_M))
            self.lb_thr = math.log(self.k / p.alpha)
        self.thr = math.log(1 / p.alpha)
        self.tr = (
            {k: np.zeros((p.T, n)) for k in ("dep", "ask", "x", "lam", "logw", "q")}
            if trace
            else None
        )

    def lb_value(self) -> np.ndarray:
        rej = self.lbw >= self.lb_thr
        c = rej.sum(2)
        return np.where(c > 0, (c - 1) * self.p.lb_step, 0.0).max(1)

    def step(self, t, l0t, l1t, dis, u, ndis):
        p = self.p
        self.loss += np.where(self.dep == 0, l0t, l1t)
        dep_t = self.dep.copy()
        slot = t % p.delay
        # issue: query decision and frozen bet use only information released by t - delay - 1
        rate = (ndis + p.prior_rate * p.prior_w) / (t + p.prior_w)
        q = np.clip(self.rem / np.maximum(rate * (p.T - t), 1e-9), p.pmin, 1.0)
        q = np.where(self.rem > 0, q, 0.0)
        ask = dis & (u < q)
        x = np.where(ask, (l0t - l1t) / np.where(q > 0, q, 1.0), 0.0)
        self.rem = self.rem - ask
        self.queries += ask
        # P3b (B2): per-event cap q_t/2 with q_t the propensity issued for this event
        cap = q / 2 if self.kind == "P3b" else p.pmin / 2
        lam = np.clip(bet_from_stats(self.s1, self.s2, self.cnt, p, kelly=False), 0, cap)
        # release: label of event s = t - delay becomes usable now
        s = t - p.delay
        sgn = np.where(self.dep == 0, 1.0, -1.0)
        if s >= 0:
            xo, lo = self.xbuf[slot], self.lbuf[slot]
            live = s >= self.seg
            y = sgn * xo
            self.logw += np.where(live, np.log1p(lo * y), 0.0)
            self.s1 = np.where(live, p.gamma * self.s1 + y, self.s1)
            self.s2 = np.where(live, p.gamma * self.s2 + y * y, self.s2)
            self.cnt = np.where(live, p.gamma * self.cnt + 1.0, self.cnt)
            if self.k:
                act = (s >= self.seg[:, None] + self.offs[None, :]) & live[:, None]
                inc = np.log1p(lo[:, None, None] * (xo[:, None, None] - self.mgrid[None, None, :]))
                self.lbw += np.where(act[:, :, None] & (self.dep == 0)[:, None, None], inc, 0.0)
        self.xbuf[slot], self.lbuf[slot] = x, lam
        if self.tr is not None:
            for key, val in (("dep", dep_t), ("ask", ask), ("x", x), ("lam", lam), ("q", q)):
                self.tr[key][t] = val
            self.tr["logw"][t] = self.logw
        # decide (effective from t + 1)
        cand = self.logw >= self.thr
        if self.k:
            mhat = min(p.hazard_mean, p.T - 1 - t)
            cand = cand & ((self.dep == 1) | (self.lb_value() * mhat > self.cs))
        promo = cand & (self.dep == 0)
        self.t_prom = np.where(promo & np.isnan(self.t_prom), t + 1, self.t_prom)
        self.rollbacks += cand & (self.dep == 1)
        self.switches += cand
        self.dep = np.where(cand, 1 - self.dep, self.dep).astype(np.int8)
        self.seg = np.where(cand, t + 1, self.seg)
        self.logw = np.where(cand, 0.0, self.logw)
        for name in ("s1", "s2", "cnt"):
            setattr(self, name, np.where(cand, 0.0, getattr(self, name)))
        if self.k:
            self.lbw[cand] = 0.0


class Alarm:
    """P2: uniform querying, discounted-Kelly cost-null e-process on incumbent loss."""

    def __init__(self, n, budget, p: Params):
        self.n, self.p, self.budget = n, p, budget
        self.q = budget / p.T
        self.dep = np.zeros(n, dtype=np.int8)
        self.rem = np.full(n, budget)
        self.logw = np.zeros(n)
        self.s1, self.s2, self.cnt = np.zeros(n), np.zeros(n), np.zeros(n)
        self.xbuf, self.lbuf = np.zeros((p.delay, n)), np.zeros((p.delay, n))
        self.queries = np.zeros(n, dtype=np.int64)
        self.t_alarm = np.full(n, np.nan)
        self.loss = np.zeros(n)
        self.nominal = p.base_err + p.eps
        self.thr = math.log(1 / p.alpha)
        self.seg = np.zeros(n, dtype=np.int64)

    def step(self, t, l0t, l1t, u):
        p = self.p
        self.loss += np.where(self.dep == 0, l0t, l1t)
        slot = t % p.delay
        active = (self.dep == 0) & (self.rem > 0)
        ask = active & (u < self.q)
        x = np.where(active, ask * l0t / self.q - self.nominal, 0.0)
        self.rem = self.rem - ask
        self.queries += ask
        lam = np.clip(bet_from_stats(self.s1, self.s2, self.cnt, p, kelly=True), 0, p.kelly_cap)
        s = t - p.delay
        if s >= 0:
            xo, lo = self.xbuf[slot], self.lbuf[slot]
            live = (self.dep == 0) & (s >= self.seg)
            self.logw += np.where(live, np.log1p(lo * xo), 0.0)
            self.s1 = np.where(live, p.gamma * self.s1 + xo, self.s1)
            self.s2 = np.where(live, p.gamma * self.s2 + xo * xo, self.s2)
            self.cnt = np.where(live, p.gamma * self.cnt + 1.0, self.cnt)
        self.xbuf[slot], self.lbuf[slot] = x, lam
        fire = (self.dep == 0) & (self.logw >= self.thr)
        self.t_alarm = np.where(fire & np.isnan(self.t_alarm), t + 1, self.t_alarm)
        self.dep = np.where(fire, 1, self.dep).astype(np.int8)


def run_policies(l0, l1, u, budget, cs_list, p: Params, trace=False, b2=False) -> dict:
    """Policies see only (l0, l1) through query decisions, the free agreement indicator and u."""
    t_len, n = l0.shape
    dis_all = l0 != l1
    p2 = Alarm(n, budget, p)
    p3 = Cert(n, budget, 0, "P3", p, trace=trace)
    p3b = Cert(n, budget, 0, "P3b", p, trace=trace) if b2 else None
    p4 = {} if b2 else {cs: Cert(n, budget, cs, "P4", p) for cs in cs_list}
    p4w = {} if b2 else {cs: Cert(n, budget, cs, "P4w", p) for cs in cs_list}
    ndis = np.zeros(n)
    for t in range(t_len):
        p2.step(t, l0[t], l1[t], u[t])
        for pol in (p3, *([p3b] if b2 else []), *p4.values(), *p4w.values()):
            pol.step(t, l0[t], l1[t], dis_all[t], u[t], ndis)
        ndis = ndis + dis_all[t]
    out = {"P3": cert_out(p3), "P2": alarm_out(p2), "_p3_obj": p3}
    out["P4"] = {cs: cert_out(v) for cs, v in p4.items()}
    out["P4w"] = {cs: cert_out(v) for cs, v in p4w.items()}
    if b2:
        out["P3b"] = cert_out(p3b)
        out["_p3b_obj"] = p3b
    return out


def cert_out(c: Cert) -> dict:
    return {
        "loss": c.loss,
        "queries": c.queries,
        "switches": c.switches,
        "rollbacks": c.rollbacks,
        "t_prom": c.t_prom,
    }


def alarm_out(a: Alarm) -> dict:
    n = a.n
    return {
        "loss": a.loss,
        "queries": a.queries,
        "switches": (~np.isnan(a.t_alarm)).astype(np.int64),
        "rollbacks": np.zeros(n, dtype=np.int64),
        "t_prom": a.t_alarm,
    }


def oracle_out(regime: np.ndarray, l0, l1) -> dict:
    best_tab = np.array([BEST_MODEL[k] for k in sorted(BEST_MODEL)])
    best = best_tab[regime]
    loss = np.where(best == 0, l0, l1).sum(0).astype(float)
    sw = (best[1:] != best[:-1]).sum(0) + (best[0] != 0)
    n = l0.shape[1]
    return {
        "loss": loss,
        "queries": np.zeros(n, dtype=np.int64),
        "switches": sw.astype(np.int64),
        "rollbacks": np.zeros(n, dtype=np.int64),
        "t_prom": np.full(n, np.nan),
    }


def simple_out(l0, l1) -> tuple[dict, dict]:
    n = l0.shape[1]
    z = np.zeros(n, dtype=np.int64)
    nan = np.full(n, np.nan)
    p0 = {"loss": l0.sum(0).astype(float), "queries": z, "switches": z, "rollbacks": z}
    p1 = {"loss": l1.sum(0).astype(float), "queries": z, "switches": z + 1, "rollbacks": z}
    p0["t_prom"], p1["t_prom"] = nan, nan
    return p0, p1


def run_world_budget(args: tuple) -> dict:
    """One (world, B) task: all policies, for every switch cost."""
    world, budget, n, seed_base, p, b2 = args
    t0 = time.time()
    s = make_stream(world, p, n, seed_base, WORLDS.index(world))
    res = run_policies(s["l0"], s["l1"], s["u"], budget, SWITCH_COSTS, p, b2=b2)
    p0, p1 = simple_out(s["l0"], s["l1"])
    p5 = oracle_out(s["regime"], s["l0"], s["l1"])
    out = {}
    for cs in SWITCH_COSTS:
        pols = {"P0": p0, "P1": p1, "P2": res["P2"], "P3": res["P3"]}
        if b2:
            pols["P3b"] = res["P3b"]
        else:
            pols["P4"], pols["P4w"] = res["P4"][cs], res["P4w"][cs]
        pols["P5"] = p5
        out[(world, budget, cs)] = {}
        for name, d in pols.items():
            cost = d["loss"] + p.cq * d["queries"] + cs * d["switches"]
            out[(world, budget, cs)][name] = {
                "cost": cost,
                "loss": d["loss"],
                "queries": d["queries"],
                "switches": d["switches"],
                "rollbacks": d["rollbacks"],
                "t_prom": d["t_prom"],
                "budget_violation": (d["queries"] > budget).astype(np.int64),
            }
    out["_seconds"] = time.time() - t0
    return out


def clopper_pearson_upper(k: int, n: int, level: float = 0.95) -> float:
    return 1.0 if k >= n else float(beta_dist.ppf(level, k + 1, n - k))


def clopper_pearson_lower(k: int, n: int, level: float = 0.95) -> float:
    return 0.0 if k == 0 else float(beta_dist.ppf(1 - level, k, n - k + 1))


def boot_ci(diff: np.ndarray, idx: np.ndarray) -> dict:
    m = diff[idx].mean(1)
    return {
        "mean": float(diff.mean()),
        "lo": float(np.percentile(m, 2.5)),
        "hi": float(np.percentile(m, 97.5)),
    }


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, list | tuple):
        return [jsonable(v) for v in o]
    if isinstance(o, np.generic):
        return jsonable(o.item())
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def policy_stats(d: dict, world: str, n: int) -> dict:
    tp = d["t_prom"]
    promoted = ~np.isnan(tp)
    k = int(promoted.sum())
    out = {
        "mean_cost": float(d["cost"].mean()),
        "mean_deployment_loss": float(d["loss"].mean()),
        "mean_labels": float(d["queries"].mean()),
        "mean_switches": float(d["switches"].mean()),
        "mean_rollbacks": float(d["rollbacks"].mean()),
        "budget_violations": int(d["budget_violation"].sum()),
        "promotion_rate": k / n,
        "mean_time_to_promotion": float(tp[promoted].mean()) if k else None,
    }
    if world in ("W2", "W4"):
        out["false_promotion_rate"] = k / n
        out["false_promotion_cp95_upper"] = clopper_pearson_upper(k, n)
        out["false_promotion_cp95_lower"] = clopper_pearson_lower(k, n)
    return out


def analyse(results: dict, n: int, seed_base: int, p: Params) -> dict:
    rng = np.random.default_rng(seed_base + 7)
    idx = rng.integers(0, n, size=(BOOT, n))
    cells, q1_settings, q2_settings, validity = {}, {}, {}, {}
    for b in BUDGETS:
        for cs in SWITCH_COSTS:
            key = f"B{b}_cs{cs}"
            cost = {w: {pol: results[(w, b, cs)][pol]["cost"] for pol in POLICIES} for w in WORLDS}
            avg = {pol: np.mean([cost[w][pol] for w in WORLDS], axis=0) for pol in POLICIES}
            best = min(SIMPLE, key=lambda pol: avg[pol].mean())
            cells[key] = {
                w: {pol: policy_stats(results[(w, b, cs)][pol], w, n) for pol in POLICIES}
                for w in WORLDS
            }
            for w in WORLDS:
                cw = cost[w]
                cells[key][w]["paired"] = {
                    "P3_minus_BEST": boot_ci(cw["P3"] - cw[best], idx),
                    "P4_minus_P3": boot_ci(cw["P4"] - cw["P3"], idx),
                    "P4w_minus_P3": boot_ci(cw["P4w"] - cw["P3"], idx),
                    "P3_minus_P0": boot_ci(cw["P3"] - cw["P0"], idx),
                }
            ci = boot_ci(avg["P3"] - avg[best], idx)
            rel = (avg[best].mean() - avg["P3"].mean()) / avg[best].mean()
            worse = {w: float(cost[w]["P3"].mean() / cost[w][best].mean() - 1) for w in WORLDS}
            q1_settings[key] = {
                "best": best,
                "world_avg_cost": {pol: float(avg[pol].mean()) for pol in POLICIES},
                "p3_minus_best": ci,
                "p3_relative_reduction": float(rel),
                "p3_worse_than_best_by_world": worse,
                "pass_10pct": bool(rel >= 0.10),
                "pass_ci_excludes_0": bool(ci["hi"] < 0),
                "pass_no_world_over_10pct_worse": bool(max(worse.values()) <= 0.10),
                "no_better_than_best": bool(avg["P3"].mean() >= avg[best].mean()),
            }
            cw3 = cost["W3"]
            cw1 = cost["W1"]
            ci3 = boot_ci(cw3["P4"] - cw3["P3"], idx)
            rel3 = (cw3["P3"].mean() - cw3["P4"].mean()) / cw3["P3"].mean()
            w1_worse = float(cw1["P4"].mean() / cw1["P3"].mean() - 1)
            q2_settings[key] = {
                "w3_p4_minus_p3": ci3,
                "w3_relative_gain": float(rel3),
                "w1_p4_relative_worse": w1_worse,
                "pass_w3": bool(rel3 >= 0.10 and ci3["hi"] < 0),
                "pass_w1": bool(w1_worse <= 0.02),
            }
            for w in ("W2", "W4"):
                st = cells[key][w]["P3"]
                validity[f"{key}_{w}"] = {
                    "rate": st["false_promotion_rate"],
                    "cp95_upper": st["false_promotion_cp95_upper"],
                    "violation": bool(st["false_promotion_cp95_lower"] > p.alpha),
                }
    pos = all(
        s["pass_10pct"] and s["pass_ci_excludes_0"] and s["pass_no_world_over_10pct_worse"]
        for s in q1_settings.values()
    )
    neg = sum(s["no_better_than_best"] for s in q1_settings.values()) * 2 >= len(q1_settings)
    q1 = "POSITIVE" if pos else ("NEGATIVE" if neg else "MIXED")
    q2 = (
        "SUPPORTED"
        if all(s["pass_w3"] and s["pass_w1"] for s in q2_settings.values())
        else "NOT SUPPORTED"
    )
    valid = not any(v["violation"] for v in validity.values())
    return {
        "cells": cells,
        "q1_settings": q1_settings,
        "q2_settings": q2_settings,
        "validity_check": validity,
        "decisions": {
            "Q1": q1,
            "Q2": q2,
            "validity_ok": valid,
            "efficacy_interpretation_halted": not valid,
        },
    }


def analyse_b2(results: dict, n: int, seed_base: int, p: Params) -> dict:
    """B2 Q1 rule applied mechanically to P3b; BEST over P0, P1, P2 (P2 cap not below rate/2)."""
    rng = np.random.default_rng(seed_base + 7)
    idx = rng.integers(0, n, size=(BOOT, n))
    cells, q1_settings, validity = {}, {}, {}
    for b in BUDGETS:
        for cs in SWITCH_COSTS:
            key = f"B{b}_cs{cs}"
            cost = {
                w: {pol: results[(w, b, cs)][pol]["cost"] for pol in B2_POLICIES} for w in WORLDS
            }
            avg = {pol: np.mean([cost[w][pol] for w in WORLDS], axis=0) for pol in B2_POLICIES}
            best = min(SIMPLE, key=lambda pol: avg[pol].mean())
            cells[key] = {
                w: {pol: policy_stats(results[(w, b, cs)][pol], w, n) for pol in B2_POLICIES}
                for w in WORLDS
            }
            for w in WORLDS:
                cw = cost[w]
                cells[key][w]["paired"] = {
                    "P3b_minus_BEST": boot_ci(cw["P3b"] - cw[best], idx),
                    "P3b_minus_P3": boot_ci(cw["P3b"] - cw["P3"], idx),
                    "P3_minus_BEST": boot_ci(cw["P3"] - cw[best], idx),
                }
            ci = boot_ci(avg["P3b"] - avg[best], idx)
            rel = (avg[best].mean() - avg["P3b"].mean()) / avg[best].mean()
            worse = {w: float(cost[w]["P3b"].mean() / cost[w][best].mean() - 1) for w in WORLDS}
            q1_settings[key] = {
                "best": best,
                "world_avg_cost": {pol: float(avg[pol].mean()) for pol in B2_POLICIES},
                "p3b_minus_best": ci,
                "p3b_relative_reduction": float(rel),
                "p3b_worse_than_best_by_world": worse,
                "p3_relative_reduction": float(
                    (avg[best].mean() - avg["P3"].mean()) / avg[best].mean()
                ),
                "pass_10pct": bool(rel >= 0.10),
                "pass_ci_excludes_0": bool(ci["hi"] < 0),
                "pass_no_world_over_10pct_worse": bool(max(worse.values()) <= 0.10),
                "no_better_than_best": bool(avg["P3b"].mean() >= avg[best].mean()),
            }
            for w in ("W2", "W4"):
                for pol in ("P3", "P3b"):
                    st = cells[key][w][pol]
                    validity[f"{key}_{w}_{pol}"] = {
                        "rate": st["false_promotion_rate"],
                        "cp95_upper": st["false_promotion_cp95_upper"],
                        "violation": bool(st["false_promotion_cp95_lower"] > p.alpha),
                    }
    pos = all(
        s["pass_10pct"] and s["pass_ci_excludes_0"] and s["pass_no_world_over_10pct_worse"]
        for s in q1_settings.values()
    )
    neg = sum(s["no_better_than_best"] for s in q1_settings.values()) * 2 >= len(q1_settings)
    q1 = "POSITIVE" if pos else ("NEGATIVE" if neg else "MIXED")
    valid = not any(v["violation"] for k, v in validity.items() if k.endswith("P3b"))
    return {
        "cells": cells,
        "q1_settings": q1_settings,
        "validity_check": validity,
        "decisions": {"Q1": q1, "validity_ok": valid, "efficacy_interpretation_halted": not valid},
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    r = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return r.stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--seed-base", type=int, default=20261031)
    ap.add_argument("--b2", action="store_true", help="B2 run: add P3b, drop P4/P4w")
    a = ap.parse_args()
    proto, proto_sha = (PROTOCOL_B2, PROTOCOL_B2_SHA256) if a.b2 else (PROTOCOL, PROTOCOL_SHA256)
    if sha256_file(proto) != proto_sha:
        raise SystemExit("protocol file does not match the registered sha256")
    p = Params()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    tasks = [(w, b, a.seeds, a.seed_base, p, a.b2) for w in WORLDS for b in BUDGETS]
    results, seconds = {}, {}
    with mp.get_context("spawn").Pool(a.workers) as pool:
        for r in pool.imap_unordered(run_world_budget, tasks):
            sec = r.pop("_seconds")
            for k, v in r.items():
                results[k] = v
                seconds[f"{k[0]}_B{k[1]}"] = sec
    summary = (analyse_b2 if a.b2 else analyse)(results, a.seeds, a.seed_base, p)
    summary["meta"] = {
        "protocol": str(proto.relative_to(ROOT)).replace("\\", "/"),
        "protocol_sha256": proto_sha,
        "repo_head": git_head(),
        "seeds": a.seeds,
        "seed_base": a.seed_base,
        "params": p.__dict__,
        "bootstrap_resamples": BOOT,
        "created_utc": datetime.now(UTC).isoformat(),
        "runtime_seconds": time.time() - t0,
        "task_seconds": seconds,
        "note": (
            "B2 development round 2; P3b = P3 with per-event cap q_t/2; P4 dropped"
            if a.b2
            else "development study; P4w is an exploratory unregistered variant"
        ),
    }
    (a.out_dir / "summary.json").write_text(
        json.dumps(jsonable(summary), indent=2), encoding="utf-8"
    )
    arrays = {}
    for (w, b, cs), pols in results.items():
        for pol, d in pols.items():
            for metric, arr in d.items():
                arrays[f"{w}|B{b}|cs{cs}|{pol}|{metric}"] = np.asarray(arr)
    np.savez_compressed(a.out_dir / "per_seed.npz", **arrays)
    d = summary["decisions"]
    print(json.dumps(d), f"runtime {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
