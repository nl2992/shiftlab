# WILDS CivilComments candidate-selection development study

**Status:** frozen development protocol, 2026-10-26. This is an offline
common-label candidate-selection study. It does not simulate a live stream,
delayed feedback, online monitoring, or causal policy value.

## Question

On WILDS CivilComments, does selecting a binary decision rule on the official
validation partition reduce held-out test decision cost relative to a fixed
incumbent threshold, and how sensitive is that result to declared asymmetric
false-positive and false-negative costs? This supplies real-data evidence for
the simple sample-split candidate-selection baseline under Q2. It does not
test Target-Scout, DIVE, or the intervention controller.

## Data and information boundary

- Dataset: local processed WILDS CivilComments v1.0, version
  `c4f79606707951bcba11`; 448,000 records from the official WILDS train,
  validation, and test partitions.
- Inputs: text only from `inputs.parquet`; use a fixed, stateless hashing
  vectorizer with word unigrams/bigrams. No `metadata` field is a model input.
- Learner labels: train partition for fitting, validation partition for
  candidate selection, and no test labels until the selected policies are
  frozen.
- Evaluator-only test fields: target and article/identity metadata, used only
  for aggregate scoring and cluster uncertainty after selection. Do not write
  text or row-level test records to outputs.
- WILDS provides no verified per-row feature or label availability clocks.
  The official partitions are offline roles, not a temporal sequence.
- Prior use of the official test partition is not fully audited. Treat the
  result as exploratory development evidence, never independent confirmation.
- The protocol verifies that `article_id` clusters are disjoint across the
  three official partitions before fitting. On the inspected artifact there
  are 0 article-ID overlaps for train/validation, train/test, and
  validation/test; this guards article-level leakage but does not settle prior
  exposure of test metrics.

## Model and candidate policies

Construct one fixed 2^18-dimensional binary, L2-normalized hashed n-gram
representation. Fit three mini-batch torch logistic models on the
official training split only, using the NVIDIA GPU when available. Freeze
training at three epochs, batch size 8,192, Adam learning rate 0.05, and L2
penalties 1e-5, 1e-4, and 1e-3. The fixed incumbent is the 1e-4 model at
probability threshold 0.5.

For each of three predeclared cost settings, validation selects one policy
from the 15 combinations of model penalty and threshold `{0.25, 0.35, 0.50,
0.65, 0.75}` by minimum average validation cost. A tie resolves to the
earlier-listed model penalty, then the lower threshold. Costs are imposed
research sensitivities, not application utility:

| Setting | False-positive cost | False-negative cost |
|---|---:|---:|
| Symmetric | 1 | 1 |
| False-negative sensitive | 1 | 2 |
| False-positive sensitive | 2 | 1 |

All settings use the same labels, candidate policies, and prediction model
family. Identity annotations are not used to train, select, or act; they are
evaluator-only group summaries.

## Outcomes and uncertainty

Primary comparison: incumbent cost minus validation-selected candidate cost
on the official test partition (positive values favor the selected candidate).
Report candidate threshold/model, average cost for both rules, paired
difference, and a 95% percentile bootstrap interval clustered by `article_id`
(2,000 resamples, fixed seed 20261026). Holm-adjust three one-sided cluster
bootstrap tests across the cost settings. This interval describes uncertainty
across article clusters in this already-inspected dataset; it is not a
distribution-free certificate or a guarantee for a new domain.

Also report accuracy, Brier score, log loss, and worst identity-by-label-group
accuracy for the fixed incumbent and each selected candidate. Group accuracy
is descriptive because there is one dataset and no temporal replication.
Report train, validation-selection and test-evaluation label counts. Do not
convert the imposed loss units into money, claim campaign utility, or infer
online risk-control behavior.

## Stopping rule and outputs

Run the frozen three-model fit once, with deterministic data order and seeds.
No test-based tuning, additional threshold search, or second model family is
allowed under this protocol. If the GPU sparse training path fails, record
the failure and use an explicitly labeled CPU fallback only if it completes
with identical model and optimization settings.

The runner writes validation policy scores, selected test aggregates,
identity-group metrics, a report, and a manifest with processed dataset
version, file hashes, protocol/source hashes, environment, GPU, parameters,
cost assumptions, label counts, results, and limitations. Outputs contain
aggregates only. No figure is planned.

## Interpretation

The test partition is kept separate from the protocol's validation selection,
but previous repository use of this test split has not been fully ruled out.
The measured comparison is therefore exploratory, not an independent final
confirmation. Positive results establish only that the fixed-split procedure
can be evaluated on one acquired text-classification domain under the named
imposed costs. Negative results are equally reportable. This study does not
close the need for a second suitable real-data family or a genuine downstream
resource-allocation evaluation.
