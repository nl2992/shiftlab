"""Development screen for sequentially activated challenger versions.

The synthetic stream has a worse first challenger, then a candidate version that improves (or is
null) at a fixed predeclared update time. All policies receive the same labels and predictions.
Existing two-model gates see the incumbent and the currently available challenger in a single
replaceable model slot; Model Picker sees all three model slots, with the future candidate copied
from the incumbent until activation. This is development evidence only.

Example:
    uv run python scripts/sota_sprint/versioned_screen.py --seeds 50 --out outputs/sota_sprint/versioned_dev
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
from registry import EXTRA
from simulator import run_episode
from suite import build_suite
from versioned_challenger import VersionAwareModelPicker, VersionIndexedGate

T = CONTRACT["T"]
B = CONTRACT["budget"]
DELAY = 24
UPDATE = 800
POLICIES = [
    "rmm:gated_adaptive_range+RMM",
    "gated_adaptive_range+front",
    "choe_ramdas_eb+front",
    "A5b",
    "CONTROL_never_switch",
]


def sample_stream(
    seed: int, scenario: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (3-model predictions, labels, active candidate version, true error rates)."""
    rng = np.random.default_rng(seed)
    labels = rng.binomial(1, 0.5, T).astype(np.int8)
    times = np.arange(T)
    active = np.where(times < UPDATE, 1, 2).astype(np.int8)

    err0 = rng.binomial(1, 0.40, T).astype(np.int8)
    if scenario == "late_better":
        p1 = np.full(T, 0.46)
        p2 = np.full(T, 0.25)
    elif scenario == "null":
        p1 = np.full(T, 0.40)
        p2 = np.full(T, 0.40)
    else:
        raise ValueError(scenario)
    err1 = rng.binomial(1, p1).astype(np.int8)
    err2 = err0.copy()  # future model is unavailable before its activation
    err2[UPDATE:] = rng.binomial(1, p2[UPDATE:]).astype(np.int8)
    preds = np.column_stack((labels ^ err0, labels ^ err1, labels ^ err2)).astype(np.int8)
    true_rates = np.array([err0.mean(), err1.mean(), err2[UPDATE:].mean()])
    return preds, labels, active, true_rates


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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=50)
    ap.add_argument("--seed-base", type=int, default=2026110906)
    ap.add_argument(
        "--scenarios", default="late_better,null", help="comma-separated subset of late_better,null"
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    records = out / "records.jsonl"
    with records.open("w", encoding="utf-8") as fh:
        scenarios = [s for s in args.scenarios.split(",") if s]
        if not scenarios or any(s not in ("late_better", "null") for s in scenarios):
            raise SystemExit("--scenarios must be a nonempty subset of late_better,null")
        for scenario_id, scenario in enumerate(scenarios):
            for seed in range(args.seeds):
                stream_seed = args.seed_base + 10_000 * scenario_id + seed
                predictions, labels, contexts, true_rates = sample_stream(stream_seed, scenario)
                run_ep = scenario_id * 100_000 + seed
                pair_predictions = predictions[:, [0, 1]].copy()
                pair_predictions[UPDATE:, 1] = predictions[UPDATE:, 2]

                policies = build_suite(
                    T,
                    B,
                    CONTRACT["cs"],
                    CONTRACT["cq"],
                    CONTRACT["alpha"],
                    DELAY,
                    run_ep,
                    args.seed_base,
                    names=POLICIES,
                    extra=EXTRA,
                )
                for policy in policies:
                    result = run_one(policy, pair_predictions, labels, contexts)
                    fh.write(
                        json.dumps(
                            {
                                "scenario": scenario,
                                "seed": seed,
                                "policy": policy.name,
                                "net": result.net_cost,
                                "loss": result.prediction_loss,
                                "labels": result.requested_labels,
                                "switches": result.deployment_switches,
                                "ever_promote": int(
                                    any(r["deployed_model"] == 1 for r in result.records)
                                ),
                                "mean_error_incumbent": float(true_rates[0]),
                                "mean_error_v1": float(true_rates[1]),
                                "mean_error_v2_post_update": float(true_rates[2]),
                            }
                        )
                        + "\n"
                    )

                rng = np.random.default_rng([args.seed_base, run_ep, 101])
                version_gate = VersionIndexedGate(2, B, CONTRACT["alpha"])
                result = run_one(version_gate, predictions, labels, contexts)
                fh.write(
                    json.dumps(
                        {
                            "scenario": scenario,
                            "seed": seed,
                            "policy": version_gate.name,
                            "net": result.net_cost,
                            "loss": result.prediction_loss,
                            "labels": result.requested_labels,
                            "switches": result.deployment_switches,
                            "ever_promote": int(bool(version_gate.promotions)),
                            "promotions": version_gate.promotions,
                            "labels_by_version": version_gate.labels_by_version,
                            "mean_error_incumbent": float(true_rates[0]),
                            "mean_error_v1": float(true_rates[1]),
                            "mean_error_v2_post_update": float(true_rates[2]),
                        }
                    )
                    + "\n"
                )

                # Published active selection baseline, with the future model hidden as an
                # incumbent copy until its predeclared activation.
                mp_policy = VersionAwareModelPicker(2, rng)
                result = run_one(mp_policy, predictions, labels, contexts)
                fh.write(
                    json.dumps(
                        {
                            "scenario": scenario,
                            "seed": seed,
                            "policy": mp_policy.name,
                            "net": result.net_cost,
                            "loss": result.prediction_loss,
                            "labels": result.requested_labels,
                            "switches": result.deployment_switches,
                            "ever_promote": int(
                                any(r["deployed_model"] > 0 for r in result.records)
                            ),
                            "mean_error_incumbent": float(true_rates[0]),
                            "mean_error_v1": float(true_rates[1]),
                            "mean_error_v2_post_update": float(true_rates[2]),
                        }
                    )
                    + "\n"
                )
                print(f"{scenario}: seed {seed + 1}/{args.seeds}", end="\r", flush=True)
    print(f"\nWrote {args.seeds * 2 * (len(POLICIES) + 2)} rows to {records}")


if __name__ == "__main__":
    main()
