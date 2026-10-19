"""Preview/export a bounded design; generation requires --execute explicitly."""

import argparse
import json
from pathlib import Path

import yaml

from shiftlab.data.cli import generate
from shiftlab.data.synthetic.planning import SamplingPlan, expand_plan, summarize_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--report", default="data/reports/sampling_plan.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = SamplingPlan.model_validate(yaml.safe_load(Path(args.config).read_text()))
    summary = summarize_plan(plan)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"coverage", "plan"}}, indent=2))
    if args.execute:
        for profile_id, config in expand_plan(plan):
            print(profile_id, generate(config), flush=True)


if __name__ == "__main__":
    main()
