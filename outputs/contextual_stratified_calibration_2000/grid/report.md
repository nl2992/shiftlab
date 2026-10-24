# Contextual stratified intervention development grid

Status: **development_only_no_independent_calibration_or_confirmation**; 70,000 stream-method rows; 28 paired contrasts; device: cuda.

The learner observes a balanced context identifier. In the heterogeneous reversal profile, shadow gain is positive in both contexts, then deployment gain becomes positive in one context and negative in the other. Global and stratum-wise gates use the same paired outcomes, query paths, query rate, and total hard label cap. The stratum-wise method applies the existing bounded e-process separately to each context, allocating alpha across strata and stages by Bonferroni. This is a standard composition, not a new test.

## Stratified versus global gate under heterogeneous reversal

| Query rate | Label cap | Stratified minus global expected utility | Realized utility contrast | 95% paired interval | Mean rollback groups | Mean safe groups retained | Mean labels / cap |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 80% | 40% | 30.82 | 30.82 | [29.78, 31.76] | 0.68 | 1.00 | 302.1 / 320 |

Every row is a development comparison. Context-specific rollback is evaluated on a deliberately visible and balanced context; no hidden regime label or evaluator expected gain enters either policy. Both procedures share the total hard budget. Null alarms in this screen are diagnostics only; independent calibration is required before any error-control claim.

The method is the standard per-stratum bounded e-process with a Bonferroni alpha split. Any gain would support context-local intervention in this DGP, not algorithmic novelty or general superiority. No figure was generated; all research visuals must use PaperBanana.

## Reproduction

```powershell
uv run shiftlab-dive-contextual-stratified-grid --seeds 500 --horizon 400 --device cuda --output-dir outputs/contextual_stratified_grid_500
```
