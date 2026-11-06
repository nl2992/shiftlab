# WP1 adaptive-gate correction sensitivity

Affected policies are replaced by same-seed rows from the corrected adaptive-gate implementation, joined on exact stream, episode, seed, and policy keys. This is a correction sensitivity on previously used data, not independent confirmation. Registered WP1 outputs are unchanged.

**Verdict:** `NOT_SUPPORTED`; 0/4 RMM hosts support improvement over the strongest certified comparator; enough episodes: True. 

Late-improvement episodes: 10 across 5 clusters. Selected best certified comparator: `gated_adaptive_range+front`.

| RMM host | Contrast | Mean Δ cost [95% interval] | Episodes |
|---|---|---:|---:|
| `rmm:gated_deployment+RMM` | vs `gated_adaptive_range+front` | -37.92 [-68.02, +11.36] | 10 |
| `rmm:discern_style+RMM` | vs `gated_adaptive_range+front` | -38.79 [-69.10, +2.84] | 10 |
| `rmm:SMCS+retain-incumbent+RMM` | vs `gated_adaptive_range+front` | -34.65 [-68.23, +17.66] | 10 |
| `rmm:gated_adaptive_range+RMM` | vs `gated_adaptive_range+front` | -30.65 [-58.44, +9.36] | 10 |

## Interpretation

This report evaluates whether the code correction changes the WP1 conclusion. The retrospective episode classifier is not causal ground truth, and its episodes come from previously exposed datasets. The result does not establish real-world late-improvement transfer or a deployment guarantee.

Analysis status: amended adapter-panel sensitivity; Xu acquisition adapter excluded; Choe-Ramdas adapter retained; not a complete published-certificate ranking; same-episode comparator selection remains unadjusted.
