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
    assert set(res["null"]["methods"]) == {"no_switch", "episode_front", "ref_family"}
    assert res["methods"]["no_switch"]["cost"][0] <= 1.0 + 1e-9
    cl = fa.classify_cell(res)
    assert cl["label"] in {
        "info_limited",
        "reference_unsafe",
        "shared_failure",
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


def synth(*, fam=0.10, base=0.20, noise=0.005, law=0.10, floor=0.35, null_fp=0.05, n=20, wide=None):
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
