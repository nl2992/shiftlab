# Headroom reconciliation after SR calibration — 2026-11-06

**Branch:** `codex/scoped-method-research-results-2026-11-06`  
**Evidence class:** synthetic development/replay only; no fresh real-data source was opened.  
**Decision:** `BENCHMARK_ONLY` (`BENCHMARK_OR_CASE_STUDY_ONLY` in the four-contribution report).

## Question

Does the rollback/acquisition pilot leave a distinct, realistically achievable economic
improvement that merits a new method? The prior economic matrix named probability-of-any-false-
promotion calibration of the conventional restart detector as its smallest next step. That
calibration and a bounded late-improvement screen have now been completed. The candidate is
existing E-SR prior art; the experiment tests headroom and operating regions, not novelty.

## Findings

1. **Reversal opportunity did not survive calibration.** In the prospective 1,000-null calibration,
   E-SR at alpha `0.0005` had 20/1,000 false promotions (one-sided 95% Wilson upper bound 0.0287).
   On the frozen worthwhile `F3_reversal_1200` cell, E-SR minus never-switch net cost was
   `+22.75 [19.70, 25.79]`, and E-SR minus E_swcert was `+3.84 [0.12, 7.57]` over 200 paired
   seeds. In `F3_reversal_800`, E-SR minus never-switch was `+45.76 [42.46, 49.05]`. The conventional
   restart method does not close the worthwhile-reversal gap.

2. **Late-persistent opportunity is explained by an existing method.** On 100 fresh paired
   `F1_late_800` streams, calibrated E-SR's mean net cost was 365.60 and it improved over
   PFA-SR:Gated adaptive range by `23.63 [19.40, 27.86]`, over E_rb/RMM by `6.20 [1.44, 10.96]`,
   and over never-switch by `22.66 [18.35, 26.97]` cost units. At `F1_late_1200`, it improved over
   PFA-SR by `12.13 [8.81, 15.45]`. This is a real scoped comparison result for an existing
   calibrated restart method, not an incremental ShiftLab mechanism.

3. **The frozen new-method gate did not pass.** E-SR cost `21.01 [16.64, 25.39]` more than the
   Qiu-inspired port and `14.39 [8.89, 19.89]` more than the Gong-inspired port in `F1_late_800`.
   These ports are not author-native implementations and promoted in 100/100 and 99/100 null
   streams, respectively, so their apparent advantage is not an equal-safety result. Separately,
   the fresh 100-stream E-SR null screen had 2 promotions and an upper bound of 0.0586, narrowly
   missing the frozen 0.05 screen gate. Preserve this screen separately from the prior 1,000-stream
   calibration; do not pool them after observing outcomes.

4. **The adverse regime remains material.** On `F3_reversal_800`, E-SR cost `45.07 [40.13,
   50.01]` more than never-switch. Thus the late-cell gain comes with an adverse reversal cost.

## Verdict and next action

No distinct repair has reproducible evidence beyond existing SR/restart prior art, and the frozen
development gates did not authorize confirmation. The tested evidence identifies a useful
regime-specific benchmark trade-off, not a method contribution. Do not begin another rollback,
acquisition, or detector-combination search on these outcomes. The smallest next step is to retain
this reconciliation in the benchmark manuscript and close the current method-search track. This
does not establish that no future method or operating region can work.

## Reproduction artifacts

- Economic matrix: `research/scoped_method/pilots/economic_headroom_matrix_20261106/run/RESULTS.md`
- E-SR calibration: `research/scoped_method/pilots/srr_any_false_calibration_20261106/`
- E-SR late screen: `research/scoped_method/pilots/srr_late_improvement_20261106/EVALUATION_RESULTS.md`
- Baseline fidelity: `docs/scoped_method_research_2026-11-06/BASELINE_FIDELITY.md`
- Four-contribution assessment: `docs/scoped_method_research_2026-11-06/FINAL_ASSESSMENT.md`
