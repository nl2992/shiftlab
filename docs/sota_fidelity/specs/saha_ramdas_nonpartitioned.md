# Spec: Saha & Ramdas, Non-partitioned e-detectors

Status: retrieval spec (step 1). Not yet independently checked. Written 2026-11-06. Nothing
downloaded was executed; code was only read.

Page numbers "pN" = arXiv v1 PDF page (94 pp).

## 1. Citation, version read, code

- Aytijhya Saha (MIT), Aaditya Ramdas (CMU). "Non-partitioned e-detectors for nonparametric
  sequential change detection". arXiv:2607.28322 v1, submitted 30 Jul 2026, stat.ME, 94 pages. The
  arXiv page lists only v1. Preprint, no venue found. PDF sha256 daaf5169...bb75e0 (scratch
  `.../scratchpad/edet/saha/saha.pdf`). The prior ShiftLab audit (docs/exhaustive_evaluation/
  NONPARTITIONED_PFA_AUDIT.md) used the arXiv HTML v1 of the same version.
- Official code: `Aytijhya/Nonseparated-e-detector` @ `1966da8dd36224c000f94f564c7219d3d90e4779`
  (2026-08-12; README is a title only; R and Python scripts, CSV outputs). Linked in the paper
  footnote (p6). Read: run_exact_up_oracle.py, run_bounded_double_asymptotic.py,
  cleveland-bounded.R (main part). Not read: Gaussian scripts, compare_with_glr_pfa.R, notebook.
- Read in full: main text pp1-26 (Sec 1-9), Appendix A statements pp27-32, Sec B.1 proofs of Thm 2.2
  and 2.3 (p36-37). Skimmed: Sec 6-7 theorem statements (pp16-22). NOT read: proofs of Sec 6-7,
  App B.2-B.4, C, D, E (pp37-94).

## 2. Native problem and estimand

- iid data, composite class P of laws on a Polish space. Alternative: X_1..X_T ~ P, X_{T+1}.. ~ Q,
  P != Q, both in P. No-change null H0: X_1, X_2, ... iid R for some unknown R in P (p1). No
  partition into pre/post classes, so a detector must fire on ANY change and is silent on any
  constant law (including a constantly "beneficial" one).
- Metrics (p3-4): ARL(tau) = inf_R E_R[tau]; PFA(tau) = sup_R P_R(tau < inf); CADD at change T;
  under PFA control CADD is infinite so a high-probability delay bound is used (Thm 3.3).
- Feedback: full observation, calendar clock, no labels/costs/delays.

## 3. Exact algorithm

- Def 2.1 (p6): for each R in P and start s, an s-delay e-process M^R_{s:t} (equal to 1 for t < s,
  nonnegative, adapted, E_R[M^R_{s:tau} | F_{s-1}] <= 1 for all stopping times).
- ARL detector, eq (1) (p7): D^ARL_t = inf_{R in P} sum_{s=1}^t M^R_{s:t}; tau = inf{t: D^ARL_t >= A}.
  Thm 2.2 (p7): D^ARL is an e-detector; E_R[tau] >= A for every R; P_R(tau <= m) <= m/A (eq (2)).
- PFA detector, eq (3) (p7): D^PFA_t = inf_R sum_s pi_s M^R_{s:t}, deterministic pi_s > 0, sum pi_s <= 1,
  tau = inf{t: D^PFA_t >= 1/alpha}. Canonical pi_s = c_pi / (s {log(es)}^2) (eq (4)). Thm 2.3 (p7):
  sup_R P_R(tau < inf) <= alpha.
- Proof structure (B.1, p36-37): for oracle R0, S^{R0}_t = sum_s M^{R0}_{s:t} satisfies
  E[S_tau] <= E[tau]; D_t <= S^{R0}_t because of the infimum; PFA via an e-process
  1 - sum pi + sum pi Z and Ville. Validity is therefore per true R, and measurability of the inf is
  assumed (p7).
- Example 1, sub-Gaussian mean (Sec 3, p8): P_theta = sigma^2-sub-Gaussian laws with mean theta;
  eq (6): M^theta_{s:t} = (1+rho^2 sigma^2 n)^{-1/2} exp{ rho^2 n^2 (Xbar_{s:t} - theta)^2 /
  (2 (1 + rho^2 sigma^2 n)) }, n = t-s+1; detector eq (7),(11): inf over theta in R. Theorems 3.2
  (ARL delay, rate I = (mu-nu)^2/(2 sigma^2)), 3.3 (PFA delay).
- Example 2, bounded mean (Sec 4, p10-12): P = laws on [0,1]; eq (17) W^theta_{s:t} = prod {1 +
  lambda_{s,i}(theta)(X_i - theta)} with predictable bets in [-1/(1-theta), 1/theta] (test martingale
  when E[X_i | F_{i-1}] = theta); recommended point-null process the Cover universal portfolio with
  arcsine (Jeffreys) mixture, eq (18): U^theta_{s:t} = int_0^1 prod_i {1 + lambda_theta(p)(X_i - theta)} Pi_J(dp),
  lambda_theta(p) = (p - theta)/(theta(1-theta)). Detector eq (21): D^{UP,w}_t = inf_{theta in (0,1)}
  sum_s w_s U^theta_{s:t}; ARL uses w_s = 1, PFA uses w_s = pi_s, A = 1/alpha. Prop 4.1 (p11) validity
  and growth, Thm 4.2 (p11) delay log A / I_bet with I_bet(Q,theta) = sup_lambda E_Q log(1+lambda(X-theta))
  = inf_{R in P_theta} KL(Q||R) (eq (19),(20)). Computation: Gauss-Chebyshev with K >= (H+1)/2
  nodes is exact for horizon H (p11); cost O(t) active starts per step, quadratic total.
- Example 3, Gaussian unknown variance (Sec 5, pp12-15): universal-inference t e-process eq (22),(23),
  detector eq (26); full Gaussian detector eq (33)-(35); Thms 5.2, 5.3. Not needed for ShiftLab.
- General delay upper bounds with adjusters (Sec 6, pp16-20), lower bounds (Sec 7, pp21-22):
  Thm 7.3 (p22) early-change impossibility. Statements only.
- Markov (App A, pp27-32): two-state chain, F_t = sigma(X_0..X_t), class Theta_kappa = [kappa,1-kappa]^2,
  Jeffreys-mixed e-process eq (51)/(52), baseline-shifted M~ = (1 + M)/2 eq (53), ARL detector eq (57),
  PFA detector eq (58), Cor A.2 (p31) validity without independence, Thm A.3 delay. Only a
  2-state first-order chain with compact parameters is covered.

## 4. Hyperparameters and defaults used

Sec 8 (pp23-24): A = 1000, rho^2 = 1, N(0,1) to N(delta,1) with T = 500, 4000 replications
(Table 1). Bounded: a = 0.3, b = 0.5; Bernoulli(0.5), Beta(10,10), two-point {0.45,0.55}; A in
{1e5,1e8,1e12,1e20}; 4000 replications (Table 2). Panel A medians/(log A / I_bet): Bernoulli
153 (1.159), 349 (1.101), 563 (1.066); Beta 28 (1.180), 62 (1.089), 101 (1.064); two-point 27
(1.186), 60 (1.098), 97 (1.065). Panel B ratios 1.284, 1.139, 1.096, 1.078. Table 1 CADD (ours vs
repeated CS): delta=1.00: 17.297 vs 28.489; 1.25: 11.297 vs 16.335; 1.50: 8.129 vs 10.905; 2.00:
5.177 vs 6.309. Cleveland R script: A = 1000, theta grid of 4001 points on [1e-5, 1-1e-5], bounds
+-80, 640 games.

## 5. Guarantee

- Thm 2.2 (ARL) and Thm 2.3 (PFA): finite-sample, for every R in P, iid null in the main text;
  extends to dependence if a conditional s-delay e-process exists (App A, Cor A.2). Requires
  deterministic start weights (PFA) and measurability of the infimum.
- The infimum is over a continuum. The author R code replaces it by a minimum on a 4001-point
  theta grid; a grid minimum is an upper bound of the true infimum, so crossings can be
  anti-conservative (the earlier ShiftLab audit makes the same point for its scalar optimiser).
  Author Python (run_bounded_double_asymptotic.py) uses 30 bisection steps for a two-start composite.
- Delay results are asymptotic (alpha -> 0, late change T_alpha); not finite-sample.
- Does NOT cover: one-sided "challenger better" detection; promotion certificates (a constantly
  better challenger never fires the detector); non-stationary pre-change laws (null is iid R);
  label budgets, IPW, delays, restart after alarm, switch costs.

## 6. Mapping to ShiftLab's contract; achievable tier

- Possible use: sentinel on the deployed model's loss stream or on d_t = paired loss difference, to
  signal "the law of the stream changed" in either direction. It is not a candidate-net-benefit
  certificate or rollback-harm test (harm can occur with an unchanged law, and a law change need
  not imply harm). Target mismatch already noted in NONPARTITIONED_PFA_AUDIT.md.
- Values must lie in [0,1]: map d to (d+1)/2; IPW subsampling would break boundedness (range 1/frac)
  and make the iid null depend on the sampling design. Label clock (queried events only) keeps iid
  if queries are outcome-independent; delayed or out-of-order releases are not treated (UNVERIFIED).
- Tier: T1 achievable for the full-information bounded-mean ARL/PFA detector (port or call the
  author R/Python code; compare crossing times with `cleveland-bounded.R` outputs
  `nonpartition_cavaliers_detector_A1000.csv`, whose file is in the repo). T2 for eqs (1),(3),(18),(21)
  with exact quadrature. In the ShiftLab contract: T3 at best, only with every deviation listed;
  must not be reported as a comparator for promotion or rollback.

## 7. Existing ShiftLab code

- `scripts/exhaustive_evaluation/check_nonpartitioned_pfa.py`: implements the sub-Gaussian Gaussian
  mean-change quadratic form (l.16-19: log mean over s of -0.5 log(1+n) + n^2 (xbar - theta)^2/(2(1+n))),
  which is eq (6) with sigma^2 = rho^2 = 1, finite support pi_s = 1/120, infimum via scalar bounded
  minimisation over the hull of segment means (l.64-72), threshold log 20. MATCHES eqs (3),(6),(11)
  (PFA form with pi_s = 1/H). Discrepancies: finite-support pi_s = 1/H instead of eq (4); numerical
  infimum is an upper bound of the true inf so crossings are diagnostic only (stated in the
  script docstring and audit); it does NOT implement the bounded-mean universal-portfolio detector
  (eq (18),(21)) that is the relevant one for losses in [0,1]; no Markov detector. Four paths,
  one seed; no PFA estimate. Tier: T2 formula pilot, not T1 (no comparison with author numbers).
- Audit text says "Section2.2 Eq3-5 and Theorem2.3, Section3 Eq6": consistent with this PDF.
- No ShiftLab implementation of Markov transition changes (scripts mention MARKOV_TESTING_APPLICABILITY.md;
  not read here).

## 8. Reproduction tests available

- Constant sequence closed form: with X_i = 0 the PFA statistic equals (1/H) sum_{t..} (1+n)^{-1/2}
  (already in check_nonpartitioned_pfa.py l.101-103); Table 1 CADD values above (needs 4000 reps;
  shorten to a CPU smoke).
- Table 2 Panel A: Bernoulli UP closed form `betaln(S+.5, n-S+.5) - betaln(.5,.5) - S log a - (n-S) log(1-a)`
  (run_exact_up_oracle.py) gives point-null log statistic; median/(log A / I_bet) 1.159 at A=1e5.
  I_bet values 0.087177, 0.485201, 0.505800 (p23).
- Eq (24)-style identity not needed. Trivially check D^ARL <= oracle S^{R0} (domination step).

## 9. Open questions / UNVERIFIED

- Proofs in Sec 6-7 and appendices B-E not read; Markov delay theorem A.3 only seen as a statement.
- Whether a certified lower bound on the inf over theta exists in the paper (not found in main text).
- Venue: preprint only as of 2026-11-06; version may change.
- Delayed/queried feedback not discussed in the paper (grep not exhaustive).
