# C1 source-theorem audit under R2

**Date:** 2026-10-30. **Status:** theorem-level primary-source audit of candidate C1 (delayed-HMM predictive confidence-set gate),
as scoped by `switching_theory_targets_c1_c2_v1.md` section 1.7. Not a novelty claim and not a complete prior-art search. It
covers the four source groups listed below only.

**R2 test applied.** A candidate result is closed only if a cited source theorem states it, or directly implies it, under the same
feedback, budget, delay and risk contract (`budgeted_switching_research_goals.md`, "Acceptance-criteria revision 2026-10-30").

**C1 targets audited.**
- C1-A: anytime false-promotion at most alpha for the model-conditional current-benefit gate over a finite HMM family.
- C1-B: promotion-delay / sample-complexity upper bound under delay `d`, cap `B`, predictable selective queries, latent switching.
- C1-C: KL lower bound on budget and promotion time.
- C1-E: persistence-aware query advantage over calendar schedules.

**Reading method and limits.** Each PDF was downloaded, converted to text locally, and the theorem statements and setup were read
directly. Proofs of Arnold et al. (in the supplement) and of Emmenegger et al. (appendices) were not checked line by line; only
statements, assumptions and setting were audited. Arnold et al. was read as arXiv v4; the JRSS-B article is a different artifact
(not read), so theorem numbers below are arXiv v4 numbers. Emmenegger et al. was read as arXiv v1; NeurIPS numbering was not
cross-checked. Statements are paraphrased; no source text is reproduced beyond a short phrase.

---

## 1. Arnold, Gavrilopoulos, Schulz, Ziegel, "Sequential model confidence sets"

- **Identity / venue.** arXiv:2404.18678 (stat.ME), v4 dated 22 Jan 2026 (read). Journal of the Royal Statistical Society Series B,
  online 13 May 2026, DOI 10.1093/jrsssb/qkag066 (per search metadata and the repo's earlier audit; journal PDF not read).
  URL: https://arxiv.org/abs/2404.18678 ; PDF https://arxiv.org/pdf/2404.18678
- **Information access.** Losses `L_{i,t}` of `m` forecasters, observed at every `t`, with `d_{ij,t} = L_{i,t} - L_{j,t}`; forecasts are
  predictable (use information to `t-1`). Filtration `(F_t)`. No hidden state, no selective observation.
- **Sampling model.** Passive and complete: every outcome at every time is scored. Predictable *betting fractions* and predictable
  bounds `c_{ij,t}` are allowed inside e-processes (Prop. 3.2, Sec. 3.4). Query selection is not part of the model.
- **Delay.** Not treated. **Budget.** None. Missing forecast values appear only as an application remark (Covid hub data) and are
  handled by excluding incomparable models, not by theory.
- **Risk event / comparator.** Time-uniform coverage of a *set of superior forecasters*: `Q(for all t: M_t* subset of M_t) >= 1-alpha`
  (eq. 4), with superiority defined by conditional expected loss differences. Three targets: strongly superior, uniformly weakly
  superior, weakly superior (eqs. 1-3).
- **Theorems (arXiv v4 numbering, as read).**
  - Thm 3.1: the set `M_t = {i : E_{i,t}^{adj} < 1/alpha}`, built from pairwise e-processes combined by the closure principle with the
    arithmetic-mean e-merging function, is an SMCS at level alpha for the strongly (and uniformly weakly) superior sets, as is its
    running intersection.
  - Prop. 3.2: for conditionally bounded `|d_{ij,t}| <= c_{ij,t}/2` with predictable `c`, `prod (1 + lambda_{ij,r} d_{ij,r})` is an
    e-process for the strong hypothesis, for predictable `lambda` in `[0, 1/c]`.
  - Prop. 3.3 (attributed to Choe-Ramdas 2023, Thm 3): e-process for the uniformly weak hypothesis under uniformly bounded differences.
  - Thm 3.4: SMCS for the weakly superior sets via a confidence sequence for the matrix of average conditional differences; Prop. 3.5
    (convexity of the confidence region) and Prop. 3.6 (a concrete supermartingale).
  - No sample-complexity, exclusion-rate, or lower-bound theorem appears; power is addressed only by simulation (Sec. 4) and
    betting-scheme heuristics.
- **Verdicts.**
  - C1-A: **PARTIAL.** Same machinery (e-process, Ville, simultaneous exclusion). The guaranteed event is coverage of the
    superior-*forecaster* set, not "the true model's current predictive mean exceeds a hurdle `h` when promoting". A parameter
    confidence set over HMM likelihoods is not a forecaster-superiority statement, and a fixed hurdle is not a forecaster. Delayed,
    capped, selective release is not in the statement. The proof technique transfers; the theorem does not imply C1-A as stated.
  - C1-B: **NO.** C1-C: **NO.** C1-E: **NO.**
- **Usable lemma.** Ville for e-processes (their eq. 5) and the closure/e-merging construction as a baseline gate; forecaster-comparison
  SMCS as a matched baseline (the repo already lists it). It cannot supply any rate.

## 2. Emmenegger, Mutny, Krause, "Likelihood Ratio Confidence Sets for Sequential Decision Making"

- **Identity / venue.** NeurIPS 2023; arXiv:2311.04402 v1, 8 Nov 2023 (read).
  URL: https://arxiv.org/abs/2311.04402 ; PDF https://arxiv.org/pdf/2311.04402 ;
  https://proceedings.neurips.cc/paper_files/paper/2023/hash/5491280797f3192b895bce84eb83df8d-Abstract-Conference.html
- **Information access / sampling model.** Pairs `(x_s, y_s)` with a conditional model `p_theta(y | x)`. The covariate `x_s` is chosen
  by the decision maker using past data (it is `F_{s-1}`-measurable, where `F_s` includes `x_{s+1}` and `y_s`); the estimator
  sequence `theta_hat_s` and weights `w_s` must also be `F_{s-1}`-measurable. So sampling is adaptive/predictable, but `y_s` is
  observed immediately after `x_s`, in every round, from a conditionally independent observation model. No latent state, no
  selective omission, no delay, no budget. A search of the text for hidden/latent/Markov/delay/missing/budget returns nothing.
- **Risk event / comparator.** Time-uniform coverage `P(for all t: theta* in C_t) >= 1-delta` of `C_t = {theta : R_t(theta) <= 1/delta}`.
- **Theorems (arXiv v1 numbering, as read).**
  - Thm 1: `R_t(theta)` (weighted sequential likelihood ratio with a running estimator sequence) is a nonnegative supermartingale
    with `R_0 <= 1`, hence `P(exists t: theta* not in C_t) <= delta` by Ville.
  - Thm 2 (bias estimate), Thm 3 (for GLMs, with probability `1-delta`, every `theta` in `C_t` satisfies a Bregman-divergence bound in
    terms of information gain and online-prediction regret `R_t`), Thm 4 and 5 (FTRL regret bounds), Thm 6 (linear-bandit pseudo-regret),
    Thm 7 (appendix, a related bound). Assumption 1 is bounded covariates, a bounded parameter ball, and a strongly convex, smooth
    log-partition function.
  - The only rate-type statements are confidence-*set size* bounds for generalized linear models, with a regret bound that matches known
    minimax orders in `t`. There is no lower bound on samples needed to exclude a rival parameter in a finite HMM family.
- **Verdicts.**
  - C1-A: **PARTIAL.** Thm 1 is the same Ville/likelihood-ratio argument. As stated, the likelihood is `p_theta(y_s | x_s)`, conditionally
    independent given the covariate. C1's factor is a history-dependent predictive `p_theta(y_j | y_{<j})` of an HMM with marginalised
    unqueried and pending outcomes. The proof pattern clearly carries over (the repo's own proof does exactly this), but the theorem
    statement does not cover delay, selective release, or hidden-state predictives, and the risk event differs (parameter coverage
    versus a hurdle on the current predictive mean). Treat as the cited method; C1-A is a corollary-by-proof-pattern, not a corollary-by-statement.
  - C1-B: **NO** (GLM set-size bounds, different model class and no delay). C1-C: **NO.** C1-E: **NO.**
- **Usable lemma.** Thm 1 / Ville's inequality for LR supermartingales with predictably chosen inputs, as the citation for the coverage step.
  Thms 3-4 are a template for what an exclusion-rate theorem looks like for conditionally independent models; they do not transfer to HMMs.

## 3. Kapoor and Nair, "MDPs with a State Sensing Cost"

- **Identity / venue.** Proceedings of AISTATS 2026, PMLR vol. 300, pp. 1648-1656 (PDF read from the PMLR repository).
  URL: https://proceedings.mlr.press/v300/kapoor26a.html ; PDF https://raw.githubusercontent.com/mlresearch/v300/main/assets/kapoor26a/kapoor26a.pdf
- **Information access.** Finite, known MDP with infinite-horizon discounted cost. At each epoch the agent picks an action and commits
  to sensing the next state (pays `k`, state revealed exactly) or acting blind (belief propagated through known `T`). Sensing reveals the
  *state itself* noiselessly (an "ACNO-MDP"), not a noisy emission and not a paired label.
- **Sampling model.** Adaptive: the policy chooses when to sense as a function of the belief/blind-action string. Formulated as an MDP over
  a countably infinite space of (last sensed state, blind action string).
- **Delay.** None; sensing is immediate. **Budget.** A soft per-sensing cost `k`, not a hard pathwise cap. **Risk event.** None: the
  objective is expected discounted cost. No false-alarm, false-promotion or anytime-validity notion. **Comparator.** Optimal policy of the
  MDP, and the always-sense policy.
- **Theorems (as read).**
  - Thm 4.1: if `k` is below a computable threshold, always sensing is optimal.
  - Thm 4.2: bound on the value gap between the truncated MDP (at most `N` consecutive blind actions) and the full MDP, of order
    `gamma^N k / (1-gamma)`.
  - Lemma 4.3 and Thm 4.4: condition for the optimal policy of the truncated MDP to be optimal for the full MDP; otherwise a computable
    suboptimality bound `Delta_N`. These give computable suboptimality gaps for any policy; the SPI algorithm is empirical.
  - The paper notes its model can be written as a POMDP and benchmarks against POMDP solvers. No lower bound on information needed.
- **Verdicts.**
  - C1-A: **NO** (no risk guarantee). C1-B: **NO** (no promotion, no statistical test, no delay). C1-C: **NO** (no KL or information
    lower bound). C1-E: **NO**, with a caveat: belief-dependent sensing is the generic idea behind a persistence-aware query rule, and
    the paper's structure (go blind while uncertainty cost is below sensing cost, truncate blind runs) is close in spirit. But no
    theorem compares belief-driven sensing with a calendar schedule, no rate in a query *count*, no hard cap, no delay.
- **Usable lemma.** None for the C1 statistics. It is the right *comparator class* for any C1-E policy (R6 baseline: costed-sensing
  policy on the belief MDP), and Thm 4.2's truncation idea may inform the finite-horizon belief DP.

## 4. HMM filter forgetting and likelihood-ratio concentration

Four primary papers were read. None is about sparse or delayed *selective* observation; the relevant usable content is the pathwise
forgetting bound and the positive-KL-rate and concentration statements.

### 4a. Douc, Moulines, Ritov, "Forgetting of the initial condition for the filter in general state-space hidden Markov chain: a coupling approach"
- **Identity / venue.** Electronic Journal of Probability 14 (2009), paper 2, pp. 27-49 (official PDF read).
  URL: https://www.maths.tcd.ie/EMIS/journals/EJP-ECP/article/view/593.html ; arXiv:0712.0285
- **Setting.** HMM with Markov signal `Q` and observations `Y_k` with density `g(x, y)`; `xi_{mu,n}[y_{0:n}]` is the law of `X_n` given `y_{0:n}`
  from initial law `mu`. Passive, every `Y_k` present.
- **Statements.** Thm 6: for any integer `m` and any observation sequence, `||xi_{mu,n} - xi_{mu',n}||_TV` is bounded by `2 prod_k (1 - eps_{k,m|n}(X x X))`,
  where `eps` are coupling constants of the posterior (smoothing) kernels (Def. 3). Prop. 5: a strong small set `C` (Def. 4:
  `sigma_- nu <= Q <= sigma_+ nu` on `C`) gives coupling constant at least `sigma_-/sigma_+`. Example 2: if the whole space is strongly
  small (uniformly ergodic kernel, e.g. a finite chain with a positive transition matrix), then the filter forgets its initial law
  geometrically in `n`, at ratio `1 - sigma_-/sigma_+` (the printed bound may carry a constant factor; confirm in the paper). The bound is
  pathwise: it holds for every observation sequence.
- **My inference (not a source statement).** Because the bound uses only the transition kernel, it should apply when some `Y_k` are
  uninformative: add a "missing" symbol with `g(x, missing) = 1`. Forgetting is then geometric in *elapsed time*, not in the number of
  observed labels, so sparse selective observation does not slow forgetting under strong mixing. This reduction is not in the paper;
  it needs a short written check, and it does not by itself give forgetting of the *predictive* of an event or of the conditional KL.
- **Verdict:** NO for C1-A/B/C/E (a lemma paper). **Supplies** the forgetting rate for U1 in C1-B step 2, as a TV bound on filters.

### 4b. van Handel, "The stability of conditional Markov processes and Markov chains in random environments"
- **Identity / venue.** Annals of Probability 37(5), 2009, pp. 1876-1925; arXiv:0801.4366 v2. URL: https://arxiv.org/abs/0801.4366
- **Statements.** Thm 3.4: under Assumption 3.1 (ergodic signal, TV convergence from almost every start) and 3.2 (nondegenerate
  observations), the conditional signal is weakly ergodic (condition equivalences in Thm 2.3). Thm 4.2 and Cor. 4.9 are the
  tail sigma-field consequences used for filter stability. The introduction says explicitly that the general theory does not give
  quantitative rates.
- **Verdict:** NO. **Supplies** only qualitative stability (no rate). Do not cite it for a forgetting rate.

### 4c. Douc, Moulines, Olsson, van Handel, "Consistency of the maximum likelihood estimator for general hidden Markov models"
- **Identity / venue.** Annals of Statistics 39(1), 2011, pp. 474-513; arXiv:0912.4480 v2. URL: https://arxiv.org/abs/0912.4480
- **Setting.** Fully observed output process `Y_0^n` of a parametrised HMM, stationary under the true parameter; passive; no delay or budget.
- **Statements.** Thm 1: strong consistency of the MLE up to the equivalence class (assumptions A1-A6; two parameters are equivalent iff
  they give the same stationary law of `Y`; Section 3.2 treats finite-state signals under irreducibility (F1)-(F4)). Thm 12: under (A2),
  (A4), (A6), for every parameter `theta` not equivalent to the truth, `liminf_n E[n^{-1} log p_{theta*}(Y_0^n) / p_theta(Y_0^n)] > 0`,
  i.e. a strictly positive KL rate between non-equivalent parameters (via exponential separation, Lemma 10 and Prop. 15). Thm 14 /
  Thm 17: Azuma-Hoeffding-type tail bounds for `sum_i f(Y_i^{i+s})` (a bounded function of a window of the observations) under a
  V-uniformly ergodic signal; the constant `K` depends on the model and the starting law.
- **Verdict:** NO for C1-A/B/C/E. **Supplies** the identifiability/positive-rate fact behind U3 (for the "query every event" schedule
  only), and a concentration inequality for window statistics, not for the log-likelihood-ratio itself.

### 4d. What was not found
- No source read states a non-asymptotic concentration inequality for the *HMM log-likelihood ratio* `LLR_n(theta*, theta)`, nor a
  finite-sample exclusion time for a finite HMM family with explicit constants, nor anything for intermittent/selective observation.
  Candidate places to look that were *not* read: Kontorovich-Ramanan (McDiarmid-type bounds for dependent sequences), Cappe-Moulines-Ryden
  (book, chapters on forgetting and on the LLR), Le Gland-Mevel (exponential forgetting). Do not cite them for these statements until read.

---

## 5. Summary table

| Source | C1-A | C1-B | C1-C | C1-E | What it supplies |
|---|---|---|---|---|---|
| Arnold et al. (arXiv v4; JRSS-B 2026) | PARTIAL | NO | NO | NO | Ville / e-process / closure construction; forecaster-SMCS baseline; no rates |
| Emmenegger-Mutny-Krause (NeurIPS 2023) | PARTIAL | NO | NO | NO | Thm 1 (LR supermartingale, coverage under predictable inputs) |
| Kapoor-Nair (AISTATS 2026) | NO | NO | NO | NO | Comparator class (costed-sensing belief MDP), truncation idea |
| Douc-Moulines-Ritov (EJP 2009) | NO | NO | NO | NO | Pathwise geometric filter forgetting under strong mixing (Thm 6, Ex. 2) |
| van Handel (AoP 2009) | NO | NO | NO | NO | Qualitative filter stability only |
| Douc-Moulines-Olsson-van Handel (AoS 2011) | NO | NO | NO | NO | Positive KL rate for non-equivalent parameters (Thm 12); window-statistic concentration (Thm 14) |

No source is KILL for any target.

## 6. Verdict

**Does C1 survive R2?** Yes, as a theory target, with the following precise status. Under the R2 kill rule no cited source theorem states
or directly implies C1-B, C1-C or C1-E under the delayed, capped, predictable-selective, latent-switching contract, and none implies C1-A
by statement. R2 does not close C1 on this evidence. This audit covers only the sources named in the task; it is not an exhaustive
search, and the two closest gaps (an HMM-LLR concentration result and a belief-driven-versus-calendar sensing separation) were searched
for only in these papers.

**Already covered (method level, not statement level).**
- C1-A: the Ville argument for likelihood-ratio and e-process confidence sets is established (Emmenegger et al. Thm 1; Arnold et al. Thm 3.1
  and Prop. 3.2). The extension to a delayed, selectively released HMM transcript is the repo's own factorisation plus that argument. It
  is not a source theorem under this contract, but its substance is standard, so C1-A remains a supporting baseline and not a contribution
  (agreeing with the repo's existing position). The risk event also differs from both sources', so the claim must be stated as a corollary-by-proof.
- The IID special case of C1-B/C1-C is classical sequential-testing material (already recorded in the theory-targets doc); none of the four
  sources changes that.

**Not covered by any source read: C1-B, C1-C (in its HMM-with-kmax form), C1-E.** For C1-C the KL lower bound is the repo's own reuse of
a standard argument; no source read states it, but its novelty is low by construction. For C1-E, Kapoor-Nair is the nearest neighbour
(belief-driven sensing) and gives no calendar-versus-adaptive rate separation, no cap and no delay; this remains the highest R2 risk
because a reviewer may read it as an instance of their policy class. Whether the *bound* is new rests on the delay and persistence dependence.

**Lemmas importable with citations.**
1. Ville's inequality and the LR/e-process coverage step: Emmenegger et al. Thm 1; Arnold et al. eq. (5), Thm 3.1.
2. Geometric forgetting of the initial law by the HMM filter, in total variation, pathwise in the observations, under a strong-mixing
   (Doeblin-type) transition kernel: Douc-Moulines-Ritov Thm 6 with Prop. 5 and Example 2. Needs a short written reduction for
   unobserved/pending steps (the "missing symbol" argument above), which is not a source statement.
3. Positive KL rate between non-equivalent parameters, and consistency up to equivalence, for the fully observed schedule: Douc et al.
   2011 Thm 12 and the finite-state Section 3.2 (U3 for "query every event"). Not for spaced or selective schedules.
4. Concentration for bounded window statistics of a V-uniformly ergodic HMM: Douc et al. 2011 Thm 14. Usable for the empirical-average
   route, but the LLR is not literally a bounded window statistic; an extra approximation step (truncating the filter via item 2) is needed.

**Not importable (must be proved or found).** The conditional-KL convergence in C1-B step 2, the LLR concentration in step 3, any statement
for spaced/selective observation, and the C1-E separation. C1-B remains a proof sketch.

**Next gate.** Before any prototype claim on C1-B, either read Kontorovich-Ramanan or an equivalent LLR-concentration source, or write the
filter-truncation plus Thm 14 argument and the "missing symbol" reduction as explicit lemmas. For C1-E, the R6 comparison must include a
Kapoor-Nair-style belief-sensing baseline.
