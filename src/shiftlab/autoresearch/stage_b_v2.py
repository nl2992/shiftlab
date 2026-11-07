"""Stage-B tranche 2 under Amendment A1 (DEV_SUITE_v2 + ``calibrated_v1`` hosts + the A1 comparator set).

Registered in ``docs/d2a_rar/AUTORESEARCH_PROGRAM.md`` section 3a (A1, frozen). This module only WIRES that amendment;
it adds no cell, seed, host or comparator beyond it. Suite v1 (``stage_b.py``) is untouched and keeps running as before.

* Suite: ``docs/d2a_rar/registry/DEV_SUITE_v2.json`` (15 cells S1a-S4c). Per-cell T / label cap / cost vector /
  retrain duration come from the JSON; the SHA-256 of the JSON and of ``configs/d2a_rar/stream_families_v2.yaml`` are
  verified at load against the values registered in A1.
* Seeds: ``110050000 + cell_index*1000 + replicate`` (20 replicates), paired across every method, disjoint from v1.
* Hosts: ``calibrated_v1`` (candidate and unmodified-host ablation); ONE ``native_v0`` host run per cell is stored as a
  reported reference (never a comparator).
* Comparators: the candidate's host, uniform_query, fixed_schedule, pending_cap, episode_front, never_switch, Gap-Mix
  ``exact0.8_s4`` and the gap-10 thinned gate (``thinned_hedged_gate``). The strongest applicable comparator is chosen
  per cell among those valid for the candidate's claimed null on its validity cells (``stage_b.analyse(suite="v2")``).
* Ledger: every record carries ``suite="v2"`` and ``amendment="A1"``.
* Scope (A1 section "Scope of tranche 2"): (i) DUPLICATE of a host-identical behaviour, (ii) UNVERIFIED for a missing family
  v2 provides; (iii) Q1 evidence identities are excluded (their hook does not exist). Cap 140.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from shiftlab.bench.contract import BudgetSpec, EnvSpec, load_cost_vectors
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_rar import BinaryPolicy, RARPolicy
from shiftlab.bench.contract.audit import AuditViolation

from . import ledger as lg
from . import stage_b as sb
from .host_audit import load_family_v2
from .preflight import preflight
from .stage_b_variants import Impl, host_policy, host_profile, make_clocks, resolve

SUITE = "v2"
AMENDMENT = "A1"
PROFILE = "calibrated_v1"
SUITE_V2_PATH = sb.REPO_ROOT / "docs" / "d2a_rar" / "registry" / "DEV_SUITE_v2.json"
FAMILIES_V2_PATH = sb.REPO_ROOT / "configs" / "d2a_rar" / "stream_families_v2.yaml"
# registered in A1 (AUTORESEARCH_PROGRAM.md section 3a): full digests of the two frozen files
SUITE_V2_SHA256 = "414eacd015799b5c4ccd0878e721b63755578e92731b262291b046275f630659"
FAMILIES_V2_SHA256 = "9cd53491002cbf5b248d90b56c207fecc4156c61328e68835a2dc40bf140f898"
SEED_START = 110_050_000
N_REP = 20
CHUNK = 2  # seeds per cached chunk (warm jobs shard heavy comparators across workers)
MAX_EXPERIMENTS = 140
MAX_WORKERS = 12
TIMEOUT_S = 300
# dev-suite families that v1 lacked and v2 now provides (identities that were UNVERIFIED for one of these enter scope ii)
PROVIDED_FAMILIES = ("tight-deadline", "hazard/semi-Markov", "reversal")
A1_COMPARATORS = (
    "uniform_query",
    "fixed_schedule",
    "pending_cap",
    "episode_front",
    "never_switch",
    "gapmix_exact08_s4",
    "thinned_hedged_gate",
)
STAGE_DIR = sb.STAGE_DIR
SCOPE_PATH = STAGE_DIR / "tranche2_scope.json"
NOT_RUN_PATH = STAGE_DIR / "not_run_t2.jsonl"
TRANCHE1_NOT_RUN = STAGE_DIR / "not_run.jsonl"
STATE_PATH = STAGE_DIR / "tranche2_state.json"
STATUS_PATH = sb.REPO_ROOT / "docs" / "d2a_rar" / "status" / "wp6_stage_b_t2.md"

# calibrated_v1 host comparators (the native_v0 versions stay in stage_b.COMPARATORS as the reference runs)
HOST_CAL = {
    "d2a": ("host_d2a", lambda env: Drift2ActContractPolicy(profile=PROFILE), "abs_risk"),
    "rar": ("host_rar", lambda env: RARPolicy(profile=PROFILE), "none"),
    "cab": ("host_cab", lambda env: BinaryPolicy(cost_aware=True, profile=PROFILE), "none"),
}
V2_COMPARATORS = {**sb.COMPARATORS, **{n: (f, nul) for n, f, nul in HOST_CAL.values()}}


# ------------------------------------------------------------------------------------------ suite
def _sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _sha(path: Path) -> str:
    """Digest in the form registered by A1: the Windows working-copy bytes (CRLF). Git stores these files with LF, so
    line endings are normalised to CRLF first; the digest is then identical on every checkout."""
    b = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(b).hexdigest()


def load_suite_v2(
    *, suite_path: Path = SUITE_V2_PATH, families_path: Path = FAMILIES_V2_PATH
) -> dict:
    """Load DEV_SUITE_v2 after verifying the registered checksums of the suite JSON and the v2 families file."""
    if _sha(suite_path) != SUITE_V2_SHA256:
        raise ValueError(
            f"{suite_path.name}: sha256 differs from the value registered in amendment A1"
        )
    if _sha(families_path) != FAMILIES_V2_SHA256:
        raise ValueError(
            f"{families_path.name}: sha256 differs from the value registered in amendment A1"
        )
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    ids = [c["id"] for c in suite["cells"]]
    if ids != [
        f"S{a}{b}" for a, bs in ((1, "abc"), (2, "abcdef"), (3, "abc"), (4, "abc")) for b in bs
    ]:
        raise ValueError(f"unexpected v2 cell ids {ids}")
    if [c["index"] for c in suite["cells"]] != list(range(len(ids))) or suite[
        "seeds_per_cell"
    ] != N_REP:
        raise ValueError("v2 suite indices / replicate count differ from A1")
    return suite


def cell_seeds(index: int) -> list[int]:
    return [SEED_START + index * 1000 + r for r in range(N_REP)]


def cell_spec(cell: dict):
    spec = load_family_v2(cell["family"], cell["family_source"])
    if spec.T != cell["T"]:
        raise ValueError(f"cell {cell['id']}: family T {spec.T} != suite T {cell['T']}")
    return spec


def make_env(spec, cell: dict, clocks: str) -> EnvSpec:
    """Per-cell T (from the family), label cap and cost vector (cell values; no host override in v2)."""
    ck = make_clocks(clocks)
    if cell["retrain_duration"] != ck.retrain_duration or cell["max_lookback"] != ck.max_lookback:
        raise ValueError(f"cell {cell['id']}: clock mismatch with the suite")
    return EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()[cell["cost_vector"]],
        budget=BudgetSpec(label_cap=cell["label_cap"]),
        clocks=ck,
    )


# ------------------------------------------------------------------------------------------ cached reference runs
def _cache_path(cache_dir: Path, tag: str, cell: dict, clocks: str, T: int, k: int) -> Path:
    key = hashlib.sha256(
        json.dumps(
            [SUITE, tag, cell["id"], cell["family"], cell["cost_vector"], clocks, PROFILE,
             SEED_START + cell["index"] * 1000, N_REP, T, cell["label_cap"], cell["retrain_duration"], sb._code_hash(), k, CHUNK]
        ).encode()
    ).hexdigest()[:20]  # fmt: skip
    return cache_dir / f"v2__{tag}__{cell['id']}__{clocks}__c{k}__{key}.json"


def _cached(
    cache_dir: Path,
    tag: str,
    cell: dict,
    clocks: str,
    mk,
    *,
    profile_ctx: bool = False,
    chunk: int | None = None,
) -> list[dict]:
    """Reference runs for one cell, cached in seed chunks of ``CHUNK`` (chunks are independent paired runs: every seed is
    its own stream and policy instance, so concatenation equals one run over all 20 seeds). ``chunk=None`` => all."""
    spec = cell_spec(cell)
    seeds = cell_seeds(cell["index"])
    runs: list[dict] = []
    for k in [chunk] if chunk is not None else range(N_REP // CHUNK):
        path = _cache_path(cache_dir, tag, cell, clocks, spec.T, k)
        if path.exists():
            runs += json.loads(path.read_text(encoding="utf-8"))["runs"]
            continue
        env = make_env(spec, cell, clocks)
        t0 = time.time()
        sub = seeds[k * CHUNK : (k + 1) * CHUNK]
        if profile_ctx:
            with host_profile(PROFILE):
                part = sb.run_method(mk, spec, env, sub, tag)
        else:
            part = sb.run_method(mk, spec, env, sub, tag)
        sb._write_json_atomic(
            path, {"tag": tag, "cell": cell["id"], "runtime_s": time.time() - t0, "runs": part}
        )
        runs += part
    return runs


def reference(
    comp: str, cell: dict, clocks: str, cache_dir: Path, chunk: int | None = None
) -> list[dict]:
    """A comparator under A1 (host comparators with the calibrated_v1 profile)."""
    return _cached(cache_dir, comp, cell, clocks, V2_COMPARATORS[comp][0], chunk=chunk)


def native_reference(
    kind: str, host_kwargs: dict, cell: dict, clocks: str, cache_dir: Path, chunk: int | None = None
) -> list[dict] | None:
    """The single native_v0 host run per cell (reported reference, never a comparator)."""
    if kind not in HOST_CAL:
        return None
    if not host_kwargs:
        return _cached(
            cache_dir,
            "native__" + HOST_CAL[kind][0],
            cell,
            clocks,
            sb.COMPARATORS[HOST_CAL[kind][0]][0],
            chunk=chunk,
        )
    tag = (
        "native__host_"
        + kind
        + "_"
        + hashlib.sha256(json.dumps(host_kwargs, sort_keys=True).encode()).hexdigest()[:8]
    )
    return _cached(cache_dir, tag, cell, clocks, lambda e: host_policy(kind, host_kwargs))


def host_runs(impl: Impl, cell: dict, cache_dir: Path) -> list[dict]:
    """Unmodified calibrated_v1 host with the candidate's non-hook host kwargs = the mechanistic ablation."""
    if not impl.host_kwargs:
        return reference(sb.HOST_COMPARATOR[impl.kind], cell, impl.clocks, cache_dir)
    tag = (
        "host_"
        + impl.kind
        + "_"
        + hashlib.sha256(json.dumps(impl.host_kwargs, sort_keys=True).encode()).hexdigest()[:8]
    )
    return _cached(
        cache_dir,
        tag,
        cell,
        impl.clocks,
        lambda e: host_policy(impl.kind, impl.host_kwargs),
        profile_ctx=True,
    )


# ------------------------------------------------------------------------------------------ v1 regression rule
def v1_regressions(candidate_id: str, ledger_path=lg.LEDGER_PATH) -> list[str]:
    """A1: a candidate must not be worse than its host on any v1 cell it ran on (paired CI above 0)."""
    out = []
    for r in lg.read_all(ledger_path):
        if (
            r.get("candidate_id") == candidate_id
            and r.get("stage") == "B"
            and r.get("suite", "v1") == "v1"
            and r.get("decision") not in ("CRASH", "INVALID")
            and r.get("uncertainty")
        ):
            for x in r["uncertainty"].get("dJ_vs_host", []):
                if x["dJ_ci95"][0] > 0:
                    out.append(
                        f"{x['role']}:{x['family']} dJ={x['dJ_mean']:.3f} CI95={x['dJ_ci95']}"
                    )
            break
    return out


def behaviour_sha(cells: list[dict], key: str) -> str:
    blob = [
        [
            c["id"],
            c["family"],
            [round(r["J"], 6) for r in c["runs"][key]],
            [r["counts"] for r in c["runs"][key]],
        ]
        for c in cells
    ]
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


def near_keep(res: dict) -> bool:
    """DISCARD only because of the control / host-ablation / complexity / simple-control criteria: valid under the claimed
    null, not invalid-aggressive, and a non-'none' effect label against the strongest applicable comparator."""
    return bool(
        res["decision"] == "DISCARD"
        and res["valid_ok"]
        and not res["invalid_aggressive"]
        and res["effect_vs_strongest"]["label"] != "none"
    )


# ------------------------------------------------------------------------------------------ experiment
def run_experiment(
    cand: dict, impl: Impl, cache_dir: Path = STAGE_DIR / "cache", ledger_path=lg.LEDGER_PATH
) -> dict:
    t0 = time.time()
    suite = load_suite_v2()
    cells_def = suite["cells"]
    kind = impl.kind
    host_key = "host"
    required = cand["required_baselines"]
    missing = sorted(b for b in required if b not in sb.BASELINE_IMPL)
    not_in_a1 = sorted(
        b for b in required if b in sb.BASELINE_IMPL
        and sb.BASELINE_IMPL[b] not in (*A1_COMPARATORS, sb.HOST_COMPARATOR[kind])
    )  # fmt: skip
    cells: list[dict] = []
    for cd in cells_def:
        runs = {host_key: host_runs(impl, cd, cache_dir)}
        for comp in A1_COMPARATORS:
            runs[comp] = reference(comp, cd, impl.clocks, cache_dir)
        nat = native_reference(kind, impl.host_kwargs, cd, impl.clocks, cache_dir)
        if nat is not None:
            runs["native_v0"] = nat
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
    hostname = sb.HOST_COMPARATOR[kind]
    comp_meta = {
        m: {
            "claimed_null": V2_COMPARATORS[m][1],
            "is_control": m in sb.SIMPLE_CONTROLS,
            "baseline_ids": [b for b in required if sb.BASELINE_IMPL.get(b) == m],
            **({"is_host": True} if m == hostname else {}),
        }
        for m in A1_COMPARATORS
    }
    kw = {
        "cand_null": cand["target_null"],
        "comp_meta": comp_meta,
        "cx": cand["complexity"]["level"],
        "suite": "v2",
    }
    pre_cells = [dict(c, runs={**c["runs"], "cand": c["runs"][host_key]}) for c in cells]
    pre = sb.analyse(pre_cells, **kw)
    target_cells = [f"{c['id']}:{c['family']}" for c in cells if c["role"] in sb.TARGET_ROLES]
    prereg = {
        **sb.preregistration(cand, impl, cells_def, pre["strongest_comparator"], target_cells),
        "suite": SUITE,
        "amendment": AMENDMENT,
        "host_profile": PROFILE,
        "comparator_set": [f"host({hostname},{PROFILE})", *A1_COMPARATORS],
        "strongest_comparator_at_registration_per_cell": pre["strongest_comparator_per_cell"],
        "native_v0_reference": "reported only (never a comparator)",
    }
    prereg_sha = hashlib.sha256(json.dumps(prereg, sort_keys=True).encode()).hexdigest()
    # ---- candidate runs (calibrated_v1 host profile for every Feed*/Gated* host)
    for cd, c in zip(cells_def, cells, strict=True):
        spec = cell_spec(cd)
        env = make_env(spec, cd, impl.clocks)
        with host_profile(PROFILE):
            c["runs"]["cand"] = sb.run_method(
                impl.build_cand, spec, env, cell_seeds(cd["index"]), "cand"
            )
    for c in cells:
        fps = {tuple(r["fingerprint"] for r in runs) for runs in c["runs"].values()}
        if len(fps) != 1:
            raise AuditViolation(f"unpaired runs in cell {c['id']}")
    absent = impl.absent_family if impl.absent_family not in PROVIDED_FAMILIES else None
    regress = v1_regressions(cand["candidate_id"], ledger_path)
    res = sb.analyse(
        cells,
        **kw,
        absent_family=absent,
        rollback_family=impl.rollback_family,
        candidate_key="cand",
        host_key=host_key,
        extra_reasons=[f"worse than host on a v1 cell it ran on: {x}" for x in regress],
    )
    strongest = res["strongest_comparator"]
    show = ["cand", host_key] + [
        m for m in dict.fromkeys(res["strongest_comparator_per_cell"].values()) if m != host_key
    ]
    pf = preflight(cand, stage="B", ledger_path=ledger_path, suite=SUITE)
    # native_v0 reference: paired dJ(candidate - native host) per cell, plus J of the native host
    native = {}
    for c in cells:
        if "native_v0" in c["runs"]:
            d = sb._a(c["runs"]["cand"]) - sb._a(c["runs"]["native_v0"])
            mean, lo, hi = sb._ci(d)
            native[c["id"]] = {
                "J_native_v0_host": float(np.mean(sb._a(c["runs"]["native_v0"]))),
                "J_calibrated_host": float(np.mean(sb._a(c["runs"][host_key]))),
                "dJ_cand_minus_native": mean,
                "dJ_ci95": [lo, hi],
            }
    seeds_all = [s for cd in cells_def for s in cell_seeds(cd["index"])]
    simple = {
        m: [x for x in res["dJ_vs_each_comparator"].get(m, []) if x["role"] in sb.TARGET_ROLES]
        for m in ("pending_cap", "fixed_schedule", "uniform_query")
    }
    record = {
        "candidate_id": cand["candidate_id"],
        "run_id": f"B2-{cand['candidate_id']}-{prereg_sha[:8]}",
        "stage": "B",
        "suite": SUITE,
        "amendment": AMENDMENT,
        "git_commit": lg.current_git_commit(),
        "method": f"{cand['family']}.{cand['variant']}@{cand['host']}[{cand['hook']}]",
        "host": cand["host"],
        "fidelity_tier": "COMMON_CONTRACT_PORT"
        if cand["host"] == "contract_native"
        else "PAPER_RECONSTRUCTION",
        "data_hashes": {
            "dev_suite_v2_sha256": SUITE_V2_SHA256,
            "stream_families_v2_sha256": FAMILIES_V2_SHA256,
            "config_sha256": pf.hashes.get("config_sha256"),
            "hook_module_sha256": pf.hashes.get("hook_module_sha256"),
            "adapter_module_sha256": pf.hashes.get("adapter_module_sha256"),
            "stage_b_variants_sha256": hashlib.sha256(
                Path(sb.__file__)
                .with_name("stage_b_variants.py")
                .read_bytes()
                .replace(b"\r\n", b"\n")
            ).hexdigest(),
            "stage_b_v2_sha256": _sha_lf(Path(__file__)),
            "code_hash16": sb._code_hash(),
        },
        "seed_group": {
            "block": "d2a_rar_dev",
            "sub_block": "v2",
            "seed_start": min(seeds_all),
            "seed_end": max(seeds_all),
            "exposure": "dev",
            "replicates_per_cell": N_REP,
            "cell_indices": [c["index"] for c in cells_def],
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
                        k: c[k] for k in ("T", "label_cap", "cost_vector", "retrain_duration")
                    }
                    for c in cells_def
                },
                "host_profile": PROFILE,
                "clocks": impl.clocks,
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
            "q2_simple_control_dJ_target_cells": simple,
            "valid_ok": res["valid_ok"],
            "invalid_aggressive": res["invalid_aggressive"],
            "near_keep": near_keep({**res}),
            "discard_reasons": res["discard_reasons"],
            "v1_regressions": regress,
            "native_v0_reference": native,
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
                "hook_restored_to_host_default": "identical to the unmodified calibrated_v1 host reference (host runs are the ablation)"
            },
            "dJ_vs_each_implemented_comparator": res["dJ_vs_each_comparator"],
            "comparator_mapping": {
                m: {"baseline_ids": comp_meta[m]["baseline_ids"]} for m in comp_meta
            },
        },
        "baselines_missing": missing,
        "required_baselines_outside_A1_set": not_in_a1,
        "counterexamples": res["counterexamples"],
        "prior_art_status": cand["prior_art_status"],
        "decision": res["decision"],
        "behaviour_sha256": behaviour_sha(cells, "cand"),
        "family_caveat": absent,
        "role": cand["role"],
        "effect_label_vs_strongest": res["effect_vs_strongest"]["label"],
    }
    if res["decision"] == "UNVERIFIED":
        record["unverified_reason"] = res["why"]
    return record


# ------------------------------------------------------------------------------------------ worker / orchestration
def _crash_record(cand: dict, error: str, runtime: float, decision: str = "CRASH", **extra) -> dict:
    rec = sb._crash_record(cand, error, runtime, decision, **extra)
    rec["run_id"] = "B2-" + rec["run_id"][2:]
    rec["suite"], rec["amendment"] = SUITE, AMENDMENT
    rec["data_hashes"] = {
        "dev_suite_v2_sha256": SUITE_V2_SHA256,
        "stream_families_v2_sha256": FAMILIES_V2_SHA256,
        "code_hash16": sb._code_hash(),
    }
    last = len(load_suite_v2()["cells"]) - 1
    rec["seed_group"] = {
        "block": "d2a_rar_dev",
        "sub_block": "v2",
        "seed_start": SEED_START,
        "seed_end": SEED_START + last * 1000 + N_REP - 1,
        "exposure": "dev",
    }
    return rec


def worker_main(cand_path: str, out_path: str, cache_dir: str | None = None) -> int:
    cand = json.loads(Path(cand_path).read_text(encoding="utf-8"))
    t0 = time.time()
    try:
        impl, why = resolve(cand)
        if impl is None:
            out = {"status": "skipped", "reason": why}
        else:
            out = {
                "status": "ok",
                "record": run_experiment(
                    cand, impl, Path(cache_dir) if cache_dir else STAGE_DIR / "cache"
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


def worker_cmd(cand_path: Path, out_path: Path, cache_dir: Path | None = None) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "shiftlab.autoresearch.stage_b_v2",
        "--worker",
        str(cand_path),
        str(out_path),
    ]
    return cmd + (["--cache-dir", str(cache_dir)] if cache_dir else [])


def triage(cand: dict, ledger_path=lg.LEDGER_PATH) -> tuple[str, dict | None]:
    v = preflight(cand, stage="B", ledger_path=ledger_path, suite=SUITE)
    if v.status == "INVALID":
        rec = _crash_record(cand, "preflight", 0.0, "INVALID", invalid_reason="; ".join(v.reasons))
        rec["results"] = {"preflight": v.to_dict()}
        return "invalid", rec
    if v.status == "DUPLICATE":
        return "duplicate", {"status": v.status, "reasons": v.reasons}
    if not v.ok:
        return "blocked", {"status": v.status, "reasons": v.reasons}
    impl, why = resolve(cand)
    if impl is None:
        return "skip", {"status": "NOT_IMPLEMENTED", "reasons": [why]}
    return "run", None


def screen(
    cand: dict, work_dir: Path, *, timeout_s: float = TIMEOUT_S, cache_dir: Path | None = None,
    argv: list[str] | None = None, ledger_path=lg.LEDGER_PATH,
) -> tuple[str, dict]:  # fmt: skip
    action, payload = triage(cand, ledger_path)
    if action != "run":
        if action == "invalid":
            return "invalid", payload
        return action, payload or {}
    work_dir.mkdir(parents=True, exist_ok=True)
    cp, op = (
        work_dir / f"{cand['candidate_id']}.t2.cand.json",
        work_dir / f"{cand['candidate_id']}.t2.out.json",
    )
    cp.write_text(json.dumps(cand), encoding="utf-8")
    if op.exists():
        op.unlink()
    cmd = argv or worker_cmd(cp, op, cache_dir)
    t0 = time.time()
    try:
        subprocess.run(
            cmd, timeout=timeout_s, check=False, capture_output=True, text=True, cwd=sb.REPO_ROOT
        )
    except subprocess.TimeoutExpired:
        return "crash", _crash_record(
            cand,
            f"timeout: exceeded {timeout_s:.0f}s wall-clock hard limit (process killed)",
            time.time() - t0,
        )
    if not op.exists():
        return "crash", _crash_record(cand, "worker exited without output", time.time() - t0)
    out = json.loads(op.read_text(encoding="utf-8"))
    if out["status"] == "skipped":
        return "skip", {"status": "NOT_IMPLEMENTED", "reasons": [out["reason"]]}
    return out["status"], out["record"]


def commit(record: dict, ledger_path=lg.LEDGER_PATH) -> dict:
    """Single-writer commit; behavioural DUPLICATE detection only against earlier suite-v2 records."""
    sig = record.get("behaviour_sha256")
    if sig and record["decision"] in ("KEEP", "DISCARD", "UNVERIFIED"):
        for r in lg.read_all(ledger_path):
            if (
                r.get("suite") == SUITE
                and r.get("behaviour_sha256") == sig
                and r["candidate_id"] != record["candidate_id"]
                and r.get("decision") in ("KEEP", "DISCARD", "UNVERIFIED")
                and r.get("stage") == "B"
            ):
                dup = dict(record)
                dup["decision_if_not_duplicate"] = record["decision"]
                dup["decision"] = "DUPLICATE"
                dup["duplicate_of"] = r["candidate_id"]
                dup["run_id"] = record["run_id"] + "-dup"
                return lg.append(dup, ledger_path)
    return lg.append(record, ledger_path)


# ------------------------------------------------------------------------------------------ scope
def _host_identical(rec: dict) -> bool:
    d = (rec.get("uncertainty") or {}).get("dJ_vs_host") or []
    return bool(d) and all(
        abs(x["dJ_mean"]) < 1e-9 and all(abs(b) < 1e-9 for b in x["dJ_ci95"]) for x in d
    )


def select_scope(
    ledger_path=lg.LEDGER_PATH,
    not_run_path: Path = TRANCHE1_NOT_RUN,
    batch: list[dict] | None = None,
    cap: int = MAX_EXPERIMENTS,
) -> dict:
    """Tranche-2 scope per A1 (i)-(ii); (iii) Q1 evidence identities are excluded. Pure function of the ledger."""
    batch = batch if batch is not None else sb.load_batch()
    bid = {c["candidate_id"]: c for c in batch}
    recs = [
        r
        for r in lg.read_all(ledger_path)
        if r.get("stage") == "B" and r.get("suite", "v1") == "v1"
    ]
    by_id = {r["candidate_id"]: r for r in recs if r["decision"] != "CRASH"}
    entries: dict[str, dict] = {}
    excluded: list[dict] = []

    def anchor_of(r):
        seen = set()
        while r["decision"] == "DUPLICATE" and r["candidate_id"] not in seen:
            seen.add(r["candidate_id"])
            r = by_id[r["duplicate_of"]]
        return r

    for r in recs:
        cid = r["candidate_id"]
        if cid not in bid:
            continue
        c = bid[cid]
        caveat = r.get("family_caveat")
        reasons = []
        if r["decision"] == "DUPLICATE":
            a = anchor_of(r)
            if _host_identical(a):
                reasons.append(
                    (
                        "i",
                        f"DUPLICATE of host-identical behaviour (anchor {a['candidate_id']}: dJ vs host = 0 on every v1 cell)",
                    )
                )
            else:
                excluded.append(
                    {
                        "candidate_id": cid,
                        "reason": f"DUPLICATE of a non-host-identical behaviour (anchor {a['candidate_id']})",
                        "also_family_gap": caveat,
                    }
                )
        if (
            r["decision"] in ("UNVERIFIED", "DUPLICATE")
            and (caveat or "") in PROVIDED_FAMILIES
            and (
                r["decision"] == "UNVERIFIED" or r.get("decision_if_not_duplicate") == "UNVERIFIED"
            )
        ):
            reasons.append(
                (
                    "ii",
                    f"UNVERIFIED in v1 for missing family '{caveat}', now provided by DEV_SUITE_v2",
                )
            )
        if not reasons and r["decision"] == "UNVERIFIED":
            excluded.append(
                {
                    "candidate_id": cid,
                    "reason": f"UNVERIFIED for family '{caveat}' that v2 does not provide",
                }
            )
        if reasons:
            e = entries.setdefault(
                cid,
                {
                    "candidate_id": cid, "research_question": c["research_question"], "family": c["family"],
                    "variant": c["variant"], "host": c["host"], "hook": c["hook"], "scope": [], "reasons": [],
                    "v1_decision": r["decision"],
                },
            )  # fmt: skip
            for s, why in reasons:
                if s not in e["scope"]:
                    e["scope"].append(s)
                e["reasons"].append(why)
            if (caveat or "") not in PROVIDED_FAMILIES and caveat:
                e["note"] = (
                    f"needs family '{caveat}' that v2 does not provide: expected to remain UNVERIFIED"
                )
    order = {c["candidate_id"]: i for i, c in enumerate(batch)}  # batch is priority-sorted
    sel = sorted(entries.values(), key=lambda e: order[e["candidate_id"]])
    over = sel[cap:]
    sel = sel[:cap]
    nr = [
        json.loads(x)
        for x in Path(not_run_path).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    q1_evidence = sorted(
        x["candidate_id"]
        for x in nr
        if bid.get(x["candidate_id"], {}).get("research_question") == "Q1"
    )
    return {
        "amendment": AMENDMENT,
        "suite": SUITE,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "ledger_head_v1": lg.read_all(ledger_path)[-1]["record_sha256"],
        "cap": cap,
        "n_selected": len(sel),
        "n_over_cap_dropped": len(over),
        "scope_counts": dict(Counter(s for e in sel for s in e["scope"])),
        "selected": sel,
        "excluded": {
            "scope_iii_q1_evidence_identities": {"n": len(q1_evidence), "reason": "label-outcome evidence hook does not exist yet (A1 scope iii needs a further amendment line)", "candidate_ids": q1_evidence},
            "other_not_run_tranche1": {"n": len([x for x in nr if x["candidate_id"] not in set(q1_evidence)]), "reason": "NOT_IMPLEMENTED / BLOCKED in tranche 1 for reasons other than a missing dev-suite family (none cites a family v2 provides); not re-screened"},
            "ledger_records_not_in_scope": excluded,
        },
    }  # fmt: skip


# ------------------------------------------------------------------------------------------ warm-up + tranche
def warm_jobs(cands: list[dict]) -> list[tuple]:
    suite = load_suite_v2()
    jobs: dict[tuple, tuple] = {}
    for c in cands:
        impl, _ = resolve(c)
        names = {*A1_COMPARATORS, sb.HOST_COMPARATOR[impl.kind]}
        for comp in names:
            for cd in suite["cells"]:
                for k in range(N_REP // CHUNK):
                    jobs[(comp, cd["id"], impl.clocks, "cal", k)] = (
                        comp, cd["index"], impl.clocks, "cal", k,
                    )  # fmt: skip
        if impl.kind in HOST_CAL and not impl.host_kwargs:
            for cd in suite["cells"]:
                for k in range(N_REP // CHUNK):
                    nm = HOST_CAL[impl.kind][0]
                    jobs[(nm, cd["id"], impl.clocks, "native", k)] = (
                        nm, cd["index"], impl.clocks, "native", k,
                    )  # fmt: skip
    heavy = {
        "gapmix_exact08_s4": 0,
        "thinned_hedged_gate": 1,
    }  # slowest comparators first (load balance)
    return sorted(
        jobs.values(),
        key=lambda j: (heavy.get(j[0], 2), -load_suite_v2()["cells"][j[1]]["label_cap"], j[1]),
    )


def warm_main(comp: str, index: int, clocks: str, which: str, chunk: int, cache_dir: str) -> int:
    cell = load_suite_v2()["cells"][index]
    if which == "native":
        native_reference(
            next(k for k, v in HOST_CAL.items() if v[0] == comp),
            {},
            cell,
            clocks,
            Path(cache_dir),
            chunk,
        )
    else:
        reference(comp, cell, clocks, Path(cache_dir), chunk)
    return 0


def write_state(st: dict) -> None:
    sb._write_json_atomic(STATE_PATH, {**st, "updated": time.time()})


def run_tranche(
    cands: list[dict], *, ledger_path=lg.LEDGER_PATH, work_dir: Path = STAGE_DIR / "work_t2",
    status_cb=None, max_workers: int = MAX_WORKERS, limit: int | None = None, log=print, timeout_s: float = TIMEOUT_S,
) -> dict:  # fmt: skip
    if max_workers > MAX_WORKERS:
        raise ValueError(f"at most {MAX_WORKERS} workers")
    work_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(
        "SHIFTLAB_STAGE_B_CODE_HASH", sb.code_hash()
    )  # pin cache keys for all child processes
    already = {
        r["candidate_id"] for r in lg.read_all(ledger_path)
        if r.get("stage") == "B" and r.get("suite") == SUITE and r.get("decision") != "CRASH"
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
                    json.dumps({"candidate_id": c["candidate_id"], "suite": SUITE, **payload})
                    + "\n"
                )
    if limit:
        todo = todo[:limit]
    st = {
        "t0": time.time(), "total": len(todo), "done": 0, "tally": Counter(), "not_run": dict(not_run),
        "inflight": [], "last": "", "phase": "warming references", "n_scope": len(cands),
    }  # fmt: skip
    write_state(st)
    if status_cb:
        status_cb(st)
    runnable = [c for c in todo if triage(c, ledger_path)[0] == "run"]
    jobs = warm_jobs(runnable)
    log(f"warming {len(jobs)} reference runs ...")
    cache_dir = STAGE_DIR / "cache"

    def warm(job):
        comp, i, clocks, which, k = job
        cmd = [
            sys.executable,
            "-m",
            "shiftlab.autoresearch.stage_b_v2",
            "--warm",
            comp,
            str(i),
            clocks,
            which,
            str(k),
            str(cache_dir),
        ]
        try:
            r = subprocess.run(
                cmd, timeout=7200, capture_output=True, text=True, cwd=sb.REPO_ROOT, check=False
            )
            if r.returncode:
                log(f"warm FAILED {comp} cell{i}.{k}: {r.stderr[-300:]}")
        except subprocess.TimeoutExpired:
            log(f"warm TIMEOUT {comp} cell{i}.{k}")

    with ThreadPoolExecutor(max_workers) as ex:
        list(ex.map(warm, jobs))
    st["phase"] = "screening candidates"
    results: dict[int, tuple[str, dict]] = {}
    nxt = 0

    def one(idx_c):
        idx, c = idx_c
        st["inflight"].append(c["candidate_id"])
        try:
            return idx, screen(c, work_dir, timeout_s=timeout_s, ledger_path=ledger_path)
        finally:
            st["inflight"].remove(c["candidate_id"])

    with ThreadPoolExecutor(max_workers) as ex:
        futs = [ex.submit(one, (i, c)) for i, c in enumerate(todo)]
        for f in futs:  # ordered commit
            idx, (action, rec) = f.result()
            results[idx] = (action, rec)
            while nxt in results:
                a, r = results.pop(nxt)
                c = todo[nxt]
                if a in ("ok", "crash", "invalid"):
                    committed = commit(r, ledger_path)
                    st["tally"][committed["decision"]] += 1
                    st["last"] = (
                        f"{c['family']}.{c['variant']}@{c['host']} -> {committed['decision']} ({committed['runtime_s']}s)"
                    )
                else:
                    st["tally"][a.upper()] += 1
                    st["last"] = f"{c['family']}.{c['variant']} -> {a}"
                st["done"] += 1
                log(st["last"])
                write_state(st)
                if status_cb:
                    status_cb(st)
                nxt += 1
    st["phase"] = "finished"
    write_state(st)
    if status_cb:
        status_cb(st)
    return {"done": st["done"], "tally": dict(st["tally"]), "not_run": dict(not_run)}


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "--worker":
        cache = argv[4] if len(argv) >= 5 and argv[3] == "--cache-dir" else None
        return worker_main(argv[1], argv[2], cache)
    if len(argv) >= 7 and argv[0] == "--warm":
        return warm_main(argv[1], int(argv[2]), argv[3], argv[4], int(argv[5]), argv[6])
    print("use scripts/d2a_rar/run_stage_b_t2.py", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
