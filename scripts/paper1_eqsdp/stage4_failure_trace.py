"""Replay the frozen Paper-1 Stage-3 failure episodes (development diagnostics only).

Install this file as scripts/paper1_eqsdp/stage4_failure_trace.py in the ShiftLab
checkout and run:
    python scripts/paper1_eqsdp/stage4_failure_trace.py

Uses the original sealed, checksum-verified datasets through trace_run.sealed_paths,
with the exact seeds and policy construction used in Stage 3. Does NOT modify any
policy, select a new candidate, or open Stage-4 holdout data.
"""

# ruff: noqa: B023  (instrumented_keep is called only within its own loop iteration)
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import stage2_policies as sp2
import trace_run as tr


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def replay_one(
    dataset: str, ep: int, seed: int, location: str, delay: int, seed_base: int, candidate_cfg: dict
):
    import c4_pilot
    from suite import build_suite, run_episode, stream_from_losses

    z = np.load(location)
    if not 0 <= ep < z["l0"].shape[0]:
        raise ValueError(f"episode index {ep} outside {dataset} ({z['l0'].shape[0]} total)")
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    T = int(losses.shape[0])
    b, cq, cs = 200, 0.05, 5.0
    assert c4_pilot.CFG["cq"] == cq and c4_pilot.CFG["cs"] == cs
    hash32 = int.from_bytes(hashlib.sha256(dataset.encode()).digest()[:4], "big")
    rng = np.random.default_rng([seed_base, hash32, ep, seed, 7])
    predictions, truth = stream_from_losses(losses, rng)

    sp2.DYN["s3_candidate"] = sp2.stage2_factory(candidate_cfg, "s3_candidate")
    registry = tr.registry()
    names = ("s3_candidate", "s2armr_H1100")
    results = {}
    gate_records = {}
    for name in names:
        policies = build_suite(
            T,
            b,
            cs,
            cq,
            c4_pilot.CFG["alpha"],
            delay,
            ep * 100_000 + seed,
            seed_base + hash32 % 1000,
            names=[name],
            extra=registry,
        )
        (policy,) = policies
        if name == "s3_candidate":
            raw_keep = policy.keep

            def instrumented_keep(event, remaining_budget):
                # The first p_cross evaluation is purely functional: no random draw,
                # no mutations. The original keep() is called exactly once below.
                p_cross = float(policy.p_cross(event.t))
                virtual = max(float(policy.virtual_remaining(remaining_budget)), 1.0)
                expected = policy._rate() * (T - event.t)
                pressure = min(max(expected / virtual - 1.0, 0.0), 10.0)
                rho_eff = float(policy.rho0 * (1.0 + policy.s * pressure))
                n_before = float(policy.n)
                skipped_before = int(policy.skipped)
                answer = raw_keep(event, remaining_budget)
                gate_records[event.t] = {
                    "p_cross": p_cross,
                    "rho_eff": rho_eff,
                    "virtual_budget": virtual,
                    "expected_remaining_disagreements": expected,
                    "posterior_n": n_before,
                    "skipped_before": skipped_before,
                    "kept_after_gate": int(answer),
                }
                return answer

            policy.keep = instrumented_keep
        result = run_episode(
            policy,
            model_predictions=predictions,
            labels=truth,
            delay=delay,
            budget=b,
            label_price=cq,
            switch_cost=cs,
            trace=True,
        )
        results[name] = result
        charged = sum(
            x["prediction_loss"] + x["query_cost"] + x["switch_cost"] for x in result.records
        )
        assert abs(result.net_cost - charged) < 1e-8, (name, result.net_cost, charged)
        assert result.requested_labels <= b

    cand, ref = (results[n] for n in names)
    s = {
        "dataset": dataset,
        "episode": ep,
        "seed": seed,
        "candidate_net": cand.net_cost,
        "reference_net": ref.net_cost,
        "delta_net": cand.net_cost - ref.net_cost,
        "candidate_loss": cand.prediction_loss,
        "reference_loss": ref.prediction_loss,
        "delta_loss": cand.prediction_loss - ref.prediction_loss,
        "candidate_labels": cand.requested_labels,
        "reference_labels": ref.requested_labels,
        "candidate_switches": cand.deployment_switches,
        "reference_switches": ref.deployment_switches,
    }
    for nm, res in [("candidate", cand), ("reference", ref)]:
        seen = [r["event_id"] for r in res.records if r["deployed_model"] == 1]
        s[nm + "_first_model1"] = min(seen) if seen else -1
        s[nm + "_pre800_queries"] = sum(r["requested"] for r in res.records[:801])
        s[nm + "_post800_queries"] = sum(r["requested"] for r in res.records[801:])

    cumulative = 0.0
    timeline = []
    for c, r in zip(cand.records, ref.records):
        assert c["event_id"] == r["event_id"]
        t = c["event_id"]
        delta_loss = c["prediction_loss"] - r["prediction_loss"]
        delta_fee = c["query_cost"] - r["query_cost"]
        delta_switch_cost = c["switch_cost"] - r["switch_cost"]
        cumulative += delta_loss + delta_fee + delta_switch_cost
        row = {
            "dataset": dataset,
            "episode": ep,
            "seed": seed,
            "t": t,
            "candidate_deployed": c["deployed_model"],
            "reference_deployed": r["deployed_model"],
            "candidate_requested": c["requested"],
            "reference_requested": r["requested"],
            "candidate_release_t": c["release_time"],
            "reference_release_t": r["release_time"],
            "delta_loss": delta_loss,
            "delta_query_fee": delta_fee,
            "delta_switch_cost": delta_switch_cost,
            "cumulative_delta_net": cumulative,
            "candidate_state": c["decision_state"],
            "reference_state": r["decision_state"],
        }
        row.update(gate_records.get(t, {}))
        timeline.append(row)
    assert abs(cumulative - s["delta_net"]) < 1e-8
    return s, timeline


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="kc_311")
    ap.add_argument("--episodes", nargs="+", type=int, default=[37, 39])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/paper1_eqsdp/stage3_failure_trace")
    args = ap.parse_args()
    freeze = json.loads((ROOT / "docs/paper1_eqsdp/stage2_frozen_config.json").read_text())
    assert freeze["new_reference"] == "s2armr_H1100"
    loc = tr.sealed_paths()  # verifies the registered array-content checksum
    if args.dataset not in loc:
        raise SystemExit(f"Dataset not among the checksum-verified nine: {args.dataset}")
    filepath, delay, sb = loc[args.dataset]
    summaries, worst = [], {}
    for ep in args.episodes:
        trials = [
            replay_one(args.dataset, ep, s, filepath, delay, sb, freeze["candidate_cfg"])
            for s in range(args.seeds)
        ]
        for summary, _ in trials:
            summaries.append(summary)
        worst_s, worst_t = max(trials, key=lambda v: v[0]["delta_net"])
        worst[ep] = worst_s
        write_csv(args.out / f"{args.dataset}_ep{ep}_worst_seed_trace.csv", worst_t)
    write_csv(args.out / f"{args.dataset}_episode_seed_summary.csv", summaries)
    for ep in args.episodes:
        vals = [r for r in summaries if r["episode"] == ep]
        print(
            f"episode {ep}: mean delta J={np.mean([r['delta_net'] for r in vals]):+.3f}; "
            f"worst seed={worst[ep]['seed']} with delta J={worst[ep]['delta_net']:+.3f}"
        )
    print("Evaluator-side diagnostic only, not confirmation. Output:", ascii(str(args.out)))


if __name__ == "__main__":
    main()
