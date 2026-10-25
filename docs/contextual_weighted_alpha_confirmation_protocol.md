# Volume-weighted context-alpha calibration and confirmation protocol

## Decision made from development

The development grid showed a small, mixed average advantage for volume-weighted alpha over equal alpha in heterogeneous reversal. This protocol selects only the volume-weighted rule for a fresh, direct comparison against equal alpha. Rare-protected alpha is excluded based on its development performance. This selection is now frozen; no alternative allocation will be substituted after seeing confirmation data.

The primary practical margin is **+1.0 utility unit per 800-event stream**, equal to one false-positive cost unit in the simulator. The estimand is the equally weighted average across nine fixed prevalence/proxy-noise profiles and twelve cost/budget settings. This makes the target explicit; it is not claimed to represent a population-weighted deployment distribution.

## Calibration

Calibration uses 2,000 independent streams per cell at seed root `103102024`. The family contains 54 cells: nine prevalence/noise profiles, three endpoints, and two methods (equal and volume-weighted alpha). Each one-sided exact Clopper–Pearson upper limit uses alpha `0.05/54`. Every cell must have at least 1,000 risk-set streams and an upper limit no larger than 0.05; all hard caps must hold.

The endpoints are:

1. **False promotion:** both contexts have mean paired gain zero in shadow and deployment. The paired gains are nondegenerate (`+5` or `-1`) and zero lies in the promotion null.
2. **False rollback at the boundary:** both contexts have shadow mean +2; in deployment, context `j` has mean exactly `-k_r/n_j`, where `k_r=0.05` and `n_j` is that context's events per phase. A false event is any promoted context being rolled back.
3. **Persistent-benefit rollback:** both contexts have shadow mean +2 and deployment mean +0.40. A false event is any rollback among promoted contexts.

The rollback risk set consists of streams in which at least one context was promoted. Outcomes are generated independently across contexts and phases; querying uses fixed `q=0.80`, and each context receives its registered population-proportional label cap under a shared 40% total cap. The context weights are fixed from an independent 500-label, outcome-free pilot before monitoring.

The calibration is an implementation and finite-sample check for these nulls. The mathematical guarantee remains the union of the per-context Ville bounds conditional on fixed pilot weights and the bounded conditional-mean assumptions.

## Independent confirmation

Confirmation uses 2,000 fresh streams for each of the nine heterogeneous-reversal prevalence/noise profiles at seed root `113102024`, after a passed calibration manifest. In each profile, identical potential outcomes, query uniforms, and pilot-derived alpha weights are paired between equal and volume-weighted allocation. The full cost/budget factorial is evaluated: intervention-cost multipliers `{0,1,2,4}` and hard label rates `{0.20,0.40,0.60}`. Promotion and rollback costs each equal `0.05 * multiplier`; the label price remains `0.01` and the query probability is `0.80`.

The primary statistic first averages paired realized net-utility differences across the twelve cost/budget cells within each stream, then averages equally across the nine fixed profiles. A 5,000-replicate paired bootstrap resamples streams within each profile. The sole efficacy gate is that the two-sided 95% bootstrap interval's lower endpoint exceeds **+1.0 utility unit per 800-event stream**, with no hard-cap violation. Failure means the development advantage is not confirmed at the registered practical margin; no per-cell winner will be promoted post hoc.

Profile-level and cell-level point estimates are descriptive secondary results. This design does not claim superiority at every factor combination or external validity to an applied setting.

## Reproduction

```powershell
uv run shiftlab-dive-contextual-weighted-alpha-calibrate --seeds 2000 --seed-offset 103102024 --horizon 400 --device cuda --output-dir outputs/contextual_weighted_alpha_calibration_2000
uv run shiftlab-dive-contextual-weighted-alpha-confirm --calibration-manifest outputs/contextual_weighted_alpha_calibration_2000/manifest.json --seeds 2000 --seed-offset 113102024 --horizon 400 --bootstrap-replicates 5000 --device cuda --output-dir outputs/contextual_weighted_alpha_confirmation_2000
```

Both runners save CSV/Parquet metrics as appropriate, reports, exact commands, source hashes, checksums, seed roots, and compute environment. No figure is prespecified. Any research visual later added must use PaperBanana and be checked against these machine-readable results.
