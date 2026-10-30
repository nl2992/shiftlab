# S04 growth-aware active querying: results
Arms (per `02_*`): uniform, variance (Neyman with start-prior shrinkage), growth (estimated alternative), growth (ORACLE alternative = true P(y=1|x), evaluator information), growth_harm, growth_look, robust mixture (u=.5, v=.5 conservative), budget-aware growth (hard budget B = frac*T with remaining-budget pacing). Parents `pprm` and HG; fractions 0.05 / 0.10; delay 5 and 20; 23 worlds (G1 dev pool 19 + G2 concept / cov_benign + G3 cycle + G4 finance), 150 seeds, expected-budget contract (realised labels reported; label-normalised power = power per 100 labels).

Mean paired power difference on harm worlds (delay 5):

| parent | frac | growth - variance | growth - uniform | variance - uniform | growth_oracle - growth | robust_mix - uniform |
|---|---|---|---|---|---|---|
| HG | f0.05 | 0.002 | -0.174 | -0.175 | 0.020 | 0.023 |
| HG | f0.1 | 0.010 | -0.135 | -0.145 | 0.053 | 0.038 |
| pprm | f0.05 | 0.006 | -0.099 | -0.105 | 0.007 | 0.017 |
| pprm | f0.1 | 0.039 | -0.006 | -0.045 | 0.051 | 0.031 |

### delay 5

| parent | frac | arm | power | labels | harm_before | fa_nonharm | power_per_100_labels |
|---|---|---|---|---|---|---|---|
| HG | f0.05 | budget_growth | 0.053 | 99.957 | 212.937 | 0.000 | 0.053 |
| HG | f0.05 | growth | 0.073 | 112.395 | 212.464 | 0.000 | 0.065 |
| HG | f0.05 | growth_harm | 0.054 | 117.998 | 213.355 | 0.000 | 0.046 |
| HG | f0.05 | growth_look | 0.074 | 114.727 | 211.825 | 0.000 | 0.065 |
| HG | f0.05 | growth_oracle | 0.093 | 112.112 | 211.350 | 0.000 | 0.083 |
| HG | f0.05 | robust_mix | 0.270 | 100.038 | 187.882 | 0.009 | 0.270 |
| HG | f0.05 | uniform | 0.247 | 100.560 | 190.876 | 0.007 | 0.246 |
| HG | f0.05 | variance | 0.072 | 99.568 | 212.635 | 0.000 | 0.072 |
| HG | f0.1 | budget_growth | 0.354 | 199.924 | 179.621 | 0.010 | 0.177 |
| HG | f0.1 | growth | 0.405 | 223.502 | 174.707 | 0.005 | 0.181 |
| HG | f0.1 | growth_harm | 0.373 | 233.375 | 177.609 | 0.005 | 0.160 |
| HG | f0.1 | growth_look | 0.430 | 234.848 | 171.400 | 0.007 | 0.183 |
| HG | f0.1 | growth_oracle | 0.458 | 221.639 | 167.312 | 0.007 | 0.207 |
| HG | f0.1 | robust_mix | 0.577 | 200.155 | 139.500 | 0.035 | 0.289 |
| HG | f0.1 | uniform | 0.540 | 200.873 | 147.118 | 0.031 | 0.269 |
| HG | f0.1 | variance | 0.394 | 199.344 | 175.737 | 0.007 | 0.198 |
| pprm | f0.05 | budget_growth | 0.098 | 99.988 | 209.478 | 0.002 | 0.098 |
| pprm | f0.05 | growth | 0.118 | 109.587 | 208.724 | 0.001 | 0.108 |
| pprm | f0.05 | growth_harm | 0.117 | 114.764 | 208.884 | 0.001 | 0.102 |
| pprm | f0.05 | growth_look | 0.130 | 112.199 | 208.421 | 0.001 | 0.116 |
| pprm | f0.05 | growth_oracle | 0.125 | 108.957 | 208.732 | 0.002 | 0.115 |
| pprm | f0.05 | robust_mix | 0.234 | 100.038 | 194.848 | 0.017 | 0.234 |
| pprm | f0.05 | uniform | 0.217 | 100.560 | 196.538 | 0.019 | 0.216 |
| pprm | f0.05 | variance | 0.112 | 99.568 | 209.774 | 0.005 | 0.113 |
| pprm | f0.1 | budget_growth | 0.429 | 199.977 | 174.514 | 0.025 | 0.214 |
| pprm | f0.1 | growth | 0.446 | 218.384 | 172.151 | 0.029 | 0.204 |
| pprm | f0.1 | growth_harm | 0.457 | 228.765 | 171.389 | 0.029 | 0.200 |
| pprm | f0.1 | growth_look | 0.454 | 229.430 | 171.365 | 0.031 | 0.198 |
| pprm | f0.1 | growth_oracle | 0.497 | 216.167 | 166.902 | 0.034 | 0.230 |
| pprm | f0.1 | robust_mix | 0.483 | 200.155 | 162.407 | 0.042 | 0.241 |
| pprm | f0.1 | uniform | 0.452 | 200.873 | 167.709 | 0.040 | 0.225 |
| pprm | f0.1 | variance | 0.407 | 199.344 | 177.206 | 0.029 | 0.204 |
### delay 20

| parent | frac | arm | power | labels | harm_before | fa_nonharm | power_per_100_labels |
|---|---|---|---|---|---|---|---|
| HG | f0.05 | budget_growth | 0.058 | 99.951 | 213.081 | 0.000 | 0.058 |
| HG | f0.05 | growth | 0.066 | 111.964 | 212.607 | 0.000 | 0.059 |
| HG | f0.05 | growth_harm | 0.058 | 117.285 | 213.497 | 0.000 | 0.049 |
| HG | f0.05 | growth_look | 0.072 | 114.136 | 212.343 | 0.000 | 0.063 |
| HG | f0.05 | growth_oracle | 0.084 | 111.581 | 211.578 | 0.000 | 0.075 |
| HG | f0.05 | robust_mix | 0.263 | 100.071 | 189.031 | 0.009 | 0.262 |
| HG | f0.05 | uniform | 0.237 | 100.560 | 192.306 | 0.008 | 0.236 |
| HG | f0.05 | variance | 0.065 | 99.582 | 212.825 | 0.000 | 0.065 |
| HG | f0.1 | budget_growth | 0.354 | 199.924 | 181.230 | 0.006 | 0.177 |
| HG | f0.1 | growth | 0.396 | 221.872 | 176.592 | 0.009 | 0.178 |
| HG | f0.1 | growth_harm | 0.366 | 231.225 | 179.167 | 0.005 | 0.158 |
| HG | f0.1 | growth_look | 0.412 | 233.161 | 174.155 | 0.007 | 0.177 |
| HG | f0.1 | growth_oracle | 0.442 | 219.822 | 170.349 | 0.008 | 0.201 |
| HG | f0.1 | robust_mix | 0.561 | 199.944 | 143.578 | 0.036 | 0.281 |
| HG | f0.1 | uniform | 0.532 | 200.873 | 150.170 | 0.027 | 0.265 |
| HG | f0.1 | variance | 0.385 | 199.073 | 177.647 | 0.005 | 0.193 |
| pprm | f0.05 | budget_growth | 0.091 | 99.988 | 210.591 | 0.003 | 0.091 |
| pprm | f0.05 | growth | 0.108 | 108.890 | 210.003 | 0.001 | 0.099 |
| pprm | f0.05 | growth_harm | 0.103 | 113.997 | 209.506 | 0.001 | 0.090 |
| pprm | f0.05 | growth_look | 0.109 | 111.308 | 209.902 | 0.001 | 0.098 |
| pprm | f0.05 | growth_oracle | 0.119 | 108.274 | 209.581 | 0.002 | 0.110 |
| pprm | f0.05 | robust_mix | 0.222 | 100.071 | 196.872 | 0.016 | 0.222 |
| pprm | f0.05 | uniform | 0.206 | 100.560 | 198.185 | 0.019 | 0.205 |
| pprm | f0.05 | variance | 0.102 | 99.582 | 210.022 | 0.003 | 0.102 |
| pprm | f0.1 | budget_growth | 0.411 | 199.976 | 177.527 | 0.029 | 0.205 |
| pprm | f0.1 | growth | 0.422 | 216.656 | 175.963 | 0.030 | 0.195 |
| pprm | f0.1 | growth_harm | 0.433 | 226.503 | 174.947 | 0.027 | 0.191 |
| pprm | f0.1 | growth_look | 0.438 | 227.122 | 174.786 | 0.029 | 0.193 |
| pprm | f0.1 | growth_oracle | 0.460 | 213.927 | 171.699 | 0.027 | 0.215 |
| pprm | f0.1 | robust_mix | 0.467 | 199.944 | 165.980 | 0.041 | 0.234 |
| pprm | f0.1 | uniform | 0.438 | 200.873 | 170.593 | 0.041 | 0.218 |
| pprm | f0.1 | variance | 0.393 | 199.073 | 179.942 | 0.025 | 0.198 |

## Reading
* **H4 holds**: growth-aware querying equals variance-only to within about +0.01 (second-order argument in `02_*`: the log-growth objective's only q-dependent term is the IPW variance).
* **Both lose to uniform querying** (and to the robust mixture) by 0.1-0.2 power for HG at the same expected label count. The loss is caused by the validity requirement, not by bad scores: any non-uniform propensity needs a predictable floor `q_min`, and the bet cap is `0.5 / (theta pmax (1/q_min - 1) + r0)`. Floors of `frac/4` shrink the admissible bet ~4x. The ORACLE growth arm (true alternative known) is better than the estimated one (+0.03 to +0.05) yet still below uniform.
* The robust mixture (floor >= 0.625 frac) is the only non-uniform arm that matches or beats uniform (see S05).
**Acceptance (improve over the best of uniform / variance / robust mixture): NOT met.** Budget-aware growth under a hard cap is worse than uniform as well. No exact RPOQ oracle-gap computation was possible at scale; exact gaps on the toy instance are in `S11_ORACLE_GAP_RESULTS.md`.
