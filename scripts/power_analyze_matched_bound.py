"""Plan a fresh paired-seed study from the locked matched-bound pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
from scipy.stats import binom

from shiftlab.dive.experiment import finalize_manifest
from shiftlab.dive.power import paired_mcnemar_power, paired_mcnemar_sample_size

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/hard_budget_matched_qmin_010_replication_60"


def main() -> None:
    metrics = pd.read_parquet(OUTPUT / "metrics/hard_budget_comparison.parquet")
    boundary = metrics.loc[metrics.scenario.eq("boundary_local_harm")]
    baseline = boundary.loc[boundary.method.eq("uniform_proxy")].set_index("seed")
    candidate = boundary.loc[boundary.method.eq("cost_stabilized_proxy")].set_index("seed")
    candidate = candidate.loc[baseline.index]
    wins = int((candidate.single_e_detected & ~baseline.single_e_detected).sum())
    losses = int((~candidate.single_e_detected & baseline.single_e_detected).sum())
    ties = len(candidate) - wins - losses
    discordant = wins + losses
    if discordant == 0 or wins <= losses:
        raise ValueError("pilot does not support a candidate-favoring McNemar planning alternative")
    p_discordant = discordant / len(candidate)
    p_candidate_win_given_discordance = wins / discordant
    observed_difference = (wins - losses) / len(candidate)
    one_sided_p = float(binom.sf(wins - 1, discordant, 0.5))

    rows = []
    for alpha in (0.05, 0.0125):
        for target_power in (0.80, 0.90):
            required = paired_mcnemar_sample_size(
                discordance_probability=p_discordant,
                candidate_win_probability_given_discordance=p_candidate_win_given_discordance,
                target_power=target_power,
                alpha=alpha,
            )
            rows.append(
                {
                    "alpha": alpha,
                    "target_power": target_power,
                    "required_fresh_seeds": required,
                    "plug_in_power_at_60": paired_mcnemar_power(
                        60,
                        discordance_probability=p_discordant,
                        candidate_win_probability_given_discordance=p_candidate_win_given_discordance,
                        alpha=alpha,
                    ),
                }
            )
    power = pd.DataFrame(rows)
    metrics_path = OUTPUT / "metrics/paired_detection_power_plan.csv"
    power.to_csv(metrics_path, index=False)

    report_path = OUTPUT / "reports/paired_detection_power_plan.md"
    lines = [
        "# Paired detection power planning",
        "",
        "This planning analysis uses only the completed 60-seed matched-bound pilot. It does not reuse these seeds for evaluation. Cost-stabilized allocation was the candidate nominated for a future independent comparison.",
        "",
        f"Against uniform on boundary-local harm, candidate-only detections were {wins}, uniform-only detections were {losses}, and paired ties were {ties}. The observed detection-rate difference was {observed_difference:+.3f}; the one-sided exact McNemar p-value for equality of marginal detection rates was {one_sided_p:.4f}.",
        "",
        f"Prospective calculations treat independent seeds as the sampling units and plug in the observed discordance rate ({p_discordant:.3f}) and candidate win fraction among discordant pairs ({p_candidate_win_given_discordance:.3f}). The exact power calculation sums over the binomial number of discordant seed pairs and applies the one-sided exact conditional McNemar rejection rule. These are optimistic plug-in values from a small pilot; they do not account for winner's curse or uncertainty in the nuisance rates.",
        "",
        "|One-sided alpha|Target power|Fresh paired seeds required|Plug-in power at 60 seeds|",
        "|---:|---:|---:|---:|",
    ]
    for row in power.to_dict("records"):
        lines.append(
            f"|{row['alpha']:.4f}|{row['target_power']:.2f}|{row['required_fresh_seeds']}|{row['plug_in_power_at_60']:.3f}|"
        )
    lines.extend(
        [
            "",
            "## Scope and decision",
            "",
            "This McNemar calculation tests the easier null of no difference in marginal detection probability. It does not test the locked protocol's practical-margin hypothesis that improvement exceeds 0.10. The pilot estimate (+0.067) is below that margin, so these sample sizes cannot be cited as powering the registered practical claim. A future study must either improve and re-lock the candidate on development seeds before a fresh test, or preserve the +0.10 margin and perform a dedicated paired-risk-difference power analysis. Do not launch a confirmatory run using the pilot seed block.",
            "",
            "Reproduce by running: uv run python scripts/power_analyze_matched_bound.py",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    manifest_path = OUTPUT / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["power_analysis"] = {
        "script": "scripts/power_analyze_matched_bound.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "method": "exact prospective one-sided conditional McNemar power; pilot plug-in discordance rates",
        "pilot_seeds_used_for_planning_only": 60,
        "fresh_seed_evaluation": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(OUTPUT)
    print(report_path.relative_to(ROOT))
    print(power.to_string(index=False))


if __name__ == "__main__":
    main()
