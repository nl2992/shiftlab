# Target-Scout comparison information-flow audit

**Audited:** 2026-10-26. This audit covers the exact reusable candidate family
and three monitor functions used by the Q2 fixed-split comparison and its
fresh null calibration.

## Data flow

Candidate actions are constructed from learner features `x`, training labels
`y[:train_end]`, and validation labels `y[train_end:validation_end]` in
`_fit_candidate_family`. The `probability_true` input is used to form
`h_truth`, the evaluator's expected candidate gain. Query propensities use the
source model's `probability_hat`, proxy expected gains, and validation-only
quantities; target labels are not used to set query probabilities.

The fixed-split candidate mapping uses validation labels and context assignments
only. Target-Scout uses queried labels from its registered first target slice
to choose its mapping. All three certification processes use only their
registered target outcomes, query flags/propensities, candidate contrasts, and
bounded betting updates. In the source, every access to `family["h_truth"]`
occurs after the relevant betting loop, for evaluator-only monitor-null and
future-net-gain reporting. Candidate choice, query schedules, certification
crossings, and promotion decisions do not depend on `h_truth`.

## Executable check

`tests/test_target_scout_fixed_split_calibration.py::test_oracle_truth_cannot_change_selection_or_certification`
replays a CPU seed through pooled rank, fixed split, and Target-Scout, then
changes only evaluator `h_truth` to an extreme constant and reruns the methods.
The selected candidate IDs, promotion decisions, label counts, processed event
counts, and stop reasons are identical. The check passes with the current
implementation. It is a targeted noninterference regression test; it does not
replace a broader architectural separation of learner and evaluator objects.

## Provenance and limitation

Audited source SHA-256: `src/shiftlab/dive/budgeted_promotion.py` at
`8eada2f9fc4e8c2c57f681e157d1b8d97a48fae054d55cc74749fa5b0339fc4f`.
The source functions receive a shared family mapping that contains evaluator
metadata, so this guarantee currently rests on code-path review plus the
metamorphic test. A future refactor should pass a learner-only view to selector
and certification code and keep truth arrays in a separate evaluator object,
provided all historical hashes and results are preserved.
