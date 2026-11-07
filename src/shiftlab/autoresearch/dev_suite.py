"""Frozen light dev suite for Stage B (definition only; running it is WP6).

Cells reference ``configs/d2a_rar/stream_families.yaml`` families and ``configs/d2a_rar/cost_vectors.yaml``
vectors. Negative/neighbouring controls live HERE (as cells), never as candidates. Do not edit once the
coordinator commits the checksum recorded by ``scripts/d2a_rar/build_candidate_registry.py``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

# expected null-truth flags per family (mirrors tests/d2a_rar/test_contract.py::test_null_truth_flags_by_family
# for the three families tested there; the rest follow from p_before/p_during/p_after and dependence).
_NULL = {
    "iid_null_boundary": {"cond": True, "marg": True},
    "iid_null_lognormal_delay": {"cond": True, "marg": True},
    "markov08_marg_null_only": {"cond": False, "marg": True},
    "iid_shift_d10": {"cond": False, "marg": False},
    "markov05_shift_d10": {"cond": False, "marg": False},
    "iid_shift_geo20": {"cond": False, "marg": False},
    "iid_shift_informative_missing": {"cond": False, "marg": False},
}


def _cell(role: str, family: str, cost_vector: str, purpose: str) -> dict:
    return {
        "role": role,
        "family": family,
        "cost_vector": cost_vector,
        "null_truth_expected": _NULL[family],
        "purpose": purpose,
    }


DEV_SUITE: dict = {
    "version": 1,
    "timeout_s_per_experiment": 300,
    "seed_block": "d2a_rar_dev",
    "seeds_per_cell": 20,
    "seed_rule": "seed = block.start + cell_index*1000 + replicate, cell_index = position in the question's "
    "cell list, replicate in [0, seeds_per_cell); paired across all methods in the batch",
    "workload": {
        "T": "family default (1000)",
        "label_cap": 50,
        "retrain_duration": 20,
        "pairing": "run_paired",
    },
    "host_cost_vector_override": {
        "rar": "intervention_dear",
        "cost_aware_binary": "intervention_dear",
    },
    "cells": {
        "Q1": [
            _cell(
                "correct_null",
                "iid_null_boundary",
                "balanced",
                "cond and marg nulls both hold: false-promotion cell",
            ),
            _cell(
                "adverse_dependence_stress",
                "markov08_marg_null_only",
                "balanced",
                "marg null holds, cond fails: validity cell for marg methods; out-of-contract stress for cond methods",
            ),
            _cell(
                "alternative",
                "markov05_shift_d10",
                "balanced",
                "persistent shift with serial dependence: power/delay",
            ),
            _cell(
                "neighbouring_negative_control",
                "iid_null_lognormal_delay",
                "balanced",
                "neighbouring null with a different delay law: must not promote",
            ),
        ],
        "Q2": [
            _cell(
                "correct_null",
                "iid_null_boundary",
                "label_dear",
                "false-promotion cell with expensive labels",
            ),
            _cell(
                "adverse_sampling_stress",
                "iid_shift_informative_missing",
                "label_dear",
                "informative missingness: selective feedback stress on acquisition",
            ),
            _cell(
                "alternative",
                "iid_shift_geo20",
                "label_dear",
                "long right-tailed delay: pending/deadline value",
            ),
            _cell(
                "neighbouring_negative_control",
                "iid_null_lognormal_delay",
                "label_dear",
                "neighbouring null with heavy-tailed delay: must not promote or over-spend",
            ),
        ],
    },
    "TODO_for_coordinator": [
        "No reversal stream family (F9 rollback / FL-043 F3_reversal_1200 not in stream_families.yaml).",
        "No hazard / semi-Markov regime-duration family (hazard_regime_duration, reversal_hazard_rollback).",
        "No subgroup-shift family (subgroup_safety).",
        "No proxy/side-information stream or ObservableState proxy predictions (surrogate families; WP2c open).",
        (
            "No tight-deadline family with a hard promotion window shorter than the delay tail (deadline_aware_querying "
            "uses iid_shift_geo20 as the nearest proxy)."
        ),
        (
            "No RAR-native persistent-drift family with label-frontier semantics (Suite A is separate); canary "
            "candidates run on the contract route() split only."
        ),
        (
            "Informative gap choice (observation mechanism carrying information) is only approximated by "
            "iid_shift_informative_missing."
        ),
    ],
}


def suite_sha256(suite: dict | None = None) -> str:
    return hashlib.sha256(
        json.dumps(suite or DEV_SUITE, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def referenced(suite: dict | None = None) -> tuple[set[str], set[str]]:
    s = suite or DEV_SUITE
    fams, vecs = set(), set(s["host_cost_vector_override"].values())
    for cells in s["cells"].values():
        for c in cells:
            fams.add(c["family"])
            vecs.add(c["cost_vector"])
    return fams, vecs


def missing_references(suite: dict | None = None, root: Path = REPO_ROOT) -> dict[str, list[str]]:
    fams, vecs = referenced(suite)
    sf = yaml.safe_load(
        (root / "configs/d2a_rar/stream_families.yaml").read_text(encoding="utf-8")
    )["families"]
    cv = yaml.safe_load((root / "configs/d2a_rar/cost_vectors.yaml").read_text(encoding="utf-8"))[
        "vectors"
    ]
    return {"families": sorted(fams - set(sf)), "cost_vectors": sorted(vecs - set(cv))}


def cells_for(question: str, target_null: str) -> dict:
    """Validity plan: which cells score false promotion for ``target_null`` and which are labelled stress only.

    ``abs_risk`` truth is stream/tau dependent and is read from ``truth.null_holds['abs_risk']`` at run time.
    """
    key = "Q1" if question == "Q1" else "Q2"
    plan: dict = {
        "validity_cells": [],
        "out_of_contract_stress": [],
        "power_cells": [],
        "controls": [],
    }
    for c in DEV_SUITE["cells"][key]:
        t = c["null_truth_expected"]
        entry = f"{c['role']}:{c['family']}"
        if c["role"] == "neighbouring_negative_control":
            plan["controls"].append(entry)
        if target_null in ("cond", "marg") and t[target_null]:
            plan["validity_cells"].append(entry)
        elif target_null in ("cond", "marg") and any(t.values()):
            plan["out_of_contract_stress"].append(entry)
        elif target_null == "absolute_risk":
            plan["validity_cells"].append(entry + " (abs_risk truth read at run time)")
        if not any(t.values()):
            plan["power_cells"].append(entry)
    return plan
