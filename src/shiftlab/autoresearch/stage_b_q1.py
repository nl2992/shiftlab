"""Stage-B tranche 2, A1 scope (iii): the 42 batch-001 Q1 evidence identities in the contract-native evidence promoter shell.

Registered in AUTORESEARCH_PROGRAM.md section 3a (A1 scope (iii) line, hook commit 35be7435). Wiring only:

* Candidate: ``adapters_evidence.promoter_adapter(identity)`` (``evidence_q1.build_evidence``), schedule ``calendar``
  (deterministic equally spaced queries, declared 'predictable'), alpha 0.1. Validity is scored on the shell only.
* Cells: the v1 section-3 Q1 row (4 cells, v1 seed rule ``110000000 + cell_index*1000 + r``, balanced, cap 50, T 1000, never
  run for these identities before) plus the DEV_SUITE_v2 cells whose family is compatible with a calendar gap schedule:
  ``label_cap < T`` (constant gap > 1, so gap structure is non-degenerate) and no informative delay/missingness (12 of 15).
* Comparators (the line): the valid Markov-LR (``markov_lr_gate``), the gap-10 thinned gate (``thinned_hedged_gate``),
  Gap-Mix ``exact0.8_s4`` and the restart mixture without gaps (``rmm_detector``); the unmodified Drift2Act host
  (native_v0 on the v1 row = suite-v1 convention, calibrated_v1 on v2 cells = A1) is the ablation/host reference.
* The Drift2Act-host run with the identity's evidence (``OutcomeAugmentedEvidence``) is run on two v1 cells as a DESCRIPTIVE
  report only: OUT_OF_CONTRACT for validity (host selection uses x_t, declares no propensity).
* Ledger records carry suite=v2, amendment=A1, scope=iii.
This module imports ``stage_b_v2`` without editing it (a tranche may be running from that module).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from shiftlab.bench.contract import load_family
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy, ProxyEvidence
from shiftlab.bench.contract.adapters_evidence import promoter_adapter
from shiftlab.bench.contract.audit import AuditViolation
from shiftlab.bench.contract.evidence_q1 import build_evidence
from shiftlab.bench.contract.evidence_seam import OutcomeAugmentedEvidence

from . import ledger as lg
from . import stage_b as sb
from . import stage_b_v2 as v2
from .preflight import preflight
from .stage_b_variants import Impl

SCOPE = "iii"
Q1_COMPARATORS = ("markov_lr_gate", "thinned_hedged_gate", "gapmix_exact08_s4", "rmm_detector")
Q1_CONTROLS = ("markov_lr_gate", "thinned_hedged_gate")  # section-4 item 4 simple controls for Q1
SCOPE_PATH = v2.STAGE_DIR / "tranche2_scope_iii.json"
STATE_PATH = v2.STAGE_DIR / "tranche2_state_iii.json"
NOT_RUN_PATH = v2.STAGE_DIR / "not_run_t2_iii.jsonl"
SCHEDULE, ALPHA = "calendar", 0.1
DESCRIPTIVE_HOST_CELLS = (0, 2)  # v1 Q1 row: correct_null, alternative


# ------------------------------------------------------------------------------------------ cells
def q1_cells() -> list[dict]:
    """v1 Q1 row (4) + compatible v2 cells (12), normalised to the v2 cell format (+ ``suite``)."""
    out = []
    for i, cd in enumerate(sb.suite_cells("Q1")):
        out.append(
            {
                "id": f"Q1_{i}",
                "suite": "v1",
                "index": i,
                "role": cd["role"],
                "family": cd["family"],
                "family_source": "v1",
                "cost_vector": cd["cost_vector"],
                "T": load_family(cd["family"]).T,
                "label_cap": sb.LABEL_CAP,
                "max_lookback": 0,
                "retrain_duration": 20,
                "null_truth_expected": {**cd["null_truth_expected"], "abs_risk": False},
            }
        )
    for cd in v2.load_suite_v2()["cells"]:
        spec = v2.cell_spec(cd)
        if (
            cd["label_cap"] < cd["T"]
            and spec.delay.kind != "informative"
            and spec.missing.kind != "informative"
        ):
            out.append({**cd, "suite": "v2"})
    return out


def seeds_of(cell: dict) -> list[int]:
    return sb.cell_seeds(cell["index"]) if cell["suite"] == "v1" else v2.cell_seeds(cell["index"])


def _spec_env(cell: dict):
    if cell["suite"] == "v1":
        spec = load_family(cell["family"])
        return spec, sb.make_env(spec, cell["cost_vector"], "default")
    spec = v2.cell_spec(cell)
    return spec, v2.make_env(spec, cell, "default")


def reference(comp: str, cell: dict, cache_dir: Path, chunk: int | None = None) -> list[dict]:
    """Comparator or host runs for one Q1 cell. v2 cells reuse the tranche-2 (i-ii) cache files; v1-row cells are cached here."""
    if cell["suite"] == "v2":
        name = comp
        return v2.reference(name, cell, "default", cache_dir, chunk)
    spec, env = _spec_env(cell)
    tag = "host_d2a_native" if comp == "host_d2a" else comp
    key = hashlib.sha256(
        json.dumps(
            [tag, cell["family"], cell["cost_vector"], cell["index"], sb._code_hash(), "q1row"]
        ).encode()
    ).hexdigest()[:20]
    path = cache_dir / f"q1row__{tag}__{cell['id']}__{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["runs"]
    t0 = time.time()
    runs = sb.run_method(sb.COMPARATORS[comp][0], spec, env, seeds_of(cell), tag)
    sb._write_json_atomic(path, {"tag": tag, "runtime_s": time.time() - t0, "runs": runs})
    return runs


def host_runs(cell: dict, cache_dir: Path) -> list[dict]:
    """Unmodified Drift2Act host: native_v0 on the v1 row (suite-v1 convention), calibrated_v1 on v2 cells (A1)."""
    return reference("host_d2a", cell, cache_dir)


# ------------------------------------------------------------------------------------------ candidate
def _impl(cand: dict) -> Impl:
    ad = promoter_adapter(cand, alpha=ALPHA, schedule=SCHEDULE)
    return Impl(
        "q1",
        {},
        lambda env: ad.build(env),
        notes=f"contract-native evidence promoter shell ({SCHEDULE} schedule, alpha {ALPHA}); validity scored on the shell only",
    )


def resolve_q1(cand: dict) -> tuple[Impl | None, str]:
    """Stage-B resolver for scope (iii): d2a.evidence_log_lik identities -> ``evidence_q1.build_evidence`` via the shell."""
    if cand["hook"] != "d2a.evidence_log_lik":
        return None, "not a Q1 evidence identity"
    try:
        build_evidence(cand)
    except Exception as e:  # noqa: BLE001
        return None, f"build_evidence failed: {type(e).__name__}: {e}"
    return _impl(cand), ""


def shell_contract_status(cand: dict, cells: list[dict]) -> dict:
    ev = build_evidence(cand, selection="predictable")
    out = {}
    for c in cells:
        spec = load_family(c["family"]) if c["suite"] == "v1" else v2.cell_spec(c)
        out[c["id"]] = ev.contract_status(spec)["status"]
    return {"validity_claim": ev.spec.validity, "per_cell": out}


def descriptive_host_runs(cand: dict, cells: list[dict], host_ref: dict[str, list[dict]]) -> dict:
    """Drift2Act host with the identity's evidence on two v1 cells: reported only, OUT_OF_CONTRACT for validity."""
    out = {}
    for c in cells:
        if c["suite"] != "v1" or c["index"] not in DESCRIPTIVE_HOST_CELLS:
            continue
        spec, env = _spec_env(c)

        def mk(e, cand=cand):
            ev = OutcomeAugmentedEvidence(ProxyEvidence(), build_evidence(cand))
            return Drift2ActContractPolicy(evidence=ev)

        runs = sb.run_method(mk, spec, env, seeds_of(c), "d2a_evidence")
        d = sb._a(runs) - sb._a(host_ref[c["id"]])
        mean, lo, hi = sb._ci(d)
        out[c["id"]] = {
            "validity_status": "OUT_OF_CONTRACT",
            "reason": "host selection uses monitor x_t and declares no propensity (monitor_adaptive)",
            "J_mean": float(np.mean(sb._a(runs))),
            "promotion_rate": sb._rate(runs, "promoted"),
            "dJ_vs_unmodified_host": mean,
            "dJ_ci95": [lo, hi],
        }
    return out


def run_experiment(cand: dict, impl: Impl, cache_dir: Path = v2.STAGE_DIR / "cache") -> dict:
    t0 = time.time()
    cells_def = q1_cells()
    host_key = "host"
    required = cand["required_baselines"]
    cells: list[dict] = []
    for cd in cells_def:
        runs = {host_key: host_runs(cd, cache_dir)}
        for comp in Q1_COMPARATORS:
            runs[comp] = reference(comp, cd, cache_dir)
        cells.append(
            {
                "id": cd["id"],
                "role": cd["role"],
                "family": cd["family"],
                "cost_vector": cd["cost_vector"],
                "null_expected": cd["null_truth_expected"],
                "runs": runs,
            }
        )
    comp_meta = {
        m: {
            "claimed_null": sb.COMPARATORS[m][1],
            "is_control": m in Q1_CONTROLS,
            "baseline_ids": [b for b in required if sb.BASELINE_IMPL.get(b) == m],
        }
        for m in Q1_COMPARATORS
    }
    kw = {
        "cand_null": cand["target_null"],
        "comp_meta": comp_meta,
        "cx": cand["complexity"]["level"],
        "suite": "v2",
    }
    pre = sb.analyse(
        [dict(c, runs={**c["runs"], "cand": c["runs"][host_key]}) for c in cells], **kw
    )
    target_cells = [f"{c['id']}:{c['family']}" for c in cells if c["role"] in sb.TARGET_ROLES]
    prereg = {
        **sb.preregistration(cand, impl, cells_def, pre["strongest_comparator"], target_cells),
        "suite": v2.SUITE,
        "amendment": v2.AMENDMENT,
        "scope": SCOPE,
        "candidate": f"evidence promoter shell, schedule={SCHEDULE}, alpha={ALPHA}",
        "comparator_set": ["host(unmodified Drift2Act)", *Q1_COMPARATORS],
        "cells": [c["id"] for c in cells_def],
        "strongest_comparator_at_registration_per_cell": pre["strongest_comparator_per_cell"],
        "validity_scored_on": "shell only; Drift2Act-host Q1 runs are descriptive (OUT_OF_CONTRACT)",
    }
    prereg_sha = hashlib.sha256(json.dumps(prereg, sort_keys=True).encode()).hexdigest()
    for cd, c in zip(cells_def, cells, strict=True):
        spec, env = _spec_env(cd)
        c["runs"]["cand"] = sb.run_method(impl.build_cand, spec, env, seeds_of(cd), "cand")
    for c in cells:
        if len({tuple(r["fingerprint"] for r in runs) for runs in c["runs"].values()}) != 1:
            raise AuditViolation(f"unpaired runs in cell {c['id']}")
    res = sb.analyse(cells, **kw, candidate_key="cand", host_key=host_key)
    desc = descriptive_host_runs(cand, cells_def, {c["id"]: c["runs"][host_key] for c in cells})
    strongest = res["strongest_comparator"]
    show = ["cand", host_key] + [
        m for m in dict.fromkeys(res["strongest_comparator_per_cell"].values()) if m != host_key
    ]
    pf = preflight(cand, stage="B", suite=v2.SUITE)
    seeds_all = [s for cd in cells_def for s in seeds_of(cd)]
    status = shell_contract_status(cand, cells_def)
    record = {
        "candidate_id": cand["candidate_id"],
        "run_id": f"B2Q1-{cand['candidate_id']}-{prereg_sha[:8]}",
        "stage": "B",
        "suite": v2.SUITE,
        "amendment": v2.AMENDMENT,
        "scope": SCOPE,
        "git_commit": lg.current_git_commit(),
        "method": f"{cand['family']}.{cand['variant']}@{cand['host']}[{cand['hook']}] via evidence promoter shell",
        "host": cand["host"],
        "fidelity_tier": "PAPER_RECONSTRUCTION",
        "data_hashes": {
            "dev_suite_v2_sha256": v2.SUITE_V2_SHA256,
            "stream_families_v2_sha256": v2.FAMILIES_V2_SHA256,
            "config_sha256": pf.hashes.get("config_sha256"),
            "hook_module_sha256": pf.hashes.get("hook_module_sha256"),
            "adapter_module_sha256": pf.hashes.get("adapter_module_sha256"),
            "stage_b_q1_sha256": hashlib.sha256(
                Path(__file__).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
            "code_hash16": sb._code_hash(),
        },
        "seed_group": {
            "block": "d2a_rar_dev",
            "sub_block": "v1_q1_row+v2",
            "seed_start": min(seeds_all),
            "seed_end": max(seeds_all),
            "exposure": "dev",
            "replicates_per_cell": v2.N_REP,
            "cells": [c["id"] for c in cells_def],
        },
        "hardware": lg.hardware_info(),
        "runtime_s": round(time.time() - t0, 3),
        "null_class": cand["target_null"],
        "assumptions": cand["assumptions"],
        "preregistered_predictions": {**prereg, "sha256": prereg_sha},
        "results": {
            "workload": {
                "per_cell": {
                    c["id"]: {
                        k: c[k]
                        for k in ("suite", "T", "label_cap", "cost_vector", "retrain_duration")
                    }
                    for c in cells_def
                },
                "shell": {"schedule": SCHEDULE, "alpha": ALPHA},
                "pairing": "run_paired",
                "verify_run": "every run",
            },
            "components_per_cell": {m: sb.components(cells, m) for m in show},
            "power_delay_per_cell": {m: sb.power_delay(cells, m) for m in show},
            "validity": res["validity"],
            "effect_vs_host": res["effect_vs_host"],
            "effect_vs_strongest": res["effect_vs_strongest"],
            "strongest_comparator": strongest,
            "strongest_comparator_per_cell": res["strongest_comparator_per_cell"],
            "excluded_comparators_invalid_for_claimed_null": res[
                "excluded_comparators_invalid_aggressive"
            ],
            "eligible_comparators": res["eligible_comparators"],
            "controls_ok": res["controls_ok"],
            "beats_simple_controls": res["beats_simple_controls"],
            "simple_controls": list(Q1_CONTROLS),
            "valid_ok": res["valid_ok"],
            "invalid_aggressive": res["invalid_aggressive"],
            "near_keep": bool(
                res["decision"] == "DISCARD"
                and res["valid_ok"]
                and not res["invalid_aggressive"]
                and res["effect_vs_strongest"]["label"] != "none"
            ),
            "discard_reasons": res["discard_reasons"],
            "shell_contract_status": status,
            "descriptive_drift2act_host_runs": desc,
            "decision_rationale": res["why"],
            "implementation_notes": impl.notes,
            "preflight": {
                "status": pf.status,
                "validity_plan": pf.validity_plan,
                "comparator_nulls": pf.comparator_nulls,
            },
        },
        "uncertainty": {
            "method": "paired percentile bootstrap over seeds (2000 resamples, 95%), mean dJ = J_cand - J_comparator (negative = candidate better)",
            "dJ_vs_host": res["dJ_vs_host"],
            "dJ_vs_strongest": res["dJ_vs_strongest"],
        },
        "baseline_relative": {
            "strongest": strongest,
            "strongest_per_cell": res["strongest_comparator_per_cell"],
            "unmodified_host": host_key,
            "mechanistic_ablation": {
                "note": "host = unmodified Drift2Act (default ProxyEvidence); comparators include the gap-ignorant Markov-LR"
            },
            "dJ_vs_each_implemented_comparator": res["dJ_vs_each_comparator"],
            "comparator_mapping": {
                m: {"baseline_ids": comp_meta[m]["baseline_ids"]} for m in comp_meta
            },
        },
        "baselines_missing": sorted(b for b in required if b not in sb.BASELINE_IMPL),
        "required_baselines_outside_scope_iii_set": sorted(
            b for b in required if sb.BASELINE_IMPL.get(b) not in (*Q1_COMPARATORS, "host_d2a")
        ),
        "counterexamples": res["counterexamples"],
        "prior_art_status": cand["prior_art_status"],
        "decision": res["decision"],
        "behaviour_sha256": v2.behaviour_sha(cells, "cand"),
        "family_caveat": None,
        "role": cand["role"],
        "effect_label_vs_strongest": res["effect_vs_strongest"]["label"],
    }
    if res["decision"] == "UNVERIFIED":
        record["unverified_reason"] = res["why"]
    return record


# ------------------------------------------------------------------------------------------ orchestration
def _crash_record(cand: dict, error: str, runtime: float, decision: str = "CRASH", **extra) -> dict:
    rec = v2._crash_record(cand, error, runtime, decision, **extra)
    rec["run_id"] = "B2Q1-" + rec["run_id"][3:]
    rec["scope"] = SCOPE
    return rec


def worker_main(cand_path: str, out_path: str, cache_dir: str | None = None) -> int:
    cand = json.loads(Path(cand_path).read_text(encoding="utf-8"))
    t0 = time.time()
    try:
        impl, why = resolve_q1(cand)
        if impl is None:
            out = {"status": "skipped", "reason": why}
        else:
            out = {
                "status": "ok",
                "record": run_experiment(
                    cand, impl, Path(cache_dir) if cache_dir else v2.STAGE_DIR / "cache"
                ),
            }
    except sb.GUARD_ERRORS as e:
        out = {
            "status": "invalid",
            "record": _crash_record(
                cand, str(e), time.time() - t0, "INVALID", invalid_reason=f"{type(e).__name__}: {e}"
            ),
        }
    except Exception as e:  # noqa: BLE001
        import traceback

        out = {
            "status": "crash",
            "record": _crash_record(
                cand, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}", time.time() - t0
            ),
        }
    sb._write_json_atomic(Path(out_path), out)
    return 0


def triage(cand: dict, ledger_path=lg.LEDGER_PATH) -> tuple[str, dict | None]:
    v = preflight(cand, stage="B", ledger_path=ledger_path, suite=v2.SUITE)
    if v.status == "INVALID":
        rec = _crash_record(cand, "preflight", 0.0, "INVALID", invalid_reason="; ".join(v.reasons))
        rec["results"] = {"preflight": v.to_dict()}
        return "invalid", rec
    if v.status == "DUPLICATE":
        return "duplicate", {"status": v.status, "reasons": v.reasons}
    if not v.ok:
        return "blocked", {"status": v.status, "reasons": v.reasons}
    impl, why = resolve_q1(cand)
    if impl is None:
        return "skip", {"status": "NOT_IMPLEMENTED", "reasons": [why]}
    return "run", None


def _run_cpu_capped(
    cmd: list[str], cpu_cap_s: float, wall_cap_s: float = 1800.0
) -> tuple[str, float]:
    """Run ``cmd``; kill it when its CPU time (user+system = active compute) exceeds ``cpu_cap_s``.

    The A1 cap is "<= 300 s active compute per experiment". On a shared machine wall-clock would also charge CPU contention
    and SMT slowdown to the experiment (a 16-cell scope-(iii) experiment needs ~270 CPU-s alone), so scope (iii) measures CPU
    seconds. A wall ceiling still guards against a hung process."""
    import subprocess

    import psutil

    p = psutil.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=sb.REPO_ROOT)
    t0, cpu = time.time(), 0.0
    while True:
        try:
            p.wait(timeout=1.0)
            return "ok", cpu
        except psutil.TimeoutExpired:
            pass
        try:
            # the venv python.exe is a launcher: the real interpreter is its child, so sum the whole process tree
            cpu = 0.0
            for q in [p, *p.children(recursive=True)]:
                ct = q.cpu_times()
                cpu += ct.user + ct.system
        except psutil.Error:
            continue
        if cpu > cpu_cap_s or time.time() - t0 > wall_cap_s:
            for c in [*p.children(recursive=True), p]:
                try:
                    c.kill()
                except psutil.Error:
                    pass
            return ("cpu_cap" if cpu > cpu_cap_s else "wall_ceiling"), cpu


def screen(
    cand: dict, work_dir: Path, *, timeout_s: float = v2.TIMEOUT_S, ledger_path=lg.LEDGER_PATH
) -> tuple[str, dict]:
    action, payload = triage(cand, ledger_path)
    if action != "run":
        return action, payload or {}
    work_dir.mkdir(parents=True, exist_ok=True)
    cp, op = (
        work_dir / f"{cand['candidate_id']}.q1.cand.json",
        work_dir / f"{cand['candidate_id']}.q1.out.json",
    )
    cp.write_text(json.dumps(cand), encoding="utf-8")
    if op.exists():
        op.unlink()
    cmd = [sys.executable, "-m", "shiftlab.autoresearch.stage_b_q1", "--worker", str(cp), str(op)]
    t0 = time.time()
    status, cpu = _run_cpu_capped(cmd, timeout_s)
    if status != "ok":
        return "crash", _crash_record(
            cand,
            f"timeout: exceeded {timeout_s:.0f}s active compute ({status}; cpu_s={cpu:.1f}); process killed",
            time.time() - t0,
        )
    if not op.exists():
        return "crash", _crash_record(cand, "worker exited without output", time.time() - t0)
    out = json.loads(op.read_text(encoding="utf-8"))
    if out["status"] == "skipped":
        return "skip", {"status": "NOT_IMPLEMENTED", "reasons": [out["reason"]]}
    return out["status"], out["record"]


def select_scope(batch: list[dict] | None = None) -> dict:
    batch = batch if batch is not None else sb.load_batch()
    sel = [
        {
            "candidate_id": c["candidate_id"], "family": c["family"], "variant": c["variant"], "host": c["host"],
            "hook": c["hook"], "null": c["target_null"], "scope": ["iii"],
            "reasons": ["A1 scope (iii): batch-001 Q1 evidence identity, hook available at commit 35be7435"],
        }
        for c in batch
        if c["research_question"] == "Q1" and c["hook"] == "d2a.evidence_log_lik"
    ]  # fmt: skip
    return {"amendment": "A1", "scope": SCOPE, "n_selected": len(sel), "selected": sel,
            "cells": [c["id"] for c in q1_cells()]}  # fmt: skip


def warm_jobs() -> list[tuple]:
    jobs = []
    for cd in q1_cells():
        for comp in (*Q1_COMPARATORS, "host_d2a"):
            for k in range(v2.N_REP // v2.CHUNK) if cd["suite"] == "v2" else [None]:
                jobs.append((comp, cd["id"], k))
    heavy = {"gapmix_exact08_s4": 0, "thinned_hedged_gate": 1}
    return sorted(jobs, key=lambda j: heavy.get(j[0], 2))


def warm_main(comp: str, cell_id: str, chunk: str, cache_dir: str) -> int:
    cell = next(c for c in q1_cells() if c["id"] == cell_id)
    reference(comp, cell, Path(cache_dir), None if chunk == "None" else int(chunk))
    return 0


def run_tranche(cands: list[dict], *, ledger_path=lg.LEDGER_PATH, work_dir: Path = v2.STAGE_DIR / "work_t2_q1",
                max_workers: int = v2.MAX_WORKERS, limit: int | None = None, log=print, status_cb=None) -> dict:  # fmt: skip
    import os
    import subprocess
    from collections import Counter

    if max_workers > v2.MAX_WORKERS:
        raise ValueError(f"at most {v2.MAX_WORKERS} workers")
    os.environ.setdefault("SHIFTLAB_STAGE_B_CODE_HASH", sb.code_hash())
    work_dir.mkdir(parents=True, exist_ok=True)
    already = {
        r["candidate_id"] for r in lg.read_all(ledger_path)
        if r.get("stage") == "B" and r.get("suite") == v2.SUITE and r.get("scope") == SCOPE and r.get("decision") != "CRASH"
    }  # fmt: skip
    todo, not_run = [], Counter()
    for c in cands:
        if c["candidate_id"] in already:
            not_run["already_in_ledger"] += 1
            continue
        action, payload = triage(c, ledger_path)
        if action in ("run", "invalid"):
            todo.append(c)
        else:
            not_run[payload["status"]] += 1
            with NOT_RUN_PATH.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps({"candidate_id": c["candidate_id"], "scope": SCOPE, **payload})
                    + "\n"
                )
    if limit:
        todo = todo[:limit]
    st = {"t0": time.time(), "total": len(todo), "done": 0, "tally": Counter(), "not_run": dict(not_run),
          "inflight": [], "last": "", "phase": "warming references", "scope": SCOPE}  # fmt: skip

    def push():
        sb._write_json_atomic(STATE_PATH, {**st, "updated": time.time()})
        if status_cb:
            status_cb(st)

    push()
    cache_dir = v2.STAGE_DIR / "cache"
    jobs = warm_jobs()
    log(f"scope iii: warming {len(jobs)} reference runs ...")

    def warm(job):
        comp, cid, k = job
        cmd = [
            sys.executable,
            "-m",
            "shiftlab.autoresearch.stage_b_q1",
            "--warm",
            comp,
            cid,
            str(k),
            str(cache_dir),
        ]
        try:
            r = subprocess.run(
                cmd, timeout=7200, capture_output=True, text=True, cwd=sb.REPO_ROOT, check=False
            )
            if r.returncode:
                log(f"warm FAILED {comp} {cid}.{k}: {r.stderr[-300:]}")
        except subprocess.TimeoutExpired:
            log(f"warm TIMEOUT {comp} {cid}.{k}")

    with ThreadPoolExecutor(max_workers) as ex:
        list(ex.map(warm, jobs))
    st["phase"] = "screening candidates"
    push()

    def one(ic):
        i, c = ic
        st["inflight"].append(c["candidate_id"])
        try:
            return i, screen(c, work_dir, ledger_path=ledger_path)
        finally:
            st["inflight"].remove(c["candidate_id"])

    results, nxt = {}, 0
    with ThreadPoolExecutor(max_workers) as ex:
        futs = [ex.submit(one, (i, c)) for i, c in enumerate(todo)]
        for f in futs:
            i, (a, r) = f.result()
            results[i] = (a, r)
            while nxt in results:
                a, r = results.pop(nxt)
                c = todo[nxt]
                if a in ("ok", "crash", "invalid"):
                    committed = v2.commit(r, ledger_path)
                    st["tally"][committed["decision"]] += 1
                    st["last"] = (
                        f"{c['family']}.{c['variant']}[{c['target_null']}] -> {committed['decision']} ({committed['runtime_s']}s)"
                    )
                else:
                    st["tally"][a.upper()] += 1
                    st["last"] = f"{c['family']}.{c['variant']} -> {a}"
                st["done"] += 1
                log(st["last"])
                push()
                nxt += 1
    st["phase"] = "finished"
    push()
    return {"done": st["done"], "tally": dict(st["tally"]), "not_run": dict(not_run)}


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "--worker":
        return worker_main(argv[1], argv[2])
    if len(argv) >= 5 and argv[0] == "--warm":
        return warm_main(argv[1], argv[2], argv[3], argv[4])
    print("use scripts/d2a_rar/run_stage_b_t2.py --scope-iii ...", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
