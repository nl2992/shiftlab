"""Guard the audit ledger against shifted CSV fields."""

import pytest

from scripts.retrospective_audit.validate_claim_ledger import LEDGER, validate


def test_current_ledger_has_aligned_claim_rows():
    assert validate() >= 31


def test_unquoted_comma_in_claim_field_is_rejected(tmp_path):
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("INTEGRATED-EFFICACY-NOGO,"))
    lines[index] = lines[index].replace(
        '"22 one-sided paired tests,', "22 one-sided paired tests,", 1
    )
    lines[index] = lines[index].replace('undefined raw p"', "undefined raw p", 1)
    malformed = tmp_path / "claims.csv"
    malformed.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected 32 fields"):
        validate(malformed)
