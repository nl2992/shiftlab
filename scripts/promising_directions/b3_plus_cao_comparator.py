"""Matched synthetic comparison of P3b/P7s with Cao-style acquisition adapters.

The evidence process and action thresholds are the existing B3+ paired e-process. Only the
acquisition controller varies. This is a model-based development study, not a reproduction of
Cao's risk-monitoring theorem or a real-data result.
"""

from __future__ import annotations

import argparse
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
from b3_plus_policy import PlusParams, b1, run_plus_policies

T = 2000
BUDGET = 200
DELAY = 50
CS = 5.0
CQ = 0.05
DISAGREEMENT = 0.30
MU = 0.12
TAU_REVERSAL = 1000
TAU_BENIGN_SHIFT = 900
SEED_DEV = 20261108
METHODS = ("P3b", "P7s", "P7s-sentinel", "P7s-evidence", "P7s-ecusum", "Cao-L", "Cao-Hybrid")
SCENARIOS = ("stationary_positive", "abrupt_reversal", "benign_covariate_shift")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_episode(scenario: str, seed: int):
    rng = np.random.default_rng(np.random.SeedSequence([seed, SCENARIOS.index(scenario)]))
    x = rng.normal(size=T)
    mu = np.full(T, MU)
    if scenario == "abrupt_reversal":
        mu[TAU_REVERSAL:] = -MU
    elif scenario == "benign_covariate_shift":
        x[TAU_BENIGN_SHIFT:] += 0.8
    elif scenario != "stationary_positive":
        raise ValueError(scenario)
    u_loss = rng.random(T)
    p_pos = (DISAGREEMENT + mu) / 2
    p_neg = (DISAGREEMENT - mu) / 2
    pos = u_loss < p_pos
    neg = (u_loss >= p_pos) & (u_loss < p_pos + p_neg)
    d0 = np.where(pos, 1, np.where(neg, -1, 0)).astype(np.int8)
    l0 = (d0 == 1).astype(np.int8)
    l1 = (d0 == -1).astype(np.int8)
    return l0, l1, x.astype(np.float64)


def paired_stream(scenario: str, n: int, seed_base: int):
    l0 = np.empty((T, n), dtype=np.int8)
    l1 = np.empty((T, n), dtype=np.int8)
    x = np.empty((T, n), dtype=np.float64)
    u = np.empty((T, n), dtype=np.float64)
    for j in range(n):
        episode_seed = seed_base + j
        a0, a1, cov = make_episode(scenario, episode_seed)
        l0[:, j], l1[:, j], x[:, j] = a0, a1, cov
        u[:, j] = np.random.default_rng(
            np.random.SeedSequence([seed_base, SCENARIOS.index(scenario), j, 991])
        ).random(T)
    return l0, l1, x, u


def bootstrap_mean_ci(values: np.ndarray, seed: int, draws: int = 4000):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(draws, len(values)))
    means = values[idx].mean(axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def run_scenario(
    scenario: str,
    n: int,
    seed_base: int,
    p7_gamma: float,
    settled_floor: float,
    sentinel_log_threshold: float,
):
    l0, l1, x, u = paired_stream(scenario, n, seed_base)
    p = b1.Params(T=T, delay=DELAY, cq=CQ, alpha=0.05, pmin=0.05)
    params = [
        PlusParams(variant="P3b"),
        PlusParams(
            variant="P7s",
            acq_shape="settled",
            r_max=1.0,
            r_floor=0.25,
            settled_floor=settled_floor,
            persist_gamma=p7_gamma,
        ),
        PlusParams(
            variant="P7s-sentinel",
            acq_shape="settled",
            r_max=1.0,
            r_floor=0.25,
            settled_floor=settled_floor,
            persist_gamma=p7_gamma,
            acquisition="settled_sentinel",
            lh_sleep=19,
        ),
        PlusParams(
            variant="P7s-evidence",
            acq_shape="settled",
            r_max=1.0,
            r_floor=0.25,
            settled_floor=settled_floor,
            persist_gamma=p7_gamma,
            acquisition="evidence_sentinel",
            sentinel_log_threshold=sentinel_log_threshold,
        ),
        PlusParams(
            variant="P7s-ecusum",
            acq_shape="settled",
            r_max=1.0,
            r_floor=0.25,
            settled_floor=settled_floor,
            persist_gamma=p7_gamma,
            acquisition="ecusum",
            sentinel_log_threshold=sentinel_log_threshold,
        ),
        PlusParams(
            variant="Cao-L",
            acquisition="label_history",
            lh_sleep=19,
        ),
        PlusParams(
            variant="Cao-Hybrid",
            acquisition="hybrid",
            lh_sleep=19,
            cov_block=25,
            cov_z=1.96,
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
        covariates=x,
        trace=True,
        return_objs=True,
    )
    if set(out) != set(METHODS):
        raise RuntimeError(f"unexpected methods returned: {sorted(out)}")
    rows = {}
    for name in METHODS:
        d = out[name]
        cost = d["loss"] + CQ * d["queries"] + CS * d["switches"]
        cap = np.asarray(d["queries"]) > BUDGET
        dep = np.asarray(objects[name].tr["dep"], dtype=np.int8)
        issued = np.asarray(objects[name].tr["ask"], dtype=np.int8)
        rolled_back = (dep[:-1] == 1) & (dep[1:] == 0)
        if scenario == "abrupt_reversal":
            at_risk = dep[TAU_REVERSAL] == 1
            delay = np.full(n, T - TAU_REVERSAL, dtype=float)
            delay[~at_risk] = 0.0
            rollback_after = np.zeros(n, dtype=bool)
            for j in np.flatnonzero(at_risk):
                after = np.flatnonzero(dep[TAU_REVERSAL + 1 :, j] == 0)
                if after.size:
                    delay[j] = float(after[0] + 1)
                    rollback_after[j] = True
            rmst = float(np.mean(delay[at_risk])) if at_risk.any() else None
            rollback_rate = float(rollback_after[at_risk].mean()) if at_risk.any() else 0.0
            prechange_rollback_rate = float(
                rolled_back[: max(TAU_REVERSAL - 1, 0)].any(axis=0).mean()
            )
            at_risk_rate = float(at_risk.mean())
        else:
            rmst = None
            rollback_rate = float(rolled_back.any(axis=0).mean())
            prechange_rollback_rate = None
            at_risk_rate = None
        rows[name] = {
            "mean_cost": float(cost.mean()),
            "mean_loss": float(np.asarray(d["loss"]).mean()),
            "mean_labels": float(np.asarray(d["queries"]).mean()),
            "mean_labels_first_half": float(issued[: T // 2].sum(axis=0).mean()),
            "mean_labels_second_half": float(issued[T // 2 :].sum(axis=0).mean()),
            "mean_switches": float(np.asarray(d["switches"]).mean()),
            "rollback_probability": rollback_rate,
            "rollback_delay_rmst": rmst,
            "challenger_deployed_at_reversal": at_risk_rate,
            "prechange_rollback_probability": prechange_rollback_rate,
            "cap_violations": int(cap.sum()),
            "cost_by_seed": [float(v) for v in cost],
            "delay_by_seed": (
                [float(delay[j]) if at_risk[j] else None for j in range(n)]
                if scenario == "abrupt_reversal"
                else None
            ),
        }
    paired = {}
    for candidate in ("P7s", "P7s-sentinel", "P7s-evidence", "P7s-ecusum"):
        paired[candidate] = {}
        for control in ("Cao-L", "Cao-Hybrid"):
            delta = np.asarray(rows[candidate]["cost_by_seed"]) - np.asarray(
                rows[control]["cost_by_seed"]
            )
            paired[candidate][control] = {
                "candidate_minus_control_mean": float(delta.mean()),
                "paired_bootstrap_95_ci": bootstrap_mean_ci(
                    delta, seed_base + 19001 + METHODS.index(control) + METHODS.index(candidate)
                ),
                "candidate_lower_cost_fraction": float((delta < 0).mean()),
            }
    return {"methods": rows, "paired_P7s_vs_Cao": paired}


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", choices=("dev", "confirm"), default="dev")
    ap.add_argument("--n-seeds", type=int, default=200)
    ap.add_argument("--p7-gamma", type=float, default=0.97)
    ap.add_argument("--settled-floor", type=float, default=0.0)
    ap.add_argument("--sentinel-log-threshold", type=float, default=float(np.log(2)))
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/b3_plus_cao_comparator")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.phase == "confirm":
        raise SystemExit(
            "Confirmatory phase is closed for the current method: development did not meet the "
            "registered reversal-cost and rollback-delay gate. Freeze a revised candidate and "
            "protocol before opening a new confirmatory run."
        )
    if args.n_seeds < 2:
        raise SystemExit("--n-seeds must be at least 2")
    seed_base = SEED_DEV
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {
        "phase": args.phase,
        "seed_base": seed_base,
        "n_seeds": args.n_seeds,
        "protocol": {
            "T": T,
            "budget": BUDGET,
            "delay": DELAY,
            "switch_cost": CS,
            "query_cost": CQ,
            "disagreement_probability": DISAGREEMENT,
            "positive_advantage": MU,
            "reversal_at": TAU_REVERSAL,
            "benign_shift_at": TAU_BENIGN_SHIFT,
            "p7_persist_gamma": args.p7_gamma,
            "p7_settled_floor": args.settled_floor,
            "sentinel_log_threshold": args.sentinel_log_threshold,
            "label_history_sleep": 19,
            "hybrid_block": 25,
            "hybrid_two_sided_z": 1.96,
            "cap_counts_issued_requests": True,
            "acquisition_only_changes": True,
        },
        "scenarios": {},
        "provenance": {
            "utc": datetime.now(UTC).isoformat(),
            "python": sys.version,
            "platform": platform.platform(),
            "source_sha256": {
                str(Path(__file__).resolve()): sha256(Path(__file__).resolve()),
                str((HERE / "b3_plus_policy.py").resolve()): sha256(HERE / "b3_plus_policy.py"),
            },
        },
    }
    for scenario in SCENARIOS:
        report["scenarios"][scenario] = run_scenario(
            scenario,
            args.n_seeds,
            seed_base,
            args.p7_gamma,
            args.settled_floor,
            args.sentinel_log_threshold,
        )
    dest = args.out / f"{args.phase}.json"
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(dest.relative_to(ROOT).as_posix())
    for scenario, result in report["scenarios"].items():
        summary = {
            name: {
                "cost": round(v["mean_cost"], 3),
                "labels": round(v["mean_labels"], 1),
                "rollback_prob": round(v["rollback_probability"], 3),
                "rollback_RMST": v["rollback_delay_rmst"],
                "cap_violations": v["cap_violations"],
            }
            for name, v in result["methods"].items()
        }
        print(scenario, json.dumps(summary))
        print("  P7s vs Cao:", json.dumps(result["paired_P7s_vs_Cao"]))


if __name__ == "__main__":
    main()
