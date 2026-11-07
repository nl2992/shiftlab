"""Coverage and integrity preflight only; no model predictions or outcome metrics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
PILOT = Path(__file__).resolve().parent
RAW = ROOT / "data/raw/eia930_f8_2026_confirmation_20261107"
DEV = ROOT / "data/raw/eia930_f8_development_20261107"
DEV_MANIFEST = ROOT / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
BAS = ["AZPS", "BANC", "EPE", "ERCO", "FMPP", "FPC", "MISO", "NEVP", "NYIS", "SWPP", "TIDC"]
TEST_START = pd.Timestamp("2026-01-01T00:00:00Z")
TEST_END = pd.Timestamp("2026-10-19T18:00:00Z")
COLUMNS = [
    "Balancing Authority",
    "UTC Time at End of Hour",
    "Demand Forecast (MW)",
    "Demand (MW)",
    "Demand (MW) (Imputed)",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    dev_manifest = json.loads(DEV_MANIFEST.read_text())
    for rel, expected in dev_manifest["raw_file_sha256"].items():
        path = ROOT / rel
        if not path.exists() or sha256(path) != expected:
            raise RuntimeError(f"development source checksum mismatch: {rel}")
    receipt = json.loads((RAW / "source_receipt.json").read_text())
    for item in receipt["files"]:
        path = RAW / item["file"]
        if not path.exists() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"new source checksum mismatch: {item['file']}")
    rows: dict[str, list[pd.DataFrame]] = {ba: [] for ba in BAS}
    input_files = [ROOT / rel for rel in dev_manifest["raw_file_sha256"]]
    input_files += [RAW / item["file"] for item in receipt["files"]]
    for path in input_files:
        if not path.exists():
            raise RuntimeError(f"missing input file: {path}")
        for chunk in pd.read_csv(path, usecols=COLUMNS, dtype=str, chunksize=150_000):
            chunk = chunk[chunk["Balancing Authority"].isin(BAS)].copy()
            if chunk.empty:
                continue
            chunk["time"] = pd.to_datetime(
                chunk["UTC Time at End of Hour"],
                format="%m/%d/%Y %I:%M:%S %p",
                utc=True,
                errors="coerce",
            )
            chunk["actual"] = pd.to_numeric(chunk["Demand (MW)"], errors="coerce")
            chunk["forecast"] = pd.to_numeric(chunk["Demand Forecast (MW)"], errors="coerce")
            chunk["imputed"] = pd.to_numeric(chunk["Demand (MW) (Imputed)"], errors="coerce")
            for ba, group in chunk.dropna(subset=["time"]).groupby("Balancing Authority"):
                rows[str(ba)].append(group[["time", "actual", "forecast", "imputed"]])

    summary = {}
    for ba in BAS:
        if not rows[ba]:
            raise RuntimeError(f"no source rows for registered BA {ba}")
        frame = pd.concat(rows[ba], ignore_index=True)
        if frame["time"].duplicated().any():
            raise RuntimeError(f"duplicate timestamps in source files for {ba}")
        frame = frame.sort_values("time")
        test = frame[(frame.time >= TEST_START) & (frame.time < TEST_END)]
        test = test[(test.actual > 0) & (test.forecast > 0) & test.imputed.isna()]
        if test.empty:
            raise RuntimeError(f"no complete raw test rows for {ba}")
        gaps = test.time.diff().dropna().dt.total_seconds().div(3600)
        summary[ba] = {
            "eligible_raw_test_rows": int(len(test)),
            "first_event_utc": test.time.iloc[0].isoformat(),
            "last_event_utc": test.time.iloc[-1].isoformat(),
            "nonhourly_gaps_in_eligible_rows": int((gaps != 1).sum()),
            "complete_nonoverlap_2000_row_episode_upper_bound": int(len(test) // 2000),
        }

    result = {
        "protocol": "eia930_f8_2026_confirmation_20261107/PROTOCOL_V2.md",
        "inspection_scope": "source integrity and raw coverage only; no model fitting, predictions, or outcome metrics",
        "test_window": [TEST_START.isoformat(), TEST_END.isoformat()],
        "registered_bas": BAS,
        "prior_2021_2023_files_checksum_verified": True,
        "new_source_receipt": receipt,
        "coverage_by_ba": summary,
        "no_2026_policy_outcomes_opened": True,
    }
    (PILOT / "PREFLIGHT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"bas": len(summary), "rows": {k: v["eligible_raw_test_rows"] for k, v in summary.items()}, "test_outcomes_scored": False}, indent=2))


if __name__ == "__main__":
    main()
