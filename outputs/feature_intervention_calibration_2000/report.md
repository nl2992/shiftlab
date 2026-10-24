# Feature-dependent intervention null calibration

Calibration status: **passed** under the frozen simultaneous error rule.

- Fresh seed block starts at 77102024; 2000 streams per cell; device `cuda`.
- `q=0.8`, budget `40%`, horizon `400` per phase, `alpha=0.05` split equally between gates.
- Four one-sided exact Clopper–Pearson bounds use Bonferroni cell alpha `alpha_total/4`.
- All pathwise label caps respected: True.

| scenario           | error_type      |   events |   streams_at_risk |   rate |   simultaneous_one_sided_cp_upper |   cell_alpha |   familywise_alpha |   family_cells | gate_pass   |
|:-------------------|:----------------|---------:|------------------:|-------:|----------------------------------:|-------------:|-------------------:|---------------:|:------------|
| benign_nuisance    | false_promotion |        9 |              2000 | 0.0045 |                        0.00916859 |       0.0125 |               0.05 |              4 | True        |
| persistent_benefit | false_rollback  |        0 |              2000 | 0      |                        0.00218861 |       0.0125 |               0.05 |              4 | True        |
| rollback_boundary  | false_rollback  |       11 |              2000 | 0.0055 |                        0.0105044  |       0.0125 |               0.05 |              4 | True        |
| stationary         | false_promotion |        9 |              2000 | 0.0045 |                        0.00916859 |       0.0125 |               0.05 |              4 | True        |

This establishes only empirical calibration for these registered synthetic controls and the assumptions in `feature_intervention_protocol.md`. It is not evidence about delayed feedback, dependence, adaptive candidates, or real application costs. No figures were generated.
