# E0b: targeted search for R1 (time-uniform chaining plus disagreement-based querying)

**Date:** 2026-10-29. **Gate:** Phase E, E0b (`LANE_CONTROL.md`). **Status:** literature audit only. No code, no experiment, no novelty claim.
**Input:** `E0_prior_art.md`, residuals R1 and R2 and composition baseline C-E.

## 1. Verdict

**R1: COVERED, as a composition. E1 should EXIT.** Confidence: moderate (about 75%).

- No single paper states the combined theorem: a time-uniform guarantee over a candidate class whose cost is a covering number in rho(c,c') = P(c(x) != c'(x)), together with a disagreement-gated, importance-weighted query rule.
- Every ingredient is published, and the join is an elementary union-over-a-net argument. That matches E0 exit trigger 1 ("dominated by a union over an eps-net plus a standard discretisation argument").
- The query rule half is IWAL itself. IWAL (Beygelzimer, Dasgupta, Langford 2009) already has all of the following:
  - a disagreement-gated query probability;
  - Horvitz-Thompson (importance) weights that depend on past data;
  - a guarantee that holds for all T at once, uniformly over all pairs in the class;
  - a label-complexity bound governed by a disagreement coefficient defined through rho.
- **R2 is also largely covered** (section 4). The IWAL rule queries on the disagreement of any two live candidates, not on disagreement with one reference. That is already a pairwise-closure sampling floor.
- Delay, hard budget and reversible switching change the power and the optimisation, not the form of the validity argument (section 5).
- Honest scope of "covered": I did **not** find a paper that writes down "time-uniform chaining for HT-weighted martingales with predictable query probabilities." It is a derivation, not a citation. A derivation this routine is not a contribution.

## 2. The IWAL statements actually read (primary text, arXiv 0812.4952)

I extracted the PDF text and read the statements and the proofs of Theorem 1, Lemma 1 and Theorem 2. Minus signs and radicals were dropped by the extractor, so I restate constants in words and do not transcribe them.

1. **Algorithm 1 and Algorithm 2 (loss-weighting).**
   - The query probability is p_t = max over f,g in H_t, and over y, of [l(f(x_t),y) - l(g(x_t),y)].
   - Here H_t is the surviving version space, the set of hypotheses whose importance-weighted empirical loss is within slack Delta_{t-1} of the best.
   - So the query probability is zero when all live hypotheses agree on x_t, and it is the size of the **pairwise** loss range among live hypotheses otherwise.
   - A queried label gets weight 1/p_t. The estimator is L_hat_T(h) = (1/T) sum_t (Q_t/p_t) l(h(x_t),y_t), which is unbiased for any predictable p_t.
2. **Theorem 1 (fixed T, finite H, p_t >= p_min).**
   - P( max_h |L_hat_T(h) - L(h)| > (1/p_min) sqrt( (2/T) (ln|H| + ln(2/delta)) ) ) < delta.
   - The proof is Azuma on the martingale Z_t = sum_i (Q_i l/p_i - L), then a union over H.
   - The paper remarks that the argument "can be extended to VC spaces." No proof is given.
3. **Lemma 1 (time-uniform, pairwise-uniform).**
   - With probability at least 1 - delta, for all T and all f,g in H_T: |L_hat_T(f) - L_hat_T(g) - L(f) + L(g)| <= Delta_T.
   - Delta_T is of order sqrt( (1/T) ln( T(T+1) |H|^2 / delta ) ). The statement as extracted shows the argument without its radical, so check the radical in the PDF.
   - Failure probability is spent as delta/(T(T+1)) across time and over all pairs (f,g) in H.
   - **The class enters only through ln|H|**, from the union over pairs.
   - Boundedness of each increment (|Z_t| <= 2) comes from p_t >= |l(f)-l(g)| for live f,g, which is exactly the pairwise-disagreement gate.
4. **Theorem 2.** With probability at least 1 - delta, for any T >= 1, the best hypothesis stays in H_T and L(f) - L(g) <= 2 Delta_{T-1} for all f,g in H_T.
5. **Theorem 7 (label complexity).**
   - If the loss has slope asymmetry K_l and the problem has disagreement coefficient theta, then with probability at least 1 - delta, the expected labels requested in the first T rounds are at most 4 theta K_l ( L* T + O( sqrt( T ln(|H| T/delta) ) ) ).
   - The disagreement coefficient is the Hanneke quantity. It is a ratio of the probability of the disagreement region DIS(h*, r) to r, and the ball is taken in the pseudometric rho. So **rho is already the metric that drives the label cost.**
6. **Follow-up (Beygelzimer, Hsu, Langford, Zhang, NIPS 2010, arXiv 1006.2588; PARTIAL).**
   - Theorem 1 there is a Bernstein-style bound for HT sums whose range and variance are controlled only where f is non-zero, with a log log r_max price for the unknown query-probability floor. That is the variance-adaptive version.
   - Lemma 1 there is a time-uniform bound via union over n and over H.
   - Theorems 2 and 3 give the consistency and label-complexity results, the latter in terms of theta.
   - The paper says explicitly "for simplicity, we assume H is finite." The class cost is again ln|H|, hidden in the constant C0 = O(log(|H|/delta)).

**What IWAL does not do:** it pays ln|H| (or an unproven VC extension), not a covering number in rho. It also has no hard budget, no delay, and an i.i.d. stream, and its error criterion is not an any-false-promotion rule against an incumbent.

## 3. Ingredients for "covering number in rho" and "time-uniform"

| Piece | Source | Level | What it gives | Gap relative to R1 |
|---|---|---|---|---|
| Chaining / majorizing measures for **martingale-dependent** data | Rakhlin, Sridharan, Tewari line; arXiv 2102.01729, "Majorizing Measures, Sequential Complexities, and Online Learning" | PARTIAL (a fetch summary of the first 100k characters, including Theorem 3 and Corollary 10; not read in full) | Sequential generic chaining; a Dudley-type bound with fractional covering numbers (Corollary 10) | **Fixed horizon n.** No time-uniform statement in what I read. The metric is on tree-valued sequences, not rho on covariates. |
| Time-uniform quantile / DKW | Howard and Ramdas, arXiv 1906.09712 (Bernoulli 2022) | PARTIAL (read the Theorem 2 statement and the chaining remark) | Theorem 2: P( exists t >= m : \|\|F_t - F\|\|_inf > 0.85 sqrt( (log log(et/m) + C)/t ) ) <= 1612 e^{-1.25 C}. Proof: a maximal inequality (James 1975; Shorack and Wellner) plus a union over exponentially spaced epochs. | One-dimensional CDF class only. The authors state that these methods "are closely related to ... chaining ... and similar bounds can be derived using existing chaining techniques." That is an explicit admission that the generalisation is routine. |
| Offline to time-uniform conversion | Manole and Ramdas, arXiv 2103.09267 | ABSTRACT (and a search snippet naming "suprema of empirical processes" and a sequential DKW) | Reverse-submartingale device that turns offline concentration into confidence sequences at an iterated-logarithm price | Exchangeable / i.i.d. only. Does not cover HT-weighted adaptive queries. |
| Time-uniform PAC-Bayes | Chugg, Wang, Ramdas, arXiv 2302.03421 (JMLR 2023) | SNIPPET | Nonnegative supermartingales, mixtures, Donsker-Varadhan, Ville. Posterior-dependent bounds at all stopping times, including non-i.i.d. and nonstationary losses. | Cost is KL(posterior \|\| prior), not a covering number. With a point-mass posterior this is ln(1/prior(c)), i.e. **weighted Bonferroni**, which the repo already has (alpha_i = alpha/[i(i+1)]). |
| PAC-Bayes meets chaining | Audibert and Bousquet, JMLR 8, 2007 | SNIPPET | A chaining-style prior (majorizing measure) inside a PAC-Bayes bound | Fixed n. Combining it with the previous row gives the time-uniform, chained prior on paper, but I found no paper that does so. |
| Self-normalized time-uniform | Whitehouse, Wu, Ramdas, arXiv 2310.09100 | SNIPPET | Dimension-dependent vector bounds | **Not a chaining result.** A 2024 citation (arXiv 2409.06060, SNIPPET) says it relies on a covering argument. Not relevant. |
| Finite-K anytime-valid selection | Molitor, "Anytime-valid optimal policy identification," arXiv 2606.17515 | ABSTRACT | Sample complexity of order (log\|Pi\| + log log(1/Delta_min))/Delta_min^2 on logged data | Finite class, ln\|Pi\|, no queries, no chaining. This is the baseline R1 would have to beat. |
| Off-policy confidence sequences | Karampatziakis, Mineiro, Ramdas, arXiv 2102.09540; Waudby-Smith et al., arXiv 2210.10768; Koppe and Jun, arXiv 2502.10826 | SNIPPET | HT/IPS betting confidence sequences, single policy or finite set | Single policy or union over a finite set. |
| Sequential model confidence sets | Arnold et al., arXiv 2404.18678 | ABSTRACT | Anytime-valid model confidence sets with time-uniform coverage | Fully observed losses, no label acquisition. |
| Class-indexed betting / PEAK | Composite sequential tests, arXiv 2402.06122 | ABSTRACT | Averaging in place of a union bound across multiple streams | Means of K streams, no covering number, no acquisition. |
| Active model selection | Model Picker (arXiv 2010.09818), CAMS (arXiv 2207.06030), CODA | SNIPPET beyond what E0 recorded | Disagreement-gated queries over a finite model set | Fixed-confidence or regret guarantees. No time-uniform covering-number analysis. |

**Searches that returned nothing, stated plainly.** Queries for "time-uniform chaining," "anytime-valid uniform convergence over a VC class," "e-process indexed by a function class," and "sequential Hanneke disagreement coefficient with confidence sequences" returned no paper stating the combined result. I cannot rule out one that the search engine did not index.

## 4. Why the join is a composition

**Validity half.** Take the e-process on a net and a pathwise slack.
1. For a decision cost in [0,1], |l(c(x),y) - l(c'(x),y)| <= 1[c(x) != c'(x)] pathwise. So rho is the natural pseudometric, and discretisation is controlled by the observed disagreement indicator.
2. Because covariates are free, 1[c(x_t) != c'(x_t)] is observed at every event, queried or not. The slack for replacing c by its net point c' is therefore **observed and pathwise**, with no extra probability to pay.
3. The probabilistic part is a union (or weighted Bonferroni) over net points at dyadic scales eps_j, spending alpha_j = alpha/[j(j+1)] across scales. That is the Dudley / stitching move, and Howard and Ramdas state that it follows from existing chaining techniques.
4. The cost is ln N(eps_j; rho) at scale j (plus the ln(j(j+1)) spend). The empirical version uses rho_hat on the observed unlabeled stream.

**Selection half.** Query with IWAL's pairwise rule. In C-E terms this is q_t(x) = max(pi_min, f(S_t(x))), where S_t(x) is the set of live candidates, **including the incumbent**, that disagree at x.

**Not new:**
- The ratio between Haussler's bound ln N(eps; rho) <= O(d ln(1/eps)) and ln K is the only quantitative question, and E0 section 4 already caps the gain at a log K factor (about 3.3x at K = 1024, alpha = 0.05).
- For the K <= 32 of E2 the covering number is dominated by K unless candidates are tightly clustered, and then the difference is a few multiples of a logarithm.

**R2 overlap.**
- IWAL's rule maximises over f,g in H_t, not over f against a fixed reference. This is the pairwise-closure sampling floor R2 proposed.
- Lemma 1 holds uniformly over all pairs (f,g). So re-baselining (switching the incumbent to a different live candidate) needs no new spending.
- The remaining R2 risk (events under-sampled because only a dead candidate disagreed) is handled by IWAL keeping dead candidates out of H_t only after they are certified worse.

## 5. Does delay, hard budget or reversible switching change anything substantive?

My judgement, with the reasoning:

- **Hard budget.**
  - Validity is not at stake. HT e-processes with any predictable q_t > 0 remain supermartingales under the causal null, because validity needs only predictability and E[Q_t/q_t | H_t] = 1.
  - IWAL's bounded-increment argument needs p_t >= pair loss range. A cap that violates this loses the range bound, so one needs a bet-size cap tied to q_min (as in a betting e-process) and a pi_min floor.
  - The budget therefore enters as a power / allocation constraint. That is the Cheng-style trade-off Lane A already has, and it is not a new guarantee.
- **Delay.**
  - Event-prefix bookkeeping from `docs/delayed_event_prefix_validity.md` preserves validity, and Ryabchenko et al. cover fixed delay.
  - IWAL has no delay. Delay is a bookkeeping layer on the e-process, not a change to the chaining argument.
- **Reversible switching.**
  - Pairwise-uniform guarantees make a data-dependent incumbent choice free.
  - The false-promotion-constrained switching cost is Lane A's G1, shared by every Lane B candidate.
- **Non-stationarity (the only real difference from IWAL).**
  - IWAL assumes an i.i.d. stream with a fixed population loss L(h), so rho is a fixed population quantity.
  - The E0 contract uses a causal conditional null E[Z_k | H_t] <= 0, which a per-candidate e-process handles directly.
  - The pathwise slack in section 4 needs no stationarity, so the net argument transfers.
  - What does not transfer is any label-complexity statement via a fixed theta. That would need a time-varying rho_t. This is a statement about analysis, not a new mechanism.

## 6. What would be left, precisely (not enough for E1)

Each item below is a technical gap rather than a new idea. None survives the E1 kill test as stated.

1. A variance-adaptive stitched chaining bound for HT-weighted martingales with predictable, data-dependent q_t and a pi_min floor. Not found in print. It is the Freedman / Bernstein version of section 4, and the Bernstein structure is already in BHLZ10 Theorem 1.
2. A **lower bound** in terms of a rho-packing number for any-false-promotion-controlled promotion with a hard label cap. I found none. It would be the only item that could meet the E1 gate ("matching bound that C-E cannot attain"), and a Fano-style packing bound is standard.
3. A separation between the chained net and Bonferroni at K <= 32. Per E0 section 4, any such gain is a log K factor at most, and likely a constant at E2 sizes.

## 7. Decision

- **R1: COVERED. R2: largely covered by IWAL's pairwise rule and pairwise-uniform lemma.** Recommend Phase E exit at E1, with the E0 exit triggers 1 and 3 as the stated grounds.
- If the lane continues anyway, the only candidate is item 2: a matching lower bound for any-false-promotion with hard budget in a rho-packing quantity. The prior from this lane's record (every earlier candidate decomposed) says to expect failure.
- If E1 opens, it must start from IWAL (pairwise rule on live candidates plus the incumbent) with the net-plus-slack validity argument as the baseline, not from C-E alone.
- Do **not** claim a time-uniform chaining theorem, a covering-number sample-complexity improvement, or a new disagreement-based acquisition rule as novel.

## 8. Sources and verification level

Levels as in E0: **FULL** (statements and proofs read), **PARTIAL**, **ABSTRACT**, **SNIPPET**, **UNVERIFIED**.

| Source | Level |
|---|---|
| Beygelzimer, Dasgupta, Langford, Importance Weighted Active Learning (ICML 2009), arXiv 0812.4952 | FULL for Theorem 1, Lemma 1, Theorem 2 and their proofs, and for the Theorem 7 statement. Not read: Theorems 3 to 6, 8 and 9 proofs; constants in Delta_T unchecked because the extractor lost radicals. |
| Beygelzimer, Hsu, Langford, Zhang, Agnostic Active Learning Without Constraints (NIPS 2010), arXiv 1006.2588 | PARTIAL: the Theorem 1, Lemma 1, Theorems 2 and 3 statements and the finite-H assumption. Proofs and the exact constants not read. |
| Howard and Ramdas, arXiv 1906.09712 | PARTIAL: the Theorem 2 statement, the chaining remark and the proof outline. |
| arXiv 2102.01729 (sequential majorizing measures) | PARTIAL, via a fetch summary of the first 100k of 148k characters. |
| Manole and Ramdas (2103.09267), Chugg et al. (2302.03421), Molitor (2606.17515), Arnold et al. (2404.18678), PEAK (2402.06122) | ABSTRACT or SNIPPET only. |
| Audibert and Bousquet (JMLR 2007), Koppe and Jun (2502.10826), Karampatziakis et al. (2102.09540), Waudby-Smith et al. (2210.10768), Whitehouse et al. (2310.09100), CAMS (2207.06030) | SNIPPET only. |
| Rakhlin et al. sequential Rademacher complexity (arXiv 1006.1138 or the "emp proc dep" paper) | SNIPPET only: seen as a search hit and not opened. Do not cite as read. |
| Haussler's covering bound for VC classes; Hanneke's survey and Wiener-Hanneke arXiv 1404.1504 | UNVERIFIED for Haussler (from memory); SNIPPET for Hanneke. |
