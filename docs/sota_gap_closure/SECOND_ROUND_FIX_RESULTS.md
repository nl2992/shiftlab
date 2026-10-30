# Second-round fixes on new development worlds (executed; rules in `SECOND_ROUND_FIX_CANDIDATES.md`)
15 new development worlds (6 dependence nulls: AR .8 / .97, cluster 50 / 200, two GARCH settings; iid null; benign shift; 4 iid harm worlds; 3 transient / recurrent), 400 seeds (1000-path precision is not needed for the power rules), seed block 80000, fraction 0.2, delay 5; per-seed data in `outputs/gap_closure/e14_fixes_dev2`.

Verdicts against the preregistered rules:

| fix | preregistered rule | parents meeting | accepted |
|---|---|---|---|
| F1_var_floor.5 | iid power gain >= +0.03 for >= 2 parents | 0 | NO |
| F2_lrv100 | dependence-null max FA <= 0.07 (Wilson hi <= 0.09) for >= 2 parents and iid power loss <= 0.05 | 0 | NO |
| F3_multiwindow | transient power gain >= +0.05 for >= 2 parents and non-harm FA change <= +0.02 | 0 | NO |

Decision table (mean over worlds; deltas vs the matched parent):

| parent | variant | d_power_iid_harm | d_power_transient | d_fa_nonharm | max_fa_dep_parent | max_fa_dep_fix | dep_fix_ci_hi | max_fa_any_nonharm_fix |
|---|---|---|---|---|---|---|---|---|
| pprm | F1_var_floor.5 | -0.000 | 0.030 | -0.012 | 0.225 | 0.215 | 0.258 | 0.215 |
| pprm | F1_var_unfloored | -0.015 | 0.020 | -0.038 | 0.225 | 0.108 | 0.142 | 0.108 |
| pprm | F2_lrv100 | -0.076 | -0.136 | -0.039 | 0.225 | 0.092 | 0.125 | 0.092 |
| pprm | F2_lrv30 | -0.021 | -0.053 | -0.026 | 0.225 | 0.145 | 0.183 | 0.145 |
| pprm | F3_multiwindow | 0.065 | 0.137 | 0.070 | 0.225 | 0.490 | 0.539 | 0.490 |
| HG | F1_var_floor.5 | -0.048 | 0.065 | -0.033 | 0.232 | 0.098 | 0.131 | 0.098 |
| HG | F1_var_unfloored | -0.081 | -0.091 | -0.057 | 0.232 | 0.048 | 0.073 | 0.048 |
| HG | F2_lrv100 | -0.050 | -0.211 | -0.050 | 0.232 | 0.048 | 0.073 | 0.048 |
| HG | F2_lrv30 | -0.028 | -0.063 | -0.034 | 0.232 | 0.115 | 0.150 | 0.115 |
| HG | F3_multiwindow | -0.006 | -0.037 | -0.004 | 0.232 | 0.215 | 0.258 | 0.215 |
| cost | F1_var_floor.5 | -0.033 | 0.040 | -0.022 | 0.200 | 0.135 | 0.172 | 0.135 |
| cost | F1_var_unfloored | -0.175 | -0.009 | -0.044 | 0.200 | 0.040 | 0.064 | 0.040 |
| cost | F2_lrv100 | -0.052 | -0.073 | -0.027 | 0.200 | 0.092 | 0.125 | 0.092 |
| cost | F2_lrv30 | -0.016 | -0.028 | -0.015 | 0.200 | 0.150 | 0.188 | 0.150 |
| cost | F3_multiwindow | -0.023 | -0.015 | 0.000 | 0.200 | 0.208 | 0.250 | 0.208 |

False-alarm rate on the dependence nulls, parents vs F2 (lrv, 100 lags):

| ('world', '') | ('HG', 'F2_lrv100') | ('HG', 'parent') | ('cost', 'F2_lrv100') | ('cost', 'parent') | ('pprm', 'F2_lrv100') | ('pprm', 'parent') |
|---|---|---|---|---|---|---|
| D2|null|ar0.8_s1.2 | 0.003 | 0.015 | 0.013 | 0.028 | 0.007 | 0.015 |
| D2|null|ar0.97_s1.2 | 0.013 | 0.037 | 0.028 | 0.070 | 0.013 | 0.022 |
| D2|null|cluster200_s1.2 | 0.030 | 0.085 | 0.092 | 0.200 | 0.025 | 0.045 |
| D2|null|cluster50_s1.2 | 0.005 | 0.022 | 0.013 | 0.035 | 0.005 | 0.013 |
| D2|null|fin_garch_a.10b.88 | 0.048 | 0.233 | 0.050 | 0.060 | 0.092 | 0.225 |
| D2|null|fin_garch_a.15b.8 | 0.045 | 0.135 | 0.013 | 0.010 | 0.030 | 0.150 |

* **F1 floored allocation: rejected.** Raising the floor to frac/2 removes most of the unfloored loss (HG iid power -0.081 -> -0.048) and even helps transient worlds (+0.03 to +0.065), but it never beats uniform on iid harm worlds.
* **F2 long-run-variance bet: rejected as an improvement claim; partial as a size mitigation.** It cuts the worst dependent-null false-alarm rate by 60-80% for all three parents (pprm .225 -> .092, HG .232 -> .048, cost .200 -> .092) but restores the nominal level for only one parent (HG: worst dependent-null FA 0.048); even that parent misses the preregistered power-loss limit (iid power change -0.0501 vs -0.05), so 0 of 3 parents pass. It costs 0.05-0.08 iid power and 0.07-0.21 transient power and is a heuristic with no proof.
* **F3 multi-window mixture: rejected.** It raises pprm's transient power (+0.14) at the price of false alarms (+0.07 non-harm, worst dependence null 0.49); for HG and cost it lowers power.
No fix generalizes to >= 2 parents. These negative results are recorded in the registry; none is promoted to confirmation (except F2-on-HG, included as an informational arm).
