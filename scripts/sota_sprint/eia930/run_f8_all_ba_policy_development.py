"""Run the frozen F8 policy panel on all profile-matched EIA-930 BAs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107"
PROFILE = PILOT.parent / "eia930_f8_all_ba_development_20261107/DATASET_PROFILE.json"
sys.path.insert(0, str(ROOT / "scripts/sota_sprint/eia930"))
sys.path.insert(0, str(ROOT / "scripts/failure_atlas_v2_flq"))
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

from profile_all_balancing_authorities import DEV_END, DEV_START, FEATURES, TRAIN_START, load_all
from registry import EXTRA, IMPORT_ERRORS
from simulator import run_episode
from suite import build_suite

T, BUDGET, LABEL_PRICE, SWITCH_COST, ALPHA, DELAY = 2000, 200, 0.05, 5.0, 0.05, 1
SEEDS = 5
SEED_BASE = 2026110711
POLICIES = (
    "PFA-SR:gated_deployment",
    "rmm:gated_deployment+RMM",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "gated_deployment",
    "gated_adaptive_range",
    "E_rb:gated_deployment",
    "cams_adapter",
    "online_llm_picker",
    "model_selector_causal",
    "model_picker_adapter",
    "gong_zhang_paid_obs",
    "qiu_delayed_movement",
    "variance_min_ipw",
    "economic_replacement",
    "CONTROL_never_switch",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def model_pair(
    ba: str, series: dict[str, pd.Series]
) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray]:
    idx = pd.date_range(TRAIN_START, DEV_END - pd.Timedelta(hours=1), freq="h")
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
    train_time = (frame.index >= TRAIN_START) & (frame.index < DEV_START)
    cutoff = float(frame.loc[train_time, "actual"].dropna().quantile(0.90))
    frame["label"] = (frame.actual >= cutoff).astype(float)
    eligible = frame[FEATURES + ["actual", "lag24", "label"]].notna().all(axis=1)
    eligible &= frame.imputed.isna()
    eligible &= (frame.actual > 0) & (frame.forecast > 0) & (frame.lag24 > 0)
    train = frame.loc[eligible & train_time]
    dev = frame.loc[eligible & (frame.index >= DEV_START) & (frame.index < DEV_END)]
    model = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.05,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=1729,
    )
    model.fit(
        train[FEATURES],
        train.label.astype(int),
        sample_weight=compute_sample_weight("balanced", train.label.astype(int)),
    )
    y = (dev.actual.to_numpy() >= cutoff).astype(np.int8)
    incumbent = (dev.lag24.to_numpy() >= cutoff).astype(np.int8)
    challenger = (model.predict_proba(dev[FEATURES])[:, 1] >= 0.5).astype(np.int8)
    return pd.DatetimeIndex(dev.index), np.column_stack((incumbent, challenger)), y


def episodes(index: pd.DatetimeIndex, predictions: np.ndarray, labels: np.ndarray):
    if len(index) == 0:
        return
    breaks = index.to_series().diff().ne(pd.Timedelta(hours=1)).cumsum().to_numpy()
    for group in np.unique(breaks):
        positions = np.flatnonzero(breaks == group)
        nblocks = len(positions) // T
        for block in range(nblocks):
            pos = positions[block * T : (block + 1) * T]
            yield block * T, index[pos[0]], predictions[pos], labels[pos]


def main() -> None:
    records_path = PILOT / "episode_policy_records.jsonl"
    manifest_path = PILOT / "run_manifest.json"
    if records_path.exists() or manifest_path.exists():
        raise SystemExit("policy outcomes exist; refusing to overwrite development run")
    if not PROFILE.exists():
        raise SystemExit("profile gate output is missing")
    profile = json.loads(PROFILE.read_text())
    if not profile["gate_pass"]:
        raise SystemExit("profile gate failed; policies must not run")
    bas = profile["matching_bas"]
    missing = set(POLICIES) - (
        {"PFA-SR:gated_deployment", "rmm:gated_deployment+RMM"}
        | set(EXTRA)
        | {
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
            "variance_min_ipw",
            "economic_replacement",
            "CONTROL_never_switch",
        }
    )
    if missing:
        raise RuntimeError(f"policy factories missing: {sorted(missing)}")
    if IMPORT_ERRORS:
        raise RuntimeError(f"registry import errors: {IMPORT_ERRORS}")
    data = load_all()
    source_manifest = json.loads(
        (
            ROOT
            / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
        ).read_text()
    )
    output_rows = []
    global_episode = 0
    for ba in bas:
        times, preds, y = model_pair(ba, data[ba])
        expected = profile["profiles"][ba]
        disagreement = preds[:, 0] != preds[:, 1]
        disagreement_rate = float(disagreement.mean())
        conditional_accuracy = float((preds[disagreement, 1] == y[disagreement]).mean())
        if len(times) != expected["eligible_dev_events"]:
            raise RuntimeError(f"eligible row count changed after profile screen for {ba}")
        if abs(disagreement_rate - expected["disagreement_frequency"]) > 1e-12:
            raise RuntimeError(f"disagreement profile changed after profile screen for {ba}")
        if abs(conditional_accuracy - expected["challenger_correct_on_disagreements"]) > 1e-12:
            raise RuntimeError(f"conditional accuracy changed after profile screen for {ba}")
        for local_episode, (start_event, start_time, p_ep, y_ep) in enumerate(
            episodes(times, preds, y)
        ):
            for seed_id in range(SEEDS):
                seed = SEED_BASE + seed_id
                policies = build_suite(
                    T,
                    BUDGET,
                    SWITCH_COST,
                    LABEL_PRICE,
                    ALPHA,
                    DELAY,
                    global_episode,
                    seed,
                    names=list(POLICIES),
                    extra=EXTRA,
                )
                for policy in policies:
                    result = run_episode(
                        policy,
                        model_predictions=p_ep,
                        labels=y_ep,
                        delay=DELAY,
                        budget=BUDGET,
                        label_price=LABEL_PRICE,
                        switch_cost=SWITCH_COST,
                        trace=True,
                    )
                    trace = result.records
                    output_rows.append(
                        {
                            "ba": ba,
                            "episode": global_episode,
                            "local_episode": local_episode,
                            "start_event_in_eligible_run": int(start_event),
                            "start_time_utc": start_time.isoformat(),
                            "policy_seed": seed_id,
                            "policy": policy.name,
                            "net_cost": result.net_cost,
                            "prediction_loss": result.prediction_loss,
                            "labels": result.requested_labels,
                            "label_cost": LABEL_PRICE * result.requested_labels,
                            "switches": result.deployment_switches,
                            "switch_cost": SWITCH_COST * result.deployment_switches,
                            "promotions": sum(
                                trace[i].get("deployed_model", 0) == 1
                                and (i == 0 or trace[i - 1].get("deployed_model", 0) == 0)
                                for i in range(len(trace))
                            ),
                            "rollbacks": sum(
                                trace[i].get("deployed_model", 0) == 0
                                and i > 0
                                and trace[i - 1].get("deployed_model", 0) == 1
                                for i in range(len(trace))
                            ),
                            "first_promotion": next(
                                (
                                    i
                                    for i, row in enumerate(trace)
                                    if row.get("deployed_model", 0) == 1
                                ),
                                None,
                            ),
                        }
                    )
            global_episode += 1
    records_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in output_rows)
    )
    scripts = [
        Path(__file__),
        ROOT / "scripts/failure_atlas_v2_flq/suite.py",
        ROOT / "scripts/sota_sprint/registry.py",
        ROOT / "scripts/promising_directions/sota/simulator.py",
        ROOT / "scripts/sota_sprint/pfa_srr_baseline.py",
        ROOT / "scripts/sota_sprint/fam_e.py",
        ROOT / "scripts/failure_atlas_v2_flq/strong_hosts.py",
    ]
    manifest_path.write_text(
        json.dumps(
            {
                "protocol": "eia930_f8_all_ba_policy_development_20261107/PROTOCOL.md",
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "respondents": bas,
                "periods": source_manifest["periods"],
                "raw_file_sha256": source_manifest["raw_file_sha256"],
                "script_sha256": {str(path.relative_to(ROOT)): digest(path) for path in scripts},
                "policies": POLICIES,
                "registry_import_errors": IMPORT_ERRORS,
                "contract": {
                    "T": T,
                    "B": BUDGET,
                    "label_price": LABEL_PRICE,
                    "switch_cost": SWITCH_COST,
                    "alpha": ALPHA,
                    "delay": DELAY,
                    "paired_seeds_per_episode": SEEDS,
                    "seed_base": SEED_BASE,
                },
                "episodes": global_episode,
                "rows": len(output_rows),
                "note": "2022-2023 development replay; revised EIA values and simulated one-hour release; no 2024+ rows used.",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"episodes": global_episode, "rows": len(output_rows), "bas": bas}, indent=2))


if __name__ == "__main__":
    main()
