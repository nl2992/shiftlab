"""Agent-run public-data acquisition/schema/split audit without final outcome analysis."""

import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "bike": (
        "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip",
        "b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401",
        "hour.csv",
    ),
    "beijing": (
        "https://archive.ics.uci.edu/static/public/381/beijing+pm2+5+data.zip",
        "40cdd29c24918e855133dce280ff59779bb0b5852898e05bafcf422a4cc0a175",
        "PRSA_data_2010.1.1-2014.12.31.csv",
    ),
}


def main():
    out = ROOT / "outputs/exhaustive_evaluation/real_data"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (url, expected, member) in SOURCES.items():
        raw = out / (name + ".zip")
        if not raw.exists():
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read(10_000_001)
            assert len(data) <= 10_000_000
            raw.write_bytes(data)
        data = raw.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, (
            "source changed: audit before proceeding"
        )
        with zipfile.ZipFile(io.BytesIO(data)) as archive, archive.open(member) as f:
            df = pd.read_csv(f)
        if name == "bike":
            clock = pd.to_datetime(df["dteday"]) + pd.to_timedelta(df["hr"], unit="h")
            target = "cnt"
            split = {
                "train_end": "2011-07-01",
                "calibration_end": "2011-09-01",
                "development_end": "2012-01-01",
                "final_end": "2013-01-01",
            }
            exclusions = ["casual", "registered", "cnt", "same-hour observed weather"]
        else:
            clock = pd.to_datetime(df[["year", "month", "day", "hour"]])
            target = "pm2.5"
            # Development pipeline uses only pre-2012 rows. Original planned
            # 2012 calibration and 2013-14 evaluation remain unopened for efficacy.
            split = {
                "train_end": "2010-10-01",
                "calibration_end": "2011-01-01",
                "development_end": "2012-01-01",
                "reserved_calibration_end": "2013-01-01",
                "final_end": "2015-01-01",
            }
            exclusions = ["same-hour target", "same-hour observed weather", "future-filled targets"]
        assert clock.is_monotonic_increasing and clock.notna().all()
        # Duplicate local timestamps are recorded, not silently dropped: DST and
        # source aggregation require explicit adjudication before one-hour lags.
        duplicate_count = int(clock.duplicated().sum())
        dev = clock < pd.Timestamp(split["development_end"])
        # Only development targets are inspected. Final outcomes remain unanalyzed.
        devdf = df.loc[dev].copy()
        devdf["event_time"] = clock[dev].to_numpy()
        devdf.to_parquet(out / f"{name}_development.parquet", index=False)
        row = {
            "dataset": name,
            "url": url,
            "sha256": expected,
            "license": "CC BY 4.0",
            "retrieved_utc": datetime.now(UTC).isoformat(),
            "rows": len(df),
            "development_rows": int(dev.sum()),
            "future_metadata_only_rows": int((~dev).sum()),
            "missing_development_targets": int(devdf[target].isna().sum()),
            "duplicate_timestamps": duplicate_count,
            "split": split,
            "no_final_outcome_analysis": True,
            "excluded_features": exclusions,
            "clock_status": "event timestamps only; publication clocks unverified; imposed replay delay",
            "exposure_status": "prior repo exposure audit still required before confirmation",
        }
        rows.append(row)
        print(
            name,
            len(devdf),
            "development rows;",
            duplicate_count,
            "duplicate timestamps",
            flush=True,
        )
    (ROOT / "docs/exhaustive_evaluation/real_data_manifest.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
