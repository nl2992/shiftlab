"""Tests for the WP5 candidate grammar, registry, experiment ledger and Stage-A preflight."""

from __future__ import annotations

import copy
import gzip
import json
from collections import Counter

import pytest

from shiftlab.autoresearch import grammar as g
from shiftlab.autoresearch import ledger as lg
from shiftlab.autoresearch import preflight as pf
from shiftlab.autoresearch.dev_suite import DEV_SUITE, cells_for, missing_references

OK = lambda *_a: None


@pytest.fixture(scope="module")
def reg():
    return g.build_registry()


@pytest.fixture(scope="module")
def ids(reg):
    return reg["identities"]


@pytest.fixture(scope="module")
def batch(ids):
    return g.select_batch(ids)


def _find(ids, **kw):
    for c in ids:
        if all(c.get(k) == v for k, v in kw.items()):
            return c
    raise AssertionError(f"no identity with {kw}")


def _ident(family, variant, host, q, null, cfg=None, **kw):
    fam = g.family_by_key(family)
    var = g.variant_of(fam, variant)
    cfg = cfg if cfg is not None else {k: g.KNOBS[k][0] for k in var.knobs}
    return g.make_identity(fam, var, host, q, null, cfg, **kw)


# ------------------------------------------------------------------ registry
def test_registry_build_is_deterministic(reg):
    again = g.build_registry()
    dump = lambda r: json.dumps(r["identities"], sort_keys=True)
    assert dump(reg) == dump(again)
    assert g.sha(reg["stats"]) == g.sha(again["stats"])


def test_cap_and_uniqueness(ids):
    assert 500 < len(ids) <= g.MAX_IDENTITIES
    assert len({c["candidate_id"] for c in ids}) == len(ids)


def test_every_identity_has_mandated_fields_and_validates(ids):
    for c in ids:
        for f in g.REQUIRED_FIELDS:
            assert f in c, (c["candidate_id"], f)
        assert g.validate_identity(c) == [], (c["candidate_id"], g.validate_identity(c))
        assert c["closest_prior_art"] and c["required_baselines"] and c["falsification_test"]
        assert c["target_null"] in g.NULLS and c["host"] in g.HOSTS


def test_all_24_phase5_families_present_and_ledger_ids_exist():
    fams = g.families()
    assert len(fams) >= 24
    led, papers = g.load_failure_ledger(), g.load_prior_art()["papers"]
    for f in fams:
        assert all(i in led for i in f.failure_links), f.key
        assert all(p in papers for p in f.closest), f.key
        for v in f.variants:
            assert all(i in led for i in v.repeats)
            assert v.hooks and all(h in g.HOOKS for h in v.hooks.values())


def test_baseline_vocabulary_resolves_in_null_registry():
    entries = g.load_null_entries()
    for b, eid in g.BASELINE_NULL_ENTRY.items():
        assert eid is None or eid in entries, b


def test_host_compat_rules_hold_and_violations_are_caught(ids):
    for c in ids:
        if c["hook"] == g.R_G2:
            assert c["host"] == "rar"
        if c["hook"] == g.R_G3:
            assert c["host"] in ("rar", "cost_aware_binary")
        if c["hook"] == g.D_RS:
            assert c["host"] == "drift2act"
        if (
            c["family"] in ("hazard_regime_duration", "actual_gap_evidence")
            and c["research_question"] == "Q1"
        ):
            assert c["target_null"] in ("cond", "marg")
    gate2 = _find(ids, hook=g.R_G2)
    bad = copy.deepcopy(gate2)
    bad["host"] = "drift2act"
    assert any(
        "hook_host_mismatch" in e or "gate2_only_on_rar" in e for e in g.validate_identity(bad)
    )
    gap = _find(ids, variant="exact_Pg_kernel", host="drift2act")
    bad = copy.deepcopy(gap)
    bad["target_null"] = bad["scoring_null"] = "economic"
    assert "gap_aware_requires_cond_or_marg" in g.validate_identity(bad)
    bad = copy.deepcopy(gap)
    bad["scoring_null"] = "marg" if gap["target_null"] == "cond" else "cond"
    assert "scoring_null_differs_from_target_null" in g.validate_identity(bad)
    rs = _find(ids, hook=g.D_RS)
    bad = copy.deepcopy(rs)
    bad["host"] = "rar"
    assert g.validate_identity(bad)


def test_required_baselines_by_question_and_rar_gate_rule(ids):
    q2 = _find(ids, family="voi_acquisition", host="drift2act")
    assert set(g.Q2_BASELINES) <= set(q2["required_baselines"])
    for need in ("uniform_query", "pending_cap", "fixed_schedule", "drift2act_native_audit", "asi_inspired",
                 "gong_zhang_paid_obs", "pave"):  # fmt: skip
        assert need in q2["required_baselines"]
    for c in ids:
        if c["family"] == "cost_aware_rar_gate":
            assert {"rar_unmodified", "rar_cost_aware_binary"} <= set(c["required_baselines"])
        if c["research_question"] == "Q1":
            assert set(g.Q1_BASELINES) <= set(c["required_baselines"])


def test_high_overlap_families_are_not_novelty_bearing(ids):
    for c in ids:
        if c["prior_art_status"] in ("HIGH_OVERLAP", "KNOWN"):
            assert c["novelty_bearing"] is False
            assert c["role"] in ("baseline_or_ablation_only", "narrow_residue_test")
        if c["prior_art_family"] in ("F1", "F2", "F3", "F8", "F10"):
            assert c["prior_art_status"] == "HIGH_OVERLAP"
            assert c["role"] == "baseline_or_ablation_only" and c["novelty_bearing"] is False
    # the plausibly-distinct families exist and are the only novelty-bearing ones
    nb = {(c["prior_art_family"], c["family"]) for c in ids if c["novelty_bearing"]}
    assert {f for f, _ in nb} <= {"F5", "F6", "F7", "F9"} and {"F5", "F7", "F9"} <= {
        f for f, _ in nb
    }
    assert all(c["variant"].startswith(("gate2", "gate3_recovery")) for c in ids
               if c["novelty_bearing"] and c["prior_art_family"] == "F6")  # fmt: skip


def test_dedup_collapses_alias_and_inert_knob_duplicates():
    a = _ident("pending_aware_budgets", "release_feasible_requests", "rar", "Q2", "economic")
    b = _ident("deadline_aware_querying", "deadline_feasibility_filter", "rar", "Q2", "economic")
    assert a["candidate_id"] == b["candidate_id"] and a["variant"] != b["variant"]
    kept, st = g.dedup([a, b, copy.deepcopy(a)])
    assert len(kept) == 1 and kept[0]["duplicates_collapsed"] == 2
    assert kept[0]["variant"] == "release_feasible_requests"  # canonical spelling is primary
    assert kept[0]["aliases"] == ["deadline_aware_querying.deadline_feasibility_filter"]
    assert st["reasons"]["alias"] >= 1
    # inert knob: on Drift2Act, request_size cannot choose indices, so propensity_score is inert
    cfgs = [{"propensity_score": s, "min_propensity": 0.05} for s in g.KNOBS["propensity_score"]]
    ds = [_ident("adaptive_query_propensities", "certificate_gap_propensity", "drift2act", "Q2",
                 "economic", c) for c in cfgs]  # fmt: skip
    assert len({x["candidate_id"] for x in ds}) == 1
    # ... but not on a host with per-item propensities
    cs = [_ident("adaptive_query_propensities", "certificate_gap_propensity", "contract_native", "Q2",
                 "economic", c) for c in cfgs]  # fmt: skip
    assert len({x["candidate_id"] for x in cs}) == 3
    kept, st = g.dedup(ds)
    assert len(kept) == 1 and st["reasons"] == {"inert_knob": 2}


def test_dedup_stats_are_recorded(reg, ids):
    s = reg["stats"]
    assert s["after_dedup"] == len(ids) < s["raw_before_dedup"]
    assert s["duplicates_collapsed"] == s["raw_before_dedup"] - s["after_dedup"] > 0
    assert sum(c["duplicates_collapsed"] for c in ids) == s["duplicates_collapsed"]


def test_blocked_by_matches_do_not_repeat_and_unblocks_with_new_hypothesis(ids):
    c = _find(ids, variant="full_sup_denominator")
    assert [b["ledger_id"] for b in c["blocked_by"]] == ["FL-016"]
    assert "SUI" in c["blocked_by"][0]["requirement"]
    d = _ident("actual_gap_evidence", "full_sup_denominator", c["host"], "Q1", c["target_null"], c["configuration"],
               new_hypothesis="Why this differs from FL-016: <declared mechanism>.")  # fmt: skip
    assert d["blocked_by"] == [] and d["candidate_id"] != c["candidate_id"]
    blocked_variants = {c["variant"] for c in ids if c["blocked_by"]}
    assert {"full_sup_denominator", "rho_robust_gapmix", "freshcheck_reset", "split_clock_burst",
            "deadline_aligned_heuristic", "triggered_kelly_onset", "joint_dp_planner", "pave_delay_gate",
            "stratified_evidence_composition"} <= blocked_variants  # fmt: skip


def test_q3_is_generated_but_blocked_and_never_batched(ids, batch):
    q3 = [c for c in ids if c["research_question"] == "Q3"]
    assert len(q3) > 50
    assert all(c["blocked_until"] == g.Q3_BLOCK for c in q3)
    assert any(c["family"] == "q3_factorial_stack" and len(c["parent_ids"]) == 2 for c in q3)
    assert not any(c["research_question"] == "Q3" for c in batch)


def test_stage_b_batch_is_200_diverse_and_deterministic(ids, batch):
    assert len(batch) == g.BATCH_SIZE == len({c["candidate_id"] for c in batch})
    assert [c["candidate_id"] for c in batch] == [c["candidate_id"] for c in g.select_batch(ids)]
    assert not any(c["blocked_by"] or c["blocked_until"] for c in batch)
    qn = Counter(c["research_question"] for c in batch)
    assert qn["Q1"] >= g.BATCH_CAPS["q1_min"] and qn["Q2"] > 100
    fam_n = Counter(c["family"] for c in batch)
    assert max(fam_n.values()) <= 14
    unblocked_fams = {c["family"] for c in ids if not c["blocked_by"] and not c["blocked_until"]}
    assert set(fam_n) == unblocked_fams
    assert Counter(c["host"] for c in batch).most_common(1)[0][1] <= g.BATCH_CAPS["per_host"]
    assert (
        Counter(c["role"] for c in batch)["baseline_or_ablation_only"]
        <= g.BATCH_CAPS["ablation_only"]
    )


def test_priority_order_follows_prior_art_status(ids):
    mean = lambda st: (
        sum(c["priority_score"] for c in ids if c["prior_art_status"] == st)
        / max(1, sum(c["prior_art_status"] == st for c in ids))
    )
    assert mean("PLAUSIBLY_DISTINCT") > mean("UNVERIFIED") > mean("HIGH_OVERLAP")
    assert abs(sum(g.SCORE_WEIGHTS.values()) - 1.0) < 1e-9


def test_committed_artifacts_match_the_code(ids, batch):
    from pathlib import Path

    root = Path(g.REGISTRY_DIR)
    f = root / "stage_b_batch_001.jsonl"
    if f.exists():
        disk = [json.loads(x)["candidate_id"] for x in f.read_text(encoding="utf-8").splitlines()]
        assert disk == [c["candidate_id"] for c in batch]
    gz = root / "CANDIDATE_REGISTRY.jsonl.gz"
    plain = root / "CANDIDATE_REGISTRY.jsonl"
    src = (
        gzip.decompress(gz.read_bytes()).decode()
        if gz.exists()
        else plain.read_text(encoding="utf-8")
    )
    if gz.exists() or plain.exists():
        assert [json.loads(x)["candidate_id"] for x in src.splitlines()] == [
            c["candidate_id"] for c in ids
        ]


def test_dev_suite_references_exist_and_validity_plan_respects_nulls():
    assert missing_references() == {"families": [], "cost_vectors": []}
    assert all(len(v) == 4 for v in DEV_SUITE["cells"].values())
    roles = {c["role"] for c in DEV_SUITE["cells"]["Q2"]}
    assert roles == {
        "correct_null",
        "adverse_sampling_stress",
        "alternative",
        "neighbouring_negative_control",
    }
    cond = cells_for("Q1", "cond")
    marg = cells_for("Q1", "marg")
    assert not any("markov08_marg_null_only" in x for x in cond["validity_cells"])
    assert any("markov08_marg_null_only" in x for x in cond["out_of_contract_stress"])
    assert any("markov08_marg_null_only" in x for x in marg["validity_cells"])


# ------------------------------------------------------------------ ledger
def _rec(run_id="r1", cid="CAND-x", stage="B", decision="DISCARD", **kw):
    r = {
        "candidate_id": cid, "run_id": run_id, "stage": stage, "git_commit": "abc", "method": "m", "host": "contract_native",
        "fidelity_tier": "COMMON_CONTRACT_PORT", "data_hashes": {"cost_vectors": "764b"},
        "seed_group": {"block": "d2a_rar_dev", "seed_start": 110000000, "seed_end": 110000019, "exposure": "dev"},
        "hardware": {"cpu": "x"}, "runtime_s": 12.5, "null_class": "cond", "assumptions": ["a"],
        "preregistered_predictions": ["J improves >= 3% on alternative"], "results": {"J": 1.0},
        "uncertainty": {"J": [0.9, 1.1]}, "baseline_relative": {"pending_cap": {"dJ": -0.02, "ci": [-0.05, 0.01]}},
        "counterexamples": [], "prior_art_status": "PLAUSIBLY_DISTINCT", "decision": decision,
    }  # fmt: skip
    r.update(kw)
    return r


def test_ledger_append_verify_and_no_rewrite(tmp_path):
    p = tmp_path / "L.jsonl"
    assert lg.verify(p).n_records == 0
    r1 = lg.append(_rec("r1"), p)
    before = p.read_bytes()
    r2 = lg.append(_rec("r2", cid="CAND-y"), p)
    assert p.read_bytes().startswith(before)  # existing bytes untouched
    assert r1["prev_sha256"] == lg.GENESIS and r2["prev_sha256"] == r1["record_sha256"]
    v = lg.verify(p)
    assert v.n_records == 2 and v.head == r2["record_sha256"] == lg.head(p)
    with pytest.raises(lg.DuplicateRun):
        lg.append(_rec("r1"), p)
    with pytest.raises(lg.InvalidRecord):
        lg.append(_rec("r9", prev_sha256="forged"), p)
    assert lg.verify(p, expected_head=v.head).n_records == 2


def test_ledger_detects_tampering(tmp_path):
    p = tmp_path / "L.jsonl"
    for i in range(3):
        lg.append(_rec(f"r{i}", cid=f"CAND-{i}"), p)
    good = p.read_text(encoding="utf-8").splitlines()

    def write(lines):
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    write([good[0].replace('"J":1.0', '"J":9.9'), *good[1:]])  # edit first line
    with pytest.raises(lg.LedgerTampered):
        lg.verify(p)
    write([good[0], good[2]])  # delete a middle record
    with pytest.raises(lg.LedgerTampered):
        lg.verify(p)
    write([good[0], good[2], good[1]])  # reorder
    with pytest.raises(lg.LedgerTampered):
        lg.verify(p)
    write([*good[:2], good[2].replace("DISCARD", "KEEP")])  # edit the last line
    with pytest.raises(lg.LedgerTampered):
        lg.verify(p)
    with pytest.raises(lg.LedgerTampered):
        lg.append(_rec("r7"), p)  # refuses to extend a tampered ledger
    write(good[:2])  # truncation: only a pinned head catches it
    head3 = json.loads(good[2])["record_sha256"]
    assert lg.verify(p).n_records == 2
    with pytest.raises(lg.LedgerTampered):
        lg.verify(p, expected_head=head3)


def test_ledger_schema_enforcement(tmp_path):
    p = tmp_path / "L.jsonl"
    with pytest.raises(lg.InvalidRecord):
        lg.append({k: v for k, v in _rec().items() if k != "git_commit"}, p)
    with pytest.raises(lg.InvalidRecord):
        lg.append(_rec(decision="MAYBE"), p)
    with pytest.raises(lg.InvalidRecord):
        lg.append(_rec(preregistered_predictions=[]), p)  # stage B needs preregistered predictions
    with pytest.raises(lg.InvalidRecord):
        lg.append(_rec(decision="CRASH"), p)  # CRASH needs error
    lg.append(
        _rec(
            "c1", decision="CRASH", error="timeout 300s", results={}, preregistered_predictions=[]
        ),
        p,
    )
    for d in ("INVALID", "DUPLICATE", "UNVERIFIED"):
        extra = {
            "INVALID": {"invalid_reason": "x"},
            "DUPLICATE": {"duplicate_of": "CAND-0"},
            "UNVERIFIED": {},
        }[d]
        lg.append(_rec(f"d-{d}", decision=d, **extra), p)
    assert {r["decision"] for r in lg.read_all(p)} == {
        "CRASH",
        "INVALID",
        "DUPLICATE",
        "UNVERIFIED",
    }


def test_confirmation_seed_block_is_refused_unless_stage_d(tmp_path):
    lo, hi = lg.confirmation_range()
    assert (lo, hi) == (120000000, 120099999)
    p = tmp_path / "L.jsonl"
    conf = {
        "block": lg.CONFIRMATION_BLOCK_ID,
        "seed_start": lo,
        "seed_end": lo + 19,
        "exposure": "confirmation",
    }
    for stage in ("A", "B", "C"):
        with pytest.raises(lg.ConfirmationSeedRefused):
            lg.append(_rec("x" + stage, stage=stage, seed_group=conf), p)
    sneaky = {"block": "d2a_rar_dev", "seed_start": lo + 5, "seed_end": lo + 9, "exposure": "dev"}
    with pytest.raises(lg.ConfirmationSeedRefused):
        lg.append(_rec("sneaky", seed_group=sneaky), p)  # block label cannot hide the range
    with pytest.raises(lg.ConfirmationSeedRefused):
        lg.append(
            _rec(
                "lab",
                seed_group={**sneaky, "seed_start": 1, "seed_end": 2, "exposure": "confirmation"},
            ),
            p,
        )
    assert not p.exists() or lg.verify(p).n_records == 0
    lg.append(_rec("d1", stage="D", decision="CONFIRM", seed_group=conf), p)
    with pytest.raises(lg.InvalidRecord):
        lg.append(
            _rec("d2", stage="D", decision="CONFIRM", seed_group=sneaky), p
        )  # range needs honest exposure label


# ------------------------------------------------------------------ preflight
PORTED = {"host_probe": OK, "hook_probe": OK}


def test_preflight_eligible_for_every_unblocked_candidate_with_stubbed_probes(ids, tmp_path):
    ledger = tmp_path / "empty.jsonl"
    statuses = Counter()
    for c in ids:
        if c["blocked_by"] or c["blocked_until"]:
            continue
        v = pf.preflight(c, ledger_path=ledger, **PORTED)
        statuses[v.status] += 1
        assert v.status == pf.ELIGIBLE, (c["candidate_id"], v.reasons)
    assert statuses[pf.ELIGIBLE] > 500


def test_preflight_eligible_records_hashes_and_validity_plan(ids, tmp_path):
    c = _find(ids, family="voi_acquisition", host="contract_native", target_null="economic")
    v = pf.preflight(
        c, ledger_path=tmp_path / "L.jsonl"
    )  # default probes: contract_native is in-repo
    assert v.status == pf.ELIGIBLE, v.reasons
    assert len(v.hashes["config_sha256"]) == 64 and v.hashes["hook_module_sha256"]
    assert v.validity_plan["controls"] and "validity_cells" in v.validity_plan


def test_preflight_null_mismatch_never_scores_cond_on_marginal(ids, tmp_path):
    c = copy.deepcopy(
        _find(ids, variant="exact_Pg_kernel", host="contract_native", target_null="cond")
    )
    c["scoring_null"] = "marg"
    v = pf.preflight(c, ledger_path=tmp_path / "L.jsonl", **PORTED)
    assert v.status in (pf.INVALID, pf.INELIGIBLE_NULL_MISMATCH)
    assert any("scoring_null" in r for r in v.reasons)
    # a cond candidate's marginal-only stress cell is labelled out-of-contract, not a validity cell
    ok = _find(ids, variant="exact_Pg_kernel", host="contract_native", target_null="cond")
    plan = pf.preflight(ok, ledger_path=tmp_path / "L.jsonl", **PORTED).validity_plan
    assert any("markov08_marg_null_only" in x for x in plan["out_of_contract_stress"])
    # no comparator sharing the claimed null -> not validity-comparable
    c2 = copy.deepcopy(ok)
    c2["required_baselines"] = ["markov_lr", "page_cusum", "uniform_query"]  # marg / none / none
    probs, comp = pf.null_check(c2)
    assert comp and any("no required baseline shares" in p for p in probs)


def test_preflight_blocked_by_is_recomputed_not_trusted(ids, tmp_path):
    c = _find(ids, variant="full_sup_denominator", host="contract_native")
    v = pf.preflight(c, ledger_path=tmp_path / "L.jsonl", **PORTED)
    assert v.status == pf.BLOCKED_BY_LEDGER and "FL-016" in v.reasons[0]
    forged = copy.deepcopy(c)
    forged["blocked_by"] = []  # a record that hides its block is still blocked
    assert (
        pf.preflight(forged, ledger_path=tmp_path / "L.jsonl", **PORTED).status
        == pf.BLOCKED_BY_LEDGER
    )
    d = _ident("actual_gap_evidence", "full_sup_denominator", "contract_native", "Q1", c["target_null"],
               c["configuration"], new_hypothesis="declared new mechanism")  # fmt: skip
    assert pf.preflight(d, ledger_path=tmp_path / "L.jsonl", **PORTED).status == pf.ELIGIBLE


def test_preflight_unported_host_is_blocked_not_invalid(ids, tmp_path):
    c = _find(ids, host="drift2act", hook=g.D_RS)
    v = pf.preflight(
        c,
        ledger_path=tmp_path / "L.jsonl",
        host_probe=lambda h: f"{h} adapter missing",
        hook_probe=OK,
    )
    assert v.status == pf.BLOCKED_HOST_NOT_PORTED != pf.INVALID
    assert "adapter missing" in v.reasons[0]


def test_preflight_missing_hook_and_unexposed_seam(ids, tmp_path):
    c = _find(ids, host="drift2act", hook=g.D_AS)
    v = pf.preflight(c, ledger_path=tmp_path / "L.jsonl", host_probe=OK)  # default hook probe
    assert v.status == pf.BLOCKED_HOOK_MISSING and "not exposed" in v.reasons[0]
    assert (
        pf.default_hook_probe(g.D_RS) is None
    )  # documented protocol exists in the Drift2Act package


def test_preflight_duplicate_against_ledger_and_q3_gate(ids, tmp_path):
    p = tmp_path / "L.jsonl"
    c = _find(ids, family="voi_acquisition", host="contract_native", target_null="economic")
    lg.append(_rec("r1", cid=c["candidate_id"]), p)
    assert pf.preflight(c, ledger_path=p, **PORTED).status == pf.DUPLICATE
    assert (
        pf.preflight(c, stage="C", ledger_path=p, **PORTED).status == pf.ELIGIBLE
    )  # other stage is not a duplicate
    lg.append(
        _rec(
            "r2",
            cid="CAND-crash",
            decision="CRASH",
            error="oom",
            preregistered_predictions=[],
            results={},
        ),
        p,
    )
    crashed = copy.deepcopy(c)
    crashed["candidate_id"] = "CAND-crash"
    assert (
        pf.preflight(crashed, ledger_path=p, **PORTED).status != pf.DUPLICATE
    )  # a crash may be retried
    q3 = _find(ids, research_question="Q3", family="q3_factorial_stack")
    assert pf.preflight(q3, ledger_path=p, **PORTED).status == pf.BLOCKED_UNTIL_WINNERS
    assert pf.preflight(q3, ledger_path=p, winners=q3["parent_ids"], **PORTED).status == pf.ELIGIBLE


def test_preflight_rejects_tampered_identity(ids, tmp_path):
    c = copy.deepcopy(
        _find(ids, family="voi_acquisition", host="contract_native", target_null="economic")
    )
    c["configuration"] = {
        **c["configuration"],
        "shadow_price": "dual" if c["configuration"].get("shadow_price") != "dual" else "off",
    }
    v = pf.preflight(c, ledger_path=tmp_path / "L.jsonl", **PORTED)
    assert v.status == pf.INVALID


def test_named_smoke_references_contract_tests_without_reimplementing():
    cmd = pf.run_named_smoke(dry_run=True)["cmd"]
    assert "tests/d2a_rar/test_contract.py" in cmd and cmd[-2] == "-k"
    from pathlib import Path

    src = (Path(g.REPO_ROOT) / "tests/d2a_rar/test_contract.py").read_text(encoding="utf-8")
    assert all(f"def {n}" in src for n in pf.SMOKE_TESTS)
