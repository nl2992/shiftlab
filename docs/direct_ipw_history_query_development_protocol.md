# Direct-IPW history-evidence query development grid

**Status:** frozen exploratory protocol, 2026-10-25. This grid is method development
only. Its null cells are not a calibration sample and its alternatives are not
confirmation data.

## Question

Does the existing past-evidence-driven query rule improve decision-harm detection,
excess-cost avoidance, or label efficiency over uniform querying when both use the
same direct-IPW monitor, query uniforms, hard dollar cap, and a common support bound?
This tests a new application of an existing predictable query policy and standard
bounded-mean e-process, not a new algorithmic guarantee.

## Registered design

- 30 matched seeds per cell, seed IDs `31025000` through `31025029`.
- Six scenarios: `stationary`, `benign_nuisance`, `boundary_local_harm`,
  `residual_variance`, `recurring_regimes`, and `harmful_adaptation`.
- Query floors `q_min ∈ {0.05, 0.10, 0.20}`, target budget rate `0.20`, and
  propensity ceiling `q_max=0.80`.
- Ten methods per cell: uniform querying and the nine predeclared evidence-curve
  combinations `activation_fraction ∈ {0, 0.025, 0.05}` and
  `urgency_power ∈ {0.5, 1, 2}`. All use the same current evidence-based query
  rule, with each propensity selected before the current query using past e-value
  and remaining realized spend only.
- `alpha=0.05`, excess-cost margin `epsilon=0.10`, `n=3200`, `d=16`, immediate
  labels, paired current/reference binary costs, and the existing synthetic tariff
  with a pathwise dollar cap calibrated from pre-monitor validation tariffs.
- Generate each stream once per scenario/seed/floor run and use common query
  uniforms across methods. Use `common_eprocess_bound=True` so uniform and adaptive
  arms at a given floor share the same global support bound. Floors are a separate
  sensitivity axis and therefore change the common bound across floor blocks.
- Run on CUDA with four independent stream workers; retain CPU smoke tests.
  Stream seeds are explicit, so worker scheduling does not alter generated records.
  Do not create a figure in this run.

## Estimand and validity

For gross paired cost difference `G_t`, monitor excess harm over `epsilon` with
`X_t = I_t G_t/q_t - epsilon`. Conditional on the past, query randomization is
independent of the current outcome and `q_t` is predictable; therefore
`E[X_t | F_(t-1)] = E[G_t | F_(t-1)] - epsilon`. With `|G_t| <= C` and
`q_t >= q_min`, a common support is `C/q_min + epsilon`. This grid uses the global
support, not a current-context eventwise normalizer. Validity still requires the
stated conditional-mean null, frozen evaluated policies, immediate randomized
feedback, and correct cost bounds.

The primary descriptive outcome is detection among all evaluator-defined harmful
streams, with onset reach reported so budget censoring is visible. Also report false
escalations in nulls, paired expected excess-cost avoided by fallback, labels,
realized spend, processed events, and hard-cap violations. Pair all methods by
scenario and seed. Report 95% paired seed-bootstrap intervals without multiplicity
correction; do not select a winner or infer nominal error control from these
development cells. Any promising configuration must receive fresh independent
null calibration before a separate disjoint confirmation.

## Reproduction

```powershell
uv run shiftlab-dive-direct-ipw-query-grid `
  --device cuda `
  --workers 4 `
  --seeds 30 `
  --seed-offset 31025000 `
  --n 3200 `
  --d 16 `
  --output outputs/direct_ipw_query_development_30
```

The runner writes per-floor source runs, a combined Parquet file, per-cell
summaries, paired contrasts, and SHA-256 hashes. It refuses to overwrite a
nonempty output directory.
