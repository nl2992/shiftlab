# Matched-path eventwise-bound confirmation protocol

**Status:** frozen after the independent 60-stream schedule/bound development grid, 2026-10-24. Calibration root seed `28504027`; disjoint harm-confirmation root seed `28604027`. Do not change the selected schedule, bounds, outcomes, threshold, or retention rule after opening either block.

## Candidate

The selected schedule is the precommitted periodic policy with `q_low=0.05` on eight of every ten positions and `q_high=0.80` on two positions, with stream phase assigned by `stream_id mod 10`. Its target mean query propensity is 0.20. Compare the eventwise PPI bound `B_t=M(2/q_t-1)` with the fixed bound `B=M(2/0.05-1)=39M`. Both systems use identical exogenous q values, query uniforms, labels, registered events, and resolved prefixes; continue updating after an alarm and stop enrolling only at the shared 480-label cap. This isolates the support-bound choice.

The development grid selected this schedule from three alternatives. This independent block evaluates the selected candidate without retuning. The constant `q=0.20` arm was an exact identity control in development and is not included as a separate calibration family here.

## Stage 1: null calibration

- Use 2,000 streams for each of the exact statewise-zero Markov null and the strict-negative control.
- Cross both controls with fixed and eventwise bounds, yielding four cells.
- Generate 2,400-event streams under the frozen Markov process; request labels after exactly 12 events, enforce the 480-label cap, use a frozen action pair and independent source-trained proxy.
- Use simultaneous one-sided exact Clopper–Pearson limits with Bonferroni per-cell alpha `0.05/4`. All four upper limits must be at most 0.05, and all query, support, prefix-order, and completion checks must pass.
- Do not run or inspect confirmation alternatives if calibration fails.

## Stage 2: disjoint harm confirmation

- Only after Stage 1 passes, run 2,000 paired streams at each Markov harm effect `{0.04,0.20,0.40,0.60}` using the disjoint confirmation seed root.
- Primary endpoint: equal-weight mean across four doses of the paired eventwise-minus-fixed post-onset detection difference. Resample whole stream IDs jointly across doses with 10,000 bootstrap replicates.
- The frozen retention rule requires a two-sided 95% bootstrap lower limit above +0.02, no increase in mean labels (the path identity should make the paired label difference exactly zero), and a passed independent calibration gate.
- Report dose-level detection, pre-onset false escalations, delays, labels, event horizon, evaluator-only state-conditional exposure, and path identity checks. Evaluator exposure assumes mitigation at the first alarm and is not realized prevented loss.

## Assumptions and interpretation

This screen relies on the two-state Markov process whose paired-cost mean is zero in each latent state under the null, a query schedule fixed before current context/outcome, independent randomized query coins, complete correctly indexed labels, a frozen action pair/proxy, and event-order prefix alarms. It does not support claims for arbitrary serial dependence, informative or missing labels, adaptive policy updates, or counterfactual policy value. The e-process is a standard bounded-factor construction. This tests whether its eventwise range improves power when acquisition propensities vary; it is not a new algorithm or theorem.

No visual is required. Any visual must use PaperBanana; if unavailable, keep the deliverable to tables and machine-readable metrics.

## Reproduction

```powershell
uv run python scripts/confirm_matched_path_bound_ablation.py --stage calibration --streams 2000 --seed 28504027 --device cuda --output outputs/matched_path_bound_calibration_2000
uv run python scripts/confirm_matched_path_bound_ablation.py --stage confirmation --streams 2000 --seed 28604027 --device cuda --calibration-summary outputs/matched_path_bound_calibration_2000/metrics/calibration.csv --output outputs/matched_path_bound_confirmation_2000
uv run pytest tests/test_matched_path_bound_ablation.py -q
```
