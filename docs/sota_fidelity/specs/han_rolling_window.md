# Spec: Han, Huang, Wang adaptive rolling window (ARW) for model assessment and selection

Retrieved 2026-11-06 by retrieval subagent. All page numbers are PDF pages of arXiv v2 (26 pp).
Text extracted with `pdftotext -layout` from the downloaded PDF (no code executed). Appendix proofs
(A.2 to A.4, B.x) were NOT read line by line: marked UNVERIFIED where relied on.

## 1. Citation, version, code

- Elise Han, Chengpiao Huang, Kaizheng Wang, "Model Assessment and Selection under Temporal
  Distribution Shift", ICML 2024, PMLR 235:17374-17392
  (https://proceedings.mlr.press/v235/han24b.html).
- Version read: arXiv 2402.08672v2 (3 Jun 2024), https://arxiv.org/pdf/2402.08672v2, 26 pages.
  The ICML proceedings PDF was not read separately (UNVERIFIED that it is identical to v2).
- Official code: https://github.com/eliselyhan/ARW, default branch `main`, pinned HEAD
  `c48f8303d317f143d6a203d88347c7fada9aee55` (2026-08-27, "Update README.md"). Last code change
  `839f8569` (2024-07-15). Paper p.11 L670 links this repo. No LICENSE file in the tree at this SHA
  (checked from the git tree listing): reuse terms are unknown; a line-by-line port is a
  derivation of unlicensed code, so prefer re-implementation from the equations and use the repo
  only as a numeric oracle.
- Files read at the SHA: `code-synthetic-data/ARW.py` (168 lines), `code-housing/ARW.py`,
  `code-synthetic-data/algo_syn.py`, `code-housing/realdata_housing.py` (grep only),
  `README.md`. Not read: arxiv notebook/`arxiv_read.py` beyond grep, `figures.ipynb` beyond grep.

## 2. Native problem and estimand

- Setting (Sec. 2, p.3): at each period j a batch of B_j i.i.d. samples from P_j, independent of
  history; goal at time t is the current risk L_t(f) = E_{z~P_t} l(f,z) (Problem 2.1), or choosing
  r in [m] with L_t(f_r) close to min (Problem 2.2). Models f are fixed given the data; loss is
  bounded in [a,b] (Assumption 3.1, p.3).
- Reduction (Problem 3.1, p.3): estimate mu_t = mean of Q_t from datasets D_1..D_t, D_j of B_j >= 1
  i.i.d. draws from Q_j. Assessment is u_{j,i} = l(f,z_{j,i}). Comparison (Alg 2, p.8) is
  u_{j,i} = l(f_1,z_{j,i}) - l(f_2,z_{j,i}), i.e. the paired gap Delta_t = L_t(f_1) - L_t(f_2).
- No null hypothesis, no alarm, no error control on a decision: it is an estimation / selection
  procedure with an oracle inequality. Feedback: every sample of every period is labelled (full
  information, no delay, no cost, no selection).

## 3. Exact algorithm

Notation M = b - a. Window k in [t] = the k most recent periods. B_{t,k} = sum_{j=t-k+1..t} B_j.

1. Window mean, Eq. (3.1) p.3: mu_hat_{t,k} = B_{t,k}^{-1} sum_{j=t-k+1..t} sum_i u_{j,i}.
   Summary-statistic form, Eq. (3.7) p.5: mu_hat_{t,k} = B_{t,k}^{-1} sum_j B_j mu_hat_j.
2. Window sample variance, Eq. (3.2) p.4: v_hat^2_{t,k} = (B_{t,k}-1)^{-1} sum (u - mu_hat_{t,k})^2.
   Summary form, Eq. (3.8) p.5: v_hat^2 = B_{t,k}/(B_{t,k}-1) * ( B_{t,k}^{-1} sum_j B_j omega_hat_j
   - mu_hat^2_{t,k} ), omega_hat_j the within-period second moment.
3. Variance proxy, Eq. (3.3) p.4:
   psi_hat(t,k,delta') = M if B_{t,k}=1; else
   v_hat_{t,k} sqrt( 2 log(2/delta') / B_{t,k} ) + 8 M log(2/delta') / ( 3 (B_{t,k} - 1) ).
4. Bias proxy (Goldenshluger-Lepski style), Eq. (3.5) p.4:
   phi_hat(t,k,delta') = max_{i in [k]} [ |mu_hat_{t,k} - mu_hat_{t,i}| - ( psi_hat(t,k) + psi_hat(t,i) ) ]_+ .
   Paper states the inspiration is Goldenshluger-Lepski (Sec. 1, p.2 L71-73).
5. Algorithm 1 (p.6): for k=1..t compute the above; choose any
   k_hat in argmin_k { phi_hat(t,k,delta') + psi_hat(t,k,delta') }; output mu_hat_{t,k_hat}.
6. Algorithm 2, model comparison (p.8): run Alg 1 on u = l(f_1) - l(f_2) to get Delta_hat_{t,k_hat};
   output f_1 if Delta_hat <= 0, else f_2.
7. Algorithm 3, single-elimination tournament (p.10): S = ceil(log2 m) rounds; split the survivor
   set F_s into disjoint pairs (one possible singleton); run Alg 2 on each pair; winners form
   F_{s+1}; |F_{s+1}| <= ceil(|F_s|/2); Alg 2 is called exactly m-1 times (p.10 text after Alg 3).
   The pairing order is not specified by the paper.

Code correspondence at SHA (`code-synthetic-data/ARW.py`, identical logic in `code-housing/ARW.py`):
- `prepare` lines 6-47: reverse-cumulative sums give B_{t,k}, mu_hat_{t,k}, v_hat_{t,k} for all k
  (Eq 3.7/3.8). Line 30-35 special-cases B_{t,1}=1. Line 40 clamps negative variance to 0 (the
  housing copy, line 35, does not clamp; the paper does not mention it).
- `ARWME` lines 53-88: psi_hat line 75-77 (B=1 gives M; else Eq 3.3 with the 8/3 factor, matches);
  phi_hat lines 79-84 (matches Eq 3.5); `k_hat = argmin(...) + 1` line 87 (first minimiser).
- `pairwise_comparison` lines 94-113: u = loss_1 - loss_2; returns 1 only if delta_hat < 0 (line 110),
  so ties go to model 2. DISCREPANCY with Alg 2 (<= 0 gives model 1).
- `tournament_selection` lines 119-164: shuffles candidates with `np.random.seed(seed)` (seed 2024),
  gives the last element a bye if odd, pairs consecutive elements. Random pairing and seed are
  code-only choices (paper unspecified).

## 4. Hyperparameters and defaults in the paper's experiments

- Experiments set delta' = 0.1 and M = 0 "throughout" (Sec. 5, p.10-11, L651-667). Code defaults
  agree: `delta=0.1, M=0` (ARW.py line 53/94/119; `realdata_housing.py:161`; `figures.ipynb`
  cell: "delta = 0.1; M = 0; seed = 2024"). Note `algo_syn.py` lines 63/116 default M=10 but the
  notebook overrides to 0.
- Consequence: with M = 0 the lower-order Bernstein term in Eq. (3.3) vanishes and psi_hat(B=1)=0,
  although the theory (Lemma 3.2, Thm 3.1) needs M = b - a and delta' = delta/(3t). The reported
  numbers therefore come from a variance-only proxy with a fixed delta'=0.1, outside the stated
  theorem. This is a paper-vs-experiment gap; do not cite the theorem for a port that copies M=0.
- Window set: ARW searches ALL k in [t] (no grid). Fixed-window baselines V_k use
  I = {1,4,16,64,256} (p.11).
- Synthetic: 100 periods, 20 trials, validation sizes uniform on {2,3,4}, train = 3x validation
  (p.11). arXiv topic data: 200 weeks, train 15 / val 5 samples per week. Housing: 192 months,
  60/20/20 split, 10 candidate models (5 windows x {RF, XGBoost}) (p.14).
- Dependencies in code: numpy only for ARW.py; sklearn, xgboost only for experiment scripts.

## 5. Guarantee

- Thm 3.1 (p.5, oracle inequality): under Assumption 3.1 (bounded loss), independent batches with
  i.i.d. samples inside a period, fixed t, delta' = delta/(3t): with probability >= 1 - delta,
  |mu_hat_{t,k_hat} - mu_t| <~ min_k { phi(t,k) + psi(t,k,delta) }, where phi(t,k) =
  max_{t-k+1<=j<=t} |mu_j - mu_t| (bias) and psi is the Bernstein half-width with true variance
  (Cor. 3.1, p.4). "<~" hides a log t and log(1/delta) factor. Chain: Cor 3.2 (event holds with
  prob >= 1-2t delta'), Lemma 3.3 (0 <= phi_hat <= 2 phi), Lemma 3.4 (factor 3, proof p.6-7),
  Lemma 3.2 (second bound controls psi_hat - psi). Appendix A.4 full proof: UNVERIFIED.
- Thm 4.1 (p.8): Alg 2 for two models, excess L_t(f_hat) - min_r L_t(f_r) bounded by the same
  bias-variance min with sigma_tilde^2 the average variance of the loss GAP; via Lemma 4.1.
- Thm 4.2 (fast rate, p.9) and Thm 4.3 (tournament, p.10, delta' = delta/(3 m^2 t)): need
  Assumptions 4.1-4.3 (bounded response, bounded models, squared loss, NO covariate shift),
  i.e. bounded regression only. Binary 0/1 classification is explicitly only conjectured
  ("We believe ... analysis still goes through", p.9).
- NOT covered: delayed, missing, selectively queried or adaptively sampled labels; dependence
  across periods or within a period; data-dependent f; sequential / anytime-valid control over t
  (the statements are for one fixed t, delta'=delta/(3t) shrinks with t; no uniform-in-t claim
  was seen, Remark 2 p.7 only mentions a possible log log t improvement via martingale tools);
  periods with B_j = 0 (Problem 3.1 requires B_j >= 1); any switching cost or label cost; the M=0
  setting used in experiments. It certifies no Type I error: nothing here is a test of harm.

## 6. Mapping to ShiftLab's deployment contract (T=2000, B=200, c_q=0.05, c_s=5, delayed labels)

Contract facts read: `scripts/sota_sprint/bench.py:25` CONTRACT = T=2000, budget=200, cq=0.05,
cs=5.0, alpha=0.05; `src/shiftlab/contract/interface_v2.py:82-101` MonitorV2/Switcher protocol
(`receive` delivers delayed labels, `propensity` precedes the harness coin, `observe` gets
Feedback/MissingFeedback/PendingQuery, `choose` returns 0=incumbent 1=candidate).
Whether "B=200" is a label count (as I read the simulator `remaining_budget` int,
`sota/simulator.py:136-163`) or a money budget in loss units was not resolved: UNVERIFIED.

Proposed T3 adapter ("label-clock ARW"):
1. Estimation target: Delta_t = L_t(incumbent) - L_t(candidate), per-round paired loss gap
   (Alg 2 with f_1=incumbent, f_2=candidate; the tournament reduces to one match, m=2).
2. Label clock: Han assumes a labelled batch every period. Under sparse queries, define a
   "period" by label arrival order, B_j = 1 (Example 3.2 case, p.6, where bounded drift
   gives k* ~ Delta^{-2/3}), OR by fixed wall-clock bins of w rounds with B_j = number of labels
   RELEASED in that bin (bins with B_j = 0 are skipped, which changes "k most recent periods"
   semantics and is a deviation). Windows are measured in label counts under B_j=1 and are not
   comparable to the paper's calendar windows. Delayed labels are inserted in release order but
   attributed to the original event index t (Feedback.t), so the bias term phi sees
   distribution at the labelled round, not at release; the estimand "L_t" then lags by the
   unknown delay (Thm 3.1 has no delay term).
3. Selective sampling: ARW assumes labelled samples are i.i.d. draws of the period distribution.
   If acquisition is disagreement-gated (as in `controls.py:28-50`), unlabelled agreement rounds
   have u = 0 exactly under 0/1 loss, so one valid choice is to estimate the disagreement-rate
   weighted gap, or to use Horvitz-Thompson u~ = u * 1[queried]/q with q the frozen
   propensity, range [-1/q_min, 1/q_min], giving M = 2/q_min (Eq 3.3 loses power as M grows).
   Both are deviations; neither has a theorem here.
4. Decision rule (code semantic, Alg 2): deploy candidate iff Delta_hat_{t,k_hat} > 0
   (note: Alg 2 says incumbent if <= 0, code says incumbent only if < 0). There is no
   significance threshold, so with c_s = 5 the unmodified rule switches on any positive point
   estimate; a switch-cost margin (switch iff Delta_hat > cost-derived margin) is an
   additional deviation. No alpha is used; alpha=0.05 has no role.
5. Acquisition: ARW has none. Reuse the shared pacer (Section 7) so labels, not the estimator,
   differ across competitors; this must be reported as a pairing of ARW's estimator with ShiftLab's acquisition.
6. delta': use delta/(3t) as in the theorems or fixed 0.1 as in the experiments; report which.
   M: use b-a (theory) not 0 (experiments).

Achievable tier:
- Core estimator on fully labelled, equally spaced batches: T1-portable (author code at pinned
  SHA; can be checked numerically against it). Not yet done.
- Deployment version (label clock, sparse delayed paid labels, switching): T3. Must be named
  "ARW-style label-clock window selection", never "Han et al." in tables.

## 7. Existing ShiftLab code

- `grep -ril "rolling.window\|goldenshluger\|lepski\|iupm" src scripts` returns only
  `scripts/validate_fitted_conformal.py` and `scripts/time_series_real_diagnostics.py`; neither
  implements ARW (matches are generic "rolling window" text; contents not inspected beyond the
  grep hit). So no ARW implementation exists.
- Reusable components:
  - Budget pacer: `scripts/promising_directions/sota/competitors/controls.py:28-50`
    (`PacedDisagreementAcquisition`, remaining/expected-disagreements pacing, floor p_min=0.05).
  - Deque windows (not paired-gap estimators): `competitors/xu_acquisition.py:242,268`
    (`window=256` deque of scores), `competitors/model_selector.py:328-342` (`window=50` pool).
  - Adapter style reference: `competitors/model_selector.py:354-385` (`request_labels`
    returns `QueryRequest(requested, probability)`, `observe` consumes `ReleasedFeedback`
    with `model_losses` per frozen model, from which the paired gap is `l0 - l1`).
  - No existing windowed paired-difference estimator with a variance-adaptive window was found
    by grep for "window|rolling|sliding" in `competitors/` and `sota/` (only those hits).
- Honest current tier: not implemented.

## 8. Reproduction tests

- Identities (printed): phi_hat in [0, 2 phi] when event (3.4) holds (Lemma 3.3); summary
  statistics form (3.7)-(3.8) equals (3.1)-(3.2); Alg 3 makes exactly m-1 Alg-2 calls; k_hat in [t].
  A port can be unit-tested against `prepare`/`ARWME` of the pinned author code on random inputs.
- Numbers (printed): Table 1 (stationary, mean excess risk, sigma^2=1 / 10): V_ARW 0.015 / 1.293,
  V_1 0.043 / 4.117, V_256 0.010 / 0.982 (p.12). Table 2 (Example 5.2): V_ARW 0.139 / 2.052 (p.12).
  Table 3 arXiv (x1e-3): V_ARW 2.4, V_1 6.7, V_256 1.9 (p.13). Table 4 housing MSE: V_ARW 0.071,
  V_1 0.071, V_256 0.095 (p.14). Reproducing Table 1/2 needs the synthetic generator with seed
  2024 (`generate_syn_data.py`, not read): UNVERIFIED feasibility; they are 20-trial averages
  so only approximate agreement is expected.

## 9. Open questions / UNVERIFIED

- Appendix proofs (A.1-A.4, B.1-B.3) not read; theorems quoted from the main text.
- Whether the ICML camera-ready differs from v2.
- Behaviour of `prepare` when a period has B_j = 0 (np.mean of an empty slice gives nan);
  inferred from reading, not executed.
- Handling of selective/IPW-weighted labels has no support in the paper; any validity statement
  for the adapter would be new and unproven.
- Whether `figures.ipynb` reproduces Table 1 exactly (notebook not run).
