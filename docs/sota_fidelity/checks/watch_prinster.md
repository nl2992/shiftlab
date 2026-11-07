# Check: WATCH (Prinster, Han, Liu, Saria; ICML 2025)

Independent check of `specs/watch_prinster.md`, 2026-11-06. No downloaded code was executed. Two small
numerical experiments (section "Own numerics") re-implement printed/read formulas in numpy.

## Sources actually read

- PMLR camera-ready: `https://raw.githubusercontent.com/mlresearch/v267/main/assets/prinster25a/prinster25a.pdf`
  (30 pp; proceedings page meta: pages 49830-49859, published 2025-10-06). arXiv 2505.04608v4 (25 Aug 2025, 30 pp)
  re-fetched. Word-level diff of the two text extractions: identical except the arXiv watermark and ONE Table 1 cell
  (MEPS / Standard row, 4th column: PMLR `81.97 (+-1.01)`, arXiv v4 `81.97 (+-10.27)`). So PMLR == arXiv v4 for
  every equation, theorem, algorithm and setting quoted below. The spec's "PMLR not read" item is closed.
- Code: `aaronhan223/watch`. Full SHA `3d17fca58ac60410d020b54dee19ee3fc4ec29c2` (2025-11-20 "Adding tutorial notebook
  example"; CONFIRMED). Paper-era commit: `3b105105` (2025-05-31, README only; code state = `0551e3b1` 2025-05-26
  "updated code for error bars"; arXiv v1 was 7 May 2025, ICML camera-ready later). I fetched `src/main.py`,
  `src/p_values.py`, `src/martingales.py` at both SHAs via `gh api` and diffed; also the Fig 2-4 shell scripts.
- Local copies: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_watch/`
  (`pmlr_watch/`, `arxiv_watch/`, `code/old` = 3b10510, `code/new` = 3d17fca).

## Claim-by-claim

| # | Spec claim | Verdict | Evidence / location |
|---|---|---|---|
| 1 | Citation, ICML 2025 PMLR 267, acronym | CONFIRMED | PMLR v267 listing + `prinster25a.html` meta (pp. 49830-49859). Spec's "pp. 49830-49859 UNVERIFIED" is now VERIFIED |
| 2 | Standard conformal p-value Eq. 2 incl. test point; weighted Eq. 9 with simplex weights; uniform weights recover Eq. 2 | CONFIRMED | PMLR p.4 (Eq. 9), p.3 (Eq. 2) |
| 3 | Oracle weights Eq. 10 (permutation ratio) | CONFIRMED | p.5 |
| 4 | Thm 3.1 = IID uniform p-values under H0(f-hat), Eq. 12, p.5 | CONFIRMED | p.5; the statement quantifies over "any appoximations ... exactly accurate" (sic). Proof deferred to App. B |
| 5 | Betting function Eq. 6 `h_eps(p)=1+eps(p-0.5)`, E={-1,0,1}, two-sided | CONFIRMED | p.3, Eq. 6; text: negative eps bets on small p, positive on large |
| 6 | Mixture martingale Eq. 7 with nu = composite jumper (Vovk et al. 2022) | CONFIRMED | p.4, Eq. 7 and the "For example, in our implementations we take nu..." sentence |
| 7 | Composite = average of Simple Jumpers over J in {1e-4,1e-3,1e-2,.1,1}; Simple J=.01 ablation | CONFIRMED | App. D.5 (p.23). The paper's "lower bounded at M_t = 0.2" is an empirical figure remark, not a theorem. My simulation (iid uniform p, 2000 paths x 1000 steps) gives path minima 0.179-0.19, i.e. approximately but not exactly 0.2 |
| 8 | Code composite jumper `martingales.py:135-181`: per-J (C_-1,C_0,C_1) init 1/3, update with shared composite `C` | CONFIRMED text; CORRECTED consequence | See "Own numerics" 1: because `C` (the previous composite) is fed into every J's update, the object is NOT the plain average of independent Simple Jumpers and is not an exact test martingale. Under iid uniform p the exact one-step conditional drift E[C_t|F_{t-1}]/C_{t-1}-1 ranged -11.3% to +6.7%, positive in 64% of steps. In 2000 null paths P(max>=100)=0.7% (<1%), so alarms were not anti-conservative in that run, but Ville validity of Eq. 14 is not guaranteed for the code's kernel. A ShiftLab port must use per-J own capitals (exact martingale) or disclose this |
| 9 | Alarm rules: Ville Eq. 14 (Prop 3.2), SR Eq. 15, ARL Eq. 16 (Prop 3.3) | CONFIRMED | p.6 |
| 10 | Numeric alarm threshold c = 100 "in experiments" (spec section 7) | CORRECTED | The paper text states no numeric c. It states a "standardized anytime-false alarm rate of 0.01" for the sequential-testing baseline (p.9, App/Baselines paragraph), which corresponds to c = 100 by Eq. 14. Code default `threshold=100` (`martingales.py:135`). So c=100 is an inference from 1/c = 0.01, not a printed number |
| 11 | Practical null Eq. 13 (p.6) / App. C Eq. 23 | CONFIRMED | p.6; App. C step 1 |
| 12 | Calibration-set source and weight formula: restricted permutations, `w_i = w(x_i)/sum over [n+t_ad-1] U {n+t}`; Eq. 17 = Eq. 27; calibration frozen after t_ad | CONFIRMED | p.6 Eq. 17; App. C Eq. 24-27 (pp.20-21); code `p_values.py:736-940` (`calculate_weighted_p_values_and_quantiles`) uses `idx_include` over cal + current test point, `normalized_weights_t = W/sum(W)`. Pre-adaptation p-values are the plain conformal p-values (`wp_values[0:x_ctm_alarm]`) |
| 13 | Calibration data are the paper's own pre-change data | CONFIRMED | Fig 2 caption: training and calibration each 1/3 of total data sampled uniformly; post-change points bias-sampled from the remaining holdout. Contrast with ShiftLab `_cal_scores` (see below) |
| 14 | Density-ratio weights from an online probabilistic classifier refit each step | CONFIRMED | Sec 3.6 p.6; code `online_lik_ratio_estimates` (`p_values.py:412-523`): refits `lik_ratio_model.fit` for each t, `W = P(target)/P(source)` with no class-prior correction (a constant, cancels in normalisation) |
| 15 | Classifier: paper says "3-layer MLP with ReLU" (p.7); code scripts use LR default | CORRECTED (both directions) | (a) Paper is internally inconsistent: p.7 says 3-layer MLP/ReLU for weight estimation; App. E Tables 4-5 describe CNN discriminators for MNIST/CIFAR; the synthetic ablation (App. D.4 Fig 6) contrasts LR vs MLP. (b) Paper-era code (3b10510): `online_lik_ratio_estimates(..., classifier='NN')` default and `main.py:233,237` pass no classifier, so tabular weights used `MLPClassifier(hidden_layer_sizes=(20,), solver='lbfgs', activation='logistic')` = ONE hidden layer, 20 logistic units, not 3-layer ReLU. (c) Pinned SHA adds CLI `--online_lik_ratio_classifier` default `'LR'` (`main.py:914`); the Fig 2/3/4 scripts for MEPS (`run_Fig2_meps_benignCov.sh` etc.) do not pass it, so they run LOGISTIC REGRESSION; only `run_synthetic_cov_benign.sh` passes `NN`. The pinned SHA therefore does not reproduce the weight model of the paper-era code |
| 16 | Anticonservative guard, App. F Alg. 2 | CONFIRMED | p.28: randomised p if `w_{n+1} < alpha`, else `u=0`. Code `p_values.py` (end of the t-loop): tests `sum(normalized_weights[scores == score_t]) < alpha`, equal to the test-point weight when scores are continuous (ties would differ) |
| 17 | Thm 3.1 holds only at t = t_ad | CONFIRMED, with an important rider | App. C p.20, right after Eq. 27: "Theorem 3.1 only directly applies ... for the timepoint t = t_ad". The paper repairs this by changing the null to Eq. 28 (adds: empirical cdf of the frozen calibration scores equals the true source score cdf, "true in the limit n -> infinity") or by resampling the calibration data per test point. Prop 3.2/3.3 (Ville, ARL) are claimed for that modified null only. The main-text Sec 4 sentence that p-value uniformity "validat[es] Theorem 3.1" is therefore empirical support for a modified null. The X-CTM-triggered, data-dependent t_ad is not analysed (spec's UNVERIFIED stands) |
| 18 | main.py:154-157 overwrites the X-CTM alarm | CONFIRMED (both SHAs) | New `main.py:154-157`; same logic at `3b10510 main.py:145-148`, so it is not post-paper drift. Branch applies when `dataset0_name != '1dim_synthetic_v3'` (all MEPS/superconduct/bike scripts). Reading: if the X-CTM (threshold 100) alarms, `x_alarm_idx = n_cal + m_alarm_time`; if it never alarms `m_alarm_time` is set to the last index. Then `if sr_alarm_time is not None and sr_alarm_time < m_alarm_time: x_alarm_idx = n_cal + sr_alarm_time else: x_alarm_idx = len-1` (no adaptation). Net rule for real-data runs: adaptation starts at the SR(x_sched_thresh=1000) alarm, only if that SR alarm is strictly earlier than the X-CTM alarm (or the X-CTM never alarms); an X-CTM alarm not preceded by an SR alarm yields NO adaptation. The paper text (Sec 3.6) says adaptation is triggered when the X-CTM "exceeds a pre-determined adaptation threshold". The synthetic branch (`main.py:138-145`) uses the X-CTM alarm only. Not executed; behaviour inferred from reading |
| 19 | `--x_ctm_thresh` unused | CONFIRMED | default 3.1623 (`main.py:915`); referenced only in an assert and comments; the X-CTM threshold is the hard default 100 of `composite_jumper_martingale`. Synthetic scripts pass `--x_ctm_thresh 10 --x_sched_thresh 3000` but the synthetic branch ignores them for the decision |
| 20 | SR threshold 1e4 in code vs ARL 20,000 in paper | CONFIRMED | Paper p.9: "for SR-WCTMs we compared vs changepoint detection variant with common average-run-length (under the null) of 20,000". Code: `shiryaev_roberts_procedure(martingale_value, 10**4, ...)` hard-coded at `main.py:422,426,431` (also `retrain_count` arg `sr_threshold=10**4` is unused; same literals at `3b10510 main.py:354-363`); baseline PR-CD delta `1/20000` (`main.py:451-452, 930-931`). So SR-WCTM runs at ARL >= 1e4 (Prop 3.3) while its baseline runs at 2e4: the paper's "common" ARL claim is not what the code does. Table 1 detection delays favour WATCH slightly by this mismatch |
| 21 | SR first stage only, no restart | CONFIRMED | `martingales.py:45-75`; matches Eq. 15 for k=1 |
| 22 | X-CTM uses 1-NN distance to the training set; threshold unstated in the paper | CONFIRMED | p.6 "nearest-neighbor nonconformity score"; no numeric threshold in text; code `main.py:110-124` (non-synthetic NN at 121) NearestNeighbors(n_neighbors=1, ball_tree) on `X_train`; synthetic branch uses signed distance to the training mean |
| 23 | Feedback regime: full, immediate labels every round; no delay/missing labels | CONFIRMED (by absence) | No treatment in Sec 2-6 or Apps C-F; the only "delay" is detection delay |
| 24 | Beneficial shifts can alarm (two-sided) | CONFIRMED | App. D.2 p.21 |
| 25 | No retraining/rollback procedure | CONFIRMED | Sec 5 and abstract: alarm "to initiate retraining" only |
| 26 | Paper-time p_values.py/main.py "not read"; changed after v4 | CORRECTED (now quantified) | GitHub compare 3b10510 -> 3d17fca: `main.py` +139/-37, `p_values.py` +356/-116, `martingales.py` +98/-5 (adds `cautious_simple_jumper`, prints, `return_alarm` on simple jumper), `utils.py` +38/-7. Material changes: (i) classifier flag, default LR vs earlier fixed NN (row 15); (ii) `init_phase` window flipped from `iloc[:init_phase]` to `iloc[-init_phase:]` (`main.py:55-56`); (iii) y-noise N(0,1e-4) added to train/test targets (`main.py:466-467`); (iv) reverse-SR changepoint estimate and `x_ctm_alarms` plumbing (computed, but `adapt_starts` still equals the X-CTM/SR alarm for non-synthetic); (v) `len_w_ahead` window-ahead weight estimator; (vi) pre-adaptation p-values cut at `x_ctm_alarm` instead of `adapt_start` (equal in non-synthetic runs). UNCHANGED: weighted p-value formula and anticonservative rule, composite jumper (`martingales.py` composite lines untouched), SR/CUSUM, X-CTM construction, the 154-157 rule, the 1e4 literals. Whether the pinned SHA reproduces published numbers remains UNVERIFIABLE (no run) |
| 27 | Dataset sizes (spec section 9 "not transcribed") | NEW | App. E.1: MEPS 33005 x 107, Superconductivity 21263 x 81, bike 17379 x 12; MNIST-C 60000 clean + 10000 corrupted; CIFAR-10-C 50000 + 10000. Table 1 ADD at changepoint 100 after deployment, 200 seeds; Fig 2 shift lambda: mep 5.0, sup 2.5, bike 5.0 |

## Own numerics (not downloaded code)

1. Composite-jumper martingale property (script `check_watch/cj2.py`, numpy, transcribed from `martingales.py:135-181`
   as read): 300 null paths x 1500 steps of iid U[0,1] p-values; exact conditional drift
   `mean_J[(1-J)S_J + J C] / C - 1`: max +6.7%, min -11.3%, positive in 64% of steps. A per-J own-capital variant has
   exactly zero drift. `cj.py`: P(max M_t >= 100) = 0.007 over 2000 null paths of length 1000; p == 0.5 keeps M == 1.
2. Neither run proves anti-conservativeness; they show the kernel is not an exact martingale.

## Which simulator / harness does each covariate statement refer to (conflict resolved)

Three distinct streams exist in the repo; the spec statement and the earlier check each describe a different one.

| Harness | Covariates? | Evidence |
|---|---|---|
| `src/shiftlab/contract` (PublicEvent contract: `interface.py:38-62`, field `x: np.ndarray` at line 54; `harness.py`, `harness_v2.py`, `sandbox.py`) fed by `src/shiftlab/real_tasks/__init__.py:131` and unit tests | YES, a covariate vector per event, labelled or not | This is what the WATCH spec section 6 cites. Its statement is TRUE for this contract |
| SOTA sprint / Failure Atlas: `scripts/promising_directions/sota/simulator.py` (`Event.context: Any = None`, line 54; `run_episode(..., contexts=None)` default, lines 134,172-177) and `scripts/failure_atlas_v2_flq/suite.py` (`stream_from_losses`, lines 96-100: balanced labels, `preds = labels XOR loss`; `run_metrics` calls `run_episode` with no `contexts`) | NO. Loss tapes only; context is None. Only exception: `scripts/sota_sprint/wp1_clock_ablation.py:191,194` passes int64 timestamps as `contexts` | The earlier check is TRUE for this benchmark |
| `scripts/sota_sprint/bench.py` | Defines no streams at all: a registry (CONTRACT dict at line 25, regime tables, comparator-class lists). Streams come from `failure_atlas_v2_flq/regimes.py` ("paired 0/1 loss streams", docstring) and real-data tapes `data/sprint_fresh_losses/*.npz`, which hold only `l0`, `l1`, `starts` (verified by loading two files; README confirms) | So the comparator pools driven by `bench.py` have NO covariates |
| `src/shiftlab/sota_search/generators.py` (`simulate`, `simulate_g3`, ...) used by `detectors.watch` | Yes: `sim["x"]` exists (lines 161,197,244,339), but `watch` reads only `sim["y"]`, `sim["p"]` (detectors.py:456-477) | The repo's WATCH-style detector never uses covariates even where they exist |

Consequence: weighted WATCH (X-CTM, Eq. 17 weights, root-cause) can be run on the contract/real_tasks stream and the
sota_search synthetic generators, but NOT on the sprint comparator pool, which has no covariates and no source
covariate sample. In the sprint pool only the unweighted score CTM is possible. The spec's "PublicEvent.x provides
covariates every round" must be rewritten as "in the `shiftlab.contract` interface only".

## ShiftLab code check (`src/shiftlab/sota_search/detectors.py`)

- p-value lines 461-464: `(#cal > s + u*(#cal == s + 1)) / (n+1)`, i.e. Eq. 2 with test point in the tie count. CONFIRMED.
  Clip at 1e-6 is not in the paper.
- Betting lines 465-466: `eps p^(eps-1)`, eps in {.1,.3,.5,.7,.9}, equal-weight mixture of constant bets,
  one-sided toward small p, each integrates to 1 so the mixture is a valid test martingale. Not Eq. 6-7 (two-sided
  linear bet with a Markov jumper). CONFIRMED discrepancy. Threshold `log(1/0.05)` (`detectors.py:716`, ALPHA line 18)
  = c 20, not c 100. Docstring (lines 57-61) already says "WATCH without covariate weighting".
- Calibration set: `_cal_scores` (449-453) simulates a fresh default `g.World(T=500)` with seed 4242, not the
  stream's own pre-change segment (WATCH: cal sampled from the same pre-change data). CONFIRMED discrepancy; which
  regimes make this a misspecified null is UNVERIFIABLE without a run.
- Verdict on tier: Inspired-by. The spec's tier call is right.

## Tier call

Spec: kernel T1/T2 feasible, whole pipeline T3, current code Inspired-by. AGREE, with two additions: (1) a T1 port
of `composite_jumper_martingale` as written would import the shared-`C` non-martingale quirk (row 8); (2) a T1 port
of the real-data adaptation trigger must reproduce the 154-157 rule or be declared a deviation (row 18).

## Remaining UNVERIFIABLE

- Whether code at 3b10510/0551e3b1 equals the code that produced Tables 1/3 and Figs 2-4 (no run).
- Whether the shipped figures used the NN or LR weight model for MEPS (paper-era default NN; pinned scripts LR).
- Effect of the 1e4 vs 2e4 ARL mismatch on Table 1 (not rerun).
- Validity under delay/propensity-selected labels (outside the paper).

## Verdict

ACCEPT WITH CORRECTIONS. Apply rows 8, 10, 15, 17 (Eq. 28 rider), 18, 20, 26 and the harness table above to the spec.
