"""Independently recompute archived generator losses without rerunning worlds."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.special import expit
from scipy.stats import t as student_t


def hash_configuration(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def verify_losses(raw, config):
    """Separate formula implementation: no make_world or loss helper imports."""
    x, y, regime = raw["features"], raw["outcomes"], raw["regime_weight"]
    family, scenario = config["family"], config["scenario"]
    if family == "G2":
        score = 2 * np.sin(x[:, 0]) + 0.8 * (x[:, 1] ** 2 - 1) - 0.6 * x[:, 2]
    elif family == "G4":
        score = 0.3 * np.tanh(x[:, 0]) - 0.1 * np.tanh(x[:, 1])
    else:
        score = 1.5 * x[:, 0] - 0.6 * x[:, 1]
    changed = score.copy()
    if scenario in (
        "harmful_concept",
        "risk_without_harm",
        "transient_challenger",
        "challenger_optimal",
        "labels_too_expensive",
        "gradual",
        "recurrent",
    ):
        changed *= 1 - 2 * regime
    elif scenario == "incumbent_best":
        changed *= 1 + 0.4 * regime
    elif scenario == "localized_harm":
        group = x[:, 2] == 1 if family == "G2" else x[:, 2] > 1.645
        changed *= 1 - 2 * regime * group
    if scenario == "tied_models":
        score[:] = 0
        changed[:] = 0
    weight = np.full(len(x), 0.1)
    if scenario == "harm_without_accuracy":
        weight += 0.9 * regime
    if scenario == "localized_harm":
        weight = np.where(group, 1, 0.02)
    nominal_weight = np.full(len(x), 0.1) if scenario == "harm_without_accuracy" else weight
    if family != "G4":
        forecasts = np.column_stack((expit(score), expit(-score), np.full(len(x), 0.5)))
        actions = (forecasts >= 0.5).astype(float)
        if scenario == "risk_without_harm":
            actions[:] = -1
        realized_prediction = (forecasts - y[:, None]) ** 2
        realized_decision = np.where(actions == -1, 0.2, weight[:, None] * (actions != y[:, None]))
        offset = 0.4 * (2 * raw["hidden_state"] - 1) if family == "G3" else 0

        def expected(signal, cost):
            p = expit(signal + offset)[:, None]
            prediction = p * (1 - forecasts) ** 2 + (1 - p) * forecasts**2
            wrong_probability = np.where(actions == 1, 1 - p, p)
            decision = np.where(actions == -1, 0.2, cost[:, None] * wrong_probability)
            return prediction, decision

        expected_prediction, expected_decision = expected(changed, weight)
        nominal_prediction, nominal_decision = expected(score, nominal_weight)
    else:
        forecasts = np.column_stack((score, -score, np.zeros(len(x))))
        actions = np.clip(forecasts / 0.12, -1, 1)
        if scenario == "risk_without_harm":
            actions[:] = 0

        def decision(position, outcome, cost):
            value = position * outcome
            return (
                0.5 - 0.3 * value + 0.15 * cost * position**2 + 0.05 * cost * np.maximum(-value, 0)
            )

        realized_prediction = (forecasts - y[:, None]) ** 2 / 4
        realized_decision = decision(actions, y[:, None], weight[:, None])
        quantiles = student_t.ppf((np.arange(64) + 0.5) / 64, df=3)
        volatility = 0.08 + 0.12 * raw["hidden_state"]

        def expected(signal, cost):
            support = np.clip(signal[:, None] + volatility[:, None] * quantiles, -1, 1)
            prediction = ((forecasts[:, :, None] - support[:, None, :]) ** 2).mean(axis=2) / 4
            costs = decision(actions[:, :, None], support[:, None, :], cost[:, None, None])
            return prediction, costs.mean(axis=2)

        expected_prediction, expected_decision = expected(changed, weight)
        nominal_prediction, nominal_decision = expected(score, nominal_weight)
    for name, calculated in (
        ("predictive_losses", realized_prediction),
        ("decision_losses", realized_decision),
        ("expected_predictive_losses", expected_prediction),
        ("expected_decision_losses", expected_decision),
        ("nominal_predictive_losses", nominal_prediction),
        ("nominal_decision_losses", nominal_decision),
    ):
        np.testing.assert_allclose(raw[name], calculated, rtol=1e-12, atol=1e-12, err_msg=name)


def verify_snapshot(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    with sqlite3.connect(
        (root / "experiments.sqlite").resolve().as_uri() + "?mode=ro", uri=True
    ) as db:
        events = db.execute("SELECT run_id,phase,payload FROM events ORDER BY sequence").fetchall()
    starts = {run_id: json.loads(p) for run_id, phase, p in events if phase == "start"}
    terminal = {run_id: json.loads(p) for run_id, phase, p in events if phase == "terminal"}
    assert len(starts) == len(terminal) == len(manifest["jobs"]) == 52
    assert starts.keys() == terminal.keys()
    source_hash = hashlib.sha256()
    with ZipFile(root / "executed_source.zip") as archive:
        for name in sorted(archive.namelist()):
            source_hash.update(name.encode() + b"\0")
            source_hash.update(hashlib.sha256(archive.read(name)).digest())
    job_map = {}
    for job in manifest["jobs"]:
        metadata = job["metadata"].copy()
        metadata["component_configuration"] = {
            "declared": metadata["component_configuration"],
            "argv": job["argv"],
        }
        job_map[hash_configuration(metadata)] = metadata
    assert len(job_map) == 52
    counts, diagnostics = {}, []
    for run_id, record in terminal.items():
        assert record["execution_status"] == "completed", record["failure_reason"]
        assert record["configuration_hash"] in job_map
        assert record["source_hash"] == source_hash.hexdigest()
        for key in ("configuration_hash", "code_commit", "source_hash"):
            assert record[key] == starts[run_id][key]
        with np.load(root / run_id / "evaluator_world.npz", allow_pickle=False) as raw:
            config = record["component_configuration"]["declared"]
            verify_losses(raw, config)
            metrics = record["secondary_metrics"]
            risk = (raw["expected_predictive_losses"] - raw["nominal_predictive_losses"])[
                :, 0
            ].mean()
            harm = (raw["expected_decision_losses"] - raw["nominal_decision_losses"])[:, 0].mean()
            assert abs(risk - metrics["predictive_deterioration"]) < 1e-12
            assert abs(harm - metrics["decision_deterioration"]) < 1e-12
        assert record["labels_used"] <= 64
        assert (
            record["labels_used"]
            == metrics["received_labels_by_horizon"] + metrics["pending_at_horizon"]
        )
        family, scenario = record["generator_family"], record["shift_type"]
        if scenario == "benign_covariate":
            assert metrics["mean_feature_displacement"] > 2 and risk == harm == 0
        elif scenario == "risk_without_harm":
            assert risk > 0.01 and abs(harm) < 1e-12
        elif scenario == "harm_without_accuracy":
            assert risk == 0 and harm > 0.01
        counts[family] = counts.get(family, 0) + 1
        diagnostics.append(
            {"family": family, "scenario": scenario, "risk_change": risk, "cost_change": harm}
        )
    assert set(counts.values()) == {13}
    return {
        "verified_worlds": 52,
        "registry_events": len(events),
        "family_counts": counts,
        "source_hash": source_hash.hexdigest(),
        "raw_loss_recomputation_passed": True,
        "matched_dimension_relations_passed": True,
        "diagnostics": diagnostics,
        "interpretation": "generator validation only; no SOTA, power or novelty conclusion",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    result = verify_snapshot(args.snapshot)
    with (args.snapshot / "independent_verification.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({key: value for key, value in result.items() if key != "diagnostics"}))


if __name__ == "__main__":
    main()
