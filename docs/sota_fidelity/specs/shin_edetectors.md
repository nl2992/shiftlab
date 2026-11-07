# Spec: Shin, Ramdas, Rinaldo, E-detectors (e-SR, e-CUSUM, bounded-mean betting e-detector)

Status: retrieval spec (step 1). Not yet independently checked. Written 2026-11-06. Nothing downloaded
was executed; code was only read.

Citation keys: "v4 pN" = arXiv v4 PDF page N (50 pp); "N(k)" = NEJSDS PDF page (printed page number
229+). Equation numbers below are arXiv v4 flat numbers. NEJSDS numbers are per section:
Sec 2: v4 (n) = NEJSDS (2.n-5); Sec 3: (3.n-19); Sec 4: (4.n-41); Sec 5: (5.n-64). Verified on
(6)=(2.1), (7)=(2.2), (41)=(3.22), (48)=(4.7), (70)=(5.6), (72)=(5.8), (75)=(5.11).

## 1. Citation, version read, code

- Jaehyeok Shin, Aaditya Ramdas, Alessandro Rinaldo. "E-detectors: A Nonparametric Framework for
  Sequential Change Detection". New England Journal of Statistics in Data Science (NEJSDS), vol 2,
  pp 229-260, 2024 (page header "Volume 2, 229-260 (2024)"; site metadata: issue 2, 2023/12/01;
  "Accepted 12 October 2023"). DOI 10.51387/23-NEJSDS51. Note: the user brief said 2024; the PDF
  header says 2024, the journal landing page says Dec 2023 online date.
- Published PDF read: https://nejsds.nestat.org/journal/NEJSDS/article/59/file/pdf (32 pp,
  sha256 6e2ac474...3c6f). arXiv: 2203.03532 v4 (29 Oct 2023, 50 pp, sha256 564dc11f...a1c;
  "49 pages, 7 figures"). v1-v3 not read.
- Differences v4 vs NEJSDS: same section structure, algorithms, theorem numbers, figures, constants.
  Only a spot check was done (91.3, 123.7, 69 baselines, 190 baselines, 0.0125, 5000 repetitions,
  Kmax=1000 all present in both; Alg 1/2/3/4 and Thm 4.3 / Cor 4.6 / Lemma 6.1 present). Equation
  numbering is per-section in NEJSDS, flat in arXiv (mapping above). A full diff was NOT done:
  UNVERIFIED that no wording change exists. The typo "M_0^{mSR} = M_0^{mCU} := 1" in (24)/(25)
  appears in BOTH versions (NEJSDS Sec 3.1) and contradicts (27)/(28) and Algorithm 1 line 4 (M_0 = 0).
- Official code (found via the paper footnote v4 p4 and `gh api users/shinjaehyeok/repos`):
  - paper repo `shinjaehyeok/e_detector_paper` @ `2fbf585457e31495978cdf7c075f43d0b15961d2`
    (R scripts for the NBA example and the Bernoulli/GLR simulation; read NBA_example.R,
    simulation_study_ber_with_glr.R headers only).
  - R package `shinjaehyeok/stcp` @ `c9ff9a69bc18a82c909f6c4c8e17cc0def0069ae` (v0.9.2.1000, MIT;
    read build_stcp_model.R, compute_baseline.R, e_detectors.R, mix_of_e_detectors.R, run_stcp.R,
    psi_fn.R).
  - R/C++ package `shinjaehyeok/stcpR6` @ `9eaafb491f315094861d1eea712677c4468dfb51` (v0.9.8.9000;
    read R/stcp.R, R/helper_functions.R, R/compute_baseline.R, src/baseline_increment.h, README).
    This is the newest implementation and the only one with a `two.sided` option.
  - Rscript exists locally (`/opt/homebrew/bin/Rscript`); not used, per the no-execution rule.
  - Scratch: `.../scratchpad/edet/{shin,nejpub,code_paper,code_stcp,code_r6}`.

## 2. Native problem and estimand

- Stream X_1, X_2, ...; unknown change time nu; pre-change class P of laws over infinite sequences
  (not iid; e.g. conditional mean <= m), post-change class Q (v4 p6, Sec 2.1; Remark 2.1 allows nu to
  be a stopping time and Q to depend on the past).
- Estimand/guarantee: average run length ARL = E_inf[N*] >= 1/alpha (v4 p3 eq (1)); probability of
  false alarm (PFA) only via Remark 2.7. Delay metrics J_L, J_P (eq (2),(3)).
- Null: pre-change class only; filtration F is the data filtration, may be coarsened or enlarged
  (v4 p6). Feedback: full observation of X_n each step; no labels, costs, budgets, or delays.

## 3. Exact algorithm

Core definitions (v4):
- e-detector: E_{P,inf}[M_tau] <= E_{P,inf}[tau] for all stopping times tau, all P in P (Def 2.2,
  eq (6), p6). Mixtures of e-detectors are e-detectors (Prop 2.3, p7).
- Thm 2.4 (p7): N* = inf{n >= 1: M_n >= 1/alpha} gives inf_P E N* >= 1/alpha. One-line proof p7;
  full proof App A.1 (v4 p38; N(251)).
- e_j-process Lambda^(j) (Def 2.5, eq (9), p8); SR and CUSUM e-detectors (Def 2.6, eq (10), p8):
  M^SR_n = sum_{j<=n} Lambda^(j)_n and M^CU_n = max_{j<=n} Lambda^(j)_n, M_0 = 0.
- Baseline increment L_n >= 0 adapted, sup_P E[L_n | F_{n-1}] <= 1 (Def 2.8, eq (11), p8);
  baseline e_j-process Lambda^(j)_n = prod_{i=j}^n L_i (eq (12), p9).
- Recursions (eq (13),(14), p9): M^SR_n = L_n (M^SR_{n-1} + 1); M^CU_n = L_n max(M^CU_{n-1}, 1);
  M_0 = 0.
- Procedures (Def 2.12, eq (15),(16), p10): N_SR = inf{n: M^SR_n >= 1/alpha};
  N_CU = inf{n: M^CU_n >= c_alpha}; c_alpha = 1/alpha always valid; smaller c_alpha needs knowledge
  of the pre-change law (Sec 2.5 and Remark 2.13, p10).

Mixtures and stakes (Sec 3, v4 pp14-16):
- Fixed mixture (eq (22),(23) integral form; (24),(25),(26) discrete form): M^mSR_n =
  sum_k w_k M^SR_n(k), M^mCU_n = sum_k w_k M^CU_n(k). That is, a mixture of per-lambda detectors,
  NOT a max over starts of a lambda-mixture. Per-component recursion (27),(28).
- Replacing the mixture by sup over lambda is NOT valid in general (Remark 3.1, p14).
- Adaptive (growing) mixtures, scheduling function K(n) (eq (29),(30), re-weight gamma_j; recursions
  (31),(32)); validity Prop 3.3 (p16, proof App A.2). Delay bound Thm 3.4 eq (36)-(41).

Exponential baseline (Sec 4, pp17-23):
- Def 4.1, eq (42): L^lambda_n = exp{lambda s(X_n) - psi(lambda) v(X_n)}, psi convex, psi(0)=psi'(0)=0.
  Delay constants eq (43)-(45): mu = E s, sigma^2 = E v, Delta_op = mu/sigma^2, lambda_op = grad psi*(Delta_op).
- Algorithm 1 (p20), mixture of e-SR for known [Delta_L, Delta_U] and Kmax:
  `{lambda_k}, {w_k}, g_alpha <- computeBaseline(alpha, Delta_L, Delta_U, Kmax)`; M_0(k)=0;
  line 9 `M_n(k) <- exp{lambda_k s(X_n) - psi_k v(X_n)} * (M_{n-1}(k) + 1)`; line 10
  `M_n = sum_k w_k M_n(k)`; stop when M_n >= 1/alpha. e-CUSUM: replace line 9 by eq (46)
  `M_n(k) <- L * max(M_{n-1}(k), 1)`.
- computeBaseline = Algorithm 3 (App B.1, v4 p45; N(256)), eqs (94)-(96):
  1. lambda_L = grad psi*(Delta_L), lambda_U = grad psi*(Delta_U), D_L = psi*(Delta_L), D_U = psi*(Delta_U).
  2. If log(1/alpha) <= v_min psi*(Delta_L): single baseline (K_alpha=1, lambda_1=lambda_L, w_1=1).
  3. g_alpha = inf{g > log(1/alpha): e^{-g} 1(g > v_min D_U) + min_{k<=Kmax} k exp(-g (D_U/D_L)^{-1/k}) <= alpha}
     (eq (94); bisection in Algorithm 4, App C, v4 p50; N(258)).
  4. K_alpha = argmin_k k exp(-g_alpha (D_U/D_L)^{-1/k}) (eq (95)); eta_alpha = (D_U/D_L)^{1/K_alpha}.
  5. lambda_0 = lambda_U, lambda_{K_alpha} = lambda_L, interior Delta_k solves psi*(z) = D_U eta^{-k}.
  6. W = e^{-g} 1(g > v_min D_U) + K_alpha e^{-g/eta}; w_0 = e^{-g} 1(.)/W, w_k = e^{-g/eta}/W (eq (96)).
  So the weights are geometric-grid, equal on interior points, with an extra atom at lambda_U.
- Thm 4.3 (p19): both mixtures control ARL by 1/alpha; for iid post-change,
  J_L <= g_alpha/D(Q||P) + Var(log L)/D^2 + 1 (eq (47)); g_alpha < inf_eta{eta log(1/alpha) + log(1 + log_eta(psi*(Delta_U)/psi*(Delta_L)))} (eq (48), Prop B.2).
- Algorithm 2 (p23) adaptive e-SR, no separation: inputs Delta_L < Delta_0, importance weight r,
  scheduling m, K_0; boundary function g (eq (59)), zeta-based s (eq (60),(61)), K(n) = K_L + ceil(m log_eta n)
  (eq (63)); bound Cor 4.6 eq (64). Numeric values of r, m, K_0 are NOT stated in the main text
  (grep found none): UNVERIFIED whether the appendix or code fixes defaults.

Bounded-mean betting e-detector (Sec 5.2, v4 pp26-29; NEJSDS Sec 5.2 pp 247-248):
- Setup: X_n in [0,1] (raw data normalised, Plus-Minus X = (X~+80)/160); pre-change
  E[X_n | F_{n-1}] <= m for all n; post-change conditional mean >= m + delta (p27).
- Baseline increment, eq (70): L^lambda_n = 1 + lambda (X_n/m - 1), lambda in (0,1). Validity
  from E[X_n | F_{n-1}] <= m (p27). Equivalent to the Waudby-Smith-Ramdas betting increment (p27).
- Sub-exponential lower bound, eq (72): L~^lambda_n = exp{lambda(X_n/m - 1) - psi_E(lambda)(X_n/m - 1)^2} <= L^lambda_n,
  psi_E(lambda) = -log(1-lambda) - lambda, s(x) = x/m - 1, v(x) = (x/m-1)^2, psi*_E(u) = u - log(1+u)
  (p28). Range for Algorithm 1: Delta_L = m delta/(1-m)^2, Delta_U = m(1-m)/delta^2 (eq (75), p28).
  Paper states the original eq (70) increments are "always more sample-efficient" (p28) but runs
  Algorithm 1 on (72).
- Paper settings for the example: alpha = 1e-3, Kmax = 1000, m = 0.494, delta = 0.0125,
  Delta_L = 0.024, Delta_U = 1600, 190 baselines returned (p28). Bernoulli win-rate example:
  p0 = 0.49, q0 = 0.51, Delta_L = 0.02, Delta_U = 0.41, 69 baselines (p26).
- CODE vs PAPER (stcp@c9ff9a6 R/build_stcp_model.R `build_stcp_bounded` and R/e_detectors.R
  `generate_log_bounded_base_fn`): lambda grid and weights come from the sub-E psi (as in (72)) but
  the running increment is log(1 + lambda*((x-lo)/m_gap - 1)), i.e. eq (70), not (72). Defaults:
  `k_max = 1000`, `tol = 1e-6`, `var_lower = 0`, `var_upper = range^2/4`, `delta_upper = bound_upper - m_pre`
  (when equal, var_upper is forced to 0, reproducing eq (75)). `update_log_e`: SR is
  `logSumExp(prev,0) + log L`, CUSUM `max(prev,0) + log L`, init `-Inf` (M_0 = 0). Alarm uses
  strict `>` log(1/alpha) (`run_stcp`), paper uses `>=`. Which increment produced the paper's
  reported detection dates is UNVERIFIED.
- Recommended threshold: `log(1/alpha)` for SR (stcpR6 helper_functions.R roxygen, ~line 152).

## 4. Hyperparameters and defaults used in the paper's experiments

alpha = 1e-3 (ARL 1000) in both NBA examples (p4, p26, p28); alpha = 1/500 in the simulation (p30);
Kmax = 1000; Bernoulli simulation p0 = 0.5, p1 = 0.6, [0.51, 0.99] known so Delta_L = 0.01,
Delta_U = 0.49, 5000 repetitions, nu in {0,...,500}, horizon 1000 (p30). Reported numbers:
worst average delay oracle CUSUM 91.3 +- 1.7, GLR 123.7 +- 2.7 (p31). e-SR with the plain log(1/alpha)
threshold; oracle CUSUM, GLR and e-CUSUM use simulated exact thresholds (p29-30). Cavaliers: e-SR
detects 2015-02-26 (win rate, Fig 2), game 378 / 2015-03-10 (Plus-Minus, Fig 3), e-CUSUM 2015-04-05
and game 444 / 2016-02-06 (p26, p29).
stcpR6 package defaults: `k_max = 1000`; threshold recommended log(1/alpha); default
`delta_upper` for Bounded two-sided `min(1-m, m) - 0.001` (helper_functions.R checkDeltaRange).

## 5. Guarantee

- ARL >= 1/alpha for any e-detector, any dependence, any change point rule (Thm 2.4; Remark 2.1:
  ARL results need no assumption on nu or Q). Needs only the per-start conditional bound (11)
  w.r.t. the same filtration. Valid for the whole composite class P (e.g. non-stationary
  conditional means <= m).
- e-SR with threshold 1/alpha dominates e-CUSUM with the same threshold; they recommend e-SR when
  pre-change is non-stationary (Remark 2.13, p10; and eq (35)).
- PFA: only a remark (Remark 2.7, p8): initial weights summing to <= 1 give sup_P P(tau<inf) <= alpha,
  at the cost of delay growing like log nu. The proof is not in the paper (grep of v4); treat as
  UNVERIFIED in-paper. (Saha-Ramdas Thm 2.3 proves this construction; see that spec.)
- Delay bounds need post-change independent of pre-change and strongly stationary, L_n a function
  of m+1 recent observations (Prop 2.14, Thm 3.4, Thm 4.3 iid).
- Does NOT cover: delayed or missing feedback, importance-weighted subsampling, label budgets,
  switch costs, repeated restart after an alarm (ARL only, one alarm), two-sided alternatives,
  ARL of the post-restart process. Also not covered: the probability of any false alarm within a
  finite horizon at threshold 1/alpha. Saha-Ramdas attribute "P(tau <= m) <= m/A" to e-detectors,
  but v4 contains no such statement (grep); it follows from the e-detector inequality (Saha-Ramdas
  Thm 2.2 proof).

## 5b. Two-sided detector (challenger better OR deployed worse)

- The paper has NO two-sided construction. grep for two-sided / both directions: nothing; Sec 4.1
  says "one-sided"; the only combination discussed is min or average across streams (Sec 6.3, p34).
- Official code: stcpR6 `Stcp$new(alternative = "two.sided")` (R/stcp.R l.83-150;
  R/helper_functions.R `convertDeltaToExpParams`, ~l.257-277): runs `compute_baseline` twice with
  alpha/2 (greater and less), concatenates lambdas and weights with each weight halved, lambda for
  "less" is negated and for Bounded set to -m * lambda_less / (1-m) (algebraic flip of
  1 + lambda((1-X)/(1-m) - 1)). Detector = one mixture e-detector, threshold log(1/alpha). Its null is
  the point null E[X | F] = m_pre (both one-sided supermartingale conditions at once). The stcp
  package instead has `is_flipped` (input 1-X) and `combine_stcp(obj1,obj2,w)` (threshold from
  alpha = w alpha1 + (1-w) alpha2).
- Direct construction (my derivation, uses Prop 2.3 only; not a paper statement): for X in [0,1] with
  m, let M+ be the e-detector for E[X|F] <= m and M- the one for E[X|F] >= m. Under E[X|F] = m both are
  e-detectors, so (M+ + M-)/2 is one, and alarm on (M+ + M-)/2 >= 1/alpha (equivalently either one >= 2/alpha
  suffices) gives ARL >= 1/alpha. Each side separately at 1/alpha does not carry this guarantee
  jointly. Under a one-sided null (mean <= m) M- is not a supermartingale, so the joint guarantee
  needs the equality null.
- Rollback is naturally sequential one-sided: after promotion the null is "challenger not worse"
  (E[d] <= 0 in the reversed sign), a new one-sided detector with its own alpha. That is how RMM and
  E_rb do it (Sec 7 below); it controls error probabilities per phase, not a joint two-sided ARL.

## 6. Mapping to ShiftLab's contract (T=2000, B=200, c_q=.05, c_s=5, two frozen models, delayed labels)

- Paired score: d_t = L_deployed - L_challenger in [-1,1] (bounded). Map to X = (d+1)/2 in [0,1]
  with m = (1+margin)/2; eq (70) factor becomes 1 + (lambda/m)(X - m). This is algebraically the
  same betting factor as ShiftLab's `1 + stake * x / B`; the lambda grid (Algorithm 3) and weights
  (eq (96)) are NOT what ShiftLab uses.
- Label budget: only queried events yield d_t. Either (a) calendar clock with factor 1 on
  unqueried events and IPW score q/frac * d (range 1/frac, loses efficiency and needs the range
  bound), or (b) label clock on queried events only (valid if the query rule is predictable and
  independent of the unobserved outcome given the past; selection into the sequence changes the
  estimand to queried-event mean). Paper covers neither; both are adaptations (T3).
- Delay: valid with the release-order filtration for fixed delay (not in the paper; the same
  argument as ShiftLab's docs/h2c_restart/VALID_RESTART_MIXTURE.md). Random out-of-order release:
  UNVERIFIED.
- Costs: alpha, c_q, c_s do not enter the construction. Any economic gate (e.g.
  `(T-t)*margin >= switch_cost`) is a ShiftLab add-on.
- Achievable tier: T1 only for the plain full-information bounded/Bernoulli/Gaussian detector
  (port stcp/stcpR6 numerically against the R code; R is available; reproduction tests in Sec 8).
  T2 for the recursion lines (13),(14),(26),(27),(28) and Algorithm 3 from printed equations.
  Anything with B=200, delays and IPW: T3, never called "Shin et al.'s e-detector" without the
  deviation list.

## 7. Existing ShiftLab code

Baseline recursions:
- `src/shiftlab/dive/horizon_edetectors.py:134-137`: SR `log f + logaddexp(0, log M)`; CUSUM
  `log f + max(0, log M)`; init -inf (M_0 = 0). MATCHES (13),(14) and the per-lambda mixture (26),
  because it mixes per-stake CUSUMs (l.139, `logsumexp(components + log_weights)`), matching (25),
  not max-of-mixture.
- l.130-132 factor `1 + stake * x / B`; stakes (0.05,0.1,0.2,0.4,0.8), uniform weights (l.42,62).
  DISCREPANCY: paper uses a geometric lambda grid with weights (96) from Algorithm 3 and K_alpha
  chosen from Delta_L,Delta_U; this is a fixed ad hoc grid. Factor form equals eq (70) after the
  mapping above. Stake 1 allowed (l.58) gives zero factor at x = -B; paper requires lambda < 1.
- l.140 `>=` threshold: matches paper (7); R code uses `>`.
- l.84-95 threshold `H/alpha`, finite horizon. Not the paper's ARL threshold. Equivalent to
  Remark 2.7 with pi_s = 1/H on H starts (SR/H >= 1/alpha); the audit's Markov-at-stopping-time
  proof (docs/horizon_edetectors_paper_to_code_audit.md) is independent of the paper and sound as
  written. Ville with V_t = M_t/H + remaining mass gives the same bound (my derivation).
- l.114-137 skip = factor 1 and a new start still opens: consistent with calendar-start SR.
- docs/horizon_edetectors_paper_to_code_audit.md cites "Section 2.2 ... Section 2.3 ... Section 2.4":
  Def 2.2 is in Sec 2.2, SR/CUSUM in Sec 2.3 (Def 2.6), baseline recursions in Sec 2.4; Prop 2.3
  correct. It says both statistics start at zero: correct (eq (13),(14)).
- `src/shiftlab/sota_search/paired_edetectors.py:36-65`: stakes (.2,.5,.8), SR mean over stakes
  and CUSUM mean over stakes (l.58-60): matches (13),(14),(25),(26). Factor
  `1 + stake*x/(1/frac+margin)` with x = q/frac*(loss-cand) - margin (l.40,56): IPW bounded
  factor (a ShiftLab adaptation). Thresholds `T/alpha` (horizon) and `1/alpha` (ARL) l.64: the
  `1/alpha` rows are Theorem 2.4 for ARL, one alarm only; PFA claims must use the H/alpha rows.
  l.65 extra gate `(T-t)*margin >= switch_cost` and one-sided only. Delay handled by indexing
  `x[:, t-delay]` and factor 1 for t < delay (l.53-57): calendar release shift, fixed delay only.
- `src/shiftlab/sota_search/paired_cusum.py`: classical CUSUM with slack, simulation-calibrated
  thresholds; not an e-detector (see page_hinkley spec).
- `src/shiftlab/sota_search/restart.py:32-42`: `S_t = (S_{t-1} + w_t) f_t`, `M_t = S_t + tail`: the
  weighted-start e-SR of Remark 2.7 plus retained unallocated mass (Ville form). l.45-54
  `sr_statistic` = (13).
- `scripts/sota_sprint/fam_e.py:SRRDetector` (~l.77-96): kind "sr": `sr = (sr+1)*f` per lambda, mean
  over lambda: MATCHES (13)+(26). kind "cusum": `prods` row per start, `stat = max over starts of
  mean over lambda` (max-of-mixture), which is valid (Def 2.6 with a mixture e_j-process) but is
  NOT (25) (mixture-of-CUSUMs). Label clock, lambdas (0.15,0.3,0.5) uniform, threshold 1/alpha_k.
  Docstring claims the CRAN package is `edetect` (R-only); the author packages found here are
  `stcp`/`stcpR6` (an `edetect` page appeared in a web search; not read: UNVERIFIED relation).

RMM, E_rb and their relation to e-SR / e-CUSUM:
- RMM detector `scripts/failure_atlas_v2/restart_monitor.py:72-102` (`MixtureSRDetector`):
  M_n = (1/|Lambda|) sum_lambda sum_{s in S} pi_s prod_{k=s}^n (1 + lambda X_k), with pi_s = 1/|S|
  (total mass 1), Lambda = {0.15,0.3,0.5}, starts every `gap=10` labels, X_k = +-1 on queried
  disagreements, alarm at M_n >= 1/alpha_k (module docstring l.1-40; update l.93-99).
  This IS an e-SR detector: Def 2.6 sum over starts, mixed over lambda (Prop 2.3, eq (26)), with the
  PFA-style start weights of Remark 2.7. Differences from Shin et al.: (1) start weights sum to 1
  (PFA, Ville, finite grid) rather than unit mass per start (ARL); (2) starts only every 10 labels,
  not every observation; (3) clock is the count of queried disagreements (label clock), not
  calendar; X = +-1 so factor 1 + lambda X equals eq (70) with m = 1/2 on (X+1)/2; (4) fixed
  3-point lambda grid with uniform weights, not Algorithm 3; (5) wrapper: alpha split (alpha/2 base,
  alpha/2 detector), alpha_det/2^j for the j-th promotion, restart of the base policy and reset of
  the detector after an alarm, continued paced acquisition. Items (1)-(5) are outside the paper.
  RMM is not e-CUSUM at any level.
- E_rb: `scripts/sota_sprint/fam_e.py` l.1-20, 226 builds `fam_b.RecoveryMonitor(rollback=True)`
  (`scripts/sota_sprint/fam_b.py` l.8-33, 142-250): after a promotion the rollback detector is the same
  restart-mixture SR (GridMixtureDetector, one component gap=10, lambdas (.15,.3,.5)) at
  alpha_rb_new = .10 over a start grid sized to the remaining budget (`m = max(_remaining_hint,20)`),
  sign flipped so X = +1 means the incumbent was right, plus a horizon gate h_min = ceil(c_s/G_REF),
  G_REF = 0.1, and halving alpha shares for re-promotion. So E_rb = alternating one-sided e-SR
  detectors (promotion, rollback) in the label clock; the two-sided structure is sequential, not the
  stcpR6 two-sided mixture. The "alpha_rb = .10" is a per-phase level with a false rollback treated
  as a cost; no joint two-sided guarantee is claimed in code comments.
- Current honest tier: RMM detector T3 e-SR-style (T2 for the SR recursion line); E_rb T3;
  `fam_e` E_srr/E_srrSR T3 (E_srr cusum variant deviates from (25)).

## 8. Paper-stated numbers/identities for reproduction tests

- Trivial e-processes Lambda = 1: M^SR_n = n and M^CU_n = 1 (v4 p10).
- Recursions against brute force: M^SR_n = sum_j prod_{i=j}^n L_i (eq (10),(12)); same for CUSUM
  (ShiftLab test_horizon_edetectors already does this).
- Algorithm 3 outputs: Bernoulli alpha=1e-3, Delta_L=0.02, Delta_U=0.41, Kmax=1000 -> 69 baselines
  (with sub-B psi, p0 = 0.49; p26); bounded alpha=1e-3, Delta_L=0.024, Delta_U=1600, Kmax=1000 -> 190
  baselines (sub-E; p28). Check weights sum to 1 and g_alpha > log(1/alpha).
- Eq (75) numbers: m = 0.494, delta = 0.0125 -> Delta_L = 0.0241, Delta_U = 1599.7 (checked by hand).
- Bernoulli simulation (p30-31): oracle CUSUM worst delay 91.3 +- 1.7, GLR 123.7 +- 2.7 at ARL 500
  (5000 reps; CPU-sized if shortened). e-SR with threshold log(500).
- Cross-check Python port against stcpR6/stcp log e-detector paths on the same Bernoulli stream
  (both packages share eq (13),(27),(31)).

## 9. Open questions / UNVERIFIED

- Full appendices A and B proofs were not read (Prop 2.14, Thm 3.4, Prop 3.3, Lemma B.1, Thm 4.3,
  Cor 4.6 proofs). Read: v4 main text pp1-33 in full, App A.1 proof of Thm 2.4, Algorithm 3/4 and
  Prop B.2 statements.
- Remark 2.7 (PFA) proof not located. Defaults for Algorithm 2 (r, m, K_0) not located.
- Which increment ((70) or (72)) produced the paper's example figures.
- Full v4-vs-NEJSDS textual diff not done.
- stcp/stcpR6 behaviour was read, not run; numeric agreement with the paper not checked.
- `edetect` package (cran-r-universe) not read.
