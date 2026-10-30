# Real-data eligibility for budgeted delayed switching

**Date:** 2026-10-28. **Status:** source/task audit; no new data run or eligibility claim for final confirmation.

## Decision

No currently audited dataset is eligible for an untouched real-data confirmation of the full
algorithmic claim (paired outcomes, genuinely delayed feedback, defensible decision/availability
clock, hard query budget, and switching utility). The closest development candidate is the
existing CRSP next-observed-daily-return panel, for a narrow **predictive-loss switching replay**
under an explicitly assumed daily clock. It does not support a real-time trading-utility or
deployment claim, and its 2020–2025 test period is already exposed by multiple studies. Do not
call a replay on it confirmatory.

## Candidate-by-candidate contract check

| Candidate | Paired outcome | Feedback timing | Utility/comparator | Prior use and decision |
|---|---|---|---|---|
| CRSP CIZ next-observed daily return | A realized next return can score two forecasts or two fixed return-loss policies on the same event; evaluator can calculate both losses while learner sees only queried labels | Existing panel orders current-close features, next-event decision, and next-close target. This is a retrospective daily convention; WRDS/publication and executable decision times are not verified | Squared prediction loss is identifiable; any decision-cost or turnover charge is imposed. No execution-cost or market-impact model | 2020–2025 test has been used in a 100-PERMNO decision-policy pilot, full-cohort monitor/e-process/exchange replays and related diagnostics. **Development-only; no untouched confirmation** |
| Criteo Attribution | Common labels can score two conversion predictors | Dataset defines a 30-day conversion window, but actual label publication is unavailable. Under the registered `impression + 30 days` maturity convention, only 544,424/16,468,027 labels (3.31%) mature by the end of its 30.917-day event stream | Predictive loss only; no application-grounded utility. | The full sequence was scanned in the maturity audit. **Not suitable for informative within-stream switching or untouched confirmation** |
| CriteoPrivateAds | A common click/sale label can score two fixed predictors; paired action/auction utility is unavailable without logged propensities and a causal design | The publisher's delay field is event-time delta for click/sale, explicitly supplied to simulate Privacy Sandbox reporting; displays are placed at day 00:00 so complete timelines are withheld. It is not an observed label-publication/release clock. A 2-day maturity rule is imposed, not publisher timing. | Costs are imposed; no causal auction value or trading-style deployment utility. Labels are non-uniformly sampled and negatives downsampled; weighted validation is required. | Full source and aggregate delay fields have been audited; days 26–30 are publisher baseline validation, not a pristine holdout. **Development sensitivity only; not evidence for actual delayed-label acquisition** |
| Open Bandit Dataset | A common observed click can score two fixed click predictors; counterfactual action values require OPE/model assumptions | UTC impression times exist; reward-release and feature-availability clocks are unknown | Click value only; fixed-horizon offline OPE, not online reversible switching | Seven-day sequence already used for development; no verified delayed-feedback contract. **Not eligible** |
| WILDS CivilComments | Common target scores two fixed classifiers | No within-stream event or label-release times | Classification loss, no application cost | Test partition has prior exposure and is offline. **Not eligible** |

The publisher's [dataset card](https://huggingface.co/datasets/criteo/CriteoPrivateAd/blob/ea4a79a5b87e7fa0c435a4b28ff112df12e222f3/README.md) explicitly calls the delay a simulation field and documents the day-00:00 timeline truncation. Its [companion paper](https://arxiv.org/html/2502.12103) describes non-uniformly sampled labels and negative downsampling. These semantics rule out treating the local Criteo copy as an observed request/release stream. The data may still support carefully weighted predictive-loss sensitivity analyses under an imposed delay model.

The supporting source records are [`crsp_study_execution.md`](crsp_study_execution.md),
[`real_data_task_contracts.md`](../papers/shiftguard_unified/real_data_task_contracts.md),
[`real_data_inventory.md`](../papers/shiftguard_unified/real_data_inventory.md), and the
[`Criteo maturity audit`](../papers/shiftguard_unified/criteo_maturity_audit_protocol.md).
The Criteo aggregate count and limitations are also recorded in [`next_phase_plan.md`](next_phase_plan.md).

## Narrow development protocol if G1–G3 pass

Use the CRSP panel only to test whether the algorithm's query/switch accounting and relative
predictive-loss behavior survive a dependent real sequence. Fit two frozen return predictors on
the registered training interval; select any tuning only on validation; use the calibration block
only for prespecified calibration; and replay decisions over a development segment of the already
exposed test period. Define each paired outcome as the two predictors' losses on the same next
observed valid return. Give the learner that pair only after the next daily event under the stated
retrospective convention. Reserve every query at initiation, count pending labels against the
budget, and report sensitivity to one- and two-event release delays. Bootstrap by calendar blocks
and security clusters; never treat rows as independent. State that the close-time ordering, release
delay, query cost and any switching charge are imposed assumptions. This is exploratory external
sequence evaluation, not a validity, causal-shift, financial-profit, or prospective-deployment test.

Do not start this run until the algorithm and matched-budget baselines are frozen after G1–G3;
reuse of exposed test data for development cannot be repaired by new seeds. Keep the existing
CRSP estimands and output directories unchanged.

## Dependency for a genuine real-data confirmation

Before G4 can pass, acquire a **new chronological period not previously inspected for outcomes**
for the frozen task, with (a) point-in-time feature snapshots and documented publication times,
(b) event and label-availability times or an auditable fixed-delay service contract, (c) both
candidate losses identifiable from a common outcome, (d) application-grounded switching/query
costs if claiming economic utility, and (e) a license and source hash that permit the proposed
analysis. A new CRSP year alone would still need a point-in-time availability/execution contract;
otherwise it supports only a retrospective predictive diagnostic. If no source meets these
conditions, report G4 as unmet and narrow the empirical scope rather than upgrading imposed clocks
or costs into observed facts.
