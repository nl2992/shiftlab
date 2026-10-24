# Fixed start-time prior: fresh validation results

The center Beta(2,2) start prior selected on the 30-seed development block was frozen before
validation. It was compared with the uniform eight-start mixture on CUDA-generated streams. The
validation design and seed blocks are registered in
[`start_prior_validation_protocol.md`](start_prior_validation_protocol.md); full stream outcomes,
cell summaries, environment, and checksums are in
[`outputs/start_prior_validation/`](../outputs/start_prior_validation/).

The null study covered 2,000 independent streams per scenario and query-rate cell. The center prior
had false-escalation rates from 0.15% to 0.85%; uniform had 0.20% to 0.90%. All 12 one-sided exact
Clopper–Pearson upper bounds, with simultaneous 95% Bonferroni coverage over both methods and all
null cells, were at most **1.62%**. This is consistent with the expected 5% threshold under the
simulated stationary and benign-variance nulls. The e-process argument remains conditional on its
bounded conditional-mean null and registered filtration assumptions.

On the 12 paired alternative cells with 2,000 streams per cell, macro-cell detection was **80.43%**
for center and **79.68%** for uniform, a **0.75 percentage-point** difference. The center prior had
236 center-only detections and 55 uniform-only detections among the 24,000 paired cell-streams.
Six of the 12 prespecified exact cellwise McNemar tests favored center after Holm correction; the
remaining cells were statistically unresolved or at ceiling. The smallest cellwise difference was
−0.05 percentage points (one stream) for center in a high-power late-onset cell; no cell showed a
material observed loss. Pre-onset escalations totaled 86 for center and 96 for uniform.

As a supplementary analysis, the macro detection difference was first averaged over all 12 cells
within each seed, then uncertainty was estimated across the 2,000 independent seed clusters. The
paired mean difference was 0.754 percentage points (95% cluster-bootstrap percentile interval
**0.600 to 0.908 points**, 20,000 resamples, seed 20261024); the paired seed-cluster t-test p-value
was 2.10×10⁻²¹. This macro-level inferential calculation was added after the registered cellwise
analysis and should be treated as supplementary. It avoids treating the 12 outcomes sharing each
seed as independent.

The evidence supports keeping center Beta(2,2) as a tested option for this delayed-feedback
simulator. Gains are modest, several cells are at ceiling, and the center prior is a fixed mixture
of established e-processes rather than a novel method. Keep the uniform mixture as a reference
baseline. The next useful comparison should test robustness to delay distributions, horizon mismatch,
and harm onsets between or outside the eight prescribed starts before using the center prior as a
default.

No figure was generated. If a visual is added later, use PaperBanana as requested by the project
owner.
