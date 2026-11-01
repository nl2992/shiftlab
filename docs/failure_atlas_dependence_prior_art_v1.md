# Failure Atlas: R2 prior-art audit of the cycle-6 dependence / sampling-density claims

Date: 2026-11-01. Status: COMPLETE (v1). Scope: literature audit only; no code was run and no repository file other than
this one was changed. Search was done with web search plus local `pdftotext` of arXiv PDFs. Absence findings mean
"not found in this search", not "does not exist".

## 0. Claims audited

Context: cycle-6 (Amendment 7) tests whether published e-process / betting gates lose null validity when queried labels
are dense relative to the correlation time of a Markov-dependent outcome. Candidate claims if V1/V4 hold:

- (i) the false-promotion inflation of a gate scales with rho^(query spacing);
- (ii) a spacing-by-mixing-time acquisition rule, or blocked betting, restores level alpha up to a beta-mixing correction.

Evidence labels. READ = PDF text obtained locally and the cited item located in the text. ABSTRACT = abstract, web
summary or second-hand citation only. MEMORY = from background knowledge, not retrieved this session.

## 1. Key framing point (affects how every source below is read)

Every e-process / betting baseline's validity contract is stated through a conditional null on a filtration, not through a
marginal or stationary-mean null.

- Waudby-Smith & Ramdas (arXiv 2010.09686, READ): the class is "(X_t) with E(X_t | F_{t-1}) = mu" (text near lines 282 and
  4437 of the extracted PDF); Prop 1 (PrPl-H), Thm 2 (PrPl-EB), Thm 3 (hedged capital CS) all rely on it.
- Shin-Ramdas-Rinaldo (arXiv 2203.03532, READ Sec 2.1, Remark 2.1): the pre-change class P is a set of laws over whole
  sequences, "we do not assume independent or identically distributed"; validity comes from a filtration-adapted
  nonnegative process that is a (super)martingale or e-process under each P in the class.

The cycle-6 nulls are "stationary E[-D] = h with a Markov benefit indicator". For a two-state chain with second eigenvalue
rho, the conditional mean of the label observed g rounds later given the last queried label is
h + rho^g (X_prev - h) (elementary Markov algebra, MEMORY/own derivation). It equals h only if rho^g = 0. So these gates'
stated null is not implied by the cycle-6 null whenever rho > 0, and with a constant bet lambda the product of two adjacent
factors has expectation 1 + lambda^2 * Cov(eps_k, eps_{k+1}) = 1 + O(lambda^2 rho^g Var). A V1-positive result is therefore a
demonstration that the gates were run outside their contract, not a refutation of a published guarantee. This is the most
important R2 point: it caps the novelty of any "failure" finding.

## 2. Source table

For each source: contract (null / dependence class / guarantee), item read, evidence label, relation to (i) and (ii).

### 2.1 E-processes, test martingales, e-detectors (iid or conditional-null contracts)

1. Waudby-Smith & Ramdas, "Estimating means of bounded random variables by betting", arXiv 2010.09686.
   Contract: [0,1]-valued X_t with conditional mean mu given the past; time-uniform CS by betting/capital processes.
   Items: Prop 1, Thm 2, Thm 3 (hedged capital), conditional-mean definition. READ.
   Dependence: allowed only via the conditional-mean condition; no mixing result.
   (i): no. (ii): no. Gives the object (hedged CS) that blocked betting would be built from.

2. Shin, Ramdas, Rinaldo, "E-detectors", arXiv 2203.03532 (NEJSDS 2024).
   Contract: composite nonparametric pre-change class of sequence laws; e-detector (a sum/CUSUM-type aggregation of
   e-processes) controls ARL, 1/alpha threshold. Items: Sec 2.1, Remark 2.1, Example 4 and the remark after Example 3 that
   homogeneity and independence examples extend beyond iid when the law drifts within the class. READ (partial; ARL
   theorem numbers not extracted). Dependence: filtration-based only. Nothing on mixing or thinning.
   (i): no. (ii): no.

3. Bhattacharyya & Ramdas, "Change detection with conformal martingales", arXiv 2609.27179.
   Contract: independent observations with unrestricted pre- and post-change laws; PFA and ARL control; delay
   Theta(log T) / Theta(log ARL) (minimax). ABSTRACT only (web-fetch summary; PDF not read).
   This paper does NOT treat dependent data per its abstract; it cannot support claims about Markov streams.
   (i): no. (ii): no.

4. Saha & Ramdas, "Non-partitioned e-detectors for nonparametric sequential change detection", arXiv 2607.28322.
   Contract: validity of Thms 2.2/2.3 "do not require the observations to be independent"; they need a conditionally valid
   delayed e-process for each candidate no-change law and restart time. Appendix on a two-state Markov(p,q) class with
   F_t = sigma(X_0..X_t): Prop A.1 (test martingale per (p,q)), Thm A.3 (delay). READ (appendix text around Prop A.1;
   statements of Thms 2.2/2.3 not read).
   Key: a correct Markov-likelihood e-process is exactly valid on the full chain with no thinning, because the null is the
   full conditional law. Does not address a marginal-mean null. (i): no. (ii): shows the alternative to thinning (model
   the dependence) already exists for parametric Markov nulls.

5. Ramdas, Ruf, Larsson, Koolen, "Testing exchangeability: fork-convexity, supermartingales and e-processes",
   arXiv 2102.00630 (IJAR). Contract: null = exchangeable binary sequences; alternatives = first-order Markov (and
   order-k via double mixture). Prop 5 (every Q-NSM is also a P1-NSM, hence powerless), Thm 6 (the mixture process R_t is a
   Q-safe e-process), Thm 7 (power/growth rate), Thm 13/14/17 (fork-convex hull). READ at the statement level.
   Relevance: a clean, proven example that supermartingale-based tests against Markov structure need the e-process (not
   NSM) route; does not give robustness of an iid betting gate to Markov data. (i): no. (ii): no.

6. Nguyen, "Finite sample inference for generic autoregressive models", arXiv 2009.11124.
   Contract: parametric order-p autoregressive model; contiguous two-block split; conditional likelihood ratio R_T(theta)
   with E[R_T] <= 1 (Lemma 1); martingale M_T (Lemma 2); sequential sup bound Pr(sup_T N_T >= 1/alpha) <= alpha (Prop 3).
   READ. This is "universal inference with dependence", in the parametric conditional-law sense. Not mixing-based and not a
   mean test. (i): no. (ii): no.

7. Bibaut, Kallus, Lindon, "Near-optimal non-parametric sequential tests and confidence sequences with possibly dependent
   observations", arXiv 2212.14411. Contract: delayed-start normal-mixture SPRT; ASYMPTOTIC (burn-in time to infinity)
   type-I error control and rejection time under general nonparametric DGPs via a strong invariance principle for
   martingales. Assumption 1 is a conditional (F_{t-1}) moment/Lindeberg-type condition; Thm 1 is the type-I result. READ
   (assumptions located; proofs not checked). It also cites (second-hand, ABSTRACT level) Bibaut et al. 2021c using McLeish's
   weak invariance principle for delayed-start CSs under dependent (mixingale-type) data. Nothing finite-sample; no spacing or
   acquisition. (i): no. (ii): partial precedent for "dependence-robust but only asymptotic".

8. Xu, Karampatziakis, Mineiro, "Active, anytime-valid risk controlling prediction sets", arXiv 2406.10490: Thm 1, Thm 2.
   Contract: (X_t, Y_t) i.i.d.; labelling policy may be adaptive and randomized (IPW-style); anytime-valid risk control.
   READ (iid assumption confirmed in text, "primarily considered the i.i.d. setting"). Zrnic & Candes, "Active statistical
   inference", arXiv 2403.03208: instances i.i.d., adaptive label collection, asymptotic CLT-based inference. READ (iid).
   These are the closest published analogues of "adaptive label acquisition with an anytime-valid guarantee"; both assume
   iid. (i): no. (ii): no. They define the baseline for adaptive acquisition validity under iid.

### 2.2 Mixing / blocking / thinning results

9. Oliveira, Orenstein, Ramos, Romano, "Split conformal prediction and non-exchangeable data", arXiv 2203.15885 (JMLR 25,
   2024). Contract: split conformal with stationary beta-mixing data; marginal coverage P[Y in C_{1-alpha}] >= 1 - alpha -
   Delta. Items: Prop 10 (Blocking Technique: for bounded h, |E h(B_odd) - E h(B~_odd)| <= 2M (m-1) beta(a), where B~ has
   independent blocks with the same marginals and a is the gap), Thm 1 (general non-exchangeable, penalty terms),
   Thm 4 (stationary beta-mixing, Delta = Delta_cal + Delta_train + epsilon_cal), Thm 5 (empirical coverage), Prop 13-15.
   READ (statements and rate remark: polynomial beta(k) <= k^-b gives iid-order bounds under 1+2c<b).
   This is the exact device cycle 6 would use. It is fixed-sample, coverage-valued, and the penalty grows linearly in the
   number of blocks times beta(gap). (i): gives the upper-bound direction only for coverage, not for sequential gates.
   (ii): directly supports the recipe "gap a, penalty (m-1) beta(a)"; applied to a sup-over-time stopped e-process the
   indicator of {ever cross 1/alpha up to horizon T} is a bounded function of the blocks, so the same coupling applies
   (own one-line extension; I did not find it stated for e-processes).

10. Yu (1994), "Rates of convergence for empirical processes of stationary mixing sequences", Ann. Probab. 22(1), 94-116.
    Blocking via independent-block sequences close in distribution to the mixing sequence; beta- and phi-mixing; VC rates.
    ABSTRACT/secondary only (search result; no theorem number read). Confirms provenance of the blocking technique that
    Oliveira et al. Prop 10 packages. Whether Berbee's lemma is the tool inside was not confirmed here (MEMORY: yes, via
    Berbee coupling).

11. Paulin (2015), "Concentration inequalities for Markov chains by Marton couplings and spectral methods", EJP 20,
    arXiv 1212.2015. Contract: Markov chains (not necessarily homogeneous) with mixing time tau(eps); Cor 2.11 McDiarmid
    for Markov chains with constants ~ tau_min; Thm 3.9 (Bernstein, reversible stationary), Thm 3.11 (non-reversible,
    pseudo spectral gap). READ at statement level. FIXED-n inequalities (union bound over times would be needed for
    anytime use); the variance inflation is ~ 1/gamma, i.e., effective sample size n * gamma. Closest to a "mixing time enters the
    boundary" statement; not time-uniform and not a betting method. No time-uniform Markov-chain CS was found in two
    searches. (i): consistent in spirit (effective sample size shrinks as correlation time grows), not a statement about
    gate false-promotion. (ii): supplies a candidate fixed-time boundary ingredient; the anytime-valid, label-spaced
    version is not there.

12. Owen (2017), "Statistically efficient thinning of a Markov chain sampler", arXiv 1510.07727. Thm 1 (eff(k) < 1 only if
    cost ratio theta < 1/(2 R_k)), Thm 3 (AR(1) optimal lag), Prop 1 (thinning never helps for AR(1) with rho <= 0 at
    zero marginal cost). READ at abstract/statement level. Contract: variance of a sample mean under cost-per-measurement
    theta. This is about estimator efficiency, not validity. It is the right prior art for the efficiency half of a
    "spacing vs power" trade-off and states that thinning pays when each evaluation is costly (here: labels). Link & Eaton
    (2012) argue against routine thinning (ABSTRACT only). (i): efficiency only. (ii): shows "thin because labels are costly"
    is classical; does not give validity.

13. Barber, Candes, Ramdas, Tibshirani, "Conformal prediction beyond exchangeability", arXiv 2202.13415 (Ann. Stat. 51(2),
    2023). Coverage gap bounded by weighted TV distances, Thm 2 (nonexchangeable full conformal) located in the text; split
    conformal theorem number not extracted. Coverage-gap form only; ABSTRACT/statement-level. Same TV-penalty family as item 9.

### 2.3 Sequential tests for Markov data (classical)

14. Phatarfod (1965), "Sequential analysis of dependent observations I", Biometrika 52, 157-166: analogue of Wald's
    fundamental identity for functions on a finite-state Markov chain (via the 1971 follow-up; ABSTRACT / secondary only).
    Wald's SPRT with Markov likelihoods is valid for a simple Markov null. (i), (ii): no.

### 2.4 Searches that returned nothing

- No source found stating that an e-process / betting gate for a stationary mean (marginal null) is anytime-valid under
  beta-mixing, with or without thinning.
- No source found analysing type-I error of active / clustered / burst label acquisition under autocorrelation. Results were
  generic (single-case designs, optional stopping with iid data). Active-label papers (item 8) assume iid.
- No time-uniform Markov-chain confidence sequence with mixing time in the boundary (two searches; Paulin is fixed-time).

## 3. Does the literature state or imply the candidate claims?

(i) Inflation scales with rho^(spacing).
- Upper-bound direction: implied. Prop 10 (item 9) bounds any bounded functional, including the false-promotion indicator
  up to horizon T, by (m-1) beta(a) for the gap-a thinned design. For a stationary two-state chain, beta(a) =
  2 pi0 pi1 |rho|^a (own computation from TV between P^a(x,.) and pi; MEMORY-level, unchecked against a reference). So
  "at most linear in B * rho^g" is a consequence of known tools.
- Lower-bound / exact scaling: not found stated for gates. The elementary computation in Sec 1 shows a drift of order
  lambda^2 rho^g Var per adjacent pair of queried labels, so rho^g is the natural first-order driver. Whether the observed
  false-promotion rate is monotone in rho^(T/B) (V4) is an empirical question; the TV bound is only a worst-case upper bound.
- Hoeffding-type gates use range-based variance; they carry slack in variance for low-prevalence indicators and may remain
  valid in V1 for that reason. Predictable-plug-in empirical-Bernstein / hedged gates adapt to variance and are more exposed.
  (own reasoning.)
- Verdict: PARTIALLY KNOWN / folklore. Not a novelty claim. Only usable as a calibrated, empirical characterisation of
  specific gates.

(ii) Spacing-by-mixing-time rule or blocked betting restores level alpha up to a beta-mixing correction.
- Essentially a corollary of Prop 10 plus Ville: run the hedged betting CS (item 1, Thm 3) on queried labels spaced by gap a;
  level <= alpha + (m-1) beta(a) up to the constant in Prop 10. Item 9 uses the same device for conformal; Yu (item 10) is
  the root. I found no paper stating it for anytime-valid e-processes, so the exact statement is not in the sources I
  read, but it is not a new idea.
- The correction is weak at realistic budgets: requiring (B-1) * 2 pi0 pi1 rho^g <= alpha/2 gives roughly
  g >= ln(B/alpha) / ln(1/rho) (+ constants). For rho = 0.8, B = 50, alpha = 0.1 this is about 30 rounds,
  i.e. B * g exceeds a T = 1000 horizon in several grid cells (B/T = 0.05 gives g = 20). So the certified regime is
  smaller than the empirical regime; an honest theorem would be vacuous where the empirical gates still look fine.
  (own arithmetic; not from a source.)
- The practical obstacle is estimating the mixing time from the same scarce labels and propagating that uncertainty;
  I found no anytime-valid treatment (Paulin-style bounds assume tau known; MEMORY: Hsu-Kontorovich-Szepesvari and
  Wolfer-Kontorovich give mixing-time/spectral-gap estimators for finite chains; not retrieved).
- Verdict: KNOWN IN SPIRIT (blocking) and thin as a contribution; only the sequential-acquisition packaging and mixing-time
  uncertainty are open.

## 4. R2 verdict

- (i): NOT NOVEL as a mechanism (follows from the conditional-null contract and standard mixing/TV bounds); at most a
  descriptive finding about named gates. Tag: R2 KILLED as a headline contribution; retain as a diagnostic result with
  contract-violation framing.
- (ii): NOT NOVEL as an idea (blocking / thinning with a beta-mixing penalty is the standard device, applied to
  conformal prediction in Oliveira et al. Prop 10 / Thm 4); the anytime-valid, label-budgeted acquisition version is a
  small, unpublished-as-far-as-found corollary with a loose correction. Tag: R2 WEAK-SURVIVE; not a paper by itself.
- Interpretation note for Amendment 7: if V1 holds, the correct description is "gates run outside their conditional-null
  contract inflate with dependence"; if V1 fails, the likely explanation is variance slack plus sparse effective
  correlation, consistent with the sampling-density explanation. Neither outcome needs a new theory to explain.

## 5. Most promising non-killed angle

Joint design of validity-driven spacing under a finite label budget when the correlation time is unknown: choose query
spacing g (validity needs rho^g small, power needs dense labels) with an anytime-valid, mixing-time-uncertain correction,
judged by decision cost at a given budget. What is known: validity side via blocking (items 9, 10), efficiency side via
thinning-under-cost (item 12), parametric Markov e-processes (items 4, 5). What was not found: finite-sample, anytime-valid
treatment where mixing time is estimated from the sparse queried labels themselves, and any analysis of clustered /
burst acquisition. This overlaps the Lane-A "joint acquisition + switching" result (calendar-optimal at tight risk) and
should be tested against the calendar baseline before being promoted. Secondary: a conditional-null-faithful gate (bet against
the estimated lag-g conditional mean), which turns dependence from a nuisance into a predictor; the validity then rests on
the estimate being predictable, as in item 1's predictable-plug-in logic.

## 6. Strongest existing baseline to beat if (ii) is pursued

1. Hedged capital betting CS (Waudby-Smith & Ramdas Thm 3) run on queries thinned by a conservative fixed gap, with the
   blocking correction of Oliveira et al. Prop 10. This IS the (ii) design, so (ii) cannot claim novelty over it without
   a better mixing-time or budget story.
2. A correctly specified Markov-likelihood e-process on the skeleton chain (valid without spacing for a Markov null;
   Ramdas-Ruf-Larsson-Koolen Thm 6; Saha-Ramdas Prop A.1; Nguyen Prop 3). The ledger's c1_hmm_cs differs: its emissions are
   assumed iid within regime, so its 0.172 at rho = 0.8 is a misspecified-likelihood result, not a bound on this baseline.
3. The existing uniform calendar with the best-safe gate (current evidence: calendar-optimal at tight risk).
Report each with the same Wilson-interval protocol as V1-V4, and include the certified bound alongside the empirical rate
so vacuity is visible.

## 7. Caveats

- Items 3, 10, 13, 14 and the second-hand citations in item 7 are ABSTRACT/secondary only.
- Theorem numbers in items 1, 4, 5, 9, 11, 12 were located in extracted PDF text; some formulas were garbled by
  `pdftotext` (e.g., the constant in Prop 10 is as extracted: 2M(m-1)beta(a)); confirm against the published version before citing.
- The beta(a) = 2 pi0 pi1 |rho|^a formula and the spacing arithmetic are my own derivations, unchecked.
- Search tool results are summaries; absence claims are limited to a handful of queries.
