"""Light invariants for the PAVE governor (GAVE-R WP2)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]

from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver.pave import PaveMethod, PaveParams

CELLS = (
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1",
    "on0.3_L0.6_strong_harmful_d10_b0.05_s0.1",
)
SEED = 101080011


class Spy(PaveMethod):
    """Records what the method saw, to check accounting and label release."""

    def start(self, cfg):
        super().start(cfg)
        self.seen = []  # (t, released event rounds)

    def step(self, t, released):
        self.seen.append((t, [ev for ev, _ in released]))
        cap = self.pending_capacity(t)
        n_pend = len(self.pending_events - {ev for ev, _ in released})
        out = super().step(t, released)
        if out[1]:  # a request was made: pending before it was below the capacity at t
            self.cap_ok = getattr(self, "cap_ok", True) and n_pend < max(cap, 2)
        return out


@pytest.mark.parametrize("cid", CELLS)
@pytest.mark.parametrize("flags", [(True, True, True), (False, False, False)])
def test_budget_release_and_pending(cid, flags):
    cell = build_cell(cid)
    cfg, stream = cell.config(SEED), fa.make_stream(cell, SEED)
    m = Spy(PaveParams(*flags))
    r = fa.run_for(cell, stream, m, cfg)
    assert r.queries <= cfg.B  # hard pathwise budget
    assert m.used == r.queries == int(r.query_mask.sum())
    req = set(np.flatnonzero(r.query_mask) + 1)  # query_mask index i is round i+1 or i; check both
    req0 = set(np.flatnonzero(r.query_mask))
    # no unreleased label used: every released label was requested exactly d rounds earlier
    released_all = []
    for t, evs in m.seen:
        for ev in evs:
            assert ev + cfg.d == t, "label released early or late"
            released_all.append(ev)
    assert len(released_all) == len(set(released_all))
    assert set(released_all) <= (req0 | req)
    # evidence/decision statistics only contain released labels
    assert len(m.labels) == len(released_all)
    assert len(m.ep_labels) + len(m.post) <= len(released_all)
    # pending accounting: pending == requested - released
    assert len(m.pending_events) == m.used - len(released_all)
    assert getattr(m, "cap_ok", True)


def test_pending_capacity_formula():
    cell = build_cell(CELLS[0])
    cfg = cell.config(SEED)
    m = PaveMethod(PaveParams(pending=True))
    m.start(cfg)
    assert m.pending_capacity(1) == int(np.ceil(50 * 50 / (1000 - 50)))  # = 3
    m2 = PaveMethod(PaveParams(pending=False))
    m2.start(cfg)
    assert m2.pending_capacity(1) == 2


def test_reserve_withheld_before_promotion():
    cell = build_cell(CELLS[1])
    m = PaveMethod(PaveParams(reserve=True, reserve_frac=0.2))
    m.start(cell.config(SEED))
    assert m._b_eff() == cell.B - int(np.ceil(0.2 * cell.B))
    m.act = 1
    assert m._b_eff() == cell.B
    m0 = PaveMethod(PaveParams(reserve=False))
    m0.start(cell.config(SEED))
    assert m0._b_eff() == cell.B


def test_spec_is_frozen_dss_engine():
    assert PaveMethod().spec.spec_id == "5b5c77b635e5"
