"""Amendment A1 wiring (Stage-B tranche 2): checksum gate, seed rule, comparator set, strongest-applicable-comparator
selection, ledger tagging, scope selection and the suite-v1 golden record. CPU-sized."""

from __future__ import annotations

import numpy as np
import pytest

from shiftlab.autoresearch import ledger as lg
from shiftlab.autoresearch import stage_b as sb
from shiftlab.autoresearch import stage_b_v2 as v2
from shiftlab.autoresearch.stage_b_variants import (
    FeedDrift2Act,
    FeedRAR,
    GatedBinary,
    host_profile,
    resolve,
)
from shiftlab.bench.contract import BudgetSpec, ClockSpec, EnvSpec, load_cost_vectors


# ------------------------------------------------------------------ suite checksum
def test_suite_checksum_verified_at_load(tmp_path):
    s = v2.load_suite_v2()
    assert len(s["cells"]) == 15 and s["seeds_per_cell"] == 20
    bad = tmp_path / "DEV_SUITE_v2.json"
    bad.write_text(
        v2.SUITE_V2_PATH.read_text(encoding="utf-8").replace('"T": 400', '"T": 401', 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="sha256"):
        v2.load_suite_v2(suite_path=bad)
    badf = tmp_path / "f.yaml"
    badf.write_text(v2.FAMILIES_V2_PATH.read_text(encoding="utf-8") + "\n# x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sha256"):
        v2.load_suite_v2(families_path=badf)


def test_checksum_is_line_ending_independent(tmp_path):
    lf = tmp_path / "s.json"
    lf.write_bytes(v2.SUITE_V2_PATH.read_bytes().replace(b"\r\n", b"\n"))
    assert v2._sha(lf) == v2.SUITE_V2_SHA256


# ------------------------------------------------------------------ seeds
def test_seeds_follow_the_rule_and_are_disjoint_from_v1():
    cells = v2.load_suite_v2()["cells"]
    allv2: set[int] = set()
    for c in cells:
        s = v2.cell_seeds(c["index"])
        assert s == [110_050_000 + c["index"] * 1000 + r for r in range(20)]
        allv2 |= set(s)
    allv1 = {s for i in range(4) for s in sb.cell_seeds(i)}
    assert len(allv2) == 15 * 20 and not (allv1 & allv2)
    assert max(allv1) < min(allv2) and max(allv2) < 110_100_000


def test_per_cell_environment_comes_from_the_suite():
    for c in v2.load_suite_v2()["cells"]:
        env = v2.make_env(v2.cell_spec(c), c, "default")
        assert (env.T, env.budget.label_cap) == (c["T"], c["label_cap"])
        assert env.costs == load_cost_vectors()[c["cost_vector"]]


# ------------------------------------------------------------------ comparator set
def test_comparator_set_is_complete_and_hosts_are_calibrated():
    assert set(v2.A1_COMPARATORS) == {
        "uniform_query",
        "fixed_schedule",
        "pending_cap",
        "episode_front",
        "never_switch",
        "gapmix_exact08_s4",
        "thinned_hedged_gate",
    }
    env = EnvSpec(
        T=200,
        costs=load_cost_vectors()["balanced"],
        budget=BudgetSpec(label_cap=20),
        clocks=ClockSpec(retrain_duration=20),
    )
    for m in v2.A1_COMPARATORS:
        v2.V2_COMPARATORS[m][0](env)  # builds
    for kind, (name, mk, _null) in v2.HOST_CAL.items():
        assert mk(env).profile == "calibrated_v1", kind
        assert sb.HOST_COMPARATOR[kind] == name
    assert sb.COMPARATORS["host_d2a"][0](env).profile == "native_v0"  # reference stays native
    assert FeedDrift2Act(None).profile == "native_v0"
    with host_profile("calibrated_v1"):
        assert (
            FeedDrift2Act(None).profile
            == FeedRAR(None).profile
            == GatedBinary(None).profile
            == "calibrated_v1"
        )
    assert FeedRAR(None).profile == "native_v0"  # context restored


# ------------------------------------------------------------------ strongest applicable comparator
def _run(j, promoted=False):
    return {
        "seed": 0,
        "fingerprint": "f",
        "J": float(j),
        "breakdown": {"loss": float(j), "cost_N_q": 1.0, "J": float(j)},
        "counts": {"N_q": 4},
        "promoted": promoted,
        "t_promo": 10 if promoted else None,
        "retrain_deployed": False,
        "rolled_back": False,
        "abs_violation": None,
        "onset": 5,
    }


def _v2_cells():
    rng = np.random.default_rng(1)
    spec = [
        ("S1a", "alternative", (False, False, False)),
        ("S1b", "correct_null", (True, True, True)),
        ("S1c", "neighbouring_negative_control", (True, True, True)),
    ]
    out = []
    for cid, role, (c, m, a) in spec:
        base = 500 + rng.normal(0, 2, 20)
        null = c and m
        out.append(
            {
                "id": cid,
                "role": role,
                "family": "f" + cid,
                "cost_vector": "x",
                "null_expected": {"cond": c, "marg": m, "abs_risk": a},
                "runs": {
                    "host": [_run(j) for j in base],
                    "cand": [_run(j * 0.9) for j in base],
                    # cheap naive control that false-promotes on the null cells
                    "naive": [_run(j * 0.5, promoted=null) for j in base],
                    "never_switch": [_run(j * 1.2) for j in base],
                    "valid_cert": [_run(j * 0.8) for j in base],
                },
            }
        )
    return out


V2META = {
    "naive": {"claimed_null": "none", "is_control": True},
    "never_switch": {"claimed_null": "none", "is_control": False},
    "valid_cert": {"claimed_null": "cond", "is_control": False},
}


def test_strongest_comparator_excludes_invalid_comparators_per_cell():
    a = sb.analyse(_v2_cells(), cand_null="cond", comp_meta=V2META, cx=2, suite="v2")
    assert "naive" in a["excluded_comparators_invalid_aggressive"]
    assert "naive" not in a["eligible_comparators"]
    per = a["strongest_comparator_per_cell"]
    assert set(per) == {"S1a", "S1b", "S1c"}
    assert all(v == "valid_cert" for v in per.values())  # lowest J among the valid ones
    assert all(x["comparator"] == "valid_cert" for x in a["dJ_vs_strongest"])
    # no validity claim: the naive control is applicable and is the strongest
    b = sb.analyse(_v2_cells(), cand_null="economic", comp_meta=V2META, cx=2, suite="v2")
    assert b["strongest_comparator_per_cell"]["S1a"] == "naive"
    assert not b["excluded_comparators_invalid_aggressive"]
    # absolute_risk claim: validity cells are those where the abs_risk truth holds
    c = sb.analyse(_v2_cells(), cand_null="absolute_risk", comp_meta=V2META, cx=2, suite="v2")
    assert "naive" in c["excluded_comparators_invalid_aggressive"]


def test_v1_strongest_comparator_rule_is_unchanged():
    cells = _v2_cells()
    for c in cells:
        c.pop("id")
    a = sb.analyse(cells, cand_null="cond", comp_meta=V2META, cx=2)
    assert "strongest_comparator_per_cell" not in a
    assert a["strongest_comparator"] in ("host", "valid_cert")


def test_v1_regression_blocks_keep():
    a = sb.analyse(
        _v2_cells(),
        cand_null="economic",
        comp_meta=V2META,
        cx=2,
        suite="v2",
        extra_reasons=["worse than host on a v1 cell it ran on: x"],
    )
    assert a["decision"] == "DISCARD"
    assert any("v1 cell" in r for r in a["discard_reasons"])


# ------------------------------------------------------------------ ledger tagging + scope
def test_records_carry_suite_v2_and_amendment_a1(tmp_path):
    cand = {
        "candidate_id": "CAND-x",
        "family": "f",
        "variant": "v",
        "host": "drift2act",
        "hook": "h",
        "target_null": "cond",
    }
    rec = v2._crash_record(cand, "boom", 0.1)
    assert rec["suite"] == "v2" and rec["amendment"] == "A1" and rec["run_id"].startswith("B2-")
    assert rec["data_hashes"]["dev_suite_v2_sha256"] == v2.SUITE_V2_SHA256
    p = tmp_path / "l.jsonl"
    out = v2.commit(rec, p)
    assert out["suite"] == "v2" and lg.verify(p).n_records == 1


def test_preflight_duplicate_check_is_per_suite(tmp_path):
    from shiftlab.autoresearch.preflight import preflight

    cand = next(
        c for c in sb.load_batch() if c["research_question"] == "Q2" and resolve(c)[0] is not None
    )
    p = tmp_path / "l.jsonl"
    rec = v2._crash_record(cand, "x", 0.0, "INVALID", invalid_reason="t")
    rec["decision"] = "DISCARD"
    rec.update(
        uncertainty={"a": 1},
        baseline_relative={"a": 1},
        results={"a": 1},
        preregistered_predictions={"a": 1},
    )
    lg.append(rec, p)
    assert preflight(cand, ledger_path=p).status != "DUPLICATE"  # v1 view ignores v2 records
    assert preflight(cand, ledger_path=p, suite="v2").status == "DUPLICATE"


def test_scope_is_within_cap_excludes_q1_and_names_a_reason():
    sc = v2.select_scope()
    assert 0 < sc["n_selected"] <= 140
    for e in sc["selected"]:
        assert e["research_question"] == "Q2" and e["reasons"]
        assert set(e["scope"]) <= {"i", "ii"}
    assert sc["excluded"]["scope_iii_q1_evidence_identities"]["n"] > 0


# ------------------------------------------------------------------ v1 golden
def _v1_record(cid):
    for r in lg.read_all():
        if (
            r["candidate_id"] == cid
            and r.get("suite", "v1") == "v1"
            and r["stage"] == "B"
            and r["decision"] in ("DISCARD", "KEEP")
        ):
            return r
    return None


def test_v1_golden_record_is_reproduced_bit_identically(tmp_path):
    """Re-run a suite-v1 identity with the modified code and compare with its ledger record (native_v0 host, v1 analyse
    path): decision, behaviour hash, per-cell dJ vs host / strongest, components."""
    cand = next(
        c
        for c in sb.load_batch()
        if c["family"] == "replacement_economic_thresholds"
        and c["variant"] == "label_cost_aware_ose"
        and c["host"] == "contract_native"
    )
    old = _v1_record(cand["candidate_id"])
    assert old is not None
    impl, _ = resolve(cand)
    new = sb.run_experiment(cand, impl, tmp_path / "cache")
    assert new["decision"] == old["decision"]
    assert new["behaviour_sha256"] == old["behaviour_sha256"]
    assert new["uncertainty"] == old["uncertainty"]
    assert new["results"]["components_per_cell"] == old["results"]["components_per_cell"]
    assert new["results"]["strongest_comparator"] == old["results"]["strongest_comparator"]
    assert "suite" not in new and "amendment" not in new


# ------------------------------------------------------------------ A1 scope (iii): Q1 evidence identities
def test_scope_iii_cells_comparators_and_resolver():
    from shiftlab.autoresearch import stage_b_q1 as q1

    cells = q1.q1_cells()
    assert [c["id"] for c in cells[:4]] == ["Q1_0", "Q1_1", "Q1_2", "Q1_3"]
    assert [c["suite"] for c in cells[:4]] == ["v1"] * 4
    assert q1.seeds_of(cells[0]) == sb.cell_seeds(0)  # v1 seed rule on the v1 Q1 row
    v2c = cells[4:]
    assert len(v2c) == 12 and all(c["label_cap"] < c["T"] for c in v2c)
    assert {c["id"] for c in v2c}.isdisjoint(
        {"S2a", "S2b", "S2c"}
    )  # cap == T: degenerate gap schedule
    assert set(q1.Q1_COMPARATORS) == {
        "markov_lr_gate",
        "thinned_hedged_gate",
        "gapmix_exact08_s4",
        "rmm_detector",
    }
    sc = q1.select_scope()
    assert sc["n_selected"] == 42
    for e in sc["selected"]:
        cand = next(c for c in sb.load_batch() if c["candidate_id"] == e["candidate_id"])
        impl, why = q1.resolve_q1(cand)
        assert impl is not None, why


def test_scope_iii_records_are_tagged(tmp_path):
    from shiftlab.autoresearch import stage_b_q1 as q1

    cand = {
        "candidate_id": "CAND-q",
        "family": "f",
        "variant": "v",
        "host": "drift2act",
        "hook": "h",
        "target_null": "marg",
    }
    rec = q1._crash_record(cand, "boom", 0.1)
    assert (rec["suite"], rec["amendment"], rec["scope"]) == ("v2", "A1", "iii")
    assert rec["run_id"].startswith("B2Q1-")
    assert v2.commit(rec, tmp_path / "l.jsonl")["scope"] == "iii"
