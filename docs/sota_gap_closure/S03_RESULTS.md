# S03 proxy-reliability-adaptive monitoring: results (preregistered in `02_S03_S06_PREREGISTRATION.md`)
Stage 1 screen: all 108 (window x smoothing x fallback x gate) combinations x 2 parents (`pprm`, HG) + parents = 218 configurations, label fraction 0.10, delay 5, 12 G5 development worlds, 100 seeds each (`outputs/gap_closure/e2_s03_screen`, 261,600 per-seed rows). Stage 2 (preregistered "top 8 at all four fractions") was replaced by a **sensitivity run of three representative variants** over the four fractions and a blend of accurate -> anti-informative proxy (`e2b_s03_sensitivity`, 200 seeds), because stage 1 produced no candidate that met the screen. The full 432 per parent was not run.

**Acceptance (adverse set A gain >= +0.05, benign set B change >= -0.03, non-harm FA change <= +0.02): 0 of 216 configurations accepted. S03 is NOT supported.**

Median change vs parent by gate x fallback (dA = power on adverse proxy-failure worlds, dB = on accurate / oracle-adapted proxies, dFA = non-harm FA):

| parent | gate | fb | dA | dB | dFA |
|---|---|---|---|---|---|
| HG | hard | conservative_bet | -0.211 | -0.128 | -0.005 |
| HG | hard | none | 0.000 | 0.000 | 0.000 |
| HG | hard | uniform | -0.091 | -0.065 | -0.005 |
| HG | soft | conservative_bet | -0.230 | -0.130 | -0.007 |
| HG | soft | none | -0.011 | 0.000 | -0.002 |
| HG | soft | uniform | -0.107 | -0.065 | -0.007 |
| HG | unc | conservative_bet | -0.256 | -0.145 | -0.008 |
| HG | unc | none | -0.026 | -0.010 | -0.003 |
| HG | unc | uniform | -0.127 | -0.072 | -0.010 |
| pprm | hard | conservative_bet | -0.249 | -0.133 | -0.002 |
| pprm | hard | none | 0.000 | 0.000 | 0.000 |
| pprm | hard | uniform | -0.111 | -0.050 | -0.002 |
| pprm | soft | conservative_bet | -0.257 | -0.138 | -0.002 |
| pprm | soft | none | -0.009 | 0.003 | -0.002 |
| pprm | soft | uniform | -0.125 | -0.053 | -0.002 |
| pprm | unc | conservative_bet | -0.305 | -0.172 | -0.002 |
| pprm | unc | none | -0.041 | -0.022 | -0.001 |
| pprm | unc | uniform | -0.143 | -0.085 | 0.002 |

Only `fallback=none` is neutral (it is the parent: `rel=hard,fallback=none` is an identity, checked in `test_parent_modified_identities`); every active fallback loses power in the adverse worlds too. Reason: with 10% labels a window of 32-256 labels gives a noisy skill / slope estimate, so the reliability gate fires spuriously on accurate proxies (dB negative) and the IPW-only fallback has much larger variance than the proxy-assisted increment even when the proxy is anti-informative (the parent loses only ~0.1 power at full anti-informative corruption).

Parents' power vs proxy corruption (blend 0 = accurate ... 1 = anti-informative after the shift; the four label fractions are in the config names):

| config | concept2|blend0.0 | concept2|blend0.25 | concept2|blend0.5 | concept2|blend0.75 | concept2|blend1.0 |
|---|---|---|---|---|---|
| HG|hard_w64_uniform|f0.01 | 0.02 | 0.00 | 0.00 | 0.00 | 0.01 |
| HG|hard_w64_uniform|f0.05 | 0.23 | 0.26 | 0.22 | 0.26 | 0.20 |
| HG|hard_w64_uniform|f0.1 | 0.60 | 0.59 | 0.57 | 0.57 | 0.54 |
| HG|hard_w64_uniform|f0.2 | 0.94 | 0.97 | 0.92 | 0.94 | 0.90 |
| HG|parent|f0.01 | 0.02 | 0.00 | 0.01 | 0.02 | 0.02 |
| HG|parent|f0.05 | 0.35 | 0.36 | 0.40 | 0.36 | 0.30 |
| HG|parent|f0.1 | 0.78 | 0.76 | 0.78 | 0.75 | 0.67 |
| HG|parent|f0.2 | 0.99 | 1.00 | 0.98 | 1.00 | 0.96 |
| HG|soft_w128_none|f0.01 | 0.02 | 0.00 | 0.02 | 0.02 | 0.02 |
| HG|soft_w128_none|f0.05 | 0.34 | 0.36 | 0.40 | 0.36 | 0.30 |
| HG|soft_w128_none|f0.1 | 0.78 | 0.76 | 0.77 | 0.74 | 0.68 |
| HG|soft_w128_none|f0.2 | 0.99 | 0.99 | 0.98 | 1.00 | 0.96 |
| HG|unc_w128_uniform|f0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.01 |
| HG|unc_w128_uniform|f0.05 | 0.22 | 0.24 | 0.22 | 0.25 | 0.19 |
| HG|unc_w128_uniform|f0.1 | 0.58 | 0.58 | 0.57 | 0.58 | 0.55 |
| HG|unc_w128_uniform|f0.2 | 0.94 | 0.97 | 0.94 | 0.95 | 0.90 |
| pprm|hard_w64_uniform|f0.01 | 0.04 | 0.02 | 0.03 | 0.04 | 0.02 |
| pprm|hard_w64_uniform|f0.05 | 0.26 | 0.26 | 0.26 | 0.21 | 0.22 |
| pprm|hard_w64_uniform|f0.1 | 0.57 | 0.56 | 0.57 | 0.60 | 0.55 |
| pprm|hard_w64_uniform|f0.2 | 0.94 | 0.94 | 0.89 | 0.91 | 0.90 |
| pprm|parent|f0.01 | 0.04 | 0.02 | 0.02 | 0.03 | 0.02 |
| pprm|parent|f0.05 | 0.36 | 0.36 | 0.32 | 0.32 | 0.25 |
| pprm|parent|f0.1 | 0.73 | 0.75 | 0.74 | 0.70 | 0.64 |
| pprm|parent|f0.2 | 0.98 | 0.96 | 0.96 | 0.97 | 0.94 |
| pprm|soft_w128_none|f0.01 | 0.04 | 0.02 | 0.02 | 0.03 | 0.02 |
| pprm|soft_w128_none|f0.05 | 0.34 | 0.36 | 0.32 | 0.32 | 0.25 |
| pprm|soft_w128_none|f0.1 | 0.74 | 0.74 | 0.71 | 0.70 | 0.64 |
| pprm|soft_w128_none|f0.2 | 0.98 | 0.96 | 0.96 | 0.97 | 0.94 |
| pprm|unc_w128_uniform|f0.01 | 0.04 | 0.02 | 0.02 | 0.04 | 0.02 |
| pprm|unc_w128_uniform|f0.05 | 0.24 | 0.26 | 0.24 | 0.20 | 0.18 |
| pprm|unc_w128_uniform|f0.1 | 0.55 | 0.55 | 0.55 | 0.58 | 0.52 |
| pprm|unc_w128_uniform|f0.2 | 0.94 | 0.92 | 0.90 | 0.92 | 0.90 |

Conclusion: reliability adaptation does not improve a predeclared adverse regime at any tested label rate; it is dominated by the unadapted parent. The proxy-weight mechanism is valid (predictable theta) but not useful here.
