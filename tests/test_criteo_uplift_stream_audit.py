"""Behavioral checks for the no-row-output Criteo source audit parser."""

import pytest

from scripts.audit_criteo_uplift_stream import EXPECTED_COLUMNS, parse_data_row


def test_parse_criteo_uplift_record_with_binary_assignment_and_outcomes() -> None:
    row = ["0.25"] * 12 + ["1", "0", "1", "1"]

    parsed = parse_data_row(row, 1)

    assert len(parsed) == len(EXPECTED_COLUMNS)
    assert parsed[12:] == [1.0, 0.0, 1.0, 1.0]


def test_rejects_malformed_record_width_without_echoing_values() -> None:
    row = ["0.25"] * 15

    with pytest.raises(ValueError, match="unexpected field count"):
        parse_data_row(row, 12)


@pytest.mark.parametrize("bad_value", ["nan", "inf", "-inf"])
def test_rejects_nonfinite_features(bad_value: str) -> None:
    row = ["0.25"] * 12 + ["1", "0", "1", "1"]
    row[0] = bad_value

    with pytest.raises(ValueError, match="non-finite field"):
        parse_data_row(row, 1)


def test_rejects_nonbinary_treatment_or_outcome() -> None:
    row = ["0.25"] * 12 + ["2", "0", "1", "1"]

    with pytest.raises(ValueError, match="non-binary"):
        parse_data_row(row, 1)
