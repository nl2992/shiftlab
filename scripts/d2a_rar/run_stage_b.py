"""WP6 Stage-B CLI: screen candidate identities on the frozen light dev suite and append ledger records.

Examples (PYTHONPATH=src):
  python scripts/d2a_rar/run_stage_b.py --candidate CAND-... [--candidate ...]   # foreground smoke
  python scripts/d2a_rar/run_stage_b.py --all [--limit N] [--workers 4]           # resumable tranche
The orchestrator is the only ledger writer; workers are subprocesses with a hard 300 s wall-clock timeout.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from shiftlab.autoresearch import ledger as lg
from shiftlab.autoresearch import stage_b as sb
from shiftlab.autoresearch.preflight import run_named_smoke


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--skip-smoke-tests", action="store_true")
    a = ap.parse_args()
    if a.workers > 4:
        ap.error("max 4 parallel workers")
    batch = sb.load_batch()
    if a.candidate:
        want = set(a.candidate)
        batch = [c for c in batch if c["candidate_id"] in want]
    elif not a.all:
        ap.error("pass --candidate ID or --all")
    sb.STAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"ledger head before: {lg.head()}  ({time.strftime('%F %T')})", flush=True)
    if not a.skip_smoke_tests:
        r = run_named_smoke()
        print(
            "guard smoke tests:", r["returncode"], r["tail"].strip().splitlines()[-1:], flush=True
        )
        if r["returncode"] != 0:
            print("guard smoke tests FAILED; refusing to screen", file=sys.stderr)
            return 1
    out = sb.run_tranche(
        batch, max_workers=a.workers, limit=a.limit, log=lambda m: print(m, flush=True)
    )
    print("finished:", out, flush=True)
    print("ledger:", lg.verify(), flush=True)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    raise SystemExit(main())
