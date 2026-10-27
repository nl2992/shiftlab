# Gas Sensor batch-held-out candidate-selection development protocol

**Status:** frozen exploratory protocol, 2026-10-26. This is a retrospective
coarse-domain evaluation, not a historical online replay or independent
confirmation. Later batches have appeared in prior repository diagnostics.

## Source and task

Use the locally verified UCI Gas Sensor Array Drift processed release
`10bbca34ef1b5061a374` (13,910 rows, 128 continuous features, six gas classes,
10 source-ordered batches). Verify the processed manifest and observations
hashes before running. Use only `features` as model input. `domain_id` supplies
the coarse batch label; target labels and batch IDs never enter the model.
There are no verified within-batch timestamps or label-release times.

## Frozen batch roles

- Batches 1–3: fit the fixed incumbent.
- Batches 1–5: fit the adaptation candidate bank.
- Batch 6: select one candidate separately for each prespecified loss matrix.
- Batches 7–10: evaluate the locked candidate against the incumbent once.

The row-random `split` field is ignored because it mixes source batches and
would not test domain transfer. Candidate training may use batch 5, but no
batch-6/7–10 labels enter fitting. The split is based on source batch order;
within-batch ordering is not assumed.

## Candidate family and costs

Fit multinomial linear softmax models using PyTorch with CUDA when available
and CPU fallback otherwise. The incumbent is fitted on batches 1–3 with
weight decay 0.01. The candidate bank is fitted on batches 1–5 with weight
decay in `{0.0001, 0.01, 1.0}`. Imputation is not performed: all 128 input
features must be finite. Centering and scaling use the respective training
pool only. Training uses a fixed seed and a fixed optimizer/epoch schedule;
no validation-based early stopping is used.

Select among the no-adaptation incumbent and the updated candidate models by
the lowest mean action cost on batch 6, considering
three matrices: symmetric unit misclassification cost; class-6 errors at cost
2; and class-6 errors at cost 5. Correct classifications cost zero. These
are imposed research scenarios inherited from the existing Gas Sensor group
diagnostic, not application utility. For probabilistic outputs, choose the
minimum posterior expected-cost class. Report accuracy, macro-F1, multiclass
log loss, Brier score, and decision cost separately.

## Analysis and limits

Report validation selection scores and test outcomes by each of batches 7–10,
along with the row-weighted and equal-batch averages. Describe feature-centroid
distance from the fit pool as a distributional diagnostic; keep it separate
from prediction and decision outcomes. Do not attach row-iid confidence
intervals: there are only four evaluation batches, and within-batch dependence
is unknown. Treat all estimates as descriptive. The existing data have prior
analysis exposure, so neither batches 7–10 nor this fixed protocol qualify as
independent final confirmation. No e-process, population-average type-I claim,
real decision utility claim, or within-batch detection-delay claim is made.

## Stopping and integrity checks

Stop with a recorded failure if source hashes, feature finiteness, six-class
support in each required fit pool, deterministic model outputs, or split
disjointness checks fail. Do not alter the frozen batches, candidate family,
costs, or selection metric after reading batches 7–10 outcomes. Store only
aggregate metrics, protocol/configuration, hashes, runtime and environment;
write no observation rows to the output directory.
