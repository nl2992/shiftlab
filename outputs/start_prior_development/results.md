# Fixed start-time prior development screen

This development-only screen compares fixed Beta-distributed priors over eight prescribed
start-time bins. Every method receives paired outcomes, queries and delays within each seed.
Candidate priors are fixed before each stream; changing the prior between streams does not
affect the component e-process guarantees. No confirmatory inference is performed here.

- Seed interval: 20262000–20262029.
- Cells: 12; seeds per cell: 30; resolved device: cuda.
- Selection rule: Highest unweighted mean detection rate across the registered alternative cells; ties use higher worst-cell detection. This is development-only selection.
- Selected prior for fresh validation: center_beta_2_2

| method              |   macro_cell_detection |   worst_cell_detection |   best_cell_detection |   mean_pre_onset_escalations |
|:--------------------|-----------------------:|-----------------------:|----------------------:|-----------------------------:|
| center_beta_2_2     |                 0.8444 |                 0.2667 |                1.0000 |                       0.0000 |
| late_beta_2_1       |                 0.8417 |                 0.2667 |                1.0000 |                       0.0000 |
| uniform_beta_1_1    |                 0.8278 |                 0.2667 |                1.0000 |                       0.0000 |
| early_beta_1_2      |                 0.8139 |                 0.2333 |                1.0000 |                       0.3333 |
| edge_beta_half_half |                 0.8083 |                 0.2333 |                1.0000 |                       0.3333 |
| full_stream_betting |                 0.6194 |                 0.0667 |                1.0000 |                       0.6667 |

Cell-level power and delay are in cell_summary.csv; per-stream outcomes are in
start_prior_development.parquet and start_prior_development.csv. The selected prior remains
a development candidate until it passes fresh null calibration and a disjoint alternative test.
No figure is included because project guidance requires PaperBanana for visuals and that tool
is unavailable in this session.
