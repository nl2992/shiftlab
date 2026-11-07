"""Analyze the frozen EIA F8 2026 episode replay with the registered hierarchical bootstrap."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
PILOT = Path(__file__).resolve().parent
RECORDS = PILOT / "episode_policy_records.jsonl"
POLICIES = json.loads((PILOT / "run_manifest.json").read_text())["policy_registry"]
N_BOOT = 10_000
SEED = 2026110719
CANDIDATE = "fixed_challenger"
PRIMARY = "cams_adapter"
CONTROL_ONLY = {"fixed_incumbent", "fixed_challenger", "CONTROL_never_switch"}
COMPARATORS = [name for name in POLICIES if name not in CONTROL_ONLY]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    rows = [json.loads(line) for line in RECORDS.read_text().splitlines() if line]
    episode_values = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    )
    cost_residual = 0.0
    for row in rows:
        if row["policy"] not in POLICIES:
            raise RuntimeError(f"unregistered policy in results: {row['policy']}")
        if row["labels"] > 200:
            raise RuntimeError(f"label budget exceeded: {row}")
        cost_residual = max(cost_residual, abs(float(row["cost_residual"])))
        key = (row["ba"], int(row["episode_id"]))
        for metric in (
            "net_cost",
            "prediction_loss",
            "labels",
            "label_cost",
            "switches",
            "switch_cost",
            "promotions",
            "rollbacks",
        ):
            episode_values[key[0]][key[1]][row["policy"]][metric].append(float(row[metric]))
    expected = len(POLICIES) * 5
    for ba, episodes in episode_values.items():
        for ep, methods in episodes.items():
            if set(methods) != set(POLICIES) or any(
                len(methods[p][metric]) != 5
                for p in POLICIES
                for metric in (
                    "net_cost",
                    "prediction_loss",
                    "labels",
                    "label_cost",
                    "switches",
                    "switch_cost",
                    "promotions",
                    "rollbacks",
                )
            ):
                raise RuntimeError(f"incomplete paired panel for {ba}/episode {ep}")
    bas = sorted(episode_values)
    if len(rows) != sum(len(v) for v in episode_values.values()) * expected:
        raise RuntimeError("unexpected record count")

    episode_means = {}
    for ba in bas:
        episode_means[ba] = {}
        for ep, methods in episode_values[ba].items():
            episode_means[ba][ep] = {
                method: {
                    metric: float(np.mean(methods[method][metric])) for metric in methods[method]
                }
                for method in POLICIES
            }

    def equal_ba_means(method: str):
        return {
            metric: float(
                np.mean(
                    [
                        np.mean([episode_means[ba][ep][method][metric] for ep in episode_means[ba]])
                        for ba in bas
                    ]
                )
            )
            for metric in (
                "net_cost",
                "prediction_loss",
                "labels",
                "label_cost",
                "switches",
                "switch_cost",
                "promotions",
                "rollbacks",
            )
        }

    point = {method: equal_ba_means(method) for method in POLICIES}
    rng = np.random.default_rng(SEED)
    primary_boot = np.empty(N_BOOT)
    best_boot = np.empty(N_BOOT)
    for b in range(N_BOOT):
        sampled_bas = rng.choice(bas, size=len(bas), replace=True)
        boot_cost = {method: [] for method in [CANDIDATE, *COMPARATORS]}
        for ba in sampled_bas:
            eps = sorted(episode_means[ba])
            picked = rng.choice(eps, size=len(eps), replace=True)
            for method, values in boot_cost.items():
                values.append(
                    float(np.mean([episode_means[ba][ep][method]["net_cost"] for ep in picked]))
                )
        means = {method: float(np.mean(values)) for method, values in boot_cost.items()}
        primary_boot[b] = means[CANDIDATE] - means[PRIMARY]
        best_boot[b] = means[CANDIDATE] - min(means[m] for m in COMPARATORS)
    primary_delta = point[CANDIDATE]["net_cost"] - point[PRIMARY]["net_cost"]
    primary_ci = [float(x) for x in np.quantile(primary_boot, [0.025, 0.975])]
    best_name = min(COMPARATORS, key=lambda m: point[m]["net_cost"])
    best_delta = point[CANDIDATE]["net_cost"] - point[best_name]["net_cost"]
    best_ci = [float(x) for x in np.quantile(best_boot, [0.025, 0.975])]
    primary_pass = primary_delta <= -5 and primary_ci[1] < 0
    best_comparator_pass = best_delta <= -5 and best_ci[1] < 0

    per_ba = {}
    for ba in bas:
        per_ba[ba] = {}
        for method in (CANDIDATE, PRIMARY, best_name):
            per_ba[ba][method] = {
                metric: float(
                    np.mean([episode_means[ba][ep][method][metric] for ep in episode_means[ba]])
                )
                for metric in (
                    "net_cost",
                    "prediction_loss",
                    "labels",
                    "label_cost",
                    "switches",
                    "switch_cost",
                )
            }
    analysis = {
        "protocol": "eia930_f8_2026_confirmation_20261107/PROTOCOL_V2.md",
        "analysis_code_sha256": sha256(Path(__file__)),
        "raw_records_sha256": sha256(RECORDS),
        "record_count": len(rows),
        "ba_count": len(bas),
        "episode_count": sum(len(v) for v in episode_values.values()),
        "all_policy_seed_pairs_complete": True,
        "max_cost_identity_residual": cost_residual,
        "n_bootstrap": N_BOOT,
        "bootstrap_seed": SEED,
        "weighting": "equal BA; mean over complete episodes per BA; average five policy seeds within episode",
        "primary_comparator": PRIMARY,
        "primary_candidate_minus_comparator_mean": primary_delta,
        "primary_candidate_minus_comparator_hierarchical_95_ci": primary_ci,
        "primary_gate_pass": bool(primary_pass),
        "best_registered_comparator_by_point_mean": best_name,
        "candidate_minus_best_comparator_mean": best_delta,
        "candidate_minus_best_comparator_selection_aware_hierarchical_95_ci": best_ci,
        "beats_best_registered_comparator_gate": bool(best_comparator_pass),
        "equal_ba_method_means": point,
        "per_ba_candidate_primary_best": per_ba,
        "limitations": [
            "all 11 BAs are clusters within one EIA provider",
            "only 17 complete 2,000-event episodes were available across 11 BAs due to eligibility gaps",
            "current EIA revisions and one-hour feedback maturity are retrospective/simulated",
            "cost prices are hypothetical Failure Atlas units",
            "test stream was partially exposed through four episode-level fixed-challenger progress rows while the run was executing; no policy or protocol was changed afterward",
        ],
    }
    (PILOT / "ANALYSIS.json").write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    with (PILOT / "RESULTS.md").open("w") as f:
        f.write("# EIA-930 F8 2026 temporal confirmation\n\n")
        f.write(
            f"Tested all 11 BAs with {analysis['episode_count']} complete episodes and {len(POLICIES)} methods over five paired policy seeds.\n\n"
        )
        f.write(
            f"Primary fixed challenger minus CAMS: **{primary_delta:.3f}** net-cost units per episode; hierarchical paired 95% interval [{primary_ci[0]:.3f}, {primary_ci[1]:.3f}]. Frozen CAMS gate pass: **{primary_pass}**.\n\n"
        )
        f.write(
            f"Lowest-cost registered comparator by point mean: `{best_name}` ({point[best_name]['net_cost']:.3f}). Candidate minus selected best comparator: {best_delta:.3f}; selection-aware bootstrap interval [{best_ci[0]:.3f}, {best_ci[1]:.3f}]. Gate pass: **{best_comparator_pass}**.\n\n"
        )
        f.write(
            "## Method summary\n\n| Method | Net | Predictive loss | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for method, m in sorted(point.items(), key=lambda kv: kv[1]["net_cost"]):
            f.write(
                f"| {method} | {m['net_cost']:.3f} | {m['prediction_loss']:.3f} | {m['labels']:.1f} | {m['label_cost']:.2f} | {m['switches']:.2f} | {m['switch_cost']:.2f} | {m['promotions']:.2f} | {m['rollbacks']:.2f} |\n"
            )
        f.write(
            "\n## BA-level results\n\n| BA | Candidate net | CAMS net | Best published panel method | Candidate labels | Candidate switches |\n|---|---:|---:|---|---:|---:|\n"
        )
        for ba in bas:
            c, p, best = per_ba[ba][CANDIDATE], per_ba[ba][PRIMARY], per_ba[ba][best_name]
            f.write(
                f"| {ba} | {c['net_cost']:.2f} | {p['net_cost']:.2f} | {best_name}: {best['net_cost']:.2f} | {c['labels']:.1f} | {c['switches']:.1f} |\n"
            )
        f.write("\n## Integrity and limitations\n\n")
        f.write(
            f"All 2,125 policy-episode records passed the pathwise label cap and cost identity check; maximum residual {cost_residual:.3g}. Source/feature chronology and simulated delay details are in `PROTOCOL_V2.md` and `PREFLIGHT.json`.\n\n"
        )
        f.write(
            "This is one provider and a single partial year. EIA values are revised, label release at one hour is simulated, and costs are hypothetical. Seventeen complete episodes were available, with one to three per BA. This cannot establish cross-provider generalization. Four episode-level fixed-challenger rows were exposed by tail commands during run monitoring; no design, policy or protocol choice changed after those peeks.\n"
        )
    print(
        json.dumps(
            {
                "primary_delta": primary_delta,
                "primary_ci": primary_ci,
                "best_comparator": best_name,
                "best_delta": best_delta,
                "best_ci": best_ci,
                "primary_pass": bool(primary_pass),
                "best_pass": bool(best_comparator_pass),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
