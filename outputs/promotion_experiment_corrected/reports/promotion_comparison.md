# Shadow candidate promotion experiment

Evaluated 30 paired streams per scenario using `cuda` synthetic generation and full immediate feedback. Candidates were frozen using only the early training slice; evaluation began at the forward-time monitor boundary.

`incumbent_snapshot` is an exact copy of the deployed policy in all scenarios except the deliberately harmful-adaptation scenario. With switching cost 0.05, its pointwise expected net gain is negative in the unchanged-policy scenarios, so those rows provide the null certification check. `recalibrated_candidate` is a cost-threshold logistic model trained on the early slice. Candidate i receives alpha_i=alpha/[i(i+1)].

This evaluates certification behavior, not an integrated intervention controller. The candidate comparison assumes paired potential costs are observable from the same outcome; it is unsuitable when actions change outcomes without a randomized/off-policy design. The recalibrated candidate can see changing regime conditions, so its descriptive false-certification rate is not interpreted as a validity check unless the conditional null holds at every event.

False certifications of the exact-copy candidate under its pointwise null: 0/150 across applicable streams. This finite simulation is a diagnostic, not the guarantee; the guarantee follows only under the documented assumptions.

| Scenario | Candidate | Mean true net gain | Certification rate (95% Wilson) | Median delay | Null applicable |
|---|---|---:|---:|---:|---|
| benign_nuisance | incumbent_snapshot | -0.0500 | 0.000 [0.000,0.114] | — | True |
| benign_nuisance | recalibrated_candidate | -0.0679 | 0.000 [0.000,0.114] | — | False |
| boundary_local_harm | incumbent_snapshot | -0.0500 | 0.000 [0.000,0.114] | — | True |
| boundary_local_harm | recalibrated_candidate | 0.2231 | 1.000 [0.886,1.000] | 1086 | False |
| harmful_adaptation | incumbent_snapshot | 0.1418 | 0.967 [0.833,0.994] | 1485 | False |
| harmful_adaptation | recalibrated_candidate | 0.2006 | 1.000 [0.886,1.000] | 1115 | False |
| recurring_regimes | incumbent_snapshot | -0.0500 | 0.000 [0.000,0.114] | — | True |
| recurring_regimes | recalibrated_candidate | 0.2204 | 1.000 [0.886,1.000] | 176 | False |
| residual_variance | incumbent_snapshot | -0.0500 | 0.000 [0.000,0.114] | — | True |
| residual_variance | recalibrated_candidate | 0.0715 | 0.733 [0.556,0.858] | 1940 | False |
| stationary | incumbent_snapshot | -0.0500 | 0.000 [0.000,0.114] | — | True |
| stationary | recalibrated_candidate | 0.0088 | 0.033 [0.006,0.167] | 1221 | False |