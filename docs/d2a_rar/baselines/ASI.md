# Implementation spec — Active Statistical Inference (Zrnic & Candès, ICML 2024, arXiv 2403.03208)

Status: NOT_IMPLEMENTED. Spec by WP1c agent, 2026-11-07. Read: first 100 000 of 151 584 chars of the arXiv HTML.
**Unread:** Appendix assumptions 1–3 (smoothness, Lindeberg), App. C (non-asymptotic / time-uniform results), Secs 8.4–8.5.
Author code: https://github.com/tijana-zrnic/active-inference (URL resolves; contents not inspected — inspect before reimplementing;
prefer AUTHOR_NATIVE for the batch/sequential mean if it runs).

## Problem
X_1..X_n i.i.d.; labels Y_i revealed on request; E[n_lab] ≤ n_b (n_b ≪ n); predictor f black-box; target
θ* = argmin_θ E ℓ_θ(X,Y). Output: point estimate and CI. Not a controller; no actions, no delay.

## Estimators (transcribed)
* Mean, batch: θ̂ = (1/n) Σ_i [ f(X_i) + (Y_i − f(X_i)) ξ_i/π(X_i) ], ξ_i ~ Bernoulli(π(X_i)), π>0 known. Uniform π = n_b/n is PPI.
  Var(θ̂) = (1/n)(Var(Y) + E[(Y−f(X))²(π(X)^{-1} − 1)]).
* M-estimation, batch: θ̂ = argmin_θ (1/n) Σ_i [ ℓ_θ(X_i,f(X_i)) + (ℓ_θ(X_i,Y_i) − ℓ_θ(X_i,f(X_i))) ξ_i/π(X_i) ].
* Sequential mean: Δ_t = f_t(X_t) + (Y_t − f_t(X_t)) ξ_t/π_t(X_t), θ̂ = (1/n)Σ_t Δ_t, with f_t, π_t depending only on data before t.
  Sequential M-estimation analogous with L_t(θ).
* Sampling rule (batch): π_η(x) = η u(x), η̂ = max{η ∈ H : η Σ_i u(X_i) ≤ n_b}; mixture π^{(τ)}(x) = (1−τ)π(x) + τ n_b/n
  (τ = 0.5 in sequential; batch τ tuned on historical data by minimising Σ_i (Y_i^h − f(X_i^h))²/π^{(τ)}(X_i^h)).
* Sequential rule: π_t(x) = clip_{[0,1]}( min{ η_t u_t(x), n_{Δ,t} } ), n_{b,t} = t n_b/n, n_{Δ,t} = n_{b,t} − n_{lab,t−1}; occasionally π_t = clip(n_{Δ,t}) to use the budget (frequency: UNVERIFIED).
* Uncertainty u: regression — trained model of |f(X) − Y|; classification — u(x) = K/(K−1)·(1 − max_i p_i(x)), binary u = 2 min{p, 1−p}.
* Oracle rule: π_opt(x) ∝ √E[(Y−f(X))² | X=x] (mean); M-estimation: ∝ √E[((∇ℓ(X,Y) − ∇ℓ(X,f(X)))ᵀ h^{(j)})² | X] with h^{(j)} column j of H^{-1}.
* Variance estimators: empirical plug-in (exact form in appendix, UNVERIFIED).

## Guarantees to carry (and not over-claim)
Asymptotic only in the read text: √n(θ̂ − θ*) → N(0,Σ*), CI θ̂ ± z_{1−α/2} σ̂/√n has asymptotic coverage 1−α (Props 1–2, Thms 1–2),
conditional on smoothness, Lindeberg and variance-convergence conditions. A time-uniform/non-asymptotic analogue exists per the paper (App. C) but **was not read**:
until read, an ASI-based monitor is *not* an anytime-valid test. Unbiasedness of Δ_t requires π_t predictable and strictly positive (propensity logged).

## Streaming variant for ShiftLab (design, NOT in the paper)
* Item stream x_t with predictor f_t (the deployed model's loss predictor or a surrogate); estimand = running risk or a paired cost difference d_t;
  propensity π_t from the host's budget pacer; IPW-corrected increments Δ_t as above; plug into an anytime-valid confidence sequence / e-process
  (ShiftLab's PPI e-process adapters in `sota_search/published_baselines.py` on `origin/codex/sprint2-leaderboards`). Release/delay: the increment for item t is
  only usable at its release time; π_t must be fixed (logged) at request time, not release time. Mark as `ASI-inspired`, tier CONCEPTUAL_PROXY, until the time-uniform theorem is read.
* Cap π_t ≥ π_min to bound the IPW range (needed for boundedness-based sequences); document the induced bias/validity trade.

## Native reproduction targets (Suite A)
α = 0.1; batch 1000 trials, sequential 100; coverage and mean CI width vs n_b (log–log); "budget saved" = (n_b − n_b^active)/n_b to match baseline width.
Reported (from text): Pew 2020 Biden >85 % vs classical, ≈25 % vs uniform; Trump >70 %/≈25 %; ACS PUMS CA 2019 age coefficient ≈80 %/>60 %; AlphaFold odds ratio >75 % vs classical.
Data: Pew, folktables ACS, Angelopoulos et al. AlphaFold — **not fetched**; prefer a synthetic mean-estimation check first (known truth), then the author repo's data loaders if present.

## Tests
IPW unbiasedness over ξ (MC), coverage ≈ 1−α for the batch mean on a synthetic problem with a deliberately bad f, uniform π recovers PPI variance,
budget E[n_lab] ≤ n_b (sequential, pathwise cap via n_{Δ,t}), CI width ordering active ≤ uniform ≤ classical when f is informative, π>0 on support.
