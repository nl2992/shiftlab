"""Correctness smoke on C6: all methods agree exactly on the certified cost."""

from __future__ import annotations

from fractions import Fraction as F

from shiftlab.paper4_continuation.ablation import METHODS, run_method

U0_C6 = F(6357803, 1600000)


def test_all_methods_agree_on_c6():
    out = {m: run_method(m, "C6") for m in METHODS}
    reference = out["R0"]["final_cost"]
    assert reference == F(39589, 10000)
    for m in ("R1", "R2", "F0"):
        assert out[m]["final_cost"] == reference, m
    # I0 is the IID relaxation + repair: a valid upper bound (U0), not the optimum.
    assert out["I0"]["final_cost"] == U0_C6 == out["F0"]["U0"]
    assert out["I0"]["final_cost"] > reference
    assert out["I0"]["L"] <= reference
    assert out["F0"]["cuts"] == 21 and out["I0"]["cuts"] == 0
    for m in METHODS:
        assert out[m]["exact_risk"] <= F(1, 10)
    assert out["R1"]["learner_sequences"] == out["R0"]["learner_sequences"]
    assert out["R1"]["belief_cache_misses"] > 0
