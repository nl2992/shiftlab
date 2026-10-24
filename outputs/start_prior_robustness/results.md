# Fixed-prior delay and horizon robustness screen

Exploratory screen; no method is selected from these data. Fixed-prior mixtures remain convex combinations of valid component e-processes under the same assumptions.

- Alternative cells: 216; streams per cell: 200; seed block: [20278000, 20278199].
- Null cells: 72; streams per cell: 500; seed block: [20280000, 20280499].
- CUDA generation resolved to: cuda.
- Paired test family: exact two-sided McNemar, Holm-adjusted across every nonuniform method and alternative cell.
- Null interval family: one-sided exact Clopper-Pearson, simultaneous 95% Bonferroni coverage over all method/null cells.

## Detection by delay and planned horizon

| method              | delay_law    |   horizon_multiplier |   macro_cell_detection |   worst_cell_detection |   pre_onset_escalations |
|:--------------------|:-------------|---------------------:|-----------------------:|-----------------------:|------------------------:|
| center_beta_2_2     | fixed_0      |               0.5000 |                 0.5017 |                 0.0000 |                      22 |
| center_beta_2_2     | fixed_0      |               1.0000 |                 0.6733 |                 0.0050 |                       8 |
| center_beta_2_2     | fixed_0      |               1.5000 |                 0.6606 |                 0.0100 |                       0 |
| center_beta_2_2     | fixed_12     |               0.5000 |                 0.5017 |                 0.0000 |                      22 |
| center_beta_2_2     | fixed_12     |               1.0000 |                 0.6733 |                 0.0050 |                       8 |
| center_beta_2_2     | fixed_12     |               1.5000 |                 0.6606 |                 0.0100 |                       0 |
| center_beta_2_2     | uniform_0_12 |               0.5000 |                 0.5017 |                 0.0000 |                      22 |
| center_beta_2_2     | uniform_0_12 |               1.0000 |                 0.6733 |                 0.0050 |                       8 |
| center_beta_2_2     | uniform_0_12 |               1.5000 |                 0.6606 |                 0.0100 |                       0 |
| center_beta_2_2     | uniform_0_6  |               0.5000 |                 0.5017 |                 0.0000 |                      22 |
| center_beta_2_2     | uniform_0_6  |               1.0000 |                 0.6733 |                 0.0050 |                       8 |
| center_beta_2_2     | uniform_0_6  |               1.5000 |                 0.6606 |                 0.0100 |                       0 |
| early_beta_1_2      | fixed_0      |               0.5000 |                 0.4778 |                 0.0000 |                      30 |
| early_beta_1_2      | fixed_0      |               1.0000 |                 0.6386 |                 0.0100 |                      12 |
| early_beta_1_2      | fixed_0      |               1.5000 |                 0.6458 |                 0.0050 |                      10 |
| early_beta_1_2      | fixed_12     |               0.5000 |                 0.4778 |                 0.0000 |                      30 |
| early_beta_1_2      | fixed_12     |               1.0000 |                 0.6386 |                 0.0100 |                      12 |
| early_beta_1_2      | fixed_12     |               1.5000 |                 0.6458 |                 0.0050 |                      10 |
| early_beta_1_2      | uniform_0_12 |               0.5000 |                 0.4778 |                 0.0000 |                      30 |
| early_beta_1_2      | uniform_0_12 |               1.0000 |                 0.6386 |                 0.0100 |                      12 |
| early_beta_1_2      | uniform_0_12 |               1.5000 |                 0.6458 |                 0.0050 |                      10 |
| early_beta_1_2      | uniform_0_6  |               0.5000 |                 0.4778 |                 0.0000 |                      30 |
| early_beta_1_2      | uniform_0_6  |               1.0000 |                 0.6386 |                 0.0100 |                      12 |
| early_beta_1_2      | uniform_0_6  |               1.5000 |                 0.6458 |                 0.0050 |                      10 |
| edge_beta_half_half | fixed_0      |               0.5000 |                 0.5161 |                 0.0000 |                      20 |
| edge_beta_half_half | fixed_0      |               1.0000 |                 0.6681 |                 0.0250 |                       6 |
| edge_beta_half_half | fixed_0      |               1.5000 |                 0.6217 |                 0.0050 |                       6 |
| edge_beta_half_half | fixed_12     |               0.5000 |                 0.5161 |                 0.0000 |                      20 |
| edge_beta_half_half | fixed_12     |               1.0000 |                 0.6681 |                 0.0250 |                       6 |
| edge_beta_half_half | fixed_12     |               1.5000 |                 0.6217 |                 0.0050 |                       6 |
| edge_beta_half_half | uniform_0_12 |               0.5000 |                 0.5161 |                 0.0000 |                      20 |
| edge_beta_half_half | uniform_0_12 |               1.0000 |                 0.6681 |                 0.0250 |                       6 |
| edge_beta_half_half | uniform_0_12 |               1.5000 |                 0.6217 |                 0.0050 |                       6 |
| edge_beta_half_half | uniform_0_6  |               0.5000 |                 0.5161 |                 0.0000 |                      20 |
| edge_beta_half_half | uniform_0_6  |               1.0000 |                 0.6681 |                 0.0250 |                       6 |
| edge_beta_half_half | uniform_0_6  |               1.5000 |                 0.6217 |                 0.0050 |                       6 |
| full_stream_betting | fixed_0      |               0.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | fixed_0      |               1.0000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | fixed_0      |               1.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | fixed_12     |               0.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | fixed_12     |               1.0000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | fixed_12     |               1.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | uniform_0_12 |               0.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | uniform_0_12 |               1.0000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | uniform_0_12 |               1.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | uniform_0_6  |               0.5000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | uniform_0_6  |               1.0000 |                 0.4072 |                 0.0000 |                      66 |
| full_stream_betting | uniform_0_6  |               1.5000 |                 0.4072 |                 0.0000 |                      66 |
| late_beta_2_1       | fixed_0      |               0.5000 |                 0.5272 |                 0.0000 |                      18 |
| late_beta_2_1       | fixed_0      |               1.0000 |                 0.6956 |                 0.0350 |                       6 |
| late_beta_2_1       | fixed_0      |               1.5000 |                 0.6347 |                 0.0100 |                       0 |
| late_beta_2_1       | fixed_12     |               0.5000 |                 0.5272 |                 0.0000 |                      18 |
| late_beta_2_1       | fixed_12     |               1.0000 |                 0.6956 |                 0.0350 |                       6 |
| late_beta_2_1       | fixed_12     |               1.5000 |                 0.6347 |                 0.0100 |                       0 |
| late_beta_2_1       | uniform_0_12 |               0.5000 |                 0.5272 |                 0.0000 |                      18 |
| late_beta_2_1       | uniform_0_12 |               1.0000 |                 0.6956 |                 0.0350 |                       6 |
| late_beta_2_1       | uniform_0_12 |               1.5000 |                 0.6347 |                 0.0100 |                       0 |
| late_beta_2_1       | uniform_0_6  |               0.5000 |                 0.5272 |                 0.0000 |                      18 |
| late_beta_2_1       | uniform_0_6  |               1.0000 |                 0.6956 |                 0.0350 |                       6 |
| late_beta_2_1       | uniform_0_6  |               1.5000 |                 0.6347 |                 0.0100 |                       0 |
| uniform_beta_1_1    | fixed_0      |               0.5000 |                 0.5092 |                 0.0000 |                      22 |
| uniform_beta_1_1    | fixed_0      |               1.0000 |                 0.6742 |                 0.0200 |                       6 |
| uniform_beta_1_1    | fixed_0      |               1.5000 |                 0.6444 |                 0.0050 |                       0 |
| uniform_beta_1_1    | fixed_12     |               0.5000 |                 0.5092 |                 0.0000 |                      22 |
| uniform_beta_1_1    | fixed_12     |               1.0000 |                 0.6742 |                 0.0200 |                       6 |
| uniform_beta_1_1    | fixed_12     |               1.5000 |                 0.6444 |                 0.0050 |                       0 |
| uniform_beta_1_1    | uniform_0_12 |               0.5000 |                 0.5092 |                 0.0000 |                      22 |
| uniform_beta_1_1    | uniform_0_12 |               1.0000 |                 0.6742 |                 0.0200 |                       6 |
| uniform_beta_1_1    | uniform_0_12 |               1.5000 |                 0.6444 |                 0.0050 |                       0 |
| uniform_beta_1_1    | uniform_0_6  |               0.5000 |                 0.5092 |                 0.0000 |                      22 |
| uniform_beta_1_1    | uniform_0_6  |               1.0000 |                 0.6742 |                 0.0200 |                       6 |
| uniform_beta_1_1    | uniform_0_6  |               1.5000 |                 0.6444 |                 0.0050 |                       0 |

## Null calibration screen

| scenario              |   query_rate |   horizon_multiplier | delay_law    | method              |   false_escalations |   streams |   false_escalation_rate |   simultaneous_cp95_upper |
|:----------------------|-------------:|---------------------:|:-------------|:--------------------|--------------------:|----------:|------------------------:|--------------------------:|
| benign_variance_shift |      0.10000 |              0.50000 | fixed_0      | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_0      | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_0      | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_0      | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_0      | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_0      | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_12     | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_12     | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_12     | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_12     | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_12     | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | fixed_12     | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_12 | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_12 | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_12 | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_12 | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_12 | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_12 | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_6  | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_6  | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_6  | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_6  | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_6  | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              0.50000 | uniform_0_6  | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_0      | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_0      | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_0      | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_0      | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_0      | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_0      | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_12     | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_12     | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_12     | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_12     | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_12     | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | fixed_12     | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_12 | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_12 | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_12 | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_12 | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_12 | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_12 | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_6  | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_6  | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_6  | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_6  | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_6  | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.00000 | uniform_0_6  | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_0      | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_0      | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_0      | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_0      | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_0      | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_0      | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_12     | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_12     | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_12     | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_12     | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_12     | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | fixed_12     | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_12 | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_12 | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_12 | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_12 | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_12 | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_12 | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_6  | center_beta_2_2     |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_6  | early_beta_1_2      |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_6  | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_6  | full_stream_betting |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_6  | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.10000 |              1.50000 | uniform_0_6  | uniform_beta_1_1    |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_0      | center_beta_2_2     |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_0      | early_beta_1_2      |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_0      | edge_beta_half_half |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_0      | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_0      | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_0      | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_12     | center_beta_2_2     |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_12     | early_beta_1_2      |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_12     | edge_beta_half_half |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_12     | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_12     | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              0.50000 | fixed_12     | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_12 | center_beta_2_2     |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_12 | early_beta_1_2      |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_12 | edge_beta_half_half |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_12 | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_12 | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_12 | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_6  | center_beta_2_2     |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_6  | early_beta_1_2      |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_6  | edge_beta_half_half |                   5 |       500 |                 0.01000 |                   0.03820 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_6  | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_6  | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              0.50000 | uniform_0_6  | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_0      | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_0      | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_0      | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_0      | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_0      | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_12     | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_12     | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_12     | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_12     | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_12     | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_12 | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_12 | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_12 | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_12 | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_12 | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_6  | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_6  | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_6  | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_6  | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_6  | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.00000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_0      | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_0      | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_0      | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_0      | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_0      | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_12     | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_12     | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_12     | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_12     | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_12     | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_12 | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_12 | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_12 | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_12 | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_12 | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_6  | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_6  | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_6  | edge_beta_half_half |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_6  | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_6  | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.25000 |              1.50000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_0      | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_0      | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_0      | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_0      | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_0      | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_0      | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_12     | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_12     | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_12     | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_12     | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_12     | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              0.50000 | fixed_12     | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_12 | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_12 | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_12 | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_12 | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_12 | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_12 | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_6  | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_6  | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_6  | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_6  | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_6  | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              0.50000 | uniform_0_6  | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_0      | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_0      | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_0      | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_0      | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_0      | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_0      | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_12     | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_12     | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_12     | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_12     | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_12     | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.00000 | fixed_12     | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_12 | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_12 | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_12 | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_12 | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_12 | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_12 | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_6  | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_6  | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_6  | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_6  | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_6  | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.00000 | uniform_0_6  | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_0      | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_0      | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_0      | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_0      | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_0      | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_12     | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_12     | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_12     | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_12     | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_12     | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.50000 |              1.50000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_12 | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_12 | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_12 | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_12 | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_12 | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_6  | center_beta_2_2     |                   1 |       500 |                 0.00200 |                   0.02295 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_6  | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_6  | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_6  | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_6  | late_beta_2_1       |                   0 |       500 |                 0.00000 |                   0.01796 |
| benign_variance_shift |      0.50000 |              1.50000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              0.50000 | fixed_0      | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_0      | early_beta_1_2      |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_0      | edge_beta_half_half |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_0      | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              0.50000 | fixed_0      | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.10000 |              0.50000 | fixed_0      | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_12     | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_12     | early_beta_1_2      |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_12     | edge_beta_half_half |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | fixed_12     | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              0.50000 | fixed_12     | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.10000 |              0.50000 | fixed_12     | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_12 | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_12 | early_beta_1_2      |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_12 | edge_beta_half_half |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_12 | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              0.50000 | uniform_0_12 | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.10000 |              0.50000 | uniform_0_12 | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_6  | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_6  | early_beta_1_2      |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_6  | edge_beta_half_half |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              0.50000 | uniform_0_6  | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              0.50000 | uniform_0_6  | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.10000 |              0.50000 | uniform_0_6  | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              1.00000 | fixed_0      | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              1.00000 | fixed_0      | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | fixed_0      | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | fixed_0      | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.00000 | fixed_0      | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.10000 |              1.00000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | fixed_12     | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              1.00000 | fixed_12     | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | fixed_12     | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | fixed_12     | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.00000 | fixed_12     | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.10000 |              1.00000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | uniform_0_12 | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              1.00000 | uniform_0_12 | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | uniform_0_12 | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | uniform_0_12 | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.00000 | uniform_0_12 | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.10000 |              1.00000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | uniform_0_6  | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.10000 |              1.00000 | uniform_0_6  | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | uniform_0_6  | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.00000 | uniform_0_6  | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.00000 | uniform_0_6  | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.10000 |              1.00000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_0      | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_0      | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_0      | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| stationary            |      0.10000 |              1.50000 | fixed_0      | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.50000 | fixed_0      | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_12     | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_12     | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_12     | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| stationary            |      0.10000 |              1.50000 | fixed_12     | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.50000 | fixed_12     | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_12 | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_12 | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_12 | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| stationary            |      0.10000 |              1.50000 | uniform_0_12 | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.50000 | uniform_0_12 | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_6  | center_beta_2_2     |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_6  | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_6  | edge_beta_half_half |                   0 |       500 |                 0.00000 |                   0.01796 |
| stationary            |      0.10000 |              1.50000 | uniform_0_6  | full_stream_betting |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.10000 |              1.50000 | uniform_0_6  | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.10000 |              1.50000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              0.50000 | fixed_0      | center_beta_2_2     |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | fixed_0      | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              0.50000 | fixed_0      | edge_beta_half_half |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | fixed_0      | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | fixed_0      | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | fixed_0      | uniform_beta_1_1    |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | fixed_12     | center_beta_2_2     |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | fixed_12     | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              0.50000 | fixed_12     | edge_beta_half_half |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | fixed_12     | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | fixed_12     | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | fixed_12     | uniform_beta_1_1    |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | uniform_0_12 | center_beta_2_2     |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | uniform_0_12 | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              0.50000 | uniform_0_12 | edge_beta_half_half |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | uniform_0_12 | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | uniform_0_12 | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | uniform_0_12 | uniform_beta_1_1    |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | uniform_0_6  | center_beta_2_2     |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | uniform_0_6  | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              0.50000 | uniform_0_6  | edge_beta_half_half |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | uniform_0_6  | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              0.50000 | uniform_0_6  | late_beta_2_1       |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              0.50000 | uniform_0_6  | uniform_beta_1_1    |                   5 |       500 |                 0.01000 |                   0.03820 |
| stationary            |      0.25000 |              1.00000 | fixed_0      | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | fixed_0      | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              1.00000 | fixed_0      | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.00000 | fixed_0      | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.00000 | fixed_0      | late_beta_2_1       |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.00000 | fixed_12     | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | fixed_12     | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              1.00000 | fixed_12     | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.00000 | fixed_12     | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.00000 | fixed_12     | late_beta_2_1       |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.00000 | uniform_0_12 | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | uniform_0_12 | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              1.00000 | uniform_0_12 | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.00000 | uniform_0_12 | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.00000 | uniform_0_12 | late_beta_2_1       |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.00000 | uniform_0_6  | center_beta_2_2     |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | uniform_0_6  | early_beta_1_2      |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.25000 |              1.00000 | uniform_0_6  | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.00000 | uniform_0_6  | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.00000 | uniform_0_6  | late_beta_2_1       |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.25000 |              1.00000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | fixed_0      | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | fixed_0      | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | fixed_0      | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | fixed_0      | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.50000 | fixed_0      | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | fixed_0      | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | fixed_12     | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | fixed_12     | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | fixed_12     | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | fixed_12     | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.50000 | fixed_12     | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | fixed_12     | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | uniform_0_12 | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | uniform_0_12 | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | uniform_0_12 | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | uniform_0_12 | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.50000 | uniform_0_12 | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | uniform_0_12 | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | uniform_0_6  | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | uniform_0_6  | early_beta_1_2      |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | uniform_0_6  | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.25000 |              1.50000 | uniform_0_6  | full_stream_betting |                   7 |       500 |                 0.01400 |                   0.04480 |
| stationary            |      0.25000 |              1.50000 | uniform_0_6  | late_beta_2_1       |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.25000 |              1.50000 | uniform_0_6  | uniform_beta_1_1    |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              0.50000 | fixed_0      | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_0      | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_0      | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_0      | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_0      | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              0.50000 | fixed_0      | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.50000 |              0.50000 | fixed_12     | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_12     | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_12     | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_12     | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | fixed_12     | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              0.50000 | fixed_12     | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.50000 |              0.50000 | uniform_0_12 | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_12 | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_12 | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_12 | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_12 | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              0.50000 | uniform_0_12 | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.50000 |              0.50000 | uniform_0_6  | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_6  | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_6  | edge_beta_half_half |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_6  | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              0.50000 | uniform_0_6  | late_beta_2_1       |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              0.50000 | uniform_0_6  | uniform_beta_1_1    |                   4 |       500 |                 0.00800 |                   0.03472 |
| stationary            |      0.50000 |              1.00000 | fixed_0      | center_beta_2_2     |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_0      | early_beta_1_2      |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_0      | edge_beta_half_half |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.50000 |              1.00000 | fixed_0      | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.00000 | fixed_0      | late_beta_2_1       |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_0      | uniform_beta_1_1    |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_12     | center_beta_2_2     |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_12     | early_beta_1_2      |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_12     | edge_beta_half_half |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.50000 |              1.00000 | fixed_12     | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.00000 | fixed_12     | late_beta_2_1       |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | fixed_12     | uniform_beta_1_1    |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_12 | center_beta_2_2     |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_12 | early_beta_1_2      |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_12 | edge_beta_half_half |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.50000 |              1.00000 | uniform_0_12 | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.00000 | uniform_0_12 | late_beta_2_1       |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_12 | uniform_beta_1_1    |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_6  | center_beta_2_2     |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_6  | early_beta_1_2      |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_6  | edge_beta_half_half |                   6 |       500 |                 0.01200 |                   0.04155 |
| stationary            |      0.50000 |              1.00000 | uniform_0_6  | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.00000 | uniform_0_6  | late_beta_2_1       |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.00000 | uniform_0_6  | uniform_beta_1_1    |                   8 |       500 |                 0.01600 |                   0.04797 |
| stationary            |      0.50000 |              1.50000 | fixed_0      | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_0      | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_0      | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              1.50000 | fixed_0      | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_0      | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.50000 |              1.50000 | fixed_0      | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_12     | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_12     | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_12     | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              1.50000 | fixed_12     | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | fixed_12     | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.50000 |              1.50000 | fixed_12     | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_12 | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_12 | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_12 | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              1.50000 | uniform_0_12 | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_12 | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.50000 |              1.50000 | uniform_0_12 | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_6  | center_beta_2_2     |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_6  | early_beta_1_2      |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_6  | edge_beta_half_half |                   2 |       500 |                 0.00400 |                   0.02720 |
| stationary            |      0.50000 |              1.50000 | uniform_0_6  | full_stream_betting |                   3 |       500 |                 0.00600 |                   0.03107 |
| stationary            |      0.50000 |              1.50000 | uniform_0_6  | late_beta_2_1       |                   1 |       500 |                 0.00200 |                   0.02295 |
| stationary            |      0.50000 |              1.50000 | uniform_0_6  | uniform_beta_1_1    |                   3 |       500 |                 0.00600 |                   0.03107 |

Cell-level alternative metrics and paired tests are in the CSV/Parquet files. Nondetections are censored in delay summaries. The study covers only the registered independent synthetic streams; dependent or outcome-informative delays require a different validity argument. This screen is not final confirmation. No figure is produced; use PaperBanana for any later visual.
