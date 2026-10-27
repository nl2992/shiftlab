# Independent Q2 paired confirmation: Target-Scout versus fixed split

**Status:** frozen conditionally before the exact-rule null-calibration result,
2026-10-26. Execute only if the calibration manifest reports `inference.pass`
true. If any null stratum fails, do not run this efficacy confirmation and do
not modify the methods using the failed block.

## Question and estimand

On an independent seed block and the same registered synthetic candidate
family, does Target-Scout improve evaluator-known cumulative future net
decision gain relative to source-validation fixed sample-split certification
and pooled-rank sequential candidate testing?

The estimand is the equal-cell mean paired contrast in
`expected_postpromotion_net_gain`, averaged over the 18 positive-signal cells
(prevalence 0.10/0.50/0.90 × signal 0.05/0.10 × proxy error 0/0.10/0.25).
The registered practical margin is +1.0 cumulative utility unit. This confirms
only the specified synthetic DGP, candidate family, label cap, and monitor
assumptions; it is not a real-data, universal-superiority, or novelty claim.

## Frozen design and inference

- 300 matched seed blocks per positive-signal cell, IDs
  `99,010,000–99,010,299`, disjoint from the development, null calibration,
  and existing repository experiment ranges.
- `n=3,200`, `d=16`, FN/FP costs 5/1, switching cost 0.05, alpha 0.05, uniform
  direct-IPW monitoring, fixed-mixture betting, and a 40% pathwise label cap.
- The three methods share the generated stream and query-uniform path within
  every seed/cell. Target-Scout scout labels remain charged to the same total
  cap and are excluded from its certification slice.
- Primary paired contrasts: Target-Scout minus fixed split; Target-Scout minus
  pooled rank. Resample matched seed IDs as blocks, 10,000 bootstrap draws,
  frozen bootstrap seed `2026102699`, and 97.5% two-sided percentile intervals
  per contrast (Bonferroni familywise target at least 95%, conditional on the
  cluster bootstrap approximation).
- Confirmation meets the registered material-benefit criterion only if both
  lower interval limits exceed +1.0. Report the point estimates and intervals
  regardless of outcome. All caps and matched-label invariants must pass. Do
  not change methods, filters, estimands, cells, or seed block after seeing
  results.
- Calibration gate: require the exact-rule calibration's 27 simultaneous
  upper limits to be ≤0.05, no cap violations, and zero positive-net-gain
  promotions. The confirmation runner checks the calibration artifact hash and
  gate before starting.
- No figures are planned. Report tables and machine-readable metrics only.

## Execution

```powershell
uv run python scripts/confirm_target_scout_fixed_split.py `
  --seeds 300 --seed-offset 99010000 --device cuda `
  --calibration outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1/manifest.json `
  --output outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_confirmation_v1
```
