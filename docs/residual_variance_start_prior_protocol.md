# Residual-variance start-prior comparison: protocol

## Question and candidate

The preceding severity-by-query-rate screen found very low detection in the residual-variance condition, including with complete labels. The expected loss gap starts after the midpoint of the generated stream and is modest relative to paired-outcome variance. This diagnostic asks whether a fixed late-start mixture, previously calibrated and independently confirmed on other scenarios, improves evidence accumulation when the harmful period begins late.

Compare three tests on exactly matched synthetic streams and prediction-powered increments:

- `fixed_mixture`: the current five-stake, full-stream bounded-mean e-process.
- `uniform_start_mixture`: eight fixed start-time components mixed using equal-width Beta(1,1) prior masses.
- `late_start_mixture`: the same eight starts mixed using Beta(2,1) prior masses.

For each component start (s_j), its e-process stays at one before (s_j) and then uses the existing valid bounded-mean process. A convex mixture with weights fixed before test outcomes is itself an e-process under the same conditional-mean null and support assumptions. The start locations are determined by the configured planned horizon before outcomes. No online reweighting or outcome-driven start selection is used. This is a comparison of established constructions, not a new validity result or novelty claim.

## Locked design

- Scenario: residual-variance (`target_variance`) generator at severities 1.5, 3.0, and 4.5.
- Label-query rates: 0.20, 0.40, 0.80, and 1.00; 1.00 is a full-label reference.
- Independent paired seeds: 60 per severity/rate cell, seed range 31,202,026–31,202,085.
- Stream: 2,400 events, 16 features; 8 start points over the planned 1,600-event monitor horizon (monitor begins at event 800).
- Alpha 0.05, decision-harm margin 0.10, registered 5:1 false-negative/false-positive costs, same bounded PPI support, same stream/proxy/query path/cost budget for all monitors.
- CUDA requested; deterministic CPU path remains available.
- Primary descriptive contrast: paired detection-rate difference for each start mixture minus fixed mixture within severity/rate cell; bootstrap resamples independent seeds.
- Report detections, false escalations, event-time delay, harm reachability, labels, realized dollars, and processed events. Alternative-only results do not calibrate null behavior.

Run from the repository root:

```powershell
uv run python -m shiftlab.dive.residual_variance_start_prior --device cuda --seeds 60
```

Outputs are written to `outputs/residual_variance_start_prior/`; the manifest records the exact configuration, source hashes, resolved compute environment, and metrics checksum. No figure is generated for this tabular diagnostic. If a visual is later needed, use PaperBanana.

Reproduce the seed-cluster pooled comparisons and path/budget audit from the saved Parquet with:

```powershell
uv run python -m shiftlab.dive.analyze_residual_variance_start_prior
```

The analysis manifest records the bootstrap seed, input checksum, and analysis-code hash. Its intervals are descriptive and unadjusted for multiplicity.

## Interpretation limits

The prior weights were selected and calibrated in independent earlier work; this targeted grid checks transfer to one different synthetic mechanism. It is not an independent null calibration for this report, an all-purpose comparison of start priors, or evidence for general superiority. A result should not be pooled with previous alternative grids as if they were one preregistered experiment. Do not claim that a start prior changes the null assumptions: the eventwise conditional-mean null, predictable policy/query choices, and bounded increments remain essential.
