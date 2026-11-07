# EIA-930 rare-disagreement development replay

**Status:** prospective development screen, not confirmation. No algorithm outcomes or model-pair
loss streams were examined before this protocol. The only source exposure was the two-row PJM API
schema smoke inspection documented in `research/scoped_method/ELECTRICITY_SOURCE_FEASIBILITY_20261107.md`.

## Question and Failure Atlas target

Test whether the published PFA-SR detector, attached to the existing Gated deployment host, can
transfer to a real chronological load-classification stream with sparse disagreements (Failure
Atlas `F8_rare_better`), and whether it has lower economic cost than its matched-host restart
baseline and the strongest fast selector. This is an application/transfer study of published
PFA-SR, **not a novelty claim**. The target matches F8 only if disagreement frequency is in
`[0.01, 0.05]` and the challenger is correct on at least `0.85` of disagreement events. If either
condition fails, report the F8 transfer as a mismatch; do not relabel the target after outcomes.

## Data and paired models

Source: U.S. EIA-930 hourly BA operating data, official API route
`/v2/electricity/rto/region-data/data/`. Frozen BA registry: `PJM`, `ERCO`, `CISO` (three U.S.
interconnection areas; correlated EIA/grid subclusters, not three independent data providers).
Fetch both `type=D` (realized demand) and `type=DF` (day-ahead demand forecast), use UTC `period`,
and retain source metadata and hashes. The source's current values can be revised, so this is a
retrospective real-data replay with **simulated** feedback timing; it is not a replay of historical
label versions.

For each BA, calculate a high-load cutoff as the 90th percentile of `D` on the fixed 2021-01-01
through 2021-12-31 training interval. On every evaluated event `t`, the incumbent is a one-day
UTC persistence classifier (`D[t-24h] >= cutoff`), the challenger is the BA's published day-ahead
forecast classifier (`DF[t] >= cutoff`), and the target is `D[t] >= cutoff`. The 2021-01-01 through
2021-12-31 interval is training; 2022-01-01 through 2023-12-31 is development only. No test
outcomes or test-trained preprocessing are used. Rows with missing/nonpositive D or DF, a populated
EIA imputed-demand field, absent D[t-24h], and duplicate UTC timestamps are excluded by this fixed
rule. No imputation is allowed. Predictions for event t are treated as available
before t; labels are released at `t+1 hour`, a simulated schedule based on EIA's documented typical
availability. Use current corrected D values as targets and as lagged persistence inputs; explicitly
record that this is a simulation simplification because the historical vintages are not retained.

Partition each BA's eligible stream into contiguous runs of hourly UTC observations. Within each
run, partition from its first retained timestamp into consecutive, non-overlapping 2,000-event
episodes; discard each final incomplete episode and never bridge a missing hour. For each episode, use
T=2,000, hard label budget B=200, label cost 0.05, switch cost 5, delay=1 event, and alpha=.05.
These costs define the Failure Atlas replay contract; they are not field cost estimates.

## Frozen method panel and estimands

Primary candidate: `PFA-SR:gated_deployment`. Primary matched comparator:
`rmm:gated_deployment+RMM`. Competitive controls: `SMCS+retain-incumbent`,
`xu_acquisition_only`, `gated_deployment`, `gated_adaptive_range`, `cams_adapter`,
`online_llm_picker`, `model_selector_causal`, `model_picker_adapter`, `gong_zhang_paid_obs`,
`qiu_delayed_movement`, and `CONTROL_never_switch`. Use the existing
implementations and same simulator contract for all methods. Report all methods. Do not choose a
real-data comparator based on this development outcome.

Primary endpoint is paired net cost per 2,000 events: binary prediction errors + 0.05 times labels
requested + 5 times deployment switches. Also report its three components, promotion/rollback
counts and times, disagreement rate, and conditional challenger correctness on disagreements.
Paired uncertainty uses 2,000 bootstrap resamples of the non-overlapping 2,000-hour episode blocks
within each BA and reports each BA separately. Episode count, within-block serial dependence, and the
three-cluster limitation must remain visible; do not treat event rows or BAs as independent
observations. A development signal requires
at least five units saved versus both the matched RMM and the prespecified fastest atlas comparator
CAMS, with the paired 95% interval wholly below zero in at least two BAs. This gate only licenses a
new frozen protocol; it does not establish
anytime validity or source-generalization.

## Data access, run, and provenance

Retrieve only the three registered BAs and periods needed for the 2021-2023 split through the
official no-key six-month balance CSVs for `2021_Jan_Jun`, `2021_Jul_Dec`, `2022_Jan_Jun`,
`2022_Jul_Dec`, `2023_Jan_Jun`, and `2023_Jul_Dec`. Filter by the frozen BA list and columns before
retaining rows; store raw responses under ignored `data/raw/eia930_f8_development_20261107/` and
hash every original file. The API attempt returned HTTP 429 with public `DEMO_KEY` before any data
were retrieved and before any policy outcome was computed. Build the paired stream and outcomes
only after this protocol amendment is committed. Hash every stream, source script, method source,
and result. No locked source or confirmation window is opened in this development run.

## Limitations fixed in advance

This uses a classification threshold of load (not a full-valued forecasting objective), a persistence
incumbent, a retrospectively revised target, simulated label-release timing, hypothetical Atlas
costs, and only one upstream provider. Any positive result would justify only a separate multi-source
confirmation design. PFA-SR is existing prior art and its conditional-null guarantee is not claimed
for serially dependent EIA data.
