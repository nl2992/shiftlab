"""A7 mechanism stage: M2 source replacement, M3 stake-matched controls, freeze ordering, guard (CPU, tiny)."""

import importlib.util
import sys
from pathlib import Path

import pytest
import torch

from shiftlab.hgxh2c import baselines as BL
from shiftlab.hgxh2c import grammar as G
from shiftlab.hgxh2c import mechanism as MC
from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.evaluate import score

ROOT = Path(__file__).resolve().parents[1]
CELL = TP.ScenarioCell("coshift", 0.16, 0, "full", "good", 200)


def cand(slots=None, **kw):
    s = [()] * 6
    for i, v in (slots or {}).items():
        s[i] = v
    return G.Candidate(tuple(s), **kw)


SHIFT = cand({0: (("shift", (0.3,)),)}, comb="mix", w=0.5)  # BC direction, S slot


def test_m2_replaces_only_source_and_keeps_target_tau():
    tape = TP.generate(CELL, "confirm", 4)
    alt = MC.generate_indep(CELL, "confirm", 4)
    tp = MC.replace_source(tape, alt, "B")
    assert torch.equal(tp["C"], tape["C"]) and torch.equal(tp["Chat"], tape["Chat"])
    assert tp["eval"] is tape["eval"] and torch.equal(tp["eval"]["tau"], tape["eval"]["tau"])
    assert torch.equal(tp["U"], tape["U"]) and torch.equal(tp["d"], tape["d"])
    assert torch.equal(tp["B"], alt["B"]) and torch.equal(tp["Bhat"], alt["Bhat"])
    assert not torch.equal(tp["B"], tape["B"])  # independent stream differs
    assert not torch.equal(alt["eval"]["tau"], tape["eval"]["tau"])
    # the original tape object is untouched and a fresh unsalted draw is bit-identical (patch undone)
    again = TP.generate(CELL, "confirm", 4)
    assert torch.equal(again["B"], tape["B"]) and torch.equal(
        again["eval"]["tau"], tape["eval"]["tau"]
    )
    assert MC.source_channels(SHIFT) == "B"


def test_m2_no_transfer_gain_vanishes():
    tape = TP.cat_tapes([TP.generate(CELL, "confirm", 6)])
    alt = TP.cat_tapes([MC.generate_indep(CELL, "confirm", 6)])
    none = cand(comb="mix", w=0.5)
    assert MC.source_channels(none) == ""
    j = lambda res, mid: score(res, tape, "J", 0, mid).J_cost.to_numpy()
    mix = j(BL.REGISTRY["mix_w0.5"][0]().run(tape), "mix")
    cn = j(G.compile_batch([none]).run(tape), "none")
    assert abs(cn - mix).max() < 1e-9  # no-transfer candidate == mix_w0.5
    tp = MC.replace_source(
        tape, alt, "B"
    )  # force a replacement: matched comparator still equals the candidate
    mt = j(BL.REGISTRY["mix_w0.5"][0]().run(tp), "mix_m2")
    cm = j(G.compile_batch([none]).run(tp), "none_m2")
    assert abs(cm - mt).max() < 1e-9  # M2 delta J = 0 exactly without transfer


def test_m3_controls_keep_factors_nonnegative_and_are_info_free():
    tape = TP.cat_tapes([TP.generate(CELL, "dev", 4)])
    add = MC.measure_shift_addon(SHIFT, tape)
    assert add["C"] > 0 and add["B"] == 0.0  # BC direction targets C
    for kw in ({"add": add}, {"mult": 2.0}, {"add": {"B": 0.05, "C": 0.05}, "mult": 1.5}):
        r = MC.mix_control(**kw).run(tape, keep_paths=True)
        for n in "BC":
            lam = r.lam[n]
            assert float(lam.min()) >= 0.0 and torch.isfinite(r.logW[n]).all()
    with pytest.raises(ValueError):
        MC.mix_control(add={"B": -0.1})
    # info-free: replacing the source channel cannot change the control run (it never reads cross-track data)
    alt = TP.cat_tapes([MC.generate_indep(CELL, "dev", 4)])
    a = MC.mix_control(add=add).run(tape).alarm["C"]
    b = MC.mix_control(add=add).run({**tape, "B": alt["B"], "Bhat": alt["Bhat"]}).alarm["C"]
    assert torch.equal(a, b)


def test_params_freeze_before_confirm(tmp_path):
    with pytest.raises(RuntimeError):
        MC.verify_m3(tmp_path)  # nothing frozen: confirm must not start
    p = MC.select_m3([SHIFT], [CELL], 4, "cpu", score, mults=(1.0, 1.5))
    assert p["mult"] in (1.0, 1.5) and SHIFT.hash in p["addon"]
    MC.freeze_m3(tmp_path, p)
    assert MC.verify_m3(tmp_path)["mult"] == p["mult"]
    (tmp_path / MC.PARAMS).write_text('{"mult": 1.0}')
    with pytest.raises(RuntimeError):
        MC.verify_m3(tmp_path)  # tampered after freeze


def test_script_refuses_without_freeze(tmp_path, monkeypatch):
    sp = importlib.util.spec_from_file_location("s4m", ROOT / "scripts/hgxh2c/stage4_mechanism.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    monkeypatch.setattr(
        sys, "argv", ["x", "--freeze-file", str(tmp_path / "none.json"), "--device", "cpu"]
    )
    with pytest.raises(RuntimeError, match="FREEZE"):
        m.main()
    assert not (ROOT / "outputs/hgxh2c/stage4_mechanism/shards").exists()


def test_verdicts():
    sp = importlib.util.spec_from_file_location("s4m2", ROOT / "scripts/hgxh2c/stage4_mechanism.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    ci = lambda mean, lo, hi, p=0.001: {"mean": mean, "lo": lo, "hi": hi, "p": p}
    v = {
        "gain_vs_mix": ci(1, 0.5, 1.5),
        "m2": {"a": ci(0.0, -0.3, 0.3), "note": "x"},
        "m3": {
            "a": ci(0.4, 0.1, 0.7),
            "b": ci(0.3, 0.1, 0.5),
            "m3a_holm_p": 0.01,
            "m3b_holm_p": 0.01,
        },
    }
    assert m.verdict(v) == "TRANSFER_SUPPORTED"
    v["m3"]["b"] = ci(0.0, -0.2, 0.2, 0.5)
    v["m3"]["m3b_holm_p"] = 0.9
    assert m.verdict(v) == "STAKE_SIZE_EFFECT"
    v["gain_vs_mix"] = ci(0.0, -0.1, 0.1)
    assert m.verdict(v) == "INCONCLUSIVE"
