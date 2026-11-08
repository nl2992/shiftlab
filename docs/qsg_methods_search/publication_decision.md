# Contribution status (2026-11-07)

| Contribution | Status | Evidence | Next |
|---|---|---|---|
| C1 Failure Atlas | **PASS (scoped)** | D0 reproduces the M1/M2 frontier: certified methods are 25–40 slower on persistent improvements, and uncertified ones churn for +11–75 on nulls. D0 also reproduces M4 at rho=.8 (QSG .26). New finding: under this contract, alpha=.05 certification costs 20–100 units, while a trivial econ+front rule sits at the delay floor. Shared failure of economic switchers: fixed-margin hysteresis cannot cut null churn without slowing the response to real changes. | merge with Atlas v2 and the other-branch diagnoses |
| C2 Method | **PASS (implementation); novelty = NOVEL-INTEGRATION** ([novelty_audit.md](novelty_audit.md)) | EQS-D / EQSDp: discounted disagreement-outcome counts and symmetric remaining-horizon payback switching, with a Beta-posterior-quantile hurdle | closest prior: Regol et al. ICML 2025 UPF (δ-quantile retrain rule; quantile > point estimate already shown there). Must beat the ported UPF-style T3 adapter, Wald/Hoeffding LCB hurdles, scaled margins and a dwell rule on new seeds |
| C3 Synthetic | **PASS (scoped)** | frozen, Holm-adjusted, 100 fresh seeds: arm A −4.8 / −5.7, arm B −8.8 / −9.7 vs tuned Gong–Zhang / Qiu; the ablation isolates the quantile | adversarial review; dependence-regime check; sensitivity to delay and switch cost |
| C4 Real data | **NOT STARTED** | — | eligibility: datasets with an authentic late improvement or reversal of a frozen challenger. The 9 cached Atlas streams are development-exposed. |

Assessment: **continue**. The novelty audit grades C2 as NOVEL-INTEGRATION (no component novelty). Next: the post-confirmation comparator panel (UPF-style, LCB variants, scaled margin, dwell) on new seeds. Plan C4 only if EQSDp survives it.
