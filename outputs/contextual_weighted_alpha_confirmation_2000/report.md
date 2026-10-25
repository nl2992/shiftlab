# Volume-weighted context-alpha independent confirmation

Status: **passed**; 2000 seeds per prevalence/noise profile; seed root 113102024; device cuda.

The primary estimand is the equally weighted mean realized-utility difference between volume-weighted and equal alpha across the nine registered prevalence/noise profiles and all twelve intervention-cost/label-cap settings. The utility margin was fixed at +1.0 per 800-event stream, equal to one false-positive cost unit in the simulator. The paired seed bootstrap resamples streams within each fixed profile and averages profiles equally.

| estimand                                                                          | method                | reference   |   paired_mean_realized_utility_difference |   bootstrap_ci95_low |   bootstrap_ci95_high |   minimum_practical_gain | primary_gate_passed   |   profile_count |   settings_per_profile |   seed_clusters_per_profile |   bootstrap_replicates |
|:----------------------------------------------------------------------------------|:----------------------|:------------|------------------------------------------:|---------------------:|----------------------:|-------------------------:|:----------------------|----------------:|-----------------------:|----------------------------:|-----------------------:|
| equal-weight average over 9 prevalence/noise profiles and 12 cost/budget settings | volume_weighted_alpha | equal_alpha |                                    1.4844 |               1.3749 |                1.5971 |                   1.0000 | True                  |               9 |                     12 |                        2000 |                   5000 |

## Profile-level means

|   prevalence |   proxy_error |   paired_mean |
|-------------:|--------------:|--------------:|
|       0.0500 |        0.0000 |        0.5500 |
|       0.0500 |        0.0500 |        1.1848 |
|       0.0500 |        0.1000 |        0.6299 |
|       0.2500 |        0.0000 |        5.3619 |
|       0.2500 |        0.0500 |        3.6616 |
|       0.2500 |        0.1000 |        2.3847 |
|       0.5000 |        0.0000 |        0.0006 |
|       0.5000 |        0.0500 |        0.1019 |
|       0.5000 |        0.1000 |       -0.5164 |

All per-context label caps respected: True.

The independent calibration covers stationary promotion nulls, least-favourable per-context rollback boundaries, and persistent-benefit rollback controls for both allocations. This confirmation evaluates only the preselected heterogeneous-reversal utility comparison; the result does not imply cellwise superiority or external validity.
