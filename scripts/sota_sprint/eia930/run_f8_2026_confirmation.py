"""Open the locked EIA F8 2026 stream and run the frozen paired comparator panel."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_2026_confirmation_20261107"
RAW = ROOT / "data/raw/eia930_f8_2026_confirmation_20261107"
DEV_RAW = ROOT / "data/raw/eia930_f8_development_20261107"
MODEL_FREEZE = PILOT / "MODEL_FREEZE.json"
PREFLIGHT = PILOT / "PREFLIGHT.json"
SOURCE_MANIFEST = (
    ROOT / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
)
PROTOCOL = PILOT / "PROTOCOL_V2.md"
T, BUDGET, CQ, CS, ALPHA, DELAY = 2000, 200, 0.05, 5.0, 0.05, 1
SEED_BASE, SEEDS = 2026110720, 5
TEST_START = pd.Timestamp("2026-01-01T00:00:00Z")
TEST_END = pd.Timestamp("2026-10-19T18:00:00Z")
BAS = ["AZPS", "BANC", "EPE", "ERCO", "FMPP", "FPC", "MISO", "NEVP", "NYIS", "SWPP", "TIDC"]
FEATURES = [
    "forecast",
    "lag1",
    "lag24",
    "lag168",
    "lag336",
    "mean24",
    "max24",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "year_sin",
    "year_cos",
]
USECOLS = [
    "Balancing Authority",
    "UTC Time at End of Hour",
    "Demand Forecast (MW)",
    "Demand (MW)",
    "Demand (MW) (Imputed)",
]
POLICIES = (
    "PFA-SR:gated_deployment",
    "PFA-SR:gated_adaptive_range",
    "rmm:gated_deployment+RMM",
    "rmm:gated_adaptive_range+RMM",
    "E_srr:gated_deployment",
    "E_srrSR:gated_deployment",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "gated_deployment",
    "gated_adaptive_range",
    "gated_adaptive_range+front",
    "E_rb:gated_deployment",
    "E_rb:gated_adaptive_range",
    "E_rb:gated_adaptive_range+front",
    "cams_adapter",
    "model_selector_causal",
    "model_picker_adapter",
    "online_llm_picker",
    "gong_zhang_paid_obs",
    "qiu_delayed_movement",
    "variance_min_ipw",
    "economic_replacement",
    "CONTROL_never_switch",
    "fixed_incumbent",
    "fixed_challenger",
)

for p in (
    ROOT / "scripts/sota_sprint",
    ROOT / "scripts/failure_atlas_v2_flq",
    ROOT / "scripts/promising_directions/sota",
):
    sys.path.insert(0, str(p))

from controls import FixedModel
from registry import EXTRA as REGISTRY_EXTRA
from registry import IMPORT_ERRORS
from simulator import run_episode
from suite import build_suite


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pinned_alpha(factory, alpha):
    return lambda T_, B_, cs_, cq_, _alpha, delay_, rng_: factory(
        T_, B_, cs_, cq_, alpha, delay_, rng_
    )


def policy_factories():
    extra = dict(REGISTRY_EXTRA)
    if "E_srr:gated_deployment" not in extra or "E_srrSR:gated_deployment" not in extra:
        raise RuntimeError("registered calibrated CUSUM/SR methods are unavailable")
    extra["E_srr:gated_deployment"] = pinned_alpha(extra["E_srr:gated_deployment"], 0.005)
    extra["E_srrSR:gated_deployment"] = pinned_alpha(extra["E_srrSR:gated_deployment"], 0.0005)
    extra["fixed_incumbent"] = lambda T_, B_, cs_, cq_, a_, d_, r_: FixedModel(
        0, name="fixed_incumbent"
    )
    extra["fixed_challenger"] = lambda T_, B_, cs_, cq_, a_, d_, r_: FixedModel(
        1, name="fixed_challenger"
    )
    return extra


def check_registry(extra):
    if IMPORT_ERRORS:
        raise RuntimeError(f"published-method registry import errors: {IMPORT_ERRORS}")
    for seed in range(SEEDS):
        build_suite(
            T, BUDGET, CS, CQ, ALPHA, DELAY, 0, SEED_BASE + seed, names=list(POLICIES), extra=extra
        )


def write_opening_marker(extra):
    marker = PILOT / "TEST_OPENING.json"
    if (
        marker.exists()
        or (PILOT / "episode_policy_records.jsonl").exists()
        or (PILOT / "run_manifest.json").exists()
    ):
        raise RuntimeError("test opening or result artifacts already exist; refusing to overwrite")
    model_freeze = json.loads(MODEL_FREEZE.read_text())
    preflight = json.loads(PREFLIGHT.read_text())
    receipt = json.loads((RAW / "source_receipt.json").read_text())
    for ba, model in model_freeze["models"].items():
        if sha256(ROOT / model["artifact"]) != model["sha256"]:
            raise RuntimeError(f"frozen model hash mismatch for {ba}")
    if not preflight.get("no_2026_policy_outcomes_opened"):
        raise RuntimeError("coverage-only preflight is missing or reports an opened outcome")
    old_sources = json.loads(SOURCE_MANIFEST.read_text())["raw_file_sha256"]
    for rel, expected in old_sources.items():
        path = ROOT / rel
        if not path.exists() or sha256(path) != expected:
            raise RuntimeError(f"registered training/development source changed: {rel}")
    for item in receipt["files"]:
        path = RAW / item["file"]
        if (
            not path.exists()
            or path.stat().st_size != item["bytes"]
            or sha256(path) != item["sha256"]
        ):
            raise RuntimeError(f"registered test source changed: {item['file']}")
    new_source = {item["file"]: item["sha256"] for item in receipt["files"]}
    code_paths = [
        ROOT / "scripts/failure_atlas_v2_flq/suite.py",
        ROOT / "scripts/sota_sprint/registry.py",
        ROOT / "scripts/sota_sprint/fam_e.py",
        ROOT / "scripts/sota_sprint/fam_p.py",
        ROOT / "scripts/sota_sprint/pfa_srr_baseline.py",
        ROOT / "scripts/failure_atlas_v2_flq/strong_hosts.py",
        ROOT / "scripts/failure_atlas_v2/restart_monitor.py",
        ROOT / "scripts/promising_directions/sota/simulator.py",
    ]
    code_paths.extend(sorted((ROOT / "scripts/promising_directions/sota/competitors").glob("*.py")))
    method_code_hashes = {
        str(path.relative_to(ROOT)): sha256(path) for path in code_paths if path.exists()
    }
    marker_obj = {
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": sha256(PROTOCOL),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runner_sha256": sha256(Path(__file__)),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "old_source_sha256": old_sources,
        "new_source_sha256": new_source,
        "new_source_receipt_sha256": sha256(RAW / "source_receipt.json"),
        "preflight_sha256": sha256(PREFLIGHT),
        "model_freeze_sha256": sha256(MODEL_FREEZE),
        "model_sha256": {ba: info["sha256"] for ba, info in model_freeze["models"].items()},
        "baseline_suite_sha256": sha256(ROOT / "scripts/failure_atlas_v2_flq/suite.py"),
        "registry_sha256": sha256(ROOT / "scripts/sota_sprint/registry.py"),
        "simulator_sha256": sha256(ROOT / "scripts/promising_directions/sota/simulator.py"),
        "method_code_sha256": method_code_hashes,
        "policy_seed_base": SEED_BASE,
        "policy_seeds": SEEDS,
        "ba_registry": BAS,
        "test_window": [TEST_START.isoformat(), (TEST_END - pd.Timedelta(hours=1)).isoformat()],
        "contract": {
            "T": T,
            "B": BUDGET,
            "label_cost": CQ,
            "switch_cost": CS,
            "alpha": ALPHA,
            "delay_hours": DELAY,
        },
        "policy_registry": list(POLICIES),
        "opened_before_test_row_parsing_or_prediction": True,
    }
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w") as f:
        json.dump(marker_obj, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    dirfd = os.open(PILOT, os.O_RDONLY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)
    return marker_obj


def load_series():
    source_manifest = json.loads(SOURCE_MANIFEST.read_text())
    receipt = json.loads((RAW / "source_receipt.json").read_text())
    paths = [ROOT / rel for rel in source_manifest["raw_file_sha256"]]
    paths.extend(RAW / item["file"] for item in receipt["files"])
    by_ba = {ba: {key: [] for key in ("D", "DF", "imputed")} for ba in BAS}
    mapping = {"Demand (MW)": "D", "Demand Forecast (MW)": "DF", "Demand (MW) (Imputed)": "imputed"}
    for path in paths:
        for chunk in pd.read_csv(path, usecols=USECOLS, dtype=str, chunksize=150_000):
            chunk = chunk[chunk["Balancing Authority"].isin(BAS)].copy()
            if chunk.empty:
                continue
            chunk["time"] = pd.to_datetime(
                chunk["UTC Time at End of Hour"],
                format="%m/%d/%Y %I:%M:%S %p",
                utc=True,
                errors="coerce",
            )
            for col in mapping:
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
            for ba, group in chunk.dropna(subset=["time"]).groupby("Balancing Authority"):
                for source_col, key in mapping.items():
                    by_ba[str(ba)][key].append(
                        group[["time", source_col]].rename(columns={source_col: key})
                    )
    out = {}
    for ba in BAS:
        out[ba] = {}
        for key, parts in by_ba[ba].items():
            if not parts:
                raise RuntimeError(f"no data for {ba}/{key}")
            frame = pd.concat(parts, ignore_index=True)
            if frame["time"].duplicated().any():
                raise RuntimeError(f"duplicate timestamp in combined input for {ba}/{key}")
            out[ba][key] = frame.set_index("time")[key].sort_index()
    return out


def features_for(series, cutoff):
    idx = pd.date_range("2021-01-01T00:00:00Z", TEST_END - pd.Timedelta(hours=1), freq="h")
    frame = pd.DataFrame(index=idx)
    frame["actual"] = series["D"].reindex(idx)
    frame["forecast"] = series["DF"].reindex(idx)
    frame["imputed"] = series["imputed"].reindex(idx)
    for lag in (1, 24, 168, 336):
        frame[f"lag{lag}"] = frame.actual.shift(lag)
    prior = frame.actual.shift(1).rolling(24, min_periods=24)
    frame["mean24"], frame["max24"] = prior.mean(), prior.max()
    h, wd, doy = idx.hour.to_numpy(), idx.dayofweek.to_numpy(), idx.dayofyear.to_numpy()
    frame["hour_sin"], frame["hour_cos"] = np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24)
    frame["weekday_sin"], frame["weekday_cos"] = (
        np.sin(2 * np.pi * wd / 7),
        np.cos(2 * np.pi * wd / 7),
    )
    frame["year_sin"], frame["year_cos"] = (
        np.sin(2 * np.pi * doy / 365.25),
        np.cos(2 * np.pi * doy / 365.25),
    )
    eligible = frame[FEATURES + ["actual", "lag24"]].notna().all(axis=1)
    eligible &= frame.imputed.isna() & (frame.actual > 0) & (frame.forecast > 0) & (frame.lag24 > 0)
    test_mask = (frame.index >= TEST_START) & (frame.index < TEST_END)
    rows = frame.loc[eligible & test_mask]
    if len(rows) == 0:
        raise RuntimeError("no eligible test events after feature construction")
    X = rows[FEATURES]
    y = (rows.actual.to_numpy() >= cutoff).astype(np.int8)
    incumbent = (rows.lag24.to_numpy() >= cutoff).astype(np.int8)
    return pd.DatetimeIndex(rows.index), X, np.column_stack((incumbent, y * 0)), y


def event_episodes(index, predictions, labels):
    boundary = index.to_series().diff().ne(pd.Timedelta(hours=1)).cumsum().to_numpy()
    for run_id in np.unique(boundary):
        pos = np.flatnonzero(boundary == run_id)
        for block in range(len(pos) // T):
            sl = pos[block * T : (block + 1) * T]
            yield int(run_id), block, index[sl[0]], predictions[sl], labels[sl]


def main():
    extra = policy_factories()
    check_registry(extra)
    opening = write_opening_marker(extra)
    model_freeze = json.loads(MODEL_FREEZE.read_text())
    data = load_series()
    records_path = PILOT / "episode_policy_records.jsonl"
    partial_path = PILOT / "episode_policy_records.partial.jsonl"
    with partial_path.open("x") as f:
        episode_id = 0
        coverage = {}
        for ba in BAS:
            cutoff = model_freeze["models"][ba]["threshold_mw"]
            time_index, X, pred_skel, y = features_for(data[ba], cutoff)
            model_path = ROOT / model_freeze["models"][ba]["artifact"]
            model = joblib.load(model_path)
            challenger = (model.predict_proba(X)[:, 1] >= 0.5).astype(np.int8)
            preds = pred_skel.copy()
            preds[:, 1] = challenger
            coverage[ba] = {
                "eligible_test_events": len(time_index),
                "first_event_utc": time_index[0].isoformat(),
                "last_event_utc": time_index[-1].isoformat(),
                "usable_episodes": 0,
            }
            for run_id, local_episode, start_time, p_ep, y_ep in event_episodes(
                time_index, preds, y
            ):
                coverage[ba]["usable_episodes"] += 1
                for seed_id in range(SEEDS):
                    policy_seed = SEED_BASE + seed_id
                    policies = build_suite(
                        T,
                        BUDGET,
                        CS,
                        CQ,
                        ALPHA,
                        DELAY,
                        episode_id,
                        policy_seed,
                        names=list(POLICIES),
                        extra=extra,
                    )
                    for policy in policies:
                        result = run_episode(
                            policy,
                            model_predictions=p_ep,
                            labels=y_ep,
                            delay=DELAY,
                            budget=BUDGET,
                            label_price=CQ,
                            switch_cost=CS,
                            trace=True,
                        )
                        trace = result.records
                        promotions = sum(
                            trace[i]["deployed_model"] == 1
                            and (i == 0 or trace[i - 1]["deployed_model"] == 0)
                            for i in range(len(trace))
                        )
                        rollbacks = sum(
                            trace[i]["deployed_model"] == 0
                            and i > 0
                            and trace[i - 1]["deployed_model"] == 1
                            for i in range(len(trace))
                        )
                        label_cost = CQ * result.requested_labels
                        switch_cost = CS * result.deployment_switches
                        residual = result.net_cost - (
                            result.prediction_loss + label_cost + switch_cost
                        )
                        if result.requested_labels > BUDGET or abs(residual) > 1e-8:
                            raise RuntimeError(
                                f"cost or budget invariant failed for {ba}/{episode_id}/{policy.name}"
                            )
                        first_promote = next(
                            (i for i, row in enumerate(trace) if row["deployed_model"] == 1), None
                        )
                        f.write(
                            json.dumps(
                                {
                                    "ba": ba,
                                    "episode_id": episode_id,
                                    "local_episode": local_episode,
                                    "run_id": run_id,
                                    "start_time_utc": start_time.isoformat(),
                                    "policy_seed": seed_id,
                                    "policy": policy.name,
                                    "net_cost": result.net_cost,
                                    "prediction_loss": result.prediction_loss,
                                    "labels": result.requested_labels,
                                    "label_cost": label_cost,
                                    "switches": result.deployment_switches,
                                    "switch_cost": switch_cost,
                                    "promotions": promotions,
                                    "rollbacks": rollbacks,
                                    "first_promotion": first_promote,
                                    "cost_residual": residual,
                                },
                                separators=(",", ":"),
                            )
                            + "\n"
                        )
                    f.flush()
                episode_id += 1
        f.flush()
        os.fsync(f.fileno())
    partial_path.replace(records_path)
    manifest = {
        "protocol": "eia930_f8_2026_confirmation_20261107/PROTOCOL_V2.md",
        "test_opening_sha256": sha256(PILOT / "TEST_OPENING.json"),
        "source_sha256": opening["new_source_sha256"],
        "model_freeze_sha256": opening["model_freeze_sha256"],
        "git_commit_at_open": opening["git_commit"],
        "current_git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "test_window": opening["test_window"],
        "ba_registry": BAS,
        "n_episodes": episode_id,
        "policy_count": len(POLICIES),
        "policy_seeds": SEEDS,
        "coverage_by_ba": coverage,
        "policy_registry": list(POLICIES),
        "records_sha256": sha256(records_path),
        "raw_rows_or_predictions_written": False,
        "assumptions": [
            "historical EIA values are revised snapshots",
            "one-hour label release is simulated",
            "cost units are hypothetical",
        ],
    }
    (PILOT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "episodes": episode_id,
                "policies": len(POLICIES),
                "seeds": SEEDS,
                "records": sum(1 for _ in records_path.open()),
                "output": str(records_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
