# CRSP CIZ decision-policy pilot: exploratory results

**Status:** frozen retrospective pilot completed 2026-10-27; exploratory only.
This is a distinct policy-comparison task from the full-cohort CRSP monitor
replays. It uses the frozen [pilot protocol](../../docs/crsp_decision_policy_replay_protocol.md)
and does not provide independent confirmation because the 2020–2025 panel was
previously examined.

The run selected 100 PERMNOs from the training-split identifier universe of
11,472 using seed 20261025, without requiring test-period presence. Only 30 of
those sampled PERMNOs appeared in the test split. The train-only CUDA Ridge
model used 166,753 rows from 2000–2014 and was evaluated on 40,557 next-observed
returns from 2020–2025. The candidate was long when its predicted next return
was positive; the reference was long when same-date `vwretd` was positive.
Returns were clipped to ±10%, and entry, position changes and terminal exits
were charged at 0, 5, 10 or 25 bps per unit of turnover.

At the prespecified 5-bps setting, candidate-minus-reference mean cost was
**−0.0005581 per event** (20-trading-date circular block 95% descriptive
interval **[−0.0009119, −0.0002021]**), favoring the candidate under this
imposed capped utility. Differences were −0.0005033, −0.0006130 and −0.0007775
at 0, 10 and 25 bps, respectively; all four block intervals excluded zero.
The candidate's test RMSE was 0.039943 versus 0.039786 for the training-mean
forecast, so it did **not** improve this predictive benchmark despite the
lower imposed decision cost. This single sampled cohort and historical period
do not establish a general decision-aware advantage.

The data manifest, panel observations, frozen protocol, runner and all three
output-file hashes were verified; annual cost means recombine to the overall
totals. The verifier checks artifact integrity and aggregation, not an
independent policy refit or inferential assumptions. Exact metrics and
provenance are in
[`the run artifacts`](../../outputs/shiftguard_unified/real_data_development/crsp_decision_policy_pilot_100_v1/);
re-run the
[`pilot`](../../scripts/evaluate_crsp_policy_replay.py) and its
[`artifact verifier`](../../scripts/verify_crsp_policy_replay.py) to reproduce
the recorded scope.

The sample is small and selected from training identifiers, and only 30
sampled securities contribute test outcomes. The date-block interval does not
account for PERMNO-sampling or model-selection uncertainty and should be read
as descriptive. Historical CRSP publication times are unknown, returns are
dependent across names and dates, and the long-only utility, return cap and
transaction costs are imposed research choices rather than sourced trading
economics. This pilot is not evidence of online monitoring validity, causal
harm, trading profitability or deployment value.
