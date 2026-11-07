"""Stage-B screening runner (WP6): preflight -> host with the candidate variant in EXACTLY the declared hook ->
frozen light dev suite (paired seeds) -> verify_run on every run -> J with separated components, validity under the
claimed null, power/delay, paired-bootstrap dJ vs (a) the unmodified host (= the mechanistic ablation: hook restored to
the host default) and (b) the strongest applicable required baseline that is implemented -> KEEP/DISCARD per
``docs/d2a_rar/AUTORESEARCH_PROGRAM.md`` section 4 -> ONE hash-chained ledger record via ``ledger.append``.

Process model: ``screen`` runs the experiment in a worker subprocess with a hard wall-clock timeout (a timeout is a
CRASH record, never a silent truncation); the orchestrator (``run_tranche``) is the single ledger writer. Reference
(comparator) runs are cached on disk keyed by (comparator, family, cost vector, clocks, seed set, T, label cap, code hash).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from shiftlab.bench.contract import (
    BudgetSpec,
    EnvSpec,
    load_cost_vectors,
    load_family,
    make_stream,
    paired_bootstrap_ci,
    run_paired,
)
from shiftlab.bench.contract.adapters_asi import ASIAdapter
from shiftlab.bench.contract.adapters_controls import CONTROLS
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_gong_zhang import GongZhangAdapter
from shiftlab.bench.contract.adapters_inrepo import ADAPTERS
from shiftlab.bench.contract.adapters_rar import BinaryPolicy, RARPolicy
from shiftlab.bench.contract.audit import AuditViolation
from shiftlab.bench.contract.guards import LeakError
from shiftlab.bench.contract.types import CANDIDATE, ActionNotAllowed, BudgetExceeded

from . import grammar as g
from . import ledger as lg
from .dev_suite import DEV_SUITE, suite_sha256
from .preflight import preflight
from .stage_b_variants import Impl, host_policy, make_clocks, resolve

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGE_DIR = REPO_ROOT / "results" / "d2a_rar" / "stage_b"
STATUS_PATH = REPO_ROOT / "docs" / "d2a_rar" / "status" / "wp6_stage_b.md"
SEED_START = 110_000_000
N_REP = DEV_SUITE["seeds_per_cell"]
LABEL_CAP = DEV_SUITE["workload"]["label_cap"]
TIMEOUT_S = DEV_SUITE["timeout_s_per_experiment"]
TARGET_ROLES = ("adverse_sampling_stress", "alternative")
CONTROL_ROLES = ("neighbouring_negative_control", "correct_null")
SIMPLE_CONTROLS = ("uniform_query", "pending_cap", "fixed_schedule")
VALIDITY_NULLS = ("cond", "marg", "absolute_risk")
FP_TOL = (
    0.10  # screen-level tolerance on the observed validity-violation rate (n=20-40 paired seeds)
)
REL_SMALL, REL_MEANINGFUL, REL_SUBSTANTIAL = 0.01, 0.03, 0.10
GUARD_ERRORS = (LeakError, AuditViolation, BudgetExceeded, ActionNotAllowed)


# ------------------------------------------------------------------------------------------ comparators
def _host_d2a(env):
    return Drift2ActContractPolicy()


COMPARATORS = {
    "host_d2a": (_host_d2a, "abs_risk"),
    "host_rar": (lambda env: RARPolicy(), "none"),
    "host_cab": (lambda env: BinaryPolicy(cost_aware=True), "none"),
    "uniform_query": (lambda env: CONTROLS["uniform_query"].build(env), "none"),
    "pending_cap": (lambda env: CONTROLS["pending_cap"].build(env), "none"),
    "fixed_schedule": (lambda env: CONTROLS["fixed_schedule"].build(env), "none"),
    "asi": (lambda env: ASIAdapter.build(env), "cond"),
    "gong_zhang": (lambda env: GongZhangAdapter.build(env), "none"),
}
for _n in (
    "episode_front",
    "pave_full",
    "markov_lr_gate",
    "thinned_hedged_gate",
    "rmm_detector",
    "dss",
    "page_cusum_default",
    "erb",
):
    COMPARATORS[_n] = (lambda env, _n=_n: ADAPTERS[_n].build(env), ADAPTERS[_n].claimed_null)

# required-baseline id -> comparator (APPROX = documented non-identical stand-in; recorded in the ledger)
BASELINE_IMPL = {
    "uniform_query": "uniform_query",
    "pending_cap": "pending_cap",
    "fixed_schedule": "fixed_schedule",
    "front_loaded": "episode_front",
    "drift2act_native_audit": "host_d2a",
    "drift2act_unmodified": "host_d2a",
    "drift2act_gate": "host_d2a",
    "asi_inspired": "asi",
    "gong_zhang_paid_obs": "gong_zhang",
    "gongzhang_adapted": "gong_zhang",
    "pave": "pave_full",
    "markov_lr": "markov_lr_gate",
    "markov_lr_plugin": "markov_lr_gate",
    "fixed_spacing": "thinned_hedged_gate",
    "restart_without_gaps": "rmm_detector",
    "conditional_null_certifier": "dss",
    "page_cusum": "page_cusum_default",
    "page_cusum_post_switch": "page_cusum_default",
    "e_rb": "erb",
    "rar_unmodified": "host_rar",
    "rar_cost_aware_binary": "host_cab",
}
APPROX = {
    "drift2act_native_audit": "Drift2Act port default (windowed uniform audit) stands in for the native audit",
    "drift2act_gate": "Drift2Act port default; no separate post-switch gate",
    "restart_without_gaps": "rmm_detector (PARTIAL port: detector+pacer only)",
    "conditional_null_certifier": "dss (started-mixture cond-null e-process) stands in for the generic conditional-null certifier",
    "fixed_spacing": "thinned_hedged_gate (gap-10 thinning)",
    "page_cusum_post_switch": "page_cusum_default (existing_cusum)",
}
HOST_COMPARATOR = {
    "d2a": "host_d2a",
    "rar": "host_rar",
    "cab": "host_cab",
    "naive": "fixed_schedule",
}
HOST_COMPARATOR_NULL = {"d2a": "abs_risk", "rar": "none", "cab": "none", "naive": "none"}


def code_hash() -> str:
    h = hashlib.sha256()
    roots = [
        REPO_ROOT / "src/shiftlab/bench/contract",
        REPO_ROOT / "src/shiftlab/sota/drift2act",
        REPO_ROOT / "src/shiftlab/sota/rar",
        REPO_ROOT / "src/shiftlab/sota/inrepo",
        REPO_ROOT / "src/shiftlab/sota/asi",
        REPO_ROOT / "src/shiftlab/dive",
    ]
    files = [p for r in roots for p in sorted(r.rglob("*.py"))]
    files.append(REPO_ROOT / "src/shiftlab/autoresearch/stage_b_variants.py")
    for p in files:
        h.update(p.name.encode())
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


_CODE_HASH: str | None = None


def _code_hash() -> str:
    global _CODE_HASH
    if _CODE_HASH is None:
        _CODE_HASH = code_hash()
    return _CODE_HASH


# ------------------------------------------------------------------------------------------ cells / env
def suite_cells(question: str) -> list[dict]:
    return DEV_SUITE["cells"]["Q1" if question == "Q1" else "Q2"]


def cell_seeds(index: int) -> list[int]:
    return [SEED_START + index * 1000 + r for r in range(N_REP)]


def effective_cost_vector(cell: dict, kind: str) -> str:
    ov = DEV_SUITE["host_cost_vector_override"]
    return ov.get({"rar": "rar", "cab": "cost_aware_binary"}.get(kind, ""), cell["cost_vector"])


def make_env(spec, cv: str, clocks: str) -> EnvSpec:
    return EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()[cv],
        budget=BudgetSpec(label_cap=LABEL_CAP),
        clocks=make_clocks(clocks),
    )


# ------------------------------------------------------------------------------------------ per-run summaries
def _abs_violation(res, stream, pol) -> bool | None:
    log = getattr(pol, "log", None)
    if not log or not isinstance(log[0], dict) or "gate_ok" not in log[0]:
        return None
    tr, T = stream.truth, stream.T
    cums = {
        0: np.concatenate([[0.0], np.cumsum(tr.risk_inc)]),
        1: np.concatenate([[0.0], np.cumsum(tr.risk_cand)]),
    }
    N = getattr(pol, "N", 1024)
    for e in log:
        if not e["gate_ok"]:
            continue
        t = e["t"]
        m = int(res.served_path[t - 1])
        if m not in cums:
            continue
        lo = max(1, t - N + 1)
        risk = (cums[m][t] - cums[m][lo - 1]) / (t - lo + 1)
        if risk > tr.tau + 1e-12 and t <= T:
            return True
    return False


def summarise(res, stream, pol) -> dict:
    mp = res.model_path
    promoted = bool((mp == CANDIDATE).any())
    regime = stream.truth.regime
    onset = int(np.argmax(regime == 1)) + 1 if bool((regime == 1).any()) else None
    return {
        "seed": res.seed,
        "fingerprint": res.stream_fingerprint,
        "J": float(res.J),
        "breakdown": {k: float(v) for k, v in res.breakdown.items()},
        "counts": {k: int(v) for k, v in res.counts.items()},
        "promoted": promoted,
        "t_promo": int(np.argmax(mp == CANDIDATE)) + 1 if promoted else None,
        "retrain_deployed": bool((mp == 2).any()),
        "rolled_back": res.counts.get("N_b", 0) > 0,
        "abs_violation": _abs_violation(res, stream, pol),
        "onset": onset,
    }


def run_method(mk_policy, spec, env: EnvSpec, seeds: list[int], name: str = "m") -> list[dict]:
    """Paired run of one policy factory on ``seeds`` (verify_run inside run_paired; on_violation='raise')."""
    held: list = []

    def fac():
        p = mk_policy(env)
        held.append(p)
        return p

    pr = run_paired({name: fac}, spec, env, seeds, on_violation="raise", verify=True)
    return [
        summarise(r, make_stream(spec, r.seed), p) for r, p in zip(pr.runs[name], held, strict=True)
    ]


def _write_json_atomic(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def cached_reference(
    comp: str, cell_index: int, cell: dict, cv: str, clocks: str, cache_dir: Path
) -> list[dict]:
    spec = load_family(cell["family"])
    seeds = cell_seeds(cell_index)
    key = hashlib.sha256(
        json.dumps(
            [
                comp,
                cell["family"],
                cv,
                clocks,
                seeds[0],
                len(seeds),
                spec.T,
                LABEL_CAP,
                _code_hash(),
            ]
        ).encode()
    ).hexdigest()[:20]
    path = cache_dir / f"{comp}__{cell['family']}__{cv}__{clocks}__{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["runs"]
    env = make_env(spec, cv, clocks)
    t0 = time.time()
    runs = run_method(COMPARATORS[comp][0], spec, env, seeds, comp)
    _write_json_atomic(
        path,
        {
            "comp": comp,
            "cell": cell["family"],
            "cv": cv,
            "clocks": clocks,
            "runtime_s": time.time() - t0,
            "runs": runs,
        },
    )
    return runs


def cached_host(impl: Impl, cell_index: int, cell: dict, cv: str, cache_dir: Path) -> list[dict]:
    """Unmodified host with the candidate's non-hook host kwargs (e.g. audit_every) = the mechanistic ablation."""
    if not impl.host_kwargs:
        return cached_reference(
            HOST_COMPARATOR[impl.kind], cell_index, cell, cv, impl.clocks, cache_dir
        )
    spec = load_family(cell["family"])
    seeds = cell_seeds(cell_index)
    tag = hashlib.sha256(json.dumps(impl.host_kwargs, sort_keys=True).encode()).hexdigest()[:8]
    key = hashlib.sha256(
        json.dumps(
            [tag, cell["family"], cv, impl.clocks, seeds[0], len(seeds), spec.T, _code_hash()]
        ).encode()
    ).hexdigest()[:20]
    path = cache_dir / f"host_{impl.kind}_{tag}__{cell['family']}__{cv}__{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["runs"]
    env = make_env(spec, cv, impl.clocks)
    runs = run_method(lambda e: host_policy(impl.kind, impl.host_kwargs), spec, env, seeds, "host")
    _write_json_atomic(path, {"runs": runs})
    return runs


# ------------------------------------------------------------------------------------------ statistics
def cp_upper(k: int, n: int, level: float = 0.95) -> float:
    if n == 0:
        return float("nan")
    if k >= n:
        return 1.0
    try:
        from scipy.stats import beta

        return float(beta.ppf(level, k + 1, n - k))
    except ImportError:  # pragma: no cover
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            tail = sum(math.comb(n, i) * mid**i * (1 - mid) ** (n - i) for i in range(k + 1))
            lo, hi = (mid, hi) if tail > 1 - level else (lo, mid)
        return hi


def _a(runs, key="J") -> np.ndarray:
    return np.array([r[key] if key in r else r["breakdown"][key] for r in runs], float)


def _ci(diff: np.ndarray) -> tuple[float, float, float]:
    return paired_bootstrap_ci(diff, n_boot=2000, rng_seed=0)


def _rate(runs, key) -> float:
    return float(np.mean([bool(r[key]) for r in runs])) if runs else 0.0


def effect_label(rel: float, ci_hi: float) -> str:
    if ci_hi >= 0 or rel < REL_SMALL:
        return "none"
    if rel >= REL_SUBSTANTIAL:
        return "substantial"
    if rel >= REL_MEANINGFUL:
        return "meaningful"
    return "small"


def validity_of(cells: list[dict], method: str, null: str, rollback_family: bool) -> dict:
    """Validity under the claimed null ONLY (never a cond method on a marg-null rate)."""
    if null in ("cond", "marg"):
        vc = [c for c in cells if c["null_expected"][null]]
        runs = [r for c in vc for r in c["runs"][method]]
        if rollback_family:
            prom = [r for r in runs if r["promoted"]]
            k, n = sum(r["rolled_back"] for r in prom), len(prom)
            metric = "false_rollback_rate_given_promotion_under_keep_null"
        else:
            k, n = sum(r["promoted"] for r in runs), len(runs)
            metric = "false_promotion_rate"
    elif null == "absolute_risk":
        vc = list(cells)
        runs = [r for c in vc for r in c["runs"][method]]
        have = [r for r in runs if r.get("abs_violation") is not None]
        if have:
            k, n, metric = (
                sum(r["abs_violation"] for r in have),
                len(have),
                "abs_risk_certificate_violation_rate",
            )
        else:
            k, n, metric = (
                sum(r["promoted"] for r in runs),
                len(runs),
                "promotion_rate(no_certificate_log)",
            )
    else:
        return {"claimed": False, "null": null}
    return {
        "claimed": True,
        "null": null,
        "metric": metric,
        "validity_cells": [f"{c['role']}:{c['family']}" for c in vc],
        "k": int(k),
        "n": int(n),
        "rate": (k / n) if n else 0.0,
        "cp95_upper": cp_upper(int(k), int(n)),
        "screen_level": True,
    }


def analyse(
    cells: list[dict],
    *,
    cand_null: str,
    comp_meta: dict[str, dict],
    cx: int,
    absent_family: str | None = None,
    rollback_family: bool = False,
    candidate_key: str = "cand",
    host_key: str = "host",
) -> dict:
    """Pure KEEP/DISCARD/UNVERIFIED logic over per-cell per-method per-seed summaries (testable on synthetic data).

    ``cells`` items: {role, family, cost_vector, null_expected, runs: {method: [summary...]}}; ``comp_meta`` maps each
    comparator method key to {claimed_null, is_control, baseline_ids}. The host key is always an eligible comparator.
    """
    claim = cand_null in VALIDITY_NULLS
    target = [c for c in cells if c["role"] in TARGET_ROLES]
    controls = [c for c in cells if c["role"] in CONTROL_ROLES]
    nullcells = [c for c in cells if c["null_expected"]["cond"] and c["null_expected"]["marg"]]
    cval = validity_of(cells, candidate_key, cand_null, rollback_family)
    hval = validity_of(cells, host_key, cand_null, rollback_family)
    valid_ok = True
    if cval["claimed"]:
        valid_ok = cval["rate"] <= FP_TOL or cval["rate"] <= hval["rate"] + 1e-12

    def pj(method, cs):
        return float(np.mean([np.mean(_a(c["runs"][method])) for c in cs])) if cs else float("nan")

    def fp(method):
        runs = [r for c in nullcells for r in c["runs"][method]]
        return _rate(runs, "promoted")

    elig, excluded = [], []
    for m in comp_meta:
        if m not in cells[0]["runs"]:
            continue
        ok = (not claim) or m == host_key or fp(m) <= FP_TOL
        (elig if ok else excluded).append(m)
    pool = [host_key, *[m for m in elig if m != host_key]]
    strongest = min(pool, key=lambda m: pj(m, target))

    def per_cell(c, comp):
        d = _a(c["runs"][candidate_key]) - _a(c["runs"][comp])
        mean, lo, hi = _ci(d)
        ref = float(np.mean(_a(c["runs"][comp])))
        return {
            "family": c["family"],
            "role": c["role"],
            "dJ_mean": mean,
            "dJ_ci95": [lo, hi],
            "J_comp": ref,
            "rel_improvement": -mean / ref if ref else 0.0,
        }

    vs_host = [per_cell(c, host_key) for c in cells]
    vs_strong = [per_cell(c, strongest) for c in cells]
    tgt = [x for x in vs_strong if x["role"] in TARGET_ROLES]
    best = max(tgt, key=lambda x: x["rel_improvement"]) if tgt else None
    label = effect_label(best["rel_improvement"], best["dJ_ci95"][1]) if best else "none"
    host_tgt = [x for x in vs_host if x["role"] in TARGET_ROLES]
    bh = max(host_tgt, key=lambda x: x["rel_improvement"]) if host_tgt else None
    label_vs_host = effect_label(bh["rel_improvement"], bh["dJ_ci95"][1]) if bh else "none"

    def spend(method, c):
        return float(np.mean(_a(c["runs"][method], "cost_N_q"))) if c["runs"][method] else 0.0

    ctl_ok, ctl_notes = True, []
    for c in controls:
        x = per_cell(c, strongest)
        worse = x["dJ_mean"] > REL_SMALL * x["J_comp"]
        extra_prom = (
            _rate(c["runs"][candidate_key], "promoted") - _rate(c["runs"][host_key], "promoted")
            > FP_TOL
        )
        extra_spend = spend(candidate_key, c) > 1.10 * spend(host_key, c) + 0.5
        if worse or extra_prom or extra_spend:
            ctl_ok = False
            ctl_notes.append(
                {
                    "cell": f"{c['role']}:{c['family']}",
                    "worse_J": bool(worse),
                    "extra_promotion": bool(extra_prom),
                    "extra_spend": bool(extra_spend),
                }
            )

    applicable_ctrl = [m for m in elig if comp_meta[m].get("is_control")]
    beats_ctrl = True
    if applicable_ctrl and tgt:
        beats_ctrl = any(
            pj(candidate_key, [c]) < min(pj(m, [c]) for m in applicable_ctrl) for c in target
        )
    invalid_aggr = None
    if not claim and nullcells:
        sc = fp(candidate_key) - fp(strongest)
        meta = comp_meta.get(strongest, {})
        if sc > FP_TOL and meta.get("claimed_null") in (
            "cond",
            "marg",
            "abs_risk",
            "absolute_risk",
        ):
            invalid_aggr = f"promotes {sc:+.2f} more on null cells than valid-claiming {strongest}"

    reasons = []
    if not valid_ok:
        reasons.append(
            f"validity: {cval['metric']} {cval['rate']:.3f} > tolerance {FP_TOL} and > host {hval['rate']:.3f}"
        )
    if invalid_aggr:
        reasons.append("invalid-aggressive: " + invalid_aggr)
    if label == "none":
        reasons.append("no effect vs strongest applicable comparator (label none)")
    elif label == "small" and cx > 2:
        reasons.append("small effect with complexity > 2")
    if label_vs_host == "none" and label != "none":
        reasons.append("no gain vs unmodified host (mechanism ablation does not isolate a gain)")
    if not ctl_ok:
        reasons.append("worse/overspend on neighbouring or negative-control cell")
    if not beats_ctrl:
        reasons.append(
            "NEGATIVE: does not beat the pending-cap/uniform/fixed-schedule controls on any target cell (Mandate Q2: stop that line, do not tune)"
        )
    would_keep = not reasons
    n_impl_baselines = len(
        [
            m
            for m in comp_meta
            if m in cells[0]["runs"] and m != host_key and not comp_meta[m].get("is_host")
        ]
    )
    if absent_family:
        decision = "UNVERIFIED"
        why = f"needs dev-suite family absent from the frozen suite: {absent_family}; would-be decision on proxy cells: {'KEEP' if would_keep else 'DISCARD'}"
    elif n_impl_baselines == 0:
        decision, why = "UNVERIFIED", "no implemented required baseline besides the unmodified host"
    elif would_keep:
        decision, why = (
            "KEEP",
            "valid under claimed null; better than strongest applicable comparator on a target cell; controls not worse",
        )
    else:
        decision, why = "DISCARD", "; ".join(reasons)

    worst = max(vs_strong, key=lambda x: x["dJ_mean"] / x["J_comp"] if x["J_comp"] else 0.0)
    counterexamples = [
        {"worst_cell_vs_strongest": worst},
        *[{"control_cell_regression": n} for n in ctl_notes],
        *[{"cell_worse_than_host_CI_excludes_0": x} for x in vs_host if x["dJ_ci95"][0] > 0],
    ]
    if cval["claimed"] and not valid_ok:
        counterexamples.append({"validity_failure": cval})
    return {
        "decision": decision,
        "why": why,
        "would_keep": would_keep,
        "discard_reasons": reasons,
        "validity": {"candidate": cval, "host": hval},
        "strongest_comparator": strongest,
        "excluded_comparators_invalid_aggressive": excluded,
        "eligible_comparators": elig,
        "effect_vs_strongest": {"label": label, "best_target_cell": best},
        "effect_vs_host": {"label": label_vs_host, "best_target_cell": bh},
        "dJ_vs_host": vs_host,
        "dJ_vs_strongest": vs_strong,
        "dJ_vs_each_comparator": {
            m: [per_cell(c, m) for c in cells] for m in comp_meta if m in cells[0]["runs"]
        },
        "controls_ok": ctl_ok,
        "beats_simple_controls": beats_ctrl,
        "counterexamples": counterexamples,
    }


def power_delay(cells: list[dict], method: str) -> dict:
    out = {}
    for c in cells:
        runs = c["runs"][method]
        prom = [r for r in runs if r["promoted"]]
        delays = [
            r["t_promo"] - r["onset"]
            for r in prom
            if r["onset"] is not None and r["t_promo"] is not None
        ]
        out[f"{c['role']}:{c['family']}"] = {
            "promotion_rate": _rate(runs, "promoted"),
            "retrain_deployed_rate": _rate(runs, "retrain_deployed"),
            "mean_delay_after_onset": float(np.mean(delays)) if delays else None,
            "n_seeds": len(runs),
        }
    return out


def components(cells: list[dict], method: str) -> dict:
    out = {}
    for c in cells:
        runs = c["runs"][method]
        keys = ["loss", "cost_N_q", "cost_N_s", "cost_N_r", "cost_N_b", "cost_N_a", "cost_N_h", "J"]
        d = {k: float(np.mean(_a(runs, k))) for k in keys}
        d["labels_used_N_q"] = float(np.mean([r["counts"]["N_q"] for r in runs]))
        out[f"{c['role']}:{c['family']}"] = d
    return out


# ------------------------------------------------------------------------------------------ experiment
@dataclass
class Skipped:
    candidate_id: str
    status: str
    reason: str


def behaviour_sha(cells: list[dict], key: str) -> str:
    blob = [
        [
            c["family"],
            [round(r["J"], 6) for r in c["runs"][key]],
            [r["counts"] for r in c["runs"][key]],
        ]
        for c in cells
    ]
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


def preregistration(
    cand: dict, impl: Impl, cells_meta: list[dict], strongest: str, target_cells: list[str]
) -> dict:
    return {
        "registered_before_candidate_runs": True,
        "primary_metric": "J (loss + c_q N_q + c_s N_s + c_r N_r + c_b N_b + c_a N_a + c_h N_h), paired dJ vs strongest applicable comparator and vs unmodified host",
        "region": cand["predicted_win_region"],
        "target_cells": target_cells,
        "null": cand["target_null"],
        "validity_metric": "own null only (cond/marg: false promotion [false rollback for rollback mechanisms]; absolute_risk: certificate violation rate; economic/none: no validity claim, descriptive FP only)",
        "strongest_comparator_at_registration": strongest,
        "expected_sign": "dJ < 0 (candidate lower J) on target cells; no extra promotion/spend on neighbouring control",
        "expected_size_category": "small",
        "failure_region": cand["predicted_failure_region"],
        "hypothesis": cand["scientific_hypothesis"],
        "implementation_notes": impl.notes,
        "constants": "fixed a priori in stage_b_variants.py; none tuned on dev streams",
        "registered_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def run_experiment(cand: dict, impl: Impl, cache_dir: Path = STAGE_DIR / "cache") -> dict:
    """Run one screened candidate end to end (called inside the worker). Returns a ledger-ready record."""
    t0 = time.time()
    q = cand["research_question"]
    cells_def = suite_cells(q)
    kind = impl.kind
    comp_names = {}
    for b in cand["required_baselines"]:
        if b in BASELINE_IMPL:
            comp_names.setdefault(BASELINE_IMPL[b], []).append(b)
    missing = sorted(b for b in cand["required_baselines"] if b not in BASELINE_IMPL)
    host_key = "host"
    # ---- references first (so the strongest comparator is registered before the candidate runs)
    cells: list[dict] = []
    for i, cd in enumerate(cells_def):
        cv = effective_cost_vector(cd, kind)
        runs = {host_key: cached_host(impl, i, cd, cv, cache_dir)}
        for comp in comp_names:
            if comp == HOST_COMPARATOR[kind] and not impl.host_kwargs:
                continue
            runs[comp] = cached_reference(comp, i, cd, cv, impl.clocks, cache_dir)
        cells.append(
            {
                "role": cd["role"],
                "family": cd["family"],
                "cost_vector": cv,
                "null_expected": cd["null_truth_expected"],
                "runs": runs,
            }
        )
    comp_meta = {
        m: {
            "claimed_null": COMPARATORS[m][1],
            "is_control": m in SIMPLE_CONTROLS,
            "baseline_ids": comp_names[m],
        }
        for m in comp_names
        if not (m == HOST_COMPARATOR[kind] and not impl.host_kwargs)
    }
    hostname = HOST_COMPARATOR[kind]
    if hostname in comp_names:  # the unmodified host is also a required baseline (same runs)
        for c in cells:
            c["runs"][hostname] = c["runs"][host_key]
        comp_meta[hostname] = {
            "claimed_null": HOST_COMPARATOR_NULL[kind],
            "is_control": hostname in SIMPLE_CONTROLS,
            "is_host": True,
            "baseline_ids": comp_names[hostname],
        }
    # pre-registration with the strongest comparator chosen from references only
    pre_cells = [dict(c, runs={**c["runs"], "cand": c["runs"][host_key]}) for c in cells]
    pre = analyse(
        pre_cells,
        cand_null=cand["target_null"],
        comp_meta=comp_meta,
        cx=cand["complexity"]["level"],
    )
    target_cells = [f"{c['role']}:{c['family']}" for c in cells if c["role"] in TARGET_ROLES]
    prereg = preregistration(cand, impl, cells_def, pre["strongest_comparator"], target_cells)
    prereg_sha = hashlib.sha256(json.dumps(prereg, sort_keys=True).encode()).hexdigest()
    # ---- candidate runs
    for i, (cd, c) in enumerate(zip(cells_def, cells, strict=True)):
        spec = load_family(cd["family"])
        env = make_env(spec, c["cost_vector"], impl.clocks)
        c["runs"]["cand"] = run_method(impl.build_cand, spec, env, cell_seeds(i), "cand")
    for c in cells:  # pairing check across separately run methods
        fps = {tuple(r["fingerprint"] for r in runs) for runs in c["runs"].values()}
        if len(fps) != 1:
            raise AuditViolation(f"unpaired runs in cell {c['family']}")
    res = analyse(
        cells,
        cand_null=cand["target_null"],
        comp_meta=comp_meta,
        cx=cand["complexity"]["level"],
        absent_family=impl.absent_family,
        rollback_family=impl.rollback_family,
        candidate_key="cand",
        host_key=host_key,
    )
    strongest = res["strongest_comparator"]
    show = ["cand", host_key] + ([strongest] if strongest not in (host_key, "cand") else [])
    ablation = {
        "hook_restored_to_host_default": "identical to the unmodified host reference (host runs are the ablation)"
    }
    pd = {m: power_delay(cells, m) for m in show}
    seeds_all = [s for i in range(len(cells_def)) for s in cell_seeds(i)]
    fam_files = [
        REPO_ROOT / "configs/d2a_rar/stream_families.yaml",
        REPO_ROOT / "configs/d2a_rar/cost_vectors.yaml",
    ]
    pf = preflight(cand, stage="B")
    runtime = time.time() - t0
    record = {
        "candidate_id": cand["candidate_id"],
        "run_id": f"B-{cand['candidate_id']}-{prereg_sha[:8]}",
        "stage": "B",
        "git_commit": lg.current_git_commit(),
        "method": f"{cand['family']}.{cand['variant']}@{cand['host']}[{cand['hook']}]",
        "host": cand["host"],
        "fidelity_tier": "COMMON_CONTRACT_PORT"
        if cand["host"] == "contract_native"
        else "PAPER_RECONSTRUCTION",
        "data_hashes": {
            "dev_suite_sha256": suite_sha256(),
            "config_sha256": pf.hashes.get("config_sha256"),
            "hook_module_sha256": pf.hashes.get("hook_module_sha256"),
            "adapter_module_sha256": pf.hashes.get("adapter_module_sha256"),
            "stage_b_variants_sha256": hashlib.sha256(
                Path(__file__).with_name("stage_b_variants.py").read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
            "code_hash16": _code_hash(),
            "config_files": {
                p.name: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                for p in fam_files
            },
        },
        "seed_group": {
            "block": "d2a_rar_dev",
            "seed_start": min(seeds_all),
            "seed_end": max(seeds_all),
            "exposure": "dev",
            "replicates_per_cell": N_REP,
            "cell_indices": list(range(len(cells_def))),
        },
        "hardware": lg.hardware_info(),
        "runtime_s": round(runtime, 3),
        "null_class": cand["target_null"],
        "assumptions": cand["assumptions"],
        "preregistered_predictions": {**prereg, "sha256": prereg_sha},
        "results": {
            "workload": {
                "T": 1000,
                "label_cap": LABEL_CAP,
                "retrain_duration": 20,
                "clocks": impl.clocks,
                "pairing": "run_paired",
                "verify_run": "every run",
            },
            "components_per_cell": {m: components(cells, m) for m in show},
            "power_delay_per_cell": pd,
            "validity": res["validity"],
            "effect_vs_host": res["effect_vs_host"],
            "effect_vs_strongest": res["effect_vs_strongest"],
            "strongest_comparator": strongest,
            "excluded_comparators_invalid_aggressive": res[
                "excluded_comparators_invalid_aggressive"
            ],
            "controls_ok": res["controls_ok"],
            "beats_simple_controls": res["beats_simple_controls"],
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
            "unmodified_host": host_key,
            "mechanistic_ablation": ablation,
            "dJ_vs_each_implemented_required_baseline": res["dJ_vs_each_comparator"],
            "comparator_mapping": {
                m: {
                    "baseline_ids": comp_meta[m]["baseline_ids"],
                    "note": [APPROX[b] for b in comp_meta[m]["baseline_ids"] if b in APPROX],
                }
                for m in comp_meta
            },
        },
        "baselines_missing": missing,
        "counterexamples": res["counterexamples"],
        "prior_art_status": cand["prior_art_status"],
        "decision": res["decision"],
        "behaviour_sha256": behaviour_sha(cells, "cand"),
        "family_caveat": impl.absent_family,
        "role": cand["role"],
        "effect_label_vs_strongest": res["effect_vs_strongest"]["label"],
    }
    if res["decision"] == "UNVERIFIED":
        record["unverified_reason"] = res["why"]
    return record


# ------------------------------------------------------------------------------------------ worker / orchestration
def _crash_record(cand: dict, error: str, runtime: float, decision: str = "CRASH", **extra) -> dict:
    rid = hashlib.sha256(f"{cand['candidate_id']}|{error}|{time.time_ns()}".encode()).hexdigest()[
        :8
    ]
    return {
        "candidate_id": cand["candidate_id"],
        "run_id": f"B-{cand['candidate_id']}-{decision.lower()}-{rid}",
        "stage": "B",
        "git_commit": lg.current_git_commit(),
        "method": f"{cand.get('family')}.{cand.get('variant')}@{cand.get('host')}[{cand.get('hook')}]",
        "host": cand.get("host", "?"),
        "fidelity_tier": "COMMON_CONTRACT_PORT"
        if cand.get("host") == "contract_native"
        else "PAPER_RECONSTRUCTION",
        "data_hashes": {"dev_suite_sha256": suite_sha256(), "code_hash16": _code_hash()},
        "seed_group": {
            "block": "d2a_rar_dev",
            "seed_start": SEED_START,
            "seed_end": SEED_START + 3000 + N_REP - 1,
            "exposure": "dev",
        },
        "hardware": lg.hardware_info(),
        "runtime_s": round(runtime, 3),
        "null_class": cand.get("target_null", "?"),
        "assumptions": cand.get("assumptions", []),
        "preregistered_predictions": {},
        "results": {},
        "baseline_relative": {},
        "counterexamples": [],
        "prior_art_status": cand.get("prior_art_status", "UNVERIFIED"),
        "decision": decision,
        **({"error": error} if decision == "CRASH" else {}),
        **extra,
    }


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
    except GUARD_ERRORS as e:
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
    _write_json_atomic(Path(out_path), out)
    return 0


def worker_cmd(cand_path: Path, out_path: Path, cache_dir: Path | None = None) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "shiftlab.autoresearch.stage_b",
        "--worker",
        str(cand_path),
        str(out_path),
    ]
    return cmd + (["--cache-dir", str(cache_dir)] if cache_dir else [])


def triage(cand: dict, ledger_path=lg.LEDGER_PATH) -> tuple[str, dict | None]:
    """Preflight + implementation lookup WITHOUT running. Returns (action, payload):
    'run' | 'invalid' (ledger INVALID record) | 'blocked' (status only) | 'skip' (not implemented) | 'duplicate'."""
    v = preflight(cand, stage="B", ledger_path=ledger_path)
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
    cand: dict,
    work_dir: Path,
    *,
    timeout_s: float = TIMEOUT_S,
    cache_dir: Path | None = None,
    argv: list[str] | None = None,
    ledger_path=lg.LEDGER_PATH,
) -> tuple[str, dict]:
    """One experiment in a subprocess with a hard wall-clock timeout. Returns (action, record-or-status)."""
    action, payload = triage(cand, ledger_path)
    if action != "run":
        return action, payload or {}
    work_dir.mkdir(parents=True, exist_ok=True)
    cp, op = (
        work_dir / f"{cand['candidate_id']}.cand.json",
        work_dir / f"{cand['candidate_id']}.out.json",
    )
    cp.write_text(json.dumps(cand), encoding="utf-8")
    if op.exists():
        op.unlink()
    cmd = argv or worker_cmd(cp, op, cache_dir)
    t0 = time.time()
    try:
        subprocess.run(
            cmd, timeout=timeout_s, check=False, capture_output=True, text=True, cwd=REPO_ROOT
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
    """Single-writer ledger commit. A behaviourally identical earlier KEEP/DISCARD/UNVERIFIED record of ANOTHER candidate
    turns this one into DUPLICATE (same behavioural signature already decided)."""
    sig = record.get("behaviour_sha256")
    if sig and record["decision"] in ("KEEP", "DISCARD", "UNVERIFIED"):
        for r in lg.read_all(ledger_path):
            if (
                r.get("behaviour_sha256") == sig
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


def tier_key(c: dict) -> tuple:
    first = {
        "pending_aware_budgets", "deadline_aware_querying", "cost_aware_rar_gate",
        "canary_exposure_verification", "reversal_aware_rollback", "drift2act_certification_scheduling",
    }  # fmt: skip
    if c["role"] in ("novelty_candidate_unconfirmed", "narrow_residue_test"):
        t = 0 if c["family"] in first else 1
    elif c["role"] == "unverified_candidate":
        t = 1
    else:
        t = 2
    return (t, -c["priority_score"], c["candidate_id"])


def load_batch(path: Path | None = None) -> list[dict]:
    p = path or (g.REGISTRY_DIR / "stage_b_batch_001.jsonl")
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return sorted(rows, key=tier_key)


def write_status(path: Path, st: dict) -> None:
    done = st["done"]
    elapsed = time.time() - st["t0"]
    eta = (elapsed / done * (st["total"] - done)) if done else float("nan")
    lines = [
        "# WP6 Stage B status (auto-generated)",
        "",
        f"Updated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"Branch commit: {lg.current_git_commit()}",
        "",
        f"* experiments done: {done} / {st['total']} runnable identities (ledger records appended: {st['ledger_records']})",
        "* decisions: " + ", ".join(f"{k}={v}" for k, v in sorted(st["tally"].items())),
        f"* not run (no ledger record): {json.dumps(st['not_run'], sort_keys=True)}",
        f"* elapsed: {elapsed / 60:.1f} min; ETA: {eta / 60:.1f} min" if done else "* elapsed: n/a",
        f"* in flight: {', '.join(st['inflight']) or 'none'}",
        f"* last: {st.get('last', '')}",
        "",
        'Ledger: `docs/d2a_rar/registry/EXPERIMENT_LEDGER.jsonl` (verify: `python -c "from shiftlab.autoresearch import ledger; print(ledger.verify())"`).',
        "Log: `results/d2a_rar/stage_b/stage_b_run.log`; skipped/blocked: `results/d2a_rar/stage_b/not_run.jsonl`.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def warm_jobs(cands: list[dict]) -> list[tuple]:
    """Distinct (comparator, cell index, cell, cost vector, clocks) references the runnable candidates need."""
    jobs: dict[tuple, tuple] = {}
    for c in cands:
        impl, _ = resolve(c)
        cs = suite_cells(c["research_question"])
        names = {BASELINE_IMPL[b] for b in c["required_baselines"] if b in BASELINE_IMPL}
        names.add(HOST_COMPARATOR[impl.kind])
        for comp in names:
            for i, cd in enumerate(cs):
                cv = effective_cost_vector(cd, impl.kind)
                jobs[(comp, i, cd["family"], cv, impl.clocks)] = (comp, i, cd, cv, impl.clocks)
    return list(jobs.values())


def warm_main(comp: str, i: int, family: str, cv: str, clocks: str, q: str, cache_dir: str) -> int:
    cd = suite_cells(q)[i]
    assert cd["family"] == family
    cached_reference(comp, i, cd, cv, clocks, Path(cache_dir))
    return 0


def run_tranche(
    cands: list[dict],
    *,
    ledger_path=lg.LEDGER_PATH,
    work_dir: Path = STAGE_DIR / "work",
    status_path: Path = STATUS_PATH,
    max_workers: int = 4,
    limit: int | None = None,
    log=print,
    timeout_s: float = TIMEOUT_S,
) -> dict:
    """Triage, warm references, run candidates with <= max_workers concurrent subprocesses, commit in batch order."""
    from concurrent.futures import ThreadPoolExecutor

    work_dir.mkdir(parents=True, exist_ok=True)
    not_run_path = STAGE_DIR / "not_run.jsonl"
    already = {
        r["candidate_id"]
        for r in lg.read_all(ledger_path)
        if r.get("stage") == "B" and r.get("decision") != "CRASH"
    }
    todo, not_run = [], Counter()
    for c in cands:
        if c["candidate_id"] in already:
            not_run["already_in_ledger"] += 1
            continue
        action, payload = triage(c, ledger_path)
        if action == "run":
            todo.append(c)
        elif action == "invalid":
            todo.append(c)  # logged INVALID without running (handled in screen)
        else:
            not_run[payload["status"]] += 1
            with not_run_path.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps(
                        {
                            "candidate_id": c["candidate_id"],
                            "family": c["family"],
                            "variant": c["variant"],
                            "host": c["host"],
                            "hook": c["hook"],
                            **payload,
                        }
                    )
                    + "\n"
                )
    if limit:
        todo = todo[:limit]
    st = {
        "t0": time.time(),
        "total": len(todo),
        "done": 0,
        "tally": Counter(),
        "not_run": dict(not_run),
        "inflight": [],
        "ledger_records": len(lg.read_all(ledger_path)),
        "last": "",
    }
    write_status(status_path, st)
    runnable = [c for c in todo if triage(c, ledger_path)[0] == "run"]
    jobs = warm_jobs(runnable)
    log(f"warming {len(jobs)} reference runs ...")
    cache_dir = STAGE_DIR / "cache"

    def warm(job):
        comp, i, cd, cv, clocks = job
        q = next(q for q in ("Q2", "Q1") if cd in suite_cells(q))
        cmd = [
            sys.executable,
            "-m",
            "shiftlab.autoresearch.stage_b",
            "--warm",
            comp,
            str(i),
            cd["family"],
            cv,
            clocks,
            q,
            str(cache_dir),
        ]
        try:
            r = subprocess.run(
                cmd, timeout=900, capture_output=True, text=True, cwd=REPO_ROOT, check=False
            )
            if r.returncode:
                log(f"warm FAILED {job[0]} cell{job[1]}: {r.stderr[-300:]}")
        except subprocess.TimeoutExpired:
            log(f"warm TIMEOUT {job[0]} cell{job[1]}")

    with ThreadPoolExecutor(max_workers) as ex:
        list(ex.map(warm, jobs))
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
        for f in futs:  # ordered commit: record i is appended only after records < i
            idx, (action, rec) = f.result()
            results[idx] = (action, rec)
            while nxt in results:
                a, r = results.pop(nxt)
                c = todo[nxt]
                if a in ("ok", "crash", "invalid"):
                    committed = commit(r, ledger_path)
                    st["tally"][committed["decision"]] += 1
                    st["ledger_records"] += 1
                    st["last"] = (
                        f"{c['family']}.{c['variant']}@{c['host']} -> {committed['decision']} ({committed['runtime_s']}s)"
                    )
                else:
                    st["tally"][a.upper()] += 1
                    st["last"] = f"{c['family']}.{c['variant']} -> {a}"
                st["done"] += 1
                log(st["last"])
                write_status(status_path, st)
                nxt += 1
    return {"done": st["done"], "tally": dict(st["tally"]), "not_run": dict(not_run)}


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "--worker":
        cache = argv[4] if len(argv) >= 5 and argv[3] == "--cache-dir" else None
        return worker_main(argv[1], argv[2], cache)
    if len(argv) >= 8 and argv[0] == "--warm":
        return warm_main(argv[1], int(argv[2]), argv[3], argv[4], argv[5], argv[6], argv[7])
    print("use scripts/d2a_rar/run_stage_b.py", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
