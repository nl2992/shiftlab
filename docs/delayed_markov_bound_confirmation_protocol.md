# Delayed Markov-volatility confirmation protocol

**Status:** frozen after the separate 60-stream development screen and before opening either validation block, 2026-10-24. No thresholds, stakes, query rule, delay, or harm doses may be tuned on these seeds.

## Candidate and question

Confirm the complete history-only query plus predictable PPI support-bound system at a fixed 12-event label delay against the same history-only query policy with fixed bound `B=M(2/q_min-1)`, `q_min=0.05`. This tests the combination under the registered two-state Markov-volatility process, not the bound in isolation and not a new algorithm. Both systems update their own monitor and can follow different query paths.

The event-time null is `E[Z_t | G_t] <= 0`, where `G_t` contains the complete past including the latent state before current context/outcome generation. Under the exact-zero control, the contrast mean is zero in each latent state. Query propensity and bound are functions of the resolved event prefix and reserved past spend, chosen before current context, outcome, and query coin. The randomized label request is independent conditional on the full past. The learner sees no latent state. Queried labels arrive after exactly 12 events, and alarms may use only a contiguous resolved evidence prefix. The event-time supermartingale plus pathwise prefix-crossing argument supports the same run-level bound under these stated assumptions; the experiment checks code and finite-sample behavior but is not the proof.

## Stage 1: fresh null calibration

- Generate 2,000 independent streams for each of two controls: the exact statewise-zero Markov null and the statewise-strict-negative control.
- Cross each control with fixed and predictable support-bound systems, for four cells total.
- Use Torch seed root `28204027`, horizon 2,400, onset index 1,200, 480 requested-label hard cap, delay 12, and independent state/context/outcome/query random variables. Pair methods and controls with common random numbers within stream.
- Use exact one-sided Clopper–Pearson upper limits with Bonferroni per-cell alpha `0.05/4`. Calibration passes only if all four upper limits are at most 0.05 and every cap, support, prefix-order, and completeness invariant passes.
- Do not run or inspect confirmation alternatives until the calibration gate passes. A failed gate ends this candidate; do not retune on either frozen seed block.

## Stage 2: disjoint harm confirmation

- Only after Stage 1 passes, run 2,000 paired streams at each of the four state-dependent harm doses `{0.04, 0.20, 0.40, 0.60}` using the disjoint Torch seed root `28304027`. Cross both systems with each dose using shared Markov states, contexts, outcome uniforms, query uniforms, and source training data within stream.
- The primary endpoint is the equal-weight average across dose levels of post-onset detection difference (predictable minus fixed), paired by stream. Resample complete stream IDs jointly across all four doses with 10,000 paired bootstrap replicates.
- Retain this candidate only if the two-sided 95% bootstrap lower confidence limit for detection gain exceeds +0.02, the upper limit for the mean paired label-count difference is at most zero, and all four independent Stage 1 simultaneous calibration upper limits are at most 0.05. Failure means stop this candidate without tuning on these blocks.
- Secondary outcomes: per-dose detection, onset reach, pre-onset alarms, event and wall detection delay, processed events, query labels, and evaluator-only cumulative expected harm exposure using latent-state conditional coefficients. Exposure assumes immediate mitigation at alarm and is not observed or empirically prevented loss.

## Scope and reporting

Claims are limited to this two-state Markov-volatility process, fixed action pair and source proxy, history-only predictable query policy, complete labels after deterministic outcome-independent delay 12, and the stated event-time conditional null. The experiment does not cover arbitrary dependence, informative delay used in decisions, non-arriving labels, adaptive candidate search, policy changes, or action-dependent outcomes. This is a standard predictable bounded-factor e-process plus an event-order prefix rule, not a new theorem or algorithm. Report the full cell counts, intervals, seeds, runtime/device, code hashes, checksums, and all failed or censored streams.

No figure is required. Any visual produced for this work must use PaperBanana; if unavailable, report the limitation and keep the deliverable to tables and machine-readable metrics.

## Reproduction

```powershell
uv run python scripts/confirm_delayed_markov_predictable_bounds.py --stage calibration --streams 2000 --seed 28204027 --device cuda --output outputs/delayed_markov_predictable_calibration_2000
uv run python scripts/confirm_delayed_markov_predictable_bounds.py --stage confirmation --streams 2000 --seed 28304027 --device cuda --calibration-summary outputs/delayed_markov_predictable_calibration_2000/metrics/calibration.csv --output outputs/delayed_markov_predictable_confirmation_2000
uv run pytest tests/test_delayed_markov_predictable_bounds.py -q
```
