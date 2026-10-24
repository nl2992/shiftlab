# Independent null-calibration replication

**Status:** Frozen-size calibration replication for the intervention design selected on the
development block and used in the independent utility confirmation. The prior 2,000-stream
confirmation observed a 1.75% rollback rate under the selected zero-gain deployment null; its
simultaneous upper limit of 2.64% did not clear the predeclared 2.5% empirical gate. This
replication resolves that uncertainty without changing the rule or its parameters.

Use the same frozen design: `q=0.80`, 40% label cap, label price 0.01, promotion cost 0.05,
rollback cost 0.05, stage alpha 0.025. Run 10,000 fresh streams per each of five controls:
zero gain in both phases, persistent positive gain, strong shadow-only benefit followed by
zero deployment gain, future-only deployment benefit, and weak persistent benefit. The seed
offset is 62,102,626 and is disjoint from both previous blocks.

Report the same nine phase-specific family cells as the independent confirmation: false
promotion under zero shadow gain in `no_benefit` and `late_benefit`, each for promotion-only
and promotion-plus-rollback; and false rollback under all five non-harmful deployment controls
for promotion-plus-rollback. Use exact one-sided Clopper-Pearson intervals with Bonferroni
correction over nine cells. Keep this replication separate from the earlier 2,000-stream
confirmation; do not pool or replace that result. Passing requires every simultaneous upper
limit to be at most 2.5%. A failure remains a calibration limitation; do not retune on these
streams.

```powershell
.\.venv\Scripts\python.exe -m shiftlab.dive.intervention_calibration_replication `
  --device cuda --seeds 10000 --horizon 800 `
  --output-dir outputs/intervention_calibration_replication
```

GPU generates potential costs and query uniforms. No visual is specified. The policy, gate
thresholds, scenarios, and calibration family are frozen before sampling.
