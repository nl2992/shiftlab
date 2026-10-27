# PPE paired-cost development protocol v1

**Frozen:** 2026-10-26, before the registered run.

## Question

Does the Prediction-Powered E-Value (PPE) correction provide a useful
selective-label decision-harm monitor relative to direct bounded e-processes
and the existing inverse-propensity PPI monitor at the same event paths and
label budget?

## Methods and endpoint

Compare `ppe_fixed_stake` against `fixed_mixture`, `predictable_kelly`, and
`plug_in_empirical_bernstein` from
`src/shiftlab/dive/risk_proxy_monitor_grid.py`. The primary endpoint is whether
the method crosses its registered 1/alpha threshold after known material
paired-cost harm onset. Secondary metrics are false alarms in stationary and
benign-nuisance controls, detection delay, queried-label count, realized label
spend, estimator RMSE, and expected excess cost.

PPE uses the paper's factor correction, base factor
`1 + 0.1 * centered_paired_cost / clip`, and its frozen pre-monitor proxy
counterpart. Base support is `[0.9, 1.1]`; minimum query probability is
`1 - 0.9/1.1 = 0.181818...`. Both query rates, 0.20 and 0.40, therefore meet
the paper's nonnegativity condition. Other methods retain their registered
estimators and e-processes. All arms share the generated event stream, uniform
query draws, label costs, hard budget, source training data, and monitor start.

## Design

- Scenarios: stationary, benign nuisance shift, boundary-local harm, residual
  variance, recurring regimes, and harmful adaptation.
- 30 streams per scenario; common stream seed for methods and query-rate arms.
- Seed offset: `2026102600`; query rates: 0.20 and 0.40.
- Horizon: 2,400 events; CUDA synthetic generation; alpha: 0.05; harm margin:
  0.10; query and event controls remain those in the runner.
- No tuning or method changes after inspecting outcomes. Any code correction
  requires a new protocol version and preserves the first run.
- Analysis: per-method cell summaries and paired, seed-cluster bootstrap
  detection-rate contrasts. These are exploratory, unadjusted development
  intervals; no superiority claim follows from them.

## Stopping and next gate

This is a 30-seed development comparison only. Regardless of outcome, retain
all metrics and failures. If the PPE implementation passes null diagnostics
without a clear severe power deficit, the next gate is a separately frozen
large null calibration and disjoint alternative confirmation. Do not call the
30-seed run calibration or independent confirmation. If it is dominated and
offers no distinct useful operating point, record the result and stop the PPE
paired-cost branch.

## Assumptions and limitations

The theoretical interpretation requires a valid conditional-mean base
e-process, a base factor in the declared support, predictable proxy and query
propensity, query randomization independent of the current outcome conditional
on learner-visible history, and an identified paired-cost outcome. In this
synthetic setting both policy costs use the same generated outcome. The results
do not establish validity under performative actions, informative query
selection, delayed labels, or misspecified real-world costs. Population-null
generator controls need not satisfy every eventwise conditional null; empirical
false-alarm rates are diagnostics, not a substitute for the theorem.
