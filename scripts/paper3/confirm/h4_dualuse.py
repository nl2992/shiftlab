"""H4 confirmation: wraps scripts/paper3/dualuse/run_kill.py logic (unchanged computation) with
base 5303300000, R=40000, boundary (noise-label) null gamma=0, m=5 and m=40, alpha=.05.
Appends the run_kill ledger row to ledger/dualuse.jsonl as run_kill does; we also write confirm.jsonl."""

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import OUT, ROOT, ledger

PY = sys.executable
res = {}
t0 = time.time()
for m in (5, 40):
    tag = f"confirm_H4_noise_m{m}"
    cfg = json.dumps({"gamma": 0.0, "m": m, "horizons": [100]})
    subprocess.run(
        [
            PY,
            "scripts/paper3/dualuse/run_kill.py",
            "--tag",
            tag,
            "--R",
            "40000",
            "--base",
            "5303300000",
            "--cfg",
            cfg,
        ],
        cwd=ROOT,
        check=True,
    )
    for line in open(  # noqa: SIM115
        ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/dualuse.jsonl"
    ):
        r = json.loads(line)
        if r.get("tag") == tag:
            res[m] = r["result"]["rates"]["preq"]
sup = all(res[m]["ci"][1] <= 0.05 for m in res)
out = {"H4_SUPPORTED": bool(sup), "preq": res}
(OUT / "h4").mkdir(exist_ok=True)
(OUT / "h4" / "summary.json").write_text(json.dumps(out, indent=1))
ledger(
    "H4",
    "confirm_run",
    {"base": 5303300000, "R": 40000, "alpha": 0.05, "m": [5, 40], "gamma": 0.0},
    out,
    time.time() - t0,
)
print(out)
