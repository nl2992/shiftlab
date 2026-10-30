# 04. Estimand and validity contract

Three quantities are kept separate (AGENTS.md): distribution shift `D(P_t,P_0)`; predictive degradation
`R_t(f)−R_0(f)`; decision harm `R_t(π_t)−R_t(π_ref)`. Everything below concerns **decision-cost harm of a frozen
incumbent against its nominal cost** — i.e. a *monitoring* null, not a promotion test.

## H2c / cost-null e-process (the object audited)
* Data: events `t = 1,2,…`, decision `a_t = 1[p_t ≥ 1/6]`, cost `L_t = a_t(1−y_t)·1 + (1−a_t)y_t·5 ∈ [0,5]`.
* Label query `Q_t ~ Bernoulli(q)` independent of `y_t` given the past and covariates; known `q` (so IPW is unbiased).
  Label released after a fixed delay `d`. Filtration `F_{s}` contains events and labels **released** by s.
* PP-IPW increment `X_t = ĉ_t + (Q_t/q)(L_t − ĉ_t) − r_0 − ε`, `ĉ_t` = proxy cost computed from `p_t`.
* **Null (conditional, per-step):** `E[L_t | F_{t−1}^{event}] ≤ r_0 + ε` for all t, with `r_0` the **nominal cost**.
  This is stronger than a stationary-average risk null and is not implied by the average-risk null.
* Bets: `λ_t` predictable w.r.t. the resolved past, `λ_t ∈ [0, cap/B_t]` with `B_t` a context-free support bound
  (uniform cap `(5/6)(1/q−1)+r_0+ε`) ⇒ `1+λ_t X_t ≥ 1−cap > 0` ⇒ product of factors is a nonnegative supermartingale ⇒ Ville: `P(∃t W_t ≥ 1/α) ≤ α` **for any predictable λ, including Brier-guided λ**.
* Known `r_0` assumed in the original studies; here `r_0` is replaced by `U_0` with `P(R_0 ≤ U_0) ≥ 1−δ_S`, alarm threshold `1/α_T`, total error `δ_S + α_T` (the Podkopaev–Ramdas allocation; Prop. 1 there).

## What is **not** guaranteed
* ARL vs finite-horizon error: e-detector guarantees (SR at `1/α`) are ARL statements; I use **horizon** Ville thresholds.
* Outcome-dependent delays/missing labels: validity shown by repo only for fixed or outcome-independent delay.
* Dependence: valid under the **conditional** null even for dependent processes; a persistent process that violates the conditional null while satisfying a stationary-average null can exceed α — that is a *null-class mismatch*, not an invalidity of the method (task rule; `dependence_sprint/03`).
* Covariate-dependent querying or covariate-dependent caps: invalid for the marginal null (HG counterexample, repaired by uniform cap).
* Real data: no conditional null can be verified. D2 uses the **exchangeable-by-construction** stream A only to exercise calibration + e-process; stream B has no defined null.

## Matching rules adopted for every comparison in 07
Same stream, proxy, label mask (one seed per cell shared by all arms), delay (5 events), calibration set, `δ_S=0.01`, `α_T=0.04`, tolerance `ε`, horizon Ville threshold `ln 25`. Brier-null methods are **not** compared with cost-null methods on power.
