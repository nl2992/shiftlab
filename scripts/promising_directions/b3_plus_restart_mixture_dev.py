"""Disjoint-seed development screen for the restart-mixture acquisition sentinel."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts" / "promising_directions"))
from b3_plus_cao_comparator import (
    BUDGET,
    CQ,
    CS,
    DELAY,
    SCENARIOS,
    TAU_REVERSAL,
    T,
    bootstrap_mean_ci,
    paired_stream,
)
from b3_plus_policy import PlusParams, b1, run_plus_policies

SEED_BASE = 21261108
METHODS = ("P7s", "P7s-RM", "Cao-L", "Cao-Hybrid")
ETA = 0.05
AUDIT_Q = 0.20


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_scenario(scenario: str, n: int):
    l0, l1, x, u = paired_stream(scenario, n, SEED_BASE)
    p = b1.Params(T=T, delay=DELAY, cq=CQ, alpha=0.05, pmin=0.05)
    params = [
        PlusParams(
            variant="P7s",
            acq_shape="settled",
            r_max=1.0,
            r_floor=0.25,
            settled_floor=0.0,
            persist_gamma=0.97,
        ),
        PlusParams(
            variant="P7s-RM",
            acq_shape="settled",
            r_max=1.0,
            r_floor=0.25,
            settled_floor=0.0,
            persist_gamma=0.97,
            acquisition="restart_mixture",
            restart_p0=0.30,
            restart_p1=0.70,
            restart_eta=ETA,
            audit_propensity=AUDIT_Q,
        ),
        PlusParams(variant="Cao-L", acquisition="label_history", lh_sleep=19),
        PlusParams(
            variant="Cao-Hybrid", acquisition="hybrid", lh_sleep=19, cov_block=25, cov_z=1.96
        ),
    ]
    out, objects = run_plus_policies(
        l0,
        l1,
        u,
        BUDGET,
        CS,
        CQ,
        p,
        params,
        trace=True,
        return_objs=True,
        covariates=x,
    )
    rows = {}
    threshold = 1.0 / ETA
    for name in METHODS:
        obj = objects[name]
        d = out[name]
        cost = d["loss"] + CQ * d["queries"] + CS * d["switches"]
        dep = np.asarray(obj.tr["dep"], dtype=np.int8)
        issued = np.asarray(obj.tr["ask"], dtype=np.int8)
        mix = np.asarray(obj.tr["restart_mix"], dtype=float)
        rolled_back = (dep[:-1] == 1) & (dep[1:] == 0)
        if scenario == "abrupt_reversal":
            at_risk = dep[TAU_REVERSAL] == 1
            delays = np.full(n, T - TAU_REVERSAL, dtype=float)
            delays[~at_risk] = 0.0
            rollback_after = np.zeros(n, dtype=bool)
            for j in np.flatnonzero(at_risk):
                after = np.flatnonzero(dep[TAU_REVERSAL + 1 :, j] == 0)
                if after.size:
                    delays[j] = float(after[0] + 1)
                    rollback_after[j] = True
            rmst = float(np.mean(delays[at_risk])) if at_risk.any() else None
            rollback_rate = float(rollback_after[at_risk].mean()) if at_risk.any() else 0.0
            false_wake = np.any(mix[:TAU_REVERSAL] >= threshold, axis=0)
        else:
            at_risk = np.zeros(n, dtype=bool)
            rmst = None
            rollback_rate = float(rolled_back.any(axis=0).mean())
            false_wake = np.any(mix >= threshold, axis=0)
        rows[name] = {
            "mean_cost": float(cost.mean()),
            "mean_loss": float(np.asarray(d["loss"]).mean()),
            "mean_labels": float(np.asarray(d["queries"]).mean()),
            "mean_labels_first_half": float(issued[: T // 2].sum(axis=0).mean()),
            "mean_labels_second_half": float(issued[T // 2 :].sum(axis=0).mean()),
            "mean_switches": float(np.asarray(d["switches"]).mean()),
            "rollback_probability": rollback_rate,
            "rollback_delay_rmst": rmst,
            "challenger_deployed_at_reversal": float(at_risk.mean())
            if scenario == "abrupt_reversal"
            else None,
            "false_wake_probability": float(false_wake.mean()) if name == "P7s-RM" else None,
            "cap_violations": int((np.asarray(d["queries"]) > BUDGET).sum()),
            "cost_by_seed": [float(v) for v in cost],
            "delay_by_seed": (
                [float(delays[j]) if at_risk[j] else None for j in range(n)]
                if scenario == "abrupt_reversal"
                else None
            ),
        }
    paired = {}
    for candidate in ("P7s-RM",):
        paired[candidate] = {}
        for control in ("P7s", "Cao-L", "Cao-Hybrid"):
            delta = np.asarray(rows[candidate]["cost_by_seed"]) - np.asarray(
                rows[control]["cost_by_seed"]
            )
            paired[candidate][control] = {
                "candidate_minus_control_mean": float(delta.mean()),
                "paired_bootstrap_95_ci": bootstrap_mean_ci(
                    delta, SEED_BASE + 29001 + METHODS.index(control)
                ),
                "candidate_lower_cost_fraction": float((delta < 0).mean()),
            }
    return {"methods": rows, "paired_cost": paired}


def main():
    n = 200
    destination = ROOT / "outputs" / "b3_plus_restart_mixture_dev"
    destination.mkdir(parents=True, exist_ok=True)
    report = {
        "phase": "disjoint development only",
        "seed_base": SEED_BASE,
        "n_seeds_per_scenario": n,
        "protocol": {
            "T": T,
            "budget": BUDGET,
            "delay": DELAY,
            "query_price": CQ,
            "switch_price": CS,
            "disagreement_probability": 0.30,
            "positive_advantage": 0.12,
            "reversal_at": TAU_REVERSAL,
            "eta": ETA,
            "audit_propensity": AUDIT_Q,
            "p0": 0.30,
            "p1": 0.70,
            "query_index_horizon": BUDGET,
            "cap_counts_at_issue": True,
            "existing_paired_eprocess_is_action_gate": True,
        },
        "scenarios": {},
        "provenance": {
            "utc": datetime.now(UTC).isoformat(),
            "python": sys.version,
            "platform": platform.platform(),
            "sha256": {
                str(Path(__file__).resolve()): sha256(Path(__file__).resolve()),
                str((HERE / "b3_plus_policy.py").resolve()): sha256(HERE / "b3_plus_policy.py"),
                str(
                    (
                        ROOT / "scripts" / "promising_directions" / "b3_plus_cao_comparator.py"
                    ).resolve()
                ): sha256(ROOT / "scripts" / "promising_directions" / "b3_plus_cao_comparator.py"),
            },
        },
    }
    for scenario in SCENARIOS:
        report["scenarios"][scenario] = run_scenario(scenario, n)
    path = destination / "dev.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    for scenario, result in report["scenarios"].items():
        brief = {
            name: {
                "cost": round(row["mean_cost"], 3),
                "labels": round(row["mean_labels"], 1),
                "rollback_probability": round(row["rollback_probability"], 3),
                "rollback_delay_rmst": row["rollback_delay_rmst"],
                "false_wake_probability": row["false_wake_probability"],
                "cap_violations": row["cap_violations"],
            }
            for name, row in result["methods"].items()
        }
        print(scenario, json.dumps(brief))
        print("paired cost:", json.dumps(result["paired_cost"]["P7s-RM"]))


if __name__ == "__main__":
    main()
