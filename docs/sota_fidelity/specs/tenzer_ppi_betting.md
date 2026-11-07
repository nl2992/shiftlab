# Spec: Tenzer, Tolochinsky, Romano, "Semi-Supervised Hypothesis Testing by Betting on Predictions" (ICML 2026)

Retrieved 2026-11-06 by subagent. Tags: **[READ]** read directly this session; **[DERIVED]** my own
algebra from read material; **[REPO]** taken from existing ShiftLab text; **UNVERIFIED** not read.

## 1. Citation, version, code

- Yaniv Tenzer*, Elad Tolochinsky*, Yaniv Romano (Technion). Title confirmed from the PDF header:
  "Semi-Supervised Hypothesis Testing by Betting on Predictions". Proceedings footer: ICML 2026, Seoul,
  PMLR 306. ICML poster page icml.cc/virtual/2026/poster/63574 (found by search; not read).
- **Version read:** arXiv 2605.28533v1 (27 May 2026), 31 pages, pdftotext of the full PDF
  (`.../scratchpad/msel/tz_paper/tz.pdf`), main text pp.1-9, appendices A-G. Camera-ready/PMLR version not
  fetched; differences UNVERIFIED. Page numbers are arXiv v1 printed pages.
- **Official code:** https://github.com/elad-tolo/betting_on_predictions (link in the paper, p.2, [READ]),
  default branch `main`, HEAD `f99e196b0087128d7ffe0291df9e68042255eae8` (committed 2026-05-25T22:38:10Z,
  i.e. HEAD today). Same SHA used by ShiftLab docs [REPO]. I fetched at that SHA (not executed):
  `sequential_tests/imputed.py`, `utils/ada_grad.py`, `mains/main_label_shift.py`, `sequential_tests/ppi.py`,
  `README.md`. NOT read: `lrt.py`, `simulations.py`, `utils/data_sampler.py`, `algs.py`, the other mains.
  Repo ships data (parquet) and a plotting notebook; I did not open them.

## 2. Native problem and estimand

Sec. 1 pp.1-2, Sec. 3 [READ]. At each step t the tester receives a batch of n i.i.d. labeled pairs
D_t = {(X_i, Y_i)} and N i.i.d. unlabeled X~_t; X is cheap, Y expensive. Two hypothesis tests:
- (P1) H0: theta_Y = theta_Y^null vs H1: theta_Y > theta_Y^null (a parameter of the Y marginal).
- (P2) H0: theta_{Y|X=x} = theta^null_{Y|X=x} for all x vs H1: > for at least one x (conditional).
Identification, Sec. 3.2 p.3 [READ]: P1 is testable only under **label shift** (P_{X|Y} fixed between null and
data); P2 only under **concept shift** (P_X fixed). Appendices C, D extend to composite nulls for binary X, Y
(not read in detail; UNVERIFIED).
- Anytime validity via e-processes and Ville (Sec. 2.1 p.2). Null needs the ability to **sample from P^null(D, X~)**
  (the joint law of labeled and unlabeled data under the null, p.3 "we sample additional data from the null").
- Feedback: all n labels in every batch are observed at once; no delay, no label cost, no budget, no choice
  of which Y to buy, no deployment action.

## 3. Exact algorithm

Batch statistic, Sec. 3.1 p.3 [READ]. Fit a learning algorithm A on labeled data D, predict the N unlabeled
points: A[D, X~] = (A[D,X~_1], ..., A[D,X~_N]).
- **Eq. (1):** e[D, X~] = K(A[D,X~]) / E_{P^null(D,X~)}[K(A[D,X~])], K: R^N -> R_+ nonnegative. In experiments
  K(y~) = sum_{i=1}^N exp(gamma * y~_i), gamma >= 0 a hyperparameter.
- **Eq. (2)** (the expectation in (1) is replaced by M independent null datasets (D^i, X~^i), i=1..M,
  with (D^0, X~^0) the observed data and Y~^i = A[D^i, X~^i]):
  e_breve[D, X~] = (M+1) K(Y~^0) / ( K(Y~^0) + sum_{i=1}^M K(Y~^i) ).
  This is a soft-rank e-value (Ramdas & Wang) when K preserves order; it tests exchangeability of observed
  and null-resampled datasets. Note the observed Y labels enter ONLY through the fitted model A[D, .]; the
  unlabeled predictions are the "bets".
- **Prop. 3.1 (formal: Prop. B.1, p.12):** e_breve is a valid e-statistic for P1 (label shift) and P2
  (concept shift), E_H0 = 1, for ANY algorithm A, any accuracy, any n, N. Proof idea [READ]: under H0 the M+1
  datasets are exchangeable and the M+1 ratios sum to M+1.
Sequential version, Sec. 3.3 p.4 [READ]. At step t draw M fresh null datasets, fit A on each, form
e_breve[D_t, X~_t] as in (2) but with K_t chosen from history D_{-t} only (e.g. gamma_t tuned online).
**Prop. 3.2** (Prop. B.2 p.12): conditional e-statistic, E_H0[e_breve_t | F_{t-1}] = 1. The product
S_t = prod_{i<=t} e_breve_i is an e-process; **Corollary 3.3:** P_H0(exists t: S_t > 1/alpha) <= alpha (Ville).
Approximate null, Sec. 3.4 p.4: if the true null law is replaced by an estimate P-hat_t^null, the statistic
is e-hat = K(Y~_t)/E_{P-hat}[K(Y~_t)] (Eq. 3) and **Theorem 3.4**: P(exists t'<=t: prod e-hat >= 1/alpha) <=
alpha + d_TV(P^null_{xt}, P-hat^null_{xt}) (proof Appendix B.2 p.13 using Ville on the P-hat measure).
Unified e-process, Sec. 5.2 p.6 [READ]: **Eq. (7)** conv(e_1,t..e_k,t; a_t) = sum_i a_{t,i} e_{i,t}, a_t in
the simplex, predictable, set by Exponentiated Gradient (Kivinen & Warmuth), following Waudby-Smith et al.
Baselines combined: likelihood-ratio e-processes e_LR^Y, e_LR^X, e_LR^{Y|X} (Wasserman et al.) and the PPI
test (Appendix E). The headline claims are about this convex combination, not the imputed process alone.

**Betting strategy.** There is no classical lambda_t wealth bet on the imputed statistic. The only learned
"bet" is gamma_t in K (Sec. 5.3 p.6: set "to optimize the e-power ... using online learning; specifically,
AdaGrad"). The wealth process is the product S_t; the cross-statistic bet is the EG weight a_t. The
comparator PPI test (Appendix E.1 p.25, **Eq. (9)**): e_PPI = 1 + lambda_t (w_t - theta^null), lambda_t in
[-1/2, 1/2], w_t = Y_t + eps_t (mean of f-hat over unlabeled - f-hat(X_t)) (the printed sum over X~_t / N
is as in text), eps_t from variance minimisation (Eq. 10), lambda_t by Online Newton Step; **Prop. E.1** valid
for H0(P1). One-sided variant: force lambda_t >= 0 (E.3).

Power (Sec. 4, pp.5; Appendix B.4-B.5) [READ headings; proofs NOT checked line by line]: for binary X, Y with
threshold classifier A_tau (Eq. 4-5) under label shift, **Theorem 4.1** (formal B.4): e, e_breve and the
conditional e_breve have non-trivial power E_alt[e] > 1 against H1(P1) (assumes P(X=1|Y=0) < P(X=1|Y=1));
with the Bayes-sampling classifier (Eq. 6) under concept shift, **Theorem 4.2** (formal B.7) power against the
right-shifted subset H1(P2+). Appendix F.4 shows the test does not work against a non-monotone alternative.

Code mapping [READ, imputed.py @f99e196]:
```
Imputed.__init__: gamma=1 (l.21), AdaGrad(weight=gamma) (l.23)           # initial gamma = 1, not stated in paper text I read
calc(): M null datasets -> scores (get_score_of_null_datasets l.43-61: each = fit alg on a fresh null_sampler
        .sample(n_training), predict on null_sampler.sample_x(n_test), score = sum_i exp(gamma*pred_i))
        statistic = (M+1)*score/(score + sum null scores)   (l.73)  == Eq. (2) with agg="sum"
        then update_gamma(...) AFTER the statistic is formed (l.39) == predictable gamma
calc_psi: exp(gamma*preds) (l.98-99)  == K(y~)=sum exp(gamma y~_i)
update_gamma: ascent step on grad_L (l.109-112) = d/dgamma [log K_obs - log(K_obs+sum K_null)] (my algebra,
        [DERIVED], sum aggregation, binary preds), AdaGrad step eta0=1e-4, clip gamma in [0.01, 1e6]
        (ada_grad.py:29,39-59; imputed.py:122)
agg="prod" option (l.85, 115-121): not in the paper text I read.
```

## 4. Hyperparameters and defaults used in the paper's experiments

[READ unless stated]: M = 128 null datasets (Sec. 5.3 p.6; Appendix F.3 p.28 shows power rises with M, small
gain beyond M>32); K(y~)=sum exp(gamma y~_i); gamma_t by AdaGrad; alpha = 0.05 (code main_label_shift.py:27);
label-shift simulations: n = 15 labeled, N in {30, 135} unlabeled, 500 steps, 500 realizations
(Sec. 5.3; code l.23-35), theta_Y^null = 0.5, alt 0.52; low correlation P(X=1|Y=0)=.35, P(X=1|Y=1)=.65, high
.2/.9 (Appendix F.1). Concept shift: N = 135, theta_{Y|X=0}=.4, theta_{Y|X=1}=.7 (low) or .2/.85 (high),
theta_X=.5, alt = +0.02 each (Appendix F.2). LLM evaluation (Sec. 6): Llama3.1-8B vs Qwen2.5-7B distilled from
DeepSeek-R1, Qwen2.5-14B for synthetic answers, GSM8K/MATH/AQUA-RAT, concept-shift n=10, N=90. Learners:
Naive-Bayes/Bayes classifiers (README: `algs.py` NB, Bayes, TabPFN; `algs.py` NOT read, UNVERIFIED).
Not in the paper text I read but in code: gamma_0 = 1, AdaGrad eta0 = 1e-4, eps = 1e-8, gamma clip [0.01,1e6].
Caption inconsistencies (cosmetic): Fig. 6 caption says N=35 and swaps "high (0.3)" / "low (0.7)" correlations.

## 5. Guarantee

Corollary 3.3 (p.4) with Prop. 3.1/3.2: finite-sample anytime type-I control **if** (i) label shift (P1) or
concept shift (P2) holds, (ii) the null law P^null(D, X~) is known exactly and can be sampled independently
of the observed batch, (iii) batches are i.i.d. across the stream under H0 and the K_t / a_t / gamma_t are
predictable, (iv) K > 0. Valid regardless of A's accuracy. With an estimated null: Theorem 3.4 adds the
total-variation term d_TV between the true and estimated joint null laws over the whole stream; the paper says
a general bound on that excess rejection is an open question (p.4) and only argues it can be small for binary
variables with enough null samples (Appendix B.3, Theorem B.3, not read in detail). Not covered: hypotheses
about excess cost between two policies, adaptive/selective labeling, delay, label budgets, distribution
shift of nuisance parts (X|Y or X moving breaks the identification premises), power for non-binary X or Y
(power theory is binary only), and power against non-monotone alternatives (F.4). The existing ShiftLab
counterexample (wrong simulator, expected factor 5848/4375) is consistent with, not contradicting, the paper
[REPO: docs/exhaustive_evaluation/PREDICTION_BETTING_APPLICABILITY.md; I did not re-run it].

## 6. Mapping to ShiftLab's deployment contract

Contract: two frozen models, per-round paired loss, hard label budget B=200 over T=2000, c_q=0.05, c_s=5,
delayed labels. The native problem differs on every axis: (a) the null must be a samplable law of (X, Y) with
fixed X|Y or fixed X; ShiftLab's null is a conditional-mean paired-loss inequality with arbitrary context
drift; (b) native batches deliver n labels every round for free; ShiftLab buys at most 200 single labels with
propensities; (c) native has no deployment decision, no switching, no delay; (d) the test statistic does not
use the unlabeled values of Y at all, whereas ShiftLab's decision hinges on labeled paired loss.
- **Achievable tier:** T1 for the authors' own simulations (code pinned, ShiftLab reproduced a reduced run:
  PARTIAL [REPO docs/hgxh2c/02_NATIVE_REPRODUCTION.md section 1]). **T3 at best, and only in a restricted
  slice** (binary candidate-vs-incumbent correctness Y, a cheap proxy X, a known/estimated source law
  providing P^null, label shift or concept shift verified by construction) with the null-estimation error
  term of Theorem 3.4 reported. In the general chronological paired-cost contract there is no valid reduction
  [REPO conclusion EXCLUDED_UNCHANGED_NULL_AND_SAMPLING_CONTRACT; consistent with my reading]. The PPI
  comparator (Eq. 9) is the more transplantable component (bounded-mean, predictable lambda_t, eps_t), T2/T3
  after replacing w_t by a prediction-powered excess-cost estimate with propensity handling.
- Deviations that any T3 version must list: switch from batch n/N to single-event labels under B and
  c_q; delay handled by acting only on released outcomes; M-resample cost (M fits per step) counted as compute;
  no deployment/switch policy defined by the paper; null-law estimation uncertainty.

## 7. Existing ShiftLab code

`src/shiftlab/hgxh2c/baselines.py:177-187` `tenzer(kind, ch)`: `imputed` = `Monitor([TS(ch, proxy_only=True,
factor="lrt", gamma=0.99)], frac=0.0)`; `lrt`/`ppi` = `TS(ch, factor="lrt", corr="ipw"|"pp", gamma=0.99)`.
Registered at baselines.py:260-268 as `tenzer_{imputed,lrt,ppi}_{B,C}` with note "SOURCE_INSPIRED /
DIFFERENT_NULL: Gaussian-LR e-factor / imputed labels". Engine: `src/shiftlab/hgxh2c/engines.py:343-350`
(proxy_only treats the proxy prediction as the label: `x = (h_ - r0) * actx`) and :441-444 (`factor == "lrt"`:
`logf = dl*x/v - dl**2/(2*v)`, a Gaussian likelihood-ratio e-factor with running mean/second moment) [READ].
Discrepancies versus the paper (all material):
1. No Eq. (2) rank statistic, no M null resamples, no fit of A on null data, no K = sum exp(gamma y~), no
   gamma_t AdaGrad. The `imputed` entry is "proxy as label + Gaussian LR", a different statistic.
2. Null is the paired-excess-cost non-improvement null, not P1/P2 (hence DIFFERENT_NULL).
3. `gamma=0.99` in `TS` is a discount factor of the ShiftLab engine, unrelated to Tenzer's gamma in K.
4. The `lrt` entries correspond (loosely) to the paper's LR baselines, not to its method.
The authors' actual `imputed.py`/`ppi.py` have been executed inside ShiftLab docs: docs/hgxh2c/02 section 1
(reduced reps 10 and 4 vs 500; imputed gain claim UNRESOLVED) and an exact component check (zero numerical
difference to `calc_statistic_finite_sample` over 9 distribution pairs, M=3) in
docs/exhaustive_evaluation/PREDICTION_BETTING_APPLICABILITY.md [REPO, scripts not re-run]. docs/hgxh2c/01
BASELINE_AUDIT.md:128 still says "Not implemented" (stale relative to the entries above).

**Current honest tier:** `tenzer_imputed_*` / `tenzer_ppi_*` / `tenzer_lrt_*` = **Inspired-by**. They must not
be called Tenzer et al. in result tables. The registry already says SOURCE_INSPIRED. Author-code harness runs
(not in any comparator pool) = T1 for the paper's own setting.

## 8. Paper-stated numbers or identities usable as tests

- E[e_breve] = 1 under exchangeable null for any K>0, any M: exact enumeration (the repo check already does
  M=3, 16 score combinations; ShiftLab file `check_prediction_betting.py` cited in the docs [REPO]).
- The M+1 per-dataset ratios sum to M+1 (proof of Prop. B.1).
- Eq. (2) numerical equality with `calc_statistic_finite_sample` (imputed.py:73).
- Power curves in Figs. 1, 2, 5, 6 are plots only; the paper has no tabulated powers (docs/hgxh2c confirms
  [REPO]). Reproducible quantities: the simulation configs (Sec. 5.3-5.5, App. F) and that adding the imputed
  process to the convex combination raises power at N=30 and low correlation.
- Expected-factor counterexample 5848/4375 (wrong-simulator) is a ShiftLab-derived check, not a paper number.

## 9. Open questions / UNVERIFIED

- Camera-ready differences; Appendices C, D (composite nulls) and B.3-B.5 proofs not read line by line.
- `lrt.py`, `simulations.py`, `data_sampler.py`, `algs.py` not read: the null samplers, how A is fit
  (`n_training` vs the paper's n), and the exact EG settings for Eq. (7) are UNVERIFIED.
- Whether gamma is updated using batch t's data before use at t+1 in every code path (looks so in imputed.py
  l.39 and l.122, but only for the `Imputed` class).
- README section labels ("Section 7", "6.3") were not matched against the full arXiv v1 section list; treat them as UNVERIFIED.
- No experiment was run by me.
