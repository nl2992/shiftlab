# Residual-variance onset-prior screen: preliminary results

## Registered design and reproducibility

This was a development-only synthetic screen, not a calibration or confirmatory experiment. It compared a full-stream fixed-stake e-process with five fixed start-time mixtures on the residual-variance / target-variance generator. The monitor horizon was 1,600 events (2,400 generated events, with monitoring beginning at event 800); the change occurred at event 1,200. The tested severity values were 1.5, 3.0, and 4.5; query rates were 0.40, 0.80, and 1.00; each cell used 60 seeds (31,302,026–31,302,085). The prior family and selection rule are described in the [frozen protocol](residual_variance_prior_development_protocol.md).

The run produced 3,240 method-stream rows: 3 severities × 3 query rates × 60 seeds × 6 monitors. Synthetic data generation used the NVIDIA GeForce RTX 4060 Laptop GPU with PyTorch 2.9.1 and CUDA 13.0. The eventwise e-process recursions ran on CPU. Output files and source hashes are recorded in `outputs/residual_variance_prior_development/manifest.json`; the Parquet SHA-256 is `10e3326dd7ca550387aee4038122758f0ec001cdc4e074dc807f53b0a24dbc6c`.

## Main findings

The primary selection set contained the six severity × query-rate cells at q=0.80 and q=1.00 (360 streams per method). The onset-centered Beta(4,12), center Beta(2,2), and early Beta(1,2) start mixtures each detected 47/360 material-harm streams (13.06%). Uniform starts detected 43/360 (11.94%), late Beta(2,1) detected 40/360 (11.11%), and the full-stream fixed mixture detected 18/360 (5.00%). The selection implementation named Beta(4,12) as the first-ranked candidate; center Beta(2,2) tied it on both registered selection statistics (macro rate 13.06%; minimum severity-averaged rate 4.17%). There is therefore no unique best prior under the stated criteria.

The small 1.11 percentage-point macro difference between Beta(4,12) and uniform starts is uncertain. A paired bootstrap that clusters the six primary cells by seed gives a descriptive 95% interval of −1.39 to +3.61 percentage points. In 50 of 60 seed clusters the two methods tied; 7 favored Beta(4,12), and 3 favored uniform. The screen does not establish that centering a prior on the known synthetic onset improves over an untuned uniform mixture.

| Severity | Query rate | Fixed full stream | Uniform starts | Beta(4,12) onset prior |
| ---: | ---: | ---: | ---: | ---: |
| 1.5 | 0.80 | 1/60 (1.7%) | 1/60 (1.7%) | 1/60 (1.7%) |
| 1.5 | 1.00 | 2/60 (3.3%) | 3/60 (5.0%) | 4/60 (6.7%) |
| 3.0 | 0.80 | 2/60 (3.3%) | 5/60 (8.3%) | 5/60 (8.3%) |
| 3.0 | 1.00 | 4/60 (6.7%) | 11/60 (18.3%) | 13/60 (21.7%) |
| 4.5 | 0.80 | 2/60 (3.3%) | 7/60 (11.7%) | 6/60 (10.0%) |
| 4.5 | 1.00 | 7/60 (11.7%) | 16/60 (26.7%) | 18/60 (30.0%) |

Detection rose with severity and label rate, but remained low even at full feedback: Beta(4,12) detected 4/60, 13/60, and 18/60 at severity 1.5, 3.0, and 4.5, respectively, when q=1. The onset prior did not uniformly beat uniform starts: at severity 4.5 and q=.80 it detected one fewer stream. This remains a weak-evidence problem for the residual-variance monitor.

Every method saw the same labels, estimator, costs, and event horizon within a seed/query-rate stream; mean labels, spend, estimator error, and expected excess cost were identical across monitors. All 540 streams reached the configured monitoring end or stopped only at the same budget-driven boundary, and every method respected the hard budget. The fixed full-stream method had 6 pre-onset alarms among 540 alternative streams; the five started mixtures had none. These alternative-only pre-onset counts are diagnostics, not a false-alarm calibration. No nondegenerate null block was included here.

## Interpretation and next step

Fixed convex mixtures of the existing valid components preserve the existing e-process guarantee under the same conditional-mean null, filtration, predictability, and bounded-increment assumptions. The experiment changes power through start-time weighting; it does not add a new validity theorem. Beta(4,12) is informed by the known onset of this generator and is not evidence for an onset-adaptive method on unknown real streams.

Do not promote a unique prior on these results. Keep uniform starts as the simpler general comparator and retain Beta(4,12) and center Beta(2,2) as tied development candidates. If this branch continues, freeze a single candidate using an independent validation block, then run fresh nondegenerate null calibration and a disjoint power block. The low detection rates at q=1 make redesigning or diagnosing the residual-variance signal more valuable than a broad search over more prior shapes. Do not tune again on these seeds.

The run generated tables and machine-readable metrics only. No figure was generated. If a paper figure is commissioned from these results, use PaperBanana and generate it from the checked-in metrics.
