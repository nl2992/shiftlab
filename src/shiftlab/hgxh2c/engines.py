"""Batched betting-monitor framework for the HG x H2c programme (PROTOCOL sections 2, 6).

One python loop over t; every op is vectorised over a leading [K, S] block (K candidates sharing a
tape x S seeds, S may stack many cells: see ``tapes.cat_tapes``). All math is float64.

Event semantics (what a monitor may know at step t)
  * proxies h_t, the design constants (delay, budget, theta, pmax, q floor) are free at issue;
  * the label (B_t, C_t) is revealed only if Q_t = 1 and then only at arrival t + d_t;
  * ``release="prefix"``: an unqueried event's proxy-only increment arrives at t, a queried event at
    t + d_t (gap-closure engine semantics); the wealth factor is released in order (running max of
    arrivals), so wealth is a supermartingale for any delay mechanism.
    ``release="legacy"``: every event (queried or not) arrives at t + d_t (sota_search semantics).
  * the stake used at step t is computed from arrivals <= t-1 only (``Ring`` buckets); a factor is
    1 + lam_t * x_t with x_t = h + (Q/q)(R - h) - theta (prediction-powered / Csillag form) and lam_t
    clipped to [0, cap/Bd], Bd = pmax*(1/q_floor - 1) + theta, so factors stay >= 1 - cap surely.
  * query: Q_t = U_t < q_t, q_t in [q_floor, 1] or exactly 0 once the pathwise budget is spent (the
    event is then inactive: factor 1, no moments).

Hook API (stage-3 grammar plugs in here; all hooks see only predictable state through ``Ctx``)
  Hooks(query=f, stake={name: g}, restart={name: r}, after_step=a)
    query(ctx, q) -> q'            S/Q channel: q [K,S] base query prob; returned value is clamped to
                                   [q_floor, 1] (then zeroed when the budget is spent).
    stake(ctx, lam) -> lam'        S channel for track ``name``: lam [K,S] is that track's base stake
                                   (min(Kelly|ONS|..., cap/Bd)). The result is clamped to [0, cap/Bd], so
                                   typing (factor >= 0) holds for any hook.
    restart(ctx) -> bool|float [K,S]  R channel: True resets the track's moment / ONS / grid state; a float
                                   in [0,1] is the fraction of that state kept (soft start component).
    gamma(ctx, gam) -> [K,S]       R channel: discount factor used when released moments are absorbed.
    after_step(ctx, Q, arr)        optional: lets a hook keep its own released state via
                                   ``ctx.defer(key, arrival, value)`` / ``ctx.collect(key)``.
    declare(ctx)                   optional: allocate hook state / ``ctx.make_aux(key, shape)`` buckets before step 0.
  ``Monitor(graph=True)`` captures the whole step in a CUDA graph (one launch per step). Requirements: all hook
  state updated in place, no python branching on tensor values or on ``ctx.t`` (a device tensor in graph mode;
  ``ctx.tt`` is always the device step counter), aux buckets declared. A failed capture falls back to eager.
  ``ctx`` exposes: t, tt, spent, budget, q0, qfloor, h[name] ([S] proxy at t, free), logW[name]
  (released log-wealth), base[name] (clipped base stake, filled for every track before any stake hook
  runs), kelly[name] (raw Kelly ratio, unclipped), mean[name]/second[name] (discounted released
  moments), hi[name] (= cap/Bd), bd[name], and ``res_scale(name, h)`` (sqrt released residual second
  moment of the proxy bin, needs TrackSpec.bins > 0).
  Special cases of the grammar: H2c = stake channel B->C with ``ratio_guidance('B','C')`` (a
  non-betting guide track B + a betting track C); HG = stake channel C->B with ``sign_gate('C')``.

Everything here is a pure function of the tape's free/released fields; ``tape["eval"]`` is never read.
"""

from __future__ import annotations

import math
import types
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ClassVar

import torch

# tiny [K,S] ops: intra-op threading only adds spin-wait time (100x slower on a loaded machine)
torch.set_num_threads(1)

ALPHA = 0.05
LOG_THR = math.log(1 / ALPHA)
ONS_C = 2.0 / (2.0 - math.log(3.0))
GRAPA_GRID = [k / 10 for k in range(1, 20)]


class Ring:
    """Arrival-time buckets: add(key, arrival, value) sums into slot arrival % R; pop frees it."""

    def __init__(self, R):
        self.R, self.b = R, {}

    def add(self, key, arr, val):
        buf = self.b.get(key)
        if buf is None:
            buf = self.b[key] = torch.zeros(
                (self.R,) + tuple(val.shape), dtype=val.dtype, device=val.device
            )
        idx = (arr % self.R).view((1,) * (1 + val.dim() - arr.dim()) + tuple(arr.shape))
        buf.scatter_add_(0, idx.expand((1,) + tuple(val.shape)).contiguous(), val.unsqueeze(0))

    def make(self, key, shape, device):
        if key not in self.b:
            self.b[key] = torch.zeros((self.R,) + tuple(shape), dtype=torch.float64, device=device)

    def pop(self, key, a):
        """Read and clear slot a % R; a is a python int or a 0-d long tensor (graph-capturable)."""
        buf = self.b.get(key)
        if buf is None:
            return None
        if isinstance(a, int):
            v = buf[a % self.R].clone()
            buf[a % self.R] = 0
            return v
        i = (a % self.R).view(1)
        v = buf.index_select(0, i)[0]
        buf.index_fill_(0, i, 0.0)
        return v


def _p(x, K, dev):
    """Scalar or length-K list -> tensor broadcastable to [K, S]."""
    return torch.as_tensor(x, dtype=torch.float64, device=dev).reshape(-1, 1).expand(K, 1)


@dataclass
class TrackSpec:
    name: str  # 'B' or 'C': which tape channel (R = tape[name], proxy = tape[name + 'hat'])
    base: str = "kelly"  # kelly | ons | fixed | grapa | grapa_grid
    gamma: object = 1.0  # discount of released moments (scalar or per-candidate list)
    cap: float = 0.5
    bet: bool = True  # False: state is maintained (guide / gate), no wealth is accumulated
    corr: str = (
        "pp"  # pp | ipw (no proxy) | csillag (stake from queried labels only) | eta (PPRM reliance)
    )
    factor: str = "log1p"  # log1p | lrt (Gaussian likelihood-ratio e-factor, different null)
    lam: object = 0.0  # fixed stake for base='fixed' (fraction of cap/Bd)
    burn_in: int = 100  # grapa: events before betting
    bins: int = 0  # >0: keep released residual-variance statistics per proxy bin
    proxy_only: bool = False  # imputed variant: pretend the proxy is the label (no queries needed)
    ch: str = (
        ""  # tape channel, default = name (lets one monitor hold two tracks on the same channel)
    )
    role: str = ""  # 'B' | 'C' key of the alarm / J combiner (bet tracks), default = channel

    def __post_init__(self):
        self.ch = self.ch or self.name
        self.role = self.role or self.ch


@dataclass
class Hooks:
    query: Callable | None = None
    stake: dict = field(default_factory=dict)
    restart: dict = field(default_factory=dict)
    after_step: Callable | None = None
    gamma: dict = field(
        default_factory=dict
    )  # R channel: track name -> f(ctx, gam [K,1]) -> discount at absorb
    declare: Callable | None = (
        None  # f(ctx): called once per run before the first step; allocate state / aux buffers here
    )


def _static(f):
    f.static = True  # elementwise in ctx.base/mean/second/kelly/hi/bd only: also valid on [K,S,T] tensors (fast path)
    return f


def ratio_guidance(src: str, dst: str):
    """H2c-style S operator: the dst stake is the src base stake re-expressed on dst's interval."""
    return _static(lambda ctx, lam: ctx.base[src] * ctx.bd[src] / ctx.bd[dst])


def sign_gate(src: str):
    """HG-style S operator: stake is switched off unless src's discounted released mean is > 0."""
    return _static(lambda ctx, lam: lam * (ctx.mean[src] > 0))


class Ctx:
    """Predictable state handed to hooks (see module docstring)."""

    def __init__(self, ring):
        self.ring, self.logW, self.base, self.mean, self.second = ring, {}, {}, {}, {}
        self.kelly, self.hi, self.bd, self.h, self.res = {}, {}, {}, {}, {}

    def defer(self, key, arr, val):
        self.ring.add("u_" + key, arr, val)

    def collect(self, key):
        return self.ring.pop("u_" + key, self.tt - 1)  # arrivals <= t-1; zeros if nothing arrived

    def make_aux(self, key, shape):
        """Declare a hook-owned arrival bucket (shape excludes the ring dim). Required for graph mode."""
        self.ring.make("u_" + key, shape, self.device)

    def res_scale(self, name, h, n0=5.0):
        rv = self.res[name]
        b = (h / self.pmax[name] * rv.shape[1]).long().clamp(0, rv.shape[1] - 1)  # [S]
        bi = b[None, None, :].expand(1, self.K, -1)
        wv, ww = torch.gather(rv[0], 0, bi)[0], torch.gather(rv[1], 0, bi)[0]
        tot = rv[1].sum(0)
        vbar = torch.where(
            tot > 0, rv[0].sum(0) / tot.clamp(min=1e-9), torch.full_like(tot, 0.0625)
        )
        return ((wv + n0 * vbar) / (ww + n0)).clamp(min=1e-12).sqrt()


@dataclass
class Result:
    ids: list
    alarm: dict  # track name ('B','C','J') -> [K, S] long; T = never
    cumq: object  # [K, S, T] int32 queries issued up to and including t (only with keep_paths, else None)
    logW: dict = field(default_factory=dict)  # only with keep_paths
    lam: dict = field(default_factory=dict)
    tracks: tuple = ()
    lw_mean: dict = field(default_factory=dict)  # role -> [K,S] time-mean released log-wealth
    nq_at: dict = field(
        default_factory=dict
    )  # role -> [K,S] queries issued up to the first alarm (final spend if none)
    spent: object = None  # [K,S] queries issued over the whole horizon


class Monitor:
    def __init__(self, tracks, ids=None, frac=None, q_floor=None, release="prefix", combiner=None, w=0.5,
                 hooks=None, alpha=ALPHA, name="", fast=True, graph=False):  # fmt: skip
        self.tracks, self.frac, self.q_floor, self.release = tracks, frac, q_floor, release
        self.comb, self.w, self.hooks, self.name, self.fast, self.graph = (
            combiner,
            w,
            hooks or Hooks(),
            name,
            fast,
            graph,
        )
        self.thr = math.log(1 / alpha)
        lens = [len(v) for tr in tracks for v in (tr.gamma, tr.lam) if isinstance(v, (list, tuple))]
        lens += [len(v) for v in (frac, w, q_floor) if isinstance(v, (list, tuple))]
        self.K = max(lens, default=1)
        self.ids = ids or ([name] if self.K == 1 else [f"{name}_{i}" for i in range(self.K)])

    # ------------------------------------------------------------------ run
    def run(self, tape, keep_paths=False) -> Result:
        if self._fast_ok():
            return self._run_fast(tape, keep_paths)
        if self.graph and tape["B"].device.type == "cuda":
            try:
                return self._run_loop(tape, keep_paths, graph=True)
            except Exception as e:  # noqa: BLE001 - CUDA-graph capture can raise arbitrary errors; fall back to eager
                import warnings

                warnings.warn(
                    f"CUDA-graph capture failed ({type(e).__name__}: {str(e)[:80]}); running eagerly"
                )
        return self._run_loop(tape, keep_paths, graph=False)

    # ------------------------------------------------------------------ vectorised path
    def _fast_ok(self):
        h = self.hooks
        if (
            not self.fast
            or h.query
            or h.restart
            or h.after_step
            or h.gamma
            or self.comb == "linear"
        ):
            return False
        if any(not getattr(f, "static", False) for f in h.stake.values()):
            return False
        if h.stake and any(tr.base == "ons" for tr in self.tracks):
            return False
        for tr in self.tracks:
            if tr.bins or tr.base not in ("kelly", "fixed", "grapa", "grapa_grid", "ons"):
                return False
            if float(torch.as_tensor(tr.gamma, dtype=torch.float64).min()) < 0.9:
                return False
        return True

    def _run_fast(self, tape, keep_paths):
        """Everything that does not feed wealth back into stakes/queries is a function of the tape alone, so it is
        computed for all t at once: query mask (cumsum for the budget), IPW increments, arrival buckets (scatter),
        discounted moments (closed-form decayed cumsum), stakes, factors and prefix release (cummax + scatter +
        cumsum). Only ONS keeps a short python loop over t. Row-chunked to bound memory. Same outputs as the loop."""
        K, tr_list = self.K, self.tracks
        dev, (S, T) = tape["B"].device, tape["B"].shape
        f64 = torch.float64
        roles = [tr.role for tr in tr_list if tr.bet]
        both = {"B", "C"} <= set(roles) and self.comb is not None
        keys = roles + (["J"] if both else [])
        out = {
            "alarm": {k: torch.full((K, S), T, dtype=torch.long, device=dev) for k in keys},
            "nq": {k: torch.zeros(K, S, dtype=f64, device=dev) for k in keys},
            "lw": {k: torch.zeros(K, S, dtype=f64, device=dev) for k in keys},
            "spent": torch.zeros(K, S, dtype=f64, device=dev),
        }
        if keep_paths:
            out["cumq"] = torch.zeros(K, S, T, dtype=torch.int32, device=dev)
            out["paths"] = {
                tr.name: torch.zeros(K, S, T, dtype=f64, device=dev) for tr in tr_list if tr.bet
            }
            out["lams"] = {tr.name: torch.zeros(K, S, T, dtype=f64, device=dev) for tr in tr_list}
            if both:
                out["paths"]["J"] = torch.zeros(K, S, T, dtype=f64, device=dev)
        G = len(GRAPA_GRID) if any(tr.base == "grapa_grid" for tr in tr_list) else 1
        step = max(1, int(12_000_000 // (K * T * G * max(1, len(tr_list)))))
        for s0 in range(0, S, step):
            self._fast_chunk(tape, slice(s0, min(S, s0 + step)), S, out)
        return Result(self.ids, out["alarm"], out.get("cumq"), out.get("paths", {}), out.get("lams", {}), tuple(keys),
                      out["lw"], out["nq"], out["spent"])  # fmt: skip

    def _fast_chunk(self, tape, sl, S, out):
        K, f64 = self.K, torch.float64
        tr_list = self.tracks
        n, T = tape["B"][sl].shape
        dev = tape["B"].device
        F = torch.nn.functional
        U, D = tape["U"][sl][None], tape["d"][sl][None]
        frac = self.frac if self.frac is not None else tape["frac"]
        if isinstance(frac, torch.Tensor) and frac.dim():
            q0 = frac[sl].reshape(1, n).to(f64).expand(K, n)
        else:
            q0 = _p(frac, K, dev).expand(K, n)
        qfl = q0 if self.q_floor is None else q0 * _p(self.q_floor, K, dev)
        qe = torch.maximum(q0, qfl).clamp(max=1.0)[
            ..., None
        ]  # constant per row (no query hook on this path)
        budget = (
            torch.as_tensor(tape.get("budget", T), dtype=f64, device=dev)
            .reshape(-1)
            .expand(S)[sl]
            .reshape(1, n, 1)
        )
        raw = (U < qe) & (qe > 0)
        act = ((raw.cumsum(-1) - raw.long()) < budget) & (qe > 0)  # budget not yet spent before t
        Q = raw & act
        spent = Q.cumsum(-1)
        Qd = Q.to(f64)
        qs = torch.where(act, qe.expand(K, n, T), torch.ones(K, n, T, dtype=f64, device=dev))
        tt = torch.arange(T, device=dev)
        Dm = int(D.max())
        L = T + Dm + 1
        arr = (
            (tt + (D if self.release == "legacy" else torch.where(Q, D, torch.zeros_like(D))))
            .expand(K, n, T)
            .contiguous()
        )
        rel = arr if self.release == "legacy" else torch.cummax(arr, -1).values
        shift = lambda c: F.pad(c[..., : T - 1], (1, 0))
        buck = lambda a, v: torch.zeros(*v.shape[:-1], L, dtype=f64, device=dev).scatter_add_(
            -1, a.expand(v.shape), v
        )

        def dscan(Bv, P, g):
            gp = g**P
            return gp * (Bv / gp).cumsum(-1)

        ctx = types.SimpleNamespace(
            base={}, mean={}, second={}, kelly={}, hi={}, bd={}, qfloor=qfl, h={}
        )
        data = {}
        for tr in tr_list:
            ch, nme = tr.ch, tr.name
            R_, h_ = tape[ch][sl][None], tape[ch + "hat"][sl][None]
            r0, hm = tape["theta"][ch], tape["pmax"][ch]
            if tr.corr == "ipw":
                h_ = torch.zeros_like(h_)
            bd = (hm * (1.0 / qfl - 1.0) + r0)[..., None]
            hi = tr.cap / bd
            bx = torch.maximum(bd, 1.0 / qfl[..., None])
            actx = act | tr.proxy_only
            if tr.proxy_only:
                x = (h_ - r0) * actx
            else:
                eta = 1.0
                if tr.corr == "eta":
                    ev = torch.stack(
                        [
                            Qd,
                            Qd * R_,
                            Qd * h_,
                            Qd * R_ * h_,
                            Qd * h_ * h_,
                            torch.ones_like(Qd),
                            h_.expand(K, n, T),
                            (h_ * h_).expand(K, n, T),
                        ]
                    )
                    dec = 0.99 ** torch.arange(L, device=dev, dtype=f64)
                    e = shift(
                        (dec * (buck(arr, ev) / dec).cumsum(-1))[..., :T]
                    )  # calendar decay .99 per step
                    nl, nu = e[0], e[5].clamp(min=1.0)
                    cov = e[3] / nl.clamp(min=1.0) - (e[1] / nl.clamp(min=1.0)) * (
                        e[2] / nl.clamp(min=1.0)
                    )
                    varh = (e[7] / nu - (e[6] / nu) ** 2).clamp(min=0.0)
                    eta = torch.where(
                        (nl >= 2) & (varh > 1e-12),
                        (cov / ((1 + nl / nu) * varh.clamp(min=1e-12))).clamp(0.0, 1.0),
                        torch.ones_like(cov),
                    )
                x = (eta * h_ + (Qd / qs) * (R_ - eta * h_) - r0) * actx
            if tr.corr == "csillag":
                mx, cnt, arr_m = Qd * (R_ - r0), Qd, (tt + D).expand(K, n, T).contiguous()
            else:
                mx, cnt, arr_m = x, actx.to(f64), arr
            data[nme] = {"x": x, "actx": actx, "hi": hi}
            g = _p(tr.gamma, K, dev)[..., None]
            P = buck(arr_m, cnt).cumsum(-1)
            c1, c2, cn = (shift(dscan(buck(arr_m, v), P, g)[..., :T]) for v in (mx, mx * mx, cnt))
            mean, second = c1 / (cn + 1.0), c2 / (cn + 1.0)
            kel = torch.where(
                second > 0, mean.clamp(min=0.0) / second.clamp(min=1e-12), torch.zeros_like(mean)
            )
            if tr.base == "kelly":
                lam = torch.minimum(kel, hi)
            elif tr.base == "fixed":
                lam = (_p(tr.lam, K, dev)[..., None] * hi).expand(K, n, T)
            elif tr.base == "grapa":
                m = c1 / cn.clamp(min=1.0)
                mu = m / (2 * bx) + 1e-10
                var = ((c2 - cn * m * m) / (cn - 1).clamp(min=1.0)) / (4 * bx**2) + 1e-10
                bet = (mu / (var + mu**2) + 1e-10).clamp(0.0, 1.0)
                lam = torch.where(cn >= tr.burn_in, bet, torch.zeros_like(bet)) / (2 * bx)
            elif tr.base == "grapa_grid":
                grid = torch.tensor(GRAPA_GRID, dtype=f64, device=dev)
                cl = shift(
                    buck(
                        arr_m, torch.log1p(grid[:, None, None, None] * x[None] / (2 * bx[None]))
                    ).cumsum(-1)[..., :T]
                )
                lam = torch.where(
                    cn >= tr.burn_in, grid[cl.argmax(0)] / (2 * bx), torch.zeros_like(mean)
                )
            else:  # ons: short sequential loop on the precomputed increments
                lam = self._ons_path(x, arr, hi[..., 0])
            if tr.base not in ("grapa", "grapa_grid"):
                lam = lam.clamp(min=0.0)
            (
                ctx.base[nme],
                ctx.mean[nme],
                ctx.second[nme],
                ctx.kelly[nme],
                ctx.hi[nme],
                ctx.bd[nme],
            ) = lam, mean, second, kel, hi, bd
        wealth = {}
        for tr in tr_list:
            nme, d = tr.name, data[tr.name]
            lam = ctx.base[nme]
            if nme in self.hooks.stake:
                lam = self.hooks.stake[nme](ctx, lam)
            if tr.base not in ("grapa", "grapa_grid"):
                lam = torch.minimum(lam.clamp(min=0.0), d["hi"])
            else:  # A3.3: clamp after the hooks, independent of parameter ranges
                lam = torch.minimum(lam.clamp(min=0.0), 0.95 / ctx.bd[nme])
            lam = lam * d["actx"]
            if "lams" in out:
                out["lams"][nme][:, sl] = lam
            if not tr.bet:
                continue
            if tr.factor == "lrt":
                v = ctx.second[nme].clamp(min=1e-12)
                dl = ctx.mean[nme].clamp(min=0.0)
                logf = (dl * d["x"] / v - dl**2 / (2 * v)) * d["actx"]
            else:
                logf = torch.log1p(lam * d["x"])
                if tr.base == "grapa_grid":
                    logf = logf.clamp(min=-30.0)
            wealth[tr.role] = (nme, buck(rel, logf).cumsum(-1)[..., :T])
        if {"B", "C"} <= set(wealth) and self.comb is not None:
            lB, lC = wealth["B"][1], wealth["C"][1]
            if self.comb == "bonf":
                lJ = torch.maximum(lB, lC) - math.log(2.0)
            elif self.comb == "mix":
                wj = _p(self.w, K, dev)[..., None]
                lJ = torch.logaddexp(torch.log(wj) + lB, torch.log1p(-wj) + lC)
            else:
                lJ = lB + lC
            wealth["J"] = ("J", lJ)
        for k, (nme, lw) in wealth.items():
            hit = lw >= self.thr
            first = torch.where(
                hit.any(-1),
                hit.long().argmax(-1),
                torch.full(hit.shape[:2], T, dtype=torch.long, device=dev),
            )
            out["alarm"][k][:, sl] = first
            out["nq"][k][:, sl] = spent.gather(-1, first.clamp(max=T - 1)[..., None])[..., 0].to(
                f64
            )
            out["lw"][k][:, sl] = lw.mean(-1)
            if "paths" in out:
                out["paths"][nme][:, sl] = lw
        out["spent"][:, sl] = spent[..., -1].to(f64)
        if "cumq" in out:
            out["cumq"][:, sl] = spent.to(torch.int32)

    @staticmethod
    def _ons_path(x, arr, hi):
        """ONS stake path lam_t [K,n,T] from precomputed increments. On CUDA the step is captured once in a graph
        (device-side step counter) and replayed T times; on CPU it is a plain loop."""
        K, n, T = x.shape
        dev, f64 = x.device, x.dtype
        L = int(arr.max()) + 2
        Bz = torch.zeros(K, n, L, dtype=f64, device=dev)
        Bz2 = torch.zeros_like(Bz)
        cur = torch.zeros(K, n, dtype=f64, device=dev)
        a = torch.ones(K, n, dtype=f64, device=dev)
        lam = torch.zeros(K, n, T, dtype=f64, device=dev)
        tt = torch.zeros((), dtype=torch.long, device=dev)
        tt1 = tt.view(1)

        def step():
            ip = (tt - 1).clamp(min=0).view(1)  # bucket t-1 (bucket 0 is still empty at t = 0)
            a.add_(Bz2.index_select(-1, ip)[..., 0])
            cur.copy_(
                torch.minimum(
                    (cur + ONS_C * Bz.index_select(-1, ip)[..., 0] / a).clamp(min=0.0), hi
                )
            )
            lam.index_copy_(2, tt1, cur[..., None])
            xt = x.index_select(2, tt1)[..., 0]
            z = xt / (1.0 + cur * xt)
            idx = arr.index_select(2, tt1)
            Bz.scatter_add_(-1, idx, z[..., None])
            Bz2.scatter_add_(-1, idx, (z * z)[..., None])
            tt.add_(1)

        if dev.type == "cuda":
            g = torch.cuda.CUDAGraph()
            side = torch.cuda.Stream()
            side.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(side), torch.cuda.graph(g, stream=side):
                step()
            torch.cuda.current_stream().wait_stream(side)
            for _ in range(T):
                g.replay()
        else:
            for _ in range(T):
                step()
        return lam

    def _run_loop(self, tape, keep_paths=False, graph=None) -> Result:
        """General event loop (any hook). One step per t, written against a device-side step counter ``tt`` so the whole
        step can be captured once in a CUDA graph and replayed T times (``graph=True``): all state is then updated in
        place and a replay costs one launch instead of ~100. Eager mode (default) runs the same step function."""
        K, tr_list = self.K, self.tracks
        R0 = tape["B"]
        dev, (S, T) = R0.device, R0.shape
        f64 = torch.float64
        U, D = tape["U"], tape["d"]
        frac = self.frac if self.frac is not None else tape["frac"]
        if isinstance(frac, torch.Tensor) and frac.dim():
            q0 = frac.reshape(1, S).to(f64).expand(K, S)
        else:
            q0 = _p(frac, K, dev).expand(K, S)
        qfl = (
            q0 if self.q_floor is None else q0 * _p(self.q_floor, K, dev)
        )  # q_floor = ratio of the base rate
        budget = tape.get("budget", T)
        budget = (torch.as_tensor(budget, dtype=f64, device=dev).reshape(-1)).expand(S)[None, :]
        Dmax = int(D.max())
        ring = Ring(Dmax + 2)
        ctx = Ctx(ring)
        ctx.K, ctx.S, ctx.T, ctx.q0, ctx.qfloor, ctx.budget, ctx.pmax = (
            K,
            S,
            T,
            q0,
            qfl,
            budget,
            {tr.name: tape["pmax"][tr.ch] for tr in tr_list},
        )
        ctx.device, ctx.call = dev, 0
        use_graph = bool((self.graph if graph is None else graph) and dev.type == "cuda")
        tt = torch.zeros((), dtype=torch.long, device=dev)  # step counter, lives on the device
        tt1 = tt.view(1)
        ctx.tt = tt
        names = [tr.name for tr in tr_list]
        st = {}
        zs = lambda: torch.zeros(K, S, dtype=f64, device=dev)
        for tr in tr_list:
            n = tr.name
            r0, hm = tape["theta"][tr.ch], tape["pmax"][tr.ch]
            bd = hm * (1.0 / qfl - 1.0) + r0
            bx = torch.maximum(bd, 1.0 / qfl)  # sup |x|-scale for the Timans [0,1] map
            hi = tr.cap / bd
            s = {"c1": zs(), "c2": zs(), "cn": zs(), "gam": _p(tr.gamma, K, dev), "r0": r0, "bd": bd, "bx": bx, "hi": hi,
                     "logW": zs(), "rel_prev": torch.zeros(K, S, dtype=torch.long, device=dev),
                     "cur": zs(), "a": torch.ones(K, S, dtype=f64, device=dev),
                     "first": torch.full((K, S), T, dtype=torch.long, device=dev), "nqat": zs(),
                     "lamf": _p(tr.lam, K, dev) * hi if tr.base == "fixed" else None}  # fmt: skip
            ring.make("m_" + n, (5, K, S), dev)
            if tr.base == "grapa_grid":
                s["cl"] = torch.zeros(len(GRAPA_GRID), K, S, dtype=f64, device=dev)
                s["grid"] = torch.tensor(GRAPA_GRID, dtype=f64, device=dev)[:, None, None]
                ring.make("g_" + n, (len(GRAPA_GRID), K, S), dev)
            if tr.corr == "eta":
                s["eta_st"] = torch.zeros(8, K, S, dtype=f64, device=dev)
                ring.make("e_" + n, (8, K, S), dev)
            if tr.bins:
                s["rv"] = torch.zeros(2, tr.bins, K, S, dtype=f64, device=dev)
                ctx.res[n] = s["rv"]
                ring.make("r_" + n, (2, tr.bins, K, S), dev)
            if tr.bet:
                ring.make("w_" + n, (K, S), dev)
            st[n] = s
            ctx.hi[n], ctx.bd[n], ctx.logW[n] = hi, bd, s["logW"]
        role = {tr.role: tr.name for tr in tr_list if tr.bet}
        both = {"B", "C"} <= set(role) and self.comb is not None
        wj = _p(self.w, K, dev) if both else None
        gs = {
            "spent": zs(),
            "firstJ": torch.full((K, S), T, dtype=torch.long, device=dev),
            "nqJ": zs(),
            "logWJ": zs(),
            "relJ": torch.zeros(K, S, dtype=torch.long, device=dev),
        }
        if self.comb == "linear":
            ring.make("w_J", (K, S), dev)
        cumq = torch.zeros(K, S, T, dtype=torch.int32, device=dev) if keep_paths else None
        paths = (
            {n: torch.zeros(K, S, T, dtype=f64, device=dev) for n in names} if keep_paths else {}
        )
        lams = {n: torch.zeros(K, S, T, dtype=f64, device=dev) for n in names} if keep_paths else {}
        if keep_paths and both:
            paths["J"] = torch.zeros(K, S, T, dtype=f64, device=dev)
        ctx.spent = gs["spent"]
        lwsum = {tr.role: zs() for tr in tr_list if tr.bet}
        if both:
            lwsum["J"] = zs()
        hk = self.hooks
        if hk.declare is not None:
            hk.declare(
                ctx
            )  # hooks allocate their state / aux buffers eagerly (needed before graph capture)

        def setv(
            d, k, v
        ):  # state update: in place under graph capture (static addresses), rebinding otherwise
            if use_graph:
                d[k].copy_(v)
            else:
                d[k] = v

        col = lambda A: A.index_select(1, tt1)[:, 0]

        def step(t_int):
            ctx.t = t_int if not use_graph else tt
            ctx.call += 1
            # ---- absorb arrivals <= t-1 (stake at t may use nothing later; at t = 0 the slot is empty)
            for tr in tr_list:
                s, n = st[tr.name], tr.name
                v = ring.pop("m_" + n, tt - 1)
                g = (hk.gamma[n](ctx, s["gam"]) if n in hk.gamma else s["gam"]) ** v[2]
                setv(s, "c1", g * s["c1"] + v[0])
                setv(s, "c2", g * s["c2"] + v[1])
                setv(s, "cn", g * s["cn"] + v[2])
                if tr.base == "ons":
                    setv(s, "a", s["a"] + v[4])
                    setv(
                        s,
                        "cur",
                        torch.minimum(
                            torch.clamp(s["cur"] + ONS_C * v[3] / s["a"], min=0.0), s["hi"]
                        ),
                    )
                if tr.base == "grapa_grid":
                    setv(s, "cl", s["cl"] + ring.pop("g_" + n, tt - 1))
                if tr.corr == "eta":
                    setv(s, "eta_st", s["eta_st"] * 0.99 + ring.pop("e_" + n, tt - 1))
                if tr.bins:
                    setv(s, "rv", 0.995 * s["rv"] + ring.pop("r_" + n, tt - 1))
                    ctx.res[n] = s["rv"]
                if tr.name in hk.restart:
                    m = hk.restart[tr.name](ctx)
                    if m.dtype == torch.bool:
                        for k in ("c1", "c2", "cn", "cur"):
                            setv(s, k, torch.where(m, torch.zeros_like(s[k]), s[k]))
                        setv(s, "a", torch.where(m, torch.ones_like(s["a"]), s["a"]))
                        if "cl" in s:
                            setv(s, "cl", s["cl"] * (~m))
                    else:  # soft: keep fraction m of the state
                        for k in ("c1", "c2", "cn", "cur"):
                            setv(s, k, s[k] * m)
                        setv(s, "a", 1.0 + (s["a"] - 1.0) * m)
                        if "cl" in s:
                            setv(s, "cl", s["cl"] * m)
            ctx.h = {tr.name: col(tape[tr.ch + "hat"]) for tr in tr_list}
            ctx.x, ctx.lam, ctx.Q = {}, {}, None
            # ---- predictable base stakes (state only)
            for tr in tr_list:
                s, n = st[tr.name], tr.name
                mean, second = s["c1"] / (s["cn"] + 1.0), s["c2"] / (s["cn"] + 1.0)
                kel = torch.where(
                    second > 0,
                    mean.clamp(min=0.0) / second.clamp(min=1e-12),
                    torch.zeros_like(mean),
                )
                if tr.base in ("kelly",):
                    lam = torch.minimum(kel, s["hi"])
                elif tr.base == "ons":
                    lam = s["cur"]
                elif tr.base == "fixed":
                    lam = s["lamf"]
                elif tr.base == "grapa":
                    nn = s["cn"]
                    mu = s["c1"] / nn.clamp(min=1.0) / (2 * s["bx"]) + 1e-10
                    var = (
                        (s["c2"] - nn * (s["c1"] / nn.clamp(min=1.0)) ** 2)
                        / (nn - 1).clamp(min=1.0)
                    ) / (4 * s["bx"] ** 2) + 1e-10
                    bet = (mu / (var + mu**2) + 1e-10).clamp(0.0, 1.0)
                    lam = torch.where(nn >= tr.burn_in, bet, torch.zeros_like(bet)) / (2 * s["bx"])
                elif tr.base == "grapa_grid":
                    lam = torch.where(
                        s["cn"] >= tr.burn_in,
                        s["grid"][s["cl"].argmax(0), 0, 0] / (2 * s["bx"]),
                        torch.zeros_like(mean),
                    )
                else:
                    raise ValueError(tr.base)
                if tr.base not in ("grapa", "grapa_grid"):
                    lam = lam.clamp(min=0.0)
                s["mean_t"], s["lam0"] = mean, lam
                ctx.mean[n], ctx.second[n], ctx.kelly[n], ctx.base[n] = mean, second, kel, lam
            # ---- query
            q = q0
            if hk.query is not None:
                q = hk.query(ctx, q)
            q = torch.maximum(q, qfl).clamp(max=1.0)
            q = torch.where(gs["spent"] < budget, q, torch.zeros_like(q))
            active = q > 0
            Q = (col(U)[None, :] < q) & active
            Qd = Q.to(f64)
            setv(gs, "spent", gs["spent"] + Qd)
            spent = gs["spent"]
            ctx.spent = spent
            qs = torch.where(active, q, torch.ones_like(q))
            d_t = col(D)[None, :].expand(K, S)
            arr = tt + (
                d_t if self.release == "legacy" else torch.where(Q, d_t, torch.zeros_like(d_t))
            )
            # ---- stake hooks, factors, deferred buckets
            for tr in tr_list:
                s, n = st[tr.name], tr.name
                lam = s["lam0"]
                if n in hk.stake:
                    lam = hk.stake[n](ctx, lam)
                if tr.base not in ("grapa", "grapa_grid"):
                    lam = torch.minimum(lam.clamp(min=0.0), s["hi"])
                else:  # A3.3
                    lam = torch.minimum(lam.clamp(min=0.0), 0.95 / s["bd"])
                act = active | tr.proxy_only
                lam = lam * act
                Rt, ht, r0 = col(tape[tr.ch])[None, :], col(tape[tr.ch + "hat"])[None, :], s["r0"]
                if tr.corr == "ipw":
                    ht = torch.zeros_like(ht)
                if tr.proxy_only:
                    x = (ht - r0) * act
                else:
                    eta = 1.0
                    if tr.corr == "eta":
                        e = s["eta_st"]  # [wL, wR, wH, wRH, wHH, nU, sH, sHH]
                        nl, nu = e[0], e[5].clamp(min=1.0)
                        cov = e[3] / nl.clamp(min=1.0) - (e[1] / nl.clamp(min=1.0)) * (
                            e[2] / nl.clamp(min=1.0)
                        )
                        varh = (e[7] / nu - (e[6] / nu) ** 2).clamp(min=0.0)
                        eta = torch.where(
                            (nl >= 2) & (varh > 1e-12),
                            (cov / ((1 + nl / nu) * varh.clamp(min=1e-12))).clamp(0.0, 1.0),
                            torch.ones_like(cov),
                        )
                    x = (eta * ht + (Qd / qs) * (Rt - eta * ht) - r0) * act
                if tr.factor == "lrt":
                    v = ctx.second[n].clamp(min=1e-12)
                    dl = ctx.mean[n].clamp(min=0.0)
                    logf = (dl * x / v - dl**2 / (2 * v)) * act
                else:
                    logf = torch.log1p(lam * x)
                    if tr.base == "grapa_grid":  # guards the Timans range (never binding)
                        logf = logf.clamp(min=-30.0)
                if tr.corr == "csillag":
                    mx, cnt, arr_m = Qd * (Rt - r0), Qd, tt + d_t
                else:
                    mx, cnt, arr_m = x, act.to(f64), arr
                if tr.base == "ons":
                    z = mx / (1.0 + s["lam0"] * mx)
                    ring.add("m_" + n, arr_m, torch.stack([mx, mx * mx, cnt, z, z * z]))
                else:
                    ring.add("m_" + n, arr_m, torch.stack([mx, mx * mx, cnt, mx, mx]))
                if tr.base == "grapa_grid":
                    ring.add(
                        "g_" + n, arr_m, torch.log1p(s["grid"] * x[None] / (2 * s["bx"][None]))
                    )
                if tr.corr == "eta":
                    ring.add(
                        "e_" + n,
                        arr_m,
                        torch.stack(
                            [
                                Qd,
                                Qd * Rt,
                                Qd * ht,
                                Qd * Rt * ht,
                                Qd * ht * ht,
                                torch.ones_like(Qd),
                                ht.expand(K, S),
                                (ht * ht).expand(K, S),
                            ]
                        ),
                    )
                if tr.bins:
                    nb = tr.bins
                    b = (ht / tape["pmax"][tr.ch] * nb).long().clamp(0, nb - 1).expand(K, S)
                    oh = torch.nn.functional.one_hot(b, nb).permute(2, 0, 1).to(f64)  # [nb,K,S]
                    w = Qd / qs
                    ring.add(
                        "r_" + n,
                        arr_m,
                        torch.stack([oh * (w * (Rt - ht) ** 2)[None], oh * w[None]]),
                    )
                if tr.bet:
                    if self.release == "legacy":
                        rel = arr
                    else:
                        rel = torch.maximum(s["rel_prev"], arr)
                        setv(s, "rel_prev", rel)
                    ring.add("w_" + n, rel, logf)
                ctx.x[n], ctx.lam[n] = x, lam
                if keep_paths:
                    lams[n].index_copy_(2, tt1, lam[..., None])
            if (
                self.comb == "linear" and both
            ):  # A3.1 linear vector factor 1 + w lam_B x_B + (1-w) lam_C x_C
                b_, c_ = role["B"], role["C"]
                logfJ = torch.log1p(
                    wj * ctx.lam[b_] * ctx.x[b_] + (1 - wj) * ctx.lam[c_] * ctx.x[c_]
                )
                relJ = arr if self.release == "legacy" else torch.maximum(gs["relJ"], arr)
                setv(gs, "relJ", relJ)
                ring.add("w_J", relJ, logfJ)
            ctx.Q = Q
            if hk.after_step is not None:
                hk.after_step(ctx, Q, arr)
            # ---- release wealth that arrives exactly now (a factor with rel == t), alarms
            for tr in tr_list:
                s, n = st[tr.name], tr.name
                if tr.bet:
                    setv(s, "logW", s["logW"] + ring.pop("w_" + n, tt))
                    ctx.logW[n] = s["logW"]
                    new = (s["logW"] >= self.thr) & (s["first"] == T)
                    setv(s, "first", torch.where(new, tt.expand_as(s["first"]), s["first"]))
                    setv(s, "nqat", torch.where(new, spent, s["nqat"]))
                    lwsum[tr.role] += s["logW"]
                    if keep_paths:
                        paths[n].index_copy_(2, tt1, s["logW"][..., None])
            if both:
                lB, lC = st[role["B"]]["logW"], st[role["C"]]["logW"]
                if self.comb == "bonf":
                    lJ = torch.maximum(lB, lC) - math.log(2.0)
                elif self.comb == "mix":
                    lJ = torch.logaddexp(torch.log(wj) + lB, torch.log1p(-wj) + lC)
                elif self.comb == "linear":
                    setv(gs, "logWJ", gs["logWJ"] + ring.pop("w_J", tt))
                    lJ = gs["logWJ"]
                else:  # prod (INVALID under dependence, THEORY_AUDIT F1; kept only to reproduce the inflation)
                    lJ = lB + lC
                new = (lJ >= self.thr) & (gs["firstJ"] == T)
                setv(gs, "firstJ", torch.where(new, tt.expand_as(gs["firstJ"]), gs["firstJ"]))
                setv(gs, "nqJ", torch.where(new, spent, gs["nqJ"]))
                lwsum["J"] += lJ
                if keep_paths:
                    paths["J"].index_copy_(2, tt1, lJ[..., None])
            if keep_paths:
                cumq.index_copy_(2, tt1, spent.to(torch.int32)[..., None])
            tt.add_(1)

        if use_graph:
            graph = torch.cuda.CUDAGraph()
            side = torch.cuda.Stream()
            side.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(side), torch.cuda.graph(graph, stream=side):
                step(None)
            torch.cuda.current_stream().wait_stream(side)
            for _ in range(T):
                graph.replay()
        else:
            for t in range(T):
                step(t)
        spent, firstJ, nqJ = gs["spent"], gs["firstJ"], gs["nqJ"]
        alarm = {tr.role: st[tr.name]["first"] for tr in tr_list if tr.bet}
        if both:
            alarm["J"] = firstJ
        nq_at = {
            tr.role: torch.where(st[tr.name]["first"] == T, spent, st[tr.name]["nqat"])
            for tr in tr_list
            if tr.bet
        }
        if both:
            nq_at["J"] = torch.where(firstJ == T, spent, nqJ)
        return Result(
            self.ids,
            alarm,
            cumq,
            paths,
            lams,
            tuple(alarm),
            {k: v / T for k, v in lwsum.items()},
            nq_at,
            spent,
        )


# ---------------------------------------------------------------------- non-wealth and vector monitors
class ClassicMonitor:
    """CUSUM / Page-Hinkley on queried losses of one track (EMPIRICAL_ALARM: thresholds calibrated on
    null audit seeds by ``calibrate``; not anytime-valid)."""

    def __init__(self, kind, track, slack=0.25, delta=0.05, name=""):
        self.kind, self.track, self.slack, self.delta, self.name = (
            kind,
            track,
            slack,
            delta,
            name or f"{kind}_{track}",
        )
        self.K, self.ids = 1, [self.name]

    def stat_max(self, tape):
        """Return (max_t stat [S], stat path [S,T] float32, cumq [S,T]). Closed form: with C_t the cumulative sum of
        released increments, CUSUM (reflected at 0) and Page-Hinkley both equal C_t - min(0, min_{u<=t} C_u)."""
        R0 = tape["B"]
        dev, (S, T) = R0.device, R0.shape
        f64 = torch.float64
        n, th, sd = self.track, tape["theta"][self.track], tape["sd"][self.track]
        q = torch.as_tensor(tape["frac"], dtype=f64, device=dev).reshape(-1).expand(S)[:, None]
        budget = (
            torch.as_tensor(tape.get("budget", T), dtype=f64, device=dev)
            .reshape(-1)
            .expand(S)[:, None]
        )
        raw = tape["U"] < q
        Q = raw & ((raw.cumsum(-1) - raw.long()) < budget)
        c = self.slack if self.kind == "cusum" else self.delta
        v = Q * ((tape[n] - th) / sd - c)
        arr = torch.arange(T, device=dev) + tape["d"]
        L = T + int(tape["d"].max()) + 1
        C = torch.zeros(S, L, dtype=f64, device=dev).scatter_add_(1, arr, v).cumsum(1)[:, :T]
        path = (C - torch.cummin(C, 1).values.clamp(max=0.0)).float()
        return path.max(1).values, path, Q.cumsum(1).to(torch.int32)

    _cache: ClassVar[dict] = {}

    def _thr(self, tape):
        """Per-seed threshold: 95% quantile of the horizon max on null_stationary audit seeds of the same
        (delay, label regime, T) cell family."""
        from shiftlab.hgxh2c import tapes as TP

        dev, out = tape["B"].device, []
        for c, n in zip(
            tape.get("cells") or [tape["cell"]], tape.get("sizes") or [tape["B"].shape[0]]
        ):
            key = (
                self.kind,
                self.track,
                self.slack,
                self.delta,
                c.delay,
                c.label_regime,
                c.T,
                str(dev),
            )
            if key not in ClassicMonitor._cache:
                nc = TP.ScenarioCell("null_stationary", 0.0, c.delay, c.label_regime, "good", c.T)
                mx, _, _ = self.stat_max(TP.generate(nc, "audit", 512, dev))
                ClassicMonitor._cache[key] = float(torch.quantile(mx.double(), 0.95))
            out.append(
                torch.full((n,), ClassicMonitor._cache[key], dtype=torch.float64, device=dev)
            )
        return torch.cat(out)

    def run(self, tape, keep_paths=False) -> Result:
        _, path, cumq = self.stat_max(tape)
        T = path.shape[1]
        hit = path >= self._thr(tape)[:, None].float()
        first = torch.where(
            hit.any(1), hit.double().argmax(1), torch.full((path.shape[0],), T, device=path.device)
        )
        stop = first.clamp(max=T - 1)
        nq = cumq.gather(1, stop[:, None])[:, 0].double()
        return Result(
            self.ids,
            {self.track: first[None]},
            None,
            {},
            {},
            (self.track,),
            {},
            {self.track: nq[None]},
            cumq[:, -1].double()[None],
        )


class VectorMixMonitor:
    """Ryu-Wornell style multivariate gambling e-process for the joint null on (B_t, C_t):
    factor 1 + lam_B x_B + lam_C x_C (lam >= 0, so it is a test supermartingale under the intersection
    null), with the mixture portfolio over a fixed grid of bets lam = s*cap*(w/Bd_B, (1-w)/Bd_C),
    w in 7 directions x s in 5 scales (positivity: sum lam_i Bd_i <= cap). Weights are uniform and
    predetermined; PP-corrected increments, prefix release. Track J only. Formula-level port of the
    mixture-portfolio idea, not a verified reproduction (the paper's ONS-adaptive variant is omitted)."""

    def __init__(
        self,
        ws=(0, 1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6, 1),
        scales=(1 / 16, 1 / 8, 1 / 4, 1 / 2, 1.0),
        cap=0.5,
        name="ryu_wornell",
    ):
        self.ws, self.scales, self.cap, self.name = ws, scales, cap, name
        self.K, self.ids = 1, [name]

    def run(self, tape, keep_paths=False) -> Result:
        S, T = tape["B"].shape
        G = len(self.ws) * len(self.scales)
        step = max(1, int(12_000_000 // (G * T)))
        parts = [self._chunk(tape, slice(s0, min(S, s0 + step)), S) for s0 in range(0, S, step)]
        first, nq, spent = (torch.cat([p[i] for p in parts]) for i in range(3))
        return Result(
            self.ids, {"J": first[None]}, None, {}, {}, ("J",), {}, {"J": nq[None]}, spent[None]
        )

    def _chunk(self, tape, sl, S):
        dev, f64 = tape["B"].device, torch.float64
        n, T = tape["B"][sl].shape
        q = torch.as_tensor(tape["frac"], dtype=f64, device=dev).reshape(-1).expand(S)[sl][:, None]
        budget = (
            torch.as_tensor(tape.get("budget", T), dtype=f64, device=dev)
            .reshape(-1)
            .expand(S)[sl][:, None]
        )
        U, d = tape["U"][sl], tape["d"][sl]
        raw = U < q
        active = (raw.cumsum(-1) - raw.long()) < budget
        Q = raw & active
        Qd = Q.to(f64)
        bd, x = {}, {}
        for c in "BC":
            h, R = tape[c + "hat"][sl], tape[c][sl]
            bd[c] = tape["pmax"][c] * (1 / q - 1) + tape["theta"][c]
            x[c] = (h + (Qd / q) * (R - h) - tape["theta"][c]) * active
        w = torch.tensor([a for a in self.ws for _ in self.scales], dtype=f64, device=dev)[
            :, None, None
        ]
        sc = torch.tensor([b for _ in self.ws for b in self.scales], dtype=f64, device=dev)[
            :, None, None
        ]
        lB, lC = (
            sc * self.cap * w / bd["B"][None],
            sc * self.cap * (1 - w) / bd["C"][None],
        )  # [G,n,1]
        arr = torch.arange(T, device=dev) + torch.where(Q, d, torch.zeros_like(d))
        rel = torch.cummax(arr, -1).values
        L = T + int(d.max()) + 1
        G = lB.shape[0]
        logf = torch.log1p(lB * x["B"][None] + lC * x["C"][None])
        lw = (
            torch.zeros(G, n, L, dtype=f64, device=dev)
            .scatter_add_(-1, rel.expand(G, n, T), logf)
            .cumsum(-1)[..., :T]
        )
        lj = torch.logsumexp(lw, 0) - math.log(G)
        hit = lj >= LOG_THR
        first = torch.where(
            hit.any(-1), hit.long().argmax(-1), torch.full((n,), T, dtype=torch.long, device=dev)
        )
        spent = Q.cumsum(-1)
        nq = spent.gather(-1, first.clamp(max=T - 1)[:, None])[:, 0].to(f64)
        return first, nq, spent[:, -1].to(f64)
