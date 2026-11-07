# Spec: Shekhar & Ramdas RCS-Detector (change detection by repeated confidence sequences)

Status: retrieval spec (step 1). Not yet independently checked. Written 2026-11-06. Nothing here was
executed; the downloaded code was only read.

Page numbers: "P" = ICML/PMLR camera-ready PDF page (15 pages); "A" = arXiv v2 page (11 pages).
Equation numbering exists only for a few displays; where the paper has no number I cite the
definition/theorem/appendix and page.

## 1. Citation, version read, code

- Shubhanshu Shekhar, Aaditya Ramdas. "Reducing sequential change detection to sequential
  estimation". ICML 2024, PMLR 235:44628-44642.
  Proceedings page https://proceedings.mlr.press/v235/shekhar24a.html (lists no supplement, no code).
- Read in full, both with `pdftotext`:
  - PMLR PDF https://raw.githubusercontent.com/mlresearch/v235/main/assets/shekhar24a/shekhar24a.pdf
    (15 pages, main text pp.1-10, appendices pp.11-15). This is the **primary version**: it is the
    only one with experiments (Section 2.4, Appendix C) and with Proposition 2.9 and Remark 2.3.
  - arXiv https://arxiv.org/pdf/2309.09111v2 (v2, 25 Nov 2023, 11 pages). No experiments section;
    different numbering (Theorem 2.2 = P's Theorem 2.4; Theorem 2.5 = P's Theorem 2.7;
    Proposition 2.7 = P's Proposition 2.10; Definition 1.3 = P's Definition 1.4).
  - Scratch copies (untrusted, not executed): `.../scratchpad/shekhar/pmlr/pmlr.pdf`,
    `.../scratchpad/shekhar/paper.pdf` (sha256 b8efe36b...d1f6a for the arXiv PDF).
- Name used in the PMLR version: **RCS-Detector** ("repeated CS"). arXiv v2 calls it
  "repeated-FCS-Detector". Predecessor: BCS-Detector (Shekhar & Ramdas, ICML 2023), recalled P11
  Definition A.5.
- Official code: **sshekhar17/SCDtoCS**, https://github.com/sshekhar17/SCDtoCS , only commit
  `c3a7eceaf9fa8e2756105c233a791592916c57d1` (2023-12-07, "first commit"; files README.md, main.py,
  utils.py, example.ipynb, .gitignore). Found via `gh repo list sshekhar17`; the README links the
  arXiv paper, the PMLR page does not link it. Read in full via the GitHub contents API (not run).
  The BCS predecessor code is sshekhar17/bcs-changepoint-detector at
  `991b098d6a61d4f5e2cbc8c425f25b27613affd3` (NOT read; irrelevant to RCS).
- The code predates the ICML version (Dec 2023) and the experiments in P Section 2.4 are NOT
  reproduced by it (no BCS-Detector, no CuSum, no dependent-data example, no alpha sweep). It
  reproduces only the style of experiment in `example.ipynb`.

## 2. Native problem and estimand

- Stream X_1, X_2, ... in space X; a functional theta(P). Filtration F_n = sigma(X_1..X_n) (P1,
  Problem 1.1). Unknown change time T in N U {inf}; pre-change trajectory of P0 with theta0,
  post-change P1 with theta1 != theta0; P1 may depend on X_1..X_T (P1).
- Problem 1.1 (non-partitioned, P1): no knowledge of any pre/post classes; require
  E_inf[tau] >= 1/alpha (average run length, ARL) and small E_T[(tau-T)^+].
- Problem 1.2 (partitioned, P2): theta0 lies in a **known** set Theta0, theta1 not in Theta0.
- Feedback: every X_n is observed at time n, no delay, no missing data, no sampling control.
- Null: "no change in theta" (non-partitioned) or "theta stays in Theta0" (partitioned). Nothing
  about harm, cost, or a reference policy.

## 3. Exact algorithm

Definition 1.4 (P2, CS): sets C_n, F_n-measurable, with P(for all n: theta in C_n) >= 1-alpha,
equivalently valid at every stopping time. Remark 1.5 (P2): WLOG nested (replace by running
intersection).

Definition 2.1, RCS-Detector (P3; A3 Definition 2.1). Put C^(0)_n = Theta (Problem 1.1) or Theta0
(Problem 1.2) for all n. For n = 1, 2, ...:
1. observe X_n;
2. update every earlier CS C^(m), 0 <= m < n, with X_n, and initialise a new level-(1-alpha) forward
   CS C^(n) that uses only X_n, X_{n+1}, ...;
3. if the intersection of all initialised CSs, cap_{m=0..n} C^(m)_n, is empty, set tau = n and
   declare a detection.
Non-nested CSs: use cap_{m=0..n} cap_{i=m..n} C^(m)_i = empty (P3, final paragraph of Def 2.1).
So: one CS per start time, **all at the same level 1-alpha**, stop when the running intersections
of all of them are jointly empty. This is a joint-emptiness rule, not "any one CS excludes
theta0" (see Section 5 caveat on Proposition 3.1).

Cost: Remark 2.3 (P3): per-step cost grows with n (n active CSs, quadratic in total); suggests
keeping only the w most recent CSs as future work, "selecting w" left open. Conclusion (P9) repeats
"per-step computation that grows linearly with sample size".

Lorden form (Section 3, P6): for singleton Theta0 = {theta0} the rule equals
tau_L = inf_m { N^(m)(alpha, theta0) + m }, "start a level-alpha sequential test at every time"
(Proposition 3.1, P6; proof Section 4.4 P8-9).

False-alarm-probability variant (Remark 2.5, P4): use level 1 - 6alpha/(n^2 pi^2) for the CS started
at n; then P_inf(tau < inf) <= alpha (ARL infinite) at the price of a delay that is logarithmic in
T (worst case over T unbounded). UNVERIFIED: the "logarithmic in T" delay claim is stated without
proof.

## 4. Hyperparameters and defaults in the paper's experiments

Only Section 2.4 (P5-P7) and Appendix C (P14-P15). Scope: they compare RCS vs BCS and CuSum, "for
simplicity", on bounded-mean change; they explicitly "leave a more thorough empirical evaluation"
(P5).
- Data: independent Beta(2, 2(1-mu0)/mu0) before T, Beta(2, 2(1-mu1)/mu1) after; Delta=|mu1-mu0|
  (P5-P6). **mu0, mu1 base values and T are not stated in the text I read: UNVERIFIED.**
- CS: Hoeffding-type CS of Waudby-Smith & Ramdas, closed form, midpoint
  mu~_t = sum lambda_i X_i / sum lambda_i, half-width (log(2/alpha) + sum lambda_i^2/8)/sum lambda_i,
  lambda_i = sqrt(8 log(2/alpha) / (i log(i+1))) ^ 1 in the main text (P6) but
  sqrt(8 log(2/alpha)/(i(i+1))) ^ 1 in Appendix C (P14). **The two printed schedules disagree.**
  The code (below) uses i(i+1). Reason given for Hoeffding: closed form, makes the detector
  "computationally feasible" (P14). The betting CS (Appendix B) and EB CS are NOT used in the
  paper's experiments; betting CS appears only in the proof of Proposition 2.10.
- ARL experiment: Delta=0, alpha in {1e-1..1e-5}, 50 trials, stopping time capped at 50000, Fig 1
  (P5). Appendix C "Heuristics" (P14): CS width was **shrunk by a multiplicative factor below 1**
  (value not stated: UNVERIFIED) because Hoeffding is conservative, and stopping was checked only
  every 10 or 20 steps, not each round. Hence Fig 1 does NOT measure the guaranteed detector; it
  measures a heuristic modification. P5 text: both schemes control ARL; RCS has "slightly higher
  variability", especially at small alpha.
- Delay experiment: alpha=0.001, Delta in {0.05, 0.075, 0.10, 0.125, 0.15, 0.175}, 50 trials, delay
  clipped at 24000 (Fig 2, P7). RCS and BCS roughly comparable; Delta=0.05 hits the cap for both.
- CuSum comparison with known P0, P1 (Fig 3 left, P14) and a dependent-data example (Fig 3 right,
  P14-15; X_n distribution depends on whether X_{n-1} < 0.5). The Fig 3 caption in the PDF still
  contains the author draft note "Fix Figure 3 + caption" (P15).
- Defaults not given anywhere in the paper: window w (Remark 2.3), betting-CS bet schedule
  (only "mixture method, Hazan Sec. 4.3", P11-12), CS grid or numerical inversion.
- Paper has no table of numeric results; only plots (Figs 1-3). So no paper-stated numbers to
  reproduce except the identities in Section 8.

Official code defaults (main.py / example.ipynb at c3a7ece):
- `BaseChangeDetector(..., Nmax=1000, alpha=0.005, max_num_CSs=1000)` (main.py:17-18);
  Hoeffding and Bernstein subclasses default `max_num_CSs=500` (main.py:112-114, 184-186), i.e.
  a **deque window of 500 most recent CSs** (main.py:64). Notebook sets `max_num_CSs=Nmax`
  (no pruning), alpha=0.005, 100 trials; Exp1 no change mu0=0.6, Nmax=1000; Exp2 change_point=500,
  Delta=0.40, mu0=0.5, Nmax=2000; Exp3 Delta in {.15..0.4}, Nmax=2500, 20 trials.
- Source: Beta(a=2, b) rescaled to [xmin, xmax] (utils.py:35-62).

## 5. Guarantees

All below are for the PMLR numbering; arXiv numbers in brackets.

- **Theorem 2.4 [A Thm 2.2] (P3), ARL.** The Definition 2.1 detector satisfies E_inf[tau] >= 1/alpha
  for T = inf. Proof Section 4.1 (P7, eq. (4)): attach e-process E^(m)_n = 1/alpha if theta0 not in
  C^(m)_n else 0; M_n = sum_m E^(m)_n is an e-detector (Shin, Ramdas, Rinaldo 2024);
  {tau <= n} subset {M_n >= 1/alpha}; then Shin et al. Prop 2.4 (cited, NOT read by me:
  UNVERIFIED) gives E[tau'] >= 1/alpha. Assumptions: each C^(m) is a valid level-(1-alpha) CS for
  the **same fixed theta0** under P_inf, started at m; no i.i.d. needed in the theorem itself.
  Contrast: BCS-Detector had ARL >= 1/(2alpha) - 3/2 (P3) and needed backward CSs.
  *Not covered:* ARL is a mean quantity. It does **not** state P(tau <= N) <= alpha. By my own
  derivation from the {tau <= n} subset {exists m<=n: theta0 not in some C^(m)} step of eq. (4), a union
  bound gives P(tau <= N) <= N alpha when every C^(m) is level 1-alpha (DERIVED, not printed).
  For alpha=0.05 the ARL guarantee is 20 observations; for a 200-label horizon use Remark 2.5
  spending or per-CS level alpha/N, not alpha=0.05.
- **Remark 2.5 (P4):** level 1-6alpha/(n^2 pi^2) for CS n gives P_inf(tau<inf) <= alpha.
- **Assumption 2.6 (P4):** deterministic width envelope w(n,P,alpha) -> 0 for every P, alpha.
- **Theorem 2.7 [A Thm 2.5] (P4), delay.** Post-change data from a **product** distribution P1,
  independent of pre-change data; good event E_T = {theta0 in cap_{n<=T} C^(1)_n} (prob >= 1-alpha).
  If w(T,P0,alpha) < d(theta0,theta1): E_T[(tau-T)^+ | E_T] <= (3/(1-alpha)) u(theta0,theta1,T),
  u := min{n: w(T,P0,alpha) + w(n,P1,alpha) < d(theta0,theta1)}. Partitioned: eq. (1) (P4)
  E_T[(tau-T)^+ | F_T] <= (3/(1-alpha)) u(Theta0, theta1) for all finite T. Proof P8 (Section 4.2):
  note the PMLR proof sums to u(k0 + alpha^k0/(1-alpha)^2) with k0 = ceil(2 log(1/(1-alpha))/log(1/alpha)),
  while arXiv v2 P8 writes /(1-alpha) and omits the 2; I did not re-derive that the constant 3/(1-alpha)
  follows from either: UNVERIFIED.
- **Proposition 2.9 (P4)** (PMLR only): post-change stationary and independent of F_T gives
  E_T[(tau-T)^+ | F_T] <= E_0[N_1], N_m = inf{n-m: C^(m)_n cap Theta0 = empty}; non-partitioned uses
  Theta0 replaced by the ball {theta: d(theta0,theta) <= d(theta0,theta1)/2}. Proof P8-9.
- **Proposition 2.10 [A Prop 2.7] (P5, eqs. (2) and (3)), bounded mean in [0,1].** Needs post-change
  independent of pre-change and **both** pre and post **i.i.d.** (P5). Betting CS of Waudby-Smith and
  Ramdas with the mixture betting strategy (regret <= 2 log n for n >= 13, P12). Non-partitioned:
  if T >= 64 log(64/(Delta^2 alpha))/Delta^2, E_inf[tau] >= 1/alpha and
  E_T[(tau-T)^+ | E] = O(log(1/(alpha K1))/K1), K1 = inf over |theta-theta0|<=Delta/2 of KL(p1||p_theta).
  Partitioned: same with K2 = inf over theta in Theta0 of KL. Remark 2.11 (P5): K1,K2 = Omega(Delta^2) by
  Pinsker, giving O(log(1/(alpha Delta))/Delta^2) (the empirical-Bernstein CS bound of the BCS paper).
  Order-optimal vs Lorden Thm 3 when P0 known i.i.d. (P5).
- **Proposition 3.1 (P6):** for singleton Theta0 = {theta0} the RCS-Detector and Lorden's reduction
  coincide (one-to-one). Remark 3.2: composite null still gets ARL >= 1/alpha via Theorem 2.4.
  Careful: Prop 3.1 does not say the joint-emptiness rule for an interval Theta0 reduces to "any
  single CS excludes Theta0".

Not covered by anything printed: delayed, missing, reordered or selectively sampled observations;
adaptive (action-dependent) sampling; stochastic dependence in the delay bound (only Fig 3 right shows
a dependent example, empirically, with no theorem); finite-sample numerical delay (all delay results
are O(.) or rely on huge T-thresholds); windowed variant (Remark 2.3 suggests it, no theorem);
two-sided versus one-sided harm; any decision or cost semantics.

## 6. Mapping to ShiftLab's deployment contract

Contract: `scripts/sota_sprint/bench.py:25` `CONTRACT = dict(T=2000, budget=200, cq=0.05, cs=5.0,
alpha=0.05)`; Switcher / MonitorV2 protocol in `src/shiftlab/contract/interface_v2.py:82-101`
(`receive` at start of round delivers released labels; `observe`; `choose`). Whether the simulator's
per-round paired loss difference is exactly in [-1,1] was given in the task brief; I did not verify
it in `bench.py` or the FLQ regimes (UNVERIFIED).

Proposed adaptation (**tier T3**, never called "Shekhar-Ramdas" without the deviation list):
- Estimand: theta = mean paired loss difference D = loss(candidate) - loss(incumbent) on the label
  clock. Rescale Y = (D+1)/2 in [0,1] so bounded-mean CSs apply (P12 Appendix B and P14).
- Use: **promotion/rollback trigger on the paired-loss mean**, run after (rollback) or before
  (promotion) a switch. Two options:
  (a) non-partitioned RCS (Problem 1.1): detects a change of theta in either direction relative to an
      unknown pre-change mean, e.g. after promotion. It never certifies D > 0 (harm), only a change.
  (b) partitioned RCS (Problem 1.2) with Theta0 = {D <= margin} for rollback, or {D >= 0} for a
      promotion trigger (stop when the CS intersection leaves Theta0). This is the harm-relevant form,
      but it is a ShiftLab choice, not an experiment of the paper.
- Label clock: labels exist only on queried rounds (hard budget B=200, cq=0.05 so at most 200
  observations over T=2000 rounds). Stream index n = order of delivered labels, NOT event time.
  Detection delay in rounds = (labels needed) + sampling gap + label delay; the paper's "no delay"
  setting is silently replaced. Event-time change T maps to label-clock change T_label only
  approximately.
- Sampling: valid CS use needs the labelled D to have the mean the null refers to. Uniform,
  history-independent querying (Bernoulli(q) independent of losses) keeps this for the labelled
  subsequence; adaptive querying needs IPW Z = Q D / q, bounded by 1/q = 20 (range 40, rescale and
  sacrifice width) and a predictable q. Both are deviations; no theorem in the paper.
- Delay/out-of-order: use the released-label arrival order as the filtration. Then "mean of D" is a
  mixture over event times and the change-time in label order is blurred. Paper silent.
- Level: ARL >= 1/alpha at alpha=0.05 is 20 labels: useless against a 200-label horizon. Use
  Remark 2.5 spending (P4) or per-CS level alpha/N (derived union bound, Section 5), then the realised
  null promotion rate must be calibrated against `NULL_PROMOTION_BOUND = 0.0936`
  (`bench.py:30`, Wilson tolerance at nominal .05). Plain level alpha=0.05 will be anti-conservative
  as a per-episode false alarm bound.
- Guarantee transfer: Proposition 2.10's delay bound needs T >= 64 log(64/(Delta^2 alpha))/Delta^2
  pre-change samples. With Y = (D+1)/2 and Delta_Y = Delta_D/2: for Delta_Y=0.5, alpha=0.05 this is
  about 2186 labels (my arithmetic), for Delta_Y=0.2 about 16,600. Both exceed B=200, so the delay
  guarantees are vacuous here. Only the ARL / PFA statements are usable; delay must be measured.
- Cost: B=200 labels -> at most 200 active CSs, ~20k CS updates, trivial; pruning is not needed.
  If window w is used (code default 500 never binds), ARL stays valid by my argument (fewer
  intersected CSs can only stop later; DERIVED from P8-9 "taking fewer intersections ... longer to
  stop") but delay guarantees do not.
- Switch cost cs=5 and query cost 0.05 enter only the decision layer (when to act on the alarm), not
  the paper.

Achievable tiers:
- Native bounded-mean RCS (Hoeffding CS), no contract: **T2** from Def 2.1 plus the Appendix C
  Hoeffding formula (fully specified), checked numerically against the official code. **T1 is
  not clean**: the official code exists (pinned) but deviates from the printed CS (Section 7), so a
  line-by-line port reproduces the code, not the paper. A T1 label needs a stated, tested
  equivalence to the code AND the discrepancy disclosed.
- Betting CS and EB CS RCS: the paper does not specify the bet schedule (P11-12), EB formulas exist
  only in the code docstring (main.py:195-204); EB CS derives from Waudby-Smith and Ramdas 2023, which I
  did not read. Cannot be T2 from this paper alone: **T3 / inspired-by** unless that paper is read.
- ShiftLab-contract promotion/rollback detector: **T3**.

## 7. Existing ShiftLab code

`grep -ril` finds no Shekhar-Ramdas / RCS / e-detector implementation (confirmed by task brief; I also
grepped `shekhar|ramdas|e-detector` in src and scripts for py files and found the
Podkopaev-Ramdas label only).

Reusable components (all one-sided / test-at-fixed-null; **none is a two-sided CS with interval
output**, so an RCS port needs a new interval object):
- `src/shiftlab/dive/eprocess.py:9` `bounded_betting_factors`; `:38` `BoundedMeanEProcess` (mixture of
  fixed-stake betting e-process for E[X] <= 0, |X| <= bound). Grid over s would yield a betting CS.
- `src/shiftlab/dive/eprocess.py:314` `PredictablePlugInEmpiricalBernsteinEProcess` (one-sided PM-EB at
  mean 1/2; note "Waudby-Smith and Ramdas (2024)" in docstring): closest to an EB-CS building block
  if run on a grid of null values s.
- `src/shiftlab/dive/eprocess.py:386` `PPIBlockConfidenceSequence`, with `lower_bound` at `:443`,
  `_radius` at `:469` (bisection of a mixture bound): the only existing object with an anytime
  one-sided **bound** output; one-sided, PPI-blockwise.
- `src/shiftlab/dive/eprocess.py:635` `StartedMixtureEProcess` and `:693` `VectorizedStartedMixtureEProcess`
  (e-processes started at fixed prespecified positions, convex mixture): structurally the nearest
  thing to "start at each time", but it MIXES (weights) rather than max/intersect, so it is the
  e-detector/mixture style (Shin et al.), a different rule. `:769` `MultiTimescaleStartedKellyEProcess`,
  `:897` `HorizonHedgedStartedMixtureEProcess` likewise. Hedged capital: `:502`
  `PredictableHedgedPositiveEProcess`.
- `src/shiftlab/sota_search/detectors.py:221` `hoeffding_width` (stitched Hoeffding,
  bound*sqrt(log(pi^2 n^2/(3 ALPHA))/(2n)), `ALPHA=0.05` at `:18`) and `:226` `pr_cs`: Podkopaev-Ramdas
  style one-sided CS vs a nominal risk; this is a different CS (stitching) than the paper's Hoeffding
  CS (Appendix C) and does not reproduce it.
- `src/shiftlab/sota_search/published_baselines.py:16` `pr_empirical_bernstein`
  (PM-EB with caps 0.5, delay wrapper, uniform query mask): shows a working delayed, budgeted, label
  clock pattern at the stream level.
- `src/shiftlab/sota_search/paired_references.py:8,96` consumes `pr_empirical_bernstein`.
- Contract hooks: `interface_v2.py:82-101`; bench constants `bench.py:25`.

What to write new: a two-sided Hoeffding CS state per start (T2, tracked intersection), a batch of
CSs with optional window w, and a label-clock wrapper that feeds a `Switcher`. Nothing existing should
be called "RCS". Honest current tier of existing RCS-like code: none exists.

### Discrepancies between official code (c3a7ece) and the printed paper (my reading; code not executed)

1. **First observation skipped.** `one_trial` (main.py:68-81) updates existing CSs with the new point,
   then appends a new CS whose state is never updated with that same point. A CS started at n0 first
   updates at n0+1 with `t = n - n0 + 1 = 2` (main.py:151), so it ignores X_{n0} and starts its lambda
   index at 2. Definition 2.1 step 2 says the new CS C^(n) uses X_n.
2. **Initial state not the paper's formula.** Hoeffding state initialises `lambda_sum = 1`,
   `mu_num = 0` (main.py:134-135), adding a pseudo-weight 1 at 0 to the midpoint and denominator;
   the printed estimator is sum(lambda X)/sum(lambda) with no extra term (P14). The Bernstein state
   does the same (main.py:213-214). I did not prove the code's interval is a valid CS; the paper's
   coverage argument is for the printed form. **Coverage of the code's CS is UNVERIFIED**, so do not treat
   its ARL as guaranteed.
3. **lambda schedule.** Code uses i(i+1) (main.py:153) = Appendix C (P14), not the main-text i log(i+1)
   (P6). The Bernstein docstring says t log(t+1) (main.py:202) but the code uses t(t+1) (main.py:244).
4. Empirical-Bernstein CS has no counterpart in the printed paper; formulas are in the code docstring only.
5. Window 500 default (main.py:112,184) is a pruning not analysed in the paper.
6. Intersection uses running max/min of per-CS bounds starting from [xmin,xmax] (main.py:162-163,
   171-177): consistent with Remark 1.5 nesting.

## 8. Paper-stated identities usable as tests (no numeric tables exist)

- Def 2.1 on a hand-built stream with exact intervals: with CSs [0.4,0.6] started at m=1 and [0.7,0.9]
  at m=2, intersection empty at n=2; a single step before that, not empty. (Logical identity.)
- Equation (4), P7: for any CS family, detector stops at n iff no common point of all running
  intersections; compare with `M_n >= 1/alpha` where M_n = sum over m of 1/alpha*[theta0 not in C^(m)]
  (inclusion {tau <= n} subset {M_n >= 1/alpha}); can be tested pointwise.
- Proposition 3.1, P6: with Theta0 = {theta0}, RCS stopping time equals Lorden's
  inf_m (N^(m)+m) when N^(m) = first exit of theta0 from the m-th CS. Test on random data.
- Remark 1.5 (nestedness invariance): replacing CSs by their running intersections leaves tau unchanged.
- Theorem 2.4 as a Monte Carlo check on pure-null Beta(2,.) data with the paper's Hoeffding CS at
  alpha = 0.1: empirical mean of tau (capped) should be >= 10; note the paper itself needed a
  width-shrink heuristic (P14) to run ARL experiments, so un-shrunk Hoeffding will be extremely
  conservative (ARL >> 1/alpha). This is a smoke check, not confirmatory.
- Fig 1/2 qualitative statements (RCS ~ BCS; delay increases as Delta shrinks, Delta=0.05 hits the 24000 cap
  at alpha=0.001) are qualitative only.

## 9. Open questions / UNVERIFIED

- mu0 and change time T in Section 2.4 experiments; width-shrink factor (Appendix C).
- The exact constant 3/(1-alpha) in Theorem 2.7: PMLR and arXiv proofs differ in the geometric sum.
- Shin, Ramdas, Rinaldo (2024) Proposition 2.4 and Definition 2.2/2.6 (used for Theorem 2.4): not read.
- Waudby-Smith and Ramdas (2023) CS definitions (Hoeffding, EB, betting) and their conditions
  (independence vs conditional mean); the CS formulas here are only as printed in this paper.
- Whether the WSR Hoeffding CS holds under non-i.i.d. but martingale-difference data (needed for ShiftLab
  with adaptive querying): not established here.
- Whether the simulator's paired loss difference is in [-1,1] and whether both action losses are
  observed on a queried round (AGENTS.md requires identifiability): not checked.
- Dependent-data example (P14-15) gives empirical results only; no guarantee statement covers it
  (the paper claims forward CSs "can work" with certain dependent streams, P15).
- ICML camera-ready vs a possible later journal/arXiv v3: only arXiv v2 and the PMLR PDF seen.
