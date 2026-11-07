"""WP6 Stage-B tranche-2 CLI (Amendment A1: DEV_SUITE_v2, calibrated_v1 hosts, A1 comparator set).

  python scripts/d2a_rar/run_stage_b_t2.py --write-scope      # select scope (A1 i-ii), write tranche2_scope.json, no compute
  python scripts/d2a_rar/run_stage_b_t2.py --run [--workers 12] [--limit N]   # resumable (ledger = checkpoint)
  python scripts/d2a_rar/run_stage_b_t2.py --report            # rewrite docs/d2a_rar/status/wp6_stage_b_t2.md from the ledger
Only the orchestrator writes the ledger; each experiment is a subprocess with a hard 300 s wall-clock timeout.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from shiftlab.autoresearch import ledger as lg
from shiftlab.autoresearch import stage_b as sb
from shiftlab.autoresearch import stage_b_q1 as q1
from shiftlab.autoresearch import stage_b_v2 as v2
from shiftlab.autoresearch import stage_b_v2_report as rep


def _state() -> dict | None:
    return json.loads(v2.STATE_PATH.read_text(encoding="utf-8")) if v2.STATE_PATH.exists() else None


def _scope() -> dict:
    return json.loads(v2.SCOPE_PATH.read_text(encoding="utf-8"))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_status(state: dict | None = None, iii: bool = False) -> None:
    """Rewrite the status file from the ledger plus both run states (scope i-ii and scope iii are shown separately)."""
    st_i, st_iii = _load(v2.STATE_PATH), _load(q1.STATE_PATH)
    if state is not None:
        st_iii, st_i = (state, st_i) if iii else (st_iii, state)
    v2.STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    v2.STATUS_PATH.write_text(
        rep.build(
            state=st_i,
            scope=_load(v2.SCOPE_PATH),
            state_iii=st_iii,
            scope_iii=_load(q1.SCOPE_PATH),
        ),
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-scope", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument(
        "--scope-iii",
        action="store_true",
        help="A1 scope (iii): Q1 evidence identities in the promoter shell",
    )
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=v2.MAX_WORKERS)
    a = ap.parse_args()
    v2.STAGE_DIR.mkdir(parents=True, exist_ok=True)
    if a.scope_iii and a.write_scope:
        if q1.SCOPE_PATH.exists():
            ap.error(f"{q1.SCOPE_PATH} exists: the scope is written once, before any run")
        sc = q1.select_scope()
        q1.SCOPE_PATH.write_text(json.dumps(sc, indent=1) + "\n", encoding="utf-8")
        print("scope iii:", sc["n_selected"], sc["cells"])
        return 0
    if a.scope_iii and a.run:
        if not q1.SCOPE_PATH.exists():
            ap.error("write the scope-iii file first (--scope-iii --write-scope)")
        v2.load_suite_v2()
        byid = {c["candidate_id"]: c for c in sb.load_batch()}
        cands = [byid[e["candidate_id"]] for e in _load(q1.SCOPE_PATH)["selected"]]
        print(f"ledger head before: {lg.head()}; scope iii {len(cands)} identities", flush=True)
        out = q1.run_tranche(
            cands, max_workers=a.workers, limit=a.limit, log=lambda m: print(m, flush=True),
            status_cb=lambda st: write_status({**st, "updated": time.time()}, iii=True),
        )  # fmt: skip
        print("finished:", out, flush=True)
        print("ledger:", lg.verify(), flush=True)
        write_status()
        return 0
    if a.write_scope:
        if v2.SCOPE_PATH.exists():
            ap.error(f"{v2.SCOPE_PATH} exists: the scope is written once, before any run")
        sc = v2.select_scope()
        v2.SCOPE_PATH.write_text(json.dumps(sc, indent=1) + "\n", encoding="utf-8")
        print("scope:", sc["n_selected"], sc["scope_counts"])
        return 0
    if a.report:
        write_status()
        return 0
    if not a.run:
        ap.error("pass --write-scope, --run or --report")
    if a.workers > v2.MAX_WORKERS:
        ap.error(f"max {v2.MAX_WORKERS} parallel workers")
    if not v2.SCOPE_PATH.exists():
        ap.error("write the scope first (--write-scope)")
    v2.load_suite_v2()  # checksum gate
    ids = [e["candidate_id"] for e in _scope()["selected"]]
    byid = {c["candidate_id"]: c for c in sb.load_batch()}
    cands = [byid[i] for i in ids]
    print(
        f"ledger head before: {lg.head()}  ({time.strftime('%F %T')}); scope {len(cands)} identities",
        flush=True,
    )
    out = v2.run_tranche(
        cands, max_workers=a.workers, limit=a.limit, log=lambda m: print(m, flush=True),
        status_cb=lambda st: write_status({**st, "updated": time.time()}),
    )  # fmt: skip
    print("finished:", out, flush=True)
    print("ledger:", lg.verify(), flush=True)
    write_status()
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    raise SystemExit(main())
