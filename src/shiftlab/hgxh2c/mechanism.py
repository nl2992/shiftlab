"""Additive helpers for the A7 mechanism stage (docs/hgxh2c/PROTOCOL.md, Amendment A7). No existing behaviour is changed.

M2: source-track replacement from an independent seed stream (target track, tau and scoring untouched).
M3: stake-matched no-transfer controls (constant add-on / multiplier on mix_w0.5, clipped by the engine so factors >= 0).
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

from shiftlab.hgxh2c import baselines as BL
from shiftlab.hgxh2c import grammar as G
from shiftlab.hgxh2c import tapes as TP

MULTS = (1.0, 1.1, 1.2, 1.3, 1.5, 2.0)
SALT = "|a7_indep_source"


@contextmanager
def salted_streams(salt=SALT):
    """Temporarily key every tape generator stream on ``key + salt`` (calibration stays on its own key)."""
    TP.calibrate()  # cached: make sure theta/sd come from the unsalted calibration stream
    orig = TP.seed_of
    TP.seed_of = lambda base, key, i: orig(base, key + salt, i)
    try:
        yield
    finally:
        TP.seed_of = orig


def generate_indep(cell, partition, n_seeds, device="cpu", seed0=0, salt=SALT):
    """Same cell / partition / seed indices as TP.generate, but drawn from an independent (salted) generator key."""
    with salted_streams(salt):
        return TP.generate(cell, partition, n_seeds, device, seed0)


def source_channels(cand: G.Candidate) -> str:
    """Source channels ('B', 'C', 'BC' or '') of the directions in which the candidate has any operator."""
    s = ""
    for d in G.DIRS:
        if any(cand.slot(d, ch) for ch in G.CHANS):
            s += G.SRC[d]
    return "".join(sorted(s))


def replace_source(tape: dict, alt: dict, chans: str) -> dict:
    """Monitor-side tape: source channel outcomes and proxies from ``alt``; everything else (target track, d, U, eval
    incl. tau) is the original object. Release times d are cell constants, so they coincide by construction."""
    t = dict(tape)
    for ch in chans:
        t[ch], t[ch + "hat"] = alt[ch], alt[ch + "hat"]
    return t


def _clipped_hook(fn):
    fn.static = True  # elementwise in ctx.base only
    return fn


def mix_control(add=None, mult=None, w=0.5):
    """mix_w{w} with a cross-track-information-free stake change: base stake + add[track] (>= 0) and/or * mult (> 0).
    The engine then clips stakes to [0, hi], so every e-factor stays non-negative."""
    mon = BL.fixed_mix(w)
    for n in "BC":
        a = float((add or {}).get(n, 0.0))
        m = 1.0 if mult is None else float(mult)
        if a < 0 or m <= 0:
            raise ValueError("stake add-on must be >= 0 and multiplier > 0")
        if a != 0.0 or m != 1.0:
            mon.hooks.stake[n] = _clipped_hook(lambda ctx, lam, a=a, m=m: lam * m + a)
    if mult is not None or add:
        mon.name = f"mix_w{w}|stake"
    return mon


def shift_only(cand: G.Candidate) -> G.Candidate:
    """Candidate with only its 'shift' stake operators kept."""
    sl = []
    for i, (d, ch) in enumerate(G.SLOTS):
        sl.append(tuple((o, p) for o, p in cand.slots[i] if ch == "S" and o == "shift"))
    return replace(cand, slots=tuple(sl))


def measure_shift_addon(cand: G.Candidate, tape: dict) -> dict:
    """Mean per-track pre-clip stake add-on {B: .., C: ..} of the candidate's shift operator on ``tape`` (all steps)."""
    cs = shift_only(cand)
    out = {"B": 0.0, "C": 0.0}
    if not any(cs.slots):
        return out
    mon = G.compile_batch([cs])
    acc = {}
    for n, f in list(mon.hooks.stake.items()):

        def w(ctx, lam, f=f, n=n):
            o = f(ctx, lam)
            s = acc.setdefault(n, [0.0, 0])
            s[0] += float((o - lam).sum())
            s[1] += o.numel()
            return o

        mon.hooks.stake[n] = w
    mon.run(tape)
    for n, (tot, cnt) in acc.items():
        out[n] = max(tot / max(cnt, 1), 0.0)
    return out


# ------------------------------------------------------------------ frozen M3 parameters
PARAMS = "m3_params.json"
SHA = "m3_params.sha256"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze_m3(out: Path, params: dict) -> str:
    out.mkdir(parents=True, exist_ok=True)
    p = out / PARAMS
    p.write_text(json.dumps(params, indent=1, sort_keys=True), "utf-8")
    h = _sha(p)
    (out / SHA).write_text(h, "utf-8")
    return h


def verify_m3(out: Path) -> dict:
    """Raise unless the frozen M3 parameters exist and match their recorded sha. Called before any confirm tape is drawn."""
    p, s = out / PARAMS, out / SHA
    if not p.exists() or not s.exists():
        raise RuntimeError("M3 parameters not frozen: run the dev-seed selection first")
    if _sha(p) != s.read_text("utf-8").strip():
        raise RuntimeError("M3 parameters changed after freeze")
    return json.loads(p.read_text("utf-8"))


def chunked(cells, n_seeds, max_seeds):
    i = 0
    while i < len(cells):
        j, tot = i, 0
        while j < len(cells) and (tot + n_seeds(cells[j]) <= max_seeds or j == i):
            tot += n_seeds(cells[j])
            j += 1
        yield cells[i:j]
        i = j


def select_m3(fin_cands, cells, n_seeds, device, score_fn, max_seeds=4096, mults=MULTS):
    """DEV-seed selection. Returns the params dict: per-finalist mean shift add-on and the best multiplier m by minimum
    equal-cell cumulative J of mix_w0.5 * m over ``cells`` (dev partition, ``n_seeds`` seeds per cell)."""
    tot = {h.hash: {"B": 0.0, "C": 0.0} for h in fin_cands}
    cnt = 0.0
    jsum = {m: 0.0 for m in mults}
    ncell = 0
    for chunk in chunked(cells, lambda c: n_seeds, max_seeds):
        tape = TP.cat_tapes([TP.generate(c, "dev", n_seeds, device) for c in chunk])
        w = len(chunk)
        for c in fin_cands:
            a = measure_shift_addon(c, tape)
            for n in "BC":
                tot[c.hash][n] += a[n] * w
        cnt += w
        for m in mults:
            res = mix_control(mult=m).run(tape)
            df = score_fn(res, tape, "J", 0, f"mix_w0.5|m{m}")
            jsum[m] += float(df.groupby("cell_id").J_cost.mean().sum())
        ncell += w
        del tape
    return {
        "addon": {h: {n: v / max(cnt, 1) for n, v in d.items()} for h, d in tot.items()},
        "mult_J": {str(m): jsum[m] / max(ncell, 1) for m in mults},
        "mult": float(min(mults, key=lambda m: jsum[m])),
        "dev_cells": ncell,
        "dev_seeds_per_cell": n_seeds,
    }
