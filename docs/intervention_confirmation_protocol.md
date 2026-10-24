# Independent intervention confirmation

**Status:** Frozen, independent-seed confirmation. The design was selected from the
development-only grid in [the sensitivity protocol](intervention_sensitivity_protocol.md).
No parameter will be tuned on this confirmation block.

## Frozen setting

Use `q=0.80`, a 40% realized-label cap over 1,600 events, label price 0.01, promotion cost
0.05, and rollback cost 0.05. This was the highest-macro-utility design among those with the
reference label price 0.01 in the 60-seed development grid. Its development macro utility was
53.48 for promotion-plus-rollback and 47.43 for promotion-only; the paired difference was
6.05 with a descriptive 95% seed-cluster interval [4.96, 7.14]. The interval is subject to
development selection and is not confirmatory.

Use 2,000 fresh seeds per scenario and 800 events per phase. The seed offset is 52,102,626,
disjoint from both the initial benchmark and the development grid. Compare continue,
unconditional promotion, promotion-only, and promotion-plus-rollback. The six reversal
profiles vary onset across 10%, 50%, and 80% of deployment and post-reversal mean gain across
-0.10 and -0.20. Five controls include zero gain in both phases, persistent positive gain,
strong shadow-only benefit followed by zero deployment gain, future-only deployment benefit,
and weak persistent benefit.

## Error and utility criteria

Report phase-specific promotion-null errors on both zero-shadow-gain controls (`no_benefit`
and `late_benefit`) for promotion-only and promotion-plus-rollback. Report rollback-null
errors on all five non-harmful deployment controls for promotion-plus-rollback. The family
contains nine cells; report exact one-sided Clopper-Pearson upper limits with a Bonferroni
family correction at 95% confidence. The e-process component alpha remains 0.025 per stage.

The primary utility contrast is the equal-weight mean across the six reversal profiles of
paired expected net utility for promotion-plus-rollback minus promotion-only. Construct the
95% interval by resampling the 2,000 seed clusters, each cluster containing one stream from
each reversal profile. Secondary contrasts compare the same policy with continue. Pass the
development hypothesis only if the primary interval is above zero, the hard cap is respected,
and every phase-specific null's simultaneous upper limit is at most 0.025. Otherwise retain
the negative result and do not retune against this block.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m shiftlab.dive.intervention_confirmation `
  --device cuda --seeds 2000 --horizon 800 --bootstrap-replicates 10000 `
  --output-dir outputs/intervention_confirmation
```

GPU is used for potential-cost and query-stream generation. Betting updates and analysis run
on CPU. The output includes seed-level Parquet/CSV metrics, per-scenario summaries and
contrasts, the primary reversal-macro interval, calibration results, code and data checksums,
and hardware/software metadata. No figure is specified; any later research visual must use
PaperBanana per the repository guidance.
