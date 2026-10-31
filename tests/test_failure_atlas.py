"""CPU-fast tests for the Failure Atlas v1 harness (R4 exploratory; protocol failure_atlas_v1)."""

from __future__ import annotations

import numpy as np
import pytest

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import BASELINES, Method, build_method, run

T = 200  # cheap horizon for tests


def small(**kw) -> fa.CellSpec:
    base = {
        "onset": 0.6,
        "duration": 1.0,
        "effect": "strong",
        "off_type": "harmful",
        "d": 1,
        "budget_frac": 0.25,
        "s": 0.1,
    }
    base.update(kw)
    return fa.CellSpec(T=T, **base)


# ------------------------------------------------------------------ grid / streams


def test_grid_size_and_unique_ids():
    cells = fa.all_cells()
    assert len(cells) == 2592
    assert len({c.cell_id for c in cells}) == 2592
    assert all(c.T == 1000 and c.c == 0.01 and c.h == 0.1 and c.alpha == 0.1 for c in cells)


def test_method_names_exist_in_harness():
    for name in fa.ALL_METHODS:
        build_method(name, fa.bernoulli_grid_spec())
    assert set(fa.UNGATED) | {fa.FLOOR} <= set(BASELINES)
    assert {"episode_geo", "episode_equal", "episode_front", "allonset_edetector"} <= set(BASELINES)


@pytest.mark.parametrize("effect", list(fa.EFFECTS))
def test_null_twin_never_favourable(effect):
    for off in fa.OFF_TYPES:
        cell = small(effect=effect, off_type=off).null_twin()
        assert cell.null and cell.off_type == "harmful"
        for sd in range(3):
            st = fa.make_family1_stream(cell, sd)
            assert st.truth.regime.sum() == 0
            assert np.all(st.truth.regime_mean >= -cell.h)  # every promotion is false


def test_stream_path_jitter_and_determinism():
    cell = small(onset=0.3, duration=0.3)
    taus = []
    for sd in range(40):
        st = fa.make_family1_stream(cell, sd)
        on = np.flatnonzero(st.truth.regime)
        taus.append(on[0])
        assert len(on) == round(0.3 * T) or on[-1] == T - 1
    assert all((0.3 - 0.05) * T - 1 <= x <= (0.3 + 0.05) * T + 1 for x in taus)
    assert len(set(taus)) > 5  # genuinely randomised
    a, b = fa.make_family1_stream(cell, 7), fa.make_family1_stream(cell, 7)
    assert np.array_equal(a.loss0, b.loss0) and np.array_equal(a.truth.regime, b.truth.regime)
    pair = cell.p_pair
    assert pair == (0.1, 0.9)
    assert small(off_type="neutral").p_pair == (0.5, 0.9)


def test_easiest_moves_one_axis():
    cell = fa.CellSpec(0.8, 0.15, "weak", "harmful", 50, 0.05, 0.5)
    for ax, val in fa.EASIEST.items():
        moved = cell.easiest(ax)
        assert getattr(moved, ax) == val
        diff = [
            f
            for f in ("onset", "duration", "effect", "d", "budget_frac", "s")
            if getattr(moved, f) != getattr(cell, f)
        ]
        assert diff == [ax]


# ------------------------------------------------------------------ information boundary


class Spy(Method):
    name = "spy"

    def _init(self):
        self.log = []
        self.q = set()

    def decide(self, t, released):
        self.log.append((t, released))
        for ev, x in released:
            assert ev + self.cfg.d == t and ev in self.q  # only queried, only after the delay
            assert isinstance(ev, int) and isinstance(x, float) and x in (-1.0, 1.0)
        q = t % 5 == 0 and t + self.cfg.d <= self.cfg.T
        if q and self.used < self.cfg.B:
            self.q.add(t)
        return 0, q


def test_methods_get_only_released_labels():
    cell = small(d=10)
    st = fa.make_family1_stream(cell, 1)
    spy = Spy()
    run(st, spy, cell.config(1))
    assert len(spy.log) == T
    assert not hasattr(spy, "stream") and not hasattr(spy, "truth")
    assert all(isinstance(r, tuple) for _, r in spy.log)
    assert sum(len(r) for _, r in spy.log) > 0


def test_filter_reference_budget_and_released_only():
    cell = small(d=10, budget_frac=0.1, onset=0.3)
    ref = fa.build_ref_family(T, 0.3)
    for sd in range(4):
        st = fa.make_family1_stream(cell, sd)
        r = run(st, ref, cell.config(sd))  # BudgetExceeded would raise
        assert r.queries <= cell.B
        assert r.query_mask[T - cell.d :].sum() == 0  # nothing unreleasable requested
    # perturb every outcome from round 101 on; with d=10 actions through round 110 must not change
    st = fa.make_family1_stream(cell, 3)
    st2 = fa.Stream(st.loss0.copy(), st.loss1.copy(), st.truth)
    st2.loss0[100:], st2.loss1[100:] = 1.0 - st.loss0[100:], 1.0 - st.loss1[100:]
    a = run(st, fa.build_ref_family(T, 0.3), cell.config(3)).actions
    b = run(st2, fa.build_ref_family(T, 0.3), cell.config(3)).actions
    assert np.array_equal(a[:110], b[:110])


def test_reference_posterior_matches_hypothesis_filter_by_hand():
    hyp = np.array([[50.0, 200.0, 0.1, 0.9], [200.0, 200.0, 0.1, 0.9]])  # on at 50 vs never
    ref = fa.FilterReference(hyp, kappa=1.0)
    cfg = small(d=1, budget_frac=0.25).config(0)
    ref.start(cfg)
    ref.decide(1, ())
    for ev in (60, 61, 62):
        ref.decide(ev + 1, ((ev, -1.0),))  # three Y=1 labels
    odds = ref.post[0] / ref.post[1]
    assert odds == pytest.approx((0.9 / 0.1) ** 3, rel=1e-4)


# ------------------------------------------------------------------ references work


def test_rlaw_beats_no_switch_on_easy_late_onset_cell():
    cell = small(onset=0.6, duration=1.0, effect="strong", d=1, budget_frac=0.25)
    law, fam, ns = [], [], []
    for sd in range(5):
        st = fa.make_family1_stream(cell, sd)
        cfg = cell.config(sd)
        law.append(run(st, fa.build_ref_law(cell), cfg).cost / T)
        fam.append(run(st, fa.build_ref_family(T, 0.1), cfg).cost / T)
        ns.append(run(st, build_method("no_switch"), cfg).cost / T)
    assert np.mean(law) < np.mean(ns) - 0.1
    assert np.mean(fam) < np.mean(ns)


def test_evaluate_cell_shapes_and_null():
    cell = small()
    res = fa.evaluate_cell(cell, [0, 1], methods=("no_switch", "episode_front"), kappa=0.1)
    for k in ("no_switch", "episode_front", "ref_law", "ref_family", "ref_regime_clairvoyant"):
        assert len(res["methods"][k]["cost"]) == 2
    assert "ref_valid" in res["methods"] and len(res["methods"]["ref_valid"]["cost"]) == 2
    assert set(res["null"]["methods"]) == {"no_switch", "episode_front", "ref_family", "ref_valid"}
    assert res["methods"]["no_switch"]["cost"][0] <= 1.0 + 1e-9
    cl = fa.classify_cell(res)
    assert cl["label"] in {
        "info_limited",
        "reference_unsafe",
        "shared_failure",
        "cost_of_validity",
        "prior_gap",
        "headroom_not_shared",
        "no_headroom",
    }


def test_calibration_and_isolate_smoke():
    cells = [small(), small(effect="medium")]
    kappa, info = fa.calibrate_family_kappa(cells, list(range(6)))
    assert kappa in fa.KAPPA_GRID and info["n_twins"] == 2
    iso = fa.isolate(
        small(d=10, budget_frac=0.1, s=0.5),
        [0, 1],
        kappa=kappa,
        axes=("d", "budget_frac", "s"),
        methods=("no_switch", "episode_front"),
    )
    assert set(iso) == {"d", "budget_frac", "s"}
    assert all("removes_failure" in v for v in iso.values())
    assert fa.isolate(small(onset=0.1), [0, 1], axes=("onset",), methods=("no_switch",)) == {}


# ------------------------------------------------------------------ classification branches


def synth(
    *,
    fam=0.10,
    base=0.20,
    noise=0.005,
    law=0.10,
    floor=0.35,
    null_fp=0.05,
    n=20,
    wide=None,
    valid=None,
):
    rng = np.random.default_rng(0)

    def arr(mu, sd=noise):
        return list(mu + sd * rng.standard_normal(n))

    z = lambda: {"cost": [], "fp": [0] * n}
    methods = {}
    for k in fa.SAFETY_GATED:
        methods[k] = {**z(), "cost": arr(base)}
    methods["no_switch"] = {**z(), "cost": arr(floor)}
    methods["ref_family"] = {**z(), "cost": arr(fam)}
    methods["ref_law"] = {**z(), "cost": arr(law)}
    if valid is not None:
        methods["ref_valid"] = {**z(), "cost": arr(valid)}
    if wide:
        for k, (mu, sd) in wide.items():
            methods[k]["cost"] = arr(mu, sd)
    k_fp = round(null_fp * n)
    null = {"methods": {"ref_family": {"cost": [0.1] * n, "fp": [1] * k_fp + [0] * (n - k_fp)}}}
    return {"cell_id": "synthetic", "alpha": 0.1, "methods": methods, "null": null}


def test_classify_shared_failure():
    cl = fa.classify_cell(synth())
    assert cl["label"] == "shared_failure" and cl["shared_failure"]
    assert cl["severity"] == pytest.approx(0.10, abs=0.01)
    assert cl["H_ci"][0] > 0.01 and not cl["info_limited"]


def test_classify_headroom_not_shared():
    # best safe baseline is 0.03 above the reference (tight); one noisy baseline has a CI reaching below 0.01
    res = synth(base=0.13, wide={"episode_geo": (0.19, 0.4)})
    cl = fa.classify_cell(res)
    assert cl["label"] == "headroom_not_shared"
    assert cl["H_ci"][0] > 0.01 and not cl["shared_failure"]


def test_classify_info_limited():
    res = synth(law=0.349, fam=0.349, floor=0.35)  # even knowing the law, switching gains nothing
    cl = fa.classify_cell(res)
    assert cl["label"] == "info_limited" and cl["info_limited"] and not cl["shared_failure"]


def test_classify_reference_unsafe_blocks_failure():
    cl = fa.classify_cell(synth(null_fp=0.5))
    assert cl["label"] == "reference_unsafe" and not cl["shared_failure"]
    assert cl["ref_family_null_fp"]["rate"] == pytest.approx(0.5)
    assert cl["ref_family_null_fp"]["wilson"][1] > 0.5


def test_classify_no_headroom():
    cl = fa.classify_cell(synth(base=0.101, floor=0.35))
    assert cl["label"] == "no_headroom" and not cl["material_headroom"]


def test_no_switch_floor_must_also_be_beaten():
    # gated baselines are all bad but doing nothing is almost as good as the reference
    cl = fa.classify_cell(synth(base=0.30, floor=0.105, law=0.10, fam=0.10))
    assert cl["best_safe"] == "no_switch" and not cl["shared_failure"]


# ------------------------------------------------------------------ seeds


def test_seed_partitions_and_confirmation_guard():
    d = fa.seeds("discovery", 5, offset=10)
    assert d == tuple(range(10, 15))
    assert fa.seeds("development", 2)[0] == 10**5
    assert fa.seeds("mechanism", 2)[0] == 2 * 10**5
    with pytest.raises(fa.ConfirmationSeedsLocked):
        fa.seeds("confirmation", 3)
    assert fa.seeds("confirmation", 3, allow_confirmation=True)[0] == 9 * 10**5
    with pytest.raises(ValueError):
        fa.seeds("discovery", 10, offset=10**5)
    with pytest.raises(fa.ConfirmationSeedsLocked):
        fa.evaluate_cell(small(), [9 * 10**5], methods=("no_switch",))


# ------------------------------------------------------------------ Amendment 1


def test_rlaw_promotes_on_transient_window_cell_after_plan_value_fix():
    """Cycle-1 defect: staying-until-T counted the harmful tail, so R_law never promoted here."""
    cell = fa.CellSpec(0.3, 0.3, "strong", "harmful", 10, 0.05, 0.5, T=200)
    assert cell.cell_id.startswith("on0.3_L0.3_strong_harmful_d10_b0.05_s0.5")
    law, ns, promos = [], [], []
    for sd in range(8):
        st = fa.make_family1_stream(cell, sd)
        cfg = cell.config(sd)
        r = run(st, fa.build_ref_law(cell), cfg)
        law.append(r.cost / cell.T)
        promos.append(r.promotions)
        ns.append(run(st, build_method("no_switch"), cfg).cost / cell.T)
    assert sum(p > 0 for p in promos) >= 6
    assert np.mean(law) < np.mean(ns) - 0.05


def test_rlaw_and_rfamily_beat_no_switch_on_strong_late_onset_cell():
    cell = small(onset=0.8, duration=1.0, effect="strong", d=1, budget_frac=0.25, s=0.1)
    law, fam, ns = [], [], []
    for sd in range(6):
        st = fa.make_family1_stream(cell, sd)
        cfg = cell.config(sd)
        law.append(run(st, fa.build_ref_law(cell), cfg).cost / T)
        fam.append(run(st, fa.build_ref_family(T, 0.1), cfg).cost / T)
        ns.append(run(st, build_method("no_switch"), cfg).cost / T)
    assert np.mean(law) < np.mean(ns) - 0.03 and np.mean(fam) < np.mean(ns) - 0.01


def test_reference_plan_value_is_revert_aware():
    # window [50, 100) of a 200-round horizon: staying promoted to the end is net negative,
    # promote-then-revert is positive; the old stay-until-T value would not promote.
    hyp = np.array([[50.0, 100.0, 0.1, 0.9]])
    ref = fa.FilterReference(hyp, kappa=1.0)
    cfg = small(d=1, budget_frac=0.25, s=0.1).config(0)
    ref.start(cfg)
    ref.decide(52, ((51, -1.0),))
    cum = ref.plan_values(52)
    assert cum[-1] < 0 < cum.max()  # tail is harmful, window is beneficial
    assert ref.act == 1  # the old rule (value of staying to T) would have stayed at 0


def test_diagnostics_decomposition_runs_and_oracles_are_not_registered():
    from shiftlab.dive.switching_explore import BASELINES

    cell = small(onset=0.3, duration=0.6, d=5, budget_frac=0.25, s=0.1)
    out = fa.diagnose_cell(cell, [0, 1, 2], kappa=0.1)
    names = set(out["per_method"])
    assert {"diag_oracle_known_onset", "diag_oracle_known_stake", "diag_oracle_known_both"} <= names
    assert not any(n.startswith("diag_oracle_") for n in fa.ALL_METHODS)
    assert not any(n.startswith("diag_oracle_") for n in BASELINES)
    with pytest.raises(ValueError):
        build_method("diag_oracle_known_both", fa.bernoulli_grid_spec())
    for k in fa.SAFETY_GATED:
        assert {"labels_after_onset", "frac_promoted", "mean_final_log_e", "analytic"} <= set(
            out["per_method"][k]
        )
    assert out["per_method"]["episode_front"]["analytic"]["labels"] > 0
    p = out["parts"]
    # identity: front - family = onset + stake + interaction + (known_both - family)
    total = p["onset_uncertainty"]["mean"] + p["stake_mismatch"]["mean"] + p["interaction"]["mean"]
    both = (
        out["per_method"]["episode_front"]["mean_cost"]
        - out["per_method"]["diag_oracle_known_both"]["mean_cost"]
    )
    assert total == pytest.approx(both, abs=1e-9)
    assert 0.0 < out["kelly_stake"] < 1.0


def test_oracle_gate_uses_given_onset_only_through_constructor():
    cell = small(onset=0.3, duration=1.0, d=5, budget_frac=0.25)
    st = fa.make_family1_stream(cell, 0)
    m = fa.DiagOracleGate("known_both", 3, 0.7)
    r = run(st, m, cell.config(0))
    assert r.queries <= cell.B and list(m.ep.starts) == [3] and list(m.ep.stakes) == [0.7]


# ------------------------------------------------------------------ Amendment 2: R_valid and classes


def test_classify_old_archives_without_ref_valid_keep_amendment1_behaviour():
    cl = fa.classify_cell(synth())
    assert cl["label"] == "shared_failure" and cl["headroom_valid"] is None and not cl["prior_gap"]


def test_classify_shared_failure_requires_headroom_against_r_valid():
    cl = fa.classify_cell(synth(valid=0.10))  # R_valid is as good as R_family: failure stands
    assert cl["label"] == "shared_failure" and cl["shared_failure"] and cl["headroom_valid"]
    assert cl["H_valid_ci"][0] > 0.01 and cl["prior_gap"]  # advantage rests on the declared prior


def test_classify_cost_of_validity():
    # R_family has headroom, but a valid method with the declared prior is no better than best_safe
    cl = fa.classify_cell(synth(valid=0.195))
    assert cl["label"] == "cost_of_validity"
    assert not cl["shared_failure"] and cl["shared_vs_family_only"] and cl["material_headroom"]
    assert cl["severity"] == 0.0 and cl["headroom_valid"] is False


def test_classify_prior_gap():
    # R_family has no material headroom (0.195 vs best 0.20) but R_valid beats every baseline
    cl = fa.classify_cell(synth(fam=0.195, valid=0.10))
    assert cl["label"] == "prior_gap" and cl["prior_gap"] and not cl["shared_failure"]
    assert not cl["material_headroom"] and cl["headroom_valid"]
    assert all(g["lo"] > 0.01 for g in cl["valid_gaps"].values())


def test_classify_headroom_not_shared_survives_with_r_valid():
    res = synth(base=0.13, wide={"episode_geo": (0.19, 0.4)}, valid=0.10)
    cl = fa.classify_cell(res)
    assert (
        cl["label"] == "headroom_not_shared" and not cl["prior_gap"]
    )  # noisy baseline CI not above 0.01


def test_classify_precedence_info_limited_and_unsafe_beat_new_classes():
    res = synth(law=0.349, fam=0.349, floor=0.35, valid=0.10)
    assert fa.classify_cell(res)["label"] == "info_limited"
    assert fa.classify_cell(synth(null_fp=0.5, valid=0.195))["label"] == "reference_unsafe"


def test_rvalid_weights_fixed_from_config_alone():
    cfg_a, cfg_b = small(d=5).config(1), small(d=5).config(99)
    sa, wa = fa.family1_start_design(cfg_a)
    sb, wb = fa.family1_start_design(cfg_b)
    assert (sa, wa) == (sb, wb)  # no dependence on the seed or on any data
    assert list(sa) == sorted(set(sa)) and min(sa) >= 0 and max(sa) < cfg_a.B
    assert all(w > 0 for w in wa) and sum(wa) == pytest.approx(1.0)
    stakes, sw = fa.family_kelly_stakes(0.1)
    assert len(stakes) == 3 and all(0 < x < 1 for x in stakes) and sum(sw) == pytest.approx(1.0)
    gate = fa.valid_gate(cfg_a, sa, wa)
    assert list(gate.stakes) == list(stakes) and gate.time == 0
    with pytest.raises(ValueError):
        fa.set_stake_mixture(gate, [0.1, 1.0], [0.5, 0.5])  # stake must be below 1
    gate.update(0.5)
    with pytest.raises(ValueError):  # not after data
        fa.set_stake_mixture(gate, [0.1], [1.0])


def _boundary_null_rate(cell, n_seeds, tag):
    """Any-promotion rate on the exact boundary null: E[-D] = h, so every promotion is false."""
    k = 0
    for sd in range(n_seeds):
        rng = np.random.default_rng([sd, tag])
        p_b = (1.0 + cell.h) / 2.0
        st = fa.make_bernoulli_stream(rng, cell.T, (p_b, p_b), path=np.zeros(cell.T, dtype=int))
        k += int(run(st, fa.build_ref_valid(cell), cell.config(sd)).promotions > 0)
    return k / n_seeds


def test_rvalid_family1_validity_on_boundary_null():
    cell = fa.CellSpec(0.6, 1.0, "strong", "harmful", 1, 0.25, 0.1, T=300)
    n = 300
    rate = _boundary_null_rate(cell, n, 99)
    sd = (cell.alpha * (1 - cell.alpha) / n) ** 0.5
    print(
        f"R_valid family-1 boundary-null any-promotion rate: {rate:.4f} (alpha 0.1, 2SD {2 * sd:.4f})"
    )
    assert rate <= cell.alpha + 2 * sd


def test_rvalid_family2_validity_on_boundary_null():
    cell = fa.Family2CellSpec(0.005, "strong", "harmful", 1, 0.25, 0.1, T=300)
    n = 200
    rate = _boundary_null_rate(cell, n, 98)
    sd = (cell.alpha * (1 - cell.alpha) / n) ** 0.5
    print(f"R_valid family-2 boundary-null any-promotion rate: {rate:.4f}")
    assert rate <= cell.alpha + 2 * sd


def test_rvalid_has_power_and_respects_budget_and_information():
    cell = fa.CellSpec(0.6, 1.0, "strong", "harmful", 10, 0.25, 0.1, T=300)
    valid, ns = [], []
    for sd in range(5):
        st = fa.make_family1_stream(cell, sd)
        r = run(st, fa.build_ref_valid(cell), cell.config(sd))
        assert r.queries <= cell.B and r.query_mask[cell.T - cell.d :].sum() == 0
        valid.append(r.cost / cell.T)
        ns.append(run(st, build_method("no_switch"), cell.config(sd)).cost / cell.T)
    assert np.mean(valid) < np.mean(ns) - 0.03
    # no peeking: perturb outcomes from round 151 on; with d=10 actions through 160 are unchanged
    st = fa.make_family1_stream(cell, 2)
    st2 = fa.Stream(st.loss0.copy(), st.loss1.copy(), st.truth)
    st2.loss0[150:], st2.loss1[150:] = 1.0 - st.loss0[150:], 1.0 - st.loss1[150:]
    a = run(st, fa.build_ref_valid(cell), cell.config(2)).actions
    b = run(st2, fa.build_ref_valid(cell), cell.config(2)).actions
    assert np.array_equal(a[:160], b[:160])


# ------------------------------------------------------------------ Amendment 2: R6 lazy integration


def test_r6_integration_gated_and_ungated_groups(monkeypatch):
    from shiftlab.dive.switching_explore import NoSwitch, PeriodicMean

    fake = {
        "fake_gated": (lambda cfg: NoSwitch(), True, "gated stand-in"),
        "fake_ungated": (lambda cfg: PeriodicMean(), False, "ungated stand-in"),
    }
    monkeypatch.setattr(fa, "_R6_CACHE", (fake, None))
    assert "fake_gated" in fa.gated_methods() and "fake_gated" not in fa.ungated_methods()
    assert "fake_ungated" in fa.ungated_methods() and "fake_ungated" not in fa.gated_methods()
    assert set(fa.all_method_names()) >= {"fake_gated", "fake_ungated", "no_switch"}
    reg = {r["name"]: r for r in fa.baseline_registry()}
    assert (
        reg["fake_gated"]["status"] == "implemented" and reg["fake_gated"]["role"] == "safety-gated"
    )
    res = fa.evaluate_cell(small(), [0, 1], kappa=0.1)
    assert {"fake_gated", "fake_ungated"} <= set(res["methods"])
    cl = fa.classify_cell(res)
    assert "fake_gated" in cl["gaps"] and "fake_ungated" not in cl["gaps"]


def test_r6_import_failure_is_a_logged_skip(monkeypatch):
    monkeypatch.setattr(fa, "_R6_CACHE", ({}, "R6 baselines skipped: ImportError: boom"))
    assert fa.r6_status().startswith("R6 baselines skipped")
    assert fa.gated_methods() == fa.SAFETY_GATED and fa.ungated_methods() == fa.UNGATED
    assert fa.all_method_names() == fa.ALL_METHODS
    assert {r["name"]: r["status"] for r in fa.baseline_registry()}[
        "gong_zhang_delayed"
    ] == "missing"


def test_r6_registry_status_updated_when_module_available(monkeypatch):
    pytest.importorskip("shiftlab.dive.atlas_r6_baselines")
    monkeypatch.setattr(fa, "_R6_CACHE", None)  # re-read the real module
    names = set(fa.r6_methods())
    assert names, "R6_METHODS is empty"
    reg = {r["name"]: r for r in fa.baseline_registry()}
    assert all(reg[n]["status"] == "implemented" for n in names)


# ------------------------------------------------------------------ Failure family 2


def small2(**kw) -> fa.Family2CellSpec:
    base = {
        "rate": 0.005,
        "effect": "strong",
        "off_type": "harmful",
        "d": 1,
        "budget_frac": 0.25,
        "s": 0.05,
    }
    base.update(kw)
    return fa.Family2CellSpec(T=400, **base)


def test_family2_grid_size_and_unique_ids():
    cells = fa.all_cells2()
    assert len(cells) == 486
    assert len({c.cell_id for c in cells}) == 486
    assert all(c.T == 1000 and c.c == 0.01 and c.h == 0.1 and c.alpha == 0.1 for c in cells)
    assert {c.rate for c in cells} == set(fa.RATES2)
    assert not {c.cell_id for c in cells} & {c.cell_id for c in fa.all_cells()}


@pytest.mark.parametrize("effect", list(fa.EFFECTS))
def test_family2_null_twin_never_favourable(effect):
    for off in fa.OFF_TYPES:
        cell = small2(effect=effect, off_type=off, rate=0.02).null_twin()
        assert cell.null and cell.off_type == "harmful" and cell.rate == fa.RATES2[0]
        for sd in range(3):
            st = fa.make_family2_stream(cell, sd)
            assert st.truth.regime.sum() == 0
            assert np.all(st.truth.regime_mean >= -cell.h)  # every promotion is false


def test_family2_stream_markov_off_start_determinism_and_disjoint_seeds():
    cell = small2(rate=0.02)
    paths = [fa.make_family2_stream(cell, sd).truth.regime for sd in range(60)]
    assert all(p[0] == 0 for p in paths)  # initial state off
    assert any(p.any() for p in paths) and any(np.any(np.diff(p) == -1) for p in paths)
    flips = np.mean([np.mean(np.diff(p) != 0) for p in paths])
    assert flips == pytest.approx(0.02, abs=0.01)
    a, b = fa.make_family2_stream(cell, 7), fa.make_family2_stream(cell, 7)
    assert np.array_equal(a.loss0, b.loss0) and np.array_equal(a.truth.regime, b.truth.regime)
    # the family tag keeps family-2 draws away from the family-1 seed sequence
    idx = cell.stable_index
    f1 = np.random.default_rng([7, idx]).random(5)
    f2 = np.random.default_rng([7, fa.FAMILY2_TAG, idx]).random(5)
    assert not np.array_equal(f1, f2)
    assert cell.p_pair == (0.1, 0.9) and small2(off_type="neutral").p_pair == (0.5, 0.9)


def test_family2_easiest_moves_one_axis():
    cell = fa.Family2CellSpec(0.02, "weak", "harmful", 50, 0.05, 0.5)
    expected = {"rate": 0.002, "d": 1, "budget_frac": 0.25, "s": 0.05, "effect": "strong"}
    assert dict(fa.EASIEST2) == expected and set(cell.axes) == set(expected)
    for ax, val in expected.items():
        moved = cell.easiest(ax)
        assert getattr(moved, ax) == val
        diff = [f for f in expected if getattr(moved, f) != getattr(cell, f)]
        assert diff == [ax]
    with pytest.raises(ValueError):
        cell.easiest("onset")


def test_family2_neighbours_one_level_one_axis():
    cell = small2()
    nb = fa.neighbours(cell)
    assert nb and all(n.family == 2 for n in nb)
    fields = ("rate", "effect", "off_type", "d", "budget_frac", "s")
    for n in nb:
        assert len([f for f in fields if getattr(n, f) != getattr(cell, f)]) == 1


def test_family2_hypothesis_grid_and_filter_by_hand():
    hyp = fa.family2_hypotheses()
    assert hyp.shape[1] == 3
    assert set(np.unique(hyp[:, 0])) == {0.0, *fa.RATES2}
    one = np.array([[0.02, 0.1, 0.9]])
    ref = fa.HMMFilterReference(one, kappa=1.0)
    ref.start(small2(d=1).config(0))
    ref.decide(52, ((51, -1.0),))  # one Y=1 label at event 51
    q = 0.5 - 0.5 * (1 - 2 * 0.02) ** 50  # P(S_51 = on) from the off start
    assert ref.p1[0] == pytest.approx(q * 0.9 / (q * 0.9 + (1 - q) * 0.1), rel=1e-9)
    # a run of Y=1 labels shifts the posterior to the rate that reaches "on", away from the null member
    two = np.array([[0.0, 0.1, 0.9], [0.02, 0.1, 0.9]])
    ref = fa.HMMFilterReference(two, kappa=1.0)
    ref.start(small2(d=1).config(0))
    for ev in range(100, 110):
        ref.decide(ev + 1, ((ev, -1.0),))
    assert ref.post[1] > 0.99


def test_family2_references_budget_and_no_peeking():
    cell = small2(d=10, budget_frac=0.1, rate=0.02)
    builders = (
        lambda: fa.build_ref_family(cell.T, 0.3, 2),
        lambda: fa.build_ref_law(cell),
        lambda: fa.build_ref_valid(cell),
    )
    for build in builders:
        for sd in range(4):
            st = fa.make_family2_stream(cell, sd)
            r = run(st, build(), cell.config(sd))  # BudgetExceeded would raise
            assert r.queries <= cell.B and r.query_mask[cell.T - cell.d :].sum() == 0
        st = fa.make_family2_stream(cell, 3)
        st2 = fa.Stream(st.loss0.copy(), st.loss1.copy(), st.truth)
        st2.loss0[200:], st2.loss1[200:] = 1.0 - st.loss0[200:], 1.0 - st.loss1[200:]
        a = run(st, build(), cell.config(3)).actions
        b = run(st2, build(), cell.config(3)).actions
        assert np.array_equal(a[:210], b[:210])  # outcomes of round 201 on are released from 211 on


def test_family2_rlaw_beats_no_switch_on_easy_persistent_cell():
    cell = small2(rate=0.005, d=1, budget_frac=0.25, s=0.05)
    law, fam, ns = [], [], []
    for sd in range(6):
        st = fa.make_family2_stream(cell, sd)
        cfg = cell.config(sd)
        law.append(run(st, fa.build_ref_law(cell), cfg).cost / cell.T)
        fam.append(run(st, fa.build_ref_family(cell.T, 0.1, 2), cfg).cost / cell.T)
        ns.append(run(st, build_method("no_switch"), cfg).cost / cell.T)
    assert np.mean(law) < np.mean(ns) - 0.05
    assert np.mean(fam) < np.mean(ns) - 0.01


def test_family2_evaluate_classify_calibrate_isolate_smoke():
    cell = small2(d=5)
    res = fa.evaluate_cell(cell, [0, 1], methods=("no_switch", "episode_front"), kappa=0.1)
    for k in (
        "no_switch",
        "episode_front",
        "ref_law",
        "ref_family",
        "ref_valid",
        "ref_regime_clairvoyant",
    ):
        assert len(res["methods"][k]["cost"]) == 2
    assert set(res["null"]["methods"]) == {"no_switch", "episode_front", "ref_family", "ref_valid"}
    labels = {
        "info_limited",
        "reference_unsafe",
        "shared_failure",
        "cost_of_validity",
        "prior_gap",
        "headroom_not_shared",
        "no_headroom",
    }
    assert fa.classify_cell(res)["label"] in labels
    kappa, info = fa.calibrate_family_kappa([cell, small2(effect="medium")], list(range(6)))
    assert kappa in fa.KAPPA_GRID and info["n_twins"] == 2
    iso = fa.isolate(
        small2(rate=0.02, d=10, budget_frac=0.1, s=0.5),
        [0, 1],
        kappa=kappa,
        axes=("rate", "d", "budget_frac", "s"),
        methods=("no_switch", "episode_front"),
    )
    assert set(iso) == {"rate", "d", "budget_frac", "s"}
    assert fa.isolate(small2(rate=0.002), [0, 1], axes=("rate",), methods=("no_switch",)) == {}


# ------------------------------------------------------------------ Amendment 5: R_valid2


def test_rvalid2_gate_stakes_clipped_and_predictable():
    cfg = small(d=5).config(1)
    gate = fa.valid2_gate(cfg, *fa.family1_start_design(cfg))
    assert gate.adaptive.max_stake < 1.0 and gate.time == 0
    for x in (0.3, -0.2, 0.9, -0.4):
        before = gate.adaptive.predictable_stakes.copy()  # depends on past only
        assert np.all(before >= 0) and np.all(before <= fa.KELLY_ADAPTIVE_MAX_STAKE)
        gate.update(x)
    assert np.isfinite(gate.log_e_value)


def test_rvalid2_family1_validity_on_boundary_null():
    cell = fa.CellSpec(0.6, 1.0, "strong", "harmful", 1, 0.25, 0.1, T=300)
    n = 300
    k = 0
    for sd in range(n):
        rng = np.random.default_rng([sd, 99])
        p_b = (1.0 + cell.h) / 2.0
        st = fa.make_bernoulli_stream(rng, cell.T, (p_b, p_b), path=np.zeros(cell.T, dtype=int))
        k += int(run(st, fa.build_ref_valid2(cell), cell.config(sd)).promotions > 0)
    rate = k / n
    sd_ = (cell.alpha * (1 - cell.alpha) / n) ** 0.5
    print(
        f"R_valid2 family-1 boundary-null any-promotion rate: {rate:.4f} (limit {cell.alpha + 2 * sd_:.4f})"
    )
    assert rate <= cell.alpha + 2 * sd_


def test_rvalid2_family2_validity_on_boundary_null():
    cell = fa.Family2CellSpec(0.005, "strong", "harmful", 1, 0.25, 0.1, T=300)
    n = 200
    rate = _boundary_null_rate_v2(cell, n, 98)
    sd_ = (cell.alpha * (1 - cell.alpha) / n) ** 0.5
    print(f"R_valid2 family-2 boundary-null any-promotion rate: {rate:.4f}")
    assert rate <= cell.alpha + 2 * sd_


def _boundary_null_rate_v2(cell, n_seeds, tag):
    k = 0
    for sd in range(n_seeds):
        rng = np.random.default_rng([sd, tag])
        p_b = (1.0 + cell.h) / 2.0
        st = fa.make_bernoulli_stream(rng, cell.T, (p_b, p_b), path=np.zeros(cell.T, dtype=int))
        k += int(run(st, fa.build_ref_valid2(cell), cell.config(sd)).promotions > 0)
    return k / n_seeds


def test_rvalid2_harmful_off_null_rate_reported():
    # candidate worse than incumbent throughout (P(Y=1)=0.3 => E[-D] < 0): promotions are false
    cell = fa.CellSpec(0.6, 1.0, "strong", "harmful", 1, 0.25, 0.1, T=300)
    n, k = 200, 0
    for sd in range(n):
        st = fa.make_bernoulli_stream(
            np.random.default_rng([sd, 7]), cell.T, (0.3, 0.3), path=np.zeros(cell.T, dtype=int)
        )
        k += int(run(st, fa.build_ref_valid2(cell), cell.config(sd)).promotions > 0)
    print(f"R_valid2 harmful-off null any-promotion rate: {k / n:.4f}")
    assert k / n <= cell.alpha


def test_rvalid2_power_late_onset_strong_and_budget_and_no_peeking():
    cell = fa.CellSpec(0.6, 1.0, "strong", "harmful", 10, 0.25, 0.1, T=300)
    v2, ns = [], []
    for sd in range(8):
        st = fa.make_family1_stream(cell, sd)
        r = run(st, fa.build_ref_valid2(cell), cell.config(sd))
        assert r.queries <= cell.B and r.query_mask[cell.T - cell.d :].sum() == 0
        v2.append(r.cost / cell.T)
        ns.append(run(st, build_method("no_switch"), cell.config(sd)).cost / cell.T)
    assert np.mean(v2) < np.mean(ns) - 0.03
    st = fa.make_family1_stream(cell, 2)
    st2 = fa.Stream(st.loss0.copy(), st.loss1.copy(), st.truth)
    st2.loss0[150:], st2.loss1[150:] = 1.0 - st.loss0[150:], 1.0 - st.loss1[150:]
    a = run(st, fa.build_ref_valid2(cell), cell.config(2)).actions
    b = run(st2, fa.build_ref_valid2(cell), cell.config(2)).actions
    assert np.array_equal(a[:160], b[:160])


def test_evaluate_cell_supports_ref_valid2_and_classify_valid_key():
    cell = small()
    res = fa.evaluate_cell(
        cell, [0, 1], ["no_switch", "episode_front"], ["ref_valid2"], with_null=False
    )
    assert len(res["methods"]["ref_valid2"]["cost"]) == 2
    old = fa.classify_cell(synth(valid=0.10))
    r = synth(valid=0.10)
    r["methods"]["ref_valid2"] = r["methods"].pop("ref_valid")
    assert fa.classify_cell(r, valid_key="ref_valid2")["label"] == old["label"]
