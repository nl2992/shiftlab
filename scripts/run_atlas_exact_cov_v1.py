"""Failure Atlas v1, Amendment 6 item 1: exact cost of validity on tiny HMM cells (cycle 5).

Protocol: docs/failure_atlas_v1_protocol.md, Amendment 6, item 1 (reading rule locked there).
The classical sequence-form LP of ``shiftlab.dive.causal_switching_game`` gives, per cell,
``V_valid`` (optimal expected total cost under the best-response causal-null risk <= alpha) and
``V_free`` (same LP, alpha = 1, which makes the risk row vacuous because every risk is <= 1).
Harness methods are Monte-Carlo evaluated on the same HMM and contract (total cost = decision
loss + c * queries + s * switches, over T rounds, not per round). The oracle is a reference only.

    .venv/Scripts/python scripts/run_atlas_exact_cov_v1.py                 # full (5000 seeds)
    .venv/Scripts/python scripts/run_atlas_exact_cov_v1.py --smoke --out <dir>   # one T=6 cell
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import bisect
import itertools
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess
from shiftlab.dive.switching_explore import (
    Config,
    EpisodeComposition,
    Stream,
    bernoulli_grid_spec,
    make_bernoulli_stream,
    paired_ci,
    uniform_calendar,
)

STRADDLE_ID = "b1a17927d9ad"
AXES_SEARCHED = ["onset", "duration", "s", "d", "budget_frac", "effect", "rate", "unknown"]
A_LEVELS = (0.1, 0.25)
EFFECT_PAIRS = {"strong": (0.02, 0.98), "medium": (0.2, 0.8)}
OFF_TYPES = ("harmful", "neutral")
TS, BS, DS = (6, 7, 8), (2, 3, 4), (1, 2)
C, S, H, ALPHA = 0.01, 0.1, 0.1, 0.1
MAX_NODES = 3_000_000
LP_TIME_LIMIT_S = 60.0  # hard-coded in causal_switching_game.solve
SEED_OFFSET = 10_000  # inside the mechanism partition [200000, 300000)
CHUNK = 500
_SPEC = None


# ----------------------------------------------------------------------------- cells


def cell_list(smoke: bool = False) -> list[dict]:
    out = []
    for T, B, d, a, eff, off in itertools.product(TS, BS, DS, A_LEVELS, EFFECT_PAIRS, OFF_TYPES):
        out.append({"T": T, "B": B, "d": d, "a": a, "effect": eff, "off": off})
    for c in out:
        c["id"] = f"a{c['a']:g}_{c['effect']}_{c['off']}_T{c['T']}_B{c['B']}_d{c['d']}"
    if smoke:
        return [
            c
            for c in out
            if (c["T"], c["B"], c["d"], c["a"], c["effect"], c["off"])
            == (6, 2, 1, 0.25, "strong", "harmful")
        ]
    return out


def p_pair(cell: dict) -> tuple[float, float]:
    lo, hi = EFFECT_PAIRS[cell["effect"]]
    return (0.5 if cell["off"] == "neutral" else lo, hi)  # (P(Y=1) off, P(Y=1) on)


def regime_model(cell: dict):
    """HMM of the solver: regime starts off, off->on w.p. a, on is absorbing (duration L = 1)."""
    from shiftlab.dive.delayed_regime_information import RegimeModel

    lo, hi = EFFECT_PAIRS[cell["effect"]]
    e1 = F(hi).limit_denominator(100)
    e0 = F(1, 2) if cell["off"] == "neutral" else F(lo).limit_denominator(100)
    m = RegimeModel(F(cell["a"]).limit_denominator(100), F(0), F(1, 4), e1, F(0))
    # RegimeModel insists on emission0 < 1/2; the neutral off state is exactly 1/2. The game only
    # evaluates propagate/emission/emission1/prior1, which are all valid at emission0 = 1/2.
    object.__setattr__(m, "emission0", e0)
    return m


# ----------------------------------------------------------------------------- exact LP


def lp_task(cell: dict) -> dict:
    from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig

    t0 = time.time()
    out = {"id": cell["id"]}
    game = CausalSwitchingGame(
        GameConfig(
            horizon=cell["T"],
            budget=cell["B"],
            delay=cell["d"],
            alpha=F(1, 10),
            query_cost=F(1, 100),
            switch_cost=F(1, 10),
            max_nodes=MAX_NODES,
        ),
        regime_model(cell),
    )
    try:
        game.build()
    except Exception as exc:  # noqa: BLE001 - node limit is a reportable outcome
        return {
            **out,
            "error": f"{type(exc).__name__}: {exc}",
            "seconds": round(time.time() - t0, 1),
            "stage": "build",
        }
    out["build_seconds"] = round(time.time() - t0, 1)
    out["nodes"] = game.nodes
    try:
        rep, _, _ = game.solve()
        out.update(
            V_valid=float(F(rep["raw_recovered_cost"])),
            valid_risk=float(F(rep["raw_causal_null_risk"])),
            valid_iid_risk=float(F(rep["iid_boundary_risk"])),
            valid_calibrated_cost=float(F(rep["calibrated_total_cost"])),
            continue_cost=float(F(rep["continue_cost"])),
            valid_solver_objective=rep["solver_objective"],
            learner_sequences=rep["learner_sequences"],
        )
        # Same game, alpha = 1: the risk row `null_payoff^T x <= F^T v`, `f v <= alpha` is then vacuous
        # (any risk is at most 1), so this is the unconstrained optimum. The tree is already built.
        game.config = replace(game.config, alpha=F(1))
        rep1, _, _ = game.solve()
        out.update(
            V_free=float(F(rep1["raw_recovered_cost"])),
            free_risk=float(F(rep1["raw_causal_null_risk"])),
            free_solver_objective=rep1["solver_objective"],
        )
    except Exception as exc:  # noqa: BLE001
        return {
            **out,
            "error": f"{type(exc).__name__}: {exc}",
            "stage": "solve",
            "seconds": round(time.time() - t0, 1),
        }
    out["seconds"] = round(time.time() - t0, 1)
    return out


# ----------------------------------------------------------------------------- R_valid (HMM cell)


def hmm_start_design(cfg: Config) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Uniform onset prior over rounds 1..T-1 mapped to label indices via the uniform calendar."""
    cal = sorted(uniform_calendar(cfg.T, cfg.B, cfg.d))
    counts: dict[int, int] = {}
    for tau in range(1, cfg.T):
        k = min(bisect.bisect_left(cal, tau), max(0, cfg.B - 1))
        counts[k] = counts.get(k, 0) + 1
    starts = tuple(sorted(counts))
    tot = float(sum(counts.values()))
    return starts, tuple(counts[k] / tot for k in starts)


def hmm_kelly_stakes(h: float) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Distinct Kelly stakes of the cell family's effect levels (on-state P(Y=1) 0.98, 0.8)."""
    st = sorted({round(fa.kelly_stake(hi, h), 6) for _, hi in EFFECT_PAIRS.values()})
    return tuple(st), tuple(1.0 / len(st) for _ in st)


class RValidHMM(EpisodeComposition):
    """Adaptation of ``fa.RValidFamily1`` to the HMM cell: same ``episode_front`` rule and
    started-mixture e-process; start weights = uniform onset prior over rounds (via the calendar),
    stakes = Kelly mixture of the family effect levels. Fixed from the config alone."""

    def __init__(self):
        super().__init__("front")
        self.name = "ref_valid"

    def _new_episode(self, j: int, start: int) -> None:
        super()._new_episode(j, start)
        if j == 0:
            starts, weights = hmm_start_design(self.cfg)
            proc = VectorizedStartedMixtureEProcess(
                bound=1.0 + self.cfg.h, alpha=self.cfg.alpha, starts=starts, weights=weights
            )
            self.ep = fa.set_stake_mixture(proc, *hmm_kelly_stakes(self.cfg.h))


def straddle_spec():
    for ax in AXES_SEARCHED:
        for sp in comp.propose_candidates(ax, max_n=60):
            if sp.spec_id == STRADDLE_ID:
                return sp
    raise LookupError(f"spec {STRADDLE_ID} not found")


def method_names() -> tuple[str, ...]:
    return (fa.FLOOR, *fa.gated_methods(), "ref_valid", "straddle")


def make(name: str, cfg: Config):
    global _SPEC
    if name == "ref_valid":
        return RValidHMM()
    if name == "straddle":
        return comp.build_candidate(straddle_spec())
    if _SPEC is None:
        _SPEC = bernoulli_grid_spec()
    return fa.make_method(name, _SPEC, cfg)


# ----------------------------------------------------------------------------- Monte Carlo


def _run_rb(stream: Stream, method, cfg: Config):
    """Harness run; returns (realised total cost, Rao-Blackwellised total cost, promoted)."""
    from shiftlab.dive.switching_explore import run

    r = run(stream, method, cfg)
    pv = np.asarray(p_of(stream), dtype=float)  # P(Y_t=1 | S_t)
    a = r.actions
    prev = np.concatenate(([0], a[:-1]))
    exp_loss = np.where(a == 1, 1.0 - pv, pv)  # a_t is independent of Y_t given the regime path
    rb = float(exp_loss.sum() + cfg.c * r.queries + cfg.s * float((a != prev).sum()))
    return r.cost, rb, r.promotions > 0, r.queries, r.switches


def p_of(stream: Stream):
    return (
        stream.truth.hmm.p[0]
        + (stream.truth.hmm.p[1] - stream.truth.hmm.p[0]) * stream.truth.regime
    )


def alt_stream(cell: dict, seed: int) -> Stream:
    rng = np.random.default_rng([int(seed), cell["T"], 6001])
    return make_bernoulli_stream(rng, cell["T"], p_pair(cell), a=cell["a"], b=0.0, prior1=0.0)


def mc_alt_task(args: tuple) -> dict:
    cell, seed_list = args
    cfg0 = Config(T=cell["T"], B=cell["B"], d=cell["d"], c=C, s=S, h=H, alpha=ALPHA)
    out: dict[str, dict[str, list]] = {}
    for sd in seed_list:
        stream = alt_stream(cell, sd)
        cfg = replace(cfg0, seed=int(sd))
        for name in method_names():
            real, rb, promo, q, sw = _run_rb(stream, make(name, cfg), cfg)
            slot = out.setdefault(name, {"real": [], "rb": [], "q": [], "sw": [], "promo": []})
            slot["real"].append(real)
            slot["rb"].append(rb)
            slot["q"].append(q)
            slot["sw"].append(sw)
            slot["promo"].append(int(promo))
    return {"id": cell["id"], "methods": out}


def mc_null_task(args: tuple) -> dict:
    """iid P(Y=1) = 1/2 boundary null (same as ``tiny_cell`` in the C1/C2 script)."""
    (T, B, d), seed_list = args
    cfg0 = Config(T=T, B=B, d=d, c=C, s=S, h=H, alpha=ALPHA)
    out: dict[str, list] = {n: [] for n in method_names()}
    for sd in seed_list:
        rng = np.random.default_rng([int(sd), T, 5151])
        y = (rng.random(T) < 0.5).astype(float)
        stream = Stream(y, 1.0 - y)
        cfg = replace(cfg0, seed=int(sd))
        from shiftlab.dive.switching_explore import run

        for name in method_names():
            out[name].append(int(run(stream, make(name, cfg), cfg).promotions > 0))
    return {"key": f"T{T}_B{B}_d{d}", "fp": out}


def exact_null_task(key: tuple) -> dict:
    """Exact null risk of each (deterministic) harness method, matching the solver definitions.

    ``iid``: every queried label is Bernoulli(1/2). ``causal``: the solver's best response, an
    opponent choosing P(Y=1) in {0, 1/2} per queried label after seeing all earlier generated
    labels (``CausalSwitchingGame.null_risk``). Risk = P(the method ever plays action 1). Computed by
    replaying the method over the 2^(#queries) label tree; randomised methods are marked ``None``.
    """
    T, B, d = key
    cfg = Config(T=T, B=B, d=d, c=C, s=S, h=H, alpha=ALPHA, seed=0)
    res: dict[str, dict | None] = {}
    for name in method_names():
        probe = make(name, cfg)
        probe.start(cfg)
        # ComposedMethod always creates an rng, used only by bernoulli_pacing acquisition.
        uses_rng = hasattr(probe, "rng") and not (
            name == "straddle" and straddle_spec().acquisition != "bernoulli_pacing"
        )
        if uses_rng:
            res[name] = None
            continue

        def replay(ys: tuple[int, ...], name=name):
            m = make(name, cfg)
            m.start(cfg)
            pending: dict[int, list] = {}
            used = 0
            for t in range(1, T + 1):
                due = tuple(pending.pop(t, ()))
                action, query = m.step(t, due)
                if action == 1:
                    return True, None
                if query:
                    if used >= len(ys):
                        return False, used
                    y = ys[used]
                    used += 1
                    if t + d <= T:
                        pending.setdefault(t + d, []).append((t, float(1 - 2 * y)))
            return False, None

        def value(ys: tuple[int, ...], mode: str) -> float:
            promoted, need = replay(ys)
            if promoted:
                return 1.0
            if need is None:
                return 0.0
            z, o = value(ys + (0,), mode), value(ys + (1,), mode)
            return (z + o) / 2 if mode == "iid" else max(z, (z + o) / 2)

        res[name] = {"iid": value((), "iid"), "causal": value((), "causal")}
    return {"key": f"T{T}_B{B}_d{d}", "exact": res}


def _dispatch(job: tuple) -> dict:
    kind, arg = job
    return {"alt": mc_alt_task, "null": mc_null_task, "exact": exact_null_task}[kind](arg)


def _guarded(args: tuple) -> dict:
    fn, arg = args
    try:
        return fn(arg)
    except MemoryError as exc:
        return {"error": f"MemoryError: {exc}", "task_error": "MemoryError", "stage": "worker"}


def run_tasks(fn, tasks: list, workers: int, per_child: int | None, tag: str, t0: float) -> list:
    """Map ``fn`` over tasks in processes, surviving killed workers (rebuild pool, then serial)."""
    results: list = [None] * len(tasks)
    todo = list(range(len(tasks)))
    for attempt, w in enumerate((workers, max(1, workers // 2), 1)):
        if not todo:
            break
        broken = []
        t_start = {}
        try:
            with ProcessPoolExecutor(max_workers=w, max_tasks_per_child=per_child) as ex:
                futs = {}
                for i in todo:
                    t_start[i] = time.time()
                    futs[ex.submit(_guarded, (fn, tasks[i]))] = i
                for f in as_completed(futs):
                    i = futs[f]
                    try:
                        results[i] = f.result()
                    except BrokenProcessPool:
                        broken.append(i)
        except BrokenProcessPool:
            pass
        todo = [i for i in todo if results[i] is None]
        if todo:
            print(
                f"[{time.time() - t0:6.0f}s] {tag}: pool broken (attempt {attempt}), "
                f"{len(todo)} tasks to retry with fewer workers",
                flush=True,
            )
    for i in todo:  # still unfinished after a single-worker retry: killed by the OS (memory)
        results[i] = {
            "error": "worker killed by the OS (out of memory) even with one worker",
            "task_error": "killed",
            "stage": "worker",
            "seconds": None,
        }
    return results


# ----------------------------------------------------------------------------- aggregation


def ci(x) -> list[float]:
    m, lo, hi = paired_ci(np.asarray(x, dtype=float))
    return [m, lo, hi]


def wilson_ci(k: int, n: int) -> list[float]:
    from shiftlab.dive.switching_explore import wilson

    return list(wilson(k, n))


def merge_alt(parts: list[dict]) -> dict:
    out: dict[str, dict[str, list]] = {}
    for p in parts:
        for name, rec in p["methods"].items():
            slot = out.setdefault(name, {k: [] for k in rec})
            for k, v in rec.items():
                slot[k] += v
    return out


def summarise_cell(cell, lp, alt, null_fp, exact) -> dict:
    n = len(next(iter(alt.values()))["rb"])
    methods = {}
    for name, rec in alt.items():
        fp = null_fp[name]
        ex = exact.get(name)
        methods[name] = {
            "cost_rb": ci(rec["rb"]),
            "cost_realised": ci(rec["real"]),
            "queries": float(np.mean(rec["q"])),
            "switches": float(np.mean(rec["sw"])),
            "alt_promotion_freq": float(np.mean(rec["promo"])),
            "mc_null_risk": float(np.mean(fp)),
            "mc_null_risk_ci": wilson_ci(int(np.sum(fp)), len(fp)),
            "exact_null_iid": None if ex is None else ex["iid"],
            "exact_null_causal": None if ex is None else ex["causal"],
        }
    # best_safe: lowest MC cost among no_switch and the gated baselines with MC null risk <= alpha
    pool = [fa.FLOOR, *fa.gated_methods()]
    safe = [m for m in pool if methods[m]["mc_null_risk"] <= ALPHA]
    best = min(safe, key=lambda m: methods[m]["cost_rb"][0])
    V_valid, V_free = lp["V_valid"], lp["V_free"]
    rv = methods["ref_valid"]["cost_rb"]
    bs = methods[best]["cost_rb"]
    return {
        **cell,
        "n_seeds": n,
        "V_free": V_free,
        "V_valid": V_valid,
        "CoV": V_valid - V_free,
        "lp": lp,
        "methods": methods,
        "best_safe": best,
        "RC": rv[0] - V_valid,
        "RC_ci": [rv[1] - V_valid, rv[2] - V_valid],
        "best_safe_gap": bs[0] - V_valid,
        "best_safe_gap_ci": [bs[1] - V_valid, bs[2] - V_valid],
        "RC_gt_CoV": bool(rv[0] - V_valid > V_valid - V_free),
    }


def fmt_c(c) -> str:
    return f"{c[0]:.4f} ± {(c[2] - c[1]) / 2:.4f}"


def render(rows: list[dict], skipped: list[dict], meta: dict) -> str:
    L = [
        "# Exact cost of validity (Failure Atlas v1, Amendment 6 item 1)",
        "",
        (
            f"Seeds per cell: {meta['n_seeds']}. Costs are expected TOTAL cost over T rounds "
            "(decision loss + 0.01 per query + 0.1 per switch), the solver's contract; "
            "MC entries are mean ± 95% half-width (paired-t across seeds, Rao-Blackwellised over "
            "unqueried labels). `null` = MC null risk under iid P(Y=1)=1/2 (P(ever act 1)); "
            "`xc` = exact best-response causal-null risk of the harness method (solver definition)."
        ),
        "",
        "| cell | V_free | V_valid | CoV | R_valid cost / null | best_safe (name) cost / null | no_switch cost / null | straddle cost / null / xc | RC | best_safe - V_valid |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        M = r["methods"]

        def cn(m, M=M):
            x = M[m]
            return f"{fmt_c(x['cost_rb'])} / {x['mc_null_risk']:.3f}"

        st = M["straddle"]
        xc = "n/a" if st["exact_null_causal"] is None else f"{st['exact_null_causal']:.3f}"
        L.append(
            f"| {r['id']} | {r['V_free']:.4f} | {r['V_valid']:.4f} | {r['CoV']:+.4f} | {cn('ref_valid')} | "
            f"{r['best_safe']}: {cn(r['best_safe'])} | {cn('no_switch')} | {cn('straddle')} / {xc} | "
            f"{r['RC']:+.4f} | {r['best_safe_gap']:+.4f} |"
        )
    n_solved = len(rows)
    n_gt = sum(r["RC_gt_CoV"] for r in rows)
    L += ["", "## Locked reading", ""]
    if n_solved:
        verdict = (
            "RC > CoV in a majority of solved cells: the cycle-3/4 `cost_of_validity` labels are "
            "attributed mainly to reference conservatism, and the family-1 headroom question is reopened."
            if n_gt > n_solved / 2
            else "RC > CoV in at most half of solved cells: the `cost_of_validity` labels stand at small T."
        )
        L += [
            f"RC > CoV in {n_gt} of {n_solved} solved cells ({n_gt / n_solved:.0%}).",
            "",
            f"**Verdict:** {verdict} Extrapolation to T = 1000 is not claimed.",
        ]
    else:
        L.append("No solved cells; no verdict.")
    L += ["", f"## Skipped cells ({len(skipped)})", ""]
    if skipped:
        L += ["| cell | stage | seconds | error |", "|---|---|---|---|"]
        for s in skipped:
            L.append(
                f"| {s['id']} | {s.get('stage', '')} | {s.get('seconds', '')} | {s['error'][:90]} |"
            )
    else:
        L.append("None.")
    L += ["", f"Runtime: {meta['seconds']:.0f} s wall ({meta['workers']} workers).", ""]
    return "\n".join(L)


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=False, cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=5000)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument(
        "--out", default=str(ROOT / "outputs" / "failure_atlas_v1_cycle5" / "exact_cov")
    )
    a = ap.parse_args()
    workers = min(a.workers, 6)
    t0 = time.time()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = cell_list(a.smoke)
    seed_list = fa.seeds("mechanism", a.n_seeds, offset=SEED_OFFSET)
    chunks = [seed_list[i : i + CHUNK] for i in range(0, len(seed_list), CHUNK)]
    groups = sorted({(c["T"], c["B"], c["d"]) for c in cells})
    print(f"{len(cells)} cells, {len(groups)} (T,B,d) groups, {len(seed_list)} seeds", flush=True)

    # Phase 1: exact LPs, one fresh process per task (the big trees can exhaust memory).
    lp_res = run_tasks(lp_task, cells, workers, per_child=1, tag="lp", t0=t0)
    lp: dict[str, dict] = {}
    for c, r in zip(cells, lp_res, strict=True):
        lp[c["id"]] = r
        print(
            f"[{time.time() - t0:6.0f}s] lp {c['id']}: "
            + (
                r["error"][:60]
                if "error" in r
                else f"V_valid={r['V_valid']:.4f} V_free={r['V_free']:.4f} ({r['seconds']}s)"
            ),
            flush=True,
        )
    # Phase 2: Monte Carlo (alternative only on solved cells), shared null MC and exact null risks.
    solved = [c for c in cells if "error" not in lp[c["id"]]]
    jobs: list[tuple] = []
    for c in solved:
        jobs += [("alt", c["id"], (c, ch)) for ch in chunks]
    for g in groups:
        jobs.append(("exact", g, g))
        jobs += [("null", g, (g, ch)) for ch in chunks]
    fns = {"alt": mc_alt_task, "null": mc_null_task, "exact": exact_null_task}
    out_res = run_tasks(
        _dispatch,
        [(fns_name, arg) for fns_name, _, arg in jobs],
        workers,
        per_child=None,
        tag="mc",
        t0=t0,
    )
    alt_parts: dict[str, list] = {c["id"]: [] for c in cells}
    null_parts: dict[tuple, list] = {g: [] for g in groups}
    exact: dict[tuple, dict] = {}
    for (kind, key, _), res in zip(jobs, out_res, strict=True):
        if "task_error" in res:
            raise RuntimeError(f"{kind} task {key} failed: {res['task_error']}")
        if kind == "alt":
            alt_parts[key].append(res)
        elif kind == "null":
            null_parts[key].append(res)
        else:
            exact[key] = res["exact"]
    del fns
    # aggregate
    rows, skipped = [], []
    null_fp: dict[tuple, dict[str, list]] = {}
    for g, parts in null_parts.items():
        merged: dict[str, list] = {}
        for p in parts:
            for n, v in p["fp"].items():
                merged.setdefault(n, []).extend(v)
        null_fp[g] = merged
    for c in cells:
        r = lp[c["id"]]
        if "error" in r:
            skipped.append({**c, **r})
            continue
        g = (c["T"], c["B"], c["d"])
        rows.append(summarise_cell(c, r, merge_alt(alt_parts[c["id"]]), null_fp[g], exact[g]))
    meta = {
        "n_seeds": len(seed_list),
        "seed_range": [seed_list[0], seed_list[-1]],
        "workers": workers,
        "seconds": time.time() - t0,
        "git_head": git_head(),
        "max_nodes": MAX_NODES,
        "alpha": ALPHA,
        "straddle_spec": STRADDLE_ID,
        "methods": list(method_names()),
        "n_solved": len(rows),
        "n_skipped": len(skipped),
        "n_RC_gt_CoV": int(sum(r["RC_gt_CoV"] for r in rows)),
    }
    (out_dir / "results.json").write_text(
        json.dumps({"meta": meta, "cells": rows, "skipped": skipped}, indent=1, default=float),
        encoding="utf-8",
    )
    (out_dir / "summary.md").write_text(render(rows, skipped, meta), encoding="utf-8")
    print(
        f"solved {len(rows)}, skipped {len(skipped)}, RC>CoV {meta['n_RC_gt_CoV']}; "
        f"{meta['seconds']:.0f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
