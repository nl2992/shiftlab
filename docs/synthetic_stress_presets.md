# Named synthetic stress presets

`shiftlab.data.synthetic.decision_stress_catalogue()` returns ten named scenarios for
decision-relevant versus irrelevant changes. Each entry includes its `SyntheticConfig`,
policy class, loss, oracle policy, learner-visible context and expected contrast. The
generator keeps decision costs and feasibility in `decision_context`; conditional laws,
optimal actions and oracle risks remain evaluator-side. Utility values are imposed research
controls, not estimates of application costs. The two rare-event cases use distinct cost and
score settings to separate high-cost events from decision regret under a small global score
change. The prediction-only preset uses symmetric costs so positive rescaling changes the
regression target while preserving the zero-threshold action.

`shiftlab.data.synthetic.conformal_stress_catalogue()` returns twelve cases covering
homoskedastic, changing variance, heteroskedastic, heavy-tailed, asymmetric, dependent,
hidden-regime, extreme-event, recurring, delayed-label and missing-label stresses. Each case
states the calibration target scope (`conditional` or `marginal`), residual law, stress and
oracle-radius scope. Hidden-regime cases explicitly distinguish the global marginal
calibration target from evaluator-only per-regime radii. Dependence still requires
dependence-aware uncertainty estimates; pointwise oracle-radius coverage is not an IID
confidence interval.

Example:

```python
from shiftlab.data.synthetic import decision_stress_catalogue, generate_chunks

case = next(
    item
    for item in decision_stress_catalogue()
    if item.name == "prediction_degradation_without_decision_degradation"
)
for learner_rows, evaluator_rows in generate_chunks(case.config):
    ...  # pass learner_rows and evaluator_rows to separate experimental paths
```

The evaluator stream must never be passed to a learner or included in the learner-facing
dataset export.

Run `python -m uv run python scripts/validate_conformal_presets.py` to regenerate five-seed
coverage evidence for all twelve conformal cases. The report compares marginal and
history-conditional split calibration radii with their evaluator-only oracle radii, checks
calibration label availability before the test boundary, and exports coverage by evaluator
regime. It uses known evaluator means to isolate residual quantile behavior; it does not
claim fitted-predictor or online guarantees.

Run `python -m uv run python scripts/validate_decision_presets.py` to regenerate descriptive
five-seed action-rate, oracle-risk and realized-loss evidence for all ten decision presets,
separated into baseline and shifted regimes. The known oracle Bernoulli variance is included
as a conditional standard-error reference. This does not evaluate a fitted policy, provide
across-seed confidence intervals, or ground the imposed cost matrices in an application.

Run `uv run python scripts/validate_fitted_decisions.py` to regenerate
`data/reports/fitted_decision_validation.json`. It fits a frozen standardized logistic policy
on training-partition event labels that arrived before the first test request. The policy uses
only features and declared per-request costs/feasibility; evaluator probabilities and test
labels are used only for scoring. Missing decision context receives an explicit symmetric
unit-cost fallback, exposing regret when downstream utility is hidden. Results are descriptive
five-seed comparisons for the ten named presets plus a supplemental hidden-utility
impossibility diagnostic, and all costs remain imposed research utilities.

Run `python -m uv run python scripts/validate_fitted_conformal.py` to compare the oracle-residual
diagnostics with a fitted Ridge predictor. It fits on train rows whose labels arrived before
calibration begins, reports a static split-conformal interval, and then runs a prequential
residual-quantile update during test. A test residual enters only after its label arrival and
only for a later prediction. The predictor stays frozen, isolating radius adaptation. The
report includes five-seed coverage and two moving-block interval sensitivities per case.
These are empirical results: changing distributions and serial dependence do not receive a
finite-sample coverage guarantee.

`shiftlab.data.synthetic.allocate_update_budget` solves an evaluator-only 0/1 budget allocation
over independent update proposals with additive expected-loss benefits and integer compute
costs. It reports the exact selected portfolio under the specified budget. It is an oracle
reference for discrete allocation, not a learned scheduler; benefits must not be exposed to a
learner, and overlapping interventions or interactions between updates require a richer state
model.
