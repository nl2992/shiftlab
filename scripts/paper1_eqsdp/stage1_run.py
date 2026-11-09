"""Stage 1 runner: one candidate's grid + controls + arm R + equality checks, even episodes.

  python stage1_run.py --cand c1 --workers 16
writes outputs/paper1_eqsdp/stage1/<cand>/records.jsonl (+ progress.txt). Reuses the Stage 0 job
runner (same seeds, same streams); the reference ``wald_l0.97_g0.2`` is read from the Stage 0
records (identical keys), not re-run.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_headroom as s0
import stage1_policies as sp
import trace_run as tr


def policy_names(cand: str, ext: bool = False) -> list[str]:
    g = sp.grid_names(cand)
    if ext:  # only the extended control policies (+ arm R for pairing checks)
        return [tr.ARM_R, *g["ext"]]
    g = {k: [x for x in v if x not in g.get("ext", [])] for k, v in g.items() if k != "ext"}
    return [tr.ARM_R, *g["check"], *g["grid"], *g["control_a"], *g["control_b"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, choices=["c1", "c2", "c5"])
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ext", action="store_true", help="run only the extended C1 control grids")
    a = ap.parse_args()
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    sub = a.cand + ("_ext" if a.ext else "")
    out = a.out or str(tr.ROOT / "outputs/paper1_eqsdp/stage1" / sub)
    s0.cmd_run(
        argparse.Namespace(
            out=out, budget=a.budget, policies=policy_names(a.cand, a.ext), workers=a.workers,
            check_orig=False,
        )
    )  # fmt: skip


if __name__ == "__main__":
    main()
