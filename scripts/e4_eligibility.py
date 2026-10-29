"""E4 eligibility freeze and development/locked split (P3).

Decides which EIA balancing authorities (BAs) are eligible for the E4 held-out study using ONLY
metadata and availability: which of the D, DF, NG and TI hourly series exist, and how many hours
in each registered window have all four series present plus an observed next-hour demand. The
reader below replaces every observed number by the placeholder 1.0 (or None for a missing or
non-finite value) before anything is stored, so no demand, forecast or generation value is ever
held in memory, printed or written. The audit's own row builder is reused unchanged.

Rule R20 (at least 20 rehearsal procure events) cannot be computed without running the Ridge
policy on values. Its definition is registered here, and its evaluation is deferred to the E4
runner (``scripts/run_e4_heldout.py``), which applies it to each authority before any monitor
result is computed.

Outputs: ``docs/research_refinement_v1/stage1/e4_eligibility.json`` (ids and counts only).
The script refuses to run unless its own SHA-256 equals the pre-run record
``docs/research_refinement_v1/stage1/e4_eligibility_prerun.json``, and refuses to overwrite an
existing output.

    uv run --no-sync python scripts/e4_eligibility.py
"""

from __future__ import annotations

import json
import math
import platform
import re
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import audit_eia_2026_holdout_readiness as audit  # reused unchanged

STAGE1 = ROOT / "docs/research_refinement_v1/stage1"
PRERUN = STAGE1 / "e4_eligibility_prerun.json"
OUTPUT = STAGE1 / "e4_eligibility.json"

# The 14 regional or national aggregates among the 70 demand series.
AGGREGATES = (
    "CAL",
    "CAR",
    "CENT",
    "FLA",
    "MIDA",
    "MIDW",
    "NE",
    "NW",
    "NY",
    "SE",
    "SW",
    "TEN",
    "TEX",
    "US48",
)
# Authorities already used or exposed in earlier ShiftLab analyses.
PREVIOUSLY_EXPOSED = ("CISO", "ERCO", "NYIS")

SPLIT_SEED = 100400000  # configs/seed_registry.yaml: e4_split_and_orientation (first id)
DEV_FRACTION = 1 / 3
COVERAGE_MIN = 0.95
MIN_REHEARSAL_PROCURE_EVENTS = 20  # rule R20, evaluated by the runner, not here

TYPES = audit.TYPES  # ("D", "DF", "NG", "TI")
HOUR = audit.HOUR
_epoch = audit._epoch

# Registered coverage windows: inclusive event-time bounds. They sit inside the audit's SPLITS and
# follow the WP4 builder (rehearsal fit 2019-2023, rehearsal 2024, development 2025 and 2026).
WINDOWS = {
    "fit_2019_2023": (_epoch("2019-01-01T00:00:00Z"), _epoch("2023-12-31T23:00:00Z")),
    "rehearsal_2024": (_epoch("2024-01-01T00:00:00Z"), _epoch("2024-12-30T23:00:00Z")),
    "path_2025": (_epoch("2025-01-01T00:00:00Z"), _epoch("2025-12-30T23:00:00Z")),
    "path_2026": (_epoch("2026-01-01T00:00:00Z"), _epoch("2026-10-19T17:00:00Z")),
}

_HEAD = re.compile(rb'^\{"series_id"\s*:\s*"EBA\.([A-Z0-9]+)-ALL\.(D|DF|NG|TI)\.H"')


def sha256_file(path: Path) -> str:
    return audit._sha256(path)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _presence(raw) -> float | None:
    """Availability of one observation. The number itself is discarded."""
    if raw is None:
        return None
    try:
        return 1.0 if math.isfinite(float(raw)) else None
    except (TypeError, ValueError):
        return None


def read_presence(archive: Path) -> tuple[dict, dict]:
    """Return ({(ba, kind): {epoch: 1.0 | None}}, {(ba, kind): duplicate-hour count})."""
    series: dict[tuple[str, str], dict[int, float | None]] = {}
    duplicates: dict[tuple[str, str], int] = {}
    with zipfile.ZipFile(archive) as zf:
        members = [n for n in zf.namelist() if Path(n).name == "EBA.txt"]
        if len(members) != 1:
            raise ValueError("EBA archive must contain exactly one EBA.txt member")
        with zf.open(members[0]) as source:
            for line in source:
                head = _HEAD.match(line)
                if head is None:
                    continue
                key = (head.group(1).decode(), head.group(2).decode())
                item = json.loads(line)
                if item.get("f") != "H":
                    raise ValueError(f"Expected hourly frequency for {key}")
                if key in series:
                    raise ValueError(f"Duplicate EBA series {key}")
                data = item.get("data", [])
                stamps = pd.to_datetime([p for p, _ in data], format="%Y%m%dT%H", utc=True)
                periods = stamps.tz_convert(None).astype("datetime64[s]").astype("int64")
                values: dict[int, float | None] = {}
                dup = 0
                for epoch, (_, raw) in zip(periods.tolist(), data, strict=True):
                    if epoch in values:
                        dup += 1
                    values[epoch] = _presence(raw)
                series[key] = values
                duplicates[key] = dup
    return series, duplicates


def window_counts(rows: list[dict]) -> dict:
    out = {}
    for name, (start, end) in WINDOWS.items():
        expected = (end - start) // HOUR + 1
        complete = sum(
            1 for r in rows if r["complete_features"] and start <= r["event_time"] <= end
        )
        out[name] = {
            "expected_hours": expected,
            "complete_rows_with_next_hour_demand": complete,
            "coverage": round(complete / expected, 6),
        }
    return out


def split_authorities(eligible: list[str]) -> tuple[list[str], list[str]]:
    """Deterministic split: sorted ids, ``default_rng(SPLIT_SEED).permutation``, first third dev."""
    ids = sorted(eligible)
    n_dev = round(len(ids) * DEV_FRACTION)
    order = np.random.default_rng(SPLIT_SEED).permutation(len(ids))
    dev = sorted(ids[i] for i in order[:n_dev])
    locked = sorted(ids[i] for i in order[n_dev:])
    return dev, locked


def verify_prerun() -> dict:
    if not PRERUN.is_file():
        raise FileNotFoundError(f"pre-run hash record missing: {PRERUN}")
    record = json.loads(PRERUN.read_text(encoding="utf-8"))
    actual = sha256_file(Path(__file__))
    if actual != record["script_sha256"]:
        raise ValueError("e4_eligibility.py changed since the pre-run hash was recorded")
    return record


def run() -> Path:
    started = time.perf_counter()
    prerun = verify_prerun()
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite {OUTPUT}")
    receipt = json.loads(audit.RECEIPT.read_text(encoding="utf-8"))
    archive_hash = sha256_file(audit.ARCHIVE)
    if archive_hash != audit.EXPECTED_SHA256 or receipt.get("sha256") != archive_hash:
        raise ValueError("EBA archive checksum does not match the frozen source receipt")

    run_utc = utc_now()
    presence, duplicates = read_presence(audit.ARCHIVE)
    demand_ids = sorted({ba for ba, kind in presence if kind == "D"})
    if set(AGGREGATES) - set(demand_ids) or set(PREVIOUSLY_EXPOSED) - set(demand_ids):
        raise ValueError("a registered exclusion id has no demand series in the archive")

    log: list[dict] = []
    per_ba: dict[str, dict] = {}
    eligible: list[str] = []
    for ba in demand_ids:
        reasons: list[str] = []
        if ba in AGGREGATES:
            reasons.append("aggregate")
        if ba in PREVIOUSLY_EXPOSED:
            reasons.append("previously_used_or_exposed")
        if reasons:
            log.append({"ba": ba, "reasons": reasons})
            continue
        have = {kind: (ba, kind) in presence for kind in TYPES}
        info: dict = {"series_present": have}
        missing = [k for k, v in have.items() if not v]
        if missing:
            reasons.append("missing_series:" + ",".join(missing))
        else:
            dups = {k: duplicates[(ba, k)] for k in TYPES}
            info["duplicate_hours_by_series"] = dups
            if any(dups.values()):
                reasons.append("duplicate_hours")
            info["n_periods_by_series"] = {k: len(presence[(ba, k)]) for k in TYPES}
            info["n_unavailable_by_series"] = {
                k: sum(v is None for v in presence[(ba, k)].values()) for k in TYPES
            }
            series = {f"EBA.{ba}-ALL.{k}.H": presence[(ba, k)] for k in TYPES}
            counts = window_counts(audit._eligible_rows(series, ba))
            info["windows"] = counts
            low = [n for n, c in counts.items() if c["coverage"] < COVERAGE_MIN]
            if low:
                reasons.append(f"coverage_below_{COVERAGE_MIN:.2f}:" + ",".join(low))
        per_ba[ba] = info
        if reasons:
            log.append({"ba": ba, "reasons": reasons})
        else:
            eligible.append(ba)

    dev, locked = split_authorities(eligible)
    result = {
        "artifact": "e4_eligibility",
        "contains": "identifiers, availability counts and exclusion reasons only; no data values",
        "script": {
            "path": "scripts/e4_eligibility.py",
            "sha256": sha256_file(Path(__file__)),
            "prerun_record": prerun,
            "run_utc": run_utc,
            "reused_unchanged": {
                "path": "scripts/audit_eia_2026_holdout_readiness.py",
                "sha256": sha256_file(Path(audit.__file__)),
                "symbols": ["_eligible_rows", "SPLITS", "TYPES", "HOUR"],
            },
        },
        "source": {
            "archive": "data/raw/eia/EBA.zip",
            "sha256": archive_hash,
            "receipt_sha256": sha256_file(audit.RECEIPT),
        },
        "rule": {
            "exclusions": {
                "aggregates": list(AGGREGATES),
                "previously_used_or_exposed": list(PREVIOUSLY_EXPOSED),
            },
            "required_series": [f"EBA.<BA>-ALL.{k}.H" for k in TYPES],
            "event": "hour with D, DF, NG and TI all present and next-hour D observed",
            "coverage_windows_utc_epoch": {k: list(v) for k, v in WINDOWS.items()},
            "coverage_min_each_window": COVERAGE_MIN,
            "R20_rehearsal_procure_events_min": MIN_REHEARSAL_PROCURE_EVENTS,
            "R20_status": "deferred: needs the Ridge policy on values; evaluated by "
            "scripts/run_e4_heldout.py per authority before any monitor result",
        },
        "counts": {
            "demand_series": len(demand_ids),
            "excluded_aggregates": sum("aggregate" in e["reasons"] for e in log),
            "excluded_previously_exposed": sum(
                "previously_used_or_exposed" in e["reasons"] for e in log
            ),
            "excluded_other": sum(
                not ({"aggregate", "previously_used_or_exposed"} & set(e["reasons"])) for e in log
            ),
            "eligible": len(eligible),
        },
        "exclusion_log": log,
        "per_authority_availability": per_ba,
        "eligible": sorted(eligible),
        "split": {
            "seed": SPLIT_SEED,
            "method": "ids sorted ascending; numpy.random.default_rng(seed).permutation(n); "
            "first round(n/3) of the permutation are development, the rest locked",
            "numpy": np.__version__,
            "development": dev,
            "locked": locked,
            "n_development": len(dev),
            "n_locked": len(locked),
        },
        "environment": {"python": platform.python_version(), "runtime_seconds": None},
    }
    result["environment"]["runtime_seconds"] = round(time.perf_counter() - started, 1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return OUTPUT


def load_eligibility() -> dict:
    """Read the frozen eligibility record (used by the E4 runner)."""
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    path = run()
    record = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(record["counts"], indent=2))
    print("development:", record["split"]["n_development"], "locked:", record["split"]["n_locked"])
    print(path.relative_to(ROOT).as_posix())
