# 12. Theory and validity status

| claim | status | note |
|---|---|---|
| T1. With known query propensity q_t (predictable) the PP increment X_t has conditional mean ≤ 0 under the null "deployed risk ≤ r0+tol" when R̂ is predictable. | PROVED (standard IPW unbiasedness) | requires q_t > 0 and bounded losses |
| T2. Any bet λ_t predictable w.r.t. the resolved-prefix filtration with 1+λ_tX_t ≥ 0.5 makes ∏(1+λX) a nonnegative supermartingale; Ville gives P(sup E ≥ 1/α) ≤ α. | PROVED | only the *negative* support of X matters, giving the tight cap 0.5/|X_min| |
| T3. DK (discounted plug-in moments) and HG (zero bet unless a gate statistic from the same resolved labels is positive) only change λ_t as a function of the resolved prefix. | PROVED (inherits T2) | the fixes cannot break the null guarantee by construction |
| T4. BD query probabilities q_t(x) are functions of the current covariate and the resolved prefix, with matching IPW weight. | PROVED conditional on q_t ≥ floor > 0 | floor was ≥ 0.25×nominal in all runs |
| T5. Validity under label delay d with events usable at s+d. | PROVED for fixed known d | informative/random delay not covered |
| T6. HG strictly improves expected log-wealth growth over the parent. | CONJECTURED | no derivation; empirical only; discounting is biased toward recent increments, so growth is non-stationary-optimal, not provably better |
| T7. Power gain persists under informative delay or dependent labels. | CONJECTURED, UNTESTED | stress tests below not run |

**Empirical validity.** Null false alarm of fixed finalists ≤ .012 (G1) and ≤ .022 (G2) at 400 seeds, well under α=.05. Empirically-thresholded baselines (Page–Hinkley, CUSUM) show .04–.065 on the G2 null and up to .074–.094 on benign worlds, i.e. they have no guarantee.
**Stress tests not run:** random/informative delay, proxy misspecification stronger than G2, heavy dependence, adversarial drift. These are listed for the real-data handoff, not claimed.
