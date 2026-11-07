"""Analyze the frozen three-scale CAMS eta development screen."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_cams_eta_followup_20261107"
RECORDS = PILOT / "episode_policy_records.jsonl"
SCALES = ("cams_eta_1p5", "cams_eta_2", "cams_eta_3")
BOOTSTRAPS = 5000


def contrasts(frame: pd.DataFrame, candidate: str) -> dict:
    means = frame.groupby(["ba", "episode", "policy"]).net_cost.mean().unstack("policy")
    diff = (means[candidate] - means["cams_adapter"]).dropna()
    rng = np.random.default_rng(2026110715)
    by_ba = {}
    for ba, group in diff.groupby(level="ba"):
        x = group.to_numpy()
        sims = np.array([rng.choice(x, len(x), replace=True).mean() for _ in range(BOOTSTRAPS)])
        lo, hi = np.quantile(sims, [0.025, 0.975])
        by_ba[str(ba)] = {
            "episodes": len(x),
            "mean_candidate_minus_cams": float(x.mean()),
            "ci95_episode_bootstrap": [float(lo), float(hi)],
            "saves_at_least_5_with_ci_below_zero": bool(x.mean() <= -5 and hi < 0),
        }
    bas = sorted(diff.index.get_level_values("ba").unique())
    values = {ba: diff.xs(ba, level="ba").to_numpy() for ba in bas}
    hier = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        sample = rng.choice(bas, len(bas), replace=True)
        hier[i] = np.mean(
            [rng.choice(values[ba], len(values[ba]), replace=True).mean() for ba in sample]
        )
    lo, hi = np.quantile(hier, [0.025, 0.975])
    return {
        "candidate": candidate,
        "equal_ba_mean_candidate_minus_cams": float(np.mean([v.mean() for v in values.values()])),
        "hierarchical_ci95": [float(lo), float(hi)],
        "ba_wins": int(sum(v.mean() < 0 for v in values.values())),
        "ba_practical_wins": int(
            sum(v["saves_at_least_5_with_ci_below_zero"] for v in by_ba.values())
        ),
        "by_ba": by_ba,
    }


def main() -> None:
    frame = pd.read_json(RECORDS, lines=True)
    frame["residual"] = (
        frame.net_cost - frame.prediction_loss - frame.label_cost - frame.switch_cost
    )
    if len(frame) != 2025 or frame.residual.abs().max() > 1e-10:
        raise RuntimeError("incomplete follow-up records or broken cost identity")
    by_ba = frame.groupby(["ba", "policy"], as_index=False).agg(
        net_cost=("net_cost", "mean"),
        loss=("prediction_loss", "mean"),
        labels=("labels", "mean"),
        label_cost=("label_cost", "mean"),
        switches=("switches", "mean"),
        switch_cost=("switch_cost", "mean"),
        promotions=("promotions", "mean"),
        rollbacks=("rollbacks", "mean"),
        first_promotion=("first_promotion", "mean"),
    )
    summary = (
        by_ba.groupby("policy")
        .agg(
            net_cost=("net_cost", "mean"),
            loss=("loss", "mean"),
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
    comp = {scale: contrasts(frame, scale) for scale in SCALES}
    best = str(summary.loc[list(SCALES), "net_cost"].idxmin())
    gate = all(
        comp[scale]["ba_practical_wins"] >= 8 and comp[scale]["hierarchical_ci95"][1] < 0
        for scale in SCALES
    )
    result = {
        "rows": len(frame),
        "episodes": int(frame[["ba", "episode"]].drop_duplicates().shape[0]),
        "bas": sorted(frame.ba.unique()),
        "max_abs_cost_identity_residual": float(frame.residual.abs().max()),
        "method_means_equal_ba": json.loads(summary.reset_index().to_json(orient="records")),
        "contrasts_vs_cams": comp,
        "lowest_cost_scale": best,
        "development_gate_pass": gate,
        "holdout_opened": False,
        "interpretation": "Bounded eta-scale screen; scale tuning is a standard hyperparameter adjustment, not novelty.",
    }
    (PILOT / "ANALYSIS.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# CAMS eta-scale follow-up results",
        "",
        "**Status:** completed, bounded development-only screen.",
        "",
        f"Rows: {len(frame)}; episodes: {result['episodes']}; BAs: {len(result['bas'])}; five policy seeds per episode.",
        f"Maximum net-cost identity residual: {result['max_abs_cost_identity_residual']:.3g}.",
        "",
        "## Equal-BA mean cost decomposition",
        "",
        "| Method | Net cost | Loss | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks | First promotion |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in summary.iterrows():
        first = "—" if pd.isna(row.first_promotion) else f"{row.first_promotion:.1f}"
        lines.append(
            f"| {name} | {row.net_cost:.3f} | {row.loss:.3f} | {row.labels:.2f} | {row.label_cost:.3f} | "
            f"{row.switches:.3f} | {row.switch_cost:.3f} | {row.promotions:.3f} | {row.rollbacks:.3f} | {first} |"
        )
    lines.extend(["", "## Paired eta-scale contrasts versus CAMS", ""])
    for name, item in comp.items():
        lo, hi = item["hierarchical_ci95"]
        lines.extend(
            [
                f"### `{name}`",
                "",
                (
                    f"Equal-BA mean difference: **{item['equal_ba_mean_candidate_minus_cams']:+.3f}**; "
                    f"hierarchical 95% interval [{lo:+.3f}, {hi:+.3f}]; directional BA wins {item['ba_wins']}/11; "
                    f"BAs with ≥5 savings and episode interval below zero: {item['ba_practical_wins']}/11."
                ),
                "",
                "| BA | Mean difference | 95% episode-bootstrap interval |",
                "|---|---:|---:|",
            ]
        )
        for ba, row in item["by_ba"].items():
            lo, hi = row["ci95_episode_bootstrap"]
            lines.append(
                f"| {ba} | {row['mean_candidate_minus_cams']:+.3f} | [{lo:+.3f}, {hi:+.3f}] |"
            )
        lines.append("")
    lines.extend(
        [
            "## Decision",
            "",
            (
                f"The lowest-cost variant is `{best}`. Frozen gate: **{'PASS' if gate else 'FAIL'}**. "
                "No variant achieved the required ≥5-unit savings, at least 8/11 BA-level wins, and a hierarchical interval below zero."
            ),
            "The future holdout remains closed. This is a standard schedule-tuning result, not a novel-method result.",
            "",
            (
                "All BAs are within one provider; chronology and one-hour feedback delay are simulated/revised; "
                "the cost contract is not calibrated field utility; no known-null error rate is available."
            ),
            "",
        ]
    )
    (PILOT / "RESULTS.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {
                "lowest_cost_scale": best,
                "scale_vs_cams": {
                    k: {
                        "mean": v["equal_ba_mean_candidate_minus_cams"],
                        "ci": v["hierarchical_ci95"],
                        "ba_wins": v["ba_wins"],
                    }
                    for k, v in comp.items()
                },
                "gate_pass": gate,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
