"""Append-only, hash-chained experiment ledger (Phase 8).

One JSON object per line in ``docs/d2a_rar/registry/EXPERIMENT_LEDGER.jsonl``. Each record stores
``prev_sha256`` (the previous record's ``record_sha256``; 64 zeros for the first) and its own
``record_sha256`` (hash of the canonical record without that field), so any edit, deletion or
reordering of an existing line is detected by :func:`verify`. :func:`append` verifies the whole chain
before writing and only ever opens the file in append mode. Pin :func:`head` externally (e.g. in a
commit message) to also detect truncation or tail rewrites.

The confirmation seed block (``configs/seed_registry.yaml`` id ``d2a_rar_confirmation_reserved``) is
refused unless ``stage == "D"``.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from shiftlab.seed_registry import load_registry

REPO_ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = REPO_ROOT / "docs" / "d2a_rar" / "registry" / "EXPERIMENT_LEDGER.jsonl"
GENESIS = "0" * 64
SCHEMA_VERSION = 1
CONFIRMATION_BLOCK_ID = "d2a_rar_confirmation_reserved"
DECISIONS = ("KEEP", "DISCARD", "CRASH", "INVALID", "DUPLICATE", "UNVERIFIED", "CONFIRM")
STAGES = ("A", "B", "C", "D")
FIDELITY_TIERS = (
    "AUTHOR_NATIVE",
    "PAPER_RECONSTRUCTION",
    "COMMON_CONTRACT_PORT",
    "CONCEPTUAL_PROXY",
)
EXPOSURES = ("smoke", "dev", "confirmation")
REQUIRED = (
    "candidate_id",
    "run_id",
    "stage",
    "git_commit",
    "method",
    "host",
    "fidelity_tier",
    "data_hashes",
    "seed_group",
    "hardware",
    "runtime_s",
    "null_class",
    "assumptions",
    "preregistered_predictions",
    "results",
    "baseline_relative",
    "counterexamples",
    "prior_art_status",
    "decision",
)


class LedgerError(Exception):
    pass


class LedgerTampered(LedgerError):
    pass


class InvalidRecord(LedgerError):
    pass


class DuplicateRun(LedgerError):
    pass


class ConfirmationSeedRefused(LedgerError):
    pass


@dataclass(frozen=True)
class VerifyResult:
    n_records: int
    head: str


def _canon(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "record_sha256"}
    return hashlib.sha256(_canon(body).encode("utf-8")).hexdigest()


def _read_lines(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        raise LedgerTampered(f"{path}: file does not end with a newline (partial write or edit)")
    return raw.decode("utf-8").split("\n")[:-1]


def verify(path: Path | str = LEDGER_PATH, expected_head: str | None = None) -> VerifyResult:
    """Check the hash chain; raise :class:`LedgerTampered` on any inconsistency."""
    prev = GENESIS
    lines = _read_lines(Path(path))
    for i, line in enumerate(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            raise LedgerTampered(f"line {i + 1}: not valid JSON") from e
        if rec.get("prev_sha256") != prev:
            raise LedgerTampered(f"line {i + 1}: prev_sha256 does not match the previous record")
        if rec.get("record_sha256") != record_hash(rec):
            raise LedgerTampered(f"line {i + 1}: record content does not match its record_sha256")
        prev = rec["record_sha256"]
    if expected_head is not None and prev != expected_head:
        raise LedgerTampered(
            "ledger head differs from the pinned head (truncation or tail rewrite)"
        )
    return VerifyResult(len(lines), prev)


def head(path: Path | str = LEDGER_PATH) -> str:
    return verify(path).head


def read_all(path: Path | str = LEDGER_PATH, *, check: bool = True) -> list[dict]:
    if check:
        verify(path)
    return [json.loads(x) for x in _read_lines(Path(path))]


def records_for(candidate_id: str, path: Path | str = LEDGER_PATH) -> list[dict]:
    return [r for r in read_all(path) if r.get("candidate_id") == candidate_id]


def current_git_commit(repo: Path = REPO_ROOT) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


def hardware_info() -> dict:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


def confirmation_range() -> tuple[int, int]:
    for b in load_registry().blocks:
        if b.id == CONFIRMATION_BLOCK_ID:
            return b.start, b.end
    raise LedgerError(f"seed block {CONFIRMATION_BLOCK_ID} missing from configs/seed_registry.yaml")


def _check_seed_group(rec: dict) -> None:
    sg = rec["seed_group"]
    if not isinstance(sg, dict) or sg.get("exposure") not in EXPOSURES or "block" not in sg:
        raise InvalidRecord(
            "seed_group needs {block, exposure in smoke|dev|confirmation, seed_start, seed_end}"
        )
    lo, hi = confirmation_range()
    s0, s1 = sg.get("seed_start"), sg.get("seed_end")
    overlaps = s0 is not None and s1 is not None and not (s1 < lo or s0 > hi)
    touches = sg["block"] == CONFIRMATION_BLOCK_ID or sg["exposure"] == "confirmation" or overlaps
    if touches and rec["stage"] != "D":
        raise ConfirmationSeedRefused(
            f"record for {rec['candidate_id']} uses the confirmation seed block {lo}-{hi}; only stage D may"
        )
    if touches and sg["exposure"] != "confirmation":
        raise InvalidRecord(
            "seeds in the confirmation range must be labelled exposure='confirmation'"
        )
    if sg["exposure"] == "confirmation" and rec["stage"] != "D":
        raise ConfirmationSeedRefused("exposure 'confirmation' is reserved for stage D")


def _validate(rec: dict) -> None:
    missing = [f for f in REQUIRED if f not in rec]
    if missing:
        raise InvalidRecord(f"missing fields: {missing}")
    if rec["decision"] not in DECISIONS:
        raise InvalidRecord(f"decision must be one of {DECISIONS}")
    if rec["stage"] not in STAGES:
        raise InvalidRecord(f"stage must be one of {STAGES}")
    if rec["fidelity_tier"] not in FIDELITY_TIERS:
        raise InvalidRecord(f"fidelity_tier must be one of {FIDELITY_TIERS}")
    if "prev_sha256" in rec or "record_sha256" in rec:
        raise InvalidRecord("prev_sha256/record_sha256 are set by append(), not by the caller")
    d = rec["decision"]
    if (
        rec["stage"] in ("B", "C", "D")
        and d not in ("CRASH", "INVALID", "DUPLICATE")
        and not rec["preregistered_predictions"]
    ):
        raise InvalidRecord(
            "stages B-D need non-empty preregistered_predictions (written before the run)"
        )
    if d in ("KEEP", "DISCARD", "CONFIRM"):
        if not rec["results"] or not rec.get("uncertainty"):
            raise InvalidRecord(f"{d} needs results and uncertainty")
        if not rec["baseline_relative"]:
            raise InvalidRecord(f"{d} needs baseline_relative results")
    if d == "CRASH" and not rec.get("error"):
        raise InvalidRecord("CRASH needs an error field")
    if d == "INVALID" and not rec.get("invalid_reason"):
        raise InvalidRecord("INVALID needs invalid_reason")
    if d == "DUPLICATE" and not rec.get("duplicate_of"):
        raise InvalidRecord("DUPLICATE needs duplicate_of")
    if d == "CONFIRM" and rec["stage"] != "D":
        raise InvalidRecord("CONFIRM is a stage-D decision")
    _check_seed_group(rec)


def append(record: dict, path: Path | str = LEDGER_PATH, *, now: datetime | None = None) -> dict:
    """Validate, chain and append one record. Never modifies existing lines."""
    path = Path(path)
    rec = dict(record)
    _validate(rec)
    state = verify(path)  # refuse to extend a tampered ledger
    if any(r.get("run_id") == rec["run_id"] for r in read_all(path, check=False)):
        raise DuplicateRun(f"run_id {rec['run_id']!r} already in the ledger")
    rec.setdefault("timestamp", (now or datetime.now(UTC)).isoformat(timespec="seconds"))
    rec["schema_version"] = SCHEMA_VERSION
    rec["prev_sha256"] = state.head
    rec["record_sha256"] = record_hash(rec)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as fh:  # append-only: no seek, no truncate
        fh.write((_canon(rec) + "\n").encode("utf-8"))
    return rec
