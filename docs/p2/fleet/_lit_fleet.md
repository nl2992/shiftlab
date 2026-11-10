# Literature check: fleet-level FDR + pooled-prior betting for model-promotion e-processes

Date: 2026-11-09. Method: web search plus arXiv abstract fetches. [fetched] = title, authors and abstract confirmed on the arXiv page. [search] = confirmed only via search-result metadata (existence solid, details less so). Items I could not verify are listed at the end and not asserted.

## A. Multiple-testing / FDR layer

1. **e-BH.** Wang & Ramdas, "False discovery rate control with e-values," JRSS-B 84(3):822-852, 2022. https://arxiv.org/abs/2009.02824 [search]. Reject the k largest e-values where e_(k) >= m/(alpha k). FDR control under arbitrary dependence. Offline, fixed m, one e-value per hypothesis.

2. **Stopped e-BH.** Wang, Dandapanthula, Ramdas, "Anytime-valid FDR control with the stopped e-BH procedure," arXiv 2502.08539, 2025 [fetched]. https://arxiv.org/abs/2502.08539. Applying e-BH to adaptively stopped e-processes can fail FDR control because information leaks across streams; they give a causal/filtration condition under which it is valid. Directly relevant caution for per-episode stopping (threshold crossing or budget exhaustion) with overlapping episodes. No pooling, delays or budgets.

3. **e-LOND.** Xu & Ramdas, "Online multiple testing with e-values," AISTATS 2024 (PMLR 238). https://arxiv.org/abs/2311.06412 ; https://proceedings.mlr.press/v238/xu24a.html [search]. LOND-style alpha-wealth spending (gamma_i) on one e-value per hypothesis; FDR control under arbitrary dependence; randomized and confidence-interval extensions. Decisions at arrival, no overlap or delay.

4. **Online e-BH / online BH.** Fischer, Xu, Ramdas, "An online generalization of the (e-)Benjamini-Hochberg procedure," arXiv 2407.20683 (v4 Sept 2025) [search]. https://arxiv.org/abs/2407.20683. Online analogue of (e-)BH; controls SupFDR (hence FDR at data-adaptive stopping times) under arbitrary dependence; uniformly improves e-LOND; boosts under local dependence. Best off-the-shelf fleet-level candidate.

5. **LOND/LORD.** Javanmard & Montanari, "On Online Control of False Discovery Rate," arXiv 1502.06197 (2015) [search]; journal version "Online rules for control of false discovery rate and false discovery exceedance," Ann. Statist. 46(2):526-554, 2018 (arXiv id not confirmed). https://arxiv.org/abs/1502.06197. p-value based; independence/PRDS.

6. **SAFFRON.** Ramdas, Zrnic, Wainwright, Jordan, ICML 2018 (PMLR 80). https://arxiv.org/abs/1802.09098 [search]. Adaptive alpha-investing with candidate threshold (online Storey-BH analogue); p-value based.

7. **Asynchronous online testing.** Zrnic, Ramdas, Jordan, JMLR 22(33):1-39, 2021. https://arxiv.org/abs/1812.05068 ; https://jmlr.org/papers/v22/19-910.html [search]. Tests start and stop at arbitrary times; "conflict sets" give FDR control under local dependence. Closest structural match to overlapping, delayed episodes. p-value based; no pooled priors, no label budgets.

8. **Bandit A/B + online FDR.** Yang, Ramdas, Jamieson, Wainwright, NeurIPS 2017. https://arxiv.org/abs/1706.05378 [search]. Each A/B test becomes a best-arm problem with an always-valid sequential p-value; online-FDR level of test i is its confidence level. Sequential per-hypothesis plus online FDR, but no prior pooling, no delayed or paid labels. ("Jamieson & Jain, A bandit approach to multiple testing with FDR control" did not surface; not cited.)

9. **Always-valid inference.** Johari, Pekelis, Walsh (+Koomen), arXiv 1512.04922; Operations Research 70(3):1806-1821, 2022. https://arxiv.org/abs/1512.04922 [search]. Mixture-SPRT always-valid p-values for A/B tests, with FDR control across experiments discussed. The mixing prior is user-chosen, not learned across experiments.

10. **Adaptive sampling + e-BH.** Lin, Ma, Ren, Wei, "Sample-Efficient Multiple Testing with Adaptive Data Collection," arXiv 2609.26651, Sept 2026 [fetched]. https://arxiv.org/abs/2609.26651. e-PS chooses which hypothesis to sample from average log e-value increments; e-BH on the e-processes; FDR at arbitrary stopping times; sampling budget. Nearest to budgeted allocation plus e-BH, but offline hypothesis set, no online arrival, no learned prior, no delays.

11. **Online closed testing.** Fischer & Ramdas, arXiv 2407.15733 [search]. https://arxiv.org/abs/2407.15733. FWER-type, background only.

## B. Pooling / empirical Bayes / learned bets

12. **Compound e-values.** Ignatiadis, Wang, Ramdas, "Asymptotic and compound e-values: multiple testing and empirical Bayes" (v1: "Compound e-values and empirical Bayes"), arXiv 2409.19812. https://arxiv.org/abs/2409.19812 [search]. Compound e-values (average null expectation <= 1) still give e-BH FDR control; every FDR procedure is e-BH with suitable compound e-values; log-optimal separable compound e-values for point alternatives come from empirical Bayes / compound decision theory. Main theory for learning the alternative from other hypotheses while keeping FDR validity, but fixed-batch and non-sequential.

13. **E-values as unnormalized weights.** Ignatiadis, Wang, Ramdas, Biometrika 2024, arXiv 2204.12447 [search]. Background on prior-informed weighted BH.

14. **Learned betting, single stream.** Taga, Oymak, Shekhar, "Learning to Bet for Horizon-Aware Anytime-Valid Testing," arXiv 2603.19551, ICML 2026 [fetched]. https://arxiv.org/abs/2603.19551. Finite-horizon control view of betting; a DQN trained on synthetic tasks maps statistics of past observations to bets across horizons and nulls. Valid via predictable bets. No FDR layer, no empirical Bayes from real earlier decisions.

15. **Betting foundations.** Waudby-Smith & Ramdas, "Estimating means of bounded random variables by betting," JRSS-B (read paper 2023), arXiv 2010.09686 [search]. https://arxiv.org/abs/2010.09686. Any predictable bet gives a nonnegative martingale, so bets may depend on anything in the past filtration, including resolved earlier decisions. This is the standard validity argument that permits cross-decision pooling.

16. A search for meta-learned or empirical-Bayes betting priors across tasks returned only online-learning/PAC-Bayes meta-learning work (e.g. across-task coin-betting initial wealth) with no e-process/FDR link [search; titles not verified, not cited].

## C. A/B platforms and EB priors

17. **A/B testing with fat tails.** Azevedo, Deng, Montiel Olea, Rao, Weyl, J. Political Economy 128(7), 2020, doi 10.1086/710607. https://www.journals.uchicago.edu/doi/10.1086/710607 [search]. Empirical Bayes on Bing experiments: estimate the cross-experiment effect distribution (fat-tailed), use it for sample-size and launch rules. Pools a prior but fixed-sample, no anytime validity or FDR guarantee.

18. Deng/Xu/Kohavi/Walker Bayesian A/B papers and Netflix/Eppo sequential-testing material: not confirmed by search; no claims made.

## D. Does anything already do the combination?

No verified source does pooled/empirical-Bayes-learned betting priors plus online FDR over overlapping model-promotion e-processes with per-decision label budgets and delays.
- Online FDR with e-values (3, 4): one e-value per hypothesis at arrival; no overlap, delay, budgets or prior learning.
- Asynchronous overlap (7): p-values and local dependence; no e-processes with budgets, no pooling.
- Sequential e-processes + FDR at stopping times (2, 8, 9, 10): offline or bandit; 10 has sampling budgets but no online arrival or learned priors.
- Empirical-Bayes e-values (12): pooling plus FDR validity, but non-sequential.
- Learned bets (14, 15): validity by predictability; no fleet FDR; no cross-decision empirical Bayes.
- EB priors in A/B (17): pooling, but no anytime or FDR guarantee.

## E. Apparently unexplored combination

1. Compound/EB theory (12) carried to sequential per-decision e-processes: the bet for decision j uses a prior fitted only on decisions whose labels were fully resolved before j's filtration starts, so per-decision validity is predictability (15); the fleet guarantee comes from online e-BH / e-LOND (3, 4) subject to the stopped-e-BH condition (2).
2. Pooling induces cross-decision dependence. e-BH and e-LOND tolerate arbitrary dependence, but the leakage condition of (2) and delayed-label conflict sets (7) must be checked explicitly; an e-process analogue of asynchronous conflict sets with delayed labels is not worked out in what I found.
3. Hard per-decision label budgets inside the alpha-wealth / e-BH calibration (e-value defined at budget exhaustion, not only at crossing) are not treated by 3 or 4; 10 is nearest.
4. Optimal bet under a learned prior for the fleet objective (expected true promotions subject to online FDR) has no result I found.

Caveats: several details come from search snippets, and (4), (12) have multiple revisions, so check the latest version before citing theorem numbers. Absence of evidence reflects a limited search, not an exhaustive survey; do a targeted check for 2026 work on "online e-BH with delayed feedback / learned priors" before claiming novelty.
