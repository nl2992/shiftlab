# Evidence-directed query allocation: development comparison

**Status:** Protocol for an exploratory, matched hard-budget comparison. This is not a
confirmatory calibration study and does not establish a new validity result.

## Question

Does increasing label propensity when a prior bounded-mean e-process accumulates positive
evidence improve decision-harm detection or estimation accuracy over fixed uniform querying,
when both methods use the same stream, query random numbers, hard label-dollar cap, and e-process
increment bound?

## Frozen candidate

For significance level `alpha`, configured support `[q_min, q_max]`, current prior log e-value
`L_(t-1)`, and remaining fraction of the original dollar budget `r_(t-1)`, use

`u_t = clip(L_(t-1) / log(1/alpha), 0, 1)`

`q_t = q_min + (q_max - q_min) * u_t * r_(t-1)`.

Both inputs are known before the current query. The propensity is at least `q_min`; the existing
hard-budget runner stops before opening an event if the remaining balance cannot cover the known
maximum tariff. Its eventwise prediction-powered monitor therefore retains the fixed support bound
based on `q_min`. The taper is a budget-aware heuristic, not an optimizer and not a power guarantee.
The e-process validity claim remains conditional on the stated predictable-query filtration,
bounded outcomes, immediate paired labels, and conditional-mean null.

## Comparison and analysis

- Compare `evidence_directed_proxy` with `uniform_proxy` on identical generated streams and common
  query uniforms; use `common_eprocess_bound=True` so threshold width is matched.
- Use the registered stationary, benign-nuisance, and boundary-local-harm scenarios, a 10% target
  budget rate, `q_min=0.05`, `q_max=0.50`, `alpha=0.05`, and the existing maximum-tariff reserve
  stopping rule.
- Run an exploratory 30-seed block per scenario on CUDA when available. Do not tune on this block.
- Report false escalations on both null controls, detection among all and reached material-harm
  streams, detection delay, stream-mean RMSE, actual label spend/count, processed horizon,
  propensity range, and pathwise cap compliance. Keep finite-stream oracle harm labels evaluator-only.
- Treat all comparisons as descriptive pending an independently sized null calibration and a
  disjoint harm confirmation. No visual is required for the protocol; any later figure must use
  PaperBanana and be checked against the exported metrics.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 20371024 --n 3200 --d 16 --budget-rate 0.10 --q-min 0.05 --q-max 0.50 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_directed_proxy --skip-figure --output outputs/evidence_directed_allocation_30
```

