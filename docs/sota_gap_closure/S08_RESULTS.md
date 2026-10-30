# S08 balanced growth-aware sampling: results
Synthetic stratified problem: a rare subgroup {x_2 > thr} (prevalence 31% / 16% / 6.7%) whose label law changes (logit shift 8 on the group) at t=800, decision-cost asymmetry FN in {5, 15}, accurate or miscalibrated proxy, null world; HG parent, fractions .05 / .10, 150 seeds, 14 worlds. Arms: stratified-uniform (= uniform), ASI-like variance, balanced (equal expected label counts per group: SOURCE_INSPIRED, **not** a verified Balanced Active Inference), growth, balanced+growth (50/50 propensity mixture). "Group coverage" = share of queried labels in the rare group (uniform: its prevalence). Harm threshold for this pool 0.02 (strong subgroup shift but small overall harm).

## v1: floors frac/4

| config | power | harm_before | labels | fa_nonharm | rare_group_label_share | ms_per_seed | rss_mb |
|---|---|---|---|---|---|---|---|
| HG|bal_growth|f0.05 | 0.002 | 156.838 | 105.164 | 0.000 | 0.328 | 7.226 | 266.090 |
| HG|bal_growth|f0.1 | 0.067 | 154.074 | 209.454 | 0.000 | 0.328 | 7.825 | 266.090 |
| HG|balanced|f0.05 | 0.003 | 156.835 | 99.100 | 0.000 | 0.497 | 5.608 | 266.090 |
| HG|balanced|f0.1 | 0.056 | 154.106 | 198.816 | 0.000 | 0.495 | 6.666 | 266.090 |
| HG|growth|f0.05 | 0.004 | 156.725 | 111.339 | 0.000 | 0.177 | 6.301 | 266.090 |
| HG|growth|f0.1 | 0.061 | 153.523 | 219.437 | 0.000 | 0.177 | 7.980 | 266.090 |
| HG|uniform|f0.05 | 0.056 | 152.221 | 100.073 | 0.000 | 0.177 | 2.474 | 266.090 |
| HG|uniform|f0.1 | 0.143 | 144.694 | 199.193 | 0.000 | 0.176 | 2.799 | 266.090 |
| HG|variance|f0.05 | 0.003 | 156.837 | 97.368 | 0.000 | 0.177 | 5.140 | 266.090 |
| HG|variance|f0.1 | 0.051 | 153.870 | 195.423 | 0.000 | 0.177 | 5.418 | 266.090 |

Power by rare-group prevalence (prev31 = 31%, prev16 = 16%, prev07 = 6.7%):

| prev | HG|bal_growth|f0.05 | HG|bal_growth|f0.1 | HG|balanced|f0.05 | HG|balanced|f0.1 | HG|growth|f0.05 | HG|growth|f0.1 | HG|uniform|f0.05 | HG|uniform|f0.1 | HG|variance|f0.05 | HG|variance|f0.1 |
|---|---|---|---|---|---|---|---|---|---|---|
| prev07 | 0.000 | 0.005 | 0.002 | 0.003 | 0.002 | 0.003 | 0.017 | 0.020 | 0.000 | 0.000 |
| prev16 | 0.000 | 0.015 | 0.000 | 0.013 | 0.000 | 0.012 | 0.035 | 0.062 | 0.000 | 0.012 |
| prev31 | 0.007 | 0.180 | 0.008 | 0.152 | 0.012 | 0.167 | 0.115 | 0.347 | 0.008 | 0.142 |

## v2: floors frac/2

| config | power | harm_before | labels | fa_nonharm | rare_group_label_share | ms_per_seed | rss_mb |
|---|---|---|---|---|---|---|---|
| HG|bal_growth|f0.05 | 0.047 | 154.243 | 107.752 | 0.000 | 0.324 | 7.367 | 264.242 |
| HG|bal_growth|f0.1 | 0.191 | 142.531 | 214.179 | 0.000 | 0.325 | 7.369 | 264.242 |
| HG|balanced|f0.05 | 0.045 | 154.263 | 99.100 | 0.000 | 0.497 | 6.282 | 264.242 |
| HG|balanced|f0.1 | 0.137 | 146.625 | 198.816 | 0.000 | 0.495 | 6.309 | 264.242 |
| HG|growth|f0.05 | 0.041 | 154.394 | 116.544 | 0.000 | 0.177 | 6.733 | 264.242 |
| HG|growth|f0.1 | 0.178 | 143.357 | 229.422 | 0.000 | 0.178 | 7.061 | 264.242 |
| HG|uniform|f0.05 | 0.056 | 152.221 | 100.073 | 0.000 | 0.177 | 2.851 | 264.242 |
| HG|uniform|f0.1 | 0.143 | 144.694 | 199.193 | 0.000 | 0.176 | 2.486 | 264.242 |
| HG|variance|f0.05 | 0.041 | 153.920 | 97.992 | 0.000 | 0.177 | 5.998 | 264.242 |
| HG|variance|f0.1 | 0.136 | 145.923 | 196.243 | 0.000 | 0.177 | 6.243 | 264.242 |

Power by rare-group prevalence (prev31 = 31%, prev16 = 16%, prev07 = 6.7%):

| prev | HG|bal_growth|f0.05 | HG|bal_growth|f0.1 | HG|balanced|f0.05 | HG|balanced|f0.1 | HG|growth|f0.05 | HG|growth|f0.1 | HG|uniform|f0.05 | HG|uniform|f0.1 | HG|variance|f0.05 | HG|variance|f0.1 |
|---|---|---|---|---|---|---|---|---|---|---|
| prev07 | 0.003 | 0.022 | 0.012 | 0.012 | 0.010 | 0.015 | 0.017 | 0.020 | 0.008 | 0.012 |
| prev16 | 0.013 | 0.083 | 0.013 | 0.058 | 0.013 | 0.087 | 0.035 | 0.062 | 0.017 | 0.063 |
| prev31 | 0.125 | 0.467 | 0.110 | 0.340 | 0.100 | 0.432 | 0.115 | 0.347 | 0.098 | 0.332 |

## Reading
Balancing does what it promises on coverage (rare-group label share ~0.50 vs ~0.18 under uniform) but, by itself, buys no sequential power. With floors raised to frac/2 (v2) the picture changes versus v1: uniform 0.143; balanced 0.137; growth 0.178; bal_growth 0.191 (harm-world power at 10% labels). Whether balancing and evidence-growth optimisation are complementary: in v2 the 50/50 balancing + growth mixture is the best arm at 10% labels, while pure balancing is not better than uniform; v1 (floor frac/4) shows the opposite ordering because the predictable cap throttles every non-uniform rule. This is a development-pool result on one synthetic family with 150 seeds per world: it is **not confirmed** on untouched pools. The estimation-quality part of S08 (MSE / CI coverage under balancing) was not run: S08 here is a sequential-monitoring benchmark only (disclosed gap).
