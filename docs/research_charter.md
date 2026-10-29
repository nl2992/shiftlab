# ShiftLab research charter

> **Active-direction update — 2026-10-28:** The user has selected one methodological contribution
> in budget-aware model switching under delayed feedback. The governing execution goals and
> precedence over earlier benchmark-paper plans are in
> [budgeted switching research goals](budgeted_switching_research_goals.md). The three questions
> below remain motivation and scientific safeguards; they are no longer three intended papers.

**Status:** Governing research direction and decision record  
**Updated:** 2026-10-22, integrating the supplied ShiftLab Research and Agent Pack and the user's
decision-harm formulation.  
**Scope:** Three candidate research contributions; evidence may justify narrowing, combining, or
dropping them. Venue targets are aspirations, not claims of novelty or acceptance.

## Research objective

Study how to detect, quantify, and mitigate **decision harm under distribution shift**. Distribution
change is not itself the operational target: deployed actions incur costs, outcomes may arrive late
or selectively, and interventions consume resources and may make outcomes worse.

Keep these quantities distinct:

\[
\underbrace{D(P_t,P_0)}_{\text{distributional change}},\qquad
\underbrace{R_t(f)-R_0(f)}_{\text{predictive degradation}},\qquad
\underbrace{R_t(\pi_t)-R_t(\pi_{\mathrm{ref}})}_{\text{decision harm}}.
\]

They answer different questions. A large discrepancy can be benign; prediction error can rise without
changing the selected action; and action-level cost can worsen near a costly decision boundary with
only a small global distribution change. Use an explicit fallback or challenger policy for the
decision comparison. That comparator can be more identifiable than regret against an unknown
Bayes-optimal policy. Reserve oracle regret for controlled synthetic evaluation, with oracle details
held in evaluator-only data.

## Candidate papers

### Paper 1: sequential monitoring of decision harm

The first paper asks whether a monitor can detect materially adverse downstream decision loss
relative to a specified reference while avoiding escalation for benign shifts. Its proposed target is

\[
H_0:\quad
\mathbb E\!\left[c(\pi_t(X_t),Y_t)-c(\pi_{\mathrm{ref}}(X_t),Y_t)
\mid\mathcal F_{t-1}\right]\leq\epsilon.
\]

Equivalently, for the paired excess score
`Z_t = c(pi_t(X_t),Y_t) - c(pi_ref(X_t),Y_t) - epsilon`, the candidate null is
`E[Z_t | F_{t-1}] <= 0`. This is a proposed formal setting, not a result already established by
choosing an e-process. Before making an anytime-valid claim, specify and justify:

- the information filtration and when each covariate, action, policy choice, query, label, and loss
  becomes available;
- whether feedback is complete, delayed, queried with known predictable propensities, or selective
  and action-dependent;
- predictable selection of the deployed and reference policies, including any resets or repeated
  testing;
- dependence assumptions and the exact conditional or marginal guarantee;
- positivity and variance implications for adaptive label sampling; and
- how counterfactual reference-action losses are observed or identified.

An e-process alone does not prove validity. A shift alarm is a diagnostic signal, not evidence that
the deployed policy is harmful and not automatic authorization to retrain. Detection, escalation,
promotion, and rollback are separate decisions with their own error and cost accounting.

Compare against direct paired-loss monitoring and established risk monitors as well as generic
feature-shift sentinels (for example, two-sample tests, CUSUM/EWMA, and ADWIN), at comparable
information and false-alarm budgets. First map failure modes: benign nuisance change, localized
harm near a decision threshold, prediction degradation without decision harm, changing costs,
delayed/selective labels, dependence, recurrence, and harmful adaptation. Build a new method only
when a reproducible limitation of strong existing methods identifies a defensible contribution.

### Paper 2: statistically certified adaptation

Paper 2 asks whether a proposed replacement has positive **net decision benefit** before it is
promoted. Freeze the candidate before fresh forward-time shadow evaluation; account for candidate
selection, multiple versions, update/deployment costs, promotion, and rollback. Detecting incumbent
harm does not certify that a replacement is better. Candidate evaluation must remain independently
testable without the new Paper 1 monitor. Where actions change outcomes, paired offline labels alone
do not identify counterfactual policy value; use a justified randomized or causal design, or narrow
the claim.

### Paper 3: budgeted active adaptation

Paper 3 asks how to allocate limited labels, monitoring, calibration, updates, retraining, switching,
or fallback actions. Start with a restricted finite-action setting and explicit feedback, compute,
and intervention budgets. Seek a falsifiable algorithmic or theoretical improvement against
cost-aware baselines; do not simply wrap Papers 1 and 2 in a heuristic controller or extend a
restricted regret theorem to arbitrary deep adaptation without proof.

Conformal prediction and uncertainty estimates support these tracks but are not, by themselves, a
separate novelty claim. Each candidate paper must stand on a distinct problem and evidence base;
combine or drop tracks if independent contributions do not emerge.

## Evidence strategy

Use controlled synthetic streams to identify failure modes because their change times, conditional
laws, and oracle costs can be known. Include stationary controls, benign high-dimensional nuisance
shifts, localized harmful changes, shifts in prediction loss without decision harm, variance and
tail changes, delayed/queried feedback, recurring regimes, and negative-transfer updates. Validate
generator properties independently and keep oracle truth inaccessible to evaluated methods.

Use real datasets to test robustness and external relevance, not to invent ground-truth shift labels.
The existing CRSP panel is a retrospective application stress test: market periods are not causal
change labels, and the retrospective close event clock is not verified feature-publication timing.
Real-data analyses must state the target, cost assumptions, timing limitations, and chronological
protocol. The current synthetic and real-data reports are evidence about implemented baselines, not
proof of the proposed papers' methods or guarantees.

Predefine the estimand, null, comparator, information access, feedback regime, thresholds, primary
metrics, and test windows before confirmatory runs. Report false escalation, detection power and
delay (including nondetections), cumulative excess decision loss, feedback/sample use, intervention
costs, and uncertainty appropriate to dependence. For serial or panel data, do not treat rows as
independent; use a justified block or cluster design. Keep smoke runs and exploratory plots separate
from locked evaluation.

Paper-specific primary outcomes should match the question: **Paper 1** reports probability of any
false escalation under the null, power by a fixed horizon, unconditional/censored detection delay,
excess decision loss before and after escalation, and labels consumed; **Paper 2** reports the rate of
promoting non-improving candidates, net decision benefit, promotion delay, rollback, and multiplicity
control; **Paper 3** reports cumulative net decision loss, labels and compute consumed, intervention
counts, and the utility-versus-resource frontier. Compare methods with matched information access and
appropriate false-alarm or promotion-error budgets. Include simple direct-risk and conservative
no-action baselines; a generic feature detector alone is not a sufficient comparator.

## Relationship to current repository work

Phase 1 data and benchmark infrastructure is substantially implemented; use
[`phase1_completion_audit.md`](phase1_completion_audit.md), the relevant validation reports, and
each paper's research log for exact status. Existing directories are retained for continuity:

The next experiment sequence after the recent acquisition comparisons is recorded in
[`next_phase_plan.md`](next_phase_plan.md). It prioritizes calibrated decision-harm monitoring,
matched-budget comparisons, and then separate candidate certification and budgeted intervention.

- `papers/paper1_decision_drift`: current decision-loss and drift baselines, not yet the proposed
  anytime-valid decision-harm method;
- `papers/paper2_adaptive_conformal`: conformal baseline work that supports uncertainty evaluation;
- `papers/paper3_cost_aware_adaptation`: current prediction/adaptation-cost baselines, not yet the
  proposed joint budgeted selection of labels and interventions.

Do not rename or reclassify existing results as a new method without a validated implementation and
paper-specific evidence. The next research task is to audit existing methods against the charter,
identify the strongest unresolved failure mode, and design a narrow, falsifiable model extension
and protocol. Do not launch large sweeps before that gap is established.

## Closest-work and novelty discipline

The supplied research programme names sequential risk monitoring, WATCH, prediction-powered risk
monitoring, harmful-shift detection without labels, monitored test-time adaptation, and online
conformal prediction as starting points for a literature audit. Treat this list as a research lead,
not a verified novelty analysis. Before priority or comparison claims, verify the current papers,
assumptions, estimands, feedback regimes, dependence conditions, code, and theorem scope from primary
sources. Record what is precisely new relative to the strongest method with the same estimand and
information access. If direct paired-risk monitoring matches the proposed contribution, report that
negative result and narrow, pivot, or stop.
