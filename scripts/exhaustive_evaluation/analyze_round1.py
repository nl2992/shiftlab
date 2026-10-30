"""Compare the registered development grid to the audited RCPS component adapter."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.sota_search.combination_screen import make_world
from shiftlab.sota_search.published_baselines import active_rcps_cost

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/round1_corrected"


def main():
    registration = json.loads((DOC / "round1_corrected_registration.json").read_text())
    comparison_reg = DOC / "rcps_development_comparison_registration.json"
    if comparison_reg.exists():
        raise FileExistsError("Comparison registration already exists; preserve completed results")
    comparison_reg.write_text(
        json.dumps(
            {
                "registered_utc": datetime.now(UTC).isoformat(),
                "stage": "post-grid exploratory baseline comparison, not confirmation",
                "baseline": "active-RCPS fixed-target FTL complement-risk adapter",
                "source_commit": "a67f85d603df2bb3e32ef007f445191923ebd990",
                "adaptation": "fixed target, uniform q, hard stop at B, issuance-time bets with fixed delay",
                "alpha": 0.05,
                "cases": registration["cases"],
                "paths": 64,
                "horizon": 1200,
                "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "baseline_sha256": hashlib.sha256(
                    (ROOT / "src/shiftlab/sota_search/published_baselines.py").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    metrics = pd.read_csv(OUT / "metrics.csv", keep_default_na=False)
    configs = pd.DataFrame(registration["configs"])
    baseline = []
    for j, (kind, delay) in enumerate(registration["cases"]):
        stream = make_world(kind, paths=64, horizon=1200, seed=registration["world_seed_base"] + j)
        result = active_rcps_cost(
            stream, frac=0.2, budget=240, delay=delay, seed=registration["query_seed_base"] + j
        )
        case = f"{j:02d}_{kind}_d{delay}"
        np.savez_compressed(OUT / f"rcps_{case}.npz", **result)
        alarm = result["first"]
        onset = stream["evaluator"]["active"].argmax(1)
        cumharm = np.cumsum(np.maximum(stream["evaluator"]["harm"], 0), axis=1)
        idx = np.maximum(np.minimum(alarm, 1199) - 1, 0)
        baseline.append(
            {
                "case": case,
                "kind": kind,
                "delay": delay,
                "alarm_rate": float(np.mean(alarm < 1200)),
                "post_power": float(np.mean((alarm >= onset) & (alarm < 1200))),
                "harm_to_alarm": float(
                    np.mean(np.where(alarm > 0, cumharm[np.arange(64), idx], 0))
                ),
                "labels": float(result["labels"].mean()),
            }
        )
    pd.DataFrame(baseline).to_csv(OUT / "rcps_baseline_metrics.csv", index=False)
    null = metrics[metrics.kind.isin(["null", "nuisance"])].groupby("id").alarm_rate.max()
    efficacy = (
        metrics[~metrics.kind.isin(["null", "nuisance"])]
        .groupby("id")[["post_power", "harm_to_alarm", "labels"]]
        .mean()
    )
    ranked = efficacy.join(null.rename("worst_null_alarm")).reset_index().merge(configs, on="id")
    ranked["empirical_screen_eligible"] = ranked.worst_null_alarm <= 0.05
    ranked = ranked.sort_values(
        ["empirical_screen_eligible", "harm_to_alarm", "post_power"], ascending=[False, True, False]
    )
    ranked.to_csv(OUT / "ranked_configs.csv", index=False)
    # Compare every intermediate-guidance composition with its exact cost-only
    # parent, matching discount, cap, allocation and restart; no winner-only audit.
    parent = (
        configs[configs.guidance == 0].drop(columns="guidance").rename(columns={"id": "parent"})
    )
    pairs = configs[configs.guidance.between(0.01, 0.99)].merge(
        parent, on=["gamma", "cap", "allocation", "restart"]
    )
    paired = (
        pairs[["id", "parent"]]
        .merge(efficacy.reset_index(), on="id")
        .merge(
            efficacy.reset_index().rename(columns={"id": "parent"}),
            on="parent",
            suffixes=("", "_parent"),
        )
    )
    paired["harm_delta_vs_parent"] = paired.harm_to_alarm - paired.harm_to_alarm_parent
    paired["power_delta_vs_parent"] = paired.post_power - paired.post_power_parent
    paired.to_csv(OUT / "matched_parent_deltas.csv", index=False)
    lines = [
        "# Round 1 development findings",
        "",
        "540 distinct algorithm configurations completed on 8 registered cases (4,320 configuration-case evaluations), 64 paths each. Corrected evaluator version is authoritative for shift-attributable harm. This is exploratory, known-nominal, finite-support simulation; not real-data confirmation or exhaustive published-method superiority.",
        "",
        "## Baseline provenance",
        "",
        "Active-RCPS fixed-target component matches author code at delay 1 (max logwealth error 1.33e-15). Its delay-5/24, hard-cap, complement-risk monitoring wrapper is a separate adaptation. The full learned query policy and RCPS grid inversion are not reproduced. Other published families remain open in BASELINE_COVERAGE.md.",
        "",
        "## Candidate ranking",
        "",
        "Ranking uses empirical null rate <=.05, then lower mean shift-attributable harm before alarm. With only 64 null paths, this is a triage filter, NOT evidence that size is controlled at .05. No confirmed finalist is declared.",
        "",
        ranked.head(10).to_string(index=False),
        "",
        "## Adapted published component, same streams/query randomness",
        "",
        pd.DataFrame(baseline).to_string(index=False),
        "",
        "## Common weaknesses and next test",
        "",
        "Late onset and small changes are the weakest cells. Allocation changes consume different numbers of labels despite the same hard cap; label/cost efficiency must therefore be compared on a frontier, not raw alarm power alone. A low propensity floor enlarges the safe betting range and reduces attainable bets. Restart mixtures trade early capital for later recovery. Auxiliary-guidance performance must be compared with its matched cost parent across all cases, including broken guidance.",
        "",
        f"{len(paired)} intermediate-guidance configurations were compared to their matched cost-only parents. Development mean harm deltas range from {paired.harm_delta_vs_parent.min():.6f} to {paired.harm_delta_vs_parent.max():.6f}; selection uncertainty and repeated testing prohibit a novelty conclusion.",
        "",
        "Next: complete faithful PR/PPRM and active query baseline audits; register a bottleneck-targeted second round addressing budget pacing and guidance reliability, with equal-label frontiers. Add realistic calibration and dependence/delay stress. Verify on untouched synthetic seeds and chronological real streams only after protocol freeze. The full user objective remains ACTIVE.",
    ]
    report = "\n".join(lines) + "\n"
    (DOC / "ROUND1_DEVELOPMENT_REPORT.md").write_text(report, encoding="utf-8")
    print(ranked.head(3).to_string(index=False))
    print(pd.DataFrame(baseline).to_string(index=False))


if __name__ == "__main__":
    main()
