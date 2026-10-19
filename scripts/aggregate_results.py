"""Across-stream bootstrap; duplicated seeds are not independent replicates."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="outputs")
args = parser.parse_args()
root = Path(args.output)
paths = list(root.glob("*/metrics.csv"))
if not paths:
    raise SystemExit("No completed metrics found")
frames = []
for p in paths:
    manifest = json.loads((p.parent / "metadata.json").read_text())
    if manifest["status"] != "complete":
        continue
    protocol = {k: v for k, v in manifest["config"].items() if k not in ["seeds", "output"]}
    protocol_hash = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    frames.append(pd.read_csv(p).assign(run=p.parent.name, protocol_hash=protocol_hash))
if not frames:
    raise SystemExit("No completed runs")
data = pd.concat(frames, ignore_index=True)
data.to_csv(root / "all_metrics.csv", index=False)
rows = []
for key, group in data.groupby(["paper", "shift", "method", "protocol_hash"]):
    group = group.drop_duplicates("seed")
    for metric in ["mse", "coverage", "mean_width", "objective", "policy_regret"]:
        values = group[metric].to_numpy()
        rng = np.random.default_rng(77)
        samples = rng.choice(values, size=(2000, len(values)), replace=True).mean(axis=1)
        lo, hi = np.quantile(samples, [0.025, 0.975])
        rows.append(
            {
                "paper": key[0],
                "shift": key[1],
                "method": key[2],
                "metric": metric,
                "protocol_hash": key[3],
                "n_seeds": len(values),
                "mean": values.mean(),
                "ci_low": lo,
                "ci_high": hi,
            }
        )
pd.DataFrame(rows).to_csv(root / "summary.csv", index=False)
print(root / "summary.csv")
