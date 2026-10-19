"""Run a configured multi-task ACS suite; network acquisition requires --execute."""

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from shiftlab.data.provenance import utc_now, write_json
from shiftlab.data.real.folktables import TASKS, acquire
from shiftlab.data.validation import validate_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("--report-dir", default="data/reports/folktables_panel")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    configuration = yaml.safe_load(Path(args.config).read_text())
    tasks = configuration.pop("tasks", sorted(TASKS))
    if not tasks or len(set(tasks)) != len(tasks) or not set(tasks) <= TASKS:
        parser.error("Require unique supported Folktables tasks")
    if not args.execute:
        print(
            json.dumps({"dry_run": True, "tasks": tasks, "configuration": configuration}, indent=2)
        )
        return
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    versions, counts = [], []
    for task in tasks:
        path = acquire({**configuration, "tasks": [task]}, Path(args.root))
        quality = validate_dataset(path)
        manifest = json.loads((path / "dataset_manifest.json").read_text())
        frame = pd.read_parquet(path / "observations.parquet")
        for domain, group in frame.groupby("domain_id", sort=False):
            weights = group.sample_weight.to_numpy(float)
            target = group.target.to_numpy(float)
            counts.append(
                {
                    "task": task,
                    "version": path.name,
                    "domain": domain,
                    "rows": len(group),
                    "positive_rate_unweighted": float(target.mean()),
                    "positive_rate_survey_weighted": float((weights * target).sum() / weights.sum())
                    if weights.sum()
                    else None,
                    "original_survey_weight_sum": float(weights.sum()),
                    "unknown_event_times": int(group.event_time.isna().sum()),
                    "unknown_label_availability": int(group.label_available_time.isna().sum()),
                }
            )
        protocol = json.loads((path / "acs_protocol.json").read_text())
        versions.append(
            {
                "task": task,
                "path": str(path),
                "manifest": manifest,
                "quality": quality,
                "protocol": protocol,
            }
        )
        # Publish progress after every finished task, so interrupted suites retain evidence.
        pd.DataFrame(counts).to_csv(report / "domain_counts.csv", index=False)
        write_json(
            report / "validation.json",
            {
                "executed_at": utc_now(),
                "completed_tasks": versions,
                "requested_tasks": tasks,
                "weighted_rate_scope": "Descriptive ratio using original PWGTP; no complex-survey confidence interval or population-total estimate",
            },
        )
        print(task, path, quality["rows"], flush=True)


if __name__ == "__main__":
    main()
