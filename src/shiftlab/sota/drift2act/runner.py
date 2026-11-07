"""Episode runner, calibration (fit T and p(z|d) on disjoint seeds), baselines and Table-1-style metrics."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from .actions import COST, LABEL_COST, Config
from .audit import LabelStore
from .belief import BeliefFilter, GaussianEvidence, estimate_T
from .controller import Drift2ActController
from .synthetic_env import SyntheticStreamEnv

METHODS = (
    "alarm_only",
    "adapt_always",
    "retrain_schedule",
    "selective_only",
    "ctrl_no_cert",
    "ctrl_cert",
    "ctrl_cert_alg1",
    "ctrl_cert_literal",
)


def _uniform_labels(store, t, rng, k=2):
    hi = t - store.delay
    for i in rng.integers(0, hi + 1, size=k) if hi >= 0 else []:
        if store.remaining > 0:
            store.request(int(i), t)


def calibrate(seeds, L=1500, cfg: Config | None = None):
    cfg = cfg or Config()
    Z, D, eps = [], [], []
    for s in seeds:
        env = SyntheticStreamEnv(s, L)
        store = LabelStore(env.oracle, cfg.delay, 0, cfg.label_budget)
        rng = np.random.default_rng(s + 7)
        Ds = []
        for t in range(L):
            _uniform_labels(store, t, rng)
            lab = {i: store.get(i, t) for i in store.released(t, max(0, t - 512), t)}
            z = env.monitor(t, lab)
            Z.append(z)
            d = env.truth_state(t)
            D.append(d)
            Ds.append(d)
        eps.append(Ds)
    Z, D = np.array(Z), np.array(D)
    ev = GaussianEvidence.fit(Z, D, var_floor=1e-4, beta=cfg.evidence_beta)
    return ev, estimate_T(eps), (Z[D == 0].mean(0), Z[D == 0].std(0) + 1e-6)


def run_episode(
    seed,
    method,
    ev,
    T,
    zref,
    cfg: Config | None = None,
    L=1500,
    policy=None,
    keep_log=False,
    drift=None,
):
    cfg = cfg or Config()
    if method == "ctrl_no_cert":
        cfg = replace(cfg, use_certificate=False)
    elif method == "ctrl_cert_alg1":  # delta_t = 6 delta/(pi^2 t^2) on top of rad(n,.)
        cfg = replace(cfg, delta_mode="alg1")
    elif (
        method == "ctrl_cert_literal"
    ):  # Alg.1 literal: per-round |Q_t| sample, delta_t, unconditional scheduling
        cfg = replace(cfg, delta_mode="alg1", pool="round", fail_schedule="literal")
    env = SyntheticStreamEnv(seed, L, drift=drift, theta_sel=cfg.theta_sel)
    store = LabelStore(env.oracle, cfg.delay, 0, cfg.label_budget)
    rng = np.random.default_rng(seed + 99)
    ctrl = None
    if method.startswith("ctrl"):
        ctrl = Drift2ActController(env, store, BeliefFilter(T, ev), cfg, policy, rng, horizon=L)
    R, W, alarm, cost, prev_alarm, abst_prev = [], [], [], 0.0, False, False
    for t in range(L):
        ab = False
        a_flag = False
        if ctrl:
            rec = ctrl.step(t)
            ab = rec["abstain"]
            a_flag = rec["belief"][0] < 0.5 or rec["action"] != "A0_noop"
        else:
            _uniform_labels(store, t, rng)
            cost += LABEL_COST * 0  # label cost added at end
            lab = {i: store.get(i, t) for i in store.released(t, max(0, t - 512), t)}
            z = env.monitor(t, lab)
            a_flag = bool(np.max(np.abs((z - zref[0]) / zref[1])) > 2.5)
            allr = lambda t=t: {i: store.get(i, t) for i in store.released(t)}
            if method == "alarm_only":
                cost += 0.3 * (a_flag and not prev_alarm)
            elif method == "adapt_always" and t % 25 == 0:
                env.apply(2, t, {})
                cost += COST[2]
            elif method == "retrain_schedule" and t == 1200:
                env.apply(4, t, allr())
                cost += COST[4]
            elif method == "selective_only":
                ab = True
                cost += 0.3 * (not abst_prev)
            prev_alarm, abst_prev = a_flag, ab
        r, w = env.truth_eval(t, ab)
        R.append(r)
        W.append(w)
        alarm.append(a_flag)
    R, W, alarm = np.array(R), np.array(W), np.array(alarm)
    o = env.onset
    tau = cfg.tau
    det = np.where(alarm[o:])[0]
    rec_ = np.where(R[o:] <= tau)[0]
    harm = np.where(R[o:] > tau)[0]
    T_rec2 = np.nan
    if len(harm):
        after = np.where(R[o + harm[0] :] <= tau)[0]
        T_rec2 = float(after[0]) if len(after) else float(L - o - harm[0])
    if ctrl:
        cost = ctrl.total_action_cost
        lab_cost = ctrl.total_label_cost
    else:
        lab_cost = LABEL_COST * store.spent
    out = {
        "seed": seed,
        "method": method,
        "drift": env.drift,
        "schedule": env.schedule,
        "onset": o,
        "C_act": float(cost),
        "C_label": float(lab_cost),
        "C_tot": float(cost + lab_cost),
        "V": int((R > tau).sum()),
        "T_det": float(det[0]) if len(det) else float(L - o),
        "T_rec": float(rec_[0]) if len(rec_) else float(L - o),
        "T_rec_post_harm": T_rec2,
        "minAccwg": float(W[o:].min()),
        "labels_used": store.spent,
        "harmful": bool(len(harm)),
    }
    if keep_log:
        out["log"] = ctrl.log if ctrl else None
        out["R"] = R.tolist()
    return out


def run_suite(episode_seeds, calib_seeds, cfg=None, methods=METHODS, out_path=None):
    cfg = cfg or Config()
    t0 = time.time()
    ev, T, zref = calibrate(calib_seeds, cfg=cfg)
    rows = []
    for s in episode_seeds:
        for m in methods:
            rows.append(run_episode(s, m, ev, T, zref, cfg))
        if out_path:
            Path(out_path).write_text(
                json.dumps(
                    {
                        "cfg": asdict(cfg),
                        "calib_seeds": list(calib_seeds),
                        "rows": rows,
                        "elapsed": time.time() - t0,
                    }
                )
            )
    return rows


def summarise(rows):
    import collections

    g = collections.defaultdict(list)
    for r in rows:
        g[r["method"]].append(r)
    out = {}
    for m, rs in g.items():
        f = lambda k, rs=rs: float(np.nanmean([r[k] for r in rs]))
        out[m] = {
            "n": len(rs),
            "C_tot": f("C_tot"),
            "C_act": f("C_act"),
            "C_label": f("C_label"),
            "V": f("V"),
            "T_det": f("T_det"),
            "T_rec": f("T_rec"),
            "T_rec_post_harm": f("T_rec_post_harm"),
            "minAccwg": f("minAccwg"),
        }
    return out


if __name__ == "__main__":
    import sys

    a, b = int(sys.argv[1]), int(sys.argv[2])
    path = sys.argv[3]
    rows = run_suite(range(1000 + a, 1000 + b), range(50_000, 50_000 + 12), out_path=path)
    for m, v in summarise(rows).items():
        print(m, {k: round(x, 2) for k, x in v.items()})
