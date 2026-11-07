# WP2 pooled V1 sensitivity excluding the Xu acquisition adapter

Generated 2026-11-04 from the existing WP2 raw runs. This is a post-run comparator-class sensitivity;
it does not modify the registered analysis or its historical results. The earlier `amended_no_xu`
analysis removed `xu_acquisition_only` from published-method rankings and the H1a powered-baseline
set, but left it in pooled V1 summaries because ShiftLab supplied its certificate. This additional
analysis excludes the composite from the pooled V1 set for H2, H4, H6 and related pooled tables.

## Results

| Protocol result | No-Xu pooled result | Registered criterion | Outcome |
|---|---:|---|---|
| H1a | 7 qualifying methods | At least 5 | Pass |
| H1b | A5b still breaches the .0936 upper-bound screen on bike and appliances | Upper bound <= .0936 on every dataset | Fail |
| H2: mean `adv_rest` on v2 twins | .0122 [.0063, .0180] | Lower 95% bound > 0 | Pass; descriptive pooled V1 evidence |
| H4: mean-reverting `pi_EI` | .4899 [.4235, .5572] | Lower bound >= .7 | Fail |
| H4: fixed-effect real `pi_EI` | .4871 [.4369, .5431] | Upper bound <= .5 | Pass at this component only |
| H4: fixed-effect synthetic `pi_EI` | .4406 [.3556, .5345] | Upper bound <= .5 | Fail |
| H6a | Promotion rates non-decreasing with T at all three delay multipliers | Non-decreasing | Pass |
| H6b | A5b upper bound breaches the screen in at least one cell | <= .0936 in every cell | Fail |

H4 remains unsupported because its conjunctive conditions do not all hold. These resamples use the
same development-exposed streams and same evaluation samples as the registered study; removing one
policy from a pooled descriptive statistic does not provide independent confirmation or selection
adjustment. The remaining methods are common-contract ports/adapters, not author-native deployments.

## Reproduction

```sh
uv run python scripts/sota_sprint/wp2_analyze.py \
  --amendment-dir docs/sprint2/wp2/amended_no_xu_pool --exclude-xu-pool
```

Machine-readable results and generated tables are in `amended_no_xu_pool/results.json` and
`amended_no_xu_pool/tables.md`. The original registered result and earlier comparator-ranking
sensitivity remain preserved in their existing directories.
