"""Policy factory, search spaces (equal budgets), multiprocess batch runner and paired statistics.

Policy specs are plain dicts ``{"kind": ..., "params": {...}}`` so they pickle and log cleanly.
"""

from __future__ import annotations

import dataclasses
import json
import time
from multiprocessing import Pool

import numpy as np

from ..baselines import CUSUM, Gate, NeverSwitch, PageHinkley, WaldEconomic
from ..simulation import (
    SimulationEvaluator,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
    seeds_for,
)
from .policies import QVOI, BeliefMPC, DualPrice, RankReversal

T_DEFAULT = 300
TUNE_SEEDS = {"stage": "dev", "n": 6, "start": 0}  # tuning seeds (dev block, offset 0)
EVAL_SEEDS = {"stage": "dev", "n": 30, "start": 100}  # dev-eval seeds (disjoint from tuning)
TRAIN_SEEDS = {"stage": "dev", "n": 40, "start": 1000}  # A4 TRAIN seeds (disjoint again)


def seeds(d):
    return seeds_for(d["stage"], d["n"], d["start"])


# --------------------------------------------------------------------------------------------
def _stop(T, frac):
    return None if frac in (None, 0) else max(int(frac * T), 1)


def make_policy(spec: dict, T: int):
    kind, p = spec["kind"], dict(spec.get("params", {}))
    if kind == "never":
        return NeverSwitch()
    if kind in ("wald", "wald_paced", "wald_cut", "wald_any"):
        return WaldEconomic(
            p.get("lam", 0.98),
            p.get("gamma", 0.3),
            p.get("acq", "paced"),
            _stop(T, p.get("stop")),
            name=spec.get("name", kind),
        )
    if kind == "cusum":
        return CUSUM(p.get("delta", 0.1), p.get("h", 4.0), _stop(T, p.get("stop")))
    if kind == "page_hinkley":
        return PageHinkley(p.get("delta", 0.05), p.get("lam", 5.0), _stop(T, p.get("stop")))
    if kind == "gate_wald":
        g = Gate(
            WaldEconomic(
                p.get("lam", 0.98),
                p.get("gamma", 0.3),
                p.get("acq", "paced"),
                _stop(T, p.get("stop")),
                name="wald",
            ),
            alpha=p.get("alpha", 0.1),
            lam=p.get("lam_g", 0.25),
        )
        return g
    if kind == "A0":
        return BeliefMPC(**p)
    if kind == "A1":
        return QVOI(**p)
    if kind == "A2":
        g = {k: p.pop(k) for k in ("alpha", "lam_g") if k in p}
        inner = QVOI(**p)
        gate = Gate(inner, alpha=g.get("alpha", 0.1), lam=g.get("lam_g", 0.25))
        gate.name = "A2"
        return gate
    if kind == "A3":
        return DualPrice(**p)
    if kind == "A5":
        return RankReversal(**p)
    if kind in ("A4", "A4_gate"):
        from .learned import LearnedContinuation  # lazy: torch-free inference

        g = {k: p.pop(k) for k in ("alpha", "lam_g") if k in p}
        inner = LearnedContinuation(**p)
        if kind == "A4_gate":
            gate = Gate(inner, alpha=g.get("alpha", 0.1), lam=g.get("lam_g", 0.25))
            gate.name = "A4"
            return gate
        return inner
    raise ValueError(kind)


# --------------------------------------------------------------------------------------------
# search spaces: one sampler per kind; config 0 is always the documented default
# --------------------------------------------------------------------------------------------
def _u(r, lo, hi):
    return float(r.uniform(lo, hi))


def _lu(r, lo, hi):
    return float(np.exp(r.uniform(np.log(lo), np.log(hi))))


def _c(r, xs):
    return xs[int(r.integers(len(xs)))]


STOPS = [None, 0.05, 0.1, 0.15, 0.2, 0.3]


def _wald(r, acq, stop):
    return {"lam": _u(r, 0.9, 0.999), "gamma": _u(r, 0.05, 0.5), "acq": acq, "stop": stop}


SPACES = {
    "wald_paced": (lambda r: _wald(r, "paced", None), {"lam": 0.98, "gamma": 0.3, "acq": "paced"}),
    "wald_cut": (
        lambda r: _wald(r, "paced", _c(r, STOPS[1:])),
        {"lam": 0.98, "gamma": 0.3, "acq": "paced", "stop": 0.15},
    ),
    "wald_any": (
        lambda r: _wald(r, _c(r, ["paced", "uniform", "calendar"]), _c(r, STOPS)),
        {"lam": 0.98, "gamma": 0.3, "acq": "paced"},
    ),
    "cusum": (
        lambda r: {"delta": _lu(r, 0.02, 0.4), "h": _lu(r, 1.0, 12.0), "stop": _c(r, STOPS)},
        {"delta": 0.1, "h": 4.0},
    ),
    "page_hinkley": (
        lambda r: {"delta": _lu(r, 0.01, 0.3), "lam": _lu(r, 1.0, 15.0), "stop": _c(r, STOPS)},
        {"delta": 0.05, "lam": 5.0},
    ),
    "gate_wald": (
        lambda r: dict(
            **_wald(r, "paced", _c(r, STOPS)),
            alpha=_c(r, [0.05, 0.1, 0.2]),
            lam_g=_c(r, [0.1, 0.25, 0.5]),
        ),
        {"lam": 0.98, "gamma": 0.3, "acq": "paced", "alpha": 0.1, "lam_g": 0.25},
    ),
    "A0": (
        lambda r: {
            "persist": _u(r, 0, 2.5),
            "pi0": _u(r, 0.3, 0.6),
            "Hmax": _c(r, [60, 120, 200]),
            "qmargin": _u(r, 0, 0.3),
            "amargin": _u(r, 0, 1.5),
            "base_margin": _u(r, 0, 2.0),
        },
        {},
    ),
    "A1": (
        lambda r: {
            "persist": _u(r, 0, 2.5),
            "pi0": _u(r, 0.3, 0.6),
            "lam_q": _u(r, -0.04, 0.1),
            "voi_mult": _lu(r, 1.0, 8.0),
            "sw_margin": _u(r, 0, 1.5),
            "rho_mult": _lu(r, 0.5, 2.0),
        },
        {},
    ),
    "A2": (
        lambda r: {
            "persist": _u(r, 0, 2.5),
            "pi0": _u(r, 0.3, 0.6),
            "lam_q": _u(r, -0.04, 0.1),
            "voi_mult": _lu(r, 1.0, 8.0),
            "sw_margin": _u(r, 0, 1.5),
            "rho_mult": _lu(r, 0.5, 2.0),
            "alpha": _c(r, [0.05, 0.1, 0.2]),
            "lam_g": _c(r, [0.1, 0.25, 0.5]),
        },
        {"alpha": 0.1, "lam_g": 0.25},
    ),
    "A3": (
        lambda r: {
            "persist": _u(r, 0, 2.5),
            "pi0": _u(r, 0.3, 0.6),
            "lam_q": _u(r, 0, 0.2),
            "lam_sw": _u(r, 0, 2.0),
            "kappa": _lu(r, 0.5, 8.0),
            "eta": _c(r, [0.0, 0.05, 0.2, 0.5]),
            "front": _u(r, 0.2, 1.0),
            "rho_mult": _lu(r, 0.5, 2.0),
        },
        {},
    ),
    "A5": (
        lambda r: {
            "persist": _u(r, 0, 2.5),
            "pi0": _u(r, 0.3, 0.6),
            "eps_flip": _lu(r, 0.01, 0.5),
            "n_batch": _c(r, [3, 5, 8, 12, 20]),
            "h_min": _c(r, [0, 5, 15, 30]),
            "sw_margin": _u(r, 0, 1.5),
        },
        {},
    ),
    "A4": (lambda r: {"margin_q": _u(r, 0, 0.3), "margin_a": _u(r, 0, 1.5)}, {}),
}
SPACES["A4_gate"] = (
    lambda r: dict(
        **SPACES["A4"][0](r), alpha=_c(r, [0.05, 0.1, 0.2]), lam_g=_c(r, [0.1, 0.25, 0.5])
    ),
    {"alpha": 0.1, "lam_g": 0.25},
)
KIND_OF = {"wald_paced": "wald", "wald_cut": "wald", "wald_any": "wald"}


def sample_configs(method: str, n: int, seed: int = 0) -> list[dict]:
    """n specs for ``method``: the default first, then n-1 uniform random draws."""
    sampler, default = SPACES[method]
    r = np.random.default_rng([seed, sum(map(ord, method))])
    cfgs = [dict(default)] + [sampler(r) for _ in range(n - 1)]
    return [{"kind": KIND_OF.get(method, method), "params": c, "name": method} for c in cfgs]


# --------------------------------------------------------------------------------------------
# batch runner
# --------------------------------------------------------------------------------------------
_REG = None


def _init():
    global _REG
    _REG = load_regimes()


KEYS = (
    "J",
    "n_queries",
    "n_switches",
    "deploy_loss",
    "global_null",
    "global_null_false_promotion",
    "false_promotions",
    "unpaid_promotions",
    "max_drawdown_vs_never",
    "J_never",
    "J_hindsight_oracle_UNATTAINABLE",
    "frac_time_wrong_model",
)


def _task(args):
    rid, seed, specs, T, B = args
    reg = _REG[rid]
    if B is not None:
        reg = dataclasses.replace(reg, B=int(B))
    tape, truth = generate_tape(reg, seed, T)  # tape depends on regime id/seed, not on B
    spec = make_spec(reg, T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    out = []
    for i, ps in enumerate(specs):
        t0 = time.time()
        rec = run_policy(make_policy(ps, T), tape, spec, seed)
        e = ev.evaluate(rec)
        row = {k: float(e[k]) for k in KEYS}
        row.update(pid=i, regime=rid, seed=seed, sec=time.time() - t0)
        out.append(row)
    return out


def run_batch(specs, regime_ids, seed_list, T=T_DEFAULT, workers=16, B_by_regime=None, log=None):
    """Run every spec on every (regime, seed) tape. Returns flat list of row dicts."""
    tasks = [
        (rid, s, specs, T, (B_by_regime or {}).get(rid)) for rid in regime_ids for s in seed_list
    ]
    rows = []
    t0 = time.time()
    with Pool(workers, initializer=_init) as pool:
        for i, out in enumerate(pool.imap_unordered(_task, tasks, chunksize=1)):
            rows.extend(out)
            if log and (i + 1) % max(len(tasks) // 5, 1) == 0:
                log(f"  {i + 1}/{len(tasks)} tapes, {time.time() - t0:.0f}s")
    return rows


def regime_ids():
    return list(load_regimes().keys())


# --------------------------------------------------------------------------------------------
# aggregation / paired statistics
# --------------------------------------------------------------------------------------------
def to_array(rows, n_pid, rids, seed_list, key="J"):
    """(n_pid, n_regime, n_seed) array."""
    ri = {r: i for i, r in enumerate(rids)}
    si = {s: i for i, s in enumerate(seed_list)}
    A = np.full((n_pid, len(rids), len(seed_list)), np.nan)
    for r in rows:
        A[r["pid"], ri[r["regime"]], si[r["seed"]]] = r[key]
    return A


def tuning_score(Jarr, Jnever):
    """Mean over regimes of (mean_seed J)/(mean_seed J_never) per config -> (n_pid,)."""
    return (Jarr.mean(2) / Jnever.mean(1)[None, :]).mean(1)


def paired_delta(JA, JB, n_boot=2000, seed=0):
    """JA, JB: (n_regime, n_seed) with identical tapes. Delta = JA - JB (negative = A better).
    Pooled = equal-weight mean over regimes per seed; cluster bootstrap over seeds."""
    D = JA - JB
    rng = np.random.default_rng(seed)
    ns = D.shape[1]
    pooled = D.mean(0)
    bs = np.array([pooled[rng.integers(0, ns, ns)].mean() for _ in range(n_boot)])
    base = JB.mean()
    per = []
    for i in range(D.shape[0]):
        b = np.array([D[i][rng.integers(0, ns, ns)].mean() for _ in range(400)])
        per.append(
            (
                float(D[i].mean()),
                float(np.percentile(b, 2.5)),
                float(np.percentile(b, 97.5)),
                float(100 * D[i].mean() / max(JB[i].mean(), 1e-9)),
            )
        )
    return {
        "delta": float(pooled.mean()),
        "lo": float(np.percentile(bs, 2.5)),
        "hi": float(np.percentile(bs, 97.5)),
        "rel_pct": float(100 * pooled.mean() / base),
        "base": float(base),
        "per_regime": per,
    }


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=float)


for _m in ("A0", "A1", "A3", "A5"):  # documented default: mild persistence prior
    SPACES[_m] = (SPACES[_m][0], {**SPACES[_m][1], "persist": 1.0})
SPACES["A2"] = (SPACES["A2"][0], {**SPACES["A2"][1], "persist": 1.0})
