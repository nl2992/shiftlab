# Validity support matrix
Columns: mathematical scope of the guarantee, and what was measured (repaired engine, 2000 paths per cell).

| null class | guarantee scope (Ville on the repaired test supermartingale) | measured |
|---|---|---|
| iid, bounded loss, fixed or outcome-independent delay, predictable bets | **proved** (marginal null, bets and caps from the past only) | all iid cells <= 0.047 |
| outcome-dependent delay | **proved only with in-order release** | no inflation either way at these settings |
| heterogeneous risk, unchanged marginal | proved for the repaired cap; **false for the earlier cap** (exact counterexample) | repaired <= 0.032 forced-bet; legacy 0.064 forced-bet |
| hard budget with inactive events | proved (inclusion probability positive or event inactive) | `hardbudget` table below, <= 0.03 |
| very low label rate | proved (same argument); information-limited power | below |
| autocorrelated / clustered / GARCH outcomes | **not covered** (conditional null fails) | **fails**: see `DEPENDENCE_STRESS_RESULTS.md` |
| proxy bias, anti-informative proxy | proved (IPW correction proxy-free) | <= 0.03 |

| null/world | HG FA | pprm FA | cost FA | verdict |
|---|---|---|---|---|
| G3|K2_null | 0.018 | 0.016 | 0.019 | empirically valid |
| G4|fin_null | 0.089 | 0.130 | 0.030 | EMPIRICAL_FAIL |
| X01|null|delay=fixed | 0.011 | 0.012 | 0.014 | empirically valid |
| X01|null|delay=geometric | 0.013 | 0.018 | 0.011 | empirically valid |
| X01|null|delay=uniform | 0.015 | 0.013 | 0.008 | empirically valid |
| X02|null|delay=burst | 0.011 | 0.015 | 0.012 | empirically valid |
| X02|null|delay=heavy | 0.004 | 0.007 | 0.007 | empirically valid |
| X02|null|delay=outcome | 0.011 | 0.014 | 0.021 | empirically valid |
| X02|null|delay=outcome_rev | 0.008 | 0.011 | 0.009 | empirically valid |
| X03|null|ar0.5_s1.0 | 0.015 | 0.019 | 0.014 | empirically valid |
| X03|null|ar0.98_s1.5 | 0.038 | 0.019 | 0.044 | empirically valid |
| X03|null|ar0.9_s1.0 | 0.016 | 0.013 | 0.018 | empirically valid |
| X04|null|cluster100_s1.5 | 0.088 | 0.052 | 0.055 | EMPIRICAL_FAIL |
| X04|null|cluster20_s1.0 | 0.013 | 0.012 | 0.013 | empirically valid |
| X04|null|cluster400_s1.5 | 0.190 | 0.121 | 0.163 | EMPIRICAL_FAIL |
| X05|null|adaptive_neg | 0.022 | 0.015 | 0.015 | empirically valid |
| X05|null|adaptive_pos | 0.029 | 0.021 | 0.021 | empirically valid |
| X06|null|hetero_calibrated | 0.032 | 0.021 | 0.021 | empirically valid |
| X06|null|hetero_rearranged | 0.022 | 0.018 | 0.018 | empirically valid |
| X07|null|proxy=anti | 0.025 | 0.018 | 0.021 | empirically valid |
| X07|null|proxy=calibration | 0.025 | 0.021 | 0.021 | empirically valid |
| X07|null|proxy=static_bias | 0.025 | 0.025 | 0.023 | empirically valid |
| X08|null|G1 | 0.017 | 0.017 | 0.015 | empirically valid |
| X08|null|G2 | 0.013 | 0.015 | 0.013 | empirically valid |
| X09|cov_benign3 | 0.013 | 0.011 | 0.009 | empirically valid |
| X09|cov_inform2 | 0.006 | 0.007 | 0.011 | empirically valid |
| X09|prior1 | 0.046 | 0.047 | 0.012 | empirically valid |
| X10|concept1.5_transient | 0.005 | 0.011 | 0.012 | empirically valid |
| X10|concept2_transient | 0.005 | 0.007 | 0.011 | empirically valid |
| X10|concept3_transient | 0.006 | 0.010 | 0.009 | empirically valid |
| X11|concept2_recurrent | 0.007 | 0.013 | 0.006 | empirically valid |
| X14|null|cost_fn=5 | 0.015 | 0.015 | 0.015 | empirically valid |
| X14|null|fin_heavy_tail_clip | 0.089 | 0.116 | 0.025 | EMPIRICAL_FAIL |

## X12 very low label availability (frac 0.2%-2%, HG and pprm)
| world | HG|f0.002 | HG|f0.005 | HG|f0.01 | HG|f0.02 | pprm|f0.002 | pprm|f0.005 | pprm|f0.01 | pprm|f0.02 |
|---|---|---|---|---|---|---|---|---|
| X12|concept2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.003 |
| X12|null | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.002 |

Power (concept shift):

| world | HG|f0.002 | HG|f0.005 | HG|f0.01 | HG|f0.02 | pprm|f0.002 | pprm|f0.005 | pprm|f0.01 | pprm|f0.02 |
|---|---|---|---|---|---|---|---|---|
| X12|concept2 | 0.000 | 0.001 | 0.007 | 0.059 | 0.001 | 0.005 | 0.018 | 0.064 |

## X13 hard budget exhaustion
| world | config | max_labels | fa | detected | exhausted |
|---|---|---|---|---|---|
| X13|concept2 | HG|bern_f0.5_B10 | 10 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|bern_f0.5_B100 | 100 | 0.004 | 0.000 | 1.000 |
| X13|concept2 | HG|bern_f0.5_B25 | 25 | 0.002 | 0.000 | 1.000 |
| X13|concept2 | HG|bern_f0.5_B5 | 5 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|const_B10 | 10 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|const_B100 | 100 | 0.001 | 0.341 | 0.509 |
| X13|concept2 | HG|const_B25 | 25 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|const_B5 | 5 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|remaining_B10 | 10 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|remaining_B100 | 100 | 0.000 | 0.362 | 1.000 |
| X13|concept2 | HG|remaining_B25 | 25 | 0.000 | 0.000 | 1.000 |
| X13|concept2 | HG|remaining_B5 | 5 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|bern_f0.5_B10 | 10 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|bern_f0.5_B100 | 100 | 0.006 | 0.000 | 1.000 |
| X13|null | HG|bern_f0.5_B25 | 25 | 0.001 | 0.000 | 1.000 |
| X13|null | HG|bern_f0.5_B5 | 5 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|const_B10 | 10 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|const_B100 | 100 | 0.002 | 0.000 | 0.509 |
| X13|null | HG|const_B25 | 25 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|const_B5 | 5 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|remaining_B10 | 10 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|remaining_B100 | 100 | 0.002 | 0.000 | 1.000 |
| X13|null | HG|remaining_B25 | 25 | 0.000 | 0.000 | 1.000 |
| X13|null | HG|remaining_B5 | 5 | 0.000 | 0.000 | 1.000 |

`max_labels` never exceeds the declared hard cap B in the config name (B in {5, 10, 25, 100}). Exhaustion on most paths for the Bernoulli-at-0.5 arm; size stays below alpha because exhausted events are inactive.
