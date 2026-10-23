# Next research phase: decision-harm evidence efficiency

**Status:** Proposed execution plan following the 2026-10-23 robust-growth replication and paired budget-frontier screen. This plan is an experiment sequence, not a claim that the repository's three paper tracks are complete.

## Decision from the latest study

Do not advance interval-robust mixture-growth allocation as the lead method. In the independent 60-seed boundary-local study it detected 0/60 harmful streams, versus 4/60 for uniform and 0/60 for exact mixture-growth. It reduced estimator RMSE relative to simple heuristics but not relative to exact mixture-growth, and it processed a shorter stream than uniform. Keep it as a tested comparator. See `docs/robust_growth_grid_protocol.md` and `outputs/robust_growth_grid_fresh_60/`.

## Phase A: lock the estimand and monitor benchmark

1. Keep the primary endpoint as paired deployed-minus-reference decision cost, with a fixed materiality margin and explicit population null. Separate discrepancy, predictive degradation, and decision harm in every result.
2. Use the existing bounded conditional-mean e-processes and direct paired-loss monitor as established controls. Include exact and robust mixture-growth, uniform, variance, cost-variance, and decision-value acquisition policies.
3. Match the hard realized label-dollar cap, propensity support, common e-process increment bound, random numbers, seed streams, and observable information across every policy. Report both labels and events processed because equal dollars do not imply equal horizons.
4. Define stationary and benign nuisance scenarios as nondegenerate nulls; include local boundary harm, predictive-only degradation, variance/tail shifts, recurrence, and harmful adaptation as alternatives or stress tests. Ensure the onset is reached before budget exhaustion or report nondetection as censored.

## Phase B: separate calibration from power

The paired budget-frontier screen is complete: it compares 10%, 20%, and feasible 25% realized-dollar caps with common streams, query uniforms, and a common e-process bound. All methods respected the cap; all had 0/60 detections in each harmful scenario at each cap, even though all harmful onsets were reached. Exact and robust mixture-growth lowered stream-mean RMSE against uniform, but did not produce harm detections. The 30% target was outside the cost-neutral feasible interval under `q_max=0.80`, so it was replaced with 25% before the upper-budget results were generated. See `docs/budget_frontier_protocol.md`, `docs/budget_frontier_results.md`, and `outputs/budget_frontier_60/`.

The matched monitor diagnostic found 0/30 detections for fixed mixture, predictable variance, and PM-EB in both harmful scenarios under three acquisition policies, with all onsets reached. The paired uniform-query bound sensitivity then changed only `q_min` from 0.05 to 0.20 on the same 30 streams: fixed mixture detected 19/30 boundary-local and 20/30 recurring harms, predictable variance detected 19/30 in each, and PM-EB detected 0/30 and 1/30. Query counts, spend, and horizon matched exactly. The two null controls remained at 0/30 alarms, which motivated the frozen independent calibration protocol in `docs/null_calibration_qmin020_protocol.md`.

That calibration run completed 2,000 streams in each of the stationary and benign-nuisance population-null controls. Fixed mixture, predictable variance, and PM-EB each had 0/2,000 false escalations in each scenario; the four primary/secondary cells have a Bonferroni simultaneous one-sided 95% Clopper–Pearson upper limit of 0.00219. There were no cap violations. This supports a low false-escalation rate under these two simulator controls and stated assumptions; it does not establish validity under delayed feedback, serial dependence, selective labels, model misspecification, or candidate selection. See `docs/null_calibration_qmin020_protocol.md`, `outputs/null_calibration_qmin020_2000/reports/null_calibration_results.md`, and its metrics/manifest. The next action is a disjoint harmful-stream confirmation at the frozen q_min and monitor configuration, followed by a pre-specified power/delay map across harm magnitude, onset, and horizon. Do not reuse these null seeds for method or threshold selection.

1. On independent null streams, estimate false escalation probability for each complete policy-plus-monitor procedure. Start at 2,000 streams per null cell, then increase if the interval cannot distinguish the target error rate from an unacceptable rate. A zero-event small pilot is only a smoke diagnostic.
2. On disjoint alternative streams, map detection probability and unconditional/censored delay over harm magnitude, onset, label budget, and dependence. Use paired stream bootstrap intervals and report event counts as well as rates.
3. Predeclare one primary comparison and one selection rule. Keep development seeds separate from final evaluation; do not choose radii, thresholds, support bounds, or scenarios on the final block.
4. Include a label-efficiency curve: detection power and excess decision loss against realized label dollars and processed horizon. Add a simple no-query / conservative fallback comparator where the task semantics support it.

## Phase C: compare against closest established methods

Implement only the portions needed for a fair comparison, while documenting deviations from published assumptions. The next literature-and-code audit should prioritize prediction-powered risk monitoring, WATCH, active statistical inference, and active sequential testing. Each comparator must receive the same labels, filtration, policy freeze, repeated-testing budget, and false-escalation target where its assumptions allow. If direct paired-loss monitoring or an existing prediction-powered monitor matches the proposed objective and information access, report that negative result and narrow Paper 1.

## Phase D: connect monitoring to intervention

After the monitor benchmark is calibrated, run a separate frozen-candidate shadow evaluation. Do not treat detecting incumbent harm as certification of a replacement. Evaluate candidate net paired decision benefit after update, switching, and rollback costs; account for repeated candidate selection and use independent forward-time feedback. Then add a small finite-action controller for continue, query, recalibrate, adapt, retrain, or fallback, with identical information and explicit label/compute/intervention budgets.

## Exit criteria

Paper 1 advances only if one procedure demonstrates the declared false-escalation target on nondegenerate nulls and a reproducible gain in power, delay, or decision loss at matched information and cost against strong existing monitors. Paper 2 requires calibrated false promotion and positive net decision value for frozen candidates. Paper 3 requires a utility-versus-resource improvement over established cost-aware policies. Otherwise, preserve the negative result, narrow the question, or stop that contribution.

Run large screens on CUDA when generation or model fitting benefits from it, but preserve deterministic CPU smoke tests. Record requested and resolved devices, seeds, versions, code hashes, manifests, and checksums for every result.
