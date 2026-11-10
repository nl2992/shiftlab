# Paper 4 Literature Notes (WP E)

Date: 2026-11-10. Written incrementally; sections marked DONE are complete, others are appended as read.

## 0. Method statement

Followed the HKUSTDial `deep-research` skill (`.agents/skills/deep-research/SKILL.md`): research questions frozen first (below), several search perspectives (mainstream structural-POMDP school, QCD/controlled-sensing, robust-optimisation/anytime-valid critics, algorithmic/verification adjacent fields), per-source verification, and evidence-first synthesis ending in per-question answers.

Steps I could not perform or performed only partly:
- Sub-agents were not used; perspectives were run serially by me.
- The skill's `references/*.md` files (citation-protocol, synthesis-framework, self-adversarial) were NOT read; I applied the SKILL.md rules only (verify every citation, unconfirmable means unused, calibrated hedging).
- Verification was by retrieving full text (arXiv / JAIR / MIT / author pages, converted with `pdftotext`) or Crossref metadata. Sources I only know from search snippets are marked "NOT READ".
- Krishnamurthy's 2016 Cambridge book was not accessible; I read the author's 130-page arXiv tutorial that covers the same structural chapters (the book chapter numbering differs; I cite the tutorial's numbering).
- Lovejoy (1987) and Rieder (1991) full texts were not accessible (paywalled). Their content is known here only through Krishnamurthy and Pareek's description.
- Full reading of Walraven-Spaan, Bork et al., Haugh-Lacedelli, Bosansky et al. was done for theorem/algorithm sections, not every proof.
- The AAAI OJS site is bot-blocked (confirmed: BotStopper page). dblp is blocked (Anubis). Crossref and arXiv PDFs worked.

## 1. Frozen research questions

- Q1 (WP C): Which structural results give monotone (threshold / increasing-in-observations) optimal policies for POMDPs and optimal stopping under TP2 transitions and MLR observations (Lovejoy 1987, Rieder, Krishnamurthy, Topkis), especially for constrained or randomised-constraint versions, and with delayed observations or costly sensing (controlled sensing, quickest change detection with sampling control, e.g. Banerjee-Veeravalli data-efficient QCD)?
- Q2 (WP C): Which price-of-robustness results quantify the cost of robust versus nominal chance constraints (Bertsimas-Sim 2004; distributionally robust chance constraints), and is there any result comparing worst-case adaptive-null (game-theoretic / e-process / anytime-valid) false-alarm control with i.i.d.-null calibration in sequential-testing cost?
- Q3 (WP C5): What is known about adaptivity gaps (adaptive vs non-adaptive sampling/sensing: stochastic probing, sequential design of experiments / Chernoff), especially under adversarial or composite nulls?
- Q4 (WP B): What is known on constrained-POMDP column generation and its pricing problem, abstraction refinement with certificates for POMDPs, robust FSC synthesis, one-sided POSG HSVI, sequence-form double oracle, information-relaxation duality for POMDPs, and the Heck et al. AAAI 2026 paper?

## 2. Source entries

Each entry: citation, URL, what I read, key statement, assumptions, bearing.

### Q1 sources

#### S1.1 Krishnamurthy, V. "Structural Results for Partially Observed Markov Decision Processes: A Tutorial", arXiv:1512.03873 (Dec 2015), 130 pages.
- URL: https://arxiv.org/abs/1512.03873
- Read: full text converted; read in detail Section 4.5 (assumptions F1-F4), Ch. 6 (Sections 6.2, 6.3 including Theorems 6.2.1, 6.3.3, 6.3.4). Skimmed Ch. 7 headings (QCD as stopping POMDP). Chapters on multi-armed bandits, costly sensing in other chapters NOT read.
- Key statements (paraphrase): Thm 6.2.1: for a stopping-time POMDP with linear stopping cost the stopping set R1 is convex in the belief simplex (proof via concavity of V). Thm 6.3.4 (switching curve): under (C) cost monotone in first-order stochastic order, (F1) B TP2, (F2) P TP2, (S) submodularity of the cost on the MLR-chains, there exists an optimal policy that is MLR-increasing on lines L(e1, pi_bar), L(eX, pi_bar); a switching curve Gamma splits the simplex into two connected regions and intersects each such line at most once. For X=2 there is a unique threshold. The tutorial explicitly says full MLR monotonicity on the whole simplex (6.10) is hard because MLR is only a partial order on the simplex, so it proves it only on lines.
- Assumptions: finite state/action, known P and B, belief-state (Bayesian filter) formulation, two actions {stop, continue} for the stopping result, costs nonlinear in belief allowed but must satisfy (C) and (S); undelayed observations; expectation criterion.
- Bearing: this is the standard "TP2 + MLR gives monotone threshold" source for stopping POMDPs. It covers neither randomised/chance constraints, nor delayed observations, nor sensing choice as an additional action (that case needs the multi-action Lovejoy/Rieder conditions, see S1.2).

#### S1.2 Krishnamurthy, V. and Pareek, U. "Myopic Bounds for Optimal Policy of POMDPs: An Extension of Lovejoy's Structural Results", Operations Research 63(2):428-434 (2015), arXiv:1404.3328.
- URL: https://arxiv.org/abs/1404.3328
- Read: full 12-page arXiv text; assumptions (A1)-(A5), Theorems 1-2 statements, introduction. Proofs in appendix skimmed only.
- Key statements: They state that the sufficient conditions of Lovejoy (1987, Prop. 2) and Rieder (1991, Thm 5.6) are "not useful" in the sense that non-trivial examples satisfying conditions (c),(e),(f) cannot be generated (the required TP2 stochastic ordering of P(a+1) over P(a) and B(a+1) over B(a) is impossible for stochastic matrices unless the matrices coincide or are rank one). They relax to (A4),(A5) and prove Thm 1: under (A1)-(A5) a myopic policy lower/upper-bounds the optimal policy (sandwiches mu*(pi)), with TP2 P_a, B_a (A3).
- Assumptions: finite state, finite action set ordered, discounted infinite horizon, cost monotone via (A1)/(A2), copositivity condition (A4).
- Bearing: critical caveat for WP C. Lovejoy's multi-action monotone-in-belief policy result has a literature-acknowledged flaw in its stated conditions, and the repaired result is a myopic sandwich, not a full threshold structure. Any ShiftLab theorem claiming "optimal sampling/alarm policy monotone in belief under TP2+MLR" cannot just cite Lovejoy for the action-selection part; it needs either the stopping-only result (S1.1) or its own proof.
- Lovejoy (1987) itself: W. S. Lovejoy, "Some Monotonicity Results for Partially Observed Markov Decision Processes", Operations Research 35(5):736-743. Existence verified (RePEc record, https://econpapers.repec.org/RePEc:inm:oropre:v:35:y:1987:i:5:p:736-743). NOT READ in full; only abstract: sufficient conditions for the optimal value to be monotone on belief vectors ordered by likelihood ratio, and for the optimal policy to be bounded below by a monotone function (and monotone in a machine replacement problem).
- Rieder (1991) "Structural results for partially observed control models", Methods and Models of OR 35:473-490: cited by S1.2 (Theorem 5.6); NOT READ, not independently verified beyond that citation.
- Topkis: C. Topkis, "Minimizing a submodular function on a lattice", Operations Research 26(2):305-321 (1978). Cited via S1.1 (the tutorial states Topkis theorem as Thm 6.3.3: submodular Q gives an increasing selection of argmin). NOT READ directly.

#### S1.3 Banerjee, T. and Veeravalli, V. V. "Data-Efficient Quickest Change Detection with On-Off Observation Control", arXiv:1105.1361 (v3 22 Nov 2011); Sequential Analysis 31(1) 2012 (journal details taken from memory, NOT verified in this session).
- URL: https://arxiv.org/abs/1105.1361
- Read: abstract, Section II (problem, Bellman equation, structure (6), Algorithm 1, Figures 1-2 discussion), statements of Theorems 1-7 located but only Section II read in detail.
- Key statements: The Bayesian problem (min delay s.t. false-alarm and expected number of observations before change) is relaxed by Lagrangian; the optimal policy takes an observation iff d(p_k) = B0(p_k) - B1(p_k) >= lambda_e (1 - p_k), and stops when p_k > A*. Because d is not concave, the line can cross d more than twice; the authors observe numerically a two-threshold structure for most parameters but exhibit a case (rho = 0.7, lambda_f = 100, lambda_e = 5) where the optimal policy has three thresholds, i.e. the two-threshold (monotone "sample if belief above B") policy is NOT optimal in general. They prove asymptotic optimality of the two-threshold rule as false-alarm probability tends to 0.
- Assumptions: i.i.d. pre- and post-change densities, geometric change prior, known distributions, observation cost per sample, no delay.
- Bearing: key negative caveat. Even in the simplest costly-sensing QCD model, an exact monotone threshold structure for the sampling decision is not a theorem; only asymptotic optimality is proved. A ShiftLab claim of exact monotone sensing policy would be new only if it adds conditions that exclude the three-threshold example, and must be checked against it.

#### S1.4 Banerjee, T. and Veeravalli, V. V. "Data-Efficient Minimax Quickest Change Detection with Composite Post-Change Distribution", arXiv:1410.3450 (2014).
- URL: https://arxiv.org/abs/1410.3450. NOT READ (title/abstract from search only). Bears on composite post-change and minimax setting.

#### S1.5 Nitinawarat, S., Atia, G. K., Veeravalli, V. V. "Controlled Sensing for Multihypothesis Testing", IEEE Trans. Automatic Control 58(10), 2013.
- Existence: recalled, NOT verified (my attempted arXiv id fetch returned an unrelated paper). Not used in conclusions. Related verified source: S3.2 below.


#### S1.5b Geng, J., Bayraktar, E., Lai, L. "Bayesian Quickest Change-Point Detection with Sampling Right Constraints", IEEE Trans. Information Theory (2014), arXiv:1309.5396v2.
- URL: https://arxiv.org/abs/1309.5396
- Read: abstract, introduction, statements of Propositions/Theorems 3-6 located by grep; proofs NOT read.
- Key statements (abstract-level, verified in text): with at most N observations allowed ("limited sampling right") the optimal stopping rule is a threshold rule and its delay is asymptotically close to classical Bayesian QCD as false alarm probability goes to 0. With stochastically replenished sampling rights the optimal solution "has a very complex structure"; a low-complexity rule (sample while rights remain, threshold stop) is shown first-order asymptotically optimal only.
- Assumptions: i.i.d. pre/post densities, geometric-type prior, immediate observations.
- Bearing: the closest verified result to "constrained sensing budget in QCD". Exact structure holds for a hard count constraint; the stochastic-budget case is only asymptotic. Neither covers chance/randomised constraints on an action-cost budget, nor delayed observations.

#### S1.6 Krishnamurthy, V. and Djonin, D. V. "Structured threshold policies for dynamic sensor scheduling - a partially observed Markov decision process approach", IEEE Trans. Signal Processing 55(10):4938-4957 (2007).
- Existence and page range confirmed via search listing; author attribution not shown in the listing (taken from the citation I was given; verify on IEEE Xplore). NOT READ.
- Per the listing: sufficient conditions on cost, dynamics and observation kernel for an MLR-threshold optimal scheduling policy; stochastic approximation to estimate the best linear MLR threshold. I could not verify whether a constrained/randomised version is treated; do not cite for that.

#### S1.7 Krishnamurthy, V. "Partially Observed Markov Decision Processes: From Filtering to Controlled Sensing", Cambridge University Press (2016), ISBN 978-1-107-13460-7.
- URL: https://www.cambridge.org/core/books/partially-observed-markov-decision-processes/ (catalog pages only). Chapter 8 "POMDPs in controlled sensing and sensor scheduling", pp. 179-200, exists per Cambridge Core. Book text NOT READ; used the arXiv tutorial S1.1 as proxy.

#### S1.8 Delayed observations
- Search for QCD/POMDP structure with delayed observations returned nothing directly on point (the results were S1.3, S1.5b and related QCD papers). I found no verified source giving monotone-threshold structure under delayed feedback in a POMDP with TP2/MLR. Standard route (state augmentation with the delay buffer) breaks the 2-state or TP2 structure of the augmented chain in general; I did not find a paper proving it either way. Treat as apparently uncovered, with the caveat that my search was one query.

### Q2 sources

#### S2.1 Bertsimas, D. and Sim, M. "The Price of Robustness", Operations Research 52(1):35-53 (2004), doi 10.1287/opre.1030.0065.
- URL: https://www.mit.edu/~dbertsim/papers/Robust%20Optimization/The%20price%20of%20Robustness.pdf
- Read: abstract, Section 1-3 formulation, Proposition 1, Theorem 1 (LP equivalent), Proposition 2, Theorem 3 statement (a)-(c) (garbled by OCR; bound in terms of a binomial-type expression B(n, Gamma) with a looser bound of Gaussian type), numerical sections skimmed only.
- Key statements: each constraint has uncertain coefficients a_ij in [a_ij - a^_ij, a_ij + a^_ij]; at most Gamma_i of them are allowed to deviate (budget of uncertainty). Gamma_i = 0 gives the nominal problem, Gamma_i = |J_i| gives Soyster's worst case (Theorem 1: the robust counterpart is an LP). Theorem 3(a): if the perturbations eta_ij are independent and symmetric on [-1,1], the probability that constraint i is violated by the robust solution is at most B(n, Gamma_i), and (b) the bound is tight for symmetric Bernoulli(+-1) variables. The "price of robustness" is the (numerically reported) objective loss as Gamma grows; the paper does not give a closed form loss bound across all problems.
- Assumptions: static one-stage linear/mixed-integer program, coefficient-wise uncertainty independent across coefficients and symmetric, bounded support; guarantee is on per-constraint violation probability.
- Bearing: gives a tunable robust-vs-nominal trade-off with an explicit violation-probability guarantee. It is not sequential, not about stopping times, and its independence/symmetry assumptions do not match an adaptive adversary. At best it is a modelling analogue for a "budgeted adversary" null.

#### S2.2 Wiesemann, W., Kuhn, D., Sim, M. "Distributionally Robust Convex Optimization", Operations Research 62(6):1358-1376 (2014), doi 10.1287/opre.2014.1314.
- URL: https://econpapers.repec.org/RePEc:inm:oropre:v:62:y:2014:i:6:p:1358-1376. Abstract only (via search results). NOT READ in full.
- Abstract-level: framework for ambiguity sets built from conic-representable confidence sets with mean on an affine manifold; sharp tractability conditions. No sequential or stopping-time content seen. I did not retrieve a source quantifying the cost of DR chance constraints versus nominal beyond this, and did not find Calafiore-El Ghaoui or Nemirovski-Shapiro texts (searched once; not verified).

#### S2.3 Ramdas, A., Grunwald, P., Vovk, V., Shafer, G. "Game-Theoretic Statistics and Safe Anytime-Valid Inference", Statistical Science (2023), arXiv:2210.01948.
- URL: https://arxiv.org/abs/2210.01948
- Read: Sections 1-2 (test martingales, e-processes, Ville's inequality), Appendix B ("Does SAVI come at a price?"). Other sections skimmed.
- Key statements: an e-process E for a composite null P satisfies E_t <= M_t^P for a test martingale family; Ville's inequality for composite P: sup_P P(exists t: E_t >= 1/alpha) <= alpha, equivalently P(E_tau >= 1/alpha) <= alpha for every stopping time tau (eqs. 9-10 in the arXiv version). Appendix B states that anytime-valid confidence sequences tend to be between 1.5 and 2 times as wide as fixed-sample intervals, while with optional stopping expected stopping times under the alternative can be about the same as or smaller than the fixed n of a Neyman-Pearson test; "it all depends how one measures performance".
- Assumptions: nonnegative (super)martingales w.r.t. a filtration; composite nulls handled via a family of test martingales or e-processes.
- Bearing: this is the best verified qualitative statement on the cost of worst-case anytime validity. It is not a theorem quantifying adaptive-null versus i.i.d.-calibrated cost in a decision-theoretic stopping problem.

#### S2.4 Howard, S. R., Ramdas, A., McAuliffe, J., Sekhon, J. "Time-uniform, nonparametric, nonasymptotic confidence sequences", Annals of Statistics 49(2) (2021), arXiv:1810.08240.
- URL: https://arxiv.org/abs/1810.08240
- Read: abstract, introduction (eq. 2 finite-LIL boundary with constant 1.7 and log log(2t)), contribution list. Theorems 1 and 3 statements not read in detail.
- Key: time-uniform boundaries cost an extra O(sqrt(log log t)) factor over pointwise intervals; stitching gives closed-form sub-Gaussian boundaries (Thm 1). Quantifies the price of time-uniform validity against fixed-n for the mean estimation problem; again not a stopping-cost-with-actions result.

#### S2.5 Shin, J., Ramdas, A., Rinaldo, A. "E-detectors: a nonparametric framework for sequential change detection", arXiv:2203.03532v4 (Oct 2023); published in the New England Journal of Statistics in Data Science (2024; venue taken from memory, not verified).
- URL: https://arxiv.org/abs/2203.03532
- Read: Section 2.1-2.4 (Definition 2.2, Theorem 2.4, Remark 2.1, Proposition 2.14), statements of Prop 3.3, Thm 3.4, Thm 4.3 located. Proofs not read.
- Key statements: Definition 2.2: M is a P-e-detector if E_{P,infinity}[M_tau] <= E_{P,infinity}[tau] for all stopping times tau and P in P. Theorem 2.4: stopping at inf{n: M_n >= 1/alpha} gives inf_P E_{P,inf} N* >= 1/alpha (ARL control). Remark 2.1: ARL results need no assumption on the change time or post-change law; "an adversary may adaptively decide" when to stop pre-change data. Proposition 2.14: worst average delay of e-SR / e-CUSUM bounded by E_{0,Q} of a first-passage time at 1/alpha (or c_alpha <= 1/alpha), with an explicit bound log(c)/E log L + variance term + 1 for i.i.d. post-change (eq. 19).
- Assumptions: for ARL, only the e-detector inequality (a supermartingale-type property under the pre-change class); for delay, post-change observations independent of pre-change and stationary, baseline increments functions of a window.
- Bearing: the verified worst-case-null (adaptive/composite) false-alarm guarantee for change detection. It has no costly-sensing or action component and no constrained POMDP. The trade-off "threshold 1/alpha vs. i.i.d.-calibrated threshold" is visible in Prop 2.14 (c_alpha <= 1/alpha) but no general theorem compares the two.

### Q3 sources

#### S3.1 Gupta, A., Nagarajan, V., Singla, S. "Adaptivity Gaps for Stochastic Probing: Submodular and XOS Functions", SODA 2017, arXiv:1608.00673.
- URL: https://arxiv.org/abs/1608.00673
- Read: abstract, introduction, statements of Theorems 1.1-1.4. Proofs NOT read.
- Key statements: Thm 1.1: for any monotone nonnegative submodular f and any prefix-closed probing constraint the adaptivity gap is at most 3 (lower bound e/(e-1)). Thm 1.2: non-monotone submodular, gap at most 40. XOS functions of width W have gap O(log W / log log W)-type, nearly tight; for general functions no small gap (Appendix B).
- Assumptions: each element active independently with known probability; probing reveals status; prefix-closed outer constraint; submodular or XOS value.
- Bearing: independence of element activity and a fixed (non-adversarial) probability model. Not directly about composite or adversarial nulls or about sequential testing; it is the closest "adaptivity gap is constant under submodularity" theorem.

#### S3.2 Naghshvar, M. and Javidi, T. "Active Sequential Hypothesis Testing", Annals of Statistics 41(6):2703-2738 (2013), arXiv:1203.4626.
- URL: https://arxiv.org/abs/1203.4626
- Read: abstract, Section 2.2 overview, locations of Theorems 1-3 and Corollaries; proofs NOT read.
- Key statements: Chernoff (1959) proposed an adaptive action-selection scheme for active (controlled) binary composite hypothesis testing and showed asymptotic optimality as the cost of a wrong declaration goes to infinity; N&J give non-asymptotic lower bounds on optimal expected cost via dynamic programming, and analyse two adaptive heuristics, one asymptotically optimal in Chernoff's sense. They also state that Chernoff's notion neglects the number of hypotheses M and give results at nonzero information-acquisition rate.
- Assumptions: finite hypotheses, known observation kernels per action, Bayesian prior with penalty for wrong declaration.
- Bearing: Chernoff-type adaptivity is the benchmark for adaptive vs fixed sensing. This paper does not compute an adaptive-vs-nonadaptive gap; it is a benchmark for adaptive sensing with composite alternatives, not for an adversarial null.
- Chernoff (1959) "Sequential design of experiments", Annals of Math. Statistics 30:755-770: cited via S3.2; NOT READ.

#### S3.3 Dean, B. C., Goemans, M. X., Vondrak, J. "Approximating the Stochastic Knapsack Problem: The Benefit of Adaptivity", Mathematics of Operations Research 33(4) (2008).
- URL: https://math.mit.edu/~goemans/PAPERS/DeanGoemansVondrak-2008-ApproximatingTheStochasticKnapsackProblem.pdf. Abstract-level from search only; NOT READ. Reported: adaptivity gap at most 4 for stochastic knapsack.

#### S3.4 Gupta, Nagarajan, Singla, "Algorithms and Adaptivity Gaps for Stochastic Probing", SODA 2016.
- Existence confirmed by search; results quoted there (O(log n) for prefix-closed outer with matroid inner constraints, etc.) were only from search snippets; NOT READ. Not used in conclusions.

#### S3.5 Adversarial / composite nulls and adaptivity gap
- I found no verified source that defines or bounds an adaptivity gap for sensing under an adversarial or composite null (one search plus the above readings). Absence of evidence is not proof.

### Q4 sources

#### S4.1 Walraven, E. and Spaan, M. T. J. "Column Generation Algorithms for Constrained POMDPs", JAIR 62:489-533 (2018).
- URL: https://www.jair.org/index.php/jair/article/view/11216 (read via https://jair.org/index.php/jair/article/download/11216/26427/20795)
- Read: Sections 2.2-3.2 (LP (8), reduced cost, Lemmas 1-5, Theorems 1-3), 4.4 algorithm skim, Section 4.5 headings. Experiments NOT read.
- Key statements: Constrained POMDP: max V^pi s.t. C^pi <= L (expected cumulative cost); an optimal policy may need to randomise, and the best deterministic policy may be suboptimal. LP (8) is over distributions on policies; column generation solves one unconstrained POMDP per iteration with reward R - lambda C (the pricing problem), and Lemma 1: each iteration returns a policy maximising reduced cost V - lambda C - lambda_i. Theorem 1/2: exact column generation terminates iff it has found an optimal Constrained-POMDP solution. Theorem 3: at most one agent needs to randomise its policy choice (n+1 LP constraints). With approximate pricing (point-based + policy graph) Lemma 1 and Lemma 4 are no longer valid; they give an adapted algorithm with bounds.
- Assumptions: finite-horizon, expected-cost constraint (not chance or path-wise), exact pricing assumed for the theorems, known model.
- Bearing: the pricing problem is exactly a Lagrangian POMDP; if the Lagrangian reward satisfies Krishnamurthy-type monotone structure (S1.1), pricing could exploit threshold policies. This structural link is not stated in the paper (my inference). Single-constraint randomisation in two policies is a standard fact here.
- Related, not read: de Nijs, Walraven, de Weerdt, Spaan, "Constrained Multiagent Markov Decision Processes: a Taxonomy of Problems and Algorithms", JAIR 70 (2021) (title/venue from memory; NOT verified this session). Cited within S4.1: Altman (1999) Constrained MDPs; Isom et al. (2008); Kim et al. (2011) CPBVI; Poupart et al. (2015) CALP; Yost and Washburn (2000) (all NOT READ).

#### S4.2 Bork, A., Junges, S., Katoen, J.-P., Quatmann, T. "Verification of Indefinite-Horizon POMDPs", ATVA 2020, arXiv:2007.00102.
- URL: https://arxiv.org/abs/2007.00102
- Read: Sections 1-4 and part of 5 (definitions, Thm 1-3, Alg. 1 loop, bounds L(b) U(b), exploration/rewiring criteria). Appendix heuristics skimmed.
- Key statements: Theorem 1: value of belief-MDP initial state equals the sup over observation-based policies of reachability probability. Theorem 2: V is convex. Theorem 3: for a discretised belief MDP with an adequate foundation F, V(b) <= sup_sigma Pr in db_F(M), i.e. a sound over-approximation; cut-offs treated as bad states give upper bounds; lower bounds from evaluating concrete observation-based policies. Abstraction-refinement alternates cut-off exploration, foundation extension and rewiring, tightening [L(b), U(b)].
- Assumptions: finite POMDP, unbounded reachability to Bad, single objective, no cost constraint, no adversary.
- Bearing: the certificate is a pair of sound upper/lower bounds, not a counterexample trace (this is not CEGAR in the counterexample-driven sense). Directly relevant as a "refinement with a certificate" template for WP B, but covers probability-of-reach, not expected-cost with constraints.

#### S4.3 Heck, L., Macak, F., Ceska, M., Junges, S. "Constrained and Robust Policy Synthesis with Satisfiability-Modulo-Probabilistic-Model-Checking", AAAI 2026 (Proc. AAAI vol. 40, no. 43, pp. 36253-36261), doi 10.1609/aaai.v40i43.40944; arXiv:2511.08078.
- Identification: Crossref returned exactly one AAAI-26 record with first author Heck on this topic. The coordinator's reference "Heck et al. AAAI 2026" is assumed to be this paper; I could not confirm there is no other Heck AAAI-26 paper. The AAAI OJS page is bot-blocked, so I read the arXiv PDF.
- URL: https://arxiv.org/abs/2511.08078 ; https://doi.org/10.1609/aaai.v40i43.40944
- Read: abstract, Sections 3-4 (problem statement, Thm 4-6 statements), benchmark/Table 1 headings, related-work paragraph. Appendix proofs NOT read; experiments skimmed only.
- Key statements: Problem (Robust Constrained Feasibility): given a colored MDP with controllable parameters X and uncontrollable Y, does there exist theta_X such that for all theta_Y, V(C[theta_X theta_Y]) >= nu (an exists-forall sentence, Eq. 1). Thm 4: satisfying assignments of the existential block iff solutions. Thm 5: if V_max of the induced MDP over the partial assignment is < nu, the partial assignment K is a T_C-conflict (from Andriushchenko et al. 2025b). Thm 6: removing parameters independent of colorings gives a smaller conflict. Deciding conflicts is NP-hard; Thm 5 is complete only if eta is a single point. Benchmarks include fixed-memory FSCs for POMDPs, decision-tree policies and multi-environment POMDPs, each with finite memory/structure.
- Assumptions: finite MDP families, memoryless/finite-memory structure, discrete controllable parameters; objective expected total reward.
- Bearing: this is a CEGIS / SMT conflict-learning scheme for robust and structurally constrained policies, with sound conflicts but NP-hardness. It is not belief-space and does not give cost-constrained POMDP column generation. It supports "robust FSC synthesis" as a baseline family for WP B. The earlier AAAI 2021 paper "Robust finite-state controllers for uncertain POMDPs" (Cubuktepe, Jansen, Junges, Marandi, Suilen, Topcu; AAAI, pp. 11792-11800) appears in S4.3's reference list; NOT READ.

#### S4.4 Horak, K., Bosansky, B., Kovarik, V., Kiekintveld, C. "Solving Zero-Sum One-Sided Partially Observable Stochastic Games", Artificial Intelligence (2023); arXiv:2010.11243v1.
- URL: https://arxiv.org/abs/2010.11243
- Read: abstract, roadmap figure (Thm 1 Bellman equation, Thm 2 value iteration, Thm 3 HSVI works, Thm 4 continual resolving gives epsilon-Nash), headings of Lemma 5.5 (V* convex), Prop 5.8 (V* Lipschitz). Proofs and experiments NOT read. Journal volume/pages not verified here.
- Key statements: one-sided POSG (only one player has imperfect information, the opponent knows the state); value V* convex and Lipschitz over the belief simplex; HSVI with point-based bound updates converges to epsilon-optimal value; continual resolving yields epsilon-Nash strategies.
- Assumptions: zero-sum, discounted, finite sets, the informed player observes the full state.
- Bearing: applies if the ShiftLab adversary (shift generator) is fully informed and the monitor is partially informed. It requires zero-sum payoff and does not include constraints on the monitor; combining with expectation constraints is not in the paper.

#### S4.5 Bosansky, B., Kiekintveld, C., Lisy, V., Pechoucek, M. "An Exact Double-Oracle Algorithm for Zero-Sum Extensive-Form Games with Imperfect Information", JAIR 51:829-866 (2014).
- URL: https://jair.org/index.php/jair/article/download/10924/26040 (full text obtained; pdftotext worked)
- Read: Sections 3.3-3.4, Section 4 intro (restricted game defined by allowed sequences; two complications), Section 5 (Lemma 5.1; Theorem 5.5), Section 6.3 discussion. Experiments tables and BRS pseudocode (Sec 4.2) skimmed only.
- Key statements: the restricted game allows only a subset of sequences; solved with sequence-form LP; best-response sequence algorithm (BRS) finds new sequences. Theorem 5.5: the algorithm terminates iff v(BRS(r_{-i}')) = -v(BRS(r_i')) = V_i^LP = V_i^*, which happens after finitely many iterations, and then the restricted strategies form a Nash equilibrium of the full game. Discussion: not suitable when all equilibria have large support; small-support is not sufficient for speed-up.
- Assumptions: finite, two-player, zero-sum, perfect recall; exact best responses.
- Bearing: guarantee is finite termination and exactness through exact best responses; it does not provide anytime approximation guarantees with inexact oracles, nor constraints.

#### S4.6 Haugh, M. B. and Lacedelli, O. R. "Information Relaxation Bounds for Partially Observed Markov Decision Processes", IEEE Trans. Automatic Control (2020) (venue per search snippets; the version I read is the working paper of 15 April 2019).
- URL: https://martin-haugh.github.io/files/Research/POMDP_IR_March_2019.pdf
- Read: abstract, Section 3 (dual penalty c_t eq. 8, weak duality eq. 9, strong duality statement), Section 6.1 (Definition 6.1 supersolution, Propositions 6.1-6.2). Applications NOT read. I searched the text for "constrain": no treatment of constrained POMDPs found.
- Key statements: with penalty c_t = E[theta_{t+1}(pi_{t+1}) | F_t] - E[theta_{t+1}(pi_{t+1}) | G_t] the dual bound V*_0 <= max over G-adapted policies of E[sum r_t + c_t] holds; strong duality if theta = V*. If theta_t is a supersolution (satisfies theta_t >= max_a {r + E[theta_{t+1}|F_t]}), the information-relaxation bound is at least as tight as theta itself (Prop 6.1, from Brown and Haugh), and MDP, QMDP, Lag-1, Lag-2 approximate value functions are supersolutions (Prop 6.2).
- Assumptions: finite horizon, unconstrained, reward maximisation (upper bound), Monte Carlo evaluation of penalty requires absolute continuity unless supersolution.
- Bearing: certified upper bounds for an unconstrained POMDP policy gap. For a Lagrangian-priced (constrained) POMDP this could certify the pricing step; this extension is not in the paper (my inference).

## 3. Synthesis per question

Legend: (a) direct corollary of a verified known result; (b) partial overlap; (c) apparently uncovered (absence of evidence is not proof; my coverage was one to three searches per sub-topic and abstract-only for several sources).

### Q1 (monotone / threshold structure)
- (a) Direct corollary: only a monotone-threshold (MLR-increasing on lines, unique threshold for two states) *stopping* policy for an *unconstrained, expected-cost, undelayed* stopping POMDP with TP2 P and B, under cost conditions (C),(S) (S1.1 Thm 6.3.4). For a two-state change/no-change belief, "alarm iff posterior >= threshold" is covered. Also covered: convexity of the stopping region (Thm 6.2.1).
- (b) Partial overlap: costly sensing / sampling control. S1.3 shows the sampling region is not always an upper set (three-threshold example) and proves only asymptotic optimality of the two-threshold rule; S1.5b proves the exact threshold only for a hard observation count N. A ShiftLab monotone-sampling theorem must exclude the S1.3 counterexample by explicit conditions, otherwise it contradicts a published numerical example. Multi-action Lovejoy-type monotone policies have documented flawed sufficient conditions (S1.2), so use the repaired myopic-sandwich conditions or prove directly. Lagrangian relaxation (as in S1.3 and S4.1) reduces an expected-cost-constrained problem to a family of unconstrained problems, so structure for each lambda plus the Walraven-Spaan randomisation over two policies would give a "randomised threshold" structure; I did not find this stated as a theorem in a verified source, so it is a plausible corollary of S1.1 + S4.1 + S1.3 whose assumptions still need checking (sampling decision must also be monotone).
- (c) Apparently uncovered: (i) chance (probability-of-event) rather than expected-cost constraints with randomised constraint satisfaction in POMDP stopping with TP2/MLR; (ii) delayed or out-of-order observations with a monotone threshold (no verified source); (iii) full MLR monotonicity of the sampling action on the whole belief simplex for X >= 3 (S1.1 admits only line-wise results).

### Q2 (price of robustness; adaptive null vs i.i.d. null)
- (a) None: no verified source gives a direct corollary quantifying robust-vs-nominal *chance-constrained sequential* cost.
- (b) Partial overlap: S2.1 gives an explicit static trade-off (budget Gamma, violation probability B(n,Gamma), tight for symmetric Bernoulli). S2.3 Appendix B and S2.4 quantify the qualitative price of anytime validity (confidence sequences about 1.5 to 2 times wider; extra log log t in boundary). S2.5 Thm 2.4 and Prop 2.14 give worst-case-null ARL control at threshold 1/alpha and an upper bound on delay in terms of a first-passage time, so a ShiftLab statement of the form "adaptive-null threshold 1/alpha costs at most the stated additional delay over an i.i.d.-calibrated threshold" would be partly a corollary of S2.5 for detection delay without sensing control.
- (c) Apparently uncovered: a theorem comparing the optimal cost of a *controlled-sensing / constrained* stopping problem under a worst-case adaptive (e-process) null versus an i.i.d.-null calibration, with the price expressed in the same units as the budget Gamma. I found none.

### Q3 (adaptivity gaps)
- (a) None applicable.
- (b) Partial overlap: S3.1 constant gaps (3 for monotone submodular, 40 non-monotone) for independent-activity stochastic probing; S3.3 gap 4 for stochastic knapsack (abstract-level only). S3.2/Chernoff gives adaptive-sensing asymptotic optimality benchmarks, i.e. why adaptivity helps asymptotically in composite testing, but not a gap statement.
- (c) Apparently uncovered: adaptivity gap for sensing under adversarial/composite nulls (the null is an adaptive adversary, so independence of element status in S3.1 fails) and for e-process-based false-alarm control. I found nothing.

### Q4 (WP B machinery)
- (a) Direct corollary / reusable: exact column generation structure for expected-cost constrained POMDPs (S4.1 Thm 1-3); LP duality yields a mixture of at most two policies for one constraint; the pricing problem is a Lagrangian POMDP. Sound belief-discretisation upper bounds with refinement (S4.2 Thm 3). Information-relaxation upper bounds with supersolution guarantee (S4.6 Props 6.1-6.2) for an unconstrained POMDP. Sequence-form double-oracle exactness theorem (S4.5 Thm 5.5) for finite zero-sum extensive-form games. HSVI convergence for one-sided zero-sum POSG (S4.4 Thm 3).
- (b) Partial overlap: robust FSC synthesis with structural constraints (S4.3; sound conflicts but NP-hard, memoryless/finite memory); combination of column generation with robust/adversarial pricing is not in S4.1 or S4.3.
- (c) Apparently uncovered: column generation whose pricing problem is a (one-sided) POSG (monitor vs adversary) with an expected-cost budget; certified abstraction refinement for *constrained* POMDPs (Bork et al. handle unconstrained reachability); information-relaxation duals for constrained or game-valued pricing. If a ShiftLab result is "the pricing problem is monotone-threshold so exact pricing is a 1-D search," that is not in any verified source.

## 4. Not-verified list (do not cite without checking)
Lovejoy 1987 and Rieder 1991 full text; Topkis 1978; Chernoff 1959; Nitinawarat-Atia-Veeravalli 2013; Krishnamurthy 2016 book text; Krishnamurthy-Djonin 2007 authorship; Banerjee-Veeravalli journal version (Sequential Analysis 2012); de Nijs et al. JAIR 2021; Cubuktepe et al. AAAI 2021; Calafiore-El Ghaoui; Nemirovski-Shapiro; Dean-Goemans-Vondrak full text; Gupta-Nagarajan-Singla SODA 2016.
