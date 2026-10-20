"""Quality checks and descriptive shift evidence; attribution is explicitly inconclusive."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from .bootstrap import mean_difference_interval
from .provenance import sha256, write_json
from .schemas import Manifest, validate_frame


def validate_dataset(directory: Path) -> dict:
    manifest = Manifest.model_validate_json((directory / "dataset_manifest.json").read_text())
    for relative, digest in manifest.files.items():
        if sha256(directory / relative) != digest:
            raise ValueError(f"Checksum mismatch: {relative}")
    frame = pd.read_parquet(directory / "observations.parquet")
    result = validate_frame(frame)
    X = np.stack(frame.features.to_numpy())
    finite = X[np.isfinite(X)]
    result.update(
        dataset=manifest.dataset,
        version=manifest.version,
        feature_missing_rate=float(np.isnan(X).mean()) if X.size else None,
        feature_infinite=int(np.isinf(X).sum()),
        min_feature=float(finite.min()) if len(finite) else None,
        max_feature=float(finite.max()) if len(finite) else None,
        duplicate_feature_target_rows=int(
            (
                pd.DataFrame({"reference": frame.feature_reference})
                if "feature_reference" in frame
                else pd.DataFrame(X)
            )
            .assign(target=frame.target.to_numpy())
            .duplicated()
            .sum()
        ),
        ground_truth=manifest.ground_truth,
        attribution="Inconclusive: descriptive evidence does not identify drift mechanism",
    )
    return result


def diagnostics(directory: Path) -> list[dict]:
    """Compare first/last quarters. Dependence and domain confounding invalidate naive p-value guarantees."""
    frame = pd.read_parquet(directory / "observations.parquet")
    X = np.stack(frame.features.to_numpy())
    n = min(2000, len(X) // 4)
    rows = []
    for j in range(X.shape[1]):
        a, b = X[:n, j], X[-n:, j]
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        row = {
            "dataset": directory.parent.name,
            "version": directory.name,
            "feature": j,
            "n_pre": len(a),
            "n_post": len(b),
            "attribution": "inconclusive",
            "window": "first/last quarter capped at 2000",
            "pvalue_caveat": "uncorrected descriptive KS; may be dependent/confounded",
            "pvalue_method": "asymptotic two-sample KS; descriptive under dependence/confounding",
        }
        if len(a) > 10 and len(b) > 10:
            test = ks_2samp(a, b, method="asymp")
            row.update(
                mean_difference=float(b.mean() - a.mean()),
                ks_statistic=float(test.statistic),
                pvalue=float(test.pvalue),
                iid_mean_se=float(np.sqrt(a.var() / len(a) + b.var() / len(b))),
            )
            if min(len(a), len(b)) >= 20:
                row.update(mean_difference_interval(a, b, seed=42 + j))
                row["uncertainty_caveat"] = (
                    "Moving-block percentile interval; requires within-window stationarity/weak dependence; complete-case gaps and confounding remain"
                )
        rows.append(row)
    # Covariance and label-frequency evidence do not establish a causal drift category.
    complete_a = X[:n][np.isfinite(X[:n]).all(axis=1)]
    complete_b = X[-n:][np.isfinite(X[-n:]).all(axis=1)]
    if X.shape[1] and len(complete_a) > 2 and len(complete_b) > 2:
        rows.append(
            {
                "dataset": directory.parent.name,
                "version": directory.name,
                "feature": "covariance",
                "covariance_frobenius_difference": float(
                    np.linalg.norm(
                        np.atleast_2d(np.cov(complete_b.T)) - np.atleast_2d(np.cov(complete_a.T))
                    )
                ),
                "attribution": "inconclusive; complete-case selection may confound",
            }
        )
    target = frame.target.to_numpy()
    observed = target[np.isfinite(target)]
    if len(np.unique(observed)) <= 20:
        for value in np.unique(observed):
            rows.append(
                {
                    "dataset": directory.parent.name,
                    "version": directory.name,
                    "feature": f"class_{value}",
                    "class_frequency_pre": float(np.mean(target[:n] == value)),
                    "class_frequency_post": float(np.mean(target[-n:] == value)),
                    "attribution": "inconclusive",
                }
            )
    return rows


def validate_all(root: Path):
    results, shift = [], []
    for path in sorted(root.glob("manifests/*.json")):
        pointer = json.loads(path.read_text())
        directory = Path(pointer["path"])
        try:
            results.append(validate_dataset(directory))
            shift.extend(diagnostics(directory))
        except (ValueError, OSError, KeyError) as exc:
            results.append(
                {"dataset": pointer["dataset"], "version": pointer["version"], "error": repr(exc)}
            )
    (root / "reports").mkdir(parents=True, exist_ok=True)
    write_json(root / "reports/validation.json", results)
    pd.DataFrame(shift).to_csv(root / "reports/shift_diagnostics.csv", index=False)
    return results
