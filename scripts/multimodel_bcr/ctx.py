"""Contextual specialists under a routing contract (BCR follow-up, directive Task 1).

Contract: observable context x in {0, 1} arrives with each event; the deployment is a routing
table (model for x=0, model for x=1); a switching cost c_s is charged once per table update
(any change to the table). Same hard label budget, delay and paid labels as the K-model pilot;
a released label reveals every model's loss on that event (and its x).

Policies (all share the IPW-consistent K-Wald evidence of policies.KWald):
  blind_*   one KWald ignoring x (table entries always equal);
  cw_*      contextual Wald: one KWald per context; each sees only its context's events and
            labels; budget pacing shares the remaining budget in proportion to each context's
            observed query-region rate;
  cmp_*     contextual Model Picker acquisition (per-context MP posterior) + contextual Wald
            deployment (tabular analogue of contextual active model selection);
  cbcr_*    per-context BCR acquisition; cemp_* per-context economic Model Picker.
Evaluator-side: expected-loss oracle = DP over the K^2 routing tables with cost c_s per update.

usage: python ctx.py --seeds 20 --seed-base 2026111501 --out DIR [--workers 8]
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "scripts/promising_directions/sota"))

T, B, CS, CQ, DELAY = 2000, 200, 5.0, 0.05, 100


@dataclass(frozen=True)
class CEnv:
    name: str
    acc: tuple  # per model: ((start, acc_x0, acc_x1), ...)
    pi: tuple = (0.5, 0.5)  # P(x=1) linear from pi[0] to pi[1]
    rho: float = 0.7

    def schedule(self):
        K = len(self.acc)
        a = np.empty((K, 2, T))
        for k, spec in enumerate(self.acc):
            for i, s in enumerate(spec):
                e = spec[i + 1][0] if i + 1 < len(spec) else T
                a[k, 0, s[0] : e], a[k, 1, s[0] : e] = s[1], s[2]
        return a, np.linspace(self.pi[0], self.pi[1], T)

    def sample(self, rng):
        a, pi = self.schedule()
        K = a.shape[0]
        y = (rng.random(T) < 0.5).astype(np.int8)
        x = (rng.random(T) < pi).astype(np.int8)
        acc = a[:, x, np.arange(T)]  # (K, T)
        common = rng.random(T) < self.rho
        u = np.where(common[None, :], rng.random(T)[None, :], rng.random((K, T)))
        preds = np.where(u < acc, y[None, :], 1 - y[None, :]).T.astype(np.int8)
        return preds, y, x


def _c(a0, a1=None):
    return ((0, a0, a0 if a1 is None else a1),)


CENVS = {
    e.name: e
    for e in [
        CEnv("C1_spec_static", (_c(0.70), _c(0.82, 0.60), _c(0.60, 0.82))),
        CEnv("C2_spec_drift", (_c(0.70), _c(0.82, 0.60), _c(0.60, 0.82)), pi=(0.15, 0.85)),
        CEnv(
            "C3_spec_late",
            (_c(0.70), ((0, 0.70, 0.70), (800, 0.82, 0.60)), ((0, 0.70, 0.70), (800, 0.60, 0.82))),
        ),
        CEnv("C4_blind_winner", (_c(0.70), _c(0.75), _c(0.72, 0.68))),
        CEnv("C5_null", (_c(0.72), _c(0.72), _c(0.72))),
    ]
}


def oracle(env):
    a, pi = env.schedule()
    K = a.shape[0]
    tabs = list(itertools.product(range(K), range(K)))
    el = np.array([(1 - pi) * (1 - a[m0, 0]) + pi * (1 - a[m1, 1]) for m0, m1 in tabs])
    v = np.where(np.array([t == (0, 0) for t in tabs]), 0.0, CS) + el[:, 0]
    for t in range(1, T):
        v = np.minimum(v, v.min() + CS) + el[:, t]
    return float(v.min()), el, tabs


class _Ev:  # minimal event for KWald
    __slots__ = ("event_id", "model_predictions", "t")

    def __init__(self, t, preds):
        self.event_id, self.t, self.model_predictions = t, t, preds


class _Fb:
    __slots__ = ("event_id", "model_losses", "query_probability", "t_released")

    def __init__(self, eid, tr, losses, q):
        self.event_id, self.t_released, self.model_losses, self.query_probability = (
            eid,
            tr,
            losses,
            q,
        )


class Routed:
    def __init__(self, K, rng, contextual, **kw):
        from policies import KWald

        n = 2 if contextual else 1
        self.ctx = contextual
        self.inst = [KWald(T, B, CS, K, rng, **kw) for _ in range(n)]
        self.rng = rng

    def table(self):
        return (self.inst[0].deployed, self.inst[-1].deployed)

    def query(self, t, preds, x, remaining):
        from simulator import QueryRequest  # noqa: F401

        i = x if self.ctx else 0
        for k in self.inst:
            k.t = t
        if self.ctx:
            r = [k.n_R + 1.0 for k in self.inst]
            share = r[i] / sum(r)
            rem = round(remaining * share) if remaining > 0 else 0
            rem = max(rem, 1) if remaining > 0 else 0
        else:
            rem = remaining
        req = self.inst[i].request_labels(_Ev(t, preds), rem)
        return (req.probability if req.requested else 0.0), i

    def observe(self, fbs):
        for inst_i, fb in fbs:
            self.inst[inst_i].observe([fb])


def make(name, K, rng):
    fam, lam, g, *rest = name.split("_")
    kw = {"lam": float(lam[1:]), "gamma": float(g[1:])}
    acq = {"blind": "anydis", "cw": "anydis", "cmp": "mp", "cbcr": "bcr", "cemp": "emp"}[fam]
    kw["acq"] = acq
    if rest:
        kw["z_u"], kw["rho_mon"] = float(rest[0][2:]), float(rest[1][2:])
    return Routed(K, rng, contextual=fam != "blind", **kw)


def names():
    out = []
    for lam, g in itertools.product((0.9, 0.95), (0.05, 0.1)):
        out += [f"blind_l{lam}_g{g}", f"cw_l{lam}_g{g}", f"cmp_l{lam}_g{g}"]
        for zu, rm in itertools.product((0.5, 1.5), (0.1, 0.3)):
            out += [f"cbcr_l{lam}_g{g}_zu{zu}_rm{rm}", f"cemp_l{lam}_g{g}_zu{zu}_rm{rm}"]
    return out


def _h(s):
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big")


def job(args):
    env_name, seed, base, pols = args
    env = CENVS[env_name]
    preds, y, x = env.sample(np.random.default_rng([base, _h(env_name), seed]))
    K = preds.shape[1]
    orc, el, tabs = oracle(env)
    tix = {t: i for i, t in enumerate(tabs)}
    rows = []
    for nm in pols:
        rng = np.random.default_rng([base, _h(env_name), seed, _h(nm)])
        pol = make(nm, K, rng)
        pend, remaining, loss, labels, upd = {}, B, 0.0, 0, 0
        exp_loss = 0.0
        prev = (0, 0)
        for t in range(T):
            due = pend.pop(t, [])
            if due:
                pol.observe(due)
            tab = pol.table()
            if tab != prev:
                upd += 1
                prev = tab
            m = tab[x[t]]
            loss += float(preds[t, m] != y[t])
            exp_loss += el[tix[tab], t]
            if remaining > 0:
                q, inst_i = pol.query(t, preds[t], int(x[t]), remaining)
                if q > 0 and rng.random() < q:
                    remaining -= 1
                    labels += 1
                    if t + DELAY < T:
                        pend.setdefault(t + DELAY, []).append(
                            (inst_i, _Fb(t, t + DELAY, (preds[t] != y[t]).astype(np.int8), q))
                        )
        net = loss + CQ * labels + CS * upd
        exp_cost = exp_loss + CQ * labels + CS * upd
        rows.append(
            {
                "env": env_name,
                "seed": seed,
                "policy": nm,
                "net": net,
                "labels": labels,
                "updates": upd,
                "regret": exp_cost - orc,
            }
        )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed-base", type=int, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", required=True)
    ap.add_argument("--policies", default="")
    a = ap.parse_args()
    pols = a.policies.split(",") if a.policies else names()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(e, s, a.seed_base, pols) for e in CENVS for s in range(a.seeds)]
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for rows in pool.imap_unordered(job, jobs):
            f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"done {len(jobs)} jobs -> {out}", flush=True)


if __name__ == "__main__":
    main()
