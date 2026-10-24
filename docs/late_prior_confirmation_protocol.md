# Late start-time prior confirmation protocol

## Status and candidate

The horizon-prior development grid selected fixed Beta(2,1) weights at the nominal expected
query horizon. This is an established fixed mixture selected during development, not a novel
algorithm. This protocol freezes the candidate and analysis before a fresh validation run.

For eight prespecified start locations at nominal expected query horizon q*n, assign the mass of
Beta(2,1) to the eight equal-width normalized start bins:

    [0.015625, 0.046875, 0.078125, 0.109375,
     0.140625, 0.171875, 0.203125, 0.234375].

The reference is the fixed uniform mixture with weight 0.125 at each start. Both methods are convex
mixtures of the same bounded-mean e-process components, with weights fixed before the stream.

## Fresh design

Alternative confirmation crosses query rates {0.10,0.25,0.50}, harm onsets {0.20,0.60,0.80},
and paired-cost increases {0.12,0.24}. Each of the 18 cells contains 2,000 paired streams with
3,000 prediction events, materiality margin 0.02, amplitude 0.60, and uniform independent feedback
delays on the integers 0 through 6. Use seeds 20286000–20287999 in every cell. Methods share generated
outcomes, query masks, and delays within each cell/seed. CUDA generates the streams; monitor paths and
resampling run on CPU.

Null calibration crosses stationary and benign-variance-shift controls with query rates
{0.10,0.25,0.50}, using 2,000 independent streams per cell from seeds 20288000–20289999. Calibrate
both fixed mixtures. Report one-sided exact Clopper–Pearson upper bounds with simultaneous 95%
Bonferroni coverage over all 12 method/scenario/query cells. The e-process claim remains conditional
on bounded contrasts, the eventwise conditional-mean null, predictable queries, and delays
independent of current outcomes.

## Frozen analysis

The primary effect is the macro detection-rate difference, computed by first averaging the paired
candidate-minus-reference detection indicator across the 18 cells within each seed. Estimate a
95% percentile interval by resampling the 2,000 independent seed clusters with replacement, 20,000
replicates, random seed 20261025. Do not treat the 18 outcomes sharing a seed as independent.

Also report all 18 cellwise rates, exact two-sided McNemar tests, and Holm adjustment across the 18
tests. Report event and wall delay among detections, censored nondetections, and pre-onset alarms.
Retain the late prior as a useful option only if the cluster-bootstrap interval for macro difference
lies above zero, its null upper bounds remain below 5%, and it has no cellwise detection loss greater
than five percentage points. Otherwise retain uniform as the default. A positive result supports only
the registered synthetic conditions and does not establish novelty.

## Reproduction

From the repository root, run:

    uv run shiftlab-dive-late-prior-confirmation --device cuda --streams-per-cell 2000 --null-streams 2000 --alternative-seed-offset 20286000 --null-seed-offset 20288000 --output-dir outputs/late_prior_confirmation

The runner writes per-stream Parquet and CSV metrics, cellwise and macro paired analyses, a manifest
with seed intervals, environment, source hashes, and checksums, and a report. No figure is needed;
any later visual should use PaperBanana.
