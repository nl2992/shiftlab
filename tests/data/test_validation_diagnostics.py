import numpy as np
import pandas as pd

from shiftlab.data.validation import diagnostics


def test_shift_report_uses_explicit_asymptotic_ks_method(tmp_path):
    directory = tmp_path / "fixture" / "fixture-version"
    directory.mkdir(parents=True)
    values = np.arange(48, dtype=float)
    frame = pd.DataFrame(
        {
            "features": [np.array([value % 3, value]) for value in values],
            "target": values,
        }
    )
    frame.to_parquet(directory / "observations.parquet", index=False)

    rows = diagnostics(directory)
    feature_rows = [row for row in rows if isinstance(row["feature"], int)]

    assert len(feature_rows) == 2
    assert all("pvalue" in row for row in feature_rows)
    assert all(row["pvalue_method"].startswith("asymptotic two-sample KS") for row in feature_rows)
