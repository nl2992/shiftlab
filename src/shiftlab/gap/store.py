"""Per-seed experiment storage, append-only registry and a parallel grid runner.

Per-seed records are the primary data; aggregates are derived by ``summarise`` and never replace them.
Peak memory is the process high-water mark (ru_maxrss) and runtime the batch wall time divided by the
number of seeds: both are batch-level quantities (seeds are vectorised), recorded as such.
"""

from __future__ import annotations

import hashlib
import json
import resource
import sqlite3
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.gap import engine as E
from shiftlab.sota_search import generators as g

ROOT = Path("outputs/gap_closure")


def cfg_hash(cfg: E.Cfg, extra: dict | None = None) -> str:
    return hashlib.sha256(
        json.dumps({**cfg.tag(), **(extra or {})}, sort_keys=True, default=str).encode()
    ).hexdigest()[:12]


def commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


@dataclass
class WorldSpec:
    """A synthetic world: ``make(S, seed)`` builds the stream, ``delay`` the label-delay model."""

    name: str
    make: Callable
    delay: object = 5  # int, or callable(stream) -> (S, T) int array
    role_hint: str = ""
    group: str = ""
    meta: dict | None = None


def g1_stream(world: g.World, S: int, seed: int) -> dict:
    """Legacy G1/G2 world through the new engine: adds proxies, nominal risks and the true label law."""
    sim = g.simulate(world, S, seed)
    x = sim["x"].astype(float)
    m = g.schedule(world.shape, world.T, world.t0, world.ramp, world.length, world.period)
    _dmu, dw, db, dsub = g._delta_terms(world.kind, world.delta)
    w = g.W_SRC[None, None, :] + m[None, :, None] * dw
    logit = (x * w).sum(-1) + g.B_SRC + m * db + m * dsub * (x[:, :, 2] > 1.0)
    if world.family == "G2":
        logit = logit + g.nonlinear_term(x)
    sim = E.ensure_stream(sim)
    sim["pi_true"] = g.sigmoid(logit)
    tr = g.truth(world)
    sim["truth"] = {
        "harm": tr["harm"],
        "predictive": tr["predictive"],
        "discrepancy": tr["discrepancy"],
        "thr": g.HARM_THRESHOLD,
    }
    return sim


def dev_worlds_g1() -> list[WorldSpec]:
    from shiftlab.sota_search import harness as h

    return [
        WorldSpec(
            f"G1|{w.kind}|{w.shape}|{w.delta:g}",
            lambda S, sd, w=w: g1_stream(w, S, sd),
            5,
            h.role(w),
            "G1dev",
        )
        for w in h.dev_pool()
    ]


def _delay_arr(spec: WorldSpec, st: dict):
    return spec.delay(st) if callable(spec.delay) else spec.delay


def run_cell(
    spec: WorldSpec, st: dict, cfg: E.Cfg, seed0: int, qseed: int, exp: str, cname: str
) -> pd.DataFrame:
    S, T = st["loss"].shape
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time.perf_counter()
    res = E.run(st, cfg, delay=_delay_arr(spec, st), qseed=qseed)
    wall = time.perf_counter() - t0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    stats = E.alarm_stats(res["alarm"], st["truth"], T)
    return pd.DataFrame(
        {
            "exp": exp,
            "T": T,
            "world": spec.name,
            "group": spec.group,
            "config": cname,
            "cfg_hash": cfg_hash(cfg),
            "seed": seed0 + np.arange(S),
            "qseed": qseed,
            "alarm_t": res["alarm"],
            "first_harm": stats["first_harm"],
            "false_alarm": stats["false_alarm"],
            "detected": stats["detected"],
            "delay": stats["delay"],
            "harm_before": stats["harm_before"],
            "labels": res["labels"],
            "mean_label_delay": res["mean_label_delay"],
            "last_label_arrival": res["last_label_arrival"],
            "labels_rare": res["labels_rare"],
            "mean_pending": res["mean_pending"],
            "max_pending": res["max_pending"],
            "exhaust_t": res["exhaust_t"],
            "runtime_s_per_seed": wall / S,
            "batch_runtime_s": wall,
            "peak_rss_mb": peak,
            "rss_delta_mb": (peak - rss0 / 1024.0),
        }
    )


_JOBS: list = []  # inherited by forked workers (specs hold lambdas, which cannot be pickled)


def _worker(i):
    spec, cfgs, S, seed0, qseed, exp = _JOBS[i]
    st = spec.make(S, seed0)
    out = [run_cell(spec, st, cfg, seed0, qseed, exp, cname) for cname, cfg in cfgs.items()]
    return pd.concat(out, ignore_index=True)


def run_grid(
    exp: str,
    specs: list[WorldSpec],
    cfgs: dict[str, E.Cfg],
    S: int = 200,
    seed0: int = 1000,
    qseed: int = 0,
    procs: int = 4,
    note: str = "",
) -> pd.DataFrame:
    """Run every (world, config) cell; world w uses seed0 + 1000 * w so all configs share the same worlds."""
    d = ROOT / exp
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    jobs = [(sp, cfgs, S, seed0 + 1000 * i, qseed, exp) for i, sp in enumerate(specs)]
    _JOBS[:] = jobs
    if procs > 1:
        with get_context("fork").Pool(procs) as pool:
            parts = pool.map(_worker, range(len(jobs)), chunksize=1)
    else:
        parts = [_worker(i) for i in range(len(jobs))]
    df = pd.concat(parts, ignore_index=True)
    df.to_parquet(d / "perseed.parquet", index=False)
    wall = time.time() - t0
    register(exp, cfgs, specs, S, seed0, qseed, wall, len(df), note)
    return df


def register(exp, cfgs, specs, S, seed0, qseed, wall, nrows, note):
    ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ROOT / "registry.sqlite")
    con.execute(
        "CREATE TABLE IF NOT EXISTS runs (ts REAL, exp TEXT, config TEXT, cfg_hash TEXT, cfg_json TEXT, n_worlds INT, seeds_per_world INT, seed0 INT, qseed INT, commit_sha TEXT, wall_s REAL, perseed_rows INT, note TEXT)"
    )
    sha = commit()
    for name, cfg in cfgs.items():
        con.execute(
            "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                time.time(),
                exp,
                name,
                cfg_hash(cfg),
                json.dumps(cfg.tag(), default=str),
                len(specs),
                S,
                seed0,
                qseed,
                sha,
                wall,
                nrows,
                note,
            ),
        )
    con.commit()
    con.close()


def wilson(k, n, z=1.96):
    n = np.maximum(n, 1)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - hw, c + hw


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Per (config, world): power among seeds with a harmful step, false alarm over all seeds, harm before alarm.

    A world is a harm world when most of its seeds contain a harmful step. Aggregates are derived only.
    """
    df = df.assign(has_harm=df.first_harm < df["T"])
    g_ = df.groupby(["config", "world", "group"], sort=False)
    out = g_.agg(
        n=("seed", "size"),
        n_harm=("has_harm", "sum"),
        det=("detected", "sum"),
        fa=("false_alarm", "mean"),
        harm_before=("harm_before", "mean"),
        labels=("labels", "mean"),
        runtime_s_per_seed=("runtime_s_per_seed", "mean"),
    ).reset_index()
    out["power"] = np.where(out.n_harm > 0, out.det / out.n_harm.clip(lower=1), np.nan)
    out["role"] = np.where(out.n_harm / out.n > 0.5, "harm", "nonharm")
    dly = df[df.delay >= 0].groupby(["config", "world"]).delay.mean().rename("delay").reset_index()
    return out.merge(dly, on=["config", "world"], how="left")


def table(sm: pd.DataFrame) -> pd.DataFrame:
    """Per-config: mean harm-world power, mean non-harm-world false alarm, mean harm before alarm (harm worlds)."""
    h = (
        sm[sm.role == "harm"]
        .groupby("config")
        .agg(
            power=("power", "mean"),
            harm_before=("harm_before", "mean"),
            delay=("delay", "mean"),
            labels=("labels", "mean"),
        )
    )
    nh = (
        sm[sm.role == "nonharm"]
        .groupby("config")
        .agg(fa_nonharm=("fa", "mean"), fa_max=("fa", "max"))
    )
    return h.join(nh)
