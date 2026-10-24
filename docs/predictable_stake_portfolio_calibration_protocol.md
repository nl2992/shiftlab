# Predictable stake portfolio development screen

**Status:** the development design is preserved in `predictable_stake_portfolio_development_protocol.md`. This calibration/confirmation extension was frozen after the development result and before calibration on 2026-10-24. Development seed root `28704027`;
independent calibration root `28714027`; disjoint confirmation root `28724027`. The development
screen is exploratory and does not itself calibrate a method or establish novelty.

## Question

The existing bounded-mean monitor uses a fixed equal-weight mixture over five nonnegative stakes.
The repository also has single-process predictable Kelly betting and discounted Kelly processes,
but no matched-path screen that rebalances a portfolio across the five existing stake processes.
Test whether predictable reweighting improves detection under the already selected periodic query
schedule, holding the query and feedback paths fixed.

For each stake `lambda_j` in `{0.05, 0.10, 0.20, 0.40, 0.80}`, define the bounded factor
`g_{j,t} = 1 + lambda_j X_t / B_t`, with `|X_t| <= B_t` and the selected eventwise bound. At the
start of event `t`, set predictable portfolio weights

`w_{j,t}(eta) proportional to w_j exp(eta L_{j,t-1})`,

where `L_{j,t-1}` is the component's cumulative log wealth from previously released events and the
prior `w_j` is uniform. Update portfolio wealth by multiplying by
`sum_j w_{j,t}(eta) g_{j,t}`. For every fixed `eta >= 0`, the weights are pre-outcome, nonnegative,
and sum to one. If each component factor has conditional expectation at most one, their predictable
convex combination does too, so its product is a nonnegative supermartingale. This argument
requires the registered event-time conditional-mean null, predictable propensity, correct complete
queried feedback, and the declared support bound. It does not make weights chosen after observing
the current increment valid.

At `eta=0`, weights stay uniform at every event. This is a predictable equal-rebalanced strategy,
not a history-adaptive weight rule; it differs from selecting one stake for the whole stream and
mixing its terminal wealth. At `eta=1`, the portfolio is algebraically identical to the existing
fixed stake mixture; this is an exact implementation check. The prespecified development grid is
`eta in {0, 0.25, 0.5, 0.75, 1, 1.5, 2}`. Stakes, prior weights, threshold, simulator, propensity
schedule, action pair, proxy, delay, and label cap are fixed. Continue updates after a crossing, as
in the parent benchmark.

## Matched paths and outcomes

- Generate 60 shared streams per each of the two registered nonpositive-mean controls and four
  Markov-volatility harm doses using CUDA when available; use the validated common-random-number
  generator and its independent source proxy.
- Use the selected phase-balanced periodic schedule `q=0.05` on eight positions and `q=0.80` on
  two positions of every ten, 2,400 events, deterministic outcome-independent delay 12, and the
  480-label cap.
- Every `eta` sees the same outcomes, randomized query coins, queried labels, event enrollment, and
  processed event prefix. The `eta=1` outputs must match the fixed equal-weight monitor exactly up
  to `1e-12` in log evidence and exactly in alarm/decision fields.
- Primary development selection score: equal-weight mean post-onset detection across the four harm
  doses. Select a nonidentity `eta` only if it improves this score over `eta=1` by at least 3
  percentage points, with a paired stream bootstrap lower 95% limit above zero, and no dose-specific
  detection loss greater than 5 points. This is a screening gate, not confirmation.
- Report per-dose detection, false escalations, pre-onset alarms, delay, labels, processed events,
  evaluator-only expected exposure, path identities, and paired bootstrap intervals. Sixty null
  streams per cell are descriptive, not calibration.

If a nonidentity eta passes, freeze it before a new independent null calibration and disjoint
confirmation. The development block selects `eta=0.0` under the frozen gate. The selected
candidate is therefore uniform per-event rebalancing, not history-adaptive stake selection.
Calibrate the
candidate and the fixed `eta=1` reference on 2,000 fresh streams in each of the two registered
nonpositive-mean controls (four method-by-null cells). Use one-sided exact Clopper-Pearson bounds
with Bonferroni alpha `0.05/4`; all simultaneous upper limits must be at most 5% before running
the alternative confirmation. If calibration passes, use 2,000 fresh paired streams per each of
the four harm doses. The confirmation retention gate requires a macro event-detection gain of at
least 2 percentage points with paired stream-bootstrap 95% lower limit above zero, identical label
and event-prefix paths, all onsets reached, and no cap/support violations. Report dose-level effects
and pre-onset alarms without additional selection. If no candidate passes development, or if
calibration fails, record the negative result and stop this branch. Do not tune the eta grid or
select on confirmatory data. No figure is required; any visual must use PaperBanana.

## Reproduction

```powershell
uv run python scripts/run_predictable_stake_portfolio.py --streams 60 --seed 28704027 --device cuda --output outputs/predictable_stake_portfolio_development
uv run pytest tests/test_predictable_stake_portfolio.py -q
uv run python scripts/confirm_predictable_stake_portfolio.py --stage calibration --streams 2000 --seed 28714027 --device cuda --output outputs/predictable_stake_portfolio_calibration_2000
uv run python scripts/confirm_predictable_stake_portfolio.py --stage confirmation --streams 2000 --seed 28724027 --device cuda --calibration-summary outputs/predictable_stake_portfolio_calibration_2000/metrics/calibration_summary.csv --output outputs/predictable_stake_portfolio_confirmation_2000
uv run pytest tests/test_confirm_predictable_stake_portfolio.py -q
```
