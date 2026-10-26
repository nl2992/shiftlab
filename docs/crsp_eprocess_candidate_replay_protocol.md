# CRSP replay of synthetic-screened e-process candidates

**Status: frozen before this candidate replay.** This experiment applies four existing bounded-mean e-process constructions to the exact aggregate daily paired-cost series saved by the full-cohort CRSP comparison. It does not re-extract WRDS data, change the fitted policy, or establish sequential validity on real data.

## Input and estimand

Read `outputs/crsp_monitor_comparison_full/monitor_trajectory.parquet` after verifying every checksum in that run. The 1,507 rows contain one cross-sectional mean paired candidate-minus-reference cost per test date at the frozen 5-bps turnover charge, plus evaluator-only labels for positive mean paired cost in the next 20 dates. These labels are used only for retrospective ranking.

All monitor candidates receive the same ordered daily paired-cost increments, the same conservative absolute bound `0.20 + 4 * (5 / 10,000)`, `epsilon=0`, and `alpha=0.05`:

1. The fixed five-stake bounded-mean mixture.
2. Predictable plug-in Kelly.
3. Predictable plug-in empirical Bernstein.
4. An equally weighted mixture of eight fixed-start bounded-mean processes, at indices `round(j * horizon / 8)` for `j=0,...,7`. The horizon and weights are fixed before replay.

These are previously implemented constructions. The uniform-start method is included because a synthetic residual-variance screen found a modest gain over a full-stream process in high-severity, high-feedback cells. That result does not imply it will help on CRSP.

## Outcomes

Report each log-e trajectory, threshold crossing at `log(1/alpha)`, crossing frequency on the observed path, maximum log-e, AUROC and average precision for the hindsight next-20-date label, and artifact checksums. Compare monitor ranking only; do not select an algorithm as valid or safe based on this single path.

## Validity and claim limits

The bounded e-process guarantee requires predictable decisions and a conditional-on-past mean excess-cost null at every update. The daily aggregate has cross-sectional aggregation and temporal dependence; CRSP close-date ordering is not verified label-release timing. The dataset does not establish the required filtration or conditional null. Therefore an e-value crossing or noncrossing is descriptive here; its nominal alpha is **not** a claimed CRSP false-alarm rate. The overlapping future-harm labels are evaluator hindsight and cannot be used online. Results concern one frozen, imposed-utility policy comparison, not causal drift or trading.

## Reproduction

```powershell
uv run python scripts/replay_crsp_eprocess_candidates.py `
  --input-dir outputs/crsp_monitor_comparison_full `
  --output-dir outputs/crsp_eprocess_candidate_replay
```

The input checksum file, trajectory hash, protocol hash, source hash, full daily paths, aggregate CSV/Parquet tables and output checksums are saved. No figure is planned; any future visual should use PaperBanana and be checked against the Parquet metrics.
