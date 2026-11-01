# 01. HG algorithm specification (reconstructed from `detectors.pp_fix`)

Per stream step t with deployed probability p_t, decision a_t = 1{p_t ≥ τ}, τ = 1/6, label query Q_t ~ Bernoulli(q) (q = label fraction, predictable, independent of the outcome), delay d.

**Proxy risks (pre-outcome, functions of p_t):** Brier ĥ_t = p_t(1−p_t); cost ĥ^c_t = a_t(1−p_t)·FP + (1−a_t)p_t·FN.
**Increments:** X_t = ĥ_t + (Q_t/q)(R_t − ĥ_t) − r0 − tol (Brier loss R_t = (y−p)²), X^c_t the same with cost loss and cost proxy; r0 = nominal source risk.
**Resolution:** the label of step s is usable from time s+d (events s ≤ t−d).
**Discounted moments (γ=0.99):** m_t = Σ_{s≤t−d−1} γ^{t−d−1−s} X_s / (n_t+1), v_t likewise with X², n_t = Σ γ^{·}. Plug-in bet λ^disc_t = clip(max(m_t,0)/v_t, 0, cap/B_t) with cap = 0.5 and one-sided bound B_t = ĥ_t(1/q −1)+r0+tol (minimum of −X_t is attained at R=0 with Q=1... the bound is on |negative part|).
**Gate (w=100, γ_g = 1−1/w):** g_t = 1{ mean_discounted(X^c_s, s ≤ t−d−1) > 0 }, built from the same resolved labels.
**Wealth and alarm:** λ_t = λ^disc_t · g_t, log E_t = Σ_{s≤t−d} log(1+λ_s X_s), alarm at first t with log E_t ≥ log(1/α), α = .05. The bet λ_s uses only labels resolved by time s (indices ≤ s−d−1) and the *current* p_s (through B_s and through X_s's proxy).

**Parent:** `pprm_tight` = γ=1, no gate, same bound. Equality when γ=1, gate off is unit-tested (`test_detectors.py`).
**Timing audit:** λ_s uses (i) resolved labels ≤ s−d−1, (ii) the current prediction p_s through the cap B_s. Item (ii) is current-context information, so λ_s is *not* F_{s−1}-measurable. This is the validity issue examined in doc 02.
**Dependency-free reference:** `scripts/sota_search/exact_null_tests.py` re-implements the capped bet in plain NumPy for the toy exact checks; a full standalone HG re-implementation remains to be written (not done; listed in open items).
