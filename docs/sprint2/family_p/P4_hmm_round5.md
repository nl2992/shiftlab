# P4 Round-5 HMM-null misspecification follow-up

1,000 seeds on the registered `P_hmm_null` generator (`hmm_p=(0.3,0.7)`). This is an out-of-class stress test, not a validity test.

| Policy | Promotions / 1,000 | Rate [Wilson 95%] | Mean J | Mean labels |
|---|---:|---:|---:|---:|
| A5b | 176/1000 | 0.176 [0.154, 0.201] | 371.5 | 199.6 |
| D2 | 256/1000 | 0.256 [0.230, 0.284] | 370.4 | 169.7 |
| P1_A5b_c10 | 179/1000 | 0.179 [0.156, 0.204] | 371.6 | 198.4 |
| P1_renew | 54/1000 | 0.054 [0.042, 0.070] | 370.0 | 182.9 |
| P1_union | 44/1000 | 0.044 [0.033, 0.059] | 370.0 | 182.8 |
| P6_LRMD_U | 139/1000 | 0.139 [0.119, 0.162] | 371.2 | 199.6 |
| rmm:gated_deployment+RMM | 250/1000 | 0.250 [0.224, 0.278] | 371.9 | 200.0 |

## Limits

- The hidden-state HMM is outside A5b's declared first-order stationary Markov null.
- Rates describe this fixed generator and do not establish guarantee validity or theorem failure.
- P1_renew additionally assumes i.i.d. observation gaps; this run does not establish that assumption.
