"""E3 factorial: timeline invariants, rollback parity, oracle isolation, tiny end-to-end."""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from shiftlab.dive import e3_intervention_factorial as e3

SEEDS = (100200200, 100200201)
DOSE_SUBSET = (0.0, 0.6)


@pytest.fixture(scope="module")
def bundles() -> dict[int, e3.StreamBundle]:
    return {seed: e3.build_stream(seed) for seed in SEEDS}


@pytest.fixture(scope="module")
def frame(bundles: dict[int, e3.StreamBundle]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rows.extend(
            e3.run_stream(seed, bundle=bundles[seed], onsets=["before", "at"], doses=DOSE_SUBSET)
        )
    return pd.DataFrame(rows)


def test_row_grid_is_complete(frame: pd.DataFrame) -> None:
    per_seed = 2 * len(e3.COVERAGE_END) * len(e3.ROLLBACKS) * len(DOSE_SUBSET)
    assert len(frame) == len(SEEDS) * per_seed * len(e3.RESPONSES)
    assert (
        frame.groupby(["seed", "onset", "coverage", "rollback", "dose"])
        .size()
        .eq(len(e3.RESPONSES))
        .all()
    )


def test_timeline_indices_follow_the_state_machine(frame: pd.DataFrame) -> None:
    alarmed = frame[frame.alarmed]
    assert len(alarmed) > 0
    assert (alarmed.trigger >= e3.FIT_END).all()
    assert (alarmed.trigger < alarmed.coverage.map(e3.COVERAGE_END)).all()
    revert = alarmed[alarmed.response.isin(["revert", "revert_while_certifying"])]
    assert (revert.revert_start == revert.trigger + 1).all()
    cert = alarmed[alarmed.response.isin(["certify_promote", "revert_while_certifying"])]
    assert (cert.cert_start == cert.trigger + 1).all()
    done = cert[cert.cert_complete >= 0]
    assert (done.cert_complete == done.cert_start + e3.CERT_WINDOW).all()
    deployed = cert[cert.deploy >= 0]
    assert (deployed.deploy >= deployed.cert_complete).all()  # no deployment before completion
    assert deployed.certified.all()
    nothing = frame[~frame.alarmed]
    assert (nothing.expected_net_gain_vs_incumbent == 0).all()
    assert (nothing.switches == 0).all() and (nothing.rollbacks == 0).all()
    plain = frame[frame.response == "continue"]
    assert (plain.expected_net_gain_vs_incumbent == 0).all()
    assert (plain.switches == 0).all()


def test_matched_trigger_across_arms_and_reference_states(frame: pd.DataFrame) -> None:
    keys = ["seed", "onset", "coverage"]
    assert (frame.groupby(keys).trigger.nunique() == 1).all()


def test_revert_while_certifying_matches_revert_and_certify(frame: pd.DataFrame) -> None:
    cells = frame.set_index(["seed", "onset", "coverage", "rollback", "dose", "response"])
    rwc = cells.xs("revert_while_certifying", level="response")
    cert = cells.xs("certify_promote", level="response")
    rev = cells.xs("revert", level="response")
    assert (rwc.cert_complete == cert.cert_complete).all()
    assert (rwc.certified == cert.certified).all()
    assert (rwc.labels_cert == cert.labels_cert).all()
    assert (rwc.revert_start == rev.revert_start).all()
    assert (rev.labels_cert == 0).all()
    deployed = rwc[rwc.deploy >= 0]
    assert (deployed.switches == 2).all()  # revert, then promote
    ctp = cells.xs("certify_promote", level="response")
    assert (ctp[ctp.deploy >= 0].switches == 1).all()


def test_rollback_parity_and_off(frame: pd.DataFrame) -> None:
    off = frame[frame.rollback == "off"]
    assert (off.labels_rollback == 0).all() and (off.rollbacks == 0).all()
    on = frame[(frame.rollback == "parity") & frame.alarmed & (frame.response != "continue")]
    deploys = (on.revert_start >= 0) | (on.deploy >= 0)
    assert (on[deploys].labels_rollback > 0).all()  # every deploying arm carries the monitor
    assert (on[~deploys].labels_rollback == 0).all()  # nothing deployed, nothing monitored
    # rollback labels never exceed the per-arm cap and rolled-back arms paid for it
    assert (on.labels_rollback <= e3.ROLLBACK_LABEL_CAP).all()
    rolled = on[on.rollbacks > 0]
    assert ((rolled.reference_rollback >= 0) | (rolled.candidate_rollback >= 0)).all()
    assert np.allclose(
        on.intervention_cost, e3.SWITCH_COST * on.switches + e3.ROLLBACK_COST * on.rollbacks
    )


def test_label_caps_are_per_stage_and_matched_within_cell(frame: pd.DataFrame) -> None:
    for coverage, group in frame.groupby("coverage"):
        assert (group.labels_q1 <= e3.monitor_label_cap(str(coverage))).all()
        assert (group.labels_total <= e3.total_label_cap(str(coverage))).all()
    assert (frame.labels_cert <= e3.SCOUT_CERT_LABEL_CAP).all()
    keys = ["seed", "onset", "coverage", "rollback", "dose"]
    assert (frame.groupby(keys).labels_q1.nunique() == 1).all()  # same trigger information


def test_reference_deterioration_starts_after_trigger_and_keeps_history(
    bundles: dict[int, e3.StreamBundle],
) -> None:
    bundle = bundles[SEEDS[0]]
    _, incumbent = e3.family_for_onset(bundle, e3.ONSETS["before"])
    y_safe, _ = e3.realised_outcomes(bundle, 0.0, e3.N_EVENTS)
    safe = e3.run_q1_monitor(
        incumbent=incumbent,
        reference=bundle.reference,
        y=y_safe,
        uniforms=bundle.uniforms,
        coverage="short",
    )
    assert safe.trigger is not None
    start = e3.deterioration_start(safe.trigger)
    assert start == safe.trigger + 1
    y_det, oracle = e3.realised_outcomes(bundle, 0.6, start)
    assert np.array_equal(y_det[:start], y_safe[:start])
    assert (y_det[start:] >= y_safe[start:]).all()  # positive shift only adds positives
    rerun = e3.run_q1_monitor(
        incumbent=incumbent,
        reference=bundle.reference,
        y=y_det,
        uniforms=bundle.uniforms,
        coverage="short",
    )
    assert rerun == safe  # identical Q1 history in both reference states
    assert oracle.probability[start:].mean() > bundle.probability_safe[start:].mean()
    assert e3.deterioration_start(None) == e3.N_EVENTS


def test_oracle_never_reaches_learner_functions(bundles: dict[int, e3.StreamBundle]) -> None:
    for fn in (e3.run_q1_monitor, e3.run_certification, e3.run_rollback_monitor, e3.build_timeline):
        names = set(inspect.signature(fn).parameters)
        assert not names & {"oracle", "probability", "probability_true", "p_true", "h_truth"}
    bundle = bundles[SEEDS[0]]
    assert not np.any(bundle.family["h_truth"])  # decoy, not truth
    assert not np.any(bundle.family["h_proxy"])
    # Decisions are invariant to the oracle: poison it and compare every learner-side column.
    clean = pd.DataFrame(
        e3.run_stream(SEEDS[0], bundle=bundle, onsets=["before"], doses=DOSE_SUBSET)
    )
    poison = e3.OracleView(np.full(e3.N_EVENTS, np.nan))
    poisoned = pd.DataFrame(
        e3.run_stream(
            SEEDS[0],
            bundle=bundle,
            onsets=["before"],
            oracle_override=poison,
            doses=DOSE_SUBSET,
        )
    )
    learner_cols = [
        "trigger",
        "revert_start",
        "cert_start",
        "cert_complete",
        "deploy",
        "certified",
        "reference_rollback",
        "candidate_rollback",
        "labels_total",
        "switches",
        "rollbacks",
    ]
    pd.testing.assert_frame_equal(clean[learner_cols], poisoned[learner_cols])
    assert poisoned.expected_net_gain_vs_incumbent.isna().any()  # evaluator did read the oracle


def test_rollback_monitor_fires_on_sustained_harm_and_is_quiet_otherwise() -> None:
    n = e3.N_EVENTS
    incumbent = np.zeros(n, dtype=int)
    deployed = np.ones(n, dtype=int)
    uniforms = np.zeros(n)  # every event queried
    harmful = e3.run_rollback_monitor(
        start=2000,
        end=n,
        deployed=deployed,
        incumbent=incumbent,
        y=np.zeros(n, dtype=int),  # false positives everywhere
        uniforms=uniforms,
        label_cap=160,
    )
    assert harmful.alarm is not None and harmful.alarm >= 2000
    quiet = e3.run_rollback_monitor(
        start=2000,
        end=n,
        deployed=deployed,
        incumbent=incumbent,
        y=np.ones(n, dtype=int),  # deployed policy is right, incumbent wrong
        uniforms=uniforms,
        label_cap=160,
    )
    assert quiet.alarm is None
    assert (
        e3.run_rollback_monitor(
            start=2000,
            end=n,
            deployed=deployed,
            incumbent=incumbent,
            y=np.zeros(n, dtype=int),
            uniforms=uniforms,
            label_cap=0,
        ).processed
        == 0
    )


def test_certification_infeasible_when_window_overruns_horizon(
    bundles: dict[int, e3.StreamBundle],
) -> None:
    bundle = bundles[SEEDS[0]]
    family, _ = e3.family_for_onset(bundle, e3.ONSETS["before"])
    y = (bundle.target > 0).astype(int)
    late = e3.run_certification(
        family=family,
        y=y,
        uniforms=bundle.uniforms,
        promotion_config=bundle.promotion_config,
        start=e3.N_EVENTS - e3.CERT_WINDOW,
        coverage="long",
    )
    assert late is None


def test_registered_levels_are_exact() -> None:
    assert e3.ONSETS == {"before": 800, "at": 1600, "after": 2000}
    assert e3.COVERAGE_END == {"short": 1600, "long": 3200}
    assert e3.ROLLBACKS == ("off", "parity")
    assert e3.RESPONSES == (
        "continue",
        "revert",
        "certify_promote",
        "revert_while_certifying",
        "wait_revert",
    )
    assert e3.DOSES == (0.0, 0.15, 0.3, 0.45, 0.6, 0.8, 1.0)
    assert len(e3.all_cells()) == 84


def test_wait_revert_is_a_matched_wait_without_certification(frame: pd.DataFrame) -> None:
    wait = frame[(frame.response == "wait_revert") & frame.alarmed]
    assert len(wait) > 0
    assert (wait.labels_cert == 0).all() and not wait.certified.any()
    feasible = wait[wait.revert_start >= 0]
    assert (feasible.revert_start == feasible.trigger + 1 + e3.CERT_WINDOW).all()
    assert (feasible.switches == 1).all()
    assert (wait[wait.revert_start < 0].switches == 0).all()


def test_dose_zero_is_safe_and_doses_share_prealarm_history(frame: pd.DataFrame) -> None:
    keys = ["seed", "onset", "coverage", "rollback", "response"]
    assert (frame.groupby(keys).trigger.nunique() == 1).all()  # trigger identical across doses
    zero = frame[frame.dose == 0.0]
    assert (zero.deterioration_start == -1).all()


def test_monitoring_diagnostics_columns(frame: pd.DataFrame) -> None:
    rwc = frame[(frame.response == "revert_while_certifying") & (frame.rollback == "parity")]
    starved = rwc[rwc.candidate_monitor_starved]
    # a starved candidate monitor means the reference monitor spent the whole shared allowance
    assert (starved.reference_monitor_labels >= e3.ROLLBACK_LABEL_CAP).all()
    assert (starved.labels_rollback == starved.reference_monitor_labels).all()
    off = frame[frame.rollback == "off"]
    assert not off.candidate_monitor_starved.any()
    cert = frame[
        frame.response.isin(["certify_promote", "revert_while_certifying"]) & frame.alarmed
    ]
    assert (cert.abstained == (~cert.deployed)).all()
    assert (frame.deployed == (frame.deploy >= 0)).all()
