# Decision-risk proxy stress grid results

Validated **180 cells**, **12,960 rows**, and **12 paired seed streams per cell**. All methods shared query labels, realized spend, and processed events within every stream; all hard caps were respected.
Generation used NVIDIA GeForce RTX 4060 Laptop GPU with requested device `cuda`. The saved Parquet SHA-256 matches the run manifest (`b8dd73b293510f76ad443f0a8ed755a802e0af98f530483c755d49c60ec296c3`).

## Aggregate comparison

| method            |   streams |   material_harm_streams |   false_escalations |   mean_rmse |   mean_labels |   mean_spend |   mean_events_processed |   validation_selected_risk_model |   detection_rate |
|:------------------|----------:|------------------------:|--------------------:|------------:|--------------:|-------------:|------------------------:|---------------------------------:|-----------------:|
| forest            |      2160 |                    1179 |                   0 |      1.2306 |      359.4352 |     539.1915 |               1527.2130 |                           0.6958 |           0.3664 |
| prequential_hedge |      2160 |                    1179 |                   0 |      1.1265 |      359.4352 |     539.1915 |               1527.2130 |                           0.6958 |           0.3723 |
| ridge             |      2160 |                    1179 |                   0 |      1.2267 |      359.4352 |     539.1915 |               1527.2130 |                           0.6958 |           0.3647 |
| risk_model        |      2160 |                    1179 |                   0 |      1.0135 |      359.4352 |     539.1915 |               1527.2130 |                           0.6958 |           0.3673 |
| validation_best   |      2160 |                    1179 |                   0 |      1.0557 |      359.4352 |     539.1915 |               1527.2130 |                           0.6958 |           0.3681 |
| zero              |      2160 |                    1179 |                   0 |      1.2882 |      359.4352 |     539.1915 |               1527.2130 |                           0.6958 |           0.3622 |

## Seed-clustered macro paired differences

The table below averages paired differences over cells within each seed, then bootstraps the 12 seed clusters. Detection favors a positive risk-model difference; RMSE favors a negative difference. These intervals are descriptive and unadjusted.

| Metric | Comparator | Risk model minus comparator | Seed-cluster 95% interval |
|---|---|---:|---:|
| detected | ridge | 0.0021 | [-0.0223, 0.0236] |
| detected | validation_best | -0.0010 | [-0.0056, 0.0025] |
| detected | prequential_hedge | -0.0055 | [-0.0210, 0.0076] |
| estimator_rmse | ridge | -0.2132 | [-0.2296, -0.1966] |
| estimator_rmse | validation_best | -0.0422 | [-0.0597, -0.0256] |
| estimator_rmse | prequential_hedge | -0.1130 | [-0.1235, -0.1021] |
| false_escalation | ridge | 0.0000 | [0.0000, 0.0000] |
| false_escalation | validation_best | 0.0000 | [0.0000, 0.0000] |
| false_escalation | prequential_hedge | 0.0000 | [0.0000, 0.0000] |

## Limits and decision

This screen had no pre-onset false escalations. It includes structural zero-harm cells where the compared policies coincide, but no nondegenerate population-null cells; therefore it gives no false-alarm calibration. Its seed count is useful for screening, not precise cellwise conclusions. Lower RMSE did not translate into a reliable detection gain over ridge, validation-best, or Hedge. Keep the logistic risk model as the strongest estimation proxy in this grid; do not advance it as a novel or confirmatory monitoring method. The next experiment should compare established, variance-sensitive anytime monitors using this proxy under matched query and cost paths, with separate nondegenerate null calibration.

No figure was generated. Use PaperBanana for any future research visual and verify plotted values against the saved metrics.
