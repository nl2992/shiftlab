"""Declarative candidate grammar for the Drift2Act / RAR SOTA-first programme (WP5).

A *candidate identity* is a structured hypothesis (mechanism x host x question x null x a few discrete
knobs), not an experiment. Nothing here runs a controller. The data tables (families, variants) live in
``families.py``; this module holds the types, hook registry, compatibility rules, canonicalisation,
deduplication, prioritisation and Stage-B batch selection.

Identity key
------------
* ``mechanism_signature`` = sha256(canonical mechanism, host, question, target_null, hook, new-hypothesis text)
* ``behavioural_signature`` = sha256(mechanism_signature, config with inert knobs masked)
* ``candidate_id`` = ``CAND-`` + first 16 hex of the behavioural signature (so two spellings that provably
  induce the same policy share one id and are collapsed by :func:`dedup`).
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

GRAMMAR_VERSION = "1.0.0"
REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_DIR = REPO_ROOT / "docs" / "d2a_rar" / "registry"
MAX_IDENTITIES = 100_000
BATCH_SIZE = 200

# ---------------------------------------------------------------- vocabularies
D, R, A, H, C = "drift2act", "rar", "cost_aware_binary", "challenger", "contract_native"
HOSTS = (D, R, A, H, C)
QUESTIONS = ("Q1", "Q2", "Q3")
NULLS = ("cond", "marg", "absolute_risk", "economic", "none")
Q3_BLOCK = "Q1 and Q2 winners"

# Nulls a candidate on a given host may meaningfully declare (host null: Drift2Act = absolute_risk,
# RAR = none/UNVERIFIED, Challenger = economic; Q1 evidence on Drift2Act is a sentinel-level cond/marg null).
HOST_ALLOWED_NULLS: dict[str, frozenset[str]] = {
    D: frozenset({"absolute_risk", "cond", "marg", "economic"}),
    R: frozenset({"economic", "none", "cond"}),
    A: frozenset({"economic", "none"}),
    H: frozenset({"economic"}),
    C: frozenset({"cond", "marg", "absolute_risk", "economic", "none"}),
}


def _hook(host, module, attr, kind, status, note, **extra):
    return dict(host=host, module=module, attr=attr, kind=kind, status=status, note=note, **extra)


# Hook registry. status: AVAILABLE = documented protocol/config class exists in the host package;
# NOT_EXPOSED = the host has no such seam yet (preflight -> BLOCKED_HOOK_MISSING, never INVALID).
HOOKS: dict[str, dict[str, Any]] = {
    "d2a.request_size": _hook(
        D,
        "shiftlab.sota.drift2act.audit",
        "LabelRequestPolicy",
        "protocol",
        "AVAILABLE",
        "decides only HOW MANY labels; index choice and certificate untouched",
    ),
    "d2a.evidence_log_lik": _hook(
        D,
        "shiftlab.sota.drift2act.belief",
        "EvidenceModel",
        "protocol",
        "AVAILABLE",
        "log_lik(z, gap) swaps belief evidence; gap carried for gap-aware work",
    ),
    "d2a.config": _hook(
        D,
        "shiftlab.sota.drift2act.actions",
        "Config",
        "config",
        "AVAILABLE",
        "dataclass fields only (tau, cooldowns, lam, audit_every, delta_mode)",
        fields=(
            "tau",
            "delta",
            "cooldown_retrain",
            "cooldown_rollback",
            "lam",
            "audit_every",
            "delta_mode",
        ),
    ),
    "d2a.action_selector": _hook(
        D,
        "shiftlab.sota.drift2act.controller",
        None,
        "seam",
        "NOT_EXPOSED",
        "per-action utility/threshold selection is internal to the controller step",
    ),
    "d2a.rollback_schedule": _hook(
        D,
        "shiftlab.sota.drift2act.controller",
        None,
        "seam",
        "NOT_EXPOSED",
        "rollback scheduling is internal to the failure branch",
    ),
    "d2a.subgroup_belief": _hook(
        D,
        "shiftlab.sota.drift2act.belief",
        None,
        "seam",
        "NOT_EXPOSED",
        "subgroup belief/ECE monitor not behind a hook",
    ),
    "rar.label_request": _hook(
        R,
        "shiftlab.sota.rar.components",
        "LabelRequestPolicy",
        "protocol",
        "AVAILABLE",
        "request(HookContext) at serve time",
    ),
    "rar.gate2": _hook(
        R,
        "shiftlab.sota.rar.components",
        "GateRule",
        "protocol",
        "AVAILABLE",
        "Gate 2 (label fraction theta_L) swap-in",
    ),
    "rar.gate3": _hook(
        R,
        "shiftlab.sota.rar.components",
        "GateRule",
        "protocol",
        "AVAILABLE",
        "Gate 3 (A_pre - A_cur >= theta_R) swap-in",
    ),
    "rar.config": _hook(
        R,
        "shiftlab.sota.rar.config",
        "RARConfig",
        "config",
        "AVAILABLE",
        "dataclass fields: canary p1/W1/W2, hold lengths kappa_*, rho",
        fields=("p1", "W1", "W2", "kappa_short", "kappa_long", "m_clear", "rho", "theta_L"),
    ),
    "rar.rollback_rule": _hook(
        R,
        "shiftlab.sota.rar.controller",
        None,
        "seam",
        "NOT_EXPOSED",
        "rollback causes/hold transitions are internal; only thresholds are config fields",
    ),
    "cab.gate": _hook(
        A,
        "shiftlab.sota.rar.config",
        "RARConfig",
        "config",
        "AVAILABLE",
        "RAR harness mode 'cost_aware_binary' (cost_gate on; gates/canary/holds off)",
        fields=("rho", "mode"),
    ),
    "challenger.rule": _hook(
        H,
        "shiftlab.sota.challenger.algorithms",
        "gse_decide",
        "function",
        "AVAILABLE",
        "GSE/OSE/LSE decide functions (paper reconstruction, closed-form economics)",
    ),
    "contract.query": _hook(
        C,
        "shiftlab.bench.contract.policies",
        "BasePolicy",
        "protocol",
        "AVAILABLE",
        "query(propensity=...) with honest-propensity verification",
    ),
    "contract.route": _hook(
        C,
        "shiftlab.bench.contract.policies",
        "BasePolicy",
        "protocol",
        "AVAILABLE",
        "route(target, fraction) canary split",
    ),
    "contract.retrospective_query": _hook(
        C,
        "shiftlab.bench.contract.policies",
        "BasePolicy",
        "protocol",
        "AVAILABLE",
        "query(round=...) retrospective labels with max_lookback",
    ),
    "contract.switch_policy": _hook(
        C,
        "shiftlab.bench.contract.policies",
        "BasePolicy",
        "protocol",
        "AVAILABLE",
        "whole-policy act(): switch/retrain/rollback/alert/abstain",
    ),
    "contract.proxy_predictions": _hook(
        C,
        "shiftlab.bench.contract.types",
        None,
        "seam",
        "NOT_EXPOSED",
        "proxy predictions / source calibration not in ObservableState (WP2c open)",
    ),
}
D_RS, D_EV, D_CF = "d2a.request_size", "d2a.evidence_log_lik", "d2a.config"
D_AS, D_RB, D_SG = "d2a.action_selector", "d2a.rollback_schedule", "d2a.subgroup_belief"
R_LR, R_G2, R_G3 = "rar.label_request", "rar.gate2", "rar.gate3"
R_CF, R_RB, CAB_G, CH_R = "rar.config", "rar.rollback_rule", "cab.gate", "challenger.rule"
C_Q, C_RT, C_RQ = "contract.query", "contract.route", "contract.retrospective_query"
C_SW, C_PX = "contract.switch_policy", "contract.proxy_predictions"

# Discrete knobs. The FIRST value is the default (used for parent/sibling bookkeeping).
KNOBS: dict[str, tuple] = {
    "gap_source": ("observed", "expected_plugin"),
    "smoothing": (0.02, 0.10),
    "declared_rho_bar": (0.5, 0.8),
    "envelope_radius": (0.05, 0.10, 0.20),
    "estimator": ("plugin", "dirichlet"),
    "start_prior": ("uniform", "geometric", "gap_weighted"),
    "max_starts": (16, 64),
    "selector_rule": ("dependence_test", "min_of_both"),
    "selector_alpha": (0.05, 0.20),
    "min_propensity": (0.05, 0.20),
    "propensity_score": ("margin", "disagreement", "gap_to_threshold"),
    "horizon_pricing": ("remaining", "deadline"),
    "shadow_price": ("off", "static", "dual"),
    "survival_model": ("none", "hazard", "empirical"),
    "pending_cap_frac": (0.10, 0.25, 0.50),
    "feasibility_q": (0.5, 0.8, 0.95),
    "deadline_source": ("certificate_window", "promotion_horizon"),
    "duration_prior": ("geometric", "semi_markov"),
    "hazard_floor": (0.001, 0.01),
    "promo_rule": ("lcb_break_even", "cvar", "expected_gain"),
    "promo_conf": (0.80, 0.95),
    "theta_L_range": ("0.5-0.8", "0.3-0.9"),
    "waiting_cost_model": ("linear", "hazard"),
    "recovery_estimator": ("A_pre_minus_A_cur", "heldout_recovery"),
    "rho_scale": (1.0, 0.5, 2.0),
    "p1": (0.2, 0.05, 0.1, 0.4),
    "W1": (300, 100),
    "W2": (600, 300),
    "ramp": ("fixed", "geometric"),
    "audit_every": (4, 2, 8, 16),
    "delta_mode": ("alg1", "mandate", "front_loaded"),
    "tau_scale_rollback": (1.0, 1.25, 1.5),
    "tau_scale_retrain": (1.0, 0.75),
    "stake_rule": ("kelly", "capped_kelly"),
    "stake_cap": (0.25, 0.50),
    "threshold_rule": ("break_even", "margin_1sd", "margin_2sd"),
    "pending_label_credit": ("off", "on"),
    "post_switch_window": (150, 50, 400),
    "pairing": ("paired", "unpaired"),
    "rollback_threshold": (0.10, 0.05, 0.20),
    "wait_for_pending": ("off", "on"),
    "hold_scale": (1.0, 0.5, 2.0),
    "release_rule": ("evidence", "cost_scaled"),
    "price_slope": (1.0, 0.5, 2.0),
    "subgroup_rule": ("worst_group", "bonferroni_groups"),
    "min_group_labels": (30, 10),
    "proxy_source": ("source_model", "shadow_model"),
    "cv_coef": ("estimated", "fixed"),
    "coupling": ("shared_price", "transfer_rule"),
    "transfer_frac": (0.1, 0.3),
    "meta_window": (100, 300),
    "meta_regime": ("free_vs_tight_budget", "ucb_over_modes"),
    "interaction_design": ("stack_independent", "shared_label_budget"),
}

FIDELITY_REQUIREMENT = {
    D: "Stage B-C: COMMON_CONTRACT_PORT on host tier PAPER_RECONSTRUCTION (no author code found); report as "
    "PAPER_RECONSTRUCTION-relative, never AUTHOR_NATIVE.",
    R: "Stage B-C: COMMON_CONTRACT_PORT on host tier PAPER_RECONSTRUCTION (Zenodo artifact not public); "
    "canary traffic split is a documented loss of fidelity in the contract.",
    A: "RAR Cost-Aware Binary run as a mode of the RAR PAPER_RECONSTRUCTION harness; same caveats as RAR.",
    H: "PAPER_RECONSTRUCTION of GSE/OSE/LSE (closed-form economics); not the Challenger's native "
    "evolving-challenger setting.",
    C: "COMMON_CONTRACT_PORT (our contract, not a paper's); results are contract-relative.",
}

# Baseline id -> null_assumptions.yaml entry id (None = no registry entry yet).
BASELINE_NULL_ENTRY: dict[str, str | None] = {
    "uniform_query": "controls_uniform_pending_cap",
    "pending_cap": "controls_uniform_pending_cap",
    "fixed_schedule": "controls_uniform_pending_cap",
    "front_loaded": "episode_front",
    "drift2act_native_audit": "drift2act_certificate",
    "drift2act_unmodified": "drift2act_certificate",
    "drift2act_gate": "drift2act_certificate",
    "asi_inspired": "asi_zrnic_candes",
    "gong_zhang_paid_obs": "gong_zhang_paid_obs",
    "pave": "pave",
    "adowip_priority": None,
    "xu_propensity_policy": None,
    "pham_fs": None,
    "markov_lr": "markov_lr",
    "markov_lr_plugin": "markov_lr",
    "sethi_plugin_on_thinned_chain": "sethi_markov_test",
    "sethi_composite_null": "sethi_markov_test",
    "robust_lfd_tests": None,
    "fixed_spacing": "thinned_hedged_gate",
    "restart_without_gaps": "rmm",
    "e_sr_markov_base": None,
    "page_cusum": "page_cusum",
    "page_cusum_post_switch": "page_cusum",
    "e_rb": "e_rb",
    "h2c": "h2c",
    "conditional_null_certifier": "certified_deployment_gates",
    "rar_unmodified": "rar_gates",
    "rar_cost_aware_binary": "rar_gates",
    "rar_fixed_canary": "rar_canary_rollback",
    "rar_no_canary": "rar_canary_rollback",
    "rar_rollback_rules": "rar_canary_rollback",
    "cara": None,
    "zliobaite_roi": None,
    "challenger_ose_gse_lse": "challenger_gse",
    "lindon_sequential_canary": None,
    "cpc_regulated_exposure": None,
    "prudent_banker_fallback": None,
    "pprm": "pprm",
    "podkopaev_cs": None,
    "rccda": None,
    "cheng_batched": None,
    "gongzhang_adapted": "gong_zhang_paid_obs",
    "j00_host": None,
    "j10_q1_only": None,
    "j01_q2_only": None,
}

Q1_BASELINES = (
    "markov_lr",
    "sethi_plugin_on_thinned_chain",
    "fixed_spacing",
    "restart_without_gaps",
    "conditional_null_certifier",
    "page_cusum",
)
Q2_BASELINES = (
    "uniform_query",
    "pending_cap",
    "fixed_schedule",
    "front_loaded",
    "drift2act_native_audit",
    "asi_inspired",
    "gong_zhang_paid_obs",
    "pave",
)
Q3_BASELINES = (
    "j00_host",
    "j10_q1_only",
    "j01_q2_only",
    "gongzhang_adapted",
    "drift2act_unmodified",
)
HOST_BASELINES = {
    D: ("drift2act_unmodified",),
    R: ("rar_unmodified", "rar_cost_aware_binary"),
    A: ("rar_unmodified", "rar_cost_aware_binary"),
    H: ("challenger_ose_gse_lse",),
    C: (),
}
# Prior-art family -> comparators the WP4 ledger makes mandatory (normalised to our ids).
F_COMPARATORS = {
    "F1": ("sethi_plugin_on_thinned_chain", "markov_lr", "fixed_spacing", "restart_without_gaps"),
    "F2": ("sethi_composite_null", "robust_lfd_tests", "markov_lr_plugin"),
    "F3": ("e_sr_markov_base", "page_cusum", "restart_without_gaps"),
    "F4": ("adowip_priority", "xu_propensity_policy"),
    "F5": ("pham_fs", "adowip_priority", "drift2act_native_audit"),
    "F6": (
        "rar_unmodified",
        "rar_cost_aware_binary",
        "cara",
        "zliobaite_roi",
        "challenger_ose_gse_lse",
    ),
    "F7": (
        "rar_fixed_canary",
        "rar_no_canary",
        "lindon_sequential_canary",
        "cpc_regulated_exposure",
    ),
    "F8": ("drift2act_unmodified", "xu_propensity_policy", "pprm", "podkopaev_cs"),
    "F9": (
        "rar_rollback_rules",
        "drift2act_gate",
        "page_cusum_post_switch",
        "prudent_banker_fallback",
    ),
    "F10": ("drift2act_unmodified", "gongzhang_adapted", "rccda", "cheng_batched"),
}

# Failure-ledger rows whose underlying problem SURVIVES the null correction (FAILURE_ATLAS_CORRECTED sec 4).
SURVIVING_FAILURES = frozenset(
    {
        "FL-039",
        "FL-043",
        "FL-009",
        "FL-031",
        "FL-030",
        "FL-021",
        "FL-012",
        "FL-045",
        "FL-052",
        "FL-035",
        "FL-036",
    }
)

SCORE_WEIGHTS = {
    "prior_art": 0.30,
    "failure_link": 0.25,
    "host_strength": 0.15,
    "simplicity": 0.15,
    "null_eligibility": 0.15,
}
CONFIG_SPRAWL_PENALTY = 0.03  # non-default knob combination
PRIOR_ART_SCORE = {
    "PLAUSIBLY_DISTINCT": 1.0,
    "UNVERIFIED": 0.5,
    "KNOWN": 0.10,
    "HIGH_OVERLAP": 0.10,
}
RESIDUE_PRIOR_ART_SCORE = (
    0.6  # narrow residue inside a HIGH_OVERLAP family (F4 VOQ vs certificate state)
)
HOST_STRENGTH = {D: 1.0, R: 1.0, A: 0.7, C: 0.6, H: 0.5}
NULL_ELIGIBILITY = {"cond": 1.0, "marg": 1.0, "absolute_risk": 0.9, "economic": 0.6, "none": 0.3}

BATCH_CAPS = {
    "per_family": 12,
    "min_per_family": 4,
    "per_variant": 3,
    "per_variant_host_null": 2,
    "per_host": 110,
    "ablation_only": 90,
    "q1_max": 70,
    "q1_min": 40,
}


# ---------------------------------------------------------------- types
@dataclass(frozen=True)
class Variant:
    key: str
    desc: str
    hyp: str
    win: str
    fail: str
    hooks: dict  # host -> hook name
    nulls: tuple
    knobs: tuple
    cx: int = 2
    questions: tuple | None = None
    prior: str | None = None  # per-variant prior-art status override
    prior_note: str = ""
    closest: tuple | None = None
    gap_aware: bool = False
    residue: bool = False
    repeats: tuple = ()  # failure-ledger ids whose do_not_repeat_without applies
    inert: tuple = ()  # ((knob, {cond}), ...): knob does not change the policy when cond holds
    canonical: str | None = None  # "family.variant" this spelling is an exact alias of
    q3_pairable: bool = False
    extra_baselines: tuple = ()


@dataclass(frozen=True)
class Family:
    key: str
    label: str
    questions: tuple
    prior_family: str | None  # F1..F10 from prior_art.yaml, or None (unmapped -> UNVERIFIED)
    closest: tuple
    failure_links: tuple
    variants: tuple = field(default_factory=tuple)


@lru_cache(maxsize=1)
def load_prior_art() -> dict:
    d = yaml.safe_load((REGISTRY_DIR / "prior_art.yaml").read_text(encoding="utf-8"))
    return {"families": {f["id"].split("_")[0]: f for f in d["families"]}, "papers": d["papers"]}


@lru_cache(maxsize=1)
def load_failure_ledger() -> dict[str, dict]:
    rows = {}
    with (REGISTRY_DIR / "failure_ledger.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                rows[r["id"]] = r
    return rows


@lru_cache(maxsize=1)
def load_null_entries() -> dict[str, dict]:
    d = yaml.safe_load((REGISTRY_DIR / "null_assumptions.yaml").read_text(encoding="utf-8"))
    return {e["id"]: e for e in d["entries"]}


def families() -> tuple[Family, ...]:
    from .families import FAMILIES

    return FAMILIES


def family_by_key(key: str) -> Family:
    for f in families():
        if f.key == key:
            return f
    raise KeyError(key)


def variant_of(fam: Family, key: str) -> Variant:
    for v in fam.variants:
        if v.key == key:
            return v
    raise KeyError(f"{fam.key}.{key}")


# ---------------------------------------------------------------- helpers
def sha(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def prior_art_status(fam: Family, var: Variant) -> tuple[str, str]:
    """(status, note). Mapped families inherit the WP4 ledger status; unmapped ones are UNVERIFIED."""
    if var.prior:
        return var.prior, var.prior_note
    if fam.prior_family is None:
        return "UNVERIFIED", "family not covered by a WP4 ledger family; no search done"
    f = load_prior_art()["families"][fam.prior_family]
    if (
        fam.prior_family == "F6" and fam.key != "cost_aware_rar_gate"
    ):  # F6 PLAUSIBLY_DISTINCT is Gate-2 only
        return (
            "UNVERIFIED",
            "F6 PLAUSIBLY_DISTINCT status covers RAR Gate-2 only; this variant is unsearched",
        )
    return f["status"], f.get("scope_note") or f.get("caveat") or ""


def role_of(status: str, var: Variant) -> tuple[str, bool]:
    """(role, novelty_bearing). HIGH_OVERLAP/KNOWN are baselines or ablation arms, never novelty-bearing."""
    if status in ("HIGH_OVERLAP", "KNOWN"):
        return ("narrow_residue_test" if var.residue else "baseline_or_ablation_only"), False
    if status == "PLAUSIBLY_DISTINCT":
        return "novelty_candidate_unconfirmed", True
    return "unverified_candidate", False


def canonical_spelling(fam: Family, var: Variant) -> str:
    return var.canonical or f"{fam.key}.{var.key}"


def _cond_holds(cond: dict, host: str, null: str, cfg: dict) -> bool:
    for k, want in cond.items():
        have = host if k == "host" else null if k == "null" else cfg.get(k)
        wants = want if isinstance(want, tuple | list | set | frozenset) else (want,)
        if have not in wants:
            return False
    return True


def canonical_config(var: Variant, host: str, null: str, cfg: dict) -> dict:
    """Mask knobs that provably do not change the induced policy for this (host, null, config)."""
    out = dict(cfg)
    for knob, cond in var.inert:
        if knob in out and _cond_holds(cond, host, null, cfg):
            out[knob] = "_inert_"
    return out


def compute_blocked_by(var: Variant, new_hyp: str | None) -> list[dict]:
    """Ledger rows whose ``do_not_repeat_without`` this construction matches (unless a new hypothesis is declared)."""
    if not var.repeats or (new_hyp and new_hyp.strip()):
        return []
    led = load_failure_ledger()
    return [
        {"ledger_id": i, "requirement": led[i]["do_not_repeat_without"]}
        for i in var.repeats
        if i in led
    ]


def required_baselines(question: str, host: str, fam: Family, var: Variant) -> list[str]:
    base: list[str] = []
    base += {"Q1": Q1_BASELINES, "Q2": Q2_BASELINES, "Q3": Q3_BASELINES}[question]
    base += HOST_BASELINES[host]
    if fam.prior_family:
        base += F_COMPARATORS[fam.prior_family]
    base += var.extra_baselines
    if "rar_gate" in fam.key:  # RAR-gate candidates: unmodified RAR AND Cost-Aware Binary
        base += ("rar_unmodified", "rar_cost_aware_binary")
    return list(dict.fromkeys(base))


def assumptions_for(host: str, null: str, var: Variant) -> list[str]:
    a = [
        (
            "policy sees only ObservableState (no evaluator truth, no unreleased labels); "
            "request/observation/release clocks as in BENCHMARK_CONTRACT"
        ),
        {
            "cond": "validity scored only on streams where H0cond: E[d_t|F_{t-1}] <= 0 holds on the whole path "
            "(F_{t-1} = released labels, actions, request/release history); query decisions F_{t-1}-predictable",
            "marg": "validity scored only on streams where H0marg: E[d_t] <= 0 holds; declared dependence class "
            "(rho_bar) stated; never scored on cond-only streams as equal",
            "absolute_risk": "bounded losses in [0,1]; window risk R_t <= tau; sample size depends only on "
            "F_{t-1}; uniform sampling within window (or declared inclusion propensities); no serial-dependence claim",
            "economic": "no anytime-valid guarantee claimed; judged on J after all costs and on safety "
            "constraints; never compared as equal with a valid-conservative method on false promotion",
            "none": "no validity claim; heuristic; reported on J and descriptive diagnostics only",
        }[null],
    ]
    if var.gap_aware:
        a.append(
            "observation gaps g_i are observed; the observation mechanism may be informative: state the gap law"
        )
    if host == D:
        a.append(
            "host fidelity PAPER_RECONSTRUCTION; Theorem 1 vs lagged-window audit item (App. D.7) unresolved"
        )
    if host in (R, A):
        a.append(
            "RAR label-frontier semantics preserved; contract canary split loses native-stage fidelity"
        )
    return a


def falsification_test(question: str, null: str) -> str:
    base = {
        "Q1": "Fails if, on the frozen dev suite, power/delay/J does not beat the best of {valid Markov-LR, "
        "thinned/fixed-spacing, restart-without-gaps, matched conditional-null certifier} at comparable "
        f"validity under its own null ({null}); an invalid-aggressive win is not a win.",
        "Q2": "Fails if J (after all costs, paired CI) is not better than the strongest of {pending cap, fixed "
        "schedule, front-loaded, Drift2Act native audit} on the target cell, or if it is worse than the host "
        "on the neighbouring/negative-control cell; if it only matches a pending cap/fixed schedule record "
        "NEGATIVE and stop (Mandate Q2).",
        "Q3": "J11 interaction I=(J00-J11)-[(J00-J10)+(J00-J01)] must favour synergy with CI excluding 0 AND "
        "J11 must beat the best single of J10/J01; combo ~ best single or negative interaction => no synergy claim.",
    }[question]
    return base + " Mechanistic ablation (hook restored to host default) must erase the gain."


# ---------------------------------------------------------------- identity construction
def make_identity(
    fam: Family,
    var: Variant,
    host: str,
    question: str,
    null: str,
    cfg: dict,
    *,
    new_hypothesis: str | None = None,
) -> dict:
    hook = var.hooks[host]
    status, note = prior_art_status(fam, var)
    role, novel = role_of(status, var)
    ccfg = canonical_config(var, host, null, cfg)
    canon = canonical_spelling(fam, var)
    mech_sig = sha([canon, host, question, null, hook, (new_hypothesis or "").strip()])
    beh_sig = sha([mech_sig, ccfg])
    hook_status = HOOKS[hook]["status"]
    level = min(5, var.cx + (1 if hook_status == "NOT_EXPOSED" else 0))
    default_cfg = {k: KNOBS[k][0] for k in var.knobs}
    parent_sig = sha([mech_sig, canonical_config(var, host, null, default_cfg)])
    return {
        "candidate_id": "CAND-" + beh_sig[:16],
        "parent_id": "BASE-" + host if parent_sig == beh_sig else "CAND-" + parent_sig[:16],
        "host": host,
        "research_question": question,
        "family": fam.key,
        "variant": var.key,
        "scientific_hypothesis": var.hyp,
        "mechanism": f"{fam.label}: {var.desc}",
        "closest_prior_art": list(var.closest or fam.closest),
        "prior_art_family": fam.prior_family,
        "prior_art_status": status,
        "prior_art_note": note,
        "role": role,
        "novelty_bearing": novel,
        "target_null": null,
        "scoring_null": null,
        "assumptions": assumptions_for(host, null, var),
        "configuration": dict(cfg),
        "canonical_configuration": ccfg,
        "predicted_win_region": var.win,
        "predicted_failure_region": var.fail,
        "complexity": {
            "level": level,
            "est_diff_loc": 30 * level,
            "hook": hook,
            "hook_status": hook_status,
        },
        "required_baselines": required_baselines(question, host, fam, var),
        "falsification_test": falsification_test(question, null),
        "fidelity_requirement": FIDELITY_REQUIREMENT[host],
        "hook": hook,
        "failure_ledger_links": sorted(set(fam.failure_links) | set(var.repeats)),
        "blocked_by": compute_blocked_by(var, new_hypothesis),
        "blocked_until": Q3_BLOCK if question == "Q3" else None,
        "new_mechanistic_hypothesis": (new_hypothesis or "").strip() or None,
        "mechanism_signature": mech_sig,
        "behavioural_signature": beh_sig,
        "canonical_mechanism": canon,
        "duplicates_collapsed": 0,
        "aliases": [],
        "grammar_version": GRAMMAR_VERSION,
    }


REQUIRED_FIELDS = (
    "candidate_id",
    "parent_id",
    "host",
    "research_question",
    "scientific_hypothesis",
    "mechanism",
    "closest_prior_art",
    "target_null",
    "assumptions",
    "configuration",
    "predicted_win_region",
    "predicted_failure_region",
    "complexity",
    "required_baselines",
    "falsification_test",
    "fidelity_requirement",
    "prior_art_status",
    "role",
    "failure_ledger_links",
    "blocked_by",
)


def validate_identity(c: dict) -> list[str]:
    """Return grammar violations (empty list = structurally valid). Empty ``blocked_by`` is allowed."""
    errs = [
        f"missing:{f}"
        for f in REQUIRED_FIELDS
        if f not in c or (c[f] in (None, "") and f not in ("blocked_by", "configuration"))
    ]
    if errs:
        return errs
    host, q, null, hook = c["host"], c["research_question"], c["target_null"], c.get("hook")
    if host not in HOSTS:
        return [f"bad_host:{host}"]
    if q not in QUESTIONS:
        errs.append(f"bad_question:{q}")
    if null not in NULLS:
        errs.append(f"bad_null:{null}")
    elif null not in HOST_ALLOWED_NULLS[host]:
        errs.append(f"null_not_allowed_on_host:{null}@{host}")
    if hook not in HOOKS:
        return [*errs, f"unknown_hook:{hook}"]
    if HOOKS[hook]["host"] != host:
        errs.append("hook_host_mismatch")
    if hook == R_G2 and host != R:
        errs.append("gate2_only_on_rar")
    if hook == R_G3 and host not in (R, A):
        errs.append("gate3_only_on_rar_or_cab")
    if hook == D_RS and host != D:
        errs.append("request_size_only_via_drift2act_hook")
    if host == D and c.get("family") in _REQUEST_FAMILIES and hook != D_RS and q == "Q2":
        errs.append("drift2act_q2_acquisition_must_use_request_size_hook")
    if c.get("scoring_null") != null:
        errs.append("scoring_null_differs_from_target_null")
    if q == "Q3" and not c.get("blocked_until"):
        errs.append("q3_not_blocked_until_winners")
    if c["prior_art_status"] in ("HIGH_OVERLAP", "KNOWN") and c.get("novelty_bearing"):
        errs.append("high_overlap_marked_novelty_bearing")
    rb = set(c["required_baselines"])
    errs += [f"unknown_baseline:{b}" for b in sorted(rb) if b not in BASELINE_NULL_ENTRY]
    for qq, need in (("Q1", Q1_BASELINES), ("Q2", Q2_BASELINES), ("Q3", Q3_BASELINES)):
        if q == qq and not set(need) <= rb:
            errs.append(f"{qq.lower()}_missing_mandatory_baselines")
    if "rar_gate" in str(c.get("family")) and not {"rar_unmodified", "rar_cost_aware_binary"} <= rb:
        errs.append("rar_gate_missing_unmodified_and_cost_aware_binary")
    errs += [
        f"unknown_prior_art_id:{p}"
        for p in c["closest_prior_art"]
        if p not in load_prior_art()["papers"]
    ]
    if c.get("family") != "q3_factorial_stack":
        try:
            fam = family_by_key(c["family"])
            var = variant_of(fam, c["variant"])
        except KeyError:
            return [*errs, "unknown_family_variant"]
        if var.gap_aware and null not in ("cond", "marg"):
            errs.append("gap_aware_requires_cond_or_marg")
        if var.hooks.get(host) != hook:
            errs.append("hook_not_declared_for_host")
        if null not in var.nulls:
            errs.append("null_not_declared_for_variant")
        if q not in (var.questions or fam.questions):
            errs.append("question_not_allowed")
        errs += [
            f"bad_knob:{k}={v}"
            for k, v in c["configuration"].items()
            if k not in var.knobs or v not in KNOBS.get(k, ())
        ]
    return errs


# Families whose Q2 mechanisms are label-request mechanisms (on Drift2Act they must go through request_size).
_REQUEST_FAMILIES = frozenset(
    {
        "adaptive_query_propensities",
        "voi_acquisition",
        "pending_aware_budgets",
        "deadline_aware_querying",
    }
)


# ---------------------------------------------------------------- generation
def _config_product(var: Variant) -> list[dict]:
    names = list(var.knobs)
    return [
        dict(zip(names, vals, strict=True))
        for vals in itertools.product(*(KNOBS[n] for n in names))
    ]


def generate_identities() -> list[dict]:
    """All raw (pre-dedup) family identities, Q1/Q2/Q3-family."""
    out: list[dict] = []
    for fam in families():
        for var in fam.variants:
            for host in HOSTS:
                if host not in var.hooks:
                    continue
                for q in var.questions or fam.questions:
                    for null in var.nulls:
                        if null in HOST_ALLOWED_NULLS[host]:
                            out.extend(
                                make_identity(fam, var, host, q, null, cfg)
                                for cfg in _config_product(var)
                            )
    return out


def dedup(identities: list[dict]) -> tuple[list[dict], dict]:
    """Collapse identities with the same behavioural signature.

    Reasons: ``alias`` (a different spelling of the same canonical mechanism) or ``inert_knob``
    (same spelling; configs differing only in knobs that are inert for this host/null/config).
    """
    groups: dict[str, list[dict]] = {}
    for c in identities:
        groups.setdefault(c["behavioural_signature"], []).append(c)
    kept, reasons = [], Counter()
    for sig in sorted(groups):
        g = sorted(  # the canonical spelling is the primary; other spellings become aliases
            groups[sig],
            key=lambda c: (
                f"{c['family']}.{c['variant']}" != c["canonical_mechanism"],
                c["family"],
                c["variant"],
                json.dumps(c["configuration"], sort_keys=True),
            ),
        )
        primary = dict(g[0])
        primary["duplicates_collapsed"] = sum(1 + x.get("duplicates_collapsed", 0) for x in g) - 1
        spell = {f"{c['family']}.{c['variant']}" for c in g}
        primary["aliases"] = sorted(spell - {f"{primary['family']}.{primary['variant']}"})[:5]
        for other in g[1:]:
            same = (other["family"], other["variant"]) == (primary["family"], primary["variant"])
            reasons["inert_knob" if same else "alias"] += 1
        kept.append(primary)
    kept.sort(key=lambda c: c["candidate_id"])
    return kept, {"before": len(identities), "after": len(kept), "reasons": dict(reasons)}


def _q3_factorial(pool: list[dict]) -> list[dict]:
    """J11 identities: default-config, unblocked, pairable Q1 x Q2 constituents on a common host."""
    by: dict[tuple, list] = {}
    for c in pool:
        if c["blocked_by"] or c["research_question"] == "Q3":
            continue
        fam = family_by_key(c["family"])
        var = variant_of(fam, c["variant"])
        if var.q3_pairable and c["configuration"] == {k: KNOBS[k][0] for k in var.knobs}:
            by.setdefault((c["host"], c["research_question"]), []).append((c, fam, var))
    out = []
    for host in (D, C):
        for c1, f1, v1 in by.get((host, "Q1"), []):
            for c2, f2, v2 in by.get((host, "Q2"), []):
                synth = Variant(
                    key=f"J11[{f1.key}.{v1.key}+{f2.key}.{v2.key}]",
                    desc=f"J11 stack of Q1 '{f1.key}.{v1.key}' ({c1['candidate_id']}) and Q2 "
                    f"'{f2.key}.{v2.key}' ({c2['candidate_id']}) on host {host}; arms J00/J10/J01/J11",
                    hyp="Evidence gains (Q1) and acquisition gains (Q2) are complementary: J11 beats the best "
                    "single of J10/J01 with a favourable interaction I. Prior: GAVE-R found a NEGATIVE "
                    "interaction (FL-030), so sub-additivity is the null expectation.",
                    win="Cells where Q1 and Q2 each help alone and attack different cost components "
                    "(late detection vs late/wasted labels), e.g. markov05_shift_d10 under label_dear.",
                    fail="Cells where both improve the same component (diminishing returns, FL-030); "
                    "a shared label budget can make Q1 and Q2 compete.",
                    hooks={host: c2["hook"]},
                    nulls=(c1["target_null"],),
                    knobs=("interaction_design",),
                    cx=min(5, v1.cx + v2.cx),
                    questions=("Q3",),
                )
                qfam = Family(
                    key="q3_factorial_stack",
                    label="Q3 factorial integration",
                    questions=("Q3",),
                    prior_family="F10",
                    closest=("gongzhang2026", "drift2act2026", "cheng2023"),
                    failure_links=("FL-030", "FL-053"),
                    variants=(synth,),
                )
                for design in KNOBS["interaction_design"]:
                    ident = make_identity(
                        qfam, synth, host, "Q3", c1["target_null"], {"interaction_design": design}
                    )
                    ident["parent_id"] = c2["candidate_id"]
                    ident["parent_ids"] = [c1["candidate_id"], c2["candidate_id"]]
                    ident["required_baselines"] = list(
                        dict.fromkeys(
                            [*Q3_BASELINES, *c1["required_baselines"], *c2["required_baselines"]]
                        )
                    )
                    out.append(ident)
    return out


def build_registry() -> dict:
    """Generate, dedup, add Q3 factorial identities, score. Deterministic."""
    raw = generate_identities()
    kept, st1 = dedup(raw)
    q3 = _q3_factorial(kept)
    final, st2 = dedup(kept + q3)
    if len(final) > MAX_IDENTITIES:
        raise RuntimeError(f"{len(final)} identities exceeds hard cap {MAX_IDENTITIES}")
    for c in final:
        c["priority_score"], c["score_components"] = priority_score(c)
    final.sort(key=lambda c: c["candidate_id"])
    reasons = Counter(st1["reasons"]) + Counter(st2["reasons"])
    stats = {
        "raw_before_dedup": len(raw) + len(q3),
        "raw_q12_families": len(raw),
        "q3_factorial_generated": len(q3),
        "after_dedup": len(final),
        "duplicates_collapsed": len(raw) + len(q3) - len(final),
        "dedup_reasons": dict(reasons),
    }
    return {"identities": final, "stats": stats}


# ---------------------------------------------------------------- prioritisation
def priority_score(c: dict) -> tuple[float, dict]:
    var = None
    if c["family"] != "q3_factorial_stack":
        var = variant_of(family_by_key(c["family"]), c["variant"])
    links = set(c["failure_ledger_links"])
    comps = {
        "prior_art": RESIDUE_PRIOR_ART_SCORE
        if (var is not None and var.residue)
        else PRIOR_ART_SCORE[c["prior_art_status"]],
        "failure_link": 1.0 if links & SURVIVING_FAILURES else (0.5 if links else 0.0),
        "host_strength": HOST_STRENGTH[c["host"]],
        "simplicity": (6 - min(5, c["complexity"]["level"])) / 5.0,
        "null_eligibility": NULL_ELIGIBILITY[c["target_null"]],
    }
    score = sum(SCORE_WEIGHTS[k] * v for k, v in comps.items())
    if var is not None:
        default = canonical_config(
            var, c["host"], c["target_null"], {k: KNOBS[k][0] for k in var.knobs}
        )
        if default != c["canonical_configuration"]:
            score -= CONFIG_SPRAWL_PENALTY
            comps["config_sprawl_penalty"] = -CONFIG_SPRAWL_PENALTY
    return round(score, 6), comps


def select_batch(
    identities: list[dict], n: int = BATCH_SIZE, caps: dict | None = None
) -> list[dict]:
    """Deterministic diversity-constrained top-n of unblocked Q1/Q2 identities (Q3 is never selected)."""
    caps = {**BATCH_CAPS, **(caps or {})}
    pool = [c for c in identities if not c["blocked_by"] and not c["blocked_until"]]
    pool.sort(key=lambda c: (-c["priority_score"], c["candidate_id"]))
    chosen: list[dict] = []
    fam_n, var_n, vhn_n, host_n, q_n = Counter(), Counter(), Counter(), Counter(), Counter()
    abl = [0]
    ids: set[str] = set()

    def ok(c: dict, per_variant: int, per_family: int) -> bool:
        vk = (c["family"], c["variant"])
        return not (
            fam_n[c["family"]] >= per_family
            or var_n[vk] >= per_variant
            or vhn_n[(*vk, c["host"], c["target_null"])] >= caps["per_variant_host_null"]
            or host_n[c["host"]] >= caps["per_host"]
            or (c["role"] == "baseline_or_ablation_only" and abl[0] >= caps["ablation_only"])
            or (c["research_question"] == "Q1" and q_n["Q1"] >= caps["q1_max"])
        )

    def take(c: dict) -> None:
        chosen.append(c)
        ids.add(c["candidate_id"])
        fam_n[c["family"]] += 1
        var_n[(c["family"], c["variant"])] += 1
        vhn_n[(c["family"], c["variant"], c["host"], c["target_null"])] += 1
        host_n[c["host"]] += 1
        q_n[c["research_question"]] += 1
        abl[0] += c["role"] == "baseline_or_ablation_only"

    for fam in sorted({c["family"] for c in pool}):  # phase A: every family represented
        k = 0
        for c in pool:
            if k >= caps["min_per_family"]:
                break
            if (
                c["family"] == fam
                and c["candidate_id"] not in ids
                and ok(c, caps["per_variant"], caps["per_family"])
            ):
                take(c)
                k += 1
    for per_variant, per_family in (
        (caps["per_variant"], caps["per_family"]),
        (4, caps["per_family"]),
        (6, 14),
    ):
        for c in pool:  # phase B: fill by score, relaxing the per-variant cap only if needed
            if len(chosen) >= n:
                break
            if c["candidate_id"] not in ids and ok(c, per_variant, per_family):
                take(c)
    chosen = chosen[:n]
    if len(chosen) != n:
        raise RuntimeError(f"could only select {len(chosen)} of {n}")
    if q_n["Q1"] < caps["q1_min"]:
        raise RuntimeError("Q1 under-represented in Stage-B batch")
    chosen.sort(key=lambda c: (-c["priority_score"], c["candidate_id"]))
    return chosen
