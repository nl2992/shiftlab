"""Paired episode-block analysis for the frozen EIA-930 development replay."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 202611078
N_BOOT = 2000
CANDIDATE = "PFA-SR:gated_deployment"
COMPARATORS = ("rmm:gated_deployment+RMM", "cams_adapter")


def paired_ci(left: np.ndarray, right: np.ndarray) -> tuple[float, float, float]:
    d = np.asarray(left, dtype=float) - np.asarray(right, dtype=float)
    rng = np.random.default_rng(SEED)
    ix = rng.integers(0, len(d), size=(N_BOOT, len(d)))
    means = d[ix].mean(axis=1)
    return float(d.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> None:
    rows = [
        json.loads(line)
        for line in (HERE / "episode_results.jsonl").read_text().splitlines()
        if line
    ]
    frame = pd.DataFrame(rows)
    ba_summary = frame.groupby(["ba", "policy"], as_index=False).agg(
        episodes=("episode", "count"),
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
    contrasts = []
    for ba in sorted(frame.ba.unique()):
        sub = frame[frame.ba == ba]
        wide = sub.pivot(index="episode", columns="policy", values="net_cost").sort_index()
        for comparator in COMPARATORS:
            if comparator not in wide or CANDIDATE not in wide:
                continue
            mean, lo, hi = paired_ci(wide[CANDIDATE].to_numpy(), wide[comparator].to_numpy())
            contrasts.append(
                {
                    "ba": ba,
                    "contrast": f"{CANDIDATE} - {comparator}",
                    "episodes": len(wide),
                    "mean_difference": mean,
                    "ci95_low": lo,
                    "ci95_high": hi,
                    "gate_saving_5_and_ci_below_zero": bool(mean <= -5 and hi < 0),
                }
            )
    eligibility = json.loads((HERE / "summary.json").read_text())["eligibility"]
    eligible = {
        ba: 0.01 <= item["disagreement_rate"] <= 0.05
        and item["challenger_correct_given_disagreement"] >= 0.85
        for ba, item in eligibility.items()
    }
    by_ba = {
        ba: {
            row["contrast"].rsplit(" - ", 1)[1]: row["gate_saving_5_and_ci_below_zero"]
            for row in contrasts
            if row["ba"] == ba
        }
        for ba in eligible
    }
    gate = (
        sum(
            eligible[ba]
            and by_ba.get(ba, {}).get("rmm:gated_deployment+RMM", False)
            and by_ba.get(ba, {}).get("cams_adapter", False)
            for ba in eligible
        )
        >= 2
    )
    ba_summary.to_csv(HERE / "summary_by_ba.csv", index=False)
    (HERE / "analysis.json").write_text(
        json.dumps(
            {
                "seed": SEED,
                "bootstrap_resamples": N_BOOT,
                "target_match_by_ba": eligible,
                "contrasts": contrasts,
                "development_gate_pass": bool(gate),
                "note": "Episode-block CIs are within-BA development diagnostics; they do not establish source-level or anytime-valid inference.",
            },
            indent=2,
        )
        + "\n"
    )
    lines = [
        "# EIA-930 F8 development results",
        "",
        "Development replay only; EIA-930 historical values use simulated one-hour label release and are subject to revision.",
        "PFA-SR is prior art. This is not a novel-method or confirmation claim.",
        "",
        "## Target-regime match",
        "",
        "| BA | events | disagreement rate | challenger accuracy on disagreements | F8 target match |",
        "|---|---:|---:|---:|---|",
    ]
    for ba, item in eligibility.items():
        lines.append(
            f"| {ba} | {item['events']} | {item['disagreement_rate']:.4f} | {item['challenger_correct_given_disagreement']:.4f} | {'yes' if eligible[ba] else 'no'} |"
        )
    lines += [
        "",
        "## Policy means",
        "",
        ba_summary.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Paired candidate contrasts",
        "",
        "| BA | contrast | episodes | mean difference | 95% CI |",
        "|---|---|---:|---:|---|",
    ]
    for row in contrasts:
        lines.append(
            f"| {row['ba']} | {row['contrast']} | {row['episodes']} | {row['mean_difference']:.3f} | [{row['ci95_low']:.3f}, {row['ci95_high']:.3f}] |"
        )
    lines += [
        "",
        f"**Frozen development gate:** {'PASS' if gate else 'FAIL'}. This gate requires the target profile to match F8 and PFA-SR to save at least five units with a paired interval below zero versus both matched RMM and CAMS in at least two BAs. If it fails, do not open the reserved future-window evaluation for this candidate.",
        "",
    ]
    (HERE / "RESULTS.md").write_text("\n".join(lines))
    print((HERE / "RESULTS.md").read_text())


if __name__ == "__main__":
    main()
