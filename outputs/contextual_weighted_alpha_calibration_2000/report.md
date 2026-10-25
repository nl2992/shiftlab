# Volume-weighted context-alpha independent calibration

Status: **passed**; 2000 streams per cell; seed root 103102024; device cuda.

The simultaneous family has 54 cells across nine prevalence/noise profiles, three endpoints, and two alpha allocations. Each one-sided exact Clopper-Pearson upper bound uses alpha 0.05/54=0.000926. False rollback is evaluated among streams where at least one context was promoted; events count any rollback among those promoted contexts.

|   prevalence |   proxy_error | calibration_type   | method                | endpoint                   |   events |   trials |   simultaneous_alpha |   upper_exact_bound | cell_pass   | all_caps_respected   |
|-------------:|--------------:|:-------------------|:----------------------|:---------------------------|---------:|---------:|---------------------:|--------------------:|:------------|:---------------------|
|      0.05000 |       0.00000 | promotion_null     | equal_alpha           | familywise_false_promotion |        8 |     2000 |              0.00093 |             0.01060 | True        | True                 |
|      0.05000 |       0.00000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |       15 |     2000 |              0.00093 |             0.01563 | True        | True                 |
|      0.05000 |       0.00000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |        8 |     2000 |              0.00093 |             0.01060 | True        | True                 |
|      0.05000 |       0.00000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       21 |     2000 |              0.00093 |             0.01967 | True        | True                 |
|      0.05000 |       0.00000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        1 |     2000 |              0.00093 |             0.00465 | True        | True                 |
|      0.05000 |       0.00000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        1 |     2000 |              0.00093 |             0.00465 | True        | True                 |
|      0.05000 |       0.05000 | promotion_null     | equal_alpha           | familywise_false_promotion |        8 |     2000 |              0.00093 |             0.01060 | True        | True                 |
|      0.05000 |       0.05000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |       13 |     2000 |              0.00093 |             0.01424 | True        | True                 |
|      0.05000 |       0.05000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |       11 |     2000 |              0.00093 |             0.01281 | True        | True                 |
|      0.05000 |       0.05000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       19 |     2000 |              0.00093 |             0.01834 | True        | True                 |
|      0.05000 |       0.05000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.05000 |       0.05000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        1 |     2000 |              0.00093 |             0.00465 | True        | True                 |
|      0.05000 |       0.10000 | promotion_null     | equal_alpha           | familywise_false_promotion |        3 |     2000 |              0.00093 |             0.00656 | True        | True                 |
|      0.05000 |       0.10000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |        7 |     2000 |              0.00093 |             0.00984 | True        | True                 |
|      0.05000 |       0.10000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |        5 |     2000 |              0.00093 |             0.00826 | True        | True                 |
|      0.05000 |       0.10000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.05000 |       0.10000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.05000 |       0.10000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.25000 |       0.00000 | promotion_null     | equal_alpha           | familywise_false_promotion |        9 |     2000 |              0.00093 |             0.01135 | True        | True                 |
|      0.25000 |       0.00000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |       12 |     2000 |              0.00093 |             0.01353 | True        | True                 |
|      0.25000 |       0.00000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.25000 |       0.00000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       11 |     2000 |              0.00093 |             0.01281 | True        | True                 |
|      0.25000 |       0.00000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.25000 |       0.00000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        2 |     2000 |              0.00093 |             0.00565 | True        | True                 |
|      0.25000 |       0.05000 | promotion_null     | equal_alpha           | familywise_false_promotion |        7 |     2000 |              0.00093 |             0.00984 | True        | True                 |
|      0.25000 |       0.05000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |        9 |     2000 |              0.00093 |             0.01135 | True        | True                 |
|      0.25000 |       0.05000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |       15 |     2000 |              0.00093 |             0.01563 | True        | True                 |
|      0.25000 |       0.05000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       16 |     2000 |              0.00093 |             0.01632 | True        | True                 |
|      0.25000 |       0.05000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.25000 |       0.05000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.25000 |       0.10000 | promotion_null     | equal_alpha           | familywise_false_promotion |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.25000 |       0.10000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |       12 |     2000 |              0.00093 |             0.01353 | True        | True                 |
|      0.25000 |       0.10000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.25000 |       0.10000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       11 |     2000 |              0.00093 |             0.01281 | True        | True                 |
|      0.25000 |       0.10000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.25000 |       0.10000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.50000 |       0.00000 | promotion_null     | equal_alpha           | familywise_false_promotion |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.50000 |       0.00000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.50000 |       0.00000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.50000 |       0.00000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       10 |     2000 |              0.00093 |             0.01209 | True        | True                 |
|      0.50000 |       0.00000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.50000 |       0.00000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.50000 |       0.05000 | promotion_null     | equal_alpha           | familywise_false_promotion |       12 |     2000 |              0.00093 |             0.01353 | True        | True                 |
|      0.50000 |       0.05000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |       12 |     2000 |              0.00093 |             0.01353 | True        | True                 |
|      0.50000 |       0.05000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |       15 |     2000 |              0.00093 |             0.01563 | True        | True                 |
|      0.50000 |       0.05000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |       15 |     2000 |              0.00093 |             0.01563 | True        | True                 |
|      0.50000 |       0.05000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.50000 |       0.05000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        0 |     2000 |              0.00093 |             0.00349 | True        | True                 |
|      0.50000 |       0.10000 | promotion_null     | equal_alpha           | familywise_false_promotion |        3 |     2000 |              0.00093 |             0.00656 | True        | True                 |
|      0.50000 |       0.10000 | promotion_null     | volume_weighted_alpha | familywise_false_promotion |        3 |     2000 |              0.00093 |             0.00656 | True        | True                 |
|      0.50000 |       0.10000 | rollback_boundary  | equal_alpha           | familywise_false_rollback  |        9 |     2000 |              0.00093 |             0.01135 | True        | True                 |
|      0.50000 |       0.10000 | rollback_boundary  | volume_weighted_alpha | familywise_false_rollback  |        9 |     2000 |              0.00093 |             0.01135 | True        | True                 |
|      0.50000 |       0.10000 | persistent_benefit | equal_alpha           | familywise_false_rollback  |        1 |     2000 |              0.00093 |             0.00465 | True        | True                 |
|      0.50000 |       0.10000 | persistent_benefit | volume_weighted_alpha | familywise_false_rollback  |        1 |     2000 |              0.00093 |             0.00465 | True        | True                 |

The promotion null has zero paired-gain mean in both contexts. The rollback-boundary profile has shadow mean +2 and deployment mean exactly `-rollback_cost/n_j` in each context with `n_j` events per phase. The persistent-benefit profile has deployment mean +0.40 in both groups. Every profile has nonzero outcome variance.

This simulation checks implementation and finite-sample behavior; it does not replace the conditional-supermartingale proof or extend validity beyond the assumptions in the protocol.
