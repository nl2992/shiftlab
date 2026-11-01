# Null and validity contracts (v2)
| method | null it targets | guarantee status |
|---|---|---|
| parent / HG / ONS / gated ONS (uniform cap) | Objective A: E[Brier_t | F_{t−1}] ≤ nominal + tol, fixed known delay | PROVED (bets and gate depend on resolved labels only); decision-awareness of the gate is empirical |
| HG with context-dependent cap | pointwise conditional null only | marginal-null claim FALSIFIED (docs/hg_validation/02_*) |
| H2 cost e-processes | Objective B: E[cost_t | F_{t−1}] ≤ nominal cost + tol, fixed known delay | PROVED by the same argument with the cost bound 5/6 (Brier information only picks the bet) |
| H3a baseline ONS | E[Brier_t | F_{t−1}] ≤ r_hat_t + tol (change relative to a predictable recent baseline) | PROVED for that null; it is not the 'no harm vs nominal' null |
| all | strongly dependent covariates with unchanged marginal | no guarantee; empirical false alarms up to .33 |
| all | random / outcome-dependent delay | UNTESTED, no claim |
