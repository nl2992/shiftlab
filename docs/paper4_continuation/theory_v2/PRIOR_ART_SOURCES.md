# WP F: Prior-art sources for the causal-safety premium results (retrieval only, no novelty verdicts)

Date: 2026-11-10. Retrieval agent: WP F (Sonnet), HKUSTDial `deep-research` method (frozen questions F1-F10, adversarial
search formulations, verify-every-citation, theorem statements read in primary text). Not committed.

**Scope.** Results under test (statements in `CAUSAL_SAFETY_PREMIUM_THEORY.md`): R, Zc, Z1/W, N1, C3', U (open).
Verdict vocabulary is limited to *reduces / partially reduces / does not reduce (difference: ...)*. Reductions marked
"(own derivation)" are my attempt at a short proof from the cited statement; they are not claims made by the source.

**Read-status vocabulary.** OPENED = full text retrieved and the named sections read. ABSTRACT = abstract or catalogue
metadata only. NOT FOUND = could not retrieve. META = Crossref/arXiv metadata verified (existence, volume, pages), no content.

**Untrusted-file handling.** Downloads were saved in
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/wpF_sources/`
(new directory), text extracted with `pdftotext` only, nothing executed. Project Euclid downloads (Huber 1965, Huber-Strassen
1973, Kamae-Krengel-O'Brien 1977, Liggett-Schonmann-Stacey 1997) returned HTML paywall pages and were deleted unread.

## 0. Gaps flagged earlier, and their status now

| Earlier gap | Status after WP F |
|---|---|
| Krishnamurthy theorem statements never read | CLOSED. Thm 4.3.1, 5.2.1, 5.3.1, 6.2.1, 6.3.3, 6.3.4 quoted in §1.1 below, from the full arXiv text. |
| Lovejoy 1987 cited from memory | PARTLY. Existence and DOI verified (META). Original paper NOT FOUND (paywalled). Its Props 1-2 hypotheses are described in Krishnamurthy-Pareek (OPENED). The "Ordered solutions" paper: META only. |
| Altman CMDP duality from memory | NOT CLOSED. Book NOT FOUND (no open text). The same duality is stated and used in Walraven-Spaan (OPENED), which is a stronger POMDP-specific source; Poupart et al. (OPENED) restate the LP and cite Altman. |
| Heck et al. AAAI 2026 not read | CLOSED at skim level: arXiv:2511.08078 retrieved; no overlap with the questions here (§4.4). |
| Fauss-Zoubir-Poor (new, not previously flagged) | OPENED. This is the closest statistical source for "minimax sequential test against a rectangular family of conditional laws, with Lagrangian handling of error constraints". See §3.1. |

## 1. Structural (monotone threshold) results

### 1.1 Krishnamurthy, "Structural Results for Partially Observed Markov Decision Processes: A Tutorial", arXiv:1512.03873v1 (12 Dec 2015)
- Status: **OPENED** (pdftotext of all 130 pages; read Ch. 4.3, 5.1-5.3, 6.2-6.3, Ch. 7 headings; proofs skimmed).
- Book mapping: the 2016 Cambridge book *Partially Observed Markov Decision Processes: From Filtering to Controlled Sensing*
  (ISBN 978-1-107-13460-7) is the source of this tutorial's chapters. Per the arXiv supplement 1604.08127 abstract/listing
  (ABSTRACT only), book chapters 9-13 are "Structural Results for MDPs / Optimal Filters / Monotonicity of Value Function /
  Stopping Time POMDPs / Stopping Time POMDPs for Quickest Change Detection". I did not open the book, so the book's theorem numbers may differ from the tutorial's.
- Assumptions (exact, p. 45, 58, 75):
  - (C) cost first-order-stochastically decreasing in belief: pi1 >=_s pi2 implies C(pi1,u) <= C(pi2,u). For linear cost, c(x,u) decreasing in x.
  - (F1) observation kernel B(u) is TP2. (F2) transition matrix P(u) is TP2.
  - (S) C(pi,u) submodular on the lines L(e_X, pibar) and L(e_1, pibar) (linear-cost form: c(x,2)-c(x,1) >= c(X,2)-c(X,1) and c(1,2)-c(1,1) >= c(x,2)-c(x,1)).
  - Finite state and action, known P and B, discounted cost (rho in [0,1]; stopping problems allow rho=1), **undelayed observations, one measure (the HMM), expected-cost criterion, no chance constraint**.
- **Theorem 4.3.1** (structural result for filtering). (1) The HMM predictor/filter preserves MLR order in pi iff (F2). (3) T(pi,y,u) is MLR-increasing in y iff (F1). (2) Under (F1),(F2), sigma(pi,u) is first-order increasing in pi. Items 4-6 compare actions u and u+1 under copositivity conditions (F3),(F3'),(F4).
- **Theorem 5.2.1.** Under (C),(F1),(F2), Q(pi,u) and V(pi) are MLR-decreasing in pi (pi1 >=_r pi2 implies V(pi1) <= V(pi2)).
- **Theorem 5.3.1** (X=2). Under (C),(F1),(F2),(F3'),(S), the optimal policy is increasing in pi(2), with U+1 thresholds. The tutorial says explicitly that this does not generalise to X>=3 ("open problem"); Chapter 8 substitutes myopic bounds.
- **Theorem 6.2.1** (cites [76]). For the stopping-time POMDP (actions stop=1, continue=2, Bellman eq. (6.4)) the stopping set R1 is convex in the belief simplex. (Proof: concavity of V and linear stopping cost.)
- **Theorem 6.3.3** (Topkis). If f on L(e_i,pibar) x U is submodular (i=1 or X), some argmin selection is increasing on [L, >=_Li].
- **Theorem 6.3.4** (switching curve). Under (C),(F1),(F2),(S): (1) an optimal policy exists that is >=_LX-increasing on lines L(e_X,pibar) and >=_L1-increasing on L(e_1,pibar); (2) a switching curve Gamma splits the simplex into two connected regions, crossing each such line at most once; (3) there is i* with e_1..e_i* in R1 and the rest in R2; (4) for X=2 a unique threshold pi*(2).
- Reductions:
  - **Z1/W (B=1)**: *partially reduces*. The mechanism (TP2 + MLR gives a monotone value function and, with submodularity, a threshold) is exactly Thm 4.3.1 + 5.2.1/5.3.1/6.3.4. Differences: (a) our objective is a Lagrangian that mixes two laws, the alternative HMM cost and the IID(1/2) null risk of the promotion event, so the information state is (belief, null/alternative likelihood ratio), not belief alone, and (C)/(S) are statements about belief-measurable costs; condition W is what replaces (C)/(S) here. (b) Labels are delayed and query-costed, so there is a query decision plus pending labels. (c) We need monotonicity of an *event* on the label tape (for the coupling), not monotonicity of a policy in belief. Hence Thm 6.3.4 does not imply Z1 without an additional lifting argument (own derivation: none found).
  - **R, Zc, N1, C3', U**: *do not reduce* (no constraint, no robust null, no premium).
  - **U (multi-label)**: *does not reduce*. Tutorial states the full-simplex MLR monotone policy is only proved on lines and for X=2 (Thm 5.3.1); this is evidence that a multi-label monotonicity proof needs new work, not a reduction.

### 1.2 Krishnamurthy & Pareek, "Myopic Bounds for Optimal Policy of POMDPs: An Extension of Lovejoy's Structural Results", Oper. Res. 63(2):428-434 (2015), arXiv:1404.3328
- Status: **OPENED** (12 pages; assumptions and discussion read; appendix proofs skimmed).
- Statement: assumptions (A1)/(A2) (cost monotone after a shift f or g), (A3) P_a,B_a TP2, (A4) copositivity of Gamma^{j,a,y}, (A5) a tail-sum condition. Theorem 1: under (A1)-(A5) myopic policies mu_lower <= mu* <= mu_upper (sandwich).
- **Description of Lovejoy (1987) Prop. 2 (second-hand, exact wording of the source):** conditions (c),(e),(f) require P_{a+1} >=_tp P_a and B_{a+1} >=_tp B_a (TP2 stochastic order); the authors state this "is impossible for stochastic matrices, unless P_a=P_{a+1}, B_a=B_{a+1} or the matrices are rank 1". Lovejoy's assumption (b) = their (A2) with decreasing cost. Lovejoy Prop. 1 gives V(T(pi,y,a)) increasing in y.
- Relevance: the *multi-action* monotone-in-belief result of Lovejoy is a lower-bound (myopic sandwich) result with a flawed hypothesis set. Any use of "Lovejoy implies monotone sensing/query policy" for Lemma U is invalid.
- Reductions: **U**, **Z1/W**: *do not reduce* (myopic bounds on action, not event monotonicity under a constraint).

### 1.3 Lovejoy 1987 (two papers)
- (a) W. S. Lovejoy, "Some monotonicity results for partially observed Markov decision processes", Oper. Res. 35(5):736-743, 1987, DOI 10.1287/opre.35.5.736. Status: **META** (Crossref verified) + second-hand statement via §1.2. Original text NOT FOUND.
- (b) W. S. Lovejoy, "Ordered solutions for dynamic programs", Math. Oper. Res. 12(2):269-276, 1987, DOI 10.1287/moor.12.2.269. Status: **META** only; content not read. Not used in any reduction.
- Do not cite theorem numbers of (a) beyond "Prop. 1/Prop. 2" as reported by Krishnamurthy-Pareek.

### 1.4 Krishnamurthy 2016 book, controlled sensing
- Status: **ABSTRACT/TOC only** (publisher listing and arXiv supplement 1604.08127 snippet). The controlled-sensing material relevant here is in tutorial §7.4 ("Quickest Detection with Controlled Sampling", p. 95), which I did not read in detail; the earlier notes (`LITERATURE_NOTES.md` S1.3, S1.5b) record that exact threshold structure for sampling control is not a theorem in the simplest costly-sensing QCD model (Banerjee-Veeravalli: three-threshold example) and holds for a hard count constraint only in Geng-Bayraktar-Lai (Bayesian QCD with sampling-right constraints, arXiv:1309.5396, ABSTRACT/partial). Not re-verified here.

## 2. Constrained POMDPs, randomised policies, Lagrangian duality

### 2.1 Walraven & Spaan, "Column Generation Algorithms for Constrained POMDPs", JAIR 62:489-533 (2018), DOI 10.1613/jair.1.11216
- Status: **OPENED** (full PDF text via jair.org; read §2-3 (eq. 5-11, Algorithm 1, Lemmas 1-5, Theorems 1-3); §4 approximate algorithms skimmed).
- Setting: finite-horizon Constrained POMDP (S,A,O,T,Z,R,C,L,b1,h), objective (6): max V^pi(1,b1) s.t. C^pi(1,b1) <= L. Quote of motivation: "an optimal policy for a Constrained POMDP may need to randomize" (citing Altman 1999) and "the best possible deterministic policy ... may be suboptimal (Kim et al., 2011)".
- Statement: the LP (8) of Yost & Washburn (2000) puts a probability distribution x_{i,pi_i} over each agent's finite policy set K_i, with one expected-cost constraint (dual variable lambda) and simplex constraints. Eq. (9)-(10): the Lagrangian upper bound is phi_u = lambda L + sum_i max_{pi_i}(V_i^{pi_i} - lambda C_i^{pi_i}). Theorems 1-2: Algorithm 1 terminates iff it has found an optimal CPOMDP solution. **Theorem 3**: the computed solution randomises over at most one agent; the proof is the basic-feasible-solution count (n+1 constraints).
- Reductions:
  - **R, steps 1-2 (mixtures of pure plans, LP, strong duality, V = max_lambda [min_pi (C+lambda R) - lambda alpha])**: *reduces* for a single-law finite-horizon constraint. The mixture-LP and the Lagrangian-dual bound are stated verbatim; Kuhn's theorem is not cited but the policy-set formulation is the same. (A single constraint gives a mixture of at most two pure plans: Thm 3 with n=1.)
  - **R, the new content**: the hypothesis that min over P equals min over a subfamily M for every lambda, together with the monotone-coupling step. *Does not reduce* (difference: the constraint is on a *family* of laws, and the subfamily M is selected so that one law's risk controls the supremum over the family; no source states this).
  - **N1/B1-S (column generation)**: *reduces* in the sense used in `NOVELTY_AUDIT_SURVIVORS.md`: policy columns = pure plans.

### 2.2 Yost & Washburn, "The LP/POMDP marriage: optimization with imperfect information", Naval Res. Logist. 47(8):607-619 (2000), DOI 10.1002/1520-6750(200012)47:8<607::AID-NAV1>3.0.CO;2-F
- Status: **META** (Crossref), content via Walraven-Spaan §3 only. It is the original LP-over-policy-mixtures source for CPOMDPs per W-S.

### 2.3 Poupart, Malhotra, Pei, Kim, Goh, Bowling, "Approximate Linear Programming for Constrained POMDPs", AAAI 2015, DOI 10.1609/AAAI.V29I1.9655
- Status: **OPENED** (6-page PDF, intro and LP sections). Statement (p. 2): CPOMDP optimal policies "may all be stochastic (Altman 1999; Kim et al. 2011)"; the exact solution is an LP over occupancy frequencies y(b,a) with cost constraints (the dual LP of the MDP with extra constraints, citing Altman); normalising y gives pi*(a|b) (eq. 9). Exact solve over belief states is intractable.
- Reduction: **R steps 1-2**: *partially reduces* (belief-occupancy LP is a different but equivalent representation of the policy-mixture LP; it is not an event-monotone decomposition).

### 2.4 Helmeczi, Kavaklioglu, Cevik, "Linear programming-based solution methods for constrained POMDPs", arXiv:2206.14081
- Status: **OPENED** (intro/related work/LP sections skimmed). Compares randomised (LP) and deterministic (MIP) CPOMDP policies, recording the reward loss from forcing determinism. Supports "randomised optimum is standard" only.

### 2.5 Kim, Lee, Kim, Poupart (IJCAI 2011), "Point-based value iteration for constrained POMDPs"
- Status: **NOT FOUND** (PDF URL guess returned another paper; deleted). Cited via Walraven-Spaan and Poupart only: (i) best deterministic policy can be suboptimal, (ii) exact solution is a minimax QCQP. Do not cite directly.

### 2.6 Altman, *Constrained Markov Decision Processes*, Chapman & Hall/CRC, 1999 (CRC reprint DOI 10.1201/9781315140223)
- Status: **NOT FOUND** (book). Metadata META. Related single-constraint randomisation results found at ABSTRACT level only:
  - Beutler & Ross, "Optimal policies for controlled Markov chains with a constraint", J. Math. Anal. Appl. 112(1):236-252 (1985), DOI 10.1016/0022-247X(85)90288-4 (META).
  - Feinberg & Shwartz, "Constrained discounted dynamic programming", Math. Oper. Res. 21(4):922-945 (1996), DOI 10.1287/moor.21.4.922 (search snippet: randomised stationary optimal policy requiring at most M more actions than a nonrandomised one).
- Theorem numbers from the book were NOT verified; the Lagrangian-duality / at-most-one-randomisation statement is verified instead in Walraven-Spaan Thm 3.
- Reduction of **R** steps 1-2 to this family: *reduces* (full-information CMDP); POMDP/perfect-recall case is covered by §2.1.

## 3. Robust sequential testing, composite nulls, adaptive-null validity

### 3.1 Fauss, Zoubir, Poor, "Minimax optimal sequential hypothesis tests for Markov processes", Ann. Statist. 48(5):2599-2621 (2020), DOI 10.1214/19-AOS1899, arXiv:1811.04286v2
- Status: **OPENED** (abstract, §1-2.3, Thms 1-9 statements read; appendices not read).
- Setting (§2.2-2.3): the observation process has a time-homogeneous Markov representation with sufficient statistic Theta_n; **the conditional law P_theta is replaced by an uncertainty set P_theta for every theta, and the global uncertainty set is the product (2.6) P = {P in M : P = prod_n P_{theta_n}, P_{theta_n} in P_{theta_n}}** (a rectangular set of per-step conditional laws). Hypotheses H_k : P in P_k, k=1..K; the run length is minimised under a set P_0.
- Thm 1: the optimal policy for the unconstrained Lagrangian problem is given by a Bellman equation in (z, theta), z the vector of likelihood ratios. Thm 4: for the *constrained* problem (3.2), if lambda* maximises rho_lambda(1,theta_0) - sum lambda_k alpha_k, then Pi*_lambda*(P) intersects the constrained-optimal set Pi*_alpha(P) (a Lagrangian-multiplier statement for sequential testing with error constraints, possibly needing randomisation on boundaries). Thm 5: integral equations for the worst-case run length/error with sup over H in P_theta have unique solutions. **Thm 6**: if the argmax sets Q_{z,theta} (maximisers over H in P_theta of the next-step value) are nonempty, then every product of such maximisers is least favourable for the policy; "the least favorable distributions adapt to the policy of the test as well as to the history of the stochastic process" and make (z_n, theta_n) Markov even if the X_n are independent. Thms 7-9: sufficient conditions for a pair (pi*, Q*) to be a minimax solution, and a constrained version (Thm 9) via the same lambda*.
- Not covered: no hidden-state label model, no query/budget/switch decisions, no delayed labels, no promotion event on a learner path, the adversary does not see pending outcomes beyond the Markov statistic (z,theta), error constraints are over decisions (accept/reject), and the premium V*_causal - V*_IID is not defined or bounded. The paper does not compare the minimax value to a nominal-null-calibrated design.
- Reductions:
  - **Definition of V*_causal (sup over adaptive nulls p_t in [0,1/2])**: *partially reduces*. It is a rectangular conditional-law uncertainty set of the form (2.6), with least-favourable laws that adapt to history (Thm 6).
  - **R**: *does not reduce* (their results compute the minimax value under a Lagrangian; they do not state a condition for the minimax value to equal the value at one fixed nominal law).
  - **Zc**: *does not reduce*. Difference: a monotone event admits a pathwise coupling; Thm 6 requires solving the adversary's DP.
  - **N1, C3'**: *do not reduce* (no premium formula; numerical examples only).
- This source also supplies an honest caveat for the question "is Gamma = V*_causal - V*_IID new?": the *object* V*_causal is a minimax sequential-test value with a rectangular family, studied here for time-homogeneous Markov data.

### 3.2 Fauss, Zoubir, Poor, "Minimax Robust Detection: Classic Results and Recent Advances", IEEE Trans. Signal Process. 69:2252-2283 (2021), DOI 10.1109/TSP.2021.3061298, arXiv:2105.09836
- Status: **OPENED** (survey; read §I-III, Criteria 1-3, §VII sequential detection).
- Statements: **Criterion 1 (stochastic dominance, Huber 1965)**: (Q0,Q1) is least favourable for all cost functions, thresholds and sample sizes if Q0(q1/q0 > lambda) >= P0(q1/q0 > lambda) and Q1(q1/q0 <= lambda) >= P1(q1/q0 <= lambda) for all (P0,P1) in P0 x P1 and all lambda >= 0. Huber-Strassen (1973): such pairs correspond to 2-alternating Choquet capacities; they also minimise all f-divergences (Criterion 2). §VII: minimax robust *sequential* tests exist for multiple hypotheses with independent data; the least-favourable laws become data dependent (cites [104] = §3.1).
- Reduction of "monotone (one-sided) test events are automatically safe under every adaptive null p_t <= 1/2":
  - *Partially reduces* in the fixed-sample, independent-observation case: Criterion 1 is a stochastic-dominance statement whose consequence is that error probabilities of *likelihood-ratio threshold tests* are maximised at (Q0,Q1). Difference: Criterion 1 concerns i.i.d.-type product uncertainty with marginal (not history-adaptive) laws and a fixed test; our statement covers adapted p_t and arbitrary monotone events along a learner-chosen label order.
- Huber 1965 (Ann. Math. Statist. 36(6):1753-1758, DOI 10.1214/aoms/1177699803) and Huber-Strassen 1973 (Ann. Statist. 1(2):251-263, DOI 10.1214/aos/1176342363; correction Ann. Statist. 2(1):223-224, 1974): **META only**; primary texts NOT FOUND (paywalled). Theorem content is quoted second-hand from §3.2.

### 3.3 Testing by betting, e-processes, composite and adaptive nulls
- **Ramdas, Grunwald, Vovk, Shafer, "Game-theoretic statistics and safe anytime-valid inference", Stat. Sci. 38(4) (2023), arXiv:2210.01948.** Status: **OPENED** (survey, §2-5 skimmed; read the test-supermartingale and composite-null passages). Statements: for a composite null set P a *test supermartingale for P* (nonnegative, starts at 1, supermartingale under every P in P) gives, by Ville's inequality, P(exists t: M_t >= 1/alpha) <= alpha for all P in P (eq. 11 region); null sets of the form "conditional mean mu" for sequences with predictable bets are covered (§5.1-5.2). No claim on optimal-policy value comparisons.
- **Waudby-Smith & Ramdas, "Estimating means of bounded random variables by betting", arXiv:2010.09686 (JRSSB 2024; journal metadata not verified here).** Status: **OPENED** (§2, Thm 1, Prop. 3 read). §2: observations in [0,1] with *conditional mean* mu given the past, i.e. P^mu = all laws with E(X_t | X_1..X_{t-1}) = mu, which includes adaptively chosen conditional laws. **Prop. 3 (universal representation)**: for any set S, (M_t) is a test martingale for S iff M_t = prod (1 + lambda_i Z_i) with E_S[Z_i | F_{i-1}] = 0 for every S in S and lambda_i predictable; for test supermartingales replace "= 0" by "<= 0".
- **Grunwald, de Heide, Koolen, "Safe Testing", arXiv:1906.07801v5.** Status: **OPENED at abstract/intro only.** E-values safe under optional continuation; GRO e-variables for composite nulls. Not used in a reduction.
- **Ruf, Larsson, Koolen, Ramdas, "A composite generalization of Ville's martingale theorem using e-processes", arXiv:2203.04485.** Status: **ABSTRACT/intro.** Not used.
- Reductions of the *adaptive causal null* to this literature:
  - **Validity of the causal family p_t in [0,1/2], p_t adapted**: *partially reduces*. Null sets of conditional-mean type (<= 1/2 for binary X_t) are the standard object for test supermartingales; a bet product prod(1+lambda_i(X_i - 1/2)) with predictable lambda_i >= 0 is a test supermartingale under every adaptive null (Prop. 3 with "<= 0"). This yields safety of *e-process-based* promotion rules (Ville), which is a different route from our pathwise coupling.
  - **Zc / R coupling step ("monotone events are safe under all adaptive nulls")**: *does not reduce* to these sources. Difference: they certify specific constructed test processes (supermartingales), not arbitrary monotone events of a learner-chosen, delayed label order; no source states the statement "P_nu(g(Y)=1) <= P_{1/2}(g(Y)=1) for every nondecreasing g and every adapted p_t <= 1/2" in that form.
  - **Optimal-policy value comparison V*_causal vs V*_IID**: *does not reduce* (these are validity-first frameworks; they compare power/growth rate, not optimal constrained values).

## 4. Stochastic dominance and coupling for adapted sequences

### 4.1 Roch, *Modern Discrete Probability* draft, Chapter 4 "Coupling" (UW-Madison Math 833, Fall 2014)
- Status: **OPENED** (lecture-note PDF; Def. 4.9, Thm 4.11, Def. 4.16, Thm 4.17 read). Lecture notes, not a peer-reviewed source; sections 4.1 are "to be written".
- **Theorem 4.11 (Strassen)**: on a finite poset, X stochastically dominates Y iff there is a monotone coupling. **Theorem 4.17 (Strassen for Markov kernels)**: if P, Q are transition matrices on a finite poset with x <= y => P(x,.) <=_st Q(y,.), then for x0 <= y0 there is a coupling of the chains with X_t <= Y_t for all t almost surely. Remark 4.12: Strassen extends to Polish spaces with closed order.
- Reduction (own derivation): take the chain state to be the full history (including the learner's public actions) in the coordinatewise partial order; the causal null kernel P(x, .) has next label Bernoulli(p(x)) with p(x) <= 1/2, the IID kernel Q has Bernoulli(1/2); since the history coordinate is carried deterministically, x <= y gives P(x,.) <=_st Q(y,.). Then Thm 4.17 gives the coupling in the **Zc/R step 3** for *Markov* learner strategies (history-measurable, pure). Randomised learners need the private coins added to the state; the delayed/query-order indexing needs an order-preserving relabelling.
  - **R step 3**: *partially reduces* (coupling statement is standard; the label-tape indexing under delayed queries is a bookkeeping extension).
  - **Zc**: *partially reduces*, same argument. The additional content in Zc is the *query-order* index set: events monotone in labels listed in the order the learner queries them, with the coupling shown to survive learner adaptivity. That is a short extension of Thm 4.17 plus a measurability argument, not a new coupling theorem. (Own derivation; unproved here.)

### 4.2 Kamae, Krengel, O'Brien, "Stochastic inequalities on partially ordered spaces", Ann. Probab. 5(6):899-912 (1977), DOI 10.1214/aop/1176995659
- Status: **META**; text NOT FOUND. Cited as the general form of Strassen's theorem (Polish space, closed order); second-hand via the Roch Remark 4.12. Not quoted.

### 4.3 Liggett, Schonmann, Stacey, "Domination by product measures", Ann. Probab. 25(1):71-95 (1997), DOI 10.1214/aop/1024404279
- Status: **META**; text NOT FOUND. Search snippet: domination of dependent Bernoulli fields by product measures under bounded conditional probabilities on graphs. This is the closest "conditional probability bounded implies domination by product Bernoulli" result found, but the statement for adaptive sequences with a learner's choices was not seen and is NOT claimed.

### 4.4 Shaked & Shanthikumar, *Stochastic Orders* (Springer 2007), Ch. 6 (multivariate stochastic orders)
- Status: **NOT FOUND** (book). I could not confirm the existence or number of a "conditional stochastic ordering" theorem for sequences (e.g. "Theorem 6.B.3") and do not assert one. Dumbgen & Mosching (arXiv:2209.07868, ABSTRACT/skim only) is a related paper extending stochastic and likelihood-ratio order results to conditional distributions of general measures. The earlier plan to cite Shaked-Shanthikumar for "domination of adapted sequences" is unsupported at this time.

## 5. Price of robustness, conservatism, and adversary adaptivity

### 5.1 Bertsimas & Sim, "The Price of Robustness", Oper. Res. 52(1):35-53 (2004), DOI 10.1287/opre.1030.0065
- Status: **META** (Crossref verified). Text NOT FOUND. Content (static linear programs, budget of uncertainty Gamma, cost of protection against Gamma coefficient deviations) is as characterised in the earlier notes, not re-read.
- Reduction of **C3'**: *does not reduce* (static LP, polyhedral budget uncertainty, no sequential adaptivity or label dynamics); "premium Gamma" in our paper is a different object from their parameter Gamma. Same for **N1**.

### 5.2 Conservative / safe bandits (cost of conservatism)
- Wu, Shariff, Lattimore, "Conservative Bandits", arXiv:1602.04282 (ICML 2016): ABSTRACT only. Maintain reward above a baseline uniformly over time; the abstract-level result is the regret cost of the conservatism constraint.
- Amani, Alizadeh, Thrampoulidis, "Linear Stochastic Bandits Under Safety Constraints", arXiv:1908.05814 (NeurIPS 2019): ABSTRACT only.
- Pacchiano, Ghavamzadeh, Bartlett, "Stochastic Bandits with Linear Constraints", arXiv:2006.10185: ABSTRACT only.
- Reduction of **C3'/N1/Gamma as a "price"**: *does not reduce*. These price a safety constraint on the learner's own rewards in a stochastic environment; Gamma prices the *calibration null* (IID vs adaptive) with an adversary, in a testing/promotion game. Zero overlap in object; no search hit used the phrase "price of causal/robust safety" in a sequential-testing context. The earlier-search negative (Q2) stands.

### 5.3 Oblivious versus adaptive adversaries
- Arora, Dekel, Tewari, "Online Bandit Learning against an Adaptive Adversary: from Regret to Policy Regret", arXiv:1206.6400 (ICML 2012): ABSTRACT only. Regret is inadequate when the adversary adapts to the learner; policy regret is proposed. Dekel, Ding, Koren, "Bandits with Switching Costs: T^{2/3} Regret", arXiv:1310.2997: ABSTRACT only (adversarial bandit with unit switch cost; relevant as the same combination "switch cost + adaptive adversary" with a regret, not safety, objective).
- Reduction of **Gamma as an adaptive-vs-oblivious gap**: *does not reduce* (regret gap in repeated play vs. error-constraint calibration gap in a one-shot promotion test). Listed as conceptual neighbour only.

### 5.4 Rectangularity (robust MDPs)
- Iyengar, "Robust Dynamic Programming", Math. Oper. Res. 30(2):257-280 (2005), DOI 10.1287/moor.1040.0129, and Nilim & El Ghaoui, Oper. Res. 53(5):780-798 (2005), DOI 10.1287/opre.1050.0216: **META** only. Per the Ou-Bi review (OPENED, arXiv:2404.00940v4, §1-2.2): they independently show a robust MDP with (s,a)-rectangular uncertainty can be solved by a robust Bellman recursion.
- Wiesemann, Kuhn, Rustem, "Robust Markov Decision Processes", Math. Oper. Res. 38(1):153-183 (2013), DOI 10.1287/moor.1120.0566: **META**; text NOT FOUND (Optimization-Online URL guess was a different paper, deleted). Second-hand (Ou-Bi): NP-hardness for general convex non-rectangular sets, s-rectangular sets admit efficient robust policy iteration, and randomised stationary policies may be needed under s-rectangularity (Prop. 1 per a 2025 citing paper; unverified).
- Epstein & Schneider, "Recursive multiple-priors", J. Econ. Theory 113(1):1-31 (2003), DOI 10.1016/S0022-0531(03)00097-8: **META**. Per Ou-Bi (§2.2): rectangularity corresponds to dynamic (time) consistency; it "precludes an inter-temporal budget for unfavorable outcomes". Shapiro, "Rectangular sets of probability measures", Oper. Res. 64(2):528-541 (2016), DOI 10.1287/opre.2015.1466: **META** (nested-form condition per Ou-Bi).
- Goyal & Grand-Clement, "Robust Markov Decision Process: Beyond Rectangularity", arXiv:1811.00215 / Math. Oper. Res. 2022 (DOI 10.1287/moor.2022.1259): **ABSTRACT only** (factor-matrix uncertainty; under rectangularity there is an optimal deterministic robust policy and the maximum principle holds).
- Krale et al., "On Evaluating Policies for Robust POMDPs", NeurIPS 2025 (**OPENED pp. 1-9, per `PRIOR_ART_MATRIX.md`, not re-read here**): (s,a)-rectangular robust POMDP, policy evaluation via a "nature MDP" with extreme-point best responses (Thm 3). Relation to V*_causal: gives the value of a *fixed* policy against the worst rectangular adversary (a risk evaluator), not the constrained optimum over learner policies.
- Reductions:
  - **Definition of the causal null family**: *reduces* to a (s,a)- (history-)rectangular uncertainty set over per-step conditional laws; this is the standard setting where an adversary best-responds by dynamic programming (robust Bellman; Fauss et al. Thm 6 is the sequential-testing instance).
  - **Gamma = V*_causal - V*_IID**: *does not reduce* — in the rectangular robust-MDP literature the object of interest is the max-min value; the *gap* to a fixed nominal law (a single point of the set) as a function of problem structure is not a statement I found. Closest: the "conservatism" discussion in Ou-Bi §1 (rectangular sets give conservative policies), qualitative only.
  - **R**: *does not reduce*. Rectangularity gives that the worst-case adversary can be found by recursion; R states that when the Lagrangian-optimal plans are monotone the adversary's best response is the nominal null (so the supremum is attained at the IID member) — a statement about *where the sup is attained*, not found in the sources read.

### 5.5 Other sequential-design neighbours (not re-opened; recorded for completeness)
- Chernoff, "Sequential design of experiments", Ann. Math. Statist. 30(3):755-770 (1959), DOI 10.1214/aoms/1177706205: META.
- Naghshvar & Javidi, "Active Sequential Hypothesis Testing", Ann. Statist. 41(6):2703-2738 (2013), arXiv:1203.4626: **OPENED at abstract/headings**; Markov stationary policies and dynamic-programming bounds for the Bayesian cost; Bayesian (fixed prior) and no composite adaptive null, so no IID-vs-adaptive calibration comparison.
- Heck, Macak, Ceska, "Constrained and Robust Policy Synthesis with Satisfiability-Modulo-Probabilistic-Model-Checking", AAAI 2026, arXiv:2511.08078v2: **OPENED at abstract/intro/benchmarks skim**. Synthesises policies satisfying structural constraints for all environments in a finite family of MDPs (decision trees, memoryless POMDP policies). A fixed-family synthesis tool; no sequential testing, no label budget, no mixture-of-plans duality. *Does not reduce* any result.

## 6. Summary map: closest source per result

| Result | Closest source(s) | Status | Verdict |
|---|---|---|---|
| R (Lagrangian reduction) | Walraven-Spaan §2-3 (LP over policy mixtures, Lagrangian bound, Thm 3); Yost-Washburn 2000 (via W-S) | OPENED / META | steps 1-2 reduce; hypothesis "value-level monotone-Lagrangian => sup attained at IID" does not reduce |
| R step 3 and Zc (coupling) | Roch Thm 4.11/4.17 (Strassen, Markov kernels); Kamae-Krengel-O'Brien (META) | OPENED (notes) / META | partially reduces: history-measurable pure strategies via Thm 4.17 (own derivation); query-order, delay, randomised coins is extension |
| Z1/W (B=1) | Krishnamurthy Thm 4.3.1, 5.2.1, 5.3.1, 6.3.4 | OPENED | partially reduces (mechanism standard; two-law Lagrangian, delay, query decision, event monotonicity differ) |
| N1 (exact Gamma, B=1) | Fauss-Zoubir-Poor (Ann. Stat. 2020) as the nearest minimax-sequential-test source | OPENED | does not reduce (no premium formula; no source computing V_robust - V_nominal exactly found) |
| C3' (positive premium family) | Bertsimas-Sim 2004 (META); conservative-bandit literature (ABSTRACT) | META / ABSTRACT | does not reduce (static / regret objects) |
| U (multi-label, open) | Krishnamurthy Thm 5.3.1 remark (monotone policy only X=2, open for X>=3); Banerjee-Veeravalli three-threshold counterexample (notes) | OPENED / earlier notes | does not reduce; sources indicate monotone-policy proofs beyond X=2 are open |
| Adaptive-null validity (family definition) | Fauss et al. §2.3 (2.6) and Thm 6; Waudby-Smith-Ramdas Prop. 3; Ramdas et al. | OPENED | family and its supermartingale route reduce; monotone-event coupling route not found |
| Rectangularity lens | Iyengar 2005 / Nilim-El Ghaoui 2005 (META, via review); Wiesemann et al. 2013 (META); Ou-Bi review | META / review OPENED | adaptive causal null = rectangular set; the Gamma-vs-nominal gap statement not found |

## 7. Search coverage and limits (for the novelty reviewer)

- Searches run (web search plus Crossref and arXiv API): structural POMDP / Lovejoy; Krishnamurthy book TOC; Altman CMDP; CPOMDP duality / randomisation (Kim, Poupart, Walraven-Spaan, Helmeczi); Huber, Huber-Strassen, Fauss et al.; testing by betting / composite nulls; "domination by product measures", Strassen, Roch; price of robustness, conservative / safe bandits; adaptive-vs-oblivious adversary; rectangularity (Iyengar, Nilim, Wiesemann, Epstein-Schneider, Shapiro, Goyal). Each sub-topic was searched one to three times; absence of a hit is not proof of absence.
- Not found (explicit): Huber / Huber-Strassen / Kamae-Krengel-O'Brien / Liggett et al. primary text; Kim et al. 2011; Altman 1999; Wiesemann et al. 2013; Bertsimas-Sim 2004 text; Shaked-Shanthikumar chapter 6.
- Specific queries with no relevant hit: (i) a published statement that monotone test events are safe under all predictable null parameters p_t <= p (found only specific supermartingale constructions and the Roch/Strassen coupling machinery); (ii) any result computing the gap between an IID-null-calibrated and an adaptive-null-calibrated optimal sequential design; (iii) "price of robust/causal safety" wording in sequential testing or bandits.
- The ARIS/Codex reviewer slot remains blocked (BL-1); nothing here was externally reviewed.
