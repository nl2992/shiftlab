"""Execute retrospective ACS domain comparisons with a train-only reference classifier."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shiftlab.data.group_diagnostics import classification_group_evidence, fit_offline_classifier
from shiftlab.data.provenance import commit, sha256, utc_now, write_json
from shiftlab.data.validation import validate_dataset


def evaluate_comparisons(frame, protocol):
    cache, evidence = {}, []
    domains = set(frame.domain_id.unique())
    for index, comparison in enumerate(protocol["comparisons"]):
        train, test = set(comparison["train_domains"]), set(comparison["test_domains"])
        if not train or not test or train & test or (train | test) - domains:
            raise ValueError(
                "Comparison requires present, nonempty, disjoint training/test domains"
            )
        key = tuple(sorted(train))
        if key not in cache:
            fitting = frame.copy()
            fitting["split"] = np.where(fitting.domain_id.isin(train), "train", "unassigned")
            cache[key] = fit_offline_classifier(fitting)
        probabilities, classes = cache[key]
        costs = np.ones((len(classes), len(classes))) - np.eye(len(classes))
        costs[:, classes == 1] *= 5
        selected = frame.domain_id.isin(train | test).to_numpy()
        part = frame.loc[selected].copy()
        part["split"] = np.where(part.domain_id.isin(train), "train", "test")
        p = probabilities[selected]
        result = classification_group_evidence(part, p, classes, costs)
        result = result.drop(columns=["accuracy_iid_descriptive_se"])
        result["comparison_id"] = index
        result["comparison_kind"] = comparison["kind"]
        result["train_domains"] = ",".join(sorted(train))
        result["uncertainty"] = "No survey-design or extra-sampling variance interval estimated"
        result["weighted_accuracy"] = np.nan
        result["weighted_decision_loss"] = np.nan
        for row_index, row in result.iterrows():
            mask = ((part.domain_id == row.domain) & (part.split == row.split)).to_numpy()
            weights = part.loc[mask, "sample_weight"].to_numpy(float)
            y = part.loc[mask, "target"].to_numpy(float)
            predictions = classes[p[mask].argmax(axis=1)]
            if weights.sum() > 0:
                result.loc[row_index, "weighted_accuracy"] = np.average(
                    predictions == y, weights=weights
                )
                known = np.isin(y, classes)
                if known.all():
                    actions = (p[mask] @ costs.T).argmin(axis=1)
                    target_indices = np.array(
                        [np.flatnonzero(classes == target)[0] for target in y]
                    )
                    result.loc[row_index, "weighted_decision_loss"] = np.average(
                        costs[actions, target_indices], weights=weights
                    )
        evidence.append(result)
    return pd.concat(evidence, ignore_index=True) if evidence else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-report", default="data/reports/folktables_panel/validation.json")
    parser.add_argument("--report-dir", default="data/reports/folktables_panel")
    args = parser.parse_args()
    suite = json.loads(Path(args.suite_report).read_text())
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    all_rows, inputs = [], []
    for entry in suite["completed_tasks"]:
        path = Path(entry["path"])
        validate_dataset(path)
        frame = pd.read_parquet(path / "observations.parquet")
        protocol = json.loads((path / "acs_protocol.json").read_text())
        evidence = evaluate_comparisons(frame, protocol["comparisons"])
        evidence["task"] = entry["task"]
        evidence["version"] = path.name
        all_rows.append(evidence)
        inputs.append(
            {
                "task": entry["task"],
                "version": path.name,
                "manifest_sha256": sha256(path / "dataset_manifest.json"),
            }
        )
        pd.concat(all_rows, ignore_index=True).to_csv(
            report / "comparison_evidence.csv", index=False
        )
        print(entry["task"], len(evidence), flush=True)
    table = pd.concat(all_rows, ignore_index=True)
    held_out = table[table.split == "test"]
    fig, ax = plt.subplots(figsize=(10, 5))
    for task, group in held_out.groupby("task"):
        means = group.groupby("comparison_kind").weighted_accuracy.mean()
        ax.plot(means.index, means.to_numpy(), marker="o", label=task)
    ax.set_ylabel("Mean held-out domain survey-weighted accuracy")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=15)
    ax.legend(fontsize=8)
    ax.set_title("Retrospective domain diagnostics; source/coding differences may confound")
    fig.tight_layout()
    fig.savefig(report / "comparison_accuracy.png", dpi=140)
    plt.close(fig)
    write_json(
        report / "comparison_protocol.json",
        {
            "executed_at": utc_now(),
            "processing_commit": commit(),
            "script_sha256": sha256(Path(__file__)),
            "inputs": inputs,
            "model": "Unweighted LogisticRegression(C=1), numeric source coding; imputation/scaling fit only on designated train domains; no later-domain tuning",
            "utility_origin": "Imposed 5:1 false-negative:false-positive cost; not operational public-policy utility",
            "weighted_metrics": "Original PWGTP weighted rates, without complex-survey or Bernoulli-sampling variance intervals",
            "plot": "Unweighted mean of held-out domain weighted accuracies within each comparison kind; descriptive, not pooled person accuracy",
            "timing": "Annual/coarse domains; no online availability or per-person chronology claimed",
            "attribution": "Inconclusive: population, survey coding, selection and label composition may confound",
        },
    )


if __name__ == "__main__":
    main()
