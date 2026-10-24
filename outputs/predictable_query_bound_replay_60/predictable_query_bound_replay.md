# History-predictable propensity-bound replay

## Scope and method

This is a post hoc replay of the existing 60-seed hard-budget run at `outputs\monitor_signal_diagnostic_20_60_v2\metrics\event_traces.parquet`. It changes no query, label, proxy, stopping, or synthetic stream path. The first process uses the run's registered fixed common support bound; the second uses `B_t = M(2/q_t - 1)` on each event, where `q_t` comes only from the prior fixed-bound e-value and remaining budget in the `evidence_curve_a0.05_p0.5` policy. The policy does not use current covariates or current outcomes. Since `q_t` is measurable from prior history, this eventwise scale is predictable under the registered past-conditional marginal null. It is standard predictable-bound betting, not a new e-process or a novelty claim.

The fixed replay reproduces every stored learner log-e value to maximum absolute error `0`. The smallest eventwise bound was `0.274` times the common fixed bound. All event increments were inside their eventwise bounds. The input Parquet checksum matched the source manifest.

## Exploratory results

On boundary-local harm, the observed post-onset detection counts and delays were:

- `evidence_curve_a0.05_p0.5`: 60 onsets reached; post-onset detections 4/60 fixed versus 44/60 predictable-bound; pre-onset crossings 0 versus 0; mean delay among detected streams 2302.2 versus 1876.6 events.
- `uniform_proxy`: 60 onsets reached; post-onset detections 6/60 fixed versus 47/60 predictable-bound; pre-onset crossings 0 versus 0; mean delay among detected streams 2266.2 versus 1964.2 events.

All onsets were reached in this scenario. Across stationary and benign-nuisance controls, crossings were:

| scenario        | method                    |   streams |   fixed_any_crossings |   dynamic_any_crossings |
|:----------------|:--------------------------|----------:|----------------------:|------------------------:|
| benign_nuisance | evidence_curve_a0.05_p0.5 |        60 |                     0 |                       0 |
| benign_nuisance | uniform_proxy             |        60 |                     0 |                       0 |
| stationary      | evidence_curve_a0.05_p0.5 |        60 |                     0 |                       0 |
| stationary      | uniform_proxy             |        60 |                     0 |                       0 |

The predictable-bound replay markedly increases crossings for both querying policies on this harmful path. The evidence-directed policy remains slightly below uniform in detections here, so the result does not show an acquisition advantage. The dynamic bound can change its scale when the learned query policy changes; a monitor that crosses can in turn influence future propensities. This replay follows the original fixed-monitor acquisition path and therefore measures monitor-only sensitivity.

### Stream-level summary

| scenario            | method                    |   streams |   onsets_reached |   fixed_any_crossings |   dynamic_any_crossings |   fixed_early_escalations |   dynamic_early_escalations |   fixed_post_onset_detections |   dynamic_post_onset_detections |   fixed_detection_delay_mean |   dynamic_detection_delay_mean |   mean_events_processed |   mean_propensity |   mean_dynamic_bound |
|:--------------------|:--------------------------|----------:|-----------------:|----------------------:|------------------------:|--------------------------:|----------------------------:|------------------------------:|--------------------------------:|-----------------------------:|-------------------------------:|------------------------:|------------------:|---------------------:|
| benign_nuisance     | evidence_curve_a0.05_p0.5 |        60 |                0 |                     0 |                       0 |                         0 |                           0 |                             0 |                               0 |                      nan     |                        nan     |                2260.883 |             0.156 |               68.882 |
| benign_nuisance     | uniform_proxy             |        60 |                0 |                     0 |                       0 |                         0 |                           0 |                             0 |                               0 |                      nan     |                        nan     |                1823.600 |             0.200 |               45.900 |
| boundary_local_harm | evidence_curve_a0.05_p0.5 |        60 |               60 |                     4 |                      44 |                         0 |                           0 |                             4 |                              44 |                     2302.250 |                       1876.636 |                2349.833 |             0.197 |               50.823 |
| boundary_local_harm | uniform_proxy             |        60 |               60 |                     6 |                      47 |                         0 |                           0 |                             6 |                              47 |                     2266.167 |                       1964.234 |                2356.033 |             0.200 |               45.900 |
| stationary          | evidence_curve_a0.05_p0.5 |        60 |                0 |                     0 |                       0 |                         0 |                           0 |                             0 |                               0 |                      nan     |                        nan     |                2398.617 |             0.158 |               67.831 |
| stationary          | uniform_proxy             |        60 |                0 |                     0 |                       0 |                         0 |                           0 |                             0 |                               0 |                      nan     |                        nan     |                2356.033 |             0.200 |               45.900 |

These reused streams do not independently establish 5% calibration, power, or superiority. The zero crossings in 120 null-control streams are a diagnostic only. A valid next step is a frozen, fresh-seed comparison that evaluates fixed and history-predictable bounds under nondegenerate marginal-null controls and disjoint harms, with the propensity rule defined entirely from past monitor state and spend. The eventwise scaling result from current-context-dependent propensities remains invalid for the marginal null.

No figure was generated for this tabular replay. Any research visual added later must be generated with PaperBanana.

## Reproduction

```powershell
uv run python scripts/analyze_predictable_query_bound_replay.py --input outputs/monitor_signal_diagnostic_20_60_v2 --output outputs/predictable_query_bound_replay_60
```

The output contains per-stream Parquet metrics, a seed-aggregated CSV, this report, and a checksum manifest.
