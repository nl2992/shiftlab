"""Tests for the B3+ dataset-screening pipeline (research/b3_plus/dataset_discovery).

All tests run on small synthetic streams (CPU, seconds)
none touches the network or raw data. The
saved-results check only reads files already written by a screening run and skips if absent.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "research/b3_plus/dataset_discovery"
sys.path.insert(0, str(DISC))
sys.path.insert(0, str(ROOT / "scripts/promising_directions"))

import construct_model_pairs as cmp
import dataset_sources as dsrc
import registry as reg
import screen_candidate as sc
import validate_stream as vs


# ------------------------------------------------------------------------------ helpers
def synthetic_raw(n=12000, seed=0, flip_locked=False, dataset_id="synthetic"):
    """Quadrant-XOR stream: LR cannot fit it, HGB can, so the dev headroom precheck passes."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 3))
    y = (x[:, 0] * x[:, 1] > 0).astype(int)
    if flip_locked:  # only labels in the locked window [60%, end) change
        y[int(0.6 * n) :] = 1 - y[int(0.6 * n) :]
    return dsrc.RawStream(dataset_id, pd.DataFrame(x, columns=["a", "b", "c"]), y)


def entry(dataset_id="synthetic", basis="documented_order", declared=True, family="synthetic_fam"):
    e = reg._cand(
        1,
        dataset_id,
        family,
        "synthetic",
        None,
        "synthetic",
        12000,
        3,
        "binary",
        reg._delay(20, "imposed_cap", "test delay"),
        {
            "declared_basis": basis,
            "justification": "test",
            "time_column": None,
            "time_reliable": None,
        },
    )
    e["timestamps"]["registered_at_utc"] = reg.now()
    if declared:
        e["declared_delay"]["declared_at_utc"] = reg.now()
    return e


def registry_with(*entries):
    return {"candidates": list(entries)}


# ------------------------------------------------------------------------------ binarisation
def test_binarisation_class0_when_rate_in_range():
    y = np.array([0] * 30 + [1] * 70 + [0] * 1000)  # only the first 100 (the train window) count
    info = cmp.binarise_info(y[:100])
    assert info["rule"] == "class0_vs_rest" and info["target_class"] == 0
    assert info["class0_rate_train"] == pytest.approx(0.30)


def test_binarisation_falls_back_to_majority_when_class0_rare():
    y = np.array([0] * 2 + [1] * 60 + [2] * 38)  # class 0 rate 2% < 0.05
    info = cmp.binarise_info(y)
    assert info["rule"] == "majority_vs_rest" and info["target_class"] == 1
    # and when class 0 is too common (> 0.95) the majority class (class 0 itself) is the target
    info2 = cmp.binarise_info(np.array([0] * 99 + [1]))
    assert info2["rule"] == "majority_vs_rest" and info2["target_class"] == 0


def test_binarisation_boundaries_and_ties_and_string_labels():
    assert (
        cmp.binarise_info(np.array([0] * 5 + [1] * 95))["rule"] == "class0_vs_rest"
    )  # 0.05 inclusive
    assert (
        cmp.binarise_info(np.array([0] * 95 + [1] * 5))["rule"] == "class0_vs_rest"
    )  # 0.95 inclusive
    tie = cmp.binarise_info(np.array(list("abcd") * 5 + ["a"] * 0))  # class 'a' rate 0.25 -> class0
    assert tie["target_class"] == "a"
    tie2 = cmp.binarise_info(np.array([1] * 50 + [2] * 50 + [3] * 1))  # class 0 rate .495 ok
    assert tie2["rule"] == "class0_vs_rest"
    assert cmp.binarise_info(np.array([7] * 10))["rule"] == "degenerate_single_class"


def test_binarisation_decided_on_training_window_only():
    n = 1000
    y = np.array(([0, 0, 1] * 334)[:n])
    y01_a, info_a = cmp.binarise(y, 300)
    y2 = y.copy()
    y2[300:] = 1  # change labels strictly after n30
    _, info_b = cmp.binarise(y2, 300)
    assert info_a == info_b and info_a["rule"] == "class0_vs_rest"
    assert y01_a.shape == (n,) and set(np.unique(y01_a)) <= {0, 1}


# ------------------------------------------------------------------------------ headroom precheck
def _losses(dis, inc, chal, n=1000):
    """Construct dev losses with a given disagreement/incumbent/challenger error (exact)."""
    l0 = np.zeros(n, dtype=np.int8)
    l1 = np.zeros(n, dtype=np.int8)
    l0[: int(inc * n)] = 1
    # challenger corrects some incumbent errors and (optionally) errs elsewhere
    l1[: int(chal * n)] = 1
    return l0, l1


def test_headroom_precheck_each_condition():
    n = 1000
    # passes: dis 0.10, adv 0.05 -> adv*T = 100 > 5
    l0 = np.zeros(n, dtype=np.int8)
    l0[:100] = 1
    l1 = np.zeros(n, dtype=np.int8)
    l1[:50] = 1
    r = cmp.headroom_precheck(l0, l1, 2000, 5.0)
    assert r["passes"] and r["cond_disagree_ge_0.02"] and r["adv_times_T"] == pytest.approx(100.0)
    # fails on disagreement (<0.02) although the challenger is better and adv*T > cs
    l0 = np.zeros(n, dtype=np.int8)
    l0[:15] = 1
    l1 = np.zeros(n, dtype=np.int8)
    r = cmp.headroom_precheck(l0, l1, 2000, 5.0)
    assert (
        r["disagree"] == pytest.approx(0.015) and not r["cond_disagree_ge_0.02"] and not r["passes"]
    )
    assert r["cond_adv_T_gt_cs"] and r["cond_challenger_better"]
    # fails because challenger is not better, even with large disagreement
    l0 = np.zeros(n, dtype=np.int8)
    l0[:100] = 1
    l1 = np.zeros(n, dtype=np.int8)
    l1[100:300] = 1
    r = cmp.headroom_precheck(l0, l1, 2000, 5.0)
    assert not r["cond_challenger_better"] and not r["passes"]
    # fails because the gain cannot repay c_s within an episode: adv*T = 4 <= 5 (strict)
    l0 = np.zeros(2000, dtype=np.int8)
    l0[:24] = 1
    l1 = np.zeros(2000, dtype=np.int8)
    l1[:22] = 1
    r = cmp.headroom_precheck(l0, l1, 2000, 5.0)
    assert r["adv_times_T"] == pytest.approx(2.0) and not r["cond_adv_T_gt_cs"]
    # exactly break-even is NOT enough
    l0 = np.zeros(2000, dtype=np.int8)
    l0[:50] = 1
    l1 = np.zeros(2000, dtype=np.int8)
    l1[:47] = 1  # adv = 0.0015 -> *2000 = 3 ; make it 5 exactly
    l1 = np.zeros(2000, dtype=np.int8)
    l1[:45] = 1  # adv = 0.0025 -> adv*T = 5.0 == cs
    r = cmp.headroom_precheck(l0, l1, 2000, 5.0)
    assert r["adv_times_T"] == pytest.approx(5.0) and not r["cond_adv_T_gt_cs"]


def test_pair_selection_uses_dev_window_only():
    raw = synthetic_raw()
    w = cmp.windows(raw.n)
    y01 = raw.y.astype(np.int8)
    sel = cmp.select_pair(raw.X.iloc[: w["n60"]], y01[: w["n60"]], w)
    assert sel["passes_headroom"] and sel["chosen"]["name"] == "A"
    assert sel["tried"][0]["dev"]["dev_rows"] == w["n60"] - w["n30"]
    # the locked window is not an argument: passing more than n60 rows is refused
    with pytest.raises(ValueError):
        cmp.select_pair(raw.X, y01, w)
    # locked losses are refused for a pair that failed the precheck
    bad = dict(sel, passes_headroom=False)
    with pytest.raises(RuntimeError):
        cmp.locked_episode_losses(bad, raw.X, y01, [w["n60"]])


def test_option_b_tried_only_after_option_a_fails():
    # an unlearnable stream: pure noise labels, so no challenger has dev headroom
    rng = np.random.default_rng(3)
    n = 6000
    x = pd.DataFrame(rng.normal(size=(n, 3)), columns=list("abc"))
    y = rng.integers(0, 2, n).astype(np.int8)
    w = cmp.windows(n)
    sel = cmp.select_pair(x.iloc[: w["n60"]], y[: w["n60"]], w)
    assert [t["name"] for t in sel["tried"]] == ["A", "B"] and not sel["passes_headroom"]
    assert sel["challenger"] is None and sel["chosen"] is None


# ------------------------------------------------------------------------------ screening
def test_pair_and_headroom_identical_when_only_locked_labels_change(tmp_path):
    """Selection must not see the locked window: flipping every locked label cannot change it."""
    outs = []
    for flip in (False, True):
        raw = synthetic_raw(flip_locked=flip)
        rg = registry_with(entry())
        res = sc.screen(
            "synthetic",
            registry=rg,
            reg_path=None,
            out_root=tmp_path / str(flip),
            raw=raw,
            n_seeds=3,
            max_episodes=1,
        )
        assert res["screening"]["stage"] == "evaluated"
        pair = json.loads((tmp_path / str(flip) / "synthetic" / "_debug" / "pair.json").read_text())
        outs.append(pair)
    a, b = outs
    assert a["options_tried_in_order"] == b["options_tried_in_order"] and a["chosen"] == b["chosen"]
    assert a["binarisation"] == b["binarisation"] and a["inc_err_dev"] == b["inc_err_dev"]


def test_budget_holds_pathwise_on_a_new_dataset_stream(tmp_path):
    raw = synthetic_raw(n=14000, seed=5)
    rg = registry_with(entry(dataset_id="synthetic2", family="synthetic2"))
    res = sc.screen(
        "synthetic2",
        registry=rg,
        reg_path=None,
        out_root=tmp_path,
        raw=raw,
        n_seeds=20,
        resume=False,
    )
    assert res["screening"]["stage"] == "evaluated"
    rows = sc.read_rows(tmp_path / "synthetic2/episodes.jsonl")
    assert len(rows) == 2  # K = floor(5600 / 2000) -> min(50, 2)
    for r in rows:
        assert r["budget"] == 200
        for v, st in r["variants"].items():
            assert st["max_queries"] <= 200, (v, st["max_queries"])
        # mechanism bookkeeping: labels before + after promotion equal total P7s labels
        m = r["mechanism"]["P7s"]
        tot = m["mean_labels_before_promotion"] + m["mean_labels_after_promotion"]
        assert tot == pytest.approx(r["variants"]["P7s"]["mean_labels"])
    summ = json.loads((tmp_path / "synthetic2/summary.json").read_text())
    assert summ["conditions"]["3_no_leakage_budget_holds_pathwise"]
    assert summ["low_power"] and summ["bootstrap_level"] == "seed"  # K = 2 < 5
    assert summ["config"] == {
        "T": 2000,
        "budget": 200,
        "cq": 0.05,
        "cs": 5.0,
        "n_seeds": 100,
        "seed_base": 20261101,
    }


def test_p7s_trace_run_matches_untraced_policy():
    exp = sc.exp
    rng = np.random.default_rng(1)
    t = 2000
    l0 = (rng.random(t) < 0.3).astype(np.int8)
    l1 = (rng.random(t) < 0.1).astype(np.int8)
    u = exp.episode_u(0, 8, t, sc.SEED_BASE)
    p = sc.b1.Params(T=t, delay=20, base_err=0.3, eps=0.05)
    ref = exp.run_variants(l0, l1, u, 200, 5.0, 0.05, p, ["P7s"])["P7s"]
    stats, _ = sc.run_episode(l0, l1, u, 20, 0.3)
    cost = ref["loss"] + 0.05 * ref["queries"] + 5.0 * ref["switches"]
    assert stats["P7s"]["mean_cost"] == pytest.approx(float(cost.mean()))


def test_screen_refuses_to_evaluate_when_validation_fails(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("must not be reached when validation fails")

    monkeypatch.setattr(cmp, "select_pair", boom)
    monkeypatch.setattr(cmp, "locked_episode_losses", boom)
    cases = {
        "no_order": entry(basis="none"),
        "timestamp_unreliable": entry(basis="timestamp_column"),
    }
    for name, e in cases.items():
        e = copy.deepcopy(e)
        e["dataset_id"] = name
        e["family"] = name
        raw = synthetic_raw(dataset_id=name)
        if name == "timestamp_unreliable":
            raw.time, raw.time_name = np.arange(raw.n, dtype=float), "t"
            e["chronology"]["time_reliable"] = False
        rg = registry_with(e)
        res = sc.screen(name, registry=rg, reg_path=None, out_root=tmp_path, raw=raw, n_seeds=2)
        assert res["status"] == "USELESS_INELIGIBLE", (name, res)
        assert "locked_window_read_at_utc" not in e["timestamps"]
        assert not (tmp_path / name / "episodes.jsonl").exists()
        assert res["screening"]["stage"] == "validation"


def test_validation_rejects_class_sorted_and_too_short_streams(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cmp, "locked_episode_losses", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    raw = synthetic_raw(n=12000)
    raw.y = np.sort(raw.y)  # a class-sorted file is not a time stream
    rep = vs.validate(raw, entry())
    assert not rep["ok"] and rep["class_sorted_check"]["class_sorted"]
    short = synthetic_raw(n=3000)  # locked window 1200 < one 2000-event episode
    rep = vs.validate(short, entry())
    assert not rep["ok"] and rep["status"] == "USELESS_INELIGIBLE"
    leak = synthetic_raw(n=12000)
    leak.X["a"] = leak.y.astype(float)  # a feature equal to the target
    rep = vs.validate(leak, entry())
    assert not rep["ok"] and rep["status"] == "USELESS_DATA_QUALITY"


def test_timestamp_order_is_sorted_not_assumed():
    raw = synthetic_raw(n=12000)
    rng = np.random.default_rng(0)
    perm = rng.permutation(raw.n)
    raw.X, raw.y = raw.X.iloc[perm].reset_index(drop=True), raw.y[perm]
    raw.time, raw.time_name = perm.astype(float), "t"  # true time is the pre-shuffle index
    e = entry(basis="timestamp_column")
    e["chronology"]["time_reliable"] = True
    order, rep = vs.resolve_order(raw, e["chronology"])
    assert rep["verdict"] == "sorted_by_timestamp" and rep["time_inversions"] > 0
    assert np.all(np.diff(raw.time[order]) >= 0)


def test_delay_must_be_declared_before_evaluation(tmp_path):
    e = entry(declared=False)
    with pytest.raises(RuntimeError, match="delay not declared"):
        sc.screen(
            "synthetic",
            registry=registry_with(e),
            reg_path=None,
            out_root=tmp_path,
            raw=synthetic_raw(),
            n_seeds=2,
        )
    e2 = entry()
    e2["declared_delay"]["value"] = 500
    with pytest.raises(RuntimeError, match="outside"):
        reg.declared_delay(e2)


def test_success_rule_is_the_preregistered_one():
    def summ(hi, p7s, p0, budget_ok=True, mech=True, low=False):
        return {
            "finite_costs": True,
            "low_power": low,
            "paired": {"P7s_minus_P3b": {"mean": hi - 1, "lo": hi - 2, "hi": hi}},
            "mean_cost": {"P7s": p7s, "P0": p0},
            "conditions": {
                "1_P7s_beats_P3b_CI_below_0": hi < 0,
                "2_P7s_below_P0": p7s < p0,
                "3_no_leakage_budget_holds_pathwise": budget_ok,
                "4_mechanism_records_complete_and_explicable": mech,
            },
        }

    assert sc.decide(summ(-0.1, 90, 100))[0] == "SUCCESS"
    assert sc.decide(summ(0.0, 90, 100))[0] == "USELESS_NO_IMPROVEMENT"  # CI must be strictly < 0
    assert (
        sc.decide(summ(-0.1, 100, 100))[0] == "USELESS_NO_HEADROOM"
    )  # mean P7s < mean P0 strictly
    assert sc.decide(summ(-0.1, 90, 100, budget_ok=False))[0] == "USELESS_UNSTABLE"
    assert sc.decide(summ(-0.1, 90, 100), is_duplicate=True)[0] == "USELESS_DUPLICATE"


def test_saved_screening_results_respect_budget_and_declared_delay_order():
    base = ROOT / "docs/promising_directions/results/b3_plus/screening"
    regp = DISC / "dataset_registry.json"
    found = [p for p in base.glob("*/summary.json")] if base.exists() else []
    if not found or not regp.exists():
        pytest.skip("no saved screening results")
    registry = json.loads(regp.read_text())
    for p in found:
        s = json.loads(p.read_text())
        for v, d in s["diagnostics"].items():
            assert d["max_queries_any_episode_seed"] <= s["config"]["budget"], (p, v)
        e = reg.get(registry, s["dataset_id"])
        t = e["timestamps"]
        assert e["declared_delay"]["declared_at_utc"] <= t["locked_window_read_at_utc"]
        assert t["validated_at_utc"] <= t["pair_selected_at_utc"] <= t["locked_window_read_at_utc"]
