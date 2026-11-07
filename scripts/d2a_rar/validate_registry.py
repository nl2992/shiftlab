"""Validate docs/d2a_rar/registry/{failure_ledger.jsonl,null_assumptions.yaml}.

Usage:
    python scripts/d2a_rar/validate_registry.py                 # structure checks
    python scripts/d2a_rar/validate_registry.py --verify-quotes  # also re-check every ledger quote via `git show`

Exit code 0 = valid, 1 = problems found. Fields set to "UNVERIFIED" are allowed (and counted); an
empty or missing required field is an error. This does not check scientific correctness.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "docs" / "d2a_rar" / "registry"
# Source kind for files that exist only on disk in the main checkout (not in any git ref).
UNTRACKED_KIND = "main-checkout-untracked"
UNTRACKED_ROOT = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")

NULL_CLASSES = {"cond", "marg", "absolute_risk", "economic", "none", "UNVERIFIED"}
LEDGER_NULL_FLAG = {"yes", "no", "partial", "n_a", "unclear"}
LEDGER_STATUS = {"development", "confirmed", "exploratory"}
LEDGER_KIND = {"negative", "narrow_positive", "correction", "theory_closed", "applicability"}
GUARANTEES = {
    "anytime-valid",
    "fixed-n",
    "asymptotic",
    "none",
    "regret_bound",
    "decision_theoretic",
    "UNVERIFIED",
}
OUTPUTS = {
    "alarm",
    "certificate",
    "label_allocation",
    "retrain",
    "promotion",
    "rollback",
    "estimate",
    "stopping_rule",
    "gate",
}
VERIFIED = {
    "REPO_CODE",
    "REPO_DOC",
    "MANDATE_ONLY",
    "ABSTRACT",
    "SNIPPET",
    "NONE",
    "PAPER_FULLTEXT",
}

LEDGER_REQUIRED = [
    "id",
    "kind",
    "source_ref",
    "mechanism",
    "claim",
    "null_used_in_measurement",
    "null_the_method_actually_targets",
    "null_mismatched",
    "mismatch_note",
    "cells_regime",
    "numbers",
    "status",
    "do_not_repeat_without",
]
NULL_REQUIRED = [
    "id",
    "name",
    "role",
    "target_null",
    "target_null_detail",
    "filtration",
    "sampling_assumption",
    "dependence_assumption",
    "label_delay_assumption",
    "guarantee_type",
    "output_type",
    "source",
    "source_verification",
    "valid_validity_metric",
    "notes_for_agents",
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def check_ledger(errors: list[str], verify_quotes: bool) -> int:
    path = REG / "failure_ledger.jsonl"
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"ledger line {i}: invalid JSON ({e})")
    seen = set()
    cache: dict[str, str] = {}
    for r in rows:
        rid = r.get("id", "?")
        if rid in seen:
            errors.append(f"{rid}: duplicate id")
        seen.add(rid)
        for k in LEDGER_REQUIRED:
            if k not in r or r[k] in (None, "", []):
                if k == "mismatch_note" and r.get("null_mismatched") in {"no", "n_a"} and k in r:
                    continue
                errors.append(f"{rid}: missing/empty field {k}")
        if r.get("kind") not in LEDGER_KIND:
            errors.append(f"{rid}: bad kind {r.get('kind')}")
        if r.get("null_mismatched") not in LEDGER_NULL_FLAG:
            errors.append(f"{rid}: bad null_mismatched {r.get('null_mismatched')}")
        if r.get("status") not in LEDGER_STATUS:
            errors.append(f"{rid}: bad status {r.get('status')}")
        if not isinstance(r.get("source_ref"), list) or not all(
            "@" in s and ":" in s for s in r.get("source_ref", [])
        ):
            errors.append(f"{rid}: source_ref must be a list of 'branch@sha:path'")
        for n in r.get("numbers", []):
            if not isinstance(n, dict) or "quote" not in n or "source" not in n:
                errors.append(f"{rid}: number entries need quote+source")
                continue
            if verify_quotes:
                src = n["source"]
                if src not in cache:
                    sha, _, p = src.partition(":")
                    if sha == UNTRACKED_KIND:
                        fp = UNTRACKED_ROOT / p
                        cache[src] = (
                            norm(fp.read_text(encoding="utf-8", errors="replace"))
                            if fp.exists()
                            else ""
                        )
                    else:
                        out = subprocess.run(
                            ["git", "show", f"{sha}:{p}"],
                            cwd=ROOT,
                            capture_output=True,
                            check=False,
                        )
                        cache[src] = (
                            norm(out.stdout.decode("utf-8", "replace"))
                            if out.returncode == 0
                            else ""
                        )
                if not cache[src]:
                    errors.append(f"{rid}: cannot read {src}")
                elif norm(n["quote"]) not in cache[src]:
                    errors.append(f"{rid}: quote not found in {src}: {n['quote'][:70]!r}")
    return len(rows)


def check_nulls(errors: list[str]) -> tuple[int, int]:
    data = yaml.safe_load((REG / "null_assumptions.yaml").read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    unverified = 0
    ids = set()
    for e in entries:
        eid = e.get("id", "?")
        if eid in ids:
            errors.append(f"{eid}: duplicate id")
        ids.add(eid)
        for k in NULL_REQUIRED:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{eid}: missing/empty field {k}")
        if e.get("target_null") not in NULL_CLASSES:
            errors.append(f"{eid}: bad target_null {e.get('target_null')}")
        if e.get("guarantee_type") not in GUARANTEES:
            errors.append(f"{eid}: bad guarantee_type {e.get('guarantee_type')}")
        if e.get("source_verification") not in VERIFIED:
            errors.append(f"{eid}: bad source_verification {e.get('source_verification')}")
        outs = e.get("output_type")
        outs = outs if isinstance(outs, list) else [outs]
        for o in outs:
            if o not in OUTPUTS:
                errors.append(f"{eid}: bad output_type {o}")
        unverified += sum(
            1 for k, v in e.items() if isinstance(v, str) and v.startswith("UNVERIFIED")
        )
    required_methods = {
        "drift2act_certificate",
        "rar_gates",
        "challenger_gse",
        "challenger_ose",
        "challenger_lse",
        "gong_zhang_paid_obs",
        "asi_zrnic_candes",
        "sethi_markov_test",
        "watch",
        "pprm",
        "h2c",
        "rmm",
        "e_rb",
        "page_cusum",
        "markov_lr",
        "gap_mix",
        "pave",
        "dss_straddle",
        "freshcheck",
        "two_phase_persistence",
        "episode_front",
        "certified_deployment_gates",
    }
    missing = required_methods - ids
    if missing:
        errors.append(f"null_assumptions missing mandated entries: {sorted(missing)}")
    return len(entries), unverified


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-quotes", action="store_true")
    args = ap.parse_args()
    errors: list[str] = []
    n_rows = check_ledger(errors, args.verify_quotes)
    n_entries, n_unv = check_nulls(errors)
    print(
        f"ledger rows: {n_rows}; null_assumption entries: {n_entries}; UNVERIFIED-valued fields: {n_unv}"
    )
    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("registry OK" + (" (quotes verified against git)" if args.verify_quotes else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
