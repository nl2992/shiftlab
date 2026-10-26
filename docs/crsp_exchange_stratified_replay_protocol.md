# Exploratory CRSP exchange-stratified monitor replay

## Question

Do established bounded-mean monitors provide useful retrospective evidence when run separately by CRSP primary exchange, and does a fixed mixture of their exchange-specific e-values behave differently from the single pooled monitor? This is an exploratory real-data diagnostic intended to broaden the set of candidate methods evaluated on the acquired CRSP panel. It is not an independent confirmation because the full 2020–2025 test period has already been inspected in previous CRSP analyses.

## Frozen policy and utility

Use the same train-only standardized Ridge (`alpha=1`) candidate policy and same-date `vwretd` reference as `docs/crsp_monitor_comparison_protocol.md`. Fit only on the 2000–2014 training split. The candidate holds a long position when its next-observed-return prediction is positive; the reference holds long when same-date `vwretd` is positive. Clip realized next-observed returns to `[-0.10, 0.10]`, and charge 5 basis points for entry, position changes, and each test-path exit. The paired increment is candidate cost minus reference cost, so positive means the candidate costs more under this imposed utility. The same frozen model and event-level policy actions are used in each exchange group.

## Predeclared strata and algorithms

Use the six `primaryexch` codes already in the panel manifest: A, B, I, N, Q, and R. The code assignment comes from WRDS and does not use test outcomes. For each exchange and each test date, aggregate the paired event costs by their arithmetic mean. Dates with no observations in a group contribute no evidence; for the fixed-start method, a zero update advances its calendar start schedule without changing wealth.

Compare two established processes:

1. The fixed five-stake bounded-mean e-process, with the registered daily support bound `0.20 + 4 × (5/10,000)` and `alpha=0.05`.
2. The equal-weight mixture of eight fixed-start bounded-mean processes, with starts fixed at `round(j × T / 8)`, `j=0,...,7`, over the full test-date horizon.

For each method, form the equal-weight mixture of the six exchange-specific e-values. The mixture crosses at `1/alpha`; separate Bonferroni subgroup crossings are also reported at `6/alpha`. Both constructions concern the intersection of the six exchange-specific conditional-mean nulls. This is distinct from the pooled population-average harm null: a subgroup can be harmful while gains elsewhere offset it.

## Outcomes and limits

Report event/date support and average paired cost for each exchange, each stratum's log-e path, the equal-weight mixture path, crossings, and retrospective AUROC/average precision against evaluator-only positive mean paired cost over the next 20 test dates. Those labels overlap and are never supplied to a monitor. All monitor scores are run over the same ordered dates and frozen candidate actions.

The textbook e-process arguments require a previsible stratum assignment, bounded increments, and the relevant exchange-specific conditional-on-past mean null. On CRSP, publication times, label availability, cross-name aggregation and temporal dependence are not established. The observed crossings and nominal thresholds are therefore descriptive, not error-rate guarantees. The test period has already been analyzed, so this run cannot support a confirmatory method-selection claim. A future confirmatory real-data study needs a frozen method and a genuinely new period or independent dataset with auditable outcome-release times.

## Reproduction

```powershell
uv run python scripts/replay_crsp_exchange_stratified_monitors.py `
  --root data `
  --device cuda `
  --batch-size 200000 `
  --output outputs/crsp_exchange_stratified_replay
```

The runner verifies the panel manifest checksum and refuses to overwrite a nonempty output directory. It records the panel, policy, monitor and protocol hashes, CSV/Parquet paths, a results report, and checksums. No figure is required for this analysis; if one is later commissioned, use PaperBanana and validate it against the saved aggregate metrics.
