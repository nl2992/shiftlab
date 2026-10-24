# Residual-variance start-prior comparison: results

## Results

The uniform eight-start mixture improved detection over the full-stream fixed mixture on this residual-variance design, while the previously confirmed late Beta(2,1) prior showed a smaller gain. Across 12 balanced severity/rate cells, fixed mixture detected 31/720 streams (4.3%), uniform starts 51/720 (7.1%), and late starts 45/720 (6.3%). A paired bootstrap that resampled the 60 seed clusters gave a descriptive macro difference of +2.78 percentage points for uniform starts versus fixed mixture (95% percentile interval +0.56 to +5.28); late starts differed by +1.94 points (−0.56 to +4.58). The uniform-minus-late difference was +0.83 points (+0.14 to +1.67). These intervals were computed after the per-cell screen and are exploratory, with no familywise adjustment.

| Severity | Query rate | Fixed full-stream | Uniform eight-start | Late Beta(2,1) eight-start |
| ---: | ---: | ---: | ---: | ---: |
| 1.5 | 0.20 | 0/60 | 0/60 | 0/60 |
| 1.5 | 0.40 | 0/60 | 0/60 | 0/60 |
| 1.5 | 0.80 | 5/60 | 5/60 | 5/60 |
| 1.5 | 1.00 | 3/60 | 5/60 | 5/60 |
| 3.0 | 0.20 | 0/60 | 0/60 | 0/60 |
| 3.0 | 0.40 | 0/60 | 0/60 | 0/60 |
| 3.0 | 0.80 | 6/60 | 6/60 | 6/60 |
| 3.0 | 1.00 | 4/60 | 8/60 | 8/60 |
| 4.5 | 0.20 | 0/60 | 0/60 | 0/60 |
| 4.5 | 0.40 | 1/60 | 0/60 | 0/60 |
| 4.5 | 0.80 | 6/60 | 13/60 | 9/60 |
| 4.5 | 1.00 | 6/60 | 14/60 | 12/60 |

The gains are concentrated in the strongest residual-variance shift with high label rates. At q=0.80 and severity 4.5, uniform starts detected 13/60 versus 6/60 for fixed mixture and 9/60 for late Beta(2,1). With complete labels, the counts were 14/60, 6/60, and 12/60. At q≤0.40, all variants were essentially powerless. Across all cells, every harm onset was reached, there were no budget violations, and all methods had identical per-stream label counts, dollar spend, and processed-event paths. No alternative stream produced a pre-onset alarm.

## Interpretation

The result supports the explanation that pre-shift negative evidence can dilute a persistent post-change signal: fixed start components discard evidence before their declared start, and a convex start mixture retains the same validity argument. It also shows that the time prior matters. Beta(2,1), which allocates still more mass to late starts, did not improve on uniform and was worse in the strongest q=0.80 cell. The generator's shift begins at event 1,200; after the monitor burn-in at event 800, that is 400 events into the planned 1,600-event monitoring horizon. Mass placed far beyond that point has too little post-change time to grow. This is a design-specific interpretation, not evidence that uniform starts are generally optimal.

The improvement is modest and does not solve the low-label-power problem: at q=0.20 there were no detections for any prior, even at severity 4.5. Full-label detection remains below 25% in the strongest cell. These alternatives do not calibrate false alarms; the start mixtures inherit the existing bounded-mean e-process validity only under its eventwise conditional-mean null, predictable policies/querying, and support assumptions.

## Decision and next algorithm screen

Retain uniform starts as the leading start-time comparator for this mechanism; do not promote the Beta(2,1) weighting as a universal improvement. The next development screen should compare a small, preregistered family of start-time priors whose mass is centered at early, middle, and late portions of the planned monitor horizon. Select any candidate only on development seeds, then freeze it for an independent nondegenerate-null calibration and disjoint confirmation. Keep the full-stream process as the no-restart reference. This is standard convex e-process mixing; the contribution would have to come from a demonstrated decision-theoretic design principle and matched performance, not the mixture identity itself.

## Reproducibility

Command: `uv run python -m shiftlab.dive.residual_variance_start_prior --device cuda --seeds 60`.

The run used an NVIDIA GeForce RTX 4060 Laptop GPU for synthetic generation; monitor recursions were CPU-bound and took approximately 30 minutes. It produced 2,160 rows (3 methods × 3 severities × 4 query rates × 60 seeds). Manifest hashes and environment are in `outputs/residual_variance_start_prior/manifest.json`; the source is pinned to commit `9965772`, and the Parquet checksum is `e02c30b92f8ca8a6bc90e13731df9602a9b750cfd419cdb8e4808887d1958a1e`.

Per-stream data are in `outputs/residual_variance_start_prior/metrics.parquet` and `metrics.csv`; grouped rates and per-cell paired contrasts are in `power_summary.csv` and `paired_detection_contrasts.csv`. Reproduce the pooled seed-cluster intervals and path/budget audit with `uv run python -m shiftlab.dive.analyze_residual_variance_start_prior`; its inputs, bootstrap seed, and outputs are recorded in `analysis_manifest.json`. No figure was produced.
