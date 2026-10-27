# Integrated benchmark protocol: decision-harm monitoring, candidate certification, and intervention

**Version:** design draft 0.7, 2026-10-26  
**Status:** this broader design draft is not preregistered and remains a protocol specification. A separately frozen v1 configuration completed its synthetic null calibration and disjoint efficacy confirmation; the latter is independently verified but does not establish real-world validity or general integrated superiority. Earlier five- and seven-policy pilots and CUDA smoke runs remain development evidence only. The 9-method × 8-profile smoke grid has 144 rows over two seeds and is descriptive only. See [`integrated_null_calibration_protocol_v1.md`](integrated_null_calibration_protocol_v1.md), [`fixed_candidate_null_protocol_v1.md`](fixed_candidate_null_protocol_v1.md), [`integrated_results.md`](integrated_results.md), [`integrated efficacy confirmation protocol`](integrated_efficacy_confirmation_protocol_v1.md), [`verified efficacy results`](integrated_efficacy_confirmation_results_v1.md), and [`integrated_fixed_certification_development_report.md`](integrated_fixed_certification_development_report.md).  
**Purpose:** evaluate whether composing the existing Q1, Q2, and Q3 components improves net decision utility over simpler policies under one stream, one information contract, and one hard label budget.

## Research question and estimands

On a common non-performative classification stream, does a staged policy—monitor incumbent-versus-reference decision harm, select and certify a fixed candidate using fresh future feedback, then deploy it with forward rollback monitoring—improve cumulative decision utility after label and intervention costs over `continue`, periodic promotion, and the existing two-gate workflow?

Keep three endpoints separate: distribution discrepancy, predictive risk, and paired decision cost. The primary evaluator metric is cumulative paired policy cost plus the preregistered label, update, switch, and fallback charges. Report the resource vector and a sensitivity frontier if conversion to one scalar is only imposed. The learner never receives oracle expected costs, latent regimes, true change times, or potential-outcome summaries.

## Stream and policy contract

Use one generated stream per seed and scenario from the current synthetic decision-harm family, with identical features, outcomes, candidate predictions, and query uniforms replayed across methods. For this first integrated benchmark, policies are fixed functions of the same event's covariates and label; an intervention changes which policy is deployed but does not change the outcome-generation law. This supports paired full-feedback scoring after a label is acquired. It does **not** represent a performative or chosen-action bandit environment.

Each event log must include event index, feature-availability index, prediction/action index, query indicator and predictable propensity, label availability index, incumbent/reference/candidate policy versions, available loss feedback, evidence value, intervention state, and resource expenditures. In this initial synthetic run labels are immediate after request. Delayed-label and event-dependent outcomes remain separate stress tests because the current component guarantees do not automatically cover them.

The evaluator alone stores the generator parameters, conditional label law, expected cost of every frozen policy, true harm onset, and counterfactual cost table. Learner-visible candidate fitting may use only the initial training and validation labels; scouting, certification, monitoring, and deployment labels are released under their registered stage rules. An information-flow test must mutate evaluator-only expected probabilities and verify that candidate identities, query decisions, e-values, promotions, rollback times, and resource counts do not change.

## Proposed stage order

The initial design retains the existing 3,200-event stream and its disjoint chronological splits, then adapts the boundaries to create a genuine composed workflow:

| Stage | Proposed events | Learner use | Fresh-data requirement |
|---|---:|---|---|
| Initial fit and validation | 0–799 | Fit incumbent and a fixed candidate family; freeze candidate ordering/rules and all costs | No monitoring or certification claims use these labels |
| Incumbent monitor | 800–1,599 | Run the frozen Q1 paired-cost monitor against a declared reference | Must not reuse these labels for scout or certification |
| Candidate scout | 1,600–1,999 | If the monitor triggers, select one member of the already-frozen family | Future labels only; selection outcomes are excluded from certification |
| Candidate certification | 2,000–2,399 | Test the selected candidate against the incumbent at the declared deployment horizon and switching charge | Fresh block, independent conditional on the past under the registered synthetic DGP |
| Deployment and rollback | 2,400–3,199 | Deploy only after certification; monitor fresh candidate-versus-reference feedback and fall back if its rollback gate crosses | Forward feedback starts after promotion; no selection labels are recycled |

The initial-fit boundary at event 800 matches the current candidate-family splitter (25% of 3,200 events); the proposed monitor, target-scouter, and deployment blocks are each 800 events. Before freezing, the runner must demonstrate that a meaningful share of each run can reach every stage under the chosen query probabilities and that each stage has adequate label support. If not, revise boundaries in development only, document why, and freeze before calibration. A no-trigger stream ends the intervention pathway and leaves its reserved budget unused. After a trigger, the unused monitoring reservation may be transferred to the fresh Target-Scout block by the predictable rule `B_scout = min(320, 640 - labels_monitor - 160)`; its constant query propensity is `B_scout / 800` (therefore 0.20–0.40). The 160-label rollback reservation is protected before that transfer. This policy is selected using only completed-stage label counts, before any scout outcome is seen, and the global 640-label cap is checked pathwise.

The integrated harmful-adaptation profiles remain distinct. `harmful_adaptation_native` changes the incumbent policy to all-positive at event 1,600, exactly after the Q1 monitor window, so that no alarm during events 800–1,599 is the expected timing result. `harmful_adaptation_at_monitor` retains the stationary outcome law but applies the same policy update at event 800, to test Q1 response. The latter is a deliberate aligned development profile; never merge its metrics with the source-timed native profile.

The candidate family and scorer must be fixed before the first monitoring event. Repeated candidate search during monitoring is out of scope. A monitor trigger cannot cause re-fitting on the same monitoring data. Candidate scouting after the trigger chooses among the frozen family; certification uses a separate later block. Rollback tests only the declared deployed-candidate harm null.

## Nulls, errors, and assumptions

Do not combine unlike null hypotheses into one success rate. The staged system has at least three error events:

1. **False incumbent escalation:** a monitor alarm when the declared conditional paired incumbent-minus-reference cost mean is at most its materiality margin at each monitored event.
2. **False candidate promotion:** certification of a candidate whose expected paired gain does not exceed the amortized switching charge on the certification target population.
3. **False rollback:** rollback when the deployed candidate is not worse than its fallback by the declared rollback margin on the deployment population.

A starting familywise target is 0.05, allocated 0.02 to incumbent escalation, 0.015 to promotion, and 0.015 to rollback. Candidate-level promotion allocations must sum to at most 0.015 before outcomes are seen. These values are proposals only: the paper-faithful components and their software must support these inputs, and a fresh simultaneous null calibration must validate the complete state machine before any confirmation run. If trigger-conditional validity of later stages cannot be established under the simulated stream law, the combined confirmatory claim is not available; report component estimates separately.

The synthetic confirmation generator must provide independent stage blocks conditional on the frozen scenario schedule (or another proved condition sufficient for the stated conditional nulls). Serially dependent, recurring, reversal, delayed-label, propensity-misspecified, and performative settings are stress scenarios, not automatically covered cases. Their results are empirical unless a matching theorem is established. For a recurring scenario whose eventwise conditional null changes sign, do not use a weak running-average guarantee as a substitute for the conditional-mean guarantee.

## Resource contract and comparators

Use a per-method hard cap of 20% of the full 3,200-event stream: at most 640 queried labels, plus fixed declared compute and action caps. Reserve the 320-label monitoring cap and 160-label rollback reserve; allow up to 320 labels in the Target-Scout stage, with its cap computed by the predictable transfer rule above. Use a 0.40 request propensity in monitoring and `B_scout/800` in Target-Scout. The Target-Scout internal 50/50 split receives approximately half of its stage labels in each part. Rollback uses propensity 0.20. These rates are design choices that must be calibrated. Every method shares the same underlying outcome paths and event-level query uniforms where the request rule is the same. Report the realized label count, cost, updates, switches, monitoring/deployment events processed, and any unused reservation. A method may not exceed the hard total even if its stage reservations permit more.

Required methods:

- `continue`: incumbent remains deployed for the whole stream.
- Fixed periodic/always adaptation: same frozen candidate and same action-cost schedule, with no statistical gate.
- Q1 monitor only: alarm/fallback but no candidate search or promotion.
- Q2 certification and two-gate promotion/rollback without the upstream Q1 trigger.
- Fixed-candidate certification without scouting, with candidate 0 frozen by initial validation before Q1/Q2; include both a Q2-only arm and a Q1-triggered full-pipeline arm to isolate the value of scout selection.
- Full staged pipeline: Q1 trigger, fresh Q2 scout and certification, then Q3 deployment and rollback.
- Controller-gated versions of the Q2 and full staged workflows. After the independent promotion e-process certifies the selected candidate, the existing `InterventionController` chooses between `PROMOTE` and `CONTINUE`. Its expected-gain input is computed only from queried labels in the fresh certification block using inverse-propensity weighted paired costs, averaged over processed certification events and scaled to the deployment horizon. The controller subtracts the declared switching cost. It is an additional heuristic filter; certification remains a mandatory gate. Query labels remain a separate resource metric because the benchmark has no justified conversion from label count to decision-cost units.
- A resource-matched implementation of *When to Retrain* only if its finite-horizon forecast inputs, retraining penalty, decision quantile, and supported observation model can be faithfully reproduced. Otherwise report it in a separate horizon-matched panel and do not call the integrated comparison SOTA-complete.

ASI and Robust ASI answer fixed-horizon allocation/inference questions; they belong in a companion fixed-horizon panel unless a specific estimation subproblem is given a separate, matched budget and endpoint. RCCDA targets predictive-loss and update-resource control; include only on a task where its published assumptions and update-cost units can be reproduced. Do not merge these into the sequential monitor's detection table.

## Generator matrix and outcomes

At minimum, use stationary and benign-nuisance null controls, boundary-local harm, residual-variance change, recurring regimes, the native harmful-adaptation profile, the separately named `harmful_adaptation_at_monitor` profile, and a `post_promotion_reversal` stress profile. The native late-onset scenario tests an adaptation outside the Q1 window; the aligned variant tests monitor response. The reversal profile uses the harmful-adaptation stream through the fresh candidate-certification block, then from event 2,400 makes the predeclared all-positive incumbent action optimal by setting the label equal to that frozen incumbent action. Candidate policies remain fixed; candidate/incumbent disagreements therefore incur evaluable harm after promotion. This is a synthetic conditional outcome schedule, not a real-data claim. Freeze scenario probabilities and onset schedules before calibration. For each scenario report: false escalations by null, alarm frequency and delay, candidate selected, certification outcomes, harmful promotions, rollback sensitivity and timing, cumulative paired decision loss, intervention costs, labels, compute, cap violations, and paired seed-level uncertainty. Provide both all-seed endpoints and explicitly eligible-onset endpoints where onset eligibility varies; do not remove a no-onset run from the registered primary denominator.

Use development seeds to select only implementation details and diagnose power. Use a fresh calibration block for simultaneous null control, then a disjoint confirmation block for efficacy. Final seed IDs, generator/code hashes, candidate family, alpha weights, budgets, scalarization or Pareto metrics, stopping rules, exclusions, and bootstrap procedure must be frozen before confirmation. Cluster uncertainty by independent stream seed, not by individual event.

## Implementation gates and deliverables

1. **Contract gate:** serialize the event record and learner/evaluator separation; add tests for timing, delayed-label maturity, propensity, policy versioning, and oracle noninterference.
2. **State-machine gate:** wire Q1 trigger to fresh Target-Scout data, certification to fresh forward deployment data, and deployment to rollback. Assert no label reuse and enforce the total and stage caps on every stream.
3. **Development gate:** run a small CUDA smoke grid plus CPU smoke tests. Inspect stage reachability, power, costs, e-process bounds, and logs. Do not report smoke results as evidence.
4. **Calibration gate:** passed for the registered v1 synthetic null cells: zero errors among 1,000 eligible streams in each of two Q1 controls, the selected-candidate Q2 null, and the Q3 rollback null. Each 98.75% one-sided exact upper bound is 0.4372%; the independent verifier replayed all 1,266 Q3 attempts. This gate does not establish efficacy or cover unregistered nulls. A changed policy or protocol requires a new calibration.
5. **Confirmation gate:** run the frozen scenario matrix on independent GPU seeds, save Parquet trial metrics, figures, manifests, source/data hashes, and the report. Use PaperBanana for scientific figures as requested; it was unavailable in the prior execution environment, so any figure work must first verify the connector is accessible.
6. **Baseline gate:** faithfully reproduce the strongest applicable published intervention baseline or document a source-based incompatibility. Local heuristics do not satisfy this gate.

## Current decision

This protocol remains a design draft, not a frozen efficacy experiment. Existing evidence independently supports Q1 and Q2 components, and the two-gate benchmark supports a separate component workflow. The first common-stream Q1 → Target-Scout → rollback pilot has a 10-seed-per-profile matched comparison over six profiles and five policies. The seven-policy, two-seed CUDA development grid exercised the controller-gated Q2 and full-pipeline arms across seven profiles. In the reversal profile, one promoted stream crossed rollback after 138 deployment events and 21 labels, with −320.10 realized incremental utility before fallback; the other stream did not promote. The runner represents the separate native event-1,600 adaptation as well as the aligned event-800 variant. The controller uses queried certification-block outcomes only and cannot override a failed promotion certificate.

The v1 synthetic null calibration has passed: 0/1,000 false escalations in each Q1 control, 0/1,000 false promotions conditional on Q1 triggering and scout selection, and 0/1,000 false rollbacks among independently verified beneficial deployments. Simultaneous one-sided exact upper bounds are 0.4372%; all eligible streams stayed under the 640-label cap. This supports the implementation under these registered synthetic assumptions only. It does not measure net utility or validate delayed, dependent, recurring, performative, or real-data settings.

Remaining work is a matched GPU development comparison including the fixed-candidate arm, a disjoint integrated efficacy confirmation, an eight-profile comparison with the required baseline set, the source-based published-comparator audit, and suitable real-data confirmation. Current development evidence has not shown that Q1 monitoring, scout selection or the controller adds utility over simpler alternatives. Richer query/retraining/fallback action choices also need a defensible cost contract. New algorithm development remains NO-GO until these comparisons identify a measured, reproducible deficiency. If the finite-horizon and sequential estimands cannot be joined while preserving valid inference, report linked panels and avoid an unsupported unified guarantee. See the [controller smoke report](integrated_controller_smoke_report.md), [reversal development report](integrated_reversal_development_report.md), and [calibration results](integrated_results.md).







