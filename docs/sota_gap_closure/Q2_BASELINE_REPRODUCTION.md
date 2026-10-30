# Q2 baselines: implementation status
| method | implementation | provenance |
|---|---|---|
| paired sequential test | `paired_e`: per-candidate betting e-process on IPW paired loss difference, no multiplicity correction | LOCAL |
| paired confidence sequence | `paired_cs`: stitched Hoeffding on IPW means, range 2M/q | SOURCE_INSPIRED, weak (never certifies) |
| prediction-powered paired evidence | `pp_paired`: proxy = candidate-implied expected loss difference | LOCAL_HEURISTIC |
| Sequential Model Confidence Sets adaptation | `seqmcs`: pairwise e-processes for all ordered pairs, Bonferroni over K(K-1) pairs, elimination, certify when the incumbent is eliminated | SOURCE_INSPIRED (not the published procedure; the source was not accessible) |
| uniform multiple-testing correction | `paired_e_bonf`: threshold log(K_c/alpha) | LOCAL |
| shared-label multiple-model testing | all methods except `indep_labels` share one label per event | LOCAL |
| CAMS-style contextual selection | `cams`: query probability ~ (0.1 + any-disagreement)/running mean, >= frac on disagreement events | SOURCE_INSPIRED, not CAMS itself |
| existing ShiftLab exact reference | `rpoq_exact` toy: exact first-promotion value of information (`Q3_EXACT_ORACLE_COMPARISON.md`) | repo code (exact) |
None is a VERIFIED_REPRODUCTION.
