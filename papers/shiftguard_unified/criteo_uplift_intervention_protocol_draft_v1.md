# Criteo Uplift v2.1 treatment-policy evaluation protocol (draft v1)

**Status:** **blocked / no-go pending primary-source clarification; not frozen, not preregistered, no policy results computed.** The source documents non-uniform negative-label sampling but not its inclusion probabilities. This prevents the proposed causal policy-value estimand from being justified for either the released population or the original advertiser population. Do not execute this protocol unless that issue is resolved.

## Research question and task boundary

Can conventional uplift models, evaluated using a separate randomized sample, select a treatment-allocation policy with higher fixed-horizon outcome value than no treatment, treating everyone, and random allocation under a prespecified capacity and treatment-cost frontier?

The unit is one user assignment from Criteo's compiled incrementality tests. Action is assigned advertising treatment `T`; outcome is either conversion or visit over the source-reported 14-day post-assignment collection window. Evaluate the two outcomes separately. The task is **fixed-horizon treatment-policy value and resource allocation**. It is not temporal distribution-shift monitoring, individual label acquisition, delayed-feedback monitoring, campaign revenue, or live deployment.

## Source, visibility, and limits

Use the pinned source `criteo/criteo-uplift@2424920019e49d52d72c13ac1143ec5d53af276b`, whose full-stream checksum and schema audit are in `../../data/reports/criteo_uplift_stream_audit.json`. The source was read completely for aggregate integrity checks, including arm-level outcome rates, but no candidate-policy value has been computed. Report this exposure. A row-level split may be held out from method-specific comparison, but do not describe the source as never inspected. The primary paper documents non-uniform negative-label sampling but gives no inclusion probabilities; do not assume a simple 0.85 treatment propensity identifies policy values after this sampling.

The primary source paper states that treatment was randomly assigned within advertiser tests, features were logged before assignment, and v2 was constructed to address treatment-feature confounding; it models observations as i.i.d. and reports a C2ST that did not reject `T ⟂ X`. The released 85% treatment fraction and the local MLP diagnostic (AUC 0.5076) are supporting diagnostics, not by themselves a proof of exact row-level propensities or independence after merging and subsampling. Before freezing this protocol, reconcile the effective assignment probability and label-sampling convention from the primary data documentation. The release has no advertiser/test IDs, user identifiers, event timestamps, or individual label-release times. The `exposure` field is post-assignment and is excluded from policy inputs.

The official Criteo page states CC BY-NC-SA 4.0 while its paper datasheet states CC BY-SA 4.0. Use the stricter official terms unless Criteo clarifies otherwise. Do not commit the raw source or a substantial derivative. Preserve the requested attribution and record the exact source and output license.

## Estimand

For fixed policy `π(X) ∈ {0,1}` and outcome `Y`, estimate the treatment-assignment value in the released benchmark population. Under known constant assignment probability `p`, the inverse-propensity score is

`ψ_i(π) = 1{π(X_i)=1} T_i Y_i / p + 1{π(X_i)=0} (1-T_i) Y_i / (1-p)`.

For a declared research-imposed treatment cost `κ`, report

`Vκ(π) = E[ψ(π)] - κ E[π(X)]`,

and the incremental value `Vκ(π) - Vκ(π_never)`. Also report the observed treatment fraction, conversion or visit value before cost, and the cost term separately. Do not call these costs revenue or profit. If the effective propensity cannot be justified after the source's sampling and merge procedure, do not use this causal estimand; downgrade the dataset to descriptive prediction/uplift ranking only.

## Candidate policies and comparators

Include no treatment, treat all, uniform random targeting at each registered capacity, and learned targeting policies trained without final-split outcomes. At minimum include the source paper's Two-Model/T-Learner and Modified Outcome (MOM) baselines. Add Class Variable Transformation (CVT) or another established uplift baseline if the implementation passes a source-paper correctness audit. Do not label an implementation a paper reproduction unless the original feature transform, tuning, metric, and split procedure are matched.

Candidate target policies are fixed before their evaluation sample is read. A policy may rank estimated uplift and treat the top eligible fraction; the capacity grid and the cost frontier must be chosen from source-independent task constraints or development data only. Compare direct policy-value estimators with IPW, self-normalized IPW, and a cross-fitted doubly robust estimator where their assumptions are met. Report effective sample size and weight concentration for every policy. Include a fixed-sample confidence procedure as the primary certification comparator. Only add an anytime-valid OPE comparator if its filtration and i.i.d./propensity assumptions map exactly to this row-level task; a shuffled source order is not real chronology.

## Split and information contract

Before method-specific evaluation, define a deterministic, row-index-only split from a recorded seed: 60% model training, 20% policy development/selection, and 20% final evaluation. The final partition is not used for fitting, policy choice, cost-grid choice, threshold selection, or debugging. The source-eligibility audit's full-file aggregate rates are disclosed, and no policy-specific score has been inspected. Keep the final partition sealed until models, candidates, cost/capacity grid, estimand, estimator, uncertainty method, and multiplicity handling are frozen.

Learner-visible model inputs are the 12 pre-assignment feature columns only. Training rows expose their assigned treatment and observed outcome according to the selected method's training algorithm. The final evaluator uses treatment and outcome only to compute off-policy value; it does not feed them back to the learner. Assignment, conversion, visit, and exposure cannot be conflated: the primary estimand is intention-to-treat on assignment, not effect of actual exposure.

## Uncertainty, multiplicity, and success rule

Use a paired user-level bootstrap over the fixed evaluation partition, reporting two-sided 95% intervals for every value contrast, alongside the estimator's effective sample size and weight diagnostics. This relies on user-level independence; the source provides no cluster identifiers, so that assumption must remain explicit and a cluster-robust claim is impossible. Prespecify one primary outcome, comparator, capacity/cost operating point, and minimum practically meaningful contrast using development data. Treat the remaining outcome/cost/capacity cells as a multiplicity-controlled frontier, not as independent confirmatory claims.

A positive result requires the frozen candidate's lower confidence bound to exceed the predeclared practical margin against no treatment and the strongest applicable conventional targeting baseline at the primary operating point, with no severe overlap failure. Otherwise preserve the result as null or negative. This benchmark can establish value only for the released source population and imposed cost model; it cannot establish temporal validity, future-shift robustness, or broader commercial utility.

## Freeze gate before any policy run

1. Confirm from the primary source whether `p=0.85` is the actual effective assignment propensity in the released v2.1 file after non-uniform negative sampling; verify whether it is constant across the merged experiments.
2. Confirm what population the non-uniform label sampling defines and whether the target is value in the released benchmark or a broader advertiser population.
3. Validate and document all candidate implementations, the exact deterministic split, cost and capacity grid, primary contrast, bootstrap, and multiplicity correction.
4. Confirm that the chosen noncommercial license terms are compatible with the planned research outputs; do not redistribute raw rows.

The primary source confirms that non-uniform negative-label sampling occurred but does not document its probabilities. Until Criteo clarifies the selection mechanism and the estimand it preserves, this protocol is ineligible for execution; no causal policy-value or intervention claim is supported by the released-file checks.
