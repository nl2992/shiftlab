# Cost-neutral robustification grid for exact mixture-growth acquisition

**Development protocol lock:** 2026-10-23, before the development grid. This tunes one robustification
weight only. It does not change the e-process or make a novelty claim.

## Candidate policies and derivation

The base exact-growth propensity `q_exact(x)` maximizes the current fixed-mixture e-process's
model-based expected one-step log increment minus a validation-calibrated label-cost price. The
robustified propensity is

`q_w(x) = (1-w) q0(x) + w q_exact(x)`,

where `q0(x)=b/k(x)`, `k(x)` is the known query-time label tariff, and `b` is the target expected
spend per monitor event estimated from the validation tariff mean. The zero-adaptive branch spends
exactly `b` in conditional expectation at each event. If `b/k(x)` lies in `[q_min,q_max]`, then for
any adaptive propensity in the same interval and any tariff in `[k_min,k_max]`,

`|k(x) q_w(x) - b| <= w * max(|k_min*q_min-b|, |k_max*q_max-b|)`.

This is a worst-case expected-spend drift bound, not a realized budget guarantee; the experiment
also imposes the hard dollar cap. Any predictable `q_w` in the registered positive interval keeps
the same PPI/e-process validity argument and common global increment bound. The mixture is standard
convex robustification, not a new theorem.

## Development grid

- Candidate weights: `w in {0, .25, .50, .75, 1}`; 0 is fully cost-neutral, 1 is the original
  exact-growth policy.
- 30 paired stream seeds per scenario, seed offset `28402026`, `n=3200`, `d=16`, CUDA.
- Scenarios: stationary, benign nuisance shift, and boundary-local harm.
- Compare each weight with uniform-query PPI under a common 20% target dollar budget, `[0.10,0.80]`
  propensity interval, common fixed-mixture e-process bound, and a hard per-stream dollar cap.
- Every weight and the uniform baseline use identical generated streams and query random uniforms.
- Primary selection target: maximize boundary-harm detections, with a development-only pooled null
  false-escalation guardrail of at most 5%. If detection ties, select lower boundary-harm stream-mean
  estimation RMSE, then longer processed horizon. This deterministic rule nominates one weight for
  an independent evaluation; it does not estimate confirmatory uncertainty or establish superiority.
- Report paired seed-bootstrap intervals for detection and RMSE differences, null-control alarms,
  spend, label counts, monitor horizon, and cap violations for every grid point. Do not use the same
  seeds for the final evaluation.

## Fresh evaluation block

If the development grid yields a candidate, evaluate the selected weight against uniform and the
four established acquisition baselines on 60 fresh seeds beginning at offset `28502026`, using the
same three scenarios and matched dollar cap. If the grid has no boundary-harm detections at any
weight, selection is based only on the prespecified RMSE tie-break and the fresh run must be
described as an estimation-efficiency test, not a detection-power confirmation.

## Reproduction

```powershell
uv run python scripts/grid_search_cost_neutral_growth.py `
  --output outputs/cost_neutral_growth_grid_development `
  --seeds 30 `
  --seed-offset 28402026 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.10 `
  --q-max 0.80 `
  --device cuda
```
