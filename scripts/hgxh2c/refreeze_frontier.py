"""Recompute frontier.json from the existing stage-2 summary.parquet (no stage-2 rerun) and re-freeze it."""

import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from shiftlab.hgxh2c import freeze, stats

out = ROOT / "outputs/hgxh2c/stage2"
fp, old = out / "frontier.json", out / "frontier_v1_invalid.json"
if not old.exists():
    shutil.copy(fp, old)
prev = json.loads(old.read_text("utf-8"))
fr = stats.frontier(pd.read_parquet(out / "summary.parquet"), registry=prev["methods"])
fr["methods"] = prev["methods"]
fr["config"] = {
    **prev["config"],
    "reason": "A4: track-filter + different-null exclusion",
    "old_sha256": hashlib.sha256(old.read_bytes()).hexdigest(),
}
fp.write_text(json.dumps(fr, indent=1, sort_keys=True))
print("old", fr["config"]["old_sha256"], "\nregistered", freeze.freeze("frontier", fp))
for t in "BCJ":
    c = Counter(m for k, v in fr["frontier"].items() if k.startswith(t + "|") for m in v)
    print(t, dict(c.most_common()))
print("references", fr["references"], "excluded", fr["excluded"])
