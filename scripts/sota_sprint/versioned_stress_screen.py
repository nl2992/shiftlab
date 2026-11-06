"""Fresh-seed stress screen for version promotion and rollback.

This is development evidence only. It compares the original version gate with its opt-in
dual-monitor extension on frozen synthetic scenarios, and records queried-union paired gains.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (
    ROOT / "scripts/failure_atlas_v2_flq",
    ROOT / "scripts/promising_directions/sota",
    ROOT / "scripts/promising_directions/sota/competitors",
    HERE,
):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from bench import CONTRACT
from simulator import run_episode
from versioned_challenger import VersionIndexedGate

T = CONTRACT["T"]
B = CONTRACT["budget"]
DELAY = 24
UPDATE = 800
DEGRADE = 650
SCENARIOS = ("null", "late_better", "degrade", "recover")


class AuditedGate(VersionIndexedGate):
    """Gate that accumulates oriented pair gains on its actual queried union."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.union_gain = {}
        self.union_n = {}

    def observe(self, feedback):
        for fb in feedback:
            for kind, version, baseline in self.issued.get(fb.event_id, []):
                raw_gain = int(fb.model_losses[baseline]) - int(fb.model_losses[version])
                gain = raw_gain if kind == "promotion" else -raw_gain
                key = f"{kind}_v{version}"
                self.union_gain[key] = self.union_gain.get(key, 0) + gain
                self.union_n[key] = self.union_n.get(key, 0) + 1
        super().observe(feedback)


def sample_stream(seed: int, scenario: str):
    rng = np.random.default_rng(seed)
    labels = rng.binomial(1, 0.5, T).astype(np.int8)
    active = np.where(np.arange(T) < UPDATE, 1, 2).astype(np.int8)
    p0 = np.full(T, 0.40)
    p1 = np.full(T, 0.40)
    p2 = np.full(T, 0.40)
    if scenario == "late_better":
        p1[:] = 0.46
        p2[UPDATE:] = 0.25
    elif scenario in ("degrade", "recover"):
        p1[:DEGRADE] = 0.25
        p1[DEGRADE:] = 0.55
        if scenario == "recover":
            p2[UPDATE:] = 0.20
    elif scenario != "null":
        raise ValueError(scenario)
    err0 = rng.binomial(1, p0).astype(np.int8)
    err1 = rng.binomial(1, p1).astype(np.int8)
    err2 = err0.copy()
    err2[UPDATE:] = rng.binomial(1, p2[UPDATE:]).astype(np.int8)
    predictions = np.column_stack((labels ^ err0, labels ^ err1, labels ^ err2)).astype(np.int8)
    rates = {
        "incumbent": float(err0.mean()),
        "v1_before_degrade": float(err1[:DEGRADE].mean()),
        "v1_after_degrade": float(err1[DEGRADE:].mean()),
        "v2_post_update": float(err2[UPDATE:].mean()),
    }
    return predictions, labels, active, rates


def run_one(policy, predictions, labels, contexts):
    return run_episode(
        policy,
        model_predictions=predictions,
        labels=labels,
        contexts=contexts,
        delay=DELAY,
        budget=B,
        label_price=CONTRACT["cq"],
        switch_cost=CONTRACT["cs"],
        trace=True,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--seed-base", type=int, default=2026110401)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "records.jsonl"
    with dest.open("w", encoding="utf-8") as fh:
        for scenario_id, scenario in enumerate(SCENARIOS):
            for seed_id in range(args.seeds):
                seed = args.seed_base + 100_000 * scenario_id + seed_id
                predictions, labels, contexts, rates = sample_stream(seed, scenario)
                results = []
                for rollback in (False, True):
                    policy = AuditedGate(2, B, CONTRACT["alpha"], rollback_monitor=rollback)
                    result = run_one(policy, predictions, labels, contexts)
                    row = {
                        "scenario": scenario,
                        "seed": seed_id,
                        "policy": "dual_monitor" if rollback else "promotion_only",
                        "net": result.net_cost,
                        "loss": result.prediction_loss,
                        "labels": result.requested_labels,
                        "switches": result.deployment_switches,
                        "promotions": policy.promotions,
                        "rollbacks": policy.rollbacks,
                        "labels_by_version": policy.labels_by_version,
                        "queried_union_gain": policy.union_gain,
                        "queried_union_n": policy.union_n,
                        "true_error_rates": rates,
                    }
                    fh.write(json.dumps(row) + "\n")
                    results.append(row)
                print(f"{scenario}: seed {seed_id + 1}/{args.seeds}", end="\r", flush=True)
    print(f"\nWrote {args.seeds * len(SCENARIOS) * 2} rows to {dest}")


if __name__ == "__main__":
    main()
