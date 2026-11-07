"""Episode-clustered analysis for the frozen EIA-930 all-BA policy replay."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107"
RECORDS = PILOT / "episode_policy_records.jsonl"
CANDIDATE = "PFA-SR:gated_deployment"
COMPARE = ("cams_adapter", "rmm:gated_deployment+RMM")
BOOTSTRAPS = 5000


def clustered_contrast(frame: pd.DataFrame, comparator: str) -> dict:
    means = frame.groupby(["ba", "episode", "policy"]).net_cost.mean().unstack("policy")
    diffs = (means[CANDIDATE] - means[comparator]).dropna()
    rng = np.random.default_rng(2026110713)
    by_ba = {}
    for ba, group in diffs.groupby(level="ba"):
        values = group.to_numpy()
        n = len(values)
        draws = np.empty(BOOTSTRAPS)
        for i in range(BOOTSTRAPS):
            draws[i] = rng.choice(values, size=n, replace=True).mean()
        low, high = np.quantile(draws, [0.025, 0.975])
        by_ba[str(ba)] = {
            "episodes": n,
            "mean_candidate_minus_comparator": float(values.mean()),
            "ci95_episode_bootstrap": [float(low), float(high)],
            "paired_savings_at_least_5": bool(values.mean() <= -5 and high < 0),
        }
    bas = sorted(diffs.index.get_level_values("ba").unique())
    grouped = {ba: diffs.xs(ba, level="ba").to_numpy() for ba in bas}
    hierarchy = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        selected = rng.choice(bas, size=len(bas), replace=True)
        hierarchy[i] = np.mean(
            [rng.choice(grouped[ba], size=len(grouped[ba]), replace=True).mean() for ba in selected]
        )
    point = float(np.mean([values.mean() for values in grouped.values()]))
    low, high = np.quantile(hierarchy, [0.025, 0.975])
    return {
        "candidate": CANDIDATE,
        "comparator": comparator,
        "equal_ba_mean_candidate_minus_comparator": point,
        "hierarchical_ba_then_episode_ci95": [float(low), float(high)],
        "ba_directional_savings_at_least_5": sum(
            v["paired_savings_at_least_5"] for v in by_ba.values()
        ),
        "ba_count": len(by_ba),
        "by_ba": by_ba,
    }


def main() -> None:
    frame = pd.read_json(RECORDS, lines=True)
    frame["cost_residual"] = (
        frame.net_cost - frame.prediction_loss - frame.label_cost - frame.switch_cost
    )
    if len(frame) != 6480 or frame.cost_residual.abs().max() > 1e-10:
        raise RuntimeError("incomplete panel or invalid cost identity")
    method = frame.groupby(["ba", "policy"], as_index=False).agg(
        net_cost=("net_cost", "mean"),
        prediction_loss=("prediction_loss", "mean"),
        labels=("labels", "mean"),
        label_cost=("label_cost", "mean"),
        switches=("switches", "mean"),
        switch_cost=("switch_cost", "mean"),
        promotions=("promotions", "mean"),
        rollbacks=("rollbacks", "mean"),
        first_promotion=("first_promotion", "mean"),
    )
    overall = (
        method.groupby("policy")
        .agg(
            net_cost=("net_cost", "mean"),
            prediction_loss=("prediction_loss", "mean"),
            labels=("labels", "mean"),
            label_cost=("label_cost", "mean"),
            switches=("switches", "mean"),
            switch_cost=("switch_cost", "mean"),
            promotions=("promotions", "mean"),
            rollbacks=("rollbacks", "mean"),
            first_promotion=("first_promotion", "mean"),
        )
        .sort_values("net_cost")
    )
    contrasts = {comp: clustered_contrast(frame, comp) for comp in COMPARE}
    baseline_order = overall.drop(index=CANDIDATE).net_cost.sort_values()
    result = {
        "rows": len(frame),
        "episodes": int(frame[["ba", "episode"]].drop_duplicates().shape[0]),
        "bas": sorted(frame.ba.unique()),
        "policy_seed_replicates_per_episode": 5,
        "max_abs_cost_identity_residual": float(frame.cost_residual.abs().max()),
        "equal_ba_method_summary": json.loads(overall.reset_index().to_json(orient="records")),
        "top_development_baseline": str(baseline_order.index[0]),
        "top_development_baseline_mean_net_cost": float(baseline_order.iloc[0]),
        "candidate_mean_net_cost": float(overall.loc[CANDIDATE, "net_cost"]),
        "candidate_minus_top_baseline": float(
            overall.loc[CANDIDATE, "net_cost"] - baseline_order.iloc[0]
        ),
        "primary_contrasts": contrasts,
        "gate_pass": all(
            contrasts[comparator]["ba_directional_savings_at_least_5"] >= 8
            and contrasts[comparator]["hierarchical_ba_then_episode_ci95"][1] < 0
            for comparator in COMPARE
        ),
        "limitations": [
            "2022-2023 is development data; BA selection used the same period's frozen profile screen.",
            "EIA history is revised and one-hour feedback release is simulated.",
            "All 11 BAs are correlated under one data provider; hierarchical intervals are not source-level uncertainty.",
            "PFA-SR is published prior art; no null guarantee is established for these serial streams.",
            "The cost contract is hypothetical Failure Atlas units, not calibrated electricity-market utility.",
        ],
    }
    (PILOT / "ANALYSIS.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# EIA-930 F8 policy development results",
        "",
        "**Status:** completed development replay; not independent confirmation.",
        "",
        f"Rows: {len(frame)}; episodes: {result['episodes']}; BAs: {len(result['bas'])}; policy seeds per episode: 5.",
        f"Maximum absolute net-cost identity residual: {result['max_abs_cost_identity_residual']:.3g}.",
        "",
        "## Mean cost decomposition (equal weight per BA, episode and policy seed)",
        "",
        "| Policy | Net | Predictive loss | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks | First promotion event |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for policy, row in overall.iterrows():
        fp = "—" if pd.isna(row.first_promotion) else f"{row.first_promotion:.1f}"
        lines.append(
            f"| {policy} | {row.net_cost:.2f} | {row.prediction_loss:.2f} | {row.labels:.2f} | "
            f"{row.label_cost:.2f} | {row.switches:.2f} | {row.switch_cost:.2f} | "
            f"{row.promotions:.2f} | {row.rollbacks:.2f} | {fp} |"
        )
    lines.extend(["", "## Frozen candidate contrasts", ""])
    for comparator, contrast in contrasts.items():
        lo, hi = contrast["hierarchical_ba_then_episode_ci95"]
        lines.extend(
            [
                f"### PFA-SR minus `{comparator}`",
                "",
                (
                    f"Equal-BA mean difference: **{contrast['equal_ba_mean_candidate_minus_comparator']:+.2f}** "
                    f"(hierarchical BA-then-episode 95% interval [{lo:+.2f}, {hi:+.2f}]); "
                    f"BAs meeting ≥5-unit savings with their episode interval below zero: "
                    f"{contrast['ba_directional_savings_at_least_5']}/{contrast['ba_count']}."
                ),
                "",
                "| BA | Episodes | Candidate − comparator | 95% episode-bootstrap interval |",
                "|---|---:|---:|---:|",
            ]
        )
        for ba, row in contrast["by_ba"].items():
            lo, hi = row["ci95_episode_bootstrap"]
            lines.append(
                f"| {ba} | {row['episodes']} | {row['mean_candidate_minus_comparator']:+.2f} | [{lo:+.2f}, {hi:+.2f}] |"
            )
        lines.append("")
    lines.extend(
        [
            "## Decision",
            "",
            f"Frozen development gate: **{'PASS' if result['gate_pass'] else 'FAIL'}**.",
            (
                f"The lowest-cost frozen panel baseline is `{result['top_development_baseline']}` at "
                f"{result['top_development_baseline_mean_net_cost']:.2f}; candidate cost is "
                f"{result['candidate_mean_net_cost']:.2f} (difference {result['candidate_minus_top_baseline']:+.2f})."
            ),
            "",
            (
                "This result is development evidence only. It does not validate real field utility, "
                "null error, source-level transfer, or a novel method claim."
            ),
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["limitations"])
    (PILOT / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "candidate_mean_net_cost": result["candidate_mean_net_cost"],
                "top_baseline": result["top_development_baseline"],
                "top_baseline_mean_net_cost": result["top_development_baseline_mean_net_cost"],
                "candidate_minus_top_baseline": result["candidate_minus_top_baseline"],
                "gate_pass": result["gate_pass"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
