"""Risk-budget shield v2 (spec 03F sections 6.1-6.4): settlement accounting + label pacing.

Validity (6.1): at every deployed round t the controller verifies W_t <= R, where on the event E of
Lemma 1' W_t >= H_t + k (H_t includes round t's own worst case, and the k pays a later rollback).
Bookkeeping classes for an exposed round (a=1, g=1):
  pi = 1    : worst case 1 while its label is pending, exact x on release;
  sampled   : (pi < 1) booked at 1 until s + w, then settled into the IPW sum and the coin mixture;
  blind     : booked at 1 forever.
The sampled contribution is min(settled form, number of sampled rounds): both are valid on E.
Ride-out: if the frozen bound plus the remaining horizon fits in R, stay deployed blind to T.
"""

from __future__ import annotations

from collections import deque
from dataclasses import replace

import numpy as np

from ..contracts import Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec
from .bounds_v2 import CoinMixture


class RiskBudgetShieldV2(PolicyAdapter):
    def __init__(
        self,
        inner: PolicyAdapter,
        R: float,
        delta: float = 0.05,
        pi_min: float = 0.5,
        window: int | None = None,
        default_window: int = 10,
        blind_margin: float | None = None,
        label_reserve_frac: float = 0.25,
        ride_out: bool = True,
        paced: bool = True,
        name: str | None = None,
        v_targets=None,
        width_scale: float = 1.0,
        mix_m: int | None = None,
        deterministic: bool = False,
    ):
        if R < 0 or not 0.0 < pi_min <= 1.0:
            raise ValueError("need R >= 0 and pi_min in (0, 1]")
        if pi_min < 1.0 and not 0.0 < delta < 1.0:
            raise ValueError("pi_min < 1 needs delta in (0, 1)")
        self.inner, self.R, self.delta, self.pi_min = inner, float(R), delta, float(pi_min)
        self.window, self.default_window = window, default_window
        self.blind_margin, self.label_reserve_frac = blind_margin, label_reserve_frac
        self.ride_out, self.paced = ride_out, paced
        self.mix_m = mix_m
        self.deterministic = deterministic  # matched safe comparator: no IPW, every unresolved/unqueried exposure booked at 1
        self.width_scale = float(width_scale)  # DIAGNOSTIC ONLY (1.0 in every reported arm)
        self.v_targets = None if v_targets is None else tuple(float(v) for v in v_targets)
        self.name = name or f"rbshield2[{inner.name}|R={R:g}]"

    # ------------------------------------------------------------------ lifecycle
    def reset(self, spec: ProblemSpec, rng: np.random.Generator) -> None:
        self.spec, self.k, self.T = spec, spec.costs.k, spec.T
        self.L_res = max(0, round(self.label_reserve_frac * spec.B))
        self.w = max(1, int(self.window or spec.delay_known or self.default_window))
        self.inner.reset(spec, np.random.default_rng(int(rng.integers(2**63))))
        self.rng = np.random.default_rng(int(rng.integers(2**63)))
        self.mix = CoinMixture(self.delta if self.delta > 0 else 0.05, v_targets=self.v_targets, scale=self.width_scale, mix_m=self.mix_m)
        self.A1 = 0.0  # pi=1 rounds: released x
        self.P1 = 0  # pi=1 rounds: pending count
        self.As = 0.0  # sampled, settled: queried & released x/pi
        self.Pu = 0.0  # sampled, settled: queried & unreleased 1/pi
        self.U = 0  # sampled, unsettled count
        self.n_samp_g = 0  # sampled exposed rounds so far
        self.nb = 0
        self.N = 0
        self.rec: dict[int, dict] = {}
        self.uns: deque[int] = deque()
        self.psi_uns = np.zeros(len(self.mix.lams))  # sum of psi over unsettled sampled rounds
        self.cap_uns = 0.0
        self.n_dis = 0
        self.riding = False
        self.rode_out = False
        self.n_forced_rollbacks = 0
        self.n_vetoed_promotions = 0
        self.n_blind = 0
        self.n_sampled = 0
        self.n_pi1 = 0
        self._pis: list[float] = []
        self.I_max = 0.0  # max verified W_t over deployed rounds (<= R by construction)
        # verified upper bound on H_t at each round (nan when undeployed); H_t <= Hb[t-1] on E
        self.Hb = np.full(self.T, np.nan)
        self._ride_base = 0.0
        self._ride_t0 = 0

    @property
    def mean_pi(self) -> float:
        return float(np.mean(self._pis)) if self._pis else 1.0

    # ------------------------------------------------------------------ bound pieces
    def _S(self, extra: int = 0) -> float:
        """Upper bound on the sum of x over sampled exposed rounds (+ ``extra`` unsettled)."""
        n = self.n_samp_g + extra
        if n == 0:
            return 0.0
        return min(self.As + self.Pu + self.U + extra + self.mix.D(), float(n))

    def _fees(self, prev: int) -> float:
        return self.k * (self.N + (1 if prev == 0 else 0))

    def _W(self, prev: int, g: int, cls: str) -> float:
        """Verified bound W_t (includes the rollback reserve and this round's own worst case)."""
        w = self._fees(prev) + self.k + self.nb + self.A1 + self.P1
        if cls == "sampled":
            return w + self._S(extra=g)
        return w + self._S() + g

    def _lookahead(self, pi: float) -> float:
        """Extra width if every unsettled sampled round (incl. one more at pi) settled now."""
        psi = self.psi_uns + self.mix.psi(pi)
        cap = self.cap_uns + self.mix.cap_of(pi)
        return self.mix.D_with(psi, cap) - self.mix.D()

    # ------------------------------------------------------------------ one round
    def act(self, view: PolicyView) -> Paper3Decision:
        t, prev, g = view.t, view.prev_action, int(view.event.disagree)
        self.n_dis += g
        for lab in view.released:
            e = self.rec.get(lab.t_request)
            if e is None or e["rel"]:
                continue
            e["rel"], e["x"] = True, -lab.z
            if e["pi"] >= 1.0:
                self.A1 += e["x"]
                self.P1 -= 1
            elif e["settled"]:
                self.As += e["x"] / e["pi"]
                self.Pu -= 1.0 / e["pi"]
        while self.uns and self.uns[0] + self.w <= t:  # settle the deterministic prefix s <= t - w
            s = self.uns.popleft()
            e = self.rec[s]
            e["settled"] = True
            self.U -= 1
            self.mix.add(e["pi"])
            self.psi_uns = np.maximum(self.psi_uns - e["psi"], 0.0)
            self.cap_uns = max(self.cap_uns - self.mix.cap_of(e["pi"]), 0.0)
            if e["queried"]:
                if e["rel"]:
                    self.As += e["x"] / e["pi"]
                else:
                    self.Pu += 1.0 / e["pi"]
        if abs(self.Pu) < 1e-12:
            self.Pu = 0.0

        v_in = view
        if prev == 0:
            v_in = replace(view, labels_remaining=max(0, view.labels_remaining - self.L_res))
        dec = self.inner.act(v_in)
        base_k = {"compute": dec.compute, "retrain": dec.retrain}
        R = self.R

        # ---- ride-out: remaining horizon cannot exhaust the budget
        if self.ride_out and not self.riding and prev == 1:
            lhs = self.k * self.N + self.nb + self.A1 + self.P1 + self._S() + (self.T - t + 1)
            if lhs <= R:
                self.riding = self.rode_out = True
                self.I_max = max(self.I_max, lhs)
                self._ride_base, self._ride_t0 = lhs - (self.T - t + 1), t
        if self.riding:
            self.Hb[t - 1] = self._ride_base + (t - self._ride_t0 + 1)
            if g:
                self.nb += 1
                self.n_blind += 1
            return Paper3Decision(1, 0, **base_k)

        # ---- shield rule
        action, cls, pi = 0, None, None
        if dec.action == 1:
            if g == 0:
                w = self._W(prev, 0, "pi1")
                if w <= R:
                    action, self.I_max = 1, max(self.I_max, w)
            else:
                action, cls, pi, w = self._choose(view, t, prev)
                if action:
                    self.I_max = max(self.I_max, w)
            if not action:
                if prev == 1:
                    self.n_forced_rollbacks += 1
                else:
                    self.n_vetoed_promotions += 1

        # ---- bookkeeping
        query = 0
        if action == 1:
            self.Hb[t - 1] = w - self.k
            if prev == 0:
                self.N += 1
            if g:
                if cls == "blind":
                    self.nb += 1
                    self.n_blind += 1
                elif cls == "det":
                    query = int(self.rng.random() < pi)
                    if query:
                        self.P1 += 1
                        self.n_pi1 += 1
                        self.rec[t] = {"pi": 1.0, "queried": True, "rel": False, "settled": False}
                    else:
                        self.nb += 1
                        self.n_blind += 1
                    self._pis.append(pi)
                elif cls == "pi1":
                    self.P1 += 1
                    self.n_pi1 += 1
                    query = 1
                    self.rec[t] = {"pi": 1.0, "queried": True, "rel": False, "settled": False}
                    self._pis.append(1.0)
                else:
                    query = int(self.rng.random() < pi)
                    self.U += 1
                    self.n_samp_g += 1
                    self.n_sampled += 1
                    self.uns.append(t)
                    ps = self.mix.psi(pi)
                    self.psi_uns = self.psi_uns + ps
                    self.cap_uns += self.mix.cap_of(pi)
                    self.rec[t] = {
                        "psi": ps,
                        "pi": pi,
                        "queried": bool(query),
                        "rel": False,
                        "settled": False,
                    }
                    self._pis.append(pi)
        else:
            if prev == 1:
                self.N += 1
            elif dec.query and v_in.labels_remaining > 0:
                query = 1  # inner's evidence query while undeployed (x = 0 there)
        return Paper3Decision(action, query, **base_k)

    # ------------------------------------------------------------------ monitoring choice (6.4)
    def _choose(self, view: PolicyView, t: int, prev: int):
        """Return (action, cls, pi, W) for an exposed round, or (0, None, None, None)."""
        R, lr = self.R, view.labels_remaining
        if lr <= 0:
            w = self._W(prev, 1, "blind")
            return (1, "blind", None, w) if w <= R else (0, None, None, None)
        if self.blind_margin is not None:
            wb = self._W(prev, 1, "blind")
            if wb <= R and R - wb >= self.blind_margin:
                return 1, "blind", None, wb
        pi_p = 1.0
        if self.pi_min < 1.0:
            if self.paced:
                rate = (self.n_dis + 0.25 * 20.0) / (t + 20.0)
                target = lr / max(rate * (self.T - t + 1), 1.0)
                if target < 1.0:
                    pi_p = max(self.pi_min, target)
            else:
                pi_p = self.pi_min
        if self.deterministic:
            w = self._W(prev, 1, "blind")  # same check whatever the coin shows
            return (1, "det", pi_p, w) if w <= R else (0, None, None, None)
        if pi_p < 1.0:
            w = self._W(prev, 1, "sampled")
            if w + self._lookahead(pi_p) <= R:
                return 1, "sampled", pi_p, w
        w = self._W(prev, 1, "pi1")
        if w <= R:
            return 1, "pi1", 1.0, w
        return 0, None, None, None
