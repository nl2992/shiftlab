"""Common per-event adapter (PROTOCOL A1.2) and scalar reference monitors.

``SequentialMonitor`` is the contract: the runner shows a ``StreamEvent`` (free at issue), the monitor
returns a query probability, and later the runner delivers a ``ReleasedObservation`` once the event's
label has matured (queried: t + d; unqueried: the proxy-only observation arrives at t, or at t + d under
``release="legacy"``). ``evidence()`` is the per-track log-wealth released so far; ``alarm()`` is the
per-track "has crossed log(1/alpha)" flag. The reference runner releases only matured labels.

The reference monitors below are plain-python, one-event-at-a-time re-statements of the batched
engines in ``engines.py`` (independent code path: floats, dicts, no tensors). A monitor sees a delivered
observation only from the next ``propose_query`` on (arrivals <= t-1 feed the stake at t); wealth factors
are applied in event order once all earlier events have been delivered (= prefix release).
The batched GPU engines are accelerators: tests require log-wealth agreement to 1e-6 and identical alarms.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from shiftlab.hgxh2c.engines import GRAPA_GRID, LOG_THR, ONS_C, TrackSpec


@dataclass(frozen=True)
class StreamEvent:
    t: int
    proxy: dict  # {'B': Bhat_t, 'C': Chat_t}, free at issue
    delay: int  # design-time label delay of this event
    theta: dict  # source calibration {'B':..,'C':..}
    pmax: dict  # proxy support bounds
    q_base: float  # design query rate
    budget_left: int  # labels still affordable (pathwise budget)


@dataclass(frozen=True)
class ReleasedObservation:
    t_event: int
    t_arrive: int
    queried: bool
    q: float  # propensity used at issue (0 = inactive event)
    proxy: dict
    labels: dict | None = None  # {'B':..,'C':..} only when queried


class SequentialMonitor(Protocol):
    def propose_query(self, event: StreamEvent) -> float: ...
    def observe_release(self, obs: ReleasedObservation) -> None: ...
    def evidence(self) -> dict: ...  # track -> released log-wealth
    def alarm(self) -> dict: ...  # track -> bool


# ------------------------------------------------------------------ reference monitors
class _RT:
    """Scalar state of one track."""

    def __init__(self, sp: TrackSpec, theta, pmax, qfl):
        self.sp, self.r0 = sp, theta
        self.bd = pmax * (1 / qfl - 1) + theta
        self.hi = sp.cap / self.bd
        self.bx = max(self.bd, 1 / qfl)
        self.c1 = self.c2 = self.cn = 0.0
        self.cur, self.a = 0.0, 1.0
        self.cl = [0.0] * len(GRAPA_GRID)
        self.lw = 0.0

    def stats(self):
        mean, second = self.c1 / (self.cn + 1), self.c2 / (self.cn + 1)
        kel = max(mean, 0.0) / max(second, 1e-12) if second > 0 else 0.0
        return mean, second, kel

    def base(self):
        sp, (_, _, kel) = self.sp, self.stats()
        if sp.base == "kelly":
            return min(kel, self.hi)
        if sp.base == "ons":
            return self.cur
        if sp.base == "grapa":
            nn = self.cn
            m = self.c1 / max(nn, 1.0)
            mu = m / (2 * self.bx) + 1e-10
            var = ((self.c2 - nn * m * m) / max(nn - 1, 1.0)) / (4 * self.bx**2) + 1e-10
            bet = min(max(mu / (var + mu * mu) + 1e-10, 0.0), 1.0)
            return bet / (2 * self.bx) if nn >= sp.burn_in else 0.0
        if sp.base == "grapa_grid":
            k = int(np.argmax(self.cl))
            return GRAPA_GRID[k] / (2 * self.bx) if self.cn >= sp.burn_in else 0.0
        raise ValueError(sp.base)

    def absorb(self, items):
        """items: [(mx, cnt, z, lam, x)] delivered with the same arrival step."""
        if not items:
            return
        n = sum(i[1] for i in items)
        g = self.sp.gamma**n
        self.c1 = g * self.c1 + sum(i[0] for i in items)
        self.c2 = g * self.c2 + sum(i[0] ** 2 for i in items)
        self.cn = g * self.cn + n
        if self.sp.base == "ons":
            self.a += sum(i[2] ** 2 for i in items)
            self.cur = min(max(self.cur + ONS_C * sum(i[2] for i in items) / self.a, 0.0), self.hi)
        if self.sp.base == "grapa_grid":
            for k, lam_g in enumerate(GRAPA_GRID):
                self.cl[k] += sum(math.log1p(lam_g * i[4] / (2 * self.bx)) for i in items)


class RefMonitor:
    """Scalar reference for the baselines HG, H2c, C1, C2, Csillag, Timans GRAPA, contextual ONS, indep HG+H2c.

    ``gate={'B':'gC'}``: sign gate; ``ratio={'C':'gB'}``: H2c ratio guidance; ``joint=True``: full-history
    contextual ONS over the two Kelly positions; ``comb``: None | 'bonf' | 'mix' (weight ``w``)."""

    def __init__(
        self,
        specs,
        gate=None,
        ratio=None,
        joint=False,
        comb=None,
        w=0.5,
        release="prefix",
        alpha=0.05,
    ):
        self.specs, self.gate, self.ratio, self.joint = specs, gate or {}, ratio or {}, joint
        self.comb, self.w, self.release, self.thr = comb, w, release, math.log(1 / alpha)
        self.tr = None
        self.issued, self.delivered, self.buckets, self.next_idx = {}, {}, {}, 0
        self.t = -1
        self.first, self.lJ = {}, 0.0
        self.qfl = None
        if joint:
            self.w3 = {s.name: np.eye(3)[1 + i].copy() for i, s in enumerate(specs)}
            self.A3 = {s.name: np.eye(3) for s in specs}
            self.jb = defaultdict(list)

    # -- contract
    def propose_query(self, ev: StreamEvent) -> float:
        t = ev.t
        if self.tr is None:
            self.qfl = ev.q_base
            self.tr = {s.name: _RT(s, ev.theta[s.ch], ev.pmax[s.ch], self.qfl) for s in self.specs}
        self.t = t
        bk = self.buckets.pop(t - 1, {})
        for r in self.tr.values():
            r.absorb(bk.get(r.sp.name, []))
        base = {n: r.base() for n, r in self.tr.items()}
        f = None
        if self.joint:
            f = np.array([1.0] + [base[n] / self.tr[n].hi for n in self.tr])
            for n in self.tr:
                items = self.jb.pop((t - 1, n), [])
                if items:  # one update per arrival bucket (sums), as in the batched engine
                    g, G = sum(i[0] for i in items), sum(i[1] for i in items)
                    self.A3[n] = self.A3[n] + G
                    self.w3[n] = np.clip(
                        self.w3[n] + 2.2 * np.linalg.solve(self.A3[n], g), -1.0, 2.0
                    )
        q = ev.q_base if ev.budget_left > 0 else 0.0
        lam = {}
        for n, r in self.tr.items():
            lam0 = base[n]
            if n in self.gate:
                lam0 = lam0 * (self.tr[self.gate[n]].stats()[0] > 0)
            if n in self.ratio:
                s = self.ratio[n]
                lam0 = base[s] * self.tr[s].bd / r.bd
            if self.joint:
                lam0 = r.hi * min(max(float(self.w3[n] @ f), 0.0), 1.0)
            if r.sp.base not in ("grapa", "grapa_grid"):
                lam0 = min(max(lam0, 0.0), r.hi)
            lam[n] = lam0 if q > 0 else 0.0
        self.issued[t] = (lam, base, f)
        return q

    def observe_release(self, o: ReleasedObservation) -> None:
        lam, base, f = self.issued[o.t_event]
        fac = {}
        for n, r in self.tr.items():
            ch = r.sp.ch
            h = o.proxy[ch]
            x = 0.0
            if o.q > 0:
                x = h + ((o.labels[ch] - h) / o.q if o.queried else 0.0) - r.r0
            if r.sp.corr == "csillag":
                mx, cnt = (o.labels[ch] - r.r0, 1.0) if o.queried else (0.0, 0.0)
            else:
                mx, cnt = x, 1.0 if o.q > 0 else 0.0
            z = mx / (1.0 + base[n] * mx) if r.sp.base == "ons" else mx
            self.buckets.setdefault(o.t_arrive, {}).setdefault(n, []).append(
                (mx, cnt, z, lam[n], x)
            )
            if self.joint:
                g = r.hi * x / (1.0 + lam[n] * x) * f
                self.jb[(o.t_arrive, n)].append((g, np.outer(g, g)))
            fac[n] = math.log1p(lam[n] * x) if r.sp.bet else 0.0
        self.delivered[o.t_event] = fac
        while self.next_idx in self.delivered:  # in-order (prefix) release
            for n, v in self.delivered.pop(self.next_idx).items():
                self.tr[n].lw += v
            self.next_idx += 1
        self._alarms()

    def _alarms(self):
        ev = self.evidence()
        for k, v in ev.items():
            if v >= self.thr and k not in self.first:
                self.first[k] = self.t

    def evidence(self) -> dict:
        if self.tr is None:
            return {}
        out = {r.sp.role: r.lw for r in self.tr.values() if r.sp.bet}
        if self.comb and {"B", "C"} <= set(out):
            lB, lC = out["B"], out["C"]
            out["J"] = (
                max(lB, lC) - math.log(2)
                if self.comb == "bonf"
                else np.logaddexp(math.log(self.w) + lB, math.log1p(-self.w) + lC)
            )
        return out

    def alarm(self) -> dict:
        return {k: v >= self.thr for k, v in self.evidence().items()}


def run_reference(make_monitor, tape, s, release="prefix"):
    """Drive a SequentialMonitor on seed ``s`` of a tape; returns (alarms {track: step or T}, logW paths, queries)."""
    T = tape["B"].shape[1]
    L = {k: tape[k][s].tolist() for k in ("B", "C", "Bhat", "Chat", "U", "d")}
    frac = (
        float(tape["frac"])
        if not hasattr(tape["frac"], "dim") or tape["frac"].dim() == 0
        else float(tape["frac"][s])
    )
    budget = (
        int(tape["budget"])
        if not hasattr(tape["budget"], "dim") or tape["budget"].dim() == 0
        else int(tape["budget"][s])
    )
    mon, pend, spent = make_monitor(), defaultdict(list), 0
    first, paths = {}, defaultdict(list)
    for t in range(T):
        proxy = {"B": L["Bhat"][t], "C": L["Chat"][t]}
        ev = StreamEvent(t, proxy, L["d"][t], tape["theta"], tape["pmax"], frac, budget - spent)
        q = mon.propose_query(ev)
        Q = q > 0 and spent < budget and L["U"][t] < q
        spent += Q
        arr = t + (L["d"][t] if (Q or release == "legacy") else 0)
        pend[arr].append(
            ReleasedObservation(
                t, arr, bool(Q), q, proxy, {"B": L["B"][t], "C": L["C"][t]} if Q else None
            )
        )
        for o in pend.pop(t, []):
            mon.observe_release(o)
        for k, v in mon.evidence().items():
            paths[k].append(v)
            if v >= LOG_THR and k not in first:
                first[k] = t
    return {k: first.get(k, T) for k in paths}, dict(paths), spent


def references():
    """name -> factory for the per-event reference of the batched baselines."""
    S = TrackSpec
    return {
        "HG": lambda r="prefix": RefMonitor([S("gC", ch="C", gamma=0.99, bet=False), S("B", gamma=0.99)], gate={"B": "gC"}, release=r),
        "H2c": lambda r="prefix": RefMonitor([S("gB", ch="B", gamma=0.995, bet=False), S("C", gamma=0.995)], ratio={"C": "gB"}, release=r),
        "C1": lambda r="prefix": RefMonitor([S("C", gamma=0.995)], release=r),
        "C2": lambda r="prefix": RefMonitor([S("C", base="ons")], release=r),
        "csillag_C": lambda r="prefix": RefMonitor([S("C", corr="csillag", gamma=0.995)], release=r),
        "timans_approx_C": lambda r="prefix": RefMonitor([S("C", base="grapa")], release=r),
        "timans_grid_C": lambda r="prefix": RefMonitor([S("C", base="grapa_grid")], release=r),
        "joint_ctx_ons": lambda r="prefix": RefMonitor([S("B", gamma=0.99), S("C", gamma=0.99)], joint=True, comb="bonf", release=r),
        "indep_HG_H2c": lambda r="prefix": RefMonitor(
            [S("gC", ch="C", gamma=0.99, bet=False), S("B", gamma=0.99), S("gB", ch="B", gamma=0.995, bet=False), S("C", gamma=0.995)],
            gate={"B": "gC"}, ratio={"C": "gB"}, comb="bonf", release=r),
    }  # fmt: skip
