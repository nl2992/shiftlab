"""Vectorised controllers. ``step(s, alarm, rel)`` returns (a_s, reset_main) where a_s in {0,1} is the
action at decision step s, a function only of releases with release time <= s-1 (``rel``) and the
monitor alarm computed from them (F_{s-1}-measurable). ``reset_main`` asks the engine to reset the
main monitor for those episodes. No truth is ever visible here."""

from __future__ import annotations

import numpy as np


class Controller:
    name = "controller"
    uses_monitor = True
    acquires = True  # pays for the query mask (labels are used)

    def __init__(self, n: int, T: int, c_s: float = 0.0):
        self.n, self.T, self.c_s = n, T, c_s
        self.a = np.zeros(n, dtype=np.int8)

    def step(self, s, alarm, rel):
        raise NotImplementedError

    def spec(self) -> dict:
        return {"name": self.name}


class Permanent(Controller):
    name = "permanent"

    def step(self, s, alarm, rel):
        self.a = (self.a.astype(bool) | alarm).astype(np.int8)
        return self.a, np.zeros(self.n, bool)


class Hold(Controller):
    """Switch for H steps on alarm, revert, reset the monitor."""

    name = "hold"

    def __init__(self, n, T, c_s=0.0, H=200):
        super().__init__(n, T, c_s)
        self.H = int(H)
        self.until = np.full(n, -1)

    def spec(self):
        return {"name": f"hold{self.H}", "H": self.H}

    def step(self, s, alarm, rel):
        ending = self.until == s
        active = s < self.until
        trig = alarm & ~active & ~ending
        self.until = np.where(trig, s + self.H, self.until)
        self.a = (s < self.until).astype(np.int8)
        return self.a, ending


class Reverse(Controller):
    """Permanent-style switch; afterwards a reverse paired monitor (x = l1 - l0, restarted at the switch,
    consuming labels released after it) switches back on its alarm. Reverse threshold is passed in."""

    name = "reverse"

    def __init__(self, n, T, c_s=0.0, rev_factory=None, rev_threshold=np.inf):
        super().__init__(n, T, c_s)
        self.rev = rev_factory(n)
        self.rev.threshold = rev_threshold

    def spec(self):
        return {
            "name": "reverse",
            "reverse_monitor": self.rev.spec(),
            "rev_threshold": float(self.rev.threshold),
        }

    def step(self, s, alarm, rel):
        on = self.a == 1
        self.rev.update(rel.l1 - rel.l0, rel.valid & on)
        back = on & self.rev.alarm()
        go = ~on & alarm
        self.rev.reset(go | back)
        self.a = np.where(go, 1, np.where(back, 0, self.a)).astype(np.int8)
        return self.a, back


class NeverSwitch(Controller):
    name = "never"
    uses_monitor = False
    acquires = False

    def step(self, s, alarm, rel):
        return self.a, np.zeros(self.n, bool)


class AlwaysChallenger(NeverSwitch):
    name = "always"

    def __init__(self, n, T, c_s=0.0):
        super().__init__(n, T, c_s)
        self.a[:] = 1


class CalendarBatch(Controller):
    """Every K steps deploy the action with lower mean released loss over labels that arrived in the last
    K steps; ties (or no labels) keep the current action."""

    name = "calendar"
    uses_monitor = False

    def __init__(self, n, T, c_s=0.0, K=200):
        super().__init__(n, T, c_s)
        self.K = int(K)
        self.s0, self.s1, self.cnt = np.zeros(n), np.zeros(n), np.zeros(n)

    def spec(self):
        return {"name": f"calendar{self.K}", "K": self.K}

    def step(self, s, alarm, rel):
        if s > 0 and s % self.K == 0:
            m0, m1 = self.s0 / np.maximum(self.cnt, 1), self.s1 / np.maximum(self.cnt, 1)
            has = self.cnt > 0
            self.a = np.where(has & (m1 < m0), 1, np.where(has & (m1 > m0), 0, self.a)).astype(
                np.int8
            )
            self.s0[:] = self.s1[:] = self.cnt[:] = 0.0
        self.s0 += np.where(rel.valid, rel.l0, 0.0)
        self.s1 += np.where(rel.valid, rel.l1, 0.0)
        self.cnt += rel.valid
        return self.a, np.zeros(self.n, bool)


class StaticThreshold(Controller):
    """Economic one-way rule: switch (permanently) when, with a full buffer of the last W released paired
    differences, mean_gap * (T - s) > c_s, i.e. projected savings over the remaining horizon exceed the
    switching cost. Uses no monitor and no calibration."""

    name = "static"
    uses_monitor = False

    def __init__(self, n, T, c_s=0.0, W=100):
        super().__init__(n, T, c_s)
        self.W = int(W)
        self.buf = np.zeros((n, self.W))
        self.cnt = np.zeros(n, dtype=np.int64)

    def spec(self):
        return {"name": f"static{self.W}", "W": self.W}

    def step(self, s, alarm, rel):
        v = rel.valid
        idx = np.flatnonzero(v)
        self.buf[idx, self.cnt[idx] % self.W] = (rel.l0 - rel.l1)[idx]
        self.cnt += v
        full = self.cnt >= self.W
        go = full & (self.buf.mean(axis=1) * (self.T - s) > self.c_s)
        self.a = (self.a.astype(bool) | go).astype(np.int8)
        return self.a, np.zeros(self.n, bool)


CONTROLLERS = {
    c.name: c
    for c in (
        Permanent,
        Hold,
        Reverse,
        NeverSwitch,
        AlwaysChallenger,
        CalendarBatch,
        StaticThreshold,
    )
}
