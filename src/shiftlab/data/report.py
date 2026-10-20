"""Actual quality, oracle validation, baseline evidence and readiness reports."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge

from ..methods import weighted_conformal_quantile
from .gpu.environment import environment
from .provenance import write_json
from .validation import validate_all


def _readiness_labels(
    name: str,
    synthetic: bool,
    classification: bool,
    task_specs: list[dict] | None = None,
    processing_config: dict | None = None,
):
    """Describe study scope from stored or registered tasks without inventing availability."""
    if synthetic:
        return "controlled decision study", "regression/classification stream", "stream ready"
    if classification:
        return (
            "offline classification only",
            "classification prediction-set protocol required",
            "offline domain benchmark; release times unavailable",
        )
    if not task_specs:
        # Immutable legacy manifests remain untouched; recover their registered task meaning
        # from the current adapter and saved acquisition parameters for reporting only.
        from .tasks import dataset_task_specs

        try:
            task_specs = dataset_task_specs(name, processing_config or {})
        except (KeyError, TypeError, ValueError):
            task_specs = []

    task_kinds = {spec.get("task_kind") for spec in task_specs}
    has_forecast_task = bool(task_kinds & {"regression", "quantile", "volatility", "binary"})
    has_task = bool(task_specs)
    paper1 = "retrospective; utility imposed"
    paper2 = (
        "retrospective forecast/conformal task; availability unknown"
        if has_forecast_task
        else "requires task/conformal target protocol"
    )
    paper3 = (
        "retrospective task; release-time protocol unknown"
        if has_task
        else "requires task and release-time protocol"
    )
    return paper1, paper2, paper3


def build_report(root: Path):
    report = root / "reports"
    report.mkdir(parents=True, exist_ok=True)
    quality = validate_all(root)
    pointers = [json.loads(p.read_text()) for p in sorted(root.glob("manifests/*.json"))]
    write_json(
        report / "dataset_manifest.json", {"environment": environment(), "datasets": pointers}
    )
    lines = [
        "# Data quality report",
        "",
        "Unknown availability timestamps are retained as unknown. No automatic filling or changepoint attribution.",
        "",
    ]
    if (report / "invalidated_versions.json").exists():
        lines.extend(
            [
                "## Invalidated historical versions",
                (report / "invalidated_versions.json").read_text(),
                "",
            ]
        )
    for row in quality:
        lines.append("- " + json.dumps(row))
    (report / "data_quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    validation = [
        "# Synthetic validation",
        "",
        "Checks use actual stored observations. Oracle radii describe the DGP, not fitted-model residuals. Monte Carlo deviations are diagnostic, not guaranteed test power.",
        "Each bullet names one immutable stored version and its generation configuration. Versions are not independent replicates.",
        "",
    ]
    readiness = [
        "# Experiment readiness",
        "",
        "| Dataset version | Paper 1 | Paper 2 | Paper 3 | Timing/ground truth |",
        "|---|---|---|---|---|",
    ]
    from .catalogue import SOURCES

    fig, ax = plt.subplots(figsize=(11, 4))
    acquired = {p["dataset"] for p in pointers}
    names = list(SOURCES)
    ax.bar(names, [1 if name in acquired else 0 for name in names])
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("Acquired and processed (1=yes)")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(report / "acquisition_status.png", dpi=140)
    plt.close(fig)
    evidence = []
    for pointer in pointers:
        directory = Path(pointer["path"])
        frame = pd.read_parquet(directory / "observations.parquet")
        X = np.stack(frame.features.to_numpy())
        y = frame.target.to_numpy()
        n = len(frame)
        synthetic = pointer["ground_truth"] == "synthetic_known"
        name = pointer["dataset"]
        oracle = None
        if synthetic:
            oracle = pd.read_parquet(directory / "evaluator_only/oracle.parquet")
            residual = y - oracle.conditional_mean.to_numpy()
            se = float(np.std(residual) / np.sqrt(n))
            radius = oracle.radius_90.to_numpy()
            finite = np.isfinite(radius)
            coverage = (
                float(np.mean(np.abs(residual[finite]) <= radius[finite])) if finite.any() else None
            )
            config = pointer["processing_config"]
            run_identity = (
                f"{name}@{pointer['version']} (n={n}, d={X.shape[1]}, "
                f"seed={config.get('seed', 'unknown')}, severity={config.get('severity', 'unknown')}, "
                f"pattern={config.get('pattern', 'unknown')})"
            )
            validation.append(
                f"- `{run_identity}`: mean residual={np.mean(residual):.5f}, iid descriptive SE={se:.5f}, oracle 90% radius coverage={coverage}; temporal cases require dependence-aware SE."
            )
            if name == "ar1":
                validation.append(
                    f"  Lag-1 autocorrelation={np.corrcoef(X[:-1, 0], X[1:, 0])[0, 1]:.4f}; configured rho={pointer['processing_config']['rho']}."
                )
        from .synthetic.generators import CLASSIFICATION

        classification = name in CLASSIFICATION or name in {
            "gas_sensor",
            "folktables",
            "wilds",
            "criteo",
        }

        paper1, paper2, paper3 = _readiness_labels(
            name,
            synthetic,
            classification,
            pointer.get("task_specs", []),
            pointer.get("processing_config", {}),
        )
        readiness.append(
            f"| `{name}@{pointer['version']}` | {paper1} | {paper2} | {paper3} | {pointer['ground_truth']}; {'known simulation clock' if synthetic else 'historical/coarse; no true changes'} |"
        )
        # No test fitting; train/calibration/test must be present with enough usable labels.
        train = (frame.split == "train").to_numpy() & np.isfinite(y)
        cal = (frame.split == "calibration").to_numpy() & np.isfinite(y)
        test = (frame.split == "test").to_numpy() & np.isfinite(y)
        if (
            X.shape[1]
            and not classification
            and train.sum() > 20
            and cal.sum() > 10
            and test.sum() > 10
        ):
            imputer = SimpleImputer(keep_empty_features=True).fit(X[train])
            clean = imputer.transform(X)
            model = Ridge().fit(clean[train], y[train])
            pred = model.predict(clean)
            radius = weighted_conformal_quantile(abs(y[cal] - pred[cal]), 0.1)
            loss = (y - pred) ** 2
            covered = (abs(y - pred) <= radius).astype(float)
            covered[~test] = np.nan
            evidence.append(
                {
                    "dataset": name,
                    "version": pointer["version"],
                    "test_mse": float(np.mean(loss[test])),
                    "test_coverage": float(np.mean(covered[test])),
                    "role": "offline diagnostic, not an online result; train-only imputation",
                }
            )
        else:
            pred = np.full(n, np.nan)
            loss = np.full(n, np.nan)
            covered = np.full(n, np.nan)
        # Nine required plot categories, always based on stored measured/generated data.
        if synthetic or name in ["gas_sensor", "noaa", "opsd"]:
            fig, axes = plt.subplots(3, 3, figsize=(14, 10))
            ax = axes.ravel()
            quarter = max(1, n // 4)
            ax[0].hist(X[:quarter, 0], bins=35, alpha=0.5, label="first quarter")
            ax[0].hist(X[-quarter:, 0], bins=35, alpha=0.5, label="last quarter")
            ax[0].set_title("Feature distributions")
            ax[0].legend()
            ks_times, ks_values = [], []
            ref = X[: min(200, n // 4), 0]
            ref = ref[np.isfinite(ref)]
            for position in range(400, n, 100):
                current = X[position - 200 : position, 0]
                current = current[np.isfinite(current)]
                if len(ref) > 10 and len(current) > 10:
                    ks_times.append(position)
                    ks_values.append(ks_2samp(ref, current).statistic)
            ax[1].plot(ks_times, ks_values)
            ax[1].set_title("Marginal x0 KS statistic (descriptive)")
            ax[2].scatter(X[:: max(1, n // 2000), 0], y[:: max(1, n // 2000)], s=2)
            ax[2].set_title("Conditional relationship (observed)")
            ax[3].plot(pd.Series(loss).rolling(100, min_periods=30).mean())
            ax[3].set_title("Train-fitted prediction loss")
            if oracle is not None:
                ax[4].plot(oracle.probability_positive, oracle.oracle_risk, ".", ms=1)
                truth = json.loads((directory / "evaluator_only/dgp.json").read_text())
                for change in truth["change_times"]:
                    ax[1].axvline(change, c="black", ls="--", alpha=0.2)
                for a, b in truth["transition_intervals"]:
                    ax[1].axvspan(a, b, color="gray", alpha=0.2)
            else:
                ax[4].text(0.05, 0.5, "No true oracle risk available", transform=ax[4].transAxes)
            ax[4].set_title("Oracle decision risk (synthetic only)")
            delay = frame.label_available_time - frame.label_event_time
            ax[5].plot(delay)
            ax[5].set_title("Known label availability delay")
            ax[6].plot(pd.Series(np.isnan(X).mean(axis=1)).rolling(100, min_periods=1).mean())
            ax[6].plot(
                frame.label_available_time.isna().astype(float).rolling(100, min_periods=1).mean(),
                label="unknown/missing label time",
            )
            ax[6].set_title("Feature missingness / unknown label times")
            ax[6].legend()
            ax[7].plot(pd.Series(covered).rolling(100, min_periods=30).mean())
            ax[7].axhline(0.9, c="gray", ls=":")
            ax[7].set_title("Offline rolling empirical coverage")
            ax[8].bar(["rows", "features"], [n, X.shape[1]])
            ax[8].set_yscale("log")
            ax[8].set_title("Acquired and schema-validated")
            fig.suptitle(f"{name}: {pointer['version']}")
            fig.tight_layout()
            fig.savefig(report / f"{name}-{pointer['version']}.png", dpi=130)
            plt.close(fig)
    pd.DataFrame(evidence).to_csv(report / "baseline_evidence.csv", index=False)
    (report / "synthetic_validation.md").write_text("\n".join(validation) + "\n", encoding="utf-8")
    readiness += [
        "",
        "Classification prediction sets and time-dependent real-data availability assumptions require additional protocols.",
        "For immutable legacy manifests without embedded task_specs, readiness uses the current registered adapter binding and saved processing configuration; this does not establish source release availability.",
        "No real-world domain change is a verified changepoint. No dynamic adaptation oracle or application-grounded utility has been inferred.",
    ]
    (report / "experiment_readiness.md").write_text("\n".join(readiness) + "\n", encoding="utf-8")
    return report
