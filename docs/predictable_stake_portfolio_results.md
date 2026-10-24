# Predictable stake portfolio: development and calibration

**Decision:** stop the selected candidate before alternative confirmation. It passed the
development nomination gate, but did not pass the predeclared simultaneous null-calibration gate.

## Development screen

The frozen 60-stream-per-cell CUDA-generated screen compared seven predictable convex portfolios
of the existing five bounded betting factors, `eta ∈ {0, .25, .5, .75, 1, 1.5, 2}`, on a common
periodic `q ∈ {.05,.80}` query schedule, delayed-label path, and 480-label cap. Every method shared
identical query, labels, event enrollment, and processed event prefixes. All onsets were reached;
there were no support or budget violations.

The `eta=0` equal-per-event rebalanced portfolio detected 27/240 harm streams (11.25%), compared
with 15/240 (6.25%) for the existing `eta=1` fixed mixture. The paired macro difference across
four doses was **+5.00 percentage points** (seed-cluster bootstrap 95% interval **[+2.50,+7.92]**).
Dose-specific differences were +1.67, +1.67, +5.00, and +11.67 points for effects 0.04, 0.20,
0.40, and 0.60. The development nomination rule passed. This block is exploratory and its small
null counts are not calibration.

At `eta=0`, the weights remain uniform at every event. The selected candidate is a predictable
equal-rebalanced strategy, not a history-adaptive weight rule. Its validity follows from multiplying
predictable convex combinations of nonnegative bounded-mean supermartingale factors. This is a
standard construction; no novelty claim is made.

## Independent null calibration

The frozen calibration used 2,000 fresh streams for each of the two nonpositive-mean controls and
both methods. With four cells and Bonferroni familywise 95% one-sided exact Clopper-Pearson limits:

| Scenario | Method | False escalations | Rate | Simultaneous upper limit |
|---|---|---:|---:|---:|
| Exact marginal null | Fixed mixture (`eta=1`) | 48/2,000 | 2.40% | 3.286% |
| Exact marginal null | Equal rebalancing (`eta=0`) | 88/2,000 | 4.40% | **5.541%** |
| Strict-negative control | Fixed mixture (`eta=1`) | 4/2,000 | 0.20% | 0.563% |
| Strict-negative control | Equal rebalancing (`eta=0`) | 5/2,000 | 0.25% | 0.637% |

The candidate's exact-null simultaneous upper limit exceeds the frozen 5% cutoff, so it did not
clear calibration. This does not show that its true error rate exceeds 5%; the observed rate was
4.40%, and the interval was too wide for the registered familywise gate. The disjoint harm
confirmation was therefore not run. Do not interpret the development power difference as an
independent performance result.

## Artifacts and reproduction

The [pre-run development protocol](predictable_stake_portfolio_development_protocol.md), [independent-stage protocol](predictable_stake_portfolio_calibration_protocol.md), and [protocol index](predictable_stake_portfolio_protocol.md), plus the [runner](../scripts/run_predictable_stake_portfolio.py),
[independent calibration runner](../scripts/confirm_predictable_stake_portfolio.py), and
[tests](../tests/test_predictable_stake_portfolio.py) describe the method and checks. Development
stream metrics, cell summaries, paired contrasts, selection record, and hash manifest are in
[`outputs/predictable_stake_portfolio_development/`](../outputs/predictable_stake_portfolio_development/).
Independent calibration metrics and its manifest are in
[`outputs/predictable_stake_portfolio_calibration_2000/`](../outputs/predictable_stake_portfolio_calibration_2000/).

```powershell
uv run python scripts/run_predictable_stake_portfolio.py --streams 60 --seed 28704027 --device cuda --output outputs/predictable_stake_portfolio_development
uv run python scripts/confirm_predictable_stake_portfolio.py --stage calibration --streams 2000 --seed 28714027 --device cuda --output outputs/predictable_stake_portfolio_calibration_2000
```

No figure was generated. Research visuals must use PaperBanana; it was unavailable in the active
environment.
