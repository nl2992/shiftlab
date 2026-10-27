import numpy as np
import pandas as pd
import pytest

from scripts.evaluate_hillstrom_policy_development import (
    ARM_CONTROL,
    ARM_MENS,
    ARM_WOMENS,
    EXPECTED_COLUMNS,
    ipw_policy_score,
    make_capacity_policy,
    split_indices,
    validate_frame,
)


def minimal_frame() -> pd.DataFrame:
    rows = []
    for index in range(64_000):
        rows.append(
            {
                "recency": 1,
                "history_segment": "1) $0 - $100",
                "history": 50.0,
                "mens": index % 2,
                "womens": (index + 1) % 2,
                "zip_code": "Urban",
                "newbie": 0,
                "channel": "Web",
                "segment": [ARM_WOMENS, ARM_CONTROL, ARM_MENS][index % 3],
                "visit": 0,
                "conversion": 0,
                "spend": 0.0,
            }
        )
    return pd.DataFrame(rows, columns=EXPECTED_COLUMNS)


def test_hillstrom_source_contract_checks_schema_and_size() -> None:
    validate_frame(minimal_frame())


def test_hillstrom_contract_rejects_wrong_column_order() -> None:
    frame = minimal_frame().rename(columns={"spend": "gross_spend"})
    with pytest.raises(ValueError, match="Unexpected Hillstrom schema"):
        validate_frame(frame)


def test_hillstrom_split_is_disjoint_and_reproducible() -> None:
    first = split_indices(64_000, 20261026)
    second = split_indices(64_000, 20261026)
    assert all(np.array_equal(left, right) for left, right in zip(first, second, strict=True))
    assert tuple(map(len, first)) == (32_000, 12_800, 19_200)
    assert len(np.unique(np.concatenate(first))) == 64_000


def test_capacity_policy_selects_exact_rounded_budget() -> None:
    scores = np.arange(100, dtype=np.float64)
    policy = make_capacity_policy(scores, 0.2)
    assert policy.sum() == 20
    assert np.all(policy[-20:] == 1)
    assert np.all(policy[:-20] == 0)


def test_three_arm_ht_policy_score_uses_only_target_and_control_arms() -> None:
    assignment = np.array([ARM_WOMENS, ARM_CONTROL, ARM_MENS])
    outcome = np.array([2.0, 4.0, 999.0])
    policy = np.array([1.0, 0.0, 1.0])
    score = ipw_policy_score(assignment, outcome, policy)
    np.testing.assert_allclose(score, [6.0, 12.0, 0.0])


def test_randomized_policy_probability_scales_both_arms() -> None:
    assignment = np.array([ARM_WOMENS, ARM_CONTROL, ARM_MENS])
    outcome = np.array([2.0, 4.0, 100.0])
    policy = np.full(3, 0.25)
    score = ipw_policy_score(assignment, outcome, policy)
    np.testing.assert_allclose(score, [1.5, 9.0, 0.0])
