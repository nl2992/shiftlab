"""Estimand study: is a conditional-null alarm (fires on persistent bad stretches) net-beneficial when it triggers a costed switch,
versus a marginal-null (Sethi-type) alarm? Stylised cluster world, fully observed binary loss, q=1 for both monitors.

World: hidden bad/good regime = lazy-resample chain (switch rate delta, P(bad)=0.3=r0). Incumbent loss = 1 in bad, 0 in good (mean r0).
Fallback ('challenger'): variant A regime-local benefit: constant loss 0.35. Variant B no regime-local benefit: incumbent loss + 0.05.
Cost: 1.0 per switch (into and out of the fallback). Policies: incumbent only; fallback only; oracle regime-aware (knows the regime);
cond-triggered (conditional-null e-process alarm -> fallback for H steps -> back, monitor restarted); marg-triggered (Sethi Algorithm 1, same hold)."""

import json
from pathlib import Path

import numpy as np

from shiftlab.dep import sethi

T, R0, ALPHA, S, C_SW = 2000, 0.3, 0.05, 600, 1.0
LOGT = np.log(1 / ALPHA)
rng = np.random.default_rng(31)


def regime(delta):
    cur = (rng.random(S) < R0).astype(int)
    z = np.zeros((S, T), dtype=int)
    for t in range(T):
        sw = rng.random(S) < delta
        cur = np.where(sw, (rng.random(S) < R0).astype(int), cur)
        z[:, t] = cur
    return z


def simulate(z, trigger, hold, variant):
    """Closed loop with restarts. trigger in {'none','fallback','oracle','cond','marg'}."""
    on_fb = np.zeros(S, bool)
    left = np.zeros(S, int)
    cost = np.zeros(S)
    nsw = np.zeros(S)
    # conditional e-process state (Kelly bet, discount .99) and Sethi counts, reset at restart
    c1, c2, cn, logw = (np.zeros(S) for _ in range(4))
    n = np.zeros((S, 2, 2))
    prev = z[:, 0].copy()
    fb = (lambda zt: np.full(S, 0.35)) if variant == "A" else (lambda zt: zt + 0.05)
    for t in range(T):
        zt = z[:, t]
        if trigger == "fallback":
            sw_to = (t == 0) * np.ones(S, bool)
            on_fb = np.ones(S, bool)
            nsw += sw_to
        if trigger == "oracle":
            want = zt == 1
            nsw += want != on_fb if t > 0 else want
            on_fb = want
        loss = np.where(on_fb, fb(zt), zt.astype(float))
        cost += loss
        if trigger in ("cond", "marg"):
            live = ~on_fb
            if trigger == "cond":
                X = zt - R0
                mean, sec = c1 / (cn + 1), c2 / (cn + 1)
                lam = np.minimum(
                    np.where(sec > 0, np.maximum(mean, 0) / np.maximum(sec, 1e-12), 0.0), 0.5 / R0
                )
                logw = np.where(live, logw + np.log1p(lam * X), logw)
                c1 = np.where(live, 0.99 * c1 + X, c1)
                c2 = np.where(live, 0.99 * c2 + X * X, c2)
                cn = np.where(live, 0.99 * cn + 1, cn)
                alarm = live & (logw >= LOGT)
            else:
                if t > 0:
                    idx = np.where(live)[0]
                    np.add.at(n, (idx, prev[idx], zt[idx]), 1)
                alarm = np.zeros(S, bool)
                if t % 5 == 0 and t > 0:
                    Lst = sethi.statistic(n[:, 0, 0], n[:, 0, 1], n[:, 1, 0], n[:, 1, 1], R0)
                    alarm = live & (Lst >= sethi.threshold(n[:, 0].sum(1), n[:, 1].sum(1), ALPHA))
            on_fb = np.where(alarm, True, on_fb)
            left = np.where(alarm, hold, left)
            nsw += alarm
            back = on_fb & (left == 0) & ~alarm
            left = np.where(on_fb, left - 1, left)
            ret = back | (on_fb & (left < 0))
            on_fb = np.where(ret, False, on_fb)
            nsw += ret
            reset = ret
            c1, c2, cn, logw = (np.where(reset, 0.0, a) for a in (c1, c2, cn, logw))
            n[reset] = 0
            left = np.where(ret, 0, left)
        prev = zt
    return cost + C_SW * nsw, nsw


out = {}
for variant in ("A", "B"):
    for delta in (0.05, 0.01, 0.003):
        z = regime(delta)
        row = {}
        for name, trig, hold in (
            ("incumbent_only", "none", 0),
            ("fallback_only", "fallback", 0),
            ("oracle_regime_aware", "oracle", 0),
            ("cond_alarm_hold20", "cond", 20),
            ("cond_alarm_hold100", "cond", 100),
            ("marg_alarm_hold20", "marg", 20),
            ("marg_alarm_hold100", "marg", 100),
        ):
            c, nsw = simulate(z, trig, hold, variant)
            row[name] = {"net_cost": float(c.mean()), "switches": float(nsw.mean())}
        out[f"variant={variant},delta={delta}"] = row
        print(variant, delta, {k: round(v["net_cost"], 1) for k, v in row.items()}, flush=True)
Path("outputs/dep_sprint/estimand_switching.json").write_text(json.dumps(out, indent=1))
