"""Q1 label-outcome evidence seam: leakage, order, gaps, validity Monte-Carlo, golden host equality, registry sync.

Monte-Carlo size: CPU-small (``D2A_Q1_MC_REPS`` overrides the default 80 paths x 20 labels). The false-alarm bound is
``alpha + 2*sqrt(alpha(1-alpha)/R)``; the claimed-valid processes are conservative, so the check is a regression guard against
an invalid construction (e.g. a wrong denominator), not a tightness proof. Descriptive diagnostics, not confirmatory evidence.
"""

from __future__ import annotations

import gzip
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shiftlab.bench.contract import (
    BudgetSpec,
    ClockSpec,
    DelaySpec,
    EnvSpec,
    LeakError,
    MissingSpec,
    Simulator,
    StreamSpec,
    load_cost_vectors,
    make_stream,
    run_paired,
)
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_evidence import EvidencePromoterPolicy, promoter_adapter
from shiftlab.bench.contract.evidence_q1 import (
    BLOCKED_VARIANTS,
    IMPLEMENTED_VARIANTS,
    BetStart,
    Ctx,
    PluginPred,
    Q1NotImplemented,
    _mixture,
    _per_start,
    build_evidence,
    is_implemented,
    registry_document,
    spec_for,
)
from shiftlab.bench.contract.evidence_seam import (
    OutcomeAugmentedEvidence,
    OutcomeSeam,
)
from shiftlab.bench.contract.policies import BasePolicy
from shiftlab.bench.contract.types import Action
from shiftlab.sota.drift2act.belief import GaussianEvidence  # noqa: F401  (hook protocol sanity)
from shiftlab.sota.inrepo import gapmix

ROOT = Path(__file__).resolve().parents[2]
COSTS = load_cost_vectors()["balanced"]
Q0 = 0.55  # (1 + hurdle 0.1) / 2


def env_of(T=300, cap=30, **kw) -> EnvSpec:
    return EnvSpec(
        T=T,
        costs=COSTS,
        budget=BudgetSpec(label_cap=cap),
        clocks=kw.pop("clocks", ClockSpec(retrain_duration=10, max_lookback=100)),
        **kw,
    )


@pytest.fixture(scope="module")
def registry():
    with gzip.open(ROOT / "docs/d2a_rar/registry/CANDIDATE_REGISTRY.jsonl.gz", "rt") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="module")
def q1_d2a(registry):
    return [r for r in registry if r["research_question"] == "Q1" and r["host"] == "drift2act"]


def _first(q1_d2a, variant, null):
    c = [r for r in q1_d2a if r["variant"] == variant and r["target_null"] == null]
    c.sort(key=lambda r: not r["in_stage_b_batch_001"])
    return c[0]


# ================================================================ golden: default host is untouched
def _golden_module():
    spec = importlib.util.spec_from_file_location(
        "q1_host_golden", ROOT / "tests/d2a_rar/golden/make_q1_host_golden.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_default_host_is_bit_identical_to_pre_seam_golden():
    """Golden produced from the host BEFORE the seam existed (audit-log sha256, J repr, counts; 2 profiles x 2 delay laws)."""
    got = _golden_module().make()
    want = json.loads((ROOT / "tests/d2a_rar/golden/q1_host_golden.json").read_text())
    assert got == want


class NoOpOutcome:
    def bind(self, env):
        pass

    def observe(self, outcomes):
        pass

    def belief_increment(self):
        return 0.0


def test_noop_seam_object_reproduces_the_default_audit_log():
    g = _golden_module()
    env = EnvSpec(T=g.T, costs=COSTS, budget=BudgetSpec(label_cap=60),
                  clocks=ClockSpec(retrain_duration=20, max_lookback=100))  # fmt: skip
    spec = StreamSpec(
        family="q1_golden",
        T=g.T,
        dependence="markov",
        rho=0.5,
        delay=DelaySpec("fixed", d=10),
        tau=0.5,
    )
    from shiftlab.bench.contract.adapters_drift2act import ProxyEvidence

    def build_default():
        p = Drift2ActContractPolicy()
        p.reset(env)
        return p

    def build_seam():
        p = Drift2ActContractPolicy(
            evidence=OutcomeAugmentedEvidence(ProxyEvidence(), NoOpOutcome())
        )
        p.reset(env)
        return p

    pr = run_paired({"d2a": build_default, "seam": build_seam}, spec, env, seeds=g.SEEDS)
    for a, b in zip(pr.runs["d2a"], pr.runs["seam"], strict=True):
        ka = [{k: v for k, v in r.items() if k != "run_id"} for r in a.audit.records]
        kb = [{k: v for k, v in r.items() if k != "run_id"} for r in b.audit.records]
        assert ka == kb and a.J == b.J and a.counts == b.counts


# ================================================================ no leakage through the seam
class _SinkLeak(OutcomeAugmentedEvidence):
    """Evidence that smuggles in an evaluator object and reads it from the sink."""

    def __init__(self, base, outcome, obj, mode):
        super().__init__(base, outcome)
        self._obj, self._mode = obj, mode

    def outcome_sink(self, state):
        try:
            if self._mode == "truth":
                _ = self._obj.gain_marg[state.t - 1]
            elif self._mode == "stream":
                _ = self._obj.loss_inc[state.t - 1]
            elif self._mode == "pending":
                for q in state.Q:
                    _ = q.value
        except LeakError:
            if self._mode != "swallow":
                raise
        super().outcome_sink(state)


class _SwallowSinkLeak(_SinkLeak):
    def outcome_sink(self, state):
        try:
            _ = self._obj.gain_marg[state.t - 1]
        except Exception:  # noqa: BLE001, S110 - the run must still fail
            pass
        OutcomeAugmentedEvidence.outcome_sink(self, state)


def _d2a_host(evidence, env):
    p = Drift2ActContractPolicy(evidence=evidence)
    p.reset(env)
    return p


@pytest.mark.parametrize("mode", ["truth", "stream", "pending", "swallow"])
def test_leaky_evidence_object_trips_the_guards_on_the_drift2act_host(mode):
    from shiftlab.bench.contract.adapters_drift2act import ProxyEvidence

    env = env_of()
    stream = make_stream(StreamSpec(family="t", T=300, delay=DelaySpec("fixed", d=10)), 7)
    obj = stream.truth if mode in ("truth", "swallow") else stream
    cls = _SwallowSinkLeak if mode == "swallow" else _SinkLeak
    ev = cls(ProxyEvidence(), NoOpOutcome(), obj if mode != "pending" else None, mode)
    with pytest.raises(LeakError):
        Simulator(stream, env).run(_d2a_host(ev, env))


class _LeakyObserve:
    """Outcome evidence (promoter shell path) that reads the stream inside observe()."""

    def __init__(self, stream):
        self._s = stream

    def bind(self, env):
        pass

    def declare_selection(self, regime):
        pass

    def observe(self, outcomes):
        _ = self._s.loss_cand[0]

    def alarm(self, alpha=None):
        return False


def test_leaky_evidence_object_trips_the_guards_in_the_promoter_shell():
    env = env_of()
    stream = make_stream(StreamSpec(family="t", T=300, delay=DelaySpec("fixed", d=5)), 8)
    pol = EvidencePromoterPolicy(_LeakyObserve(stream))
    pol.reset(env)
    with pytest.raises(LeakError):
        Simulator(stream, env).run(pol)


def test_clean_evidence_passes_both_hosts_with_no_leak_attempts(q1_d2a):
    from shiftlab.bench.contract.adapters_drift2act import ProxyEvidence

    env = env_of()
    spec = StreamSpec(family="t", T=300, delay=DelaySpec("fixed", d=10))
    ident = _first(q1_d2a, "exact_Pg_kernel", "marg")
    made = {}

    def d2a():
        made["d2a"] = build_evidence(ident, cell_width=0.05)
        return _d2a_host(OutcomeAugmentedEvidence(ProxyEvidence(), made["d2a"]), env)

    pr = run_paired(
        {"d2a": d2a, "shell": lambda: promoter_adapter(ident).build(env)}, spec, env, seeds=(1, 2)
    )
    for r in (*pr.runs["d2a"], *pr.runs["shell"]):
        assert r.leak_attempts == []
    # the seam delivered released outcomes only: n_used cannot exceed released labels
    assert made["d2a"].n_used > 0
    # Drift2Act's own selection is not predictable: flagged, never scored as in-contract
    assert made["d2a"].contract_status()["status"] == "OUT_OF_CONTRACT"


# ================================================================ released order, out-of-order, gaps
class _Feed(BasePolicy):
    name = "feed"

    def __init__(self, rounds):
        self.rounds, self.seam, self.out, self.states = set(rounds), OutcomeSeam(), [], []

    def act(self, state):
        self.out += [(state.t, o) for o in self.seam.feed(state)]
        return Action("query", propensity=1.0) if state.t in self.rounds else Action("continue")


def test_seam_delivers_released_labels_only_once_in_release_order_with_gaps():
    spec = StreamSpec(family="t", T=300, delay=DelaySpec("uniform", lo=1, hi=40))
    env = env_of(cap=40)
    stream = make_stream(spec, 5)
    pol = _Feed(range(3, 123, 3))
    res = Simulator(stream, env).run(pol)
    rel = res.audit.of("release")
    assert len(pol.out) <= len(rel)  # labels released after the last act() are not delivered
    # each outcome delivered at its release round, never earlier (a pending label is invisible)
    for t, o in pol.out:
        assert o.release_round <= t
        assert o.request_round <= o.release_round
    ids = [o.label_id for _, o in pol.out]
    assert len(ids) == len(set(ids))
    # independent recomputation of gap/order from the audit's release order
    run_max, exp = 0, []
    for r in rel[: len(pol.out)]:
        lr = r["label_round"]
        if run_max == 0:
            exp.append((lr, None, "first"))
            run_max = lr
        elif lr > run_max:
            exp.append((lr, lr - run_max, "in_order"))
            run_max = lr
        else:
            exp.append((lr, None, "out_of_order"))
    assert [(o.label_round, o.gap, o.order) for _, o in pol.out] == exp
    assert any(e[2] == "out_of_order" for e in exp), "uniform delays must reorder some labels"
    assert all(o.gap is None or o.gap >= 1 for _, o in pol.out)
    # d is the released paired loss difference loss(cand) - loss(inc) (shadow mode)
    for _, o in pol.out:
        li, lc = dict(o.losses)[0], dict(o.losses)[1]
        assert o.d == lc - li


def test_evidence_drops_out_of_order_outcomes_and_counts_them(q1_d2a):
    spec = StreamSpec(family="t", T=300, delay=DelaySpec("uniform", lo=1, hi=40))
    env = env_of(cap=40)
    stream = make_stream(spec, 5)
    ident = _first(q1_d2a, "exact_Pg_kernel", "cond")
    ev = build_evidence(ident)
    ev.bind(env)
    pol = _Feed(range(3, 123, 3))
    Simulator(stream, env).run(pol)
    outs = [o for _, o in pol.out]
    ev.observe(outs)
    n_ooo = sum(o.order == "out_of_order" for o in outs)
    assert ev.n_dropped_ooo == n_ooo > 0
    assert ev.n_used == len(outs) - n_ooo
    # the used event rounds are strictly increasing and the recorded gaps are their differences
    used = [o for o in outs if o.order != "out_of_order"]
    assert [o.label_round for o in used] == sorted({o.label_round for o in used})
    assert ev.gaps == [b.label_round - a.label_round for a, b in itertools.pairwise(used)]


def test_unidentified_outcomes_are_skipped_not_guessed(q1_d2a):
    spec = StreamSpec(family="t", T=200, delay=DelaySpec("fixed", d=5))
    env = env_of(T=200, cap=20, obs_mode="deployed")
    stream = make_stream(spec, 3)
    pol = _Feed(range(2, 60, 3))
    Simulator(stream, env).run(pol)
    outs = [o for _, o in pol.out]
    assert outs and all(o.d is None and o.order == "unidentified" for o in outs)
    ev = build_evidence(_first(q1_d2a, "exact_Pg_kernel", "cond"))
    ev.bind(env)
    ev.observe(outs)
    assert ev.n_used == 0 and ev.n_unidentified == len(outs) and ev.log_e == 0.0


@pytest.mark.parametrize(
    "schedule,expect",
    [("calendar", {10}), ("cyclic_gaps", {1, 2, 3, 6}), ("bernoulli", None)],
)
def test_promoter_shell_declares_its_schedule_and_computes_gaps(schedule, expect, q1_d2a):
    spec = StreamSpec(
        family="t", T=400, delay=DelaySpec("fixed", d=4), p_before=0.55, p_during=0.55, p_after=0.55
    )
    env = env_of(T=400, cap=40)
    ident = _first(q1_d2a, "exact_Pg_kernel", "cond")
    ad = promoter_adapter(ident, schedule=schedule)
    pr = run_paired({"p": lambda: ad.build(env)}, spec, env, seeds=(11,))
    run = pr.runs["p"][0]
    rounds = sorted(a["label_round"] for a in run.audit.of("request"))
    gaps = {b - a for a, b in itertools.pairwise(rounds)}
    if expect is not None:
        assert gaps <= expect and gaps
    props = {a.get("propensity") for a in run.audit.of("request")}
    assert None not in props  # every query carries its declared propensity
    assert run.leak_attempts == []


def test_promoter_shell_regime_is_declared_and_in_contract(q1_d2a):
    env = env_of(T=400, cap=40)
    ev = build_evidence(_first(q1_d2a, "exact_Pg_kernel", "marg"))
    pol = EvidencePromoterPolicy(ev, schedule="cyclic_gaps")
    pol.reset(env)
    assert ev.selection == "predictable"
    base = StreamSpec(
        family="t", T=400, dependence="markov", rho=0.5, delay=DelaySpec("fixed", d=4)
    )
    spec_of_ev = lambda s: ev.contract_status(s)
    assert spec_of_ev(base)["status"] == "IN_CONTRACT"
    inf_delay = StreamSpec(family="t", T=400, delay=DelaySpec("informative"))
    inf_miss = StreamSpec(family="t", T=400, missing=MissingSpec("informative", p_fav=0.5))
    for s in (inf_delay, inf_miss):
        st = spec_of_ev(s)
        assert st["status"] == "OUT_OF_CONTRACT" and "informative" in st["reasons"][0]
    too_dep = StreamSpec(family="t", T=400, dependence="markov", rho=0.95)
    assert "rho_bar" in spec_of_ev(too_dep)["reasons"][0]


# ================================================================ reuse of gapmix is exact
def _chain(rng, p, rho, n, rule):
    ev, z, out = 0, None, []
    for i in range(n):
        g = rule(i, z)
        ev += g
        if z is None:
            z = int(rng.random() < p)
        else:
            lam = rho**g
            z = int(rng.random() < (p * (1 - lam) if z == 0 else p + (1 - p) * lam))
        out.append((ev, z))
    return out


def test_exact_gap_and_envelope_match_gapmix_components():
    cfg = SimpleNamespace(T=1000, h=0.1, B=50)
    ctx = Ctx(Q0, 1000, 50, 0.8)
    rng = np.random.default_rng(3)
    seq = _chain(rng, 0.8, 0.5, 36, lambda i, z: [1, 3, 2, 6, 10][i % 5])
    mine_x = _mixture(ctx, _per_start("marg", "altgrid", ctx, {}))
    ref_x = gapmix.exact_evidence(cfg, 0.1, 0.8, True)
    mine_e = _mixture(ctx, lambda: BetStart(ctx, PluginPred(), "marg", rho_bar=0.8))
    ref_e = gapmix.envelope_evidence(cfg, 0.1, 0.8, True)
    for ev, z in seq:
        mine_x.update(ev, z)
        ref_x.update(ev, -1.0 if z else 1.0)
        mine_e.update(ev, z)
        ref_e.update(ev, -1.0 if z else 1.0)
    assert mine_x.log_e == pytest.approx(ref_x.log_e_value, abs=1e-9)
    assert mine_e.log_e == pytest.approx(ref_e.log_e_value, abs=1e-12)


# ================================================================ validity Monte-Carlo (correctly specified null chain)
ALPHA = 0.1
REPS = int(os.environ.get("D2A_Q1_MC_REPS", "80"))
N_LAB = 20
RULES = {
    "cyclic_predictable": lambda i, z: [1, 3, 2, 6][i % 4],
    "adaptive_on_past_outcome": lambda i, z: 2 if z == 1 else 5,  # F_{i-1}-measurable gap rule
}
MC_ENV = EnvSpec(T=400, costs=COSTS, budget=BudgetSpec(label_cap=24))


@pytest.fixture(scope="module")
def mc_pool():
    rng = np.random.default_rng(20261107)
    # cond null boundary: iid p = q0 (rho 0).  marg null boundary: stationary chain p = q0, rho 0.5 <= declared rho_bar
    return {
        (null, rn): [_chain(rng, Q0, rho, N_LAB, RULES[rn]) for _ in range(REPS)]
        for null, rho in (("cond", 0.0), ("marg", 0.5))
        for rn in RULES
    }


def _false_alarm_rate(ident, paths, alpha):
    fa = 0
    for seq in paths:
        ev = build_evidence(ident, cell_width=0.05)
        ev.bind(MC_ENV)
        thr = -math.log(ev.alpha_level or alpha)
        for e, z in seq:
            ev.core.update(e, z)
            if ev.log_e >= thr:
                fa += 1
                break
    return fa / len(paths)


def _claimed_valid_idents(q1_d2a):
    out, seen = [], set()
    for r in q1_d2a:
        if not is_implemented(r):
            continue
        k = (r["variant"], r["target_null"])
        if k in seen or spec_for(r).validity == "NOT_CLAIMED":
            continue
        seen.add(k)
        c = dict(r)
        c["configuration"] = {
            **r["configuration"],
            **({"max_starts": 4} if "max_starts" in r["configuration"] else {}),
        }
        out.append(c)
    return out


def test_claimed_valid_evidence_false_alarm_at_or_below_alpha(q1_d2a, mc_pool):
    idents = _claimed_valid_idents(q1_d2a)
    assert len(idents) >= 28
    rows, bad = [], []
    for ident in idents:
        for rn in RULES:
            a = (
                ident["configuration"].get("selector_alpha")
                if ident["variant"] == "min_of_both_certificate"
                else ALPHA
            )
            rate = _false_alarm_rate(ident, mc_pool[(ident["target_null"], rn)], a)
            tol = a + 2 * math.sqrt(a * (1 - a) / REPS)
            rows.append((ident["variant"], ident["target_null"], rn, a, rate))
            if rate > tol:
                bad.append(rows[-1])
    assert not bad, bad
    # min_of_both is valid under EITHER null: also check it on the other null's boundary stream
    for ident in idents:
        if ident["variant"] in ("min_of_both_certificate", "dual_null_reporting"):
            other = "marg" if ident["target_null"] == "cond" else "cond"
            if ident["variant"] == "min_of_both_certificate":
                a = ident["configuration"]["selector_alpha"]
                assert _false_alarm_rate(
                    ident, mc_pool[(other, "cyclic_predictable")], a
                ) <= a + 2 * math.sqrt(a * (1 - a) / REPS)
    os.makedirs(ROOT / "results/d2a_rar", exist_ok=True)
    (ROOT / "results/d2a_rar/q1_hook_validity_mc.json").write_text(
        json.dumps({"reps": REPS, "n_labels": N_LAB, "alpha": ALPHA, "rows": rows}, indent=1)
    )


def test_claimed_valid_evidence_has_power_under_a_real_alternative(q1_d2a):
    """Guard against vacuous validity (an evidence that never alarms): exact-gap marg and cond alarm under p=0.9."""
    rng = np.random.default_rng(5)
    paths = [_chain(rng, 0.9, 0.5, 30, RULES["cyclic_predictable"]) for _ in range(30)]
    for null in ("cond", "marg"):
        ident = _first(q1_d2a, "exact_Pg_kernel", null)
        ident = {**ident, "configuration": {**ident["configuration"], "declared_rho_bar": 0.5}}
        assert _false_alarm_rate(ident, paths, ALPHA) >= 0.5


def test_informative_selection_inflates_false_alarms_and_is_flagged(q1_d2a):
    """Zeros are dropped w.p. 0.7 under an iid boundary null: the gap/observation mechanism carries information."""
    rng = np.random.default_rng(9)
    paths = []
    for _ in range(REPS):
        seq, ev = [], 0
        while len(seq) < N_LAB:
            ev += 1
            z = int(rng.random() < Q0)
            if z == 0 and rng.random() < 0.7:
                continue
            seq.append((ev, z))
        paths.append(seq)
    ident = _first(q1_d2a, "exact_Pg_kernel", "cond")
    rate = _false_alarm_rate(ident, paths, ALPHA)
    assert rate > ALPHA + 2 * math.sqrt(ALPHA * (1 - ALPHA) / REPS)
    ev = build_evidence(ident)
    ev.declare_selection("predictable")
    informative = StreamSpec(
        family="t", T=400, missing=MissingSpec("informative", p_fav=0.0, p_unfav=0.7)
    )
    assert ev.contract_status(informative)["status"] == "OUT_OF_CONTRACT"


# ================================================================ registry / identity coverage
def test_every_registry_q1_evidence_identity_is_implemented_or_blocked_by_ledger(q1_d2a):
    for r in q1_d2a:
        if is_implemented(r):
            sp = spec_for(r)
            assert sp.null == r["target_null"] and sp.validity in (
                "PROVEN_DECLARED_CLASS", "DOMINATED_BY_VALID", "NOT_CLAIMED")  # fmt: skip
        else:
            assert (r["family"], r["variant"]) in BLOCKED_VARIANTS and r["blocked_by"]
            with pytest.raises(Q1NotImplemented):
                spec_for(r)


def test_high_overlap_identities_stay_labelled_baselines(q1_d2a):
    for r in q1_d2a:
        if r["prior_art_status"] in ("HIGH_OVERLAP", "KNOWN"):
            assert r["role"] == "baseline_or_ablation_only" and not r["novelty_bearing"]


def test_registry_file_is_in_sync_with_code():
    path = ROOT / "docs/d2a_rar/registry/Q1_EVIDENCE_IMPLS.json"
    assert json.loads(path.read_text(encoding="utf8")) == json.loads(
        json.dumps(registry_document(), sort_keys=True)
    )
    ents = registry_document()["entries"]
    assert len(ents) == 2 * len(IMPLEMENTED_VARIANTS)
    for e in ents:
        for k in (
            "filtration",
            "transition_model",
            "stopping",
            "parameter_uncertainty",
            "selection_requirement",
            "validity",
        ):
            assert e[k]
