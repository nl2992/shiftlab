"""Light invariants for the GAVE-R WP5 factorial (budget, released labels only, delay gate)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]

from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver.integrated import GaverMethod, pave_active

D50 = "on0.6_L1_strong_harmful_d50_b0.05_s0.1"
D1 = "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1"
SEED = 101160001


class Spy(GaverMethod):
    def start(self, cfg):
        super().start(cfg)
        self.seen = []

    def step(self, t, released):
        self.seen.append((t, [ev for ev, _ in released]))
        return super().step(t, released)


@pytest.mark.parametrize("cid", [D50, D1])
@pytest.mark.parametrize("ev", ["dss", "gapmix", "env", "mlr"])
@pytest.mark.parametrize("aq", ["dss", "pave"])
def test_budget_and_no_unreleased_labels(cid, ev, aq):
    cell = build_cell(cid)
    cfg, stream = cell.config(SEED), fa.make_stream(cell, SEED)
    m = Spy(ev, aq)
    r = fa.run_for(cell, stream, m, cfg)
    assert r.queries <= cfg.B and m.used == r.queries
    for t, evs in m.seen:
        assert all(e + cfg.d == t for e in evs)  # released exactly d after request
    assert not m._evq


def test_delay_gate():
    assert pave_active(build_cell(D50).config(0))  # 50 >= 2000/52
    assert not pave_active(build_cell(D1).config(0))
    # inactive cell: gated PAVE is exactly DSS (same actions and queries)
    cell = build_cell(D1)
    cfg, stream = cell.config(SEED), fa.make_stream(cell, SEED)
    a = fa.run_for(cell, stream, GaverMethod("dss", "dss"), cfg)
    b = fa.run_for(cell, stream, GaverMethod("dss", "pave"), cfg)
    c = fa.run_for(cell, stream, comp.build_candidate(comp.dss_spec(4, True)), cfg)
    assert np.array_equal(a.actions, b.actions) and a.cost == b.cost == c.cost


def test_active_cell_pave_differs_and_dss_is_uniform():
    cell = build_cell(D50)
    cfg, stream = cell.config(SEED), fa.make_stream(cell, SEED)
    m = GaverMethod("dss", "dss")
    r = fa.run_for(cell, stream, m, cfg)
    assert m.dss_uniform and not m.pave_on and r.queries == cfg.B
    m2 = GaverMethod("dss", "pave")
    fa.run_for(cell, stream, m2, cfg)
    assert m2.pave_on and not m2.dss_uniform and m2.reserve_n == 0


def test_rollback_hook_replaces_cusum():
    cell = build_cell(D1)
    cfg, stream = cell.config(SEED), fa.make_stream(cell, SEED)
    never = GaverMethod("dss", "dss", rollback_hook=lambda *a: False)
    r = fa.run_for(cell, stream, never, cfg)
    assert r.switches <= 1  # promotion only, no rollback
