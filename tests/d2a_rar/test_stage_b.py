"""WP6 Stage-B runner tests: host unchanged except the hook, timeout->CRASH, cached references, ledger schema and hash chain,
INVALID candidates are not run, KEEP logic on constructed results. CPU-sized (< 60 s)."""

from __future__ import annotations

import json
import sys

import numpy as np
import pytest

from shiftlab.autoresearch import ledger as lg
from shiftlab.autoresearch import stage_b as sb
from shiftlab.autoresearch.stage_b_variants import (
    FeasibleRule,
    FeedDrift2Act,
    FeedRAR,
    GatedBinary,
    Impl,
    Rule,
    resolve,
)
from shiftlab.bench.contract import (
    BudgetSpec,
    ClockSpec,
    DelaySpec,
    EnvSpec,
    StreamSpec,
    UniformQueryNaiveSwitch,
    load_cost_vectors,
    run_paired,
)
from shiftlab.bench.contract.adapters_controls import CONTROLS
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_rar import BinaryPolicy, RARPolicy
from shiftlab.bench.contract.policies import LeakyPendingPolicy

SPEC = StreamSpec(family="sb_smoke", T=300, delay=DelaySpec("fixed", d=10), tau=0.5)
SEEDS = (110_900_000, 110_900_001)


def _env(cv="balanced", cap=40):
    return EnvSpec(
        T=300,
        costs=load_cost_vectors()[cv],
        budget=BudgetSpec(label_cap=cap),
        clocks=ClockSpec(retrain_duration=20, max_lookback=0),
    )


def _trace(r):
    return (r.J, [(a["t"], a["kind"]) for a in r.audit.of("action") if a["performed"]])


def _find(**kw):
    for c in sb.load_batch():
        if all(c.get(k) == v for k, v in kw.items()):
            return c
    raise AssertionError(kw)


# ------------------------------------------------------------------ host unchanged except the hook
@pytest.mark.parametrize(
    "plain,wrapped,cv",
    [
        (lambda: Drift2ActContractPolicy(), lambda: FeedDrift2Act(None), "balanced"),
        (lambda: RARPolicy(), lambda: FeedRAR(None), "intervention_dear"),
        (lambda: BinaryPolicy(cost_aware=True), lambda: GatedBinary(None), "intervention_dear"),
    ],
)
def test_wrapper_without_hook_is_behaviourally_identical_to_host(plain, wrapped, cv):
    env = _env(cv)
    pr = run_paired({"plain": plain, "wrapped": wrapped}, SPEC, env, SEEDS)
    for a, b in zip(pr.runs["plain"], pr.runs["wrapped"], strict=True):
        assert _trace(a) == _trace(b)


class PassThrough(Rule):
    def size(self, f, n0, info):
        return n0


class DropAll(Rule):
    def size(self, f, n0, info):
        return 0


def test_hook_changes_only_label_requests_of_drift2act():
    env = _env()
    pr = run_paired(
        {
            "host": lambda: FeedDrift2Act(None),
            "pass": lambda: FeedDrift2Act(PassThrough()),
            "drop": lambda: FeedDrift2Act(DropAll()),
        },
        SPEC,
        env,
        SEEDS,
    )
    for h, p, d in zip(pr.runs["host"], pr.runs["pass"], pr.runs["drop"], strict=True):
        assert _trace(h) == _trace(p)  # a pass-through hook is the host
        assert d.counts["N_q"] == 0 < h.counts["N_q"]  # the hook controls label requests ...
        assert h.stream_fingerprint == d.stream_fingerprint  # ... on the same stream


def test_rule_state_is_fresh_for_every_policy_instance():
    c = _find(variant="release_feasible_requests", host="drift2act", target_null="economic")
    impl, _ = resolve(c)
    a, b = impl.build_cand(None), impl.build_cand(None)
    assert a is not b and a.rule is not b.rule and isinstance(a.rule, FeasibleRule)


def test_unfaithful_mechanisms_are_skipped_with_a_reason():
    c = _find(hook="d2a.evidence_log_lik")
    impl, why = resolve(c)
    assert impl is None and "evidence" in why


# ------------------------------------------------------------------ simple controls (comparators)
def test_controls_fixed_schedule_equals_naive_and_others_are_honest():
    env = _env(cap=30)
    pr = run_paired(
        {
            "naive": lambda: UniformQueryNaiveSwitch(),
            "fixed": lambda: CONTROLS["fixed_schedule"].build(env),
            "uniform": lambda: CONTROLS["uniform_query"].build(env),
            "pcap": lambda: CONTROLS["pending_cap"].build(env),
        },
        SPEC,
        env,
        SEEDS,
    )  # verify_run inside: declared propensities honest, budgets respected
    for a, b in zip(pr.runs["naive"], pr.runs["fixed"], strict=True):
        assert _trace(a) == _trace(b)
    for r in pr.runs["uniform"] + pr.runs["pcap"]:
        assert r.counts["N_q"] <= 30


# ------------------------------------------------------------------ decision logic on constructed results
def _run(J, promoted=False, nq=10, viol=None, rolled=False):
    return {
        "seed": 0,
        "fingerprint": "f",
        "J": float(J),
        "breakdown": {"loss": float(J), "cost_N_q": 0.25 * nq, "J": float(J)},
        "counts": {"N_q": nq},
        "promoted": promoted,
        "t_promo": 100 if promoted else None,
        "retrain_deployed": False,
        "rolled_back": rolled,
        "abs_violation": viol,
        "onset": 80,
    }


def _cells(cand_scale=0.85, ctl_scale=1.0, host_J=600.0, fp_cand=False):
    rng = np.random.default_rng(0)
    out = []
    spec = [
        ("correct_null", "a", True),
        ("adverse_sampling_stress", "b", False),
        ("alternative", "c", False),
        ("neighbouring_negative_control", "d", True),
    ]
    for role, fam, null in spec:
        base = host_J + rng.normal(0, 3, 20)
        sc = cand_scale if role in ("adverse_sampling_stress", "alternative") else ctl_scale
        out.append(
            {
                "role": role,
                "family": fam,
                "cost_vector": "x",
                "null_expected": {"cond": null, "marg": null},
                "runs": {
                    "host": [_run(j) for j in base],
                    "cand": [_run(j * sc, promoted=fp_cand and null) for j in base],
                    "fixed_schedule": [_run(j * 1.02, promoted=True) for j in base],
                    "other": [_run(j * 1.00) for j in base],
                },
            }
        )
    return out


META = {
    "fixed_schedule": {"claimed_null": "none", "is_control": True},
    "other": {"claimed_null": "cond", "is_control": False},
}


def test_keep_when_valid_better_and_controls_not_worse():
    a = sb.analyse(_cells(), cand_null="economic", comp_meta=META, cx=2)
    assert a["decision"] == "KEEP", a["why"]
    assert a["effect_vs_strongest"]["label"] == "substantial"
    assert a["strongest_comparator"] in ("host", "other")


def test_discard_when_no_effect_or_control_regression_or_invalid():
    assert (
        sb.analyse(_cells(1.0), cand_null="economic", comp_meta=META, cx=2)["decision"] == "DISCARD"
    )
    worse_ctl = sb.analyse(_cells(0.85, ctl_scale=1.10), cand_null="economic", comp_meta=META, cx=2)
    assert worse_ctl["decision"] == "DISCARD" and not worse_ctl["controls_ok"]
    # cond-null candidate that promotes on cond-null cells while a valid-conservative host never does
    inv = sb.analyse(_cells(0.85, fp_cand=True), cand_null="cond", comp_meta=META, cx=2)
    assert inv["decision"] == "DISCARD" and inv["validity"]["candidate"]["rate"] > 0.5


def test_cond_method_is_not_scored_on_marg_only_cells():
    cells = _cells()
    cells[0]["null_expected"] = {"cond": False, "marg": True}  # marg holds, cond fails
    for r in cells[0]["runs"]["cand"]:
        r["promoted"] = True
    v = sb.validity_of(cells, "cand", "cond", False)
    assert "correct_null:a" not in v["validity_cells"]
    assert sb.validity_of(cells, "cand", "marg", False)["rate"] > 0


def test_absent_family_is_unverified_and_no_baseline_is_unverified():
    a = sb.analyse(_cells(), cand_null="economic", comp_meta=META, cx=2, absent_family="reversal")
    assert a["decision"] == "UNVERIFIED" and a["would_keep"]
    a = sb.analyse(_cells(), cand_null="economic", comp_meta={}, cx=2)
    assert a["decision"] == "UNVERIFIED"


def test_small_effect_with_high_complexity_is_discarded():
    a = sb.analyse(_cells(0.985), cand_null="economic", comp_meta=META, cx=4)
    assert a["effect_vs_strongest"]["label"] == "small" and a["decision"] == "DISCARD"


# ------------------------------------------------------------------ cache, timeout, schema, INVALID
@pytest.fixture
def cheap_baselines(monkeypatch):
    monkeypatch.setattr(
        sb,
        "BASELINE_IMPL",
        {
            "fixed_schedule": "fixed_schedule",
            "uniform_query": "uniform_query",
            "drift2act_unmodified": "host_d2a",
        },
    )


def test_cached_reference_is_computed_once_and_reused(tmp_path, monkeypatch):
    cell = sb.suite_cells("Q2")[0]
    r1 = sb.cached_reference("fixed_schedule", 0, cell, "label_dear", "default", tmp_path)
    assert len(list(tmp_path.glob("*.json"))) == 1

    def boom(*a, **k):
        raise AssertionError("reference recomputed instead of read from cache")

    monkeypatch.setattr(sb, "run_method", boom)
    r2 = sb.cached_reference("fixed_schedule", 0, cell, "label_dear", "default", tmp_path)
    assert r1 == r2
    assert [x["seed"] for x in r1] == sb.cell_seeds(
        0
    )  # shared, fixed paired seed set from d2a_rar_dev


def test_full_experiment_ledger_record_schema_and_hash_chain(tmp_path, cheap_baselines):
    c = _find(variant="release_feasible_requests", host="drift2act", target_null="economic")
    impl, _ = resolve(c)
    rec = sb.run_experiment(c, impl, cache_dir=tmp_path / "cache")
    led = tmp_path / "ledger.jsonl"
    out = sb.commit(rec, led)
    assert out["decision"] in ("KEEP", "DISCARD", "UNVERIFIED")
    for k in lg.REQUIRED:
        assert k in out
    assert out["seed_group"]["block"] == "d2a_rar_dev" and out["seed_group"]["exposure"] == "dev"
    assert out["runtime_s"] < sb.TIMEOUT_S
    assert out["preregistered_predictions"]["sha256"]
    assert isinstance(out["baselines_missing"], list)
    comp = next(iter(out["results"]["components_per_cell"]["cand"].values()))
    for k in ("loss", "cost_N_q", "cost_N_s", "cost_N_r", "cost_N_b", "cost_N_a", "cost_N_h"):
        assert k in comp
    # an identical-behaviour candidate is DUPLICATE, not a second decision
    other = dict(rec, candidate_id="CAND-other", run_id="B-other")
    dup = sb.commit(other, led)
    assert dup["decision"] == "DUPLICATE" and dup["duplicate_of"] == c["candidate_id"]
    assert lg.verify(led).n_records == 2
    lines = led.read_text(encoding="utf-8").splitlines()
    led.write_text(
        "\n".join([lines[0].replace('"B"', '"A"', 1), lines[1]]) + "\n", encoding="utf-8"
    )
    with pytest.raises(lg.LedgerTampered):
        lg.verify(led)


def test_timeout_is_a_crash_record_not_a_silent_truncation(tmp_path):
    c = _find(variant="release_feasible_requests", host="drift2act", target_null="economic")
    led = tmp_path / "ledger.jsonl"
    action, rec = sb.screen(
        c,
        tmp_path / "work",
        timeout_s=2,
        argv=[sys.executable, "-c", "import time; time.sleep(30)"],
        ledger_path=led,
    )
    assert action == "crash" and rec["decision"] == "CRASH" and "timeout" in rec["error"]
    out = sb.commit(rec, led)
    assert out["decision"] == "CRASH" and out["runtime_s"] < 20
    assert lg.verify(led).n_records == 1


def test_null_mismatched_candidate_is_invalid_and_not_run(tmp_path):
    c = dict(_find(variant="release_feasible_requests", host="drift2act", target_null="economic"))
    c["scoring_null"] = "marg"  # scored on a different null than claimed (the P2 error)
    marker = tmp_path / "ran.txt"
    led = tmp_path / "ledger.jsonl"
    action, rec = sb.screen(
        c,
        tmp_path / "work",
        argv=[sys.executable, "-c", f"open(r'{marker}','w').write('x')"],
        ledger_path=led,
    )
    assert action == "invalid" and not marker.exists()
    out = sb.commit(rec, led)
    assert out["decision"] == "INVALID" and "scoring_null" in out["invalid_reason"]


def test_leaky_candidate_is_flagged_invalid_by_the_guards(tmp_path, monkeypatch, cheap_baselines):
    c = _find(variant="release_feasible_requests", host="drift2act", target_null="economic")
    monkeypatch.setattr(
        sb, "resolve", lambda cand: (Impl("naive", {}, lambda env: LeakyPendingPolicy()), "")
    )
    cp, op = tmp_path / "c.json", tmp_path / "o.json"
    cp.write_text(json.dumps(c), encoding="utf-8")
    sb.worker_main(str(cp), str(op), str(tmp_path / "cache"))
    out = json.loads(op.read_text(encoding="utf-8"))
    assert out["status"] == "invalid" and out["record"]["decision"] == "INVALID"
    assert "Leak" in out["record"]["invalid_reason"] or "Label" in out["record"]["invalid_reason"]
