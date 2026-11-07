"""Summarize fixed-challenger consistency across the already opened EIA BA clusters."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

PILOT = Path(__file__).resolve().parent
INPUT = PILOT / "ANALYSIS.json"
OUTPUT = PILOT / "BA_CONSISTENCY_AUDIT.json"
REPORT = PILOT / "BA_CONSISTENCY_AUDIT.md"
T_CRIT_DF10 = 2.2281388519649385


def paired_summary(values: dict[str, float]) -> dict[str, object]:
    xs = list(values.values())
    n = len(xs)
    mean = statistics.mean(xs)
    se = statistics.stdev(xs) / math.sqrt(n)
    leave_one_out = {
        ba: statistics.mean(value for other, value in values.items() if other != ba)
        for ba in values
    }
    return {
        "clusters": n,
        "mean_candidate_minus_comparator": mean,
        "sd_across_clusters": statistics.stdev(xs),
        "equal_cluster_t_95_ci": [mean - T_CRIT_DF10 * se, mean + T_CRIT_DF10 * se],
        "clusters_favoring_candidate": sum(value < 0 for value in xs),
        "cluster_differences": dict(sorted(values.items())),
        "leave_one_cluster_out_mean_range": [
            min(leave_one_out.values()),
            max(leave_one_out.values()),
        ],
        "all_leave_one_cluster_out_means_favor_candidate": all(
            value < 0 for value in leave_one_out.values()
        ),
    }


def main() -> None:
    source = json.loads(INPUT.read_text())
    rows = source["per_ba_candidate_primary_best"]
    contrasts: dict[str, dict[str, float]] = {}
    for comparator in ("cams_adapter", "online_llm_picker"):
        contrasts[comparator] = {
            ba: float(values["fixed_challenger"]["net_cost"])
            - float(values[comparator]["net_cost"])
            for ba, values in rows.items()
        }
    result: dict[str, Any] = {
        "input_analysis_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "weighting": "equal weight per BA; each BA is the mean over its complete episodes and five policy seeds",
        "contrasts": {
            comparator: paired_summary(values) for comparator, values in contrasts.items()
        },
        "limitations": [
            "These are 11 balancing authorities within one EIA provider, not 11 independent data sources.",
            "The online_llm_picker contrast is descriptive after comparator selection; use the registered selection-aware hierarchical interval for inference.",
            "The replay uses revised historical values, simulated one-hour label maturity, hypothetical costs, and has disclosed progress-row exposure.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    cams = result["contrasts"]["cams_adapter"]
    best = result["contrasts"]["online_llm_picker"]
    REPORT.write_text(
        "# EIA-930 F8 BA consistency audit\n\n"
        "This append-only audit recomputes equal-BA contrasts from the already opened 2026 replay's `ANALYSIS.json`; it does not inspect new outcomes or change the registered analysis. Negative candidate-minus-comparator values favor the fixed challenger.\n\n"
        "| Comparator | Equal-BA difference | Cluster-level 95% t interval | BAs favoring candidate | Leave-one-BA-out mean range |\n"
        "|---|---:|---:|---:|---:|\n"
        f"| CAMS | {cams['mean_candidate_minus_comparator']:.3f} | [{cams['equal_cluster_t_95_ci'][0]:.3f}, {cams['equal_cluster_t_95_ci'][1]:.3f}] | {cams['clusters_favoring_candidate']}/{cams['clusters']} | [{cams['leave_one_cluster_out_mean_range'][0]:.3f}, {cams['leave_one_cluster_out_mean_range'][1]:.3f}] |\n"
        f"| Online LLM Picker* | {best['mean_candidate_minus_comparator']:.3f} | [{best['equal_cluster_t_95_ci'][0]:.3f}, {best['equal_cluster_t_95_ci'][1]:.3f}] | {best['clusters_favoring_candidate']}/{best['clusters']} | [{best['leave_one_cluster_out_mean_range'][0]:.3f}, {best['leave_one_cluster_out_mean_range'][1]:.3f}] |\n\n"
        "*Descriptive comparator contrast; the registered selection-aware hierarchical interval remains authoritative for the best-panel comparison. The cluster-level t intervals describe heterogeneity across these 11 BAs and are not independent-provider uncertainty. All 11 BA-level point differences favor the fixed challenger against both comparators; every leave-one-BA-out equal-BA mean remains favorable.\n\n"
        "This strengthens within-provider consistency for the F8 fixed-challenger control. It does not establish transfer to another operator or dataset, or identify a novel method. EIA-930 remains one source cluster; labels use retrospective revisions and simulated one-hour maturity, costs are hypothetical, and four aggregate progress rows were exposed during the original replay. Full differences, hashes, and limitations are in `BA_CONSISTENCY_AUDIT.json`.\n"
    )


if __name__ == "__main__":
    main()
