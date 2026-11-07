# Check: Tenzer, Tolochinsky, Romano (ICML 2026) "Semi-Supervised Hypothesis Testing by Betting on Predictions"

Checker run 2026-11-06. Re-read: PMLR v306 camera-ready (`proceedings.mlr.press/v306/tenzer26a.html`, PDF
`raw.githubusercontent.com/mlresearch/v306/main/assets/tenzer26a/tenzer26a.pdf`, pages 120089-120119) and
arXiv 2605.28533v1. Code `elad-tolo/betting_on_predictions`, full SHA
`f99e196b0087128d7ffe0291df9e68042255eae8` (equals `main` HEAD). Read in full this time: `imputed.py`,
`lrt.py`, `simulations.py`, `utils/data_sampler.py` (label-shift sampler), `utils/ada_grad.py`, `algs.py`,
`mains/main_label_shift.py`. Nothing executed.

## Version difference
PMLR and arXiv v1 are word-identical apart from the arXiv stamp (word diff: 5 tokens). CONFIRMED: no change
from the camera-ready. The spec's "camera-ready differences UNVERIFIED" is therefore resolved: none.

## Claim-by-claim
1. Citation, authors (Tenzer*, Tolochinsky*, Romano; Technion), ICML 2026, PMLR 306: CONFIRMED.
2. Problem: P1 (H0 theta_Y = theta_Y^null vs >) and P2 (conditional): CONFIRMED (Sec. 2/3). Identifiability:
   P1 needs fixed P(X|Y) (label shift), P2 needs fixed P(X) (concept shift): CONFIRMED (Sec. 3.2).
   The null must be fully specified and sampleable: CONFIRMED ("we sample additional data from the null",
   Sec. 2.2/3.1).
3. Eq. (1) e = K(A[D,X~]) / E_null[K(.)], K(y) = sum_i exp(gamma y_i): CONFIRMED. **Eq. (2) soft-rank
   statistic** e_breve = (M+1) K(Y0) / (K(Y0) + sum_{i=1}^M K(Yi)): CONFIRMED verbatim in structure; the
   paper itself says it follows the soft-rank e-value construction (needs K order-preserving) and tests
   exchangeability of the observed and M null datasets. Labels of D enter only through the fitted A:
   CONFIRMED (code: `fit_predict(labeled, unlabeled)`).
4. Prop. 3.1 / B.1: valid for ANY A; E[e_breve] = 1 (proof: the M+1 ratios sum to M+1 under exchangeability):
   CONFIRMED. Prop. 3.2 / B.2: E[e_breve_t | F_{t-1}] = 1 with K_t built from history only: CONFIRMED (the main
   text defines conditional e-statistics with "<= 1", the appendix proof states "= 1"). Cor. 3.3 Ville:
   CONFIRMED. Required side-conditions the proof uses and the spec only half-states: the M null datasets
   must be independent of the observed batch and the null labeled sets have the same size n as the observed
   one (code: `n_training` for both).
5. Eq. (3) / Theorem 3.4: P(exists t' <= t: prod e_hat >= 1/alpha) <= alpha + d_TV(P_null^{x t}, P_hat^{x t}),
   needs K strictly positive; the paper calls a general bound on d_TV "an open question": CONFIRMED. Appendix
   B.3 only for binary variables.
6. Sec. 5.2 Eq. (7) convex combination with predictable a_t via Exponentiated Gradient (Kivinen & Warmuth,
   following Waudby-Smith et al. 2025): CONFIRMED. **Gap in the spec**: the EG step size is not in the paper
   text I read; the code default is `eta=0.7`, `eps=1e-12` (simulations.py, `combine_martingales_growth_rate_eg`),
   weights start uniform, update uses the return `w_t . x_t` before the weights are changed (predictable).
7. gamma via AdaGrad (Sec. 5.3), M = 128 (Sec. 5.3; App. F.3 shows power rising with M): CONFIRMED.
   **CORRECTED/COMPLETED on gamma in practice**: `AdaGrad(eta0=1e-4)` (ada_grad.py:29) with
   `eta_t = eta0 / (sqrt(G2) + eps)` gives a step of magnitude <= 1e-4 per round; over 500 steps gamma can move
   at most ~0.05 from its initial value 1 (imputed.py:21). So "gamma tuned by AdaGrad" is, with the shipped
   defaults, essentially gamma ~ 1. That is an inference from reading the update, not an executed result.
   The clip [0.01, 1e6] (imputed.py:122) and the gradient (sum aggregation) = d/dgamma of
   log K_obs - log(K_obs + sum K_null): CONFIRMED by my own algebra (imputed.py:104-112). `agg="prod"`
   gradient (:115-121) is not in the paper and the formula does not match d/dgamma of a log-ratio of
   products; it is only used for an extra baseline curve (simulations.py:224-227).
8. Statistic code: `(M+1)*score/(score + null_scores)` (imputed.py:73), gamma updated AFTER the statistic is
   formed (:39), null datasets sampled fresh each call from `null_sampler` (:48-51): CONFIRMED.
9. **Native learner A in the label-shift experiments (spec: UNVERIFIED)**: `NaiveBayesClassifier(T1, T0)`
   (algs.py:7-18) predicts for each unlabeled x the thresholded indicator `y_hat > T_x` where
   `y_hat = mean(y)` of the labeled batch; T0/T1 are computed from the KNOWN null parameters (data_sampler.py
   :13-24; simulations.py:100-101). So the labels reach the test only through the batch mean of Y, and the
   thresholds use oracle knowledge of P(X|Y). Concept-shift uses `BayesClassifier` (CategoricalNB with a
   random-sampling output, algs.py:21-48).
10. **Simulation harness (spec: not read)**: `simulations.py` generates all sequences from the ALTERNATIVE
    sampler only (`get_e_sequences` draws `alt_sampler`); there is no type-I-error simulation in the shipped
    main scripts. Validity is therefore from the theorems plus the ShiftLab exact-enumeration check, not from
    an author null simulation. Rejection time = first step where the cumulative product exceeds 1/alpha
    (alpha = 0.05, main_label_shift.py:27); n = 15, N in {30, 135}, 500 steps, 500 reps, p_null 0.5, p_alt
    0.52, M = 128: all CONFIRMED (main_label_shift.py:11-35). Concept-shift scripts not opened.
11. LR baselines `lrt.py`: one-sided Bernoulli LR e-values with phat from PRIOR batches only, returning 1
    when phat <= p0 (lrt.py:57-81), `lrt_y_given_x` product of two conditional LRs, `lrt_x` uses labeled plus
    unlabeled x: CONFIRMED. These are the baselines in conv(...), so ShiftLab `tenzer_lrt_*` (Gaussian LR)
    resembles them only in name.
12. PPI comparator Eq. (9)-(10), Prop. E.1: not re-verified line by line (UNVERIFIABLE; ppi.py not read).
13. Power results (Thm 4.1/4.2, binary, threshold or Bayes classifier; F.4 non-monotone failure): headings
    and statements CONFIRMED; proofs not checked.
14. Sec numbers: README labels versus paper sections still unmatched (cosmetic).

## ShiftLab mapping (verified against the repo)
- `src/shiftlab/hgxh2c/baselines.py:177-187` `tenzer(kind, ch)`: CONFIRMED exactly as quoted
  (`imputed` -> `TS(ch, proxy_only=True, factor="lrt", gamma=0.99)`, `frac=0.0`; `lrt`/`ppi` -> `corr` "ipw"/"pp").
- Registration `baselines.py:260-268` with note "DIFFERENT_NULL: Gaussian-LR e-factor / imputed labels" and
  fidelity tag SOURCE_INSPIRED: CONFIRMED.
- `engines.py:343-350` (`proxy_only`: `x = (h_ - r0) * actx`) and `:441-444` (`factor == "lrt"`:
  `logf = (dl*x/v - dl**2/(2*v))*actx`, with `v` the running second moment, `dl` the running mean):
  CONFIRMED. `gamma=0.99` is the engine's moment discount (engines.py:28, :108, :387), unrelated to Tenzer's
  gamma in K: CONFIRMED.
- **The claim that the ShiftLab `tenzer_*` entries are a different statistic: CONFIRMED.** No M null
  resamples, no fit of A on null data, no soft-rank, no K = sum exp(gamma y), no AdaGrad gamma. Correct tier:
  Inspired-by; must not be called Tenzer et al. in tables.
- docs/hgxh2c/01_BASELINE_AUDIT.md:128 says "Not implemented": stale (CONFIRMED stale).

## Fidelity-tier call
T1 only for the authors' own simulations. No faithful reduction exists to the general paired-cost null with
selective, delayed, budgeted labels: the null law must be known and sampleable, identification needs fixed
P(X|Y) or P(X), batch labels are free. The restricted binary T3 slice proposed in the spec is acceptable if
the d_TV term is reported. CONFIRMED.

## Verdict
Spec is accurate on the statistic, validity theorems, M, the repo's non-faithfulness, and the tier. Additions
and corrections: PMLR identical to arXiv; read-in-full code reveals EG eta = 0.7, tiny AdaGrad step so gamma
stays near 1, learner A uses oracle thresholds and only the batch mean of Y, and the harness has no null
simulation.

**ACCEPT WITH CORRECTIONS**
