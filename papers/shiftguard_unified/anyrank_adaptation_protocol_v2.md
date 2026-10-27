# AnyRank corrective ShiftGuard development replay

**Status:** frozen corrective replay; exploratory only, not independent confirmation.

## Purpose

The first AnyRank pilot used the wrong direction for the registered asymmetric classification costs when constructing its candidate reward matrix. It assigned false-negative cost to action 1 on outcome 0 and false-positive cost to action 0 on outcome 1. The repository's canonical cost function defines action 1 as the positive prediction: action 1/outcome 0 is a false positive (cost 1), and action 0/outcome 1 is a false negative (cost 5). The v1 AnyRank method results are invalid and are retained only as an audit artifact.

This replay changes only that cost mapping. It reuses the exact six seed IDs and the same two cells from v1, so it is a corrected development replay on previously inspected random streams, not fresh confirmation and not evidence for calibrated power. The zero-signal and positive-signal cells remain prevalence 0.50, proxy error 0.10, signals 0 and 0.10. The candidate bank, AnyRank reference-star hypothesis family, alpha split, query uniforms, label cap, evaluation window, and comparator methods are unchanged.

## Frozen cost and reward contract

For binary prediction action `a` and outcome `y`, cost is 0 when `a == y`; otherwise cost is 1 when `a == 1` (false positive) and 5 when `a == 0` (false negative). A changed policy adds the existing switching-cost amortization `0.05 / deployment_length` per deployed event. The AnyRank score is one minus this cost divided by `5 + switching_cost_per_event`, so every score is in `[0, 1]`. The incumbent receives no switching charge.

All decision code uses queried labels and the frozen candidate action matrix. Generator probabilities and evaluator expected losses are used only for the common post-monitor holdout metrics and the separate oracle diagnostic; they never enter AnyRank inputs.

## Comparison

Within each of the two learner-visible contexts, the official AnyRank tie-aware sequential graphical procedure tests the 12 non-incumbent candidates against the incumbent using the frozen star family. Contexts each receive alpha 0.025, summing to 0.05. If multiple candidates are certified to have a strictly higher bounded reward distribution than the incumbent, the one with the largest observed mean reward is selected; the tests do not identify the global best challenger. Pooled fixed-mixture, source-validation fixed split, and Target-Scout run on the same stream and query path. Every method is scored on the common evaluator-only slice `[monitor_end, n)`.

The six-stream result is descriptive and underpowered. It cannot calibrate the FWER, establish efficacy, support a publication claim, or be described as an independent confirmation. The star-shaped adaptation and common-label setting do not reproduce AnyRank's full all-pairs ranking or active per-policy trial savings.

Run with:

```powershell
uv run --with-editable tmp/AnyRank-source-audit python scripts/reproduce_anyrank_shiftguard.py --output outputs/shiftguard_unified/sota_reproductions/anyrank_shiftguard_pilot_v2
uv run python scripts/verify_anyrank_shiftguard_pilot.py --output outputs/shiftguard_unified/sota_reproductions/anyrank_shiftguard_pilot_v2
```

The official AnyRank dependency licenses and exact versions remain recorded in the manifest. The source package stays external; use is for non-commercial academic research.
