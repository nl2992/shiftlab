# Spec: Regol et al., "When to retrain a machine learning model" (UPF)

Retrieved 2026-11-06 by a retrieval subagent. Equation, section, table and page numbers refer to the
**PMLR proceedings PDF** (36 pages, main text pp. 1-9, appendix pp. 15-36) unless marked "arXiv".
Anything not read directly is marked UNVERIFIED. Items marked "retriever derivation" are not claims
of the paper.

## 1. Citation, venue, version read, code

- Florence Regol, Leo Schwinn, Kyle Sprague, Mark Coates, Thomas Markovich. "When to retrain a
  machine learning model." ICML 2025 (42nd), PMLR 267:51369-51404. arXiv:2505.14903.
- Read in full (text extracted with `pdftotext`, both columns, appendix included):
  - PMLR: `https://raw.githubusercontent.com/mlresearch/v267/main/assets/regol25a/regol25a.pdf`,
    36 pages, SHA-256 `a4eaccfab1e3c284a477608a8e6779e9359a76cf22006258c7c62138cbc9c139`.
    Landing page: `https://proceedings.mlr.press/v267/regol25a.html`.
  - arXiv v1 (only version; "Submitted on 20 May 2025"): `https://arxiv.org/pdf/2505.14903`, 36 pages,
    SHA-256 `b2144679b011c02f52ecdee2d5f43675d50d813a064763e87dd45dbf532a350d`.
  - Local copies: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/regol/`
    (`pmlr.pdf`, `arxiv.pdf`, `*_raw.txt`).
- arXiv-v1 vs PMLR: same page count, same equation set. A line-set comparison shows only wording,
  citation-format and layout differences (e.g. PMLR adds the Hoffman et al. 2025 related-work
  sentence and "independent of each other" wording near Eq. 8). Spot checks of Prop. 3.1 text,
  delta=95%, ElasticNetCV, eN=1, w=7, Table 1 UPF row (2.5782, 3.0498), 0.96 in A.4.1 and
  "bootstrapping" are present in both. No numeric difference found in anything cited below; a full
  line-by-line diff of the appendix tables was not done (UNVERIFIED beyond the spot checks).
- **Official code: none found.** Searched: PMLR landing page (links only to mlresearch GitHub
  repo, OpenReview, PDF); arXiv abs page (generic CatalyzeX widget, no repo); paper text (only
  "github" hit is the timm reference, p. 11); Cash App blog `https://ai.cash.app/when-to-retrain`
  (links only the `github.com/cashapp/` org root); `gh repo list` for `block` (about 145 repos) and
  `cashapp` (about 57): no retraining/UPF repo; `gh search repos` for the title and "UPF" terms:
  only unrelated third-party repos. OpenReview forum `X7X4YLMneu` could not be read (bot-challenge
  page; not bypassed), so an OpenReview supplementary zip is UNVERIFIED. The paper states no code
  availability. Commit SHA: n/a.

## 2. Native problem and estimand

- Sequence of fully labelled datasets D_{-w},...,D_0,...,D_T, drawn from p_t (Sec. 3, p. 3).
  Offline period t in [-w..0] (all models f_{-w}..f_0 and datasets available); online period
  t=1..T. At each online t the practitioner may (re)train f_t using data up to t at cost c_t
  (Sec. 3, p. 3). No restriction on how the retrained model is obtained (Sec. 1, p. 2).
- Decision vector theta in {0,1}^T; r_theta(t) = last training time <= t (p. 3). Predictions at t use
  f_{r_theta(t)}. The last offline model f_0 is always available.
- Estimand/objective, Eq. 1: C_alpha(theta) = E[sum_t e_t sum_i loss(f_{r(t)}(x_it), y_it) + theta_t c_t].
  Shorthand pe_{i,j} = E_{D_j}[loss(f_i(X_j),Y_j)] for i<=j, else 0 (Eq. 2). With constant c, e, N and
  alpha = c/(eN): **Eq. 3: C_alpha(theta) = eN( alpha*||theta||_1 + sum_{t=1}^T pe_{r_theta(t),t} )**.
  Goal: theta* = argmin C_alpha (Eq. 5), subject to g(t, I_<t) decisions from past information only
  (Eq. 4, Sec. 3.1, p. 4). Information I_<t = offline data plus online datasets D_1..D_{t-1} and only the
  models actually trained online.
- Cost model: **two scalars in one loss-unit scale**: performance cost eN*pe (bounded loss, per-period
  mean, N predictions per period) and retrain cost c, expressed as the ratio alpha. alpha is assumed
  known by the practitioner (Sec. 5 "Evaluation Metrics", p. 6; robustness to wrong alpha in A.2).
  Labels are free; there is no label cost, no switch-back, no query decision.
- Feedback: every period's full dataset with labels is observed (UNVERIFIED nuance: the paper never
  discusses label delay; I_<t excluding D_t implies at most a one-period lag). No hypothesis test,
  null, or error-control target. The method is a point-decision heuristic, not a test.
- Evaluation: C_hat_alpha = alpha*||theta||_1 + sum_t pe_test_{r(t),t}, with eN=1 and 0-1 loss (Eq. 24,
  p. 6), reported as AUC over 10 alpha values in [0, alpha_max], alpha_max = smallest alpha at which the
  oracle (argmin over theta with all pe known) retrains zero times (p. 6).

## 3. Exact algorithm (UPF = Uncertainty-Performance Forecaster)

Pseudocode, each line tied to the paper. Index: model i, evaluation period j.

```
Offline: collect M_<0 = {(r_ij, a_ij)} for all trained models and datasets in I_<0           [Eq. 10, p. 5]
for t = 1..T (online):
  1. Refit forecaster on M_<t = {(r_ij,a_ij): f_i,D_j in I_<t}                                 [Eq. 10; "retrain ... each time", p. 5]
       features r_ij = [i, j, j-i, z_shift]                                                    [Sec. 4.1 p. 4; A.7 p. 20]
       z_shift = || xbar_t - xbar_{t-1} ||_1  (mean feature vectors of the two most
                 recent available datasets)                                                    [Eq. 53, A.7 p. 20]
       Gaussian approx Beta(alpha(r),beta(r)) ~ N(mu(r), sigma(r)); sigma_phi constant;
       MLE in mu = least squares (ElasticNetCV)                                                [Eq. 11-13, p. 5; p. 7]
       recover Beta params (with "appropriate clipping if needed"):
         alpha = mu*(mu(1-mu)/sigma^2 - 1);  beta = (1-mu)*(mu(1-mu)/sigma^2 - 1)             [Eq. 51-52, A.7 p. 20]
       P_phi(A_ij) = Beta(alpha_phi(r_ij), beta_phi(r_ij))                                     [Eq. 14]
       cells A_ij treated as independent                                                       [Eq. 8-9, p. 4]
  2. Cost-to-go random variables (alpha deterministic, future decisions theta~ deterministic):
       C~|retrain = alpha + A_{t,t} + theta~_{t+1} C~_{t+1}|retrain + (1-theta~_{t+1}) C~_{t+1}|keep   [Eq. 17]
                  = alpha + A_{t,t} + sum_{t'>t} ( A_{r(t'),t'} + alpha*theta~_{t'} )                   [Eq. 19]
       C~|keep    = A_{r(t-1),t} + sum_{t'>t} ( A_{r(t'),t'} + alpha*theta~_{t'} )                      [Eq. 20]
     where r(.) for t'>t follows the same rule's decisions (backward recursion).
  3. Decision (delta-quantile comparison, deterministic):
       theta~_t = 1[ F^{-1}_{C~|retrain}(delta) < F^{-1}_{C~|keep}(delta) ]                     [Eq. 16, 21-22, p. 5]
     quantiles estimated by Monte Carlo ("bootstrapping") when no closed form                   [Eq. 23, p. 6]
  4. If theta~_t = 1, train f_t (cost alpha); apply, observe D_t, go to t+1.
```

Notes on what the text fixes and what it does not:

- Fixed: the keep/retrain cost-to-go recursion (Eq. 17-20), strict "<" comparison of delta-quantiles
  (Eq. 16), delta-level semantics ("Lower values of delta ... lower variance", delta=0.5 = median,
  p. 5), Beta moment conversion (Eq. 51-52), feature vector [i, j, j-i, z_shift] (p. 4, A.7).
- **Not specified in the paper** (all UNVERIFIED because no code): how sigma_phi is estimated (only
  "constant sigma_phi"; MLE is stated for mu only, p. 5); the clipping rules; the number of Monte Carlo/
  bootstrap draws; whether samples are shared across the keep and retrain branches and across states;
  the quantile estimator; how z_shift is assigned to training pairs (i,j) (A.7 defines it only as the
  latest available shift); whether the diagonal pe_{i,i} is in the training set (Eq. 2 defines it; the count
  |M_<0|=21 in Table 4 at w=7 matches neither 28 (i<=j over 7 periods) nor 36 (8 periods); which
  convention gives 21 is unclear).
- The paper itself says past decisions affect I^online but "this effect is ignored by the algorithm"
  (p. 5), i.e. the forecaster is trained on data whose distribution depends on its own actions.
- Interpretation (retriever observation, not in paper): nested delta-quantiles of a recursively defined
  cost are not the delta-quantile of any single coherent risk functional of the whole schedule; the
  paper presents the rule as a conservative heuristic and supports it only by the ablation in A.1.

Connection to Q-learning (A.11, Eq. 58-70, pp. 28-30): deterministic MDP, state (model index, t),
reward -alpha*a - pe_{s_{t+1}}, gamma=1. UPF is described as an offline-Q-learning variant with a
parametric Q (Sec. 5, p. 6). The offline RL baseline results are in A.11.1 (UNVERIFIED in detail, not
read line by line).

## 4. Hyperparameters and defaults in the paper's experiments

| Item | Value | Source |
|---|---|---|
| Quantile delta | 0.95 ("standard value used for confidence intervals") | Sec. 5 "Baselines", p. 7 |
| Mean model mu_phi | scikit-learn `ElasticNetCV`; "all other optimization parameters ... defaults" | p. 7 |
| Loss / scale | 0-1 loss, eN = 1, classification | Sec. 5, p. 6 |
| Offline length | w = 7; online horizon T = 8 for all datasets; |M_<0| = 21 | Table 4, p. 19 |
| Trials | 10 per dataset (3 for iWild); each trial samples a different sequence of length w+T | p. 6 |
| alpha grid | 10 operating points from 0 to alpha_max (oracle's zero-retrain alpha); metric = AUC of C_hat_alpha | p. 6 |
| alpha_max by dataset | Gauss 0.5, circles 0.25, electricity 1, yelpCHI 0.1, epicgames 0.1, airplanes 0.7, iWild 1 (column alignment inferred from extraction order of Table 4) | Table 4, p. 19 |
| Dataset size |D| | Gauss 5000, circles 5000, electricity 2000, yelpCHI 4000, epicgames 1000, airplanes 3000, iWild 40,605 (same caveat) | Table 4, p. 19 |
| Base models | XGBoost (all but iWild); iWild: timm models, random search over 188 | Sec. 5; A.6.1, p. 20 |
| Baselines | ADWIN, KSWIN, FHDDM at 5% and 50% significance (window = |D|, reset at retrain); CARA, CARA cumul., CARA per. | Sec. 5, p. 7 |
| Monte Carlo draws, sigma_phi estimator, clipping, seed | **not stated** | UNVERIFIED |
| Gaussian vs Beta ablation | UPF (Gaussian) variant shows little difference | A.8.1, Figs. 9-12, p. 23-24 |
| Unbounded metrics | Log-Normal replaces Beta (Eq. 54-56) | A.8, p. 23 |

Runtime (A.9, Table 6, p. 24): UPF offline 0.0947 ms, online 0.0247 ms per step (circles, as reported).

## 5. Guarantee

- **There is no guarantee for the UPF decision rule.** Evidence is empirical (Tables 1-3, Figs. 2, 13-19).
  The conclusion says the method is "primarily suited to gradual changes" and abrupt shifts are open
  (p. 9).
- **Proposition 3.1 (p. 4; proof A.4, pp. 15-17):** Assume L >= |pe_{i,t} - pe_{i+1,t}| for all t (Eq. 6)
  (adjacent-model performance gap on the same dataset), horizon T, relative retrain cost alpha. Then
  the optimal number of retrains r* = ||theta*||_1 satisfies **r* <= T - sqrt(alpha/L)** (Eq. 7, 25, 46).
  It is a statement about the oracle schedule under the *true* table pe, not about UPF's schedule.
  It is not used by UPF. A.4.1 (p. 17) uses the empirical maximum of |pe_{i,t}-pe_{i+1,t}| as L (the
  paper notes L cannot be bounded in general) and reports "alpha > 0.96 guarantees no retrain" on Gauss.
- **The printed statement is false as written.** The repo's one-step counterexample is correct against
  the printed text (pe = [[1],[0]], alpha = 0.25, L = 1, T = 1: optimal r* = 1 > 0.5). Retriever
  derivation from the proof text: Lemma A.1 (Eq. 39, p. 16) gives M*_r - M*_{r+1} <= L(T-r)^2, so retraining
  count cannot exceed any r with L(T-r)^2 < alpha. Eq. 40 then writes "L(T-r*)^2 < alpha implies
  r* < T - sqrt(alpha/L)", but the condition on the left implies the *opposite* inequality
  (r* > T - sqrt(alpha/L)); it is a condition on r, not a consequence of r*. The supportable
  conclusion is r* <= max(0, floor(T - sqrt(alpha/L)) + 1). Checked by brute force on 2978 random
  triangular instances (T <= 6, bounded loss, L set to the empirical adjacent gap):
  the printed bound was violated 392 times, the floor+1 form 0 times (script:
  `.../scratchpad/regol_scripts/prop31.py`, not committed). This is a numerical sanity check, not a
  proof; the step from (44) to (45) was checked by hand and holds. Lemma A.1's "r in {1, T-1}" (p. 16) is
  presumably a typo for {1,...,T-1}.
- Does not cover: any distributional assumption, dependence, feedback delay, selective labels, partial
  observation of pe, forecaster error, switching back, or anytime-valid error control.

## 6. Mapping to ShiftLab's deployment contract, tier, deviations

ShiftLab contract (from `scripts/sota_sprint/bench.py:25`, `src/shiftlab/contract/interface_v2.py`): T=2000
rounds, hard label budget B=200, label cost c_q=0.05, switch cost c_s=5, alpha=.05 (the level), two frozen
models (incumbent 0, challenger 1), paired per-round loss, delayed or missing labels, purchase decided per
event, the Switcher chooses `A_t` each round from public information (`interface_v2.py:98-101`).

Native-vs-contract differences that cannot be removed:

| Regol native | ShiftLab | Consequence |
|---|---|---|
| Retraining creates a **new** model f_t each time; only latest model used; no return | Two **fixed** models; switching is reversible | State is (current arm, t), not (model index, t). Features i and j-i lose meaning (models are frozen, trained before t=0). |
| All periods' pe_{i,j} observed (full labels) | Labels purchased, B=200 of 2000, delayed | pe must be estimated from sparse IPW labels; Beta-forecaster inputs are noisy, and the paper's data-scarcity story is about few *periods*, not few *labels*. |
| Labels free; cost = alpha*#retrains + loss | Labels cost 0.05 each; switch costs 5; loss summed per round | Label allocation is outside UPF; need a separate labeling rule, which would confound the comparison. |
| Offline phase with all models and w=7 periods | No offline paired-loss table unless a prefix is labelled | Needs a warm-up prefix paid from B, or fixed prior. |
| delta-quantile of total cost, no error control | Harm-null / false-promotion control is the experimental criterion | Rule gives no type-I control; belongs in the uncertified class. |
| Period = dataset D_t with N examples | Per-round events | Must choose a period length m (free parameter; lock before runs). eN = m, alpha_native = c_s / m. |

**Achievable tier.** Native problem (fully labelled period tables): **T2 is achievable** from Eq. 1-3,
10-24, 51-53 (the existing module is already such a port), with the unspecified items in Sec. 3 listed as
named, documented choices. **T1 is not achievable** (no official code found). For the ShiftLab contract
the best honest tier is **T3 (common-contract adaptation)**; it must not be called "UPF" or "Regol et al."
in result tables.

**An honest T3 "cost-aware switch timing" comparator** (name suggestion: `upf_style_switch_timing_T3`):
1. Partition the stream into periods of m rounds (m locked before any run).
2. Two "models" k in {0 incumbent, 1 challenger}; cell A_{k,j} = period-mean paired loss, estimated from
   IPW over labels that have matured (released) by the decision round; labelling follows a fixed shared
   rule (the benchmark's default or a constant rate B/T), not chosen by the adapter.
3. Forecaster: ElasticNetCV on [k, j, z_shift] (i and j-i collapse to a per-arm index and time) plus
   sigma from residuals; Beta by Eq. 51-52 with stated clipping.
4. State (current arm a, period j), action switch/stay. cost-to-go per Eq. 17-20 with "retrain" replaced
   by "switch to the other arm" (cost c_s/m + A_{other,j}) and "keep" by A_{a,j}; compare delta-quantiles
   (Eq. 16); delta=0.95 default.
5. Apply the first action, then refit when labels mature and replan (as in Sec. 4.1, p. 5).
Every one of these is a deviation: reversible switching; frozen models; sparse, delayed IPW cell estimates;
no offline w=7 table; periodization; exogenous labelling; label and switch costs mapped to alpha. The
adapter has no harm guarantee and should be reported as an uncertified published-style comparator
(cf. `UNCERTIFIED_PUBLISHED` in `bench.py:65`), with the class name making its T3 status explicit.

## 7. Existing ShiftLab code: comparison

Files: `src/shiftlab/dive/upf_retraining.py` (264 lines), `scripts/audit_upf_retrain_count_bound.py`,
`scripts/evaluate_upf_eia_frontier.py` (the only caller), tests `tests/test_upf_retraining.py`,
`tests/test_upf_retrain_bound_audit.py`. Matrix entry: `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` 1.1 (line 359).

**What matches the paper**
- Backward quantile recursion (`upf_retraining.py:241-261`) is a faithful reading of Eq. 17-20 and 22: state
  (incumbent, t), keep = sampled A_{inc,t} + value[t+1,inc]; retrain = alpha + A_{t,t} + value[t+1,t];
  strict `<` on delta-quantiles (line 258); value carries the chosen branch (line 261); first action
  applied and replanned (docstring lines 180-182; caller `evaluate_upf_eia_frontier.py:340-349,
  `schedule[1,0]`).
- delta = 0.95 default (line 168) matches p. 7; eN=1 convention (alpha added in loss units) matches p. 6.
- Beta moment conversion (lines 78-81) matches Eq. 51-52 in the unclipped regime.
- Features [i, j, j-i, z_shift] (lines 31-52) match p. 4 and A.7 Eq. 53.
- Elastic-net mean, constant variance, independent cells (lines 106-109, 233-239) match Eq. 11-14, 8-9.
- Forecaster fit only on matured entries (lines 115-160): an addition that respects ShiftLab's availability
  semantics, not in the paper.
- alpha grid construction (`evaluate_upf_eia_frontier.py:131-152`, N_ALPHA_POINTS=10, linspace 0..alpha_max) matches p. 6.

**Discrepancies and undetermined choices (file:line)**
1. `upf_retraining.py:106`: `ElasticNetCV(cv=min(5,n), random_state=seed, max_iter=50_000)`. Paper: scikit-learn
   defaults for everything else (p. 7). `max_iter` is a non-default convergence change (low impact);
   `cv` equals the sklearn default of 5 only when n >= 5.
2. `upf_retraining.py:108-109`: sigma^2 = **in-sample** mean squared residual of the same fit. Paper gives no
   estimator for the constant sigma_phi (p. 5, UNVERIFIED). In-sample variance is optimistic with ElasticNetCV
   on about 28 points, and it can be tiny, in which case line 77 floors it at epsilon^2 = 1e-10,
   producing a near-point-mass Beta and making delta-quantiles almost equal to means (it would
   erase the "uncertainty" in UPF). A.1 shows that uncertainty matters (Table 3), so this choice
   is consequential.
3. `upf_retraining.py:73-81`: epsilon = 1e-5 clip on the mean, variance cap 0.99*mu(1-mu), concentration and
   alpha/beta floors at epsilon. Paper: "appropriate clipping if needed" only (A.7, p. 20). Repo choice, undocumented
   as such.
4. `upf_retraining.py:169` (20,000 draws) and `evaluate_upf_eia_frontier.py:34` (10,000): paper does not state a
   draw count (UNVERIFIED). The sampling uses a single draw per cell shared across states and both branches
   (lines 233-239); the paper only says independent cells and "bootstrapping" (Eq. 8-9, 23). Whether the
   authors share draws is UNVERIFIED. `torch.quantile` linear interpolation is also an unstated choice.
5. `upf_retraining.py:99`: requires >= 3 observations; paper has 21 offline entries. Harmless but with n of
   3-4 the forecaster is degenerate (see item 2).
6. `evaluate_upf_eia_frontier.py:280-292`: training set = all i<=j pairs among 7 offline periods = **28** entries,
   including the diagonal. Paper reports |M_<0| = 21 for w=7 (Table 4, p. 19); the paper's pair convention
   is unresolved (UNVERIFIED which one gives 21).
7. `evaluate_upf_eia_frontier.py:288`: z_shift for training pair (i,j) = shift at evaluation period j.
   Paper (A.7 Eq. 53) defines z_shift only as the shift between the two most recent available datasets, so
   the per-pair assignment is unspecified; the forecast-time assignment (line 326-331, `latest_shift` for
   all cells) matches the paper.
8. `evaluate_upf_eia_frontier.py:567, 592`: application uses a clipped, normalized MAE as the "bounded
   loss" in a Beta model. The paper models bounded 0-1 accuracy with Beta and unbounded metrics with
   Log-Normal (A.8, Eq. 54-56); clipped-normalized-MAE-with-Beta is a ShiftLab choice, not a paper setting.
   Also T and w differ from the paper's 8 and 7 (script `N_PERIODS=15`, `ONLINE_START=7`, so 8 online
   periods and 7 offline: this part matches, line 29-31).
9. `scripts/audit_upf_retrain_count_bound.py:55-61`: counterexample against the printed Prop. 3.1 is
   valid. It treats the statement as `r* <= T - sqrt(alpha/L)` (matches Eq. 7); it does not note that the
   proof (Eq. 39-40) supports a different bound, and it does not report the corrected form
   r* <= max(0, floor(T - sqrt(alpha/L)) + 1). Recommend adding this as a second audit (not changing the
   existing counterexample).
10. `PRIOR_ART_AND_NOVELTY_MATRIX.md:362`: "cost C = eN(1 + alpha * sum_t pe)" is wrong. Eq. 3 is
    eN(alpha*||theta||_1 + sum_t pe_{r(t),t}). Line 366 claim "Verification: FULL ... algorithm details rely on the
    repo's implementation audit" is now superseded by this spec. Line 919 states a risk-averse quantile rule
    appears "only in a vendor blog"; the quantile rule (Eq. 16, 21-22, delta=0.95) is in the paper itself.
11. `PRIOR_ART_AND_NOVELTY_MATRIX.md:363`: "performance forecast from low-data regression" is accurate;
    "Guarantees: none for the decision rule" is accurate.
12. Docstring `upf_retraining.py:3-5` ("independent implementation"): accurate; it should also say that
    sigma_phi, clipping, Monte Carlo size and draw sharing are not specified by the paper.

**Current honest tier of existing code:** T2-in-progress for the native retraining problem (equations
traced, but sigma_phi/clipping/MC choices are the repo's own); **not T1; not T3** (nothing in ShiftLab's
two-model switch contract uses it). In the benchmark it should not appear under the paper's name.

## 8. Paper-stated numbers and identities usable as reproduction tests

- Metric identity (Eq. 24): C_hat = alpha*#retrains + sum over 8 online steps of (1 - accuracy). Check
  on Table 2 (electricity, p. 8), stated means (rounded; use tolerance about 0.05):
  - alpha = 0.9: UPF 0.1 retrains, avg acc 0.68, C_hat 2.69; oracle 0 retrains, acc 0.66, C_hat 2.68
    (0.9*0 + 8*0.34 = 2.72).
  - alpha = 0.1: UPF 2.5 retrains, acc 0.75, C_hat 2.24 (0.25 + 2.00 = 2.25); oracle 5.6, acc 0.83,
    C_hat 1.93 (0.56 + 1.36 = 1.92).
- Table 1 (p. 8): AUC of C_hat for UPF: electricity 2.5782, Gauss 0.3829, circles 0.0668, airplanes 2.2865,
  yelpCHI 0.1293, epicgames 0.3189, iWild 3.0498; oracle row 2.4217, 0.3724, 0.0627, 2.2298, 0.1275, 0.3170, 2.4973.
  Reproducing these needs the original data splits and sampled sequences (UNVERIFIED reproducible: only
  electricity and airplanes are public; synthetic generator formulas in A.6 are garbled in the text
  extraction and follow Mahadevan and Mathioudakis 2024, not read).
- Table 3 (A.1, p. 13): PF (delta = 0.5) vs UPF (delta = 0.95), e.g. airplanes 2.3688 vs 2.2688, circles 0.0697
  vs 0.0670, with Wilcoxon-significant differences on all but electricity.
- Prop. 3.1 (p. 4) and A.4.1 (p. 17): on Gauss, with L set to the empirical max gap, "no retrain
  needed" for alpha > 0.96, while the oracle stops retraining near alpha about 0.5. Per Sec. 5 above, the printed
  bound as stated fails on small instances; use the floor+1 form for any test.
- Structural tests derivable without data: (i) delta = 0.5 recovers the median-cost rule (p. 5);
  (ii) alpha = 0 with strictly better fresh model always retrains; (iii) alpha above the oracle's zero-retrain
  value gives zero retrains under exact pe (A.4.1); (iv) Beta conversion round-trip: mean/variance recovered
  from Eq. 51-52.

## 9. Open questions / UNVERIFIED

- Official code or OpenReview supplementary: could not be read (OpenReview bot challenge; `mlresearch/v267`
  asset directory listing returned 404). Treat as "no code found", not as "no code exists".
- sigma_phi estimator, clipping, Monte Carlo draw count, draw sharing across branches, quantile estimator,
  z_shift assignment to training pairs, the pair convention giving |M_<0| = 21: not in the paper.
- Whether f_t is trained on D_t and evaluated on a held-out part of D_t (A.6 mentions train/val/test splits;
  Sec. 3 says "data acquired up until time t"): ambiguous.
- Appendix A.10 per-dataset figures, A.11.1 offline-RL baseline, A.12 CARA relation (Eq. 82-86), A.13 and
  A.14 (Wild-Time) tables: skimmed for relevance only, not checked line by line.
- Table 4 column alignment (alpha_max, |D|) inferred from text-extraction order; verify against the PDF
  image before using the numbers as test targets.
- Retriever derivation of the corrected Prop. 3.1 bound rests on my reading of Eq. 39-45 and a random
  brute-force check; the independent checker should re-derive it.
- Whether T3 adaptation helps ShiftLab is untested; none of the adaptation above has been run.
