# Context-nested promotion pilot

This pilot integrates nested candidate-by-context alpha spending into the fitted 13-candidate, hard-label-budget promotion controller. Contexts are defined before monitoring by the learner-visible rule `x[0] >= 0`. Candidate rank weights are fixed on validation outcomes; context-volume weights use validation features only. The two nested methods split each candidate's rank allocation between equal-weight and validation-volume contexts. They are implemented only with the fixed-mixture e-process and a common global support bound.

## Run and artifacts

The pilot used 30 matched seeds per scenario, `n=3,200`, CUDA generation on an NVIDIA RTX 4060 Laptop GPU, the fixed-mixture monitor, uniform label acquisition, direct IPW, and 10%/20% hard label caps. It crossed pooled rank spending with equal-context and volume-weighted nested spending over six study scenarios and two null controls. No figure was generated.

```powershell
uv run shiftlab-dive-budgeted-promotion `
  --seeds 30 --seed-offset 20261024 --n 3200 --device cuda `
  --monitoring-rules fixed_mixture --query-policies uniform `
  --estimators direct_ipw `
  --alpha-allocations rank rank_context_equal rank_context_volume `
  --budget-rates 0.10 0.20 `
  --scenario-subset stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation candidate_family_null candidate_context_zero_mean `
  --skip-figure --output outputs/iter_context_alpha_pilot_20261024
```

The run produced 1,440 seed-level controller rows and 48 aggregate rows under `outputs/iter_context_alpha_pilot_20261024/`. The output directory is governed by the repository's existing output ignore policy; the command and summarized findings are versioned here. The Parquet files and manifest remain available in the local checkout.

## Preliminary results

At the 20% label cap, pooled rank spending promoted in 2/30 boundary-local-harm streams (6.7%; exact binomial 95% interval 1.8%–21.3%), 6/30 recurring-regime streams (20.0%; 9.5%–37.3%), and 9/30 harmful-adaptation streams (30.0%; 16.7%–47.9%). Mean evaluator-known post-promotion net gains were respectively 21.1 (95% t interval −9.0 to 51.2), 59.2 (13.5 to 105.0), and 92.0 (38.2 to 145.7) in the simulator's cumulative cost units. No future-harmful promotion occurred in these pilot cells.

Both context-nested methods promoted in 0/30 streams for each of those scenarios and for both null controls. The exact 95% upper bound for a zero-of-30 event rate is 11.4%, so these pilot results do not establish 5% error control. The pooled exact-copy null also had zero promotions; the stochastic context-zero-mean null had zero promotions. No pointwise-null candidate certificate occurred in any pilot cell. Every treatment respected the common pathwise query cap; at the 20% cap the methods used a mean 313.5 of 320 available labels.

This is a development pilot, not a calibrated comparison or evidence that nested spending is inferior. The observed lack of contextual promotions is consistent with low power after dividing small rank allocations across two contexts. The pilot used one query policy and one estimator, and it does not test context definitions chosen adaptively, repeated changes in the context boundary, or policy-dependent outcomes.

## Next validation

Before using context-specific promotion as a research result, run a predeclared calibration study with substantially more independent seeds under both exact-copy and stochastic context-zero-mean nulls, reporting familywise and candidate-by-context crossing rates with exact intervals. Then use fresh seeds for power and utility comparisons under benign nuisance, localized harm, recurring regimes, and harmful adaptation. Compare context allocations with pooled rank at equal alpha and equal budget, and report the loss from context splitting alongside any improvement in targeting. Treat the feature threshold and switching-cost interpretation as fixed design choices for that confirmation.
