# Integrated Q1–Q3 efficacy confirmation protocol v1

**Status:** frozen before execution. This is an independent-seed synthetic efficacy comparison, not real-data confirmation or a novelty test. **Freeze date:** 2026-10-26.

## Question and endpoint

Does the staged system that monitors incumbent harm, selects/certifies a candidate, and rolls back a harmful deployment improve cumulative downstream decision utility over continuing with the incumbent? Does the Q1 gate or Target-Scout selection add value over simpler staged controls?

The primary endpoint is per-stream **evaluator-expected cumulative paired-cost reduction net of declared switching/rollback charges**, `expected_incremental_utility`, in the method runner. Labels and model-update or intervention counts are separate resources; no conversion of label counts into decision-cost units is made. The paired realized-utility endpoint is secondary. All comparisons use independent stream seeds as the unit; event rows are not treated as independent replicates.

The frozen primary contrast family contains 22 one-sided tests of positive mean paired expected utility:

1. `full_pipeline` versus `continue` on each of `boundary_local_harm`, `post_promotion_reversal`, `recurring_regimes`, `residual_variance`, `harmful_adaptation_at_monitor`, and `harmful_adaptation_native` (6 tests).
2. `full_pipeline` versus `two_gate` on each of the eight registered profiles (8 tests), testing the incremental value of the upstream Q1 gate under this staged design.
3. `full_pipeline` versus `full_pipeline_fixed_certification` on each of the eight profiles (8 tests), testing the incremental value of Target-Scout over the frozen candidate ablation.

Use one-sided paired t tests at the stream level for the positive-mean alternatives and apply Holm correction across all 22 primary tests at familywise 0.05. Report paired mean differences with Holm simultaneous one-sided 95% t lower bounds using Bonferroni `alpha/22`; these are conservative, predeclared intervals. Also report two-sided 95% paired bootstrap intervals as descriptive sensitivity, with 20,000 resamples and seed `2026104101`. The secondary realized-utility contrasts and all rate/resource outcomes are descriptive; do not select a winner from them.

No single positive contrast supports a general superiority claim. A design-specific efficacy signal requires a Holm-adjusted primary p-value below 0.05 and a positive simultaneous lower bound, and must be reported only for that frozen profile/contrast. A system-level claim additionally requires that the full pipeline not show a materially negative expected-utility contrast against `continue` in either `stationary` or `benign_nuisance`; report both null-control contrasts and false intervention rates regardless of significance.

## Frozen stream design

- Run 100 independent seeds per profile: `2026104000` through `2026104099`. These are disjoint from the development block `2026103000`–`2026103029` and the separately registered 1,000-stream null-calibration blocks.
- Run all eight profiles: `stationary`, `benign_nuisance`, `boundary_local_harm`, `post_promotion_reversal`, `recurring_regimes`, `residual_variance`, `harmful_adaptation_at_monitor`, and `harmful_adaptation_native`.
- Run all nine registered methods: `continue`, `scheduled_promote`, `two_gate`, `two_gate_controller`, `q1_fallback`, `full_pipeline`, `full_pipeline_controller`, `fixed_candidate_certification`, and `full_pipeline_fixed_certification`.
- Use the current frozen 3,200-event state machine, costs, policies, stage boundaries, `640` hard per-stream label cap, and allocated alphas (`.02`, `.015`, `.015`). Use the NVIDIA CUDA device. The algorithm and generator are unchanged from the separately calibrated source; this confirmation changes the seed block and records its own immutable protocol/status.
- Each seed-method pair reuses the same generated covariates, outcomes, evaluator oracle and seed-derived query uniforms as the existing runner permits. Preserve the full learner-visible and evaluator-only event logs and do not release evaluator-only fields into learner decisions.
- Stop after all 100 seeds in all eight profiles and all methods. Do not tune thresholds, costs, candidates, scenarios, exclusions, or endpoints on this block.

## Required verification and outputs

The output must contain 7,200 seed-method metric rows, exactly 100 rows for each of the 72 profile-method cells, and 23,040,000 rows in each 3,200-event stream log. Independently verify unique keys, stage ordering, event visibility, query-propensity support, learner/evaluator field separation, all label caps, profile/method completeness, and SHA-256 hashes for sources, protocol snapshot, Parquet outputs, and generated tables. Recompute the primary endpoint from seed metrics, paired tests, Holm values and simultaneous lower bounds with an independent analysis script. Record CUDA hardware and environment. Preserve raw logs and all unsuccessful/no-action streams.

PaperBanana was requested for scientific visuals, but no PaperBanana connector is available in this execution environment. This frozen numerical confirmation therefore emits no figure; any later visualization must use PaperBanana when the connector is available and must not alter the frozen analysis.

## Interpretation limits

All synthetic counterfactual costs are evaluator-known; the learner receives only registered feedback. The environment is non-performative and labels are immediate. The null-calibration study supports only its registered synthetic nulls and assumptions. This experiment does not establish performance under delayed or selectively matured labels, serial dependence beyond the registered generators, action-dependent outcomes, finance, or other real deployments. It cannot establish that the method is novel or that results transfer to an untouched real dataset.
