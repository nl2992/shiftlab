# CUVET-Policy fixed-horizon cost-constrained evaluation protocol (draft)

**Status:** design draft only; not frozen or registered. No ShiftLab policy-value estimate has been computed, and the official test CSV body remains unread. The source paper has already reported results on this benchmark's test split, so that split is sealed only against ShiftLab development and cannot be described as a community-unseen holdout.
**Data version:** Hugging Face `anonadata/CUVET-policy`, revision `36583ac60379ed83fd375c84d2bf8ce1c73869c1`.
**Scope:** one fixed-horizon downstream resource-allocation task (Q3). This dataset does not test sequential monitoring, delayed feedback, or deployment-time adaptation.

## Research question and estimand

Can a context-dependent assignment policy increase expected source-scaled value while keeping expected source-scaled spend no greater than the reference multiplier-1 policy? The task follows the source paper's objective, `max E[value(policy(X))]` subject to `E[spend(policy(X))] <= E[spend(reference)]`. Value and spend are anonymized, scaled, and perturbed; all reported quantities must remain in source units and must not be described as dollars, profit, or realized production utility.

Each observation provides five released features, one assigned multiplier from `{0.8, 0.9, 1.0, 1.1, 1.2}`, and one observed value/spend pair. The learner may use the five features and outcomes available in its declared split. It must exclude the source row identifier and evaluator-only metrics from policy inputs. The paper describes randomized assignment and independent bidding opportunities; no event or outcome-release clock is provided.

## Information and split contract

1. **Policy fitting:** use only train rows with `is_val=0` to fit outcome/response models and construct policies.
2. **Policy selection:** use only train rows with `is_val=1` to select hyperparameters and choose among candidate policies under the reference-spend constraint.
3. **Final evaluation:** access the official test file once, after method code, candidate set, propensities, estimator, uncertainty calculation, and comparison table are frozen. No model or threshold changes may follow test inspection.

The train file has been fully streamed for aggregate checks; no raw rows were retained. The test file has only been inspected by metadata/HEAD. The released source says train/test were randomly split; whether the validation flag is a random split is described in the source paper/card and must be confirmed before treating the three partitions as independent.

## Assignment mechanism and identification assumptions

The source card and paper call the five arms randomized but do not disclose numerical assignment probabilities or the detailed design. The full train arm shares are `(0.08484, 0.09218, 0.60254, 0.10693, 0.11352)` in multiplier order. They varied by at most 0.057 percentage points across ten anonymized source-row-ID bands. A seeded feature-only audit of 845,867 train rows found no useful held-out prediction over a prevalence-only classifier (see `cuvet_assignment_predictability.json`). These diagnostics are compatible with stable arm-specific marginal propensities, but do not establish randomization, rule out hidden confounding, or verify the paper's independence claim.

The working identification assumptions for any causal policy-value interpretation are:

- consistency and no relevant interference between bidding opportunities;
- treatment assignment independent of potential value/spend outcomes, with constant positive arm probabilities over the target population;
- train/validation/test represent the same target population under the source's random split;
- the five released features are available to the policy before treatment assignment;
- the supplied value/spend outcomes correspond to the assigned multiplier and are not differentially selected by treatment.

These assumptions are not established by the feature-predictability diagnostic. Estimate arm propensities only from the non-validation training rows and propagate their uncertainty. Report sensitivity to arm-specific relative propensity perturbations of ±10%, renormalized to sum to one. If the assignment assumptions cannot be defended or conclusions change materially under that sensitivity set, present descriptive predictive results only and do not make causal policy-value claims.

## Candidate policies and comparators

The required comparison set is:

- **Reference:** assign multiplier 1.0 to every row.
- **Best feasible constant arm:** choose one multiplier using validation data only, subject to the reference-spend budget.
- **Outcome-model policy:** estimate arm-specific expected value and spend from non-validation training data; choose a context-dependent supported arm under the cost constraint, with model and tuning choice fixed on validation.
- **CUVET:** excluded on this release unless the source authors document an outcome encoding different from the released columns. The paper defines a bucket outcome as the per-arm conditional mean times common bucket population mass (Section C.1), so treatment-count-weighted raw sums are not the response curve. Released per-row means have `γ=-0.748` on `is_val=0`, violating the increasing-value assumption. Do not fit or evaluate CUVET by altering this response. Keep split-search adaptation and CF proxy ambiguities explicit in any future source-faithful reproduction.
- **Published task baselines:** use the source paper's reported baseline implementations when available and applicable. The paper's broader comparator discussion includes causal trees/forests, HTE-based assignment, and policy-tree methods; applicability and fidelity must be audited before the final comparator list is frozen.

No new ShiftLab intervention algorithm is proposed by this protocol. The outcome-model policy and constant-arm control establish straightforward reference points. The primary published comparator is CUVET, with the source paper's four comparator learners/configurations: causal forest with heterogeneity-score splitting (CF-Het), causal forest with MSE splitting (CF-MSE), clipped CUVET, and unclipped CUVET. The source uses EconML causal forests and a value-cost proxy outcome for CF because the forest accepts one outcome. CUVET clipping constrains leaf treatment to the observed arm interval; the unclipped variant only constrains it to be positive. The paper evaluates each learned partition with three budget solvers: continuous mCUV equalization, deterministic integer linear programming (ILP), and stochastic linear programming (LP). These are the correct published task comparators to include if they can be faithfully reproduced. A simplified arm-wise outcome model remains a transparent benchmark but must not stand in for any of them.

The source paper already used the official CUVET-policy test split for published evaluation. Its Table 2 reports relative value and spend uplifts, using ten bootstrap replicates and `1.96 × σ` intervals. For mCUV equalization, clipped/unclipped CUVET report value uplifts `0.0103 ± 0.0033` / `0.0098 ± 0.0036` and spend uplifts `0.0019 ± 0.0013` / `0.0010 ± 0.0010`; CF-Het / CF-MSE report value `0.0042 ± 0.0029` / `0.0055 ± 0.0036` and spend `0.0015 ± 0.0016` / `−0.0017 ± 0.0018`. Under ILP, clipped/unclipped CUVET report value `0.0149 ± 0.0100` / `0.0118 ± 0.0060` and spend `0.0045 ± 0.0038` / `−0.0013 ± 0.0021`. Under LP, the corresponding value uplifts are `0.0094 ± 0.0096` / `0.0155 ± 0.0109`, with spend uplifts `0.0035 ± 0.0043` / `0.0023 ± 0.0029`. These are source-reported contextual results, not ShiftLab replications. The mCUV and LP CUVET point estimates increase spend; the source's prose says “slightly violating” the budget, despite a nearby parenthetical that appears inconsistent with Table 2. Thus the paper's higher-value point estimates do not establish feasibility under this draft's stricter rule that the one-sided upper confidence bound on paired spend difference be at most zero. The paper's ten-replicate intervals also do not substitute for our prespecified paired uncertainty analysis.

An aggregate-only full-train response audit found that in `is_val=0`, per-row mean value has slope `γ=-0.7481` and mean spend has `η=0.2072`; `is_val=1` is similar. This fails CUVET's stated `γ>0` and `η>γ` assumptions. The paper's Section C.1 resolves the aggregation definition: bucket outcomes are per-arm conditional means multiplied by shared bucket population mass. Raw sums by treatment are count-confounded because arm shares are highly unequal, and are not an alternative valid fit target. Use no transformed outcome merely to force the expected ordering. Omit CUVET from this dataset-specific run unless source authors document a different encoding; retain published results as context and compare flexible supported-arm policies separately.

Two source ambiguities affect faithful comparator reproduction: Algorithm 1 leaves the feature-threshold candidate generator abstract, and the causal-forest proxy is `v − (γ/η)c` in Appendix H.4 but `v − (η/γ)c` in the synthetic-example appendix. No real-data CF proxy coefficient is unambiguously established by the paper. Until authors' code/configuration is recovered, report both a paper-informed adapted CUVET and transparently specified CF proxies, not a reproduction of the published baseline table.

## Evaluation estimators and metrics

For an outcome `Z` (value or spend), let `A_i` be the observed arm, `π(X_i)` the frozen policy arm, `p_a` the train-only estimated marginal arm probability, and `μ_a(x)` the train-fitted arm-specific outcome model. The test estimates are:

```text
IPW:  V_IPW(π; Z) = n^-1 Σ_i 1{A_i = π(X_i)} Z_i / p_{π(X_i)}

DR:   V_DR(π; Z) = n^-1 Σ_i [ μ_{π(X_i)}(X_i)
                              + 1{A_i = π(X_i)} (Z_i - μ_{A_i}(X_i)) / p_{A_i} ]
```

For the reference comparison, compute the same estimator for `π_ref(X)=1.0` and report paired policy-minus-reference differences in both value and spend. The cost constraint is feasible only when a one-sided upper confidence bound for `E[spend(π(X)) - spend(π_ref(X))]` is at most zero (the exact confidence level and multiplicity allocation must be frozen before test access). Do not use predictions from a model trained on the official test. Report:

- estimated expected value and spend in source-scaled units;
- paired differences versus the reference policy;
- reference-budget constraint gap and its one-sided uncertainty bound;
- allocation share assigned to each multiplier;
- IPW and doubly robust estimates side by side;
- sensitivity over the prespecified propensity perturbations;
- a cost/value frontier for feasible policies;
- compute time, memory, source revision, script hashes, and exact split counts.

For the prespecified propensity sensitivity, form `p_a(δ) = p_hat_a (1 + δ_a) / Σ_b p_hat_b (1 + δ_b)` for `δ_a ∈ {-0.10, 0, +0.10}` and evaluate all 243 vectors. Use a paired row bootstrap for test uncertainty, conditional on the stated independent-opportunity assumption, and a training-resampling layer for propensity estimation. Also report a paired influence-function interval as a check. These intervals quantify sampling variation under the assumptions; they do not repair an incorrect assignment or independence model.

## Stop and claim rules

- Do not open the official test body until the assignment-contract audit and comparator list are complete and this protocol has been versioned as frozen.
- Stop causal interpretation if treatment support is inadequate, propensity estimates are unstable, test split construction is not independent of training/validation, or source outcome selection is treatment-dependent.
- Do not claim sequential validity, real-time adaptation, future distribution-shift robustness, online campaign impact, or monetary profit from this task.
- A positive estimate is evidence for this source's fixed-horizon policy objective only; it is not evidence of ShiftGuard's full monitor-certify-intervene system.
- Preserve negative or inconclusive results and all analysis artifacts.

## Remaining pre-freeze work

1. Verify the source paper's exact train/validation/test construction and row-level independence statement; record that its published test evaluation limits claims of a novel untouched benchmark.
2. If pursuing a source-faithful CUVET reproduction, obtain author clarification for why released per-row outcomes violate the response ordering, and recover the complete EconML/CF configuration (including split candidates and the conflicting proxy coefficient). The paper's bucket aggregation itself is specified; unless the authors identify a different outcome encoding, mark CUVET inapplicable to these released outcomes rather than forcing an exponent fit.
3. Specify model classes, tuning ranges, budget tolerance, and a practical-effect threshold using development data only.
4. Define the exact bootstrap and propensity-sensitivity implementation and test it on synthetic data with known assignment probabilities.
5. Review the frozen draft independently before any test access.
