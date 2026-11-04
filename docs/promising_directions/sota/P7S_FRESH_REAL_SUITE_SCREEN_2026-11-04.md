# P7s fresh-stream comparator screen — 2026-11-04

**Status:** exploratory comparison on exposed benchmark outcomes; not untouched confirmation.

## Question

Does P7s retain its cost/label-efficiency signal against the available source-matched suite when
policies receive the actual binary labels and frozen-model predictions from the five chronological
UCI streams? The primary comparator is Gated Deployment; the remaining default suite is reported
as secondary.

## Frozen design

- Source stream and model pair: [`fresh_real_protocol.md`](../../sota_sprint/fresh_real_protocol.md).
  Keep its train-only preprocessing, chronological episodes, paired fixed models and delay
  assignments unchanged.
- Policy inputs: actual `labels`, `predictions`, and `starts` exported from the frozen builder;
  verify `prediction != label` reproduces the saved `l0/l1` arrays exactly before simulation.
- Methods: the full default suite in `run_vs_sota.py`; feature-dependent methods remain explicitly
  not-run because contexts and fitted nuisance models are not supplied by this simulator.
- Contract: `T=2000`, `B=200`, `c_q=.05`, `c_s=5`, `alpha=.05`, `eps=0`, `p_min=.05`, 20
  query seeds per episode, seed base `20261101`, delays as registered by the fresh-data protocol.
- Primary statistic: episode-level mean paired `P7s - Gated` net cost, negative favoring P7s.
  Report all per-dataset contrasts and action/cost decompositions; do not pool episodes as
  independent across a source time series.

## Interpretation

The underlying data and outcomes have already been used by the SOTA sprint for other policies.
This is therefore not a confirmatory holdout for the overall research programme. Report it as an
exposed, source-faithful predictive-loss replay. Label publication delays and query/switch prices
are imposed assumptions; the result does not establish production feedback validity or causal
deployment value. A favorable result can nominate a new preregistered task on untouched data, but
cannot satisfy the SOTA completion gate by itself.

## Reproduction

```powershell
uv run python scripts/sota_sprint/fresh_real.py --save-policy-inputs
uv run python scripts/promising_directions/sota/run_vs_sota.py `
  --datasets metro,beijing_pm25,bike_hour,appliances,household_power `
  --loss-roots data/sprint_fresh_losses `
  --policy-input-roots data/sprint_fresh_policy_inputs `
  --label-mode cached `
  --n-seeds 20 `
  --out outputs/p7s_fresh_real_suite_screen_corrected
```

## Amendment: registered delays restored

The first completed invocation is **invalidated**: the runner used its old fallback delay of 100
events for every stream, while the registered fresh-data protocol specifies 24 events for metro,
beijing_pm25, and bike_hour, and 144 events for appliances and household_power. The fixed runner
now maps each fresh stream to that registered delay. The first output directory
`outputs/p7s_fresh_real_suite_screen/` is retained only as a debugging artifact and must not be
used for any reported result. The reproduction command above writes the corrected run to a separate
directory. The runner reports episode-level percentile bootstrap intervals (4,000 resamples); these
are descriptive and optimistic because episodes are consecutive windows of the same series.
