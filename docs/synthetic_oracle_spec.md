# Structured synthetic oracle specifications

Every synthetic version now stores a `structured_oracle_specification` in its evaluator-only
`dgp.json`. It records the conditional-mean formula, residual law, scale formula, exact
discrete regime values (or representative values for continuously varying schedules), and
regime-specific coefficients, costs, class priors, feature correlations, mixture probabilities,
delays, missingness and imposed retraining cost where applicable. The full temporal schedule
and original `SyntheticConfig` remain alongside it. The callable functions
`shiftlab.data.synthetic.conditional_mean` and `conditional_scale` provide independent
evaluators for per-sample truth; tests compare these functions against generated evaluator
rows for every registered scenario.

For smoothly varying linear, sigmoid and seasonal schedules, the specification includes the
minimum, median and maximum weights and points to the complete transition interval or change
schedule. Discrete schedules retain every distinct regime value, up to the configured limit.
Concept-shift checks verify that the feature moments remain stable while the exact conditional
function changes. The formulas preserve the intended distinctions between coefficient,
nonlinear, interaction, latent-offset and conditional-variance changes.

For `dependent_errors`, `conditional_mean` is the marginal expectation given current features.
`conditional_mean_given_history` is the exact one-step mean when the previous standardized
residual is available, and `conditional_radius_90` uses the innovation scale. The first sample
uses the stationary marginal law because no prior residual has been observed. When feedback is
delayed, this history oracle is evaluator-only until the previous label becomes available.
`radius_90` retains its separately named marginal temporal target. All oracle columns remain in
the evaluator-only Parquet file.

Regenerate a synthetic version through the normal CLI, for example:

```powershell
python -m uv run python scripts/generate_synthetic.py --root data --config configs/data/synthetic/smoke.yaml
```
