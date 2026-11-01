"""Summarize full registered round and negative real-development outcomes."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    data = ROOT / "outputs/exhaustive_evaluation/round2"
    df = pd.read_csv(data / "metrics.csv", keep_default_na=False)
    configs = pd.DataFrame(json.loads((DOC / "round2_registration.json").read_text())["configs"])
    audit = json.loads((DOC / "effective_combination_audit.json").read_text())
    alias_ids = {a["alias"] for a in audit["aliases"]}
    null = (
        df[df.kind.isin(["null", "nuisance"])].groupby("id").alarm_rate.max().rename("worst_null")
    )
    harm = (
        df[~df.kind.isin(["null", "nuisance"])]
        .groupby("id")[["harm_to_alarm", "post_power", "labels"]]
        .mean()
    )
    ranked = harm.join(null).reset_index().merge(configs, on="id")
    ranked = ranked[~ranked.id.isin(alias_ids)]
    ranked["screen_eligible"] = ranked.worst_null <= 0.05
    ranked = ranked.sort_values(["screen_eligible", "harm_to_alarm"], ascending=[False, True])
    ranked.to_csv(data / "ranked_configs.csv", index=False)
    references = harm[~harm.index.str.startswith("R2_")]
    best = ranked.iloc[0]
    anchor = references.loc["round1_top", "harm_to_alarm"]
    gain = 1 - best.harm_to_alarm / anchor
    real = pd.read_csv(ROOT / "outputs/exhaustive_evaluation/real_development/summary.csv")
    mainreal = real[(real.query_cost == 0.001) & (real.switch_cost == 1)]
    text = f"""# Round 2 and real-development decision

## Execution

756 registered parameter tuples completed 12 cases (9,072 configuration-case evaluations), with 96 paths per case and horizon 2,000. A mathematical activity audit found 108 exact aliases: the cost-floor guard cannot change a blend already retaining at least half the cost-only bet. All alias arrays match on every stored path. Thus round 2 contains **648 effective distinct configurations**, and together with round 1: **1,188 effective distinct configurations**. Corrected reruns/replays and aliases are not counted twice. Both rounds individually exceed 500 effective configurations. Six references accompany every case.

These are exploratory composition evaluations, not 1,296 new algorithms or independent confirmation. No final holdout was opened. Source-calibrated cases use 300/1,000/5,000 independent calibration labels per simulated path, a Hoeffding upper bound at .01, and test alpha .04. Known-nominal cases retain alpha .04. Source calibration is counted separately.

## All-case ranking

Rank: empirical null screen <=.05, then equal-case mean shift-attributable harm before first alarm. With 96 null paths, this is triage, not a proven false-alarm rate. Query counts differ; full equal-label frontiers remain required.

```
{ranked.head(8).to_string(index=False)}
```

Reference means:

```
{references.to_string()}
```

The best grid mean is {best.harm_to_alarm:.6f}, versus round-1 anchor {anchor:.6f}: **{100 * gain:.2f}%** development reduction. It is a cost-only paced configuration, not a guided winner. This is below the proposed 10% practical gate and is selected from 756 alternatives. No statistical or novelty success is established. Per-cell winners do not constitute a single deployable policy.

## Baseline interpretation

- Historical H2c anchor reproduced exactly for all 600 paths in the selected accurate/concept2 cell, at 10% and 20% labels, for H2c, discounted cost and cost-ONS. This validates reproduction, not new evidence.
- PR PM-EB uses the paper's Appendix E bounded-loss formula and predictable variance. PPRM uses equations 19/22/27, hard synthetic labels, one random label per five-event batch and a declared 32-point discrete mixing distribution. Both are formula-based cost/delay adaptations; neither is a full author experimental reproduction.
- PPRM observes batches, while betting candidates observe randomly queried events. Same maximum labels does not make those observation contracts identical. Its conservative running-average procedure has a different null structure from conditional cost betting. Inferiority here cannot establish general superiority over published PPRM.
- The active-RCPS FTL component parity remains verified only at delay1. Full learned sampling/grid inversion, empirical PH/CUSUM thresholds and remaining published families remain open.

## Real-data pilot: negative

Two frozen, training-only model banks were scored on development periods only. Calendar-only features; training median targets; no weather or target-lag leakage. Data are serial and release delays imposed. Source calibration bounds are descriptive assumptions here, not verified iid guarantees.

At query cost .001 and switch cost 1:

```
{mainreal.to_string(index=False)}
```

Bike: all monitors abstained from switching, so they only added query cost. Beijing: the selected blended monitor and its cost parent switched to a worse challenger; RCPS did so on some query paths. H2c/PR/PPRM abstained and only added query cost. All nine preregistered cost scenarios are retained in per-path outputs, not selected by success. Query seeds replicate acquisition randomness on one stream, not independent real datasets.

This falsifies a useful net-benefit claim for **these frozen alarm-to-challenger controllers on these development tasks**. It does not falsify the underlying monitors or all possible future candidates. The challenger being worse is an observed failure to handle, not permission to replace it after inspecting the same evaluation and call the replacement confirmed.

## Shared bottlenecks and next iteration

1. Detection is not promotion certification: an incumbent-risk alarm does not establish that the candidate beats the incumbent after switching cost. Test a separately valid paired-benefit certificate using common queried outcomes, including harmful challengers and persistent/reversing benefits.
2. Calibration can remove much of a monitor's practical power. Compare total historical-plus-online label cost and consider the different paired-reference target explicitly, rather than assuming known source risk.
3. Propensity floors and budget pacing trade evidence range against label consumption. Best raw-power cells cannot replace a matched label-cost frontier.
4. Faster compact risk verification remains useful engineering. The primary robust-FSC text and author code are now located; product-state memory and robust verification already appear there. J's verifier-only speedup is not a new optimizer. The two-law synthesis/value-gap residual remains unresolved.

**Decision: RESTRICT current monitor/controller claims; continue with paired-benefit and action-set tests plus remaining source-faithful baselines.** No defensible new method is established. Fresh synthetic confirmation and reserved real evaluation remain closed until a candidate clears the scientific and development gates. The user's full goal remains ACTIVE.
"""
    (DOC / "ROUND2_AND_REAL_DEVELOPMENT_REPORT.md").write_text(text, encoding="utf-8")
    print(
        "Wrote report; top mean improvement", round(100 * gain, 3), "percent; no confirmation claim"
    )


if __name__ == "__main__":
    main()
