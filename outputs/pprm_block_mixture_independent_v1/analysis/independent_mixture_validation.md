# Independent fixed-mixture validation

This evaluates the development-selected 10% CM-EB / positive-betting mixture on a fresh seed block. The mixture weight, horizon, block size, reliance cap, scenarios, and seed range were fixed before these streams. This tests the selected candidate; it is not an algorithm discovery experiment.

- Streams per scenario: 200
- Seed range: 20373000–20373199
- Configuration manifest: outputs/pprm_block_mixture_independent_v1/block_20/reports/manifest.json
- Primary endpoint: stream-level harm detection. Exact paired McNemar tests compare the fixed mixture with eventwise updating PPI in three harm scenarios, with Holm adjustment.
- Controls: stationary, benign nuisance, and residual variance. False escalations have Wilson intervals.
- The monitor is not a candidate-promotion certificate. Validity remains conditional on the documented boundedness, predictability, and feedback assumptions.

## Primary detection results

| Scenario | Mixture | Eventwise updating PPI | Difference (paired bootstrap 95% CI) | Discordant (mixture only / eventwise only) | Exact p | Holm p |
|---|---:|---:|---:|---:|---:|---:|
| boundary_local_harm | 0.565 | 0.895 | -0.330 [-0.415, -0.250] | 13 / 79 | 1.073e-12 | 2.147e-12 |
| recurring_regimes | 0.595 | 0.860 | -0.265 [-0.345, -0.185] | 13 / 66 | 1.078e-09 | 1.078e-09 |
| harmful_adaptation | 0.580 | 0.970 | -0.390 [-0.460, -0.320] | 2 / 80 | 1.408e-21 | 4.224e-21 |

## Control false escalations

| Scenario | Monitor | Errors / streams | Rate | Wilson 95% interval |
|---|---|---:|---:|---:|
| stationary | fixed_mixture_w0p1 | 0 / 200 | 0.000 | [0.000, 0.019] |
| stationary | cm_eb | 0 / 200 | 0.000 | [0.000, 0.019] |
| stationary | eventwise_updating | 0 / 200 | 0.000 | [0.000, 0.019] |
| stationary | eventwise_frozen | 0 / 200 | 0.000 | [0.000, 0.019] |
| benign_nuisance | fixed_mixture_w0p1 | 0 / 200 | 0.000 | [0.000, 0.019] |
| benign_nuisance | cm_eb | 0 / 200 | 0.000 | [0.000, 0.019] |
| benign_nuisance | eventwise_updating | 0 / 200 | 0.000 | [0.000, 0.019] |
| benign_nuisance | eventwise_frozen | 0 / 200 | 0.000 | [0.000, 0.019] |
| residual_variance | fixed_mixture_w0p1 | 0 / 200 | 0.000 | [0.000, 0.019] |
| residual_variance | cm_eb | 0 / 200 | 0.000 | [0.000, 0.019] |
| residual_variance | eventwise_updating | 0 / 200 | 0.000 | [0.000, 0.019] |
| residual_variance | eventwise_frozen | 0 / 200 | 0.000 | [0.000, 0.019] |

## Interpretation limits

These results assess one fixed candidate and registered synthetic designs. They do not establish error control under arbitrary serial dependence, adaptive label selection, delayed feedback, or real-world shift. Interpret them as evidence for the declared generator and feedback protocol only.
