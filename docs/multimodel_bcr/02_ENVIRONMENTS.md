# Environments (code: `scripts/multimodel_bcr/envs.py`)

Each event draws a label y ~ Bern(.5) and an observable context x. Model k is correct with
probability a_k(t, x). Correctness is coupled: with probability ρ=.7 all models share one uniform
draw, otherwise the draws are independent. The contract is T=2000, B=200, delay 100, c_q=.05,
c_s=5, and model 0 is the incumbent. The expected-loss oracle (a dynamic program over K
deployment states with switching cost) is evaluator-side only.

| env | accuracies | tests |
|---|---|---|
| E1_persist | .70 / .76 / .72 | persistent winner |
| E2_late | .72 / .66→.80 @800 / .70 | late improvement |
| E3_reversal | .70 / .78→.62 @1000 / .74 | initially preferred challenger reverses; recovery to a third model |
| E4_specialist | .70 / (.82 x=0, .60 x=1) / (.60, .82); P(x=1) drifts .15→.85 | specialists under covariate shift |
| E5_ambiguous | .70 / .725 / .73 | near-tied challengers |
| E6_null / E6_worse | equal / challengers worse | waste and churn |
| E2_late_K5, E5_ambiguous_K5, E6_null_K5 | K=5 versions | multiple comparisons |

Observed any-disagreement rates are .18–.34.
