"""Paper 1 EQSDp foundation: record loading restricted to the nine C4-supporting datasets.

Inputs are the gitignored record files of the main checkout (read only). Override the location
with the environment variable P1_RECORDS_ROOT.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

MAIN = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
RECORDS_ROOT = Path(
    os.environ.get("P1_RECORDS_ROOT", MAIN / "outputs/qsg_methods_search/sota_expansion")
)
RECORD_FILES = {
    "batch1_panel": RECORDS_ROOT / "nine/records.jsonl",
    "batch1_armR": RECORDS_ROOT / "nine_armR/records.jsonl",
    "batch2_panel_and_armR": RECORDS_ROOT / "batch2/records.jsonl",
}
ALL_TIER_CSV = RECORDS_ROOT / "all_tier_per_dataset.csv"

# Datasets supporting the registered C4 claim (docs/qsg_methods_search/c4_cumulative_b2.txt).
NINE = {
    "sf_311": ("City and County of San Francisco (DataSF / SF311)", 1),
    "kc_311": ("City of Kansas City, Missouri (311 Call Center / MyKCMO)", 1),
    "montgomery_traffic": ("Montgomery County, Maryland (Dept of Police / dataMontgomery)", 1),
    "dallas_311": ("City of Dallas (311 / dallasopendata.com)", 1),
    "dc_311": ("Government of the District of Columbia (DC 311 / DCGIS)", 1),
    "austin_311": ("City of Austin (Austin 311 Unified Data)", 2),
    "cincinnati_311": ("City of Cincinnati (311 Non-Emergency Service Requests)", 2),
    "oakland_311": ("City of Oakland (OAK 311 Call Center)", 2),
    "sandiego_311": ("City of San Diego (Get It Done)", 2),
}
DATASETS = list(NINE)

ARMS = {"B": "EQSDp_l0.9_g0.2", "R": "EQSDp_l0.98_g0.3"}
NEVER = "CONTROL_never_switch"
# Contract (c4_pilot.CFG): budget, label price cq, switch cost cs; horizon T per episode.
B_BUDGET, CQ, CS, T = 200, 0.05, 5.0, 2000

# Comparator taxonomy, copied from scripts/qsg_methods_search/analyze_all.py (ADAPTERS, CONTROLS)
# and 02_BASELINE_FIDELITY.md (certified rows). Certified methods are NOT COMPARABLE.
ADAPTERS = [
    "qiu_delayed_movement", "gong_zhang_paid_obs", "gongT_w100_m10", "gongT_w800_m20",
    "upf_d0.95_m50", "upf_d0.8_m50", "chalgse_l1.0_g0.2", "chalgse_l0.9_g0.3", "cams_adapter",
    "model_selector_causal", "model_picker_adapter", "online_llm_picker", "variance_min_ipw",
    "han_arw_label_clock",
]  # fmt: skip
CONTROLS = [
    "wald_l0.9_g0.2", "wald_l0.97_g0.2", "hoef_l0.9_g0.45", "hoef_l0.97_g0.3", "smarg_l0.9_k0.2",
    "smarg_l0.97_k0.2", "dwell_l0.9_s5", "dwell_l0.97_s3", "econF_mo5_m5", "econF_mo5_m0",
    "economic_replacement",
]  # fmt: skip
CERTIFIED = [
    "discern_style", "discern_style+QCE+front", "discern_design_floor", "discern_design_floor+front",
    "SMCS+retain-incumbent", "SMCS+QCE+front", "xu_acquisition_only", "xu+front_only",
    "gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front",
    "two_sided_esr_label_clock", "esr_rmmbets_fullalpha", "shekhar_ramdas_rcs_t3_anyexcl", "QSG",
]  # fmt: skip
UNCERTIFIED = ADAPTERS + CONTROLS


def policy_class(p: str) -> str:
    if p in ADAPTERS:
        return "adapter"
    if p in CONTROLS:
        return "control"
    if p in CERTIFIED:
        return "certified"
    if p == NEVER:
        return "reference"
    if p.startswith("EQSDp"):
        return "own"
    raise KeyError(p)


def load_records() -> pd.DataFrame:
    """Seed-level records for the nine datasets (deduplicated on stream, ep, seed, policy)."""
    frames = []
    for src, path in RECORD_FILES.items():
        d = pd.read_json(path, lines=True)
        d = d[d.stream.isin(DATASETS)].copy()
        d["source"] = src
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d = d.drop_duplicates(["stream", "ep", "seed", "policy"])
    return d.sort_values(["stream", "ep", "seed", "policy"]).reset_index(drop=True)


def episode_net(d: pd.DataFrame) -> pd.DataFrame:
    """Seed-mean net cost per (stream, ep) x policy, as in analyze_all.load."""
    return d.groupby(["stream", "ep", "policy"]).net.mean().unstack("policy")


def check_invariants(d: pd.DataFrame) -> dict:
    """Field-semantics checks used by 01_MEASURES.md; raises on violation."""
    out = {}
    out["max|net-(loss+cq*labels+cs*switches)|"] = float(
        (d.net - (d.loss + CQ * d.labels + CS * d.switches)).abs().max()
    )
    assert out["max|net-(loss+cq*labels+cs*switches)|"] < 1e-6
    out["max labels"] = int(d.labels.max())
    assert d.labels.max() <= B_BUDGET
    g = d.groupby(["stream", "ep"]).mean_gain.nunique().max()
    assert g == 1, "mean_gain must be an episode constant"
    out["max|mean_gain*T - round|"] = float(
        (d.mean_gain * T - (d.mean_gain * T).round()).abs().max()
    )
    nv = d[d.policy == NEVER]
    assert (nv.labels == 0).all() and (nv.switches == 0).all()
    assert (nv.net == nv.loss).all()
    sd = nv.groupby(["stream", "ep"]).net.nunique().max()
    assert sd == 1, "never-switch cost must be seed independent"
    nz = nv[nv.mean_gain != 0]
    out["never_switch frac_on_wrong == 1[gain>0]"] = bool(
        np.allclose(nz.frac_on_wrong, (nz.mean_gain > 0).astype(float))
    )
    assert out["never_switch frac_on_wrong == 1[gain>0]"]
    out["first_deploy range"] = (int(d.first_deploy.min()), int(d.first_deploy.max()))
    out["ever_promote == (first_deploy>=0)"] = bool(
        ((d.first_deploy >= 0).astype(int) == d.ever_promote).all()
    )
    assert out["ever_promote == (first_deploy>=0)"]
    return out


def provenance() -> str:
    """Markdown tables of file line counts and per-dataset episode/row counts (for 00_SCOPE.md)."""
    import hashlib

    lines = ["| source | path | lines | sha256 |", "|---|---|---|---|"]
    for k, p in RECORD_FILES.items():
        n = p.read_bytes().count(b"\n")
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(
            f"| {k} | `{p.relative_to(RECORDS_ROOT.parents[2]).as_posix()}` | {n} | `{h[:16]}...` |"
        )
    d = load_records()
    lines += [
        "",
        "| dataset | org | C4 batch | episodes | policies | seeds | rows used |",
        "|---|---|---|---|---|---|---|",
    ]
    for s, (org, b) in NINE.items():
        g = d[d.stream == s]
        lines.append(
            f"| {s} | {org} | {b} | {g.ep.nunique()} | {g.policy.nunique()} | {g.seed.nunique()} | {len(g)} |"
        )
    lines.append(f"\nTotal rows used: {len(d)}; distinct policies: {d.policy.nunique()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(provenance())
