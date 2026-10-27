# CriteoPrivateAds real-data development task contract

**Status:** proposed development protocol; not a registered confirmation.
**Source:** CriteoPrivateAds, Hugging Face revision
`343645889b157f104ac23d0d07afa6a18115eb30`.
**Availability audit:** [`criteo_privatead_snapshot_audit.json`](../../data/reports/criteo_privatead_snapshot_audit.json).

## Scientific question

On a real, production-derived advertising prediction task, how do delayed label
availability and label-query budgets change the evidence and cost-sensitive
candidate decisions produced by the existing monitoring and certification
methods? This is a retrospective development question. It is not an estimate
of the causal value of a new bidding policy.

## Source-supported task and information contract

The primary outcome is the publisher's binary `is_clicked` label. `is_visit`,
`is_click_landed`, and `nb_sales` are separate secondary tasks and must not be
combined into a single label. For the primary task, the learner may use only
the source's inference-available feature groups: key-value features,
browser features, and contextual features. The feature group marked
`features_not_available` is evaluator-only and excluded. Display, campaign,
publisher, and user identifiers may define grouping or dependence diagnostics,
but are excluded as predictors unless a separately frozen ablation states
otherwise. The learner cannot observe labels, delay fields, or future day
partitions before they are released.

`day_int` is the only global order used by the primary replay. `display_order`
is local to a user/campaign/day and does not define a global event order. The
publisher intentionally withholds complete display timelines. Therefore, the
replay advances in daily blocks and does not claim event-level chronology.
The publisher describes click, landed-click and sale delay arrays in minutes,
but its paper's 24-hour sale example is written as `24 × 3600 seconds`. A
full aggregate-only scan of all 103,862,032 records passed the 288-file and
30-partition row-count checks. Stored sale-delay values range from −51 to
1,678, consistent with the stated 28-hour window of 1,680 minutes; this is
evidence for minute units, not a resolution of the negative values. Click and
landed-click delay entries also include negative offsets (−58 to −1), and the
source does not define their meaning. All negative click/landed-click entries
occur on rows with positive outcomes. The sale-delay arrays do not align
one-to-one with the derived positive-sales label; the click-delay value count
also exceeds the number of positive click rows, so event-to-label alignment is
not established by the arrays alone. The sample click-positive rate is
36.43%, reflecting the publisher's nonuniform label sampling; it must not be
reported as a deployment click-through rate. Aggregate counts and ranges are
saved in `data/reports/criteo_privatead_delay_audit.json`; no record values
were emitted. The raw delays are diagnostic only until negative-offset and
array-to-label semantics are clarified.

The primary delayed replay will therefore use daily blocks and a conservative
two-day label-maturity convention: labels from block `d` are withheld until
the start of block `d+2`. Immediate and one-day release are sensitivity arms.
This convention is a research assumption based on the publisher's next-day
click and 28-hour sale descriptions; it is not observed per-impression release
time. For negative labels, the maturity convention applies to the whole block
and does not infer maturity from an empty delay array. Report the raw-delay
diagnostics separately from the simulated release schedule.

The source labels are nonuniformly sampled. Primary predictive-risk and
decision-cost summaries use the publisher's case-control reweighting for a
target click-through rate of 0.5%; 0.1% and 1% are prespecified sensitivities.
The sample-distribution metric is also reported so readers can see the effect
of weighting. The weights do not turn imposed action costs into observed ad
revenue.

## Candidate evaluation

Use a fixed, source-supported regularized logistic model first. Construct a
small frozen candidate bank from development days only: the incumbent trained
on an earlier block, a candidate updated on a later block, and the incumbent
with recalibration. All certification methods receive the same queried labels
and common candidate score vectors. The deployment decision is interpreted as
a non-performative cost-sensitive classification decision whose realized
label is unaffected by the classifier. No logged bid actions, action
propensities, auction win/loss outcomes, or counterfactual campaign responses
are present, so off-policy or causal bidding-value claims are out of scope.

Report a paired false-positive/false-negative cost frontier using normalized
cost units and prespecified ratios `C_FN/C_FP ∈ {1, 5, 20}`. These are research
scenarios, not monetary values. Include the publisher-recommended weighted
log-loss and calibration metrics alongside thresholded decision cost. Do not
select the cost ratio after inspecting the final block.

## Protocol boundary and stopping rule

The initial run is limited to the source's 30 daily partitions and a single
frozen model family. Days 1–20 may be used for model fitting and method
development; days 21–25 may be used for internal chronological evaluation.
Days 26–30 are excluded from any claim of independent confirmation because
the publisher used them for its published baseline validation. The source
paper also used days 1–25 for training, so all results remain exploratory with
respect to the public benchmark. Do not tune repeatedly on day 26–30 and call
it a held-out result.

The comparison reports: weighted and unweighted predictive loss, calibration,
paired decision-cost difference, promotion/nonpromotion, alarms as descriptive
events, labels consumed, feedback delay under the registered daily convention,
and update counts. Real-data alarm counts do not estimate false-alarm
probability, and there is no known true harmful changepoint. Any anytime-valid
guarantee is restricted to its independently verified assumptions and
calibration evidence; the chronological source replay alone cannot establish
it.

Run the full source only after the metadata audit passes and a streaming
prototype confirms the selected feature groups, outcome-delay representation,
target-prevalence weights, and bounded artifact footprint. Reuse Parquet
partitions directly and keep large transformed copies out of the repository.
If negative-label maturity cannot be supported, stop the delayed-feedback
analysis at click-positive reporting and retain the full-label replay only as
a retrospective predictive/cost-sensitive evaluation.

## Provenance and current limits

The publisher snapshot is approximately 31.7 GiB compressed, 103,862,032
records across 30 partitions, and uses CC BY-SA 4.0. Its source manifest pins
revision, file sizes, and SHA-256 values. The current metadata-only audit
validates all 288 files and row counts without reading or emitting record
values; a full local re-hash is available as a separate audit mode. The
current host has less than 1 GiB of free space; use streaming reads and avoid
materializing a second full copy. The repository's official 1TB ClickLogs,
Attribution, PrivateAds, and unavailable Sponsored Search sources are separate
datasets and must remain distinct in reports.

Primary sources: [Criteo dataset card](https://huggingface.co/datasets/criteo/CriteoPrivateAd),
[Sebbar et al. (2025)](https://arxiv.org/abs/2502.12103).
