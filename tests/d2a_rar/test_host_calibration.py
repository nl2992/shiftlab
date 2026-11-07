"""WP6 host-port calibration: native_v0 bit-identical to cc867f40, calibrated_v1 valid and paced, DEV_SUITE_v2 cells pass the
contract guards and actually reach the hooks they were built for (host-only, no candidate). CPU-sized (< 60 s)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from shiftlab.autoresearch import host_audit as ha
from shiftlab.autoresearch import stage_b as sb
from shiftlab.bench.contract import Simulator, make_stream
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_rar import BinaryPolicy, PacedLabelPolicy, RARPolicy

# Golden values recorded at cc867f40 (before the profile switch) on Q1[0] / Q1[2], first seed, intervention_dear.
GOLDEN = {
    "0:binary": (536.5, {"N_a": 0, "N_b": 0, "N_h": 0, "N_q": 50, "N_r": 0, "N_s": 0}),
    "0:cab": (536.5, {"N_a": 0, "N_b": 0, "N_h": 0, "N_q": 50, "N_r": 0, "N_s": 0}),
    "0:d2a": (952.5, {"N_a": 0, "N_b": 2, "N_h": 1000, "N_q": 50, "N_r": 2, "N_s": 0}),
    "0:rar": (537.0, {"N_a": 1, "N_b": 0, "N_h": 0, "N_q": 50, "N_r": 0, "N_s": 0}),
    "2:binary": (662.5, {"N_a": 0, "N_b": 0, "N_h": 0, "N_q": 50, "N_r": 0, "N_s": 0}),
    "2:cab": (662.5, {"N_a": 0, "N_b": 0, "N_h": 0, "N_q": 50, "N_r": 0, "N_s": 0}),
    "2:d2a": (952.5, {"N_a": 0, "N_b": 2, "N_h": 1000, "N_q": 50, "N_r": 2, "N_s": 0}),
    "2:rar": (662.5, {"N_a": 0, "N_b": 0, "N_h": 0, "N_q": 50, "N_r": 0, "N_s": 0}),
}
MK = {
    "d2a": lambda: Drift2ActContractPolicy(),
    "rar": lambda: RARPolicy(),
    "cab": lambda: BinaryPolicy(cost_aware=True),
    "binary": lambda: BinaryPolicy(cost_aware=False),
}


def _frozen(ci):
    cell = sb.suite_cells("Q1")[ci]
    spec = sb.load_family(cell["family"])
    return spec, sb.make_env(spec, "intervention_dear", "default"), sb.cell_seeds(ci)[0]


@pytest.mark.parametrize("key", sorted(GOLDEN))
def test_native_v0_default_is_bit_identical_to_cc867f40(key):
    ci, name = key.split(":")
    spec, env, seed = _frozen(int(ci))
    p = MK[name]()
    p.reset(env)
    res = Simulator(make_stream(spec, seed), env).run(p)
    J, counts = GOLDEN[key]
    assert round(res.J, 9) == J and res.counts == counts
    assert getattr(p, "profile", "native_v0") == "native_v0"


def test_calibrated_profile_valid_and_paced_on_frozen_cell():
    spec, env, seed = _frozen(2)  # markov05_shift_d10, cap 50
    out = ha.run_cell(
        spec, env, [seed, seed + 1], ("d2a_cal", "rar_cal", "cab_cal", "bin_cal"), probe=True
    )  # verify_run inside
    T = spec.T
    for m, recs in out.items():
        for r in recs:
            assert r["counts"]["N_q"] <= 50
    # the cap is spread over the horizon (native_v0 exhausted it at t=200 / t=50): last query is late
    for m in ("rar_cal", "cab_cal", "d2a_cal"):
        r = out[m][0]
        assert r["counts"]["N_q"] >= 40, m
        assert r["reach"]["n_query_rounds"] >= 40
    d = out["d2a_cal"][0]["reach"]
    assert d["cert_evaluations"] > 0
    # the pacing rule k_low/audit_every <= B/T: audit cadence is ceil(T/B)=20
    p = Drift2ActContractPolicy(profile="calibrated_v1")
    p.reset(env)
    assert p.audit_every == 20 and p.N == round(1024 * T / 1500)
    assert (p.cd_rt, p.cd_rb) == (round(800 * T / 1500), round(400 * T / 1500))
    assert PacedLabelPolicy(1000, 50).every == 20


def test_probe_does_not_change_behaviour():
    spec, env, seed = _frozen(2)
    a = ha.run_cell(spec, env, [seed], ("d2a_cal", "rar_v0", "uniform_query"), probe=False)
    b = ha.run_cell(spec, env, [seed], ("d2a_cal", "rar_v0", "uniform_query"), probe=True)
    for m in a:
        assert a[m][0]["J"] == b[m][0]["J"] and a[m][0]["counts"] == b[m][0]["counts"]


def test_suite_v2_files_are_deterministic_and_frozen_files_untouched():
    assert json.loads(ha.SUITE_V2_PATH.read_text(encoding="utf8")) == json.loads(
        json.dumps(ha.build_suite_v2())
    )
    assert ha.FAMILIES_V2_PATH.read_text(encoding="utf8") == ha.families_v2_yaml()
    suite = ha.load_suite_v2()
    import hashlib

    assert (
        suite["parent"]["sha256"]
        == hashlib.sha256(
            (ha.REPO_ROOT / "docs/d2a_rar/registry/DEV_SUITE.json").read_bytes()
        ).hexdigest()
    )
    ids = [c["id"] for c in suite["cells"]]
    assert len(ids) == len(set(ids)) == 15
    for scen in {c["scenario"] for c in suite["cells"]}:
        roles = {c["role"] for c in suite["cells"] if c["scenario"] == scen}
        assert {"alternative", "correct_null", "neighbouring_negative_control"} <= roles
    # correct-null cells have the cond and marg nulls TRUE; alternatives have them false
    for c in suite["cells"]:
        if c["role"] == "correct_null":
            assert c["null_truth_expected"]["cond"] and c["null_truth_expected"]["marg"]
        if c["role"] == "alternative":
            assert not c["null_truth_expected"]["marg"]


def test_v2_cells_pass_contract_guards_with_hosts_and_controls():
    # run_paired(verify=True, on_violation='raise') inside run_cell: leak / budget / audit guards on every run
    suite = ha.load_suite_v2()
    for c in suite["cells"]:
        spec = ha.load_family_v2(c["family"], c["family_source"])
        env = ha.make_env(
            spec, c["cost_vector"], c["label_cap"], c["max_lookback"], c["retrain_duration"]
        )
        seeds = [ha.SEED_START_V2 + c["index"] * 1000]
        out = ha.run_cell(
            spec, env, seeds, ("uniform_query", "d2a_cal", "rar_cal", "cab_cal"), probe=False
        )
        for m, recs in out.items():
            assert recs[0]["counts"]["N_q"] <= c["label_cap"], (c["id"], m)


def test_semi_markov_regime_process_alternates_and_v1_path_is_untouched():
    spec = ha.load_family_v2("hazard_shift_k25")
    st = make_stream(spec, 123)
    reg = st.truth.regime
    assert set(np.unique(reg)) <= {0, 1}
    assert int((np.diff(reg.astype(int)) != 0).sum()) >= 2
    assert make_stream(spec, 123).fingerprint == st.fingerprint
    v1 = sb.load_family("iid_shift_d10")
    assert v1.regime_process == "single" and set(np.unique(make_stream(v1, 5).truth.regime)) == {
        0,
        1,
        2,
    }


def _reach(cell_id, methods, nseed=3):
    suite = ha.load_suite_v2()
    c = next(c for c in suite["cells"] if c["id"] == cell_id)
    spec = ha.load_family_v2(c["family"], c["family_source"])
    env = ha.make_env(
        spec, c["cost_vector"], c["label_cap"], c["max_lookback"], c["retrain_duration"]
    )
    seeds = [ha.SEED_START_V2 + c["index"] * 1000 + r for r in range(nseed)]
    return ha.run_cell(spec, env, seeds, methods, probe=True)


def test_hook_reach_tight_deadline_feasibility_binds():
    tight = _reach("S1a", ("d2a_cal", "uniform_query"))
    short = _reach("S1c", ("d2a_cal", "uniform_query"))
    # tight-deadline cell: requests are issued while the observed delay law has mass beyond the remaining horizon
    assert sum(r["reach"]["q_rounds_p_within_lt_1"] for r in tight["uniform_query"]) > 0
    assert sum(r["reach"]["labels_released_after_T"] for r in tight["uniform_query"]) > 0
    # neighbouring control (short tail): strictly less binding
    assert sum(r["reach"]["labels_released_after_T"] for r in short["uniform_query"]) < sum(
        r["reach"]["labels_released_after_T"] for r in tight["uniform_query"]
    )


def test_hook_reach_rar_gate2_reachable_with_label_rich_cap_and_not_at_cap50():
    rich = _reach("S2a", ("rar_cal",))
    assert sum(r["reach"]["gate_evaluations"] for r in rich["rar_cal"]) > 0
    assert sum(r["reach"]["gate2_passes"] for r in rich["rar_cal"]) > 0
    spec, env, seed = _frozen(2)
    poor = ha.run_cell(spec, env, [seed], ("rar_v0", "rar_cal"), probe=True)
    assert all(r["reach"]["gate2_passes"] == 0 for m in poor for r in poor[m])


def test_hook_reach_certificate_opens_with_cap_300():
    out = _reach("S2d", ("d2a_cal",))
    assert sum(r["reach"]["gate_open_rounds"] for r in out["d2a_cal"]) > 0


def test_hook_reach_reversal_and_hazard():
    rev = _reach("S3a", ("uniform_query",))
    assert any(r["reach"]["promoted_then_regime_left"] for r in rev["uniform_query"])
    assert (
        sum(r["reach"]["candidate_rounds_when_candidate_worse"] for r in rev["uniform_query"]) > 0
    )
    haz = _reach("S4a", ("uniform_query",))
    assert all(r["reach"]["regime_switches"] >= 2 for r in haz["uniform_query"])
    assert any(r["reach"]["promoted_then_regime_left"] for r in haz["uniform_query"])
