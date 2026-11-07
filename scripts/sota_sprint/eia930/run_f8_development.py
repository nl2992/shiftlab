"""Run the prospectively frozen EIA-930 F8 development replay.

Historical EIA values and generated outcomes are kept under ignored data/raw and the pilot folder;
no source values are committed. This is a simulated-feedback replay, not historical vintages.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_development_20261107"
RAW = ROOT / "data/raw/eia930_f8_development_20261107"
ENDPOINT = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
BAS = ("PJM", "ERCO", "CISO")
TYPES = ("D", "DF")
START, END = "2019-01-01T00", "2023-12-31T23"
TRAIN_END = pd.Timestamp("2021-01-01T00:00:00Z")
DEV_START = TRAIN_END
DEV_END = pd.Timestamp("2024-01-01T00:00:00Z")
PAGE = 5000
BUDGET, CQ, CS, ALPHA, DELAY = 200, 0.05, 5.0, 0.05, 1
POLICIES = (
    "PFA-SR:gated_deployment",
    "rmm:gated_deployment+RMM",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "gated_deployment",
    "gated_adaptive_range",
    "cams_adapter",
    "online_llm_picker",
    "model_selector_causal",
    "model_picker_adapter",
    "gong_zhang_paid_obs",
    "qiu_delayed_movement",
    "CONTROL_never_switch",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def api_rows(ba: str, kind: str, api_key: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        params = {
            "api_key": api_key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": ba,
            "facets[type][]": kind,
            "start": START,
            "end": END,
            "length": str(PAGE),
            "offset": str(offset),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
        }
        url = ENDPOINT + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as response:
            doc = json.load(response)
        response = doc.get("response", {})
        page = response.get("data", [])
        if not isinstance(page, list):
            raise TypeError(f"unexpected EIA response for {ba}/{kind}: {doc}")
        rows.extend(page)
        total = int(response.get("total", 0))
        if not page or offset + len(page) >= total:
            break
        offset += len(page)
        time.sleep(0.2)
    return rows


def retrieve() -> dict[str, dict[str, pd.Series]]:
    RAW.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("EIA_API_KEY") or "DEMO_KEY"
    out: dict[str, dict[str, pd.Series]] = {}
    hashes: dict[str, str] = {}
    for ba in BAS:
        out[ba] = {}
        for kind in TYPES:
            rows = api_rows(ba, kind, key)
            path = RAW / f"{ba}_{kind}.json"
            path.write_text(json.dumps(rows, separators=(",", ":")) + "\n")
            hashes[str(path.relative_to(ROOT))] = sha(path)
            frame = pd.DataFrame(rows)
            if frame.empty:
                raise RuntimeError(f"empty API response: {ba}/{kind}")
            frame["period"] = pd.to_datetime(frame["period"], utc=True)
            frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
            frame = frame.dropna(subset=["period", "value"]).drop_duplicates("period", keep="last")
            out[ba][kind] = frame.set_index("period")["value"].sort_index()
    (PILOT / "source_manifest.json").write_text(
        json.dumps(
            {
                "endpoint": ENDPOINT,
                "respondents": BAS,
                "types": {"D": "Demand", "DF": "Day-ahead demand forecast"},
                "start": START,
                "end": END,
                "api_key_source": "EIA_API_KEY if configured; otherwise public DEMO_KEY",
                "raw_response_sha256": hashes,
                "retrieved_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                "note": "Current revised historical values; simulated feedback protocol.",
            },
            indent=2,
        )
        + "\n"
    )
    return out


def paired_stream(
    ba: str, data: dict[str, pd.Series]
) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, float]:
    actual, forecast = data["D"], data["DF"]
    lagged_series = actual.copy()
    lagged_series.index = lagged_series.index + pd.Timedelta(hours=24)
    lagged = lagged_series.reindex(actual.index).to_numpy()
    cutoff = float(actual.loc[actual.index < TRAIN_END].quantile(0.90))
    frame = pd.concat(
        [
            actual.rename("actual"),
            forecast.rename("forecast"),
            pd.Series(lagged, index=actual.index, name="lag24"),
        ],
        axis=1,
    )
    frame = frame.loc[(frame.index >= DEV_START) & (frame.index < DEV_END)]
    frame = frame.dropna()
    frame = frame.loc[(frame.actual > 0) & (frame.forecast > 0) & (frame.lag24 > 0)]
    times = pd.DatetimeIndex(frame.index)
    labels = (frame.actual.to_numpy() >= cutoff).astype(np.int8)
    predictions = np.column_stack(
        [
            (frame.lag24.to_numpy() >= cutoff).astype(np.int8),
            (frame.forecast.to_numpy() >= cutoff).astype(np.int8),
        ]
    )
    disagreements = predictions[:, 0] != predictions[:, 1]
    cond = (
        float((predictions[disagreements, 1] == labels[disagreements]).mean())
        if disagreements.any()
        else float("nan")
    )
    return times, predictions, labels, cond


def run_episode(predictions: np.ndarray, labels: np.ndarray, episode: int, ba: str) -> list[dict]:
    sys.path.insert(0, str(ROOT / "scripts/failure_atlas_v2_flq"))
    sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))
    from registry import EXTRA, IMPORT_ERRORS
    from simulator import run_episode
    from suite import build_suite

    if IMPORT_ERRORS:
        raise RuntimeError(f"policy import errors: {IMPORT_ERRORS}")
    policies = build_suite(
        len(labels),
        BUDGET,
        CS,
        CQ,
        ALPHA,
        DELAY,
        episode,
        int.from_bytes(hashlib.sha256(ba.encode()).digest()[:4], "big"),
        names=list(POLICIES),
        extra=EXTRA,
    )
    rows = []
    for policy in policies:
        result = run_episode(
            policy,
            model_predictions=predictions,
            labels=labels,
            delay=DELAY,
            budget=BUDGET,
            label_price=CQ,
            switch_cost=CS,
            trace=True,
        )
        rows.append(
            {
                "ba": ba,
                "episode": episode,
                "start_event": episode * 2000,
                "policy": policy.name,
                "net_cost": result.net_cost,
                "prediction_loss": result.prediction_loss,
                "labels": result.requested_labels,
                "label_cost": CQ * result.requested_labels,
                "switches": result.deployment_switches,
                "switch_cost": CS * result.deployment_switches,
                "promotions": sum(
                    r.get("deployed_model", 0) == 1
                    and (i == 0 or result.records[i - 1].get("deployed_model", 0) == 0)
                    for i, r in enumerate(result.records)
                ),
                "rollbacks": sum(
                    r.get("deployed_model", 0) == 0
                    and i > 0
                    and result.records[i - 1].get("deployed_model", 0) == 1
                    for i, r in enumerate(result.records)
                ),
                "first_promotion": next(
                    (i for i, r in enumerate(result.records) if r.get("deployed_model", 0) == 1),
                    None,
                ),
            }
        )
    return rows


def main() -> None:
    PILOT.mkdir(parents=True, exist_ok=True)
    if (PILOT / "RUN_STARTED.json").exists():
        raise SystemExit("run marker exists; refusing to overwrite development outcomes")
    (PILOT / "RUN_STARTED.json").write_text(
        json.dumps(
            {
                "protocol_sha256": sha(PILOT / "PROTOCOL.md"),
                "started_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            },
            indent=2,
        )
        + "\n"
    )
    source = retrieve()
    records: list[dict] = []
    eligibility: dict[str, dict] = {}
    for ba in BAS:
        times, predictions, labels, cond = paired_stream(ba, source[ba])
        disagreement = float(np.mean(predictions[:, 0] != predictions[:, 1]))
        eligibility[ba] = {
            "events": len(labels),
            "disagreement_rate": disagreement,
            "challenger_correct_given_disagreement": cond,
        }
        # A one-step simulated release delay is one hour only on contiguous UTC runs. Never
        # concatenate across data gaps, since that would alter both chronology and delay.
        cuts = np.flatnonzero(np.diff(times.asi8) != pd.Timedelta(hours=1).value) + 1
        boundaries = np.r_[0, cuts, len(times)]
        ep = 0
        for left, right in itertools.pairwise(boundaries):
            for lo in range(int(left), int(right) - 1999, 2000):
                hi = lo + 2000
                records.extend(run_episode(predictions[lo:hi], labels[lo:hi], ep, ba))
                ep += 1
    result_path = PILOT / "episode_results.jsonl"
    result_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records))
    pd.DataFrame(records).groupby(["ba", "policy"], as_index=False).mean(numeric_only=True).to_csv(
        PILOT / "summary_by_ba.csv", index=False
    )
    method_files = [
        ROOT / "scripts/sota_sprint/eia930/run_f8_development.py",
        ROOT / "scripts/sota_sprint/registry.py",
        ROOT / "scripts/sota_sprint/pfa_srr_baseline.py",
        ROOT / "scripts/failure_atlas_v2_flq/suite.py",
        ROOT / "scripts/failure_atlas_v2_flq/strong_hosts.py",
        ROOT / "scripts/failure_atlas_v2_flq/v2_extra.py",
        ROOT / "scripts/failure_atlas_v2/restart_monitor.py",
        ROOT / "scripts/promising_directions/sota/simulator.py",
    ]
    summary = {
        "eligibility": eligibility,
        "episode_count": {ba: len({r["episode"] for r in records if r["ba"] == ba}) for ba in BAS},
        "methods": POLICIES,
        "raw_rows_sha256": sha(result_path),
        "protocol_sha256": sha(PILOT / "PROTOCOL.md"),
        "method_source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in method_files},
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "cost_identity_max_abs_residual": max(
            abs(r["net_cost"] - r["prediction_loss"] - r["label_cost"] - r["switch_cost"])
            for r in records
        ),
    }
    (PILOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (PILOT / "RUN_COMPLETE.json").write_text(
        json.dumps(
            {
                "completed_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                "records": len(records),
                "summary_sha256": sha(PILOT / "summary.json"),
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
