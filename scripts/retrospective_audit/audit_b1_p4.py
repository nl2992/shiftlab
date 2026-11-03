"""Recompute the B1 P4-versus-P3 persistence gate from archived paired seeds."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results/b1"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/B1_P4_PAIRED_AUDIT.json"


def run() -> dict[str, object]:
    expected_hashes = {
        "summary.json": "0062aec5eeba38caf93cdc69d307c9b957928ba0450b9911447566fc010a562e",
        "per_seed.npz": "18d9d45ee81b08feaec04c06f4b4494648a00507b55a86409641cf8130994183",
    }
    for name, expected in expected_hashes.items():
        actual = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f"B1 archived hash mismatch: {name}")
    summary = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    seed_base = int(summary["meta"]["seed_base"])
    n = int(summary["meta"]["seeds"])
    draws = int(summary["meta"]["bootstrap_resamples"])
    indices = np.random.default_rng(seed_base + 7).integers(0, n, size=(draws, n))
    rows = []
    max_error = 0.0
    with np.load(SOURCE / "per_seed.npz") as data:
        for budget in (200, 400):
            for switch_cost in (5, 20):
                key = f"B{budget}_cs{switch_cost}"
                q2 = summary["q2_settings"][key]
                w3_p3 = data[f"W3|B{budget}|cs{switch_cost}|P3|cost"]
                w3_p4 = data[f"W3|B{budget}|cs{switch_cost}|P4|cost"]
                w1_p3 = data[f"W1|B{budget}|cs{switch_cost}|P3|cost"]
                w1_p4 = data[f"W1|B{budget}|cs{switch_cost}|P4|cost"]
                if not all(len(x) == n for x in (w3_p3, w3_p4, w1_p3, w1_p4)):
                    raise AssertionError(f"incomplete B1 cell {key}")
                diff = w3_p4 - w3_p3
                boot = diff[indices].mean(axis=1)
                values = {
                    "mean": float(diff.mean()),
                    "lo": float(np.percentile(boot, 2.5)),
                    "hi": float(np.percentile(boot, 97.5)),
                }
                for field, value in values.items():
                    error = abs(value - float(q2["w3_p4_minus_p3"][field]))
                    max_error = max(max_error, error)
                    if error > 1e-10:
                        raise AssertionError(f"W3 paired interval mismatch {key}/{field}")
                w3_gain = float((w3_p3.mean() - w3_p4.mean()) / w3_p3.mean())
                w1_worse = float(w1_p4.mean() / w1_p3.mean() - 1)
                for field, value in (
                    ("w3_relative_gain", w3_gain),
                    ("w1_p4_relative_worse", w1_worse),
                ):
                    error = abs(value - float(q2[field]))
                    max_error = max(max_error, error)
                    if error > 1e-10:
                        raise AssertionError(f"relative cost mismatch {key}/{field}")
                pass_w3 = w3_gain >= 0.1 and values["hi"] < 0
                pass_w1 = w1_worse <= 0.02
                if pass_w3 != q2["pass_w3"] or pass_w1 != q2["pass_w1"]:
                    raise AssertionError(f"Q2 gate mismatch {key}")
                rows.append(
                    {
                        "setting": key,
                        "w3_p4_minus_p3_mean_cost": values["mean"],
                        "w3_paired_bootstrap_95": [values["lo"], values["hi"]],
                        "w3_relative_cost_gain": w3_gain,
                        "w1_relative_cost_worsening": w1_worse,
                        "pass_w3_10pct_and_ci": pass_w3,
                        "pass_w1_no_more_than_2pct_worse": pass_w1,
                    }
                )
    if summary["decisions"]["Q2"] != "NOT SUPPORTED":
        raise AssertionError("historical B1 Q2 verdict changed")
    return {
        "scope": "B1 archived 500 paired seeds per world/setting; source simulator not replayed",
        "source_hashes_verified": len(expected_hashes),
        "bootstrap_draws": draws,
        "max_numeric_error": max_error,
        "settings": rows,
        "historical_q2_verdict": "NOT SUPPORTED",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{len(result['settings'])} settings, max error {result['max_numeric_error']}")
