# Implementation spec — Active Statistical Inference (Zrnic & Candès, ICML 2024, arXiv 2403.03208)

Status: NOT_IMPLEMENTED. Spec by WP1c agent, 2026-11-07. Read: first 100 000 of 151 584 chars of the arXiv HTML.

**UPDATE 2026-11-07 (WP1d): status IMPLEMENTED for the MEAN; tier `PAPER_RECONSTRUCTION` (batch + sequential native) and `COMMON_CONTRACT_PORT` (streaming monitor).** Code `src/shiftlab/sota/asi/`,
tests `tests/d2a_rar/test_asi.py`, port `src/shiftlab/bench/contract/adapters_asi.py`. The 'Status' line above is superseded WP1c text.
**Reading coverage (WP1d):** full arXiv PDF text layer (main text Secs 1-8, App. A proofs and Assumptions 1-3, App. C non-asymptotic extension). Waudby-Smith & Ramdas (arXiv 2010.09686) Thm 2 / Eqs. 13-15 also read for the streaming CS. Author code: not read, not run.
Resolved: sequential rule is Eq. (8) with eta_t = n_b / (n Ehat[u_t]) and tau = 0.5; the variance estimator is the empirical variance of the increments (paper text); the Lindeberg condition is Ass. 2 (sequential mean); App. C is only a SHORT statement (bounded increments with pi_t >= tau n_b/n, then apply betting CSs of WSR / Orabona-Jun), no new theorem; the frequency of the occasional budget-fill rounds is not specified anywhere (our `fill_every` is a design parameter).
Not implemented: general M-estimation, GLM rules, the Pew / ACS / AlphaFold reproductions (data not fetched).
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

---

## Implementation and reproduction record (WP1d, 2026-11-07)

### Tiers
* `src/shiftlab/sota/asi/active.py`: **`PAPER_RECONSTRUCTION`** (Eq. 4 budget scaling, mixture rule, Eq. 12 tau tuning, Eq. 5/7 IPW increments, Wald CI, oracle rule, uncertainty measures Eq. 3, sequential rule Eq. 8).
* `src/shiftlab/sota/asi/streaming.py` + `adapters_asi.py`: **`COMMON_CONTRACT_PORT`**, ASI-inspired. NOT a result of the paper.

### Conditions of the native guarantees (asymptotic only)
Batch (Prop 1): i.i.d. (X_i, Y_i); known pi > 0; f fixed; P(eta_hat = eta*) -> 1. Sequential (Prop 2): f_t, pi_t F_{t-1}-measurable (given X_t),
(1/n) sum sigma_t^2 -> sigma^2 in probability, Lindeberg (Ass. 2). Conclusion: asymptotic coverage 1 - alpha. Nothing finite-sample or time-uniform is claimed for the Wald CI.

### Streaming COMMON_CONTRACT_PORT: assumptions and provenance
From WSR (read): PrPl-EB process and two-sided CS for [0,1]-valued data with common conditional mean. From ASI App. C: bounded IPW increments if pi >= pi_min.
**Ours, not stated in either paper:** (i) one-sided use under a CONDITIONAL null E[d_t | past] <= h (the supermartingale argument needs only E[X_t - m | past] <= 0 for lambda >= 0); (ii) affine rescaling by the range implied by pi_min; (iii) in-order consumption of increments under delayed labels.
Required: losses in [0,1]; pi_t >= pi_min fixed at request time; xi_t drawn from the declared propensity independently of d_t given the past; f_t built only from labels released before the request. The two-sided CS is for a CONSTANT conditional mean and loses its meaning under drift (only the one-sided conditional-null test remains).
The IPW range ~ 1/pi_min makes the evidence conservative (null alarm rate 0 in the tests below). Validity of (i)-(iii) has Monte Carlo support only, no proof here.

### Reproduction vs paper (CPU, synthetic; the paper's real-data experiments are NOT reproduced)
| Item | Paper | Here | Status |
|---|---|---|---|
| IPW unbiasedness over xi | Sec 3 | MC 6000 draws, abs(mean - Ybar) < 4 SE | MATCH |
| Batch CI coverage, alpha=.1 | ~ nominal | n=3000, n_b=300, 500 trials: active 0.932, uniform-PPI 0.914, classical 0.914 | CONSISTENT (asymptotic; MC error ~0.013) |
| Mean CI width | active < PPI < classical | 0.0841 < 0.0890 < 0.0950 (binary classifier, noise .05) | ORDER MATCHES; effect small (-5.5% vs PPI, -11.5% vs classical) |
| Uniform pi recovers PPI variance | (1/n)(Var(Y)+E[(Y-f)^2](1/p-1)) | within 12% relative (finite-population variant) | MATCH |
| Oracle pi proportional to sqrt(E[(Y-f)^2 given X]) | Sec 7.1 | variance proxy below uniform and below pi proportional to g | MATCH |
| Sequential CI coverage, tau=.5 | Prop 2 | n=1500, n_b=150, 400 trials: coverage in [0.84, 0.96]; E[n_lab] <= 1.1 n_b | CONSISTENT |
| Streaming CS (WSR Thm 2) miscoverage over horizon 300, alpha=.1 | <= alpha | within alpha + 3 SE (400 trials) | CONSISTENT |
| Streaming one-sided alarm under conditional null with drift + random delays | (ours) | 0 / 300 alarms (alpha=.1); power test passes at mean gain .5 | VALID, very conservative |
| Budget savings vs classical on Pew / ACS / AlphaFold | Sec 8 | NOT reproduced (data not fetched) | NOT REPRODUCED |

n_b is an expected budget, not a pathwise cap: the sequential rule keeps E[n_lab] ~ n_b via n_{Delta,t}, while the tau-mixture adds at most tau n_b/n per round.
