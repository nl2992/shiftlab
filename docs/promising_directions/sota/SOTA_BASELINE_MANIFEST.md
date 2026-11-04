# SOTA baseline manifest

Gate: **EXPLORATORY SUITE RUN COMPLETE — SOTA GATE NOT MET.** The objective is five real-data cases
that beat every mandatory applicable competitor on

    net_cost = prediction_loss + label_price * requested_labels + switch_cost * deployment_switches

Beating P3b does not satisfy it. Nothing in the existing `B3_PLUS_*` documents counts toward this
gate, and those results remain as they are.

## 1. Source verification (checked 2026-11-03, before any implementation)

Every source was fetched and confirmed to exist. No citation here was taken on trust.

| # | Source | Identifier | Verified | Author code | Clone |
|---|---|---|---|---|---|
| 1 | Liu et al., Contextual Active Model Selection (CAMS), NeurIPS 2024 | arXiv:2207.06030 | yes | `xuefeng-cs/Contextual-Active-Model-Selection` | 44 .py |
| 2 | Karimi et al., Online Active Model Selection for Pre-trained Classifiers, AISTATS 2021 | PMLR v130 | yes | `DS3Lab/online-active-model-selection` | 28 .py |
| 3 | Okanovic et al., Model Selection with Limited Labels, AISTATS 2025 | PMLR v258 | yes | not located yet | -- |
| 4 | Hara et al., Active model selection: a variance minimization approach | doi:10.1007/s10994-024-06603-1 | yes | `sato9hara/active-model-selection` | 11 .py |
| 5 | Xu, Karampatziakis, Mineiro, Active anytime-valid RCPS, NeurIPS 2024 | arXiv:2406.10490 | yes | `neilzxu/active-rcps` | 12 .py |
| 6 | Arnold et al., Sequential model confidence sets | arXiv:2404.18678 | yes | not located yet | -- |
| 7 | Lamaakal et al., Drift2Act | arXiv:2603.08578 | yes | not located yet | -- |
| 8 | Turrin et al., Online LLM Picker | arXiv:2610.01592 | yes | not located yet | -- |
| 9 | Reyzin, Saha, Wu, Expert Advice with Costly Observations, UAI 2026 | PMLR v337 | yes | n/a (theory) | -- |

Clones are under `vendor_sota/`, which is gitignored: third-party code is not vendored into this
repository, and the exact commit of each clone is recorded in the validation document.

## 2. Classification of each comparison

Per the instruction that native guarantees do not transfer to adapters, each competitor is
labelled by how it is being used.

| Competitor | Class | Why |
|---|---|---|
| CAMS | native reproduction + end-to-end adapter | Has a prediction action and a query rule; needs a deployment-switch charge it never defines |
| Model Picker | native reproduction + end-to-end adapter | Native prediction samples from the posterior; the deployment adapter uses its recommendation |
| Model Selector | native pool reproduction + causal adapter | Published method is pool-based with retrospective labelling; streaming use is an adaptation |
| Variance minimization | native pool reproduction + causal adapter | LURE correction assumes pool sampling; a streaming IPW variant is a different estimator and gets a different name |
| Xu et al. | component adapter | Acquisition component inside our certification machinery; its labelling constraint is not our hard cap |
| Sequential model confidence sets | component adapter | An inference component; a confidence set is not a switching policy and needs a deployment rule attached |
| Drift2Act | applicability assessment | Action space is recalibration/TTA/rollback/retrain; our two-frozen-model task supports only a restriction of it |
| Online LLM Picker | source review | Applicability to classification streams to be established from the full paper, not the title |
| Expert Advice with Costly Observations | source review | Its model charges per expert observed; one label here reveals every frozen model's loss, so the cost model may not map |

## 3. Fidelity findings recorded before porting

**Model Picker (read from `src/methods/model_picker.py`).** Algorithm 1 is:
`eta_0 = sqrt(ln M / 2)`, `eta_t = eta_0/sqrt(t)`, `posterior ∝ exp(-eta_t * loss)`,
`u_t = tuning_par * max_c (p·loss_c)(1 - p·loss_c)`, querying only inside the disagreement region,
with `u_t <- max(u_t, eta_t)` when positive, and an importance-weighted update
`loss += 1{pred != y}/u_t`. The prediction action **samples** a model from the posterior each
round; the recommendation is separate.

**A budget-handling discrepancy that must not be papered over:** the reference implementation does
**not** stop querying when the budget is exhausted. It keeps querying and updating `loss_t`, and
only stops *recording* queries into `z_t_budget`. Our task has a hard per-episode cap. Enforcing
the cap is therefore an **adapter decision**, it changes the algorithm's information state, and it
will be reported as such rather than presented as the published method.

**Degeneracy check required.** With two models and binary labels, `p·loss_c` reduces to the
posterior mass of whichever model is wrong for class `c`, so `u_t` depends only on how balanced
the posterior is and fires only in the disagreement region. Whether Model Picker's query rule
collapses to disagreement-gated sampling in our binary two-model setting is an empirical question
that must be checked and reported, because if it does, part of the comparison is weaker than it
looks.

## 4. Current comparison status (updated 2026-11-04)

The implemented default suite has now been run against P7s on five chronological UCI streams using
the actual frozen-model predictions and labels. P7s is cheaper than Gated Deployment on all five,
but loses to the best suite method on all five (Model Picker on four; Model Selector on
household_power). This is an exposed exploratory comparison with imposed label delays and costs,
not a confirmatory SOTA result. The corrected report and exact run artifact are
[`P7S_FRESH_REAL_SUITE_RESULTS_2026-11-04.md`](P7S_FRESH_REAL_SUITE_RESULTS_2026-11-04.md) and
`outputs/p7s_fresh_real_suite_screen_corrected/`.

Still outstanding: an untouched stream for the final comparison, an application-grounded query and
switching utility, and feature-dependent comparators that need unavailable covariates or nuisance
fits. Do not treat the exploratory screen as meeting the completion gate.
