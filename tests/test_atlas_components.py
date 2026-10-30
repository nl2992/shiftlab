"""Tests for the typed composition engine (CPU-fast; smoke checks, not confirmatory)."""

from __future__ import annotations

import subprocess
import sys

import numpy as np
import pytest

from shiftlab.dive.atlas_components import (
    DEFAULTS,
    CandidateSpec,
    _Evidence,
    ablation_of,
    build_candidate,
    default_spec,
    differing_slots,
    propose_candidates,
    validate_spec,
    weighted_start_design,
    wide_stakes_gate,
)
from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess
from shiftlab.dive.switching_explore import (
    Config,
    Stream,
    make_bernoulli_stream,
    run,
)

AXES = ("d", "budget_frac", "s", "effect", "duration", "onset", "unknown_axis")
T, B, D = 200, 40, 5


def _cfg(seed: int = 0) -> Config:
    return Config(T=T, B=B, d=D, c=0.01, s=0.1, h=0.1, alpha=0.1, seed=seed)


def _all_proposals():
    out = [default_spec()]
    for ax in AXES:
        out += propose_candidates(ax)
    return out


def test_every_proposal_validates_or_is_rejected_with_reasons():
    n_valid = 0
    for sp in _all_proposals():
        ok, why = validate_spec(sp)
        assert ok or why, sp
        n_valid += ok
        assert sp.hypothesis
    assert n_valid >= 30


def test_proposals_include_ablation_partners_and_are_bounded():
    for ax in AXES:
        props = propose_candidates(ax)
        assert 2 <= len(props) <= 40
        assert len({p.spec_id for p in props}) == len(props)
        for p in props:
            if p.focus is not None and not p.hypothesis.startswith("Ablation"):
                partner = ablation_of(p, p.focus)
                assert partner.spec_id in {q.spec_id for q in props}
    assert len(propose_candidates("d", max_n=3)) == 3


def test_ablation_differs_in_exactly_one_slot_and_validates():
    for sp in _all_proposals():
        if sp.focus is None or sp.hypothesis.startswith("Ablation"):
            continue
        ab = ablation_of(sp, sp.focus)
        assert ab.spec_id != sp.spec_id
        assert differing_slots(ab, sp) == (sp.focus,)
        assert getattr(ab, sp.focus) == DEFAULTS[sp.focus]
        if validate_spec(sp)[0]:
            ok, why = validate_spec(ab)
            assert ok, why
    with pytest.raises(ValueError):
        ablation_of(CandidateSpec(*DEFAULTS.values(), hypothesis="x"), "memory")


def test_invalid_combinations_are_rejected_not_repaired():
    base = {
        "acquisition": "uniform",
        "evidence": "started_mixture_eprocess",
        "memory": "none",
        "decision": "certificate_econ",
        "hypothesis": "h",
    }
    # restart needs a rollback-capable decision
    ok, why = validate_spec(CandidateSpec(**{**base, "memory": "restart_on_rollback"}))
    assert not ok and any("restart_on_rollback" in w for w in why)
    # discounting the evidence itself voids e-process validity
    sp = CandidateSpec(**{**base, "memory": "discount"}, params={"memory.scope": "evidence"})
    ok, why = validate_spec(sp)
    assert not ok and any("supermartingale" in w for w in why)
    assert not sp.is_safety_gated
    # discount on non-evidence stats is fine and stays gated
    sp = CandidateSpec(**{**base, "memory": "discount"})
    assert validate_spec(sp)[0] and sp.is_safety_gated
    # window_mean is never gated
    assert not CandidateSpec(**{**base, "evidence": "window_mean"}).is_safety_gated
    # unknown component, out-of-range and foreign params, missing hypothesis, pending cap > 2
    assert not validate_spec(CandidateSpec(**{**base, "acquisition": "nope"}))[0]
    assert not validate_spec(CandidateSpec(**base, params={"decision.econ_mult": 99}))[0]
    assert not validate_spec(CandidateSpec(**base, params={"decision.kappa": 2.0}))[0]
    assert not validate_spec(CandidateSpec(**{**base, "hypothesis": ""}))[0]
    st = {**base, "acquisition": "straddle"}
    assert not validate_spec(CandidateSpec(**st, params={"acquisition.pending_cap": 3}))[0]
    with pytest.raises(ValueError):
        build_candidate(CandidateSpec(**{**base, "memory": "restart_on_rollback"}))


def test_spec_id_stable_across_runs_and_param_forms():
    sp = default_spec()
    code = "from shiftlab.dive.atlas_components import default_spec;print(default_spec().spec_id)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == sp.spec_id
    a = CandidateSpec(
        "uniform", "horizon_cusum", "none", "rollback_monitor", {"decision.kappa": 2}, "a"
    )
    b = CandidateSpec(
        "uniform",
        "horizon_cusum",
        "none",
        "rollback_monitor",
        (("decision.kappa", 2.0),),
        "different text",
    )
    assert a.spec_id == b.spec_id
    assert a.spec_id != sp.spec_id


def _stream(seed: int, p=(0.1, 0.9)) -> Stream:
    return make_bernoulli_stream(np.random.default_rng([seed, 1]), T, p, a=0.03, b=0.03)


def test_every_valid_proposal_runs_without_budget_overrun_and_without_peeking():
    t0 = T // 2
    for sp in _all_proposals():
        if not validate_spec(sp)[0]:
            continue
        s1 = _stream(3)
        # flip the paired losses after t0: only reachable through labels released after t0 + d
        l0, l1 = s1.loss0.copy(), s1.loss1.copy()
        l0[t0:], l1[t0:] = s1.loss1[t0:].copy(), s1.loss0[t0:].copy()
        s2 = Stream(l0, l1, s1.truth)
        r1 = run(s1, build_candidate(sp), _cfg())
        r2 = run(s2, build_candidate(sp), _cfg())
        assert r1.queries <= B
        k = t0 + D
        assert np.array_equal(r1.actions[:k], r2.actions[:k]), sp.spec_id
        assert np.array_equal(r1.query_mask[:k], r2.query_mask[:k]), sp.spec_id


def test_safety_gated_candidates_rarely_promote_under_null():
    gated = [s for s in _all_proposals() if validate_spec(s)[0] and s.is_safety_gated]
    assert gated
    seen, picks = set(), []
    for s in gated:  # one spec per (evidence, acquisition, decision) family
        key = (s.evidence, s.acquisition, s.decision)
        if key not in seen:
            seen.add(key)
            picks.append(s)
    rates = {}
    for sp in picks:
        fp = 0
        for seed in range(40):
            st = make_bernoulli_stream(np.random.default_rng([seed, 9]), T, (0.3, 0.3))
            fp += run(st, build_candidate(sp), _cfg(seed)).promotions > 0
        rates[sp.spec_id] = fp / 40
    print("null false-promotion rates (40 seeds):", rates)
    assert max(rates.values()) <= 0.2, rates


def test_gated_candidate_promotes_under_a_strong_effect():
    st = make_bernoulli_stream(np.random.default_rng(5), T, (1.0, 1.0))
    res = run(st, build_candidate(default_spec()), _cfg())
    assert res.promotions >= 1 and res.actions[-1] == 1


# ------------------------------------------------------------------ Amendment 1 evidence components

NEW_EVIDENCE = ("started_kelly", "weighted_starts", "wide_stakes")


def _new_evidence_proposals():
    out = []
    for ax in ("onset", "unknown_axis"):
        out += [p for p in propose_candidates(ax) if p.evidence in NEW_EVIDENCE]
    return out


def test_new_evidence_components_are_proposed_gated_and_ablatable():
    for ax in ("onset", "unknown_axis"):
        props = propose_candidates(ax)
        kinds = {p.evidence for p in props}
        assert set(NEW_EVIDENCE) <= kinds, ax
        acqs = {p.acquisition for p in props if p.evidence in NEW_EVIDENCE}
        decs = {p.decision for p in props if p.evidence in NEW_EVIDENCE}
        assert {"reserve_pacing", "straddle"} <= acqs and {"hysteresis", "certificate_econ"} <= decs
        ids = {p.spec_id for p in props}
        for p in props:
            if p.evidence in NEW_EVIDENCE and not p.hypothesis.startswith("Ablation"):
                assert validate_spec(p)[0] and p.is_safety_gated
                assert p.focus == "evidence"
                assert ablation_of(p, "evidence").spec_id in ids
    # the d / s axes do not get them
    assert not any(p.evidence in NEW_EVIDENCE for p in propose_candidates("d"))


def test_new_evidence_runs_and_does_not_peek():
    t0 = T // 2
    for sp in _new_evidence_proposals():
        s1 = _stream(4)
        l0, l1 = s1.loss0.copy(), s1.loss1.copy()
        l0[t0:], l1[t0:] = s1.loss1[t0:].copy(), s1.loss0[t0:].copy()
        s2 = Stream(l0, l1, s1.truth)
        r1 = run(s1, build_candidate(sp), _cfg())
        r2 = run(s2, build_candidate(sp), _cfg())
        assert r1.queries <= B
        k = t0 + D
        assert np.array_equal(r1.actions[:k], r2.actions[:k]), sp.spec_id
        assert np.array_equal(r1.query_mask[:k], r2.query_mask[:k]), sp.spec_id


def test_new_evidence_promotes_under_a_strong_effect():
    for kind in NEW_EVIDENCE:
        sp = CandidateSpec(
            "uniform", kind, "none", "rollback_monitor", {"decision.kappa": 2.0}, "strong effect"
        )
        st = make_bernoulli_stream(np.random.default_rng(5), T, (1.0, 1.0))
        assert run(st, build_candidate(sp), _cfg()).promotions >= 1, kind


def test_weighted_starts_design_is_predeclared_and_has_floor():
    cfg = Config(T=1000, B=50, d=10)
    for acq in ("uniform", "reserve_pacing", "straddle", "bernoulli_pacing"):
        starts, w = weighted_start_design(acq, cfg)
        w = np.asarray(w)
        assert list(starts) == sorted(set(starts)) and np.all(w > 0) and w.sum() == pytest.approx(1)
        assert w.min() >= 0.2 / len(starts) - 1e-12  # uniform floor of at least 20%
        # mass near each declared level (0.1/0.3/0.6/0.8 T): the label index is about frac * B
        arr = np.asarray(starts)
        for f in (0.1, 0.3, 0.6, 0.8):
            near = np.abs(arr - f * 50 * (990 / 1000 if f > 0.2 else 1.0)) <= 5
            assert w[near].sum() > 0.75 / 4 * 0.9, (acq, f)
    # depends on configuration only, never on data
    assert weighted_start_design("uniform", cfg) == weighted_start_design("uniform", cfg)
    with pytest.raises(ValueError):
        weighted_start_design("uniform", cfg, floor=0.1)


def test_wide_stakes_instance_only_and_below_one():
    g = wide_stakes_gate(1.1, 0.1, 40)
    assert g.stakes.max() == pytest.approx(0.95) and 0.9 in g.stakes
    assert g.log_wealth.shape == (len(g.starts), len(g.stakes))
    assert VectorizedStartedMixtureEProcess.DEFAULT_STAKES.max() == pytest.approx(
        0.8
    )  # class untouched
    other = VectorizedStartedMixtureEProcess(bound=1.1, alpha=0.1, starts=(0,))
    assert other.stakes.max() == pytest.approx(0.8)
    for _ in range(20):
        g.update(-1.1)  # worst case for the bettor: factor 1 - 0.95 > 0
    assert np.isfinite(g.log_e_value)


def test_new_evidence_null_false_promotion_sanity():
    rates = {}
    for kind in NEW_EVIDENCE:
        sp = CandidateSpec(
            "uniform", kind, "none", "rollback_monitor", {"decision.kappa": 2.0}, "null sanity"
        )
        fp = 0
        for seed in range(40):
            st = make_bernoulli_stream(np.random.default_rng([seed, 9]), T, (0.3, 0.3))
            fp += run(st, build_candidate(sp), _cfg(seed)).promotions > 0
        rates[kind] = fp / 40
    print("new-evidence null false-promotion rates (40 seeds):", rates)
    assert max(rates.values()) <= 0.2, rates


def test_new_evidence_boundary_null_validity():
    """Bernoulli stream with E[-D] exactly h (P(D=-1) = (1+h)/2): any-promotion rate <= alpha + 2 SD."""
    h, alpha, n_seeds, T_b = 0.1, 0.1, 300, 300
    q = (1.0 + h) / 2.0
    sd = float(np.sqrt(alpha * (1 - alpha) / n_seeds))
    cfg0 = Config(T=T_b, B=60, d=5, c=0.01, s=0.1, h=h, alpha=alpha)
    rates, direct = {}, {}
    for kind in NEW_EVIDENCE:
        sp = CandidateSpec("uniform", kind, "none", "certificate_econ", {}, "boundary null")
        k_run = k_alarm = 0
        for seed in range(n_seeds):
            cfg = Config(**{**cfg0.__dict__, "seed": seed})
            rng = np.random.default_rng([seed, 31])
            y = (rng.random(T_b) < q).astype(float)  # P(Y=1) = q, D = 1 - 2Y, P(D=-1) = q
            st = Stream(y, 1.0 - y)
            m = build_candidate(sp)
            k_run += run(st, m, cfg).promotions > 0
            ev = _Evidence(kind, cfg, alpha, 3, 0.0, design=weighted_start_design("uniform", cfg))
            ever = False
            for x in 1.0 - 2.0 * y[rng.permutation(T_b)[: cfg.B]]:  # B iid labels, evidence alone
                ev.update(float(x))
                ever = ever or ev.alarm
            k_alarm += ever
        rates[kind], direct[kind] = k_run / n_seeds, k_alarm / n_seeds
    print(f"boundary-null any-promotion rates ({n_seeds} seeds, T={T_b}):", rates)
    print("boundary-null evidence-alarm rates:", direct)
    for kind in NEW_EVIDENCE:
        assert rates[kind] <= alpha + 2 * sd, (kind, rates)
        assert direct[kind] <= alpha + 2 * sd, (kind, direct)
