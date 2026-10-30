"""Read-only verification of a running or complete development screen."""
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np


def verify(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    with sqlite3.connect((root / "experiments.sqlite").resolve().as_uri() + "?mode=ro", uri=True) as db:
        events = db.execute("SELECT run_id,phase,payload FROM events ORDER BY sequence").fetchall()
    starts = {i: json.loads(p) for i, phase, p in events if phase == "start"}
    terminal = {i: json.loads(p) for i, phase, p in events if phase == "terminal"}
    assert terminal.keys() <= starts.keys()
    assert len(starts) <= len(manifest["jobs"]) == 540
    hashes = set()
    failures = []
    checked = []
    for run_id, record in terminal.items():
        original = starts[run_id]
        for field in ("configuration_hash", "code_commit", "source_hash", "random_seed"):
            assert record[field] == original[field]
        metadata = {k: v for k, v in original.items() if k not in (
            "execution_status", "configuration_hash", "failure_reason", "primary_metric",
            "secondary_metrics", "uncertainty_estimates", "runtime", "peak_memory", "labels_used", "artifacts",
            "predictive_degradation", "decision_harm",
        )}
        # The manifest is authoritative for which explicit null fields were supplied.
        expected = []
        for job in manifest["jobs"]:
            candidate = dict(job["metadata"])
            candidate["component_configuration"] = {
                "declared": candidate.get("component_configuration"), "argv": job["argv"]
            }
            encoded = json.dumps(candidate, sort_keys=True, separators=(",", ":"), allow_nan=False)
            expected.append(hashlib.sha256(encoded.encode()).hexdigest())
        assert record["configuration_hash"] in expected
        assert record["configuration_hash"] not in hashes
        hashes.add(record["configuration_hash"])
        if record["execution_status"] != "completed":
            failures.append({"run_id": run_id, "reason": record["failure_reason"]})
            continue
        metrics = record["secondary_metrics"]
        with np.load(root / run_id / "trajectory.npz", allow_pickle=False) as raw:
            n = len(raw["queried"])
            assert n == 512
            assert raw["queried"].sum() == metrics["labels_used"] <= metrics["hard_label_cap"]
            for name in ("effective_propensity", "requested_propensity"):
                assert np.isfinite(raw[name]).all()
                assert np.all((raw[name] >= 0) & (raw[name] <= 1))
            assert not np.isnan(raw["log_e_values"]).any()
            for kind in ("expected", "realized"):
                total = raw[f"{kind}_deployed_loss"].sum() + raw["label_charge"].sum() + raw["switch_charge"].sum()
                assert np.isclose(total, metrics[f"{kind}_net_cost"])
            models = raw["deployed_model"]
            expected_loss = raw["evaluator_expected_model_losses"][np.arange(n), models]
            np.testing.assert_array_equal(expected_loss, raw["expected_deployed_loss"])
            assert np.count_nonzero(np.diff(np.r_[0, models])) == metrics["switches"]
            regret = (expected_loss - raw["evaluator_expected_model_losses"].min(axis=1)).sum()
            assert np.isclose(regret, metrics["expected_available_model_regret"])
            assert metrics["source_labels"] == 512
        checked.append(run_id)
    return {
        "manifest_jobs": 540, "started": len(starts), "terminal": len(terminal),
        "verified_trajectories": len(checked), "failures": failures,
        "complete": len(terminal) == 540, "verified_run_ids": checked,
        "scope": "record provenance and accounting only; no algorithm superiority conclusion",
    }


if __name__ == "__main__":
    result = verify(Path("outputs/sota_search/development_screen_v1"))
    print(json.dumps({k: v for k, v in result.items() if k != "verified_run_ids"}))
