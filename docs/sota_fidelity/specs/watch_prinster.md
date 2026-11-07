# Spec: WATCH (Prinster, Han, Liu, Saria; ICML 2025)

Status: retrieval spec, step 1 of the fidelity workflow. Not yet independently checked (step 2).
Retrieved 2026-11-06. Every claim carries a page/equation (paper) or file:line (code) locator.
Anything not read directly is marked UNVERIFIED. Nothing was executed.

## 1. Citation, version read, code

- D. Prinster, X. Han, A. Liu, S. Saria, "WATCH: Adaptive Monitoring for AI Deployments via
  Weighted-Conformal Martingales", ICML 2025, PMLR 267 (title page, p.1). Acronym expansion:
  Weighted Adaptive Testing for Changepoint Hypotheses (p.2).
- Version read: arXiv 2505.04608 **v4** (25 Aug 2025), 30 pages, from
  https://arxiv.org/pdf/2505.04608v4. Pages cited as printed footer numbers (= PDF pages).
  The PMLR proceedings PDF (PMLR 267, pp. 49830-49859 per a search index entry, UNVERIFIED)
  was NOT read; v4 vs proceedings text differences are UNVERIFIED.
- Official code: the paper itself names https://github.com/aaronhan223/watch (p.7, Experiments
  section, "Code to reproduce all experiments"). Owner is coauthor Xing Han. There is no repo
  under github.com/drewprinster for WATCH (listed his repos: jaws, jaws-x, conformal-mfcs only).
  **Pinned SHA: `3d17fca58ac60410d020b54dee19ee3fc4ec29c2`** (2025-11-20, "Adding tutorial notebook
  example"). Cloned to scratchpad `watch/code_w/watch`, read only.
- Version caveat: the core files changed after arXiv v4 (25 Aug 2025). `git diff 3b10510
  3d17fca` (3b10510 = last commit before 2025-08-25) shows `src/p_values.py` +472/-158 lines
  combined with main.py (593 insertions total across three files). `src/martingales.py` diff
  contains only prints and added functions in the portion inspected; the jumper arithmetic read
  below is therefore likely identical to paper-time code, but **the paper-time p_values.py and
  main.py were not read** (UNVERIFIED that the pinned SHA reproduces the paper's numbers).
- Files read at the pinned SHA: `src/martingales.py` (all 245 lines), `src/p_values.py`
  (lines 17-27, 274-560, 736-940), `src/main.py` (lines 30-232, 295-300, 382-438, 886-968),
  `scripts/run_Fig2_meps_benignCov.sh`, `scripts/run_Fig3_meps_conceptShift_PR1.sh`, `README.md`.
  Not read: `main_mnist_cifar.py`, `main_pod_ram.py`, plotting, notebooks, resnet.

## 2. Native problem and estimand

- Setting: one pretrained model mu-hat deployed on a stream (X_t, Y_t); calibration data
  Z_{1:n} available; labels (so conformity scores) are observed for every test point t
  (Sec. 2, p.2; the monitored statistic uses y_t). Split-conformal assumed (footnote 1, p.2).
- Estimand is not risk or harm. It is whether a *weighted conformal p-value sequence* stays
  i.i.d. Uniform[0,1] under a stated null H0(f-hat) (Thm 3.1, Eq. 12, p.5). Rejection means the
  assumption set behind the (weighted) conformal predictor is wrong, i.e. a change in the score
  distribution relative to what the weights predict.
- Practical null (Eq. 13, p.6; derived App. C Eq. 23, p.19): the first n+t_ad-1 points are i.i.d.
  F_{Y|X} x F_X; from t_ad on, i.i.d. F_{Y|X} x G_X where G_X has density ratio w-hat(x) relative
  to F_X. "Concept shift or unanticipated covariate shift" is the alarm target (Sec. 3.3, p.5-6).
- Alarm semantics: both directions. Under-coverage (safety) and over-coverage (uninformative
  sets) violate uniformity (App. D.2, p.21); the paper explicitly penalises uninformative
  intervals with an anticonservative p-value (App. F Algorithm 2, p.28). A beneficial shift can
  therefore alarm.
- Feedback assumed: full, immediate label every round. No delay, missingness, or selective
  labelling is treated anywhere in the paper (UNVERIFIED by absence; not found in the sections
  read: Sec. 2-4, App. C, E, F).

## 3. Exact algorithm

### 3.1 Weighted conformal p-value (Sec. 3.1, p.4)

- Standard conformal p-value, Eq. 2 (p.3): p_{n+1} = (#{v_i > v_{n+1}} + u_{n+1} #{v_i = v_{n+1}}) / (n+1),
  scores v_i = S-hat(x_i, y_i), i in [n+1] (includes the test point), u ~ Unif[0,1].
- Weighted version, Eq. 9 (p.4): p^w~_{n+1} = sum_{i=1}^{n+1} w~_i [1{v_i > v_{n+1}} + u_{n+1} 1{v_i = v_{n+1}}],
  weights w~ in the simplex. Uniform weights 1/(n+1) recover Eq. 2 (p.5 text after Eq. 11).
- Oracle weights, Eq. 10 (p.5): w~_i^o = P{V_{n+1}=v_i | E_z} = sum over permutations with
  sigma(n+1)=i of the joint density f, divided by the sum over all permutations.

### 3.2 Covariate-shift weights and their online estimation (Sec. 3.3, 3.6; App. C)

- Factorisation, App. C Eq. 24 (p.20): f(z_1..z_{n+t}) = [prod_{j>=n+t_ad} w-hat(x_j)] x [prod_j f_Z(z_j)].
  The second factor is permutation invariant and cancels.
- Eq. 25-26 (p.20): permuting over all of [n+t] is intractable (n+t choose t_ad). The paper
  restricts permutations to those fixing the post-adaptation test points, giving
  w~_i^{(t)} = w-hat(x_i) / sum_{k in [n+t_ad-1] U {n+t}} w-hat(x_k).
- Implemented p-value, Eq. 17 (p.6) = App. C Eq. 27 (p.20): sum over i in [n+t_ad-1] U {n+t} of
  w~_i^{(t)} [1{v_i > v_{n+t}} + u 1{v_i = v_{n+t}}]. After t_ad the calibration set is frozen
  (no test points added), p.6.
- Estimating w-hat online (p.6, Sec. 3.6): an online probabilistic classifier (MLP or logistic
  regression "similar to Zhang et al. 2024") distinguishing source vs target covariates, refit
  each step, giving w-hat^{(t)}(x). The paper's own text for experiments (p.7): "3-layer MLP
  with ReLU" for weight estimation. Class-prior correction is not stated (UNVERIFIED;
  normalisation of Eq. 26 makes a constant factor irrelevant).
- Anticonservative guard, App. F Algorithm 2 (p.28): if w~_{n+1} < alpha, use the randomised
  exact p-value (Eq. 9); else use u_{n+1} = 0 (derandomised, anticonservative) because the weighted CP
  set would be the whole label space. Intentionally breaks uniformity to alarm faster on
  noninformative sets (stated in the algorithm note).
- Algorithm 1 (p.27) is Tibshirani et al. 2019 weighted CP set (calibration quantile with
  point mass w~_{n+1} at infinity). Only two algorithm boxes exist; App. F says fuller
  pseudocode is promised (App. F, p.27).

### 3.3 Betting / calibrator and martingale (Sec. 2.3, p.3-4)

- Betting function, Eq. 6 (p.3): h_eps(p) = 1 + eps (p - 0.5), eps in E = {-1, 0, 1}; integrates
  to one on [0,1]. eps<0 bets on small p, eps>0 on large p, so it is **two-sided**.
- Strategy: "composite jumper" Markov chain of Vovk et al. 2022 (p.3-4); mixture form Eq. 7
  (p.4): M_t = integral of prod h_{eps_i}(p_i) nu(d eps). Experiments use the composite jumper
  (p.4, 6). Composite = average of simple jumpers over J in {0.0001, 0.001, 0.01, 0.1, 1}
  (App. D.5, p.23). Simple Jumper with J=0.01 is the ablation baseline.
- Code (`src/martingales.py`): `composite_jumper_martingale` lines 135-181: for each J keep
  (C_-1, C_0, C_1) initialised 1/3; per step C_k <- (1-J) C_k + (J/3) C_prev, then multiply by
  (1 + (p-0.5) eps_k), and C = mean over J of the sum of three. Note C_prev is the previous
  *composite* value, shared across J (lines 147-161). Default alarm threshold 100 (line 135).
  `simple_jumper_martingale` lines 85-131. `cautious_simple_jumper_martingale` lines 184-244 is
  extra, not in the paper.
- Alarm rules (Sec. 3.4-3.5, p.6):
  - Anytime-valid: alarm when M~_t / M~_0 >= c; Prop. 3.2, Eq. 14: P_H0{exists t: M~_t/M~_0 >= c} <= 1/c.
  - Scheduled/multistage: Shiryaev-Roberts, Eq. 15 (p.6, checked on the rendered page):
    tau_k = min{t > tau_{k-1}: sum_{i=tau_{k-1}}^{t-1} M~_t / M~_i >= c}. Prop. 3.3, Eq. 16: E_H0[tau_1] >= c
    (ARL control, inherited from Vovk 2021 Prop. 4.2, App. B.2 p.18). CUSUM is mentioned
    (Sec. 3.5, p.6) but only SR is analysed in experiments.
  - Code (`martingales.py`): SR `shiryaev_roberts_procedure` lines 45-75 computes
    sigma[n] = sum_{i<n} S[n]/S[i], matching Eq. 15 for the first stage (tau_0 = 0). Only the
    first stage (k=1) is detected; no restart.
    CUSUM lines 20-42 uses max_i S[n]/S[i].

### 3.4 Adaptation (Sec. 3.6, p.6) and root-cause analysis (p.7, Fig. 1)

1. Run two things in parallel from deployment: (a) the main monitor, initially a standard CTM
   (uniform weights); (b) a secondary **X-CTM**: a standard conformal test martingale whose
   nonconformity score depends on X only, a nearest-neighbour distance (p.6, citing Vovk et al.
   2021).
2. When the X-CTM exceeds a "pre-determined adaptation threshold" at time t_ad, begin adaptation:
   switch the main monitor to weighted p-values with online density-ratio weights (Eq. 17).
   The numeric adaptation threshold is **not stated in the paper text read** (UNVERIFIED in paper;
   see code below).
3. Alarm = main WCTM (or SR-WCTM) crosses its threshold. The paper's stated purpose of the
   alarm is "initiate retraining" (Sec. 1, p.1-2). The paper contains **no retraining or
   rollback procedure**; the experiments only record alarms and coverage/width.
4. Root cause (p.7, "Root-Cause Analysis with Parallelized WCTM and X-CTM"): WCTM alarm and X-CTM
   fired -> extreme (out-of-support) covariate shift; WCTM alarm and X-CTM not fired -> concept
   shift in Y|X; X-CTM fired and no WCTM alarm -> benign covariate shift (adapted). Sec. 4.4, Fig. 4.
   "Fired" is a threshold crossing, no separate test with its own error control.

Code details of the adaptation trigger (pinned SHA, `src/main.py`, method `fixed_cal_dyn`,
lines 100-216; read, not executed):
- X-CTM score: 1-NN ball-tree distance of each cal+test x to `X_train` (lines 118-124).
- X-CTM p-values: `calculate_p_values` (p_values.py:551-560); martingale on `p_values[n_cal:]`
  with `composite_jumper_martingale` at its **default threshold 100** (main.py:129).
  `--x_ctm_thresh` (default 3.1623, main.py:915) is only referenced in comments and an assert
  (lines 101, 139, 196); it appears unused. SR on the X-CTM uses `--x_sched_thresh`
  (default 1000, main.py:916; scripts pass 1000).
- Lines 146-157: as read, if the X-CTM martingale alarms, `x_alarm_idx = n_cal + m_alarm_time`
  (line 149), but the following `if sr_alarm_time < m_alarm_time ... else x_alarm_idx = len-1`
  (lines 154-157) overwrites it with "no adaptation" whenever the SR alarm is not strictly
  earlier. This looks like a control-flow bug or an undocumented rule; UNVERIFIED by running.
- An SR run backward from the alarm estimates a changepoint (lines 160-191), but
  `adapt_starts` is then set to `x_alarm_idx` (lines 215-216), not the estimated changepoint.
- Before the X-CTM alarm, p-values are standard conformal (p_values.py:764-765).
  After it, weighted p-values from `calculate_weighted_p_values_and_quantiles` (736-940); the
  anticonservative rule appears at line 857 conditioned on the summed weight of scores tied
  with the test score being < alpha (equals w~_{n+1} when scores are distinct).
- Weights for `fixed_cal_dyn`: `online_lik_ratio_estimates_window_ahead` (p_values.py:274-406):
  classifier labels 0 for the first `adapt_start` points and 1 for later ones (line 303);
  `StandardScaler` is fit on **all** cal and test covariates including future test points
  (lines 296-298), a look-ahead leak of covariate moments; weights = P(target|x)/P(source|x)
  (line 399), zero source probability replaced by the smallest nonzero (lines 390-393).
  Default classifier is `LR` (main.py:32, 914, 453); the Fig. 2/3/4 scripts read do not override
  it, so the tabular experiments appear to run logistic regression, **not** the "3-layer MLP" the
  paper text states (p.7). `NN` in code is an sklearn MLP with one hidden layer of 20 logistic units
  (p_values.py:325-327). UNVERIFIED for the figures actually in the paper.

## 4. Hyperparameters and defaults in the paper's experiments

- Target coverage 90% (alpha=0.1): Fig. 2 caption (p.7) and `--alpha` default 0.1 (main.py:900).
- Tabular: MEPS, UCI Superconductivity, Bike Sharing; regression, score |y - mu-hat(x)|;
  predictor sklearn MLPRegressor (L-BFGS, logistic) (p.7, App. E.1 p.24). Image: MNIST-C and
  CIFAR-10-C, 1 - softmax score; ResNet-32 / MLP; weight estimator CNN discriminators (App. E.3
  p.26-29, Tables 4-5).
- Benign-shift runs: 3000 test points, changepoint after the 500th, 200 seeds, 1/3 train, 1/3
  cal, exponential tilting lambda_mep=5, lambda_sup=2.5, lambda_bik=5 (Fig. 2 caption, p.7).
- Anytime-valid false-alarm 0.01 (threshold 100) for WCTM vs PR-ST; SR-WCTM compared with
  PR-CD at average run length 20,000 (Sec. 4.3, p.9). **Code uses `10**4` as the SR threshold**
  (main.py:422-435, hard-coded; the `sr_threshold` argument is not used in `retrain_count`), so
  which value produced Table 1 is UNVERIFIED.
- ADD experiment: changepoint 100 samples after deployment (App. D.3, p.22). Image corruption
  runs: 5-10 seeds (Fig. 3, Table 3).
- Betting: composite jumper, J set above (p.23). X-CTM uses NN-distance score; adaptation
  thresholds: paper silent, code defaults 100 (martingale, implicit) and 1000 (SR).
- Table 1 (p.8) reports average detection delay; WCTM and CTM comparable, both >3x faster than
  PR-ST; the numeric entries were not transcribed (figure/table text not read cell by cell, UNVERIFIED).

## 5. Guarantee

- Thm 3.1, Eq. 12 (p.5): if H0(f-hat) holds (all assumptions on the joint density f, including
  that any approximation of w~^o is exactly accurate) then P^w~_1, P^w~_2, ... are i.i.d. uniform
  on [0,1] (online p-values). Proof App. B.1 (p.15-18) by time reversal; needs the score function
  to be bijective (p.16, Lemma B.1).
- Prop. 3.2 (Eq. 14, p.6): Ville bound 1/c on false alarm for the WCTM. Prop. 3.3 (Eq. 16): SR ARL >= c.
  Proofs reduce to Thm 3.1 plus Vovk 2021 (App. B.2, p.18).
- **The implemented adaptive algorithm is weaker than Thm 3.1.** App. C (p.20-21): because the
  p-value in Eq. 27 is not computed over the full data sequence, Thm 3.1 "only directly applies"
  at t = t_ad; later p-values share the frozen calibration data and may be dependent. The paper
  offers two fixes (resample calibration per test point, or additionally assume the calibration
  score CDF equals the source CDF, i.e. n large; Eq. 28, p.20-21) and states the validity then
  holds for the modified null Eq. 28.
- Also outside the guarantee: the anticonservative p-value (App. F) breaks uniformity by design;
  online estimation error of w-hat is covered only by assuming w-hat = true ratio (robustness
  to approximate weights is listed as future work, Sec. 5, p.9); the adaptation trigger (X-CTM
  crossing) is data-dependent and its effect on the null of the later WCTM is not analysed in
  the sections read (UNVERIFIED); the alarm is not a harm test (detects change in the
  weighted-score distribution in either direction).
- Delayed, missing or selectively sampled labels: not covered.
- Root-cause labels carry no stated error-control guarantee.

## 6. Mapping to ShiftLab's deployment contract; achievable tier

ShiftLab contract: two frozen models (deployed and reference), paired per-round loss
Z_t = c(deployed) - c(reference) in [-5,5], hard budget B=200 over T=2000, query cost 0.05,
switch cost 5, delayed labels (`scripts/sota_sprint/bench.py:25`, `src/shiftlab/contract/interface.py`,
`interface_v2.py`).

- **WATCH monitors one model's conformity stream, not a paired comparison.** Its null is about
  the score distribution of one predictor. A paired quantity can be fed in (score = Z_t) but the
  "calibration set" and the null then change meaning; that is a ShiftLab construction, not WATCH.
- Covariates: `PublicEvent.x` (interface.py:54) gives a covariate vector at every event, labelled or
  not, so the weight classifier could be trained on unlabelled covariates at all T rounds.
  Caveats: (i) the X-CTM and Eq. 17 need a *source covariate sample / training set* (NN distance to
  `X_train`, main.py:121-122; calibration cal set); `TaskSpec` carries none (interface.py:
  cost_bound, epsilon, alpha, horizon, label_budget, price_range). It would need a pre-registered
  source sample passed outside the public interface. (ii) p-values need y, so only
  queried-and-released events produce p-values; if the query probability depends on x, the
  labelled subsample's covariate distribution is shifted by design and the weights would have to
  absorb the propensity (not in the paper; UNVERIFIED validity). (iii) Under delay, labels arrive
  in release order, not event order; Thm 3.1's online time-reversal argument is not shown for
  this ordering (UNVERIFIED).
- Honest rollback / degradation trigger: "WATCH-style trigger" = run the unweighted CTM
  (Eq. 2, Eq. 6 composite jumper, Eq. 14 threshold) on the *deployed* model's conformity scores
  using labelled events within budget; on alarm, call `Switcher.choose` to roll back to the
  reference model, paying switch cost 5. This is an adaptation of the alarm, not WATCH's
  adaptation (WATCH adapts weights, not models, and prescribes no rollback). It detects
  predictive-score change, not decision harm relative to the reference (AGENTS.md: keep
  D(P_t,P_0), R_t(f)-R_0(f), and decision harm separate), is two-sided so it also fires on
  improvements unless the jumper is restricted to eps<0 or a one-sided calibrator is used (that
  restriction would be a deviation), and has no evidence that the reference is better, so the
  switch can be wrong.
- Tiers:
  - T1 for the *kernel*: `martingales.py` composite jumper and SR are pure numpy and small;
    a line-by-line port validated numerically against the pinned file is feasible. T1 for the whole
    WATCH pipeline is not achievable on the ShiftLab contract.
  - T2: unweighted WCTM = CTM (Eq. 2, 6, 7, 14-16) from printed equations. Feasible.
    Weighted + X-CTM adaptation: T2 only for Eq. 9/17/26-27; the adaptation trigger is code-defined
    (thresholds 100/1000, and the main.py:154-157 overwrite) so cannot be T2 from the paper alone.
  - T3: any ShiftLab deployment (budgeted labels, delays, paired score, switch-on-alarm). Every
    item above is a deviation to list.

## 7. Existing ShiftLab code

`src/shiftlab/sota_search/detectors.py:456-477` (`watch`) and registry row A6
(`docs/sota_synthetic_search/01_SOTA_ALGORITHM_REGISTRY.md:15`, label SOURCE_INSPIRED_BASELINE
"weights omitted"; description at detectors.py:57-61).

Matches:
- p-value: lines 461-464 reproduce Eq. 2 including the test point in the tie count (ge - ties + 1)
  with uniform tie-breaking; clipped at 1e-6 (not in paper).
- Mask and delay semantics: unqueried events contribute factor 1 (line 468), labels shifted by
  `delay` (lines 469-472). Alarm threshold log(1/alpha) (detectors.py:716), consistent with Eq. 14
  with alpha=0.05 (c=20; the paper uses c=100 in experiments).

Discrepancies (each is a reason it is not WATCH):
1. **Betting function.** Code uses a mixture of power calibrators eps p^(eps-1), eps in
   {0.1,0.3,0.5,0.7,0.9} (lines 466-467), one-sided toward small p. WATCH uses h_eps(p)=1+eps(p-0.5),
   eps in {-1,0,1}, two-sided, with the composite jumper Markov chain over J (Eq. 6-7;
   martingales.py:135-181). Different martingale, different power, different direction.
2. No weights, no X-CTM, no adaptation phase, no SR/CUSUM stage, no root-cause output
   (all Sec. 3.3-3.6 content absent).
3. **Calibration set.** `_cal_scores` (detectors.py:449-453) draws 500 scores from a fresh default
   `g.World(T=500)` simulation with seed 4242, not from the stream's own pre-change segment or a
   contract-provided source sample. If a regime's pre-change score distribution differs from that
   default world, the null is misspecified (UNVERIFIED which regimes differ; needs a run).
4. Score is |y - p| with y,p from `sim`; whether this equals the deployed model's conformity in
   every family is not asserted in the code (UNVERIFIED).
5. Label budget: `label_mask(sim, frac, lseed)` (line 79-81) is Bernoulli(frac) per round, not the
   hard B=200 reserve of the contract; no query cost or switch cost is accounted in this detector
   (it returns log-e only).
6. It is a single-model degradation monitor labelled as a rival to paired-harm monitors; it has
   no access to the reference model's loss, so it cannot test harm. Result tables must not call
   it WATCH (README: inspired-by must not use the paper's name).

Current honest tier: **Inspired-by** (shares conformal p-value + test-martingale idea only).

## 8. Reproduction tests available (identities and paper-stated facts)

- Eq. 2 vs Eq. 9 with uniform weights are identical; Eq. 26 with constant w-hat gives
  w~_i = 1/(n+t_ad).
- Simple/composite jumper with p == 0.5 for all t leaves C == 1 exactly (every factor is 1 and
  the update preserves total mass; derivable from `martingales.py:98-106`; not stated in paper, a
  property test, not a paper number).
- Ville bound: under i.i.d. Uniform p, empirical P(max_t M_t >= 100) <= 0.01 (Eq. 14 with c=100;
  paper Fig. 2/3 average martingale paths, p.7-8, are consistent in text only).
- Composite-jumper floor: App. D.5 (p.23) says composite betting is lower-bounded at M_t = 0.2.
  This is a paper-stated numeric claim usable as a test; I did not verify it numerically.
- Algorithm 2 branch: w~_{n+1} >= alpha implies p equals the derandomised sum (u=0).
- Paper numbers (Table 1 ADD, Table 3 corruption results p.24) exist but were not transcribed;
  reproducing them needs the datasets and the paper-time p_values.py (UNVERIFIED availability).

## 9. Open questions / UNVERIFIED

- PMLR proceedings text vs arXiv v4; whether the code at 3d17fca (post-publication) equals the
  code used for the paper (p_values.py and main.py changed after v4).
- Whether main.py:154-157 overwrites the X-CTM martingale alarm in the figures' runs, and the
  actual adaptation thresholds for the published figures (code: implicit 100 and 1000;
  `--x_ctm_thresh` unused).
- SR threshold used for Table 1 (paper 20,000 ARL; code literal 10^4).
- Classifier used for weights in published tabular figures (paper: MLP; code scripts: LR default).
- Whether Thm 3.1 survives the X-CTM-triggered, data-dependent t_ad and frozen calibration (paper
  flags only the dependence issue; Eq. 28 assumption or resampling).
- Validity under delayed or propensity-selected labels.
- App. E.1 (p.24) dataset sizes and Table 1 entries not transcribed.
