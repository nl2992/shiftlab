"""Stage A preflight: decide whether a candidate identity may be implemented and screened.

Checks (in verdict-priority order): structural validity / identity integrity (INVALID), ``blocked_by``
(BLOCKED_BY_LEDGER), Q3 gating (BLOCKED_UNTIL_WINNERS), duplicate against the ledger (DUPLICATE), null
eligibility (INELIGIBLE_NULL_MISMATCH), host adapter importable (BLOCKED_HOST_NOT_PORTED), hook exists
(BLOCKED_HOOK_MISSING). An unported host or a missing hook is a *blocked* state, never INVALID. Source/config
hashes are computed and returned so the caller can store them in the ledger. Leakage/budget/cost guards live
in ``tests/d2a_rar/test_contract.py``; :func:`run_named_smoke` runs a named subset of those tests on request.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import importlib.util
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import cache, lru_cache
from pathlib import Path

from . import grammar as g
from .dev_suite import cells_for
from .ledger import LEDGER_PATH, LedgerTampered, current_git_commit, read_all

ELIGIBLE = "ELIGIBLE"
INVALID = "INVALID"
BLOCKED_BY_LEDGER = "BLOCKED_BY_LEDGER"
BLOCKED_UNTIL_WINNERS = "BLOCKED_UNTIL_WINNERS"
DUPLICATE = "DUPLICATE"
INELIGIBLE_NULL_MISMATCH = "INELIGIBLE_NULL_MISMATCH"
BLOCKED_HOST_NOT_PORTED = "BLOCKED_HOST_NOT_PORTED"
BLOCKED_HOOK_MISSING = "BLOCKED_HOOK_MISSING"
PRIORITY = (
    INVALID,
    BLOCKED_BY_LEDGER,
    BLOCKED_UNTIL_WINNERS,
    DUPLICATE,
    INELIGIBLE_NULL_MISMATCH,
    BLOCKED_HOST_NOT_PORTED,
    BLOCKED_HOOK_MISSING,
)

ADAPTER_MODULES = {
    g.D: "shiftlab.bench.contract.adapters_drift2act",
    g.R: "shiftlab.bench.contract.adapters_rar",
    g.A: "shiftlab.bench.contract.adapters_rar",
    g.H: "shiftlab.bench.contract.adapters_challenger",
    g.C: "shiftlab.bench.contract.policies",
}
SMOKE_TESTS = (
    "test_labels_never_visible_before_release",
    "test_policy_reading_evaluator_truth_fails_the_run",
    "test_label_budget_overspend_raises",
    "test_costs_only_for_performed_actions",
    "test_paired_runs_share_streams_and_unpaired_is_rejected",
)
FALSIFIER_NULLS = ("cond", "marg", "absolute_risk")


@dataclass
class Verdict:
    status: str
    candidate_id: str
    checks: list[dict] = field(default_factory=list)
    hashes: dict = field(default_factory=dict)
    validity_plan: dict = field(default_factory=dict)
    comparator_nulls: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == ELIGIBLE

    def to_dict(self) -> dict:
        return dataclasses.asdict(self) | {"ok": self.ok}


def default_host_probe(host: str) -> str | None:
    """None if the host's contract adapter is importable and ported; else a reason string."""
    mod = ADAPTER_MODULES[host]
    try:
        m = importlib.import_module(mod)
    except ImportError as e:
        return f"adapter module {mod} not importable ({e.__class__.__name__}: {e})"
    if host == g.C:
        return None
    vals = list(vars(m).values())
    vals += [x for v in vals if isinstance(v, dict) for x in v.values()]
    if any(
        getattr(v, "port_status", None) == "COMMON_CONTRACT_PORT"
        for v in vals
        if not isinstance(v, type)
    ):
        return None
    return f"{mod} imported but exposes no object with port_status == COMMON_CONTRACT_PORT"


def default_hook_probe(hook: str) -> str | None:
    """None if the hook exists in the host package; else a reason string."""
    h = g.HOOKS[hook]
    if h["status"] == "NOT_EXPOSED":
        return f"{hook} is not exposed by the host ({h['note']})"
    try:
        m = importlib.import_module(h["module"])
    except ImportError as e:
        return f"{h['module']} not importable ({e})"
    obj = getattr(m, h["attr"], None) if h["attr"] else None
    if h["attr"] and obj is None:
        return f"{h['module']}.{h['attr']} not found"
    if h["kind"] == "config" and dataclasses.is_dataclass(obj):
        have = {f.name for f in dataclasses.fields(obj)}
        miss = [f for f in h.get("fields", ()) if f not in have]
        if miss:
            return f"{h['module']}.{h['attr']} lacks config fields {miss}"
    return None


@cache
def _module_sha256(module: str) -> str | None:
    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None
    if spec is None or not spec.origin or not Path(spec.origin).is_file():
        return None
    return hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _git_commit() -> str:
    return current_git_commit()


def null_check(c: dict) -> tuple[list[str], dict]:
    """Null-eligibility. Returns (problems, comparator_nulls). Never lets a cond/marg method be scored on the other null."""
    problems = []
    null = c["target_null"]
    if c.get("scoring_null") != null:
        problems.append(
            f"scoring_null {c.get('scoring_null')!r} != target_null {null!r} (P2 error)"
        )
    if null not in g.HOST_ALLOWED_NULLS[c["host"]]:
        problems.append(f"null {null!r} not allowed on host {c['host']!r}")
    entries = g.load_null_entries()
    comp: dict[str, str] = {}
    for b in c["required_baselines"]:
        eid = g.BASELINE_NULL_ENTRY.get(b)
        raw = entries[eid]["target_null"] if eid in entries else "UNREGISTERED"
        comp[b] = {"abs_risk": "absolute_risk"}.get(raw, raw)
    if null in FALSIFIER_NULLS and not any(v == null for v in comp.values()):
        problems.append(
            f"no required baseline shares target_null {null!r}: validity not comparable"
        )
    return problems, comp


def run_named_smoke(
    names: Iterable[str] = SMOKE_TESTS, *, dry_run: bool = False, timeout: int = 180
) -> dict:
    """Run a named subset of tests/d2a_rar/test_contract.py (leakage/budget/cost guards); do not reimplement them."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/d2a_rar/test_contract.py",
        "-k",
        " or ".join(names),
    ]
    if dry_run:
        return {"cmd": cmd, "ran": False}
    r = subprocess.run(
        cmd, cwd=g.REPO_ROOT, capture_output=True, text=True, timeout=timeout, check=False
    )
    return {"cmd": cmd, "ran": True, "returncode": r.returncode, "tail": r.stdout[-400:]}


def preflight(
    c: dict,
    *,
    stage: str = "B",
    ledger_path: Path | str = LEDGER_PATH,
    host_probe: Callable[[str], str | None] = default_host_probe,
    hook_probe: Callable[[str], str | None] = default_hook_probe,
    winners: Iterable[str] = (),
    smoke: bool = False,
) -> Verdict:
    v = Verdict(ELIGIBLE, c.get("candidate_id", "?"))
    fails: dict[str, list[str]] = {}

    def fail(status: str, why: str) -> None:
        fails.setdefault(status, []).append(why)
        v.checks.append({"status": status, "reason": why})

    # 1. structure + identity integrity (recompute id and blocked_by from the grammar, do not trust the record)
    errs = g.validate_identity(c)
    if errs:
        fail(INVALID, "; ".join(errs))
    elif c["family"] != "q3_factorial_stack":
        fam = g.family_by_key(c["family"])
        var = g.variant_of(fam, c["variant"])
        again = g.make_identity(
            fam, var, c["host"], c["research_question"], c["target_null"], c["configuration"],
            new_hypothesis=c.get("new_mechanistic_hypothesis"),
        )  # fmt: skip
        if again["candidate_id"] != c["candidate_id"]:
            fail(INVALID, "candidate_id does not match the grammar-recomputed identity")
        if again["blocked_by"]:
            ids = [b["ledger_id"] for b in again["blocked_by"]]
            fail(
                BLOCKED_BY_LEDGER,
                f"matches do_not_repeat_without of {ids}; declare new_mechanistic_hypothesis",
            )
    elif c.get("blocked_by"):
        fail(BLOCKED_BY_LEDGER, "q3 identity carries blocked_by")

    # 2. Q3 gating
    if c.get("blocked_until") and not set(c.get("parent_ids", [])) <= set(winners):
        fail(BLOCKED_UNTIL_WINNERS, f"blocked_until: {c['blocked_until']}")

    # 3. duplicate against the ledger (same candidate + stage already decided, other than CRASH)
    try:
        prior = [
            r for r in read_all(ledger_path)
            if r.get("candidate_id") == c.get("candidate_id") and r.get("stage") == stage and r.get("decision") != "CRASH"
        ]  # fmt: skip
        if prior:
            fail(
                DUPLICATE,
                f"already in ledger at stage {stage}: run_ids {[r['run_id'] for r in prior]}",
            )
    except LedgerTampered as e:
        fail(INVALID, f"ledger verification failed: {e}")

    # 4. null eligibility
    if not errs:
        problems, v.comparator_nulls = null_check(c)
        for p in problems:
            fail(INELIGIBLE_NULL_MISMATCH, p)
        v.validity_plan = cells_for(c["research_question"], c["target_null"])
        v.validity_plan["note"] = (
            "false promotion is scored only on validity_cells for the candidate's own null; "
            "out_of_contract_stress cells are descriptive only"
        )

    # 5. host adapter, 6. hook
    if not errs:
        why = host_probe(c["host"])
        if why:
            fail(BLOCKED_HOST_NOT_PORTED, why)
        why = hook_probe(c["hook"])
        if why:
            fail(BLOCKED_HOOK_MISSING, why)

        # 7. hashes
        h = g.HOOKS[c["hook"]]
        v.hashes = {
            "config_sha256": g.sha(
                {"host": c["host"], "hook": c["hook"], "cfg": c["configuration"]}
            ),
            "hook_module": h["module"],
            "hook_module_sha256": _module_sha256(h["module"]),
            "adapter_module_sha256": _module_sha256(ADAPTER_MODULES[c["host"]]),
            "grammar_version": g.GRAMMAR_VERSION,
            "git_commit": _git_commit(),
        }

    for st in PRIORITY:
        if st in fails:
            v.status = st
            break
    v.reasons = [r for st in PRIORITY if st in fails for r in fails[st]]
    if smoke and v.ok:
        v.checks.append({"smoke": run_named_smoke()})
    return v
