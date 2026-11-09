#!/usr/bin/env python3
"""Build metric-specific WP1 ranks on the frozen retrospective late-improvement stratum.

All policies share the same 10 classified episodes, five source clusters and three policy seeds.
Ranks are descriptive within this stratum; the certified comparator is selected on these same data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import screen
from bench import CERTIFIED_PUBLISHED

ROOT = Path(__file__).resolve().parents[2]
RECORDS = ROOT / "outputs/sprint2/WP1/primary/records.jsonl"
CLASSES = ROOT / "outputs/sprint2/WP1/classes.json"
MANIFEST = ROOT / "outputs/sprint2/WP1/primary/manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cluster_ci(
    frame: pd.DataFrame, value: str, seed: int = 20261105, n_boot: int = 10_000
) -> dict[str, float | int | None]:
    """Percentile bootstrap over independent source clusters, matching WP1 summaries."""
    by_cluster = {k: g[value].to_numpy(float) for k, g in frame.groupby("cluster")}
    keys = list(by_cluster)
    mean = float(frame[value].mean()) if len(frame) else float("nan")
    if len(keys) < 3:
        return {"mean": mean, "lo": None, "hi": None, "episodes": len(frame), "clusters": len(keys)}
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        selected = rng.integers(0, len(keys), len(keys))
        boot[b] = np.concatenate([by_cluster[keys[i]] for i in selected]).mean()
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return {
        "mean": mean,
        "lo": float(lo),
        "hi": float(hi),
        "episodes": len(frame),
        "clusters": len(keys),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", type=Path, default=Path("docs/sprint2/wp1/late_metric_leaderboard.json")
    )
    parser.add_argument(
        "--markdown", type=Path, default=Path("docs/sprint2/wp1/late_metric_leaderboard.md")
    )
    parser.add_argument("--bootstrap-reps", type=int, default=10_000)
    args = parser.parse_args()

    records = pd.read_json(RECORDS, lines=True)
    classes = json.loads(CLASSES.read_text())
    class_map = {(r["stream"], int(r["ep"])): r for r in classes}
    manifest = json.loads(MANIFEST.read_text())
    selected = records[
        records.apply(
            lambda r: (
                r["regime"] in manifest["streams"]
                and class_map[(r["regime"], int(r["ep"]))]["class"] == "late_improvement"
            ),
            axis=1,
        )
    ].copy()
    selected["cluster"] = [
        class_map[(r.regime, int(r.ep))]["cluster"] for r in selected.itertuples()
    ]
    selected["detect_delay_promoted"] = selected["detect_delay"].where(selected["ever_promote"] > 0)
    episode = selected.groupby(["regime", "ep", "cluster", "policy"], as_index=False).agg(
        net=("net", "mean"),
        regret_hindsight=("regret_hindsight", "mean"),
        labels=("labels", "mean"),
        switches=("switches", "mean"),
        promoted=("ever_promote", "mean"),
        delay_promoted=("detect_delay_promoted", "mean"),
    )
    expected_episodes = {
        (r["stream"], int(r["ep"]))
        for r in classes
        if r["stream"] in manifest["streams"] and r["class"] == "late_improvement"
    }
    observed_episodes = set(zip(episode.regime, episode.ep.astype(int)))
    if observed_episodes != expected_episodes:
        raise ValueError(
            f"late episode coverage mismatch: expected {len(expected_episodes)}, got {len(observed_episodes)}"
        )
    policy_sets = episode.groupby(["regime", "ep"]).policy.apply(set)
    if not all(policies == set(manifest["policies"]) for policies in policy_sets):
        raise ValueError("policy coverage differs across late episodes or from primary manifest")

    certified = [p for p in CERTIFIED_PUBLISHED if p in set(episode.policy)]
    mean_j = episode.groupby("policy").net.mean()
    best_certified = min(certified, key=lambda p: mean_j[p])
    base = episode[episode.policy == best_certified].set_index(["regime", "ep"]).net
    paired = episode.copy()
    paired["delta_j_vs_best_certified"] = [
        row.net - base.loc[(row.regime, row.ep)] for row in paired.itertuples()
    ]

    metrics = {
        "net_cost_J": (episode, "net", "lower", "Mean net cost J per episode"),
        "hindsight_regret": (
            episode,
            "regret_hindsight",
            "lower",
            "Mean retrospective hindsight regret per episode",
        ),
        "label_expenditure": (
            episode.assign(value=episode.labels * float(screen.CONTRACT["cq"])),
            "value",
            "lower",
            "Mean label expenditure c_q × labels per episode",
        ),
        "switching_expenditure": (
            episode.assign(value=episode.switches * float(manifest["cs"])),
            "value",
            "lower",
            "Mean switching expenditure c_s × switches per episode",
        ),
        "delta_J_vs_best_certified": (
            paired,
            "delta_j_vs_best_certified",
            "lower",
            f"Paired ΔJ vs same-sample selected comparator `{best_certified}`",
        ),
    }
    # Delay is conditional on a promotion; non-promoting policies are reported as not rankable.
    promoted = episode[episode.promoted > 0].copy()
    metrics["first_promotion_delay"] = (
        promoted,
        "delay_promoted",
        "lower",
        "Mean detect_delay among episodes with a promotion",
    )

    report: dict = {
        "title": "WP1 late-improvement metric-specific leaderboard",
        "status": "RETROSPECTIVE_DESCRIPTIVE_SELECTED_STRATUM",
        "stratum": "late_improvement",
        "episodes": len(expected_episodes),
        "clusters": int(episode.cluster.nunique()),
        "seeds_per_episode": int(manifest["seeds"]),
        "policy_count": int(episode.policy.nunique()),
        "best_certified_selected_on_same_stratum": best_certified,
        "bootstrap": {
            "unit": "source cluster",
            "reps": args.bootstrap_reps,
            "seed": 20261105,
            "interval": "percentile 95%",
        },
        "cost_contract": {
            "c_q": float(screen.CONTRACT["cq"]),
            "c_s": float(manifest["cs"]),
            "budget": manifest["budget"],
        },
        "source_hashes": {
            str(p.relative_to(ROOT)): sha256(p) for p in (RECORDS, CLASSES, MANIFEST)
        },
        "generator_sha256": sha256(Path(__file__).resolve()),
        "metrics": {},
        "limitations": [
            "The episode classes are retrospective outcome-derived labels, not causal change times.",
            "Raw datasets and episodes were exposed during development; this is not independent confirmation.",
            "The strongest certified comparator is selected on the same ten episodes; paired differences are exploratory and unadjusted for this selection.",
            "Delay is conditional on promotion; non-promoting runs are not assigned a fictitious delay rank.",
            "Hindsight regret is retrospective and is not the registered prospective objective.",
            "These metric ranks describe the WP1 late-improvement slice, not a global cross-track ordering.",
        ],
    }
    for key, (frame, column, direction, label) in metrics.items():
        rank = frame.groupby("policy")[column].mean().sort_values(ascending=True)
        rows = []
        for position, (policy, value) in enumerate(rank.items(), 1):
            policy_rows = frame[frame.policy == policy].copy()
            if key == "first_promotion_delay":
                ci = cluster_ci(
                    policy_rows.rename(columns={column: "_value"}),
                    "_value",
                    seed=20261105,
                    n_boot=args.bootstrap_reps,
                )
                promoted_seeds = int(selected.loc[selected.policy == policy, "ever_promote"].sum())
                total_seeds = int((selected.policy == policy).sum())
                promotion_fraction = promoted_seeds / total_seeds
            else:
                ci = cluster_ci(
                    policy_rows.rename(columns={column: "_value"}),
                    "_value",
                    seed=20261105,
                    n_boot=args.bootstrap_reps,
                )
                promoted_seeds = None
                promotion_fraction = None
            rows.append(
                {
                    "rank": position,
                    "policy": policy,
                    **ci,
                    "promotion_fraction_seed_runs": promotion_fraction,
                }
            )
        report["metrics"][key] = {"label": label, "direction": direction, "ranking": rows}

    out_json = args.json if args.json.is_absolute() else ROOT / args.json
    out_md = args.markdown if args.markdown.is_absolute() else ROOT / args.markdown
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# WP1 late-improvement metric-specific leaderboard",
        "",
        (
            f"**Scope:** {report['episodes']} retrospective episodes from {report['clusters']} source clusters; "
            f"{report['seeds_per_episode']} paired seeds per episode; {report['policy_count']} policies."
        ),
        (
            f"The selected strongest certified comparator is `{best_certified}`. It is selected on the same "
            "episodes used for these descriptive rankings."
        ),
        "",
        (
            f"These are within-stratum rankings, not a global ordering across Tracks E/R/V. Intervals are "
            f"95% percentile bootstraps over source clusters ({args.bootstrap_reps:,} resamples). Raw streams and class labels "
            "were development-exposed; episode classes are retrospective, not causal change labels."
        ),
        "",
        "## Metric-specific rankings",
        "",
    ]
    for key, metric in report["metrics"].items():
        lines += [
            f"### {metric['label']}",
            "",
            "| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |",
            "|---:|---|---:|---:|---:|---:|",
        ]
        for row in metric["ranking"]:
            interval = (
                "not estimable" if row["lo"] is None else f"[{row['lo']:.2f}, {row['hi']:.2f}]"
            )
            mean = "NA" if not np.isfinite(row["mean"]) else f"{row['mean']:.2f}"
            lines.append(
                f"| {row['rank']} | `{row['policy']}` | {mean} | {interval} | {row['episodes']} | {row['clusters']} |"
            )
        if key == "first_promotion_delay":
            not_promoted = sorted(set(episode.policy) - set(promoted.policy))
            if not_promoted:
                lines += [
                    "",
                    "Not rankable for promotion delay (no promotion in any seed): "
                    + ", ".join(f"`{p}`" for p in not_promoted)
                    + ".",
                ]
        lines.append("")
    lines += [
        "## Scope and reproduction",
        "",
        (
            "Label and switch expenditure are reported separately from J; total J already includes both. "
            "Hindsight regret is retrospective. The paired ΔJ table uses the same-sample selected "
            f"comparator `{best_certified}`, so it is exploratory and not selection-adjusted."
        ),
        "",
        (
            "Limitations: retrospective class labels, exposed raw streams, five source clusters, and "
            "no independent confirmation. See `RESULTS.md` and `protocol.md` for the registered WP1 "
            "estimand, comparator definitions and late-class verdict."
        ),
        "",
        "Reproduce from the registered saved records:",
        "",
        "```sh",
        "uv run python scripts/sota_sprint/build_wp1_late_metric_leaderboard.py",
        "```",
        "",
    ]
    out_md.write_text("\n".join(lines))
    print(
        json.dumps(
            {
                "status": "PASS",
                "policies": report["policy_count"],
                "episodes": report["episodes"],
                "clusters": report["clusters"],
                "best_certified": best_certified,
                "json": str(out_json.relative_to(ROOT)),
                "markdown": str(out_md.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
