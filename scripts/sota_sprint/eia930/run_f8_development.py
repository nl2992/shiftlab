"""Run the prospectively frozen EIA-930 F8 development replay.

Historical EIA values and generated outcomes are kept under ignored data/raw and the pilot folder;
no source values are committed. This is a simulated-feedback replay, not historical vintages.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_development_20261107"
RAW = ROOT / "data/raw/eia930_f8_development_20261107"
FILE_BASE = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"
BAS = ("PJM", "ERCO", "CISO")
PERIODS = (
    "2021_Jan_Jun",
    "2021_Jul_Dec",
    "2022_Jan_Jun",
    "2022_Jul_Dec",
    "2023_Jan_Jun",
    "2023_Jul_Dec",
)
TRAIN_START = pd.Timestamp("2021-01-01T00:00:00Z")
TRAIN_END = pd.Timestamp("2022-01-01T00:00:00Z")
DEV_START = TRAIN_END
DEV_END = pd.Timestamp("2024-01-01T00:00:00Z")
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


def retrieve() -> dict[str, dict[str, pd.Series]]:
    RAW.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict[str, list[pd.DataFrame]]] = {
        ba: {"D": [], "DF": [], "imputed": []} for ba in BAS
    }
    hashes: dict[str, str] = {}
    manifest_rows = []
    usecols = [
        "Balancing Authority",
        "UTC Time at End of Hour",
        "Demand Forecast (MW)",
        "Demand (MW)",
        "Demand (MW) (Imputed)",
    ]
    for period in PERIODS:
        name = f"EIA930_BALANCE_{period}.csv"
        path = RAW / name
        url = FILE_BASE + name
        if not path.exists():
            temp_path = path.with_suffix(path.suffix + ".part")
            request = urllib.request.Request(url, headers={"User-Agent": "ShiftLab-research/1.0"})
            with (
                urllib.request.urlopen(request, timeout=120) as response,
                temp_path.open("wb") as output,
            ):
                expected = int(response.headers.get("Content-Length", "0"))
                for block in iter(lambda: response.read(1 << 20), b""):
                    output.write(block)
            if expected and temp_path.stat().st_size != expected:
                raise OSError(
                    f"incomplete bulk file {name}: {temp_path.stat().st_size} != {expected}"
                )
            temp_path.replace(path)
        digest = sha(path)
        hashes[str(path.relative_to(ROOT))] = digest
        manifest_rows.append(
            {"url": url, "file": name, "sha256": digest, "bytes": path.stat().st_size}
        )
        for chunk in pd.read_csv(path, usecols=usecols, dtype=str, chunksize=100_000):
            chunk = chunk.loc[chunk["Balancing Authority"].isin(BAS)]
            if chunk.empty:
                continue
            chunk["period"] = pd.to_datetime(
                chunk["UTC Time at End of Hour"],
                format="%m/%d/%Y %I:%M:%S %p",
                utc=True,
                errors="coerce",
            )
            chunk["actual"] = pd.to_numeric(chunk["Demand (MW)"], errors="coerce")
            chunk["forecast"] = pd.to_numeric(chunk["Demand Forecast (MW)"], errors="coerce")
            chunk["imputed"] = pd.to_numeric(chunk["Demand (MW) (Imputed)"], errors="coerce")
            for ba, group in chunk.groupby("Balancing Authority"):
                out[ba]["D"].append(group[["period", "actual"]])
                out[ba]["DF"].append(group[["period", "forecast"]])
                out[ba]["imputed"].append(group[["period", "imputed"]])
    series: dict[str, dict[str, pd.Series]] = {}
    for ba in BAS:
        series[ba] = {}
        for kind, column in (("D", "actual"), ("DF", "forecast"), ("imputed", "imputed")):
            frame = pd.concat(out[ba][kind], ignore_index=True)
            frame = frame.dropna(subset=["period"]).drop_duplicates("period", keep="last")
            series[ba][kind] = frame.set_index("period")[column].sort_index()
    (PILOT / "source_manifest.json").write_text(
        json.dumps(
            {
                "endpoint": FILE_BASE,
                "respondents": BAS,
                "periods": PERIODS,
                "columns": usecols,
                "raw_file_sha256": hashes,
                "download_manifest": manifest_rows,
                "retrieved_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                "note": "Current revised historical values; simulated feedback protocol.",
            },
            indent=2,
        )
        + "\n"
    )
    return series


def paired_stream(
    ba: str, data: dict[str, pd.Series]
) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, float]:
    actual, forecast, imputed = data["D"], data["DF"], data["imputed"]
    lagged_series = actual.copy()
    lagged_series.index = lagged_series.index + pd.Timedelta(hours=24)
    lagged = lagged_series.reindex(actual.index).to_numpy()
    train = actual.loc[(actual.index >= TRAIN_START) & (actual.index < TRAIN_END)]
    cutoff = float(train.quantile(0.90))
    frame = pd.concat(
        [
            actual.rename("actual"),
            forecast.rename("forecast"),
            pd.Series(lagged, index=actual.index, name="lag24"),
            imputed.rename("imputed"),
        ],
        axis=1,
    )
    frame = frame.loc[(frame.index >= DEV_START) & (frame.index < DEV_END)]
    frame = frame.dropna(subset=["actual", "forecast", "lag24"])
    frame = frame.loc[frame.imputed.isna()]
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
    if (PILOT / "episode_results.jsonl").exists():
        raise SystemExit("episode outcomes exist; refusing to overwrite development results")
    start_marker = PILOT / "RUN_STARTED.json"
    prior_attempts = []
    if start_marker.exists():
        previous = json.loads(start_marker.read_text())
        prior_attempts = previous.get("prior_attempts", []) + [previous]
    start_marker.write_text(
        json.dumps(
            {
                "protocol_sha256": sha(PILOT / "PROTOCOL.md"),
                "runner_sha256": sha(Path(__file__)),
                "git_head": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "started_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                "prior_attempts": prior_attempts,
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
