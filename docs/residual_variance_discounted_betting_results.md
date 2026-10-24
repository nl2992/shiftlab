# Multi-timescale discounted betting: development results

## Design and artifacts

This fresh-seed alternative-only screen evaluated the frozen protocol in [residual_variance_discounted_betting_protocol.md](residual_variance_discounted_betting_protocol.md). It compared four monitors on the same generated streams, prediction-powered increments, query paths, and hard label-dollar caps: fixed-stake mixture, cumulative predictable Kelly, uniform-start fixed-stake mixture, and a fixed mixture over eight start times × three discounted predictable-Kelly half-lives (16, 64, 256 events).

The grid included severity 1.5, 3.0, and 4.5; query rates 0.80 and 1.00; and 60 seeds per cell (31,303,026–31,303,085), for 1,440 monitor-stream rows. The RTX 4060 Laptop GPU with PyTorch 2.9.1/CUDA 13.0 generated the synthetic streams; the eventwise monitor recursions ran on CPU. `outputs/residual_variance_discounted_betting/manifest.json` records the source hashes, environment, and Parquet checksum. The Parquet SHA-256 is `20fe479c4c503025f9d89ef94ac20564cd0ffa9118d3c78524bb093ab7cfd580`.

## Findings

Across the six equally weighted severity × query-rate cells (360 streams per method), the discounted start mixture detected 34 streams (9.44%). The fixed-stake mixture detected 47 (13.06%), cumulative predictable Kelly detected 38 (10.56%), and uniform-start fixed mixture detected 74 (20.56%). The discounted process was lower than uniform starts by 11.11 percentage points; the seed-clustered descriptive 95% bootstrap interval was [−16.39, −6.39]. It was lower than the fixed-stake mixture by 3.61 points (interval [−8.89, +1.11]) and lower than cumulative Kelly by 1.11 points (interval [−5.28, +3.06]). No seed cluster favored discounted betting over uniform starts.

| Severity | Query rate | Fixed mixture | Cumulative Kelly | Uniform-start fixed mixture | Discounted start mixture |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1.5 | 0.80 | 5/60 (8.3%) | 5/60 (8.3%) | 5/60 (8.3%) | 1/60 (1.7%) |
| 1.5 | 1.00 | 4/60 (6.7%) | 3/60 (5.0%) | 8/60 (13.3%) | 2/60 (3.3%) |
| 3.0 | 0.80 | 8/60 (13.3%) | 5/60 (8.3%) | 12/60 (20.0%) | 4/60 (6.7%) |
| 3.0 | 1.00 | 9/60 (15.0%) | 8/60 (13.3%) | 15/60 (25.0%) | 8/60 (13.3%) |
| 4.5 | 0.80 | 10/60 (16.7%) | 7/60 (11.7%) | 15/60 (25.0%) | 7/60 (11.7%) |
| 4.5 | 1.00 | 11/60 (18.3%) | 10/60 (16.7%) | 19/60 (31.7%) | 12/60 (20.0%) |

The candidate produced no evaluator-defined pre-onset alarms on these alternatives, as did the other monitors. Every method shared labels and spend within each paired stream; all respected the hard cap, all material-harm onsets were reached, and the mean spend, labels, and processed horizon were identical across monitors. Because this screen did not include stationary or benign-shift population-null streams, it does not estimate a false-escalation rate.

## Decision

Stop this discounted-Kelly branch for the registered residual-variance design. Its predictable stake rule is mathematically valid under the same bounded conditional-mean assumptions, but it did not improve power; the fixed mixture of start times and fixed stakes performed substantially better. This negative result does not rule out discounted betting for other change geometries. Do not search half-lives again on these seeds. Return to the leading uniform-start fixed-stake comparator for this mechanism, and prioritize a separately calibrated horizon/power study or other harm scenarios where the decision gap is larger. No figure was generated; any requested figure from these results should use PaperBanana.
