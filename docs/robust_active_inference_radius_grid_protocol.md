# Robust active-inference radius development grid

**Status: frozen development screen.** This protocol is for method development only. It does not
authorize a confirmatory claim or select a default for the full project. The current robust
active-inference implementation is an adaptation of a batch sampling method; it has no new
sequential guarantee.

## Question and candidates

Test whether the default L2 residual-variance uncertainty radius changes the operating behavior of
the validation-selected geometric path between cost-adjusted Neyman and uniform querying. Compare
radius fractions `{0, 0.1, 0.25, 0.5, 1, 2}`. For each stream, the absolute uncertainty radius is
`c = fraction * ||v_hat||_2` on the pre-monitor validation slice, and the path point is selected
from the fixed 21-point grid `rho ∈ {0, 0.05, ..., 1}` by minimizing the robust score. No parameter
is selected using monitoring outcomes.

The matched references are uniform querying, square-root residual-variance querying, and
cost-adjusted square-root residual-variance querying. All policies share generated outcomes, query
random numbers, a 10% expected dollar-rate target, the 0.05–0.50 propensity range, common e-process
support bound, and the same pathwise dollar cap.

## Design and outcomes

Use 30 common seeds per each of stationary, benign-nuisance, and boundary-local-harm scenarios,
with `n=3200`, dimension 16, and seed offset `56220000`. Generate streams on CUDA when available;
this run is configured to require CUDA. Preserve the current/reference paired-cost estimand and
the registered 0.10 harm margin.

The primary development score is macro mean squared error of the stream-mean paired-cost
estimator, giving equal weight to the three scenarios and to independent seed streams. Report the
per-scenario RMSE and paired seed bootstrap intervals against uniform as context. Secondary
outcomes are single-start harm detection among streams whose onset is reached, false escalations on
the two population-null controls, dollar spend, labels queried, processed horizon, and the selected
`rho`. The 30-stream null counts are diagnostics only and cannot pass or establish a calibration
gate.

The score is a development selection statistic only. If one radius appears useful, freeze it and
test it on independent null-calibration and harm-confirmation blocks before promoting it. Report
all six radii regardless of outcome, and do not create a visual unless PaperBanana is available.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 56220000 --n 3200 --d 16 --budget-rate 0.10 --q-min 0.05 --q-max 0.50 --device cuda --workers 2 --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy cost_variance_proxy robust_active_inference_r0 robust_active_inference_r0.1 robust_active_inference_r0.25 robust_active_inference_r0.5 robust_active_inference_r1 robust_active_inference_r2 --skip-figure --output outputs/robust_active_inference_radius_development
```

The runner writes seed-level Parquet metrics, paired summaries, an environment and code-hash
manifest, and a text report. Do not overwrite an existing output directory.
