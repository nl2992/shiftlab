"""WP6 host-port calibration audit: host-only runs on the frozen dev suite and on DEV_SUITE_v2 (no candidate is run).

* ``METHODS``: hosts under both profiles (native_v0 / calibrated_v1), the simple controls, episode_front and never-switch.
* ``run_cell``: paired run (one stream per seed, verify_run on every run) -> per-method per-seed records.
* ``compare``: paired-bootstrap dJ = J(host) - J(control) with 95% CI.
* ``ReachProbe``: read-only wrapper that records how often a hook's trigger condition is actually reached, WITHOUT acting.
* ``build_suite_v2`` / ``load_suite_v2``: DEV_SUITE_v2.json (new cells; DEV_SUITE.json and stream_families.yaml are never modified).

CLI: ``python -m shiftlab.autoresearch.host_audit frozen|v2|build-v2 [--out DIR]``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from shiftlab.bench.contract import (
    AlwaysContinue,
    BudgetSpec,
    ClockSpec,
    EnvSpec,
    load_cost_vectors,
    make_stream,
    paired_bootstrap_ci,
    run_paired,
)
from shiftlab.bench.contract.adapters_controls import CONTROLS
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy
from shiftlab.bench.contract.adapters_inrepo import ADAPTERS
from shiftlab.bench.contract.adapters_rar import BinaryPolicy, RARPolicy
from shiftlab.bench.contract.policies import BasePolicy
from shiftlab.bench.contract.streams import _spec_from_dict, load_family

from .dev_suite import DEV_SUITE

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "configs" / "d2a_rar"
SUITE_V2_PATH = REPO_ROOT / "docs" / "d2a_rar" / "registry" / "DEV_SUITE_v2.json"
FAMILIES_V2_PATH = CONFIG_DIR / "stream_families_v2.yaml"
OUT_DIR = REPO_ROOT / "results" / "d2a_rar" / "host_audit"
SEED_START_V1 = 110_000_000
SEED_START_V2 = 110_050_000  # inside the dev block 110_000_000-110_099_999, disjoint from v1 (cells * 1000 apart)
N_REP = 20

HOSTS = ("d2a_v0", "d2a_cal", "rar_v0", "rar_cal", "cab_v0", "cab_cal", "bin_v0", "bin_cal")
CONTROL_NAMES = ("uniform_query", "pending_cap", "fixed_schedule", "episode_front", "never_switch")


def _mk(name: str):
    return {
        "d2a_v0": lambda env: Drift2ActContractPolicy(),
        "d2a_cal": lambda env: Drift2ActContractPolicy(profile="calibrated_v1"),
        "rar_v0": lambda env: RARPolicy(),
        "rar_cal": lambda env: RARPolicy(profile="calibrated_v1"),
        "cab_v0": lambda env: BinaryPolicy(cost_aware=True),
        "cab_cal": lambda env: BinaryPolicy(cost_aware=True, profile="calibrated_v1"),
        "bin_v0": lambda env: BinaryPolicy(cost_aware=False),
        "bin_cal": lambda env: BinaryPolicy(cost_aware=False, profile="calibrated_v1"),
        "uniform_query": lambda env: CONTROLS["uniform_query"].build(env),
        "pending_cap": lambda env: CONTROLS["pending_cap"].build(env),
        "fixed_schedule": lambda env: CONTROLS["fixed_schedule"].build(env),
        "episode_front": lambda env: ADAPTERS["episode_front"].build(env),
        "never_switch": lambda env: AlwaysContinue(),
    }[name]


# ------------------------------------------------------------------------------------------ reach probe
class ReachProbe(BasePolicy):
    """Wraps a host policy and records the state it sees; never changes its actions (tested: identical J)."""

    def __init__(self, inner: BasePolicy) -> None:
        self.inner = inner
        self.name = getattr(inner, "name", "probe")

    def reset(self, env: EnvSpec) -> None:
        self.env = env
        self.inner.reset(env)
        self.delays: list[int] = []
        self._seen = 0
        self.rows: list[dict] = []

    def act(self, state):
        for lab in state.H[self._seen :]:
            self.delays.append(lab.release_t - lab.request_t)
        self._seen = len(state.H)
        out = self.inner.act(state)
        acts = [out] if not isinstance(out, (list, tuple)) else list(out)
        n_q = sum(1 for a in acts if a.kind == "query")
        rem = self.env.T - state.t
        if len(self.delays) >= 5:
            arr = np.asarray(self.delays)
            p_in = float((arr <= rem).mean())
        else:
            p_in = 1.0
        ages = [state.t - q.request_t for q in state.Q]
        self.rows.append(
            {
                "t": state.t,
                "n_query": n_q,
                "p_within_remaining": p_in,
                "pending": state.b.pending,
                "max_age": max(ages) if ages else 0,
                "n_released": len(state.H),
            }
        )
        return out

    def __getattr__(self, k):  # expose host internals (log, N, ...) read-only
        if k in ("inner", "rows", "delays", "env", "_seen"):
            raise AttributeError(k)
        return getattr(self.inner, k)


def reach_counters(probe: ReachProbe, res, stream, kind: str) -> dict:
    """Counters of how often hook trigger conditions are reached by a HOST-ONLY run (no candidate predicate is applied)."""
    inner = probe.inner
    rows = probe.rows
    T = stream.T
    q_rows = [r for r in rows if r["n_query"] > 0]
    c: dict = {
        "n_query_rounds": len(q_rows),
        # deadline / feasibility hook: query opportunities where the host's own observed delay law puts mass beyond the horizon
        "q_rounds_p_within_lt_1": sum(r["p_within_remaining"] < 1.0 for r in q_rows),
        "q_rounds_p_within_lt_0.9": sum(r["p_within_remaining"] < 0.9 for r in q_rows),
        "q_rounds_p_within_lt_0.5": sum(r["p_within_remaining"] < 0.5 for r in q_rows),
        # inventory-cap hook: pending mass
        "max_pending": max((r["pending"] for r in rows), default=0),
        "max_pending_age": max((r["max_age"] for r in rows), default=0),
        # evaluator-side: requested labels that are never usable before the horizon
        "labels_released_after_T": sum(
            1 for r in res.audit.of("request") if r.get("release_t") is None or r["release_t"] > T
        ),
        "labels_requested": len(res.audit.of("request")),
    }
    log = getattr(inner, "log", None) or []
    if kind == "d2a":
        c["cert_evaluations"] = sum(1 for e in log if e.get("n_cert", 0) > 0)
        c["gate_open_rounds"] = sum(1 for e in log if e.get("gate_ok"))
        c["abstain_rounds"] = int(res.counts.get("N_h", 0))
    if kind in ("rar", "bin"):
        ev = [e for e in log if isinstance(e, dict)]
        gates = [e for e in ev if e.get("event") == "gates"]
        c["detector_flags"] = sum(1 for e in ev if e.get("event") == "detector_flag")
        c["gate_evaluations"] = len(gates)
        c["gate2_passes"] = sum(1 for e in gates if e.get("g2"))
        c["gate3_passes"] = sum(1 for e in gates if e.get("g3"))
        c["max_labeled_in_window"] = max((e.get("win", 0) for e in gates), default=0)
        c["cost_gate_evaluations"] = sum(1 for e in ev if e.get("event") == "cost_gate")
        c["cost_gate_passes"] = sum(
            1 for e in ev if e.get("event") == "cost_gate" and e.get("passes")
        )
        c["retrains_issued"] = sum(1 for e in ev if e.get("event") == "retrain_issued")
        c["canary_commits"] = sum(1 for e in ev if e.get("event") == "commit")
        c["canary_rollback_events"] = sum(
            1 for e in ev if e.get("event") in ("stage1_abort", "stage2_fail")
        )
    # evaluator-side stream facts for reversal / hazard hooks
    reg = stream.truth.regime
    sw = int((np.diff(reg.astype(int)) != 0).sum())
    mp = res.model_path
    on_cand = mp == 1
    c["regime_switches"] = sw
    c["rounds_on_candidate"] = int(on_cand.sum())
    c["promoted_then_regime_left"] = bool(
        on_cand.any()
        and (reg[int(np.argmax(on_cand)) :] != 1).any()
        and (reg[int(np.argmax(on_cand)) :] == 1).any()
    )
    c["candidate_rounds_when_candidate_worse"] = int((on_cand & (stream.truth.gain_marg < 0)).sum())
    return c


def _kind(name: str) -> str:
    return {"d": "d2a", "r": "rar", "c": "bin", "b": "bin"}.get(name[0], "ctl")


# ------------------------------------------------------------------------------------------ running
def make_env(
    spec, cv: str, label_cap: int, max_lookback: int = 0, retrain_duration: int = 20
) -> EnvSpec:
    return EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()[cv],
        budget=BudgetSpec(label_cap=label_cap),
        clocks=ClockSpec(retrain_duration=retrain_duration, max_lookback=max_lookback),
    )


def run_cell(
    spec, env: EnvSpec, seeds: list[int], methods: tuple[str, ...], probe: bool = False
) -> dict[str, list[dict]]:
    """Paired run of ``methods`` on ``seeds``; returns {method: [per-seed record]} (verify_run inside run_paired)."""
    held: dict[str, list] = {m: [] for m in methods}

    def factory(m):
        def f():
            p = _mk(m)(env)
            if probe:
                p = ReachProbe(p)
            held[m].append(p)
            return p

        return f

    facs = {}
    for m in methods:
        facs[m] = factory(m)
    # policies are reset by the Simulator; adapters already reset once (idempotent)
    pr = run_paired(facs, spec, env, seeds, on_violation="raise", verify=True)
    out: dict[str, list[dict]] = {}
    for m in methods:
        recs = []
        for r, p in zip(pr.runs[m], held[m], strict=True):
            stream = make_stream(spec, r.seed)
            rec = {
                "seed": r.seed,
                "J": float(r.J),
                "breakdown": {k: float(v) for k, v in r.breakdown.items()},
                "counts": {k: int(v) for k, v in r.counts.items()},
                "promoted": bool((r.model_path == 1).any()),
            }
            if probe:
                rec["reach"] = reach_counters(p, r, stream, _kind(m))
            recs.append(rec)
        out[m] = recs
    return out


def mean_row(recs: list[dict]) -> dict:
    bd = {k: float(np.mean([r["breakdown"][k] for r in recs])) for k in recs[0]["breakdown"]}
    cn = {k: float(np.mean([r["counts"][k] for r in recs])) for k in recs[0]["counts"]}
    return {
        "J": bd["J"],
        "bd": bd,
        "counts": cn,
        "promoted": float(np.mean([r["promoted"] for r in recs])),
    }


def dJ(a: list[dict], b: list[dict]) -> tuple[float, float, float]:
    d = np.array([x["J"] - y["J"] for x, y in zip(a, b, strict=True)])
    return paired_bootstrap_ci(d)


def grade(rel: float) -> str:
    a = abs(rel)
    s = (
        "negligible"
        if a < 0.01
        else "small"
        if a < 0.03
        else "meaningful"
        if a < 0.10
        else "substantial"
    )
    return s


# ------------------------------------------------------------------------------------------ frozen suite
def frozen_cells() -> list[tuple[str, int, dict]]:
    out = []
    for q in ("Q1", "Q2"):
        for i, cell in enumerate(DEV_SUITE["cells"][q]):
            out.append((q, i, cell))
    return out


def run_frozen(methods: tuple[str, ...], cv_mode: str = "cell", probe: bool = False) -> dict:
    res: dict = {}
    for q, i, cell in frozen_cells():
        spec = load_family(cell["family"])
        cv = cell["cost_vector"] if cv_mode == "cell" else "intervention_dear"
        seeds = [SEED_START_V1 + i * 1000 + r for r in range(N_REP)]
        env = make_env(spec, cv, DEV_SUITE["workload"]["label_cap"])
        res[f"{q}[{i}]:{cell['family']}"] = {
            "cv": cv,
            "role": cell["role"],
            "runs": run_cell(spec, env, seeds, methods, probe=probe),
        }
    return res


# ------------------------------------------------------------------------------------------ DEV_SUITE_v2
def _f(**kw):
    return kw


FAMILIES_V2 = {
    # S1 tight deadline: heavy-tailed delay on a SHORT horizon (remaining horizon at onset ~ delay tail)
    "td_shift_lognormal_T400": _f(
        T=400,
        dependence="iid",
        onset_frac=0.35,
        duration_frac=1.0,
        delay=_f(kind="lognormal", median=80.0, sigma=1.0),
    ),
    "td_null_lognormal_T400": _f(
        T=400,
        dependence="iid",
        p_before=0.55,
        p_during=0.55,
        p_after=0.55,
        delay=_f(kind="lognormal", median=80.0, sigma=1.0),
    ),
    "td_null_fixed10_T400": _f(
        T=400,
        dependence="iid",
        p_before=0.55,
        p_during=0.55,
        p_after=0.55,
        delay=_f(kind="fixed", d=10),
    ),
    # S2b certifiable-risk cells (Drift2Act certificate can open: stable risk 0.30 <= tau - rad(n) for n >~ 160)
    "cert_null_p030": _f(
        dependence="iid", p_before=0.30, p_during=0.30, p_after=0.30, delay=_f(kind="fixed", d=10)
    ),
    "cert_null_p030_lognormal": _f(
        dependence="iid",
        p_before=0.30,
        p_during=0.30,
        p_after=0.30,
        delay=_f(kind="lognormal", median=15.0, sigma=1.0),
    ),
    # S3 reversal (FL-043 / F3_reversal_1200): candidate better in the middle third, harmful again after the reversal
    "reversal_1200": _f(
        T=1200,
        dependence="iid",
        onset_frac=0.25,
        duration_frac=0.35,
        p_before=0.25,
        p_during=0.9,
        p_after=0.25,
        delay=_f(kind="fixed", d=10),
    ),
    "reversal_null_1200": _f(
        T=1200,
        dependence="iid",
        p_before=0.55,
        p_during=0.55,
        p_after=0.55,
        delay=_f(kind="fixed", d=10),
    ),
    "reversal_persistent_1200": _f(
        T=1200,
        dependence="iid",
        onset_frac=0.25,
        duration_frac=1.0,
        p_before=0.25,
        p_during=0.9,
        delay=_f(kind="fixed", d=10),
    ),
    # S4 hazard / semi-Markov regime durations (Weibull sojourns; shape 2.5 = increasing hazard)
    "hazard_shift_k25": _f(
        dependence="iid",
        regime_process="semi_markov",
        hazard_shape=2.5,
        dur_before=250.0,
        dur_during=150.0,
        p_before=0.25,
        p_during=0.9,
        delay=_f(kind="fixed", d=10),
    ),
    "hazard_null_k25": _f(
        dependence="iid",
        regime_process="semi_markov",
        hazard_shape=2.5,
        dur_before=250.0,
        dur_during=150.0,
        p_before=0.55,
        p_during=0.55,
        p_after=0.55,
        delay=_f(kind="fixed", d=10),
    ),
    "hazard_shift_k10": _f(
        dependence="iid",
        regime_process="semi_markov",
        hazard_shape=1.0,
        dur_before=250.0,
        dur_during=150.0,
        p_before=0.25,
        p_during=0.9,
        delay=_f(kind="fixed", d=10),
    ),
}

# (id, scenario, role, family, source, cost_vector, label_cap, hook target, purpose)
CELLS_V2 = [
    ("S1a", "tight_deadline", "alternative", "td_shift_lognormal_T400", "v2", "label_dear", 50,
     "d2a/rar request-feasibility, deadline-priority, pending inventory",
     "T=400, lognormal delay (median 80, sigma 1): P(delay > remaining horizon) is large for requests after t~200"),
    ("S1b", "tight_deadline", "correct_null", "td_null_lognormal_T400", "v2", "label_dear", 50,
     "same", "boundary null with the same delay tail: tight-deadline mechanisms must not promote or over-spend"),
    ("S1c", "tight_deadline", "neighbouring_negative_control", "td_null_fixed10_T400", "v2", "label_dear", 50,
     "same", "boundary null with a SHORT delay tail: the feasibility/deadline predicate should (almost) never bind"),
    ("S2a", "rar_gate2_label_rich", "alternative", "iid_shift_d10", "v1", "intervention_dear", 1000,
     "rar.gate2/gate3, cab.gate (cap = T: labels as in RAR's native 'every label arrives')",
     "persistent shift, cap=T so Gate 2 (70% labelled in W_train) is reachable"),
    ("S2b", "rar_gate2_label_rich", "correct_null", "iid_null_boundary", "v1", "intervention_dear", 1000,
     "same", "boundary null with cap=T: gates must not fire retrains on noise"),
    ("S2c", "rar_gate2_label_rich", "neighbouring_negative_control", "iid_null_lognormal_delay", "v1", "intervention_dear", 1000,
     "same", "neighbouring null with a heavy-tailed delay law (labels lag the detector)"),
    ("S2d", "d2a_certifiable", "alternative", "iid_shift_d10", "v1", "label_dear", 300,
     "d2a certificate gate / request size / abstain economics",
     "persistent shift, cap=300: certificate opens (n >~ 100 at pre-shift risk 0.25) before/near onset"),
    ("S2e", "d2a_certifiable", "correct_null", "cert_null_p030", "v2", "label_dear", 300,
     "same", "all of cond/marg/abs-risk nulls hold (risk 0.30 <= tau 0.5): a certificate-gated host should stay open and quiet"),
    ("S2f", "d2a_certifiable", "neighbouring_negative_control", "cert_null_p030_lognormal", "v2", "label_dear", 300,
     "same", "same null with heavy-tailed delay"),
    ("S3a", "reversal", "alternative", "reversal_1200", "v2", "balanced", 60,
     "rollback / promote-then-revert economics (FL-043 F3_reversal_1200)",
     "T=1200: candidate better on [~300,~720), worse again after (p_after=0.25)"),
    ("S3b", "reversal", "correct_null", "reversal_null_1200", "v2", "balanced", 60,
     "same", "boundary null at T=1200: nothing to roll back"),
    ("S3c", "reversal", "neighbouring_negative_control", "reversal_persistent_1200", "v2", "balanced", 60,
     "same", "persistent-shift twin (no reversal): a rollback mechanism must not hurt here"),
    ("S4a", "hazard", "alternative", "hazard_shift_k25", "v2", "balanced", 50,
     "hazard-aware gating / regime-duration priors", "alternating regimes with increasing-hazard Weibull(2.5) sojourns"),
    ("S4b", "hazard", "correct_null", "hazard_null_k25", "v2", "balanced", 50,
     "same", "boundary null with the same regime clock (regimes are irrelevant to the gain)"),
    ("S4c", "hazard", "neighbouring_negative_control", "hazard_shift_k10", "v2", "balanced", 50,
     "same", "same means but flat hazard (shape 1): a hazard prior should not gain here"),
]  # fmt: skip


def families_v2_yaml() -> str:
    import yaml

    body = {k: dict(v) for k, v in FAMILIES_V2.items()}
    head = (
        "# DEV_SUITE_v2 stream families (WP6 host audit). NEW file: stream_families.yaml is not modified.\n"
        "# Families that already exist in stream_families.yaml are referenced from there (source: v1).\n"
        "# Generated by shiftlab.autoresearch.host_audit.build_suite_v2 (deterministic).\n"
    )
    return head + yaml.safe_dump({"version": 1, "families": body}, sort_keys=True)


def load_family_v2(name: str, source: str = "v2"):
    import yaml

    if source == "v1":
        return load_family(name)
    fams = yaml.safe_load(FAMILIES_V2_PATH.read_text(encoding="utf8"))["families"]
    return _spec_from_dict({"family": name, **fams[name]})


def build_suite_v2() -> dict:
    v1_sha = hashlib.sha256(
        (REPO_ROOT / "docs" / "d2a_rar" / "registry" / "DEV_SUITE.json").read_bytes()
    ).hexdigest()
    cells = []
    for idx, (cid, scen, role, fam, src, cv, cap, hook, purpose) in enumerate(CELLS_V2):
        if src == "v2":
            spec = _spec_from_dict({"family": fam, **FAMILIES_V2[fam]})
        else:
            spec = load_family(fam)
        tr = make_stream(spec, SEED_START_V2 + idx * 1000).truth
        cells.append(
            {
                "id": cid,
                "index": idx,
                "scenario": scen,
                "role": role,
                "family": fam,
                "family_source": src,
                "cost_vector": cv,
                "T": spec.T,
                "label_cap": cap,
                "max_lookback": 0,
                "retrain_duration": 20,
                "hook_target": hook,
                "purpose": purpose,
                "null_truth_expected": {
                    "cond": bool(tr.null_holds["cond"]),
                    "marg": bool(tr.null_holds["marg"]),
                    "abs_risk": bool(tr.null_holds["abs_risk"]),
                },
            }
        )
    return {
        "version": 2,
        "parent": {
            "file": "DEV_SUITE.json",
            "sha256": v1_sha,
            "note": "frozen cells are NOT modified; v2 adds cells",
        },
        "seed_block": "d2a_rar_dev (sub-block v2)",
        "seed_rule": f"seed = {SEED_START_V2} + cell_index*1000 + replicate, replicate in [0, {N_REP}); paired across methods",
        "seeds_per_cell": N_REP,
        "host_cost_vector_override": {},
        "note": "per-cell cost_vector/label_cap/T are authoritative (no host override in v2: every method on the cell vector)",
        "cells": cells,
    }


def load_suite_v2() -> dict:
    return json.loads(SUITE_V2_PATH.read_text(encoding="utf8"))


def run_v2(
    methods: tuple[str, ...], probe: bool = True, ids: tuple[str, ...] | None = None
) -> dict:
    suite = load_suite_v2()
    res = {}
    for c in suite["cells"]:
        if ids and c["id"] not in ids:
            continue
        spec = load_family_v2(c["family"], c["family_source"])
        env = make_env(
            spec, c["cost_vector"], c["label_cap"], c["max_lookback"], c["retrain_duration"]
        )
        seeds = [SEED_START_V2 + c["index"] * 1000 + r for r in range(N_REP)]
        res[c["id"]] = {"cell": c, "runs": run_cell(spec, env, seeds, methods, probe=probe)}
    return res


def _dump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True), encoding="utf8")


def main(argv: list[str]) -> int:
    cmd = argv[0]
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else OUT_DIR
    allm = HOSTS + CONTROL_NAMES
    if cmd == "build-v2":
        FAMILIES_V2_PATH.write_text(families_v2_yaml(), encoding="utf8")
        SUITE_V2_PATH.write_text(
            json.dumps(build_suite_v2(), indent=1, sort_keys=True) + "\n", encoding="utf8"
        )
        print("wrote v2 families + suite")
    elif cmd == "frozen":
        for mode in ("cell", "override"):
            _dump(run_frozen(allm, mode, probe=True), out / f"frozen_{mode}.json")
            print("done", mode, flush=True)
    elif cmd == "v2":
        _dump(run_v2(allm, probe=True), out / "v2_host_only.json")
        print("done v2")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
