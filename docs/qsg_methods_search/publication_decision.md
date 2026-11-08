# Contribution status (2026-11-07)

| Contribution | Status | Evidence | Next |
|---|---|---|---|
| C1 Failure Atlas | **PASS (scoped)** | D0 reproduces the M1/M2 frontier: certified methods are 25–40 slower on persistent improvements, and uncertified ones churn for +11–75 on nulls. D0 also reproduces M4 at rho=.8 (QSG .26). New finding: under this contract, alpha=.05 certification costs 20–100 units, while a trivial econ+front rule sits at the delay floor. Shared failure of economic switchers: fixed-margin hysteresis cannot cut null churn without slowing the response to real changes. | merge with Atlas v2 and the other-branch diagnoses |
| C2 Method | **PASS (implementation); novelty PENDING** | EQS-D / EQSDp: discounted disagreement-outcome counts and symmetric remaining-horizon payback switching, with a Beta-posterior-quantile hurdle | targeted prior-art audit: LCB/UCB switching with switching costs, Bayesian optimal switching, Gong–Zhang |
| C3 Synthetic | **PASS (scoped)** | frozen, Holm-adjusted, 100 fresh seeds: arm A −4.8 / −5.7, arm B −8.8 / −9.7 vs tuned Gong–Zhang / Qiu; the ablation isolates the quantile | adversarial review; dependence-regime check; sensitivity to delay and switch cost |
| C4 Real data | **NOT STARTED** | — | eligibility: datasets with an authentic late improvement or reversal of a frozen challenger. The 9 cached Atlas streams are development-exposed. |

Assessment: **continue**. Do not write the paper yet. Run the novelty audit first: it could
reduce C2 to "known rule, new evaluation". Then plan C4.
