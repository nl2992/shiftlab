import dataclasses
import importlib.util
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

import shiftlab.dive.e2_acquisition_pacing as e2

ROOT = Path(__file__).resolve().parents[1]


def _load_analysis():
    spec = importlib.util.spec_from_file_location("analyze_e2", ROOT / "scripts" / "analyze_e2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["analyze_e2"] = module
    spec.loader.exec_module(module)
    return module


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_e2_acquisition_pacing", ROOT / "scripts" / "run_e2_acquisition_pacing.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_e2_acquisition_pacing"] = module
    spec.loader.exec_module(module)
    return module


def _uniform_inputs(z, coins, rate, disagreement=None):
    n = len(z)
    return e2.MonitorInputs(
        x=np.zeros((n, 2)),
        paired_cost=np.asarray(z, dtype=float),
        disagreement=np.asarray(z != 0 if disagreement is None else disagreement),
        tariffs=np.ones(n),
        uniforms=coins,
        validation_disagreement=np.arange(200) % 10 == 0,
        validation_tariffs=np.ones(200),
        proxy=None,  # type: ignore[arg-type]
        budget_rate=rate,
    )


def test_harmless_burst_has_null_paired_cost_mean():
    cell = e2.CELLS["b2_ii"]
    burst_means, sample_means = [], []
    for seed in e2.cell_seeds("dev", "b2_ii", 12):
        s = e2.build_stream(cell, seed)
        start, end, label = s.oracle.regimes[0]
        assert label == "harmless_burst"
        window = slice(start, end)
        burst_means.append(float(s.oracle.expected_cost[window].mean()))
        sample_means.append(float(s.monitor.paired_cost[window].mean()))
        # the harmless burst is not material; onset is the late harm regime
        assert s.oracle.onset == s.oracle.regimes[1][0]
        assert s.oracle.onset > end
        assert s.oracle.weight[window].max() == 0.0
    assert max(burst_means) <= e2.EPSILON
    assert np.mean(sample_means) <= e2.EPSILON + 0.05  # Monte Carlo noise of 12 x 400 events


def test_harmful_regimes_exceed_epsilon():
    for name in ("b2_i", "b2_iii", "b1_r0.05"):
        s = e2.build_stream(e2.CELLS[name], e2.cell_seeds("dev", name, 1)[0])
        assert s.oracle.onset is not None
        post = s.oracle.expected_cost[s.oracle.onset : s.oracle.onset + 200]
        assert post.mean() > e2.EPSILON


def test_bursts_raise_disagreement_rate():
    s = e2.build_stream(e2.CELLS["b2_ii"], e2.cell_seeds("dev", "b2_ii", 1)[0])
    start, end, _ = s.oracle.regimes[0]
    assert s.monitor.disagreement[start:end].mean() > 3 * s.monitor.disagreement[:start].mean()


def test_seed_blocks_are_disjoint_and_inside_registry():
    registry = yaml.safe_load((ROOT / "configs" / "seed_registry.yaml").read_text("utf-8"))
    entries = {b["id"]: b for b in registry["studies"]}
    order = [*e2.CONFIRMATION_CORE, *[c.name for c in e2.GRID_CELLS[:7]]]
    spans = {
        "dev": [e2.cell_seed_range("dev", c.name) for c in e2.ALL_CELLS],
        "grid": [e2.cell_seed_range("grid", c.name) for c in e2.GRID_CELLS],
        "confirmation": [e2.cell_seed_range("confirmation", name, order) for name in order],
    }
    for block, spec in e2.SEED_BLOCKS.items():
        reg = entries[spec["id"]]
        assert (reg["start"], reg["end"]) == (spec["start"], spec["end"])
        ranges = sorted(spans[block])
        assert ranges[0][0] >= spec["start"] and ranges[-1][1] <= spec["end"]
        for (_, hi), (lo, _) in itertools.pairwise(ranges):
            assert hi < lo
    blocks = [(v["start"], v["end"]) for v in e2.SEED_BLOCKS.values()]
    for (_, hi), (lo, _) in itertools.pairwise(sorted(blocks)):
        assert hi < lo
    with pytest.raises(ValueError):
        e2.cell_seeds("dev", "b2_i", 251)
    with pytest.raises(ValueError):
        e2.cell_seed_range("confirmation", "b1_r0.02")  # needs the locked order


def test_horizon_baseline_is_predictable_bounded_and_protects_reserve():
    cell = e2.CELLS["g_ii_s1.5_r0.05_L200"]
    s = e2.build_stream(cell, e2.cell_seeds("grid", cell.name, 1)[0])
    h = e2.replay_gated_horizon(m=s.monitor)
    assert np.all(np.abs(h.increments) <= h.bounds)
    assert h.dollars <= h.budget
    # q depends on past spend only: altering the cost of an event that is never queried is inert
    spend_first = h.queried.copy()
    again = e2.replay_gated_horizon(
        m=dataclasses.replace(s.monitor, paired_cost=s.monitor.paired_cost + 0.0)
    )
    np.testing.assert_array_equal(spend_first, again.queried)
    fixed = e2.replay_gated(
        arm="gated_ht_fixed",
        x=s.monitor.x,
        paired_cost=s.monitor.paired_cost,
        disagreement=s.monitor.disagreement,
        tariffs=s.monitor.tariffs,
        uniforms=s.monitor.uniforms,
        validation_disagreement=s.monitor.validation_disagreement,
        validation_tariffs=s.monitor.validation_tariffs,
        budget_rate=s.monitor.budget_rate,
    )
    assert len(h.queried) >= len(fixed.queried)  # survives at least as long as the fixed arm


def test_row_expenditure_and_reserve_columns():
    cell = e2.CELLS["g_ii_s1.5_r0.1_L300"]
    stream = e2.build_stream(cell, e2.cell_seeds("grid", cell.name, 1)[0])
    rows = e2.run_arms(stream, cell.arms, ("fixed08",))
    assert [r["arm"] for r in rows] == list(e2.GATED_ARMS_E2)
    for r in rows:
        assert r["dollars_pre_onset"] + r["dollars_post_onset"] == pytest.approx(r["dollars"])
        assert 0 <= r["reserve_used_frac_pre_onset"] <= 1 + 1e-9


def _fake_rows(cells, seeds, arms=("gated_ht_fixed", "gated_ht_paced"), engine="fixed08"):
    out = []
    for cell in cells:
        for seed in seeds:
            for arm in arms:
                out.append(
                    {
                        "cell": cell,
                        "seed": seed,
                        "arm": arm,
                        "engine": engine,
                        "onset": 100,
                        "first_alarm": 150,
                        "detected": True,
                        "false_alarm_pre_onset": False,
                        "labels_to_alarm_or_horizon": 10,
                        "dollars": 5.0,
                    }
                )
    return pd.DataFrame(out)


def test_analysis_rejects_duplicates_ragged_nan_and_wrong_seeds():
    an = _load_analysis()
    good = _fake_rows(["c"], [1, 2, 3])
    an.validate_rows(good, {"c": [1, 2, 3]})
    with pytest.raises(ValueError, match="duplicate"):
        an.validate_rows(pd.concat([good, good.iloc[:1]]))
    with pytest.raises(ValueError, match="incomplete"):
        an.validate_rows(good.drop(good.index[0]))
    nan = good.copy()
    nan["dollars"] = nan["dollars"].astype(float)
    nan.loc[nan.index[0], "dollars"] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        an.validate_rows(nan)
    with pytest.raises(ValueError, match="seeds differ"):
        an.validate_rows(good, {"c": [1, 2, 4]})
    with pytest.raises(ValueError, match="cells differ"):
        an.validate_rows(good, {"c": [1, 2, 3], "d": [1]})
    # pairing helper refuses to drop unpaired streams or take duplicate first values
    with pytest.raises(ValueError):
        an.paired_table(good.drop(good.index[0]), "c", "gated_ht_fixed", "gated_ht_paced")
    with pytest.raises(ValueError):
        an.paired_table(pd.concat([good, good.iloc[:1]]), "c", "gated_ht_fixed", "gated_ht_paced")


def test_grid_selection_rules_on_synthetic_rows():
    an = _load_analysis()
    rng = np.random.default_rng(0)
    names = {
        "g_i_mid": ("i", 0.5, 0.7),  # paced detection 0.5: eligible
        "g_i_high": ("i", 0.97, 0.99),  # ceiling: not eligible
        "g_iii_high": ("iii", 0.98, 0.99),  # no eligible iii cell -> uninformative
        "g_ii_partial": ("ii", 0.95, 0.1),  # fixed mostly detects only 10%: exhaustion band B
    }
    rows = []
    for cell, (tag, p_paced, p_fixed) in names.items():
        for seed in range(100):
            for arm, p in (
                ("gated_ht_paced", p_paced),
                ("gated_ht_fixed", p_fixed),
                ("gated_ht_horizon", p_paced),
            ):
                exhausted = tag == "ii" and rng.random() < 0.5
                rows.append(
                    {
                        "cell": cell,
                        "seed": seed,
                        "arm": arm,
                        "engine": "fixed08",
                        "onset": 100,
                        "first_alarm": 150,
                        "detected": bool(rng.random() < p),
                        "false_alarm_pre_onset": False,
                        "labels_to_alarm_or_horizon": 10,
                        "dollars": 5.0,
                        "reserve_exhausted_before_onset": exhausted
                        if arm == "gated_ht_fixed"
                        else False,
                        "reserve_used_frac_pre_onset": 0.3,
                    }
                )
    grid = pd.DataFrame(rows)
    dev = _fake_rows(["b1_r0.02", "b1_r0.05"], range(50), ("gated_ht_paced", "uniform_ht"))
    dev.loc[dev.arm == "uniform_ht", "detected"] = False
    locked = an.select_grid(grid, dev)
    cells = {t["cell"]: t for t in locked["h_b2"]}
    assert "g_i_mid" in cells and "g_i_high" not in cells
    assert "iii" in locked["uninformative"]
    assert cells["g_ii_partial"]["type"] == "superior"
    assert all(an.FLOOR_N <= t["n"] <= an.CEIL_N for t in locked["h_b2"])
    assert locked["order"][: len(an.CORE_NAMES)] == list(an.CORE_NAMES)
    assert set(locked["n"]) == set(locked["order"])


def test_confirmation_runner_checks_freeze_before_any_seed(tmp_path, monkeypatch):
    runner = _load_runner()

    def forbidden(*_a, **_k):
        raise AssertionError("a confirmation seed was generated before the freeze check")

    monkeypatch.setattr(runner.e2, "cell_seeds", forbidden)
    monkeypatch.setattr(runner.e2, "run_stream", forbidden)
    bogus = tmp_path / "freeze.json"
    bogus.write_text('{"sha256": {"README.md": "' + "0" * 64 + '"}}', encoding="utf-8")
    monkeypatch.setattr(runner, "FREEZE_RECORD", bogus)
    with pytest.raises(RuntimeError, match="freeze check failed"):
        runner.main(["--block", "confirmation", "--out", str(tmp_path / "out")])
    monkeypatch.setattr(runner, "FREEZE_RECORD", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        runner.main(["--block", "confirmation", "--out", str(tmp_path / "out")])


def test_uniform_ht_is_unbiased_and_ignores_disagreement():
    z = np.where(np.arange(400) % 7 == 0, 5.0, -1.0)
    z[::3] = 0.0
    q = 0.2
    # exact conditional expectation over the coin: E[V] = Z - eps for every event
    for value in (-1.0, 0.0, 5.0):
        queried = e2.gated_increment(
            disagreement=True, observed_cost=value, propensity=q, epsilon=e2.EPSILON
        )
        missed = e2.gated_increment(
            disagreement=True, observed_cost=None, propensity=q, epsilon=e2.EPSILON
        )
        assert q * queried + (1 - q) * missed == pytest.approx(value - e2.EPSILON)
    # Monte Carlo over coins on a fixed cost sequence (budget cap not reached early)
    errors = []
    for rep in range(300):
        coins = np.random.default_rng(rep).random(400)
        r = e2.replay_uniform(arm="uniform_ht", m=_uniform_inputs(z, coins, q))
        k = len(r.increments)
        errors.append(r.increments - (z[:k] - e2.EPSILON))
    assert abs(np.concatenate(errors).mean()) < 0.1
    # flipping the disagreement flags changes nothing: the indicator is not used
    coins = np.random.default_rng(3).random(400)
    a = e2.replay_uniform(arm="uniform_ht", m=_uniform_inputs(z, coins, q))
    b = e2.replay_uniform(arm="uniform_ht", m=_uniform_inputs(z, coins, q, z == 0))
    np.testing.assert_array_equal(a.increments, b.increments)
    np.testing.assert_array_equal(a.queried, b.queried)
    assert np.all(np.abs(a.increments) <= a.bounds)
    assert a.bounds[0] == pytest.approx(5 / q + e2.EPSILON)


def test_uniform_ht_spends_on_agreements():
    n = 400
    base = _uniform_inputs(np.zeros(n), np.random.default_rng(0).random(n), 0.25)
    assert not base.disagreement.any()  # every event is an agreement
    r = e2.replay_uniform(arm="uniform_ht", m=base)
    assert r.queried.sum() > 0  # labels are bought on agreements
    assert r.dollars == pytest.approx(r.queried.sum())
    assert r.dollars <= r.budget
    gated = e2.replay_gated(
        arm="gated_ht_fixed",
        x=base.x,
        paired_cost=base.paired_cost,
        disagreement=base.disagreement,
        tariffs=base.tariffs,
        uniforms=base.uniforms,
        validation_disagreement=base.validation_disagreement,
        validation_tariffs=base.validation_tariffs,
        budget_rate=0.25,
    )
    assert gated.queried.sum() == 0  # the gated arm buys nothing on the same stream


def test_end_to_end_tiny_run_and_oracle_separation():
    seed = e2.cell_seeds("dev", "b2_ii", 1)[0]
    cell = e2.CELLS["b2_ii"]
    stream = e2.build_stream(cell, seed)
    rows = e2.run_arms(stream, cell.arms, ("fixed08",))
    assert len(rows) == len(cell.arms)
    needed = {
        "cell",
        "seed",
        "arm",
        "engine",
        "onset",
        "first_alarm",
        "detected",
        "false_alarm_pre_onset",
        "labels_spent",
        "labels_to_alarm_or_horizon",
        "dollars",
    }
    assert needed <= set(rows[0])
    assert all(r["dollars"] <= r["budget"] + 1e-9 for r in rows)
    # scramble every oracle quantity: alarms, labels and dollars cannot change
    rng = np.random.default_rng(0)
    n = len(stream.oracle.weight)
    scrambled = dataclasses.replace(
        stream,
        oracle=dataclasses.replace(
            stream.oracle,
            weight=rng.random(n),
            expected_cost=rng.normal(size=n),
            burst=~stream.oracle.burst,
        ),
    )
    again = e2.run_arms(scrambled, cell.arms, ("fixed08",))
    for a, b in zip(rows, again, strict=True):
        assert (a["first_alarm"], a["labels_spent"], a["dollars"]) == (
            b["first_alarm"],
            b["labels_spent"],
            b["dollars"],
        )
    assert not any(f.name == "oracle" for f in dataclasses.fields(e2.MonitorInputs))


def test_registered_test_helpers():
    an = _load_analysis()
    assert an.mcnemar_exact_p(7, 0) == pytest.approx(0.5**7)
    assert an.mcnemar_exact_p(0, 0) == 1.0
    assert an.holm({"a": 0.001, "b": 0.02}, 0.025) == {"a": True, "b": True}
    assert an.holm({"a": 0.02, "b": 0.02}, 0.025) == {"a": False, "b": False}
    assert an.newcombe_lower(50, 0, 0, 50, 0.025) > an.MARGIN
    assert an.newcombe_lower(50, 0, 40, 10, 0.025) < an.MARGIN
    assert an.ni_pvalue(50, 0, 0, 50) < 0.025
    assert an.ni_pvalue(50, 0, 40, 10) > 0.025
    assert an.mcnemar_power(30, 1.0, 0.7, 0.0125) > 0.99
