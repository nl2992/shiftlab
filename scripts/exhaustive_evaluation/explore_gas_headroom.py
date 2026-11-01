"""Registered exploratory gas action-bank diagnostic; previously exposed batches."""

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.datasets import load_svmlight_file
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def decision_cost(probability, labels, costs):
    action = (probability @ costs.T).argmin(axis=1)
    return costs[action, labels.astype(int) - 1]


def main():
    regpath = DOC / "gas_headroom_registration.json"
    if regpath.exists():
        raise FileExistsError("Inspect existing artifacts; do not silently rerun")
    archive = ROOT / "outputs/exhaustive_evaluation/gas_source/uci224.zip"
    expected = json.loads((DOC / "gas_source_manifest.json").read_text())["sha256"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exploratory; all batches have prior repository exposure",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "archive_sha256": expected,
        "bank": "incumbent train1-3 C=1; candidates train1-5 C=.01,.1,1; standardized logistic max_iter=1000",
        "selection": "batch6 minimum decision cost including incumbent; fixed order tie break",
        "primary": "symmetric decision cost; batches7-10 pooled and individually",
        "sensitivity": "class6 false-negative cost multipliers2,5; reported separately",
        "limits": "no online ordering/delay/safety claim, no independent confirmation, no new algorithm",
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        batches = {
            b: load_svmlight_file(
                io.BytesIO(z.read(f"Dataset/batch{b}.dat")), n_features=128, zero_based=False
            )
            for b in range(1, 11)
        }
    assert sum(len(y) for _, y in batches.values()) == 13910
    data = {b: (x.toarray(), y) for b, (x, y) in batches.items()}
    probabilities = {}
    for name, end, c in [
        ("incumbent", 3, 1),
        ("candidate_C.01", 5, 0.01),
        ("candidate_C.1", 5, 0.1),
        ("candidate_C1", 5, 1),
    ]:
        x = np.concatenate([data[b][0] for b in range(1, end + 1)])
        y = np.concatenate([data[b][1] for b in range(1, end + 1)])
        assert np.isfinite(x).all() and set(y) == set(range(1, 7))
        model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=1000))
        model.fit(x, y)
        np.testing.assert_array_equal(model[-1].classes_, np.arange(1, 7))
        probabilities[name] = {b: model.predict_proba(data[b][0]) for b in range(6, 11)}
    rows, selections = [], []
    for multiplier in (1, 2, 5):
        costs = np.ones((6, 6)) - np.eye(6)
        costs[:, 5] *= multiplier
        validation = {
            name: float(decision_cost(p[6], data[6][1], costs).mean())
            for name, p in probabilities.items()
        }
        selected = min(validation, key=validation.get)
        selections.append(
            {"class6_multiplier": multiplier, "selected": selected, "validation_costs": validation}
        )
        for name, p in probabilities.items():
            aggregate = []
            for b in range(7, 11):
                loss = decision_cost(p[b], data[b][1], costs)
                aggregate.append(loss)
                rows.append(
                    {
                        "multiplier": multiplier,
                        "model": name,
                        "batch": b,
                        "n": len(loss),
                        "mean_cost": float(loss.mean()),
                        "selected": name == selected,
                    }
                )
            rows.append(
                {
                    "multiplier": multiplier,
                    "model": name,
                    "batch": "pooled",
                    "n": sum(map(len, aggregate)),
                    "mean_cost": float(np.concatenate(aggregate).mean()),
                    "selected": name == selected,
                }
            )
    result = {"status": "completed", "selections": selections, "rows": rows}
    (DOC / "gas_headroom_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"selections": selections, "pooled": [r for r in rows if r["batch"] == "pooled"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
