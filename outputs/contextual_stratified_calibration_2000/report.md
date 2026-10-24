# Contextual stratification null calibration

Status: **passed**; 2000 independent streams per scenario; seed root 90102024; device cuda.

The eight prespecified cells cover familywise false promotion under two nulls for both methods, false rollback at each method's own least-favourable boundary, and false rollback under persistent benefit. Rollback rates use promoted streams as the risk set. Each cell receives one-sided Clopper–Pearson alpha 0.05/8; passing requires at least 1,000 at-risk streams and upper bound at most 0.05.

| scenario                     | method                        | event                      | risk_set   |   events |   trials |   simultaneous_one_sided_alpha |   clopper_pearson_upper | cell_pass   |
|:-----------------------------|:------------------------------|:---------------------------|:-----------|---------:|---------:|-------------------------------:|------------------------:|:------------|
| stationary_null              | promotion_rollback            | false_promotion_under_null | all        |       10 |     2000 |                        0.00625 |                 0.01047 | True        |
| stationary_null              | stratified_promotion_rollback | false_promotion_under_null | all        |        3 |     2000 |                        0.00625 |                 0.00533 | True        |
| benign_nuisance              | promotion_rollback            | false_promotion_under_null | all        |       14 |     2000 |                        0.00625 |                 0.01316 | True        |
| benign_nuisance              | stratified_promotion_rollback | false_promotion_under_null | all        |        4 |     2000 |                        0.00625 |                 0.00613 | True        |
| rollback_boundary_global     | promotion_rollback            | false_rollback_under_null  | promoted   |        0 |     2000 |                        0.00625 |                 0.00253 | True        |
| rollback_boundary_stratified | stratified_promotion_rollback | false_rollback_under_null  | promoted   |        1 |     2000 |                        0.00625 |                 0.00358 | True        |
| persistent_benefit           | promotion_rollback            | false_rollback_under_null  | promoted   |        0 |     2000 |                        0.00625 |                 0.00253 | True        |
| persistent_benefit           | stratified_promotion_rollback | false_rollback_under_null  | promoted   |        0 |     2000 |                        0.00625 |                 0.00253 | True        |

This is a finite registered synthetic calibration, not a general theorem beyond the gate's stated bounded-mean assumptions and this data-generating process.
