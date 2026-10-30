# S05 robust growth/variance hybrid: results
Full probability-simplex grid (u in {0,.1,.25,.5,.75,1} x g in {0,.25,.5,.75,1}, u+g <= 1, v = 1-u-g) x reliability mode {fixed, adaptive, conservative} = 51 mixtures + uniform parent = 52 configurations (HG, fraction 0.10, delay 5, 12 worlds, 100 seeds). No guarantee of the published Robust-ASI is claimed for any mixture.

Top configurations by harm-world power:

| config | power | harm_before | labels | fa_nonharm_mean | fa_nonharm_max | power_worst2_worlds |
|---|---|---|---|---|---|---|
| HG|mix|u0.1|g0|v0.9|conservative | 0.601 | 157.122 | 199.716 | 0.008 | 0.020 | 0.260 |
| HG|mix|u0|g0|v1|conservative | 0.601 | 157.122 | 199.716 | 0.008 | 0.020 | 0.260 |
| HG|mix|u0.5|g0|v0.5|fixed | 0.601 | 157.122 | 199.716 | 0.008 | 0.020 | 0.260 |
| HG|mix|u0.25|g0|v0.75|conservative | 0.601 | 157.122 | 199.716 | 0.008 | 0.020 | 0.260 |
| HG|mix|u0.5|g0|v0.5|adaptive | 0.600 | 157.127 | 200.813 | 0.010 | 0.020 | 0.265 |
| HG|mix|u0.75|g0|v0.25|adaptive | 0.596 | 160.010 | 201.173 | 0.016 | 0.040 | 0.250 |
| HG|mix|u0.75|g0|v0.25|fixed | 0.594 | 158.806 | 200.557 | 0.016 | 0.040 | 0.240 |
| HG|mix|u0.25|g0|v0.75|adaptive | 0.584 | 168.007 | 200.679 | 0.002 | 0.010 | 0.225 |
| HG|mix|u0.25|g0|v0.75|fixed | 0.579 | 166.301 | 198.991 | 0.006 | 0.020 | 0.210 |
| HG|mix|u1.0|g0|v0.0|adaptive | 0.569 | 163.048 | 201.080 | 0.018 | 0.040 | 0.215 |
| HG|uniform | 0.569 | 163.048 | 201.080 | 0.018 | 0.040 | 0.215 |
| HG|mix|u1.0|g0|v0.0|fixed | 0.569 | 163.048 | 201.080 | 0.018 | 0.040 | 0.215 |

Power (fixed mode) by uniform share u (rows) and growth share g (columns):

| u | 0 | 0.25 | 0.5 | 0.75 | 1.0 |
|---|---|---|---|---|---|
| 0 | 0.406 | 0.351 | 0.286 | 0.184 | 0.080 |
| 0.1 | 0.501 | 0.443 | 0.343 | 0.227 |  |
| 0.25 | 0.579 | 0.489 | 0.379 | 0.206 |  |
| 0.5 | 0.601 | 0.489 | 0.331 |  |  |
| 0.75 | 0.594 | 0.446 |  |  |  |
| 1.0 | 0.569 |  |  |  |  |

* Every configuration with g > 0 loses power; the growth component never helps (consistent with S04).
* The best Pareto points are the variance/uniform mixtures with floor >= 0.5 (power 0.601 vs uniform 0.569, lower non-harm FA 0.008 vs 0.018, better worst-2 power). That **is** the Robust-ASI analogue (u=.5, v=.5), so the hybrid occupies no improved Pareto position over the simpler robust mixture; configurations improving on it by +0.02 power without FA or worst-case loss: **0**.
* Acceptance: NOT met. The tested hybrid addresses no failure that the robust variance mixture does not already handle; fixed / adaptive / conservative differ only where u < 0.5.
