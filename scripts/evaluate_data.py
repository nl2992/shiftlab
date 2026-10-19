"""Run existing regression baselines against a versioned standardized stream."""

import argparse
import json
from pathlib import Path

from shiftlab.data.benchmark import evaluate_regression

parser = argparse.ArgumentParser()
parser.add_argument("--dataset-path", type=Path, required=True)
parser.add_argument("--paper", type=int, choices=[1, 2, 3], required=True)
args = parser.parse_args()
print(json.dumps(evaluate_regression(args.dataset_path, args.paper), indent=2))
