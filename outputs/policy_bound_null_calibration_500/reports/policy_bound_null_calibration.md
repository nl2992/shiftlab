# Policy-specific-bound null calibration

This is a frozen synthetic null-calibration study, not a harmful-regime power comparison or a real-world validity guarantee. Independent stream seeds are the calibration units. Each method uses its guaranteed propensity floor in the PPI support bound; the shared-bound option is disabled.

GPU: `NVIDIA GeForce RTX 4060 Laptop GPU`; resolved device: `cuda`. Seeds: 500 per scenario, block `54000000–54000499`. The fixed-mixture primary family contains 10 policy-by-scenario cells; its simultaneous one-sided limits use Bonferroni familywise 95% coverage. The calibration criterion is **PASS**: every primary simultaneous upper limit must be below 0.05.
With 500 streams per primary cell, passing this criterion requires at most 12 false escalations in every cell.

|Scenario|Policy|Monitor|Floor|PPI bound|False escalations / streams|Rate|Wilson 95% interval|Pointwise exact upper|Primary familywise exact upper|Mean labels|Mean spend / cap|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|374.3|710.49 / 720.26|
|benign_nuisance|cost_stabilized_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|374.3|710.49 / 720.26|
|benign_nuisance|cost_stabilized_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|374.3|710.49 / 720.26|
|benign_nuisance|cost_variance_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|370.5|718.74 / 720.26|
|benign_nuisance|cost_variance_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|370.5|718.74 / 720.26|
|benign_nuisance|cost_variance_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|370.5|718.74 / 720.26|
|benign_nuisance|decision_value_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|363.9|718.97 / 720.26|
|benign_nuisance|decision_value_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|363.9|718.97 / 720.26|
|benign_nuisance|decision_value_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|363.9|718.97 / 720.26|
|benign_nuisance|uniform_proxy|fixed_mixture|0.20|45.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|362.4|718.98 / 720.26|
|benign_nuisance|uniform_proxy|predictable_variance|0.20|45.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|362.4|718.98 / 720.26|
|benign_nuisance|uniform_proxy|pm_eb|0.20|45.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|362.4|718.98 / 720.26|
|benign_nuisance|variance_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|363.0|718.90 / 720.26|
|benign_nuisance|variance_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|363.0|718.90 / 720.26|
|benign_nuisance|variance_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|363.0|718.90 / 720.26|
|stationary|cost_stabilized_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|514.7|706.64 / 720.26|
|stationary|cost_stabilized_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|514.7|706.64 / 720.26|
|stationary|cost_stabilized_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|514.7|706.64 / 720.26|
|stationary|cost_variance_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|493.6|708.03 / 720.26|
|stationary|cost_variance_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|493.6|708.03 / 720.26|
|stationary|cost_variance_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|493.6|708.03 / 720.26|
|stationary|decision_value_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|475.4|712.40 / 720.26|
|stationary|decision_value_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|475.4|712.40 / 720.26|
|stationary|decision_value_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|475.4|712.40 / 720.26|
|stationary|uniform_proxy|fixed_mixture|0.20|45.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|470.1|705.31 / 720.26|
|stationary|uniform_proxy|predictable_variance|0.20|45.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|470.1|705.31 / 720.26|
|stationary|uniform_proxy|pm_eb|0.20|45.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|470.1|705.31 / 720.26|
|stationary|variance_proxy|fixed_mixture|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|0.01054|471.9|706.93 / 720.26|
|stationary|variance_proxy|predictable_variance|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|471.9|706.93 / 720.26|
|stationary|variance_proxy|pm_eb|0.10|96.90|0/500|0.00000|[0.00000, 0.00762]|0.00597|—|471.9|706.93 / 720.26|

The fixed-mixture primary familywise bound controls the ten registered method/scenario comparisons under arbitrary dependence between cells. PVA is a secondary existing comparator; PM-EB is exploratory. Their pointwise limits are descriptive and are not used to pass the primary calibration criterion.

Calibration is limited to the registered stationary and benign-nuisance generators, immediate paired feedback, predictable query rules, the stated policy floors, the specified reference policy, and the conditional-mean assumptions. It does not establish validity with delayed, selectively sampled, serially dependent, misspecified, or post-selected feedback. A passing simulator calibration does not prove those assumptions in deployment.

No visual was generated; PaperBanana was not available in the active environment.
