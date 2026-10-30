# 02. Null hypotheses and what HG controls

Let F_{t−1} be the resolved-prefix filtration and Z_t the current context (features, prediction p_t).
- **H0-A:** E[X_t | F_{t−1}] ≤ 0 (marginal over Z_t given the past).
- **H0-B:** E[X_t | F_{t−1}, Z_t] ≤ 0 (pointwise over contexts).
- **H0-C:** the deployed model's average risk has not exceeded r0.
H0-B ⇒ H0-A ⇒ (for a stationary stream) H0-C, and H0-C does not imply H0-B: the source stream itself has E[R|Z] varying with Z.

Product ∏(1+λ_tX_t) is a supermartingale when λ_t is predictable and E[λ_tX_t | past] ≤ 0.
- If **λ_t is F_{t−1}-measurable** (the bet does not use Z_t): it follows from H0-A. This covers the *context-free-cap* HG.
- If **λ_t depends on Z_t** (as HG's cap does through ĥ_t and a context-dependent q), it follows only from **H0-B**; under H0-A/C it can fail (counterexample, doc 02_VALIDITY_COUNTEREXAMPLES).
So as implemented HG controls the *conditional-risk* null H0-B, which is stronger than the "no average harm" claim stated in the synthetic reports (doc 12 T2/T3 over-claimed).
