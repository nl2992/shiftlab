# 06. Null validity under temporally dependent covariates (partial G6)
AR(1) covariates with stationary N(0,1) marginal (so the *marginal* risk is exactly the nominal r0 but the conditional risk given the past is not), no shift, 400 seeds, T=2000, α=.05, theory threshold, delay 5. Source: `outputs/hg_validation/06_DEPENDENCE_NULL.json`. Null false-alarm rate (G1 / G2 deployed-model families):

| ρ | labels | parent | HG ctx-cap | HG unif-cap | ONS |
|---|---|---|---|---|---|
| 0 | 10% | .013 / .015 | .013 / .015 | .013 / .015 | .035 / .037 |
| 0.9 | 10% | .028 / .025 | .020 / .018 | .020 / .015 | .030 / .045 |
| 0.9 | 20% | .020 / .025 | .028 / .040 | .030 / .035 | **.072** / .068 |
| 0.98 | 10% | **.077** / .062 | **.117** / .113 | **.125** / .122 | **.177** / .180 |
| 0.98 | 20% | **.170** / .138 | **.273** / .275 | **.295** / .287 | **.360** / .323 |

**Findings.**
1. With moderate dependence (ρ ≤ 0.9) every method stays at or below .05 except ONS at 20% labels (.07).
2. With strong dependence (ρ = 0.98) **all** e-process variants, including the undiscounted parent, exceed α (up to .36). This is the expected failure of H0-A: when the covariates are slowly varying, the conditional risk given the resolved past differs from r0 for long stretches, so the plug-in bet is positively correlated with the increment.
3. **Discounting + gating makes it worse than the parent** (.27–.30 vs .17 at 20% labels): shorter memory tracks the local conditional-risk drift. The uniform-cap repair does not fix this, because the repaired theorem needs E[R_t | F_{t−1}] ≤ r0, which strong dependence violates.
4. Therefore HG's validity claim must be stated as: valid under H0-A (conditional-on-the-past risk ≤ nominal) with fixed known delay; **not** valid, and more fragile than its parent, under strongly dependent streams. Not tested: random and outcome-dependent delay, clustered outcomes, adversarial proxy shifts (G5), query-budget exhaustion.
