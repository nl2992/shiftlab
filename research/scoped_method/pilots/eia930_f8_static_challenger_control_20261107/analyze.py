"""Paired episode analysis of the static EIA model controls."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_static_challenger_control_20261107"
STATIC = PILOT / "fixed_control_records.jsonl"
PANEL = (
    ROOT
    / "research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107/episode_policy_records.jsonl"
)
BOOTSTRAPS = 5000


def contrast(static: pd.DataFrame, cams: pd.DataFrame, policy: str) -> dict:
    s = static[static.policy == policy].set_index(["ba", "episode"])
    c = cams.set_index(["ba", "episode"])
    diff = s.net_cost - c.net_cost
    rng = np.random.default_rng(2026110716)
    by_ba = {}
    for ba, group in diff.groupby(level="ba"):
        x = group.to_numpy()
        draws = np.array([rng.choice(x, len(x), replace=True).mean() for _ in range(BOOTSTRAPS)])
        lo, hi = np.quantile(draws, [0.025, 0.975])
        by_ba[str(ba)] = {
            "episodes": len(x),
            "mean_candidate_minus_cams": float(x.mean()),
            "ci95_episode_bootstrap": [float(lo), float(hi)],
            "saves_at_least_5": bool(x.mean() <= -5 and hi < 0),
        }
    bas = sorted(diff.index.get_level_values("ba").unique())
    grouped = {ba: diff.xs(ba, level="ba").to_numpy() for ba in bas}
    hierarchy = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        sample = rng.choice(bas, len(bas), replace=True)
        hierarchy[i] = np.mean(
            [rng.choice(grouped[ba], len(grouped[ba]), replace=True).mean() for ba in sample]
        )
    lo, hi = np.quantile(hierarchy, [0.025, 0.975])
    return {
        "policy": policy,
        "equal_ba_mean_difference": float(np.mean([x.mean() for x in grouped.values()])),
        "hierarchical_ci95": [float(lo), float(hi)],
        "ba_wins": int(sum(x.mean() < 0 for x in grouped.values())),
        "ba_saves_at_least_5_with_ci_below_zero": int(
            sum(v["saves_at_least_5"] for v in by_ba.values())
        ),
        "by_ba": by_ba,
    }


def main() -> None:
    static = pd.read_json(STATIC, lines=True)
    panel = pd.read_json(PANEL, lines=True)
    cams = (
        panel[panel.policy == "cams_adapter"]
        .groupby(["ba", "episode"], as_index=False)
        .agg(
            net_cost=("net_cost", "mean"),
            prediction_loss=("prediction_loss", "mean"),
            labels=("labels", "mean"),
            label_cost=("label_cost", "mean"),
            switches=("switches", "mean"),
            switch_cost=("switch_cost", "mean"),
        )
    )
    if static.groupby(["ba", "episode"]).size().ne(2).any() or len(cams) != 81:
        raise RuntimeError("fixed controls do not cover the full common episode panel")
    results = {
        policy: contrast(static, cams, policy) for policy in ("fixed_challenger", "fixed_incumbent")
    }
    static_summary = static.groupby("policy").agg(
        net_cost=("net_cost", "mean"),
        prediction_loss=("prediction_loss", "mean"),
        labels=("labels", "mean"),
        label_cost=("label_cost", "mean"),
        switches=("switches", "mean"),
        switch_cost=("switch_cost", "mean"),
    )
    cams_summary = cams[
        ["net_cost", "prediction_loss", "labels", "label_cost", "switches", "switch_cost"]
    ].mean()
    result = {
        "episodes": len(cams),
        "bas": sorted(cams.ba.unique()),
        "fixed_control_means": json.loads(static_summary.reset_index().to_json(orient="records")),
        "cams_mean": cams_summary.to_dict(),
        "contrasts_vs_cams": results,
        "max_static_cost_identity_residual": float(
            (static.net_cost - static.prediction_loss - static.label_cost - static.switch_cost)
            .abs()
            .max()
        ),
        "selection_limitation": (
            "BAs were selected by the same 2022-2023 profile period used for this comparison. "
            "The fixed challenger is therefore a post-selection development control, not confirmation."
        ),
        "holdout_opened": False,
    }
    (PILOT / "ANALYSIS.json").write_text(json.dumps(result, indent=2) + "\n")
    challenger = results["fixed_challenger"]
    lo, hi = challenger["hierarchical_ci95"]
    lines = [
        "# Fixed challenger control results",
        "",
        "**Status:** positive but post-selection development diagnostic; independent confirmation is still required.",
        "",
        "| Policy | Net cost | Prediction loss | Labels | Label cost | Switches | Switch cost |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for policy, row in static_summary.iterrows():
        lines.append(
            f"| {policy} | {row.net_cost:.2f} | {row.prediction_loss:.2f} | {row.labels:.2f} | "
            f"{row.label_cost:.2f} | {row.switches:.2f} | {row.switch_cost:.2f} |"
        )
    lines.append(
        f"| CAMS (five-seed episode mean) | {cams_summary.net_cost:.2f} | {cams_summary.prediction_loss:.2f} | "
        f"{cams_summary.labels:.2f} | {cams_summary.label_cost:.2f} | {cams_summary.switches:.2f} | {cams_summary.switch_cost:.2f} |"
    )
    lines.extend(
        [
            "",
            "## Primary fixed challenger contrast",
            "",
            (
                f"Fixed challenger minus CAMS equal-BA cost: **{challenger['equal_ba_mean_difference']:+.2f}**; "
                f"hierarchical BA-then-episode 95% interval [{lo:+.2f}, {hi:+.2f}]; directional BA wins "
                f"{challenger['ba_wins']}/11; BAs with at least 5 units saved and an episode interval below zero: "
                f"{challenger['ba_saves_at_least_5_with_ci_below_zero']}/11."
            ),
            "",
            "| BA | Episodes | Fixed challenger − CAMS | 95% episode-bootstrap interval |",
            "|---|---:|---:|---:|",
        ]
    )
    for ba, row in challenger["by_ba"].items():
        lo, hi = row["ci95_episode_bootstrap"]
        lines.append(
            f"| {ba} | {row['episodes']} | {row['mean_candidate_minus_cams']:+.2f} | [{lo:+.2f}, {hi:+.2f}] |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The fixed challenger uses no label feedback and pays one switch cost per episode. It is a simple feasible policy, "
                "not a new algorithm. This panel was selected by the same 2022–2023 development-period F8 profile being evaluated, "
                "so the result is optimistic by construction. The next scientific test is an untouched chronological confirmation "
                "with a train-time model-selection rule fixed before opening outcomes; otherwise this is only a benchmark observation."
            ),
            "",
            (
                "All BAs share one EIA provider, label release is simulated, historical values are revised, and cost units are hypothetical. "
                "No field-utility or cross-provider claim follows."
            ),
            "",
        ]
    )
    (PILOT / "RESULTS.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {
                "fixed_challenger_vs_cams": {
                    "mean": challenger["equal_ba_mean_difference"],
                    "ci95": challenger["hierarchical_ci95"],
                    "ba_wins": challenger["ba_wins"],
                },
                "fixed_challenger_cost": float(static_summary.loc["fixed_challenger", "net_cost"]),
                "cams_cost": float(cams_summary.net_cost),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
