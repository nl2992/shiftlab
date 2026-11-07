# Wild-Time arXiv F8 transfer protocol

**Status:** frozen before acquiring the official arXiv tensor archive or inspecting validation or
test outcomes. This tests transfer of the Failure Atlas F8 rare-informative-pair scenario to a new
chronological text-classification source. The static challenger is a conventional control, not a
novel method.

## Question and claim boundary

On a fresh chronological arXiv stream whose validation period matches the Atlas F8 profile, does
choosing the later-trained model before deployment and holding it fixed beat CAMS and the registered
online selector panel under the same label and switch budget? The only prospective information used
to select the model is the designated 2017 validation period. Test outcomes cannot affect model,
policy, costs, code or eligibility.

A positive result is one chronological dataset-level transfer result under a simulated label delay.
It is not cross-domain generalization, operational deployment evidence, causal utility, or a
guarantee under serial dependence. A negative or ineligible result will be retained as such.

## Source and chronology

- Source: Wild-Time official arXiv dataset, obtained through its official repository at commit
  `23b0696dc82479a0689d678f44328153a19527e1`; official README identifies arXiv data as CC0.
- Source fields: arXiv `update_date`, title and primary category as used by Wild-Time. Event time is
  `update_date` at its available date resolution, with arXiv ID as stable tie-breaker. This is an
  update-time retrospective ordering, not verified original submission or category-publication
  time. The current metadata snapshot may revise categories.
- Training window for incumbent M0: 2007-01-01 through 2012-12-31.
- Training window for challenger M1: 2013-01-01 through 2016-12-31.
- Validation and model-choice window: 2017-01-01 through 2017-12-31.
- Untouched test window: 2018-01-01 through 2022-12-31.
- Stable ordering within a timestamp is arXiv ID ascending. No sample is randomly reordered for
  prediction or evaluation.

The task label set is the intersection of categories observed in both model-training windows,
computed from training metadata only. Rows outside that shared label set are ineligible and counted
by year; no test-derived category frequency or label mapping is allowed. This keeps both frozen
models' prediction spaces identical and limits any conclusion to the shared-category task.

## Frozen model pair

Both models use the same stateless `HashingVectorizer` with word unigrams and bigrams, lowercase,
`n_features=2^18`, `alternate_sign=False`, L2 normalization, and fixed token pattern
`(?u)\\b\\w+\\b`. Each uses `SGDClassifier(loss="log_loss", alpha=1e-5, max_iter=5, tol=None,
random_state=1729, average=True)`. M0 is fit only on eligible records in its incumbent training
window; M1 only on eligible records in its challenger training window. No title, label, category
count, or preprocessing statistic from validation or test is used to fit either model. Record model
and feature-code hashes before opening test outcomes.

## Validation gate and fixed decision

On 2017 only, calculate disagreement frequency, M1 accuracy conditional on disagreement, and
overall accuracy for each model. The F8 target gate passes only when disagreement is in `[0.01,
0.05]` and M1 accuracy conditional on disagreement is at least `0.85`. If it passes, the static
candidate is fixed to M1 for the entire test period. Otherwise stop this dataset lane without
computing any test-policy or test-cost metrics. Do not alter the model pair, gate or windows.

## Replay and comparator panel

Use non-overlapping contiguous episodes of 2,000 eligible test events; discard and report a final
incomplete episode. Reset each policy at episode start. Each event reveals both model predictions;
labels are requested only through the common acquisition interface. A requested label is released
at `update_date + 24 hours`; requests at a timestamp occur before labels released at that timestamp.
This one-day delay is simulated because source release logs are unavailable.

Contract per episode: `T=2000`, pathwise label cap `B=200`, label price `0.05`, switch price `5`,
and `alpha=0.05`. Candidate: always deploy validation-selected M1, use zero labels, pay one switch
cost at episode start. Primary comparator: CAMS adapter, the strongest Atlas F8 published-method
comparator in the frozen synthetic discovery table. The full secondary panel is fixed to CAMS,
Model Selector adapter, Model Picker adapter, Online LLM Picker, Gong-Zhang, Qiu, Xu acquisition-only,
SMCS+retain-incumbent, RMM, E_rb, PFA-SR with its registered host, gated deployment and never-switch.
All methods receive the same prediction stream, episode boundaries, label-release queue and costs.
Methods without support for timestamp-aware release must be adapted only at the queue boundary; their
acquisition, inference and thresholds remain unchanged and the adapter is documented.

Primary outcome is net cost: predictive error + label expenditure + switching expenditure. Report
all three terms separately, labels, switches, promotions, rollbacks and time to first deployment of
M1. Confirmatory pass requires the static candidate to save at least 5 units per 2,000-event
episode versus CAMS, with a paired one-sided 95% moving-block bootstrap upper bound below zero for
candidate-minus-CAMS. Resample whole seven-day event-time blocks within calendar year, then aggregate
episodes; report year-level estimates and all source rows. This is one source cluster and cannot
support a pooled multi-source claim.

## Data and outcome handling

1. Freeze and hash this protocol, runner, model implementation and baseline registry.
2. Acquire the official source without inspecting validation/test metrics. Record upstream URL,
   commit, license statement, retrieval time, bytes and SHA-256.
3. Fit both models and compute only train-derived shared label set and 2017 validation gate.
4. Persist validation eligibility, model hashes and an exclusive test-opening marker before test
   predictions or outcomes are accessed.
5. Generate predictions in event order, write only the ordered prediction-stream hash and aggregate
   metrics to Git, keep raw article text and row-level outcomes local.

If the official archive is inaccessible, does not contain the registered periods, or has fewer than
2,000 eligible events in a test year, report the specific coverage issue and stop without substituting
another source or shifting dates.
