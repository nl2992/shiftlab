"""Regenerates q1_host_golden.json from the Drift2Act contract host.  Run ONLY against a host known to be unmodified
(the committed golden was produced at cc867f40-era host code BEFORE the Q1 outcome-evidence seam was added)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from shiftlab.bench.contract import (
    BudgetSpec,
    ClockSpec,
    DelaySpec,
    EnvSpec,
    StreamSpec,
    load_cost_vectors,
    run_paired,
)
from shiftlab.bench.contract.adapters_drift2act import Drift2ActContractPolicy

SEEDS = (110_900_000, 110_900_001)
T = 300


def fingerprint(profile: str, delay: DelaySpec) -> dict:
    spec = StreamSpec(family="q1_golden", T=T, dependence="markov", rho=0.5, delay=delay, tau=0.5)
    env = EnvSpec(
        T=T,
        costs=load_cost_vectors()["balanced"],
        budget=BudgetSpec(label_cap=60),
        clocks=ClockSpec(retrain_duration=20, max_lookback=100),
    )

    def build():
        p = Drift2ActContractPolicy(profile=profile)
        p.reset(env)
        return p

    pr = run_paired({"d2a": build}, spec, env, seeds=SEEDS)
    out = []
    for r in pr.runs["d2a"]:
        out.append(
            {
                "seed": r.seed,
                "J": repr(r.J),
                "counts": r.counts,
                "audit_sha256": hashlib.sha256(r.audit.to_jsonl().encode()).hexdigest(),
            }
        )
    return {"profile": profile, "delay": delay.kind, "runs": out}


def make() -> list[dict]:
    return [
        fingerprint(p, d)
        for p in ("native_v0", "calibrated_v1")
        for d in (DelaySpec("fixed", d=10), DelaySpec("uniform", lo=1, hi=30))
    ]


if __name__ == "__main__":
    Path(__file__).with_name("q1_host_golden.json").write_text(json.dumps(make(), indent=1))
