# Predictable stake portfolio development screen

**Status:** frozen before the development run, 2026-10-24. Seed root `28704027`. This screen is
exploratory and does not calibrate the selected method or establish novelty.

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

At `eta=1`, the portfolio is algebraically identical to the existing fixed stake mixture; this is
an exact implementation check. The prespecified development grid is
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
confirmation. If none passes, record the negative result and retain the fixed mixture. Do not tune
the eta grid or select on confirmatory data. No figure is required; any visual must use PaperBanana.

## Reproduction

```powershell
uv run python scripts/run_predictable_stake_portfolio.py --streams 60 --seed 28704027 --device cuda --output outputs/predictable_stake_portfolio_development
uv run pytest tests/test_predictable_stake_portfolio.py -q
```
