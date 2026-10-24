# Decision-risk proxy stress grid results

## Registered design and verification

The CUDA run used an NVIDIA GeForce RTX 4060 Laptop GPU and a fresh seed block beginning at
20402024. It completed **180 design cells**, **12 paired streams per cell**, and **12,960
method-stream rows** across boundary-local harm, residual-variance shift, recurring regimes, and
harmful adaptation. The grid crossed three severity levels where meaningful, false-negative to
false-positive cost ratios of 5:1 and 1:1, training fractions 5%, 12.5%, and 25%, and query rates
10%, 20%, and 40%. Each cell used the same outcome/query path across the six proxy methods.

The post-run verifier checked the Parquet checksum and row count against the manifest, confirmed 12
seeds and all six methods in every cell, verified identical label counts, dollar spend, and
processed-event counts across methods within every stream, and confirmed every hard budget was
respected. The seed block does not overlap the prior proxy-Hedge development run. The manifest
records the GPU, code hashes, design, and metrics checksum in
[`outputs/risk_proxy_stress_grid/`](../outputs/risk_proxy_stress_grid/).

## Findings

The logistic risk proxy had the lowest aggregate estimator RMSE: **1.014**, compared with **1.056**
for validation-best, **1.127** for prequential Hedge, **1.227** for ridge, **1.231** for random
forest, and **1.288** for zero. Averaging paired differences within each seed and bootstrapping
those 12 seed clusters, risk-model RMSE was lower than ridge by **0.213** (95% interval
**[−0.230, −0.197]**), lower than validation-best by **0.042** (**[−0.060, −0.026]**), and lower
than Hedge by **0.113** (**[−0.123, −0.102]**). It beat ridge on RMSE in every cell and beat
validation-best in 40 cells, lost in 56, and tied in 84. The validation selector chose the logistic
proxy in about **69.6%** of the cell/seed fits.

That estimation advantage did not yield a measurable detection advantage. Under the balanced 1:1
cost regime, the deployed 0.5-threshold action and the reference coincide in the boundary, recurring,
and residual-variance scenarios; those cells have no material harm and are excluded from the
conditional power denominator. Over the remaining **1,179 material-harm streams per method**,
detection was **36.73%** for the risk proxy, **36.47%** for ridge, **36.81%** for validation-best,
and **37.23%** for Hedge. Seed-clustered paired differences were +0.21 percentage points versus
ridge (95% interval **[−2.23, +2.36]**), −0.10 points versus validation-best (**[−0.56, +0.25]**),
and −0.55 points versus Hedge (**[−2.10, +0.76]**). These data do not support a detection gain over
any comparator. Detection differences varied with query rate: the risk proxy's difference versus
ridge was −1.02 points at 10%, −1.02 at 20%, and +2.80 at 40%. That subgroup pattern is exploratory
and not a confirmed interaction.

No pre-onset escalation occurred. The 81 cost-balanced classifier/boundary cells are structural
zero-harm controls because the two actions coincide; the other cells are alternatives. There are no
nondegenerate population-null streams, so this is not a false-alarm calibration result. Twelve seeds
per cell are adequate only for screening large changes. The broad low detection rates also show that
an improved proxy alone does not solve the monitor's evidence-efficiency limitation.

## Research decision

Keep the logistic model as the strongest tested **estimation** proxy in this grid. Do not claim a
monitoring-power improvement or novelty: its RMSE improvement is robust across the registered
conditions, but detection remains statistically unresolved. The next grounded experiment should
hold this proxy and the matched query paths fixed, then compare established bounded-mean and
variance-sensitive anytime monitors. Since those monitors already exist in the repository, the
research question is whether lower-residual-variance PPI inputs yield useful power under a
nondegenerate, independently calibrated null—not whether a new confidence sequence can be named.

The aggregate results were not made into a plot. PaperBanana should be used for any later research
visual, with every displayed value checked against the saved metrics.
