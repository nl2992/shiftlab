# 02. Revised guarantee table

| claim | status |
|---|---|
| HG (context-dependent cap) is an e-process under H0-B (pointwise conditional risk ≤ r0+tol), fixed known delay | PROVED (λ_t measurable w.r.t. F_{t−1}∨σ(Z_t), E[X|·] ≤ 0, 1+λX ≥ 0.5) |
| HG (context-dependent cap) is an e-process under the marginal no-harm null H0-A/H0-C | **FALSIFIED** (exact counterexample, doc 02_VALIDITY_COUNTEREXAMPLES) |
| HG with the uniform support cap (`uniform_cap=True`) is an e-process under H0-A (E[R_t|F_{t−1}] ≤ r0+tol) with q predictable and context-free, fixed known delay, bounded losses | PROVED: λ_t ∈ F_{t−1}, E[λ_tX_t|F_{t−1}] = λ_t(E[R_t|F_{t−1}] − r0 − tol) ≤ 0, 1+λX ≥ 0.5; Ville |
| same under random independent delay, outcome-dependent delay, dependence beyond H0-A | CONJECTURED / UNTESTED (stress generators G6 not built) |
| Gate and discount preserve validity | PROVED when they use resolved labels only (they do) |
| BD (context-dependent q) | CONDITIONAL: needs the cap built from q_min |
