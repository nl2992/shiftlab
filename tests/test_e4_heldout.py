"""Synthetic-data tests for the E4 runner (scripts/run_e4_heldout.py). No EIA data is read."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from shiftlab.dive import eia_validity_analysis as eva
from shiftlab.dive.eia_paired_reserve import PairedReserveStream
from shiftlab.dive.reserve_costs import paired_cost, reserve_actions

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("run_e4_heldout", ROOT / "scripts/run_e4_heldout.py")
rh = importlib.util.module_from_spec(_spec)
sys.modules["run_e4_heldout"] = rh
_spec.loader.exec_module(rh)


def _stream(ba: str, window: str, n: int, seed: int, procure: bool = True) -> PairedReserveStream:
    rng = np.random.default_rng(seed)
    margin = rng.normal(size=n) * 2 if procure else -np.abs(rng.normal(size=n)) - 1
    ref_pred = margin + rng.normal(size=n) * 1.5
    demand = margin + rng.normal(size=n)
    da, ra = reserve_actions(margin, 0.0), reserve_actions(ref_pred, 0.0)
    return PairedReserveStream(
        respondent=ba,
        window=window,
        event_time=3600.0 * np.arange(n) + 1.7e9,
        x=np.zeros((n, 4)),
        demand=demand,
        tau=0.0,
        deployed_prediction=margin,
        reference_prediction=ref_pred,
        deployed_action=da,
        reference_action=ra,
        paired_cost=paired_cost(da, ra, demand, 0.0),
        disagreement=da != ra,
        frozen_margin=margin,
    )


def _builder(procure: bool = True):
    def build(series, ba, device):
        return [
            _stream(ba, "rehearsal_2024", 300, 1, procure),
            _stream(ba, "2025", 150, 2, procure),
            _stream(ba, "2026", 150, 3, procure),
        ]

    return build


@pytest.fixture
def restore_coins(monkeypatch):
    for name in rh.REPLACED_NAMES + ("rerun_coins",):
        monkeypatch.setattr(eva, name, getattr(eva, name))


# ---- coin replacement ---------------------------------------------------------------------
def test_coin_replacement_changes_exactly_three_names_with_registered_seeds(restore_coins):
    before = dict(vars(eva))
    names = rh.install_e4_coins()
    changed = {k for k, v in vars(eva).items() if before.get(k) is not v}
    assert changed == set(rh.REPLACED_NAMES) == set(names)
    k, n, reps = 3, 20, 5
    signs, uniforms = eva.orientation_coins(k, n, reps)
    rng = np.random.default_rng(100400000 + 1 + k)
    assert np.array_equal(signs, 2 * rng.integers(0, 2, size=(reps, n)) - 1)
    assert np.array_equal(uniforms, rng.random((reps, n)))
    assert np.array_equal(
        eva.unmodified_coins(k, n, reps), np.random.default_rng(100400111 + k).random((reps, n))
    )
    for o in range(3):
        assert np.array_equal(
            eva.injection_coins(k, o, n, reps),
            np.random.default_rng(100400221 + 3 * k + o).random((reps, n)),
        )
    # the WP4 stream for the same index differs
    assert not np.array_equal(uniforms, np.random.default_rng(59200000 + k).random((reps, n)))


def test_coin_seeds_stay_inside_registered_block_and_do_not_collide(restore_coins):
    seeds = []
    for k in range(rh.MAX_PATHS):
        seeds.append(rh.SEED_NULL + k)
        seeds.append(rh.SEED_UNMOD + k)
        seeds.extend(rh.SEED_INJ + 3 * k + o for o in range(3))
    assert len(seeds) == len(set(seeds))
    assert min(seeds) >= 100400001 and max(seeds) <= 100400999
    with pytest.raises(ValueError):
        rh.e4_orientation_coins(rh.MAX_PATHS, 5, 2)
    with pytest.raises(ValueError):
        rh.e4_injection_coins(0, 3, 5, 2)


def test_null_loop_never_uses_the_unadjusted_rerun(restore_coins, monkeypatch):
    rh.install_e4_coins()

    def boom(*a, **k):
        raise AssertionError("rerun coins must not be used")

    monkeypatch.setattr(eva, "rerun_coins", boom)
    path = eva.PathData(0, _stream("AAA", "2025", 150, 2), _stream("AAA", "rehearsal_2024", 300, 1))
    df = rh.e4_null_analysis([path], 40)
    assert len(df) == 17 * 2 and set(df["stage"]) == {"fixed"}
    assert set(df["replicates"]) == {40}
    again = rh.e4_null_analysis([path], 40)
    assert df["alarms"].tolist() == again["alarms"].tolist()


# ---- Bonferroni family and fixed replication count -----------------------------------------
def test_replication_count_certifies_zero_alarms_at_the_largest_family():
    m = rh.MAX_FAMILY_CELLS
    assert m == 714
    need = rh.min_zero_alarm_replicates(m)
    level = 1 - 0.05 / m
    assert eva.clopper_pearson_upper(0, need, level) <= 0.05
    assert eva.clopper_pearson_upper(0, need - 1, level) > 0.05
    assert need <= rh.REPLICATES["null"]


def _null_df(m_paths: int, alarms: int, reps: int, d: int = 100) -> pd.DataFrame:
    rows = []
    for k in range(m_paths):
        for arm, budget in eva.registered_cells():
            for eps in (0.1, 0.0):
                rows.append(
                    {
                        "path": k,
                        "arm": arm,
                        "budget": np.nan if budget is None else budget,
                        "epsilon": eps,
                        "replicates": reps,
                        "alarms": alarms,
                        "disagreements": d,
                        "mean_labels": 10.0,
                        "expected_queried_disagreements": 50.0,
                    }
                )
    return pd.DataFrame(rows)


def test_bonferroni_family_size_is_enforced_and_codex_example_is_not_skipped():
    df = _null_df(42, 30, 1000)  # 714 primary cells
    summary = rh.null_summary(df, 714, 1000)
    assert summary["m_family"] == 714 and summary["n_cells"] == 714
    assert summary["level"] == pytest.approx(1 - 0.05 / 714)
    # 30/1000 passes an unadjusted 95% bound but is insufficient at m = 714; no re-run exists
    assert eva.clopper_pearson_upper(30, 1000) <= 0.05
    assert not summary["cells"]["passes"].any()
    assert summary["cells"]["point_exceeds_alpha"].sum() == 0  # 3% is not above alpha
    assert rh.null_summary(_null_df(42, 25, 1000), 714, 1000)["all_validated"]
    with pytest.raises(ValueError, match="family size"):
        rh.null_summary(df, 700, 1000)
    with pytest.raises(ValueError, match="cannot certify"):
        rh.null_summary(_null_df(42, 0, 100), 714, 100)


# ---- verdicts ------------------------------------------------------------------------------
def _cells(paths, arm="gated_ht_fixed", passes=True, informative=True):
    return pd.DataFrame(
        [
            {
                "path": k,
                "arm": arm,
                "budget": 0.2,
                "informative": informative,
                "passes": passes,
                "point_exceeds_alpha": False,
            }
            for k in paths
        ]
    )


def test_arm_support_verdicts():
    six_paths_three_authorities = [0, 1, 2, 3, 4, 5]
    assert rh.arm_states(_cells(six_paths_three_authorities))["gated_ht_fixed"]["state"] == (
        "SUPPORTED"
    )
    # five paths, or only two authorities: stays INCONCLUSIVE
    assert rh.arm_states(_cells([0, 1, 2, 3, 4]))["gated_ht_fixed"]["state"] == "INCONCLUSIVE"
    assert (
        rh.arm_states(_cells([0, 1, 2, 3, 4, 5, 6, 7][:4] * 1))["gated_ht_fixed"]["state"]
        == "INCONCLUSIVE"
    )
    assert (
        rh.arm_states(_cells([0, 1, 2, 3, 4, 5], informative=False))["gated_ht_fixed"]["state"]
        == "INCONCLUSIVE"
    )
    failing = rh.arm_states(_cells(six_paths_three_authorities, passes=False))
    assert failing["gated_ht_fixed"]["state"] == "NOT_VALIDATED"
    assert rh.arm_states(pd.DataFrame()) == {}


def _path(k: int, rehearsal_rate: float):
    dis = np.zeros(1000, dtype=bool)
    dis[: int(rehearsal_rate * 1000)] = True
    return SimpleNamespace(
        k=k,
        validation_disagreement=dis,
        validation_tariffs=np.ones(1000),
    )


def _injected(ks, match: bool):
    rows = []
    for k in ks:
        for f in (0.25, 0.5):
            rows.append(
                {
                    "path": k,
                    "onset_fraction": f,
                    "arm": "full_feedback",
                    "budget": np.nan,
                    "detection_rate": 1.0,
                    "median_delay_events": 100.0,
                    "median_delay_hours": 100.0,
                }
            )
            for r in (0.05, 0.10, 0.20):
                rows.append(
                    {
                        "path": k,
                        "onset_fraction": f,
                        "arm": "gated_ht_fixed",
                        "budget": r,
                        "detection_rate": 1.0,
                        "median_delay_events": 100.0 if match else 140.0,
                        "median_delay_hours": 100.0 if match else 140.0,
                    }
                )
    return pd.DataFrame(rows)


def test_hb4b_is_stratified_and_q_equal_one_cells_cannot_support():
    ks = [0, 2, 4]  # three authorities
    structural = [_path(k, 0.001) for k in ks]  # rehearsal rate tiny -> fixed q = 1
    out = rh.injected_summary(_injected(ks, True), structural)
    assert set(out["strata"]) == {"q_eq_1_structural"}
    assert out["strata"]["q_eq_1_structural"]["match_exact_events"] == 1.0
    assert out["state"] == "INCONCLUSIVE"  # perfect matching at q = 1 is not support
    informative = [_path(k, 0.5) for k in ks]  # fixed q = r/0.5 < 1
    supported = rh.injected_summary(_injected(ks, True), informative)
    assert set(supported["strata"]) == {"q_lt_1"}
    assert supported["strata"]["q_lt_1"]["n_cells"] == 18 and supported["state"] == "SUPPORTED"
    assert rh.injected_summary(_injected(ks, False), informative)["state"] == "WITHDRAWN"
    few = rh.injected_summary(_injected([0], True), [_path(0, 0.5)])
    assert few["state"] == "INCONCLUSIVE"  # too few cells and authorities
    assert rh.injected_summary(pd.DataFrame(), [])["state"] == "INCONCLUSIVE"


# ---- empty paths and a full synthetic run --------------------------------------------------
def test_all_authorities_failing_r20_gives_empty_but_recorded_result(tmp_path, restore_coins):
    out = tmp_path / "res"
    result = rh.run_authorities(
        ["AAA", "BBB"],
        ["AAA", "BBB"],
        out,
        rh.REPLICATES,
        reader=lambda a: {},
        builder=_builder(procure=False),
        wp4_check=lambda: True,
        region_of={},
    )
    assert result["paths"] == [] and "null_summary" not in result
    assert all(not v["passes_R20"] for v in result["r20"].values())
    summary = rh.write_outputs(result, out, {"mode": "test"})
    assert summary["n_paths"] == 0 and set(summary["r20"]) == {"AAA", "BBB"}
    assert (out / "summary.json").is_file()


def test_full_synthetic_run_retains_r20_failures_and_computes_family(tmp_path, restore_coins):
    def build(series, ba, device):
        return _builder(procure=ba != "BBB")(series, ba, device)

    out = tmp_path / "res"
    reps = {"null": 200, "unmodified": 3, "injected": 3}
    result = rh.run_authorities(
        ["AAA", "BBB"],
        ["AAA", "BBB"],
        out,
        reps,
        reader=lambda a: {},
        builder=build,
        wp4_check=lambda: True,
        region_of={"AAA": "NW", "BBB": "NW"},
    )
    assert result["r20"]["BBB"]["passes_R20"] is False  # retained, not replaced
    assert [p.k for p in result["paths"]] == [0, 1]  # AAA has rank 0
    assert result["null_summary"]["m_family"] == 34
    summary = rh.write_outputs(result, out, {"mode": "test"})
    assert "arm_states" in summary["null"] and summary["hb4b"]["state"]
    assert set(summary["regions"]["per_authority"]) == {"AAA"}
    assert summary["regions"]["region_map_unverified"] is True
    with pytest.raises(FileExistsError):
        rh.run_authorities(
            ["AAA"],
            ["AAA"],
            out,
            reps,
            reader=lambda a: {},
            builder=_builder(),
            wp4_check=lambda: True,
        )


# ---- one-opening guard ---------------------------------------------------------------------
def test_acquire_opening_is_atomic(tmp_path):
    results = []

    def attempt(i):
        try:
            rh.acquire_opening(tmp_path / "locked", {"i": i})
            results.append("ok")
        except FileExistsError:
            results.append("exists")

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count("ok") == 1 and results.count("exists") == 7


def _fake_freeze(tmp_path, files):
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps({"sha256": dict.fromkeys(files, "x")}), encoding="utf-8")
    return path


ELIG = {
    "eligible": ["AAA", "BBB", "CCC"],
    "split": {"locked": ["BBB", "CCC"], "development": ["AAA"]},
}


def test_locked_mode_refuses_without_valid_freeze_and_creates_no_marker(tmp_path):
    called = []
    with pytest.raises(FileNotFoundError):
        rh.run_locked(
            freeze_path=tmp_path / "missing.json",
            out_root=tmp_path / "out",
            eligibility=ELIG,
            reader=lambda a: called.append(a),
        )
    assert not (tmp_path / "out" / "locked").exists() and not called


def test_locked_mode_refuses_when_required_files_are_not_frozen(tmp_path, monkeypatch):
    freeze_path = _fake_freeze(tmp_path, ["only/one.py"])
    monkeypatch.setattr(rh.freeze, "require_freeze", lambda p, r: json.loads(p.read_text()))
    with pytest.raises(RuntimeError, match="required files"):
        rh.run_locked(freeze_path=freeze_path, out_root=tmp_path / "out", eligibility=ELIG)
    assert not (tmp_path / "out" / "locked").exists()


def test_locked_mode_opens_once_and_marker_precedes_any_read(tmp_path, monkeypatch, restore_coins):
    freeze_path = _fake_freeze(tmp_path, list(rh.REQUIRED_FROZEN))
    monkeypatch.setattr(rh.freeze, "require_freeze", lambda p, r: json.loads(p.read_text()))
    out_root = tmp_path / "out"
    seen = []

    def reader(authorities):
        marker = out_root / "locked" / "opened.json"
        seen.append((list(authorities), marker.is_file()))
        return {}

    kwargs = {
        "freeze_path": freeze_path,
        "out_root": out_root,
        "eligibility": ELIG,
        "reader": reader,
        "builder": _builder(procure=False),
        "wp4_check": lambda: True,
        "region_of": {},
    }
    summary = rh.run_locked(**kwargs)
    assert seen == [(["BBB", "CCC"], True)]  # marker existed when the first read happened
    marker = json.loads((out_root / "locked" / "opened.json").read_text())
    assert marker["opened_utc"].endswith("+00:00") and len(marker["git_head"]) == 40
    assert marker["n_locked_authorities"] == 2
    assert summary["mode"] == "locked" and set(summary["r20"]) == {"BBB", "CCC"}
    with pytest.raises(RuntimeError, match="already opened"):
        rh.run_locked(**kwargs)
    assert len(seen) == 1  # the second attempt read nothing


def test_smoke_refuses_locked_authority_before_reading(monkeypatch):
    monkeypatch.setattr(rh.elig, "load_eligibility", lambda: ELIG)
    monkeypatch.setattr(rh, "read_series", lambda a: pytest.fail("must not read"))
    with pytest.raises(SystemExit, match="LOCKED"):
        rh.smoke("BBB", rh.REPLICATES)
    with pytest.raises(SystemExit, match="not in the development"):
        rh.smoke("ZZZ", rh.REPLICATES)


def test_freeze_list_covers_runner_and_imported_modules():
    files = rh.effective_program_files()
    for needed in (
        "scripts/run_e4_heldout.py",
        "scripts/e4_eligibility.py",
        "scripts/audit_eia_2026_holdout_readiness.py",
        "scripts/evaluate_eia_retraining_frontier.py",
        "src/shiftlab/dive/eia_validity_analysis.py",
        "src/shiftlab/dive/orientation_replay.py",
        "src/shiftlab/dive/gated_monitor_comparison.py",
        "src/shiftlab/dive/eprocess.py",
        "src/shiftlab/freeze.py",
        "docs/research_refinement_v1/stage1/e4_region_map.json",
        "docs/eia_real_data_validity_freeze.json",
    ):
        assert needed in files
    assert set(rh.REQUIRED_FROZEN) <= set(files)


# ---- information over the processed prefix only ---------------------------------------------
def _late_disagreement_path(n: int = 400, late: int = 100):
    import dataclasses

    base = _stream("AAA", "2025", n, 2)
    dis = np.zeros(n, dtype=bool)
    dis[-late:] = True
    z = np.where(dis, np.where(np.arange(n) % 2 == 0, 1.0, -1.0), 0.0)
    stream = dataclasses.replace(base, disagreement=dis, paired_cost=z)
    return eva.PathData(0, stream, _stream("AAA", "rehearsal_2024", 300, 1))


def test_information_ignores_disagreements_after_reserve_exhaustion(restore_coins):
    rh.install_e4_coins()
    p = _late_disagreement_path()
    reps = 200
    signs, uniforms = eva.orientation_coins(p.k, p.n, reps)
    batch = eva._replay(
        p,
        "ungated_ht",
        0.02,
        paired_cost=p.stream.paired_cost,
        disagreement=p.stream.disagreement,
        signs=signs,
        uniforms=uniforms,
        epsilon=0.1,
    )
    # the reserve (0.02 * 400 = 8 tariff units) is spent long before the late disagreements
    assert batch.processed.mean() < 0.9 * p.n
    naive = 0.02 * 100  # the old full-path figure
    info = rh.cell_information(p, "ungated_ht", 0.02, batch.processed)
    alive = (batch.processed[:, None] > np.arange(p.n)[None, :]).mean(axis=0)
    assert info == pytest.approx(0.02 * alive[-100:].sum())
    assert info < 0.5 * naive
    assert rh.cell_information(p, "full_feedback", None, np.full(reps, p.n)) == 100.0
    # a path with no exhaustion keeps the full figure
    assert rh.cell_information(p, "ungated_ht", 0.02, np.full(reps, p.n)) == pytest.approx(naive)
    # the screen: the same path is not informative for the exhausted cell
    df = rh.e4_null_analysis([p], 60)
    row = df[(df.arm == "ungated_ht") & (df.budget == 0.02) & (df.epsilon == 0.1)].iloc[0]
    assert row["expected_queried_disagreements"] < rh.MIN_EXPECTED_QUERIED
