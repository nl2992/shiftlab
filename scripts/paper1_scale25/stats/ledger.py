"""Append-only confirmation-attempt ledger and cohort certificate (Design B).

File: docs/paper1_scale25/confirmation_attempts.csv. One row per EVENT:
  register  assigns the chronological attempt index i = (max index so far) + 1 and alpha_i = .05/(i(i+1)).
            Written BEFORE the confirmation window is opened. The index is consumed even if never opened.
  open      records the outcome (r_hat, L at level alpha_i) of an attempt that was opened. One per index.
Rows carry prev_hash/row_hash (sha256 chain over the preceding row), so edits or deletions of earlier rows
are detectable by `validate`. Legacy rows (legacy=1) reserve indices for earlier, separately-registered
openings; they count in the alpha schedule but are excluded from cohorts.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy import stats

try:
    from .certify import alpha_i, primary_lower
except ImportError:  # imported as a top-level module
    from certify import alpha_i, primary_lower

COLUMNS = [
    "attempt_index",
    "event",
    "opened",
    "utc",
    "dataset_id",
    "parent_source_id",
    "protocol_id",
    "contrast",
    "alpha_i",
    "n_episodes",
    "block_len",
    "r_hat_pct",
    "L_pct",
    "legacy",
    "note",
    "prev_hash",
    "row_hash",
]
GENESIS = "0" * 64
_HASHED = [c for c in COLUMNS if c != "row_hash"]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fmt(x) -> str:
    if x is None or x == "":
        return ""
    if isinstance(x, float):
        return "-inf" if x == -math.inf else repr(x)
    return str(x)


def _row_hash(row: dict) -> str:
    payload = "\x1f".join(_fmt(row.get(c, "")) for c in _HASHED)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read(path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class _Lock:
    def __init__(self, path, timeout=30.0):
        self.lp, self.timeout = str(path) + ".lock", timeout

    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(self.lp, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.time() - t0 > self.timeout:
                    raise TimeoutError("ledger lock held: " + self.lp)
                time.sleep(0.05)

    def __exit__(self, *a):
        os.close(self.fd)
        os.remove(self.lp)


def _append(path, row: dict):
    rows = read(path)
    row = {c: _fmt(row.get(c, "")) for c in COLUMNS}
    row["prev_hash"] = rows[-1]["row_hash"] if rows else GENESIS
    row["row_hash"] = _row_hash(row)
    p = Path(path)
    new = not p.exists() or p.stat().st_size == 0
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)
    return row


def next_index(rows) -> int:
    idx = [int(r["attempt_index"]) for r in rows if r["event"] == "register"]
    return (max(idx) if idx else 0) + 1


def validate(path) -> list[str]:
    """Return a list of integrity problems (empty list = ledger is valid)."""
    rows, bad = read(path), []
    prev, seen_reg, seen_open = GENESIS, {}, set()
    for n, r in enumerate(rows, 1):
        if list(r.keys()) != COLUMNS:
            bad.append(f"row {n}: wrong columns")
            continue
        if r["prev_hash"] != prev:
            bad.append(f"row {n}: prev_hash mismatch (earlier row altered/removed)")
        if r["row_hash"] != _row_hash(r):
            bad.append(f"row {n}: row_hash mismatch (row altered)")
        prev = r["row_hash"]
        i = int(r["attempt_index"])
        if r["event"] == "register":
            if i != len(seen_reg) + 1:
                bad.append(f"row {n}: register index {i} not the next index {len(seen_reg) + 1}")
            if i in seen_reg:
                bad.append(f"row {n}: index {i} reused")
            if abs(float(r["alpha_i"]) - alpha_i(i)) > 1e-12 * alpha_i(i):
                bad.append(f"row {n}: alpha_i != .05/(i(i+1))")
            if r["opened"] != "0":
                bad.append(f"row {n}: register row must have opened=0")
            seen_reg[i] = r
        elif r["event"] == "open":
            if i not in seen_reg:
                bad.append(f"row {n}: open for unregistered index {i}")
            elif r["utc"] < seen_reg[i]["utc"]:
                bad.append(f"row {n}: opened before registered")
            elif (
                r["alpha_i"] != seen_reg[i]["alpha_i"]
                or r["dataset_id"] != seen_reg[i]["dataset_id"]
            ):
                bad.append(f"row {n}: open row disagrees with its register row")
            if i in seen_open:
                bad.append(f"row {n}: attempt {i} opened twice")
            seen_open.add(i)
            if r["opened"] != "1":
                bad.append(f"row {n}: open row must have opened=1")
        else:
            bad.append(f"row {n}: unknown event {r['event']!r}")
    return bad


def register_attempt(
    path, dataset_id, parent_source_id, protocol_id, contrast, utc=None, legacy=0, note=""
):
    """Reserve the next chronological index BEFORE the window is opened. Returns the register row."""
    with _Lock(path):
        rows = read(path)
        problems = validate(path)
        if problems:
            raise RuntimeError("ledger invalid: " + "; ".join(problems))
        if any(
            r["event"] == "register"
            and r["dataset_id"] == dataset_id
            and r["protocol_id"] == protocol_id
            for r in rows
        ):
            raise ValueError(
                "this (dataset_id, protocol_id) is already registered; a window opens once"
            )
        i = next_index(rows)
        return _append(
            path,
            {
                "attempt_index": i,
                "event": "register",
                "opened": 0,
                "utc": utc or _now(),
                "dataset_id": dataset_id,
                "parent_source_id": parent_source_id,
                "protocol_id": protocol_id,
                "contrast": contrast,
                "alpha_i": alpha_i(i),
                "legacy": int(legacy),
                "note": note,
            },
        )


def record_open(path, index, r_hat_pct, L_pct, n_episodes, block_len, utc=None, note=""):
    """Record the outcome of an opened attempt (low level)."""
    with _Lock(path):
        rows = read(path)
        problems = validate(path)
        if problems:
            raise RuntimeError("ledger invalid: " + "; ".join(problems))
        reg = [r for r in rows if r["event"] == "register" and int(r["attempt_index"]) == index]
        if not reg:
            raise ValueError(f"index {index} was never registered")
        if any(r["event"] == "open" and int(r["attempt_index"]) == index for r in rows):
            raise ValueError(f"attempt {index} already opened; an index cannot be reused")
        g = reg[0]
        return _append(
            path,
            {
                "attempt_index": index,
                "event": "open",
                "opened": 1,
                "utc": utc or _now(),
                "dataset_id": g["dataset_id"],
                "parent_source_id": g["parent_source_id"],
                "protocol_id": g["protocol_id"],
                "contrast": g["contrast"],
                "alpha_i": g["alpha_i"],
                "n_episodes": n_episodes,
                "block_len": block_len,
                "r_hat_pct": float(r_hat_pct),
                "L_pct": float(L_pct),
                "legacy": g["legacy"],
                "note": note,
            },
        )


def open_attempt(path, index, a, b, utc=None, note=""):
    """Open attempt `index`: compute the PRIMARY bound at the REGISTERED alpha_i and record it."""
    reg = [r for r in read(path) if r["event"] == "register" and int(r["attempt_index"]) == index]
    if not reg:
        raise ValueError(f"index {index} was never registered")
    res = primary_lower(a, b, float(reg[0]["alpha_i"]))
    record_open(path, index, res["r_hat"], res["L"], res["n"], res["block_len"], utc, note)
    return res


# ---------------------------------------------------------------- cohort certificate


def attempt_table(path):
    """Merge register+open rows per index into dicts with floats."""
    rows = read(path)
    reg = {int(r["attempt_index"]): r for r in rows if r["event"] == "register"}
    opn = {int(r["attempt_index"]): r for r in rows if r["event"] == "open"}
    out = []
    for i, g in sorted(reg.items()):
        o = opn.get(i)
        has = o is not None and o["r_hat_pct"] != ""
        out.append(
            {
                "index": i,
                "dataset_id": g["dataset_id"],
                "parent": g["parent_source_id"],
                "alpha": float(g["alpha_i"]),
                "protocol": g["protocol_id"],
                "legacy": int(g["legacy"]),
                "opened": o is not None,
                "r": float(o["r_hat_pct"]) if has else None,
                "L": float(o["L_pct"]) if has else None,
            }
        )
    return out


def certify_cohort(path, S=None, min_datasets=25, min_R=2.5, distinct="parent"):
    """Cohort certificate. S = attempt indices chosen (possibly after seeing results); default = all opened
    non-legacy attempts with L > 0. Valid for any S simultaneously (union bound over all registered indices)."""
    problems = validate(path)
    t = attempt_table(path)
    cand = [x for x in t if x["opened"] and not x["legacy"]]
    sel_idx = [x["index"] for x in cand if x["L"] > 0] if S is None else list(S)
    byi = {x["index"]: x for x in t}
    for i in sel_idx:
        if i not in byi or not byi[i]["opened"] or byi[i]["legacy"]:
            problems.append(f"index {i} is not an opened non-legacy attempt")
    sel = [byi[i] for i in sel_idx if i in byi and byi[i]["opened"] and not byi[i]["legacy"]]
    keys = [x["parent"] if distinct == "parent" else x["dataset_id"] for x in sel]
    if len(set(keys)) != len(keys):
        problems.append("selected attempts are not distinct datasets")
    R_lower = float(np.mean([x["L"] for x in sel])) if sel else float("nan")
    R_hat = float(np.mean([x["r"] for x in sel])) if sel else float("nan")
    ok = (
        not problems
        and len(sel) >= min_datasets
        and all(x["L"] > 0 for x in sel)
        and R_lower >= min_R
    )
    # all-confirmed mean: every opened non-legacy attempt, regardless of outcome
    all_lo = float(np.mean([x["L"] for x in cand])) if cand else float("nan")
    all_hat = float(np.mean([x["r"] for x in cand])) if cand else float("nan")
    rs = np.array([x["r"] for x in cand], float)
    if len(rs) > 1:
        h = stats.t.ppf(0.975, len(rs) - 1) * rs.std(ddof=1) / math.sqrt(len(rs))
        t_ci = (float(rs.mean() - h), float(rs.mean() + h))
    else:
        t_ci = (float("nan"), float("nan"))
    return {
        "success": bool(ok),
        "integrity_problems": problems,
        "counts": {
            "registered": len(t),
            "legacy_reserved": sum(x["legacy"] for x in t),
            "opened": len(cand),
            "positive_r": sum(x["r"] > 0 for x in cand),
            "supported_L_gt_0": sum(x["L"] > 0 for x in cand),
            "selected": len(sel),
            "distinct_selected": len(set(keys)),
        },
        "selected_R_lower": R_lower,
        "selected_R_hat": R_hat,
        "all_opened_mean_r_hat": all_hat,
        "all_opened_mean_simultaneous_lower": all_lo,
        "all_opened_mean_cross_dataset_t95": t_ci,
        "criteria": {"min_datasets": min_datasets, "min_R": min_R, "distinct_by": distinct},
        "note": (
            "simultaneous lower bounds (mean of L_i) are valid for any selection by the union bound; "
            "R_hat of a selected cohort is subject to winner's curse"
        ),
    }
