"""Stage B under Amendment A2 (registered: docs/d2a_rar/AUTORESEARCH_PROGRAM.md section 3b; draft: drafts/A2_DRAFT.md).

Wiring only. A1 modules (``stage_b``, ``stage_b_v2``, ``stage_b_q1``) are imported, never edited.

* Seeds: ``110070000 + a2_index*1000 + replicate`` (20 replicates; 100 for the null audit). A2 index space: Q1 panel 0-15
  (the 16 scope-iii cells in ``stage_b_q1.q1_cells`` order), ``rar_persistent`` S5a-S5e 16-20, null-audit cells 21-24.
* Records: ``suite="a2"``, ``amendment="A2"``. They report BOTH control readings: the strict A1 reading (``stage_b.analyse``,
  unchanged) and the A2 reading (:func:`a2_control_reading`, a NEW function). The record decision is the A2 decision.
* CPU cap 300 s per experiment (process tree), at most 12 workers, reference runs cached (not experiments).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from shiftlab.bench.contract import BudgetSpec, EnvSpec, load_cost_vectors
from shiftlab.bench.contract.adapters_rar import BinaryPolicy
from shiftlab.bench.contract.audit import AuditViolation
from shiftlab.bench.contract.canary_a2 import (
    NO_ALERT_ACTIONS,
    PROFILE,
    CABHorizonPolicy,
    RARCanaryA2Policy,
    a2_clocks,
    rollback_only,
)
from shiftlab.bench.contract.evidence_q1_a2 import build_evidence_a2, promoter_adapter_a2
from shiftlab.bench.contract.streams import make_stream

from . import ledger as lg
from . import stage_b as sb
from . import stage_b_q1 as sq1
from . import stage_b_v2 as v2
from .preflight import preflight

SUITE, AMENDMENT = "a2", "A2"
SEED_START, N_REP, AUDIT_REP, CHUNK = 110_070_000, 20, 100, 2
MAX_WORKERS, CPU_CAP_S = 12, 300
REPO = sb.REPO_ROOT
FAMILIES_V3_PATH = REPO / "configs" / "d2a_rar" / "stream_families_v3.yaml"
SUITE_A2_PATH = REPO / "docs" / "d2a_rar" / "registry" / "DEV_SUITE_A2.json"
STAGE_DIR = sb.STAGE_DIR
CACHE_DIR = STAGE_DIR / "cache"
WORK_DIR = STAGE_DIR / "work_a2"
STATE_PATH = STAGE_DIR / "a2_state.json"
STATUS_PATH = REPO / "docs" / "d2a_rar" / "status" / "wp6_stage_b_a2.md"
RAR_INDEX0 = 16  # A2 cell index of S5a
AUDIT_CELLS = ("Q1_0", "Q1_3", "S3b", "S4b")
AUDIT_INDEX0 = 21

Q1_COMPARATORS = (
    sq1.Q1_COMPARATORS
)  # markov_lr_gate, thinned_hedged_gate, gapmix_exact08_s4, rmm_detector
Q1_SHELL_FAMILY = Q1_COMPARATORS  # action family of the promoter shell
RAR_CONTROLS = (
    "never_switch",
    "uniform_query",
    "fixed_schedule",
    "pending_cap",
    "episode_front",
    "thinned_hedged_gate",
    "gapmix_exact08_s4",
)
RAR_FAMILY_COMPS = ("host", "nocanary", "rollback_only", "binary", "cab", "cab_horizon")
RAR_COMPARATORS = (
    *RAR_FAMILY_COMPS[1:],
    *RAR_CONTROLS,
)  # + "host" as the unmodified RAR calibrated_v1
RAR_CELL_IDS = ("S5a", "S5b", "S5c", "S5d", "S5e")
K2_TARGET_CELLS = ("S5a", "S5c", "S5d")


# ------------------------------------------------------------------------------------------ files / suite
def sha_crlf(path: Path) -> str:
    """Digest of the CRLF-normalised bytes (A1 convention, identical on every checkout)."""
    b = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(b).hexdigest()


def load_family_v3(name: str):
    import yaml

    from shiftlab.bench.contract.streams import _spec_from_dict

    fams = yaml.safe_load(FAMILIES_V3_PATH.read_text(encoding="utf8"))["families"]
    return _spec_from_dict({"family": name, **fams[name]})


_RAR_CELLS = (
    # id, role, family, purpose
    (
        "S5a",
        "alternative",
        "rar_persist_alt",
        "drift where retraining pays (0.25/round); candidate model 1 is not better, so no free switch substitutes",
    ),
    (
        "S5b",
        "correct_null",
        "rar_persist_null",
        "no drift: retraining has zero benefit; gates/canary must not spend",
    ),
    (
        "S5c",
        "neighbouring_negative_control",
        "rar_persist_harm",
        "drift where retraining is harmful (retrained 0.45-0.70 vs incumbent 0.33); drop 0.08 < Delta_crit 0.10",
    ),
    (
        "S5d",
        "alternative",
        "rar_persist_alt_tau40",
        "S5a with fixed label delay 40 (label-frontier stress)",
    ),
    (
        "S5e",
        "stress_descriptive",
        "rar_persist_strong_bad",
        "visible drop 0.25 but retraining does not help (K2 failure probe); descriptive only",
    ),
)


def build_suite_a2() -> dict:
    cells = []
    for k, (cid, role, fam, purpose) in enumerate(_RAR_CELLS):
        spec = load_family_v3(fam)
        tr = make_stream(spec, SEED_START + (RAR_INDEX0 + k) * 1000).truth
        cells.append(
            {
                "id": cid,
                "index": RAR_INDEX0 + k,
                "role": role,
                "family": fam,
                "family_source": "v3",
                "cost_vector": "intervention_dear",
                "T": spec.T,
                "label_cap": spec.T,
                "max_lookback": 10,
                "retrain_duration": 20,
                "w_train": 100,
                "purpose": purpose,
                "null_truth_expected": {k2: bool(v) for k2, v in tr.null_holds.items()},
            }
        )
    return {
        "version": "a2",
        "amendment": "A2",
        "seed_block": "d2a_rar_dev (sub-block a2)",
        "seed_rule": f"seed = {SEED_START} + a2_index*1000 + replicate; Q1 panel idx 0-15, rar_persistent idx 16-20, null audit idx 21-24",
        "seeds_per_cell": N_REP,
        "families_file": "configs/d2a_rar/stream_families_v3.yaml",
        "clocks": "canary comparators/candidates: ClockSpec(deploy_on_complete=False, max_lookback=10, w_train=100, retrain_duration=20); nocanary/binary/CAB/simple controls: deploy_on_complete=True, same lookback",
        "obs_mode": "shadow",
        "null_truth_note": "null_truth_expected is the contract's statistical-null truth for the free CANDIDATE model (gain = l_inc - l_cand, hurdle 0.1); it is not a claim about retraining. All RAR-arm candidates/comparators claim null none/economic, so it is never used for a validity claim; roles are authoritative.",
        "cells": cells,
    }


def load_suite_a2() -> dict:
    return json.loads(SUITE_A2_PATH.read_text(encoding="utf-8"))


def write_registered_files() -> dict:
    SUITE_A2_PATH.write_text(
        json.dumps(build_suite_a2(), indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "families_v3_sha256_crlf": sha_crlf(FAMILIES_V3_PATH),
        "suite_a2_sha256_crlf": sha_crlf(SUITE_A2_PATH),
    }


# ------------------------------------------------------------------------------------------ cells / seeds / envs
def seeds_of(a2_index: int, n: int = N_REP) -> list[int]:
    return [SEED_START + a2_index * 1000 + r for r in range(n)]


def q1_panel() -> list[dict]:
    return [{**c, "a2_index": i, "arm": "q1"} for i, c in enumerate(sq1.q1_cells())]


def rar_panel() -> list[dict]:
    return [{**c, "a2_index": c["index"], "arm": "rar"} for c in load_suite_a2()["cells"]]


def audit_panel() -> list[dict]:
    by_id = {c["id"]: c for c in q1_panel()}
    return [{**by_id[cid], "a2_index": AUDIT_INDEX0 + k} for k, cid in enumerate(AUDIT_CELLS)]


def spec_env(cell: dict, clocks: str = "default", allowed: tuple | None = None):
    if cell["arm"] == "q1":
        return sq1._spec_env(cell)
    spec = load_family_v3(cell["family"])
    if spec.T != cell["T"]:
        raise ValueError(f"cell {cell['id']}: family T != suite T")
    kw = {"allowed_actions": allowed} if allowed else {}
    env = EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()[cell["cost_vector"]],
        budget=BudgetSpec(label_cap=cell["label_cap"]),
        clocks=a2_clocks(clocks, cell["retrain_duration"], cell["w_train"]),
        **kw,
    )
    return spec, env


# comparator registry for the RAR arm: name -> (factory(env), clocks kind, allowed actions, claimed null)
def _sbc(name: str):
    return sb.COMPARATORS[name][0]


RAR_METHODS: dict[str, tuple] = {
    "host": (lambda env: RARCanaryA2Policy("host"), "canary", None, "none"),
    "nocanary": (lambda env: RARCanaryA2Policy("nocanary"), "default", None, "none"),
    "rollback_only": (lambda env: rollback_only(), "canary", NO_ALERT_ACTIONS, "none"),
    "binary": (
        lambda env: BinaryPolicy(cost_aware=False, profile=PROFILE),
        "default",
        None,
        "none",
    ),
    "cab": (lambda env: BinaryPolicy(cost_aware=True, profile=PROFILE), "default", None, "none"),
    "cab_horizon": (lambda env: CABHorizonPolicy(), "default", None, "none"),
    **{n: (_sbc(n), "default", None, sb.COMPARATORS[n][1]) for n in RAR_CONTROLS},
    # candidates and ablations (never cached as references)
    "k2_skip": (lambda env: RARCanaryA2Policy("k2_skip"), "canary", None, "none"),
    "k1_p1": (lambda env: RARCanaryA2Policy("k1_p1"), "canary", None, "none"),
    "L_routed": (lambda env: RARCanaryA2Policy("L_routed"), "canary", None, "none"),
}


def _cache_key(*parts) -> str:
    return hashlib.sha256(json.dumps(list(parts)).encode()).hexdigest()[:20]


def run_ref(
    comp: str, cell: dict, cache_dir: Path = CACHE_DIR, chunk: int | None = None
) -> list[dict]:
    """Cached reference runs for one comparator on one cell with the A2 seeds (chunks of ``CHUNK`` seeds)."""
    if cell["arm"] == "q1":
        if cell["suite"] == "v1":
            factory = sb.COMPARATORS["host_d2a" if comp == "host" else comp][0]
        else:
            factory = v2.V2_COMPARATORS["host_d2a" if comp == "host" else comp][0]
        clocks, allowed = "default", None
    else:
        factory, clocks, allowed, _ = RAR_METHODS["host" if comp == "host" else comp]
    spec, env = spec_env(cell, clocks, allowed)
    seeds = seeds_of(cell["a2_index"])
    runs: list[dict] = []
    for k in [chunk] if chunk is not None else range(N_REP // CHUNK):
        key = _cache_key(
            SUITE,
            cell["arm"],
            comp,
            cell["id"],
            cell["family"],
            cell["cost_vector"],
            seeds[0],
            N_REP,
            spec.T,
            cell["label_cap"],
            sb._code_hash(),
            k,
            CHUNK,
        )
        path = cache_dir / f"a2__{comp}__{cell['id']}__c{k}__{key}.json"
        if path.exists():
            runs += json.loads(path.read_text(encoding="utf-8"))["runs"]
            continue
        t0 = time.time()
        part = sb.run_method(factory, spec, env, seeds[k * CHUNK : (k + 1) * CHUNK], comp)
        sb._write_json_atomic(
            path, {"comp": comp, "cell": cell["id"], "runtime_s": time.time() - t0, "runs": part}
        )
        runs += part
    return runs


# ------------------------------------------------------------------------------------------ the A2 control reading
def a2_control_reading(
    cells: list[dict],
    res: dict,
    *,
    cand_null: str,
    candidate_key: str = "cand",
    host_key: str = "host",
    spend_family: tuple[str, ...],
) -> dict:
    """NEW function (A2). The A1 reading (``stage_b.analyse`` -> ``controls_ok``) is NOT altered.

    For every neighbouring-negative-control / correct-null cell:
      (a) extra promotion counts only on cells where the candidate's claimed null holds in evaluator truth;
      (b) extra spend (N_q cost) is measured against the strongest applicable comparator of the same action family
          (``spend_family`` intersected with the eligible comparators), tolerance 1.10x + 0.5;
      (c) worse J requires the paired 95% CI of dJ vs the per-cell strongest comparator to lie entirely above 0.
    """
    claim = cand_null in sb.VALIDITY_NULLS
    nk = {"absolute_risk": "abs_risk"}.get(cand_null, cand_null)
    elig = set(res["eligible_comparators"]) | {host_key}
    strong = res["strongest_comparator_per_cell"]
    notes, ok = [], True
    for c in cells:
        if c["role"] not in sb.CONTROL_ROLES:
            continue
        s = strong[c["id"]]
        d = sb._a(c["runs"][candidate_key]) - sb._a(c["runs"][s])
        mean, lo, hi = sb._ci(d)
        worse = lo > 0.0
        holds = bool(claim and c["null_expected"].get(nk))
        extra_prom = bool(
            holds
            and sb._rate(c["runs"][candidate_key], "promoted")
            - sb._rate(c["runs"][host_key], "promoted")
            > sb.FP_TOL
        )
        fam = [m for m in spend_family if m in elig and m in c["runs"]]
        ref = min(fam, key=lambda m: float(np.mean(sb._a(c["runs"][m])))) if fam else host_key

        def sp(m, c=c):
            return float(np.mean(sb._a(c["runs"][m], "cost_N_q"))) if c["runs"][m] else 0.0

        extra_spend = sp(candidate_key) > 1.10 * sp(ref) + 0.5
        if worse or extra_prom or extra_spend:
            ok = False
            notes.append(
                {
                    "cell": sb.cell_label(c),
                    "worse_J_ci_excludes_0": bool(worse),
                    "dJ_vs_strongest": {"comparator": s, "mean": mean, "ci95": [lo, hi]},
                    "extra_promotion_on_claimed_null_cell": extra_prom,
                    "extra_spend_vs_same_family": extra_spend,
                    "spend_reference": ref,
                }
            )
    return {"controls_ok": ok, "notes": notes}


def a2_decision(res: dict, reading: dict, extra_reasons: list[str] | None = None) -> dict:
    """A2 decision = the A1 decision logic with the control reason replaced by the A2 control reading."""
    reasons = [r for r in res["discard_reasons"] if not r.startswith("worse/overspend")]
    if not reading["controls_ok"]:
        reasons.append(
            "A2 control reading: worse (CI excludes 0) / extra promotion on claimed-null cell / extra spend vs same-family comparator"
        )
    reasons.extend(extra_reasons or [])
    if res["decision"] == "UNVERIFIED":
        return {"decision": "UNVERIFIED", "reasons": [res["why"]]}
    return {"decision": "DISCARD" if reasons else "KEEP", "reasons": reasons}


def k2_extra_reasons(cells: list[dict], candidate_key: str = "cand") -> list[str]:
    """Registered K2 rule: beat BOTH RAR calibrated_v1 and NoCanary (CI excluding 0) on S5a/S5c/S5d; never significantly
    worse than either on S5b/S5c."""
    out = []
    by = {c["id"]: c for c in cells}
    for m in ("host", "nocanary"):
        wins = []
        for cid in K2_TARGET_CELLS:
            d = sb._a(by[cid]["runs"][candidate_key]) - sb._a(by[cid]["runs"][m])
            wins.append(sb._ci(d)[2] < 0.0)
        if not any(wins):
            out.append(f"does not beat {m} with paired CI excluding 0 on any of {K2_TARGET_CELLS}")
        for cid in ("S5b", "S5c"):
            d = sb._a(by[cid]["runs"][candidate_key]) - sb._a(by[cid]["runs"][m])
            if sb._ci(d)[1] > 0.0:
                out.append(f"significantly worse than {m} on {cid}")
    return out


# ------------------------------------------------------------------------------------------ candidates
@dataclass
class Impl:
    arm: str
    build_cand: object
    clocks: str = "default"
    allowed: tuple | None = None
    notes: str = ""


def _base_a2_identity(src: dict, **over) -> dict:
    c = deepcopy(src)
    c.update(over)
    c["a2_identity"] = True
    c["blocked_by"] = []
    return c


def r1_candidate() -> dict:
    src = {c["candidate_id"]: c for c in sb.load_batch()}["CAND-0c6c168c019f555d"]
    c = _base_a2_identity(
        src,
        candidate_id="CAND-A2-restart_min",
        variant="restart_min_certificate",
        parent_id=src["candidate_id"],
        role="a2_repaired_variant",
        scientific_hypothesis="min_of_both's S2d loss to rmm_detector is pre-onset dilution; a restart mixture with one shared summable start prior inside both components removes it while keeping validity under either null.",
        mechanism="log e = min(log sum_j w_j E_cond^(j), log sum_j w_j E_marg^(j)); starts at label index 4^j-1 < B, w_j ~ 1/((j+1)(j+2)).",
        predicted_win_region="dependent-chain alternatives with sparse gap labels (Q1_2) and persistent shifts (S2d, S1a)",
        predicted_failure_region="transient / reversal cells (S3a, S4a, S4c): promotion-only shell has no exit after the advantage expires (FL-043)",
        closest_prior_art=["shin2023_edetectors", "sethi2026", "gafni2026"],
        prior_art_status="HIGH_OVERLAP",
        complexity={"est_diff_loc": 50, "hook": "d2a.evidence_log_lik", "level": 2},
    )
    return c


def rar_candidate(
    variant: str, role: str, hypothesis: str, win: str, fail: str, level: int, art: list[str]
) -> dict:
    return {
        "a2_identity": True,
        "candidate_id": f"CAND-A2-{variant}",
        "family": "canary_exposure_verification",
        "variant": variant,
        "host": "rar",
        "hook": "rar.config",
        "research_question": "Q3",
        "target_null": "economic",
        "scoring_null": "economic",
        "role": role,
        "scientific_hypothesis": hypothesis,
        "predicted_win_region": win,
        "predicted_failure_region": fail,
        "assumptions": [
            "policy reads ObservableState only; canary evidence from labels of rounds served by the retrained model (routed) before commit",
            "RAR PAPER_RECONSTRUCTION; contract charges c_s for the commit switch (adapters_rar deviation (ii)); no statistical null is claimed",
        ],
        "configuration": {},
        "complexity": {"level": level, "hook": "rar.config", "est_diff_loc": 40},
        "closest_prior_art": art,
        "prior_art_status": "PLAUSIBLY_DISTINCT",
        "required_baselines": ["rar_unmodified", "rar_cost_aware_binary"],
        "blocked_by": [],
    }


def rar_candidates() -> dict[str, dict]:
    return {
        "k2_skip": rar_candidate(
            "critical_degradation_skip_stage1",
            "candidate",
            "When released-label degradation already exceeds RAR's own critical threshold (2 theta_R), waiting tau + W1/p1 rounds in Canary-1 costs more than the harm it can avert: skip Canary-1, switch and verify in stage 2.",
            "S5a, S5d (saves stage-1 latency); S5c keeps the full canary (drop 0.08 < 0.10)",
            "S5e: skips the canary on a retrain that does not help; pays c_b plus ~40 rounds of full exposure",
            2,
            ["rar2026", "cmas2026", "karampatziakis2021", "cara2023"],
        ),
        "k1_p1": rar_candidate(
            "fast_verification_full_traffic",
            "baseline_or_ablation_only",
            "At a fixed number of routed labelled observations the harm of a bad retrain is W1*h independent of p1, while latency is tau + W1/p1; p1<1 only buys delay in J-units (ablation of RAR, not a method).",
            "S5a, S5d",
            "exposure-risk metrics (peak exposed traffic share 1.0 vs 0.2)",
            1,
            ["rar2026", "lindon2022"],
        ),
        "L_routed": rar_candidate(
            "routed_only_stage_labels",
            "baseline_or_ablation_only",
            "Retrospective routed-only labelling during Canary-1 saves (1-p1) of the stage-1 label cost (< 1% of J); ablation bounding the claim and exercising ClockSpec.max_lookback.",
            "none expected (<1% of J)",
            "none",
            1,
            ["rar2026"],
        ),
    }


def q1_candidates() -> dict[str, dict]:
    by = {c["candidate_id"]: c for c in sb.load_batch()}
    return {
        "REP1": by["CAND-0c6c168c019f555d"],
        "REP2": by["CAND-554673b35895b8a4"],
        "REP3": by["CAND-535bb9e297b2660b"],
        "R1": r1_candidate(),
    }


def all_candidates() -> dict[str, dict]:
    return {**q1_candidates(), **rar_candidates()}


def a2_preflight(cand: dict, ledger_path=lg.LEDGER_PATH) -> dict:
    """Registry identities (REP1-3) use the real preflight with ``suite="a2"``; A2-only identities are not in the grammar
    (the registry is append-only, batch_002 is the coordinator's), so they get a reduced, explicitly labelled check."""
    if not cand.get("a2_identity"):
        v = preflight(cand, stage="B", ledger_path=ledger_path, suite=SUITE)
        return {
            "status": v.status,
            "ok": v.ok,
            "reasons": v.reasons,
            "hashes": v.hashes,
            "validity_plan": v.validity_plan,
            "comparator_nulls": v.comparator_nulls,
            "kind": "grammar_preflight",
        }
    prior = [
        r["run_id"]
        for r in lg.read_all(ledger_path)
        if r.get("candidate_id") == cand["candidate_id"]
        and r.get("suite") == SUITE
        and r.get("decision") != "CRASH"
    ]
    return {
        "status": "DUPLICATE" if prior else "ELIGIBLE",
        "ok": not prior,
        "reasons": [f"already decided: {prior}"] if prior else [],
        "hashes": {
            "candidate_spec_sha256": hashlib.sha256(
                json.dumps(cand, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "git_commit": lg.current_git_commit(),
        },
        "kind": "a2_identity_reduced_check (not in grammar; appended by amendment A2)",
    }


def resolve(key: str, cand: dict) -> Impl:
    if key in ("REP1", "REP2", "REP3", "R1"):
        ad = promoter_adapter_a2(cand, alpha=sq1.ALPHA, schedule=sq1.SCHEDULE)
        build_evidence_a2(cand)  # raises if not implemented
        return Impl(
            "q1",
            lambda env: ad.build(env),
            notes=f"contract-native evidence promoter shell ({sq1.SCHEDULE} schedule, alpha {sq1.ALPHA}); validity scored on the shell only",
        )
    f, clocks, allowed, _ = RAR_METHODS[key]
    return Impl(
        "rar", f, clocks, allowed, notes=f"RAR calibrated_v1 port, mode {key}, clocks {clocks}"
    )


# ------------------------------------------------------------------------------------------ experiment
def _panel_runs(arm: str, cells_def: list[dict], cache_dir: Path) -> list[dict]:
    comps = ("host", *(Q1_COMPARATORS if arm == "q1" else RAR_COMPARATORS))
    cells = []
    for cd in cells_def:
        cells.append(
            {
                "id": cd["id"],
                "role": cd["role"],
                "family": cd["family"],
                "cost_vector": cd["cost_vector"],
                "null_expected": cd["null_truth_expected"],
                "runs": {m: run_ref(m, cd, cache_dir) for m in comps},
            }
        )
    return cells


def _comp_meta(arm: str, required: list[str]) -> dict:
    if arm == "q1":
        names, ctl = Q1_COMPARATORS, sq1.Q1_CONTROLS
        null = {m: sb.COMPARATORS[m][1] for m in names}
    else:
        names, ctl = RAR_COMPARATORS, sb.SIMPLE_CONTROLS
        null = {m: RAR_METHODS[m][3] for m in names}
    return {
        m: {
            "claimed_null": null[m],
            "is_control": m in ctl,
            "baseline_ids": [b for b in required if sb.BASELINE_IMPL.get(b) == m],
        }
        for m in names
    }


def run_experiment(key: str, cand: dict, impl: Impl, cache_dir: Path = CACHE_DIR) -> dict:
    t0 = time.time()
    arm = impl.arm
    cells_def = q1_panel() if arm == "q1" else rar_panel()
    required = cand["required_baselines"]
    cells = _panel_runs(arm, cells_def, cache_dir)
    comp_meta = _comp_meta(arm, required)
    if arm == "rar":
        comp_meta["host"] = {
            "claimed_null": "none",
            "is_control": False,
            "is_host": True,
            "baseline_ids": ["rar_unmodified"],
        }
    kw = {
        "cand_null": cand["target_null"],
        "comp_meta": comp_meta,
        "cx": cand["complexity"]["level"],
        "suite": "v2",
    }
    pre = sb.analyse([dict(c, runs={**c["runs"], "cand": c["runs"]["host"]}) for c in cells], **kw)
    target_cells = [f"{c['id']}:{c['family']}" for c in cells if c["role"] in sb.TARGET_ROLES]
    prereg = {
        **sb.preregistration(cand, impl, cells_def, pre["strongest_comparator"], target_cells),
        "suite": SUITE,
        "amendment": AMENDMENT,
        "arm": arm,
        "candidate_key": key,
        "registered_in": "docs/d2a_rar/AUTORESEARCH_PROGRAM.md section 3b",
        "comparator_set": ["host", *comp_meta],
        "cells": [c["id"] for c in cells_def],
        "strongest_comparator_at_registration_per_cell": pre["strongest_comparator_per_cell"],
        "a2_control_reading": "extra promotion only on claimed-null cells; extra spend vs strongest same-family comparator; worse J needs paired CI > 0",
        "expected_size_category": "small",
    }
    prereg_sha = hashlib.sha256(json.dumps(prereg, sort_keys=True).encode()).hexdigest()
    for cd, c in zip(cells_def, cells, strict=True):
        spec, env = spec_env(cd, impl.clocks, impl.allowed)
        c["runs"]["cand"] = sb.run_method(
            impl.build_cand, spec, env, seeds_of(cd["a2_index"]), "cand"
        )
    for c in cells:
        if len({tuple(r["fingerprint"] for r in runs) for runs in c["runs"].values()}) != 1:
            raise AuditViolation(f"unpaired runs in cell {c['id']}")
    res = sb.analyse(cells, **kw, candidate_key="cand", host_key="host")
    family = Q1_SHELL_FAMILY if arm == "q1" else RAR_FAMILY_COMPS[1:]
    reading = a2_control_reading(cells, res, cand_null=cand["target_null"], spend_family=family)
    extra = k2_extra_reasons(cells) if key == "k2_skip" else []
    a2 = a2_decision(res, reading, extra)
    strongest = res["strongest_comparator"]
    show = [
        "cand",
        "host",
        *[m for m in dict.fromkeys(res["strongest_comparator_per_cell"].values()) if m != "host"],
    ]
    if arm == "rar":
        show = list(dict.fromkeys([*show, "nocanary"]))
    pf = a2_preflight(cand)
    seeds_all = [s for cd in cells_def for s in seeds_of(cd["a2_index"])]
    record = {
        "candidate_id": cand["candidate_id"],
        "run_id": f"A2{arm.upper()}-{cand['candidate_id']}-{prereg_sha[:8]}",
        "stage": "B",
        "suite": SUITE,
        "amendment": AMENDMENT,
        "arm": arm,
        "candidate_key": key,
        "git_commit": lg.current_git_commit(),
        "method": f"{cand['family']}.{cand['variant']}@{cand['host']}[{cand['hook']}]"
        + (" via evidence promoter shell" if arm == "q1" else ""),
        "host": cand["host"],
        "fidelity_tier": "PAPER_RECONSTRUCTION",
        "data_hashes": {
            "stream_families_v3_sha256_crlf": sha_crlf(FAMILIES_V3_PATH)
            if FAMILIES_V3_PATH.exists()
            else None,
            "dev_suite_a2_sha256_crlf": sha_crlf(SUITE_A2_PATH) if SUITE_A2_PATH.exists() else None,
            "stage_b_a2_sha256": hashlib.sha256(
                Path(__file__).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
            "code_hash16": sb._code_hash(),
            **{k: v for k, v in pf["hashes"].items() if isinstance(v, str)},
        },
        "seed_group": {
            "block": "d2a_rar_dev",
            "sub_block": "a2",
            "seed_start": min(seeds_all),
            "seed_end": max(seeds_all),
            "exposure": "dev",
            "replicates_per_cell": N_REP,
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
                        k: c[k] for k in ("T", "label_cap", "cost_vector", "retrain_duration")
                    }
                    for c in cells_def
                },
                "pairing": "run_paired",
                "verify_run": "every run",
            },
            "components_per_cell": {m: sb.components(cells, m) for m in show},
            "power_delay_per_cell": {m: sb.power_delay(cells, m) for m in show},
            "validity": res["validity"],
            "strongest_comparator": strongest,
            "strongest_comparator_per_cell": res["strongest_comparator_per_cell"],
            "eligible_comparators": res["eligible_comparators"],
            "excluded_comparators_invalid_for_claimed_null": res[
                "excluded_comparators_invalid_aggressive"
            ],
            "effect_vs_strongest": res["effect_vs_strongest"],
            "effect_vs_host": res["effect_vs_host"],
            "beats_simple_controls": res["beats_simple_controls"],
            "valid_ok": res["valid_ok"],
            "invalid_aggressive": res["invalid_aggressive"],
            "reading_A1": {
                "decision": res["decision"],
                "discard_reasons": res["discard_reasons"],
                "controls_ok": res["controls_ok"],
                "control_cell_notes": [
                    c["control_cell_regression"]
                    for c in res["counterexamples"]
                    if "control_cell_regression" in c
                ],
            },
            "reading_A2": {
                "decision": a2["decision"],
                "discard_reasons": a2["reasons"],
                "controls_ok": reading["controls_ok"],
                "control_cell_notes": reading["notes"],
            },
            "decision_rationale": "; ".join(a2["reasons"]) or res["why"],
            "implementation_notes": impl.notes,
            "preflight": pf,
            **(
                {"shell_contract_status": sq1.shell_contract_status(cand, cells_def)}
                if arm == "q1"
                else {}
            ),
            **({"canary_entry_rates": _canary_rates(cells)} if arm == "rar" else {}),
        },
        "uncertainty": {
            "method": "paired percentile bootstrap over seeds (2000 resamples, 95%), mean dJ = J_cand - J_comparator (negative = candidate better)",
            "dJ_vs_host": res["dJ_vs_host"],
            "dJ_vs_strongest": res["dJ_vs_strongest"],
        },
        "baseline_relative": {
            "strongest": strongest,
            "strongest_per_cell": res["strongest_comparator_per_cell"],
            "unmodified_host": "host",
            "dJ_vs_each_implemented_comparator": res["dJ_vs_each_comparator"],
        },
        "baselines_missing": sorted(b for b in required if b not in sb.BASELINE_IMPL),
        "counterexamples": res["counterexamples"],
        "prior_art_status": cand["prior_art_status"],
        "decision": a2["decision"],
        "behaviour_sha256": v2.behaviour_sha(cells, "cand"),
        "role": cand["role"],
        "effect_label_vs_strongest": res["effect_vs_strongest"]["label"],
    }
    return record


def _canary_rates(cells: list[dict]) -> dict:
    out = {}
    for c in cells:
        out[c["id"]] = {
            m: {
                "retrain_deployed_rate": sb._rate(c["runs"][m], "retrain_deployed"),
                "rollback_rate": sb._rate(c["runs"][m], "rolled_back"),
            }
            for m in ("host", "nocanary", "cand")
            if m in c["runs"]
        }
    return out


def run_audit(cand: dict, impl: Impl) -> dict:
    """100-replicate null audit of R1 on its validity cells (candidate only; pooled false-promotion + Clopper-Pearson)."""
    t0 = time.time()
    per, runs_all = {}, []
    for cd in audit_panel():
        spec, env = sq1._spec_env(cd)
        runs = sb.run_method(
            impl.build_cand, spec, env, seeds_of(cd["a2_index"], AUDIT_REP), "cand"
        )
        per[cd["id"]] = {"k": int(sum(r["promoted"] for r in runs)), "n": len(runs)}
        runs_all += runs
    k, n = int(sum(r["promoted"] for r in runs_all)), len(runs_all)
    cp = sb.cp_upper(k, n)
    outcome = "PASS" if (k / n <= sb.FP_TOL and cp <= 0.15) else "FAIL"
    seeds_all = [s for cd in audit_panel() for s in seeds_of(cd["a2_index"], AUDIT_REP)]
    rid = hashlib.sha256(f"{cand['candidate_id']}|audit|{SEED_START}".encode()).hexdigest()[:8]
    return {
        "candidate_id": cand["candidate_id"],
        "run_id": f"A2AUD-{cand['candidate_id']}-{rid}",
        "stage": "B",
        "suite": SUITE,
        "amendment": AMENDMENT,
        "arm": "q1",
        "candidate_key": "R1",
        "role": "validity_audit",
        "git_commit": lg.current_git_commit(),
        "method": "restart_min_certificate 100-replicate null audit (4 validity cells)",
        "host": cand["host"],
        "fidelity_tier": "PAPER_RECONSTRUCTION",
        "data_hashes": {"code_hash16": sb._code_hash()},
        "seed_group": {
            "block": "d2a_rar_dev",
            "sub_block": "a2",
            "seed_start": min(seeds_all),
            "seed_end": max(seeds_all),
            "exposure": "dev",
            "replicates_per_cell": AUDIT_REP,
            "cells": list(AUDIT_CELLS),
        },
        "hardware": lg.hardware_info(),
        "runtime_s": round(time.time() - t0, 3),
        "null_class": cand["target_null"],
        "assumptions": cand["assumptions"],
        "preregistered_predictions": {
            "hypothesis": "pooled false-promotion <= 0.10 with Clopper-Pearson 95% upper <= 0.15 over 4 x 100 null paths",
            "registered_in": "AUTORESEARCH_PROGRAM.md section 3b",
            "registered_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "results": {
            "audit_outcome": outcome,
            "pooled": {"k": k, "n": n, "rate": k / n, "cp95_upper": cp},
            "per_cell": per,
            "note": "audit record, not a screening decision: decision field is UNVERIFIED by construction; audit_outcome carries PASS/FAIL",
        },
        "baseline_relative": {},
        "counterexamples": [],
        "prior_art_status": cand["prior_art_status"],
        "decision": "UNVERIFIED",
        "unverified_reason": f"validity audit record (audit_outcome={outcome})",
    }


# ------------------------------------------------------------------------------------------ workers / orchestration
def _crash_record(cand: dict, error: str, runtime: float, decision: str = "CRASH", **extra) -> dict:
    rec = sb._crash_record(cand, error, runtime, decision, **extra)
    rec["run_id"] = "A2-" + rec["run_id"][2:]
    rec["suite"], rec["amendment"] = SUITE, AMENDMENT
    rec["data_hashes"] = {"code_hash16": sb._code_hash()}
    rec["seed_group"] = {
        "block": "d2a_rar_dev",
        "sub_block": "a2",
        "seed_start": SEED_START,
        "seed_end": SEED_START + 24 * 1000 + AUDIT_REP - 1,
        "exposure": "dev",
    }
    return rec


def worker_main(key: str, out_path: str, cache_dir: str | None = None) -> int:
    cand = all_candidates()[key.split(":")[0]]
    t0 = time.time()
    try:
        impl = resolve(key.split(":")[0], cand)
        if key.endswith(":audit"):
            out = {"status": "ok", "record": run_audit(cand, impl)}
        else:
            out = {
                "status": "ok",
                "record": run_experiment(
                    key, cand, impl, Path(cache_dir) if cache_dir else CACHE_DIR
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


def screen(key: str, work_dir: Path = WORK_DIR) -> tuple[str, dict]:
    cand = all_candidates()[key.split(":")[0]]
    pf = a2_preflight(cand)
    if not pf["ok"] and not key.endswith(":audit"):
        return "blocked", {"status": pf["status"], "reasons": pf["reasons"]}
    work_dir.mkdir(parents=True, exist_ok=True)
    op = work_dir / (key.replace(":", "_") + ".out.json")
    if op.exists():
        op.unlink()
    cmd = [sys.executable, "-m", "shiftlab.autoresearch.stage_b_a2", "--worker", key, str(op)]
    t0 = time.time()
    status, cpu = sq1._run_cpu_capped(cmd, CPU_CAP_S)
    if status != "ok":
        return "crash", _crash_record(
            cand,
            f"timeout: exceeded {CPU_CAP_S}s active compute ({status}; cpu_s={cpu:.1f}); process killed",
            time.time() - t0,
        )
    if not op.exists():
        return "crash", _crash_record(cand, "worker exited without output", time.time() - t0)
    out = json.loads(op.read_text(encoding="utf-8"))
    return out["status"], out["record"]


def warm_jobs(arm: str) -> list[tuple]:
    cells = q1_panel() if arm == "q1" else rar_panel()
    comps = ("host", *(Q1_COMPARATORS if arm == "q1" else RAR_COMPARATORS))
    jobs = [(arm, m, c["id"], k) for c in cells for m in comps for k in range(N_REP // CHUNK)]
    heavy = {"gapmix_exact08_s4": 0, "thinned_hedged_gate": 1}
    return sorted(jobs, key=lambda j: heavy.get(j[1], 2))


def warm_main(arm: str, comp: str, cell_id: str, chunk: str, cache_dir: str) -> int:
    cell = next(c for c in (q1_panel() if arm == "q1" else rar_panel()) if c["id"] == cell_id)
    run_ref(comp, cell, Path(cache_dir), int(chunk))
    return 0


def run_arm(
    arm: str, keys: list[str], *, workers: int = MAX_WORKERS, log=print, ledger_path=lg.LEDGER_PATH
) -> dict:
    import os

    if workers > MAX_WORKERS:
        raise ValueError(f"at most {MAX_WORKERS} workers")
    os.environ.setdefault("SHIFTLAB_STAGE_B_CODE_HASH", sb.code_hash())
    os.environ["PYTHONIOENCODING"] = "utf-8"
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    done_ids = {
        (r.get("candidate_key"), r.get("role") == "validity_audit")
        for r in lg.read_all(ledger_path)
        if r.get("suite") == SUITE and r.get("decision") != "CRASH"
    }
    todo = [k for k in keys if (k.split(":")[0], k.endswith(":audit")) not in done_ids]
    st = {
        "t0": time.time(),
        "arm": arm,
        "total": len(todo),
        "done": 0,
        "tally": Counter(),
        "phase": "warming references",
        "last": "",
    }

    def push():
        sb._write_json_atomic(STATE_PATH, {**st, "updated": time.time()})

    push()
    jobs = warm_jobs(arm)
    log(f"A2 {arm}: warming {len(jobs)} reference jobs ...")

    def warm(job):
        a, comp, cid, k = job
        cmd = [
            sys.executable,
            "-m",
            "shiftlab.autoresearch.stage_b_a2",
            "--warm",
            a,
            comp,
            cid,
            str(k),
            str(CACHE_DIR),
        ]
        try:
            r = subprocess.run(
                cmd,
                timeout=14400,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=REPO,
                check=False,
            )
            if r.returncode:
                log(f"warm FAILED {comp} {cid}.{k}: {r.stderr[-300:]}")
        except subprocess.TimeoutExpired:
            log(f"warm TIMEOUT {comp} {cid}.{k}")

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(warm, jobs))
    if arm == "rar":
        g0 = g0_check()
        log(f"G0: {json.dumps(g0)}")
        if not g0["pass"]:
            st["phase"] = (
                "G0 FAILED: family does not exercise the canary; no candidate records (arm UNVERIFIED)"
            )
            push()
            return {"done": 0, "tally": {}, "g0": g0}
    st["phase"] = "screening"
    push()
    with ThreadPoolExecutor(workers) as ex:
        futs = {k: ex.submit(screen, k) for k in todo}
        for k, f in futs.items():
            a, r = f.result()
            if a in ("ok", "crash", "invalid"):
                rec = lg.append(r, ledger_path)
                st["tally"][rec["decision"]] += 1
                st["last"] = f"{k} -> {rec['decision']} ({rec['runtime_s']}s)"
            else:
                st["tally"][a.upper()] += 1
                st["last"] = f"{k} -> {a}: {r}"
            st["done"] += 1
            log(st["last"])
            push()
    st["phase"] = "finished"
    push()
    return {"done": st["done"], "tally": dict(st["tally"])}


G0_PATH = STAGE_DIR / "a2_g0.json"


def g0_check(cache_dir: Path = CACHE_DIR) -> dict:
    """G0 (draft 2.2, host-only reference runs, no ledger record): RAR calibrated_v1 must retrain (N_r >= 1, i.e. reach the
    canary path) in >= 80% of seeds on S5a/S5c/S5d and <= 10% on S5b; on S5c the retrain must be undone/never deployed
    (retrain issued and no retrained model in force at the end) in >= 50% of seeds for RAR, and NoCanary must pay a J
    penalty vs RAR there. Computed from the cached reference runs only."""
    cells = {c["id"]: c for c in rar_panel()}
    out = {
        "cells": {},
        "thresholds": "S5a/S5c/S5d retrain rate >= 0.8; S5b <= 0.1; S5c undone rate >= 0.5 and J(nocanary) > J(host)",
    }
    for cid, c in cells.items():
        host = run_ref("host", c, cache_dir)
        nc = run_ref("nocanary", c, cache_dir)
        out["cells"][cid] = {
            "host_retrain_rate": float(np.mean([r["counts"]["N_r"] >= 1 for r in host])),
            "host_retrain_undone_rate": float(
                np.mean([r["counts"]["N_r"] >= 1 and not r["retrain_deployed"] for r in host])
            ),
            "J_host": float(np.mean(sb._a(host))),
            "J_nocanary": float(np.mean(sb._a(nc))),
            "nocanary_retrain_rate": float(np.mean([r["counts"]["N_r"] >= 1 for r in nc])),
        }
    c = out["cells"]
    ok = (
        all(c[k]["host_retrain_rate"] >= 0.8 for k in ("S5a", "S5c", "S5d"))
        and c["S5b"]["host_retrain_rate"] <= 0.1
        and c["S5c"]["host_retrain_undone_rate"] >= 0.5
        and c["S5c"]["J_nocanary"] > c["S5c"]["J_host"]
    )
    out["pass"] = bool(ok)
    sb._write_json_atomic(G0_PATH, out)
    return out


Q1_KEYS = ["REP1", "REP2", "REP3", "R1", "R1:audit"]
RAR_KEYS = ["k2_skip", "k1_p1", "L_routed"]


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "--worker":
        return worker_main(argv[1], argv[2])
    if len(argv) >= 6 and argv[0] == "--warm":
        return warm_main(argv[1], argv[2], argv[3], argv[4], argv[5])
    if argv and argv[0] == "--status":
        print(write_status())
        return 0
    if argv and argv[0] == "--write-registered":
        print(json.dumps(write_registered_files(), indent=1))
        return 0
    if argv and argv[0] in ("--q1", "--rar"):
        arm = argv[0][2:]
        print(
            run_arm(
                arm,
                Q1_KEYS if arm == "q1" else RAR_KEYS,
                workers=int(argv[1]) if len(argv) > 1 else MAX_WORKERS,
            )
        )
        return 0
    print("usage: --q1 [workers] | --rar [workers] | --write-registered", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


# ------------------------------------------------------------------------------------------ status report (numbers copied from ledger records only)
def _fmt_ci(x: dict) -> str:
    lo, hi = x["dJ_ci95"]
    return f"{x['dJ_mean']:+.2f} [{lo:+.2f}, {hi:+.2f}]"


def _record_section(r: dict) -> list[str]:
    R = r["results"]
    v = R["validity"]["candidate"]
    out = [f"### {r['candidate_key']}: {r['method']} ({r['candidate_id']})", ""]
    out.append(
        f"* decision (A2 reading, binding): **{R['reading_A2']['decision']}**; strict A1 reading: **{R['reading_A1']['decision']}**; "
        f"effect label vs strongest: {r['effect_label_vs_strongest']}; role: {r['role']}; runtime {r['runtime_s']} s; run_id `{r['run_id']}`"
    )
    if v.get("claimed"):
        out.append(
            f"* validity under claimed null `{v['null']}`: {v['metric']} {v['k']}/{v['n']} = {v['rate']:.3f}, Clopper-Pearson 95% upper {v['cp95_upper']:.3f} (screen-level)"
        )
    else:
        out.append(
            "* validity: no statistical null claimed (economic); no Clopper-Pearson bound applies"
        )
    out.append(f"* A1 reasons: {'; '.join(R['reading_A1']['discard_reasons']) or 'none'}")
    out.append(f"* A2 reasons: {'; '.join(R['reading_A2']['discard_reasons']) or 'none'}")
    out.append(
        f"* strongest comparator overall: `{R['strongest_comparator']}`; per cell: {json.dumps(R['strongest_comparator_per_cell'])}"
    )
    out.append("")
    out.append(
        "| cell | role | strongest applicable comparator | paired dJ vs strongest [95% CI] | J comp | rel. improvement |"
    )
    out.append("|---|---|---|---|---|---|")
    for x in r["uncertainty"]["dJ_vs_strongest"]:
        out.append(
            f"| {x['id']} | {x['role']} | {x['comparator']} | {_fmt_ci(x)} | {x['J_comp']:.2f} | {x['rel_improvement']:+.3f} |"
        )
    out.append("")
    notes1 = R["reading_A1"]["control_cell_notes"]
    notes2 = R["reading_A2"]["control_cell_notes"]
    out.append(f"* A1 control-cell failures: {json.dumps(notes1)}")
    out.append(f"* A2 control-cell failures: {json.dumps(notes2)}")
    if "canary_entry_rates" in R:
        out.append(
            f"* retrain / rollback rates (host, nocanary, cand): {json.dumps(R['canary_entry_rates'])}"
        )
    out.append("")
    return out


def write_status(path: Path = STATUS_PATH, ledger_path=lg.LEDGER_PATH) -> Path:
    recs = [r for r in lg.read_all(ledger_path) if r.get("suite") == SUITE]
    lines = [
        "# WP6 Stage B amendment A2 status (generated by `stage_b_a2.write_status`; numbers copied from ledger records)",
        "",
    ]
    lines.append(
        f"Ledger head: `{lg.head(ledger_path)}` ({len(lg.read_all(ledger_path))} records; {len(recs)} A2 records)  "
    )
    lines.append(f"Updated: {datetime.now(UTC).isoformat(timespec='seconds')}  ")
    lines.append(
        "Registered: `AUTORESEARCH_PROGRAM.md` section 3b. Seeds `110070000 + a2_index*1000 + replicate`. dJ = J(cand) - J(comparator), negative = candidate better, 95% paired bootstrap CI."
    )
    lines.append("")
    for arm, title in (
        ("q1", "Q1 arm (fresh-seed replications, restart_min, 100-replicate null audit)"),
        ("rar", "RAR arm (rar_persistent family; K2 candidate, K1 and L ablations)"),
    ):
        lines += [f"## {title}", ""]
        rs = [
            r
            for r in recs
            if r.get("arm") == arm or (arm == "q1" and r.get("role") == "validity_audit")
        ]
        if not rs:
            lines += ["No A2 record yet.", ""]
            continue
        lines.append(
            "| key | decision (A2) | decision (A1 strict) | effect | validity | best target cell dJ vs strongest |"
        )
        lines.append("|---|---|---|---|---|---|")
        for r in rs:
            R = r["results"]
            if r.get("role") == "validity_audit":
                p = R["pooled"]
                lines.append(
                    f"| {r['candidate_key']}:audit | audit {R['audit_outcome']} | n/a | n/a | FP {p['k']}/{p['n']} = {p['rate']:.3f}, CP95 upper {p['cp95_upper']:.3f} | n/a |"
                )
                continue
            if "reading_A2" not in R:
                lines.append(
                    f"| {r.get('candidate_key', r['candidate_id'])} | {r['decision']} | n/a | n/a | n/a | {r.get('error', '')[:80]} |"
                )
                continue
            v = R["validity"]["candidate"]
            val = (
                f"{v['k']}/{v['n']} = {v['rate']:.3f}, CP95 upper {v['cp95_upper']:.3f}"
                if v.get("claimed")
                else "none claimed"
            )
            b = R["effect_vs_strongest"]["best_target_cell"]
            best = f"{b['id']} vs {b['comparator']}: {_fmt_ci(b)}" if b else "n/a"
            lines.append(
                f"| {r['candidate_key']} | {R['reading_A2']['decision']} | {R['reading_A1']['decision']} | {r['effect_label_vs_strongest']} | {val} | {best} |"
            )
        lines.append("")
        for r in rs:
            if r.get("role") == "validity_audit":
                R = r["results"]
                lines += [
                    f"### {r['candidate_key']}:audit: {r['method']}",
                    "",
                    f"* outcome {R['audit_outcome']}; pooled {json.dumps(R['pooled'])}; per cell {json.dumps(R['per_cell'])}; run_id `{r['run_id']}`",
                    "",
                ]
            elif "reading_A2" in r["results"]:
                lines += _record_section(r)
    crashes = [r for r in recs if r["decision"] in ("CRASH", "INVALID")]
    if crashes:
        lines += (
            ["## CRASH / INVALID records", ""]
            + [
                f"* {r['candidate_id']} {r['decision']}: {(r.get('error') or r.get('invalid_reason') or '')[:300]}"
                for r in crashes
            ]
            + [""]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
