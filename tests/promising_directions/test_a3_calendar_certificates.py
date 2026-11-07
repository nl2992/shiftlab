from __future__ import annotations

import importlib.util
import sys
import time
from fractions import Fraction as F
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/promising_directions"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "a3_calendar_certificates", SCRIPTS / "a3_calendar_certificates.py"
)
a3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a3)
a1 = a3.a1

ROOT = Path(a1.DEFAULT_SOLVER_ROOT)
needs_solver = pytest.mark.skipif(not ROOT.exists(), reason="solver root missing")


def flags(**kw) -> dict:
    base = {"support_size": 1, "P_holds": False, "chain_deterministic": False}
    return {**base, **kw}


def test_classify_priority_and_overlap():
    assert a3.classify(flags(support_size=3, P_holds=True, chain_deterministic=True), 3) == {
        "cert_prop6": True,
        "cert_thm7_pure": True,
        "cert_thm7_mix": True,
        "cert_class": "prop6",
        "certifies_C_star": True,
    }
    c = a3.classify(flags(support_size=4, P_holds=True, chain_deterministic=True), 3)
    assert c["cert_class"] == "thm7_pure"
    assert c["certifies_C_star"]
    c = a3.classify(flags(support_size=4, P_holds=True, chain_deterministic=False), 3)
    assert c["cert_class"] == "thm7_mix"
    assert not c["certifies_C_star"]
    c = a3.classify(flags(support_size=4, P_holds=False, chain_deterministic=True), 3)
    assert c["cert_class"] == "uncertified"
    assert not c["cert_prop6"] and not c["cert_thm7_pure"] and not c["cert_thm7_mix"]


def test_decision_rules():
    base = {
        "tight_completed": 5,
        "uncertified_cells": [],
        "n_tight_cells_with_g_positive": 0,
        "n_tight_cells_g_undetermined": 0,
    }
    assert a3.decide_part1(base) == "THEOREM EXPLAINS"
    assert a3.decide_part1({**base, "uncertified_cells": [{}]}) == "PARTIAL"
    assert a3.decide_part1({**base, "tight_completed": 0}) == "NO_DATA"
    assert a3.decide_part2(base) == "CALENDAR-OPTIMAL AT B=4"
    assert a3.decide_part2({**base, "n_tight_cells_with_g_positive": 1}) == "GAP AT B=4"
    assert a3.decide_part2({**base, "n_tight_cells_g_undetermined": 1}).startswith("INCOMPLETE")


def test_effective_g_positive():
    assert a3.effective_g_positive({"certifies_C_star": True}) is False
    assert a3.effective_g_positive({"certifies_C_star": False}) is None
    assert a3.effective_g_positive({"certifies_C_star": False, "computed": {"g_positive": True}})


@needs_solver
def test_enumerator_on_hand_policies():
    a1.verify_solver(ROOT)
    a1.load_solver(str(ROOT))
    p = {
        "T": 5, "B": 1, "d": 1, "trans": "1/10", "e0": "1/10", "e1": "9/10",
        "alpha": "1/10", "cq": "1/100", "cs": "1/20", "prior1": "1/5",
    }  # fmt: skip
    cfg, model = a1.make(p)
    game = a1._SOLVER["Joint"](cfg, model)
    far = time.time() + 600

    def one_hot(history, action, query):
        return tuple(F(c == (action, query)) for c in game.choices(history))

    def make_policy(promote_on_zero: bool):
        def pol(history, outcomes):
            t = len(history) + 1
            old = history[-1][0] if history else 0
            released = dict(game.information(history, outcomes)[1])
            if t == 1:
                return one_hot(history, 0, 1)
            if old == 1:
                return one_hot(history, 1, 0)
            go = t == 3 and (promote_on_zero or released.get(1) == 1)
            return one_hot(history, int(go), 0)

        return pol

    ok = a3.enumerate_flags(game, make_policy(False), far)
    assert ok["query_support"] == [1]
    assert ok["P_holds"] and ok["Pprime_holds"]
    assert ok["promotion_times"] == [3]
    assert ok["promotion_mass_by_t_released_zeros"] == {"3,1,0": pytest.approx(ok["p_promote"])}
    assert ok["chain_query_times"] == [1] and ok["chain_deterministic"]
    assert ok["chain_paths_query_times"] == [[1]]

    bad = a3.enumerate_flags(game, make_policy(True), far)
    assert not bad["P_holds"] and not bad["Pprime_no_promo_after_zero"]
    assert set(bad["P_violations"]) == {"3,1,1"}
    assert bad["Pprime_no_query_after_promo"]
    assert bad["p_promote"] == pytest.approx(1.0)


@needs_solver
@pytest.mark.parametrize("alpha", ["1/20", "1/10", "1"])
def test_flags_consistent_with_independent_calendar_gap(alpha):
    a1.verify_solver(ROOT)
    a1.load_solver(str(ROOT))
    p = {
        "T": 4, "B": 2, "d": 1, "trans": "1/10", "e0": "1/10", "e1": "9/10",
        "alpha": alpha, "cq": "1/100", "cs": "1/20", "prior1": "1/5",
    }  # fmt: skip
    cfg, model = a1.make(p)
    game = a1._SOLVER["Joint"](cfg, model)
    rep, pol, _ = game.solve()
    fl = a3.enumerate_flags(game, pol, time.time() + 600)
    cls = a3.classify(fl, p["B"])
    ref = a1.solve_cell(p)  # independent: joint vs every fixed calendar
    j = F(rep["calibrated_total_cost"])
    assert str(j) == ref["J"]
    assert set(fl["query_support"]) <= set(range(1, p["T"] + 1))
    assert fl["P_holds"] == (not fl["P_violations"])
    # A policy never spends beyond B on a path, so a support larger than B needs branching.
    if cls["certifies_C_star"]:
        assert abs(F(ref["abs_gap"])) <= a3.GAP_TOL
    if cls["cert_prop6"]:
        crep = a1._SOLVER["Calendar"](cfg, model, tuple(fl["query_support"])).solve()[0]
        assert abs(F(crep["calibrated_total_cost"]) - j) <= a3.GAP_TOL
