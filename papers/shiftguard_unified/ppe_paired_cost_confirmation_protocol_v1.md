# PPE paired-cost calibration and confirmation protocol v1

**Frozen:** 2026-10-26, after the registered 30-seed development run and
before confirmation execution. Source implementation and analysis are frozen;
no stake, threshold, query rate, endpoint, generator, or scenario may be tuned
using confirmation outcomes.

## Claim under test

The published Prediction-Powered E-Value correction, transferred to the
registered paired decision-cost estimand, yields a valid nonnegative e-process
under the declared eventwise conditional-mean null and randomized query design.
Its detection performance may be useful relative to direct fixed-mixture,
predictable-Kelly, and plug-in empirical-Bernstein monitors at matched label
budgets. No superiority claim is assumed.

## Frozen implementation

Use `src/shiftlab/dive/risk_proxy_monitor_grid.py` and
`src/shiftlab/dive/prediction_powered_evalues.py` with no algorithm changes.
PPE has base factor `1 + 0.1 * Z_t / B`, support `[0.9, 1.1]`, and query floor
`1 - 0.9/1.1 = 0.181818...`. Query rates stay at 0.20 and 0.40. The four
comparators and all monitor thresholds stay as registered in the source.

## Null calibration

- Stationary and benign-nuisance controls, 1,000 independent seeds per cell.
- Query rates 0.20 and 0.40; four methods, yielding 16 simultaneous null cells.
- A cell passes only if its one-sided Clopper-Pearson upper bound, using
  Bonferroni level `0.05/16`, is at most 0.05.
- The population-null generators are finite simulation diagnostics. Passing
  does not replace the e-process proof or extend it to serial dependence,
  informative missingness, delayed labels, or action-dependent outcomes.

## Disjoint alternative confirmation

- Four registered alternatives: boundary-local harm, residual variance,
  recurring regimes, and harmful adaptation.
- 300 independent seeds per alternative; common random streams and label
  paths across methods; query rates 0.20 and 0.40.
- Seed offset 2,026,102,700. Null stream seeds occupy 2,026,102,700–2,026,103,699;
  alternative stream seeds occupy 2,026,103,700–2,026,103,999.
- Primary endpoint: detection-rate difference PPE minus fixed-mixture,
  averaged equally within each seed over all four alternatives and both query
  rates. Report a two-sided 95% bootstrap interval resampling whole stream
  seeds (10,000 replicates; analysis seed 2,026,102,701).
- Secondary pooled contrasts against predictable Kelly and plug-in empirical
  Bernstein use simultaneous Bonferroni-adjusted bootstrap intervals across
  the three comparator contrasts. Scenario-by-query-rate estimates remain
  descriptive, with unadjusted intervals clearly labeled.
- Also report false alarms, delay, labels, realized spend, RMSE, event count,
  and all per-seed outcomes. Enforce the registered hard label cap.

## Decision and stopping rule

Accept the implementation/calibration gate only if all 16 null-cell bounds
pass, all hard caps hold, source/protocol/output hashes verify, and independent
replay reproduces the reported event counts and false alarms. Regardless of
outcome, retain the full data and report the result. A calibration failure
stops this PPE adaptation until its assumption mismatch is diagnosed under a
new protocol. Alternative efficacy is reported as evidence, not as proof of
validity or generalization; if PPE is dominated without a useful trade-off,
stop this branch and return to the Q1–Q3 go/no-go decision.
