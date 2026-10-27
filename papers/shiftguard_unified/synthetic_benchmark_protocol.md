# Synthetic benchmark protocol, version 0.1

**Status:** protocol draft for development comparisons; not registered confirmation. No new algorithm is proposed. The benchmark reuses existing known-truth generators and established monitors. It may be executed only after source-faithful comparator implementations and exact method versions are checked off in [`sota_fidelity_matrix.md`](sota_fidelity_matrix.md) and [`reference_method_freeze.md`](reference_method_freeze.md).

## Scientific questions

1. When do feature-distribution alarms, predictive-risk alarms and paired decision-cost alarms disagree under controlled changes?
2. At a matched label budget, which established monitor/acquisition combination detects a declared paired-cost margin violation with calibrated false escalation?
3. Under known candidate costs and fixed resource budgets, when does held-out certification and an intervention policy improve net utility over continue, always-promote and periodic-update controls?

The unit of randomization and uncertainty is a complete generated seed stream (or seed cluster when the same generated stream is reused across methods/onsets). Rows/events inside a stream are never treated as independent replications.

## Data-generating cases

Use the existing `SCENARIOS` and data-generation implementations; freeze their exact source hashes in every manifest. No parameters may be tuned on the confirmation family.

| Family | Role | Known truth / required check |
|---|---|---|
| Stationary | Population no-harm control | Evaluator verifies the declared population conditional paired-cost margin under the null. |
| Benign nuisance shift | Negative control for “shift implies harm” | Feature distribution changes while the decision-cost null remains true; predictive risk may be stable or change per generator definition. |
| Boundary-local harm | Targeted alternative | Record true local and population expected paired costs, harm onset and oracle policy. |
| Residual-variance scale shift | Monitoring stress | Conditional mean remains at its specified null/alternative level while increment variance changes; do not substitute a contextwise null for population harm. |
| Recurring regimes | Onset/scale stress | Evaluator records each regime and expected cost; learner receives only observable features and past mature labels. |
| Harmful adaptation / heterogeneous reversal | Q2/Q3 intervention stress | Evaluator records potential policy costs, fixed candidate and reference, reversal time and postpromotion expected utility. Learner cannot see future reversal or oracle losses. |
| Delayed-label Markov-scale null and alternative | Feedback stress | Preserve separate null calibration, delay law, predictable query propensity, event/arrival order, and fresh confirmation seed blocks. Existing result only covers fresh fair signs with persistent amplitude, not persistent sign dependence or informative delay. |

The historical negative residual-variance context screen remains in the benchmark archive and is not evidence for the population-average endpoint. If a subgroup estimand is studied, declare it as a separate question with null-specific calibration.

## Frozen comparator families

Every method must be an exact source version, not merely a name in a results table.

**Q1:** direct paired-cost bounded monitor; verified author-method reproduction of *Comparing Sequential Forecasters*; paper-faithful prediction-powered risk and Prediction-Powered E-Values on their original predictive-risk endpoints; PPRM; WATCH only on a justified conformal score/null task; CUSUM and MMD feature-shift diagnostics; predictive-loss monitor. A feature-shift or predictive-risk alarm is not scored as a decision-harm alarm.

**Q2:** fixed sample-split evaluation; pooled candidate-rank testing; context-nested allocation; pinned Target-Scout source commit; a paired anytime candidate gate such as PACE only under matched paired-outcome assumptions; OCS/HCPI/CPC/AnyRank where the task actually supplies their action-dependent or safe-reference feedback. Always state when candidate policies share a common observed label versus receive only chosen-action feedback.

**Q3:** uniform label requests; ASI and robust ASI at their fixed-horizon estimator objective; cost-adjusted uncertainty acquisition; never-adapt/continue; unconditional promotion; periodic update; triggered update; frozen intervention controller; RCCDA and When-to-Retrain on a matching model-update task. A method with no executable implementation or incompatible feedback model is listed as excluded, with the exact reason, and cannot silently disappear from the protocol.

## Information and intervention rules

- Generate each stream with separate learner/evaluator objects. The learner sees only (X_t), current policy versions/actions, prior mature labels, actual request probabilities, and declared costs available before an action.
- The evaluator retains latent regimes, true probabilities, expected costs, all identified potential-policy costs, true change points and oracle comparisons. The evaluator computes outcomes after the learner action sequence is fixed.
- On full-feedback classification streams, a single mature label may score multiple precomputed fixed policies. On performative/action-dependent streams, only the selected action's outcome is observable; use a logged causal/off-policy baseline or mark the comparison unsupported.
- Query policies log (q_t=\Pr(I_t=1\mid\mathcal F_{t-1},X_t)), obey (q_t\ge q_{\min}>0) where needed, and share the same hard cost/label budget within each matched comparison.
- Candidate certification uses a scout/development slice and an untouched independent confirmation slice, or a faithful anytime method with its full multiplicity design. Do not reuse candidate selection data as independent confirmation.
- Intervention cost is split into label, compute/update, switching and decision-cost components. Use one scalar utility only under a predeclared justified conversion; otherwise report the Pareto vector.

## Metrics

Report per seed and aggregate with seed-cluster confidence intervals:

- feature-discrepancy statistic and detection/false-alarm rate;
- predictive loss, predictive-loss change, and time to threshold;
- paired expected cost contrast, realized paired cost where observable, harm detection, false escalation and detection delay;
- candidate selection accuracy, certification error, false promotion, harmful promotion and postpromotion utility;
- cumulative decision loss and net utility after each separately reported intervention cost;
- labels queried, label spend, compute/update count and spend, switching count, and any hard-budget violations;
- calibration coverage/error at the declared unit and all simultaneous/multiple-testing adjustments.

Do not average incompatible nulls, mix calibration and alternative seeds, compare methods with different label access without reporting the difference, or treat seed-stream reuse as independent evidence.

## Development and confirmation separation

1. **Source/code audit:** verify each comparator against the primary paper, freeze exact implementations, write a fidelity note, and add correctness tests before running method comparisons.
2. **Development screen:** 30 paired seed streams per predeclared cell estimate runtime, obvious failure modes and effect scale only. This sample does not validate a 5% sequential false-alarm rate. No threshold or query parameter selected on this screen can be called confirmed.
3. **Null calibration:** use fresh, independent seed blocks for every method × null × acquisition design that makes a separate validity claim. Allocate familywise alpha before simulation. Use one-sided exact upper bounds with the prespecified multiplicity correction; require the bound, not just the point estimate, to meet the gate.
4. **Positive confirmation:** lock code and configuration after calibration; use disjoint seeds, declared onset/severity/query-rate family, matched budgets and a prespecified primary contrast. Report all registered cells including failures.
5. **Integrated development:** only after component comparisons, combine monitor, certification and intervention on shared generated streams; do not infer end-to-end benefit by summing component-level gains.
6. **Decision gate:** rank performance gaps and decide whether current methods suffice, one specific extension is warranted, a narrower empirical paper is stronger, or the unified claim should stop. Do not start an optimization branch before this decision.

## Required run artifacts and stop rules

For every run write immutable config, protocol SHA, source hashes, generator/data version, seed range, action and feedback assumptions, budgets, per-stream Parquet/CSV metrics, summary intervals, environment/GPU metadata, checksums, warnings/exclusions, stopping rule and pass/fail status. Store under `outputs/shiftguard_unified/<family>/<run-id>/` without overwriting prior evidence.

Stop a method comparison if source fidelity fails, learner/evaluator separation fails, query propensities or costs cannot be verified, any hard budget is violated, or calibration bounds fail. Preserve the failed run and diagnose before another run. Stop the study at the Phase D research decision described in `goal-objective.md`; this protocol does not authorize speculative optimization.
