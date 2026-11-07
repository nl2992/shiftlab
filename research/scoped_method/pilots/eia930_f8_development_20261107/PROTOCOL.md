# EIA-930 rare-disagreement development replay

**Status:** prospective development screen, not confirmation. No algorithm outcomes or model-pair
loss streams were examined before this protocol. The only source exposure was the two-row PJM API
schema smoke inspection documented in `research/scoped_method/ELECTRICITY_SOURCE_FEASIBILITY_20261107.md`.

## Question and Failure Atlas target

Test whether the published PFA-SR detector, attached to the existing Gated deployment host, can
transfer to a real chronological load-classification stream with sparse disagreements (Failure
Atlas `F8_rare_better`), and whether it has lower economic cost than its matched-host restart
baseline and the strongest fast selector. This is an application/transfer study of published
PFA-SR, **not a novelty claim**. If the observed disagreement rate is not rare or the forecast
model is not strongly better conditional on disagreement, report the target as a mismatch and do
not relabel the target after outcomes.

## Data and paired models

Source: U.S. EIA-930 hourly BA operating data, official API route
`/v2/electricity/rto/region-data/data/`. Frozen BA registry: `PJM`, `ERCO`, `CISO` (three U.S.
interconnection areas; correlated EIA/grid subclusters, not three independent data providers).
Fetch both `type=D` (realized demand) and `type=DF` (day-ahead demand forecast), use UTC `period`,
and retain source metadata and hashes. The source's current values can be revised, so this is a
retrospective real-data replay with **simulated** feedback timing; it is not a replay of historical
label versions.

For each BA, calculate a high-load cutoff as the 90th percentile of `D` on the fixed 2019-01-01
through 2020-12-31 training interval. On every evaluated event `t`, the incumbent is a one-day
UTC persistence classifier (`D[t-24h] >= cutoff`), the challenger is the BA's published day-ahead
forecast classifier (`DF[t] >= cutoff`), and the target is `D[t] >= cutoff`. The 2021-01-01 through
2023-12-31 interval is development only. No test outcomes or test-trained preprocessing are used.
Rows with missing/nonpositive D or DF, absent D[t-24h], and duplicate UTC timestamps are excluded
by this fixed rule. No imputation is allowed. Predictions for event t are treated as available
before t; labels are released at `t+1 hour`, a simulated schedule based on EIA's documented typical
availability. Use current corrected D values as targets and as lagged persistence inputs; explicitly
record that this is a simulation simplification because the historical vintages are not retained.

Partition each BA's eligible stream from the first retained development timestamp into consecutive,
non-overlapping 2,000-event episodes; discard a final incomplete episode. For each episode, use
T=2,000, hard label budget B=200, label cost 0.05, switch cost 5, delay=1 event, and alpha=.05.
These costs define the Failure Atlas replay contract; they are not field cost estimates.

## Frozen method panel and estimands

Primary candidate: `PFA-SR:gated_deployment`. Primary matched comparator:
`rmm:gated_deployment+RMM`. Competitive controls: `SMCS+retain-incumbent`,
`xu_acquisition_only`, `gated_deployment`, `gated_adaptive_range`, `cams_adapter`,
`model_selector_causal`, `qiu_delayed_movement`, and `CONTROL_never_switch`. Use the existing
implementations and same simulator contract for all methods. Report all methods. Do not choose a
real-data comparator based on this development outcome.

Primary endpoint is paired net cost per 2,000 events: binary prediction errors + 0.05 times labels
requested + 5 times deployment switches. Also report its three components, promotion/rollback
counts and times, disagreement rate, and conditional challenger correctness on disagreements.
Paired uncertainty uses a seven-day moving-block bootstrap within each BA and reports each BA
separately. Episode count, overlapping dependence, and the three-cluster limitation must remain
visible; do not treat event rows or BAs as independent observations. A development signal requires
at least five units saved versus both the matched RMM and CAMS, with the paired 95% interval wholly
below zero in at least two BAs. This gate only licenses a new frozen protocol; it does not establish
anytime validity or source-generalization.

## Data access, run, and provenance

Retrieve only the three registered BAs and the 2019-2023 periods through the official EIA API, with
`DEMO_KEY` or a user-held `EIA_API_KEY` (never store a key). Use paged requests capped at 5,000 rows;
store raw responses under ignored `data/raw/eia930_f8_development_20261107/`. Build the derived
paired stream and run outcomes only after this protocol is committed. Hash every raw response,
stream, source script, method source, and result. No locked source or confirmation window is opened
in this development run.

## Limitations fixed in advance

This uses a classification threshold of load (not a full-valued forecasting objective), a persistence
incumbent, a retrospectively revised target, simulated label-release timing, hypothetical Atlas
costs, and only one upstream provider. Any positive result would justify only a separate multi-source
confirmation design. PFA-SR is existing prior art and its conditional-null guarantee is not claimed
for serially dependent EIA data.
