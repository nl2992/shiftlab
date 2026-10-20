from shiftlab.data.report import _readiness_labels


def test_registered_real_forecast_task_is_not_reported_as_missing_a_task():
    paper1, paper2, paper3 = _readiness_labels(
        "eia",
        False,
        False,
        [{"task_kind": "regression", "label_availability_rule": "unknown"}],
    )
    assert paper1 == "retrospective; utility imposed"
    assert paper2 == "retrospective forecast/conformal task; availability unknown"
    assert paper3 == "retrospective task; release-time protocol unknown"


def test_coarse_classification_domains_are_not_misrepresented_as_online_streams():
    _, paper2, paper3 = _readiness_labels("gas_sensor", False, True, [])
    assert paper2 == "classification prediction-set protocol required"
    assert paper3 == "offline domain benchmark; release times unavailable"


def test_synthetic_streams_remain_available_for_all_three_research_tracks():
    assert _readiness_labels("concept", True, False, []) == (
        "controlled decision study",
        "regression/classification stream",
        "stream ready",
    )


def test_legacy_monash_manifest_uses_registered_horizon_without_claiming_online_availability():
    _, paper2, paper3 = _readiness_labels("monash", False, False, [], {"dataset": "m4_weekly"})
    assert paper2 == "retrospective forecast/conformal task; availability unknown"
    assert paper3 == "retrospective task; release-time protocol unknown"
