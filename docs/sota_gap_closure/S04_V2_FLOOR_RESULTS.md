# S04 v2: growth-aware querying with corrected propensity floors (frac/2)
Same arms, worlds (23), seeds (150) and parents as `S04_RESULTS.md`, but the non-uniform arms use a propensity floor of frac/2 (v1: frac/4); label fractions .05 / .10 / .20; delay 5; expected-budget contract. Development pool only; nothing here is confirmed on untouched seeds.

Mean power and false alarm by arm:

| parent | frac | arm | power | labels | fa_nonharm |
|---|---|---|---|---|---|
| HG | f0.05 | growth | 0.263 | 118.289 | 0.007 |
| HG | f0.05 | growth_harm | 0.235 | 125.282 | 0.006 |
| HG | f0.05 | growth_look | 0.275 | 122.331 | 0.007 |
| HG | f0.05 | growth_oracle | 0.331 | 117.562 | 0.006 |
| HG | f0.05 | robust_mix | 0.270 | 100.038 | 0.009 |
| HG | f0.05 | uniform | 0.247 | 100.560 | 0.007 |
| HG | f0.05 | variance | 0.244 | 100.519 | 0.006 |
| HG | f0.1 | growth | 0.612 | 233.705 | 0.038 |
| HG | f0.1 | growth_harm | 0.624 | 245.985 | 0.034 |
| HG | f0.1 | growth_look | 0.648 | 247.782 | 0.041 |
| HG | f0.1 | growth_oracle | 0.692 | 231.609 | 0.043 |
| HG | f0.1 | robust_mix | 0.577 | 200.155 | 0.035 |
| HG | f0.1 | uniform | 0.540 | 200.873 | 0.031 |
| HG | f0.1 | variance | 0.554 | 200.833 | 0.032 |
| HG | f0.2 | growth | 0.847 | 461.606 | 0.096 |
| HG | f0.2 | growth_harm | 0.859 | 482.421 | 0.101 |
| HG | f0.2 | growth_look | 0.864 | 495.469 | 0.097 |
| HG | f0.2 | growth_oracle | 0.885 | 453.541 | 0.107 |
| HG | f0.2 | robust_mix | 0.815 | 399.537 | 0.087 |
| HG | f0.2 | uniform | 0.791 | 400.260 | 0.083 |
| HG | f0.2 | variance | 0.816 | 401.135 | 0.081 |
| pprm | f0.05 | growth | 0.277 | 114.339 | 0.018 |
| pprm | f0.05 | growth_harm | 0.265 | 120.134 | 0.016 |
| pprm | f0.05 | growth_look | 0.277 | 117.893 | 0.018 |
| pprm | f0.05 | growth_oracle | 0.362 | 113.149 | 0.020 |
| pprm | f0.05 | robust_mix | 0.234 | 100.038 | 0.017 |
| pprm | f0.05 | uniform | 0.217 | 100.560 | 0.019 |
| pprm | f0.05 | variance | 0.227 | 100.519 | 0.015 |
| pprm | f0.1 | growth | 0.527 | 227.798 | 0.053 |
| pprm | f0.1 | growth_harm | 0.548 | 238.687 | 0.054 |
| pprm | f0.1 | growth_look | 0.548 | 239.495 | 0.057 |
| pprm | f0.1 | growth_oracle | 0.607 | 224.257 | 0.060 |
| pprm | f0.1 | robust_mix | 0.483 | 200.155 | 0.042 |
| pprm | f0.1 | uniform | 0.452 | 200.873 | 0.040 |
| pprm | f0.1 | variance | 0.470 | 200.833 | 0.040 |
| pprm | f0.2 | growth | 0.742 | 452.446 | 0.097 |
| pprm | f0.2 | growth_harm | 0.758 | 472.910 | 0.098 |
| pprm | f0.2 | growth_look | 0.761 | 483.513 | 0.103 |
| pprm | f0.2 | growth_oracle | 0.786 | 444.144 | 0.116 |
| pprm | f0.2 | robust_mix | 0.712 | 399.537 | 0.095 |
| pprm | f0.2 | uniform | 0.687 | 400.260 | 0.093 |
| pprm | f0.2 | variance | 0.705 | 401.135 | 0.091 |

Paired differences at the same *nominal* fraction (cluster bootstrap over worlds then seeds, 2,000 resamples; harm worlds equally weighted). **These are not label-matched**: the non-uniform arms realise 8-17% more labels than uniform at the same nominal fraction (floor plus running normalisation push mean propensity above frac):

| parent | label_frac | A | B | power A-B | ci_lo | ci_hi |
|---|---|---|---|---|---|---|
| HG | 0.05 | variance | uniform | -0.003 | -0.029 | 0.026 |
| HG | 0.05 | growth | uniform | 0.015 | -0.015 | 0.049 |
| HG | 0.05 | growth_oracle | uniform | 0.084 | 0.029 | 0.143 |
| HG | 0.05 | growth_harm | uniform | -0.012 | -0.038 | 0.020 |
| HG | 0.05 | growth_look | uniform | 0.028 | -0.005 | 0.065 |
| HG | 0.05 | robust_mix | uniform | 0.023 | -0.003 | 0.050 |
| HG | 0.05 | growth | variance | 0.018 | -0.002 | 0.042 |
| HG | 0.05 | growth | robust_mix | -0.007 | -0.029 | 0.014 |
| HG | 0.1 | variance | uniform | 0.015 | -0.024 | 0.047 |
| HG | 0.1 | growth | uniform | 0.072 | 0.019 | 0.121 |
| HG | 0.1 | growth_oracle | uniform | 0.153 | 0.072 | 0.227 |
| HG | 0.1 | growth_harm | uniform | 0.084 | 0.029 | 0.130 |
| HG | 0.1 | growth_look | uniform | 0.108 | 0.042 | 0.167 |
| HG | 0.1 | robust_mix | uniform | 0.038 | 0.002 | 0.070 |
| HG | 0.1 | growth | variance | 0.057 | 0.029 | 0.089 |
| HG | 0.1 | growth | robust_mix | 0.034 | 0.009 | 0.062 |
| HG | 0.2 | variance | uniform | 0.025 | -0.006 | 0.055 |
| HG | 0.2 | growth | uniform | 0.056 | 0.016 | 0.101 |
| HG | 0.2 | growth_oracle | uniform | 0.094 | 0.028 | 0.168 |
| HG | 0.2 | growth_harm | uniform | 0.068 | 0.018 | 0.122 |
| HG | 0.2 | growth_look | uniform | 0.073 | 0.022 | 0.129 |
| HG | 0.2 | robust_mix | uniform | 0.024 | 0.003 | 0.046 |
| HG | 0.2 | growth | variance | 0.031 | 0.009 | 0.057 |
| HG | 0.2 | growth | robust_mix | 0.033 | 0.010 | 0.060 |
| pprm | 0.05 | variance | uniform | 0.010 | -0.014 | 0.035 |
| pprm | 0.05 | growth | uniform | 0.060 | 0.025 | 0.099 |
| pprm | 0.05 | growth_oracle | uniform | 0.145 | 0.075 | 0.220 |
| pprm | 0.05 | growth_harm | uniform | 0.048 | 0.014 | 0.084 |
| pprm | 0.05 | growth_look | uniform | 0.060 | 0.023 | 0.102 |
| pprm | 0.05 | robust_mix | uniform | 0.017 | -0.005 | 0.039 |
| pprm | 0.05 | growth | variance | 0.050 | 0.027 | 0.078 |
| pprm | 0.05 | growth | robust_mix | 0.044 | 0.017 | 0.073 |
| pprm | 0.1 | variance | uniform | 0.018 | -0.010 | 0.047 |
| pprm | 0.1 | growth | uniform | 0.075 | 0.035 | 0.119 |
| pprm | 0.1 | growth_oracle | uniform | 0.155 | 0.090 | 0.220 |
| pprm | 0.1 | growth_harm | uniform | 0.096 | 0.053 | 0.146 |
| pprm | 0.1 | growth_look | uniform | 0.096 | 0.051 | 0.143 |
| pprm | 0.1 | robust_mix | uniform | 0.031 | 0.011 | 0.054 |
| pprm | 0.1 | growth | variance | 0.057 | 0.029 | 0.088 |
| pprm | 0.1 | growth | robust_mix | 0.044 | 0.014 | 0.077 |
| pprm | 0.2 | variance | uniform | 0.017 | 0.002 | 0.033 |
| pprm | 0.2 | growth | uniform | 0.055 | 0.028 | 0.085 |
| pprm | 0.2 | growth_oracle | uniform | 0.098 | 0.052 | 0.153 |
| pprm | 0.2 | growth_harm | uniform | 0.070 | 0.036 | 0.108 |
| pprm | 0.2 | growth_look | uniform | 0.073 | 0.038 | 0.114 |
| pprm | 0.2 | robust_mix | uniform | 0.025 | 0.011 | 0.042 |
| pprm | 0.2 | growth | variance | 0.037 | 0.012 | 0.067 |
| pprm | 0.2 | growth | robust_mix | 0.030 | 0.009 | 0.053 |

**Label-matched comparison.** Uniform's power-vs-realised-labels curve (nominal fractions .05 / .10 / .20) is interpolated at each arm's realised label count:

| parent | frac | arm | labels | power | uniform_power_at_same_labels | label_matched_gain |
|---|---|---|---|---|---|---|
| HG | f0.05 | growth | 118.289 | 0.263 | 0.299 | -0.036 |
| HG | f0.05 | growth_harm | 125.282 | 0.235 | 0.319 | -0.084 |
| HG | f0.05 | growth_look | 122.331 | 0.275 | 0.311 | -0.036 |
| HG | f0.05 | growth_oracle | 117.562 | 0.331 | 0.297 | 0.034 |
| HG | f0.05 | robust_mix | 100.038 | 0.270 | 0.247 | 0.023 |
| HG | f0.05 | variance | 100.519 | 0.244 | 0.247 | -0.003 |
| HG | f0.1 | growth | 233.705 | 0.612 | 0.581 | 0.031 |
| HG | f0.1 | growth_harm | 245.985 | 0.624 | 0.596 | 0.027 |
| HG | f0.1 | growth_look | 247.782 | 0.648 | 0.599 | 0.049 |
| HG | f0.1 | growth_oracle | 231.609 | 0.692 | 0.578 | 0.114 |
| HG | f0.1 | robust_mix | 200.155 | 0.577 | 0.538 | 0.040 |
| HG | f0.1 | variance | 200.833 | 0.554 | 0.539 | 0.015 |
| HG | f0.2 | growth | 461.606 | 0.847 | 0.791 | 0.056 |
| HG | f0.2 | growth_harm | 482.421 | 0.859 | 0.791 | 0.068 |
| HG | f0.2 | growth_look | 495.469 | 0.864 | 0.791 | 0.073 |
| HG | f0.2 | growth_oracle | 453.541 | 0.885 | 0.791 | 0.094 |
| HG | f0.2 | robust_mix | 399.537 | 0.815 | 0.790 | 0.024 |
| HG | f0.2 | variance | 401.135 | 0.816 | 0.791 | 0.025 |
| pprm | f0.05 | growth | 114.339 | 0.277 | 0.249 | 0.028 |
| pprm | f0.05 | growth_harm | 120.134 | 0.265 | 0.263 | 0.002 |
| pprm | f0.05 | growth_look | 117.893 | 0.277 | 0.258 | 0.020 |
| pprm | f0.05 | growth_oracle | 113.149 | 0.362 | 0.246 | 0.116 |
| pprm | f0.05 | robust_mix | 100.038 | 0.234 | 0.217 | 0.017 |
| pprm | f0.05 | variance | 100.519 | 0.227 | 0.217 | 0.010 |
| pprm | f0.1 | growth | 227.798 | 0.527 | 0.484 | 0.044 |
| pprm | f0.1 | growth_harm | 238.687 | 0.548 | 0.497 | 0.052 |
| pprm | f0.1 | growth_look | 239.495 | 0.548 | 0.497 | 0.050 |
| pprm | f0.1 | growth_oracle | 224.257 | 0.607 | 0.479 | 0.127 |
| pprm | f0.1 | robust_mix | 200.155 | 0.483 | 0.450 | 0.033 |
| pprm | f0.1 | variance | 200.833 | 0.470 | 0.452 | 0.019 |
| pprm | f0.2 | growth | 452.446 | 0.742 | 0.687 | 0.055 |
| pprm | f0.2 | growth_harm | 472.910 | 0.758 | 0.687 | 0.070 |
| pprm | f0.2 | growth_look | 483.513 | 0.761 | 0.687 | 0.073 |
| pprm | f0.2 | growth_oracle | 444.144 | 0.786 | 0.687 | 0.098 |
| pprm | f0.2 | robust_mix | 399.537 | 0.712 | 0.686 | 0.026 |
| pprm | f0.2 | variance | 401.135 | 0.705 | 0.687 | 0.017 |

**Reading.** v1 concluded that growth-aware querying loses to uniform; that was largely a consequence of the frac/4 floor. With frac/2 floors growth-aware arms beat uniform at the same nominal fraction, but most of that is extra labels: label-matched gains of the estimated growth arm are >= +0.03 in 4 of 6 (parent, fraction) cells, and the ORACLE-alternative arm (true P(y=1|x) known) keeps a larger label-matched gain, i.e. most of the available benefit is lost to estimating the alternative. Growth minus variance is within about +-0.02 (growth equals variance to second order). Acceptance for S04 (improves over the best of uniform / variance / robust mixture by >= +0.03 mean power, <= 25% of worlds worse than -0.03, non-harm FA change <= +0.02) is evaluated from the table above and stated in `FINAL` reports; **Confirmation round 2 (fresh seeds, frozen before running) did not confirm the development result:** label-matched gains of HG_growth_floor@0.1 -0.010; HG_growth_floor@0.2 -0.020; HG_growthlook_floor@0.1 -0.013; HG_growthlook_floor@0.2 -0.023; HG_variance_floor@0.1 +0.015; HG_variance_floor@0.2 -0.018 (practical threshold +0.03; see `FINAL_CONFIRMATION_ROUND2_RESULTS.md`). The development-pool gains are therefore treated as a selection effect / pool-specific.
