# WP1 label-clock vs timestamp-clock RMM ablation

Post hoc paired replay on the five timestamped fresh datasets (three policy seeds per episode).
Positive ΔJ means timestamp-clock costs more.

| Dataset | Episodes | Label-clock J | Timestamp-clock J | ΔJ | Label-clock promotes | Timestamp-clock promotes |
|---|---:|---:|---:|---:|---:|---:|
| appliances | 6 | 657.9 | 647.1 | -10.8 | 1.000 | 1.000 |
| beijing_pm25 | 14 | 564.7 | 566.9 | +2.3 | 0.881 | 0.881 |
| bike_hour | 6 | 287.9 | 288.9 | +1.0 | 1.000 | 1.000 |
| household_power | 20 | 539.3 | 542.2 | +3.0 | 0.833 | 0.817 |
| metro | 16 | 151.6 | 153.2 | +1.5 | 1.000 | 1.000 |

Equal-dataset mean ΔJ: **-0.61**; five-cluster bootstrap 95% CI **[-5.85, +2.41]**.

Exploratory post hoc evidence only. Limitations are enumerated in the JSON; this does not cover cached streams or publication-time delays.
