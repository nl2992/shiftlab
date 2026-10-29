# IID-relaxation paired T=8 grid results

The candidate was run once on the five previously untested cells. For all five,
the exact full causal-null verifier passed and the rational dual interval was
about `0.84e-12` to `1.26e-12` wide. The recovered feasible cost exactly equals
the recorded robust reference cost in every cell.

| Transition | Emissions | Candidate risk | Candidate minus best calendar | Candidate minus m=3 cap | Candidate minus best gate | End-to-end seconds |
|---|---|---:|---:|---:|---:|---:|
| `1/10` | `(1/10,9/10)` | `1/10` | `-0.00863243136` | `-0.01979722624` | `-0.09820893952` | 9.87 |
| `1/4` | `(1/10,9/10)` | `1/10` | `0` | `0` | `-0.0279995` | 9.54 |
| `1/4` | `(1/50,49/50)` | `1/10` | `0` | `-0.0048301824` | `-0.0376399296` | 9.43 |
| `9/20` | `(1/10,9/10)` | `0` | `0` | `0` | `0` | 10.02 |
| `9/20` | `(1/50,49/50)` | `0` | `0` | `0` | `0` | 10.39 |

The other low-persistence/high-separation T=8 cell was tested in the earlier
single-cell pipeline: it also matched the reference, had risk `1/10`, and beat
the best calendar by `0.01139306973`. Thus the candidate reproduces the exact
reference cost and wins over the calendar, cap and gate baselines where the
registered reference had an adaptive-timing gain; it ties calendars in the four
control cells. It does not improve on the full robust reference.

The candidate builds 3,441 nodes versus 17,922 in the robust reference on these
T=8 cells. However, its complete T=8 runtime is roughly 9.4–10.4 seconds, while
the paired reference runs took roughly 5.1–5.4 seconds. The smaller relaxation
master therefore has no end-to-end runtime advantage in this family. This is an
economic synthetic win over restricted baselines with exact risk/value
certificates, not evidence of computational superiority or generalization to
randomized streams.

The output `iid_relaxation_t8_grid_v1.json` stores all five dual flow multiplier
vectors, exact lower bounds, input/source hashes, phase timings, and baseline
comparisons. Its executed runner is preserved in
`iid_relaxation_t8_grid_executed_source_v1.txt`; the checked-in runner only
received lint-required import spacing afterward. The run excludes the cell already recorded in
`iid_relaxation_certified_pipeline_v1.json`; it does not rerun prior baselines.
