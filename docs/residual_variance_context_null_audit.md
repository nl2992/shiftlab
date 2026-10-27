# Post-run audit: residual-variance context stratification

The frozen [development protocol](residual_variance_context_grid_protocol.md) split each monitor event into a near-boundary context (`abs(x1 - 0.9*x2) <= 0.3`) or its complement. The [60-seed alternative screen](../outputs/residual_variance_context_grid_60/results.md) showed high subgroup-monitor detection, but this does not establish population-average harm monitoring.

## Assumption failure in the registered null controls

The stratified e-process tests the intersection null that each context's expected paired cost minus the 0.10 margin is nonpositive. That premise is stronger than the registered population-average null and does not hold in the existing stationary or benign-nuisance controls. An evaluator audit on eight fresh seeds per control (`n=1600`, seeds 31,998,000–31,998,007) found mean boundary-context expected margin excess `+0.342` for each control (per-seed range `+0.245` to `+0.448`); the non-boundary context mean was `−0.100` in every stream. The nuisance shift leaves the first two signal coordinates and therefore this context-risk decomposition unchanged.

These 16 streams are a prerequisite diagnostic, not a calibration study or a formal population-parameter estimate. They are sufficient to show that this generator's evaluator-defined subgroup null is false in the nominal population-null controls. Consequently, the naive context-stratified alarm rates in the alternative screen cannot be interpreted as power under calibrated error control. The striking 91.7%–96.7% detection rates mostly reflect known baseline harm concentrated near the decision boundary, not a sequentially certified increase from baseline.

## Decision and next design

Do not calibrate or promote the naive subgroup procedure against the population-null controls. Keep its code as a valid implementation only for settings where the user explicitly wants the intersection of fixed subgroup nulls and those nulls are scientifically appropriate.

The next candidate should test *increase over an independently estimated context-specific baseline*. Use a disjoint pre-monitor calibration block to form simultaneous one-sided upper confidence bounds for each context's baseline paired cost; subtract those predictable bounds from monitor-period PPI estimates; split total type-I error between baseline estimation and sequential monitoring; and use a deterministic support bound for the centered PPI increments. State the required exchangeability / conditional-mean assumptions explicitly. Develop this as a separate, fresh-seed experiment. It would test context-specific deterioration from baseline, not the original population-average null, and it remains a standard confidence-bound plus e-process construction until literature review says otherwise.
