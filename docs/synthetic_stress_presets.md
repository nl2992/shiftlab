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
